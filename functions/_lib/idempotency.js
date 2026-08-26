// Submission idempotency for /api/lead. The funnel stamps each submit with a
// client-generated submission_id (a UUID); a retry of the same submit (the
// funnel's own 3-attempt retry loop, a double-tap, a flaky network that
// delivered the first POST after the client gave up on it) must not produce a
// second alert, a second CRM event, or a second drip enrollment.
//
// rememberSubmission(env, id, ttlSeconds) -> { duplicate }
//   duplicate=true  : this id was accepted inside the TTL; deliver nothing.
//   duplicate=false : first sight (or the old sighting expired); proceed.
//
// Storage: D1 (env.EMAIL_DB) with a lazily created lead_submissions table and
// ONE atomic conditional upsert, else the Cache API (best effort, per-colo).
// A store failure resolves to duplicate=false: a lead is never rejected or
// dropped because the dedupe layer hiccuped.

const TABLE_SQL =
  "CREATE TABLE IF NOT EXISTS lead_submissions (id TEXT PRIMARY KEY, seen_at INTEGER NOT NULL)";

const ensuredDbs = new WeakSet();
const ID_RE = /^[A-Za-z0-9._:-]{8,80}$/;

export function normalizeSubmissionId(raw) {
  const s = String(raw == null ? "" : raw).trim();
  return ID_RE.test(s) ? s : "";
}

async function rememberD1(db, id, nowSec, ttlSeconds) {
  if (!ensuredDbs.has(db)) {
    await db.prepare(TABLE_SQL).run();
    ensuredDbs.add(db);
  }
  // Insert on first sight; on conflict, refresh ONLY when the prior sighting
  // has expired. A live duplicate leaves the row untouched, so RETURNING yields
  // no row: that absence IS the duplicate signal, decided in one statement.
  const row = await db.prepare(
    "INSERT INTO lead_submissions (id, seen_at) VALUES (?1, ?2) " +
    "ON CONFLICT(id) DO UPDATE SET seen_at = excluded.seen_at WHERE lead_submissions.seen_at < ?3 " +
    "RETURNING seen_at"
  ).bind(id, nowSec, nowSec - ttlSeconds).first();
  return { duplicate: !row };
}

async function rememberCache(cache, id, nowSec, ttlSeconds) {
  const req = new Request("https://idempotency.drozq.internal/lead/" + encodeURIComponent(id), { method: "GET" });
  const hit = await cache.match(req);
  if (hit) return { duplicate: true };
  await cache.put(req, new Response(JSON.stringify({ seen_at: nowSec }), {
    status: 200,
    headers: { "content-type": "application/json", "cache-control": "public, max-age=" + ttlSeconds }
  }));
  return { duplicate: false };
}

export async function rememberSubmission(env, id, ttlSeconds) {
  const e = env || {};
  const nowSec = Math.floor(Date.now() / 1000);
  try {
    if (e.EMAIL_DB && typeof e.EMAIL_DB.prepare === "function") {
      return await rememberD1(e.EMAIL_DB, id, nowSec, ttlSeconds);
    }
    if (typeof caches !== "undefined" && caches && caches.default) {
      return await rememberCache(caches.default, id, nowSec, ttlSeconds);
    }
    return { duplicate: false, reason: "no_storage" };
  } catch (err) {
    console.error("LEAD_DEDUPE_STORAGE_FAILED " + ((err && err.message) || err));
    return { duplicate: false, reason: "storage_failed" };
  }
}

// Housekeeping: drop sightings older than a day. Called best-effort (inside
// waitUntil) on a small fraction of requests so the table never grows without
// bound. Silent on failure.
export async function pruneSubmissions(env, olderThanSeconds) {
  try {
    const db = env && env.EMAIL_DB;
    if (!db || typeof db.prepare !== "function" || !ensuredDbs.has(db)) return;
    const cutoff = Math.floor(Date.now() / 1000) - (olderThanSeconds || 86400);
    await db.prepare("DELETE FROM lead_submissions WHERE seen_at < ?1").bind(cutoff).run();
  } catch (e) {}
}
