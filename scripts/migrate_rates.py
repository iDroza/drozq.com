"""Migrate /rates/ to the homepage template scaffold.

/rates/ is the site's auto-refreshing data resource. The page reads four
mortgage-finance benchmarks live from FRED (Federal Reserve Economic
Data) and renders them as a citation-worthy reference combined with a
maximally-converting lead path.

Structure (top to bottom):
  1. Hero with 3-tab funnel CTA (Sell / Buy / Sell&Buy).
  2. Live rate cards w/ sparkline + WoW delta + YoY delta.
  3. Affordability table at today's 30-year rate (5 common loan sizes).
  4. Interactive mortgage payment calculator. Output ends in a Buy-mode
     landing form pill so the calculator IS a lead capture path.
  5. Three plain-English explainers (30y vs 15y, the 10y Treasury link,
     the Fed funds chain) -- long-tail SEO + citable paragraphs.
  6. Mid-page sell/buy tabs (template requirement).
  7. FAQ accordion -- six questions, paired with FAQPage JSON-LD for
     SERP rich results.
  8. Methodology + crosslinks to /market-insights/, /process/,
     /field-notes/. Outbound link to FRED for source credibility.
  9. Closing CTA pill + phone fallback.
 10. JSON-LD: WebPage + 4 Dataset + FAQPage + BreadcrumbList + Person.

Data is fetched client-side from /api/rates which now returns:
  series[key]: {
    seriesId, label, unit, cadence,
    latest:   {value, date},
    previous: {value, date},  // last observation prior to latest
    yearAgo:  {value, date},  // oldest observation in ~1yr window
    history:  [{date, value}, ...]   // ascending order, ~1yr
    delta, deltaYoY
  }
  lastUpdated, fetchedAt, source, sourceUrl

The page ships static skeletons; an inline IIFE hydrates the cards,
sparklines, calculator default rate, and affordability table on
DOMContentLoaded. If /api/rates returns an error or never responds,
each section degrades gracefully.

Card-on-section contrast: rate cards (white) live on a warm-gray
section (#f2f0ef). The white-on-white blunder is explicitly avoided
per the project's contrast rule.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page


# ---------------------------------------------------------------------------
# Shared funnel landing pill (used in hero, mid-tabs, calculator CTA, closing)
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
            See Plan
          </button>
        </div>
      </div>
      <input type="hidden" name="gclid" value="">
    </form>"""


# ---------------------------------------------------------------------------
# 1. Hero
# ---------------------------------------------------------------------------

HERO = f"""
<div class="pos_relative ov_hidden d_flex flex-d_column jc_center" style="min-height:100vh;min-height:100svh">
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_100%_60% [&_img]:[@media_(max-width:_480px)]:obj-p_right">
    <img src="/media/images/coastal-modern.webp" alt="Modern hillside home overlooking the Southern California coast at sunset" width="1672" height="941" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0)"></div>
  </div>

  <section aria-labelledby="rates-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="rates-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">Today's mortgage and benchmark rates.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">The four numbers that frame every offer, refinance, and pricing conversation in Southern California.</p>
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
# Scoped styles for rate cards, calculator, table, FAQ helper
# ---------------------------------------------------------------------------

PAGE_STYLE = """
<style>
.drozq-rates-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 640px) { .drozq-rates-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 960px) { .drozq-rates-grid { grid-template-columns: repeat(4, 1fr); gap: 20px; } }
.drozq-rate-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 220px;
}
.drozq-rate-card__label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #3f4650;
  line-height: 1.35;
  margin: 0;
}
.drozq-rate-card__value {
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  color: #1a1816;
  font-variant-numeric: tabular-nums;
}
.drozq-rate-card__spark { display: block; width: 100%; height: 36px; }
.drozq-rate-card__spark svg { width: 100%; height: 100%; display: block; overflow: visible; }
.drozq-rate-card__deltas {
  display: flex; flex-direction: column; gap: 4px;
  font-size: 0.82rem;
  font-variant-numeric: tabular-nums;
}
.drozq-rate-card__delta { font-weight: 700; letter-spacing: 0.01em; color: #757575; }
.drozq-rate-card__delta--up   { color: #b81d22; }
.drozq-rate-card__delta--down { color: #0a801f; }
.drozq-rate-card__delta--flat { color: #757575; }
.drozq-rate-card__date { font-size: 0.78rem; color: #757575; margin: 0; }
.drozq-rates-meta {
  text-align: center;
  color: #757575;
  font-size: 0.875rem;
  margin: 24px 0 0;
}
.drozq-rates-meta strong { color: #2b2b2b; font-weight: 700; }

/* Affordability table */
.drozq-aff-wrap {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 8px;
  overflow-x: auto;
}
.drozq-aff-table {
  width: 100%; border-collapse: collapse; min-width: 360px;
  font-variant-numeric: tabular-nums;
}
.drozq-aff-table th, .drozq-aff-table td {
  padding: 14px 16px; text-align: left; font-size: 0.95rem;
}
.drozq-aff-table thead th {
  text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.72rem;
  color: #3f4650; border-bottom: 1px solid #e5e5e5;
}
.drozq-aff-table tbody tr + tr td { border-top: 1px solid #f0f0f0; }
.drozq-aff-table tbody tr:hover td { background: #faf7f3; }
.drozq-aff-table td.num { text-align: right; font-weight: 700; color: #1a1816; }
.drozq-aff-table caption {
  caption-side: top; text-align: left;
  padding: 12px 16px 4px; font-size: 0.82rem; color: #3f4650;
}

/* Affordability table -- stacked cards on mobile so the four-column figures never
   force a horizontal drag. Desktop (>=768px) keeps the scrolling table above, unchanged. */
@media (max-width: 767.98px) {
  .drozq-aff-wrap {
    background: transparent; border: 0; border-radius: 0; padding: 0; overflow: visible;
  }
  .drozq-aff-table { min-width: 0; }
  .drozq-aff-table thead { display: none; }
  .drozq-aff-table caption { padding: 0 2px 14px; }
  .drozq-aff-table tbody tr {
    display: block; background: #ffffff; border: 1px solid #e5e5e5; border-radius: 14px;
    padding: 4px 16px 8px; margin-bottom: 12px;
  }
  .drozq-aff-table tbody tr:last-child { margin-bottom: 0; }
  .drozq-aff-table tbody tr:hover td { background: transparent; }
  .drozq-aff-table td {
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 16px; padding: 9px 0; font-size: 0.95rem;
  }
  .drozq-aff-table td:first-child {
    display: block; border-top: 0; border-bottom: 1px solid #ececec;
    padding: 6px 0 10px; margin-bottom: 2px;
    font-weight: 800; font-size: 1.02rem; color: #1a1816;
  }
  .drozq-aff-table td.num { border-top: 1px solid #f4f2f0; text-align: right; }
  .drozq-aff-table td[data-aff-mo] { border-top: 0; }
  .drozq-aff-table td[data-aff-mo]::before  { content: "Monthly P&I"; }
  .drozq-aff-table td[data-aff-int]::before { content: "Total interest (30y)"; }
  .drozq-aff-table td[data-aff-tot]::before { content: "Total paid"; }
  .drozq-aff-table td.num::before {
    font-weight: 600; font-size: 0.9rem; letter-spacing: 0; text-transform: none; color: #3f4650;
  }
}

/* Calculator */
.drozq-calc {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px;
}
@media (min-width: 768px) { .drozq-calc { padding: 32px; } }
.drozq-calc__grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 640px) { .drozq-calc__grid { grid-template-columns: 1fr 1fr; gap: 20px; } }
.drozq-calc__field { display: flex; flex-direction: column; gap: 6px; }
.drozq-calc__field label {
  font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: #3f4650;
}
.drozq-calc__field input {
  font: inherit; font-size: 16px; padding: 12px 14px;
  border: 1px solid #d3cfca; border-radius: 10px; background: #fff;
  color: #1a1816;
}
.drozq-calc__field input:focus { outline: none; border-color: #d92228; }
.drozq-calc__radios { display: flex; gap: 8px; }
.drozq-calc__radio {
  flex: 1; display: inline-flex; align-items: center; justify-content: center;
  padding: 12px 14px; border-radius: 10px; border: 1px solid #d3cfca;
  background: #fff; font-weight: 700; font-size: 0.95rem; cursor: pointer;
  color: #1a1816;
}
.drozq-calc__radio.is-active { border-color: #d92228; color: #d92228; background: #fff5f5; }
.drozq-calc__results {
  margin-top: 24px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 640px) { .drozq-calc__results { grid-template-columns: repeat(3, 1fr); } }
.drozq-calc__stat { background: #f7f4ef; border-radius: 12px; padding: 16px; }
.drozq-calc__stat .lbl {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: #3f4650; margin: 0 0 6px;
}
.drozq-calc__stat .val {
  font-size: 1.5rem; font-weight: 800; line-height: 1; color: #1a1816;
  font-variant-numeric: tabular-nums;
}
.drozq-calc__note {
  margin-top: 18px;
  font-size: 0.82rem; color: #757575;
}

/* Secondary outlined button */
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

/* Explainer cards */
.drozq-explain-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}
@media (min-width: 768px) { .drozq-explain-grid { grid-template-columns: repeat(3, 1fr); gap: 24px; } }
.drozq-explain {
  background: #f7f4ef;
  border: 1px solid #ece8e1;
  border-radius: 16px;
  padding: 24px 22px;
}
.drozq-explain h3 {
  font-size: 1.1rem; font-weight: 800; color: #1a1816;
  margin: 0 0 8px; line-height: 1.4;
}
.drozq-explain__num {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em;
  text-transform: uppercase; color: #d92228; margin: 0 0 6px;
}
.drozq-explain p { color: #3f4650; font-size: 0.95rem; line-height: 1.6; margin: 0; }

/* FAQ (mirrors homepage accordion) */
.drozq-faq-list { max-width: 720px; margin: 0 auto; }
.drozq-faq-item { border-bottom: 1px solid #e5e5e5; }
.drozq-faq-item button {
  width: 100%; background: transparent; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: space-between;
  text-align: left; padding: 16px 40px 16px 0; color: #1a1816;
  font: inherit; font-size: 16px; font-weight: 400; line-height: 1.5;
  position: relative;
}
.drozq-faq-item button:hover { color: #d92228; }
.drozq-faq-item button svg {
  width: 20px; height: 20px; flex-shrink: 0; color: #3f4650;
  transition: transform .2s ease;
}
.drozq-faq-item button[aria-expanded="true"] svg { transform: rotate(45deg); color: #d92228; }
.drozq-faq-region {
  overflow: hidden; max-height: 0; transition: max-height .3s ease;
}
.drozq-faq-region p {
  margin: 0 0 16px; color: #3f4650; font-size: 15px; line-height: 1.6;
}
</style>
"""


# ---------------------------------------------------------------------------
# 2. Rate cards with sparkline + deltas
# ---------------------------------------------------------------------------

def rate_card(key: str, label: str, cadence_hint: str, anchor: str) -> str:
    return f"""
      <div class="drozq-rate-card" id="{anchor}" data-rate-card="{key}">
        <p class="drozq-rate-card__label">{label}</p>
        <span class="drozq-rate-card__value" data-rate-value="{key}">&hellip;</span>
        <span class="drozq-rate-card__spark" data-rate-spark="{key}" aria-hidden="true"></span>
        <div class="drozq-rate-card__deltas">
          <span class="drozq-rate-card__delta drozq-rate-card__delta--flat" data-rate-delta-wow="{key}">Loading {cadence_hint} data&hellip;</span>
          <span class="drozq-rate-card__delta drozq-rate-card__delta--flat" data-rate-delta-yoy="{key}">&nbsp;</span>
        </div>
        <p class="drozq-rate-card__date" data-rate-date="{key}">&nbsp;</p>
      </div>"""


RATES_SECTION = f"""
<section aria-labelledby="rates-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Rates</p>
      <h2 id="rates-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Live mortgage and benchmark rates, refreshed automatically.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Each card shows the latest weekly (mortgage), daily (Treasury), or monthly (Fed funds) read from FRED, with the change since the prior observation and one year ago. The sparkline traces the last ~52 weeks.</p>
    </div>

    <div class="drozq-rates-grid" id="drozq-rates-grid">
{rate_card("rate30y",     "30-year fixed mortgage",  "weekly",  "rate30y")}
{rate_card("rate15y",     "15-year fixed mortgage",  "weekly",  "rate15y")}
{rate_card("treasury10y", "10-year Treasury yield",  "daily",   "treasury10y")}
{rate_card("fedFunds",    "Federal funds rate",      "monthly", "fedFunds")}
    </div>

    <p class="drozq-rates-meta" id="drozq-rates-meta">
      <strong>Loading&hellip;</strong>
    </p>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 3. Affordability table at today's 30-year rate
# ---------------------------------------------------------------------------

AFFORDABILITY_SECTION = """
<section aria-labelledby="rates-affordability-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">At today's rate</p>
      <h2 id="rates-affordability-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">What a Southern California mortgage actually costs today.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Principal-and-interest only, 30-year fixed, today's PMMS rate. Property taxes, insurance, and HOA are on top. Scan to your price band, then run the calculator for your actual numbers.</p>
    </div>

    <div class="drozq-aff-wrap">
      <table class="drozq-aff-table" aria-describedby="rates-aff-cap">
        <caption id="rates-aff-cap" data-aff-caption>Computed at <span data-aff-rate>...</span> &middot; 30-year fixed</caption>
        <thead>
          <tr>
            <th scope="col">Loan amount</th>
            <th scope="col" style="text-align:right">Monthly P&amp;I</th>
            <th scope="col" style="text-align:right">Total interest (30y)</th>
            <th scope="col" style="text-align:right">Total paid</th>
          </tr>
        </thead>
        <tbody id="drozq-aff-tbody">
          <tr><td>$500,000</td><td class="num" data-aff-mo="500000">...</td><td class="num" data-aff-int="500000">...</td><td class="num" data-aff-tot="500000">...</td></tr>
          <tr><td>$750,000</td><td class="num" data-aff-mo="750000">...</td><td class="num" data-aff-int="750000">...</td><td class="num" data-aff-tot="750000">...</td></tr>
          <tr><td>$1,000,000</td><td class="num" data-aff-mo="1000000">...</td><td class="num" data-aff-int="1000000">...</td><td class="num" data-aff-tot="1000000">...</td></tr>
          <tr><td>$1,500,000</td><td class="num" data-aff-mo="1500000">...</td><td class="num" data-aff-int="1500000">...</td><td class="num" data-aff-tot="1500000">...</td></tr>
          <tr><td>$2,000,000</td><td class="num" data-aff-mo="2000000">...</td><td class="num" data-aff-int="2000000">...</td><td class="num" data-aff-tot="2000000">...</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 4. Interactive payment calculator
# ---------------------------------------------------------------------------

CALCULATOR_SECTION = f"""
<section aria-labelledby="rates-calc-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_840px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Run your numbers</p>
      <h2 id="rates-calc-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Mortgage payment calculator.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Pre-filled with today's 30-year fixed rate from FRED. Adjust to your scenario; the math updates live.</p>
    </div>

    <form class="drozq-calc" id="drozq-calc" novalidate>
      <div class="drozq-calc__grid">
        <div class="drozq-calc__field">
          <label for="calc-price">Home price</label>
          <input id="calc-price" type="number" inputmode="numeric" min="50000" step="10000" value="1000000" aria-describedby="calc-price-hint">
          <span id="calc-price-hint" class="drozq-calc__note" style="margin-top:0">Total purchase price, in dollars.</span>
        </div>
        <div class="drozq-calc__field">
          <label for="calc-down">Down payment (%)</label>
          <input id="calc-down" type="number" inputmode="decimal" min="0" max="100" step="0.5" value="20" aria-describedby="calc-down-hint">
          <span id="calc-down-hint" class="drozq-calc__note" style="margin-top:0">Percent of purchase price paid up front.</span>
        </div>
        <div class="drozq-calc__field">
          <label>Loan term</label>
          <div class="drozq-calc__radios" role="radiogroup" aria-label="Loan term">
            <button type="button" class="drozq-calc__radio is-active" data-calc-term="30" aria-pressed="true">30-year</button>
            <button type="button" class="drozq-calc__radio"           data-calc-term="15" aria-pressed="false">15-year</button>
          </div>
        </div>
        <div class="drozq-calc__field">
          <label for="calc-rate">Interest rate (%)</label>
          <input id="calc-rate" type="number" inputmode="decimal" min="0" max="20" step="0.01" value="6.50" aria-describedby="calc-rate-hint">
          <span id="calc-rate-hint" class="drozq-calc__note" style="margin-top:0">Pre-filled from today's FRED reading for the selected term.</span>
        </div>
      </div>

      <div class="drozq-calc__results" aria-live="polite">
        <div class="drozq-calc__stat"><p class="lbl">Monthly P&amp;I</p><p class="val" id="calc-out-monthly">$0</p></div>
        <div class="drozq-calc__stat"><p class="lbl">Total interest</p><p class="val" id="calc-out-interest">$0</p></div>
        <div class="drozq-calc__stat"><p class="lbl">Total paid</p><p class="val" id="calc-out-total">$0</p></div>
      </div>

      <p class="drozq-calc__note">Principal and interest only. Property tax, insurance, HOA, and PMI not included. For a full picture of your specific scenario, the conversation below is the next step.</p>
    </form>

    <div class="ta_center mt_32px md:mt_40px">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">From math to strategy</p>
      <h3 class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_40px fs_22px md:fs_28px ls_0.3px ta_center mb_12px">These numbers are math. Your specific Orange County purchase is a strategy.</h3>
      <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px max-w_640px m_0_auto mb_24px">A monthly payment is one variable. Comps, condition, contingencies, and timing are the rest. Tell me where you're looking and I'll run the read.</p>

      <div role="tabpanel" aria-labelledby="tab-buy" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("City, neighborhood, or ZIP", value="Irvine, CA")}</div>
      </div>
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 5. Plain-English explainers
# ---------------------------------------------------------------------------

EXPLAINERS_SECTION = """
<section aria-labelledby="rates-explain-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">What these numbers mean</p>
      <h2 id="rates-explain-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The plain-English read.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Three short explainers on the relationships that drive every California offer's math.</p>
    </div>

    <div class="drozq-explain-grid">
      <div class="drozq-explain">
        <p class="drozq-explain__num">Explainer 01</p>
        <h3>30-year vs. 15-year: the trade you're actually making.</h3>
        <p>A 15-year fixed typically runs 60 to 90 basis points below the 30-year, but the monthly payment is higher because the principal pays off in half the time. The 30-year wins on cash flow; the 15-year wins on total interest. The right answer depends on how long you plan to hold the home and what else the money could be doing.</p>
      </div>
      <div class="drozq-explain">
        <p class="drozq-explain__num">Explainer 02</p>
        <h3>The 10-year Treasury is the leading indicator.</h3>
        <p>30-year mortgage rates trade at a spread (historically 150 to 200 basis points) above the 10-year Treasury yield. When the 10-year moves, mortgages follow within roughly two weeks. If you're watching for rate-lock timing, the 10-year is the line on the chart that matters most, not the Fed funds rate.</p>
      </div>
      <div class="drozq-explain">
        <p class="drozq-explain__num">Explainer 03</p>
        <h3>The Fed funds rate sets the floor, not the rate.</h3>
        <p>The Federal Open Market Committee sets the Federal funds rate, which is the overnight rate banks charge each other. It influences short-term yields, which influence long-term yields, which influence mortgage rates. The link is real but indirect: a 25-basis-point Fed cut does not produce a 25-basis-point mortgage drop.</p>
      </div>
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 6. Mid-page tabs (template requirement)
# ---------------------------------------------------------------------------

MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">Rates frame the math. Strategy decides the outcome.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">Pick a side and I'll run a real read on your specific home, block, and timing.</p>
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
# 7. FAQ
# ---------------------------------------------------------------------------

FAQ_QUESTIONS = [
    ("How often does this page update?",
     "The page reads four series live from Federal Reserve Economic Data (FRED). The 30- and 15-year fixed rates come from Freddie Mac's Primary Mortgage Market Survey, published every Thursday at 12 pm ET. The 10-year Treasury yield refreshes every business day. The Federal funds rate updates monthly. New releases surface here within roughly an hour of publication."),
    ("Why is the 10-year Treasury on a mortgage rate page?",
     "Mortgage rates do not track the Fed funds rate directly. They track the 10-year Treasury yield with a typical spread of 150 to 200 basis points. If you want a leading indicator for where 30-year mortgages are about to move, watch the 10-year, not the next FOMC meeting headline."),
    ("What's the difference between an interest rate and an APR?",
     "The interest rate is the cost of borrowing the principal. The APR (annual percentage rate) is the interest rate plus the loan's fees (origination, points, mortgage insurance, certain closing costs) expressed as an annualized percentage. APR is higher than the rate. For an apples-to-apples lender comparison, ask for both."),
    ("Why are 15-year mortgage rates lower than 30-year rates?",
     "Two reasons. First, the lender's risk is shorter (the loan is paid off in half the time). Second, the yield curve. Longer-duration loans price off longer-duration Treasuries, which usually yield more than shorter-duration ones. The trade-off is the monthly payment: a 15-year payment is meaningfully higher than a 30-year payment on the same loan amount, even at a lower rate."),
    ("Do these rates apply to me in Southern California?",
     "The mortgage rates on this page are the national average for a conventional, conforming 30- or 15-year fixed-rate loan. For most California buyers in Orange County, Los Angeles County, and the Inland Empire, this is the right benchmark. If you're shopping a jumbo loan (above the 2026 conforming limit of $806,500 in most SoCal counties, higher in OC), expect jumbo rates to vary from this benchmark by 25 to 75 basis points up or down depending on the lender and the credit profile."),
    ("How do I actually get a rate quoted on my home?",
     "Two paths. For a strategic read on your specific home (the right list price for a seller, the right offer math for a buyer), use the form above and I'll come back inside 24 hours with the numbers pulled. For a live rate quote on a specific mortgage application, I'll connect you with a vetted local lender from my bench. No app, no credit pull, just a real conversation."),
]


def faq_item(idx: int, q: str, a: str) -> str:
    qid = f"rates-faq-{idx}-header"
    aid = f"rates-faq-{idx}-content"
    return f"""
      <div class="drozq-faq-item">
        <button aria-controls="{aid}" aria-expanded="false" id="{qid}" type="button">
          <span>{q}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>
        <div role="region" aria-labelledby="{qid}" id="{aid}" class="drozq-faq-region" style="max-height: 0;">
          <p>{a}</p>
        </div>
      </div>"""


FAQ_SECTION = f"""
<section aria-labelledby="rates-faq-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">FAQ</p>
      <h2 id="rates-faq-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Questions about the numbers on this page.</h2>
    </div>

    <div class="drozq-faq-list">
{"".join(faq_item(i+1, q, a) for i, (q, a) in enumerate(FAQ_QUESTIONS))}
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 8. Methodology + crosslinks
# ---------------------------------------------------------------------------

METHOD_CROSSLINKS = """
<section aria-labelledby="rates-method-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_840px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Methodology</p>
    <h2 id="rates-method-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">Where this data comes from.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">All four series are pulled directly from <a href="https://fred.stlouisfed.org/" rel="noopener" class="c_#d92228 fw_700">Federal Reserve Economic Data (FRED)</a>, maintained by the Federal Reserve Bank of St. Louis. The 30- and 15-year fixed mortgage rates are Freddie Mac's Primary Mortgage Market Survey (series MORTGAGE30US and MORTGAGE15US), the 10-year Treasury yield is the constant-maturity series (DGS10), and the Federal funds rate is the monthly average (FEDFUNDS).</p>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">Each card carries its own observation date so you always know how fresh the read is. New releases surface on this page within roughly an hour of publication.</p>
    <p class="c_#3f4650 fs_15px md:fs_16px lh_24px md:lh_28px m_0"><em>Authored by Joshua Guerrero, Real Estate Agent, Real Brokerage. California DRE #02267255. Reach out at <a href="tel:9494385948" class="c_#d92228 fw_700">(949) 438-5948</a> or <a href="/contact/" class="c_#d92228 fw_700">/contact/</a>.</em></p>
  </div>

  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center mt_40px md:mt_48px">
    <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Related on Drozq</p>
    <h3 class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_40px fs_22px md:fs_28px ls_0.3px ta_center mb_24px">Pair the rate with the local market read.</h3>
    <div class="d_flex flex-wrap_wrap jc_center gap_12px md:gap_16px">
      <a href="/market-insights/" class="btn-secondary-outline">Southern California market data &rarr;</a>
      <a href="/process/" class="btn-secondary-outline">How I work &rarr;</a>
      <a href="/field-notes/" class="btn-secondary-outline">Field Notes &rarr;</a>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 9. Closing CTA
# ---------------------------------------------------------------------------

CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Your home, your number</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Rates are a number. Your home is a strategy.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Whether you're running refinance math or sequencing a sell-then-buy, the conversation starts with your specific home. Free CMA, delivered within 24 hours.</p>

      <div id="rates-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 10. JSON-LD (WebPage + 4 Dataset + FAQPage + BreadcrumbList + Person)
# ---------------------------------------------------------------------------

def faq_jsonld_entity(q: str, a: str) -> dict:
    return {
        "@type": "Question",
        "name": q,
        "acceptedAnswer": {"@type": "Answer", "text": a}
    }


import json as _json
import datetime as _dt

_TODAY = _dt.date.today().isoformat()

PERSON_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Person",
    "@id": "https://drozq.com/#person-joshua",
    "name": "Joshua Guerrero",
    "url": "https://drozq.com/",
    "jobTitle": "Real Estate Agent",
    "worksFor": {"@type": "Organization", "name": "Real Brokerage"},
    "telephone": "+1-949-438-5948",
    "areaServed": [
        {"@type": "Place", "name": "Orange County, California"},
        {"@type": "Place", "name": "Los Angeles County, California"},
        {"@type": "Place", "name": "Irvine, California"}
    ],
    "identifier": {
        "@type": "PropertyValue",
        "propertyID": "California DRE",
        "value": "02267255"
    }
}

WEBPAGE_JSONLD = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "Today's Mortgage Rates -- Live from FRED",
    "description": "Live 30-year and 15-year mortgage rates, 10-year Treasury yield, and Fed funds rate, refreshed automatically from the Federal Reserve.",
    "url": "https://drozq.com/rates/",
    "dateModified": _TODAY,
    "author": {"@id": "https://drozq.com/#person-joshua"},
    "isPartOf": {"@type": "WebSite", "name": "Drozq", "url": "https://drozq.com/"},
    "mainContentOfPage": {
        "@type": "WebPageElement",
        "name": "Live Federal Reserve Rate Snapshot"
    }
}


def dataset_jsonld(series_id: str, name: str, description: str, anchor: str, cadence: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": name,
        "description": description,
        "url": f"https://drozq.com/rates/#{anchor}",
        "creator": {
            "@type": "Organization",
            "name": "Federal Reserve Bank of St. Louis",
            "url": "https://fred.stlouisfed.org/"
        },
        "isBasedOn": f"https://fred.stlouisfed.org/series/{series_id}",
        "license": "https://research.stlouisfed.org/docs/api/terms_of_use.html",
        "temporalCoverage": "rolling-1-year",
        "measurementTechnique": cadence,
        "variableMeasured": {"@type": "PropertyValue", "name": name, "unitText": "percent"},
        "datePublished": _TODAY,
        "dateModified": _TODAY
    }


FAQ_JSONLD = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [faq_jsonld_entity(q, a) for q, a in FAQ_QUESTIONS]
}

BREADCRUMB_JSONLD = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
        {"@type": "ListItem", "position": 2, "name": "Today's Mortgage Rates", "item": "https://drozq.com/rates/"}
    ]
}

DATASETS_JSONLD = [
    dataset_jsonld(
        "MORTGAGE30US",
        "30-Year Fixed Rate Mortgage Average (United States)",
        "Weekly national average for 30-year fixed conventional conforming mortgage rates from Freddie Mac's Primary Mortgage Market Survey (PMMS), published every Thursday.",
        "rate30y", "weekly"
    ),
    dataset_jsonld(
        "MORTGAGE15US",
        "15-Year Fixed Rate Mortgage Average (United States)",
        "Weekly national average for 15-year fixed conventional conforming mortgage rates from Freddie Mac's Primary Mortgage Market Survey (PMMS), published every Thursday.",
        "rate15y", "weekly"
    ),
    dataset_jsonld(
        "DGS10",
        "10-Year Treasury Constant Maturity Rate",
        "Daily yield on the 10-year U.S. Treasury security at constant maturity, published every business day by the U.S. Treasury via the Federal Reserve.",
        "treasury10y", "daily"
    ),
    dataset_jsonld(
        "FEDFUNDS",
        "Effective Federal Funds Rate",
        "Monthly average of the daily effective federal funds rate, published by the Federal Reserve Board.",
        "fedFunds", "monthly"
    )
]


JSON_LD_BLOCKS = "\n".join(
    f'<script type="application/ld+json">{_json.dumps(obj, indent=2)}</script>'
    for obj in [PERSON_JSONLD, WEBPAGE_JSONLD] + DATASETS_JSONLD + [FAQ_JSONLD, BREADCRUMB_JSONLD]
)


# ---------------------------------------------------------------------------
# 11. Inline hydration script
# ---------------------------------------------------------------------------

RATES_SCRIPT = r"""
<script>
(function(){
  var endpoint = '/api/rates';
  var dateFmt  = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  var rateKeys = ['rate30y','rate15y','treasury10y','fedFunds'];

  // Mortgage payment math.
  function payment(P, annualRate, years) {
    var r = annualRate / 100 / 12;
    var n = years * 12;
    if (n <= 0) return 0;
    if (r === 0) return P / n;
    var f = Math.pow(1 + r, n);
    return P * (r * f) / (f - 1);
  }

  var dollars = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

  function fmtRate(v) {
    if (v == null || !isFinite(v)) return '...';
    return v.toFixed(2) + '%';
  }
  function fmtDeltaWoW(d, cadence) {
    if (d == null || !isFinite(d)) return { text: 'No change data', cls: 'flat' };
    var label = cadence === 'daily' ? 'vs. prior day' : (cadence === 'monthly' ? 'vs. prior month' : 'vs. prior week');
    if (d === 0) return { text: 'Flat ' + label, cls: 'flat' };
    var sign = d > 0 ? '+' : '';
    return {
      text: sign + d.toFixed(2) + ' ' + label,
      cls: d > 0 ? 'up' : 'down'
    };
  }
  function fmtDeltaYoY(d) {
    if (d == null || !isFinite(d)) return { text: '', cls: 'flat' };
    if (d === 0) return { text: 'Flat vs. one year ago', cls: 'flat' };
    var sign = d > 0 ? '+' : '';
    return {
      text: sign + d.toFixed(2) + ' vs. one year ago',
      cls: d > 0 ? 'up' : 'down'
    };
  }
  function fmtDate(iso) {
    if (!iso) return '';
    var d = new Date(iso + 'T00:00:00Z');
    if (isNaN(d.getTime())) return '';
    return dateFmt.format(d);
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
    var valEl   = document.querySelector('[data-rate-value="' + key + '"]');
    var sparkEl = document.querySelector('[data-rate-spark="' + key + '"]');
    var wowEl   = document.querySelector('[data-rate-delta-wow="' + key + '"]');
    var yoyEl   = document.querySelector('[data-rate-delta-yoy="' + key + '"]');
    var dateEl  = document.querySelector('[data-rate-date="' + key + '"]');

    if (!s || !s.latest || s.latest.value == null) {
      if (valEl)  valEl.textContent  = '...';
      if (wowEl)  { wowEl.textContent = 'Data unavailable'; wowEl.className = 'drozq-rate-card__delta drozq-rate-card__delta--flat'; }
      if (yoyEl)  { yoyEl.textContent = ''; yoyEl.className = 'drozq-rate-card__delta drozq-rate-card__delta--flat'; }
      if (dateEl) dateEl.innerHTML = '&nbsp;';
      if (sparkEl) sparkEl.innerHTML = '';
      return;
    }

    if (valEl) valEl.textContent = fmtRate(s.latest.value);
    if (sparkEl) renderSparkline(sparkEl, s.history || []);

    var wow = fmtDeltaWoW(s.delta, s.cadence);
    if (wowEl) {
      wowEl.textContent = wow.text;
      wowEl.className = 'drozq-rate-card__delta drozq-rate-card__delta--' + wow.cls;
    }
    var yoy = fmtDeltaYoY(s.deltaYoY);
    if (yoyEl) {
      yoyEl.textContent = yoy.text;
      yoyEl.className = 'drozq-rate-card__delta drozq-rate-card__delta--' + yoy.cls;
    }
    if (dateEl) {
      dateEl.textContent = s.latest.date ? 'As of ' + fmtDate(s.latest.date) : '';
    }
  }

  function renderAffordability(rate30) {
    var amounts = [500000, 750000, 1000000, 1500000, 2000000];
    var capRate = document.querySelector('[data-aff-rate]');
    if (capRate) capRate.textContent = fmtRate(rate30);
    if (rate30 == null || !isFinite(rate30)) return;
    amounts.forEach(function(P){
      var mo = payment(P, rate30, 30);
      var total = mo * 30 * 12;
      var interest = total - P;
      var moEl  = document.querySelector('[data-aff-mo="' + P + '"]');
      var intEl = document.querySelector('[data-aff-int="' + P + '"]');
      var totEl = document.querySelector('[data-aff-tot="' + P + '"]');
      if (moEl)  moEl.textContent  = dollars.format(Math.round(mo));
      if (intEl) intEl.textContent = dollars.format(Math.round(interest));
      if (totEl) totEl.textContent = dollars.format(Math.round(total));
    });
  }

  // Calculator state
  var calcRateEl   = document.getElementById('calc-rate');
  var calcPriceEl  = document.getElementById('calc-price');
  var calcDownEl   = document.getElementById('calc-down');
  var calcTermEls  = document.querySelectorAll('[data-calc-term]');
  var calcMonthlyOut  = document.getElementById('calc-out-monthly');
  var calcInterestOut = document.getElementById('calc-out-interest');
  var calcTotalOut    = document.getElementById('calc-out-total');
  var apiRate30 = null, apiRate15 = null;
  var currentTerm = 30;
  var userTouchedRate = false;

  function setCalcTerm(term, sourceClick) {
    currentTerm = term;
    calcTermEls.forEach(function(el){
      var on = (parseInt(el.getAttribute('data-calc-term'), 10) === term);
      el.classList.toggle('is-active', on);
      el.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    if (sourceClick && !userTouchedRate) {
      var r = (term === 15 ? apiRate15 : apiRate30);
      if (r != null && calcRateEl) calcRateEl.value = r.toFixed(2);
    }
    recompute();
  }

  function recompute() {
    if (!calcPriceEl || !calcDownEl || !calcRateEl) return;
    var price = parseFloat(calcPriceEl.value) || 0;
    var downPct = parseFloat(calcDownEl.value) || 0;
    var rate = parseFloat(calcRateEl.value) || 0;
    var loan = Math.max(0, price - (price * downPct / 100));
    var mo = payment(loan, rate, currentTerm);
    var total = mo * currentTerm * 12;
    var interest = total - loan;
    if (calcMonthlyOut)  calcMonthlyOut.textContent  = dollars.format(Math.round(mo));
    if (calcInterestOut) calcInterestOut.textContent = dollars.format(Math.round(interest));
    if (calcTotalOut)    calcTotalOut.textContent    = dollars.format(Math.round(total));
  }

  function wireCalc() {
    if (!calcPriceEl) return;
    [calcPriceEl, calcDownEl, calcRateEl].forEach(function(el){
      if (!el) return;
      el.addEventListener('input', function(){
        if (el === calcRateEl) userTouchedRate = true;
        recompute();
      });
    });
    calcTermEls.forEach(function(el){
      el.addEventListener('click', function(){
        var t = parseInt(el.getAttribute('data-calc-term'), 10) || 30;
        setCalcTerm(t, true);
      });
    });
    recompute();
  }

  function render(payload) {
    var series = (payload && payload.series) || {};
    rateKeys.forEach(function(k){ renderCard(k, series[k]); });

    var rate30 = (series.rate30y && series.rate30y.latest && series.rate30y.latest.value) || null;
    var rate15 = (series.rate15y && series.rate15y.latest && series.rate15y.latest.value) || null;
    apiRate30 = rate30; apiRate15 = rate15;

    if (!userTouchedRate && calcRateEl && rate30 != null) {
      calcRateEl.value = (currentTerm === 15 && rate15 != null ? rate15 : rate30).toFixed(2);
    }
    renderAffordability(rate30);
    recompute();

    var meta = document.getElementById('drozq-rates-meta');
    if (meta) {
      if (payload && payload.lastUpdated) {
        meta.innerHTML = 'Latest reading: <strong>' + fmtDate(payload.lastUpdated) + '</strong> &middot; Source: '
          + '<a href="' + (payload.sourceUrl || 'https://fred.stlouisfed.org/') + '" rel="noopener" style="color:#d92228; font-weight:700; text-decoration:none">Federal Reserve Economic Data (FRED), St. Louis Fed</a>';
      } else if (payload && payload.error) {
        meta.innerHTML = '<strong>Data temporarily unavailable.</strong> Refresh the page in a few minutes.';
      } else {
        meta.innerHTML = 'Source: Federal Reserve Economic Data (FRED), St. Louis Fed';
      }
    }
  }

  function fail(err) {
    rateKeys.forEach(function(k){ renderCard(k, null); });
    render({ error: (err && err.message) || 'fetch_failed' });
  }

  // FAQ accordion is wired by the synced funnel JS (delegated click handler
  // on every button[aria-controls][aria-expanded] paired with a role="region"
  // panel). No local handler needed; adding one would double-toggle.

  function go() {
    wireCalc();
    fetch(endpoint, { headers: { 'accept': 'application/json' }})
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
    + RATES_SECTION
    + AFFORDABILITY_SECTION
    + CALCULATOR_SECTION
    + EXPLAINERS_SECTION
    + MID_TABS
    + FAQ_SECTION
    + METHOD_CROSSLINKS
    + CLOSING_CTA
    + JSON_LD_BLOCKS
    + RATES_SCRIPT
)


if __name__ == "__main__":
    scaffold_page(
        target="rates/index.html",
        title="Today's Mortgage Rates -- Live from FRED | Joshua Guerrero, Real Brokerage",
        description="Live 30-year and 15-year mortgage rates, 10-year Treasury yield, and Fed funds rate, pulled directly from the Federal Reserve and refreshed hourly. Plus a mortgage payment calculator, affordability table, and plain-English read on what each rate actually does.",
        canonical="/rates/",
        main_body_html=MAIN_BODY,
        og_title="Today's Mortgage Rates -- Live from FRED",
        og_description="Live mortgage and benchmark rates refreshed automatically. 30-year fixed, 15-year fixed, 10-year Treasury, Fed funds. Plus a calculator and affordability table.",
    )
