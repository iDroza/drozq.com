// Tests for the email platform's tick: the stuck-row reaper (real SQL on a
// real SQLite via the D1 stand-in), the lazy column migration, and the
// per-step retry / give-up path for transient sequence send failures.
//
// Run:  node scripts/test_email_tick.mjs
import { onRequestPost as initDb } from "../functions/api/email/init.js";
import { onRequestPost as tick, reapStuckRows } from "../functions/api/email/tick.js";
import { ensureEmailColumns, isTransientSend } from "../functions/_lib/email.js";
import { enrollSubscriber } from "../functions/_lib/enroll.js";
import { memoryD1, makeContext, checker } from "./_test_d1.mjs";

const { check, done } = checker();

let mailStatus = 202;
let mailPosts = 0;
globalThis.fetch = async (url) => {
  const u = String(url);
  if (u.includes("mailchannels")) { mailPosts++; return new Response("{}", { status: mailStatus }); }
  return new Response("{}", { status: 200 });   // PostHog capture
};

async function freshEnv() {
  const env = { EMAIL_DB: memoryD1(), EMAIL_SECRET: "s", MAILCHANNELS_API_KEY: "k", EMAIL_TEST_FAST: "1" };
  const r = await initDb(makeContext(new Request("https://drozq.com/api/email/init", { method: "POST", headers: { authorization: "Bearer s" } }), env));
  const d = await r.json();
  if (!d.ok) throw new Error("init failed: " + JSON.stringify(d));
  return env;
}
const sql = (env, q, ...args) => env.EMAIL_DB.prepare(q).bind(...args);
async function runTick(env) {
  const r = await tick(makeContext(new Request("https://drozq.com/api/email/tick", { method: "POST", headers: { authorization: "Bearer s" } }), env));
  return r.json();
}
function captureConsole() {
  const lines = [];
  const oe = console.error, ol = console.log;
  console.error = (m) => lines.push(String(m));
  console.log = (m) => lines.push(String(m));
  return { lines, restore() { console.error = oe; console.log = ol; } };
}

console.log("\n== lazy column migration ==");
{
  const env = await freshEnv();
  // init already applied the ALTERs; ensureEmailColumns must still report ready
  // (duplicate-column errors swallowed, probe SELECT succeeds) and cache it.
  const ready = await ensureEmailColumns(env);
  const again = await ensureEmailColumns(env);
  check("columns ready after init + idempotent re-run", ready === true && again === true);
  const cols = (await sql(env, "PRAGMA table_info(email_log)").all()).results.map((c) => c.name);
  const scols = (await sql(env, "PRAGMA table_info(subscribers)").all()).results.map((c) => c.name);
  check("email_log has retry_count + claimed_at", cols.includes("retry_count") && cols.includes("claimed_at"), cols);
  check("subscribers has step_attempts", scols.includes("step_attempts"), scols);
  check("no EMAIL_DB -> not ready, no throw", (await ensureEmailColumns({})) === false);
}

console.log("\n== isTransientSend ==");
check("5xx / 0 / 429 / 408 transient", [500, 503, 0, 429, 408].every((s) => isTransientSend({ ok: false, status: s })));
check("4xx permanent", [400, 401, 403, 404, 422].every((s) => !isTransientSend({ ok: false, status: s })));
check("ok is never transient", !isTransientSend({ ok: true, status: 202 }));

console.log("\n== reaper ==");
{
  const env = await freshEnv();
  await ensureEmailColumns(env);
  await sql(env, "INSERT INTO subscribers (id, email, source, status, sequence_id) VALUES (1, 'a@example.com', 'lead', 'active', 'lead-response-v1')").run();
  await sql(env, "INSERT INTO campaigns (id, slug, subject, payload) VALUES (7, 'c', 'Subj', '{\"paragraphs\":[\"x\"]}')").run();
  const ins = (kind, status, extra, vals) => sql(env,
    "INSERT INTO email_log (subscriber_id, campaign_id, email, kind, ref, status" + (extra ? ", " + extra : "") + ") " +
    "VALUES (1, 7, 'a@example.com', '" + kind + "', 'r', '" + status + "'" + (vals ? ", " + vals : "") + ")").run();
  await ins("broadcast", "sending", "claimed_at, retry_count", "datetime('now','-20 minutes'), 0");                           // 1 requeue
  await ins("broadcast", "sending", "send_after, retry_count", "'" + new Date(Date.now() - 20 * 60000).toISOString() + "', 1"); // 2 legacy claim (ISO send_after) -> requeue
  await ins("broadcast", "sending", "claimed_at, retry_count", "datetime('now','-20 minutes'), 3");                           // 3 gave up
  await ins("broadcast", "sending", "claimed_at, retry_count", "datetime('now','-5 minutes'), 0");                            // 4 live, untouched
  await ins("sequence", "sending", "created_at", "datetime('now','-20 minutes')");                                            // 5 orphaned
  await ins("manual", "sending", "created_at", "datetime('now','-20 minutes')");                                              // 6 orphaned
  await ins("sequence", "sending", null, null);                                                                               // 7 fresh, untouched
  await ins("broadcast", "queued", "send_after", "'" + new Date(Date.now() - 60000).toISOString() + "'");                     // 8 queued, untouched by reaper
  await ins("broadcast", "sent", "claimed_at", "datetime('now','-40 minutes')");                                              // 9 sent, untouched

  const cap = captureConsole();
  const reaped = await reapStuckRows(env);
  cap.restore();
  const rows = (await sql(env, "SELECT id, status, error, retry_count, claimed_at FROM email_log ORDER BY id").all()).results;
  const st = (i) => rows[i - 1];
  check("requeued=2 failed=3", reaped.requeued === 2 && reaped.failed === 3, reaped);
  check("EMAIL_REAPER logged", cap.lines.some((l) => l === "EMAIL_REAPER requeued=2 failed=3"), cap.lines);
  check("1: stuck broadcast -> queued, retry_count 1, claimed_at cleared", st(1).status === "queued" && st(1).retry_count === 1 && st(1).claimed_at === null, st(1));
  check("2: legacy claim (no claimed_at, ISO send_after) -> queued, retry_count 2", st(2).status === "queued" && st(2).retry_count === 2, st(2));
  check("3: retry_count 3 -> failed reaper_gave_up", st(3).status === "failed" && st(3).error === "reaper_gave_up", st(3));
  check("4: 5-minute-old sending left alone", st(4).status === "sending", st(4));
  check("5: old sequence sending -> failed orphaned_sending", st(5).status === "failed" && st(5).error === "orphaned_sending", st(5));
  check("6: old manual sending -> failed orphaned_sending", st(6).status === "failed" && st(6).error === "orphaned_sending", st(6));
  check("7: fresh sequence sending left alone", st(7).status === "sending", st(7));
  check("8/9: queued + sent rows untouched", st(8).status === "queued" && st(9).status === "sent", [st(8), st(9)]);

  // reaper must never throw, even against a broken DB
  const broken = { EMAIL_DB: memoryD1({ failOn: /email_log/ }) };
  const cap2 = captureConsole();
  const r2 = await reapStuckRows(broken);
  cap2.restore();
  check("reaper swallows a DB failure (EMAIL_REAPER_FAILED)", r2.requeued === 0 && r2.failed === 0 && cap2.lines.some((l) => l.startsWith("EMAIL_REAPER_FAILED")), cap2.lines);

  // the tick stamps claimed_at when it claims a queued broadcast row
  mailStatus = 202;
  const t = await runTick(env);
  const after = (await sql(env, "SELECT id, status, claimed_at FROM email_log WHERE id IN (1, 2, 8) ORDER BY id").all()).results;
  check("tick drained the requeued + queued rows (3 sent)", t.ok && t.broadcast_sent === 3, t);
  check("claim stamped claimed_at on every drained row", after.every((r) => r.status === "sent" && r.claimed_at), after);
}

console.log("\n== sequence step retry: transient failure rolls back, 3 attempts, then gives up ==");
{
  const env = await freshEnv();
  const past = new Date(Date.now() - 60000).toISOString();
  await sql(env, "INSERT INTO subscribers (id, email, first_name, source, status, sequence_id, sequence_step, next_send_at) VALUES (1, 'b@example.com', 'Pat', 'lead', 'active', 'lead-response-v1', 0, ?1)").bind(past).run();
  const sub = async () => sql(env, "SELECT sequence_step, step_attempts, next_send_at, status FROM subscribers WHERE id = 1").first();

  mailStatus = 503;
  let cap = captureConsole();
  let t1 = await runTick(env);
  cap.restore();
  let s = await sub();
  check("attempt 1 fails -> rolled back to step 0, attempts 1, retried", t1.sequence_failed === 1 && t1.sequence_retried === 1 && s.sequence_step === 0 && s.step_attempts === 1, { t1, s });
  const retryMs = Date.parse(s.next_send_at) - Date.now();
  check("next_send_at ~ 10 minutes out", retryMs > 9 * 60000 && retryMs <= 10 * 60000 + 1000, retryMs);
  check("EMAIL_SEQ_STEP_RETRY logged with masked email", cap.lines.some((l) => l.startsWith("EMAIL_SEQ_STEP_RETRY email=b***@example.com step=") && l.includes("attempt=1")), cap.lines);
  check("failed send logged in email_log", (await sql(env, "SELECT COUNT(*) AS n FROM email_log WHERE status = 'failed' AND kind = 'sequence'").first()).n === 1);

  const notDue = await runTick(env);
  check("not due again until the retry time (nothing sent)", notDue.sequence_sent === 0 && notDue.sequence_failed === 0, notDue);

  await sql(env, "UPDATE subscribers SET next_send_at = ?1 WHERE id = 1").bind(past).run();
  await runTick(env);
  s = await sub();
  check("attempt 2 fails -> still step 0, attempts 2", s.sequence_step === 0 && s.step_attempts === 2, s);

  await sql(env, "UPDATE subscribers SET next_send_at = ?1 WHERE id = 1").bind(past).run();
  cap = captureConsole();
  const t3 = await runTick(env);
  cap.restore();
  s = await sub();
  check("attempt 3 fails -> gave up: advanced to step 1, attempts reset", t3.sequence_gave_up === 1 && s.sequence_step === 1 && s.step_attempts === 0 && s.next_send_at, { t3, s });
  check("EMAIL_SEQ_STEP_GAVE_UP logged", cap.lines.some((l) => l.startsWith("EMAIL_SEQ_STEP_GAVE_UP email=b***@example.com") && l.includes("attempts=3")), cap.lines);
  check("no raw email in retry/give-up lines", !cap.lines.some((l) => /EMAIL_SEQ_STEP_(RETRY|GAVE_UP)/.test(l) && l.includes("b@example.com")), cap.lines);

  // recovery: the next due step sends fine and attempts stay 0
  mailStatus = 202;
  await sql(env, "UPDATE subscribers SET next_send_at = ?1 WHERE id = 1").bind(past).run();
  const t4 = await runTick(env);
  s = await sub();
  check("step 1 sends on recovery, advanced to step 2", t4.sequence_sent === 1 && s.sequence_step === 2 && s.step_attempts === 0, { t4, s });
}

console.log("\n== sequence step: permanent failure advances immediately ==");
{
  const env = await freshEnv();
  const past = new Date(Date.now() - 60000).toISOString();
  await sql(env, "INSERT INTO subscribers (id, email, source, status, sequence_id, sequence_step, next_send_at) VALUES (1, 'c@example.com', 'lead', 'active', 'lead-response-v1', 0, ?1)").bind(past).run();
  mailStatus = 400;
  const cap = captureConsole();
  const t = await runTick(env);
  cap.restore();
  const s = await sql(env, "SELECT sequence_step, step_attempts FROM subscribers WHERE id = 1").first();
  check("4xx -> no retry, advanced to step 1 as before", t.sequence_failed === 1 && t.sequence_retried === 0 && s.sequence_step === 1 && s.step_attempts === 0, { t, s });
  check("EMAIL_SEQ_STEP_PERMANENT logged", cap.lines.some((l) => l.startsWith("EMAIL_SEQ_STEP_PERMANENT")), cap.lines);
  mailStatus = 202;
}

console.log("\n== enrollment: instant step 0 transient failure arms a retry ==");
{
  const env = await freshEnv();
  mailStatus = 503;
  const cap = captureConsole();
  const r = await enrollSubscriber(env, { email: "d@example.com", first_name: "Pat", source: "lead", intent: "Home Valuation" });
  cap.restore();
  const s = await sql(env, "SELECT sequence_step, step_attempts, next_send_at FROM subscribers WHERE email = 'd@example.com'").first();
  check("enroll reports sent=false retry=true", r.inserted && r.sent === false && r.retry === true, r);
  check("subscriber parked on step 0 with attempts 1 and a retry time", s.sequence_step === 0 && s.step_attempts === 1 && s.next_send_at, s);
  check("EMAIL_SEQ_STEP_RETRY logged from enrollment", cap.lines.some((l) => l.startsWith("EMAIL_SEQ_STEP_RETRY email=d***@example.com")), cap.lines);

  mailStatus = 202;
  await sql(env, "UPDATE subscribers SET next_send_at = ?1 WHERE email = 'd@example.com'").bind(new Date(Date.now() - 1000).toISOString()).run();
  const t = await runTick(env);
  const s2 = await sql(env, "SELECT sequence_step, step_attempts FROM subscribers WHERE email = 'd@example.com'").first();
  check("tick retries step 0 successfully -> step 1, attempts 0", t.sequence_sent === 1 && s2.sequence_step === 1 && s2.step_attempts === 0, { t, s2 });

  const r2 = await enrollSubscriber(env, { email: "e@example.com", source: "lead" });
  const s3 = await sql(env, "SELECT sequence_step, step_attempts FROM subscribers WHERE email = 'e@example.com'").first();
  check("healthy enrollment unchanged: step 0 sent, advanced to 1", r2.sent === true && s3.sequence_step === 1 && s3.step_attempts === 0, { r2, s3 });
}

done();
