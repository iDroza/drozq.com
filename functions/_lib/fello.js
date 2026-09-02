// Fello (fello.ai) integration helpers, shared by /api/fello/webhook (the
// inbound event receiver) and /api/fello/engagement (the lead-score readback
// for the dashboard + CLI). pushLeadToFello exists for the CLI / a future
// explicit opt-in ONLY: site leads are NOT pushed to Fello (Joshua's order,
// 2026-09-02, "do not submit leads to fello"); /api/lead never calls it.
//
// Env contract (Cloudflare Pages > Settings):
//   FELLO_API_KEY        the Custom App key (x-api-key). Full account access.
//   FELLO_CLIENT_SECRET  the Custom App client secret: ONLY used to verify the
//                        HMAC on inbound webhooks (base64-decoded key,
//                        HMAC-SHA256 over the raw body, base64 digest in the
//                        fello-webhook-signature header).
//
// Everything here is best-effort and never throws into a request path: the
// callers wrap each call in try/catch or waitUntil. Log markers:
//   LEAD_FELLO_PUSHED / LEAD_FELLO_DUPLICATE / LEAD_FELLO_FAILED / LEAD_FELLO_THREW
//   FELLO_WEBHOOK_* (see /api/fello/webhook)
//
// The tag vocabulary (step 3 of notes/fello/fello-api-brief.md) lives in
// felloTagsFor(): tags are the ONLY handle the API gives into Fello's segments
// and workflows, so every lead pushed from the site carries the same set.

import { fetchWithTimeout } from "./email.js";
import { maskEmail } from "./redact.js";

export const FELLO_BASE = "https://api.fello.ai/public/v1";
export const FELLO_TIMEOUT_MS = 8000;

// The canonical tag set. Keep this list in sync with the brief + /fello/.
export const FELLO_TAGS = Object.freeze({
  site: "Drozq Website",
  seller: "Seller",
  buyer: "Buyer",
  modes: Object.freeze({
    sell: "Drozq: Sell",
    buy: "Drozq: Buy",
    sellandbuy: "Drozq: Sell + Buy",
    valuation: "Drozq: Valuation",
    netsheet: "Drozq: Net Sheet",
    onetap: "Drozq: One Tap",
    other: "Drozq: Lead"
  }),
  timelines: Object.freeze({
    now: "Timeline: Now",
    soon: "Timeline: 1-3 mo",
    later: "Timeline: 4+ mo",
    curious: "Timeline: Curious"
  }),
  paid: "Paid: Google",
  hot: "Drozq Hot"
});

export function felloReady(env) {
  return Boolean(env && env.FELLO_API_KEY);
}

// intent (the /api/lead "intent" field) -> funnel mode key
export function felloModeFor(intent) {
  const i = String(intent || "");
  if (i === "Home Valuation") return "sell";
  if (i === "Home Purchase") return "buy";
  if (i === "Home Sale + Purchase") return "sellandbuy";
  if (i === "Home Valuation Lead") return "valuation";
  if (i === "Seller Net Sheet") return "netsheet";
  if (i === "Google One Tap Lead") return "onetap";
  return "other";
}

// The funnel's four timeline answers -> the four canonical timeline tags.
export function felloTimelineTag(timeline) {
  const t = String(timeline || "").toLowerCase();
  if (!t) return "";
  if (/immediately|right away|asap|now/.test(t)) return FELLO_TAGS.timelines.now;
  if (/1-3|1 to 3|three months|3 months/.test(t)) return FELLO_TAGS.timelines.soon;
  if (/4 or more|4\+|more months|6\+|later/.test(t)) return FELLO_TAGS.timelines.later;
  if (/curious|not sure|just/.test(t)) return FELLO_TAGS.timelines.curious;
  return "";
}

// "/sellers/" -> "Page: sellers", "/" -> "Page: home", "https://drozq.com/x/" -> "Page: x"
export function felloPageTag(sourcePage) {
  let s = String(sourcePage || "").trim();
  if (!s) return "";
  try {
    if (/^https?:\/\//i.test(s)) s = new URL(s).pathname;
  } catch (e) {}
  s = s.split("?")[0].split("#")[0].replace(/^\/+|\/+$/g, "").replace(/\.html$/i, "").replace(/\/index$/i, "");
  if (!s || s === "index") return "Page: home";
  return "Page: " + s.slice(0, 40);
}

export function felloTagsFor(seed) {
  const s = seed || {};
  const intent = String(s.intent || "");
  const mode = felloModeFor(intent);
  const sellerIntent = /valuation|seller|sell|sale|net sheet/i.test(intent);
  const buyerIntent = /purchase|buy/i.test(intent);
  const tags = [FELLO_TAGS.site];
  if (sellerIntent) tags.push(FELLO_TAGS.seller);
  if (buyerIntent) tags.push(FELLO_TAGS.buyer);
  tags.push(FELLO_TAGS.modes[mode] || FELLO_TAGS.modes.other);
  const tl = felloTimelineTag(s.timeline);
  if (tl) tags.push(tl);
  const pg = felloPageTag(s.sourcePage);
  if (pg) tags.push(pg);
  if (s.gclid) tags.push(FELLO_TAGS.paid);
  return tags;
}

// Which /api/lead submissions go to Fello. Newsletter subscribers never do
// (the /field-notes/ page promises no marketing sequences and Fello sends its
// own), and leads that ORIGINATED in Fello (the webhook receiver re-posting a
// FormSubmission into the lead pipeline) never loop back.
export function felloShouldPush(seed) {
  const s = seed || {};
  const intent = String(s.intent || "");
  if (intent === "Field Notes Subscribe") return false;
  if (intent === "Home Valuation View") return false;
  if (/^fello/i.test(intent)) return false;
  if (/^fello/i.test(String(s.referralSource || ""))) return false;
  return Boolean(s.email);
}

export async function felloFetch(env, method, path, body, query) {
  let url = FELLO_BASE + path;
  if (query) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) if (v != null && v !== "") qs.set(k, String(v));
    const q = qs.toString();
    if (q) url += "?" + q;
  }
  const headers = { "x-api-key": env.FELLO_API_KEY, "accept": "application/json" };
  const init = { method, headers };
  if (body !== undefined) {
    headers["content-type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const r = await fetchWithTimeout(url, init, FELLO_TIMEOUT_MS);
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  return { status: r.status, ok: r.ok, data, rateRemaining10: r.headers.get("X-RateLimit-Remaining-10") };
}

export async function felloGetContact(env, ident) {
  const query = String(ident).indexOf("@") >= 0 ? { emailId: ident } : { contactId: ident };
  return felloFetch(env, "GET", "/contact", undefined, query);
}

// Build the POST /contact body from a lead seed (the /api/lead field set).
export function buildFelloContact(seed) {
  const s = seed || {};
  const body = { email: String(s.email || "").trim().toLowerCase(), tags: felloTagsFor(s) };
  const name = String(s.name || "").trim();
  if (name && !/name not provided|website lead/i.test(name)) body.name = name.slice(0, 64);
  // Only a real NANP number: the "0000000000" One Tap placeholder passes the
  // regex but is useless in Fello, so it is dropped rather than sent.
  const digits = String(s.phone || "").replace(/\D/g, "");
  const national = digits.length === 11 && digits.charAt(0) === "1" ? digits.slice(1) : digits;
  if (/^[2-9]\d{2}[2-9]\d{6}$/.test(national)) body.phone = "+1" + national;
  const address = String(s.address || "").trim();
  if (address) body.address = address.slice(0, 256);
  body.crmFields = {
    name: "FollowUpBoss",
    source: "drozq.com",
    stage: "Lead",
    createdDate: s.createdAt || new Date().toISOString()
  };
  if (s.assignedUserEmailId) body.assignedUserEmailId = s.assignedUserEmailId;
  return body;
}

// Push one lead into Fello. Create; on DuplicateContact, append the tags and
// attach the property to the existing record instead (a re-submit or a second
// address is still useful signal). Never throws.
export async function pushLeadToFello(env, seed) {
  if (!felloReady(env) || !felloShouldPush(seed)) return { ok: false, skipped: true };
  const safe = maskEmail(seed.email);
  try {
    const body = buildFelloContact(seed);
    const created = await felloFetch(env, "POST", "/contact", body);
    if (created.ok) {
      const c = (created.data && created.data.contact) || {};
      const warnings = (created.data && created.data.warnings) || [];
      console.log("LEAD_FELLO_PUSHED email=" + safe + " id=" + (c.contactId || "-") + " tags=" + body.tags.length + (warnings.length ? " warnings=" + warnings.join(",") : ""));
      return { ok: true, created: true, contactId: c.contactId || null };
    }
    const code = created.data && created.data.code;
    if (created.status === 400 && code === "DuplicateContact") {
      const existing = await felloGetContact(env, body.email);
      const contactId = existing.ok && existing.data && existing.data.contactId;
      if (!contactId) {
        console.error("LEAD_FELLO_FAILED duplicate but lookup failed status=" + existing.status + " email=" + safe);
        return { ok: false, duplicate: true };
      }
      const tagged = await felloFetch(env, "POST", "/contact/" + encodeURIComponent(contactId) + "/tags", { tags: body.tags });
      let propertyAdded = false;
      if (body.address) {
        const prop = await felloFetch(env, "POST", "/contact/" + encodeURIComponent(contactId) + "/property", { address: body.address });
        propertyAdded = prop.ok;
      }
      console.log("LEAD_FELLO_DUPLICATE email=" + safe + " id=" + contactId + " tags=" + (tagged.ok ? "ok" : tagged.status) + " property=" + (body.address ? (propertyAdded ? "added" : "existing") : "none"));
      return { ok: true, created: false, duplicate: true, contactId };
    }
    console.error("LEAD_FELLO_FAILED status=" + created.status + " code=" + (code || "-") + " msg=" + ((created.data && created.data.message) || "-") + " email=" + safe);
    return { ok: false, status: created.status, code };
  } catch (e) {
    console.error("LEAD_FELLO_THREW " + ((e && e.message) || e) + " email=" + safe);
    return { ok: false, error: String((e && e.message) || e) };
  }
}

// --- inbound webhook signature ----------------------------------------------

function b64ToBytes(b64) {
  const bin = atob(String(b64 || "").trim());
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function bytesToB64(bytes) {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}

export async function felloSignature(clientSecret, rawBody) {
  const key = await crypto.subtle.importKey("raw", b64ToBytes(clientSecret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(String(rawBody)));
  return bytesToB64(new Uint8Array(sig));
}

export async function verifyFelloSignature(clientSecret, rawBody, signatureHeader) {
  if (!clientSecret || !signatureHeader) return false;
  let expected;
  try { expected = await felloSignature(clientSecret, rawBody); } catch (e) { return false; }
  const a = new TextEncoder().encode(expected);
  const b = new TextEncoder().encode(String(signatureHeader).trim());
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

// --- engagement scoring (the dashboard readback) -----------------------------

const DAY_MS = 86400000;

function ts(v) {
  const t = Date.parse(String(v || ""));
  return Number.isFinite(t) ? t : 0;
}

// Reduce one Fello contact read into the shape the call list needs. "Hot" =
// a dashboard or email CTA click inside the window (default 7 days), the
// strongest intent signal Fello exposes. lastActivityAt is the newest of
// every engagement timestamp. The Fello auto tags (FELLO HIGH OWNER MATCH,
// FELLO TARGET HOMEOWNER ...) ride along as signals.
export function summarizeFelloContact(contact, nowMs, hotWindowDays) {
  const c = contact || {};
  const e = c.engagement || {};
  const now = nowMs || Date.now();
  const windowMs = (hotWindowDays || 7) * DAY_MS;
  const clicks = Math.max(ts(e.lastDashboardClickedDate), ts(e.lastEmailClickDate));
  const views = Math.max(ts(e.lastDashboardViewedDate), ts(e.lastEmailOpenDate));
  const lastActivity = Math.max(clicks, views, ts(e.lastFormSubmissionDate));
  const hot = clicks > 0 && now - clicks <= windowMs;
  const warm = !hot && views > 0 && now - views <= windowMs;
  const tags = Array.isArray(c.tags) ? c.tags : [];
  const signals = tags.filter((t) => /^FELLO /i.test(String(t)));
  const properties = Array.isArray(c.properties) ? c.properties.map((p) => {
    const a = (p && p.address) || {};
    return [a.aptOrUnitNumber, a.streetAddress].filter(Boolean).join(" ") + ", " + [a.city, a.state].filter(Boolean).join(", ") + (a.zip ? " " + a.zip : "");
  }) : [];
  return {
    contactId: c.contactId || null,
    email: c.email || null,
    name: c.name || null,
    phone: c.phone || null,
    emailStatus: c.emailStatus || null,
    leadScore: typeof c.leadScore === "number" ? c.leadScore : null,
    dashboardViews: e.numOfDashboardViews || 0,
    dashboardClicks: e.numOfDashboardClicks || 0,
    emailOpens: e.numOfEmailOpens || 0,
    emailClicks: e.numOfEmailClicks || 0,
    formSubmissions: e.numOfFormSubmissions || 0,
    lastClickAt: clicks ? new Date(clicks).toISOString() : null,
    lastActivityAt: lastActivity ? new Date(lastActivity).toISOString() : null,
    hot,
    warm,
    signals,
    properties,
    // rank: hot first, then warm, then newest activity, then score
    rank: (hot ? 2e15 : 0) + (warm ? 1e15 : 0) + lastActivity + (typeof c.leadScore === "number" ? c.leadScore : 0)
  };
}
