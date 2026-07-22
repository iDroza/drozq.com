// Enrollment orchestration: one function that /api/lead, /api/subscribe, and
// /api/email/backfill all call. Inserts the subscriber (never re-enrolls an
// existing or unsubscribed address), then either sends sequence step 0
// immediately (the "instant" promise) or schedules it (backfill stagger).

import { upsertSubscriber, sendSequenceStep, windowedISO, offsetMs, phCapture } from "./email.js";
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

  const ok = await sendSequenceStep(env, row, seq.steps[0]);

  const next = seq.steps[1];
  await env.EMAIL_DB.prepare(
    "UPDATE subscribers SET sequence_step = 1, next_send_at = ?1, updated_at = datetime('now') WHERE id = ?2"
  ).bind(
    next ? windowedISO(Date.now() + offsetMs(next.offsetDays, env), env) : null,
    row.id
  ).run();

  return { inserted: true, row, sent: ok };
}
