// The heartbeat. A cron (Worker or any scheduler) POSTs here every 10 minutes
// with Authorization: Bearer EMAIL_SECRET. Each tick:
//   0. Reaps rows stuck in 'sending' (a tick that died mid-send): broadcast
//      rows go back to 'queued' up to 3 times, then 'failed' (reaper_gave_up);
//      sequence / manual rows are marked 'failed' (orphaned_sending), since
//      their sender owns the retry (below) or was a one-shot admin call.
//   1. Sends every due sequence step (subscribers.next_send_at <= now),
//      claiming rows optimistically so overlapping ticks can never double-send.
//      A transient send failure rolls the subscriber back to the failed step
//      with a 10-minute retry, capped at 3 attempts per step; after the cap it
//      advances as before and logs EMAIL_SEQ_STEP_GAVE_UP.
//   2. Drains queued broadcast rows from email_log (send_after <= now).
// Batch caps keep a single tick well inside CPU limits; anything left over is
// picked up by the next tick.

import { json, adminGate } from "../../_lib/admin.js";
import { sendSequenceStep, sendPayloadTo, windowedISO, offsetMs, phCapture, ensureEmailColumns } from "../../_lib/email.js";
import { getSequence } from "../../_lib/sequence.js";
import { maskEmail } from "../../_lib/redact.js";

const SEQUENCE_BATCH = 30;
const BROADCAST_BATCH = 40;
const STUCK_AFTER = "-15 minutes";      // SQLite modifier, applied to datetime('now')
const BROADCAST_MAX_RETRIES = 3;
const STEP_MAX_ATTEMPTS = 3;
const STEP_RETRY_MS = 10 * 60 * 1000;

// Reaper. Anything still 'sending' 15 minutes after it was claimed is a dead
// tick, not a slow one (every send has a 10s timeout). datetime() normalizes
// both timestamp formats the log carries (ISO with Z from windowedISO, and
// SQLite's own datetime('now')), so the comparison is sound either way.
// Returns { requeued, failed }; never throws (a reaper problem must not stop
// the tick from sending what is due).
export async function reapStuckRows(env) {
  const db = env.EMAIL_DB;
  const out = { requeued: 0, failed: 0 };
  try {
    const stuckBroadcast =
      "status = 'sending' AND kind = 'broadcast' AND " +
      "datetime(COALESCE(claimed_at, send_after, created_at)) <= datetime('now', '" + STUCK_AFTER + "')";
    const gaveUp = await db.prepare(
      "UPDATE email_log SET status = 'failed', error = 'reaper_gave_up' WHERE " + stuckBroadcast +
      " AND retry_count >= " + BROADCAST_MAX_RETRIES
    ).run();
    const requeued = await db.prepare(
      "UPDATE email_log SET status = 'queued', retry_count = retry_count + 1, claimed_at = NULL WHERE " + stuckBroadcast +
      " AND retry_count < " + BROADCAST_MAX_RETRIES
    ).run();
    const orphaned = await db.prepare(
      "UPDATE email_log SET status = 'failed', error = 'orphaned_sending' WHERE " +
      "status = 'sending' AND kind <> 'broadcast' AND " +
      "datetime(COALESCE(claimed_at, created_at)) <= datetime('now', '" + STUCK_AFTER + "')"
    ).run();
    out.requeued = (requeued.meta && requeued.meta.changes) || 0;
    out.failed = ((gaveUp.meta && gaveUp.meta.changes) || 0) + ((orphaned.meta && orphaned.meta.changes) || 0);
    console.log("EMAIL_REAPER requeued=" + out.requeued + " failed=" + out.failed);
  } catch (e) {
    console.error("EMAIL_REAPER_FAILED " + ((e && e.message) || e));
  }
  return out;
}

export async function onRequestPost(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env } = context;
  const started = Date.now();
  const nowISO = new Date().toISOString();
  const out = {
    ok: true, sequence_sent: 0, sequence_failed: 0, sequence_retried: 0, sequence_gave_up: 0,
    broadcast_sent: 0, broadcast_failed: 0, skipped: 0, reaper_requeued: 0, reaper_failed: 0
  };

  try {
    // ---- 0) Schema upgrade (lazy, cached per isolate) + reaper --------------
    // If the retry columns cannot be added, the tick still runs exactly as it
    // did before them: no reaper, no per-step retries, legacy claim statement.
    const cols = await ensureEmailColumns(env);
    if (cols) {
      const reaped = await reapStuckRows(env);
      out.reaper_requeued = reaped.requeued;
      out.reaper_failed = reaped.failed;
    } else {
      console.error("EMAIL_REAPER_SKIPPED columns_missing");
    }

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

      const sendOut = {};
      const ok = await sendSequenceStep(env, sub, step, sendOut);
      if (ok) {
        out.sequence_sent++;
        if (cols && Number(sub.step_attempts || 0) > 0) {
          await env.EMAIL_DB.prepare("UPDATE subscribers SET step_attempts = 0 WHERE id = ?1").bind(sub.id).run();
        }
        continue;
      }

      out.sequence_failed++;
      const attempts = Number(sub.step_attempts || 0) + 1;   // this failure included
      if (cols && sendOut.transient && attempts < STEP_MAX_ATTEMPTS) {
        // Roll back to the step that failed (only if nobody else moved it) and
        // retry in 10 minutes. Step 0 is instant by design; later steps keep
        // the send window.
        const retryMs = Date.now() + STEP_RETRY_MS;
        const retryAt = sub.sequence_step === 0 ? new Date(retryMs).toISOString() : windowedISO(retryMs, env);
        const rolled = await env.EMAIL_DB.prepare(
          "UPDATE subscribers SET sequence_step = ?1, next_send_at = ?2, step_attempts = ?3, updated_at = datetime('now') " +
          "WHERE id = ?4 AND sequence_step = ?5 AND status = 'active'"
        ).bind(sub.sequence_step, retryAt, attempts, sub.id, sub.sequence_step + 1).run();
        if (rolled.meta && rolled.meta.changes > 0) {
          out.sequence_retried++;
          console.log("EMAIL_SEQ_STEP_RETRY email=" + maskEmail(sub.email) + " step=" + step.id + " attempt=" + attempts + " status=" + sendOut.status);
          continue;
        }
      }
      // Permanent failure, or the cap is reached: stay advanced (as before the
      // retry logic existed) so one bad step never wedges the whole sequence.
      if (cols && attempts > 1) {
        await env.EMAIL_DB.prepare("UPDATE subscribers SET step_attempts = 0 WHERE id = ?1").bind(sub.id).run();
      }
      if (sendOut.transient) {
        out.sequence_gave_up++;
        console.error("EMAIL_SEQ_STEP_GAVE_UP email=" + maskEmail(sub.email) + " step=" + step.id + " attempts=" + attempts + " status=" + sendOut.status);
      } else {
        console.error("EMAIL_SEQ_STEP_PERMANENT email=" + maskEmail(sub.email) + " step=" + step.id + " status=" + sendOut.status);
      }
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

      // The claim stamps claimed_at so the reaper can tell a dead tick from a
      // live one (legacy statement when the column is unavailable).
      const claim = await env.EMAIL_DB.prepare(
        cols
          ? "UPDATE email_log SET status = 'sending', claimed_at = datetime('now') WHERE id = ?1 AND status = 'queued'"
          : "UPDATE email_log SET status = 'sending' WHERE id = ?1 AND status = 'queued'"
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
