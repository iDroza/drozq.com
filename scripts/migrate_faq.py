"""Migrate /faq/ to the homepage template scaffold.

This is the seller FAQ hub. Its unique value is the 29 question-and-answer
pairs organized across 5 categories, plus the FAQPage + BreadcrumbList
JSON-LD that drives both classic search and AI search visibility.

KILLED from the legacy page:
- Brand-mode (mint/navy/green/red) palette + custom CSS reset.
- "Top-Rated Listing Agent" topbar + brand-mode sticky header with the
  510-935-5701 phone + dropdown nav grid.
- Brand-mode hero (faq-hero with gradient overlay + jump-nav pills
  styled on the brand-mode tokens).
- Lead-modal popover form (replaced by the inline 3-funnel system).
- Brand-mode navy footer with 4-column grid + brokerage badge.

PRESERVED + reframed:
- All 29 FAQ Q&As, verbatim, grouped into the same 5 categories.
- Internal links in the answers (Testimonials index, Long Beach
  firefighter case file).
- Jump-nav pills at the top of the FAQ stack, re-styled to homepage
  tokens.
- FAQPage JSON-LD covering every visible question, regenerated from the
  same source list so JSON-LD and HTML never drift.
- BreadcrumbList JSON-LD.
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
            Compare Agents
          </button>
        </div>
      </div>
      <input type="hidden" name="gclid" value="">
    </form>"""


HERO = f"""
<div class="pos_relative ov_hidden">
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_50%_55% [&_img]:[@media_(max-width:_480px)]:obj-p_center">
    <img src="/media/images/outside-home-pic1.webp" alt="Southern California home exterior at golden hour" width="1280" height="640" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.62)"></div>
  </div>

  <section aria-labelledby="faq-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <p class="op_0.9 c_#fff ls_2px fs_11px md:fs_12px fw_700 mb_8px" style="text-transform:uppercase">Frequently Asked Questions</p>
      <h1 id="faq-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">The questions sellers actually ask. Answered honestly.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">No canned answers. No dodging the uncomfortable questions. If you have been thinking it, it is probably on this page. If it is not, drop your address below and ask it directly.</p>
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


JUMP_NAV_STYLE = """
<style>
.faq-jump-pills {
  display: flex; flex-wrap: wrap; justify-content: center;
  gap: 8px; max-width: 1100px; margin: 0 auto;
  padding: 0 24px;
}
.faq-jump-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 9999px;
  border: 1px solid #e5e5e5; background: #fff;
  font-size: 13px; font-weight: 700; color: #2b2b2b;
  letter-spacing: 0.01em; text-decoration: none;
  transition: border-color .2s ease, color .2s ease, transform .2s ease;
}
.faq-jump-pill:hover {
  border-color: #d92228; color: #d92228;
  transform: translateY(-1px);
}
.faq-jump-pill__num {
  font-size: 11px; font-weight: 700; letter-spacing: 0.2em;
  color: #d92228; opacity: 0.85;
}
@media (min-width: 768px) {
  .faq-jump-pill { font-size: 14px; padding: 11px 20px; }
}
</style>
"""


JUMP_NAV = """
<section aria-label="FAQ categories" class="bg-c_#f2f0ef py_24px md:py_32px bd-b_1px_solid_#e5e5e5">
  <nav class="faq-jump-pills">
    <a class="faq-jump-pill" href="#getting-started"><span class="faq-jump-pill__num">01</span>Getting Started</a>
    <a class="faq-jump-pill" href="#working-with-joshua"><span class="faq-jump-pill__num">02</span>Working With Joshua</a>
    <a class="faq-jump-pill" href="#pricing-offers"><span class="faq-jump-pill__num">03</span>Pricing &amp; Offers</a>
    <a class="faq-jump-pill" href="#the-process"><span class="faq-jump-pill__num">04</span>The Process</a>
    <a class="faq-jump-pill" href="#after-the-sale"><span class="faq-jump-pill__num">05</span>After the Sale</a>
  </nav>
</section>
"""


# Each item: (question, html_answer_for_visible_body, plain_text_for_jsonld)
# plain_text is what FAQPage schema actually sees. The visible body may
# carry inline <a> links; JSON-LD stays text-only to keep the schema clean
# and match Google's expectations for FAQPage answer text.
CATEGORIES = [
    (
        "getting-started", "01", "Getting Started",
        "The questions that come up before you have even decided to list.",
        [
            (
                "How do I know if it's the right time to sell?",
                """The honest answer: nobody can time the market perfectly, and most people who try end up waiting too long. The better question is whether selling now lines up with your personal situation. Are you trying to move up, move out of state, cash in on equity, or simplify? Each of those has different timing dynamics. On our first call, I'll walk you through where the Irvine market is, what comparable homes are doing right now, and what selling in the next 30 to 90 days would realistically look like for your home specifically. You leave the call with clear numbers and an honest read on whether to list.""",
                """The honest answer: nobody can time the market perfectly, and most people who try end up waiting too long. The better question is whether selling now lines up with your personal situation. Are you trying to move up, move out of state, cash in on equity, or simplify? Each of those has different timing dynamics. On our first call, I'll walk you through where the Irvine market is, what comparable homes are doing right now, and what selling in the next 30 to 90 days would realistically look like for your home specifically. You leave the call with clear numbers and an honest read on whether to list.""",
            ),
            (
                "What is my home actually worth?",
                """The Zillow Zestimate is a starting point, not an answer. Real home valuation comes from analyzing three things: recently sold comparable homes, currently active listings, and your home's specific condition and features. I'll run a full comparative market analysis (CMA) for you before we even meet in person. That report will give you a realistic price range, not the inflated number some agents throw out to win your listing.""",
                """The Zillow Zestimate is a starting point, not an answer. Real home valuation comes from analyzing three things: recently sold comparable homes, currently active listings, and your home's specific condition and features. I'll run a full comparative market analysis (CMA) for you before we even meet in person. That report will give you a realistic price range, not the inflated number some agents throw out to win your listing.""",
            ),
            (
                "Should I make repairs or improvements before listing?",
                """Sometimes yes, often no. Over-improving before a sale is one of the most common ways sellers burn money. A fresh coat of paint, minor landscaping, and a deep clean almost always return more than they cost. A full kitchen remodel almost never does. When I walk your home, I'll tell you the three highest-leverage improvements and the three things not to bother touching. Being honest about what not to do is part of the service.""",
                """Sometimes yes, often no. Over-improving before a sale is one of the most common ways sellers burn money. A fresh coat of paint, minor landscaping, and a deep clean almost always return more than they cost. A full kitchen remodel almost never does. When I walk your home, I'll tell you the three highest-leverage improvements and the three things not to bother touching. Being honest about what not to do is part of the service.""",
            ),
            (
                "How long will it take to sell?",
                """In a balanced Irvine market, a well-priced home typically sells within 14 to 30 days. Overpriced homes sit for 60+ days and then sell for less than they would have if priced correctly on day one. Speed is a function of pricing strategy, preparation, and marketing. I build a timeline with you upfront so you know exactly what to expect at every stage.""",
                """In a balanced Irvine market, a well-priced home typically sells within 14 to 30 days. Overpriced homes sit for 60+ days and then sell for less than they would have if priced correctly on day one. Speed is a function of pricing strategy, preparation, and marketing. I build a timeline with you upfront so you know exactly what to expect at every stage.""",
            ),
            (
                """What does "off-market" mean and should I consider it?""",
                """An off-market sale means your home is sold without being listed publicly on the MLS. It can be faster and more private, but it almost always costs you money because you lose competitive tension between buyers. I'll explore off-market options for clients who genuinely need privacy or speed over price, but I'll be upfront that for most sellers, going to market publicly nets more.""",
                """An off-market sale means your home is sold without being listed publicly on the MLS. It can be faster and more private, but it almost always costs you money because you lose competitive tension between buyers. I'll explore off-market options for clients who genuinely need privacy or speed over price, but I'll be upfront that for most sellers, going to market publicly nets more.""",
            ),
        ],
    ),
    (
        "working-with-joshua", "02", "Working With Joshua",
        "What to expect when you hire me and how we will work together.",
        [
            (
                "Why should I hire you specifically?",
                """I give you three things most agents don't. First, negotiation skill trained in the most adversarial sales environment in the country (I averaged 20 units a month selling cars before I moved into real estate, which means I learned to close hard deals with hostile buyers). Second, responsiveness. I answer texts and calls fast, because deals die in silence. Third, documentation. Every deal I close becomes a case file with real numbers and real outcomes. You can read them at <a href="/testimonials/" class="c_#d92228 fw_700">Testimonials</a> before we even talk. Most agents ask you to trust them. I show you the receipts first.""",
                """I give you three things most agents don't. First, negotiation skill trained in the most adversarial sales environment in the country (I averaged 20 units a month selling cars before I moved into real estate, which means I learned to close hard deals with hostile buyers). Second, responsiveness. I answer texts and calls fast, because deals die in silence. Third, documentation. Every deal I close becomes a case file with real numbers and real outcomes. You can read them at /testimonials before we even talk. Most agents ask you to trust them. I show you the receipts first.""",
            ),
            (
                "You're relatively new to real estate. Is that a problem?",
                """Fair question, and I'd rather you ask it than wonder. I'm licensed, I'm closing deals, and I'm backed by a full brokerage with decades of collective experience behind me. What I lack in years I more than make up for in responsiveness, work ethic, and negotiation track record. Newer agents often outperform veterans on communication and hustle because we have to. Read the case files. The work speaks for itself.""",
                """Fair question, and I'd rather you ask it than wonder. I'm licensed, I'm closing deals, and I'm backed by a full brokerage with decades of collective experience behind me. What I lack in years I more than make up for in responsiveness, work ethic, and negotiation track record. Newer agents often outperform veterans on communication and hustle because we have to. Read the case files. The work speaks for itself.""",
            ),
            (
                "Is your commission negotiable?",
                """I'll always be transparent about what I charge and what you're getting for it. My commission reflects the quality of the marketing, negotiation, and service I deliver, and I'll walk you through exactly what that includes on our first call. If another agent is quoting you a lower rate, ask them what they're cutting to get there. It's usually the marketing budget, the photography, or the hours they'll actually spend on your listing. You get what you pay for in this business.""",
                """I'll always be transparent about what I charge and what you're getting for it. My commission reflects the quality of the marketing, negotiation, and service I deliver, and I'll walk you through exactly what that includes on our first call. If another agent is quoting you a lower rate, ask them what they're cutting to get there. It's usually the marketing budget, the photography, or the hours they'll actually spend on your listing. You get what you pay for in this business.""",
            ),
            (
                "How often will I hear from you?",
                """More than you expect. My rule is simple: no client of mine ever waits more than a few hours for a response during normal hours. During active listing periods, expect regular updates even if there's nothing dramatic to report. I'd rather over-communicate than leave you wondering. Silence is where trust dies.""",
                """More than you expect. My rule is simple: no client of mine ever waits more than a few hours for a response during normal hours. During active listing periods, expect regular updates even if there's nothing dramatic to report. I'd rather over-communicate than leave you wondering. Silence is where trust dies.""",
            ),
            (
                "What if I'm not happy with how the listing is going?",
                """We talk about it immediately. I'd rather have an uncomfortable conversation in week two than discover in week six that you've been unhappy the whole time. Every listing agreement I do includes a clear structure for how we course-correct if things aren't working, whether that means adjusting price, adjusting strategy, or (rarely) parting ways. I don't hold clients hostage to contracts.""",
                """We talk about it immediately. I'd rather have an uncomfortable conversation in week two than discover in week six that you've been unhappy the whole time. Every listing agreement I do includes a clear structure for how we course-correct if things aren't working, whether that means adjusting price, adjusting strategy, or (rarely) parting ways. I don't hold clients hostage to contracts.""",
            ),
            (
                "Do you work alone or with a team?",
                """I work directly with you. You'll never get passed off to an assistant or a junior agent for the important moments. Behind the scenes, I have a brokerage, lending partners, inspectors, photographers, and a transaction coordinator I work with, but you deal with me for everything that matters.""",
                """I work directly with you. You'll never get passed off to an assistant or a junior agent for the important moments. Behind the scenes, I have a brokerage, lending partners, inspectors, photographers, and a transaction coordinator I work with, but you deal with me for everything that matters.""",
            ),
        ],
    ),
    (
        "pricing-offers", "03", "Pricing & Offers",
        "How pricing actually works and what to do when offers come in.",
        [
            (
                "How do you determine the listing price?",
                """I build a comparative market analysis using three inputs: recently sold homes similar to yours (within 90 days, within a tight geographic radius), currently active listings you'd be competing against, and expired listings that failed to sell. Then I factor in your home's specific condition, features, and any unique value drivers. The result is a price range, not a single number, with a recommended strategy for where in that range to list.""",
                """I build a comparative market analysis using three inputs: recently sold homes similar to yours (within 90 days, within a tight geographic radius), currently active listings you'd be competing against, and expired listings that failed to sell. Then I factor in your home's specific condition, features, and any unique value drivers. The result is a price range, not a single number, with a recommended strategy for where in that range to list.""",
            ),
            (
                "Should I price high and negotiate down, or price right and attract offers?",
                """Pricing high almost always hurts you. Homes that sit on the market get stale, and buyers start asking "what's wrong with it." The data is clear: homes priced right on day one sell faster and often for more money than homes that are initially overpriced and then reduced. I'll never recommend a listing price designed to make you feel good on day one if it'll cost you on day thirty.""",
                """Pricing high almost always hurts you. Homes that sit on the market get stale, and buyers start asking "what's wrong with it." The data is clear: homes priced right on day one sell faster and often for more money than homes that are initially overpriced and then reduced. I'll never recommend a listing price designed to make you feel good on day one if it'll cost you on day thirty.""",
            ),
            (
                "What happens if I get multiple offers?",
                """We structure a clear process to evaluate them. Price matters, but so do contingencies, financing type, down payment size, closing timeline, and buyer seriousness. A $5,000 higher offer from a buyer with weak financing can easily be worse than a slightly lower cash offer that closes in two weeks. I walk you through each offer side by side so the decision is clear.""",
                """We structure a clear process to evaluate them. Price matters, but so do contingencies, financing type, down payment size, closing timeline, and buyer seriousness. A $5,000 higher offer from a buyer with weak financing can easily be worse than a slightly lower cash offer that closes in two weeks. I walk you through each offer side by side so the decision is clear.""",
            ),
            (
                "Can I reject an offer?",
                """Absolutely. You're in control of your listing at every stage. I'll give you my honest read on every offer (whether I think it's strong, weak, or negotiable), but the final decision is always yours.""",
                """Absolutely. You're in control of your listing at every stage. I'll give you my honest read on every offer (whether I think it's strong, weak, or negotiable), but the final decision is always yours.""",
            ),
            (
                "What's a seller credit and why does it matter?",
                """A seller credit is money the seller contributes toward the buyer's closing costs or rate buy-down at the close of the transaction. It doesn't reduce your proceeds in the same way a price reduction does because it's structured differently in the deal. Smart agents use seller credits as negotiation leverage to keep the headline sale price high while giving the buyer what they actually need. You can see an example of this at <a href="/testimonials/001-long-beach-firefighter/" class="c_#d92228 fw_700">this case file</a> where we structured a $23,250 seller credit that paid for closing costs and bought down the buyer's rate.""",
                """A seller credit is money the seller contributes toward the buyer's closing costs or rate buy-down at the close of the transaction. It doesn't reduce your proceeds in the same way a price reduction does because it's structured differently in the deal. Smart agents use seller credits as negotiation leverage to keep the headline sale price high while giving the buyer what they actually need. You can see an example of this at this case file where we structured a $23,250 seller credit that paid for closing costs and bought down the buyer's rate.""",
            ),
            (
                "What if my home doesn't sell?",
                """First, we don't let it get to that point without course-correcting. If a listing isn't getting showings or offers in the expected window, we adjust (price, photography, marketing strategy, or staging). If after all adjustments the home still doesn't sell, we have an honest conversation about whether the timing is wrong or whether your goals have changed. I don't leave clients stuck.""",
                """First, we don't let it get to that point without course-correcting. If a listing isn't getting showings or offers in the expected window, we adjust (price, photography, marketing strategy, or staging). If after all adjustments the home still doesn't sell, we have an honest conversation about whether the timing is wrong or whether your goals have changed. I don't leave clients stuck.""",
            ),
        ],
    ),
    (
        "the-process", "04", "The Process",
        "Timelines, inspections, escrow, and what actually happens between listing and closing.",
        [
            (
                "What does the timeline look like from listing to close?",
                """A typical Irvine home sale breaks down like this: 1 to 2 weeks of prep and staging, 2 to 4 weeks on market, 30 to 45 days of escrow after accepting an offer. Total: roughly 6 to 10 weeks from first conversation to keys exchanged. I'll build a specific timeline for your situation on our first call.""",
                """A typical Irvine home sale breaks down like this: 1 to 2 weeks of prep and staging, 2 to 4 weeks on market, 30 to 45 days of escrow after accepting an offer. Total: roughly 6 to 10 weeks from first conversation to keys exchanged. I'll build a specific timeline for your situation on our first call.""",
            ),
            (
                "What do I need to do before the first showing?",
                """Three things. Declutter aggressively (most sellers underestimate how much). Deep clean every surface. Handle obvious cosmetic issues like scuffed paint or burnt-out bulbs. I'll send you a detailed prep checklist after our first meeting, including which rooms to prioritize.""",
                """Three things. Declutter aggressively (most sellers underestimate how much). Deep clean every surface. Handle obvious cosmetic issues like scuffed paint or burnt-out bulbs. I'll send you a detailed prep checklist after our first meeting, including which rooms to prioritize.""",
            ),
            (
                "Do I need to leave during showings?",
                """Yes, every time. Buyers don't open closets or discuss their real reactions when the owner is home. A 30 to 60 minute window is all we usually need, and I coordinate scheduling so it's as painless as possible.""",
                """Yes, every time. Buyers don't open closets or discuss their real reactions when the owner is home. A 30 to 60 minute window is all we usually need, and I coordinate scheduling so it's as painless as possible.""",
            ),
            (
                "Will I need a home inspection?",
                """The buyer will typically order a home inspection as part of their due diligence. You don't pay for it, but you do respond to any issues it uncovers. Some sellers also choose to get a pre-listing inspection so we can address problems before they become negotiation points. I'll recommend whether that's worth it based on your home's age and condition.""",
                """The buyer will typically order a home inspection as part of their due diligence. You don't pay for it, but you do respond to any issues it uncovers. Some sellers also choose to get a pre-listing inspection so we can address problems before they become negotiation points. I'll recommend whether that's worth it based on your home's age and condition.""",
            ),
            (
                "What happens during escrow?",
                """Escrow is the 30 to 45 day period between the buyer's offer being accepted and the sale closing. During this window: the buyer does their inspections, the buyer's lender orders an appraisal, both parties handle contingency removals, the title is cleared, and the final paperwork is prepared for signing. I manage the day-to-day coordination and keep you informed of every milestone.""",
                """Escrow is the 30 to 45 day period between the buyer's offer being accepted and the sale closing. During this window: the buyer does their inspections, the buyer's lender orders an appraisal, both parties handle contingency removals, the title is cleared, and the final paperwork is prepared for signing. I manage the day-to-day coordination and keep you informed of every milestone.""",
            ),
            (
                "What if the appraisal comes in low?",
                """It happens, especially in a fast-moving market. If the appraisal comes in below the agreed sale price, there are three paths: the buyer makes up the difference in cash, we renegotiate the price to match the appraisal, or we cancel the deal and relist. Most appraisal issues can be resolved with good negotiation, which is where having an experienced advocate on your side matters.""",
                """It happens, especially in a fast-moving market. If the appraisal comes in below the agreed sale price, there are three paths: the buyer makes up the difference in cash, we renegotiate the price to match the appraisal, or we cancel the deal and relist. Most appraisal issues can be resolved with good negotiation, which is where having an experienced advocate on your side matters.""",
            ),
            (
                "What are closing costs for a seller?",
                """Sellers typically pay the agent commissions, title and escrow fees, any agreed-upon credits to the buyer, and prorated property taxes and HOA fees. On a typical Irvine home, seller closing costs run roughly 7 to 9 percent of the sale price when commissions are included. I'll give you a detailed net sheet showing exactly what you'll walk away with before you sign any listing agreement.""",
                """Sellers typically pay the agent commissions, title and escrow fees, any agreed-upon credits to the buyer, and prorated property taxes and HOA fees. On a typical Irvine home, seller closing costs run roughly 7 to 9 percent of the sale price when commissions are included. I'll give you a detailed net sheet showing exactly what you'll walk away with before you sign any listing agreement.""",
            ),
        ],
    ),
    (
        "after-the-sale", "05", "After the Sale",
        "What happens once the deal is done and how we stay connected.",
        [
            (
                "How long before I get my money?",
                """In California, sale proceeds are wired to you on the day escrow closes or the following business day, depending on the time of day the closing is recorded. I walk you through the wire process in advance so there are no surprises on closing day.""",
                """In California, sale proceeds are wired to you on the day escrow closes or the following business day, depending on the time of day the closing is recorded. I walk you through the wire process in advance so there are no surprises on closing day.""",
            ),
            (
                "Are there tax implications I should know about?",
                """There can be, especially if your home has appreciated significantly. The IRS allows a capital gains exclusion of up to $250,000 for single filers and $500,000 for married filers on the sale of a primary residence (with conditions). Investment properties and second homes are treated differently and may be eligible for a 1031 exchange. I am not a tax professional, but I'll point you to trusted CPAs I work with who specialize in real estate transactions.""",
                """There can be, especially if your home has appreciated significantly. The IRS allows a capital gains exclusion of up to $250,000 for single filers and $500,000 for married filers on the sale of a primary residence (with conditions). Investment properties and second homes are treated differently and may be eligible for a 1031 exchange. I am not a tax professional, but I'll point you to trusted CPAs I work with who specialize in real estate transactions.""",
            ),
            (
                "Can you help me buy my next home?",
                """Yes, and most of my clients choose to work with me on both sides. If you're selling and buying in the same window, we coordinate the timing carefully, using contingencies, bridge financing, or rent-back agreements to make the transition smooth. Selling and buying at the same time is one of the most complex things you can do in real estate, which is exactly why you want the same person managing both sides.""",
                """Yes, and most of my clients choose to work with me on both sides. If you're selling and buying in the same window, we coordinate the timing carefully, using contingencies, bridge financing, or rent-back agreements to make the transition smooth. Selling and buying at the same time is one of the most complex things you can do in real estate, which is exactly why you want the same person managing both sides.""",
            ),
            (
                "What if I'm relocating out of state?",
                """I work with a trusted network of agents nationally, so if you're moving to Texas, New York, or anywhere else, I can connect you with an agent I've personally vetted in that market. You get a referral I stand behind, and I stay in the loop to make sure your relocation goes smoothly on both ends.""",
                """I work with a trusted network of agents nationally, so if you're moving to Texas, New York, or anywhere else, I can connect you with an agent I've personally vetted in that market. You get a referral I stand behind, and I stay in the loop to make sure your relocation goes smoothly on both ends.""",
            ),
            (
                "Do you stay in touch after the sale?",
                """Yes. Most of my clients become long-term relationships, not one-time transactions. I check in a few times a year, keep you posted on market conditions, and am always available if you have questions about your home, your next move, or a friend's situation. I'm not going anywhere.""",
                """Yes. Most of my clients become long-term relationships, not one-time transactions. I check in a few times a year, keep you posted on market conditions, and am always available if you have questions about your home, your next move, or a friend's situation. I'm not going anywhere.""",
            ),
        ],
    ),
]


def faq_item(anchor: str, idx: int, q: str, html_a: str) -> str:
    item_id = f"faq-{anchor}-{idx}"
    return f"""
    <section data-expanded="false" class="m_0">
      <button type="button" data-expanded="false" aria-expanded="false" aria-controls="{item_id}-content" id="{item_id}-header" data-has-custom-icon="true"
              class="d_flex ai_center jc_space-between w_100% p_10px_40px_16px_0 bg-c_transparent bd_none cursor_pointer fs_14px md:fs_16px lh_24px md:lh_32px ta_left pos_relative bd-b_1px_solid_rgba(75,_92,_117,_0.1019607843) focus:ring_none">
        <h3 class="flex_1 fw_400 fs_16px">{q}</h3>
        <div class="pos_absolute right_0 d_flex ai_center jc_center w_20px h_20px">
          <svg width="14" height="14" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 6L10 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
            <path class="faq-icon-vertical" d="M6 2L6 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
          </svg>
        </div>
      </button>
      <div class="ov_hidden max-h_0 trs_max-height_0.2s_ease-out" id="{item_id}-content" role="region" aria-labelledby="{item_id}-header" style="max-height: 0px;">
        <div class="accordion-inner-content ov_hidden fs_16px fw_400 lh_24px bdr_16px mt_16px p_16px bg-c_#f7f7f7">{html_a}</div>
      </div>
    </section>"""


def category_section(anchor: str, num: str, headline: str, sub: str, items, is_alt_bg: bool) -> str:
    bg = "bg-c_#f2f0ef" if is_alt_bg else "bg_#fff"
    accordion = "\n".join(
        faq_item(anchor, idx + 1, q, html_a)
        for idx, (q, html_a, _plain) in enumerate(items)
    )
    return f"""
<section id="{anchor}" class="{bg} py_48px md:py_64px lg:py_72px" style="scroll-margin-top: 24px;">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <div class="ta_center mb_32px md:mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Category {num}</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_12px">{headline}</h2>
      <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px m_0">{sub}</p>
    </div>
    <div class="max-w_820px m_0_auto bd_none c_textBody [&:last-child_button]:bd-b_none">
      {accordion}
    </div>
  </div>
</section>
"""


CATEGORY_SECTIONS = "\n".join(
    category_section(anchor, num, headline, sub, items, is_alt_bg=(i % 2 == 1))
    for i, (anchor, num, headline, sub, items) in enumerate(CATEGORIES)
)


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Still have a question? Start the short qualifier.</h2>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A prep plan that doesn't burn your money.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">The three highest-leverage improvements and the three things not to touch. Over-improving is one of the most common ways sellers burn cash before listing.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">One agent. One phone. Same-hour replies.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Every offer, escrow question, and timeline shift routes through me on the same number.</p>
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
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">I help you decide what you are actually buying for, then narrow the field with a written framework. Saves weeks of touring homes that were never the right call.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Offers structured to actually win.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Tight contingencies, clean appraisal language, and seller credits used where they move price. Strategy adapts to the specific listing, not a template.</p>
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


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Didn't see your question?</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Drop your address. Ask whatever is on your mind.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Tell me what you are thinking about and I'll come back within the hour with a real answer, not a sales pitch.</p>

      <div id="faq-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


def _jsonld_question(q: str, plain_a: str) -> str:
    return '    {{"@type":"Question","name":"{q}","acceptedAnswer":{{"@type":"Answer","text":"{a}"}}}}'.format(
        q=q.replace("\\", "\\\\").replace('"', '\\"'),
        a=plain_a.replace("\\", "\\\\").replace('"', '\\"'),
    )


_all_jsonld_items = []
for _, _, _, _, items in CATEGORIES:
    for q, _html, plain in items:
        _all_jsonld_items.append(_jsonld_question(q, plain))


JSON_LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
    {"@type": "ListItem", "position": 2, "name": "FAQ", "item": "https://drozq.com/faq/"}
  ]
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
""" + ",\n".join(_all_jsonld_items) + """
  ]
}
</script>
"""


SMOOTH_SCROLL_SCRIPT = """
<script>
(function() {
  var pills = document.querySelectorAll('.faq-jump-pill');
  if (!pills.length) return;
  var reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var OFFSET = 24;
  var DURATION = 350;

  function smoothTo(targetY) {
    var start = window.scrollY;
    var dist = targetY - start;
    var t0 = null;
    function tick(now) {
      if (t0 === null) t0 = now;
      var p = Math.min((now - t0) / DURATION, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      window.scrollTo(0, start + dist * eased);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  pills.forEach(function(pill) {
    pill.addEventListener('click', function(e) {
      var href = this.getAttribute('href') || '';
      if (!href.startsWith('#') || href.length < 2) return;
      var target = document.getElementById(href.slice(1));
      if (!target) return;
      e.preventDefault();
      var top = target.getBoundingClientRect().top + window.scrollY - OFFSET;
      if (reduceMotion) {
        window.scrollTo(0, top);
      } else {
        smoothTo(top);
      }
      history.replaceState(null, '', href);
    });
  });
})();
</script>
"""


MAIN_BODY = (
    HERO
    + JUMP_NAV_STYLE
    + JUMP_NAV
    + CATEGORY_SECTIONS
    + MID_TABS
    + CLOSING_CTA
    + JSON_LD
    + SMOOTH_SCROLL_SCRIPT
)


if __name__ == "__main__":
    scaffold_page(
        target="faq/index.html",
        title="FAQ for Home Sellers | Joshua Guerrero, Real Brokerage",
        description="Honest answers to the questions home sellers actually ask. Pricing, commission, timeline, inspections, and what to expect when listing your home in Southern California.",
        canonical="/faq/",
        main_body_html=MAIN_BODY,
        og_title="FAQ for Home Sellers | Joshua Guerrero",
        og_description="29 questions sellers actually ask, answered honestly. Pricing, commission, timeline, inspections, escrow, taxes, and what to expect when listing in Southern California.",
    )
