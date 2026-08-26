// Enrollment orchestration: one function that /api/lead, /api/subscribe, and
// /api/email/backfill all call. Inserts the subscriber (never re-enrolls an
// existing or unsubscribed address), then either sends sequence step 0
// immediately (the "instant" promise) or schedules it (backfill stagger).

import { upsertSubscriber, sendSequenceStep, windowedISO, offsetMs, phCapture, ensureEmailColumns } from "./email.js";
import { maskEmail } from "./redact.js";
import { getSequence, sequenceIdFor } from "./sequence.js";

export async function enrollSubscriber(env, seed, opts) {
  const options = opts || {};
  const sequenceId = seed.sequence_id || sequenceIdFor(seed.source, seed.intent);
  const seq = getSequence(sequenceId);
  if (!seq) return { inserted: false, reason: "unknown_sequence" };

  // Idle import: on the list (broadcasts reach them) but no sequence sends.
  if (options.idle) {
    const { inserted, row } = await upsertSubscriber(env, Object.assign({}, seed, {
      sequence_id: sequenceId,
      next_send_at: null
    }));
    if (inserted) await phCapture("email_subscriber_enrolled", seed.email, { source: seed.source, sequence_id: sequenceId, mode: "idle" });
    return { inserted, row, sent: false };
  }

  // Scheduled start (backfill): step 0 goes out via the cron tick at start_at.
  if (options.startAtMs) {
    const { inserted, row } = await upsertSubscriber(env, Object.assign({}, seed, {
      sequence_id: sequenceId,
      next_send_at: windowedISO(options.startAtMs, env)
    }));
    if (inserted) await phCapture("email_subscriber_enrolled", seed.email, { source: seed.source, sequence_id: sequenceId, mode: "scheduled" });
    return { inserted, row, sent: false };
  }

  // Instant start: insert idle (next_send_at NULL so a concurrent tick cannot
  // grab it), send step 0 right now, then arm the next step.
  const { inserted, row } = await upsertSubscriber(env, Object.assign({}, seed, {
    sequence_id: sequenceId,
    next_send_at: null
  }));
  if (!inserted || !row) return { inserted: false, row, sent: false };

  await phCapture("email_subscriber_enrolled", row.email, { source: seed.source, sequence_id: sequenceId, mode: "instant" });

  const sendOut = {};
  const ok = await sendSequenceStep(env, row, seq.steps[0], sendOut);

  // A transient failure on the instant step (MailChannels 5xx, a timeout) is
  // retried by the tick in 10 minutes: stay on step 0 and arm next_send_at,
  // with this send counted as attempt 1 of 3 (the tick enforces the cap and
  // logs EMAIL_SEQ_STEP_GAVE_UP when it is reached).
  if (!ok && sendOut.transient && await ensureEmailColumns(env)) {
    await env.EMAIL_DB.prepare(
      "UPDATE subscribers SET sequence_step = 0, next_send_at = ?1, step_attempts = 1, updated_at = datetime('now') WHERE id = ?2"
    ).bind(new Date(Date.now() + 10 * 60 * 1000).toISOString(), row.id).run();
    console.log("EMAIL_SEQ_STEP_RETRY email=" + maskEmail(row.email) + " step=" + seq.steps[0].id + " attempt=1 status=" + sendOut.status);
    return { inserted: true, row, sent: false, retry: true };
  }

  const next = seq.steps[1];
  await env.EMAIL_DB.prepare(
    "UPDATE subscribers SET sequence_step = 1, next_send_at = ?1, updated_at = datetime('now') WHERE id = ?2"
  ).bind(
    next ? windowedISO(Date.now() + offsetMs(next.offsetDays, env), env) : null,
    row.id
  ).run();

  return { inserted: true, row, sent: ok };
}
