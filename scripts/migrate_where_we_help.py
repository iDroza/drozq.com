"""Migrate /where-we-help/ to the homepage template scaffold.

This is the service-area hub. Its unique value is the city grid: 38
SoCal cities across 6 counties, each one its own conversion entry into
the inline funnel. Click a city card -> Sell funnel opens with that
city pre-seeded into the location input. This is the page's primary
conversion mechanic and the reason the SEO areaServed schema exists.

KILLED from the legacy page:
- Brand-mode hero with "Sell Your Home With a Trusted Southern
  California Realtor" + Waist.png portrait.
- Intro section + Property Types + About Joshua + What Makes Me
  Different (all replaced by the more focused homepage-template
  sections: 3-tier coverage, why-work-with-me, mid-page tabs).
- 510-935-5701 phone everywhere.
- Brand-mode lead-modal flow (replaced with inline funnel).
- Brand-mode navy footer + topbar.

PRESERVED + reframed:
- 38-city grid grouped by county. Each city card is now a form whose
  hidden `location` input is seeded with the city, wrapped in a
  Sell-mode tabpanel so click -> Sell funnel opens with that city.
- 5 service-area FAQ items verbatim (with telephone updated).
- All three JSON-LD blocks (RealEstateAgent with full 38-city
  areaServed list, BreadcrumbList, FAQPage). Telephone updated to
  the site-wide 949-438-5948.
- LA County cities (LA, Pasadena, Long Beach, Santa Monica, Torrance,
  Redondo Beach, Burbank, Glendale, Malibu) preserve their secondary
  link to /los-angeles/ via a "Read the LA listing playbook" sub-CTA
  surfaced below the LA County county header.
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

  <section aria-labelledby="wwh-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="wwh-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">Selling across Southern California.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Direct in Orange County, active across LA and the South Bay, partnered everywhere else.</p>
    </div>
  </section>

  <section aria-label="Compare Southern California real estate agents" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px">
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
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter your Southern California address")}</div>
            </div>
            <div id="tabpanel-buy"      role="tabpanel" aria-labelledby="tab-buy"      hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("City, neighborhood, or ZIP", value="Southern California")}</div>
            </div>
            <div id="tabpanel-sell-buy" role="tabpanel" aria-labelledby="tab-sell-buy" hidden class="d_none">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">{landing_form_pill("Enter your Southern California address")}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </section>
</div>
"""


# (city, county, image_filename, alt_text, tier)
# tier: 1=Direct (OC), 2=Active (LA County), 3=Referral (everywhere else)
CITIES = [
    # Orange County (Tier 1 - Direct service)
    ("Irvine",            "Orange County",         "irvine.jpeg",          "Irvine, California",          1),
    ("Newport Beach",     "Orange County",         "newport-beach.jpg",    "Newport Beach, California",   1),
    ("Costa Mesa",        "Orange County",         "coasta-mesa.jpg",      "Costa Mesa, California",      1),
    ("Mission Viejo",     "Orange County",         "mission-viejo.jpg",    "Mission Viejo, California",   1),
    ("Laguna Niguel",     "Orange County",         "laguna-niguel.jpg",    "Laguna Niguel, California",   1),
    ("Lake Forest",       "Orange County",         "lake-forest.jpeg",     "Lake Forest, California",     1),
    ("Laguna Hills",      "Orange County",         "laguna-hills.webp",    "Laguna Hills, California",    1),
    ("Tustin",            "Orange County",         "tustin.webp",          "Tustin, California",          1),
    ("Anaheim",           "Orange County",         "anaheim.jpg",          "Anaheim, California",         1),
    ("Fullerton",         "Orange County",         "fullerton.jpg",        "Fullerton, California",       1),
    ("Huntington Beach",  "Orange County",         "huntington-beach.webp","Huntington Beach, California",1),
    ("Garden Grove",      "Orange County",         "garden-grove.jpg",     "Garden Grove, California",    1),
    ("Santa Ana",         "Orange County",         "santa-ana.jpg",        "Santa Ana, California",       1),
    ("Westminster",       "Orange County",         "westminster.jpg",      "Westminster, California",     1),
    ("Yorba Linda",       "Orange County",         "yorba-linda.jpg",      "Yorba Linda, California",     1),
    # Los Angeles County (Tier 2 - Active service)
    ("Los Angeles",       "Los Angeles County",    "los-angeles.webp",     "Los Angeles, California",     2),
    ("Pasadena",          "Los Angeles County",    "pasadena.jpeg",        "Pasadena, California",        2),
    ("Long Beach",        "Los Angeles County",    "long-beach.jpg",       "Long Beach, California",      2),
    ("Santa Monica",      "Los Angeles County",    "santa-monica.jpg",     "Santa Monica, California",    2),
    ("Torrance",          "Los Angeles County",    "torrance.jpg",         "Torrance, California",        2),
    ("Redondo Beach",     "Los Angeles County",    "redondo-beach.jpg",    "Redondo Beach, California",   2),
    ("Burbank",           "Los Angeles County",    "burbank.webp",         "Burbank, California",         2),
    ("Glendale",          "Los Angeles County",    "glendale.webp",        "Glendale, California",        2),
    ("Malibu",            "Los Angeles County",    "malibu.jpeg",          "Malibu, California",          2),
    # Riverside County (Tier 3 - Referral)
    ("Riverside",         "Riverside County",      "riverside.jpg",        "Riverside, California",       3),
    ("Corona",            "Riverside County",      "Corona.webp",          "Corona, California",          3),
    ("Murrieta",          "Riverside County",      "Murrieta.webp",        "Murrieta, California",        3),
    ("Temecula",          "Riverside County",      "temecula.avif",        "Temecula, California",        3),
    ("Lake Elsinore",     "Riverside County",      "lake-elsinore.webp",   "Lake Elsinore, California",   3),
    # San Bernardino County (Tier 3 - Referral)
    ("Rancho Cucamonga",  "San Bernardino County", "rancho-cucamonga.jpg", "Rancho Cucamonga, California",3),
    ("Fontana",           "San Bernardino County", "fontana.jpg",          "Fontana, California",         3),
    ("Chino",             "San Bernardino County", "chino.jpg",            "Chino, California",           3),
    ("Chino Hills",       "San Bernardino County", "chino-hills.webp",     "Chino Hills, California",     3),
    # San Diego County (Tier 3 - Referral)
    ("San Diego",         "San Diego County",      "san-diego.jpg",        "San Diego, California",       3),
    ("Carlsbad",          "San Diego County",      "carlsbad.webp",        "Carlsbad, California",        3),
    ("Oceanside",         "San Diego County",      "oceanside.jpg",        "Oceanside, California",       3),
    # Ventura County (Tier 3 - Referral)
    ("Thousand Oaks",     "Ventura County",        "thousand-oaks.webp",   "Thousand Oaks, California",   3),
    ("Simi Valley",       "Ventura County",        "simi-valley.jpg",      "Simi Valley, California",     3),
]


TIER_LABEL = {
    1: ("Direct service", "I personally manage every listing here."),
    2: ("Active service", "I work these submarkets regularly and have closed transactions in them."),
    3: ("Referral network", "Vetted local partners I have personally chosen. I stay involved on strategy."),
}


def city_card(city: str, county: str, image: str, alt: str) -> str:
    return f"""
    <form class="m_0">
      <input type="hidden" name="location" value="{city}, CA">
      <input type="hidden" name="gclid" value="">
      <button type="submit"
              class="d_flex flex-d_column w_100% h_100% bd_1px_solid_#e5e5e5 bg_#fff bdr_16px ov_hidden cursor_pointer p_0 ta_left c_inherit hover:bd-c_#d92228 trs_all_.2s_ease">
        <div class="w_100% pos_relative" style="aspect-ratio: 4 / 3; overflow: hidden;">
          <img src="/media/images/{image}" alt="{alt}" loading="lazy" decoding="async"
               width="320" height="240"
               style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block;">
        </div>
        <div class="d_flex flex-d_column gap_4px p_16px md:p_20px w_100% bx-s_border-box">
          <p class="fs_11px fw_700 ls_1.5px c_#d92228 m_0" style="text-transform:uppercase">{county}</p>
          <span class="fs_18px md:fs_20px fw_700 c_#1a1816 lh_1.3">{city}</span>
          <span class="fs_13px md:fs_14px c_#3f4650 mt_4px">Sell my {city} home &rarr;</span>
        </div>
      </button>
    </form>"""


def tier_section(tier: int, anchor: str) -> str:
    label, sub = TIER_LABEL[tier]
    cities_in_tier = [(c, co, im, al) for (c, co, im, al, t) in CITIES if t == tier]
    counties = []
    for (_, county, _, _) in cities_in_tier:
        if county not in counties:
            counties.append(county)
    county_str = " &middot; ".join(counties)
    cards = "\n".join(city_card(c, co, im, al) for (c, co, im, al) in cities_in_tier)
    extra_la_link = ""
    if tier == 2:
        extra_la_link = (
            '<div class="ta_center mt_24px">'
            '<a href="/los-angeles/" class="btn-secondary-outline">Read the full Los Angeles listing playbook &rarr;</a>'
            '</div>'
        )
    return f"""
<section id="{anchor}" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1200px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">
    <div class="ta_center mb_32px md:mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Tier {tier} &middot; {label}</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_26px md:fs_34px ls_0.3px ta_center mb_12px">{county_str}</h2>
      <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px m_0">{sub} Tap a city to start the Sell funnel with that city pre-filled.</p>
    </div>

    <div class="d_grid grid-tc_repeat(2,_1fr) md:grid-tc_repeat(3,_1fr) lg:grid-tc_repeat(4,_1fr) gap_12px md:gap_20px">
      {cards}
    </div>

    {extra_la_link}
  </div>
</section>
"""


CITY_GRID_WRAPPER_OPEN = """
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
<div role="tabpanel" aria-labelledby="tab-sell" id="city-grid-tabpanel" class="d_block">
<section class="bg-c_#f2f0ef py_32px md:py_40px">
  <div class="max-w_780px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Coverage</p>
    <h2 class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px mb_12px">38 cities. 6 counties. One standard.</h2>
    <p class="c_#3f4650 fs_16px md:fs_17px lh_28px m_0">Grouped into three tiers based on how I cover each market. Same standard on every listing, regardless of tier. Don't see your city? Drop your address in the closing form and I'll route you to the right agent in my network.</p>
  </div>
</section>
"""

CITY_GRID_WRAPPER_CLOSE = "</div>\n"


CITY_GRID = (
    CITY_GRID_WRAPPER_OPEN
    + tier_section(1, "tier-direct")
    + tier_section(2, "tier-active")
    + tier_section(3, "tier-referral")
    + CITY_GRID_WRAPPER_CLOSE
)


WHY = """
<section aria-labelledby="wwh-why-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_16px pr_32px md:pr_16px">

    <div class="ta_center mb_40px max-w_780px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Why Work With Me</p>
      <h2 id="wwh-why-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">What you get, regardless of tier.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">The level of involvement scales with how close you are to me. The standard does not.</p>
    </div>

    <div class="d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px">

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="2.4"/><circle cx="24" cy="24" r="10" stroke="currentColor" stroke-width="2.4"/><path d="M24 4v8M24 36v8M4 24h8M36 24h8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>
        </div>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Negotiation that translates.</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">I learned negotiation in the most adversarial sales environment in America (car sales) before moving into real estate. The skill set transfers directly. When I sit across from a buyer's agent on your deal, I already know how the conversation ends.</p>
      </article>

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
        <div class="d_inline-flex ai_center jc_center w_44px h_44px c_#d92228 mb_8px">
          <svg viewBox="0 0 48 48" fill="none" width="38" height="38" aria-hidden="true"><rect x="11" y="6" width="26" height="36" rx="3" stroke="currentColor" stroke-width="2.4"/><path d="M17 17h14M17 24h14M17 31h10" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>
        </div>
        <h3 class="fs_20px md:fs_22px fw_700 c_#1a1816 lh_1.25 m_0">Documented results.</h3>
        <p class="fs_14px md:fs_15px lh_1.6 c_#3f4650 m_0">Every transaction I close becomes a case file with the actual numbers, the actual negotiation, and the actual outcome. You can read them before we even talk. Most agents ask you to trust them. I show you the receipts.</p>
      </article>

      <article class="bg_#fff bdr_16px p_24px md:p_28px bd_1px_solid_#e5e5e5 d_flex flex-d_column gap_8px">
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
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Why work with an agent in Southern California?</h2>
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
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Local comps, not statewide averages.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Pricing built on active and pending sales inside your specific submarket, not a national algorithm.</p>
          </div>
        </li>
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">2</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Marketing that earns the listing premium.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">Professional photography, video, paid syndication, and a real pre-list prep plan. Marketing pays for itself in days saved on market.</p>
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
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("Your Southern California address")}</div>
    </div>

    <div id="buyTab" role="tabpanel" aria-labelledby="buyTabBtn" hidden class="d_none mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <ul class="d_flex flex-d_column gap_24px lg:gap_44px m_0 li-s_none p_0 mb_32px">
        <li class="d_flex ai_flex-start gap_16px">
          <span class="flex-sh_0 d_inline-flex ai_center jc_center w_40px h_40px bdr_full bg-c_#fbe9ea c_#d92228 fw_700" aria-hidden="true">1</span>
          <div>
            <h3 class="fs_16px lg:fs_20px fw_700 lh_24px lg:lh_24px mb_8px c_#1a1816">Search across SoCal without losing your shortlist.</h3>
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">From the coast to the Inland Empire, I keep your shortlist tight with real notes on why each home is in or out.</p>
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
            <p class="c_#757575 fs_14px lg:fs_16px lh_21px lg:lh_24px m_0">A vetted bench of SoCal-specific partners means escrow runs on schedule and inspection reports come back in plain English.</p>
          </div>
        </li>
      </ul>

      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Tell me where you want to buy.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("City, neighborhood, or ZIP", value="Southern California")}</div>
    </div>

  </div>
</section>
"""


def faq_item(idx: int, q: str, a: str) -> str:
    return f"""
    <section data-expanded="false" class="m_0">
      <button type="button" data-expanded="false" aria-expanded="false" aria-controls="wwh-faq-{idx}-content" id="wwh-faq-{idx}-header" data-has-custom-icon="true"
              class="d_flex ai_center jc_space-between w_100% p_10px_40px_16px_0 bg-c_transparent bd_none cursor_pointer fs_14px md:fs_16px lh_24px md:lh_32px ta_left pos_relative bd-b_1px_solid_rgba(75,_92,_117,_0.1019607843) focus:ring_none">
        <h3 class="flex_1 fw_400 fs_16px">{q}</h3>
        <div class="pos_absolute right_0 d_flex ai_center jc_center w_20px h_20px">
          <svg width="14" height="14" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 6L10 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
            <path class="faq-icon-vertical" d="M6 2L6 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
          </svg>
        </div>
      </button>
      <div class="ov_hidden max-h_0 trs_max-height_0.2s_ease-out" id="wwh-faq-{idx}-content" role="region" aria-labelledby="wwh-faq-{idx}-header" style="max-height: 0px;">
        <div class="accordion-inner-content ov_hidden fs_16px fw_400 lh_24px bdr_16px mt_16px p_16px bg-c_#f7f7f7">{a}</div>
      </div>
    </section>"""


FAQ_ITEMS = [
    ("What counties do you cover in Southern California?",
     "I list and sell homes across Orange County, Los Angeles County, Riverside County, San Bernardino County, San Diego County, and Ventura County. If you're in any of those counties, I can help, from beach properties to inland single-family homes, condos, and multi-unit properties."),
    ("My city isn't on the list. Can you still help me?",
     "The grid above is a snapshot, not an exhaustive list. I routinely take listings in smaller and neighboring communities throughout Southern California. If you don't see your city, drop your address in the closing form or call (949) 438-5948. I'll either handle it directly or connect you with a vetted agent in my network."),
    ("Do you charge more to sell homes outside your home market?",
     "No. Pricing is based on the listing itself, including price point, condition, and scope of work, not the city. You get the same marketing package, negotiation support, and transaction management whether your home is in Irvine, Long Beach, Temecula, or San Diego."),
    ("Can you handle condos, townhomes, and multi-unit properties?",
     "Yes. I list single-family homes, condos, townhomes, and small multi-family properties (duplexes, triplexes, fourplexes) throughout Southern California. Each property type has its own pricing, marketing, and buyer pool, and I'll build a strategy around yours."),
    ("How fast can you get my home on the market?",
     "For most listings, I can be on the MLS within 7 to 10 days of signing the listing agreement, sometimes faster if your home is already show-ready. That includes photography, staging consultation, listing prep, and marketing launch. If you need to move faster, let me know during our initial call and we'll compress the timeline."),
]


FAQ = """
<section class="max-w_1035px mt_48px md:mt_64px mb_64px mx_auto pl_32px md:pl_16px pr_32px md:pr_16px">
  <div class="ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">FAQ</p>
    <h2 class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_45px fs_24px md:fs_30px mb_32px md:mb_48px ta_center">Service area questions.</h2>
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
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Don't see your city above?</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Drop your address. I'll route it to the right agent.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">If your city is on the grid, I will follow up within the hour. If it isn't, I will connect you with a vetted partner in my network and stay involved on strategy.</p>

      <div id="wwh-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your Southern California address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


_areaServed_cities = ",\n".join(
    f'    {{"@type":"City","name":"{c}"}}' for (c, _, _, _, _) in CITIES
)
_areaServed_counties = ",\n".join(
    f'    {{"@type":"AdministrativeArea","name":"{co}"}}' for co in [
        "Los Angeles County",
        "Orange County",
        "San Diego County",
        "Riverside County",
        "San Bernardino County",
        "Ventura County",
    ]
)


JSON_LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "RealEstateAgent",
  "name": "Joshua Guerrero",
  "url": "https://drozq.com/where-we-help/",
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
    "latitude": "33.6846",
    "longitude": "-117.8265"
  },
  "areaServed": [
""" + _areaServed_cities + """,
""" + _areaServed_counties + """
  ],
  "priceRange": "$$$",
  "hasCredential": {
    "@type": "EducationalOccupationalCredential",
    "credentialCategory": "California Real Estate License",
    "identifier": "DRE# 02267255"
  },
  "sameAs": [
    "https://maps.app.goo.gl/Si6haXZbeQSwmgGXA"
  ]
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
    {"@type": "ListItem", "position": 2, "name": "Where We Help", "item": "https://drozq.com/where-we-help/"}
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


MAIN_BODY = HERO + CITY_GRID + WHY + MID_TABS + FAQ + CLOSING_CTA + JSON_LD


if __name__ == "__main__":
    scaffold_page(
        target="where-we-help/index.html",
        title="Where We Help | 38 SoCal Cities | Joshua Guerrero, Real Brokerage",
        description="Joshua Guerrero serves home sellers and buyers across Southern California. 38 cities, 6 counties: Orange, Los Angeles, Riverside, San Bernardino, San Diego, Ventura. Tap your city to start the Sell funnel.",
        canonical="/where-we-help/",
        main_body_html=MAIN_BODY,
        og_title="Where We Help | 38 SoCal Cities | Joshua Guerrero",
        og_description="38 cities across 6 SoCal counties. Direct service in OC, active across LA + South Bay, vetted partners statewide. Tap your city to start the Sell funnel.",
    )
