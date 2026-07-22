// Manual 1:1 send in the brand template: the "progress update for a buyer"
// tool. POST with Authorization: Bearer EMAIL_SECRET and JSON:
// {
//   to, to_name?, first_name?, city?,
//   subject, headline?, paragraphs: ["...", "..."], preheader?,
//   cta_label?, cta_url?, include_unsub? (default false: 1:1 updates are
//   transactional and should not carry an unsubscribe footer)
// }
// Paragraphs support **bold** and [label](https://url). Sends immediately,
// logs to email_log (kind 'manual'), returns { ok, sent, log_id }.

import { json, adminGate } from "../../_lib/admin.js";
import { sendPayloadTo, validEmail, phCapture } from "../../_lib/email.js";

export async function onRequestPost(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env, request } = context;

  try {
    const body = await request.json();
    const to = String(body.to || "").trim().toLowerCase();
    if (!validEmail(to)) return json({ ok: false, error: "invalid_to" }, 400);
    if (!body.subject || !Array.isArray(body.paragraphs) || body.paragraphs.length === 0) {
      return json({ ok: false, error: "subject_and_paragraphs_required" }, 400);
    }

    const existing = await env.EMAIL_DB.prepare("SELECT * FROM subscribers WHERE email = ?1").bind(to).first();
    if (existing && existing.status === "unsubscribed" && body.force !== true) {
      return json({ ok: false, error: "recipient_unsubscribed", note: "This address opted out. Pass force:true only for transactional mail the person explicitly asked for." }, 409);
    }
    const sub = {
      id: existing ? existing.id : null,
      email: to,
      first_name: body.first_name || (existing && existing.first_name) || null,
      name: body.to_name || (existing && existing.name) || null,
      city: body.city || (existing && existing.city) || null,
      intent: existing ? existing.intent : null
    };

    const payload = {
      subject: String(body.subject),
      preheader: body.preheader ? String(body.preheader) : "",
      headline: body.headline ? String(body.headline) : "",
      paragraphs: body.paragraphs.map(String),
      ctaLabel: body.cta_label ? String(body.cta_label) : "",
      ctaUrl: body.cta_url ? String(body.cta_url) : "",
      includeUnsub: body.include_unsub === true
    };

    const log = await env.EMAIL_DB.prepare(
      "INSERT INTO email_log (subscriber_id, email, kind, ref, subject, status, payload) VALUES (?1, ?2, 'manual', ?3, ?4, 'sending', ?5) RETURNING id"
    ).bind(sub.id, to, body.ref ? String(body.ref) : "manual", payload.subject, JSON.stringify(payload)).first();

    const sent = await sendPayloadTo(env, sub, log.id, payload);

    await env.EMAIL_DB.prepare(
      "UPDATE email_log SET status = ?1, error = ?2, sent_at = CASE WHEN ?1 = 'sent' THEN datetime('now') ELSE NULL END WHERE id = ?3"
    ).bind(sent.ok ? "sent" : "failed", sent.ok ? null : String(sent.error || sent.status), log.id).run();

    phCapture(sent.ok ? "email_sent" : "email_send_failed", to, { kind: "manual", subject: payload.subject });
    return json({ ok: sent.ok, sent: sent.ok, log_id: log.id, error: sent.ok ? undefined : sent.error });
  } catch (e) {
    console.error("EMAIL_SEND_ENDPOINT_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}
