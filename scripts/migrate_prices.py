"""Migrate /prices/ to the homepage template scaffold.

/prices/ is the site's second FRED-backed data resource and the
California housing market companion to /rates/. The first pass ships
the SKELETON: hero with funnel CTA, three data sections (8 cards
total across the three tiers we surveyed), template-required mid-page
tabs, and a closing CTA. A second pass will add plain-English
explainers, FAQ accordion + FAQPage JSON-LD, methodology section,
crosslinks, and Dataset JSON-LD.

Data product layout:
  Section 1: "California Home Prices" -- Tier 1 (LXXRSA, SDXRSA, CASTHPI)
  Section 2: "Market Signals"         -- Tier 3 (MSACSR, EXHOSLUSM495S,
                                                  FIXHAI, UNRATE)
  Section 3: "Cost of Money"          -- Tier 2 (MORTGAGE5US),
                                                  with crosslink to /rates/

Data flows through /functions/api/prices.js, which uses the same
FRED_API_KEY env var as /api/rates. Edge-cached 1h. Per-card sparkline
+ delta + per-cadence date all hydrate on DOMContentLoaded; the page
ships static skeletons so the SEO crawler sees a complete document.

This page reuses a generic ".drozq-data-card" CSS class instead of the
".drozq-rate-card" used on /rates/, because card values here span
mixed units (index, percent, months, thousands) and the future second
pass may evolve the card structure independently of /rates/.

Card-on-section contrast follows the project's contrast rule: white
cards live on warm-gray sections, never on white sections.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page


# ---------------------------------------------------------------------------
# Shared landing form pill (used in hero, mid-tabs, closing CTA)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 1. Hero
# ---------------------------------------------------------------------------

HERO = f"""
<div class="pos_relative ov_hidden">
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_50%_55% [&_img]:[@media_(max-width:_480px)]:obj-p_center">
    <img src="/media/images/crystal-cove.webp" alt="Southern California coastline" width="1280" height="640" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.62)"></div>
  </div>

  <section aria-labelledby="prices-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <p class="op_0.9 c_#fff ls_2px fs_11px md:fs_12px fw_700 mb_8px" style="text-transform:uppercase">Live Market Data &middot; Federal Reserve, refreshed automatically</p>
      <h1 id="prices-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">California home prices and the market signals around them.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Eight series pulled directly from Federal Reserve Economic Data (FRED), refreshed within an hour of every release. The LA and San Diego Case-Shiller indices, the statewide HPI, plus the supply, sales, affordability, and employment signals that move them.</p>
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


# ---------------------------------------------------------------------------
# Scoped styles -- generic data card, sized for 3 / 4 / 1 card sections
# ---------------------------------------------------------------------------

PAGE_STYLE = """
<style>
.drozq-data-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
.drozq-data-grid--3 { grid-template-columns: 1fr; }
@media (min-width: 768px) { .drozq-data-grid--3 { grid-template-columns: repeat(3, 1fr); gap: 20px; } }
.drozq-data-grid--4 { grid-template-columns: 1fr; }
@media (min-width: 640px) { .drozq-data-grid--4 { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 960px) { .drozq-data-grid--4 { grid-template-columns: repeat(4, 1fr); gap: 20px; } }
.drozq-data-grid--1 { grid-template-columns: 1fr; max-width: 360px; margin-left: auto; margin-right: auto; }

.drozq-data-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 220px;
}
.drozq-data-card__label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #3f4650;
  line-height: 1.35;
  margin: 0;
}
.drozq-data-card__sub {
  font-size: 0.78rem;
  color: #757575;
  margin: -4px 0 0;
}
.drozq-data-card__value {
  font-size: clamp(1.85rem, 3.6vw, 2.5rem);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  color: #1a1816;
  font-variant-numeric: tabular-nums;
}
.drozq-data-card__spark { display: block; width: 100%; height: 36px; }
.drozq-data-card__spark svg { width: 100%; height: 100%; display: block; overflow: visible; }
.drozq-data-card__deltas {
  display: flex; flex-direction: column; gap: 4px;
  font-size: 0.82rem; font-variant-numeric: tabular-nums;
}
.drozq-data-card__delta { font-weight: 700; letter-spacing: 0.01em; color: #757575; }
.drozq-data-card__delta--up   { color: #b81d22; }
.drozq-data-card__delta--down { color: #0a801f; }
.drozq-data-card__delta--flat { color: #757575; }
.drozq-data-card__date { font-size: 0.78rem; color: #757575; margin: 0; }

/* Per-section meta line under the grid */
.drozq-data-meta {
  text-align: center;
  color: #757575;
  font-size: 0.875rem;
  margin: 20px 0 0;
}
.drozq-data-meta strong { color: #2b2b2b; font-weight: 700; }

/* Section "tier" eyebrow chip */
.drozq-tier-chip {
  display: inline-block;
  font-size: 0.66rem; font-weight: 800; letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #d92228;
  background: #fff5f5; border: 1px solid #f7d3d4;
  border-radius: 999px; padding: 4px 10px;
  margin-bottom: 12px;
}

/* Secondary outlined button (cost-of-money crosslink to /rates/) */
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
"""


# ---------------------------------------------------------------------------
# Card factory (one shape, used across all three sections)
# ---------------------------------------------------------------------------

def data_card(key: str, label: str, sub: str = "") -> str:
    sub_html = f'<p class="drozq-data-card__sub">{sub}</p>' if sub else ""
    return f"""
      <div class="drozq-data-card" id="card-{key}" data-data-card="{key}">
        <p class="drozq-data-card__label">{label}</p>
        {sub_html}
        <span class="drozq-data-card__value" data-data-value="{key}">&hellip;</span>
        <span class="drozq-data-card__spark" data-data-spark="{key}" aria-hidden="true"></span>
        <div class="drozq-data-card__deltas">
          <span class="drozq-data-card__delta drozq-data-card__delta--flat" data-data-delta="{key}">Loading&hellip;</span>
          <span class="drozq-data-card__delta drozq-data-card__delta--flat" data-data-delta-yoy="{key}">&nbsp;</span>
        </div>
        <p class="drozq-data-card__date" data-data-date="{key}">&nbsp;</p>
      </div>"""


# ---------------------------------------------------------------------------
# 2. California Home Prices (Tier 1, warm gray bg, 3 cards)
# ---------------------------------------------------------------------------

TIER1_SECTION = f"""
<section aria-labelledby="prices-tier1-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <span class="drozq-tier-chip">California Home Prices</span>
      <h2 id="prices-tier1-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The three indices that track California housing.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Case-Shiller for the LA and San Diego metros (the two canonical city indices in the state) plus the FHFA's statewide All-Transactions HPI for the broadest read. All three are reported as index values, so the meaningful number is the year-over-year percent change.</p>
    </div>

    <div class="drozq-data-grid drozq-data-grid--3">
{data_card("hpiLA",  "LA Metro Home Price Index",         "Case-Shiller, monthly")}
{data_card("hpiSD",  "San Diego Metro Home Price Index",  "Case-Shiller, monthly")}
{data_card("hpiCA",  "California Statewide HPI",          "FHFA, quarterly")}
    </div>

    <p class="drozq-data-meta" id="prices-tier1-meta">&nbsp;</p>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 3. Market Signals (Tier 3, white bg, 4 cards)
# ---------------------------------------------------------------------------

TIER3_SECTION = f"""
<section aria-labelledby="prices-tier3-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <span class="drozq-tier-chip">Market Signals</span>
      <h2 id="prices-tier3-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The four signals that move prices.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Supply, demand, affordability, and the broader labor market. National data, monthly cadence. Movements here show up in California-specific prices over the following one to three quarters.</p>
    </div>

    <div class="drozq-data-grid drozq-data-grid--4">
{data_card("supplyMonths",  "Months of Supply",        "MSACSR, new homes, US")}
{data_card("existingSales", "Existing Home Sales",     "EXHOSLUSM495S, SAAR")}
{data_card("affordIdx",     "Affordability Index",     "NAR Composite, US")}
{data_card("unemployment",  "US Unemployment Rate",    "UNRATE, monthly")}
    </div>

    <p class="drozq-data-meta" id="prices-tier3-meta">&nbsp;</p>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 4. Cost of Money (Tier 2, warm gray bg, 1 card + crosslink to /rates/)
# ---------------------------------------------------------------------------

TIER2_SECTION = f"""
<section aria-labelledby="prices-tier2-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_840px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_640px mx_auto">
      <span class="drozq-tier-chip">Cost of Money</span>
      <h2 id="prices-tier2-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The 5/1 ARM, the underrated California play.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Most buyers default to the 30-year fixed. In a state where median prices clear $1M, the 5/1 ARM's lower headline rate is worth understanding before defaulting. Full set of rates lives on the rates page.</p>
    </div>

    <div class="drozq-data-grid drozq-data-grid--1 mb_32px md:mb_40px">
{data_card("rate5_1ARM", "5/1 ARM Rate", "MORTGAGE5US, weekly")}
    </div>

    <p class="ta_center m_0">
      <a href="/rates/" class="btn-secondary-outline">See all mortgage and benchmark rates &rarr;</a>
    </p>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 5. Mid-page tabs (template requirement)
# ---------------------------------------------------------------------------

MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Prices are the trend. Your home is the data point.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">Pick a side and I'll run a real read on your specific block, condition, and timing.</p>
    </div>

    <div role="tablist" keyboard-select-mode="focus"
         class="d_flex jc_center pos_relative bg_#fff max-w_251px w_100% h_48px m_0_auto bdr_24px bx-sh_0_1px_5px_rgba(0,0,0,.11) mt_14px bd_1px_solid_#e5e5e5">
      <button id="sellTabBtn" role="tab" aria-controls="sellTab" aria-selected="true"  data-selected="true"  type="button"
              class="ap_none bd_none bg_transparent cursor_pointer max-w_125px max-h_42px w_100% p_10px_16px bdr_999px fs_14px md:fs_16px fw_700 lh_20px ta_center m_3px_3px_0 c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:bg-c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:c_#fff">I'm selling</button>
      <button id="buyTabBtn"  role="tab" aria-controls="buyTab"  aria-selected="false" data-selected="false" type="button"
              class="ap_none bd_none bg_transparent cursor_pointer max-w_125px max-h_42px w_100% p_10px_16px bdr_999px fs_14px md:fs_16px fw_700 lh_20px ta_center m_3px_3px_0 c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:bg-c_#2b2b2b [&amp;[data-selected=&quot;true&quot;]]:c_#fff">I'm buying</button>
    </div>

    <div id="sellTab" role="tabpanel" aria-labelledby="sellTabBtn" class="d_block mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Enter your address to start the home value report.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("Your address")}</div>
    </div>

    <div id="buyTab" role="tabpanel" aria-labelledby="buyTabBtn" hidden class="d_none mt_35px md:mt_64px w_100% max-w_780px m_0_auto">
      <h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Tell me where you want to buy.</h4>
      <div style="width:100%; max-width: 540px; margin: 0 auto;">{landing_form_pill("City, neighborhood, or ZIP", value="Irvine, CA")}</div>
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 6. Closing CTA
# ---------------------------------------------------------------------------

CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Your home, your number</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Indices set the trend. Your home sets the strategy.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">A statewide index is one variable. The block, the condition, the comps, and the timing are the rest. Free CMA, delivered within 24 hours.</p>

      <div id="prices-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 7. Inline hydration script (per-unit formatters)
# ---------------------------------------------------------------------------

PRICES_SCRIPT = r"""
<script>
(function(){
  var endpoint = '/api/prices';
  var dateFmt    = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  var monthFmt   = new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' });
  var integerFmt = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
  var oneDecFmt  = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  var tier1Keys = ['hpiLA','hpiSD','hpiCA'];
  var tier3Keys = ['supplyMonths','existingSales','affordIdx','unemployment'];
  var tier2Keys = ['rate5_1ARM'];
  var allKeys = tier1Keys.concat(tier3Keys).concat(tier2Keys);

  function fmtDate(iso, cadence) {
    if (!iso) return '';
    var d = new Date(iso + 'T00:00:00Z');
    if (isNaN(d.getTime())) return '';
    if (cadence === 'monthly' || cadence === 'quarterly') return monthFmt.format(d);
    return dateFmt.format(d);
  }

  function fmtValue(s) {
    if (!s || !s.latest || s.latest.value == null) return '...';
    var v = s.latest.value;
    switch (s.unit) {
      case '%':         return v.toFixed(2) + '%';
      case 'months':    return oneDecFmt.format(v) + ' mo';
      case 'thousands': return oneDecFmt.format(v / 1000) + 'M';   // SAAR thousands -> millions, annualized
      case 'index':
      default:          return integerFmt.format(Math.round(v));
    }
  }

  function pickPrimaryDelta(s) {
    // For percent series, the absolute delta in pp is the meaningful read.
    // For everything else, the percent change is the meaningful read.
    if (!s) return { text: '', cls: 'flat' };
    if (s.unit === '%') {
      var d = s.delta;
      if (d == null || !isFinite(d)) return { text: 'No prior data', cls: 'flat' };
      var unitLbl = (s.cadence === 'monthly') ? 'pp vs. prior month' :
                    (s.cadence === 'weekly')  ? 'pp vs. prior week'  :
                    (s.cadence === 'daily')   ? 'pp vs. prior day'   :
                    'pp vs. prior';
      if (d === 0) return { text: 'Flat ' + unitLbl.replace('pp ', ''), cls: 'flat' };
      var sign = d > 0 ? '+' : '';
      return { text: sign + d.toFixed(2) + ' ' + unitLbl, cls: d > 0 ? 'up' : 'down' };
    }
    var p = s.deltaPct;
    if (p == null || !isFinite(p)) return { text: 'No prior data', cls: 'flat' };
    var lbl = (s.cadence === 'quarterly') ? 'vs. prior quarter' :
              (s.cadence === 'monthly')   ? 'vs. prior month'   :
              (s.cadence === 'weekly')    ? 'vs. prior week'    :
              'vs. prior';
    if (p === 0) return { text: 'Flat ' + lbl, cls: 'flat' };
    var sign2 = p > 0 ? '+' : '';
    // For supply / unemployment, a rise is bad for buyers/economy: keep up=red, down=green.
    return { text: sign2 + p.toFixed(1) + '% ' + lbl, cls: p > 0 ? 'up' : 'down' };
  }

  function pickYoYDelta(s) {
    if (!s) return { text: '', cls: 'flat' };
    if (s.unit === '%') {
      var d = s.deltaYoY;
      if (d == null || !isFinite(d)) return { text: '', cls: 'flat' };
      if (d === 0) return { text: 'Flat YoY', cls: 'flat' };
      var sign = d > 0 ? '+' : '';
      return { text: sign + d.toFixed(2) + ' pp YoY', cls: d > 0 ? 'up' : 'down' };
    }
    var p = s.deltaYoYPct;
    if (p == null || !isFinite(p)) return { text: '', cls: 'flat' };
    if (p === 0) return { text: 'Flat YoY', cls: 'flat' };
    var sign2 = p > 0 ? '+' : '';
    return { text: sign2 + p.toFixed(1) + '% YoY', cls: p > 0 ? 'up' : 'down' };
  }

  function renderSparkline(targetEl, history) {
    if (!targetEl) return;
    if (!history || history.length < 2) { targetEl.innerHTML = ''; return; }
    var values = history.map(function(o){ return o.value; }).filter(function(v){ return v != null; });
    if (values.length < 2) { targetEl.innerHTML = ''; return; }
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    var range = (max - min) || 1;
    var n = values.length;
    var pts = values.map(function(v, i){
      var x = (i / (n - 1)) * 100;
      var y = 30 - ((v - min) / range) * 30;
      return x.toFixed(2) + ',' + y.toFixed(2);
    }).join(' ');
    targetEl.innerHTML =
      '<svg viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true">'
      + '<polyline points="' + pts + '" stroke="#d92228" stroke-width="1.6" fill="none" stroke-linejoin="round" stroke-linecap="round" />'
      + '</svg>';
  }

  function renderCard(key, s) {
    var valEl   = document.querySelector('[data-data-value="' + key + '"]');
    var sparkEl = document.querySelector('[data-data-spark="' + key + '"]');
    var deltaEl = document.querySelector('[data-data-delta="' + key + '"]');
    var yoyEl   = document.querySelector('[data-data-delta-yoy="' + key + '"]');
    var dateEl  = document.querySelector('[data-data-date="' + key + '"]');

    if (!s || !s.latest || s.latest.value == null) {
      if (valEl)   valEl.textContent  = '...';
      if (deltaEl) { deltaEl.textContent = 'Data unavailable'; deltaEl.className = 'drozq-data-card__delta drozq-data-card__delta--flat'; }
      if (yoyEl)   { yoyEl.textContent = ''; yoyEl.className = 'drozq-data-card__delta drozq-data-card__delta--flat'; }
      if (dateEl)  dateEl.innerHTML = '&nbsp;';
      if (sparkEl) sparkEl.innerHTML = '';
      return;
    }

    if (valEl)  valEl.textContent = fmtValue(s);
    if (sparkEl) renderSparkline(sparkEl, s.history || []);

    var d = pickPrimaryDelta(s);
    if (deltaEl) { deltaEl.textContent = d.text; deltaEl.className = 'drozq-data-card__delta drozq-data-card__delta--' + d.cls; }
    var y = pickYoYDelta(s);
    if (yoyEl)   { yoyEl.textContent   = y.text; yoyEl.className   = 'drozq-data-card__delta drozq-data-card__delta--' + y.cls; }

    if (dateEl) {
      dateEl.textContent = s.latest.date ? 'As of ' + fmtDate(s.latest.date, s.cadence) : '';
    }
  }

  function setMeta(elId, payload) {
    var el = document.getElementById(elId);
    if (!el) return;
    if (payload && payload.lastUpdated) {
      el.innerHTML = 'Latest reading across this section: <strong>' + fmtDate(payload.lastUpdated, 'monthly') + '</strong>';
    } else if (payload && payload.error) {
      el.innerHTML = '<strong>Data temporarily unavailable.</strong>';
    } else {
      el.innerHTML = '&nbsp;';
    }
  }

  function render(payload) {
    var series = (payload && payload.series) || {};
    allKeys.forEach(function(k){ renderCard(k, series[k]); });
    setMeta('prices-tier1-meta', payload);
    setMeta('prices-tier3-meta', payload);
  }

  function fail(err) {
    allKeys.forEach(function(k){ renderCard(k, null); });
    render({ error: (err && err.message) || 'fetch_failed' });
  }

  function go() {
    fetch(endpoint, { headers: { 'accept': 'application/json' } })
      .then(function(r){
        if (!r.ok && r.status !== 200) {
          return r.json().then(function(j){ throw new Error(j.error || ('http_' + r.status)); });
        }
        return r.json();
      })
      .then(render)
      .catch(fail);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', go);
  } else { go(); }
})();
</script>
"""


# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------

MAIN_BODY = (
    HERO
    + PAGE_STYLE
    + TIER1_SECTION
    + TIER3_SECTION
    + TIER2_SECTION
    + MID_TABS
    + CLOSING_CTA
    + PRICES_SCRIPT
)


if __name__ == "__main__":
    scaffold_page(
        target="prices/index.html",
        title="California Home Prices and Market Signals -- Live from FRED | Joshua Guerrero, Real Brokerage",
        description="Live LA and San Diego Case-Shiller home price indices, the California statewide HPI, and the four national market signals that move them, pulled directly from the Federal Reserve and refreshed automatically.",
        canonical="/prices/",
        main_body_html=MAIN_BODY,
        og_title="California Home Prices and Market Signals -- Live from FRED",
        og_description="LA + San Diego Case-Shiller, California statewide HPI, plus months of supply, existing sales, affordability, and unemployment. Refreshed automatically from FRED.",
    )
