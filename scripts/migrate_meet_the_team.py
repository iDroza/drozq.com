"""Migrate /meet-the-team/ to the homepage template scaffold.

The page concept is "you hire one agent, you get an entire operation."
Three layers: Joshua at the center, six trusted partners in the middle,
three operating systems on the outside. The angle is anti-bait-and-switch:
most agent sites oversell a "team" that doesn't exist or hand you off to
juniors. This page is the inverse pitch.

KILLED from the legacy page:
- Brand-mode (mint/navy/green/red) palette + custom CSS reset.
- Concentric SVG-positioned diagram (six partner nodes + three system
  nodes orbiting a Joshua center). Decorative; not recreatable in Panda
  utilities without a special-purpose style block. Replaced with a
  three-column "layers" overview band that delivers the same hierarchy
  in a much simpler layout.
- 510-935-5701 phone (replaced with 949-438-5948 site-wide).
- Brand-mode header with dropdown nav grid + lead-modal popover form.
- Brand-mode navy footer.
- Final CTA pointing at /contact/ (replaced with the inline address-form
  pill so the page captures leads directly, matching every other migrated
  page).

PRESERVED + reframed:
- Hero copy: "You hire one agent. You get an entire operation." + sub.
- All three layer concepts: Joshua (Layer 01), the six partners (Layer
  02), the three systems (Layer 03).
- All six partner cards verbatim (Active Realty, Transaction
  Coordinator, Listing Photographer, Lending Network, Inspectors and
  Specialists, Title and Escrow).
- All three system cards verbatim (Communication Cadence, 48-Hour
  Launch Playbook, Deal Management Protocol).
- Joshua's portrait, moved from the legacy hero into Layer 01 so the
  face stays in front of the copy that introduces him.
- Outcome paragraph + cross-link to case files.
- Person + BreadcrumbList JSON-LD.
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
    <img src="/media/images/coastal-modern-home.webp" alt="Modern hillside home overlooking the Southern California coast at sunset" width="1672" height="941" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.4)"></div>
  </div>

  <section aria-labelledby="mtt-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="mtt-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">You hire one agent. You get an entire operation.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">One point of contact, a network of trusted partners, a system built so nothing slips.</p>
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


THREE_LAYERS = """
<section aria-labelledby="mtt-layers-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Structure</p>
      <h2 id="mtt-layers-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Three layers. One operation.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Every layer is real. Every partner is someone I work with on every transaction. Every system runs whether you're watching or not.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <p class="c_#d92228 fs_11px fw_700 ls_2px m_0" style="text-transform:uppercase">Layer 01</p>
        <h3 class="fs_22px md:fs_24px fw_700 c_#1a1816 lh_1.25 m_0">Joshua Guerrero</h3>
        <p class="c_#757575 fs_13px md:fs_14px fw_700 m_0">Point of contact</p>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Every text, call, negotiation, and decision routes through me. No assistants, no handoffs.</p>
      </article>

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <p class="c_#d92228 fs_11px fw_700 ls_2px m_0" style="text-transform:uppercase">Layer 02</p>
        <h3 class="fs_22px md:fs_24px fw_700 c_#1a1816 lh_1.25 m_0">Six trusted partners</h3>
        <p class="c_#757575 fs_13px md:fs_14px fw_700 m_0">Brokerage &middot; Coordinator &middot; Photographer &middot; Lending &middot; Inspectors &middot; Title</p>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Specialists I've worked with on real deals, handling the work that requires their expertise so I can stay focused on yours.</p>
      </article>

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <p class="c_#d92228 fs_11px fw_700 ls_2px m_0" style="text-transform:uppercase">Layer 03</p>
        <h3 class="fs_22px md:fs_24px fw_700 c_#1a1816 lh_1.25 m_0">Three operating systems</h3>
        <p class="c_#757575 fs_13px md:fs_14px fw_700 m_0">Communication cadence &middot; 48-hour launch &middot; Deal management protocol</p>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Nothing about how I work is improvised. Each system runs on every client so nothing slips.</p>
      </article>

    </div>
  </div>
</section>
"""


LAYER_01 = """
<style>
.drozq-portrait-split {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  align-items: center;
}
@media (min-width: 768px) {
  .drozq-portrait-split {
    grid-template-columns: 280px 1fr;
    gap: 48px;
  }
}
</style>
<section aria-labelledby="mtt-layer-01-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="drozq-portrait-split">

      <div class="ta_center md:ta_left">
        <img src="/media/images/Waist.png" alt="Joshua Guerrero, Real Estate Agent" width="280" height="380" loading="lazy"
             class="d_inline-block w_220px md:w_280px h_auto bdr_16px ov_hidden bx-sh_0_16px_40px_rgba(30,_47,_73,_0.12)">
      </div>

      <div>
        <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Layer 01</p>
        <h2 id="mtt-layer-01-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px mb_16px">Joshua Guerrero. The one you call.</h2>
        <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Every text, every call, every negotiation, every difficult decision: that's me. You'll never get passed off to an assistant for the moments that matter. You'll never wonder which person on a "team" is actually responsible for your listing. The buck stops with one person, and that person is the one you hired.</p>
        <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">What that means practically: I'm the one who walks your home, builds your pricing strategy, presents your listing to buyers' agents, negotiates every offer, manages every contingency, and coordinates every milestone through close. The execution is leveraged. The accountability is not.</p>
      </div>

    </div>
  </div>
</section>
"""


# Each partner: (subtitle, title, body, inline_svg)
PARTNERS = [
    (
        "The Brokerage", "Active Realty, Inc.",
        "The licensed brokerage backing every transaction. Decades of collective experience, a deep network of California agents, and the institutional infrastructure that makes large transactions move smoothly. I'm an agent. They're the platform.",
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><path d="M8 42V20l16-12 16 12v22" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/><path d="M18 42V28h12v14" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/></svg>',
    ),
    (
        "Behind-the-Scenes Operations", "Transaction Coordinator",
        "A dedicated coordinator manages the paperwork, the deadlines, the disclosures, and the document trail of every escrow. While I'm negotiating your deal, she's making sure every form is signed, filed, and on time. You'd never know she existed unless something went wrong, which is exactly the point.",
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><rect x="11" y="6" width="26" height="36" rx="3" stroke="currentColor" stroke-width="2.4"/><path d="M17 17h14M17 24h14M17 31h10" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    ),
    (
        "First Impressions", "Listing Photographer",
        "A professional real estate photographer shoots every listing I take. Twilight shots, drone aerials, interior coverage that actually shows the space the way a buyer will experience it. The first 48 hours of a listing are decided by the photos. I don't take chances with that.",
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><rect x="6" y="13" width="36" height="26" rx="3" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="26" r="7" stroke="currentColor" stroke-width="2.4"/><path d="M16 13l3-5h10l3 5" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/></svg>',
    ),
    (
        "Buyer Financing", "Lending Network",
        "A trusted network of lenders I've worked with on real deals. When buyer financing is shaky, I know which lender to call. When a buyer needs a creative solution (rate buy-down, second-loan structure, bridge financing), I have a direct line to someone who can actually execute, not just promise.",
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="2.4"/><path d="M24 13v22M30 18c-1-2.5-3.5-3-6-3s-5 1.2-5 4 3 3.5 6 4.2 6 1.5 6 4.3-2 4.5-5 4.5-5.5-1-6-3.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    ),
    (
        "Due Diligence", "Inspectors and Specialists",
        "Home inspectors, sewer line specialists, termite inspectors, structural engineers when needed. I've worked with all of them on real transactions. When an inspection finding is ambiguous, I know exactly who to call to get a clean second opinion fast.",
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="20" cy="20" r="11" stroke="currentColor" stroke-width="2.4"/><path d="M28 28l12 12" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M16 20h8M20 16v8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
    ),
    (
        "The Close", "Title and Escrow",
        "Trusted title and escrow partners who close transactions cleanly and on time. The last 30 days of any deal is a coordination problem. The right title and escrow team makes that problem invisible to you.",
        '<svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><path d="M6 28l8-8 6 6 8-8 6 6 8-8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 36l4 4 6-6 6 6 4-4" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    ),
]


def partner_card(sub: str, title: str, body: str, svg: str) -> str:
    return f"""
      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">{svg}</div>
        <p class="c_#757575 fs_11px md:fs_12px fw_700 ls_1.5px m_0" style="text-transform:uppercase">{sub}</p>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">{title}</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">{body}</p>
      </article>"""


LAYER_02 = """
<section aria-labelledby="mtt-layer-02-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Layer 02</p>
      <h2 id="mtt-layer-02-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The partners working behind every listing.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">One agent can't do everything alone. Anyone who tells you they can is either lying or doing it badly. What I've built instead is a network of specialists who handle the work that requires their expertise, while I stay focused on the work that requires mine.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(2,_1fr) lg:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">
""" + "\n".join(partner_card(s, t, b, svg) for (s, t, b, svg) in PARTNERS) + """
    </div>
  </div>
</section>
"""


# Each system: (number, title, body)
SYSTEMS = [
    (
        "System 01", "The communication cadence.",
        "You will never wonder what's happening with your listing. From day one, you receive scheduled updates: weekly during the listing period, every 48 hours during escrow, and immediately when anything changes. No \"I'll get back to you tomorrow\" voicemails. No silence between milestones.",
    ),
    (
        "System 02", "The 48-hour launch playbook.",
        "When you sign with me, your home is on the market within 48 to 72 hours. Photos, copy, syndication across the major platforms, social media campaigns, and a dedicated property landing page all launch on a fixed timeline. Every listing follows the same playbook so nothing gets missed and nothing happens late.",
    ),
    (
        "System 03", "The deal management protocol.",
        "Every active transaction is tracked through a clear set of milestones with assigned deadlines: contingency removals, inspection responses, appraisal coordination, document signing, and closing logistics. Nothing happens last-minute. Nothing falls through the cracks. The protocol is the reason.",
    ),
]


def system_card(num: str, title: str, body: str) -> str:
    return f"""
      <article class="bg_#fff bdr_16px p_28px md:p_32px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_12px">
        <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_2px m_0" style="text-transform:uppercase">{num}</p>
        <h3 class="fs_22px md:fs_24px fw_700 c_#1a1816 lh_1.25 m_0">{title}</h3>
        <p class="fs_15px md:fs_16px lh_1.65 c_#3f4650 m_0">{body}</p>
      </article>"""


LAYER_03 = """
<section aria-labelledby="mtt-layer-03-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Layer 03</p>
      <h2 id="mtt-layer-03-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The systems that make sure nothing slips.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">The reason I can deliver responsiveness most agents can't is that nothing about how I work is improvised. Every step of every transaction follows a system I've built, refined, and use on every client. The systems aren't visible to you. The results are.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">
""" + "\n".join(system_card(n, t, b) for (n, t, b) in SYSTEMS) + """
    </div>
  </div>
</section>
"""


OUTCOME = """
<section aria-labelledby="mtt-outcome-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_780px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Result</p>
    <h2 id="mtt-outcome-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">One agent, working with a real network, running a real system.</h2>
    <div style="max-width: 560px; margin: 0 auto;">
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">When you list your home with me, you get the personal accountability of working directly with one agent, plus the operational depth of a brand that's been built deliberately. That combination is rare in real estate. Most agents are either solo and overwhelmed, or large teams where you get passed around. What I've built is the third option.</p>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">If that's the kind of operation you want behind your home sale, let's talk.</p>
    </div>
  </div>
</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Put the operation to work.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">Pick the side that matches your move. Same operation, mode-aware. I see every submission in real time.</p>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">One agent on every call.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Every text, negotiation, and milestone routes through me directly.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Six partners doing the work behind it.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Brokerage, coordinator, photographer, lending, inspectors, title and escrow. All vetted, all on every listing.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Three systems so nothing slips.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Communication cadence, 48-hour launch, deal management protocol. Same playbook on every transaction.</p>
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
<section aria-labelledby="mtt-crosslink-title" class="bg_#fff py_48px md:py_64px">
  <div class="max-w_780px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Want to see it in action?</p>
    <h2 id="mtt-crosslink-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_24px md:fs_30px ls_0.3px mb_16px">Read the case files.</h2>
    <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px mb_24px m_0_auto" style="max-width:560px;">Every transaction I close becomes a documented case file with the real numbers, the real negotiation, and the real outcome. The operation in action.</p>
    <a href="/testimonials/" class="btn-secondary-outline">See the case files &rarr;</a>
  </div>
</section>
"""


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Ready to See It First-Hand?</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Drop your address. Start the conversation.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">The fastest way to understand how I work is to start the qualifier. A few quick questions, then I follow up directly within the hour.</p>

      <div id="mtt-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
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
  "@type": "Person",
  "name": "Joshua Guerrero",
  "jobTitle": "Real Estate Agent",
  "description": "Solo real estate agent operating with a deliberate network of partners and a structured set of operating systems.",
  "url": "https://drozq.com/meet-the-team/",
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
  "worksFor": {
    "@type": "Organization",
    "name": "Real Brokerage"
  },
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
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
    {"@type": "ListItem", "position": 2, "name": "Meet the Team", "item": "https://drozq.com/meet-the-team/"}
  ]
}
</script>
"""


MAIN_BODY = (
    HERO
    + THREE_LAYERS
    + LAYER_01
    + LAYER_02
    + LAYER_03
    + OUTCOME
    + MID_TABS
    + CROSSLINK
    + CLOSING_CTA
    + JSON_LD
)


if __name__ == "__main__":
    scaffold_page(
        target="meet-the-team/index.html",
        title="Meet the Operation | Joshua Guerrero, Real Brokerage",
        description="One agent, one phone, one network of trusted partners, and three operating systems. See the three-layer operation behind every Joshua Guerrero listing.",
        canonical="/meet-the-team/",
        main_body_html=MAIN_BODY,
        og_title="Meet the Operation | Joshua Guerrero",
        og_description="One agent, one phone, six trusted partners, three operating systems. The three-layer operation behind every listing in Irvine and Southern California.",
    )
