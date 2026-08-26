// Endpoint-level tests for the rate limits + email format check on the three
// guarded handlers (/api/netsheet, /api/valuation, /api/subscribe): a blocked
// or malformed request must cost no Rentcast call, save no lead, send no mail,
// and come back as the documented 429 / 400 shapes. Internal compute-only
// valuation calls (x-drozq-internal: EMAIL_SECRET) are exempt.
//
// Run:  node scripts/test_gate_limits.mjs
import { onRequest as netsheet } from "../functions/api/netsheet.js";
import { onRequest as valuation } from "../functions/api/valuation.js";
import { onRequestPost as subscribe } from "../functions/api/subscribe.js";
import { onRequestPost as initDb } from "../functions/api/email/init.js";
import { memoryD1, makeContext, checker } from "./_test_d1.mjs";

const { check, done } = checker();

let rentcastCalls = 0, leadPosts = 0, mailPosts = 0;
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  if (u.includes("rentcast")) { rentcastCalls++; return new Response("[]", { status: 200, headers: { "content-type": "application/json" } }); }
  if (u.includes("/api/lead")) { leadPosts++; return new Response("{}", { status: 200 }); }
  if (u.includes("mailchannels")) { mailPosts++; return new Response("{}", { status: 202 }); }
  return new Response("{}", { status: 200 });
};
const quiet = () => { const oe = console.error, ol = console.log; console.error = () => {}; console.log = () => {}; return () => { console.error = oe; console.log = ol; }; };

function post(path, body, headers) {
  return new Request("https://drozq.com" + path, {
    method: "POST",
    headers: Object.assign({ "content-type": "application/json", "cf-connecting-ip": "203.0.113.9" }, headers || {}),
    body: JSON.stringify(body)
  });
}
async function call(handler, req, env) {
  const c = makeContext(req, env);
  const r = await handler(c);
  const d = await r.json();
  await Promise.all(c._waits);
  return { status: r.status, d, hdr: r.headers.get("retry-after") };
}
const CONTACT = { address: "1 Example Way, Irvine, CA 92620", email: "seller@example.com", phone: "(949) 555-0134", consent: "yes", name: "Pat Sample" };

console.log("\n== /api/netsheet ==");
{
  const env = { RENTCAST_API_KEY: "k", EMAIL_DB: memoryD1() };
  const restore = quiet();
  rentcastCalls = 0; leadPosts = 0;
  const bad = await call(netsheet, post("/api/netsheet", Object.assign({}, CONTACT, { email: "nope" })), env);
  const badSpend = rentcastCalls, badLeads = leadPosts;
  const results = [];
  for (let i = 0; i < 6; i++) results.push(await call(netsheet, post("/api/netsheet", CONTACT), env));
  restore();
  check("malformed email -> 400 invalid_email, no spend, no lead", bad.status === 400 && bad.d.error === "invalid_email" && badSpend === 0 && badLeads === 0, bad);
  check("first 5 lookups pass the limiter (not 429)", results.slice(0, 5).every((r) => r.status !== 429), results.map((r) => r.status));
  const sixth = results[5];
  check("6th in 10 minutes -> 429 rate_limited + Retry-After", sixth.status === 429 && sixth.d.error === "rate_limited" && sixth.d.retryAfter >= 1 && sixth.hdr === String(sixth.d.retryAfter), sixth);
  check("blocked call: no Rentcast spend, no lead (spend/leads only from the 5 allowed)", rentcastCalls === 10 && leadPosts === 5, { rentcastCalls, leadPosts });
  const restore2 = quiet();
  const otherIp = await call(netsheet, new Request("https://drozq.com/api/netsheet", { method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": "198.51.100.2" }, body: JSON.stringify(CONTACT) }), env);
  restore2();
  check("another IP is not blocked", otherIp.status !== 429, otherIp.status);
  const rows = await env.EMAIL_DB.prepare("SELECT key, count FROM rate_limits ORDER BY key").all();
  check("counters live in rate_limits: per-IP 10m/1d + shared global", rows.results.map((r) => r.key).join(" ") === "rl:netsheet:10m:198.51.100.2 rl:netsheet:10m:203.0.113.9 rl:netsheet:1d:198.51.100.2 rl:netsheet:1d:203.0.113.9 rl:rentcast:global:1h:global", rows.results);
}

console.log("\n== /api/valuation ==");
{
  const env = { RENTCAST_API_KEY: "k", EMAIL_DB: memoryD1(), EMAIL_SECRET: "sec" };
  const restore = quiet();
  rentcastCalls = 0; leadPosts = 0;
  const bad = await call(valuation, post("/api/valuation", Object.assign({}, CONTACT, { email: "a@b" })), env);
  const badSpend = rentcastCalls;
  const results = [];
  for (let i = 0; i < 6; i++) results.push(await call(valuation, post("/api/valuation", CONTACT), env));
  const spendBeforeInternal = rentcastCalls;
  // internal compute-only calls are exempt from the limiter even after the IP is blocked
  const internal = await call(valuation, post("/api/valuation", CONTACT, { "x-drozq-internal": "sec" }), env);
  const internalSpent = rentcastCalls > spendBeforeInternal;
  restore();
  check("malformed email -> 400 invalid_email, no spend", bad.status === 400 && bad.d.error === "invalid_email" && badSpend === 0, bad);
  check("6th in 10 minutes -> 429 rate_limited", results[5].status === 429 && results[5].d.error === "rate_limited", results.map((r) => r.status));
  check("internal call bypasses the limiter and computes", internal.status !== 429 && internalSpent, { status: internal.status, internalSpent });
  const g = await env.EMAIL_DB.prepare("SELECT count FROM rate_limits WHERE key = 'rl:rentcast:global:1h:global'").first();
  check("global cap counted the 5 allowed public calls only", g && g.count === 5, g);
}

console.log("\n== shared global cap across both endpoints ==");
{
  const env = { RENTCAST_API_KEY: "k", EMAIL_DB: memoryD1() };
  await env.EMAIL_DB.prepare("CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, window_start INTEGER NOT NULL, count INTEGER NOT NULL)").run();
  await env.EMAIL_DB.prepare("INSERT INTO rate_limits (key, window_start, count) VALUES ('rl:rentcast:global:1h:global', ?1, 300)").bind(Math.floor(Date.now() / 1000)).run();
  const restore = quiet();
  rentcastCalls = 0; leadPosts = 0;
  const n = await call(netsheet, post("/api/netsheet", CONTACT), env);
  const v = await call(valuation, post("/api/valuation", CONTACT), env);
  restore();
  check("with the hourly global cap spent, fresh IPs get 429 on both endpoints", n.status === 429 && v.status === 429 && rentcastCalls === 0 && leadPosts === 0, { n: n.status, v: v.status, rentcastCalls, leadPosts });
}

console.log("\n== /api/subscribe ==");
{
  const env = { EMAIL_DB: memoryD1(), EMAIL_SECRET: "s", MAILCHANNELS_API_KEY: "k", EMAIL_TEST_FAST: "1" };
  await initDb(makeContext(new Request("https://drozq.com/api/email/init", { method: "POST", headers: { authorization: "Bearer s" } }), env));
  const restore = quiet();
  mailPosts = 0;
  const results = [];
  for (let i = 0; i < 4; i++) results.push(await call(subscribe, post("/api/subscribe", { email: "reader" + i + "@example.com" }), env));
  const bad = await call(subscribe, post("/api/subscribe", { email: "nope" }), env);
  const honey = await call(subscribe, post("/api/subscribe", { email: "bot@example.com", company_website: "x" }), env);
  restore();
  check("first 3 subscribes accepted + welcomed", results.slice(0, 3).every((r) => r.status === 200 && r.d.ok) && mailPosts === 3, { statuses: results.map((r) => r.status), mailPosts });
  check("4th in 10 minutes -> 429, no mail", results[3].status === 429 && results[3].d.error === "rate_limited" && mailPosts === 3, results[3]);
  check("invalid_email still 400", bad.status === 400 && bad.d.error === "invalid_email", bad);
  check("honeypot still a silent 200", honey.status === 200 && honey.d.ok === true, honey);
}

done();
