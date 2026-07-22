// The heartbeat. A cron (Worker or any scheduler) POSTs here every 10 minutes
// with Authorization: Bearer EMAIL_SECRET. Each tick:
//   1. Sends every due sequence step (subscribers.next_send_at <= now),
//      claiming rows optimistically so overlapping ticks can never double-send.
//   2. Drains queued broadcast rows from email_log (send_after <= now).
// Batch caps keep a single tick well inside CPU limits; anything left over is
// picked up by the next tick.

import { json, adminGate } from "../../_lib/admin.js";
import { sendSequenceStep, sendPayloadTo, windowedISO, offsetMs, phCapture } from "../../_lib/email.js";
import { getSequence } from "../../_lib/sequence.js";

const SEQUENCE_BATCH = 30;
const BROADCAST_BATCH = 40;

export async function onRequestPost(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env } = context;
  const started = Date.now();
  const nowISO = new Date().toISOString();
  const out = { ok: true, sequence_sent: 0, sequence_failed: 0, broadcast_sent: 0, broadcast_failed: 0, skipped: 0 };

  try {
    // ---- 1) Due sequence steps -------------------------------------------
    const due = await env.EMAIL_DB.prepare(
      "SELECT * FROM subscribers WHERE status = 'active' AND next_send_at IS NOT NULL AND next_send_at <= ?1 ORDER BY next_send_at LIMIT " + SEQUENCE_BATCH
    ).bind(nowISO).all();

    for (const sub of (due.results || [])) {
      const seq = getSequence(sub.sequence_id);
      const step = seq && seq.steps[sub.sequence_step];
      if (!step) {
        await env.EMAIL_DB.prepare(
          "UPDATE subscribers SET next_send_at = NULL, updated_at = datetime('now') WHERE id = ?1"
        ).bind(sub.id).run();
        out.skipped++;
        continue;
      }
      const next = seq.steps[sub.sequence_step + 1];
      const nextAt = next ? windowedISO(Date.now() + offsetMs(next.offsetDays, env), env) : null;

      // Optimistic claim: only the tick that advances the step sends the email.
      const claim = await env.EMAIL_DB.prepare(
        "UPDATE subscribers SET sequence_step = ?1, next_send_at = ?2, updated_at = datetime('now') WHERE id = ?3 AND sequence_step = ?4 AND status = 'active'"
      ).bind(sub.sequence_step + 1, nextAt, sub.id, sub.sequence_step).run();
      if (!claim.meta || claim.meta.changes === 0) { out.skipped++; continue; }

      const ok = await sendSequenceStep(env, sub, step);
      if (ok) out.sequence_sent++; else out.sequence_failed++;
    }

    // ---- 2) Queued broadcast / campaign rows ------------------------------
    const queued = await env.EMAIL_DB.prepare(
      "SELECT el.id AS log_id, el.campaign_id AS campaign_id, el.ref AS ref, " +
      "s.id AS id, s.email AS email, s.first_name AS first_name, s.name AS name, " +
      "s.city AS city, s.intent AS intent, s.sequence_id AS sequence_id " +
      "FROM email_log el JOIN subscribers s ON s.id = el.subscriber_id " +
      "WHERE el.status = 'queued' AND (el.send_after IS NULL OR el.send_after <= ?1) " +
      "AND s.status = 'active' ORDER BY el.send_after LIMIT " + BROADCAST_BATCH
    ).bind(nowISO).all();

    const campaignCache = new Map();
    for (const row of (queued.results || [])) {
      let payload = campaignCache.get(row.campaign_id);
      if (!payload) {
        const c = await env.EMAIL_DB.prepare("SELECT subject, payload FROM campaigns WHERE id = ?1").bind(row.campaign_id).first();
        if (!c) {
          await env.EMAIL_DB.prepare("UPDATE email_log SET status = 'failed', error = 'campaign_missing' WHERE id = ?1").bind(row.log_id).run();
          out.broadcast_failed++;
          continue;
        }
        try {
          payload = Object.assign({ subject: c.subject }, JSON.parse(c.payload));
        } catch (e) {
          // A malformed payload must fail ITS rows, not 500 the whole tick and
          // jam every campaign behind it forever.
          await env.EMAIL_DB.prepare("UPDATE email_log SET status = 'failed', error = 'payload_parse' WHERE id = ?1").bind(row.log_id).run();
          out.broadcast_failed++;
          continue;
        }
        campaignCache.set(row.campaign_id, payload);
      }

      const claim = await env.EMAIL_DB.prepare(
        "UPDATE email_log SET status = 'sending' WHERE id = ?1 AND status = 'queued'"
      ).bind(row.log_id).run();
      if (!claim.meta || claim.meta.changes === 0) { out.skipped++; continue; }

      const sent = await sendPayloadTo(env, row, row.log_id, payload);
      await env.EMAIL_DB.prepare(
        "UPDATE email_log SET status = ?1, error = ?2, sent_at = CASE WHEN ?1 = 'sent' THEN datetime('now') ELSE NULL END WHERE id = ?3"
      ).bind(sent.ok ? "sent" : "failed", sent.ok ? null : String(sent.error || sent.status), row.log_id).run();

      await phCapture(sent.ok ? "email_sent" : "email_send_failed", row.email, { kind: "broadcast", ref: row.ref });
      if (sent.ok) out.broadcast_sent++; else out.broadcast_failed++;
    }

    out.took_ms = Date.now() - started;
    console.log("EMAIL_TICK " + JSON.stringify(out));
    return json(out);
  } catch (e) {
    console.error("EMAIL_TICK_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}
