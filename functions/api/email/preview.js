// Render any email in the browser, no auth, no database: the design proof and
// the copy-review tool. The copy shipped here is already public the moment it
// is sent, so there is nothing to protect.
//
//   /api/email/preview                          sequence step 0, sell voice
//   /api/email/preview?step=2&mode=buy          any step, any voice
//   /api/email/preview?seq=newsletter-welcome-v1
//   /api/email/preview?kind=update              sample 1:1 buyer progress update
//   &first=Sam&city=Irvine                      personalization overrides

import { renderEmail, paragraphsToHtml, personalize, escapeHtml } from "../../_lib/email.js";
import { getSequence } from "../../_lib/sequence.js";

const MODES = { sell: "Home Valuation", buy: "Home Purchase", neutral: "" };

const UPDATE_SAMPLE = {
  subject: "Escrow update: inspection cleared, appraisal ordered",
  preheader: "Day 9 of 30. On schedule.",
  headline: "Inspection cleared. We're on schedule.",
  paragraphs: [
    "Quick update on 123 Alder Street, day 9 of a 30-day escrow.",
    "**Done:** offer accepted, deposit wired, inspection completed and cleared with zero repair requests.",
    "**This week:** the appraisal is ordered for Thursday morning. I'll have the report back within 48 hours of the visit.",
    "**You:** nothing needed from you right now. Your next signature comes with the loan documents, about ten days out.",
    "Questions in the meantime? Reply here or call me directly."
  ],
  ctaLabel: "See what happens next",
  ctaUrl: "https://drozq.com/process/"
};

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const sub = {
    first_name: url.searchParams.get("first") || "Sam",
    city: url.searchParams.get("city") || "Irvine",
    intent: MODES[url.searchParams.get("mode") || "sell"] ?? ""
  };

  let subject, r;
  if (url.searchParams.get("kind") === "update") {
    subject = UPDATE_SAMPLE.subject;
    r = UPDATE_SAMPLE;
  } else {
    const seq = getSequence(url.searchParams.get("seq") || "lead-response-v1");
    if (!seq) return new Response("Unknown sequence", { status: 404 });
    const step = seq.steps[Number(url.searchParams.get("step")) || 0];
    if (!step) return new Response("Unknown step", { status: 404 });
    subject = personalize(step.subject(sub), sub);
    r = step.render(sub);
  }

  const html = renderEmail({
    subject,
    preheader: personalize(r.preheader || "", sub),
    headline: escapeHtml(personalize(r.headline || "", sub)),
    bodyHtml: paragraphsToHtml((r.paragraphs || []).map((p) => personalize(p, sub))),
    ctaLabel: r.ctaLabel || "",
    ctaUrl: r.ctaUrl ? personalize(r.ctaUrl, sub) : "",
    unsubUrl: "https://drozq.com/api/email/unsubscribe",
    pixelUrl: "",
    postal: context.env.EMAIL_POSTAL_ADDRESS || ""
  });

  return new Response(html, {
    status: 200,
    headers: { "content-type": "text/html; charset=UTF-8", "cache-control": "no-store" }
  });
}
