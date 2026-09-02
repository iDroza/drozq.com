// GET|POST /api/fello/engagement : the Fello lead-score readback (step 4 of
// notes/fello/fello-api-brief.md). Admin only (Bearer EMAIL_SECRET, the same
// gate as /api/email/*), because the response names leads.
//
// The site already knows every lead by email (D1 `subscribers`, source
// "lead"). For the newest N of them (default 100, last 90 days) this reads
// the Fello contact (GET /contact?emailId=, 5 at a time, well inside the
// 100-per-10-seconds app limit), ranks them (hot: a dashboard or email click
// inside 7 days; warm: a view; then newest activity; then lead score) and,
// when FOLLOWUPBOSS_API_KEY is set, decorates the hot + warm ones with the
// Fello-fed custom fields on their Follow Up Boss person (home value, equity,
// mortgage: whatever the native Fello -> FUB sync has been mapped to write).
//
// Result is cached in D1 for 8 minutes (`fello_engagement_cache`) so the
// dashboard worker's 10-minute cron and the CLI share one Fello sweep.
//   ?days=90 ?limit=100 ?fresh=1 (bypass the cache) ?hotDays=7
//
// Response: { ok, generatedAt, cached, summary: { leadsChecked, matched, hot,
// warm, avgLeadScore, hotWindowDays }, leads: [ { email, name, phone,
// leadScore, hot, warm, lastActivityAt, lastClickAt, dashboardClicks,
// emailClicks, dashboardViews, emailOpens, signals[], properties[],
// intent, city, createdAt, crm: { fubId, fields{} } | null } ] }

import { json, adminGate } from "../../_lib/admin.js";
import { fetchWithTimeout } from "../../_lib/email.js";
import { felloReady, felloGetContact, summarizeFelloContact } from "../../_lib/fello.js";

const CACHE_TABLE = "CREATE TABLE IF NOT EXISTS fello_engagement_cache (id TEXT PRIMARY KEY, generated_at TEXT NOT NULL, body TEXT NOT NULL)";
const CACHE_TTL_MS = 8 * 60 * 1000;
const CONCURRENCY = 5;
const FUB_BASE = "https://api.followupboss.com/v1";

function clampInt(v, def, min, max) {
  const n = parseInt(String(v == null ? "" : v), 10);
  if (!Number.isFinite(n)) return def;
  return Math.min(max, Math.max(min, n));
}

async function mapLimit(items, limit, fn) {
  const out = new Array(items.length);
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const idx = i++;
      out[idx] = await fn(items[idx], idx);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return out;
}

// Custom fields the Fello -> FUB sync writes carry Fello's names; surface every
// custom* key that looks like value / equity / mortgage / Fello, whatever the
// mapping was called, so this needs no reconfiguration when Joshua maps more.
export function pickFelloFubFields(person) {
  const out = {};
  if (!person || typeof person !== "object") return out;
  for (const [k, v] of Object.entries(person)) {
    if (!/^custom/i.test(k)) continue;
    if (v == null || v === "") continue;
    if (/fello|value|avm|equity|mortgage|loan|balance|rate|score|intent|signal|ownership|owner/i.test(k)) out[k] = v;
  }
  return out;
}

async function fubPersonFields(env, email) {
  try {
    const r = await fetchWithTimeout(FUB_BASE + "/people?email=" + encodeURIComponent(email) + "&limit=1&fields=allFields", {
      headers: { "Authorization": "Basic " + btoa(env.FOLLOWUPBOSS_API_KEY + ":"), "Accept": "application/json", "X-System": "Drozq.com" }
    }, 8000);
    if (!r.ok) return null;
    const d = await r.json().catch(() => null);
    const p = d && Array.isArray(d.people) && d.people[0];
    if (!p || !p.id) return null;
    return { fubId: p.id, stage: p.stage || null, fields: pickFelloFubFields(p) };
  } catch (e) {
    return null;
  }
}

export async function buildEngagement(env, opts) {
  const o = opts || {};
  const days = clampInt(o.days, 90, 1, 3650);
  const limit = clampInt(o.limit, 100, 1, 300);
  const hotDays = clampInt(o.hotDays, 7, 1, 90);
  const now = Date.now();
  const since = new Date(now - days * 86400000).toISOString().replace("T", " ").slice(0, 19);

  const rows = (await env.EMAIL_DB.prepare(
    "SELECT email, name, first_name, intent, city, street, timeline, created_at FROM subscribers " +
    "WHERE source != 'newsletter' AND status != 'unsubscribed' AND created_at >= ?1 " +
    "ORDER BY created_at DESC LIMIT ?2"
  ).bind(since, limit).all()).results || [];

  let felloErrors = 0;
  const leads = await mapLimit(rows, CONCURRENCY, async (row) => {
    const base = {
      email: row.email, name: row.name || row.first_name || null, phone: null, intent: row.intent || null,
      city: row.city || null, street: row.street || null, timeline: row.timeline || null, createdAt: row.created_at || null,
      matched: false, leadScore: null, hot: false, warm: false, lastActivityAt: null, lastClickAt: null,
      dashboardClicks: 0, emailClicks: 0, dashboardViews: 0, emailOpens: 0, formSubmissions: 0, signals: [], properties: [], rank: 0, crm: null
    };
    const got = await felloGetContact(env, row.email);
    if (got.status === 404) return base;
    if (!got.ok || !got.data) { felloErrors++; return base; }
    const s = summarizeFelloContact(got.data, now, hotDays);
    return Object.assign(base, s, { matched: true, name: s.name || base.name, contactId: s.contactId });
  });

  leads.sort((a, b) => (b.rank - a.rank) || String(b.createdAt || "").localeCompare(String(a.createdAt || "")));

  if (env.FOLLOWUPBOSS_API_KEY) {
    const decorate = leads.filter((l) => l.matched && (l.hot || l.warm)).slice(0, 25);
    await mapLimit(decorate, 4, async (l) => { l.crm = await fubPersonFields(env, l.email); });
  }

  const matched = leads.filter((l) => l.matched);
  const scored = matched.filter((l) => typeof l.leadScore === "number");
  const summary = {
    leadsChecked: leads.length,
    matched: matched.length,
    hot: matched.filter((l) => l.hot).length,
    warm: matched.filter((l) => l.warm).length,
    avgLeadScore: scored.length ? Math.round((scored.reduce((a, l) => a + l.leadScore, 0) / scored.length) * 10) / 10 : null,
    hotWindowDays: hotDays,
    windowDays: days,
    felloErrors
  };
  for (const l of leads) delete l.rank;
  return { ok: true, generatedAt: new Date(now).toISOString(), cached: false, summary, leads };
}

async function readCache(env, key) {
  try {
    await env.EMAIL_DB.prepare(CACHE_TABLE).run();
    const row = await env.EMAIL_DB.prepare("SELECT generated_at, body FROM fello_engagement_cache WHERE id = ?1").bind(key).first();
    if (!row) return null;
    if (Date.now() - Date.parse(row.generated_at) > CACHE_TTL_MS) return null;
    const parsed = JSON.parse(row.body);
    parsed.cached = true;
    return parsed;
  } catch (e) { return null; }
}

async function writeCache(env, key, payload) {
  try {
    await env.EMAIL_DB.prepare(CACHE_TABLE).run();
    await env.EMAIL_DB.prepare(
      "INSERT INTO fello_engagement_cache (id, generated_at, body) VALUES (?1, ?2, ?3) ON CONFLICT(id) DO UPDATE SET generated_at = excluded.generated_at, body = excluded.body"
    ).bind(key, payload.generatedAt, JSON.stringify(payload)).run();
  } catch (e) {}
}

async function handle(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env, request } = context;
  if (!felloReady(env)) return json({ ok: false, error: "fello_api_key_missing" }, 503);
  const url = new URL(request.url);
  const q = (k) => url.searchParams.get(k);
  const opts = { days: q("days"), limit: q("limit"), hotDays: q("hotDays") };
  const key = "v1:" + clampInt(opts.days, 90, 1, 3650) + ":" + clampInt(opts.limit, 100, 1, 300) + ":" + clampInt(opts.hotDays, 7, 1, 90);
  if (q("fresh") !== "1") {
    const hit = await readCache(env, key);
    if (hit) return json(hit);
  }
  try {
    const payload = await buildEngagement(env, opts);
    await writeCache(env, key, payload);
    console.log("FELLO_ENGAGEMENT checked=" + payload.summary.leadsChecked + " matched=" + payload.summary.matched + " hot=" + payload.summary.hot + " errors=" + payload.summary.felloErrors);
    return json(payload);
  } catch (e) {
    console.error("FELLO_ENGAGEMENT_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}

export const onRequestGet = handle;
export const onRequestPost = handle;
