"""Migrate /contact/ to the homepage template scaffold.

The legacy /contact/ is a CMA-request conversion page disguised as a
contact page. The H1 is "What's your home actually worth?" and the
primary body element is a 7-field intake form (name / email / phone /
address / timeline / referral source / message) that posts to /api/lead
with intent=Home Valuation. That intent is now better served by the
inline 3-funnel system (Sell funnel exit = "Send My Home Value Report"),
so the dedicated intake form gets replaced with the 3-tab hero CTA + the
closing address-form pill.

What still belongs on a /contact/ page that doesn't belong elsewhere:
direct contact details (phone, email, address, business hours) and the
Google Maps embed showing the Irvine office. Those are trust signals
that make the difference for visitors who want to verify the agent is
real before submitting any form.

KILLED from the legacy page:
- Brand-mode (mint/navy/green/red) palette + custom CSS reset.
- 7-field contact-form (replaced by the inline funnel + closing pill).
- Brand-mode hero with side-by-side map + form.
- Brand-mode header (with the dropdown nav grid + 510-935-5701 phone)
  and brand-mode navy footer.
- "510-935-5701" phone everywhere (replaced with 949-438-5948 site-wide).

PRESERVED + reframed:
- Hero copy: "What's your home actually worth?" + sub.
- "Why this matters: pricing wrong costs more than you think." block.
- "After one 15-minute call." three-card grid (CMA / pricing strategy /
  no-pressure path forward).
- Direct contact section with phone, email, address, business hours.
- Google Maps embed of the Irvine office.
- Cross-link to /testimonials/ case files.
- BreadcrumbList JSON-LD + new ContactPage JSON-LD with current phone.
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
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_50%_55% [&_img]:[@media_(max-width:_480px)]:obj-p_center">
    <img src="/media/images/crystal-cove.webp" alt="Southern California coastline" width="1280" height="640" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.4)"></div>
  </div>

  <section aria-labelledby="contact-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="contact-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">What's your home actually worth?</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">A real CMA and a real pricing strategy, delivered in writing in fifteen minutes.</p>
    </div>
  </section>

  <section aria-label="Compare agents" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px">
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
  </section>
</div>
"""


# The map is the Irvine office; preserve verbatim including the
# original Google Maps embed URL with Joshua's verified place id.
MAP_IFRAME_SRC = (
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3000!2d-117.8473843!3d33.6860012"
    "!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x80dcdf8dbfbe3395%3A0xc09c886b39a043c2"
    "!2sJoshua%20Guerrero%20-%20Realtor!5e0!3m2!1sen!2sus!4v1"
)


DIRECT_CONTACT = f"""
<section aria-labelledby="contact-direct-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Prefer to talk?</p>
      <h2 id="contact-direct-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Reach me directly.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Some people want to fill out a form. Some people want to talk. Either works. Direct line, email, and office below.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px mb_32px md:mb_40px">

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

    <div class="w_100% bdr_16px ov_hidden bd_1px_solid_#e5e5e5 bx-sh_0_8px_24px_rgba(30,_47,_73,_0.08)" style="aspect-ratio: 16 / 9;">
      <iframe src="{MAP_IFRAME_SRC}"
              width="100%" height="100%" style="border:0;"
              allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
              title="Joshua Guerrero - Realtor on Google Maps"></iframe>
    </div>

  </div>
</section>
"""


WHY_PRICING = """
<section aria-labelledby="contact-why-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_560px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Why this matters</p>
    <h2 id="contact-why-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">Pricing wrong costs more than you think.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Most sellers overprice on day one because an agent told them what they wanted to hear. That home sits. After 30 days, the "what's wrong with it?" questions start. After 60 days, the price cuts start. After 90 days, the home sells for less than it would have if priced correctly from the beginning.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">The difference between a home priced right and a home priced wrong isn't a few thousand dollars. It's often tens of thousands. That's the conversation I want to have with you before you list, not after.</p>
  </div>
</section>
"""


# (icon_svg, title, body)
WHAT_YOU_GET = [
    (
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><rect x="9" y="6" width="30" height="36" rx="3" stroke="currentColor" stroke-width="2.4"/><path d="M15 16h18M15 23h18M15 30h12" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
        "A real CMA.",
        "A full comparative market analysis of your home, built from recent sales, active listings, and expired listings within your specific radius. Not a Zestimate.",
    ),
    (
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="10" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="3" fill="currentColor"/></svg>',
        "A pricing strategy.",
        "A clear recommendation on listing price, timing, and approach. Based on your home, your goals, and current market conditions.",
    ),
    (
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><path d="M10 12h28M10 24h28M10 36h18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="38" cy="36" r="4" stroke="currentColor" stroke-width="2.4"/></svg>',
        "A no-pressure path forward.",
        "If it makes sense to list, we list. If it doesn't, you walk away with better information than you came in with. That's it.",
    ),
]


def what_you_get_card(svg: str, title: str, body: str) -> str:
    return f"""
      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">{svg}</div>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">{title}</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">{body}</p>
      </article>"""


WHAT_YOU_GET_SECTION = """
<section aria-labelledby="contact-get-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">What You Get</p>
      <h2 id="contact-get-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">After one 15-minute call.</h2>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">
""" + "\n".join(what_you_get_card(s, t, b) for (s, t, b) in WHAT_YOU_GET) + """
    </div>
  </div>
</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Or start the qualifier instead.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">Pick the side that matches your move. Same form, mode-aware. I see every submission in real time.</p>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A real CMA, not a Zestimate.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Comparative market analysis pulled from active, pending, sold, and expired comps inside your specific submarket. Price range with a strategy, not a single number.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A clear recommendation, in writing.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">List price, timing, and prep plan. You leave the call with a document, not a vibe.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">An honest read on whether to list.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">If listing now doesn't make sense, I'll tell you. You walk away with better information about your home and the market than you came in with.</p>
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


CROSSLINK = """
<style>
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
<section aria-labelledby="contact-proof-title" class="bg_#fff py_48px md:py_64px">
  <div class="max-w_780px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Want proof first?</p>
    <h2 id="contact-proof-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_24px md:fs_30px ls_0.3px mb_16px">Read the case files.</h2>
    <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px mb_24px m_0_auto" style="max-width:560px;">Every transaction I close becomes a documented case file with the real numbers, the real negotiation, and the real outcome. If you want to know how I work before you reach out, start there.</p>
    <a href="/testimonials/" class="btn-secondary-outline">See the case files &rarr;</a>
  </div>
</section>
"""


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Ready to talk?</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Drop your address. I'll come back within the hour.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">A few quick questions, then I follow up directly. If you'd rather skip the form, my direct line is below.</p>

      <div id="contact-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
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
  "@type": "ContactPage",
  "name": "Contact Joshua Guerrero",
  "url": "https://drozq.com/contact/",
  "description": "Contact Joshua Guerrero, licensed California REALTOR. Direct line, email, and Irvine office address.",
  "mainEntity": {
    "@type": "RealEstateAgent",
    "name": "Joshua Guerrero",
    "url": "https://drozq.com/",
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
    "geo": {
      "@type": "GeoCoordinates",
      "latitude": "33.6860012",
      "longitude": "-117.8473843"
    },
    "hasCredential": {
      "@type": "EducationalOccupationalCredential",
      "credentialCategory": "California Real Estate License",
      "identifier": "DRE# 02267255"
    }
  }
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
    {"@type": "ListItem", "position": 2, "name": "Contact", "item": "https://drozq.com/contact/"}
  ]
}
</script>
"""


MAIN_BODY = (
    HERO
    + DIRECT_CONTACT
    + WHY_PRICING
    + WHAT_YOU_GET_SECTION
    + MID_TABS
    + CROSSLINK
    + CLOSING_CTA
    + JSON_LD
)


if __name__ == "__main__":
    scaffold_page(
        target="contact/index.html",
        title="Contact Joshua Guerrero | Irvine Listing Agent",
        description="Direct line, email, and Irvine office for Joshua Guerrero, licensed California REALTOR. Free CMA in 15 minutes. Real numbers, real strategy.",
        canonical="/contact/",
        main_body_html=MAIN_BODY,
        og_title="Contact Joshua Guerrero | Irvine Listing Agent",
        og_description="Direct line, email, and Irvine office. Free CMA in 15 minutes. Real numbers, real strategy, walk-ins welcome.",
    )
