"""Build Case File 003 on the shared testimonial framework.

Richard W.'s story follows the same Client, Mission, Search, Deal, Execution,
and Takeaway rhythm as Case Files 001 and 002. Listing photography is kept
inside a 1000px container so the 1024px CRMLS source is never enlarged.
"""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from scaffold_page import scaffold_page
from _case_file_shared import (
    CF_STYLE_BLOCK,
    COUNT_UP_AND_REVEAL_SCRIPT,
    cta_pill,
    postprocess_case_file,
    proof_xref,
)


PAGE_PATH = "testimonials/003-riverside-first-home/index.html"
CANONICAL = "https://drozq.com/testimonials/003-riverside-first-home/"
OG_IMAGE = "https://drozq.com/media/images/euclid/pool-day.webp"


HERO = """
<section class="cf-hero">
  <div class="cf-hero__inner">
    <div class="cf-label">Case File 003 &middot; Riverside &middot; First-Time Buyer</div>
    <h1>The first home of his life. The place his whole family had been waiting for.</h1>
  </div>
  <div class="cf-hero__scroll" aria-hidden="true">Scroll</div>
</section>
"""


CLIENT = """
<section class="cf-section">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Client</div>
    <p class="cf-body">Richard W. spent 22 years building a steady life through his work at Ralphs. He had never owned a home. When he was finally ready to buy, this was not a temporary move or a box to check. He wanted the first home of his life to be the home that carried him into retirement.</p>
    <div class="cf-badges">
      <span class="cf-badge">First-Time Buyer</span>
      <span class="cf-badge">22 Years at Ralphs</span>
      <span class="cf-badge">Retirement Home</span>
      <span class="cf-badge">Riverside, CA</span>
    </div>
  </div>
</section>
"""


MISSION = """
<section class="cf-section cf-section--alt">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Mission</div>
    <p class="cf-body">Find a home with enough room for Richard to live comfortably, enough life in it to feel like a dream, and enough space for the whole family to gather. His children and grandchildren needed more than an address to visit. They needed a place where birthdays, BBQs, and long summer afternoons could become traditions.</p>
  </div>
</section>
"""


SEARCH = """
<section class="cf-section">
  <div class="cf-wide cf-reveal" style="text-align:center;">
    <div class="cf-label">The Search</div>
    <h2 class="cf-headline-stat">Only one home had the pool. His family could already see the summers ahead.</h2>
    <div style="max-width:680px; margin:0 auto;">
      <p class="cf-body">Euclid Court had the bedrooms, the living space, and the right setting. More than that, it was the only home in Richard's search with a pool. The grandchildren could be in the water while the adults gathered around the grill, and everyone could stay without wondering where they would fit.</p>
    </div>
    <div class="cf-photo-grid cf-photo-grid--feature" aria-label="Euclid Court property photos">
      <figure class="cf-photo">
        <img src="/media/images/euclid/pool-day.webp" width="1024" height="683" alt="Private backyard swimming pool in daylight" loading="lazy" decoding="async">
        <figcaption>The pool that set it apart</figcaption>
      </figure>
      <figure class="cf-photo">
        <img src="/media/images/euclid/front-day.jpg" width="1024" height="683" alt="Front exterior of 4194 Euclid Court in Riverside" loading="lazy" decoding="async">
        <figcaption>4194 Euclid Court</figcaption>
      </figure>
      <figure class="cf-photo">
        <img src="/media/images/euclid/pool-dusk.webp" width="1024" height="686" alt="Euclid Court backyard pool glowing at dusk" loading="lazy" decoding="async">
        <figcaption>The family's new gathering place</figcaption>
      </figure>
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
      <div class="cf-hero-stat__number" data-count-target="15000" data-count-prefix="$">$15,000</div>
      <div class="cf-hero-stat__label">Credit negotiated toward closing costs</div>
    </div>

    <div class="cf-grid">
      <div class="cf-grid__card">
        <div class="cf-grid__value">$665,000</div>
        <div class="cf-grid__label">Closed purchase price</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">3</div>
        <div class="cf-grid__label">Bedrooms</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">2</div>
        <div class="cf-grid__label">Bathrooms</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">1,900</div>
        <div class="cf-grid__label">Square feet</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">Private</div>
        <div class="cf-grid__label">Backyard pool</div>
      </div>
      <div class="cf-grid__card">
        <div class="cf-grid__value">Early</div>
        <div class="cf-grid__label">Closing timeline</div>
      </div>
    </div>

    <div class="cf-receipt" role="group" aria-label="Euclid Court buyer-side ledger">
      <div class="cf-receipt__title">Buyer-Side Ledger</div>
      <div class="cf-receipt__row">
        <span class="cf-receipt__label">Original list price</span>
        <span class="cf-receipt__amount">$649,000.00</span>
      </div>
      <div class="cf-receipt__row">
        <span class="cf-receipt__label">Closed purchase price</span>
        <span class="cf-receipt__amount">$665,000.00</span>
      </div>
      <div class="cf-receipt__row">
        <span class="cf-receipt__label">Closing-cost credit</span>
        <span class="cf-receipt__amount">&minus;$15,000.00</span>
      </div>
      <div class="cf-receipt__row cf-receipt__row--total">
        <span class="cf-receipt__label">Price less credit</span>
        <span class="cf-receipt__amount">$650,000.00</span>
      </div>
    </div>
  </div>
</section>
"""


EXECUTION = """
<section class="cf-section">
  <div class="cf-narrow cf-reveal">
    <div class="cf-label">The Execution</div>
    <p class="cf-body">A first purchase carries enough emotion. The file itself needed discipline. Richard had a strong lender, we stayed ahead of every inspection, and decisions were made while there was still time to make them well. That coordination is what turned an accepted offer into keys ahead of schedule.</p>
  </div>

  <div class="cf-wide cf-reveal">
    <ol class="cf-steps" aria-label="How the transaction closed early">
      <li class="cf-step">
        <span class="cf-step__number">1</span>
        <h3>The loan file stayed ahead.</h3>
        <p>Richard's lender kept underwriting, conditions, and communication moving before anyone had to chase them.</p>
      </li>
      <li class="cf-step">
        <span class="cf-step__number">2</span>
        <h3>Inspections moved immediately.</h3>
        <p>We ordered the work promptly, evaluated the findings quickly, and kept every decision point from becoming a delay.</p>
      </li>
      <li class="cf-step">
        <span class="cf-step__number">3</span>
        <h3>Escrow closed early.</h3>
        <p>With lending and inspections moving together, the file was ready ahead of schedule and Richard received the keys sooner.</p>
      </li>
    </ol>

    <div class="cf-compare">
      <div class="cf-compare__card cf-compare__card--muted">
        <div class="cf-compare__cap">Original list price</div>
        <div class="cf-compare__value">$649,000</div>
      </div>
      <div class="cf-compare__arrow" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none"><path d="M4 12h16m0 0l-6-6m6 6l-6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
      <div class="cf-compare__card cf-compare__card--hero">
        <div class="cf-compare__cap">Price less credit</div>
        <div class="cf-compare__value">$650,000</div>
      </div>
    </div>
    <p class="cf-body" style="max-width:680px; margin:42px auto 0; text-align:center;">The recorded sale price remains $665,000. The lender-approved $15,000 credit was applied to allowable buyer closing costs on the final settlement statement.</p>
  </div>
</section>
"""


FAMILY = """
<section class="cf-section cf-section--alt">
  <div class="cf-wide cf-reveal" style="text-align:center;">
    <div class="cf-label">What the Keys Opened</div>
    <h2 class="cf-headline-stat">The pool was the feature. The family was the reason.</h2>
    <div style="max-width:680px; margin:0 auto;">
      <p class="cf-body">Richard did not just buy a property. He changed what home means for his family. There is room for everyone, a pool his grandchildren can grow up remembering, and a covered patio ready for BBQs, birthdays, and ordinary afternoons that turn into the memories people keep.</p>
    </div>
    <div class="cf-photo-grid cf-photo-grid--three" aria-label="Spaces for Richard's family">
      <figure class="cf-photo">
        <img src="/media/images/euclid/living-room.webp" width="1024" height="684" alt="Spacious living room inside the Euclid Court home" loading="lazy" decoding="async">
        <figcaption>The main living room</figcaption>
      </figure>
      <figure class="cf-photo">
        <img src="/media/images/euclid/family-room.webp" width="1024" height="683" alt="Large family room with a pool table" loading="lazy" decoding="async">
        <figcaption>A second place to gather</figcaption>
      </figure>
      <figure class="cf-photo">
        <img src="/media/images/euclid/covered-patio.webp" width="1024" height="686" alt="Covered backyard patio beside the pool at dusk" loading="lazy" decoding="async">
        <figcaption>The future BBQ table</figcaption>
      </figure>
    </div>
  </div>
</section>
"""


TAKEAWAY = f"""
<section class="cf-section">
  <div class="cf-narrow cf-reveal cf-takeaway">
    <div class="cf-label">The Takeaway</div>
    <h2 class="cf-takeaway__headline">First home. Retirement plan. Family gathering place. Early close. One set of keys.</h2>
    <p class="cf-takeaway__sub">If you are ready to make your first purchase fit the life you are building, tell me the city or ZIP where you want to buy.</p>
    {cta_pill()}
    <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    <div class="cf-takeaway__next"><a href="/sold/">See all three closed deals &rarr;</a></div>
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
    <span class="cf-crosslink__sep" aria-hidden="true">&middot;</span>
    <a href="/testimonials/002-corona-analyst/">Case File 002 &middot; Corona</a>
    <span class="cf-crosslink__sep" aria-hidden="true">&middot;</span>
    <a href="/buyers/">Buyer guide</a>
  </nav>
</aside>
"""


PROOF_XREF = proof_xref(
    "4194 Euclid Ct",
    "$665,000 with $15,000 toward closing costs, a private pool, and an early close. On the record.",
    "Buying like Richard did",
)


MAIN_BODY = (
    CF_STYLE_BLOCK
    + HERO
    + CLIENT
    + MISSION
    + SEARCH
    + DEAL
    + EXECUTION
    + FAMILY
    + TAKEAWAY
    + CROSSLINK
    + PROOF_XREF
    + COUNT_UP_AND_REVEAL_SCRIPT
)


def json_script(payload: dict) -> str:
    return '<script type="application/ld+json">' + json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "</script>"


ARTICLE_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "Article",
    "@id": CANONICAL + "#story",
    "headline": "Richard W.'s first home and family gathering place in Riverside",
    "description": "After 22 years at Ralphs, first-time buyer Richard W. bought 4194 Euclid Ct with a $15,000 closing-cost credit and an early close.",
    "image": [
        OG_IMAGE,
        "https://drozq.com/media/images/euclid/front-day.jpg",
        "https://drozq.com/media/images/euclid/pool-dusk.webp",
    ],
    "datePublished": "2026-08-12",
    "dateModified": "2026-08-12",
    "author": {"@id": "https://drozq.com/#realestateagent"},
    "publisher": {"@id": "https://drozq.com/#localbusiness"},
    "mainEntityOfPage": {"@type": "WebPage", "@id": CANONICAL},
    "about": {
        "@type": "SingleFamilyResidence",
        "name": "4194 Euclid Ct",
        "numberOfBedrooms": 3,
        "numberOfBathroomsTotal": 2,
        "floorSize": {"@type": "QuantitativeValue", "value": 1900, "unitCode": "FTK"},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "4194 Euclid Ct",
            "addressLocality": "Riverside",
            "addressRegion": "CA",
            "postalCode": "92504",
            "addressCountry": "US",
        },
    },
}


BREADCRUMB_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
        {"@type": "ListItem", "position": 2, "name": "Client Stories", "item": "https://drozq.com/testimonials/"},
        {"@type": "ListItem", "position": 3, "name": "Richard's Riverside First Home", "item": CANONICAL},
    ],
}


if __name__ == "__main__":
    scaffold_page(
        target=PAGE_PATH,
        title="Case File 003 · Richard's Riverside First Home | Joshua Guerrero",
        description="Richard W. bought his first home at 4194 Euclid Ct with a $15,000 closing-cost credit, a private pool, and an early close.",
        canonical="/testimonials/003-riverside-first-home/",
        main_body_html=MAIN_BODY,
        og_title="Case File 003: $15,000 credit on Richard's Riverside first home",
        og_description="After 22 years at Ralphs, Richard bought the retirement home where his whole family can gather.",
        twitter_title="Case File 003: Richard's Riverside First Home",
        twitter_description="$15,000 toward closing costs, a private pool, room for every generation, and keys ahead of schedule.",
        og_image=OG_IMAGE,
    )
    postprocess_case_file(
        PAGE_PATH,
        head_additions=json_script(ARTICLE_SCHEMA) + json_script(BREADCRUMB_SCHEMA),
        twitter_image=OG_IMAGE,
        og_image_dimensions=(1024, 683),
    )
