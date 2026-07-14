// Shared email engine for drozq.com. One place owns: the MailChannels send call
// (with DKIM signing once the key env vars exist), the branded HTML template
// every outbound email renders through, the subscriber enrollment used by
// /api/lead and /api/subscribe, and the sequence step sender used by the
// enrollment path and the cron tick. Endpoints under /functions/api/email/*
// are thin wrappers around this module.
//
// Env contract (Cloudflare Pages > Settings):
//   EMAIL_DB              D1 binding (database: drozq-email). All list state.
//   EMAIL_SECRET          shared secret: admin endpoint auth + unsubscribe/
//                         open/click HMAC tokens. One secret on purpose.
//   MAILCHANNELS_API_KEY  already set (lead alerts use it today).
//   EMAIL_FROM            optional, default "updates@drozq.com"
//   EMAIL_FROM_NAME       optional, default "Joshua Guerrero"
//   EMAIL_REPLY_TO        optional, default "josh@drozq.com"
//   EMAIL_POSTAL_ADDRESS  optional CAN-SPAM postal line for the footer.
//   DKIM_PRIVATE_KEY      optional, base64 DER RSA key. With DKIM_SELECTOR
//                         (default "mc1") turns on DKIM signing.
//   EMAIL_DRY_RUN         optional. "1" = log instead of calling MailChannels.
//   EMAIL_TEST_FAST       optional. "1" = sequence day offsets become seconds
//                         and the send window clamp is skipped (local testing).

const BASE_URL = "https://drozq.com";
const POSTHOG_TOKEN = "phc_Aa6GdWNbL9Kc9PhrnqR3Zq7Fc4zv2GxB2sPS59QamhyW";

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

export function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function b64urlEncode(s) {
  const bytes = new TextEncoder().encode(String(s));
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64urlDecode(s) {
  let b = String(s).replace(/-/g, "+").replace(/_/g, "/");
  while (b.length % 4) b += "=";
  const bin = atob(b);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

export async function hmacHex(secret, msg) {
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(String(secret)),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(String(msg)));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export function validEmail(s) {
  const e = String(s || "").trim();
  return e.length >= 6 && e.length <= 200 && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e);
}

export function firstNameOf(sub) {
  const f = (sub && (sub.first_name || sub.name)) || "";
  const tok = String(f).trim().split(/\s+/)[0] || "";
  if (!tok || /lead|subscriber|provided|website/i.test(tok)) return "";
  return tok.charAt(0).toUpperCase() + tok.slice(1);
}

export function fetchWithTimeout(url, options, ms) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  return fetch(url, Object.assign({}, options, { signal: ctrl.signal }))
    .finally(() => clearTimeout(t));
}

// Fire a server-side PostHog event. Best effort, never throws. distinct_id is
// the subscriber email so opens/clicks line up per person in PostHog.
export function phCapture(event, distinctId, props) {
  return fetchWithTimeout("https://us.i.posthog.com/capture/", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      api_key: POSTHOG_TOKEN,
      event,
      distinct_id: distinctId || "email-platform",
      properties: Object.assign({ $lib: "drozq-email-platform" }, props || {}),
      timestamp: new Date().toISOString()
    })
  }, 5000).catch(() => {});
}

// ---------------------------------------------------------------------------
// Send window: sequence sends land 9:30am to 7pm Pacific so drip emails read
// like a person sent them. Instant sends (step 0) skip this on purpose.
// ---------------------------------------------------------------------------

function laClock(ms) {
  const f = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles", hour12: false,
    hour: "2-digit", minute: "2-digit"
  });
  const p = Object.fromEntries(f.formatToParts(new Date(ms)).map((x) => [x.type, x.value]));
  return { h: Number(p.hour) % 24, min: Number(p.minute) };
}

export function windowedISO(baseMs, env) {
  if (env && env.EMAIL_TEST_FAST === "1") return new Date(baseMs).toISOString();
  let ms = baseMs;
  const { h, min } = laClock(ms);
  if (h < 9) {
    ms += (((9 - h) * 60) - min + 30) * 60000;
  } else if (h >= 19) {
    ms += (((24 - h + 9) * 60) - min + 30) * 60000;
  }
  ms += Math.floor(Math.random() * 40) * 60000; // up to 40min jitter, never robotic
  return new Date(ms).toISOString();
}

export function offsetMs(days, env) {
  if (env && env.EMAIL_TEST_FAST === "1") return days * 1000; // days become seconds
  return days * 86400000;
}

// ---------------------------------------------------------------------------
// Tracking + unsubscribe URLs (HMAC-bound to EMAIL_SECRET, so nobody can mint
// or replay them for other addresses)
// ---------------------------------------------------------------------------

export async function unsubscribeUrl(env, email) {
  const e = b64urlEncode(email);
  const t = await hmacHex(env.EMAIL_SECRET, "unsub:" + email);
  return BASE_URL + "/api/email/unsubscribe?e=" + e + "&t=" + t;
}

export async function openPixelUrl(env, logId) {
  const t = await hmacHex(env.EMAIL_SECRET, "open:" + logId);
  return BASE_URL + "/api/email/open?id=" + logId + "&t=" + t;
}

export async function clickUrl(env, logId, targetUrl) {
  const u = b64urlEncode(targetUrl);
  const t = await hmacHex(env.EMAIL_SECRET, "click:" + logId + ":" + u);
  return BASE_URL + "/api/email/click?id=" + logId + "&u=" + u + "&t=" + t;
}

// ---------------------------------------------------------------------------
// Copy helpers: API callers (CLI, broadcast) pass plain paragraphs with a tiny
// markdown subset (**bold**, [label](https://url)). Everything is escaped
// first, so no caller can inject markup.
// ---------------------------------------------------------------------------

export function paragraphsToHtml(paragraphs) {
  return (paragraphs || []).map((p) => {
    let s = escapeHtml(p);
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" class="dz-a" style="color:#d92228;font-weight:700;text-decoration:underline;">$1</a>');
    return '<p class="dz-p" style="margin:0 0 18px;font-size:16px;line-height:1.65;color:#2b2b2b;">' + s + "</p>";
  }).join("");
}

export function paragraphsToText(paragraphs) {
  return (paragraphs || []).map((p) =>
    String(p).replace(/\*\*([^*]+)\*\*/g, "$1").replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, "$1: $2")
  ).join("\n\n");
}

export function personalize(s, sub) {
  const first = firstNameOf(sub) || "there";
  const city = (sub && sub.city) || "Orange County";
  return String(s == null ? "" : s).replace(/\{first\}/g, first).replace(/\{city\}/g, city);
}

// ---------------------------------------------------------------------------
// The branded template. Same design system as the site: warm #efe9e1 backdrop,
// white card, #1a1816 headings, #2b2b2b body, #d92228 CTA. System font stack
// on purpose: it is what renders in Apple Mail and Gmail, and it is the reason
// Apple and Cloudflare emails look the way they do.
// ---------------------------------------------------------------------------

const FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";

export function renderEmail(opts) {
  const {
    subject = "",
    preheader = "",
    headline = "",
    bodyHtml = "",
    ctaLabel = "",
    ctaUrl = "",
    signature = true,
    unsubUrl = "",
    pixelUrl = "",
    postal = ""
  } = opts || {};

  const cta = (ctaLabel && ctaUrl) ? (
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:26px 0 6px;">' +
      '<tr><td style="border-radius:10px;background:#d92228;">' +
        '<a href="' + escapeHtml(ctaUrl) + '" target="_blank" ' +
           'style="display:inline-block;padding:14px 28px;font-family:' + FONT + ';font-size:16px;font-weight:700;' +
           'color:#ffffff;text-decoration:none;border-radius:10px;">' + escapeHtml(ctaLabel) + "</a>" +
      "</td></tr></table>"
  ) : "";

  const sig = signature ? (
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" class="dz-divider" style="margin-top:30px;border-top:1px solid #ece8e2;width:100%;">' +
      '<tr><td style="padding-top:22px;font-family:' + FONT + ';">' +
        '<p class="dz-h1" style="margin:0;font-size:16px;font-weight:800;color:#1a1816;">Joshua Guerrero</p>' +
        '<p class="dz-muted" style="margin:4px 0 0;font-size:13px;line-height:1.6;color:#757575;">Active Realty &middot; California DRE #02267255<br>' +
          '<a href="tel:9494385948" class="dz-p" style="color:#2b2b2b;text-decoration:none;font-weight:700;">(949) 438-5948</a>' +
          ' &nbsp;&middot;&nbsp; <a href="https://drozq.com" class="dz-a" style="color:#d92228;text-decoration:none;font-weight:700;">drozq.com</a></p>' +
      "</td></tr></table>"
  ) : "";

  const footerLinks = [
    unsubUrl ? '<a href="' + escapeHtml(unsubUrl) + '" class="dz-muted" style="color:#8a8378;text-decoration:underline;">Unsubscribe</a>' : "",
    '<a href="https://drozq.com/privacy/" class="dz-muted" style="color:#8a8378;text-decoration:underline;">Privacy</a>',
    '<a href="https://drozq.com/terms/" class="dz-muted" style="color:#8a8378;text-decoration:underline;">Terms</a>'
  ].filter(Boolean).join(" &nbsp;&middot;&nbsp; ");

  const postalLine = postal ? escapeHtml(postal) : "Active Realty &middot; 17875 Von Karman Ave Suite 150, Irvine, CA 92614";

  return "<!doctype html>" +
'<html lang="en"><head>' +
'<meta charset="utf-8">' +
'<meta name="viewport" content="width=device-width,initial-scale=1">' +
'<meta name="color-scheme" content="light dark">' +
'<meta name="supported-color-schemes" content="light dark">' +
"<title>" + escapeHtml(subject) + "</title>" +
"<style>" +
":root{color-scheme:light dark;supported-color-schemes:light dark;}" +
"body{margin:0;padding:0;background:#efe9e1;-webkit-text-size-adjust:100%;}" +
".dz-logo-dark{display:none;}" +
"@media only screen and (max-width:620px){.dz-card{border-radius:14px !important;}.dz-card-pad{padding:26px 22px 30px !important;}.dz-topbar{border-radius:13px 13px 0 0 !important;}.dz-h1{font-size:24px !important;line-height:1.3 !important;}.dz-wrap{padding:20px 12px !important;}}" +
// Dark theme: same token family as the site. Page #1a1816 (the dark-block
// token), card #2b2b2b, warm-white text #f2f0ef, taupe muted #beb8b0, light-red
// links #f7d3d4, slate dividers #3f4650. CTA stays #d92228 with white text.
"@media (prefers-color-scheme:dark){" +
  "body,.dz-bg{background:#1a1816 !important;}" +
  ".dz-card{background:#2b2b2b !important;border-color:#3f4650 !important;}" +
  ".dz-h1{color:#ffffff !important;}" +
  ".dz-p{color:#f2f0ef !important;}" +
  ".dz-a{color:#e04a4f !important;}" +
  ".dz-topbar,.dz-rule{background:#e04a4f !important;}" +
  ".dz-muted,.dz-muted a{color:#beb8b0 !important;}" +
  ".dz-divider{border-top-color:#3f4650 !important;}" +
  ".dz-logo-light{display:none !important;}" +
  ".dz-logo-dark{display:block !important;}" +
"}" +
"</style>" +
"</head>" +
'<body class="dz-bg" style="margin:0;padding:0;background:#efe9e1;">' +
'<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">' + escapeHtml(preheader) +
  "&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;</div>" +
'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="dz-bg" style="background:#efe9e1;">' +
'<tr><td align="center" class="dz-wrap" style="padding:36px 16px;">' +
  '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">' +

    '<tr><td style="padding:0 6px 18px;" align="left">' +
      '<a href="https://drozq.com" target="_blank" style="text-decoration:none;">' +
        '<img src="https://drozq.com/api/email/logo" width="170" height="24" alt="drozq.com" class="dz-logo-light" ' +
             'style="display:block;border:0;outline:none;font-family:' + FONT + ';font-size:16px;font-weight:800;color:#1a1816;">' +
        '<img src="https://drozq.com/api/email/logo?v=white" width="170" height="24" alt="drozq.com" class="dz-logo-dark" ' +
             'style="display:none;border:0;outline:none;font-family:' + FONT + ';font-size:16px;font-weight:800;color:#f2f0ef;">' +
      "</a>" +
    "</td></tr>" +

    '<tr><td class="dz-card" style="background:#ffffff;border:1px solid #e5e5e5;border-radius:16px;padding:0;" align="left">' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' +
        '<tr><td class="dz-topbar" style="height:4px;line-height:4px;font-size:2px;background:#d92228;border-radius:15px 15px 0 0;">&nbsp;</td></tr>' +
        '<tr><td class="dz-card-pad" style="padding:38px 44px 42px;font-family:' + FONT + ';" align="left">' +
          (headline
            ? '<h1 class="dz-h1" style="margin:0 0 14px;font-size:27px;line-height:1.28;letter-spacing:-0.4px;font-weight:800;color:#1a1816;">' + headline + "</h1>" +
              '<div class="dz-rule" style="width:44px;height:3px;background:#d92228;border-radius:2px;margin:0 0 20px;font-size:0;line-height:0;">&nbsp;</div>'
            : "") +
          bodyHtml +
          cta +
          sig +
        "</td></tr>" +
      "</table>" +
    "</td></tr>" +

    '<tr><td class="dz-muted" style="padding:26px 8px 8px;font-family:' + FONT + ';font-size:12px;line-height:1.7;color:#8a8378;" align="center">' +
      "Joshua Guerrero &middot; " + postalLine + "<br>" +
      footerLinks +
    "</td></tr>" +

  "</table>" +
"</td></tr></table>" +
(pixelUrl ? '<img src="' + escapeHtml(pixelUrl) + '" width="1" height="1" alt="" style="display:block;border:0;">' : "") +
"</body></html>";
}

// ---------------------------------------------------------------------------
// MailChannels send. Mirrors the proven /api/lead call, plus an HTML part,
// DKIM fields when configured, and RFC 8058 one-click unsubscribe headers.
// ---------------------------------------------------------------------------

export async function sendEmail(env, msg) {
  const { to, toName, subject, html, text, unsubUrl } = msg;
  const from = env.EMAIL_FROM || "updates@drozq.com";
  const fromName = env.EMAIL_FROM_NAME || "Joshua Guerrero";
  const replyTo = env.EMAIL_REPLY_TO || "josh@drozq.com";

  if (env.EMAIL_DRY_RUN === "1") {
    console.log("EMAIL_DRY_RUN to=" + to + " subject=" + subject);
    return { ok: true, status: 200, dryRun: true };
  }
  if (!env.MAILCHANNELS_API_KEY) {
    console.error("EMAIL_SEND_SKIPPED MailChannels key missing to=" + to);
    return { ok: false, status: 0, error: "mailchannels_key_missing" };
  }

  const personalization = { to: [{ email: to, name: toName || undefined }] };
  if (env.DKIM_PRIVATE_KEY) {
    personalization.dkim_domain = "drozq.com";
    personalization.dkim_selector = env.DKIM_SELECTOR || "mc1";
    personalization.dkim_private_key = env.DKIM_PRIVATE_KEY;
  }
  if (unsubUrl) {
    personalization.headers = {
      "List-Unsubscribe": "<" + unsubUrl + ">",
      "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
    };
  }

  const content = [];
  if (text) content.push({ type: "text/plain", value: text });
  if (html) content.push({ type: "text/html", value: html });

  try {
    const r = await fetchWithTimeout("https://api.mailchannels.net/tx/v1/send", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-Api-Key": env.MAILCHANNELS_API_KEY,
        "Accept": "application/json"
      },
      body: JSON.stringify({
        personalizations: [personalization],
        from: { email: from, name: fromName },
        reply_to: { email: replyTo, name: "Joshua Guerrero" },
        subject,
        content
      })
    }, 10000);
    if (!r.ok) {
      let body = "";
      try { body = await r.text(); } catch (e) {}
      console.error("EMAIL_SEND_FAILED status=" + r.status + " to=" + to + " body=" + body.slice(0, 500));
      return { ok: false, status: r.status, error: body.slice(0, 500) };
    }
    return { ok: true, status: r.status };
  } catch (e) {
    console.error("EMAIL_SEND_THREW to=" + to + " " + ((e && e.message) || e));
    return { ok: false, status: 0, error: String((e && e.message) || e) };
  }
}

// ---------------------------------------------------------------------------
// Subscriber enrollment + sequence sending
// ---------------------------------------------------------------------------

export function emailReady(env) {
  return Boolean(env.EMAIL_DB && env.EMAIL_SECRET);
}

// Insert if new. Never touches an existing row, so an unsubscribed address can
// never be re-enrolled by a form submit, and a mid-sequence subscriber is never
// reset by a duplicate lead. Returns { inserted, row }.
export async function upsertSubscriber(env, seed) {
  const email = String(seed.email || "").trim().toLowerCase();
  if (!validEmail(email)) return { inserted: false, row: null, reason: "invalid_email" };
  if (/@drozq\.com$/i.test(email)) return { inserted: false, row: null, reason: "internal" };

  const res = await env.EMAIL_DB.prepare(
    "INSERT INTO subscribers (email, first_name, name, source, intent, city, street, timeline, status, sequence_id, sequence_step, next_send_at, gclid, page_url) " +
    "VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 'active', ?9, 0, ?10, ?11, ?12) " +
    "ON CONFLICT(email) DO NOTHING"
  ).bind(
    email,
    seed.first_name || null,
    seed.name || null,
    seed.source || "newsletter",
    seed.intent || null,
    seed.city || null,
    seed.street || null,
    seed.timeline || null,
    seed.sequence_id,
    seed.next_send_at || null,
    seed.gclid || null,
    seed.page_url || null
  ).run();

  const inserted = Boolean(res.meta && res.meta.changes > 0);
  const row = await env.EMAIL_DB.prepare("SELECT * FROM subscribers WHERE email = ?1").bind(email).first();
  return { inserted, row };
}

// Render + send an arbitrary payload (manual 1:1 update or broadcast) to one
// recipient, personalized, tracked, and templated. The caller owns email_log
// bookkeeping. payload: { subject, preheader, headline, paragraphs, ctaLabel,
// ctaUrl, includeUnsub (default true), signature (default true) }.
export async function sendPayloadTo(env, sub, logId, payload) {
  const first = firstNameOf(sub);
  const subject = personalize(payload.subject, sub);
  const includeUnsub = payload.includeUnsub !== false;

  const unsub = includeUnsub ? await unsubscribeUrl(env, sub.email) : "";
  const pixel = await openPixelUrl(env, logId);
  let ctaUrl = "";
  if (payload.ctaUrl) ctaUrl = await clickUrl(env, logId, personalize(payload.ctaUrl, sub));

  const paragraphs = (payload.paragraphs || []).map((p) => personalize(p, sub));
  const html = renderEmail({
    subject,
    preheader: personalize(payload.preheader || "", sub),
    headline: escapeHtml(personalize(payload.headline || "", sub)),
    bodyHtml: paragraphsToHtml(paragraphs),
    ctaLabel: payload.ctaLabel || "",
    ctaUrl,
    signature: payload.signature !== false,
    unsubUrl: unsub,
    pixelUrl: pixel,
    postal: env.EMAIL_POSTAL_ADDRESS || ""
  });
  const text = paragraphsToText(paragraphs) +
    (payload.ctaUrl ? "\n\n" + (payload.ctaLabel || "Link") + ": " + personalize(payload.ctaUrl, sub) : "") +
    "\n\nJoshua Guerrero\nActive Realty, California DRE #02267255\n(949) 438-5948" +
    (unsub ? "\n\nUnsubscribe: " + unsub : "");

  return sendEmail(env, { to: sub.email, toName: first || sub.name || "", subject, html, text, unsubUrl: unsub });
}

// Render + send one sequence step to a subscriber, with open/click tracking and
// the unsubscribe footer, logging the send in email_log. Never throws.
export async function sendSequenceStep(env, sub, step) {
  try {
    const first = firstNameOf(sub);
    const subject = personalize(step.subject(sub), sub);
    const log = await env.EMAIL_DB.prepare(
      "INSERT INTO email_log (subscriber_id, email, kind, ref, subject, status) VALUES (?1, ?2, 'sequence', ?3, ?4, 'sending') RETURNING id"
    ).bind(sub.id, sub.email, step.id, subject).first();
    const logId = log.id;

    const r = step.render(sub);
    const [unsub, pixel] = await Promise.all([unsubscribeUrl(env, sub.email), openPixelUrl(env, logId)]);
    let ctaUrl = "";
    if (r.ctaUrl) ctaUrl = await clickUrl(env, logId, personalize(r.ctaUrl, sub));

    const html = renderEmail({
      subject,
      preheader: personalize(r.preheader || "", sub),
      headline: escapeHtml(personalize(r.headline || "", sub)),
      bodyHtml: paragraphsToHtml(r.paragraphs.map((p) => personalize(p, sub))),
      ctaLabel: r.ctaLabel || "",
      ctaUrl,
      unsubUrl: unsub,
      pixelUrl: pixel,
      postal: env.EMAIL_POSTAL_ADDRESS || ""
    });
    const text = paragraphsToText(r.paragraphs.map((p) => personalize(p, sub))) +
      (r.ctaUrl ? "\n\n" + (r.ctaLabel || "Link") + ": " + personalize(r.ctaUrl, sub) : "") +
      "\n\nJoshua Guerrero\nActive Realty, California DRE #02267255\n(949) 438-5948\n\nUnsubscribe: " + unsub;

    const sent = await sendEmail(env, { to: sub.email, toName: first || sub.name || "", subject, html, text, unsubUrl: unsub });

    await env.EMAIL_DB.prepare(
      "UPDATE email_log SET status = ?1, error = ?2, sent_at = CASE WHEN ?1 = 'sent' THEN datetime('now') ELSE NULL END WHERE id = ?3"
    ).bind(sent.ok ? "sent" : "failed", sent.ok ? null : String(sent.error || sent.status), logId).run();

    phCapture(sent.ok ? "email_sent" : "email_send_failed", sub.email, {
      kind: "sequence", ref: step.id, subject, sequence_id: sub.sequence_id
    });
    return sent.ok;
  } catch (e) {
    console.error("EMAIL_SEQ_STEP_THREW email=" + (sub && sub.email) + " step=" + (step && step.id) + " " + ((e && e.message) || e));
    return false;
  }
}
