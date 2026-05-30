"""Migrate /thank-you/ to the homepage template scaffold.

This page is the post-submit landing page. It is conversion-CRITICAL because
the GA4 generate_lead event (and the Google Ads conversion riding on it) is
gated by the lead_confirmed dataLayer event fired from this page.

Preserved verbatim from the legacy /thank-you/:
  1. The conversion-gate IIFE that reads sessionStorage.drozq_lead_just_submitted,
     pushes lead_confirmed to dataLayer with funnel_mode metadata, and strips
     ?ref=funnel from the URL via history.replaceState.
  2. The Irvine office Google Maps embed.

Replaced:
  - Brand-mode mint hero / scoped CSS / navy footer / 510-935-5701 phone.
  - Now uses homepage scaffold + minimal conversion footer + 949 phone +
    scoped 'thankyou-*' styles for the celebration card.

noindex,follow per legal/operational page convention.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page


MAIN_BODY = """
<style>
  /* Scoped styles for /thank-you/. Inline only; no Panda layer pollution. */
  .ty-hero {
    position: relative;
    background: #f2f0ef;
    color: #1a1816; padding: 112px 24px 80px; text-align: center;
    overflow: hidden;
  }
  @media (min-width: 768px) { .ty-hero { padding: 152px 32px 104px; } }
  .ty-hero__inner { position: relative; z-index: 1; max-width: 760px; margin: 0 auto; }
  .ty-hero__badge {
    display: inline-flex; align-items: center; gap: 10px;
    background: #fff; border: 1px solid #e5e5e5;
    padding: 8px 16px 8px 8px; border-radius: 9999px;
    margin-bottom: 28px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }
  .ty-hero__check {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%; background: #0a801f;
    color: #fff; flex-shrink: 0;
  }
  .ty-hero__check svg { width: 16px; height: 16px; fill: none; stroke: #fff; stroke-width: 3.5; stroke-linecap: round; stroke-linejoin: round; }
  .ty-hero__badge-text {
    font-size: 12px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #1a1816;
  }
  .ty-hero h1 {
    font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 800; color: #1a1816;
    margin: 0 0 18px; letter-spacing: -1px; line-height: 1.02;
  }
  .ty-hero__sub {
    font-size: 18px; color: #3f4650; line-height: 1.6;
    max-width: 600px; margin: 0 auto;
  }
  @media (min-width: 768px) { .ty-hero__sub { font-size: 20px; } }

  /* Timeline strip */
  .ty-timeline {
    background: #fff; padding: 48px 24px;
    border-bottom: 1px solid #ece8e2;
  }
  @media (min-width: 768px) { .ty-timeline { padding: 64px 32px; } }
  .ty-timeline__grid {
    max-width: 1000px; margin: 0 auto;
    display: grid; grid-template-columns: 1fr; gap: 20px;
  }
  @media (min-width: 720px) {
    .ty-timeline__grid { grid-template-columns: repeat(3, 1fr); gap: 24px; }
  }
  .ty-step {
    position: relative; padding: 28px;
    background: #fbf8f4; border: 1px solid #ece8e2; border-radius: 16px;
  }
  .ty-step__when {
    display: inline-block; font-size: 11px; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; color: #d92228;
    background: #fdecec; padding: 4px 10px; border-radius: 9999px;
    margin-bottom: 14px;
  }
  .ty-step--now .ty-step__when { color: #fff; background: #0a801f; }
  .ty-step h3 {
    font-size: 18px; font-weight: 800; color: #1a1816;
    margin: 0 0 8px; line-height: 1.25;
  }
  .ty-step p { font-size: 14px; color: #3f4650; line-height: 1.55; margin: 0; }
  .ty-step__icon {
    position: absolute; top: 28px; right: 28px;
    width: 28px; height: 28px; color: #d92228; opacity: 0.5;
  }
  .ty-step--now .ty-step__icon { color: #0a801f; opacity: 0.85; }
  .ty-step__icon svg { width: 100%; height: 100%; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

  .ty-body {
    background: #f7f5f1; padding: 64px 24px;
  }
  @media (min-width: 768px) { .ty-body { padding: 96px 32px; } }
  .ty-grid {
    max-width: 1000px; margin: 0 auto; display: grid;
    grid-template-columns: 1fr; gap: 24px;
  }
  @media (min-width: 900px) {
    .ty-grid { grid-template-columns: 1.15fr 1fr; gap: 32px; align-items: stretch; }
  }
  .ty-card {
    background: #fff; border-radius: 20px; padding: 36px;
    box-shadow: 0 8px 32px rgba(26,24,22,0.06);
    display: flex; flex-direction: column; gap: 16px;
  }
  @media (min-width: 768px) { .ty-card { padding: 44px; } }
  .ty-card__eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #d92228; margin: 0;
  }
  .ty-card h2 {
    font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 800;
    color: #1a1816; margin: 0; line-height: 1.15; letter-spacing: -0.5px;
  }
  .ty-card p { font-size: 16px; color: #3f4650; line-height: 1.65; margin: 0; }
  .ty-card p strong { color: #1a1816; }
  .ty-phone {
    display: inline-flex; align-items: center; justify-content: center; gap: 14px;
    background: #d92228; color: #fff; padding: 20px 32px;
    border-radius: 9999px; text-decoration: none; font-weight: 800;
    font-size: 24px; letter-spacing: -0.3px; margin: 12px 0 4px;
    box-shadow: 0 12px 32px rgba(217,34,40,0.32);
    transition: background 150ms, transform 150ms;
  }
  .ty-phone:hover { background: #a92e2a; color: #fff; transform: translateY(-2px); }
  .ty-phone svg { width: 26px; height: 26px; fill: currentColor; flex-shrink: 0; }
  .ty-card__fineprint { font-size: 13px; color: #6b6864; margin-top: 6px; }

  .ty-casefile {
    margin-top: 8px; padding: 20px; border-radius: 12px;
    background: linear-gradient(135deg, #fbf8f4 0%, #f2f0ef 100%);
    border: 1px solid #ece8e2; text-decoration: none; color: inherit;
    display: block; transition: transform 150ms, box-shadow 150ms;
  }
  .ty-casefile:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,0.08); }
  .ty-casefile__eyebrow {
    font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #d92228; margin: 0 0 8px;
  }
  .ty-casefile__stat {
    font-size: 28px; font-weight: 800; color: #d92228;
    letter-spacing: -0.5px; margin: 0; line-height: 1;
  }
  .ty-casefile__label {
    font-size: 13px; font-weight: 600; color: #1a1816;
    margin: 6px 0 0; line-height: 1.3;
  }
  .ty-casefile__arrow {
    font-size: 12px; color: #6b6864; margin: 10px 0 0;
    display: inline-flex; align-items: center; gap: 6px;
  }

  .ty-map {
    border-radius: 20px; overflow: hidden;
    min-height: 360px; height: 100%;
    box-shadow: 0 8px 32px rgba(26,24,22,0.06);
  }
  .ty-map iframe { border: 0; width: 100%; height: 100%; min-height: 360px; display: block; }

  .ty-cta {
    background: #f2f0ef; color: #1a1816; padding: 72px 24px; text-align: center;
  }
  @media (min-width: 768px) { .ty-cta { padding: 96px 32px; } }
  .ty-cta__eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #d92228; margin: 0 0 12px;
  }
  .ty-cta h2 {
    font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 800;
    color: #1a1816; margin: 0 0 14px; letter-spacing: -0.5px;
  }
  .ty-cta p { font-size: 16px; color: #3f4650; line-height: 1.6; max-width: 560px; margin: 0 auto 28px; }
  .ty-cta__pill {
    max-width: 540px; margin: 0 auto;
    position: relative; display: flex; flex-direction: column;
    align-items: stretch; background: #fff; border-radius: 30px;
    box-shadow: 0 1px 5px rgba(0,0,0,0.11); border: 1px solid #e5e5e5; overflow: hidden;
  }
  @media (min-width: 560px) {
    .ty-cta__pill { flex-direction: row; align-items: center; }
  }
  .ty-cta__pill input[name="location"] {
    flex: 1; height: 56px; padding: 0 24px; border: none;
    background: transparent; font-size: 16px; color: #1a1816;
    outline: none; font-family: inherit;
  }
  .ty-cta__pill button[type="submit"] {
    height: 48px; margin: 4px; padding: 0 28px;
    background: #d92228; color: #fff; border: none; cursor: pointer;
    border-radius: 9999px; font-size: 16px; font-weight: 700;
    letter-spacing: 0.3px; font-family: inherit;
  }
  .ty-cta__pill button[type="submit"]:hover { background: #a92e2a; }
</style>

<section class="ty-hero">
  <div class="ty-hero__inner">
    <div class="ty-hero__badge">
      <span class="ty-hero__check" aria-hidden="true">
        <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
      </span>
      <span class="ty-hero__badge-text">Request received</span>
    </div>
    <h1>Now we get to work.</h1>
    <p class="ty-hero__sub">I review every request personally. Expect to hear from me within the hour during business hours, or first thing the next morning if it is late.</p>
  </div>
</section>

<section class="ty-timeline">
  <div class="ty-timeline__grid">

    <div class="ty-step ty-step--now">
      <span class="ty-step__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
      </span>
      <span class="ty-step__when">Now</span>
      <h3>Your details are in.</h3>
      <p>I just received your request and your address is queued up on my desk.</p>
    </div>

    <div class="ty-step">
      <span class="ty-step__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      </span>
      <span class="ty-step__when">Within the hour</span>
      <h3>Personal first reply.</h3>
      <p>You hear from me directly, with a same-day timeline and any quick questions I need to pull accurate comps.</p>
    </div>

    <div class="ty-step">
      <span class="ty-step__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="15" y2="17"/></svg>
      </span>
      <span class="ty-step__when">Within 24 hours</span>
      <h3>Full CMA in your inbox.</h3>
      <p>Recent comps, active competition, recommended price range, and a clear pricing strategy. The real read on what your home is worth.</p>
    </div>

  </div>
</section>

<section class="ty-body">
  <div class="ty-grid">

    <div class="ty-card">
      <p class="ty-card__eyebrow">Want to talk first?</p>
      <h2>Skip the wait. Call me direct.</h2>
      <p>I work with a limited number of sellers at a time so each client gets my full attention. If your situation is time-sensitive, the fastest path is a direct call.</p>
      <a class="ty-phone" href="tel:9494385948">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6.62 10.79a15.05 15.05 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24 11.36 11.36 0 003.58.57 1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1 11.36 11.36 0 00.57 3.58 1 1 0 01-.24 1.01l-2.2 2.2z"/>
        </svg>
        (949) 438-5948
      </a>
      <p class="ty-card__fineprint">Or reply to the email I send within 24 hours and we will set a time.</p>

      <a class="ty-casefile" href="/testimonials/001-long-beach-firefighter/">
        <p class="ty-casefile__eyebrow">While you wait &middot; Case File 001</p>
        <p class="ty-casefile__stat">$23,250</p>
        <p class="ty-casefile__label">Seller credit negotiated for a Long Beach buyer. Real deal, real numbers.</p>
        <p class="ty-casefile__arrow">Read the case file &rarr;</p>
      </a>
    </div>

    <div class="ty-map">
      <iframe
        src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3000!2d-117.8473843!3d33.6860012!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x80dcdf8dbfbe3395%3A0xc09c886b39a043c2!2sJoshua%20Guerrero%20-%20Realtor!5e0!3m2!1sen!2sus!4v1"
        allowfullscreen=""
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
        title="Joshua Guerrero, REALTOR. Irvine office location on Google Maps">
      </iframe>
    </div>

  </div>
</section>

<section class="ty-cta">
  <p class="ty-cta__eyebrow">Another property on your radar?</p>
  <h2>Run another home through the funnel.</h2>
  <p>Selling and buying in the same window, or sending in an additional property for a friend or family member? Drop another address and I will treat it as its own file.</p>
  <div id="ty-cta-panel" role="tabpanel" aria-labelledby="tab-sell">
    <form class="pos_relative">
      <div class="ty-cta__pill">
        <input type="text" name="location" placeholder="Enter another address"
               autocomplete="off" aria-label="Enter another address">
        <button type="submit">Compare Agents</button>
      </div>
      <input type="hidden" name="gclid" value="">
    </form>
  </div>
  <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
</section>

<script>
  // Conversion gate (preserved verbatim from legacy /thank-you/).
  // Only push lead_confirmed (and the GA4 generate_lead it backs) when this
  // thank-you view is the result of a real funnel submit. The funnel sets
  // sessionStorage.drozq_lead_just_submitted = "1" right before redirecting
  // here; we read + clear it so refreshes, direct visits, and bookmarks
  // DO NOT inflate Google Ads conversions.
  // generate_lead now fires via a GTM "GA4 Event" tag bound to this
  // lead_confirmed dataLayer event. The old GA4 "Create event" rule that
  // synthesized generate_lead from every /thank-you/ page_view was removed
  // 2026-05-29, so this gate is the only source of the conversion.
  (function(){
    var flag = null;
    try { flag = sessionStorage.getItem("drozq_lead_just_submitted"); } catch (e) {}
    if (flag !== "1") return;
    var mode = "";
    try { mode = sessionStorage.getItem("drozq_lead_mode") || ""; } catch (e) {}
    try {
      sessionStorage.removeItem("drozq_lead_just_submitted");
      sessionStorage.removeItem("drozq_lead_mode");
    } catch (e) {}
    // Strip ?ref=funnel from the URL so a refresh or bookmark of the
    // resulting page does not carry a misleading attribution param.
    try {
      var url = new URL(location.href);
      if (url.searchParams.get("ref") === "funnel") {
        url.searchParams.delete("ref");
        history.replaceState({}, "", url.pathname + (url.search ? url.search : "") + url.hash);
      }
    } catch (e) {}
    (window.dataLayer = window.dataLayer || []).push({
      event: "lead_confirmed",
      funnel_mode: mode || "unknown"
    });
  })();
</script>
"""

if __name__ == "__main__":
    scaffold_page(
        target="thank-you/index.html",
        title="Thanks for reaching out | Drozq",
        description="Your home valuation request was received. Joshua Guerrero personally reviews every request and follows up within the hour.",
        canonical="/thank-you/",
        main_body_html=MAIN_BODY,
        og_title="Thanks for reaching out | Drozq",
        og_description="Your home valuation request was received. Personal follow-up within the hour.",
        noindex=True,
    )
