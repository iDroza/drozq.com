// Per-IP rate limiting for the endpoints that cost money or send mail:
// /api/valuation and /api/netsheet (every uncached call is paid Rentcast
// spend) and /api/subscribe (every accepted call sends a welcome email).
//
// Fixed-window counters keyed on the client IP (CF-Connecting-IP) + bucket.
// Storage, in order of preference:
//   1. D1 (env.EMAIL_DB): table rate_limits(key, window_start, count),
//      created lazily with one CREATE TABLE IF NOT EXISTS per isolate, and a
//      single atomic UPSERT that resets the window when it has expired. This
//      is the only globally-consistent path (D1 is one database, not per-colo).
//   2. Cache API (caches.default): a short-TTL counter Response. Best effort
//      and per-colo, so a rotating-IP attacker spread across colos can exceed
//      the nominal limit; it still stops the common single-IP hammer.
//   3. Neither available (local tests, a stripped runtime): allow.
//
// The limiter NEVER throws and never blocks on a storage problem: any error
// resolves to allowed=true and logs RATE_LIMIT_STORAGE_FAILED. Losing a lead
// to a broken counter would cost more than the spend it protects.
//
// The dashboard-side complement is a Cloudflare WAF rate-limiting rule on the
// same three paths (see docs); this code is the application-level guard that
// works even when that rule is absent.

import { maskIp } from "./redact.js";

const TABLE_SQL =
  "CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, window_start INTEGER NOT NULL, count INTEGER NOT NULL)";

// One-per-isolate memo of D1 instances whose rate_limits table is known to
// exist, so the CREATE runs once per isolate, not once per request.
const ensuredDbs = new WeakSet();
let warnedNoStorage = false;

const json = (data, status, extraHeaders) =>
  new Response(JSON.stringify(data), {
    status,
    headers: Object.assign({ "content-type": "application/json; charset=UTF-8" }, extraHeaders || {})
  });

export function clientIp(request) {
  const h = request && request.headers;
  if (!h) return "unknown";
  const ip = h.get("CF-Connecting-IP") || h.get("cf-connecting-ip") || "";
  if (ip) return ip.trim();
  const xff = h.get("x-forwarded-for") || "";
  if (xff) return xff.split(",")[0].trim() || "unknown";
  return "unknown";
}

function storageKey(bucket, subject) {
  return "rl:" + bucket + ":" + subject;
}

// D1 path. SET expressions in SQLite evaluate against the pre-update row, so
// both CASEs see the OLD window_start: an expired window resets to count=1
// with a fresh start; a live window increments in place. One round trip,
// atomic under D1's single-writer model.
async function bumpD1(db, key, nowSec, windowSeconds) {
  if (!ensuredDbs.has(db)) {
    await db.prepare(TABLE_SQL).run();
    ensuredDbs.add(db);
  }
  const expiredBefore = nowSec - windowSeconds;
  const row = await db.prepare(
    "INSERT INTO rate_limits (key, window_start, count) VALUES (?1, ?2, 1) " +
    "ON CONFLICT(key) DO UPDATE SET " +
    "count = CASE WHEN window_start <= ?3 THEN 1 ELSE count + 1 END, " +
    "window_start = CASE WHEN window_start <= ?3 THEN ?2 ELSE window_start END " +
    "RETURNING window_start, count"
  ).bind(key, nowSec, expiredBefore).first();
  if (!row) throw new Error("rate_limits upsert returned no row");
  return { windowStart: Number(row.window_start), count: Number(row.count) };
}

// Cache API path. Read-modify-write (not atomic), per-colo, short TTL. The
// synthetic URL is never fetched; it is only a cache key.
async function bumpCache(cache, key, nowSec, windowSeconds) {
  const req = new Request("https://ratelimit.drozq.internal/" + encodeURIComponent(key), { method: "GET" });
  let windowStart = nowSec;
  let count = 0;
  const hit = await cache.match(req);
  if (hit) {
    try {
      const prev = await hit.json();
      const ws = Number(prev && prev.window_start);
      const c = Number(prev && prev.count);
      if (Number.isFinite(ws) && Number.isFinite(c) && ws > nowSec - windowSeconds) {
        windowStart = ws;
        count = c;
      }
    } catch (e) {}
  }
  count += 1;
  const ttl = Math.max(1, windowStart + windowSeconds - nowSec);
  await cache.put(req, new Response(JSON.stringify({ window_start: windowStart, count }), {
    status: 200,
    headers: { "content-type": "application/json", "cache-control": "public, max-age=" + ttl }
  }));
  return { windowStart, count };
}

// checkRateLimit(context, { bucket, limit, windowSeconds, key? })
//   -> { allowed, remaining, retryAfter, count, ip }
// `key` overrides the per-IP subject (e.g. "global" for the shared Rentcast
// spend cap). retryAfter is in whole seconds (>= 1) when blocked, else 0.
export async function checkRateLimit(context, opts) {
  const { bucket, limit, windowSeconds } = opts || {};
  const request = context && context.request;
  const env = (context && context.env) || {};
  const ip = clientIp(request);
  const subject = (opts && opts.key) || ip;
  const nowSec = Math.floor(Date.now() / 1000);
  const key = storageKey(bucket, subject);

  let counter = null;
  try {
    if (env.EMAIL_DB && typeof env.EMAIL_DB.prepare === "function") {
      counter = await bumpD1(env.EMAIL_DB, key, nowSec, windowSeconds);
    } else if (typeof caches !== "undefined" && caches && caches.default) {
      counter = await bumpCache(caches.default, key, nowSec, windowSeconds);
    } else {
      if (!warnedNoStorage) {
        warnedNoStorage = true;
        console.error("RATE_LIMIT_STORAGE_FAILED reason=no_storage bucket=" + bucket + " (allowing; bind EMAIL_DB for enforcement)");
      }
      return { allowed: true, remaining: limit, retryAfter: 0, count: 0, ip };
    }
  } catch (e) {
    console.error("RATE_LIMIT_STORAGE_FAILED bucket=" + bucket + " " + ((e && e.message) || e));
    return { allowed: true, remaining: limit, retryAfter: 0, count: 0, ip };
  }

  const allowed = counter.count <= limit;
  const remaining = Math.max(0, limit - counter.count);
  const retryAfter = allowed ? 0 : Math.max(1, counter.windowStart + windowSeconds - nowSec);
  return { allowed, remaining, retryAfter, count: counter.count, ip };
}

// Run a list of rules in order; the first one that blocks wins. Returns null
// when every rule allows, else a ready-to-return 429 Response (and logs the
// RATE_LIMITED line with the IP masked). Rule shape: { bucket, limit,
// windowSeconds, key? }.
export async function enforceRateLimits(context, rules) {
  for (const rule of rules) {
    const r = await checkRateLimit(context, rule);
    if (!r.allowed) {
      console.log("RATE_LIMITED bucket=" + rule.bucket + " ip=" + maskIp(r.ip) + " count=" + r.count + " retryAfter=" + r.retryAfter);
      return json({ ok: false, error: "rate_limited", retryAfter: r.retryAfter }, 429, {
        "retry-after": String(r.retryAfter),
        "cache-control": "no-store"
      });
    }
  }
  return null;
}

// The policy table, in one place so the three endpoints and the docs agree.
const TEN_MIN = 600;
const ONE_HOUR = 3600;
const ONE_DAY = 86400;

// Shared spend cap across the two Rentcast-backed endpoints: even with rotating
// IPs, at most 300 paid lookups an hour site-wide.
const RENTCAST_GLOBAL = { bucket: "rentcast:global:1h", limit: 300, windowSeconds: ONE_HOUR, key: "global" };

export const RATE_RULES = {
  valuation: [
    { bucket: "valuation:10m", limit: 5, windowSeconds: TEN_MIN },
    { bucket: "valuation:1d", limit: 20, windowSeconds: ONE_DAY },
    RENTCAST_GLOBAL
  ],
  netsheet: [
    { bucket: "netsheet:10m", limit: 5, windowSeconds: TEN_MIN },
    { bucket: "netsheet:1d", limit: 20, windowSeconds: ONE_DAY },
    RENTCAST_GLOBAL
  ],
  subscribe: [
    { bucket: "subscribe:10m", limit: 3, windowSeconds: TEN_MIN },
    { bucket: "subscribe:1d", limit: 10, windowSeconds: ONE_DAY }
  ]
};
