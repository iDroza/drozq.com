const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8" }
  });

// Normalize a US/Canada phone to a clean national + E.164 form. Defense in depth
// behind the client formatter: drops a leaked "+1" country code (an 11-digit
// string starting with 1 — NANP area codes never start with 1) so the number is
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

// Deliver an accepted lead to every configured channel, best effort. CRITICAL
// DESIGN POINT: acceptance (the 200 the visitor sees) is fully DECOUPLED from
// delivery. This function runs in context.waitUntil AFTER the response is sent,
// so a slow or misconfigured delivery channel can never surface as "something
// went wrong" in the funnel again. Each channel is independent; a failure is
// logged, never thrown. If NO channel is configured, the full lead is logged so
// it is still recoverable from Cloudflare's function logs — a lead is never
// silently dropped.
async function deliverLead(env, lead) {
  const { emailContent, zapierPayload, logLine } = lead;
  const tasks = [];
  let channels = 0;

  const TO_EMAIL = env.TO_EMAIL;
  const FROM_EMAIL = env.FROM_EMAIL;
  const MAILCHANNELS_API_KEY = env.MAILCHANNELS_API_KEY;

  if (TO_EMAIL && FROM_EMAIL && MAILCHANNELS_API_KEY) {
    channels++;
    tasks.push(
      fetchWithTimeout("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "X-Api-Key": MAILCHANNELS_API_KEY,
          "Accept": "application/json"
        },
        body: JSON.stringify({
          personalizations: [{ to: [{ email: TO_EMAIL }] }],
          from: { email: FROM_EMAIL, name: "drozq.com Lead Form" },
          reply_to: { email: emailContent.replyToEmail, name: emailContent.replyToName },
          subject: emailContent.subject,
          content: [{ type: "text/plain", value: emailContent.body }]
        })
      }, 8000).then(async (r) => {
        if (!r.ok) {
          let body = "";
          try { body = await r.text(); } catch (e) {}
          console.error("LEAD_EMAIL_FAILED MailChannels status=" + r.status + " body=" + body + " | " + logLine);
        }
      }).catch((e) => {
        console.error("LEAD_EMAIL_THREW MailChannels " + ((e && e.message) || e) + " | " + logLine);
      })
    );
  } else {
    console.error("LEAD_EMAIL_SKIPPED MailChannels not configured (need TO_EMAIL + FROM_EMAIL + MAILCHANNELS_API_KEY) | " + logLine);
  }

  if (env.ZAPIER_WEBHOOK_URL) {
    channels++;
    tasks.push(
      fetchWithTimeout(env.ZAPIER_WEBHOOK_URL, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(zapierPayload)
      }, 8000).then((r) => {
        if (!r.ok) console.error("LEAD_ZAPIER_FAILED status=" + r.status + " | " + logLine);
      }).catch((e) => {
        console.error("LEAD_ZAPIER_THREW " + ((e && e.message) || e) + " | " + logLine);
      })
    );
  }

  if (channels === 0) {
    // No delivery channel at all: log the full lead so Joshua can recover it
    // from the Cloudflare Pages function logs. The visitor still got a 200.
    console.error("LEAD_NOT_DELIVERED no channel configured; recoverable lead below | " + logLine);
  }

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
    const gclid = String(formData.get("gclid") || "").trim();

    // 4) Validation. Email + phone + consent are the hard requirements: they are
    // what makes a lead contactable and compliant. Name is captured when present
    // but NEVER blocks a lead — a client-side gap in name capture must not cost a
    // conversion, so a missing name falls back to a placeholder instead of a 400
    // (which the funnel surfaces to the visitor as "something went wrong"). Same
    // for intent: default it rather than reject.
    if (!email || !phone) {
      return json({ ok: false, error: "Missing required fields" }, 400);
    }
    if (consent !== "yes") {
      return json({ ok: false, error: "Consent required" }, 400);
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
${addressBlock || fullAddress || "—"}
Full (Google): ${fullAddress || "—"}
Lat/Lng: ${lat || "—"}, ${lng || "—"}

INQUIRY
Type: ${safeIntent}
Timeline: ${timeline || "—"}
Referral Source: ${referralSource || "—"}

NOTES
${message || "—"}

META
Source: ${sourcePage || "—"}
Page URL: ${pageUrl || "—"}
Submitted: ${submittedAt || "—"}
GCLID: ${gclid || "—"}
Endpoint: ${url.pathname}
IP: ${ip || "—"}
User-Agent: ${ua || "—"}
Consent: ${consent}
`;

    // 9) Build channel payloads + a compact recoverable log line
    const emailContent = {
      subject: `🏠 New Lead (${safeIntent}): ${safeName} — ${city || "Unknown City"}, ${state || "CA"}`,
      body: emailBody,
      replyToEmail: email,
      replyToName: safeName
    };

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
      gclid,
      message,
      source_page: sourcePage,
      consent,
      ip,
      user_agent: ua
    };

    const logLine = JSON.stringify({
      name: safeName, email, phone, intent: safeIntent,
      city, state, source: sourcePage, gclid, submitted_at: submittedAt
    });

    // 10) Accept now, deliver after. The visitor's 200 does not depend on email
    // or Zapier succeeding, so a delivery outage can never break the funnel.
    context.waitUntil(deliverLead(env, { emailContent, zapierPayload, logLine }));

    return json({ ok: true }, 200);
  } catch (err) {
    console.error("LEAD_HANDLER_ERROR " + ((err && err.stack) || err));
    return json({ ok: false, error: "Server error" }, 500);
  }
}
