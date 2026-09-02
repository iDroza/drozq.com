import { enrollSubscriber } from "../_lib/enroll.js";
import { renderLeadAlert, escapeHtml, sendEmail, validEmail } from "../_lib/email.js";
import { maskEmail, maskPhone, maskAddress } from "../_lib/redact.js";
import { normalizeSubmissionId, rememberSubmission, pruneSubmissions } from "../_lib/idempotency.js";
import { renderValuationReport, reportInputFromApiResponse } from "../_lib/valuation_email.js";

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8" }
  });

// Normalize a US/Canada phone to a clean national + E.164 form. Defense in depth
// behind the client formatter: drops a leaked "+1" country code (an 11-digit
// string starting with 1, NANP area codes never start with 1) so the number is
// never truncated or mis-bucketed, and stamps "+1" on every real lead's phone
// (the email Joshua reads + the Zapier/CRM payload), per the "capture the +1 on
// every lead" rule. Anything that isn't a recognizable 10-digit NANP number
// (e.g. the "0000000000" placeholder used by One Tap + valuation-view leads)
// passes through untouched, so this never rejects or mangles a lead.
function normalizePhone(raw) {
  const original = String(raw == null ? "" : raw).trim();
  let digits = original.replace(/\D/g, "");
  if (digits.length === 11 && digits.charAt(0) === "1") digits = digits.slice(1);
  if (digits.length === 10 && /^[2-9]\d{2}[2-9]\d{6}$/.test(digits)) {
    return {
      e164: "+1" + digits,
      pretty: "+1 (" + digits.slice(0, 3) + ") " + digits.slice(3, 6) + "-" + digits.slice(6),
      valid: true
    };
  }
  return { e164: original, pretty: original, valid: false };
}

// fetch() with a hard timeout. A degraded upstream (e.g. MailChannels after the
// free tier ended) must never hang the worker. This runs inside waitUntil, after
// the visitor already has their 200, so it can never delay or fail the response.
async function fetchWithTimeout(url, options, ms) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, Object.assign({}, options, { signal: ctrl.signal }));
  } finally {
    clearTimeout(t);
  }
}

// The instant valuation report for sell-side funnel leads (the other half of
// "both land in your inbox"). Compute-only internal call: the x-drozq-internal
// header makes /api/valuation skip re-saving the lead. Runs inside waitUntil;
// every failure logs and dies quietly.
async function sendFunnelReport(env, seed) {
  const resp = await fetchWithTimeout(seed.origin + "/api/valuation", {
    method: "POST",
    headers: { "content-type": "application/json", "x-drozq-internal": env.EMAIL_SECRET },
    body: JSON.stringify({
      address: seed.address,
      lat: seed.lat || undefined,
      lng: seed.lng || undefined,
      email: seed.email,
      phone: seed.phone,
      consent: "yes",
      name: seed.name
    })
  }, 25000);
  if (!resp.ok) {
    console.error("VALUATION_REPORT_FETCH_FAILED status=" + resp.status + " addr=" + maskAddress(seed.address));
    return;
  }
  const data = await resp.json();
  if (!data || !data.ok) {
    console.log("VALUATION_REPORT_NO_DATA addr=" + maskAddress(seed.address));
    return;
  }
  const report = renderValuationReport(reportInputFromApiResponse(data));
  const sent = await sendEmail(env, { to: seed.email, toName: seed.name || "", subject: report.subject, html: report.html, text: report.text, unsubUrl: "" });
  if (sent && sent.ok) console.log("VALUATION_REPORT_SENT to=" + maskEmail(seed.email) + " addr=" + maskAddress(seed.address));
  else console.error("VALUATION_REPORT_FAILED to=" + maskEmail(seed.email) + " err=" + (sent && (sent.error || sent.status)));
}

// Deliver an accepted lead to every configured channel, best effort. CRITICAL
// DESIGN POINT: acceptance (the 200 the visitor sees) is fully DECOUPLED from
// delivery. This function runs in context.waitUntil AFTER the response is sent,
// so a slow or misconfigured delivery channel can never surface as "something
// went wrong" in the funnel again. Each channel is independent; a failure is
// logged, never thrown. If NO channel is configured, the full lead is logged so
// it is still recoverable from Cloudflare's function logs, a lead is never
// silently dropped.
async function deliverLead(env, lead) {
  // logLine is the FULL lead (recoverable); safeLine is the redacted shape
  // (masked email, last four of the phone, no name). Only LEAD_NOT_DELIVERED,
  // the no-channel recovery path, ever logs the full line.
  const { emailContent, zapierPayload, fubEvent, logLine, safeLine } = lead;
  const tasks = [];
  let channels = 0;

  const TO_EMAIL = env.TO_EMAIL;
  const FROM_EMAIL = env.FROM_EMAIL;
  const MAILCHANNELS_API_KEY = env.MAILCHANNELS_API_KEY;

  if (TO_EMAIL && FROM_EMAIL && MAILCHANNELS_API_KEY) {
    channels++;
    // DKIM-sign the alert when the platform key exists (same domain key as
    // updates@); the HTML part is the branded v2.1 template, the plaintext
    // part is unchanged so alerts stay grep-able and forwardable.
    const alertPersonalization = { to: [{ email: TO_EMAIL }] };
    if (env.DKIM_PRIVATE_KEY) {
      alertPersonalization.dkim_domain = "drozq.com";
      alertPersonalization.dkim_selector = env.DKIM_SELECTOR || "mc1";
      alertPersonalization.dkim_private_key = env.DKIM_PRIVATE_KEY;
    }
    const alertContent = [{ type: "text/plain", value: emailContent.body }];
    if (emailContent.html) alertContent.push({ type: "text/html", value: emailContent.html });
    tasks.push(
      fetchWithTimeout("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "X-Api-Key": MAILCHANNELS_API_KEY,
          "Accept": "application/json"
        },
        body: JSON.stringify({
          personalizations: [alertPersonalization],
          from: { email: FROM_EMAIL, name: "drozq.com Lead Form" },
          reply_to: { email: emailContent.replyToEmail, name: emailContent.replyToName },
          subject: emailContent.subject,
          content: alertContent
        })
      }, 8000).then(async (r) => {
        if (!r.ok) {
          let body = "";
          try { body = await r.text(); } catch (e) {}
          console.error("LEAD_EMAIL_FAILED MailChannels status=" + r.status + " body=" + body + " | " + safeLine);
        }
      }).catch((e) => {
        console.error("LEAD_EMAIL_THREW MailChannels " + ((e && e.message) || e) + " | " + safeLine);
      })
    );
  } else {
    console.error("LEAD_EMAIL_SKIPPED MailChannels not configured (need TO_EMAIL + FROM_EMAIL + MAILCHANNELS_API_KEY) | " + safeLine);
  }

  if (env.ZAPIER_WEBHOOK_URL) {
    channels++;
    tasks.push(
      fetchWithTimeout(env.ZAPIER_WEBHOOK_URL, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(zapierPayload)
      }, 8000).then((r) => {
        if (!r.ok) console.error("LEAD_ZAPIER_FAILED status=" + r.status + " | " + safeLine);
      }).catch((e) => {
        console.error("LEAD_ZAPIER_THREW " + ((e && e.message) || e) + " | " + safeLine);
      })
    );
  }

  // FollowUpBoss CRM (best effort, optional). Gated on FOLLOWUPBOSS_API_KEY so the
  // site behaves exactly as before until the key is set in Cloudflare. fubEvent is
  // null for placeholder soft-saves (e.g. "Home Valuation View") so junk contacts
  // never reach the CRM. Uses the FUB Events API: it creates-or-merges the person
  // by email and logs a lead event that can trigger FUB action plans / lead routing.
  // The FollowUpBoss Widget Tracker pixel already on the site then matches on-site
  // activity to this person's record.
  if (env.FOLLOWUPBOSS_API_KEY && fubEvent) {
    channels++;
    tasks.push(
      fetchWithTimeout("https://api.followupboss.com/v1/events", {
        method: "POST",
        headers: {
          "Authorization": "Basic " + btoa(env.FOLLOWUPBOSS_API_KEY + ":"),
          "Content-Type": "application/json",
          "Accept": "application/json",
          "X-System": "Drozq.com"
        },
        body: JSON.stringify(fubEvent)
      }, 8000).then(async (r) => {
        if (!r.ok) {
          let body = "";
          try { body = await r.text(); } catch (e) {}
          console.error("LEAD_FUB_FAILED status=" + r.status + " body=" + body + " | " + safeLine);
        }
      }).catch((e) => {
        console.error("LEAD_FUB_THREW " + ((e && e.message) || e) + " | " + safeLine);
      })
    );
  }

  if (channels === 0) {
    // No delivery channel at all: log the full lead so Joshua can recover it
    // from the Cloudflare Pages function logs. The visitor still got a 200.
    console.error("LEAD_NOT_DELIVERED no channel configured; recoverable lead below | " + logLine);
  }

  // Instant valuation report to the lead. Not a delivery channel for the
  // alert (never counts toward the channels gauge); requires EMAIL_SECRET
  // for the internal compute call and MailChannels for the send.
  if (lead.reportSeed && env.EMAIL_SECRET) {
    tasks.push(
      sendFunnelReport(env, lead.reportSeed).catch((e) => {
        console.error("VALUATION_REPORT_THREW " + ((e && e.message) || e) + " | " + safeLine);
      })
    );
  }

  // Email platform enrollment (best effort, additive, NOT a delivery channel:
  // it never affects the channels gauge above). Gated on the EMAIL_DB D1
  // binding + EMAIL_SECRET, so behavior is byte-identical until those exist.
  // New addresses get sequence step 0 instantly; existing or unsubscribed
  // addresses are never touched. See functions/_lib/enroll.js.
  if (env.EMAIL_DB && env.EMAIL_SECRET && lead.subscriberSeed) {
    tasks.push(
      enrollSubscriber(env, lead.subscriberSeed).catch((e) => {
        console.error("LEAD_ENROLL_THREW " + ((e && e.message) || e) + " | " + safeLine);
      })
    );
  }

  // Fello: leads are NEVER pushed from here. Joshua's order, 2026-09-02
  // ("do not submit leads to fello"). functions/_lib/fello.js keeps
  // pushLeadToFello for the CLI only; nothing in the request path calls it.

  await Promise.allSettled(tasks);
}

export async function onRequestPost(context) {
  try {
    const { request, env } = context;

    // 1) Only accept HTML form submits
    const contentType = request.headers.get("Content-Type") || "";
    const isForm =
      contentType.includes("application/x-www-form-urlencoded") ||
      contentType.includes("multipart/form-data");

    if (!isForm) {
      return json({ ok: false, error: "Unsupported content type" }, 415);
    }

    const formData = await request.formData();

    // 2) Honeypot check
    const honey = formData.get("company_website");
    if (honey && String(honey).trim() !== "") {
      return json({ ok: true }, 200);
    }

    // 3) Extract fields
    const firstName = String(formData.get("first_name") || "").trim();
    const lastName = String(formData.get("last_name") || "").trim();
    const name = (firstName + " " + lastName).trim() || String(formData.get("name") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const phoneRaw = String(formData.get("phone") || "").trim();
    const phoneNorm = normalizePhone(phoneRaw);
    // pretty carries the +1 for valid numbers; falls back to the raw value for
    // placeholders (One Tap / valuation-view) so nothing is ever dropped.
    const phone = phoneNorm.pretty;

    const intent = String(formData.get("intent") || "").trim();
    const message = String(formData.get("message") || "").trim();

    // Address fields
    const streetAddress = String(formData.get("street_address") || "").trim();
    const addressLine2 = String(formData.get("address_line_2") || "").trim();
    const city = String(formData.get("city") || "").trim();
    const state = String(formData.get("state") || "").trim();
    const zip = String(formData.get("zip") || "").trim();
    const fullAddress = String(formData.get("full_address") || "").trim();
    const lat = String(formData.get("lat") || "").trim();
    const lng = String(formData.get("lng") || "").trim();

    const referralSource = String(formData.get("referral_source") || "").trim();
    const sourcePage = String(formData.get("source_page") || formData.get("source") || "").trim();
    const consent = String(formData.get("consent") || "").trim();
    const timeline = String(formData.get("timeline") || "").trim();
    const buyLocation = String(formData.get("buy_location") || "").trim();
    const buyTimeline = String(formData.get("buy_timeline") || "").trim();
    const buyProcess = String(formData.get("buy_process") || "").trim();
    const gclid = String(formData.get("gclid") || "").trim();

    // 4) Validation. Email + phone + consent are the hard requirements: they are
    // what makes a lead contactable and compliant. Name is captured when present
    // but NEVER blocks a lead, a client-side gap in name capture must not cost a
    // conversion, so a missing name falls back to a placeholder instead of a 400
    // (which the funnel surfaces to the visitor as "something went wrong"). Same
    // for intent: default it rather than reject.
    if (!email || !phone) {
      return json({ ok: false, error: "Missing required fields" }, 400);
    }
    if (consent !== "yes") {
      return json({ ok: false, error: "Consent required" }, 400);
    }
    // Email must at least be shaped like one (the drip, the CRM merge, and the
    // report delivery all key on it). Phone stays lenient on purpose: the
    // "0000000000" placeholder from One Tap must keep passing.
    if (!validEmail(email)) {
      return json({ ok: false, error: "invalid_email" }, 400);
    }
    const safeName = name || "Website Lead (name not provided)";
    const safeIntent = intent || "Website Lead";

    // 5) Length guards
    if (
      safeName.length > 200 ||
      email.length > 200 ||
      phone.length > 50 ||
      safeIntent.length > 80 ||
      sourcePage.length > 100 ||
      message.length > 5000 ||
      streetAddress.length > 300 ||
      fullAddress.length > 500
    ) {
      return json({ ok: false, error: "Payload too large" }, 413);
    }

    // 6) Metadata
    const ip =
      request.headers.get("cf-connecting-ip") ||
      request.headers.get("x-forwarded-for") ||
      "";
    const ua = request.headers.get("user-agent") || "";
    const url = new URL(request.url);
    const pageUrl = String(formData.get("page_url") || "");
    const submittedAt = String(formData.get("submitted_at") || "");

    // 7) Compose address block
    const addressBlock = [
      streetAddress,
      addressLine2,
      [city, state, zip].filter(Boolean).join(", ")
    ].filter(Boolean).join("\n");

    // 8) Compose email
    const emailBody =
`New lead from drozq.com

IDENTITY
Name: ${safeName}
Email: ${email}
Phone: ${phone}

ADDRESS
${addressBlock || fullAddress || "-"}
Full (Google): ${fullAddress || "-"}
Lat/Lng: ${lat || "-"}, ${lng || "-"}

INQUIRY
Type: ${safeIntent}
Timeline: ${timeline || "-"}
Buy Location: ${buyLocation || "-"}
Buy Timeline: ${buyTimeline || "-"}
Buy Process: ${buyProcess || "-"}
Referral Source: ${referralSource || "-"}

NOTES
${message || "-"}

META
Source: ${sourcePage || "-"}
Page URL: ${pageUrl || "-"}
Submitted: ${submittedAt || "-"}
GCLID: ${gclid || "-"}
Endpoint: ${url.pathname}
IP: ${ip || "-"}
User-Agent: ${ua || "-"}
Consent: ${consent}
`;

    // 9) Build channel payloads + a compact recoverable log line
    const emailContent = {
      subject: `🏠 New Lead (${safeIntent}): ${safeName} · ${city || "Unknown City"}, ${state || "CA"}`,
      body: emailBody,
      replyToEmail: email,
      replyToName: safeName
    };

    // Branded HTML part for the alert (v2.1 template, 2026-07-13). The
    // plaintext body above remains the text/plain part, so alerts stay
    // grep-able and forwardable; this only changes what the inbox displays.
    emailContent.html = renderLeadAlert({
      subject: emailContent.subject,
      name: safeName,
      firstName: firstName || (name ? name.split(/\s+/)[0] : ""),
      intent: safeIntent,
      city,
      email,
      phone,
      phoneValid: phoneNorm.valid,
      phoneE164: phoneNorm.e164,
      addressHtml: escapeHtml(addressBlock || fullAddress || "-").replace(/\n/g, "<br>"),
      timeline,
      referral: referralSource,
      message,
      sourcePage,
      pageUrl,
      gclid,
      ip,
      consent,
      submittedAt
    });

    const zapierPayload = {
      first_name: firstName,
      last_name: lastName,
      name: safeName,
      email,
      phone,
      phone_e164: phoneNorm.e164,
      intent: safeIntent,
      street_address: streetAddress,
      address_line_2: addressLine2,
      city,
      state,
      zip,
      full_address: fullAddress,
      lat,
      lng,
      referral_source: referralSource,
      timeline,
      buy_location: buyLocation,
      buy_timeline: buyTimeline,
      buy_process: buyProcess,
      gclid,
      message,
      source_page: sourcePage,
      consent,
      ip,
      user_agent: ua
    };

    // FollowUpBoss CRM event payload. Built here where every field is in scope; sent
    // (best effort) from deliverLead only when FOLLOWUPBOSS_API_KEY is set. Skipped
    // for the valuation-view soft-save (placeholder identity) so the CRM stays clean.
    const sellerIntent = /valuation|seller|sell|sale/i.test(safeIntent);
    const buyerIntent = /purchase|buy/i.test(safeIntent);
    const fubType = sellerIntent ? "Seller Inquiry" : (buyerIntent ? "Property Inquiry" : "Registration");
    const fubTags = ["Drozq Website"];
    if (sellerIntent) fubTags.push("Seller");
    if (buyerIntent) fubTags.push("Buyer");
    if (safeIntent === "Google One Tap Lead") fubTags.push("Google One Tap");

    const nameTokens = name ? name.split(/\s+/) : [];
    const fubPerson = {
      firstName: firstName || nameTokens[0] || "Drozq",
      lastName: lastName || (nameTokens.length > 1 ? nameTokens.slice(1).join(" ") : (name ? "" : "Website Lead")),
      emails: [{ value: email }],
      tags: fubTags,
      source: "Drozq.com"
    };
    if (phoneNorm.valid) fubPerson.phones = [{ value: phoneNorm.pretty }];
    if (streetAddress || city || state || zip) {
      fubPerson.addresses = [{
        type: "home",
        street: streetAddress || fullAddress || "",
        city: city || "",
        state: state || "",
        code: zip || ""
      }];
    }
    const fubMessage =
      "Lead via drozq.com (" + safeIntent + ")." +
      (timeline ? " Timeline: " + timeline + "." : "") +
      (fullAddress ? " Address: " + fullAddress + "." : "") +
      (referralSource ? " Referral: " + referralSource + "." : "") +
      (message ? " Notes: " + message + "." : "") +
      (sourcePage ? " Page: " + sourcePage + "." : "") +
      (gclid ? " gclid: " + gclid : "");
    const fubEvent = (safeIntent === "Home Valuation View")
      ? null
      : {
          source: "Drozq.com",
          system: "Drozq.com",
          type: fubType,
          message: fubMessage,
          person: fubPerson
        };

    const logLine = JSON.stringify({
      name: safeName, email, phone, intent: safeIntent,
      city, state, source: sourcePage, gclid, submitted_at: submittedAt
    });
    // Redacted twin for every routine log line (see deliverLead).
    const safeLine = JSON.stringify({
      email: maskEmail(email), phone: maskPhone(phone), intent: safeIntent,
      city, state, source: sourcePage, gclid, submitted_at: submittedAt
    });

    // Email-platform enrollment seed. Field Notes subscribers are newsletter
    // members (welcome email only, per the /field-notes/ page promise); every
    // other intent enters the lead-response sequence. Delivered best-effort in
    // deliverLead, only when the email platform env is configured.
    const subscriberSeed = {
      email,
      first_name: firstName || nameTokens[0] || null,
      name: safeName,
      intent: safeIntent,
      city: city || null,
      street: streetAddress || null,
      timeline: timeline || null,
      source: safeIntent === "Field Notes Subscribe" ? "newsletter" : "lead",
      gclid: gclid || null,
      page_url: pageUrl || sourcePage || null
    };

    // Instant-report delivery: sell-side funnel leads with a real address get
    // their valuation report emailed the moment they submit ("both land in
    // your inbox"). /value/ leads are excluded here because /api/valuation
    // already emails them directly (intent "Home Valuation Lead").
    const wantsReport = (safeIntent === "Home Valuation" || safeIntent === "Home Sale + Purchase") && !!fullAddress && !!email;
    const reportSeed = wantsReport ? {
      origin: url.origin,
      address: fullAddress,
      lat: lat || null,
      lng: lng || null,
      email: email,
      phone: phoneRaw,
      name: safeName
    } : null;

    // Backstop: the placeholder "Home Valuation View" soft-save was retired (the
    // /value/ page no longer creates anonymous leads). If a stale cached page
    // still posts it, accept the request but DELIVER NOTHING, so Joshua never
    // gets an empty-lead notification. Only real, contact-bearing submissions
    // are delivered.
    if (safeIntent === "Home Valuation View") {
      console.log("LEAD_SOFT_SKIPPED " + safeLine);
      return json({ ok: true }, 200);
    }

    // 9b) Idempotency. The funnel stamps every submit with a submission_id; a
    // retry of an already-accepted id inside 15 minutes is acknowledged (so the
    // client still redirects to /thank-you/) but delivers nothing: one alert,
    // one CRM event, one enrollment per real submit. A dedupe-store failure
    // resolves to "not a duplicate": the store can never cost a lead.
    const submissionId = normalizeSubmissionId(formData.get("submission_id"));
    if (submissionId) {
      const seen = await rememberSubmission(env, submissionId, 15 * 60);
      if (seen.duplicate) {
        console.log("LEAD_DUPLICATE_SKIPPED id=" + submissionId + " " + safeLine);
        return json({ ok: true, duplicate: true }, 200);
      }
      if (Math.random() < 0.02) context.waitUntil(pruneSubmissions(env, 86400));
    }

    // 10) Accept now, deliver after. The visitor's 200 does not depend on email
    // or Zapier succeeding, so a delivery outage can never break the funnel.
    context.waitUntil(deliverLead(env, { emailContent, zapierPayload, fubEvent, logLine, safeLine, subscriberSeed, reportSeed }));

    return json({ ok: true }, 200);
  } catch (err) {
    console.error("LEAD_HANDLER_ERROR " + ((err && err.stack) || err));
    return json({ ok: false, error: "Server error" }, 500);
  }
}
