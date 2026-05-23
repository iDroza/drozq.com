"""Migrate /testimonials/ (case-file index) to the homepage template scaffold.

Content-first treatment, with the cf-* design system scoped inside <main>:
hero + aggregate stats strip + 3-card case file grid + closing CTA.

Closing CTA replaces the legacy "Book a 15-minute call" link to /contact/
with an inline funnel-opening Sell-mode pill, per the always-inline directive.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page
from _case_file_shared import CF_STYLE_BLOCK, cta_pill


HERO = """
<section class="cf-hero cf-index-hero">
  <div class="cf-hero__inner" style="text-align:center;">
    <div class="cf-label">Case Files</div>
    <h1>Real deals. Real numbers. Real leverage.</h1>
    <p class="cf-index-hero__sub">Every client comes in with a different goal. A first home, an investment, a strategic entry, a move up. Here is how we execute on those goals, one deal at a time. Every case file is a real transaction with real numbers. We anonymize the clients because discretion is part of the service.</p>
  </div>
</section>
"""

STATS = """
<section class="cf-stats-strip">
  <div class="cf-stats-strip__inner cf-reveal">
    <div class="cf-label cf-stats-strip__label">The Numbers, So Far</div>
    <div class="cf-stats-strip__grid">

      <div class="cf-stats-strip__item">
        <!-- UPDATE AS NEW CASE FILES ARE ADDED -->
        <span class="cf-stats-strip__number">$43,250</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Total client savings</div>
      </div>

      <div class="cf-stats-strip__item">
        <!-- UPDATE AS NEW CASE FILES ARE ADDED -->
        <span class="cf-stats-strip__number">2</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Homes closed</div>
      </div>

      <div class="cf-stats-strip__item">
        <!-- UPDATE AS NEW CASE FILES ARE ADDED -->
        <span class="cf-stats-strip__number">2</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Closed ahead of schedule</div>
      </div>

      <div class="cf-stats-strip__item">
        <!-- UPDATE AS NEW CASE FILES ARE ADDED -->
        <span class="cf-stats-strip__number">23</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Properties toured</div>
      </div>

    </div>
  </div>
</section>
"""

CARDS = """
<section class="cf-index-section">
  <div class="cf-label cf-index-section__label">The Case Files</div>
  <div class="cf-index-grid cf-reveal">

    <a class="cf-card" href="/testimonials/001-long-beach-firefighter/" aria-label="Read Case File 001: Long Beach firefighter, first-time buyer">
      <span class="cf-card__tab">Case File 001</span>
      <p class="cf-card__meta">Long Beach &middot; First-Time Buyer</p>
      <h2 class="cf-card__headline">He spends his career protecting other people's homes. We helped him acquire his first.</h2>
      <div class="cf-card__stat">
        <span class="cf-card__stat-value">$23,250</span>
        <span class="cf-card__stat-label">Seller credit negotiated</span>
      </div>
    </a>

    <a class="cf-card" href="/testimonials/002-corona-analyst/" aria-label="Read Case File 002: Corona financial analyst, strategic purchase">
      <span class="cf-card__tab">Case File 002</span>
      <p class="cf-card__meta">Corona &middot; Strategic Purchase</p>
      <h2 class="cf-card__headline">He analyzes numbers for the State of California. Then he ran the numbers on us.</h2>
      <div class="cf-card__stat">
        <span class="cf-card__stat-value">$20,000</span>
        <span class="cf-card__stat-label">Saved off asking price</span>
      </div>
    </a>

    <div class="cf-card cf-card--soon" aria-hidden="true">
      <span class="cf-card__tab">Case File 003</span>
      <h2 class="cf-card__headline">Currently in escrow</h2>
      <p class="cf-card__escrow-sub">Details coming soon</p>
    </div>

  </div>
</section>
"""

CTA = f"""
<section class="cf-cta-strip">
  <div class="cf-narrow">
    <div class="cf-label">What's Next</div>
    <h2>Want your deal to be the next case file?</h2>
    <p class="cf-cta-strip__sub">Most clients find us right here. They read a case file, see themselves in it, and start the conversation. If that is you, drop your address.</p>
    {cta_pill()}
  </div>
</section>
"""


MAIN_BODY = CF_STYLE_BLOCK + HERO + STATS + CARDS + CTA


if __name__ == "__main__":
    scaffold_page(
        target="testimonials/index.html",
        title="Case Files | Real Drozq Deals, Real Numbers | Joshua Guerrero",
        description="Every Drozq transaction documented: real numbers, real negotiation, real outcome. Read the case files before you reach out.",
        canonical="/testimonials/",
        main_body_html=MAIN_BODY,
        og_title="Case Files | Joshua Guerrero, Real Brokerage",
        og_description="Real deals, real numbers. Drozq case files document every transaction.",
    )
