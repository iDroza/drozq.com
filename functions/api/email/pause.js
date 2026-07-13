// Pause or resume one subscriber's sequence. The moment a lead REPLIES, pause
// them: a drip email landing mid-conversation reads robotic and burns the
// thread. POST with Bearer EMAIL_SECRET: { email, action: "pause" | "resume" }.
// Pause only touches active subscribers; resume only touches paused ones, so
// an unsubscribe can never be accidentally reversed.

import { json, adminGate } from "../../_lib/admin.js";

export async function onRequestPost(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env, request } = context;

  try {
    const body = await request.json();
    const email = String(body.email || "").trim().toLowerCase();
    const action = String(body.action || "").trim();
    if (!email) return json({ ok: false, error: "email_required" }, 400);
    if (action !== "pause" && action !== "resume") return json({ ok: false, error: "action_must_be_pause_or_resume" }, 400);

    const res = action === "pause"
      ? await env.EMAIL_DB.prepare(
          "UPDATE subscribers SET status = 'paused', updated_at = datetime('now') WHERE email = ?1 AND status = 'active'"
        ).bind(email).run()
      : await env.EMAIL_DB.prepare(
          "UPDATE subscribers SET status = 'active', updated_at = datetime('now') WHERE email = ?1 AND status = 'paused'"
        ).bind(email).run();

    const row = await env.EMAIL_DB.prepare("SELECT email, status, sequence_step, next_send_at FROM subscribers WHERE email = ?1").bind(email).first();
    if (!row) return json({ ok: false, error: "not_found" }, 404);

    return json({ ok: true, changed: Boolean(res.meta && res.meta.changes > 0), subscriber: row });
  } catch (e) {
    console.error("EMAIL_PAUSE_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}
