// One-click unsubscribe. Links carry ?e=<b64url email>&t=<HMAC(email)>, so a
// token only works for its own address. GET renders a small branded
// confirmation page (and unsubscribes); POST is the RFC 8058 one-click path
// mail clients call from the List-Unsubscribe header. Unsubscribing also
// cancels any queued broadcast rows for the address.

import { b64urlDecode, hmacHex, phCapture } from "../../_lib/email.js";

async function resolveEmail(context) {
  const { request, env } = context;
  if (!env.EMAIL_SECRET) return null;
  const url = new URL(request.url);
  const e = url.searchParams.get("e") || "";
  const t = url.searchParams.get("t") || "";
  if (!e || !t) return null;
  let email = "";
  try { email = b64urlDecode(e); } catch (err) { return null; }
  const expect = await hmacHex(env.EMAIL_SECRET, "unsub:" + email);
  return t === expect ? email : null;
}

async function unsubscribe(context, email) {
  const env = context.env;
  if (!env.EMAIL_DB) return;
  await env.EMAIL_DB.prepare(
    "UPDATE subscribers SET status = 'unsubscribed', next_send_at = NULL, updated_at = datetime('now') WHERE email = ?1"
  ).bind(email).run();
  await env.EMAIL_DB.prepare(
    "UPDATE email_log SET status = 'cancelled' WHERE email = ?1 AND status = 'queued'"
  ).bind(email).run();
  // waitUntil: the confirmation page returns right after this call.
  context.waitUntil(phCapture("email_unsubscribed", email, {}));
}

const FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";

function page(title, body) {
  return new Response(
    "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">" +
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
    "<meta name=\"color-scheme\" content=\"light dark\">" +
    "<meta name=\"robots\" content=\"noindex\"><title>" + title + "</title>" +
    "<style>.uz-logo-dark{display:none;}" +
    "@media (prefers-color-scheme:dark){" +
    "body{background:#1a1816 !important;}" +
    ".uz-card{background:#2b2b2b !important;border-color:#3f4650 !important;border-top-color:#d9222a !important;}" +
    ".uz-card h1{color:#ffffff !important;}.uz-card p{color:#f2f0ef !important;}" +
    ".uz-card strong{color:#ffffff !important;}" +
    ".uz-logo-light{display:none !important;}.uz-logo-dark{display:block !important;}" +
    "}</style></head>" +
    "<body style=\"margin:0;background:#efe9e1;font-family:" + FONT + ";\">" +
    "<div style=\"max-width:520px;margin:64px auto;padding:0 16px;\">" +
    "<img src=\"https://drozq.com/api/email/logo\" class=\"uz-logo-light\" width=\"142\" height=\"20\" alt=\"drozq.com\" style=\"display:block;border:0;margin:0 0 14px;\">" +
    "<img src=\"https://drozq.com/api/email/logo?v=dark\" class=\"uz-logo-dark\" width=\"142\" height=\"20\" alt=\"drozq.com\" style=\"border:0;margin:0 0 14px;\">" +
    "<div class=\"uz-card\" style=\"background:#fff;border:1px solid #e5e5e5;border-top:4px solid #d9222a;border-radius:16px;padding:36px 32px;\">" + body + "</div>" +
    "</div></body></html>",
    { status: 200, headers: { "content-type": "text/html; charset=UTF-8", "cache-control": "no-store" } }
  );
}

export async function onRequestGet(context) {
  const email = await resolveEmail(context);
  if (!email) {
    return page("Link expired", "<h1 style=\"margin:0 0 12px;font-size:24px;color:#1a1816;\">That link didn't check out.</h1><p style=\"margin:0;font-size:16px;line-height:1.6;color:#2b2b2b;\">Email <a href=\"mailto:josh@drozq.com\" style=\"color:#d9222a;font-weight:700;\">josh@drozq.com</a> and I'll remove you by hand, same day.</p>");
  }
  // GET must NOT unsubscribe: corporate mail scanners (SafeLinks, Barracuda)
  // prefetch every link with GET and were silently unsubscribing real leads
  // the moment step 0 landed. Render a one-button confirm instead; the POST
  // below (which is also the RFC 8058 one-click path) does the actual work.
  return page("Unsubscribe",
    "<h1 style=\"margin:0 0 12px;font-size:24px;color:#1a1816;\">Unsubscribe this address?</h1>" +
    "<p style=\"margin:0;font-size:16px;line-height:1.6;color:#2b2b2b;\">One click and <strong>" + email.replace(/</g, "&lt;") + "</strong> never hears from me again.</p>" +
    "<form method=\"post\" style=\"margin:20px 0 0;\"><button type=\"submit\" style=\"background:#d9222a;color:#fff;border:none;border-radius:9999px;font-weight:700;font-size:16px;height:48px;padding:0 26px;cursor:pointer;font-family:inherit;\">Unsubscribe</button></form>");
}

export async function onRequestPost(context) {
  const email = await resolveEmail(context);
  if (email) await unsubscribe(context, email);
  // Mail clients calling the one-click header ignore the body; a human landing
  // here from the confirm button gets the branded confirmation.
  return page("Unsubscribed",
    "<h1 style=\"margin:0 0 12px;font-size:24px;color:#1a1816;\">You're unsubscribed.</h1>" +
    "<p style=\"margin:0;font-size:16px;line-height:1.6;color:#2b2b2b;\">No more emails" + (email ? " to <strong>" + email.replace(/</g, "&lt;") + "</strong>" : "") + ". If you ever want a straight read on the market, <a href=\"https://drozq.com\" style=\"color:#d9222a;font-weight:700;\">drozq.com</a> is always open.</p>");
}
