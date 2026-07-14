// Backfill the living subscriber list. Two sources:
//
//   1. A POSTed people list (primary since 2026-07-13: the personal
//      FollowUpBoss account is cancelled, and the lead-alert emails in
//      Joshua's inbox are the richer record anyway):
//        { people: [{email, name?, first_name?, city?, street?, intent?,
//                    timeline?}, ...], dry_run?, enroll?, stagger_seconds? }
//   2. FollowUpBoss pull (legacy; used only when no people list is posted and
//      FOLLOWUPBOSS_API_KEY is set): { dry_run?, enroll?, stagger_seconds?,
//      max_pages? }
//
// Common options: dry_run defaults TRUE (set false to actually enroll);
// enroll=true schedules the lead-response sequence from step 0, staggered
// inside the send window; enroll=false imports to the list only. Existing
// subscribers and unsubscribed addresses are never touched.

import { json, adminGate } from "../../_lib/admin.js";
import { validEmail, fetchWithTimeout } from "../../_lib/email.js";
import { enrollSubscriber } from "../../_lib/enroll.js";

function intentFromTags(tags) {
  const t = (tags || []).map((x) => String(x).toLowerCase());
  if (t.includes("seller")) return "Home Valuation";
  if (t.includes("buyer")) return "Home Purchase";
  return null;
}

export async function onRequestPost(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env, request } = context;

  try {
    let body = {};
    try { body = await request.json(); } catch (e) {}
    const dryRun = body.dry_run !== false;
    const enroll = body.enroll !== false;
    const stagger = Math.max(30, Number(body.stagger_seconds) || 240);
    const maxPages = Math.min(50, Number(body.max_pages) || 20);

    const people = [];
    if (Array.isArray(body.people)) {
      // Source 1: caller-provided list (parsed lead alerts, CSV export, etc.)
      for (const p of body.people) {
        people.push({
          emails: [{ value: p.email }],
          firstName: p.first_name || null,
          name: p.name || null,
          addresses: [{ city: p.city || null, street: p.street || null }],
          tags: [],
          _intent: p.intent || null,
          _timeline: p.timeline || null
        });
      }
    } else {
      // Source 2: FollowUpBoss pull.
      if (!env.FOLLOWUPBOSS_API_KEY) return json({ ok: false, error: "followupboss_key_missing" }, 503);
      const auth = "Basic " + btoa(env.FOLLOWUPBOSS_API_KEY + ":");
      for (let page = 0; page < maxPages; page++) {
      const r = await fetchWithTimeout(
        "https://api.followupboss.com/v1/people?limit=100&offset=" + (page * 100),
        { headers: { "Authorization": auth, "Accept": "application/json", "X-System": "Drozq.com" } },
        10000
      );
      if (!r.ok) {
        const t = await r.text().catch(() => "");
        // 503, not 502: Cloudflare's edge replaces 502 bodies with its generic
        // error page, which hides this diagnostic from the caller.
        console.error("EMAIL_BACKFILL_FUB_FETCH_FAILED status=" + r.status + " body=" + t.slice(0, 300));
        return json({ ok: false, error: "fub_fetch_failed", status: r.status, body: t.slice(0, 300) }, 503);
      }
      const data = await r.json();
      const batch = (data && data.people) || [];
      people.push(...batch);
      if (batch.length < 100) break;
      }
    }

    const candidates = [];
    const seen = new Set();
    for (const p of people) {
      const email = String(((p.emails || [])[0] || {}).value || "").trim().toLowerCase();
      if (!validEmail(email) || /@drozq\.com$/i.test(email)) continue;
      if (seen.has(email)) continue;
      seen.add(email);
      candidates.push({
        email,
        first_name: p.firstName || null,
        name: p.name || [p.firstName, p.lastName].filter(Boolean).join(" ") || null,
        city: (((p.addresses || [])[0] || {}).city) || null,
        street: (((p.addresses || [])[0] || {}).street) || null,
        intent: p._intent || intentFromTags(p.tags),
        timeline: p._timeline || null,
        source: "backfill"
      });
    }

    if (dryRun) {
      return json({
        ok: true, dry_run: true, fetched: people.length, candidates: candidates.length,
        sample: candidates.slice(0, 8).map((c) => c.email),
        note: "POST {\"dry_run\": false} to enroll. Sends start inside the next 9:30am-7pm PT window, one every " + stagger + "s."
      });
    }

    let inserted = 0, existing = 0;
    const start = Date.now() + 60000;
    for (let i = 0; i < candidates.length; i++) {
      const seed = candidates[i];
      const res = await enrollSubscriber(
        env, seed,
        enroll ? { startAtMs: start + inserted * stagger * 1000 } : { idle: true }
      ).catch(() => ({ inserted: false }));
      if (res.inserted) inserted++; else existing++;
    }

    console.log("EMAIL_BACKFILL fetched=" + people.length + " inserted=" + inserted + " existing=" + existing + " enroll=" + enroll);
    return json({ ok: true, fetched: people.length, candidates: candidates.length, inserted, existing_or_skipped: existing, enrolled: enroll, stagger_seconds: stagger });
  } catch (e) {
    console.error("EMAIL_BACKFILL_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}
