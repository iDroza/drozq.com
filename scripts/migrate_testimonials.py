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
from _case_file_shared import (
    CF_STYLE_BLOCK,
    COUNT_UP_AND_REVEAL_SCRIPT,
    XREF_STYLE_BLOCK,
    cta_pill,
    postprocess_case_file,
)


INDEX_CHROME_STYLE = (
    '<style id="drozq-page-chrome">'
    '@layer base{#__next>header{position:fixed !important;top:0;left:0;right:0}}'
    '#__next>header{box-shadow:0 1px 5px rgba(0,0,0,.11)}'
    'body{padding-top:48px}@media(min-width:768px){body{padding-top:64px}}'
    '.drozq-photo-band{height:190px;background:#1a1816 url(/media/images/hero-giem/giem-18.webp) center/cover no-repeat}'
    '@media(min-width:768px){.drozq-photo-band{height:250px}}'
    '[id]{scroll-margin-top:80px}'
    '</style>'
)


PHOTO_BAND = '<div class="drozq-photo-band" role="presentation"></div>'


HERO = """
<section class="cf-hero cf-index-hero">
  <div class="cf-hero__inner" style="text-align:center;">
    <div class="cf-label">Case Files</div>
    <h1>Real deals. Real numbers. Real leverage.</h1>
    <p class="cf-index-hero__sub">Every client comes in with a different goal. A first home, an investment, a strategic entry, a move up. Here is how we execute on those goals, one deal at a time. Every case file is a real transaction with real numbers. We anonymize the clients because discretion is part of the service.</p>
    <p class="ta_center" style="margin-top:18px"><a href="/sold/" style="color:#d92228;font-weight:700;text-decoration:none">See the sold board &rarr;</a></p>
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
        <span class="cf-stats-strip__number" data-count-target="58250" data-count-prefix="$">$58,250</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Negotiated for clients</div>
      </div>

      <div class="cf-stats-strip__item">
        <!-- UPDATE AS NEW CASE FILES ARE ADDED -->
        <span class="cf-stats-strip__number" data-count-target="3">3</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Homes closed</div>
      </div>

      <div class="cf-stats-strip__item">
        <!-- UPDATE AS NEW CASE FILES ARE ADDED -->
        <span class="cf-stats-strip__number" data-count-target="3">3</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Closed ahead of schedule</div>
      </div>

      <div class="cf-stats-strip__item">
        <!-- UPDATE AS NEW CASE FILES ARE ADDED -->
        <span class="cf-stats-strip__number" data-count-target="1790000" data-count-prefix="$">$1,790,000</span>
        <!-- END UPDATE -->
        <div class="cf-stats-strip__sub">Closed purchase volume</div>
      </div>

    </div>
  </div>
</section>
"""

CARDS = """
<section class="cf-index-section">
  <div class="cf-label cf-index-section__label">The Case Files</div>
  <div class="cf-index-grid cf-reveal">

    <a class="cf-card cf-card--image" href="/testimonials/001-long-beach-firefighter/" aria-label="Read Case File 001: Long Beach firefighter, first-time buyer">
      <img class="cf-card__image" src="/media/images/hero-giem/giem-29.webp" alt="The Long Beach home purchased by a first-time buyer" width="1600" height="1114" loading="lazy" decoding="async">
      <div class="cf-card__content">
        <span class="cf-card__tab">Case File 001</span>
        <p class="cf-card__meta">Long Beach &middot; First-Time Buyer</p>
        <h2 class="cf-card__headline">He protects other people's homes. We helped him acquire his first.</h2>
        <div class="cf-card__stat"><span class="cf-card__stat-value">$23,250</span><span class="cf-card__stat-label">Seller credit negotiated</span></div>
      </div>
    </a>

    <a class="cf-card cf-card--image" href="/testimonials/002-corona-analyst/" aria-label="Read Case File 002: Corona financial analyst, strategic purchase">
      <img class="cf-card__image" src="/media/images/Corona.webp" alt="The Corona condo purchased by a financial analyst" width="1024" height="683" loading="lazy" decoding="async">
      <div class="cf-card__content">
        <span class="cf-card__tab">Case File 002</span>
        <p class="cf-card__meta">Corona &middot; Strategic Purchase</p>
        <h2 class="cf-card__headline">A financial analyst ran the numbers on his own purchase.</h2>
        <div class="cf-card__stat"><span class="cf-card__stat-value">$20,000</span><span class="cf-card__stat-label">Saved off asking price</span></div>
      </div>
    </a>

    <a class="cf-card cf-card--image" href="/testimonials/003-riverside-first-home/" aria-label="Read Case File 003 about the Riverside truck driver">
      <img class="cf-card__image" src="/media/images/euclid/pool-dusk.webp" alt="The Riverside pool home purchased by a truck driver" width="1024" height="686" loading="lazy" decoding="async">
      <div class="cf-card__content">
        <span class="cf-card__tab">Case File 003</span>
        <p class="cf-card__meta">Riverside &middot; Truck Driver</p>
        <h2 class="cf-card__headline">His first home became his family's gathering place.</h2>
        <div class="cf-card__stat"><span class="cf-card__stat-value">$15,000</span><span class="cf-card__stat-label">Closing-cost credit negotiated</span></div>
      </div>
    </a>

  </div>
</section>
"""


XREF = XREF_STYLE_BLOCK + """<section class="xr-band xr--white"><div class="xr-wrap"><div class="xr-head"><h2>The numbers live one page over.</h2><p>Where these deals sit on the record, and how the next one runs.</p></div><div class="xr-grid xr-grid--3"><a class="xr-card" href="/sold/"><p class="xr-eyebrow">The board</p><h3>Sold, with numbers left in</h3><p>$775,000 in Long Beach, $350,000 in Corona, $665,000 in Riverside, and $58,250 negotiated across all three.</p><span class="xr-go">See the board &rarr;</span></a><a class="xr-card" href="/process/"><p class="xr-eyebrow">Method</p><h3>The five steps</h3><p>The sequence behind every case file on this page.</p><span class="xr-go">See the process &rarr;</span></a><a class="xr-card" href="/about/"><p class="xr-eyebrow">The agent</p><h3>Who runs these deals</h3><p>One agent, one phone number. Every file above closed by me.</p><span class="xr-go">About me &rarr;</span></a></div></div></section>"""

CTA = f"""
<section class="cf-cta-strip">
  <div class="cf-narrow">
    <div class="cf-label">What's Next</div>
    <h2>Want your deal to be the next case file?</h2>
    <p class="cf-cta-strip__sub">Most clients find me right here. They read a client story, see themselves in it, and start the conversation. If that is you, tell me where you want to buy.</p>
    {cta_pill()}
    <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
  </div>
</section>
"""


MAIN_BODY = PHOTO_BAND + CF_STYLE_BLOCK + HERO + STATS + CARDS + XREF + CTA + COUNT_UP_AND_REVEAL_SCRIPT


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
    postprocess_case_file(
        "testimonials/index.html",
        page_chrome=INDEX_CHROME_STYLE,
        og_type=None,
        add_scroll_script=False,
    )
