// Durable, cross-visit "returning visitor" identity, keyed by the opaque
// drozq_vid cookie that functions/_middleware.js re-issues (Set-Cookie) on
// every request. Exists because the funnel's original returning-visitor
// system lived entirely in localStorage: Safari ITP caps ALL script-writable
// storage (document.cookie AND localStorage) to 7 days regardless of the
// 30-day TTL coded in the client JS, and this site's traffic is mostly
// mobile Safari. The vid cookie sidesteps that cap because it is refreshed
// via an HTTP Set-Cookie response header, not JS -- see _lib/visitorid.js.
// This endpoint is the D1-backed store the vid points at, so no PII rides
// along in a client-readable cookie: only the opaque id does.
//
// GET  -> { ok, found, data: {fullName, email, phone, address, gclid, updatedAt} }
// POST -> merges whatever fields are present into the visitor's row (never
//         blanks a field the caller omitted or sent empty).
//
// No email is sent and no CRM record is created here; this is purely a
// client-experience cache (form prefill + gclid recall), so the bar is
// lower than /api/lead: light per-IP rate limiting is enough, no honeypot,
// no consent gate.

import { getVid } from "../_lib/visitorid.js";
import { enforceRateLimits } from "../_lib/ratelimit.js";

const TABLE_SQL =
  "CREATE TABLE IF NOT EXISTS returning_visitors (" +
  "vid TEXT PRIMARY KEY, full_name TEXT, email TEXT, phone TEXT, " +
  "address_json TEXT, gclid TEXT, updated_at INTEGER NOT NULL)";

const ensuredDbs = new WeakSet();
const TTL_SECONDS = 60 * 60 * 24 * 30; // 30 days, matches the client's STORAGE_TTL_DAYS
const PRUNE_AFTER_SECONDS = 60 * 60 * 24 * 60; // buffer past TTL before a row is deleted

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8", "cache-control": "private, no-store" }
  });

async function ensureTable(db) {
  if (ensuredDbs.has(db)) return;
  await db.prepare(TABLE_SQL).run();
  ensuredDbs.add(db);
}

function clip(v, n) {
  return String(v == null ? "" : v).trim().slice(0, n);
}

export async function onRequestGet(context) {
  try {
    const { request, env } = context;
    if (!env.EMAIL_DB) return json({ ok: true, found: false });

    const vid = getVid(request);
    if (!vid) return json({ ok: true, found: false });

    await ensureTable(env.EMAIL_DB);
    const row = await env.EMAIL_DB.prepare(
      "SELECT full_name, email, phone, address_json, gclid, updated_at FROM returning_visitors WHERE vid = ?1"
    ).bind(vid).first();

    if (!row) return json({ ok: true, found: false });

    const ageSec = Math.floor(Date.now() / 1000) - Number(row.updated_at || 0);
    if (ageSec > TTL_SECONDS) return json({ ok: true, found: false });

    let address = null;
    if (row.address_json) {
      try { address = JSON.parse(row.address_json); } catch (e) {}
    }

    return json({
      ok: true,
      found: true,
      data: {
        fullName: row.full_name || "",
        email: row.email || "",
        phone: row.phone || "",
        address,
        gclid: row.gclid || "",
        updatedAt: Number(row.updated_at || 0)
      }
    });
  } catch (e) {
    console.error("VISITOR_GET_FAILED " + ((e && e.message) || e));
    return json({ ok: true, found: false });
  }
}

export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    if (!env.EMAIL_DB) return json({ ok: false, error: "unconfigured" }, 503);

    const vid = getVid(request);
    if (!vid) return json({ ok: false, error: "no_visitor_id" }, 200);

    const limited = await enforceRateLimits(context, [
      { bucket: "visitor:10m", limit: 30, windowSeconds: 600 }
    ]);
    if (limited) return limited;

    const contentType = request.headers.get("Content-Type") || "";
    let fields = {};
    if (contentType.includes("application/json")) {
      fields = await request.json().catch(() => ({}));
    } else {
      const formData = await request.formData();
      for (const [k, v] of formData.entries()) fields[k] = String(v);
    }

    const fullName = clip(fields.fullName, 200);
    const email = clip(fields.email, 200);
    const phone = clip(fields.phone, 40);
    const gclid = clip(fields.gclid, 200);

    let addressJson = "";
    if (fields.address) {
      try {
        const addr = typeof fields.address === "string" ? JSON.parse(fields.address) : fields.address;
        if (addr && typeof addr === "object" && addr.formatted) {
          addressJson = JSON.stringify(addr).slice(0, 2000);
        }
      } catch (e) {}
    }

    if (!fullName && !email && !phone && !addressJson && !gclid) {
      return json({ ok: true }, 200); // nothing worth storing
    }

    await ensureTable(env.EMAIL_DB);
    const now = Math.floor(Date.now() / 1000);
    await env.EMAIL_DB.prepare(
      "INSERT INTO returning_visitors (vid, full_name, email, phone, address_json, gclid, updated_at) " +
      "VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7) " +
      "ON CONFLICT(vid) DO UPDATE SET " +
      "full_name = CASE WHEN ?2 != '' THEN ?2 ELSE returning_visitors.full_name END, " +
      "email = CASE WHEN ?3 != '' THEN ?3 ELSE returning_visitors.email END, " +
      "phone = CASE WHEN ?4 != '' THEN ?4 ELSE returning_visitors.phone END, " +
      "address_json = CASE WHEN ?5 != '' THEN ?5 ELSE returning_visitors.address_json END, " +
      "gclid = CASE WHEN ?6 != '' THEN ?6 ELSE returning_visitors.gclid END, " +
      "updated_at = ?7"
    ).bind(vid, fullName, email, phone, addressJson, gclid, now).run();

    if (Math.random() < 0.02) {
      context.waitUntil(
        env.EMAIL_DB.prepare("DELETE FROM returning_visitors WHERE updated_at < ?1")
          .bind(now - PRUNE_AFTER_SECONDS).run().catch(() => {})
      );
    }

    return json({ ok: true }, 200);
  } catch (e) {
    console.error("VISITOR_POST_FAILED " + ((e && e.message) || e));
    return json({ ok: false, error: "server_error" }, 500);
  }
}
