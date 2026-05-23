"""Migrate /testimonials/002-corona-analyst/ to the homepage scaffold.

Content-first with the cf-* design system. Preserves the full case file
narrative (Client / Mission / Search / Deal / Negotiation / Takeaway).
Case 002 has no "In His Words" section; the asymmetry vs case 001 is
intentional and preserved.

Changes from the legacy page:
- Replaced the "Book a 15-minute call" link to /contact/ with an inline
  funnel-opening Sell-mode pill, per the always-inline directive.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page
from _case_file_shared import CF_STYLE_BLOCK, COUNT_UP_AND_REVEAL_SCRIPT, cta_pill


CONDO_SVG = '<svg viewBox="0 0 100 100"><path fill-rule="evenodd" d="M12 14 L88 14 L88 92 L12 92 Z M28 26 L42 26 L42 40 L28 40 Z M58 26 L72 26 L72 40 L58 40 Z M28 48 L42 48 L42 62 L28 62 Z M58 48 L72 48 L72 62 L58 62 Z M28 70 L42 70 L42 84 L28 84 Z M58 70 L72 70 L72 84 L58 84 Z"/></svg>'
CONDOS = (
    "\n".join(f'<span class="cf-house" aria-hidden="true">{CONDO_SVG}</span>' for _ in range(8))
    + f'\n<span class="cf-house cf-house--match" aria-hidden="true">{CONDO_SVG}</span>'
)


HERO = """
<section class="cf-hero">
  <div class="cf-hero__inner">
    <div class="cf-label">Case File 002 &middot; Corona &middot; Strategic Purchase</div>
    <h1>He analyzes numbers for the State of California. Then he ran the numbers on us.</h1>
  </div>
  <div class="cf-hero__scroll" aria-hidden="true">Scroll</div>
</section>
"""

CLIENT = """
<section class="cf-section">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Client</div>
    <p class="cf-body">He's a financial analyst for the State of California. He doesn't make decisions emotionally. He makes them on spreadsheets. He wasn't looking for a forever home, he was looking for a strategic first position: a condo that would keep his monthly payment low, build equity quietly in the background, and set him up to trade into something larger down the road. The brief was clean. The execution had to match.</p>
    <div class="cf-badges">
      <span class="cf-badge">Strategic Buyer</span>
      <span class="cf-badge">Financial Analyst</span>
      <span class="cf-badge">Step-Up Strategy</span>
      <span class="cf-badge">Corona, CA</span>
    </div>
  </div>
</section>
"""

MISSION = """
<section class="cf-section cf-section--alt">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Mission</div>
    <p class="cf-body">The mandate was simple and unsentimental: lowest viable monthly payment, cleanest possible condo, smallest possible drama. No vanity square footage. No "stretch" pricing. Find the asset, win the negotiation, close on time, and position him to make the next move from a stronger seat.</p>
  </div>
</section>
"""

SEARCH = f"""
<section class="cf-section">
  <div class="cf-wide cf-reveal" style="text-align:center;">
    <div class="cf-label">The Search</div>
    <h2 class="cf-headline-stat">9 condos. One worth fighting for.</h2>

    <div class="cf-houses cf-houses--three" role="img" aria-label="Eight condos reviewed, one condo selected">
      {CONDOS}
    </div>

    <div style="max-width:680px; margin:0 auto;">
      <p class="cf-body">We toured 9 condos across Corona. Most were priced for the listing agent's optimism, not the market's reality. We weren't there to fall in love. We were there to find the one unit where the math worked, the building was sound, and the seller had a reason to move. The 9th checked every box.</p>
    </div>
  </div>
</section>
"""

DEAL = """
<section class="cf-section cf-section--alt">
  <div class="cf-wide cf-reveal">
    <div style="text-align:center;">
      <div class="cf-label">The Deal</div>
    </div>

    <div class="cf-hero-stat">
      <div class="cf-hero-stat__number" data-count-target="20000" data-count-prefix="$">$20,000</div>
      <div class="cf-hero-stat__label">Saved off asking price</div>
    </div>

    <div class="cf-grid">
      <div class="cf-grid__card">
        <div class="cf-grid__value">$370,000</div>
        <div class="cf-grid__label">Original list price</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">$350,000</div>
        <div class="cf-grid__label">Final purchase price</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">$75,000</div>
        <div class="cf-grid__label">Down payment</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value cf-grid__value--accent" aria-label="Yes">&#10003;</div>
        <div class="cf-grid__label">All requested repairs secured</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">Early</div>
        <div class="cf-grid__label">Closing timeline</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">9</div>
        <div class="cf-grid__label">Condos evaluated</div>
      </div>
    </div>

    <div class="cf-receipt" role="group" aria-label="Price negotiation breakdown">
      <div class="cf-receipt__title">Price Negotiation</div>
      <div class="cf-receipt__row">
        <span class="cf-receipt__label">Asking price</span>
        <span class="cf-receipt__amount">$370,000.00</span>
      </div>
      <div class="cf-receipt__row">
        <span class="cf-receipt__label">Final price</span>
        <span class="cf-receipt__amount">$350,000.00</span>
      </div>
      <div class="cf-receipt__row cf-receipt__row--total cf-receipt__row--accent">
        <span class="cf-receipt__label">Delta</span>
        <span class="cf-receipt__amount">&minus;$20,000.00</span>
      </div>
    </div>
  </div>
</section>
"""

NEGOTIATION = """
<section class="cf-section">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Negotiation</div>
    <p class="cf-body">The seller didn't want to budge. We didn't blink. We had inspection findings in hand, a buyer who had already walked from 8 other units, and a lender moving fast enough that we could credibly close in days, not weeks. That combination, real leverage plus real urgency, is what moves sellers off their number.</p>
    <p class="cf-body">They came down $20,000. Then they agreed to the repairs. Then we closed early.</p>
  </div>

  <div class="cf-wide cf-reveal">
    <div class="cf-compare">
      <div class="cf-compare__card cf-compare__card--muted">
        <div class="cf-compare__cap">Standard outcome</div>
        <div class="cf-compare__value">$5,000</div>
      </div>
      <div class="cf-compare__arrow" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none"><path d="M4 12h16m0 0l-6-6m6 6l-6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
      <div class="cf-compare__card cf-compare__card--hero">
        <div class="cf-compare__cap">With Josh</div>
        <div class="cf-compare__value">$20,000</div>
      </div>
    </div>
  </div>
</section>
"""

TAKEAWAY = f"""
<section class="cf-section cf-section--alt">
  <div class="cf-narrow cf-reveal cf-takeaway">
    <div class="cf-label">The Takeaway</div>
    <h2 class="cf-takeaway__headline">Lower price. Repairs handled. Early close. Position secured. No emotion. Just execution.</h2>
    <p class="cf-takeaway__sub">If you are approaching your first purchase as a strategic move rather than a milestone, drop your address below.</p>
    {cta_pill()}
    <div class="cf-takeaway__next">Case File 003 coming soon.</div>
  </div>
</section>
"""

CROSSLINK = """
<aside class="cf-crosslink">
  <span class="cf-crosslink__label">More Case Files</span>
  <nav class="cf-crosslink__nav" aria-label="More case files">
    <a href="/testimonials/">All case files</a>
    <span class="cf-crosslink__sep" aria-hidden="true">&middot;</span>
    <a href="/testimonials/001-long-beach-firefighter/">Case File 001 &middot; Long Beach</a>
  </nav>
</aside>
"""


MAIN_BODY = CF_STYLE_BLOCK + HERO + CLIENT + MISSION + SEARCH + DEAL + NEGOTIATION + TAKEAWAY + CROSSLINK + COUNT_UP_AND_REVEAL_SCRIPT


if __name__ == "__main__":
    scaffold_page(
        target="testimonials/002-corona-analyst/index.html",
        title="Case File 002 · Corona Analyst | Joshua Guerrero",
        description="$20,000 saved off asking on a Corona condo, repairs handled, early close. Real deal, real numbers, real strategy.",
        canonical="/testimonials/002-corona-analyst/",
        main_body_html=MAIN_BODY,
        og_title="Case File 002: $20,000 off asking on a Corona condo",
        og_description="9 condos toured. One worth fighting for. A strategic first-position play.",
    )
