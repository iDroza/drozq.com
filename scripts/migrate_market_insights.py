"""Migrate /market-insights/ to the homepage template scaffold.

The market insights page is the only "data product" on the site: a regularly
updated snapshot of where the Southern California housing market actually is,
county by county. The conversion job is anchor + authority: visitors who land
here are researching the market, and the funnel is the next step after they
trust the read.

KILLED from the legacy page:
- Brand-mode (mint/navy/green/red) palette + custom CSS reset.
- Brand-mode sticky header + 510-935-5701 phone + dropdown nav grid.
- Lead-modal popover form (replaced by the inline 3-funnel system).
- Brand-mode navy footer with 4-column grid + brokerage badge.
- Reports On Housing as the sourcing claim (their data is behind a $200/year
  paywall; can't reliably refresh from there). Re-source to public CAR +
  Redfin + Freddie Mac with explicit as-of dates.
- Stale March 30 / April 6, 2026 county snapshots.
- "Where does this data come from" section's MLS + Reports On Housing
  attribution (replaced with the live public-source attribution).

REFRESHED + reframed:
- All county data refreshed to the latest public reads (CAR April 2026 release
  for medians + sales, Redfin county data for days on market + inventory,
  Freddie Mac May 21, 2026 PMMS for the mortgage rate).
- New top-of-page "Snapshot" band: mortgage rate, statewide median, sales
  trend, OC tightness — the four numbers that frame everything below.
- New Irvine zoom section (Joshua is the solo agent in Irvine; his expertise
  is the city, not the abstract county aggregate).
- WebPage + 4 Dataset + BreadcrumbList JSON-LD, with refreshed
  spatialCoverage, creator, and dateModified fields.

Data as of:
- Mortgage rate: Freddie Mac PMMS, May 21, 2026
- Statewide + county medians + sales: California Association of Realtors,
  April 2026 release (published May 19, 2026)
- Days on market + inventory: Redfin Data Center, March-April 2026 (the
  latest monthly close at the time of writing)
- Irvine specifics: Redfin Data Center, May 2026

To refresh later, edit the SNAPSHOT, COUNTIES, and IRVINE dicts at the top of
this file, update SOURCE_DATE, and re-run.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page


SOURCE_DATE = "May 26, 2026"


# Top-of-page snapshot: 4 stats that frame everything below.
# (value, label, sublabel, direction: "up" / "down" / "flat")
SNAPSHOT = [
    ("6.51%",     "30-year mortgage rate",   "Freddie Mac PMMS, May 21",     "down"),
    ("$914,810",  "California median",       "Record high, April 2026",       "up"),
    ("+4.1%",     "Statewide sales YoY",     "275,580 annualized pace",       "up"),
    ("2.6 mo.",   "OC months of supply",     "Below the 3.2 statewide",       "flat"),
]


# Per-county snapshot: 4 stats per county.
# Each stat is (delta_str, label, detail, direction: "up" / "down" / "flat" / "days")
COUNTIES = [
    {
        "slug": "los-angeles-county",
        "num": "01",
        "name": "Los Angeles County",
        "updated": "April 2026 close",
        "stats": [
            ("$845,410",   "Median sale price",     "Up 2.1% YoY, April 2026 (CAR).",              "up"),
            ("+15%",       "Sales YoY",             "April 2026 sales pace vs April 2025 (CAR).",  "up"),
            ("45 days",    "Median days on market", "Up from 42 days last year (Redfin, March).",  "days"),
            ("21 days",    "SoCal regional median", "Down from 23 in March (CAR, April 2026).",    "down"),
        ],
        "interp": (
            "Los Angeles County keeps surprising people who only follow the headlines. Prices are "
            "still climbing year-over-year, sales are up sharply, and the regional median time on "
            "market actually dropped from March to April. The county is not soft. What's true is "
            "that homes are taking a few days longer than they did a year ago, and the buyers who "
            "are active are picky. Pricing on day one is the difference between selling in 30 days "
            "and selling in 90."
        ),
    },
    {
        "slug": "orange-county",
        "num": "02",
        "name": "Orange County",
        "updated": "April 2026 close",
        "stats": [
            ("$1.47M",     "Median sale price",     "Up 3.7% YoY, April 2026 (CAR).",              "up"),
            ("2.6 mo.",    "Months of supply",      "Below CA 3.2 and national 3.5 (CAR).",        "flat"),
            ("42 days",    "Median days on market", "Irvine specifically, May 2026 (Redfin).",     "days"),
            ("1% under",   "Close vs. list price",  "Homes under $2.5M, May 2026 weekly read.",    "flat"),
        ],
        "interp": (
            "Orange County remains the tightest of the four counties on this page. Months of supply "
            "is still under three, which by historical standards is a seller's market. The asterisk: "
            "the gap between asking and closing widened a touch in May, with homes under $2.5M "
            "closing about 1% below list. That's a normal, healthy spread. It is also a clear signal "
            "that overpricing is now punished faster than at any point since 2023. A real comp study "
            "still wins the listing here. A wishful price still loses it."
        ),
    },
    {
        "slug": "riverside-county",
        "num": "03",
        "name": "Riverside County",
        "updated": "March 2026 close",
        "stats": [
            ("$615K",      "Median sale price",     "Down 2.1% YoY, March 2026 (Redfin).",         "down"),
            ("+3.5%",      "Active inventory YoY",  "6,991 active listings (Feb 2026).",           "up"),
            ("55 days",    "Median days on market", "Up from 53 days last year (Redfin).",         "days"),
            ("Balanced",   "Market signal",         "More inventory, softer prices, slower DOM.",  "flat"),
        ],
        "interp": (
            "Riverside has cooled the most of the four counties. Prices are down year-over-year, "
            "inventory is up, and homes are taking about two more days to find a buyer. None of "
            "that is a crash. It is a market that has rebalanced toward the buyer enough that "
            "sellers who price aggressively, prep the home properly, and act decisively still "
            "close on a reasonable timeline. The sellers who treat it like 2022 sit at 120 days."
        ),
    },
    {
        "slug": "san-bernardino-county",
        "num": "04",
        "name": "San Bernardino County",
        "updated": "March 2026 close",
        "stats": [
            ("$535K",      "Median sale price",     "Down 2.7% YoY, March 2026 (Redfin).",         "down"),
            ("+2.1%",      "Active inventory YoY",  "7,378 active listings (Redfin).",             "up"),
            ("52 days",    "Median days on market", "Up 1 day YoY (Redfin).",                      "days"),
            ("25.6%",      "Sold above list",       "Down 8.1 pp YoY (Redfin).",                   "down"),
        ],
        "interp": (
            "San Bernardino County is the most rate-sensitive of the four. With the median home "
            "around $535K, more buyers here are financing the full purchase, so every 25 basis "
            "points on the mortgage rate moves the offer math. Year-over-year, the share of homes "
            "selling above list dropped from a third to a quarter, which is the cleanest signal "
            "on this page that the bidding-war era is functionally over in the Inland Empire. The "
            "good news for sellers: inventory is only modestly higher than a year ago, so the "
            "right home priced right still moves."
        ),
    },
]


# Irvine zoom section. Joshua is the solo agent in Irvine; his expertise is
# the city, not the abstract OC aggregate.
IRVINE = {
    "median":      ("$1.5M",   "Median sale price",       "Down 5.9% YoY (Redfin, May 2026)."),
    "ppsf":        ("$793",    "Median price per sq ft",  "Down 9.06% YoY (Redfin)."),
    "dom":         ("42 days", "Median days on market",   "Two offers on average."),
    "competitive": ("Mod.",    "Market competitiveness",  "\"Somewhat competitive\" rating (Redfin)."),
}


# Two-section hero with a coastal-modern-home background. Page-specific copy and
# tab-CTA mirror the canonical pattern in /TEMPLATE.md section 4.
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

  <section aria-labelledby="mi-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="mi-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">Where the Southern California market actually is.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">The same data I use to advise clients on pricing, timing, and strategy, refreshed {SOURCE_DATE}.</p>
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


# Scoped stat card style. Panda CSS does not ship rules for the colored
# directional arrows or the tabular-numeric stat layout, so define them once
# here.
STAT_STYLE = """
<style>
.drozq-mi-stat-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 640px) { .drozq-mi-stat-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 960px) { .drozq-mi-stat-grid { grid-template-columns: repeat(4, 1fr); gap: 20px; } }
.drozq-mi-stat {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.drozq-mi-stat__top {
  display: inline-flex;
  align-items: baseline;
  gap: 10px;
}
.drozq-mi-stat__value {
  font-size: clamp(1.85rem, 3.6vw, 2.5rem);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}
.drozq-mi-stat__value--up { color: #0a801f; }
.drozq-mi-stat__value--down { color: #b81d22; }
.drozq-mi-stat__value--flat { color: #1a1816; }
.drozq-mi-stat__value--days { color: #1a1816; }
.drozq-mi-stat__label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #3f4650;
  line-height: 1.35;
  margin: 0;
}
.drozq-mi-stat__detail {
  font-size: 0.92rem;
  line-height: 1.5;
  color: #3f4650;
  margin: 0;
}
.drozq-mi-pill-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}
.drozq-mi-pill {
  display: inline-flex;
  align-items: center;
  padding: 10px 18px;
  border-radius: 999px;
  border: 1px solid #e5e5e5;
  background: #ffffff;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1a1816;
  letter-spacing: 0.01em;
  text-decoration: none;
  transition: border-color .2s ease, color .2s ease, transform .2s ease;
}
.drozq-mi-pill:hover { border-color: #d92228; color: #d92228; transform: translateY(-1px); }
.drozq-mi-pill__num {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  color: #d92228;
  margin-right: 8px;
  opacity: 0.85;
}
</style>
"""


def snapshot_card(value: str, label: str, sublabel: str, direction: str) -> str:
    return f"""
      <div class="drozq-mi-stat">
        <div class="drozq-mi-stat__top">
          <span class="drozq-mi-stat__value drozq-mi-stat__value--{direction}">{value}</span>
        </div>
        <p class="drozq-mi-stat__label">{label}</p>
        <p class="drozq-mi-stat__detail">{sublabel}</p>
      </div>"""


SNAPSHOT_SECTION = f"""
<section aria-labelledby="mi-snapshot-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Snapshot</p>
      <h2 id="mi-snapshot-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Four numbers that frame the rest of the page.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">The mortgage rate, the statewide median, the direction of sales, and how tight Orange County still is. Read these first. The county breakdowns below tell you what they mean for your specific zip.</p>
    </div>

    <div class="drozq-mi-stat-grid">
""" + "\n".join(snapshot_card(v, l, sl, d) for (v, l, sl, d) in SNAPSHOT) + """
    </div>
  </div>
</section>
"""


HOW_TO_READ = """
<section aria-labelledby="mi-howto-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">How to Read This</p>
    <h2 id="mi-howto-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">Numbers without context are noise.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Every county block below shows four numbers: where the median sale price is now, how the past twelve months have moved, how long the average home is sitting before going under contract, and a fourth signal that matters for that specific county. Read those four together and you'll know whether your county is leaning toward sellers, leaning toward buyers, or roughly balanced.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">If you want to know what these numbers mean for your specific home, that's the conversation worth having on a call.</p>
  </div>
</section>
"""


JUMP_NAV = """
<section aria-label="Jump to county" class="bg_#fff py_24px md:py_32px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <p class="ta_center c_#757575 fs_11px md:fs_12px fw_700 ls_2px mb_16px" style="text-transform:uppercase">Jump to your county</p>
    <nav class="drozq-mi-pill-row" aria-label="Jump to county">
      <a class="drozq-mi-pill" href="#los-angeles-county"><span class="drozq-mi-pill__num">01</span>Los Angeles County</a>
      <a class="drozq-mi-pill" href="#orange-county"><span class="drozq-mi-pill__num">02</span>Orange County</a>
      <a class="drozq-mi-pill" href="#riverside-county"><span class="drozq-mi-pill__num">03</span>Riverside County</a>
      <a class="drozq-mi-pill" href="#san-bernardino-county"><span class="drozq-mi-pill__num">04</span>San Bernardino County</a>
      <a class="drozq-mi-pill" href="#irvine-zoom"><span class="drozq-mi-pill__num">+</span>Irvine zoom</a>
    </nav>
  </div>
</section>
"""


def county_section(slug: str, num: str, name: str, updated: str, stats: list, interp: str, alt_bg: bool) -> str:
    bg_class = "bg-c_#f2f0ef" if alt_bg else "bg_#fff"
    stat_cards = "\n".join(snapshot_card(v, l, d, dir_) for (v, l, d, dir_) in stats)
    return f"""
<section aria-labelledby="mi-{slug}-title" id="{slug}" class="{bg_class} py_48px md:py_64px lg:py_72px" style="scroll-margin-top:24px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">County {num}</p>
      <h2 id="mi-{slug}-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_8px">{name}</h2>
      <p class="c_#757575 fs_13px md:fs_14px ls_0.5px m_0">As of {updated}</p>
    </div>

    <div class="drozq-mi-stat-grid mb_32px md:mb_40px">
{stat_cards}
    </div>

    <div class="max-w_640px m_0_auto ta_center">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">What this means for sellers</p>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">{interp}</p>
    </div>
  </div>
</section>
"""


COUNTY_SECTIONS = "".join(
    county_section(c["slug"], c["num"], c["name"], c["updated"], c["stats"], c["interp"], alt_bg=(i % 2 == 0))
    for i, c in enumerate(COUNTIES)
)


IRVINE_ZOOM = f"""
<section aria-labelledby="mi-irvine-title" id="irvine-zoom" class="bg_#fff py_48px md:py_64px lg:py_72px" style="scroll-margin-top:24px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Local zoom</p>
      <h2 id="mi-irvine-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_8px">Irvine, specifically.</h2>
      <p class="c_#757575 fs_13px md:fs_14px ls_0.5px m_0">Redfin, May 2026</p>
    </div>

    <div class="drozq-mi-stat-grid mb_32px md:mb_40px">
{snapshot_card(IRVINE["median"][0],      IRVINE["median"][1],      IRVINE["median"][2],      "down")}
{snapshot_card(IRVINE["ppsf"][0],        IRVINE["ppsf"][1],        IRVINE["ppsf"][2],        "down")}
{snapshot_card(IRVINE["dom"][0],         IRVINE["dom"][1],         IRVINE["dom"][2],         "days")}
{snapshot_card(IRVINE["competitive"][0], IRVINE["competitive"][1], IRVINE["competitive"][2], "flat")}
    </div>

    <div class="max-w_640px m_0_auto ta_center">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">What this means in Irvine</p>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Irvine is the only number on this page that has dropped meaningfully YoY. The median is down 5.9% and price per square foot is down 9%, both of which reflect a shift from 2024's bidding-war pricing to a more normal market. Two offers per listing is still healthy. Forty-two days is a normal sale timeline.</p>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">The Irvine market rewards three things now: clean preparation, defensible pricing on day one, and an agent who actually shows up to compete. The last twenty years of automatic appreciation isn't doing the work anymore. Strategy is.</p>
    </div>
  </div>
</section>
"""


SOURCE_SECTION = f"""
<section aria-labelledby="mi-source-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Source</p>
    <h2 id="mi-source-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">Where this data actually comes from.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Medians and statewide sales come from the California Association of Realtors monthly release (April 2026 close, published May 19, 2026). Days on market and active inventory come from Redfin Data Center (March-April 2026 close, the latest monthly read at the time of writing). The mortgage rate is Freddie Mac's PMMS, dated May 21, 2026. Irvine-specific numbers come from Redfin, May 2026.</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">I refresh this page on a regular cadence. The page header carries the date of the current read so you always know how fresh the snapshot is.</p>
  </div>
</section>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Run the numbers on your specific home.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">County averages are the starting point. The price your home will actually clear depends on the block, the condition, the comps, and the agent. Pick a side and I'll run the read.</p>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Your block, not the county average.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">A real comp study uses the eight to twelve homes most like yours, not the county-wide median.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A defensible price, not a wishful one.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">I price to the comps and tell you what to fix, what to skip, and what to leverage.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">3</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A 48-hour launch with the marketing already done.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Pro photos, copy, syndication, and a property landing page all live within two days of signing.</p>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">A buying read tuned to your county.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Orange County looks nothing like San Bernardino. Your offer math should reflect that.</p>
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
<section aria-labelledby="mi-crosslink-title" class="bg-c_#f2f0ef py_48px md:py_64px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Want the deeper read?</p>
    <h2 id="mi-crosslink-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_24px md:fs_30px ls_0.3px mb_16px">The notes behind the numbers.</h2>
    <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px mb_24px m_0_auto" style="max-width:560px;">Stats give you the snapshot. Field Notes give you the commentary. Short observational posts on what's actually happening in Southern California real estate, written when there's something worth saying.</p>
    <a href="/field-notes/" class="btn-secondary-outline">Read Field Notes &rarr;</a>
  </div>
</section>
"""


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Your home, your number</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The data is one thing. Your home is another.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">County-level data is useful, but it doesn't tell you what your specific home, in your specific neighborhood, will actually sell for. That's what a real comparative market analysis is for. Free, delivered within 24 hours.</p>

      <div id="mi-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


JSON_LD = f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Southern California Real Estate Market Insights",
  "description": "Refreshed against CAR, Redfin, and Freddie Mac. Median prices, days on market, sales trends, and inventory direction for Los Angeles, Orange, Riverside, and San Bernardino counties, plus an Irvine zoom.",
  "url": "https://drozq.com/market-insights/",
  "dateModified": "2026-05-26",
  "author": {{"@type": "Person", "name": "Joshua Guerrero"}},
  "mainEntity": [
    {{
      "@type": "Dataset",
      "name": "Los Angeles County Real Estate Market Data",
      "description": "Median sale price, days on market, sales YoY, and regional median time on market for Los Angeles County, refreshed monthly.",
      "url": "https://drozq.com/market-insights/#los-angeles-county",
      "spatialCoverage": {{"@type": "Place", "name": "Los Angeles County, California"}},
      "creator": {{"@type": "Person", "name": "Joshua Guerrero"}},
      "license": "https://drozq.com/privacy/"
    }},
    {{
      "@type": "Dataset",
      "name": "Orange County Real Estate Market Data (Includes Irvine)",
      "description": "Median sale price, months of supply, days on market, and sale-to-list spread for Orange County and Irvine, refreshed monthly.",
      "url": "https://drozq.com/market-insights/#orange-county",
      "spatialCoverage": [
        {{"@type": "Place", "name": "Orange County, California"}},
        {{"@type": "Place", "name": "Irvine, California"}}
      ],
      "creator": {{"@type": "Person", "name": "Joshua Guerrero"}},
      "license": "https://drozq.com/privacy/"
    }},
    {{
      "@type": "Dataset",
      "name": "Riverside County Real Estate Market Data",
      "description": "Median sale price, active inventory YoY, days on market, and market signal for Riverside County, refreshed monthly.",
      "url": "https://drozq.com/market-insights/#riverside-county",
      "spatialCoverage": {{"@type": "Place", "name": "Riverside County, California"}},
      "creator": {{"@type": "Person", "name": "Joshua Guerrero"}},
      "license": "https://drozq.com/privacy/"
    }},
    {{
      "@type": "Dataset",
      "name": "San Bernardino County Real Estate Market Data",
      "description": "Median sale price, active inventory YoY, days on market, and share of homes sold above list for San Bernardino County, refreshed monthly.",
      "url": "https://drozq.com/market-insights/#san-bernardino-county",
      "spatialCoverage": {{"@type": "Place", "name": "San Bernardino County, California"}},
      "creator": {{"@type": "Person", "name": "Joshua Guerrero"}},
      "license": "https://drozq.com/privacy/"
    }}
  ]
}}
</script>

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"}},
    {{"@type": "ListItem", "position": 2, "name": "Market Insights", "item": "https://drozq.com/market-insights/"}}
  ]
}}
</script>
"""


MAIN_BODY = (
    HERO
    + STAT_STYLE
    + SNAPSHOT_SECTION
    + HOW_TO_READ
    + JUMP_NAV
    + COUNTY_SECTIONS
    + IRVINE_ZOOM
    + SOURCE_SECTION
    + MID_TABS
    + CROSSLINK
    + CLOSING_CTA
    + JSON_LD
)


if __name__ == "__main__":
    scaffold_page(
        target="market-insights/index.html",
        title="Southern California Market Insights | Joshua Guerrero, Real Brokerage",
        description="Refreshed against CAR, Redfin, and Freddie Mac. Median prices, days on market, sales trends, and inventory for Los Angeles, Orange, Riverside, and San Bernardino counties, plus an Irvine zoom.",
        canonical="/market-insights/",
        main_body_html=MAIN_BODY,
        og_title="Southern California Market Insights | Joshua Guerrero",
        og_description="Where the Southern California housing market actually is. Refreshed against CAR, Redfin, and Freddie Mac. Four counties plus an Irvine zoom.",
    )
