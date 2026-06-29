"""Migrate /california/ to the homepage template scaffold.

State-level positioning page. The unique value prop is the three-tier
geography model (Direct service / Active service / Statewide referral).
Conversion-first treatment: 3-tab funnel hero, honest scope section,
3-tier geography cards, why-work-with-me cards, mid-page tabs, market
context with link to /market-insights/, case file proof, 6 CA-specific
FAQ, closing CTA, JSON-LD preserved (RealEstateAgent + BreadcrumbList +
FAQPage).

KILLED from the legacy page:
- Brand-mode hero with the outside-home-pic1.webp background (replaced
  with coastal-modern.webp for consistency with /los-angeles/).
- 510-935-5701 phone line in header/footer/modal (the homepage scaffold
  carries 949-438-5948 site-wide).
- Brand-mode lead-modal flow (replaced with inline funnel via
  always-inline directive).
- /contact/ link CTAs on closing block + market section (replaced with
  inline funnel-opening Sell-mode pill + phone fineprint).
- Brand-mode navy footer + topbar (homepage scaffold carries minimal
  conversion footer).

PRESERVED + reframed:
- The three-tier geography model (Direct / Active / Referral). This is
  the page's unique angle and the reason it exists.
- The "honest version" framing about local-vs-statewide.
- Why-work-with-me copy (Negotiation / Documented results /
  Responsiveness).
- 6 CA-specific FAQ items verbatim.
- All three JSON-LD blocks (RealEstateAgent with full areaServed,
  BreadcrumbList, FAQPage).
- Two case file preview cards (001 Long Beach + 002 Corona).
- Market context paragraphs (rewritten as a narrower section that
  links to /market-insights/).
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
<div class="pos_relative ov_hidden d_flex flex-d_column jc_center" style="min-height:100vh;min-height:100svh">
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_100%_60% [&_img]:[@media_(max-width:_480px)]:obj-p_right">
    <img src="/media/images/coastal-modern.webp" alt="Modern hillside home overlooking the Southern California coast at sunset" width="1672" height="941" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0)"></div>
  </div>

  <section aria-labelledby="ca-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="ca-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">Selling a home in California, done right.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Irvine-based REALTOR&reg;, direct across Orange County and the South Bay, partnered everywhere else.</p>
    </div>
  </section>

  <section aria-label="Compare California real estate agents" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px">
    <div class="d_flex jc_center pl_32px pr_32px bx-s_border-box">
      <div style="width:100%; max-width: 540px;">
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
            <div id="tabpanel-sell"     role="tabpanel" aria-labelledby="tab-sell"     class="d_block">{landing_form_pill("Enter your California address")}</div>
            <div id="tabpanel-buy"      role="tabpanel" aria-labelledby="tab-buy"      hidden class="d_none">{landing_form_pill("City, neighborhood, or ZIP", value="California")}</div>
            <div id="tabpanel-sell-buy" role="tabpanel" aria-labelledby="tab-sell-buy" hidden class="d_none">{landing_form_pill("Enter your California address")}</div>
          </div>
        </div>
      </div>
    </div>

  </section>
</div>
"""


HONEST = """
<section aria-labelledby="ca-honest-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_640px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Honest Version</p>
      <h2 id="ca-honest-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">What "serves California" actually means.</h2>
    </div>

    <div class="c_#3f4650 fs_16px md:fs_17px lh_26px md:lh_28px">
      <p class="mb_16px">Most agents who claim to serve all of California are exaggerating. Real estate is hyper-local. The agent who wins your listing in Bakersfield isn't the same one who wins it in Beverly Hills. I'd rather tell you the truth.</p>
      <p class="mb_16px">I work most densely in Orange County and the South Bay. That's where I show up in person, walk your home, manage your listing, and negotiate your deal. If you're selling in those markets, you get my full attention.</p>
      <p class="m_0">Outside Orange County and the South Bay, I work through a vetted referral network of California agents I've personally chosen. Same standards. Same accountability. You still benefit from my involvement on strategy and structure, just with a local expert physically running the day-to-day.</p>
    </div>
  </div>
</section>
"""


GEOGRAPHY = """
<section aria-labelledby="ca-geo-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Geography</p>
      <h2 id="ca-geo-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Three tiers. One standard.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">How I cover California honestly. The level of involvement scales with how close you are to me. The standard does not.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="9" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="3" fill="currentColor"/></svg>
        </div>
        <p class="fs_11px md:fs_12px fw_700 ls_2px c_#3f4650 m_0" style="text-transform:uppercase">Irvine &amp; Orange County</p>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Direct service</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Where I'm based and where I work most densely. I personally manage every listing, every showing, every negotiation. Irvine, Newport Beach, Costa Mesa, Tustin, Lake Forest, Mission Viejo, Laguna Niguel, Aliso Viejo, and surrounding communities.</p>
      </article>

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="24" cy="24" r="6" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="13" stroke="currentColor" stroke-width="2" stroke-dasharray="2 3"/><circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="1.8" stroke-dasharray="2 4" opacity="0.7"/></svg>
        </div>
        <p class="fs_11px md:fs_12px fw_700 ls_2px c_#3f4650 m_0" style="text-transform:uppercase">LA County &amp; South Bay</p>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Active service</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Markets where I work regularly and have closed transactions. Long Beach, Manhattan Beach, Hermosa Beach, Redondo Beach, Torrance, El Segundo, and the broader South Bay. Same level of personal involvement, with travel built into the timeline.</p>
      </article>

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="10" cy="10" r="4" stroke="currentColor" stroke-width="2.4"/><circle cx="38" cy="10" r="4" stroke="currentColor" stroke-width="2.4"/><circle cx="10" cy="38" r="4" stroke="currentColor" stroke-width="2.4"/><circle cx="38" cy="38" r="4" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="5" fill="currentColor"/><path d="M13 13l8 8M35 13l-8 8M13 35l8-8M35 35l-8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </div>
        <p class="fs_11px md:fs_12px fw_700 ls_2px c_#3f4650 m_0" style="text-transform:uppercase">Statewide</p>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Referral network</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">For sellers outside my direct markets, I work through a network of vetted California agents I've personally chosen. You still get my involvement on strategy and structure. They handle the in-person work. Every referral is one I'd send my own family to.</p>
      </article>

    </div>
  </div>
</section>
"""


WHY = """
<section aria-labelledby="ca-why-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Why Work With Me</p>
      <h2 id="ca-why-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">What you get when you hire me.</h2>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">

      <article class="bg-c_#f2f0ef bdr_16px p_24px md:p_28px d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="10" stroke="currentColor" stroke-width="2.4"/><path d="M24 4v8M24 36v8M4 24h8M36 24h8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>
        </div>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Negotiation that translates.</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">I learned negotiation in the most adversarial sales environment in America (car sales) before moving into real estate. 20 units a month average. The skill set transfers directly. When I sit across from a buyer's agent on your deal, I already know how the conversation ends.</p>
      </article>

      <article class="bg-c_#f2f0ef bdr_16px p_24px md:p_28px d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><rect x="11" y="6" width="26" height="36" rx="3" stroke="currentColor" stroke-width="2.4"/><path d="M17 17h14M17 24h14M17 31h10" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>
        </div>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Documented results.</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Every transaction I close becomes a case file with the actual numbers, the actual negotiation, and the actual outcome. You can read them before we even talk. Most agents ask you to trust them. I show you the receipts.</p>
      </article>

      <article class="bg-c_#f2f0ef bdr_16px p_24px md:p_28px d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><path d="M26 4L12 28h10L22 44l14-24H26L26 4z" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" fill="none"/></svg>
        </div>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Responsiveness as a system.</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Deals die in silence. My communication cadence is built so you never wonder what's happening with your listing. Weekly updates during listing, every 48 hours during escrow, immediately when anything changes. No exceptions.</p>
      </article>

    </div>
  </div>
</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Why work with an agent in California?</h2>
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
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">California submarkets move on their own clocks. I pull active and pending comps inside your specific corridor before quoting a number.</p>
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

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Enter your California address to start the home value report.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("Your California address")}</div>
    </div>

    <div id="buyTab" role="tabpanel" aria-labelledby="buyTabBtn" hidden class="d_none mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <ul class="d_flex flex-d_column gap_24px lg:gap_44px m_0 li-s_none p_0 mb_32px">
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">1</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Search across California without losing your shortlist.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">From Orange County to the South Bay to the cities I cover through my referral network, I keep your shortlist tight with real notes on why each home is in or out.</p>
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
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">A vetted bench of California-specific partners means escrow runs on schedule and inspection reports come back in plain English.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Tell me where you want to buy.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("City, neighborhood, or ZIP", value="California")}</div>
    </div>

  </div>
</section>
"""


MARKET = """
<section aria-labelledby="ca-market-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_640px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Market</p>
      <h2 id="ca-market-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">What's happening in California real estate right now.</h2>
    </div>

    <div class="c_#3f4650 fs_16px md:fs_17px lh_26px md:lh_28px mb_24px">
      <p class="mb_16px">The California market is not one market. It's a dozen. Inventory in Orange County is moving differently than the Inland Empire. The Bay Area follows different rules than the Central Valley. What I can tell you, statewide, is this: most California metros are seeing slowly increasing inventory, flat-to-soft demand, and longer expected market times than a year ago. That means pricing strategy matters more than it has in years.</p>
      <p class="m_0">If you want county-level data, that's what the Market Insights page is for. Here, the takeaway is simpler: this isn't 2021. The market rewards prepared, well-priced homes and punishes everything else.</p>
    </div>

    <div class="ta_center">
      <a href="/market-insights/" class="btn-secondary-outline">See county-by-county data &rarr;</a>
    </div>

  </div>
</section>
"""


PROOF = """
<style>
.ca-proof-card {
  transition: box-shadow .2s ease, transform .2s ease, border-color .2s ease;
}
.ca-proof-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(217, 34, 40, 0.14);
  border-color: #d92228;
}
.btn-secondary-outline {
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent; color: #d92228;
  border: 1px solid #d92228;
  font-weight: 700; font-size: 14px; letter-spacing: 0.3px;
  padding: 10px 22px; border-radius: 9999px;
  text-decoration: none;
  transition: background-color .2s ease, color .2s ease;
}
.btn-secondary-outline:hover { background: #d92228; color: #fff; }
@media (min-width: 768px) { .btn-secondary-outline { font-size: 15px; } }
</style>
<section aria-labelledby="ca-proof-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

    <div class="ta_center mb_40px max-w_640px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Proof</p>
      <h2 id="ca-proof-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Two recent California transactions.</h2>
      <p class="c_#3f4650 fs_16px md:fs_17px lh_26px md:lh_28px m_0">Every transaction I close becomes a documented case file. Real address, real numbers, real outcome. The clients are anonymized because discretion is part of the service.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(2,_1fr) gap_16px md:gap_20px mb_32px">

      <a href="/testimonials/001-long-beach-firefighter/" aria-label="Read Case File 001: Long Beach firefighter, first-time buyer"
         class="ca-proof-card bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_12px c_#1a1816" style="text-decoration:none;">
        <span class="as_flex-start fs_11px fw_700 ls_2px c_#d92228 bg-c_#fdecec bd_1px_solid_#d92228 bdr_4px p_6px_12px" style="text-transform:uppercase">Case File 001</span>
        <p class="fs_11px fw_700 ls_1.5px c_#3f4650 m_0" style="text-transform:uppercase">Long Beach &middot; First-Time Buyer</p>
        <h3 class="fs_18px md:fs_20px fw_700 c_#1a1816 lh_1.3 m_0">He spends his career protecting other people's homes. We helped him acquire his first.</h3>
        <div class="mt_auto pt_16px bd-t_1px_solid_#e5e5e5">
          <span class="d_block fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_4px" style="font-variant-numeric: tabular-nums;">$23,250</span>
          <span class="fs_13px c_#3f4650 fw_500">Seller credit negotiated</span>
        </div>
      </a>

      <a href="/testimonials/002-corona-analyst/" aria-label="Read Case File 002: Corona financial analyst, strategic purchase"
         class="ca-proof-card bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_12px c_#1a1816" style="text-decoration:none;">
        <span class="as_flex-start fs_11px fw_700 ls_2px c_#d92228 bg-c_#fdecec bd_1px_solid_#d92228 bdr_4px p_6px_12px" style="text-transform:uppercase">Case File 002</span>
        <p class="fs_11px fw_700 ls_1.5px c_#3f4650 m_0" style="text-transform:uppercase">Corona &middot; Strategic Purchase</p>
        <h3 class="fs_18px md:fs_20px fw_700 c_#1a1816 lh_1.3 m_0">He analyzes numbers for the State of California. Then he ran the numbers on us.</h3>
        <div class="mt_auto pt_16px bd-t_1px_solid_#e5e5e5">
          <span class="d_block fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_4px" style="font-variant-numeric: tabular-nums;">$20,000</span>
          <span class="fs_13px c_#3f4650 fw_500">Saved off asking price</span>
        </div>
      </a>

    </div>

    <div class="ta_center">
      <a href="/testimonials/" class="btn-secondary-outline">Read more case files &rarr;</a>
    </div>

  </div>
</section>
"""


def faq_item(idx: int, q: str, a: str) -> str:
    return f"""
    <section data-expanded="false" class="m_0">
      <button type="button" data-expanded="false" aria-expanded="false" aria-controls="ca-faq-{idx}-content" id="ca-faq-{idx}-header" data-has-custom-icon="true"
              class="d_flex ai_center jc_space-between w_100% p_10px_40px_16px_0 bg-c_transparent bd_none cursor_pointer fs_14px md:fs_16px lh_24px md:lh_32px ta_left pos_relative bd-b_1px_solid_rgba(75,_92,_117,_0.1019607843) focus:ring_none">
        <h3 class="flex_1 fw_400 fs_16px">{q}</h3>
        <div class="pos_absolute right_0 d_flex ai_center jc_center w_20px h_20px">
          <svg width="14" height="14" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 6L10 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
            <path class="faq-icon-vertical" d="M6 2L6 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
          </svg>
        </div>
      </button>
      <div class="ov_hidden max-h_0 trs_max-height_0.2s_ease-out" id="ca-faq-{idx}-content" role="region" aria-labelledby="ca-faq-{idx}-header" style="max-height: 0px;">
        <div class="accordion-inner-content ov_hidden fs_16px fw_400 lh_24px bdr_16px mt_16px p_16px bg-c_#f7f7f7">{a}</div>
      </div>
    </section>"""


FAQ_ITEMS = [
    ("Do I need to be physically present in California to sell my home?",
     "No. I work with sellers who live out of state, out of the country, or who simply travel often. With electronic signing, virtual walkthroughs, and a strong communication system, the entire process can happen without you being on-site. I handle every in-person element on your behalf."),
    ("What are California-specific seller disclosures I need to know about?",
     "California requires sellers to disclose a long list of items: known defects, environmental hazards, neighborhood nuisances, prior repairs, natural hazard zones, and more. The Transfer Disclosure Statement (TDS) and Natural Hazard Disclosure (NHD) are the two big ones. I walk every seller through these line by line so nothing gets missed and nothing becomes a liability after closing."),
    ("How long does it actually take to sell a home in California?",
     "In Orange County, a well-priced home typically goes under contract within 2 to 4 weeks, with another 30 to 45 days of escrow. That's a 6 to 10 week timeline from listing to keys exchanged. Other California markets vary. I'll give you a specific timeline for your home and your area on our first call."),
    ("What about California capital gains tax when I sell?",
     "California taxes capital gains on home sales as ordinary income (no special long-term capital gains rate at the state level). Federally, you may qualify for the $250,000 single or $500,000 married primary residence exclusion. I'm not a tax professional, but I'll connect you with CPAs I trust who specialize in California real estate transactions."),
    ("Can you help me sell a home in a part of California where you don't work directly?",
     "Yes, through my referral network. I personally vet every agent I refer to. You'll get my involvement on strategy, pricing, and structure, while a local expert handles the day-to-day. The referral process is transparent and I stay in the loop until your home closes."),
    ("How does your commission work?",
     "I'll always be transparent about what I charge and what you're getting for it. My commission reflects the marketing, negotiation, and personal service I deliver. We discuss specifics on our first call, with full transparency about every line item. If another agent is quoting you a lower rate, ask them what they're cutting. It's usually the marketing budget, the photography, or the hours actually spent on your listing."),
]


FAQ = """
<section class="max-w_1035px mt_48px md:mt_64px mb_64px mx_auto pl_32px md:pl_16px pr_32px md:pr_16px">
  <div class="ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">FAQ</p>
    <h2 class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_45px fs_24px md:fs_30px mb_32px md:mb_48px ta_center">What California sellers actually ask.</h2>
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
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Start your California home value report</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Free CMA. Sharp pricing. Real California expertise.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Enter your address. I will follow up within the hour with a real number, a written marketing plan, and a proposed timeline. If you are outside my direct markets, I will route you to the right agent in my network and stay involved.</p>

      <div id="ca-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your California address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


JSON_LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "RealEstateAgent",
  "name": "Joshua Guerrero",
  "url": "https://drozq.com/california/",
  "image": "https://drozq.com/media/images/Waist.png",
  "telephone": "+19494385948",
  "email": "Josh@Drozq.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "17875 Von Karman Ave, Suite 150",
    "addressLocality": "Irvine",
    "addressRegion": "CA",
    "postalCode": "92614",
    "addressCountry": "US"
  },
  "areaServed": [
    {"@type": "State", "name": "California"},
    {"@type": "City", "name": "Irvine"},
    {"@type": "City", "name": "Newport Beach"},
    {"@type": "City", "name": "Costa Mesa"},
    {"@type": "City", "name": "Long Beach"},
    {"@type": "City", "name": "Manhattan Beach"},
    {"@type": "AdministrativeArea", "name": "Orange County"},
    {"@type": "AdministrativeArea", "name": "Los Angeles County"}
  ],
  "priceRange": "$$$",
  "hasCredential": {
    "@type": "EducationalOccupationalCredential",
    "credentialCategory": "California Real Estate License",
    "identifier": "DRE# 02267255"
  }
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/" },
    { "@type": "ListItem", "position": 2, "name": "California", "item": "https://drozq.com/california/" }
  ]
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
""" + ",\n".join(
    '    {{"@type":"Question","name":"{q}","acceptedAnswer":{{"@type":"Answer","text":"{a}"}}}}'.format(
        q=q.replace('"', '\\"'),
        a=a.replace('"', '\\"'),
    ) for q, a in FAQ_ITEMS
) + """
  ]
}
</script>
"""


MAIN_BODY = HERO + HONEST + GEOGRAPHY + WHY + MID_TABS + MARKET + PROOF + FAQ + CLOSING_CTA + JSON_LD


if __name__ == "__main__":
    scaffold_page(
        target="california/index.html",
        title="California Listing Agent | Joshua Guerrero, Real Brokerage",
        description="Selling a home in California? Joshua Guerrero, licensed CA REALTOR(R) based in Irvine. Direct service across Orange County and the South Bay. Vetted statewide referral network. Free CMA.",
        canonical="/california/",
        main_body_html=MAIN_BODY,
        og_title="California Listing Agent | Joshua Guerrero",
        og_description="Licensed CA REALTOR(R) based in Irvine. Direct service in OC and South Bay. Vetted referral network statewide. Free CMA. DRE #02267255.",
    )
