// POST /api/fello/webhook : the receiver for Fello's webhook events.
//
// Contract (docs.fello.ai/webhooks): Fello POSTs {events:[{eventType,
// eventDate, data}]} with the raw body HMAC-SHA256-signed by the base64-decoded
// Custom App client secret; the base64 digest arrives in the
// fello-webhook-signature header. Answer 2xx fast (5 seconds, the stricter of
// the two figures in the docs) and do the work afterwards, so every handler
// runs inside context.waitUntil after the 200 is already on the wire.
//
// Routing (step 2 of notes/fello/fello-api-brief.md):
//   FormSubmission          -> the drozq lead pipeline (an internal POST to
//                              /api/lead: alert email, FUB event, drip
//                              enrollment; the Fello push is skipped there so
//                              nothing loops). intent "Fello Seller Lead: ...".
//   DashboardClick, EmailClick, PostcardScan, FelixAIHandoff
//                           -> the HOT path: enrich from Fello, alert email to
//                              TO_EMAIL, FUB "General Inquiry" event tagged
//                              "Fello Hot" (+ "Fello Handoff" for Felix).
//   ContactUnsubscribed     -> pause the drozq drip for that email (never
//                              touches FUB, never re-subscribes anyone).
//   ContactEnriched, ContactDetailsUpdated
//                           -> refresh the FUB person (name / phone / address /
//                              Fello signal tags) via PUT, no timeline noise.
//   TagsAdded               -> mirror the tags onto the FUB person (additive).
//   TagsRemoved, unknown    -> logged only.
// Every event is also captured to PostHog (event "fello_<type>", distinct_id =
// the contact email) and deduped for 6 hours on a hash of the event, because
// Fello retries on anything but a 2xx.
//
// Env: FELLO_CLIENT_SECRET (required; 503 until set so Fello's retry window
// buys time to configure it), FELLO_API_KEY (enrichment reads), TO_EMAIL +
// MailChannels (alerts), FOLLOWUPBOSS_API_KEY (CRM), EMAIL_DB (dedupe + pause).

import { fetchWithTimeout, renderEmail, sendEmail, escapeHtml, phCapture, validEmail } from "../../_lib/email.js";
import { maskEmail } from "../../_lib/redact.js";
import { rememberSubmission } from "../../_lib/idempotency.js";
import { verifyFelloSignature, felloReady, felloGetContact, summarizeFelloContact, FELLO_TAGS } from "../../_lib/fello.js";

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=UTF-8" } });

const HOT_EVENTS = new Set(["DashboardClick", "EmailClick", "PostcardScan", "FelixAIHandoff"]);
const REFRESH_EVENTS = new Set(["ContactEnriched", "ContactDetailsUpdated"]);
const FUB_BASE = "https://api.followupboss.com/v1";

async function sha1hex(s) {
  const d = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(String(s)));
  return Array.from(new Uint8Array(d)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function str(v, max) {
  const s = v == null ? "" : String(v).trim();
  return max ? s.slice(0, max) : s;
}

function snake(eventType) {
  return String(eventType || "unknown").replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase();
}

// Pull the contact identity out of any event shape Fello documents (and a few
// it might): data.contactInfo, data.formSubmissionInfo.formData, or flat.
export function extractContactRef(event) {
  const d = (event && event.data) || {};
  const ci = d.contactInfo || {};
  const fd = (d.formSubmissionInfo && d.formSubmissionInfo.formData) || d.formData || {};
  const email = str(ci.emailId || ci.email || fd.emailId || fd.email || d.emailId || d.email).toLowerCase();
  const contactId = str(ci.contactId || d.contactId);
  const propertyId = str(ci.propertyId || d.propertyId);
  return { email: validEmail(email) ? email : "", contactId, propertyId, assignedUser: str(ci.assignedUserEmailId) };
}

// What happened, in one line, for alerts and CRM notes.
export function describeEvent(event) {
  const d = (event && event.data) || {};
  const type = str(event && event.eventType);
  const info = d.dashboardClickInfo || d.emailClickInfo || d.postcardScanInfo || d.felixAIHandoffInfo || d.handoffInfo || d.clickInfo || {};
  const detail = [info.source, info.sourceDetail || info.cta || info.reason || info.skill].filter(Boolean).join(" / ");
  const labels = {
    DashboardClick: "clicked a call to action on their home-value dashboard",
    EmailClick: "clicked a call to action in a Fello email",
    PostcardScan: "scanned a postcard",
    FelixAIHandoff: "Felix AI handed off the conversation (a live reply is waiting)",
    ContactEnriched: "was enriched with new data",
    ContactDetailsUpdated: "changed contact details",
    TagsAdded: "had tags added",
    TagsRemoved: "had tags removed",
    ContactUnsubscribed: "unsubscribed from Fello email",
    FormSubmission: "submitted a Fello form"
  };
  return (labels[type] || ("triggered " + type)) + (detail ? " (" + detail + ")" : "");
}

// FormSubmission -> the /api/lead field set. Fello's formData is optional
// field by field, so everything is best-effort and the leftovers land in the
// message so nothing is lost.
export function formSubmissionToLead(event, hash) {
  const d = (event && event.data) || {};
  const fsi = d.formSubmissionInfo || {};
  const fd = fsi.formData || d.formData || {};
  const ref = extractContactRef(event);
  const leadType = str(fsi.leadType);
  const buyerish = /buy|purchase/i.test(leadType);
  const intent = (buyerish ? "Fello Buyer Lead: " : "Fello Seller Lead: ") + (leadType || "Form");
  const comps = fd.addressComponents || {};
  const address = str(fd.address) || [
    [comps.aptOrUnitNumber, comps.streetAddress].filter(Boolean).join(" "),
    comps.city, [comps.state, comps.zip].filter(Boolean).join(" ")
  ].filter(Boolean).join(", ");
  const identity = new Set(["firstName", "lastName", "phone", "emailId", "email", "address", "addressComponents", "message"]);
  const extras = [];
  for (const [k, v] of Object.entries(fd)) {
    if (identity.has(k) || v == null || v === "" ) continue;
    extras.push(k + ": " + (typeof v === "object" ? JSON.stringify(v) : String(v)));
  }
  const message = [str(fd.message), extras.length ? "Fello form details:\n" + extras.join("\n") : ""].filter(Boolean).join("\n\n");
  const fields = {
    first_name: str(fd.firstName, 100),
    last_name: str(fd.lastName, 100),
    email: ref.email,
    phone: str(fd.phone) || "0000000000",
    consent: "yes",
    intent: intent.slice(0, 80),
    full_address: address.slice(0, 500),
    street_address: [comps.aptOrUnitNumber, comps.streetAddress].filter(Boolean).join(" ").slice(0, 300),
    city: str(comps.city, 100),
    state: str(comps.state, 20),
    zip: str(comps.zip, 20),
    timeline: str(fd.saleTimeline || fd.timeline, 100),
    referral_source: "Fello",
    source_page: ("fello:" + [fsi.sourceType, fsi.sourceDetail].filter(Boolean).join(":")).slice(0, 100),
    page_url: str(fsi.referrerUrl, 500),
    message: message.slice(0, 5000),
    submitted_at: str(fsi.submissionDate || (event && event.eventDate)),
    submission_id: ("fello-" + hash).slice(0, 80)
  };
  return fields;
}

async function postLead(env, origin, fields) {
  const body = new URLSearchParams();
  for (const [k, v] of Object.entries(fields)) if (v != null && v !== "") body.set(k, String(v));
  const r = await fetchWithTimeout(origin + "/api/lead", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: body.toString()
  }, 15000);
  let data = null;
  try { data = await r.json(); } catch (e) {}
  return { status: r.status, data };
}

// --- Follow Up Boss helpers (personal account, FOLLOWUPBOSS_API_KEY) ------------

function fubHeaders(env) {
  return {
    "Authorization": "Basic " + btoa(env.FOLLOWUPBOSS_API_KEY + ":"),
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-System": "Drozq.com"
  };
}

async function fubEvent(env, payload) {
  const r = await fetchWithTimeout(FUB_BASE + "/events", { method: "POST", headers: fubHeaders(env), body: JSON.stringify(payload) }, 8000);
  return r.status;
}

async function fubFindPerson(env, email) {
  const r = await fetchWithTimeout(FUB_BASE + "/people?email=" + encodeURIComponent(email) + "&limit=1&fields=id,tags,firstName,lastName", { headers: fubHeaders(env) }, 8000);
  if (!r.ok) return null;
  const d = await r.json().catch(() => null);
  const p = d && Array.isArray(d.people) && d.people[0];
  return p && p.id ? p : null;
}

async function fubPatchPerson(env, email, patch, addTags) {
  const person = await fubFindPerson(env, email);
  if (!person) return { ok: false, reason: "not_in_fub" };
  const body = Object.assign({}, patch || {});
  if (addTags && addTags.length) {
    const existing = Array.isArray(person.tags) ? person.tags : [];
    body.tags = Array.from(new Set(existing.concat(addTags)));
  }
  const r = await fetchWithTimeout(FUB_BASE + "/people/" + person.id, { method: "PUT", headers: fubHeaders(env), body: JSON.stringify(body) }, 8000);
  return { ok: r.ok, status: r.status, id: person.id };
}

// --- the HOT alert ----------------------------------------------------------------

function alertHtml(env, summary, what, ref) {
  const rows = [];
  const row = (label, valueHtml) =>
    '<tr><td class="dz-muted" style="padding:7px 16px 7px 0;font-size:11px;letter-spacing:0.8px;text-transform:uppercase;color:#757575;vertical-align:top;white-space:nowrap;">' + label + "</td>" +
    '<td class="dz-p" style="padding:7px 0;font-size:15px;line-height:1.5;color:#2b2b2b;" width="100%">' + valueHtml + "</td></tr>";
  rows.push(row("Signal", "<strong>" + escapeHtml(what) + "</strong>"));
  if (summary.leadScore != null) rows.push(row("Fello score", escapeHtml(String(summary.leadScore)) + " / 100"));
  if (summary.phone) rows.push(row("Phone", '<a href="tel:' + escapeHtml(summary.phone) + '" style="color:#d9222a;font-weight:700;text-decoration:none;">' + escapeHtml(summary.phone) + "</a>"));
  if (summary.email) rows.push(row("Email", '<a href="mailto:' + escapeHtml(summary.email) + '" style="color:#d9222a;font-weight:700;text-decoration:none;">' + escapeHtml(summary.email) + "</a>"));
  if (summary.properties && summary.properties.length) rows.push(row("Property", summary.properties.map(escapeHtml).join("<br>")));
  if (summary.signals && summary.signals.length) rows.push(row("Fello signals", summary.signals.map(escapeHtml).join(", ")));
  rows.push(row("Engagement", escapeHtml(summary.dashboardClicks + " dashboard clicks, " + summary.emailClicks + " email clicks, " + summary.dashboardViews + " dashboard views")));
  if (summary.lastActivityAt) rows.push(row("Last activity", escapeHtml(summary.lastActivityAt)));
  if (ref.contactId) rows.push(row("Fello id", escapeHtml(ref.contactId)));
  const bodyHtml = '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width:100%;margin:2px 0 6px;">' + rows.join("") + "</table>";
  return renderEmail({
    subject: "",
    preheader: what,
    headline: escapeHtml(summary.name || summary.email || "A Fello contact"),
    bodyHtml,
    ctaLabel: summary.phone ? "Call now" : "",
    ctaUrl: summary.phone ? "tel:" + summary.phone : "",
    signature: false,
    unsubUrl: "",
    pixelUrl: "",
    postal: ""
  });
}

async function handleHot(env, event, ref, what) {
  let summary = summarizeFelloContact({ email: ref.email, contactId: ref.contactId }, Date.now(), 7);
  if (felloReady(env) && (ref.contactId || ref.email)) {
    const got = await felloGetContact(env, ref.contactId || ref.email);
    if (got.ok && got.data) summary = summarizeFelloContact(got.data, Date.now(), 7);
  }
  const email = summary.email || ref.email;
  const name = summary.name || email || "Fello contact";
  const tasks = [];
  if (env.TO_EMAIL && env.MAILCHANNELS_API_KEY) {
    const subject = "🔥 Fello hot: " + name + " " + what.split(" (")[0];
    tasks.push(sendEmail(env, {
      to: env.TO_EMAIL, toName: "Joshua", subject,
      html: alertHtml(env, summary, what, ref),
      text: "Fello hot signal\n\n" + name + " " + what + "\nScore: " + (summary.leadScore == null ? "-" : summary.leadScore) + "\nPhone: " + (summary.phone || "-") + "\nEmail: " + (email || "-") + "\nProperty: " + (summary.properties.join(" | ") || "-") + "\n",
      unsubUrl: ""
    }).then((r) => { if (!r || !r.ok) console.error("FELLO_WEBHOOK_ALERT_FAILED " + ((r && (r.error || r.status)) || "-") + " email=" + maskEmail(email)); }));
  }
  if (env.FOLLOWUPBOSS_API_KEY && email) {
    const tags = ["Fello", FELLO_TAGS.hot];
    if (event.eventType === "FelixAIHandoff") tags.push("Fello Handoff");
    const nameTokens = String(summary.name || "").split(/\s+/).filter(Boolean);
    const person = { emails: [{ value: email }], tags, source: "Fello" };
    if (nameTokens.length) { person.firstName = nameTokens[0]; person.lastName = nameTokens.slice(1).join(" "); }
    if (summary.phone) person.phones = [{ value: summary.phone }];
    tasks.push(fubEvent(env, {
      source: "Fello", system: "Drozq.com", type: "General Inquiry",
      message: "Fello: " + what + "." + (summary.leadScore != null ? " Lead score " + summary.leadScore + "." : "") + (summary.properties.length ? " Property: " + summary.properties[0] + "." : "") + (summary.signals.length ? " Signals: " + summary.signals.join(", ") + "." : ""),
      person
    }).then((status) => { if (status < 200 || status >= 300) console.error("FELLO_WEBHOOK_FUB_FAILED status=" + status + " email=" + maskEmail(email)); }));
  }
  await Promise.allSettled(tasks);
  console.log("FELLO_WEBHOOK_HOT type=" + event.eventType + " email=" + maskEmail(email) + " score=" + (summary.leadScore == null ? "-" : summary.leadScore));
}

async function handleUnsubscribe(env, ref) {
  if (!ref.email) return;
  if (env.EMAIL_DB) {
    try {
      const res = await env.EMAIL_DB.prepare(
        "UPDATE subscribers SET status = 'paused', updated_at = datetime('now') WHERE email = ?1 AND status = 'active'"
      ).bind(ref.email).run();
      console.log("FELLO_WEBHOOK_PAUSED email=" + maskEmail(ref.email) + " changed=" + Boolean(res.meta && res.meta.changes > 0));
    } catch (e) {
      console.error("FELLO_WEBHOOK_PAUSE_FAILED " + ((e && e.message) || e) + " email=" + maskEmail(ref.email));
    }
  }
}

async function handleRefresh(env, event, ref) {
  if (!env.FOLLOWUPBOSS_API_KEY || !ref.email) return;
  let summary = null;
  if (felloReady(env) && (ref.contactId || ref.email)) {
    const got = await felloGetContact(env, ref.contactId || ref.email);
    if (got.ok && got.data) summary = summarizeFelloContact(got.data, Date.now(), 7);
  }
  const patch = {};
  const tags = ["Fello"];
  if (summary) {
    const nameTokens = String(summary.name || "").split(/\s+/).filter(Boolean);
    if (nameTokens.length) { patch.firstName = nameTokens[0]; if (nameTokens.length > 1) patch.lastName = nameTokens.slice(1).join(" "); }
    if (summary.phone) patch.phones = [{ value: summary.phone }];
    for (const s of summary.signals) tags.push(s);
  }
  const d = (event && event.data) || {};
  const upd = d.contactDetailsUpdatedInfo || {};
  if (upd.phone && upd.phone.current) patch.phones = [{ value: String(upd.phone.current) }];
  if (upd.fullName && upd.fullName.current) {
    const t = String(upd.fullName.current).split(/\s+/).filter(Boolean);
    if (t.length) { patch.firstName = t[0]; patch.lastName = t.slice(1).join(" "); }
  }
  const r = await fubPatchPerson(env, ref.email, patch, tags);
  console.log("FELLO_WEBHOOK_FUB_REFRESH type=" + event.eventType + " email=" + maskEmail(ref.email) + " result=" + (r.ok ? "ok" : (r.reason || r.status)));
}

async function handleTagsAdded(env, event, ref) {
  const d = (event && event.data) || {};
  const info = d.tagsAddedInfo || {};
  const tags = Array.isArray(info.tagsAdded) ? info.tagsAdded.map((t) => String(t).slice(0, 60)) : [];
  if (!tags.length || !env.FOLLOWUPBOSS_API_KEY || !ref.email) return;
  const r = await fubPatchPerson(env, ref.email, {}, ["Fello"].concat(tags));
  console.log("FELLO_WEBHOOK_TAGS_MIRRORED email=" + maskEmail(ref.email) + " n=" + tags.length + " result=" + (r.ok ? "ok" : (r.reason || r.status)));
}

export async function processEvent(env, origin, event) {
  const type = str(event && event.eventType);
  const ref = extractContactRef(event);
  const hash = await sha1hex(JSON.stringify(event));
  const key = "fello:" + hash.slice(0, 40);
  const seen = await rememberSubmission(env, key, 6 * 3600);
  if (seen.duplicate) {
    console.log("FELLO_WEBHOOK_DUPLICATE type=" + type + " email=" + maskEmail(ref.email));
    return { type, duplicate: true };
  }
  await phCapture("fello_" + snake(type), ref.email || ref.contactId || "fello-anon", {
    event_type: type, contact_id: ref.contactId || null, event_date: (event && event.eventDate) || null, what: describeEvent(event)
  });

  if (type === "FormSubmission") {
    const fields = formSubmissionToLead(event, hash.slice(0, 32));
    if (!fields.email) {
      console.error("FELLO_WEBHOOK_FORM_NO_EMAIL id=" + (ref.contactId || "-"));
      return { type, skipped: "no_email" };
    }
    const r = await postLead(env, origin, fields);
    const ok = r.status === 200 && r.data && r.data.ok;
    (ok ? console.log : console.error)("FELLO_WEBHOOK_FORM_LEAD status=" + r.status + " intent=" + fields.intent + " email=" + maskEmail(fields.email) + (r.data && r.data.duplicate ? " duplicate" : ""));
    return { type, leadStatus: r.status };
  }
  if (HOT_EVENTS.has(type)) { await handleHot(env, event, ref, describeEvent(event)); return { type, hot: true }; }
  if (type === "ContactUnsubscribed") { await handleUnsubscribe(env, ref); return { type }; }
  if (REFRESH_EVENTS.has(type)) { await handleRefresh(env, event, ref); return { type }; }
  if (type === "TagsAdded") { await handleTagsAdded(env, event, ref); return { type }; }
  console.log("FELLO_WEBHOOK_LOGGED type=" + type + " email=" + maskEmail(ref.email));
  return { type, logged: true };
}

async function processAll(env, origin, events) {
  for (const ev of events) {
    try { await processEvent(env, origin, ev); }
    catch (e) { console.error("FELLO_WEBHOOK_EVENT_THREW type=" + str(ev && ev.eventType) + " " + ((e && e.message) || e)); }
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    if (!env.FELLO_CLIENT_SECRET) {
      console.error("FELLO_WEBHOOK_UNCONFIGURED FELLO_CLIENT_SECRET missing");
      return json({ ok: false, error: "webhook_unconfigured" }, 503);
    }
    const raw = await request.text();
    if (raw.length > 512 * 1024) return json({ ok: false, error: "payload_too_large" }, 413);
    const sig = request.headers.get("fello-webhook-signature") || "";
    if (!(await verifyFelloSignature(env.FELLO_CLIENT_SECRET, raw, sig))) {
      console.error("FELLO_WEBHOOK_BAD_SIGNATURE len=" + raw.length + " hasSig=" + Boolean(sig));
      return json({ ok: false, error: "bad_signature" }, 401);
    }
    let body;
    try { body = JSON.parse(raw); } catch (e) { return json({ ok: false, error: "invalid_json" }, 400); }
    const events = Array.isArray(body && body.events) ? body.events : (body && body.eventType ? [body] : []);
    const origin = new URL(request.url).origin;
    if (events.length) context.waitUntil(processAll(env, origin, events));
    console.log("FELLO_WEBHOOK_RECEIVED n=" + events.length + " types=" + events.map((e) => str(e && e.eventType)).join(","));
    return json({ ok: true, received: events.length }, 200);
  } catch (e) {
    console.error("FELLO_WEBHOOK_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: "server_error" }, 500);
  }
}

export async function onRequestGet() {
  return json({ ok: true, endpoint: "fello-webhook", accepts: "POST" });
}
