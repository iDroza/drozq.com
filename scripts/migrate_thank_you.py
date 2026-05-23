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
    background: linear-gradient(180deg, #fbf8f4 0%, #ffffff 100%);
    padding: 96px 24px 56px;
    text-align: center;
  }
  @media (min-width: 768px) { .ty-hero { padding: 144px 32px 80px; } }
  .ty-hero__check {
    display: inline-flex; align-items: center; justify-content: center;
    width: 80px; height: 80px; border-radius: 50%; background: #0a801f;
    color: #fff; margin: 0 auto 28px; box-shadow: 0 14px 40px rgba(10,128,31,0.28);
  }
  .ty-hero__check svg { width: 44px; height: 44px; fill: none; stroke: #fff; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
  .ty-hero h1 {
    font-size: clamp(2rem, 5vw, 3rem); font-weight: 800; color: #1a1816;
    margin: 0 0 14px; letter-spacing: -0.5px; line-height: 1.1;
  }
  .ty-hero .ty-hero__sub {
    font-size: 17px; color: #3f4650; line-height: 1.6; max-width: 640px;
    margin: 0 auto;
  }
  @media (min-width: 768px) { .ty-hero .ty-hero__sub { font-size: 19px; } }

  .ty-body {
    background: #fff; padding: 56px 24px;
  }
  @media (min-width: 768px) { .ty-body { padding: 80px 32px; } }
  .ty-grid {
    max-width: 1000px; margin: 0 auto; display: grid;
    grid-template-columns: 1fr; gap: 32px;
  }
  @media (min-width: 900px) {
    .ty-grid { grid-template-columns: 1.2fr 1fr; gap: 48px; align-items: stretch; }
  }
  .ty-card {
    background: #fbf8f4; border: 1px solid #ece8e2; border-radius: 16px;
    padding: 32px; display: flex; flex-direction: column; gap: 14px;
  }
  @media (min-width: 768px) { .ty-card { padding: 40px; } }
  .ty-card__eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #d92228; margin: 0;
  }
  .ty-card h2 {
    font-size: clamp(1.375rem, 3vw, 1.875rem); font-weight: 800;
    color: #1a1816; margin: 0; line-height: 1.2;
  }
  .ty-card p { font-size: 16px; color: #3f4650; line-height: 1.65; margin: 0; }
  .ty-card p strong { color: #1a1816; }
  .ty-phone {
    display: inline-flex; align-items: center; gap: 12px;
    background: #d92228; color: #fff; padding: 14px 28px;
    border-radius: 9999px; text-decoration: none; font-weight: 700;
    font-size: 18px; letter-spacing: 0.3px; margin: 6px 0 4px;
    align-self: flex-start; transition: background 150ms;
  }
  .ty-phone:hover { background: #a92e2a; color: #fff; }
  .ty-phone svg { width: 20px; height: 20px; fill: currentColor; }
  .ty-card__fineprint {
    font-size: 13px; color: #6b6864; margin-top: 8px;
  }
  .ty-map {
    border-radius: 16px; overflow: hidden;
    min-height: 320px; height: 100%;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }
  .ty-map iframe { border: 0; width: 100%; height: 100%; min-height: 320px; display: block; }

  .ty-cta {
    background: #f2f0ef; padding: 56px 24px;
    text-align: center;
  }
  @media (min-width: 768px) { .ty-cta { padding: 80px 32px; } }
  .ty-cta__eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #d92228; margin: 0 0 12px;
  }
  .ty-cta h2 {
    font-size: clamp(1.5rem, 3.5vw, 2rem); font-weight: 800;
    color: #1a1816; margin: 0 0 14px; letter-spacing: -0.3px;
  }
  .ty-cta p { font-size: 16px; color: #3f4650; line-height: 1.6; max-width: 560px; margin: 0 auto 28px; }
  .ty-cta__pill {
    max-width: 540px; margin: 0 auto;
    position: relative; display: flex; flex-direction: column;
    align-items: stretch; background: #fff; border-radius: 30px;
    box-shadow: 0 1px 5px rgba(0,0,0,0.11); overflow: hidden;
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
  <div class="ty-hero__check" aria-hidden="true">
    <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
  </div>
  <h1>Got it. Thanks.</h1>
  <p class="ty-hero__sub">I review every request personally. You will hear from me within the hour during business hours, or first thing the next morning if it is late.</p>
</section>

<section class="ty-body">
  <div class="ty-grid">

    <div class="ty-card">
      <p class="ty-card__eyebrow">Next Steps</p>
      <h2>Want to skip the wait?</h2>
      <p>I work with a limited number of sellers at a time so I can give each client my full attention. If your situation is time-sensitive, the fastest path is a direct call.</p>
      <a class="ty-phone" href="tel:9494385948">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6.62 10.79a15.05 15.05 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24 11.36 11.36 0 003.58.57 1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1 11.36 11.36 0 00.57 3.58 1 1 0 01-.24 1.01l-2.2 2.2z"/>
        </svg>
        (949) 438-5948
      </a>
      <p class="ty-card__fineprint">Or reply to the email I send within 24 hours and we will set a time.</p>
      <p>While you wait: read a <a href="/testimonials/" style="color:#d92228;font-weight:700;text-decoration:underline">recent case file</a> to see how a real Drozq transaction breaks down, numbers and all.</p>
    </div>

    <div class="ty-map">
      <iframe
        src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3000!2d-117.8473843!3d33.6860012!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x80dcdf8dbfbe3395%3A0xc09c886b39a043c2!2sJoshua%20Guerrero%20-%20Realtor!5e0!3m2!1sen!2sus!4v1"
        allowfullscreen=""
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
        title="Joshua Guerrero, REALTOR &mdash; Irvine office location on Google Maps">
      </iframe>
    </div>

  </div>
</section>

<section class="ty-cta">
  <p class="ty-cta__eyebrow">Need to send another address?</p>
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
</section>

<script>
  // Conversion gate (preserved verbatim from legacy /thank-you/).
  // Only push lead_confirmed (and the GA4 generate_lead it backs) when this
  // thank-you view is the result of a real funnel submit. The funnel sets
  // sessionStorage.drozq_lead_just_submitted = "1" right before redirecting
  // here; we read + clear it so refreshes, direct visits, and bookmarks
  // DO NOT inflate Google Ads conversions.
  // GTM action item: change the generate_lead trigger from "Page View on
  // /thank-you/" to "Custom Event = lead_confirmed".
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
        title="Thanks &mdash; we got your request | Joshua Guerrero",
        description="Your home valuation request was received. Joshua Guerrero personally reviews every request and follows up within the hour.",
        canonical="/thank-you/",
        main_body_html=MAIN_BODY,
        og_title="Thanks &mdash; we got your request | Joshua Guerrero",
        og_description="Your home valuation request was received. Personal follow-up within the hour.",
        noindex=True,
    )
