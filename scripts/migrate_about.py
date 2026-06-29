"""Migrate /about/ to the homepage template scaffold.

The /about/ page is Joshua's bio / origin story page. It is the longest
piece of first-person writing on the site and the most "human" surface
in the funnel. The conversion job it does is different from every other
page: visitors who land on /about/ are not researching pricing or
shopping for a comparison agent. They are deciding whether to trust the
person.

The legacy page is brand-mode (mint/navy palette, custom design system,
lead-modal popover, brand-mode footer with full nav grid, 510-935-5701
phone). The migration drops all of that but preserves the copy verbatim
because the bio is the asset.

KILLED from the legacy page:
- Brand-mode CSS (mint/navy/green/red, custom font system, cf-* class
  hierarchy).
- Lead-modal popover form + the about-cta-strip "/contact" link CTA
  (replaced by inline 3-funnel + closing address pill).
- 510-935-5701 phone (replaced by 949-438-5948 site-wide).
- Brand-mode header with dropdown nav grid + brand-mode navy footer.
- cf-count-up animated stat counters (replaced with static numbers;
  the animation script lives in the brand-mode JS which we drop).

PRESERVED + reframed:
- Hero copy: "I'm not from here." + the Irvine / January 2026 license
  subline.
- Backstory section: 3 paragraphs about Vallejo / family / sacrifice.
  Joshua's portrait (Waist.png) moved out of the hero into this
  section as a 2-column split, since the backstory is the most
  personal copy on the page.
- By the Numbers stats: $1.1M volume / 2 homes / 20 units past life.
- The School: 3 paragraphs on car sales as training.
- The Pattern: 6 paragraphs on "rebuild the system" with concrete
  metrics (auto-dialer, e-commerce, waste management, dealerships).
- Values: 3 principles (Competitive Greatness / Unimpeachable
  Character / Speed is King) as numbered cards.
- The Mission: "Why real estate. Why now." 3 paragraphs.
- The Receipts: case file framing + 2 mini-cards linking to
  /testimonials/001-long-beach-firefighter/ and
  /testimonials/002-corona-analyst/ with the $23,250 and $20,000
  outcome stats preserved.
- The Closer: 3 paragraphs ending on "You get me."
- Person + BreadcrumbList JSON-LD (Person refreshed to current phone,
  brokerage = Real Brokerage, DRE).
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
    <img src="/media/images/crystal-cove.webp" alt="Southern California coastline at Crystal Cove" width="1280" height="640" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.4)"></div>
  </div>

  <section aria-labelledby="about-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="about-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">I'm not from here.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Irvine, California &middot; Licensed since January 2026.</p>
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


# Backstory section: 2-column split with Joshua's portrait on one side,
# the Vallejo origin story on the other. This is the most personal copy
# on the page; the face belongs next to it.
#
# The Panda CSS soup inherited from /index.html does not ship the arbitrary
# `md:grid-tc_280px_1fr` class. Without a real CSS rule the section stacks
# at desktop (portrait above copy, not beside it). The scoped
# `.drozq-portrait-split` class supplies the missing grid-template-columns.
# Mirror this same pattern on `/meet-the-team/` (see migrate_meet_the_team.py).
BACKSTORY = """
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
<section aria-labelledby="about-backstory-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="drozq-portrait-split">

      <div class="ta_center md:ta_left">
        <img src="/media/images/Waist.png" alt="Joshua Guerrero, Real Estate Agent" width="280" height="380" loading="lazy"
             class="d_inline-block w_220px md:w_280px h_auto bdr_16px ov_hidden bx-sh_0_16px_40px_rgba(30,_47,_73,_0.12)">
      </div>

      <div>
        <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Backstory</p>
        <h2 id="about-backstory-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px mb_16px">From Vallejo to Irvine.</h2>
        <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">I grew up in Vallejo. My family, my parents, my siblings, everyone I love, still lives there. When I tell people I moved to Los Angeles to build a real estate career, they usually nod politely. What they don't understand is what that actually cost.</p>
        <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">I see my family on weekends I can afford. I miss birthdays. I have dinner alone more nights than I'd like to admit. I made that trade on purpose, and I'd make it again.</p>
        <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Because I'm not here to sell a few houses. I'm here to build something.</p>
      </div>

    </div>
  </div>
</section>
"""


# Stats: ($number, $sublabel)
STATS = [
    ("$1.1M", "Volume closed"),
    ("2", "Homes sold"),
    ("20", "Units / month (past life)"),
]


def stat_item(number: str, sub: str) -> str:
    return f"""
      <div class="ta_center px_16px">
        <p class="c_#d92228 fw_800 fs_36px md:fs_44px lh_1.1 mb_8px m_0">{number}</p>
        <p class="c_#3f4650 fs_13px md:fs_14px fw_700 ls_0.5px m_0" style="text-transform:uppercase">{sub}</p>
      </div>"""


STATS_STRIP = """
<section aria-label="By the numbers" class="bg-c_#f2f0ef py_32px md:py_40px lg:py_48px">
  <div class="max-w_780px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <p class="ta_center c_#757575 fs_11px md:fs_12px fw_700 ls_2px mb_20px m_0_auto" style="text-transform:uppercase">By the Numbers</p>
    <div class="d_grid grid-tc_1fr_1fr_1fr gap_12px md:gap_24px ai_center">
""" + "\n".join(stat_item(n, s) for (n, s) in STATS) + """
    </div>
  </div>
</section>
"""


THE_SCHOOL = """
<section aria-labelledby="about-school-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px ta_center" style="text-transform:uppercase">The School</p>
    <h2 id="about-school-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">What car sales taught me.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Before real estate, I spent two years selling cars. Most people hear that and assume it's a red flag. I think it's the most important thing on my resume.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">I averaged 20 units a month. I was salesman of the month more times than I can count. My average front-end gross was $1,870 per deal, in an industry where the average salesperson barely clears half of that. I learned how to read a room in the first 90 seconds. I learned how to negotiate when the other side thinks they already won. I learned how to stay calm when a deal falls apart at 9:47pm on a Saturday night and put it back together by Sunday morning.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Every one of those skills translates directly to your home sale. When I sit across from a buyer's agent, I already know what they're going to say before they say it. When an inspection comes back with a list of issues, I already know which ones matter, which ones don't, and which ones I can turn into leverage for you.</p>
  </div>
</section>
"""


THE_PATTERN = """
<section aria-labelledby="about-pattern-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px ta_center" style="text-transform:uppercase">The Pattern</p>
    <h2 id="about-pattern-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">I don't just show up. I rebuild the system.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Look at my track record and you'll see the same thing in every chapter.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">At a real estate wholesaling startup, I built the auto-dialer system that cut call time by more than half, then wrote the scripts the rest of the team used.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">At an e-commerce company, I took a product doing $600 a month and built it to $7,500 by rebuilding the logistics from scratch.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">At a waste management startup, I took revenue from zero to $260,000 in a year by rewriting the deal structures the company had been using for years.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">At every dealership I worked at, I didn't just hit quota. I was top performer.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">The pattern isn't "he shows up." The pattern is "he shows up, he figures out what's broken, and he rebuilds it." That's what I do for my clients too.</p>
  </div>
</section>
"""


# (number, title, note)
VALUES = [
    ("01", "Competitive Greatness", "The willingness to do what average agents won't, on the days it matters most."),
    ("02", "Unimpeachable Character", "I'd rather lose a commission than lose your trust. Every time."),
    ("03", "Speed is King", "Deals die in the silence between messages. I don't let that silence happen."),
]


def value_card(num: str, name: str, note: str) -> str:
    return f"""
      <article class="bg_#fff bdr_16px p_28px md:p_32px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_12px">
        <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_2px m_0" style="text-transform:uppercase">Principle {num}</p>
        <h3 class="fs_22px md:fs_24px fw_700 c_#1a1816 lh_1.25 m_0">{name}</h3>
        <p class="fs_15px md:fs_16px lh_1.65 c_#3f4650 m_0">{note}</p>
      </article>"""


VALUES_SECTION = """
<section aria-labelledby="about-values-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">What I Stand On</p>
      <h2 id="about-values-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Three principles. No exceptions.</h2>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">
""" + "\n".join(value_card(n, t, b) for (n, t, b) in VALUES) + """
    </div>
  </div>
</section>
"""


THE_MISSION = """
<section aria-labelledby="about-mission-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px ta_center" style="text-transform:uppercase">The Mission</p>
    <h2 id="about-mission-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">Why real estate. Why now.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Selling cars was the school. Real estate is the career.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Because this is the transaction that matters. A car is a purchase. A home is a financial turning point, for the seller and the buyer. It's the biggest number most people will ever negotiate. And it's the one transaction where, in 2026, most agents are still operating the same way they did in 2006.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">I'm not interested in being an average agent. I'm interested in building a reputation that makes my clients tell their friends without being asked. That's the whole strategy. Do exceptional work. Document it. Let the work recruit the next client.</p>
  </div>
</section>
"""


# (slug, label, meta, headline, stat, stat_label, aria)
CASE_FILE_MINICARDS = [
    (
        "001-long-beach-firefighter",
        "Case File 001",
        "Long Beach &middot; First-Time Buyer",
        "He spends his career protecting other people's homes. We helped him acquire his first.",
        "$23,250",
        "Seller credit negotiated",
        "Read Case File 001: Long Beach firefighter, first-time buyer",
    ),
    (
        "002-corona-analyst",
        "Case File 002",
        "Corona &middot; Strategic Purchase",
        "He analyzes numbers for the State of California. Then he ran the numbers on us.",
        "$20,000",
        "Saved off asking price",
        "Read Case File 002: Corona financial analyst, strategic purchase",
    ),
]


def minicard(slug: str, label: str, meta: str, headline: str, stat: str, stat_label: str, aria: str) -> str:
    return f"""
      <a href="/testimonials/{slug}/" aria-label="{aria}"
         class="about-proof-card bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_12px c_#1a1816" style="text-decoration:none;">
        <span class="as_flex-start fs_11px fw_700 ls_2px c_#d92228 bg-c_#fdecec bd_1px_solid_#d92228 bdr_4px p_6px_12px" style="text-transform:uppercase">{label}</span>
        <p class="fs_11px fw_700 ls_1.5px c_#3f4650 m_0" style="text-transform:uppercase">{meta}</p>
        <h3 class="fs_18px md:fs_20px fw_700 c_#1a1816 lh_1.3 m_0">{headline}</h3>
        <div class="mt_auto pt_16px bd-t_1px_solid_#e5e5e5">
          <span class="d_block fs_28px md:fs_32px fw_800 c_#d92228 lh_1 mb_4px" style="font-variant-numeric: tabular-nums;">{stat}</span>
          <span class="fs_13px c_#3f4650 fw_500">{stat_label}</span>
        </div>
      </a>"""


THE_RECEIPTS = """
<style>
.about-proof-card {
  transition: box-shadow .2s ease, transform .2s ease, border-color .2s ease;
}
.about-proof-card:hover {
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
<section aria-labelledby="about-receipts-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Receipts</p>
      <h2 id="about-receipts-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">Every deal gets documented.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">I don't just tell you I do the work. I show you. Every transaction becomes a case file, anonymized to protect the client, with the real numbers, the real negotiation, and the real outcome. If you want to know how I think, read the case files.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(2,_1fr) gap_16px md:gap_20px mb_32px">
""" + "\n".join(minicard(*c) for c in CASE_FILE_MINICARDS) + """
    </div>

    <div class="ta_center">
      <a href="/testimonials/" class="btn-secondary-outline">Read more case files &rarr;</a>
    </div>
  </div>
</section>
"""


THE_CLOSER = """
<section aria-labelledby="about-closer-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px ta_center" style="text-transform:uppercase">The Closer</p>
    <h2 id="about-closer-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px d_none">The Closer</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">You get someone who is not waiting for your deal to be comfortable. Someone who has walked away from more deals than most agents have ever closed, because I'd rather lose a commission than lose your trust. Someone who will be responsive to the point of being annoying about it, because I know what it feels like to be on the other side of an agent who disappears for three days.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">You get someone who took the hardest path available and is not about to waste your time on the easy version.</p>
    <p class="c_#1a1816 fs_22px md:fs_28px fw_800 lh_1.3 m_0 ta_center mt_24px">You get me.</p>
  </div>
</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Put the work to use.</h2>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Negotiation trained in the hardest room.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Two years selling cars at 20 units a month before real estate. The skill set transfers directly to your offer table.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Responsiveness to the point of being annoying.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">I know what it feels like to be on the other side of an agent who disappears for three days. I don't do that.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Every deal becomes a case file.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Real numbers, real negotiation, real outcome. You can read every one before you decide to work with me.</p>
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


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Let's Talk</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Ready to sell?</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">If you've read this far, you already know I'm going to work harder on your listing than any other agent in Irvine. The next step is a 15-minute conversation. A clear look at what your home is worth and what it'll take to sell it well.</p>

      <div id="about-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
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
  "description": "Solo real estate agent based in Irvine, California. Trained in negotiation through two years selling cars at 20 units per month. Licensed January 2026.",
  "url": "https://drozq.com/about/",
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
    {"@type": "ListItem", "position": 2, "name": "About", "item": "https://drozq.com/about/"}
  ]
}
</script>
"""


MAIN_BODY = (
    HERO
    + BACKSTORY
    + STATS_STRIP
    + THE_SCHOOL
    + THE_PATTERN
    + VALUES_SECTION
    + THE_MISSION
    + THE_RECEIPTS
    + THE_CLOSER
    + MID_TABS
    + CLOSING_CTA
    + JSON_LD
)


if __name__ == "__main__":
    scaffold_page(
        target="about/index.html",
        title="About Joshua Guerrero | Irvine Listing Agent",
        description="From Vallejo to Irvine. Two years selling cars at 20 units a month before real estate. The training, the principles, and the receipts behind every listing.",
        canonical="/about/",
        main_body_html=MAIN_BODY,
        og_title="About Joshua Guerrero | Irvine Listing Agent",
        og_description="From Vallejo to Irvine. Two years selling cars at 20 units a month before real estate. The training, the principles, and the receipts behind every listing.",
    )
