// One-time (and safely re-runnable) schema bootstrap for the email platform.
// POST with Authorization: Bearer EMAIL_SECRET after binding the EMAIL_DB D1
// database. Everything is CREATE IF NOT EXISTS, so re-running is a no-op.

import { json, adminGate } from "../../_lib/admin.js";

const STATEMENTS = [
  `CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT,
    name TEXT,
    source TEXT NOT NULL DEFAULT 'newsletter',
    intent TEXT,
    city TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    sequence_id TEXT,
    sequence_step INTEGER NOT NULL DEFAULT 0,
    next_send_at TEXT,
    gclid TEXT,
    page_url TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  )`,
  `CREATE INDEX IF NOT EXISTS idx_subscribers_due ON subscribers(status, next_send_at)`,
  `CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE,
    subject TEXT NOT NULL,
    payload TEXT NOT NULL,
    segment TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )`,
  `CREATE TABLE IF NOT EXISTS email_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER,
    campaign_id INTEGER,
    email TEXT NOT NULL,
    kind TEXT NOT NULL,
    ref TEXT,
    subject TEXT,
    status TEXT NOT NULL,
    error TEXT,
    payload TEXT,
    send_after TEXT,
    sent_at TEXT,
    opened_at TEXT,
    clicked_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )`,
  `CREATE INDEX IF NOT EXISTS idx_email_log_queue ON email_log(status, send_after)`
];

export async function onRequestPost(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  try {
    await context.env.EMAIL_DB.batch(STATEMENTS.map((s) => context.env.EMAIL_DB.prepare(s)));
    return json({ ok: true, tables: ["subscribers", "campaigns", "email_log"] });
  } catch (e) {
    console.error("EMAIL_INIT_FAILED " + ((e && e.message) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}
