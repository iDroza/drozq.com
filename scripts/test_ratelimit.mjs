// Tests for functions/_lib/ratelimit.js.
//
// Exercises both storage paths (D1 via the node:sqlite adapter, the Cache API
// via a fake caches.default), the fixed-window reset, the limit boundary, the
// storage-failure and no-storage fallbacks (always allow), and the 429 shape
// enforceRateLimits returns.
//
// Run:  node scripts/test_ratelimit.mjs
import { checkRateLimit, enforceRateLimits, clientIp, RATE_RULES } from "../functions/_lib/ratelimit.js";
import { memoryD1, fakeCache, makeContext, checker } from "./_test_d1.mjs";

const { check, done } = checker();
const req = (ip) => new Request("https://drozq.com/api/valuation", { method: "POST", headers: ip ? { "CF-Connecting-IP": ip } : {} });

// Freeze/advance the clock so windows are deterministic.
const realNow = Date.now;
let clock = 1_800_000_000_000;
Date.now = () => clock;

console.log("\n== clientIp ==");
check("CF-Connecting-IP wins", clientIp(req("203.0.113.9")) === "203.0.113.9");
check("x-forwarded-for fallback", clientIp(new Request("https://x/", { headers: { "x-forwarded-for": "198.51.100.7, 10.0.0.1" } })) === "198.51.100.7");
check("no header -> unknown", clientIp(req()) === "unknown");

console.log("\n== D1 path: limit, boundary, window reset ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const rule = { bucket: "t:10m", limit: 3, windowSeconds: 600 };
  const results = [];
  for (let i = 0; i < 4; i++) results.push(await checkRateLimit(makeContext(req("203.0.113.9"), env), rule));
  check("first 3 allowed", results.slice(0, 3).every((r) => r.allowed), results.map((r) => r.allowed));
  check("remaining counts down 2,1,0", results.slice(0, 3).map((r) => r.remaining).join() === "2,1,0", results.map((r) => r.remaining));
  check("4th blocked", results[3].allowed === false);
  check("retryAfter ~ window remainder (<= 600, >= 1)", results[3].retryAfter >= 1 && results[3].retryAfter <= 600, results[3].retryAfter);
  const other = await checkRateLimit(makeContext(req("198.51.100.1"), env), rule);
  check("a different IP has its own counter", other.allowed && other.count === 1, other);
  const otherBucket = await checkRateLimit(makeContext(req("203.0.113.9"), env), { bucket: "t:1d", limit: 3, windowSeconds: 86400 });
  check("a different bucket has its own counter", otherBucket.allowed && otherBucket.count === 1, otherBucket);

  clock += 601 * 1000;   // window expired
  const after = await checkRateLimit(makeContext(req("203.0.113.9"), env), rule);
  check("window reset after expiry -> count 1, allowed", after.allowed && after.count === 1, after);

  const table = await env.EMAIL_DB.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='rate_limits'").first();
  check("rate_limits table created lazily", !!table);
}

console.log("\n== D1 path: keyed (global) bucket ignores IP ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const rule = { bucket: "g:1h", limit: 2, windowSeconds: 3600, key: "global" };
  await checkRateLimit(makeContext(req("1.1.1.1"), env), rule);
  await checkRateLimit(makeContext(req("2.2.2.2"), env), rule);
  const third = await checkRateLimit(makeContext(req("3.3.3.3"), env), rule);
  check("third IP blocked by the shared cap", third.allowed === false && third.count === 3, third);
}

console.log("\n== D1 storage failure -> allowed, logged ==");
{
  const env = { EMAIL_DB: memoryD1({ failOn: /rate_limits/ }) };
  const errs = [];
  const origErr = console.error;
  console.error = (m) => errs.push(String(m));
  const r = await checkRateLimit(makeContext(req("203.0.113.9"), env), { bucket: "t", limit: 1, windowSeconds: 60 });
  console.error = origErr;
  check("allowed on storage failure", r.allowed === true && r.retryAfter === 0, r);
  check("RATE_LIMIT_STORAGE_FAILED logged", errs.some((e) => e.startsWith("RATE_LIMIT_STORAGE_FAILED")), errs);
}

console.log("\n== Cache API fallback (no D1) ==");
{
  const cache = fakeCache();
  globalThis.caches = { default: cache };
  const env = {};
  const rule = { bucket: "c:10m", limit: 2, windowSeconds: 600 };
  const a = await checkRateLimit(makeContext(req("203.0.113.9"), env), rule);
  const b = await checkRateLimit(makeContext(req("203.0.113.9"), env), rule);
  const c = await checkRateLimit(makeContext(req("203.0.113.9"), env), rule);
  check("cache path counts 1,2,3", [a.count, b.count, c.count].join() === "1,2,3", [a, b, c]);
  check("cache path blocks at limit", a.allowed && b.allowed && !c.allowed);
  check("counter stored under the bucket key", [...cache._store.keys()].some((k) => k.includes("c%3A10m")), [...cache._store.keys()]);
  clock += 601 * 1000;
  const d = await checkRateLimit(makeContext(req("203.0.113.9"), env), rule);
  check("cache window reset after expiry", d.allowed && d.count === 1, d);

  // cache.put throwing -> allowed
  cache.put = async () => { throw new Error("cache down"); };
  const errs = [];
  const origErr = console.error;
  console.error = (m) => errs.push(String(m));
  const e = await checkRateLimit(makeContext(req("203.0.113.9"), env), rule);
  console.error = origErr;
  check("cache failure -> allowed + logged", e.allowed && errs.some((x) => x.startsWith("RATE_LIMIT_STORAGE_FAILED")), { e, errs });
  delete globalThis.caches;
}

console.log("\n== no storage at all -> allowed ==");
{
  const r = await checkRateLimit(makeContext(req("203.0.113.9"), {}), { bucket: "n", limit: 1, windowSeconds: 60 });
  const r2 = await checkRateLimit(makeContext(req("203.0.113.9"), {}), { bucket: "n", limit: 1, windowSeconds: 60 });
  check("both allowed with nothing to count in", r.allowed && r2.allowed);
}

console.log("\n== enforceRateLimits: 429 shape + policy table ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const logs = [];
  const origLog = console.log;
  console.log = (m) => logs.push(String(m));
  let resp = null;
  for (let i = 0; i < 6 && !resp; i++) resp = await enforceRateLimits(makeContext(req("203.0.113.9"), env), RATE_RULES.valuation);
  console.log = origLog;
  check("valuation: 6th call in 10 minutes is blocked", !!resp, resp && resp.status);
  const body = resp ? await resp.json() : null;
  check("429 + rate_limited + retryAfter + Retry-After header",
    resp && resp.status === 429 && body.ok === false && body.error === "rate_limited" && body.retryAfter >= 1 && resp.headers.get("retry-after") === String(body.retryAfter),
    { status: resp && resp.status, body, hdr: resp && resp.headers.get("retry-after") });
  check("RATE_LIMITED logged with a masked IP", logs.some((l) => l.startsWith("RATE_LIMITED bucket=valuation:10m") && l.includes("ip=203.0.*.*") && !l.includes("203.0.113.9")), logs);

  check("policy: valuation 5/10m, 20/1d, global 300/1h",
    RATE_RULES.valuation.map((r) => r.bucket + "=" + r.limit + "/" + r.windowSeconds).join(" ") === "valuation:10m=5/600 valuation:1d=20/86400 rentcast:global:1h=300/3600");
  check("policy: netsheet 5/10m, 20/1d, shares the global cap",
    RATE_RULES.netsheet.map((r) => r.bucket + "=" + r.limit).join(" ") === "netsheet:10m=5 netsheet:1d=20 rentcast:global:1h=300" && RATE_RULES.netsheet[2].key === "global");
  check("policy: subscribe 3/10m, 10/1d",
    RATE_RULES.subscribe.map((r) => r.bucket + "=" + r.limit).join(" ") === "subscribe:10m=3 subscribe:1d=10");
}

Date.now = realNow;
done();
