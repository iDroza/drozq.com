// The living subscriber list, readable on demand. GET with Authorization:
// Bearer EMAIL_SECRET. Query params:
//   status=active|paused|unsubscribed   optional filter
//   source=lead|backfill|newsletter|... optional filter
//   format=json (default) | csv
//   limit=N (default 1000)
// JSON responses include summary counts (by status, by source) plus 7-day
// send/open/click totals so one call answers "how is the list doing".

import { json, adminGate } from "../../_lib/admin.js";

export async function onRequestGet(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env, request } = context;

  try {
    const url = new URL(request.url);
    const status = url.searchParams.get("status");
    const source = url.searchParams.get("source");
    const format = url.searchParams.get("format") || "json";
    const limit = Math.min(10000, Number(url.searchParams.get("limit")) || 1000);

    // ?view=log : the send log instead of the subscriber list. This is where
    // failed sends surface (status='failed' + the MailChannels error text).
    if (url.searchParams.get("view") === "log") {
      const log = await env.EMAIL_DB.prepare(
        "SELECT id, email, kind, ref, subject, status, error, send_after, sent_at, opened_at, clicked_at, created_at " +
        "FROM email_log ORDER BY id DESC LIMIT " + Math.min(500, limit)
      ).all();
      return json({ ok: true, count: (log.results || []).length, log: log.results || [] });
    }

    const where = [];
    const binds = [];
    if (status) { where.push("status = ?" + (binds.length + 1)); binds.push(status); }
    if (source) { where.push("source = ?" + (binds.length + 1)); binds.push(source); }
    const whereSql = where.length ? " WHERE " + where.join(" AND ") : "";

    const rows = await env.EMAIL_DB.prepare(
      "SELECT id, email, first_name, name, source, intent, city, street, timeline, status, sequence_id, sequence_step, next_send_at, created_at " +
      "FROM subscribers" + whereSql + " ORDER BY created_at DESC LIMIT " + limit
    ).bind(...binds).all();

    if (format === "csv") {
      const cols = ["id", "email", "first_name", "name", "source", "intent", "city", "street", "timeline", "status", "sequence_id", "sequence_step", "next_send_at", "created_at"];
      const esc = (v) => {
        const s = v == null ? "" : String(v);
        return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
      };
      const csv = [cols.join(",")]
        .concat((rows.results || []).map((r) => cols.map((c) => esc(r[c])).join(",")))
        .join("\n");
      return new Response(csv, {
        status: 200,
        headers: {
          "content-type": "text/csv; charset=UTF-8",
          "content-disposition": "attachment; filename=drozq-subscribers.csv"
        }
      });
    }

    const byStatus = await env.EMAIL_DB.prepare("SELECT status, COUNT(*) AS n FROM subscribers GROUP BY status").all();
    const bySource = await env.EMAIL_DB.prepare("SELECT source, COUNT(*) AS n FROM subscribers GROUP BY source").all();
    const week = await env.EMAIL_DB.prepare(
      "SELECT COUNT(*) AS sent, SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) AS opened, " +
      "SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END) AS clicked " +
      "FROM email_log WHERE status = 'sent' AND sent_at >= datetime('now', '-7 days')"
    ).first();

    return json({
      ok: true,
      count: (rows.results || []).length,
      by_status: Object.fromEntries((byStatus.results || []).map((r) => [r.status, r.n])),
      by_source: Object.fromEntries((bySource.results || []).map((r) => [r.source, r.n])),
      last_7_days: { sent: week.sent || 0, opened: week.opened || 0, clicked: week.clicked || 0 },
      subscribers: rows.results || []
    });
  } catch (e) {
    console.error("EMAIL_LIST_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}
