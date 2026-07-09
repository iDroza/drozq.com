"""Build /404.html, the site-wide not-found page, on the homepage template scaffold.

WHY THIS PAGE EXISTS:
Cloudflare Pages with no 404.html falls back to SPA mode and serves the
homepage with a 200 for every missing path. Google reads that as a soft-404
(duplicate homepage content on junk URLs, wasted crawl budget, dead URLs never
dropped from the index), analytics logs phantom pageviews on garbage paths,
and a visitor on a dead link silently gets the homepage under the wrong URL.
A root /404.html is served by Pages with a REAL 404 status for any missing
path, which fixes all three. Requesting /404.html directly returns 200, so
the page carries noindex,follow.

DESIGN:
- Hero: dark block (#1a1816 -> #2b2b2b) with a massive typographic backdrop,
  THE WORLD IS YOURS, in brand red: outlined strokes with YOURS solid.
  Stacks one word per line at mobile, two lines at md+. Pure CSS text, no
  image weight. Foreground is the canonical two-section hero: H1 blurb +
  one-sentence subhead, then the 3-tab funnel pill + trust line.
- Purpose switcher: the mid-page tabs pattern reframed as "what this site
  does" (I'm selling / I'm buying), each panel 3 numbered value points + the
  540px address pill.
- Destination grid: 6 interactive cards to the working pages (canonical
  hover lift + red border).
- Direct contact: the /contact/ page's phone / email / office card row,
  verbatim (no map iframe; the 404 stays light).
- Closing CTA: standard 540px pill + "Or call direct" fineprint.

Served at arbitrary URL depth, so every asset reference inherited from the
scaffold is root-absolute (verified).

NOT in sitemap.xml. Registered in funnels.json like every template page.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page


def landing_form_pill(placeholder: str, value: str = "") -> str:
    return f"""
    <form class="pos_relative">
      <div class="pos_relative d_flex flex-d_column xs:flex-d_row ai_center bg-c_#fff mb_16px xs:mb_0 h_48px sm:h_auto bdr_30px bx-sh_0_1px_5px_rgba(0,_0,_0,_.11)">
        <input name="location" placeholder="{placeholder}" title="{placeholder}" autocomplete="off"
               class="w_100% bd_none bg-c_transparent -webkit-appearance_none flex_1 focus:ring_none h_48px md:h_60px lh_48px md:lh_60px pt_16px md:pt_0 pb_16px md:pb_0 pl_16px md:pl_32px pr_32px xs:pr_8px mb_16px xs:mb_0 bdr-tl_30px bdr-bl_30px fs_14px md:fs_18px"
               value="{value}" aria-label="{placeholder}">
        <div class="w_100% xs:w_auto mr_0 md:mr_3px h_48px md:h_60px lh_48px md:lh_60px pos_absolute xs:pos_static top_60px xs:top_0">
          <button type="submit"
                  class="bg_primary c_white cursor_pointer w_100% xs:w_145px md:w_auto h_48px md:h_54px fs_13px md:fs_18px fw_bold bdr_full px_0px md:px_28px ls_0.5px d_block md:d_inline-flex ai_center gap_0px md:gap_10px hover:bg_primaryHover">
            See Plan
          </button>
        </div>
      </div>
      <input type="hidden" name="gclid" value="">
    </form>"""


# Scoped styles for the 404-specific pieces. Plain string (CSS braces).
# Every color resolves to a TEMPLATE.md section-1 token or an established
# /index.html value: #1a1816, #2b2b2b, #d92228, #fff, #e5e5e5, and the
# canonical hover shadow rgba(217,34,40,0.14) / hero tint rgba(26,24,22,x).
NF_STYLE = """
<style>
.nf-hero {
  background: linear-gradient(180deg, #1a1816 0%, #2b2b2b 100%);
  min-height: 100vh;
  min-height: 100svh;
  display: flex;
  flex-direction: column;
}
/* The words frame the content: THE WORLD above it, IS YOURS below it.
   MOBILE: the two word rows sit in NORMAL FLOW (row, copy, pill, row) so no
   viewport height can ever collide them with the foreground; the auto
   margins on the two content sections center the copy block between the
   rows when there is room and collapse to plain flow when there isn't.
   DESKTOP (min-width 768px): the rows pin absolutely to the hero's top and
   bottom edges, the original poster composition. */
.nf-row {
  position: relative;
  z-index: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: GalanoGrotesqueAltBold, "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-weight: 700;
  text-transform: uppercase;
  line-height: 0.9;
  letter-spacing: 0.02em;
  white-space: nowrap;
  font-size: clamp(56px, 20vw, 110px);
  overflow: hidden;
  pointer-events: none;
  -webkit-user-select: none;
  user-select: none;
}
.nf-row-top { padding-top: 60px; }
.nf-row-bottom { padding-bottom: 8px; }
.nf-sec-text { margin-top: auto; }
.nf-sec-pill { margin-bottom: auto; }
.nf-outline {
  color: transparent;
  -webkit-text-stroke: 2px rgba(217, 34, 40, 0.75);
}
@supports not (-webkit-text-stroke: 1px #d92228) {
  .nf-outline { color: rgba(217, 34, 40, 0.28); }
}
.nf-solid { color: #d92228; opacity: 0.9; }
.nf-hero-copy { text-shadow: 0 2px 24px rgba(26, 24, 22, 0.85), 0 1px 6px rgba(26, 24, 22, 0.9); }
/* Mobile pill: the See Plan button is absolutely positioned ~108px deep while
   the form only flows ~64px, so the trust line below needs explicit clearance. */
.nf-trust { margin-top: 48px; }
@media (min-width: 480px) {
  .nf-trust { margin-top: 0; }
}
@media (min-width: 768px) {
  .nf-hero { justify-content: center; }
  .nf-sec-text, .nf-sec-pill { margin-top: 0; margin-bottom: 0; }
  .nf-row {
    position: absolute;
    left: 0;
    right: 0;
    flex-direction: row;
    justify-content: center;
    gap: 0.24em;
    font-size: clamp(110px, 14.5vw, 210px);
  }
  .nf-row-top { top: 76px; padding-top: 0; }
  .nf-row-bottom { bottom: 16px; padding-bottom: 0; }
  .nf-outline { -webkit-text-stroke-width: 3px; }
}
.nf-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
@media (min-width: 768px) { .nf-grid { grid-template-columns: repeat(2, 1fr); gap: 20px; } }
@media (min-width: 992px) { .nf-grid { grid-template-columns: repeat(3, 1fr); } }
.nf-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px 28px;
  text-decoration: none;
  color: inherit;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}
.nf-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(217, 34, 40, 0.14);
  border-color: #d92228;
}
.nf-card-arrow { color: #d92228; font-weight: 700; font-size: 15px; margin-top: auto; }
</style>
"""


HERO = f"""
<div class="pos_relative ov_hidden nf-hero">
  <div class="nf-row nf-row-top" aria-hidden="true"><span class="nf-outline">The</span><span class="nf-outline">World</span></div>

  <section aria-labelledby="nf-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px nf-sec-text">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="nf-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px nf-hero-copy">This page doesn't exist.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0 nf-hero-copy">Your home's value does, so drop the address and leave with the number.</p>
    </div>
  </section>

  <section aria-label="Start your home valuation" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px nf-sec-pill">
    <div class="d_flex jc_center pl_32px pr_32px bx-s_border-box mb_24px">
      <div class="pos_relative w_100% max-w_700px">
        <div class="pos_relative" role="button" tabindex="0" aria-label="Property transaction type selector">
          <div class="d_flex jc_center gap_6px mb_0px">
            <div role="tablist" class="d_flex jc_center bdr_8px_8px_0_0 ov_hidden">
              <button role="tab" aria-selected="true"  aria-controls="tabpanel-sell"     id="tab-sell"     tabindex="0"
                      class="bdr_8px_8px_0_0 p_12px_16px fw_700 fs_13px lh_16px ta_center bg_#fff   c_#d92228 bd_none cursor_pointer as_flex-end [&:not(:first-child)]:ml_6px">Sell</button>
              <button role="tab" aria-selected="false" aria-controls="tabpanel-buy"      id="tab-buy"      tabindex="-1"
                      class="bdr_8px_8px_0_0 p_8px_16px  fw_700 fs_13px lh_16px ta_center bg_#d92228 c_#fff    bd_none cursor_pointer as_flex-end [&:not(:first-child)]:ml_6px [&:hover]:bg_#a92e2a">Buy</button>
              <button role="tab" aria-selected="false" aria-controls="tabpanel-sell-buy" id="tab-sell-buy" tabindex="-1"
                      class="bdr_8px_8px_0_0 p_8px_16px  fw_700 fs_13px lh_16px ta_center bg_#d92228 c_#fff    bd_none cursor_pointer as_flex-end [&:not(:first-child)]:ml_6px [&:hover]:bg_#a92e2a">Sell &amp; Buy</button>
            </div>
          </div>

          <div class="w_100% bdr_30px pos_relative min-h_60px">
            <div id="tabpanel-sell"     role="tabpanel" aria-labelledby="tab-sell"     class="d_block">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter the address you are selling")}</div>
            </div>
            <div id="tabpanel-buy"      role="tabpanel" aria-labelledby="tab-buy"      hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("City, neighborhood, or ZIP")}</div>
            </div>
            <div id="tabpanel-sell-buy" role="tabpanel" aria-labelledby="tab-sell-buy" hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter the address you are selling")}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <p class="ta_center op_0.85 c_#fff fs_12px md:fs_13px ls_1.5px fw_700 nf-hero-copy nf-trust" style="text-transform:uppercase">Joshua Guerrero &middot; Real Brokerage &middot; CA DRE #02267255</p>
  </section>

  <div class="nf-row nf-row-bottom" aria-hidden="true"><span class="nf-outline">Is</span><span class="nf-solid">Yours</span></div>
</div>
"""


PURPOSE_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Error 404 &middot; Page not found</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">The page is gone. What I do isn't.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">This site turns Southern California homes into sold signs: instant valuation, five seller playbooks, one agent running every hard part personally. Pick your side.</p>
    </div>

    <div role="tablist" keyboard-select-mode="focus"
         class="d_flex jc_center pos_relative bg_#fff max-w_251px w_100% h_48px m_0_auto bdr_24px bx-sh_0_1px_5px_rgba(0,0,0,.11) mt_14px bd_1px_solid_#e5e5e5">
      <button id="sellTabBtn" role="tab" aria-controls="sellTab" aria-selected="true"  data-selected="true"  type="button"
              class="ap_none bd_none bg_transparent cursor_pointer max-w_125px max-h_42px w_100% p_10px_16px bdr_999px fs_14px md:fs_16px fw_700 lh_20px ta_center m_3px_3px_0 c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:bg-c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:c_#fff">I'm selling</button>
      <button id="buyTabBtn"  role="tab" aria-controls="buyTab"  aria-selected="false" data-selected="false" type="button"
              class="ap_none bd_none bg_transparent cursor_pointer max-w_125px max-h_42px w_100% p_10px_16px bdr_999px fs_14px md:fs_16px fw_700 lh_20px ta_center m_3px_3px_0 c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:bg-c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:c_#fff">I'm buying</button>
    </div>

    <div id="sellTab" role="tabpanel" aria-labelledby="sellTabBtn" class="d_block mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <ul class="d_flex flex-d_column gap_24px lg:gap_44px m_0 li-s_none p_0 mb_32px">
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">1</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">An instant, defensible number.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">My valuation model prices your home from the same data investors and other buyers use: true market value, rebuild cost, and a same-day cash offer figure.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Five seller playbooks, free.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Pricing, marketing, negotiation, speed, concierge: the exact internal documents I run on every listing, sent the instant you finish.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Sold in about six weeks.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">A five-step listing system where the hard parts land on my desk, not yours.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Enter your address to start the home value report.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("Your address")}</div>
    </div>

    <div id="buyTab" role="tabpanel" aria-labelledby="buyTabBtn" hidden class="d_none mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <ul class="d_flex flex-d_column gap_24px lg:gap_44px m_0 li-s_none p_0 mb_32px">
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">1</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A buying strategy, not a property list.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">I help you decide what you are actually buying for, then narrow the field with a written framework.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Offers structured to actually win.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Tight contingencies, clean appraisal language, and seller credits used where they move price.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Lender, inspector, and escrow already in place.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">A vetted bench of local partners means escrow runs on schedule and inspection reports come back in plain English.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Tell me where you want to buy.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("City, neighborhood, or ZIP", value="Irvine, CA")}</div>
    </div>

  </div>
</section>
"""


# (title, body, href)
DOORS = [
    ("What's my home worth?",
     "The instant valuation: true market value, rebuild cost, and a cash-offer figure.",
     "/value/"),
    ("Today's mortgage rates",
     "Live rates for every loan program, refreshed daily, with a payment calculator.",
     "/rates/"),
    ("Where prices stand",
     "California home prices and market signals, straight from the data.",
     "/prices/"),
    ("How I sell your home",
     "Five steps, six to ten weeks, every hard part on my desk.",
     "/process/"),
    ("The case files",
     "Real clients, real negotiations, real numbers.",
     "/testimonials/"),
    ("The homepage",
     "The whole offer on one page, starting with your address.",
     "/"),
]


def door_card(title: str, body: str, href: str) -> str:
    return f"""
      <a href="{href}" class="nf-card">
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">{title}</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">{body}</p>
        <span class="nf-card-arrow" aria-hidden="true">&rarr;</span>
      </a>"""


DOORS_SECTION = """
<section aria-labelledby="nf-doors-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Where to next</p>
      <h2 id="nf-doors-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Every other door opens.</h2>
    </div>

    <div class="nf-grid">
""" + "\n".join(door_card(t, b, h) for (t, b, h) in DOORS) + """
    </div>
  </div>
</section>
"""


DIRECT_CONTACT = """
<section aria-labelledby="nf-direct-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Direct line</p>
      <h2 id="nf-direct-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Or skip the site. Reach me.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Call, text, email, or walk in. Same person answers every channel: me.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">

      <a href="tel:9494385948" class="bg-c_#f7f7f7 bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px ta_center td_none c_inherit hover:bd-c_#d92228 trs_all_.2s_ease">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 m_0_auto mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><path d="M14 6c-2 0-4 2-4 4 0 14 14 28 28 28 2 0 4-2 4-4v-6l-8-4-4 4c-6-2-10-6-12-12l4-4-4-8H14z" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/></svg>
        </div>
        <p class="c_#757575 fs_11px md:fs_12px fw_700 ls_1.5px m_0" style="text-transform:uppercase">Call or text</p>
        <p class="fs_20px md:fs_24px fw_700 c_#1a1816 lh_1.25 m_0">(949) 438-5948</p>
        <p class="fs_13px md:fs_14px c_#3f4650 m_0">Direct line. I answer it.</p>
      </a>

      <a href="mailto:Josh@Drozq.com" class="bg-c_#f7f7f7 bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px ta_center td_none c_inherit hover:bd-c_#d92228 trs_all_.2s_ease">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 m_0_auto mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><rect x="6" y="10" width="36" height="28" rx="3" stroke="currentColor" stroke-width="2.4"/><path d="M6 14l18 14L42 14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <p class="c_#757575 fs_11px md:fs_12px fw_700 ls_1.5px m_0" style="text-transform:uppercase">Email</p>
        <p class="fs_18px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Josh@Drozq.com</p>
        <p class="fs_13px md:fs_14px c_#3f4650 m_0">Reply within a few hours.</p>
      </a>

      <div class="bg-c_#f7f7f7 bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px ta_center">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 m_0_auto mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><path d="M24 6c-7 0-12 5-12 12 0 9 12 24 12 24s12-15 12-24c0-7-5-12-12-12z" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/><circle cx="24" cy="18" r="4" stroke="currentColor" stroke-width="2.4"/></svg>
        </div>
        <p class="c_#757575 fs_11px md:fs_12px fw_700 ls_1.5px m_0" style="text-transform:uppercase">Office</p>
        <p class="fs_15px md:fs_16px fw_700 c_#1a1816 lh_1.4 m_0">17875 Von Karman Ave<br>Suite 150, Irvine, CA 92614</p>
        <p class="fs_13px md:fs_14px c_#3f4650 m_0">Walk-ins welcome.</p>
      </div>

    </div>
  </div>
</section>
"""


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Before you go</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Leave with your home's number.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">A few quick questions, and the report lands the instant you finish.</p>

      <div id="nf-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


MAIN_BODY = (
    NF_STYLE
    + HERO
    + PURPOSE_TABS
    + DOORS_SECTION
    + DIRECT_CONTACT
    + CLOSING_CTA
)


if __name__ == "__main__":
    scaffold_page(
        target="404.html",
        title="Page Not Found | Joshua Guerrero, Real Brokerage",
        description="That link is dead. What this site does isn't: instant home valuation, five free seller playbooks, and a listing system that sells Southern California homes in about six weeks.",
        canonical="/404.html",
        main_body_html=MAIN_BODY,
        og_title="Page Not Found | Drozq",
        og_description="The page is gone. The world is yours: instant home valuation, five free seller playbooks, one agent.",
        noindex=True,
    )
