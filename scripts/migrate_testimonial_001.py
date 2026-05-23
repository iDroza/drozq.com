"""Migrate /testimonials/001-long-beach-firefighter/ to the homepage scaffold.

Content-first with the cf-* design system. Preserves the full case file
narrative (Client / Mission / Search / Deal / Negotiation / In His Words /
Takeaway) and every dollar figure verbatim.

Changes from the legacy page:
- Anonymized client attribution: "Elijah D., Long Beach" -> "The Client,
  Long Beach, CA". Per the index page promise ("we anonymize the clients
  because discretion is part of the service"), the legacy page leaking a
  real first name + last initial was a violation.
- Removed the 5-star row above the quote. CLAUDE.md voice principle: no
  star ratings or platform-aggregated social proof. The quote text itself
  remains; the stars were redundant theater.
- Replaced the "Book a 15-minute call" link to /contact/ with an inline
  funnel-opening Sell-mode pill, per the always-inline directive.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page
from _case_file_shared import CF_STYLE_BLOCK, COUNT_UP_AND_REVEAL_SCRIPT, cta_pill


HOUSE_SVG = '<svg viewBox="0 0 100 100"><path d="M50 12 L8 48 L18 48 L18 88 L42 88 L42 64 L58 64 L58 88 L82 88 L82 48 L92 48 Z"/></svg>'
HOUSES = (
    "\n".join(f'<span class="cf-house" aria-hidden="true">{HOUSE_SVG}</span>' for _ in range(13))
    + f'\n<span class="cf-house cf-house--match" aria-hidden="true">{HOUSE_SVG}</span>'
)


HERO = """
<section class="cf-hero">
  <div class="cf-hero__inner">
    <div class="cf-label">Case File 001 &middot; Long Beach &middot; First-Time Buyer</div>
    <h1>He spends his career protecting other people's homes. We helped him acquire his first.</h1>
  </div>
  <div class="cf-hero__scroll" aria-hidden="true">Scroll</div>
</section>
"""

CLIENT = """
<section class="cf-section">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Client</div>
    <p class="cf-body">He's a Southern California firefighter with a long-term plan. While most of his peers were waiting for the "perfect" market, he was studying it. He wanted his first property to do double duty: a home to live in, and an asset that would start generating income from day one. He came in disciplined, informed, and ready to move the moment the right opportunity surfaced.</p>
    <div class="cf-badges">
      <span class="cf-badge">First-Time Buyer</span>
      <span class="cf-badge">Firefighter</span>
      <span class="cf-badge">House-Hack Strategy</span>
      <span class="cf-badge">Long Beach</span>
    </div>
  </div>
</section>
"""

MISSION = """
<section class="cf-section cf-section--alt">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Mission</div>
    <p class="cf-body">The brief was specific: a home he could live in, with enough flexibility to rent part of it out from day one. In a Long Beach market where competition is fierce and inventory moves fast, "primary residence that doubles as an investment" requires a sharp eye and sharper negotiation.</p>
  </div>
</section>
"""

SEARCH = f"""
<section class="cf-section">
  <div class="cf-wide cf-reveal" style="text-align:center;">
    <div class="cf-label">The Search</div>
    <h2 class="cf-headline-stat">14 properties. One yes.</h2>

    <div class="cf-houses" role="img" aria-label="Thirteen homes reviewed, one home selected">
      {HOUSES}
    </div>

    <div style="max-width:680px; margin:0 auto;">
      <p class="cf-body">We walked 14 homes together. Some didn't pencil out as investments. Some had issues we caught before the inspector did. One had a sewer line so corroded it would have turned into a five-figure problem within a year. We kept moving. The 14th was the one.</p>
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
      <div class="cf-hero-stat__number" data-count-target="23250" data-count-prefix="$">$23,250</div>
      <div class="cf-hero-stat__label">Seller credit negotiated</div>
    </div>

    <div class="cf-grid">
      <div class="cf-grid__card">
        <div class="cf-grid__value">$775,000</div>
        <div class="cf-grid__label">Purchase price</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">5%</div>
        <div class="cf-grid__label">Down payment, conventional</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">$0</div>
        <div class="cf-grid__label">Out of pocket closing costs</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value cf-grid__value--accent" aria-label="Yes">&#10003;</div>
        <div class="cf-grid__label">Rate permanently bought down</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">Early</div>
        <div class="cf-grid__label">Closing timeline</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">3</div>
        <div class="cf-grid__label">Inspections ordered (Home, Termite, Sewer)</div>
      </div>
    </div>

    <div class="cf-receipt" role="group" aria-label="Seller credit allocation">
      <div class="cf-receipt__title">Credit Allocation</div>
      <div class="cf-receipt__row">
        <span class="cf-receipt__label">Closing costs covered</span>
        <span class="cf-receipt__amount">$14,725.00</span>
      </div>
      <div class="cf-receipt__row">
        <span class="cf-receipt__label">Permanent rate buy-down</span>
        <span class="cf-receipt__amount">$8,525.00</span>
      </div>
      <div class="cf-receipt__row cf-receipt__row--total">
        <span class="cf-receipt__label">Total seller credit</span>
        <span class="cf-receipt__amount">$23,250.00</span>
      </div>
    </div>
  </div>
</section>
"""

NEGOTIATION = """
<section class="cf-section">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Negotiation</div>
    <p class="cf-body">Most agents would have accepted a $5,000 to $10,000 credit and called it a day. We didn't. We pushed, armed with three inspection reports, a clear read on the seller's timeline, and a buyer with the discipline to walk if the numbers didn't land.</p>
    <p class="cf-body">The result: $23,250. Enough to cover every dollar of closing costs and still have room left to permanently lower his monthly mortgage payment for the life of the loan.</p>
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
        <div class="cf-compare__value">$23,250</div>
      </div>
    </div>
  </div>
</section>
"""

QUOTE = """
<section class="cf-section cf-section--alt">
  <div class="cf-reveal">
    <div style="text-align:center;">
      <div class="cf-label">In His Words</div>
    </div>
    <div class="cf-quote">
      <blockquote class="cf-quote__body">Working with Josh was a great experience. He's a young real estate agent but did extremely well. He was always by my side and answered any questions I had. Josh was quick to respond and if he didn't have an answer for me he worked hard to figure the information out and get it back to me as soon as possible. He did excellent work during negotiations and fought well for me. I would definitely recommend Josh!</blockquote>
      <div class="cf-quote__attribution">The Client &middot; Long Beach, CA</div>
    </div>
  </div>
</section>
"""

TAKEAWAY = f"""
<section class="cf-section">
  <div class="cf-narrow cf-reveal cf-takeaway">
    <div class="cf-label">The Takeaway</div>
    <h2 class="cf-takeaway__headline">First home. Investment property. Rate buy-down. Zero closing costs. One deal. One strategy.</h2>
    <p class="cf-takeaway__sub">If you are a first-time buyer who wants to build real wealth in this market, this is the conversation we want to have with you. Drop your address below.</p>
    {cta_pill()}
    <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    <div class="cf-takeaway__next"><a href="/testimonials/002-corona-analyst/">Read Case File 002 &rarr;</a></div>
  </div>
</section>
"""

CROSSLINK = """
<aside class="cf-crosslink">
  <span class="cf-crosslink__label">More Case Files</span>
  <nav class="cf-crosslink__nav" aria-label="More case files">
    <a href="/testimonials/">All case files</a>
    <span class="cf-crosslink__sep" aria-hidden="true">&middot;</span>
    <a href="/testimonials/002-corona-analyst/">Case File 002 &middot; Corona</a>
  </nav>
</aside>
"""


MAIN_BODY = CF_STYLE_BLOCK + HERO + CLIENT + MISSION + SEARCH + DEAL + NEGOTIATION + QUOTE + TAKEAWAY + CROSSLINK + COUNT_UP_AND_REVEAL_SCRIPT


if __name__ == "__main__":
    scaffold_page(
        target="testimonials/001-long-beach-firefighter/index.html",
        title="Case File 001 · Long Beach Firefighter | Joshua Guerrero",
        description="$23,250 seller credit negotiated on a Long Beach first-home + investment property. Real deal, real numbers, real strategy.",
        canonical="/testimonials/001-long-beach-firefighter/",
        main_body_html=MAIN_BODY,
        og_title="Case File 001: $23,250 seller credit on a Long Beach first home",
        og_description="14 properties walked. One yes. A first-home + investment play in Long Beach.",
    )
