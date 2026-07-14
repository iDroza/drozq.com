// Open-tracking pixel. Every templated email embeds a 1x1 GIF pointing here
// with an HMAC-bound log id. First load stamps opened_at on the email_log row
// and fires a PostHog email_opened event. Always answers with the GIF, valid
// token or not, so a broken link can never render as a broken image.

import { hmacHex, phCapture } from "../../_lib/email.js";

const GIF = Uint8Array.from(atob("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"), (c) => c.charCodeAt(0));

export async function onRequestGet(context) {
  const { request, env } = context;
  try {
    const url = new URL(request.url);
    const id = url.searchParams.get("id") || "";
    const t = url.searchParams.get("t") || "";
    if (id && t && env.EMAIL_SECRET && env.EMAIL_DB) {
      const expect = await hmacHex(env.EMAIL_SECRET, "open:" + id);
      if (t === expect) {
        const res = await env.EMAIL_DB.prepare(
          "UPDATE email_log SET opened_at = datetime('now') WHERE id = ?1 AND opened_at IS NULL"
        ).bind(Number(id)).run();
        if (res.meta && res.meta.changes > 0) {
          const row = await env.EMAIL_DB.prepare("SELECT email, kind, ref FROM email_log WHERE id = ?1").bind(Number(id)).first();
          // waitUntil, not fire-and-forget: this handler returns immediately
          // and the runtime cancels in-flight fetches at that point.
          if (row) context.waitUntil(phCapture("email_opened", row.email, { kind: row.kind, ref: row.ref, log_id: Number(id) }));
        }
      }
    }
  } catch (e) {
    console.error("EMAIL_OPEN_THREW " + ((e && e.message) || e));
  }
  return new Response(GIF, {
    status: 200,
    headers: { "content-type": "image/gif", "cache-control": "no-store, private", "content-length": String(GIF.length) }
  });
}
