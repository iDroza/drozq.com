// Tests for /functions/api/lead.js: submission_id idempotency, the email
// format check, and PII redaction in the routine log lines.
//
// Drives onRequestPost end to end with a mocked MailChannels (the only
// delivery channel configured) and a real-SQLite D1 stand-in, so the dedupe
// store, the 15-minute window, the Cache API fallback, and the "store failure
// never costs a lead" rule are all exercised with no network and no real lead.
//
// Run:  node scripts/test_lead_idempotency.mjs
import { onRequestPost } from "../functions/api/lead.js";
import { memoryD1, fakeCache, makeContext, checker } from "./_test_d1.mjs";

const { check, done } = checker();

const realNow = Date.now;
let clock = realNow();
Date.now = () => clock;

let mailPosts = [];
let mailStatus = 202;
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  if (u.includes("mailchannels")) { mailPosts.push(JSON.parse(opts.body)); return new Response("{}", { status: mailStatus }); }
  return new Response("{}", { status: 200 });
};

const CHANNELS = { TO_EMAIL: "josh@drozq.com", FROM_EMAIL: "leads@drozq.com", MAILCHANNELS_API_KEY: "k" };

function formRequest(fields) {
  const body = new URLSearchParams();
  for (const [k, v] of Object.entries(fields)) body.set(k, v);
  return new Request("https://drozq.com/api/lead", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded", "cf-connecting-ip": "203.0.113.9" },
    body: body.toString()
  });
}
const LEAD = { name: "Pat Sample", email: "seller@example.com", phone: "(949) 555-0134", consent: "yes", intent: "Home Valuation", city: "Irvine", state: "CA", source_page: "/" };

async function submit(env, fields) {
  const c = makeContext(formRequest(fields), env);
  const r = await onRequestPost(c);
  const d = await r.json();
  await Promise.all(c._waits);
  return { status: r.status, d, waits: c._waits.length };
}

function captureConsole() {
  const lines = [];
  const oe = console.error, ol = console.log;
  console.error = (m) => lines.push(String(m));
  console.log = (m) => lines.push(String(m));
  return { lines, restore() { console.error = oe; console.log = ol; } };
}

console.log("\n== idempotency (D1) ==");
{
  const env = Object.assign({ EMAIL_DB: memoryD1() }, CHANNELS);
  const id = "3f2b1c4e-0d5a-4b7e-9c8d-112233445566";
  mailPosts = [];
  const first = await submit(env, Object.assign({}, LEAD, { submission_id: id }));
  check("first submit accepted, not flagged duplicate", first.status === 200 && first.d.ok === true && !first.d.duplicate, first);
  check("first submit delivered (1 MailChannels post)", mailPosts.length === 1, mailPosts.length);

  const cap = captureConsole();
  const second = await submit(env, Object.assign({}, LEAD, { submission_id: id }));
  cap.restore();
  check("retry of the same id -> {ok:true, duplicate:true}", second.status === 200 && second.d.ok === true && second.d.duplicate === true, second);
  check("retry delivered nothing (still 1 post, no waitUntil work)", mailPosts.length === 1 && second.waits === 0, { posts: mailPosts.length, waits: second.waits });
  check("LEAD_DUPLICATE_SKIPPED logged with masked email", cap.lines.some((l) => l.startsWith("LEAD_DUPLICATE_SKIPPED id=" + id) && l.includes("s***@example.com") && !l.includes("seller@example.com")), cap.lines);

  const third = await submit(env, Object.assign({}, LEAD, { submission_id: "aaaaaaaa-1111-2222-3333-444444444444" }));
  check("a different id delivers", third.d.ok && !third.d.duplicate && mailPosts.length === 2, { third, posts: mailPosts.length });

  const noId = await submit(env, LEAD);
  const noId2 = await submit(env, LEAD);
  check("no submission_id -> every submit delivers (legacy clients unchanged)", noId.d.ok && noId2.d.ok && !noId.d.duplicate && !noId2.d.duplicate && mailPosts.length === 4, mailPosts.length);

  clock += 16 * 60 * 1000;
  const expired = await submit(env, Object.assign({}, LEAD, { submission_id: id }));
  check("same id after 15 minutes is a fresh submit", expired.d.ok && !expired.d.duplicate && mailPosts.length === 5, { expired, posts: mailPosts.length });

  const junk = await submit(env, Object.assign({}, LEAD, { submission_id: "<script>" }));
  const junk2 = await submit(env, Object.assign({}, LEAD, { submission_id: "<script>" }));
  check("malformed submission_id is ignored (no dedupe, no rejection)", junk.d.ok && junk2.d.ok && !junk2.d.duplicate, { junk, junk2 });
}

console.log("\n== idempotency: dedupe store failure never costs a lead ==");
{
  const env = Object.assign({ EMAIL_DB: memoryD1({ failOn: /lead_submissions/ }) }, CHANNELS);
  mailPosts = [];
  const cap = captureConsole();
  const a = await submit(env, Object.assign({}, LEAD, { submission_id: "dedupe-store-down-0001" }));
  const b = await submit(env, Object.assign({}, LEAD, { submission_id: "dedupe-store-down-0001" }));
  cap.restore();
  check("both accepted and delivered when the store is down", a.d.ok && b.d.ok && !b.d.duplicate && mailPosts.length === 2, { a, b, posts: mailPosts.length });
  check("LEAD_DEDUPE_STORAGE_FAILED logged", cap.lines.some((l) => l.startsWith("LEAD_DEDUPE_STORAGE_FAILED")), cap.lines);
}

console.log("\n== idempotency: Cache API fallback (no D1) ==");
{
  globalThis.caches = { default: fakeCache() };
  const env = Object.assign({}, CHANNELS);
  mailPosts = [];
  const a = await submit(env, Object.assign({}, LEAD, { submission_id: "cache-path-0000000001" }));
  const b = await submit(env, Object.assign({}, LEAD, { submission_id: "cache-path-0000000001" }));
  check("cache path: first delivers, retry is a duplicate", a.d.ok && !a.d.duplicate && b.d.duplicate === true && mailPosts.length === 1, { a, b, posts: mailPosts.length });
  delete globalThis.caches;
}

console.log("\n== email format check ==");
{
  const env = Object.assign({ EMAIL_DB: memoryD1() }, CHANNELS);
  mailPosts = [];
  const bad = await submit(env, Object.assign({}, LEAD, { email: "not-an-email" }));
  check("malformed email -> 400 invalid_email, nothing delivered", bad.status === 400 && bad.d.error === "invalid_email" && mailPosts.length === 0, bad);
  const bad2 = await submit(env, Object.assign({}, LEAD, { email: "a@b" }));
  check("missing TLD -> 400 invalid_email", bad2.status === 400 && bad2.d.error === "invalid_email", bad2);
  const placeholder = await submit(env, Object.assign({}, LEAD, { phone: "0000000000", intent: "Google One Tap Lead" }));
  check("phone stays lenient: One Tap placeholder still accepted", placeholder.status === 200 && placeholder.d.ok === true, placeholder);
  const missing = await submit(env, Object.assign({}, LEAD, { email: "" }));
  check("missing email is still the original 400 (required fields)", missing.status === 400 && missing.d.error === "Missing required fields", missing);
}

console.log("\n== PII redaction in routine log lines ==");
{
  const env = Object.assign({ EMAIL_DB: memoryD1() }, CHANNELS);
  mailStatus = 500;
  const cap = captureConsole();
  await submit(env, LEAD);
  cap.restore();
  mailStatus = 202;
  const failed = cap.lines.find((l) => l.startsWith("LEAD_EMAIL_FAILED"));
  check("LEAD_EMAIL_FAILED line exists", !!failed, cap.lines);
  check("  masked email, no raw email", failed && failed.includes("s***@example.com") && !failed.includes("seller@example.com"), failed);
  check("  last four of phone only", failed && failed.includes("***0134") && !failed.includes("555-0134") && !failed.includes("(949)"), failed);
  check("  no name", failed && !failed.includes("Pat Sample"), failed);
  check("  intent/city kept for diagnosis", failed && failed.includes("Home Valuation") && failed.includes("Irvine"), failed);

  const cap2 = captureConsole();
  await submit({ EMAIL_DB: memoryD1() }, LEAD);   // no channel configured at all
  cap2.restore();
  const notDelivered = cap2.lines.find((l) => l.startsWith("LEAD_NOT_DELIVERED"));
  check("LEAD_NOT_DELIVERED (no channel) still carries the full recoverable lead", notDelivered && notDelivered.includes("seller@example.com") && notDelivered.includes("Pat Sample"), notDelivered);
  const skipped = cap2.lines.find((l) => l.startsWith("LEAD_EMAIL_SKIPPED"));
  check("LEAD_EMAIL_SKIPPED is redacted", skipped && !skipped.includes("seller@example.com") && skipped.includes("s***@example.com"), skipped);

  const cap3 = captureConsole();
  await submit(env, Object.assign({}, LEAD, { intent: "Home Valuation View" }));
  cap3.restore();
  const soft = cap3.lines.find((l) => l.startsWith("LEAD_SOFT_SKIPPED"));
  check("LEAD_SOFT_SKIPPED is redacted", soft && !soft.includes("seller@example.com") && !soft.includes("Pat Sample"), soft);
}

Date.now = realNow;
done();
