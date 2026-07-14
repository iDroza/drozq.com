// Click tracking: CTA links in templated emails route through here with an
// HMAC that binds the log id AND the destination, then 302 to the real URL.
// Tokens can't be minted or repointed without EMAIL_SECRET, so this is not an
// open redirect. If anything fails after the token checks out, the redirect
// still happens: tracking must never eat a click.

import { b64urlDecode, hmacHex, phCapture } from "../../_lib/email.js";

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const id = url.searchParams.get("id") || "";
  const u = url.searchParams.get("u") || "";
  const t = url.searchParams.get("t") || "";

  if (!id || !u || !t || !env.EMAIL_SECRET) {
    return Response.redirect("https://drozq.com/", 302);
  }
  const expect = await hmacHex(env.EMAIL_SECRET, "click:" + id + ":" + u);
  if (t !== expect) return Response.redirect("https://drozq.com/", 302);

  let target = "https://drozq.com/";
  try { target = b64urlDecode(u); } catch (e) {}
  if (!/^https?:\/\//i.test(target)) target = "https://drozq.com/";

  try {
    if (env.EMAIL_DB) {
      const res = await env.EMAIL_DB.prepare(
        "UPDATE email_log SET clicked_at = datetime('now') WHERE id = ?1 AND clicked_at IS NULL"
      ).bind(Number(id)).run();
      if (res.meta && res.meta.changes > 0) {
        const row = await env.EMAIL_DB.prepare("SELECT email, kind, ref FROM email_log WHERE id = ?1").bind(Number(id)).first();
        // waitUntil: the redirect returns immediately and would cancel the capture.
        if (row) context.waitUntil(phCapture("email_link_clicked", row.email, { kind: row.kind, ref: row.ref, url: target, log_id: Number(id) }));
      }
    }
  } catch (e) {
    console.error("EMAIL_CLICK_THREW " + ((e && e.message) || e));
  }
  return Response.redirect(target, 302);
}
