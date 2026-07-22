// Campaign broadcast: queue one templated email to a segment of the list. The
// cron tick drains the queue on a stagger so sends look human and stay inside
// rate limits. POST with Authorization: Bearer EMAIL_SECRET and JSON:
// {
//   subject, headline?, paragraphs: [...], preheader?, cta_label?, cta_url?,
//   segment?  "all" (default) | "leads" | "newsletter",
//   slug?     campaign identifier (default derived from time),
//   stagger_seconds? (default 90), dry_run? (default false)
// }
// {first} and {city} in subject/paragraphs personalize per subscriber.

import { json, adminGate } from "../../_lib/admin.js";
import { windowedISO } from "../../_lib/email.js";

const SEGMENT_WHERE = {
  all: "status = 'active'",
  leads: "status = 'active' AND source IN ('lead', 'backfill')",
  newsletter: "status = 'active' AND source IN ('newsletter', 'field-notes-subscribe')"
};

export async function onRequestPost(context) {
  const gate = adminGate(context);
  if (gate) return gate;
  const { env, request } = context;

  try {
    const body = await request.json();
    if (!body.subject || !Array.isArray(body.paragraphs) || body.paragraphs.length === 0) {
      return json({ ok: false, error: "subject_and_paragraphs_required" }, 400);
    }
    const segment = String(body.segment || "all");
    const where = SEGMENT_WHERE[segment];
    if (!where) return json({ ok: false, error: "unknown_segment", segments: Object.keys(SEGMENT_WHERE) }, 400);

    const recipients = await env.EMAIL_DB.prepare(
      "SELECT id, email FROM subscribers WHERE " + where + " ORDER BY id"
    ).all();
    const rows = recipients.results || [];

    if (body.dry_run === true) {
      return json({ ok: true, dry_run: true, segment, recipients: rows.length, sample: rows.slice(0, 5).map((r) => r.email) });
    }
    if (rows.length === 0) return json({ ok: true, queued: 0, segment, note: "no active recipients in segment" });

    const slug = String(body.slug || "campaign-" + new Date().toISOString().slice(0, 16).replace(/[:T]/g, "-"));
    const payload = {
      preheader: body.preheader ? String(body.preheader) : "",
      headline: body.headline ? String(body.headline) : "",
      paragraphs: body.paragraphs.map(String),
      ctaLabel: body.cta_label ? String(body.cta_label) : "",
      ctaUrl: body.cta_url ? String(body.cta_url) : "",
      includeUnsub: true
    };

    const campaign = await env.EMAIL_DB.prepare(
      "INSERT INTO campaigns (slug, subject, payload, segment) VALUES (?1, ?2, ?3, ?4) RETURNING id"
    ).bind(slug, String(body.subject), JSON.stringify(payload), segment).first();

    const stagger = Math.max(5, Number(body.stagger_seconds) || 90);
    const start = Date.now();
    const inserts = rows.map((r, i) =>
      env.EMAIL_DB.prepare(
        "INSERT INTO email_log (subscriber_id, campaign_id, email, kind, ref, subject, status, send_after) VALUES (?1, ?2, ?3, 'broadcast', ?4, ?5, 'queued', ?6)"
      ).bind(r.id, campaign.id, r.email, slug, String(body.subject), windowedISO(start + i * stagger * 1000, env))
    );
    for (let i = 0; i < inserts.length; i += 50) {
      await env.EMAIL_DB.batch(inserts.slice(i, i + 50));
    }

    const last = new Date(start + (rows.length - 1) * stagger * 1000).toISOString();
    console.log("EMAIL_BROADCAST_QUEUED slug=" + slug + " segment=" + segment + " queued=" + rows.length);
    return json({ ok: true, campaign_id: campaign.id, slug, segment, queued: rows.length, first_send_at: new Date(start).toISOString(), last_send_at: last });
  } catch (e) {
    console.error("EMAIL_BROADCAST_THREW " + ((e && e.stack) || e));
    return json({ ok: false, error: String((e && e.message) || e) }, 500);
  }
}
