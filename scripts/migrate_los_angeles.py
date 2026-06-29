"""Migrate /los-angeles/ to the homepage template scaffold.

Conversion-first treatment: 3-tab funnel hero with LA-specific copy, LA
market data (21 bullets), anti-claim 6-tile block, mid-page tabs,
LA County seal + market context, 6 LA-specific FAQ, closing CTA.

KILLED from the legacy page:
- "5-Star Rated on Google" stat (violates CLAUDE.md voice principle:
  no star ratings or platform-aggregated reviews).
- "Backed by 5-Star Local Reviews".
- Brand-mode mint hero, 510-935-5701 phone, brand-mode navy footer.

PRESERVED + reframed:
- LA-specific H1 (rewritten: "Sell your Los Angeles home, on your
  timeline." replaces "Sell Your Los Angeles Home For Top Dollar"
  which was generic).
- 21 LA market bullets (2-col layout).
- Anti-claim 6-tile block ("NO UPFRONT FEES", etc.).
- LA County Seal + the 4 paragraphs of LA market context.
- 6 LA-specific FAQ questions.
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


HERO = f"""
<div class="pos_relative ov_hidden">
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_100%_60% [&_img]:[@media_(max-width:_480px)]:obj-p_left">
    <img src="/media/images/coastal-modern-home.webp" alt="Modern hillside home overlooking the Southern California coast at sunset" width="1672" height="941" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.4)"></div>
  </div>

  <section aria-labelledby="la-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="la-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">Sell your Los Angeles home, on your timeline.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Sharp pricing, modern marketing, and one agent who picks up the phone.</p>
    </div>
  </section>

  <section aria-label="Compare Los Angeles real estate agents" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px">
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
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter your LA address")}</div>
            </div>
            <div id="tabpanel-buy"      role="tabpanel" aria-labelledby="tab-buy"      hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("LA neighborhood, city, or ZIP", value="Los Angeles, CA")}</div>
            </div>
            <div id="tabpanel-sell-buy" role="tabpanel" aria-labelledby="tab-sell-buy" hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter your LA address")}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </section>
</div>
"""


HOW_I_HELP = """
<section aria-labelledby="la-help-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

    <div class="ta_center mb_32px md:mb_48px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Selling in LA, Simplified</p>
      <h2 id="la-help-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Top dollar without the usual stress.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">I help LA homeowners sell for more without rushed cash offers, confusing paperwork, or guessing on price. Here is what you get when you list with me.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(2,_1fr) gap_x_40px gap_y_4px max-w_950px m_0_auto">
      <ul class="li-s_none m_0 p_0">
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>A local LA listing agent who actually knows your submarket.</span></li>
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>Pricing built on this week's comps and real buyer demand.</span></li>
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>Showings scheduled around your life, not random strangers.</span></li>
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>Clear guidance on which repairs return their cost and which to skip.</span></li>
      </ul>
      <ul class="li-s_none m_0 p_0">
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>Vetted vendor network so you avoid predatory contractors.</span></li>
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>Pre-qualified buyers so you avoid last-minute back-outs.</span></li>
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>A closing date that actually fits your timeline.</span></li>
        <li class="d_flex ai_flex-start gap_12px py_12px fs_15px md:fs_16px lh_1.5 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>One agent. One phone. Same-hour replies during business hours.</span></li>
      </ul>
    </div>

  </div>
</section>
"""


ANTI_CLAIMS = """
<section aria-labelledby="la-no-block-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">
    <div class="ta_center mb_40px max-w_780px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">What you don't get</p>
      <h2 id="la-no-block-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Six things I will not put you through.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Most listing pitches lead with what they promise. These are the things I refuse to do, on every LA listing, with no exceptions.</p>
    </div>

    <div class="d_grid grid-tc_1fr xs:grid-tc_1fr_1fr lg:grid-tc_1fr_1fr_1fr gap_16px md:gap_20px">
      <div class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5">
        <div class="fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_8px">NO</div>
        <div class="fs_18px md:fs_20px fw_700 c_#1a1816 mb_8px lh_1.3">Upfront fees.</div>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">You pay nothing to list, nothing for photography, nothing for staging consults. Commissions come out of closing, not your savings account.</p>
      </div>
      <div class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5">
        <div class="fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_8px">NO</div>
        <div class="fs_18px md:fs_20px fw_700 c_#1a1816 mb_8px lh_1.3">Double commissions.</div>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">No bait-and-switch fee structure. The number we agree to in writing is the number on the closing statement, broken out line by line.</p>
      </div>
      <div class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5">
        <div class="fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_8px">NO</div>
        <div class="fs_18px md:fs_20px fw_700 c_#1a1816 mb_8px lh_1.3">Lowball offers.</div>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Your home is not a wholesale flip. I price it to the LA submarket and the actual condition, then negotiate from a number you and I both believe in.</p>
      </div>
      <div class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5">
        <div class="fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_8px">NO</div>
        <div class="fs_18px md:fs_20px fw_700 c_#1a1816 mb_8px lh_1.3">Repairs required.</div>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">You don't have to renovate to list. We walk the home together and decide which fixes actually move the needle, and which are wasted money.</p>
      </div>
      <div class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5">
        <div class="fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_8px">NO</div>
        <div class="fs_18px md:fs_20px fw_700 c_#1a1816 mb_8px lh_1.3">Surprises.</div>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Every milestone, every credit, every contingency gets flagged before it lands. You see the calendar and the dollar figures before they are official.</p>
      </div>
      <div class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5">
        <div class="fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_8px">NO</div>
        <div class="fs_18px md:fs_20px fw_700 c_#1a1816 mb_8px lh_1.3">Hassles.</div>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Showings, disclosures, escrow paperwork, contractor coordination. I handle the friction so your week looks like your week.</p>
      </div>
    </div>
  </div>
</section>
"""


MARKET_DATA_BULLETS = [
    "Home prices in Los Angeles rose roughly 4-6% year-over-year through 2025, continuing a long upward trend of nearly 90% over the last decade.",
    "Los Angeles remains the second-largest city in the United States.",
    "The current median home price in Los Angeles is approximately $975,000 as of early 2026.",
    "High interest rates and tightened lender standards continue to shape buyer demand across Southern California in 2025-2026.",
    "Most California cities continue to receive C-minus ratings for efforts to deliver affordable housing.",
    "The median household income in Los Angeles is around $76,000, still outpaced by housing and rent prices.",
    "Home prices cooled from 2022 peaks, with some LA submarkets seeing price corrections of 10 to 15% before stabilizing.",
    "Los Angeles remains one of the most expensive housing markets in the country, with record highs still recent memory.",
    "Single-family home prices across California have softened slightly year-over-year but remain historically elevated.",
    "Despite its high cost of living, Los Angeles has met more of California's state-mandated housing goals than most neighboring cities.",
    "Rental prices in Los Angeles have risen roughly 8 to 11% over the past two years, with average monthly rent near $2,800.",
    "Los Angeles earned high marks from the Southern California News Group for its affordable housing efforts relative to peer cities.",
    "Overinflated housing prices that began climbing in 2020 continue to push many buyers out of the market.",
    "California home sales volume remains below pre-pandemic norms due to low inventory and elevated mortgage rates.",
    "Cities across the United States, including Los Angeles, continue to face challenges delivering affordable housing.",
    "Mortgage rates edged lower heading into 2026 but remain meaningfully above the lows of 2020-2021.",
    "Forecasts for 2025-2026 point to continued price growth in LA, driven by strong demand and a persistent shortage of homes for sale.",
    "The population of Los Angeles is approximately 3.82 million as of 2025.",
    "California is still experiencing a structural housing shortage, keeping pressure on prices.",
    "The LA housing market continues to shift, making it a critical time for current and prospective homeowners to watch.",
    "Los Angeles continues to see a growing homeless population tied to the ongoing affordability crisis.",
]


def market_bullet(text: str) -> str:
    return f'<li class="d_flex ai_flex-start gap_12px py_10px fs_14px md:fs_15px lh_1.6 c_#2b2b2b"><span class="c_#0a801f fw_700 flex-sh_0">&#10003;</span><span>{text}</span></li>'


_half = (len(MARKET_DATA_BULLETS) + 1) // 2
MARKET_DATA = """
<section aria-labelledby="la-market-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

    <div class="ta_center mb_32px md:mb_48px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">LA, by the numbers</p>
      <h2 id="la-market-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The LA market, 2025-2026.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Pricing a Los Angeles listing without these numbers is guesswork. I anchor every CMA to current submarket data, not last year's headlines.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_1fr_1fr gap_x_40px gap_y_0 max-w_950px m_0_auto">
      <ul class="li-s_none m_0 p_0">
""" + "\n".join(market_bullet(b) for b in MARKET_DATA_BULLETS[:_half]) + """
      </ul>
      <ul class="li-s_none m_0 p_0">
""" + "\n".join(market_bullet(b) for b in MARKET_DATA_BULLETS[_half:]) + """
      </ul>
    </div>

  </div>
</section>
"""


KEY_STATS = """
<section aria-labelledby="la-key-stats-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Key LA Stats and Facts</p>
      <h2 id="la-key-stats-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center">The bigger picture.</h2>
    </div>

    <div class="d_grid grid-tc_1fr lg:grid-tc_220px_1fr gap_32px md:gap_48px ai_start max-w_950px m_0_auto">
      <div class="ta_center lg:ta_left">
        <img src="/media/icons/county-seal-for-los-angeles-california-768x768.webp"
             alt="Los Angeles County Seal" width="180" height="180" loading="lazy" decoding="async"
             class="d_block m_0_auto lg:m_0">
      </div>
      <div class="c_#3f4650 fs_15px md:fs_17px lh_1.7">
        <p class="mb_16px">As of 2025, Los Angeles, the second-largest city in the U.S., hosts a population of approximately 3.82 million. Despite its high cost of living, the city has outperformed many other Californian cities in its efforts to provide affordable housing, earning strong marks from the Southern California News Group while many peer cities lag with C-minus ratings. While property prices in Los Angeles have nearly doubled over the last decade, recent years have brought modest corrections in certain submarkets, with some areas seeing price drops of 10 to 15% before stabilizing.</p>
        <p class="mb_16px">Even so, the median home price sits near $975,000, well ahead of the city's roughly $76,000 median household income. Rents have climbed too, with average monthly rent for an apartment near $2,800. The housing market continues to navigate higher mortgage rates, tighter lending standards, and ongoing inventory shortages heading into 2026.</p>
        <p class="mb_16px">California remains in a structural housing shortage, which keeps upward pressure on prices of available properties. With limited new construction and steady demand from buyers waiting on the sidelines, supply has stayed tight across most LA submarkets.</p>
        <p class="m_0">Even with some moderation in single-family home prices and slightly easing mortgage rates, the gap between local incomes and housing costs remains significant. Forecasts for 2025-2026 point to continued price growth and elevated interest rates driven by high demand and a shortage of homes for sale.</p>
      </div>
    </div>

  </div>
</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Why work with an agent in LA?</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">Pick the side that matches your move. The form opens a short qualifier I see in real time.</p>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Pricing built on this week, not last year.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">LA submarkets move on their own clocks. I pull active and pending comps inside your specific corridor before quoting a number.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Marketing that earns the listing premium.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Professional photography, walkthrough video, paid syndication, and a real pre-list prep plan. Marketing pays for itself in days saved on market.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">One agent. One phone. Same-hour replies.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">You text me, I answer. Every offer, escrow question, and timeline shift routes through me on the same number.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Enter your LA address to start the home value report.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("Your LA address")}</div>
    </div>

    <div id="buyTab" role="tabpanel" aria-labelledby="buyTabBtn" hidden class="d_none mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <ul class="d_flex flex-d_column gap_24px lg:gap_44px m_0 li-s_none p_0 mb_32px">
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">1</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Search across LA without losing your shortlist.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">From the Westside to the Valley to the South Bay, I keep your shortlist tight, with real notes on why each home is in or out.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Offers written to win, not to look pretty.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Strategy depends on the listing. Tight contingencies, clean appraisal language, and seller credits used where they actually move price.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Lender, inspector, and escrow already in place.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">A vetted bench of LA-specific partners means escrow runs on schedule and inspection reports come back in plain English.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Tell me where you want to buy.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("City, neighborhood, or ZIP", value="Los Angeles, CA")}</div>
    </div>

  </div>
</section>
"""


def faq_item(idx: int, q: str, a: str) -> str:
    return f"""
    <section data-expanded="false" class="m_0">
      <button type="button" data-expanded="false" aria-expanded="false" aria-controls="la-faq-{idx}-content" id="la-faq-{idx}-header" data-has-custom-icon="true"
              class="d_flex ai_center jc_space-between w_100% p_10px_40px_16px_0 bg-c_transparent bd_none cursor_pointer fs_14px md:fs_16px lh_24px md:lh_32px ta_left pos_relative bd-b_1px_solid_rgba(75,_92,_117,_0.1019607843) focus:ring_none">
        <h3 class="flex_1 fw_400 fs_16px">{q}</h3>
        <div class="pos_absolute right_0 d_flex ai_center jc_center w_20px h_20px">
          <svg width="14" height="14" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 6L10 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
            <path class="faq-icon-vertical" d="M6 2L6 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
          </svg>
        </div>
      </button>
      <div class="ov_hidden max-h_0 trs_max-height_0.2s_ease-out" id="la-faq-{idx}-content" role="region" aria-labelledby="la-faq-{idx}-header" style="max-height: 0px;">
        <div class="accordion-inner-content ov_hidden fs_16px fw_400 lh_24px bdr_16px mt_16px p_16px bg-c_#f7f7f7">{a}</div>
      </div>
    </section>"""


FAQ_ITEMS = [
    ("What should I look for when choosing a Los Angeles listing agent?",
     "Look for a local agent with real LA submarket knowledge, a transparent pricing strategy, and a full-service marketing plan, not just a sign in the yard and an MLS entry. Check recent closed sales in your submarket, ask how the agent handles disclosures and escrow, and pay attention to how quickly they reply before you sign anything. Work with someone who picks up the phone and explains a CMA without hand-waving."),
    ("Which Los Angeles neighborhoods do you list in?",
     "I list throughout Los Angeles County, from the Westside to the South Bay to the San Fernando Valley and Northeast LA. If your home is in a submarket I have not personally closed in, I will tell you directly and either staff the listing accordingly or refer you to a trusted partner in my network. The goal is the right answer for your address, not the easiest answer for me."),
    ("Do all listing agents follow the same process?",
     "No. Experience, marketing budget, and negotiation skill vary widely. My process starts with a no-pressure consultation, a real walk-through of your home, and a written pricing strategy with comp packets attached. You see the numbers and the marketing plan before you sign anything, so the decision is informed, not pressured."),
    ("How long do Los Angeles home sales take right now?",
     "Most well-priced, well-marketed LA listings go under contract in 14 to 28 days and close within 30 to 45 days. I can also run faster private-sale or off-MLS timelines when your situation calls for one, and I will say so up front if that fits your case better than a public listing."),
    ("Do I have to pay anything upfront to list my home?",
     "No. There are no upfront fees to list. Commissions are only paid at closing, directly from sale proceeds. Photography, staging consults, and pre-list prep coordination are included, and any third-party costs you might consider are previewed in writing before you decide."),
    ("Will you list my home if it is in rough condition?",
     "Yes. I list homes in every condition across LA, from move-in ready to deferred-maintenance fixer to tenant-occupied. You do not need to clean, stage, or renovate before we talk. We walk it together, decide which repairs return their cost, and price the listing to the home as it actually is."),
]


FAQ = """
<section class="max-w_1035px mt_48px md:mt_64px mb_64px mx_auto pl_32px md:pl_16px pr_32px md:pr_16px">
  <div class="ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">FAQ</p>
    <h2 class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_45px fs_24px md:fs_30px mb_32px md:mb_48px ta_center">Common questions from LA homeowners.</h2>
  </div>
  <div class="d_block w_100% m_0_auto bd_none c_textBody [&:last-child_button]:bd-b_none">
""" + "\n".join(faq_item(i + 1, q, a) for i, (q, a) in enumerate(FAQ_ITEMS)) + """
  </div>
</section>
"""


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Start your LA home value report</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Free CMA. Sharp pricing. Real LA expertise.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Enter your address. I will follow up within the hour with a real number, a written marketing plan, and a proposed timeline.</p>

      <div id="la-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your LA address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


MAIN_BODY = HERO + HOW_I_HELP + ANTI_CLAIMS + MARKET_DATA + KEY_STATS + MID_TABS + FAQ + CLOSING_CTA


if __name__ == "__main__":
    scaffold_page(
        target="los-angeles/index.html",
        title="Sell Your Los Angeles Home | Joshua Guerrero, Real Brokerage",
        description="Selling a home in Los Angeles County? Joshua Guerrero, licensed CA REALTOR&reg; at Real Brokerage. Free CMA, sharp pricing, modern marketing. No 5-star fluff.",
        canonical="/los-angeles/",
        main_body_html=MAIN_BODY,
        og_title="Sell Your Los Angeles Home | Joshua Guerrero",
        og_description="LA listing agent. Free CMA in 24 hours. Sharp pricing, modern marketing, one phone line. DRE #02267255.",
    )
