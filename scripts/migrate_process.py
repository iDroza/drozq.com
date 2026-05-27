"""Migrate /process/ to the homepage template scaffold.

Conversion-first treatment: 3-tab funnel hero (Sell / Buy / Sell & Buy),
5-step process body, total-timeline callout, mid-page "Why work with an
agent?" tabs, 5-question FAQ accordion, closing CTA.

Page-specific scoped CSS (only what's not already in Panda) lives in a
small <style> island at the top of <main>. Everything else uses the
homepage Panda CSS utility-class vocabulary so the page visually matches
/index.html.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page


def landing_form_pill(placeholder: str, value: str = "") -> str:
    """Replicates the homepage's address-pill landing form."""
    return f"""
    <form class="pos_relative">
      <div class="pos_relative d_flex flex-d_column xs:flex-d_row ai_center bg-c_#fff mb_16px xs:mb_0 h_48px sm:h_auto bdr_30px bx-sh_0_1px_5px_rgba(0,_0,_0,_.11)">
        <input name="location" placeholder="{placeholder}" title="{placeholder}" autocomplete="off"
               class="w_100% bd_none bg-c_transparent -webkit-appearance_none flex_1 focus:ring_none h_48px md:h_60px lh_48px md:lh_60px pt_16px md:pt_0 pb_16px md:pb_0 pl_16px md:pl_32px pr_32px xs:pr_8px mb_16px xs:mb_0 bdr-tl_30px bdr-bl_30px fs_14px md:fs_18px"
               value="{value}" aria-label="{placeholder}">
        <div class="w_100% xs:w_auto mr_0 md:mr_3px h_48px md:h_60px lh_48px md:lh_60px pos_absolute xs:pos_static top_60px xs:top_0">
          <button type="submit"
                  class="bg_primary c_white cursor_pointer w_100% xs:w_145px md:w_auto h_48px md:h_54px fs_13px md:fs_18px fw_bold bdr_full px_0px md:px_28px ls_0.5px d_block md:d_inline-flex ai_center gap_0px md:gap_10px hover:bg_primaryHover disabled:bg_primaryHover disabled:cursor_not-allowed">
            Compare Agents
          </button>
        </div>
      </div>
      <input type="hidden" name="gclid" value="">
    </form>"""


HERO = f"""
<div class="pos_relative ov_hidden">
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_100%_60% [&_img]:[@media_(max-width:_480px)]:obj-p_left">
    <img src="/media/images/crystal-cove.webp" alt="Crystal Cove coastline along the Newport Coast"
         width="1280" height="640" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.5)"></div>
  </div>

  <section aria-labelledby="process-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="process-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">How I sell your home.<br>Five steps. Six to ten weeks.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">The full path from your first call to keys in the buyer's hand.</p>
    </div>
  </section>

  <section aria-label="Compare real estate agents" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px">
    <div class="d_flex jc_center pl_32px pr_32px bx-s_border-box">
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
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("City and State or ZIP", value="Irvine, CA")}</div>
            </div>
            <div id="tabpanel-sell-buy" role="tabpanel" aria-labelledby="tab-sell-buy" hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter the address you are selling")}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>
"""


FIVE_STEPS = """
<section aria-labelledby="five-steps-title"
         class="bg_#fff d_block pt_48px md:pt_64px pb_48px md:pb_64px w_100% max-w_100% md:max-w_972px xl:max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

  <div class="ta_center mb_40px md:mb_56px">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Five Steps</p>
    <h2 id="five-steps-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">From first call to closing day.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px max-w_640px m_0_auto">A clear path. No improvised steps, no surprises. Here is what working with me actually looks like.</p>
  </div>

  <div class="d_flex flex-d_column gap_24px md:gap_32px max-w_860px m_0_auto">

    <article class="d_flex flex-d_row gap_20px md:gap_32px ai_flex-start p_24px md:p_32px bg-c_#fff bdr_16px bd_1px_solid_#e5e5e5 bx-sh_0_2px_8px_rgba(0,0,0,.04)">
      <div class="flex-sh_0 d_flex ai_center jc_center w_56px h_56px md:w_72px md:h_72px bdr_full bg-c_#d92228 c_#fff fw_700 fs_18px md:fs_24px ls_0.5px">01</div>
      <div class="flex_1">
        <div class="d_flex flex-d_column md:flex-d_row md:ai_baseline gap_4px md:gap_12px mb_8px">
          <h3 class="fw_700 fs_20px md:fs_24px lh_28px md:lh_32px c_#1a1816 m_0">First call</h3>
          <span class="d_inline-flex ai_center gap_6px c_#d92228 fs_12px md:fs_13px fw_700 ls_1px" style="text-transform:uppercase">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            15 minutes
          </span>
        </div>
        <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px m_0">Fill out the form or call me at <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a>. We spend 15 minutes on the phone so I can understand your home, your timeline, and your goals. <strong class="c_#1a1816 fw_700">A real conversation.</strong></p>
      </div>
    </article>

    <article class="d_flex flex-d_row gap_20px md:gap_32px ai_flex-start p_24px md:p_32px bg-c_#fff bdr_16px bd_1px_solid_#e5e5e5 bx-sh_0_2px_8px_rgba(0,0,0,.04)">
      <div class="flex-sh_0 d_flex ai_center jc_center w_56px h_56px md:w_72px md:h_72px bdr_full bg-c_#d92228 c_#fff fw_700 fs_18px md:fs_24px ls_0.5px">02</div>
      <div class="flex_1">
        <div class="d_flex flex-d_column md:flex-d_row md:ai_baseline gap_4px md:gap_12px mb_8px">
          <h3 class="fw_700 fs_20px md:fs_24px lh_28px md:lh_32px c_#1a1816 m_0">The walk-through</h3>
          <span class="d_inline-flex ai_center gap_6px c_#d92228 fs_12px md:fs_13px fw_700 ls_1px" style="text-transform:uppercase">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            At your home
          </span>
        </div>
        <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px m_0">I meet you at your home and walk every room. I tell you honestly what helps the sale and what hurts it. Most agents flatter you to win the listing. <strong class="c_#1a1816 fw_700">I don't.</strong></p>
      </div>
    </article>

    <article class="d_flex flex-d_row gap_20px md:gap_32px ai_flex-start p_24px md:p_32px bg-c_#fff bdr_16px bd_1px_solid_#e5e5e5 bx-sh_0_2px_8px_rgba(0,0,0,.04)">
      <div class="flex-sh_0 d_flex ai_center jc_center w_56px h_56px md:w_72px md:h_72px bdr_full bg-c_#d92228 c_#fff fw_700 fs_18px md:fs_24px ls_0.5px">03</div>
      <div class="flex_1">
        <div class="d_flex flex-d_column md:flex-d_row md:ai_baseline gap_4px md:gap_12px mb_8px">
          <h3 class="fw_700 fs_20px md:fs_24px lh_28px md:lh_32px c_#1a1816 m_0">Your market analysis</h3>
          <span class="d_inline-flex ai_center gap_6px c_#d92228 fs_12px md:fs_13px fw_700 ls_1px" style="text-transform:uppercase">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            Within 24 hours
          </span>
        </div>
        <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px m_0">Within 24 hours, you get a real comparative market analysis. Recent comps, active competition, recommended price, and a clear pricing strategy. <strong class="c_#1a1816 fw_700">You decide if and when to list.</strong></p>
      </div>
    </article>

    <article class="d_flex flex-d_row gap_20px md:gap_32px ai_flex-start p_24px md:p_32px bg-c_#fff bdr_16px bd_1px_solid_#e5e5e5 bx-sh_0_2px_8px_rgba(0,0,0,.04)">
      <div class="flex-sh_0 d_flex ai_center jc_center w_56px h_56px md:w_72px md:h_72px bdr_full bg-c_#d92228 c_#fff fw_700 fs_18px md:fs_24px ls_0.5px">04</div>
      <div class="flex_1">
        <div class="d_flex flex-d_column md:flex-d_row md:ai_baseline gap_4px md:gap_12px mb_8px">
          <h3 class="fw_700 fs_20px md:fs_24px lh_28px md:lh_32px c_#1a1816 m_0">Launch</h3>
          <span class="d_inline-flex ai_center gap_6px c_#d92228 fs_12px md:fs_13px fw_700 ls_1px" style="text-transform:uppercase">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>
            48 to 72 hours
          </span>
        </div>
        <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px m_0">Once you sign, your home is on the market in 48 to 72 hours. Professional photography, drone, walk-through video, MLS syndication, social campaigns, and a dedicated property page. All on a fixed timeline you can hold me to.</p>
      </div>
    </article>

    <article class="d_flex flex-d_row gap_20px md:gap_32px ai_flex-start p_24px md:p_32px bg-c_#fff bdr_16px bd_1px_solid_#e5e5e5 bx-sh_0_2px_8px_rgba(0,0,0,.04)">
      <div class="flex-sh_0 d_flex ai_center jc_center w_56px h_56px md:w_72px md:h_72px bdr_full bg-c_#d92228 c_#fff fw_700 fs_18px md:fs_24px ls_0.5px">05</div>
      <div class="flex_1">
        <div class="d_flex flex-d_column md:flex-d_row md:ai_baseline gap_4px md:gap_12px mb_8px">
          <h3 class="fw_700 fs_20px md:fs_24px lh_28px md:lh_32px c_#1a1816 m_0">Negotiate and close</h3>
          <span class="d_inline-flex ai_center gap_6px c_#d92228 fs_12px md:fs_13px fw_700 ls_1px" style="text-transform:uppercase">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            30 to 45 days
          </span>
        </div>
        <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px m_0">Offers come in. I walk you through each one so the trade-offs are clear. Then I manage every inspection, contingency, and milestone through close. <strong class="c_#1a1816 fw_700">30 to 45 days later, the wire hits your account.</strong></p>
      </div>
    </article>

  </div>

  <div class="mt_40px md:mt_56px max-w_860px m_0_auto p_24px md:p_32px bg-c_#fbf8f4 bdr_16px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_8px" style="text-transform:uppercase">Total timeline</p>
    <p class="c_#1a1816 fs_24px md:fs_32px fw_800 lh_32px md:lh_40px mb_8px">Six to ten weeks from listing to keys.</p>
    <p class="c_#3f4650 fs_15px md:fs_16px lh_24px m_0">In Orange County, a well-priced home typically goes under contract in 14 to 30 days, followed by 30 to 45 days of escrow. I build a specific timeline for your situation on the first call.</p>
  </div>

</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Why work with an agent?</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">The five steps above only work if the agent driving them shows up. Here is the difference an agent makes, whether you are selling or buying.</p>
    </div>

    <div role="tablist" keyboard-select-mode="focus"
         class="d_flex jc_center pos_relative bg_#fff max-w_251px w_100% h_48px m_0_auto bdr_24px bx-sh_0_1px_5px_rgba(0,0,0,.11) mt_14px">
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
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">I anchor every CMA to current submarket data, not last year's headlines.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Marketing that earns the listing premium.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Professional photography, walkthrough video, paid syndication. Marketing pays for itself in days saved on market.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">One agent. One phone. Same-hour replies.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">You text me, I answer. Every milestone routes through me on the same number.</p>
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


def faq_item(idx: int, q: str, a: str) -> str:
    return f"""
    <section data-expanded="false" class="m_0">
      <button type="button" data-expanded="false" aria-expanded="false" aria-controls="process-faq-{idx}-content" id="process-faq-{idx}-header" data-has-custom-icon="true"
              class="d_flex ai_center jc_space-between w_100% p_10px_40px_16px_0 bg-c_transparent bd_none cursor_pointer fs_14px md:fs_16px lh_24px md:lh_32px ta_left pos_relative bd-b_1px_solid_rgba(75,_92,_117,_0.1019607843) focus:ring_none">
        <h3 class="flex_1 fw_400 fs_16px">{q}</h3>
        <div class="pos_absolute right_0 d_flex ai_center jc_center w_20px h_20px">
          <svg width="14" height="14" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 6L10 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
            <path class="faq-icon-vertical" d="M6 2L6 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
          </svg>
        </div>
      </button>
      <div class="ov_hidden max-h_0 trs_max-height_0.2s_ease-out" id="process-faq-{idx}-content" role="region" aria-labelledby="process-faq-{idx}-header" style="max-height: 0px;">
        <div class="accordion-inner-content ov_hidden fs_16px fw_400 lh_24px bdr_16px mt_16px p_16px bg-c_#f7f7f7">{a}</div>
      </div>
    </section>"""


FAQ_ITEMS = [
    ("What should I look for in a listing agent?",
     "Three things. How fast they respond to you during the sales process (a slow agent before you sign will be a slow agent after). Whether they'll tell you uncomfortable truths instead of just flattering you. And their track record in your specific price band and area. Everything else is noise."),
    ("What areas do you serve?",
     "I'm based in Irvine and work most densely across Orange County (Irvine, Newport Beach, Costa Mesa, Tustin, Lake Forest, Mission Viejo, Laguna Niguel) and the South Bay (Long Beach, Manhattan Beach, Hermosa Beach, Torrance). For sellers elsewhere in California, I work through a vetted referral network of agents I trust personally."),
    ("Is this process different from other agents?",
     'The five steps themselves are fairly standard across good agents. What separates agents isn\'t the steps, it\'s how many of them actually happen on time, how honestly you\'re treated at each stage, and how much work gets done when nobody\'s watching. If you want to see what that looks like in practice, the <a href="/testimonials/" class="c_#d92228 fw_700">case files</a> are worth reading.'),
    ("How long does the process take?",
     "In Orange County, a well-priced home typically goes under contract in 14 to 30 days, followed by 30 to 45 days of escrow. Six to ten weeks total from listing to keys. I build a specific timeline for your situation on the first call and update it at every milestone."),
    ("Do I need to make repairs before listing?",
     "Usually, no. Over-improving before a sale is one of the fastest ways sellers burn money. A fresh coat of paint, minor landscaping, and a deep clean almost always return more than they cost. A full kitchen remodel almost never does. I walk through your home and tell you the three improvements worth making and the three not to bother touching."),
]


FAQ = """
<section class="max-w_1035px mt_48px md:mt_64px mb_64px mx_auto pl_32px md:pl_16px pr_32px md:pr_16px">
  <div class="ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Common Questions</p>
    <h2 class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_45px fs_24px md:fs_30px mb_32px md:mb_48px ta_center">Questions sellers ask.</h2>
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
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Ready when you are</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Start with a 15-minute call.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Drop your address. You will get a free comparative market analysis within 24 hours, an honest read on whether listing now makes sense, and a real conversation about your timeline.</p>

      <div id="process-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your home address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


MAIN_BODY = HERO + FIVE_STEPS + MID_TABS + FAQ + CLOSING_CTA


if __name__ == "__main__":
    scaffold_page(
        target="process/index.html",
        title="The Process | How I Sell Your Home | Joshua Guerrero",
        description="How I sell your home: five steps, six to ten weeks. From first call to closing day, with timing, deliverables, and no surprises.",
        canonical="/process/",
        main_body_html=MAIN_BODY,
        og_title="How I Sell Your Home | The Process | Joshua Guerrero",
        og_description="Five steps. Six to ten weeks. The full path from first call to keys in the buyer's hand.",
    )
