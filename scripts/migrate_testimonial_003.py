"""Build Richard W.'s Riverside first-home story on the homepage scaffold.

This is a Trust-archetype page: real property photography, a compact story
masthead, transparent deal math, a buyer-mode closing CTA, and the synced
site funnel. The page intentionally uses its own mobile-first rw-* system
instead of extending the legacy cf-* case-file presentation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from scaffold_page import scaffold_page


PAGE_PATH = "testimonials/003-riverside-first-home/index.html"
CANONICAL = "https://drozq.com/testimonials/003-riverside-first-home/"
OG_IMAGE = "https://drozq.com/media/images/euclid/front-day.jpg"


STYLE = r"""
<style id="rw-story-css">
.rw-story{color:#1a1816;background:#fff}
.rw-wrap{width:100%;max-width:1035px;margin:0 auto;padding:0 20px;box-sizing:border-box}
.rw-copy{width:100%;max-width:720px;margin:0 auto}
.rw-section{padding:56px 0;background:#fff}
.rw-section--warm{background:#f2f0ef}
.rw-kicker{margin:0 0 10px;color:#d92228;font-size:12px;font-weight:800;line-height:18px;letter-spacing:1.6px;text-transform:uppercase}
.rw-h2{margin:0;color:#1a1816;font-size:31px;font-weight:800;line-height:37px;letter-spacing:-.6px}
.rw-lede{margin:18px 0 0;color:#3f4650;font-size:18px;line-height:29px}
.rw-body{margin:18px 0 0;color:#3f4650;font-size:17px;line-height:28px}
.rw-body strong{color:#1a1816}
.rw-photo-band{height:300px;background:#f2f0ef;overflow:hidden}
.rw-photo-band img{display:block;width:100%;height:100%;object-fit:cover;object-position:center 50%}
.rw-masthead{padding:48px 0 42px;background:#fbf8f4;text-align:center}
.rw-masthead h1{max-width:850px;margin:0 auto;color:#1a1816;font-size:38px;font-weight:800;line-height:43px;letter-spacing:-1px}
.rw-masthead__sub{max-width:700px;margin:18px auto 0;color:#3f4650;font-size:18px;line-height:28px}
.rw-address{margin:22px 0 0;color:#1a1816;font-size:14px;font-weight:700;line-height:22px}
.rw-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;margin-top:34px;border-top:1px solid #d3cfca;border-bottom:1px solid #d3cfca}
.rw-fact{padding:15px 8px;text-align:center}
.rw-fact:nth-child(odd){border-right:1px solid #d3cfca}
.rw-fact:nth-child(-n+4){border-bottom:1px solid #d3cfca}
.rw-fact__value{display:block;color:#1a1816;font-size:18px;font-weight:800;line-height:23px;font-variant-numeric:tabular-nums}
.rw-fact__label{display:block;margin-top:3px;color:#757575;font-size:12px;line-height:17px}
.rw-dream-grid{display:grid;grid-template-columns:1fr;gap:14px;margin-top:30px}
.rw-dream{padding:26px 24px;border-radius:16px;background:#fff;box-shadow:0 1px 5px rgba(26,24,22,.08)}
.rw-dream__num{display:flex;width:32px;height:32px;align-items:center;justify-content:center;border-radius:50%;background:#d92228;color:#fff;font-size:14px;font-weight:800}
.rw-dream h3{margin:18px 0 0;color:#1a1816;font-size:21px;font-weight:800;line-height:27px}
.rw-dream p{margin:8px 0 0;color:#3f4650;font-size:15px;line-height:24px}
.rw-gallery{display:grid;grid-template-columns:1fr;gap:10px;margin-top:32px}
.rw-gallery figure{position:relative;margin:0;overflow:hidden;border-radius:14px;background:#f2f0ef}
.rw-gallery img{display:block;width:100%;height:100%;min-height:250px;object-fit:cover}
.rw-gallery figcaption{position:absolute;left:12px;bottom:12px;max-width:calc(100% - 24px);padding:8px 11px;border-radius:8px;background:rgba(26,24,22,.78);color:#fff;font-size:12px;font-weight:700;line-height:17px}
.rw-deal-head{text-align:center}
.rw-deal-number{margin:22px 0 0;color:#d92228;font-size:62px;font-weight:800;line-height:1;letter-spacing:-2px;font-variant-numeric:tabular-nums}
.rw-deal-label{margin:10px 0 0;color:#3f4650;font-size:15px;font-weight:700;line-height:22px}
.rw-ledger{max-width:620px;margin:34px auto 0;padding:24px 20px;border-radius:16px;background:#fff;box-shadow:0 1px 5px rgba(26,24,22,.08)}
.rw-ledger__title{margin:0 0 10px;color:#757575;font-size:11px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase}
.rw-ledger__row{display:flex;justify-content:space-between;gap:18px;padding:13px 0;border-bottom:1px solid #e5e5e5;color:#3f4650;font-size:15px;line-height:21px}
.rw-ledger__row span:last-child{flex:0 0 auto;color:#1a1816;font-weight:800;font-variant-numeric:tabular-nums}
.rw-ledger__row--credit span:last-child{color:#d92228}
.rw-ledger__row--total{padding-top:18px;border-bottom:0;color:#1a1816;font-weight:800}
.rw-ledger__row--total span:last-child{font-size:21px}
.rw-ledger__note{margin:12px 0 0;color:#757575;font-size:12px;line-height:18px}
.rw-proof-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:18px}
.rw-proof{padding:18px 12px;border-radius:12px;background:#fbf8f4;text-align:center}
.rw-proof strong{display:block;color:#1a1816;font-size:18px;line-height:23px}
.rw-proof span{display:block;margin-top:4px;color:#757575;font-size:12px;line-height:17px}
.rw-run{list-style:none;margin:32px 0 0;padding:0;counter-reset:run}
.rw-run li{position:relative;margin:0;padding:0 0 28px 50px;counter-increment:run}
.rw-run li:last-child{padding-bottom:0}
.rw-run li:before{content:counter(run);position:absolute;top:0;left:0;display:flex;width:32px;height:32px;align-items:center;justify-content:center;border-radius:50%;background:#d92228;color:#fff;font-size:14px;font-weight:800}
.rw-run li:not(:last-child):after{content:"";position:absolute;top:36px;bottom:4px;left:15px;width:1px;background:#d3cfca}
.rw-run h3{margin:0;color:#1a1816;font-size:20px;font-weight:800;line-height:26px}
.rw-run p{margin:7px 0 0;color:#3f4650;font-size:15px;line-height:24px}
.rw-pool{position:relative;min-height:510px;margin:0;background:#1a1816;overflow:hidden}
.rw-pool img{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:cover;object-position:center}
.rw-pool:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(26,24,22,.08) 20%,rgba(26,24,22,.88) 100%)}
.rw-pool figcaption{position:relative;z-index:1;display:flex;min-height:510px;align-items:flex-end;padding:44px 20px;box-sizing:border-box}
.rw-pool__copy{max-width:760px;margin:0 auto;color:#fff;text-align:center}
.rw-pool__copy h2{margin:0;color:#fff;font-size:34px;font-weight:800;line-height:40px;letter-spacing:-.7px}
.rw-pool__copy p{margin:15px 0 0;color:#fff;font-size:17px;line-height:27px}
.rw-final{text-align:center}
.rw-final .rw-body{max-width:680px;margin-left:auto;margin-right:auto}
.rw-xref{padding:48px 0;background:#f2f0ef}
.rw-xref__head{max-width:700px;margin:0 auto 24px;text-align:center}
.rw-xref__head h2{margin:0;color:#1a1816;font-size:28px;font-weight:800;line-height:35px}
.rw-xref__head p{margin:9px 0 0;color:#3f4650;font-size:15px;line-height:24px}
.rw-xref__grid{display:grid;grid-template-columns:1fr;gap:12px}
.rw-xref__card{display:block;padding:22px;border-radius:14px;background:#fff;color:inherit;text-decoration:none;box-shadow:0 1px 5px rgba(26,24,22,.07);transition:transform .15s ease,box-shadow .15s ease}
.rw-xref__card:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(26,24,22,.09)}
.rw-xref__eyebrow{margin:0;color:#d92228;font-size:11px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase}
.rw-xref__card h3{margin:8px 0 0;color:#1a1816;font-size:19px;font-weight:800;line-height:25px}
.rw-xref__card p{margin:7px 0 0;color:#3f4650;font-size:14px;line-height:22px}
.rw-xref__go{display:block;margin-top:10px;color:#d92228;font-size:14px;font-weight:800}
.rw-cta{padding:56px 0;background:#fff;text-align:center}
.rw-cta h2{max-width:720px;margin:0 auto;color:#1a1816;font-size:31px;font-weight:800;line-height:37px;letter-spacing:-.5px}
.rw-cta__sub{max-width:620px;margin:14px auto 0;color:#3f4650;font-size:16px;line-height:25px}
.rw-cta__form{max-width:620px;margin:28px auto 0}
.rw-cta__pill{position:relative;display:flex;flex-direction:column;align-items:stretch;border-radius:30px;background:#fff;box-shadow:0 1px 7px rgba(26,24,22,.17);overflow:visible}
.rw-cta__pill input{width:100%;height:56px;padding:0 22px;border:0;border-radius:30px;background:#fff;color:#1a1816;font-family:inherit;font-size:16px;box-sizing:border-box;outline:0}
.rw-cta__pill input:focus{box-shadow:inset 0 0 0 2px #1a1816}
.rw-cta__pill button{height:50px;margin:4px;border:0;border-radius:9999px;background:#d92228;color:#fff;font-family:inherit;font-size:16px;font-weight:800;cursor:pointer}
.rw-cta__pill button:hover{background:#a92e2a}
.rw-cta__phone{margin:20px 0 0;color:#757575;font-size:14px;line-height:21px}
.rw-cta__phone a{color:#d92228;font-weight:800;text-decoration:none}
@media(min-width:560px){
  .rw-cta__pill{flex-direction:row;align-items:center}
  .rw-cta__pill input{flex:1;min-width:0}
  .rw-cta__pill button{flex:0 0 auto;padding:0 26px}
}
@media(min-width:768px){
  .rw-wrap{padding:0 32px}
  .rw-section{padding:80px 0}
  .rw-photo-band{height:500px}
  .rw-masthead{padding:70px 0 62px}
  .rw-masthead h1{font-size:58px;line-height:62px;letter-spacing:-1.8px}
  .rw-masthead__sub{font-size:21px;line-height:32px}
  .rw-facts{grid-template-columns:repeat(6,minmax(0,1fr))}
  .rw-fact{padding:17px 10px;border-right:1px solid #d3cfca;border-bottom:0!important}
  .rw-fact:nth-child(odd){border-right:1px solid #d3cfca}
  .rw-fact:last-child{border-right:0}
  .rw-dream-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
  .rw-gallery{grid-template-columns:repeat(12,minmax(0,1fr));grid-auto-rows:280px;gap:12px}
  .rw-gallery figure{grid-column:span 6}
  .rw-gallery figure:first-child{grid-column:span 7;grid-row:span 2}
  .rw-gallery figure:nth-child(2),.rw-gallery figure:nth-child(3){grid-column:span 5}
  .rw-gallery figure:nth-child(4),.rw-gallery figure:nth-child(5){grid-column:span 6}
  .rw-gallery img{min-height:0}
  .rw-deal-number{font-size:102px;letter-spacing:-4px}
  .rw-ledger{padding:30px 34px}
  .rw-proof-grid{grid-template-columns:repeat(4,minmax(0,1fr))}
  .rw-pool,.rw-pool figcaption{min-height:650px}
  .rw-pool figcaption{padding:70px 32px}
  .rw-pool__copy h2{font-size:50px;line-height:56px;letter-spacing:-1.2px}
  .rw-pool__copy p{font-size:19px;line-height:30px}
  .rw-xref{padding:64px 0}
  .rw-xref__grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
  .rw-cta{padding:80px 0}
  .rw-cta h2{font-size:42px;line-height:48px}
}
@media(min-width:1100px){
  .rw-photo-band{height:560px}
}
@media(prefers-reduced-motion:reduce){.rw-xref__card{transition:none}}
</style>
"""


PHOTO_BAND = """
<div class="rw-photo-band">
  <img src="/media/images/euclid/front-day.jpg" width="1024" height="683"
       alt="Front exterior of 4194 Euclid Court in Riverside" fetchpriority="high" decoding="async">
</div>
"""


MASTHEAD = """
<section class="rw-masthead" aria-labelledby="rw-title">
  <div class="rw-wrap">
    <h1 id="rw-title">The first home of his life. The place his whole family had been waiting for.</h1>
    <p class="rw-masthead__sub">After 22 years at Ralphs, Richard W. bought the Riverside pool home he plans to enjoy into retirement.</p>
    <p class="rw-address">4194 Euclid Ct, Riverside, CA 92504</p>
    <div class="rw-facts" aria-label="Closed sale facts">
      <div class="rw-fact"><span class="rw-fact__value">$665,000</span><span class="rw-fact__label">Closed price</span></div>
      <div class="rw-fact"><span class="rw-fact__value">3</span><span class="rw-fact__label">Bedrooms</span></div>
      <div class="rw-fact"><span class="rw-fact__value">2</span><span class="rw-fact__label">Bathrooms</span></div>
      <div class="rw-fact"><span class="rw-fact__value">1,900</span><span class="rw-fact__label">Square feet</span></div>
      <div class="rw-fact"><span class="rw-fact__value">Private</span><span class="rw-fact__label">Pool</span></div>
      <div class="rw-fact"><span class="rw-fact__value">Aug 10</span><span class="rw-fact__label">Closed in 2026</span></div>
    </div>
  </div>
</section>
"""


STORY = """
<section class="rw-section">
  <div class="rw-wrap">
    <div class="rw-copy">
      <p class="rw-kicker">Richard's story</p>
      <h2 class="rw-h2">This was never just about buying a house.</h2>
      <p class="rw-lede">Richard had spent 22 years building a life through steady work at Ralphs. He had never owned a home. Now he was ready to turn that lifetime of consistency into something permanent: his first set of keys, his retirement home, and a place his family could keep coming back to.</p>
      <p class="rw-body">The search changed the moment we found Euclid Court. It had the bedrooms, the living space, and the right setting. More than that, it was the only home in his search with a pool. His family could already see the grandchildren in the water, the adults around the grill, and every generation together without anyone wondering where they would all fit.</p>
    </div>
  </div>
</section>
"""


DREAM = """
<section class="rw-section rw-section--warm" aria-labelledby="rw-dream-title">
  <div class="rw-wrap">
    <div class="rw-copy">
      <p class="rw-kicker">What he was really buying</p>
      <h2 class="rw-h2" id="rw-dream-title">A first home, a retirement plan, and a gathering place in one address.</h2>
    </div>
    <div class="rw-dream-grid">
      <article class="rw-dream"><span class="rw-dream__num">1</span><h3>His first front door</h3><p>After a lifetime of renting, Richard would finally walk into a home that was his.</p></article>
      <article class="rw-dream"><span class="rw-dream__num">2</span><h3>A home for retirement</h3><p>Not a temporary stop. A place with enough comfort and space to settle into the years ahead.</p></article>
      <article class="rw-dream"><span class="rw-dream__num">3</span><h3>Room for everybody</h3><p>A pool, covered patio, and generous living areas made family BBQs and long visits part of the plan.</p></article>
    </div>
  </div>
</section>
"""


GALLERY = """
<section class="rw-section" aria-labelledby="rw-space-title">
  <div class="rw-wrap">
    <div class="rw-copy">
      <p class="rw-kicker">The home</p>
      <h2 class="rw-h2" id="rw-space-title">Enough space to live quietly. Enough space to bring everyone together.</h2>
    </div>
    <div class="rw-gallery">
      <figure><img src="/media/images/euclid/living-room.webp" width="1024" height="684" alt="Spacious living room inside the Euclid Court home" loading="lazy" decoding="async"><figcaption>The main living room</figcaption></figure>
      <figure><img src="/media/images/euclid/dining-room.webp" width="1024" height="683" alt="Dining room with space for family meals" loading="lazy" decoding="async"><figcaption>Room for family dinners</figcaption></figure>
      <figure><img src="/media/images/euclid/family-room.webp" width="1024" height="683" alt="Large family room with a pool table" loading="lazy" decoding="async"><figcaption>A second place to gather</figcaption></figure>
      <figure><img src="/media/images/euclid/pool-day.webp" width="1024" height="683" alt="Private backyard swimming pool in daylight" loading="lazy" decoding="async"><figcaption>The pool that set it apart</figcaption></figure>
      <figure><img src="/media/images/euclid/covered-patio.webp" width="1024" height="686" alt="Covered backyard patio beside the pool at dusk" loading="lazy" decoding="async"><figcaption>The future BBQ table</figcaption></figure>
    </div>
  </div>
</section>
"""


DEAL = """
<section class="rw-section rw-section--warm" aria-labelledby="rw-deal-title">
  <div class="rw-wrap">
    <div class="rw-deal-head">
      <p class="rw-kicker">The negotiation</p>
      <h2 class="rw-h2" id="rw-deal-title">We protected the dream with real dollars.</h2>
      <p class="rw-deal-number">$15,000</p>
      <p class="rw-deal-label">Credit negotiated toward Richard's allowable closing costs</p>
    </div>
    <div class="rw-ledger" role="group" aria-label="Euclid Court purchase ledger">
      <p class="rw-ledger__title">The buyer-side ledger</p>
      <div class="rw-ledger__row"><span>Original list price</span><span>$649,000</span></div>
      <div class="rw-ledger__row"><span>Closed purchase price</span><span>$665,000</span></div>
      <div class="rw-ledger__row rw-ledger__row--credit"><span>Closing-cost credit</span><span>-$15,000</span></div>
      <div class="rw-ledger__row rw-ledger__row--total"><span>Price less credit</span><span>$650,000</span></div>
      <p class="rw-ledger__note">The closed sale price remains $665,000. The $15,000 credit was applied to allowable buyer closing costs, subject to the lender and final settlement statement.</p>
    </div>
    <div class="rw-proof-grid" aria-label="Additional sale facts">
      <div class="rw-proof"><strong>3 beds</strong><span>Space for family</span></div>
      <div class="rw-proof"><strong>2 baths</strong><span>Built for everyday living</span></div>
      <div class="rw-proof"><strong>1,900 sq ft</strong><span>Room to gather</span></div>
      <div class="rw-proof"><strong>Closed early</strong><span>Keys ahead of schedule</span></div>
    </div>
  </div>
</section>
"""


EXECUTION = """
<section class="rw-section" aria-labelledby="rw-execution-title">
  <div class="rw-wrap">
    <div class="rw-copy">
      <p class="rw-kicker">The execution</p>
      <h2 class="rw-h2" id="rw-execution-title">A strong lender. Fast inspections. Early keys.</h2>
      <p class="rw-lede">The emotional part of a first purchase is big. The transaction itself still has to run with discipline.</p>
      <ol class="rw-run">
        <li><h3>The loan file stayed ahead.</h3><p>Richard had a strong lender who kept underwriting, conditions, and communication moving before anyone had to chase them.</p></li>
        <li><h3>We stayed on top of every inspection.</h3><p>Inspections were ordered promptly, findings were evaluated quickly, and the decision points never became delays.</p></li>
        <li><h3>Escrow closed early.</h3><p>With the lender and inspection work moving together, the file was ready ahead of schedule and Richard got the keys sooner.</p></li>
      </ol>
    </div>
  </div>
</section>
"""


POOL = """
<figure class="rw-pool">
  <img src="/media/images/euclid/pool-dusk.webp" width="1024" height="686" alt="Euclid Court backyard pool glowing at dusk" loading="lazy" decoding="async">
  <figcaption>
    <div class="rw-pool__copy">
      <h2>The pool was the feature. The family was the reason.</h2>
      <p>Now birthdays, summer afternoons, BBQ smoke, grandchildren in the water, and everyone staying a little longer have one address.</p>
    </div>
  </figcaption>
</figure>
"""


FINAL = """
<section class="rw-section rw-final">
  <div class="rw-wrap">
    <div class="rw-copy">
      <p class="rw-kicker">The outcome</p>
      <h2 class="rw-h2">Richard did not just buy a property. He changed what home means for his family.</h2>
      <p class="rw-body">The first home of his life became the dream home he had worked toward for 22 years. There is room for everyone, a pool his grandchildren can grow up remembering, and a place that can carry him into retirement. That is what the keys opened.</p>
    </div>
  </div>
</section>
"""


CROSSLINKS = """
<aside class="rw-xref" aria-labelledby="rw-xref-title">
  <div class="rw-wrap">
    <div class="rw-xref__head"><h2 id="rw-xref-title">See the record behind the work.</h2><p>Every closed deal, the buyer process, and the other client stories are one step away.</p></div>
    <div class="rw-xref__grid">
      <a class="rw-xref__card" href="/sold/"><p class="rw-xref__eyebrow">The board</p><h3>Every closing, numbers included</h3><p>$58,250 negotiated across three closed purchases, and all three closed early.</p><span class="rw-xref__go">See the sold board &rarr;</span></a>
      <a class="rw-xref__card" href="/buyers/"><p class="rw-xref__eyebrow">The process</p><h3>How I run a buyer search</h3><p>Payment-first budgeting, filtered homes, comp-backed offers, and clean execution.</p><span class="rw-xref__go">Read the buyer guide &rarr;</span></a>
      <a class="rw-xref__card" href="/testimonials/"><p class="rw-xref__eyebrow">More stories</p><h3>Three buyers. Three different wins.</h3><p>Long Beach, Corona, and Riverside, with the strategy and result left in.</p><span class="rw-xref__go">Read every story &rarr;</span></a>
    </div>
  </div>
</aside>
"""


CTA = """
<section class="rw-cta" aria-labelledby="rw-cta-title">
  <div class="rw-wrap">
    <p class="rw-kicker">Your first home can start here</p>
    <h2 id="rw-cta-title">Tell me where you want to buy. I will build the search around your life.</h2>
    <p class="rw-cta__sub">Your payment, timing, family, and long-term plan come first. Enter a city or ZIP and I will take it from there.</p>
    <div id="rw-buy-panel" role="tabpanel" aria-labelledby="tab-buy" class="rw-cta__form">
      <form class="pos_relative">
        <div class="rw-cta__pill">
          <input type="text" name="location" placeholder="City and State or ZIP" autocomplete="off" aria-label="City and State or ZIP">
          <button type="submit">Run my Valuation</button>
        </div>
        <input type="hidden" name="gclid" value="">
      </form>
    </div>
    <p class="rw-cta__phone">Or call direct: <a href="tel:9494385948">(949) 438-5948</a></p>
  </div>
</section>
"""


MAIN_BODY = STYLE + '<article class="rw-story">' + PHOTO_BAND + MASTHEAD + STORY + DREAM + GALLERY + DEAL + EXECUTION + POOL + FINAL + CROSSLINKS + CTA + "</article>"


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
        "https://drozq.com/media/images/euclid/pool-dusk.webp",
        "https://drozq.com/media/images/euclid/living-room.webp",
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


def postprocess() -> None:
    path = ROOT / PAGE_PATH
    text = path.read_text(encoding="utf-8")

    text, css_count = re.subn(
        r'<style id="drozq-hero-rotate-css">.*?</style>',
        '<style id="drozq-page-chrome">@layer base{#__next>header{position:fixed !important;top:0;left:0;right:0}}#__next>header{box-shadow:0 1px 5px rgba(0,0,0,.11)}body{padding-top:48px}@media(min-width:768px){body{padding-top:64px}}[id]{scroll-margin-top:80px}</style>',
        text,
        count=1,
        flags=re.DOTALL,
    )
    if css_count != 1:
        raise RuntimeError(f"Expected one homepage hero CSS block, found {css_count}")

    text, js_count = re.subn(
        r'<script id="drozq-hero-rotate-js">.*?</script>',
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )
    if js_count != 1:
        raise RuntimeError(f"Expected one homepage hero JS block, found {js_count}")

    text, faq_count = re.subn(
        r'<script type="application/ld\+json">(?=[^<]*"@type":"FAQPage")[^<]*</script>',
        "",
        text,
        count=1,
    )
    if faq_count != 1:
        raise RuntimeError(f"Expected one inherited FAQPage schema, found {faq_count}")

    text, twitter_count = re.subn(
        r'<meta name="twitter:image" content="[^"]+">',
        f'<meta name="twitter:image" content="{OG_IMAGE}">',
        text,
        count=1,
    )
    if twitter_count != 1:
        raise RuntimeError(f"Expected one twitter:image tag, found {twitter_count}")

    meta_replacements = {
        '<meta property="og:type" content="website">': '<meta property="og:type" content="article">',
        '<meta property="og:image:width" content="1200">': '<meta property="og:image:width" content="1024">',
        '<meta property="og:image:height" content="630">': '<meta property="og:image:height" content="683">',
    }
    for old, new in meta_replacements.items():
        if text.count(old) != 1:
            raise RuntimeError(f"Expected one metadata tag: {old}")
        text = text.replace(old, new, 1)

    head_additions = (
        '<link rel="preload" as="image" href="/media/images/euclid/front-day.jpg" type="image/jpeg">'
        + json_script(ARTICLE_SCHEMA)
        + json_script(BREADCRUMB_SCHEMA)
    )
    if text.count("</head>") != 1:
        raise RuntimeError("Expected exactly one closing head tag")
    text = text.replace("</head>", head_additions + "</head>", 1)

    funnel_marker = "<!-- DROZQ_FUNNEL_HTML_BEGIN:"
    if text.count(funnel_marker) != 1:
        raise RuntimeError("Expected exactly one funnel HTML start marker")
    page_prefix, synced_funnel = text.split(funnel_marker, 1)
    page_prefix = "\n".join(line.rstrip() for line in page_prefix.splitlines()) + "\n"
    text = page_prefix + funnel_marker + synced_funnel

    path.write_text(text, encoding="utf-8")
    print(f"Postprocessed: {PAGE_PATH}")


if __name__ == "__main__":
    scaffold_page(
        target=PAGE_PATH,
        title="Richard W.'s First Home in Riverside | $15,000 Credit",
        description="After 22 years at Ralphs, Richard W. bought his first home at 4194 Euclid Ct with a $15,000 closing-cost credit and an early close.",
        canonical="/testimonials/003-riverside-first-home/",
        main_body_html=MAIN_BODY,
        og_title="Richard's first home. His family's new gathering place.",
        og_description="A Riverside pool home, $15,000 toward closing costs, an early close, and room for every generation.",
        twitter_title="Richard's First Home in Riverside",
        twitter_description="A Riverside pool home, $15,000 toward closing costs, an early close, and room for every generation.",
        og_image=OG_IMAGE,
    )
    postprocess()
