"""Migrate /prices/ to the homepage template scaffold.

Second-pass build: production-worthy resource page on California home
prices and the broader market signals around them. The page is meant
to be cited by reporters, agents, prospective buyers/sellers, and any
California real estate observer.

Page anatomy (top to bottom):
  1.  Hero w/ 3-tab funnel CTA (template requirement).
  2.  Tier 1 grid: LA Case-Shiller, San Diego Case-Shiller, California
      statewide HPI. Current value, MoM/QoQ, YoY, sparkline.
  3.  Long-term appreciation table: 5-year + 10-year CAGR per market.
      Citation magnet. Hydrated from cagr5y/cagr10y fields on the API.
  4.  Plain-English explainers (3 cards): Case-Shiller method, FHFA
      method, what the market signals actually predict.
  5.  Tier 3 grid: months of supply, existing home sales, NAR
      affordability index, US unemployment. Cards switch to a tinted
      bg so the white section keeps card-on-section contrast.
  6.  Thin "Cost of Money" crosslink band to /rates/ (5/1 ARM
      discontinued upstream).
  7.  Mid-page sell/buy tabs (template requirement, second lead path).
  8.  6-question FAQ accordion. Paired with FAQPage JSON-LD for SERP
      rich results. Accordion behavior is wired by the synced funnel
      JS -- no local handler.
  9.  Methodology section. Source, refresh cadence, outbound links to
      Case-Shiller (S&P), FHFA, NAR, BLS, FRED. Author attribution
      with DRE.
 10.  Crosslinks band (secondary-outlined): /rates/,
      /market-insights/, /process/, /field-notes/, /about/.
 11.  Closing CTA pill + direct phone fallback.
 12.  JSON-LD: WebPage + 7 Dataset + FAQPage + BreadcrumbList +
      Person. The Person entity reuses the same @id as /rates/ so the
      author identity is consistent across both data products.

Data flows through /functions/api/prices.js (FRED-backed, edge-cached
1h). Hydration runs on DOMContentLoaded: cards, sparklines, primary +
YoY delta, and the appreciation table. FAQ accordion + tab switching
are wired globally by the synced funnel JS.

Card-on-section contrast: warm-gray sections use white cards, white
sections use tinted (#f7f4ef) cards. Both directions preserve
contrast; same-on-same is the banned pattern.
"""
from pathlib import Path
import sys
import json as _json
import datetime as _dt

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

  <section aria-labelledby="prices-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="prices-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">California home prices and the market signals around them.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Live LA and San Diego Case-Shiller, the statewide HPI, and the signals that move them.</p>
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
# Page styles -- data cards (2 variants), appreciation table, explainers, FAQ
# ---------------------------------------------------------------------------

PAGE_STYLE = """
<style>
/* ---- Data card grid ---------------------------------------------------- */
.drozq-data-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
.drozq-data-grid--3 { grid-template-columns: 1fr; }
@media (min-width: 768px) { .drozq-data-grid--3 { grid-template-columns: repeat(3, 1fr); gap: 20px; } }
.drozq-data-grid--4 { grid-template-columns: 1fr; }
@media (min-width: 640px) { .drozq-data-grid--4 { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 960px) { .drozq-data-grid--4 { grid-template-columns: repeat(4, 1fr); gap: 20px; } }

.drozq-data-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px 22px;
  display: flex; flex-direction: column; gap: 10px;
  min-height: 220px;
}
/* Tinted card variant: used on white sections so cards keep contrast. */
.drozq-data-card--tint { background: #f7f4ef; border-color: #ece8e1; }

.drozq-data-card__label {
  font-size: 0.78rem; font-weight: 700; letter-spacing: 0.18em;
  text-transform: uppercase; color: #3f4650; line-height: 1.35; margin: 0;
}
.drozq-data-card__sub { font-size: 0.78rem; color: #757575; margin: -4px 0 0; }
.drozq-data-card__value {
  font-size: clamp(1.85rem, 3.6vw, 2.5rem); font-weight: 800;
  line-height: 1; letter-spacing: -0.02em; color: #1a1816;
  font-variant-numeric: tabular-nums;
}
.drozq-data-card__spark { display: block; width: 100%; height: 36px; }
.drozq-data-card__spark svg { width: 100%; height: 100%; display: block; overflow: visible; }
.drozq-data-card__deltas { display: flex; flex-direction: column; gap: 4px; font-size: 0.82rem; font-variant-numeric: tabular-nums; }
.drozq-data-card__delta { font-weight: 700; letter-spacing: 0.01em; color: #757575; }
.drozq-data-card__delta--up   { color: #b81d22; }
.drozq-data-card__delta--down { color: #0a801f; }
.drozq-data-card__delta--flat { color: #757575; }
.drozq-data-card__date { font-size: 0.78rem; color: #757575; margin: 0; }

.drozq-data-meta { text-align: center; color: #757575; font-size: 0.875rem; margin: 20px 0 0; }
.drozq-data-meta strong { color: #2b2b2b; font-weight: 700; }

.drozq-tier-chip {
  display: inline-block;
  font-size: 0.66rem; font-weight: 800; letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #d92228;
  background: #fff5f5; border: 1px solid #f7d3d4;
  border-radius: 999px; padding: 4px 10px; margin-bottom: 12px;
}

/* ---- Long-term appreciation table ------------------------------------- */
.drozq-app-wrap {
  background: #ffffff; border: 1px solid #e5e5e5; border-radius: 16px;
  padding: 8px; overflow-x: auto;
}
.drozq-app-table {
  width: 100%; border-collapse: collapse; min-width: 540px;
  font-variant-numeric: tabular-nums;
}
.drozq-app-table th, .drozq-app-table td { padding: 14px 16px; font-size: 0.95rem; }
.drozq-app-table thead th {
  text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.72rem;
  color: #3f4650; border-bottom: 1px solid #e5e5e5; text-align: right;
}
.drozq-app-table thead th:first-child { text-align: left; }
.drozq-app-table tbody td { text-align: right; font-weight: 700; color: #1a1816; }
.drozq-app-table tbody td:first-child { text-align: left; font-weight: 700; }
.drozq-app-table tbody tr + tr td { border-top: 1px solid #f0f0f0; }
.drozq-app-table tbody tr:hover td { background: #faf7f3; }
.drozq-app-table td.cagr { color: #0a801f; }
.drozq-app-table td.cagr-down { color: #b81d22; }
.drozq-app-table caption {
  caption-side: top; text-align: left;
  padding: 12px 16px 4px; font-size: 0.82rem; color: #3f4650;
}
.drozq-app-date {
  display: block; font-size: 0.72rem; font-weight: 400;
  color: #757575; letter-spacing: 0.04em; margin-top: 2px;
}

/* ---- Signal explainers (compact, value-per-second) -------------------- */
.drozq-signals-explain-grid {
  display: grid; grid-template-columns: 1fr; gap: 12px;
  margin-top: 32px;
}
@media (min-width: 640px) { .drozq-signals-explain-grid { grid-template-columns: repeat(2, 1fr); gap: 16px; } }
@media (min-width: 1024px) { .drozq-signals-explain-grid { grid-template-columns: repeat(4, 1fr); gap: 16px; } }
.drozq-signals-explain__lead {
  text-align: center; margin: 40px auto 0; max-width: 720px;
}
.drozq-signals-explain__lead h3 {
  font-size: 1.25rem; font-weight: 800; color: #1a1816;
  margin: 0 0 8px; line-height: 1.4;
}
@media (min-width: 768px) { .drozq-signals-explain__lead h3 { font-size: 1.5rem; } }
.drozq-signals-explain__lead p {
  color: #3f4650; font-size: 0.95rem; line-height: 1.55; margin: 0;
}
.drozq-signal-explain {
  background: #f7f4ef; border: 1px solid #ece8e1; border-radius: 12px;
  padding: 18px 18px 20px; display: flex; flex-direction: column; gap: 6px;
  border-left: 3px solid #d92228;
}
.drozq-signal-explain__eyebrow {
  font-size: 0.64rem; font-weight: 700; letter-spacing: 0.16em;
  text-transform: uppercase; color: #d92228;
  margin: 0;
}
.drozq-signal-explain h4 {
  font-size: 1rem; font-weight: 800; color: #1a1816;
  margin: 2px 0 4px; line-height: 1.35;
}
.drozq-signal-explain p {
  color: #3f4650; font-size: 0.88rem; line-height: 1.55; margin: 0;
}

/* ---- Explainer cards -------------------------------------------------- */
.drozq-explain-grid {
  display: grid; grid-template-columns: 1fr; gap: 20px;
}
@media (min-width: 768px) { .drozq-explain-grid { grid-template-columns: repeat(3, 1fr); gap: 24px; } }
.drozq-explain {
  background: #ffffff; border: 1px solid #e5e5e5; border-radius: 16px;
  padding: 24px 22px;
}
.drozq-explain__num {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em;
  text-transform: uppercase; color: #d92228; margin: 0 0 6px;
}
.drozq-explain h3 {
  font-size: 1.1rem; font-weight: 800; color: #1a1816;
  margin: 0 0 8px; line-height: 1.4;
}
.drozq-explain p { color: #3f4650; font-size: 0.95rem; line-height: 1.6; margin: 0; }

/* ---- FAQ (matches /rates/, wired by synced funnel JS) ----------------- */
.drozq-faq-list { max-width: 720px; margin: 0 auto; }
.drozq-faq-item { border-bottom: 1px solid #e5e5e5; }
.drozq-faq-item button {
  width: 100%; background: transparent; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: space-between;
  text-align: left; padding: 16px 40px 16px 0; color: #1a1816;
  font: inherit; font-size: 16px; font-weight: 400; line-height: 1.5;
}
.drozq-faq-item button:hover { color: #d92228; }
.drozq-faq-item button svg {
  width: 20px; height: 20px; flex-shrink: 0; color: #3f4650;
  transition: transform .2s ease;
}
.drozq-faq-item button[aria-expanded="true"] svg { transform: rotate(45deg); color: #d92228; }
.drozq-faq-region { overflow: hidden; max-height: 0; transition: max-height .3s ease; }
.drozq-faq-region p { margin: 0 0 16px; color: #3f4650; font-size: 15px; line-height: 1.6; }

/* ---- Mortgage payment calculator (ported from /rates/) ---------------- */
.drozq-calc {
  background: #ffffff; border: 1px solid #e5e5e5; border-radius: 16px;
  padding: 24px;
}
@media (min-width: 768px) { .drozq-calc { padding: 32px; } }
.drozq-calc__grid {
  display: grid; grid-template-columns: 1fr; gap: 16px;
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
  margin-top: 24px; display: grid; grid-template-columns: 1fr; gap: 16px;
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
.drozq-calc__note { margin-top: 18px; font-size: 0.82rem; color: #757575; }

/* ---- Secondary outlined link ------------------------------------------ */
.btn-secondary-outline {
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent; color: #d92228; border: 1px solid #d92228;
  font-weight: 700; font-size: 14px; letter-spacing: 0.3px;
  padding: 10px 22px; border-radius: 9999px; text-decoration: none;
  transition: background-color .2s ease, color .2s ease;
}
.btn-secondary-outline:hover { background: #d92228; color: #fff; }
@media (min-width: 768px) { .btn-secondary-outline { font-size: 15px; } }
</style>
"""


# ---------------------------------------------------------------------------
# Card factory (reused across both data sections)
# ---------------------------------------------------------------------------

def data_card(key: str, label: str, sub: str = "", variant: str = "") -> str:
    cls = "drozq-data-card" + (" " + variant if variant else "")
    sub_html = f'<p class="drozq-data-card__sub">{sub}</p>' if sub else ""
    return f"""
      <div class="{cls}" id="card-{key}" data-data-card="{key}">
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
# 2. California Home Prices (Tier 1)
# ---------------------------------------------------------------------------

TIER1_SECTION = f"""
<section aria-labelledby="prices-tier1-title" id="california-home-prices" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
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
# 3. Long-term appreciation table -- citation magnet
# ---------------------------------------------------------------------------

# Historical reference values for the appreciation table. Snapshotted from
# FRED on 2026-05-27. Today's column stays live; the rest of the row is
# manually re-anchored when this script is re-run (the index-point values
# don't move once published, so the 5y_ago / 10y_ago cells are immutable;
# the CAGR cells drift by ~0.05 percentage points per month and are
# considered acceptably stable for a "snapshot" framing).
APPRECIATION_SNAPSHOT_DATE = "May 2026"
APPRECIATION_ROWS = [
    # (display name, key, 5y_ago, 5y_ago_date, 10y_ago, 10y_ago_date, 5y_cagr_pct, 10y_cagr_pct)
    ("Los Angeles Metro",      "hpiLA", "333", "March 2021",   "246", "March 2016",   "5.87%", "6.05%"),
    ("San Diego Metro",        "hpiSD", "320", "March 2021",   "222", "March 2016",   "6.79%", "7.18%"),
    ("California (statewide)", "hpiCA", "719", "Q1 2021",      "544", "Q1 2016",      "6.33%", "6.03%"),
]


def appreciation_row(name: str, key: str, fy: str, fyd: str, ty: str, tyd: str, cagr5: str, cagr10: str) -> str:
    return f"""
          <tr>
            <td>{name}</td>
            <td data-app-today="{key}">&hellip;</td>
            <td>{fy}<br><span class="drozq-app-date">{fyd}</span></td>
            <td>{ty}<br><span class="drozq-app-date">{tyd}</span></td>
            <td class="cagr">{cagr5}</td>
            <td class="cagr">{cagr10}</td>
          </tr>"""


APPRECIATION_TABLE_SECTION = f"""
<section aria-labelledby="prices-appreciation-title" id="long-term-appreciation" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <span class="drozq-tier-chip">Long-term appreciation</span>
      <h2 id="prices-appreciation-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Five and ten years, compounded.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">CAGR = compound annual growth rate. The headline question for most California homeowners isn't this month, it's what their equity has actually done since they bought. These two columns are that answer for the LA metro, the San Diego metro, and the state as a whole.</p>
    </div>

    <div class="drozq-app-wrap">
      <table class="drozq-app-table" aria-describedby="prices-app-cap">
        <caption id="prices-app-cap">Today's column updates live from FRED. Historical anchors and CAGR snapshotted {APPRECIATION_SNAPSHOT_DATE}.</caption>
        <thead>
          <tr>
            <th scope="col">Market</th>
            <th scope="col">Today</th>
            <th scope="col">5y ago</th>
            <th scope="col">10y ago</th>
            <th scope="col">5y CAGR</th>
            <th scope="col">10y CAGR</th>
          </tr>
        </thead>
        <tbody>
{"".join(appreciation_row(*row) for row in APPRECIATION_ROWS)}
        </tbody>
      </table>
    </div>

    <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_16px ta_center m_0">Index values are unitless (Case-Shiller normalized to 100 at January 2000; FHFA normalized to 100 at Q1 1991). Read CAGR as the annualized rate at which an index point compounded over that window.</p>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 4. Plain-English explainers
# ---------------------------------------------------------------------------

EXPLAINERS_SECTION = """
<section aria-labelledby="prices-explain-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <span class="drozq-tier-chip">What these numbers mean</span>
      <h2 id="prices-explain-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The plain-English read.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Three short explainers on what these indices actually measure and why each one tells a slightly different story.</p>
    </div>

    <div class="drozq-explain-grid">
      <div class="drozq-explain">
        <p class="drozq-explain__num">Explainer 01</p>
        <h3>Case-Shiller tracks the same homes over time.</h3>
        <p>The S&amp;P CoreLogic Case-Shiller index uses a repeat-sales methodology: it follows the same physical homes through multiple transactions and measures how their prices changed. That filters out the mix-shift problem (medians get distorted when expensive homes sell more often, or vice versa). It's the cleanest read on what a typical home in the LA or San Diego metro actually appreciated.</p>
      </div>
      <div class="drozq-explain">
        <p class="drozq-explain__num">Explainer 02</p>
        <h3>FHFA tracks the conforming half of the market.</h3>
        <p>The Federal Housing Finance Agency's All-Transactions HPI is built from mortgages bought or guaranteed by Fannie Mae and Freddie Mac. That means it covers conforming loans (under the federal limit, currently $806,500 in most counties) and misses jumbo, cash, and non-conforming purchases. The trade-off: it's the only index that gives a single number for the entire state, including counties Case-Shiller doesn't cover.</p>
      </div>
      <div class="drozq-explain">
        <p class="drozq-explain__num">Explainer 03</p>
        <h3>Supply, demand, affordability, and jobs are the four drivers.</h3>
        <p>The market signals at the top of the page (months of supply, existing home sales, NAR affordability, US unemployment) are what move the indices over the following one to three quarters. When months of supply stretches above ~6, prices typically soften. When the affordability index climbs past 100, demand returns. The labor market sets the ceiling: prices rarely keep climbing through a rising unemployment trend.</p>
      </div>
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 5. Market Signals (Tier 3) -- white bg, tinted cards for contrast
# ---------------------------------------------------------------------------

def signal_explain(eyebrow: str, headline: str, body: str) -> str:
    return f"""
      <div class="drozq-signal-explain">
        <p class="drozq-signal-explain__eyebrow">{eyebrow}</p>
        <h4>{headline}</h4>
        <p>{body}</p>
      </div>"""


TIER3_SECTION = f"""
<section aria-labelledby="prices-tier3-title" id="market-signals" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <span class="drozq-tier-chip">Market Signals</span>
      <h2 id="prices-tier3-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">The four signals that move prices.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Supply, demand, affordability, and the broader labor market. National data, monthly cadence. Movements here show up in California-specific prices over the following one to three quarters.</p>
    </div>

    <div class="drozq-data-grid drozq-data-grid--4">
{data_card("supplyMonths",  "Months of Supply",        "MSACSR, new homes, US",       variant="drozq-data-card--tint")}
{data_card("existingSales", "Existing Home Sales",     "EXHOSLUSM495S, SAAR",         variant="drozq-data-card--tint")}
{data_card("affordIdx",     "Affordability Index",     "NAR Composite, US",           variant="drozq-data-card--tint")}
{data_card("unemployment",  "US Unemployment Rate",    "UNRATE, monthly",             variant="drozq-data-card--tint")}
    </div>

    <p class="drozq-data-meta" id="prices-tier3-meta">&nbsp;</p>

    <div class="drozq-signals-explain__lead">
      <h3>What each signal actually tells you.</h3>
      <p>Cause on the left, effect on the right. Read across all four to see where the market is heading.</p>
    </div>

    <div class="drozq-signals-explain-grid">
{signal_explain(
    "Signal 01 &middot; MSACSR",
    "The inventory clock.",
    "Months of inventory at the current sales pace. Under 4 is a seller's market, 4 to 6 is balanced, over 6 starts to favor buyers. When supply stretches past six, listings begin cutting price. When it drops under four, multiple-offer dynamics come back."
)}
{signal_explain(
    "Signal 02 &middot; EXHOSLUSM495S",
    "The demand pulse.",
    "Annualized pace of resales closing each month. Healthy is around 5 million, weak is under 4 million, the 2021 peak was 6.5 million. A rising line says buyers are unlocking; a falling line says they're sitting out, and prices follow with a one- to two-quarter lag."
)}
{signal_explain(
    "Signal 03 &middot; FIXHAI",
    "The qualify-or-not test.",
    "Compares median family income to the income needed to qualify for the median-priced home with 20% down. 100 is exact match. Above means buyers have surplus; below means deficit. California's standalone read runs far below this national composite, which is why local affordability matters more than the headline."
)}
{signal_explain(
    "Signal 04 &middot; UNRATE",
    "The ceiling on demand.",
    "Share of the labor force unemployed and actively looking. Under 4% supports wage growth and qualifying power. Over 5% erodes both. Prices rarely keep climbing through a rising unemployment trend, because the marginal buyer can't qualify when paychecks are at risk."
)}
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 6. Cost of Money (thin band) -- MORTGAGE5US discontinued, link to /rates/
# ---------------------------------------------------------------------------

RATES_CROSSLINK = """
<section aria-labelledby="prices-rates-link" class="bg-c_#f2f0ef py_40px md:py_56px">
  <div class="max-w_720px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <span class="drozq-tier-chip">Cost of Money</span>
    <h2 id="prices-rates-link" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_24px md:fs_30px ls_0.3px ta_center mb_16px">Prices set the ceiling. Rates set the math.</h2>
    <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px mb_24px m_0_auto" style="max-width:560px;">The companion page tracks the 30-year and 15-year fixed mortgages, the 10-year Treasury (the leading indicator for both), and the Fed funds rate. Same FRED source, same hourly refresh.</p>
    <a href="/rates/" class="btn-secondary-outline">See live mortgage rates &rarr;</a>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 7. Mid-page sell/buy tabs (template requirement)
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
# 8. FAQ (paired with FAQPage JSON-LD below)
# ---------------------------------------------------------------------------

FAQ_QUESTIONS = [
    ("How are these home price indices actually calculated?",
     "The Case-Shiller index uses a repeat-sales methodology: it tracks transactions of the same physical homes over time, which filters out mix-shift bias and gives a cleaner read on what a typical home in that metro appreciated. The FHFA All-Transactions HPI is built from transactions on properties whose mortgages were bought or guaranteed by Fannie Mae or Freddie Mac, which means it covers conforming loans (under the federal limit, currently $806,500 in most counties) and includes both purchases and refinances."),
    ("Why is the LA index number so different from San Diego if they're both Case-Shiller?",
     "Each Case-Shiller metro is its own series with its own base. All metros are normalized to 100 at January 2000. From there, the index level just compounds with that metro's price growth. The absolute number doesn't compare across metros; the year-over-year (or multi-year) percent change does."),
    ("Why are the months-of-supply and existing-sales numbers national, not California-specific?",
     "There is no single FRED series for California-specific months of supply or existing home sales. The Census Bureau and the National Association of Realtors publish only national aggregates at this cadence. National supply and demand are the leading indicators that California-specific prices follow with a one- to three-quarter lag; for California-specific volumes by county, see the market-insights page."),
    ("What does the affordability index mean exactly?",
     "It's the NAR Housing Affordability Composite Index. 100 = a median-income family has exactly enough income to qualify for a conventional 30-year fixed mortgage on a median-priced existing single-family home with a 20% down payment. Above 100 = surplus. Below 100 = deficit. California's standalone affordability is much lower than the national composite shown here; the national index is the macro signal."),
    ("How current is the data on this page?",
     "Each card shows its own observation date. The home price indices typically lag two to three months because of how repeat-sales data is collected and revised. The market signals (supply, sales, affordability, unemployment) lag one to two months. The page itself reads from FRED hourly, so a new release surfaces here within about an hour of publication."),
    ("Where does the underlying data come from?",
     "All series come from FRED, the Federal Reserve Bank of St. Louis's economic data system. FRED is the redistribution layer; the original publishers are S&amp;P CoreLogic and Case-Shiller (the metro home price indices), the Federal Housing Finance Agency (the statewide HPI), the U.S. Census Bureau (months of supply), the National Association of Realtors (existing sales, affordability), and the Bureau of Labor Statistics (unemployment). Methodology section below links each one."),
]


def faq_item(idx: int, q: str, a: str) -> str:
    qid = f"prices-faq-{idx}-header"
    aid = f"prices-faq-{idx}-content"
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
<section aria-labelledby="prices-faq-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <span class="drozq-tier-chip">FAQ</span>
      <h2 id="prices-faq-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Questions about the numbers on this page.</h2>
    </div>

    <div class="drozq-faq-list">
{"".join(faq_item(i+1, q, a) for i, (q, a) in enumerate(FAQ_QUESTIONS))}
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 9. Methodology
# ---------------------------------------------------------------------------

METHODOLOGY_SECTION = """
<section aria-labelledby="prices-method-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_840px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <span class="drozq-tier-chip">Methodology</span>
    <h2 id="prices-method-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_20px">Where this data actually comes from.</h2>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">All seven series are pulled directly from <a href="https://fred.stlouisfed.org/" rel="noopener" class="c_#d92228 fw_700">Federal Reserve Economic Data (FRED)</a>, maintained by the Federal Reserve Bank of St. Louis. FRED is the redistribution layer. The underlying publishers are:</p>
    <ul class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px ta_left mb_24px" style="max-width:680px; margin-left:auto; margin-right:auto;">
      <li><a href="https://fred.stlouisfed.org/series/LXXRSA" rel="noopener" class="c_#d92228 fw_700">LXXRSA</a> &middot; <a href="https://fred.stlouisfed.org/series/SDXRSA" rel="noopener" class="c_#d92228 fw_700">SDXRSA</a>. S&amp;P CoreLogic Case-Shiller Home Price Indices, LA and San Diego metros. Monthly, two-month lag, seasonally adjusted.</li>
      <li><a href="https://fred.stlouisfed.org/series/CASTHPI" rel="noopener" class="c_#d92228 fw_700">CASTHPI</a>. Federal Housing Finance Agency All-Transactions House Price Index for California. Quarterly.</li>
      <li><a href="https://fred.stlouisfed.org/series/MSACSR" rel="noopener" class="c_#d92228 fw_700">MSACSR</a>. U.S. Census Bureau Monthly Supply of New Houses. Monthly.</li>
      <li><a href="https://fred.stlouisfed.org/series/EXHOSLUSM495S" rel="noopener" class="c_#d92228 fw_700">EXHOSLUSM495S</a>. National Association of Realtors Existing Home Sales, seasonally adjusted annualized rate, thousands of units. Monthly.</li>
      <li><a href="https://fred.stlouisfed.org/series/FIXHAI" rel="noopener" class="c_#d92228 fw_700">FIXHAI</a>. National Association of Realtors Housing Affordability Composite Index. Monthly (with gaps).</li>
      <li><a href="https://fred.stlouisfed.org/series/UNRATE" rel="noopener" class="c_#d92228 fw_700">UNRATE</a>. Bureau of Labor Statistics Civilian Unemployment Rate, seasonally adjusted. Monthly.</li>
    </ul>
    <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_16px">The page itself reads FRED via a Cloudflare Pages function and caches the response at the edge for one hour. New FRED observations surface within roughly an hour of publication. CAGR figures in the appreciation table are computed at request time from the latest observation and the corresponding observation 5 or 10 years prior (or as close to those points as the published cadence allows).</p>
    <p class="c_#3f4650 fs_15px md:fs_16px lh_24px md:lh_28px m_0"><em>Authored and maintained by Joshua Guerrero, Real Estate Agent, Real Brokerage. California DRE #02267255. Reach out at <a href="tel:9494385948" class="c_#d92228 fw_700">(949) 438-5948</a> or via <a href="/contact/" class="c_#d92228 fw_700">/contact/</a>.</em></p>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 10. Crosslinks
# ---------------------------------------------------------------------------

CROSSLINKS_SECTION = """
<section aria-labelledby="prices-crosslinks-title" class="bg_#fff py_48px md:py_64px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px ta_center">
    <span class="drozq-tier-chip">Related on Drozq</span>
    <h2 id="prices-crosslinks-title" class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_40px fs_22px md:fs_28px ls_0.3px ta_center mb_24px">Pair the indices with the local read.</h2>
    <div class="d_flex flex-wrap_wrap jc_center gap_12px md:gap_16px">
      <a href="/rates/" class="btn-secondary-outline">Live mortgage rates &rarr;</a>
      <a href="/market-insights/" class="btn-secondary-outline">Southern California county data &rarr;</a>
      <a href="/process/" class="btn-secondary-outline">How I work &rarr;</a>
      <a href="/field-notes/" class="btn-secondary-outline">Field Notes &rarr;</a>
      <a href="/about/" class="btn-secondary-outline">About the author &rarr;</a>
    </div>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 11. Mortgage payment calculator (duplicated from /rates/)
#
# Lives directly above the closing CTA so the journey reads as
# "play with the math" -> "talk to me". The rate input is pre-filled
# live from /api/rates (separate fetch from /api/prices, runs in
# parallel inside the page IIFE). When the term toggles between 30y
# and 15y, the rate input swaps to the matching FRED series. If the
# user manually edits the rate, the auto-fill stops respecting the
# term toggle (userTouchedRate flag).
# ---------------------------------------------------------------------------

CALCULATOR_SECTION = f"""
<section aria-labelledby="prices-calc-title" class="bg-c_#f2f0ef py_48px md:py_64px lg:py_72px">
  <div class="max-w_840px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Run your numbers</p>
      <h2 id="prices-calc-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Mortgage payment calculator.</h2>
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
      <h3 class="fw_800 op_0.87 c_#2b2b2b lh_32px md:lh_40px fs_22px md:fs_28px ls_0.3px ta_center mb_12px">These numbers are math. Your specific California purchase is a strategy.</h3>
      <p class="c_#3f4650 fs_15px md:fs_17px lh_24px md:lh_28px max-w_640px m_0_auto mb_24px">A monthly payment is one variable. Comps, condition, contingencies, and timing are the rest. Tell me where you're looking and I'll run the read.</p>

      <div role="tabpanel" aria-labelledby="tab-buy" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("City, neighborhood, or ZIP", value="Irvine, CA")}</div>
      </div>
    </div>

  </div>
</section>
"""


# ---------------------------------------------------------------------------
# 12. Closing CTA
# ---------------------------------------------------------------------------

CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
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
# 12. JSON-LD: WebPage + 7 Dataset + FAQPage + BreadcrumbList + Person
# ---------------------------------------------------------------------------

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
    "name": "California Home Prices and Market Signals -- Live from FRED",
    "description": "Live LA + San Diego Case-Shiller home price indices, FHFA California statewide HPI, plus months of supply, existing sales, NAR affordability, and US unemployment. Pulled from the Federal Reserve, refreshed hourly. Includes 5- and 10-year CAGR for each home price index.",
    "url": "https://drozq.com/prices/",
    "dateModified": _TODAY,
    "author": {"@id": "https://drozq.com/#person-joshua"},
    "isPartOf": {"@type": "WebSite", "name": "Drozq", "url": "https://drozq.com/"},
    "mainContentOfPage": {
        "@type": "WebPageElement",
        "name": "California Home Prices and Market Signals"
    }
}


def dataset_jsonld(series_id: str, name: str, description: str, anchor: str,
                   cadence: str, original_creator: str, original_creator_url: str | None = None) -> dict:
    creator = {"@type": "Organization", "name": original_creator}
    if original_creator_url:
        creator["url"] = original_creator_url
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": name,
        "description": description,
        "url": f"https://drozq.com/prices/#{anchor}",
        "creator": creator,
        "distribution": {
            "@type": "DataDownload",
            "contentUrl": f"https://fred.stlouisfed.org/series/{series_id}",
            "encodingFormat": "text/html"
        },
        "isBasedOn": f"https://fred.stlouisfed.org/series/{series_id}",
        "license": "https://research.stlouisfed.org/docs/api/terms_of_use.html",
        "temporalCoverage": "rolling",
        "measurementTechnique": cadence,
        "variableMeasured": {"@type": "PropertyValue", "name": name},
        "datePublished": _TODAY,
        "dateModified": _TODAY
    }


DATASETS_JSONLD = [
    dataset_jsonld(
        "LXXRSA",
        "S&P CoreLogic Case-Shiller LA Home Price Index",
        "Repeat-sales home price index for the Los Angeles-Long Beach-Anaheim metro statistical area, normalized to 100 at January 2000. Monthly, seasonally adjusted.",
        "california-home-prices",
        "monthly",
        "S&P Dow Jones Indices / CoreLogic",
        "https://www.spglobal.com/spdji/en/index-family/indicators/sp-corelogic-case-shiller/"
    ),
    dataset_jsonld(
        "SDXRSA",
        "S&P CoreLogic Case-Shiller San Diego Home Price Index",
        "Repeat-sales home price index for the San Diego-Carlsbad metro statistical area, normalized to 100 at January 2000. Monthly, seasonally adjusted.",
        "california-home-prices",
        "monthly",
        "S&P Dow Jones Indices / CoreLogic",
        "https://www.spglobal.com/spdji/en/index-family/indicators/sp-corelogic-case-shiller/"
    ),
    dataset_jsonld(
        "CASTHPI",
        "FHFA All-Transactions House Price Index for California",
        "FHFA-published purchase + refinance transaction price index covering Fannie Mae and Freddie Mac conforming-loan transactions in California. Quarterly.",
        "california-home-prices",
        "quarterly",
        "Federal Housing Finance Agency",
        "https://www.fhfa.gov/data/hpi"
    ),
    dataset_jsonld(
        "MSACSR",
        "U.S. Census Bureau Monthly Supply of New Houses",
        "Ratio of houses for sale to houses sold, measured in months, for new single-family homes in the United States. Monthly, seasonally adjusted.",
        "market-signals",
        "monthly",
        "U.S. Census Bureau",
        "https://www.census.gov/construction/nrs/"
    ),
    dataset_jsonld(
        "EXHOSLUSM495S",
        "National Association of Realtors Existing Home Sales",
        "Seasonally adjusted annualized rate of existing single-family, townhome, condo, and co-op home sales in the United States, in thousands of units. Monthly.",
        "market-signals",
        "monthly",
        "National Association of Realtors",
        "https://www.nar.realtor/research-and-statistics/housing-statistics/existing-home-sales"
    ),
    dataset_jsonld(
        "FIXHAI",
        "National Association of Realtors Housing Affordability Composite Index",
        "Ratio of median family income to qualifying income for a conventional 30-year fixed mortgage on a median-priced existing single-family home with a 20% down payment. 100 = exact qualification. Monthly.",
        "market-signals",
        "monthly",
        "National Association of Realtors",
        "https://www.nar.realtor/research-and-statistics/housing-statistics/housing-affordability-index"
    ),
    dataset_jsonld(
        "UNRATE",
        "U.S. Bureau of Labor Statistics Civilian Unemployment Rate",
        "Percentage of the civilian labor force that is unemployed and actively seeking work in the United States. Monthly, seasonally adjusted.",
        "market-signals",
        "monthly",
        "U.S. Bureau of Labor Statistics",
        "https://www.bls.gov/cps/"
    )
]


FAQ_JSONLD = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}
        } for q, a in FAQ_QUESTIONS
    ]
}

BREADCRUMB_JSONLD = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
        {"@type": "ListItem", "position": 2, "name": "California Home Prices", "item": "https://drozq.com/prices/"}
    ]
}


JSON_LD_BLOCKS = "\n".join(
    f'<script type="application/ld+json">{_json.dumps(obj, indent=2)}</script>'
    for obj in [PERSON_JSONLD, WEBPAGE_JSONLD] + DATASETS_JSONLD + [FAQ_JSONLD, BREADCRUMB_JSONLD]
)


# ---------------------------------------------------------------------------
# 13. Inline hydration script
# ---------------------------------------------------------------------------

PRICES_SCRIPT = r"""
<script>
(function(){
  var endpoint = '/api/prices';
  var dateFmt    = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  var monthFmt   = new Intl.DateTimeFormat('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' });
  var integerFmt = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
  var oneDecFmt  = new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var dollars    = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

  var tier1Keys = ['hpiLA','hpiSD','hpiCA'];
  var tier3Keys = ['supplyMonths','existingSales','affordIdx','unemployment'];
  var allKeys = tier1Keys.concat(tier3Keys);

  // Mortgage payment math: standard fixed-rate formula.
  function payment(P, annualRate, years) {
    var r = annualRate / 100 / 12;
    var n = years * 12;
    if (n <= 0) return 0;
    if (r === 0) return P / n;
    var f = Math.pow(1 + r, n);
    return P * (r * f) / (f - 1);
  }

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
      case 'thousands': return oneDecFmt.format(v / 1000) + 'M';
      case 'index':
      default:          return integerFmt.format(Math.round(v));
    }
  }

  function pickPrimaryDelta(s) {
    if (!s) return { text: '', cls: 'flat' };
    if (s.unit === '%') {
      var d = s.delta;
      if (d == null || !isFinite(d)) return { text: 'No prior data', cls: 'flat' };
      var unitLbl = (s.cadence === 'monthly') ? 'pp vs. prior month' :
                    (s.cadence === 'weekly')  ? 'pp vs. prior week'  :
                    (s.cadence === 'daily')   ? 'pp vs. prior day'   : 'pp vs. prior';
      if (d === 0) return { text: 'Flat ' + unitLbl.replace('pp ', ''), cls: 'flat' };
      var sign = d > 0 ? '+' : '';
      return { text: sign + d.toFixed(2) + ' ' + unitLbl, cls: d > 0 ? 'up' : 'down' };
    }
    var p = s.deltaPct;
    if (p == null || !isFinite(p)) return { text: 'No prior data', cls: 'flat' };
    var lbl = (s.cadence === 'quarterly') ? 'vs. prior quarter' :
              (s.cadence === 'monthly')   ? 'vs. prior month'   :
              (s.cadence === 'weekly')    ? 'vs. prior week'    : 'vs. prior';
    if (p === 0) return { text: 'Flat ' + lbl, cls: 'flat' };
    var sign2 = p > 0 ? '+' : '';
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
    // Sparkline shows ~1 year (or the most recent 1y slice of the longer
    // window we pull for CAGR). Tail of the array since history is ascending.
    var slice = values.slice(Math.max(0, values.length - 60));
    var min = Math.min.apply(null, slice);
    var max = Math.max.apply(null, slice);
    var range = (max - min) || 1;
    var n = slice.length;
    var pts = slice.map(function(v, i){
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

    if (valEl) valEl.textContent = fmtValue(s);
    if (sparkEl) renderSparkline(sparkEl, s.history || []);

    var d = pickPrimaryDelta(s);
    if (deltaEl) { deltaEl.textContent = d.text; deltaEl.className = 'drozq-data-card__delta drozq-data-card__delta--' + d.cls; }
    var y = pickYoYDelta(s);
    if (yoyEl)   { yoyEl.textContent   = y.text; yoyEl.className   = 'drozq-data-card__delta drozq-data-card__delta--' + y.cls; }

    if (dateEl) {
      dateEl.textContent = s.latest.date ? 'As of ' + fmtDate(s.latest.date, s.cadence) : '';
    }
  }

  function renderAppreciationTable(series) {
    // Only the "Today" column is live; the 5y/10y/CAGR columns are
    // hardcoded snapshots in the HTML and don't need hydration.
    tier1Keys.forEach(function(key){
      var s = series[key];
      var todayEl = document.querySelector('[data-app-today="' + key + '"]');
      if (!todayEl) return;
      if (!s || !s.latest || s.latest.value == null) {
        todayEl.textContent = 'n/a';
        return;
      }
      todayEl.textContent = integerFmt.format(Math.round(s.latest.value));
    });
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
    renderAppreciationTable(series);
    setMeta('prices-tier1-meta', payload);
    setMeta('prices-tier3-meta', payload);
  }

  function fail(err) {
    allKeys.forEach(function(k){ renderCard(k, null); });
    render({ error: (err && err.message) || 'fetch_failed' });
  }

  // ---- Calculator (ported from /rates/) ----
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
    calcRecompute();
  }

  function calcRecompute() {
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
        calcRecompute();
      });
    });
    calcTermEls.forEach(function(el){
      el.addEventListener('click', function(){
        var t = parseInt(el.getAttribute('data-calc-term'), 10) || 30;
        setCalcTerm(t, true);
      });
    });
    calcRecompute();
  }

  function fetchRatesForCalc() {
    // Separate fetch (the /api/prices payload doesn't carry mortgage rates).
    // If this fails, the calculator keeps its 6.50% default and the visitor
    // can still adjust manually.
    return fetch('/api/rates', { headers: { 'accept': 'application/json' } })
      .then(function(r){ if (!r.ok) throw new Error('rates_unavailable'); return r.json(); })
      .then(function(p){
        var series = (p && p.series) || {};
        var r30 = series.rate30y && series.rate30y.latest && series.rate30y.latest.value;
        var r15 = series.rate15y && series.rate15y.latest && series.rate15y.latest.value;
        apiRate30 = r30 != null ? r30 : null;
        apiRate15 = r15 != null ? r15 : null;
        if (!userTouchedRate && calcRateEl && apiRate30 != null) {
          var pick = (currentTerm === 15 && apiRate15 != null ? apiRate15 : apiRate30);
          calcRateEl.value = pick.toFixed(2);
          calcRecompute();
        }
      })
      .catch(function(){ /* keep the 6.50% default */ });
  }

  function go() {
    wireCalc();
    fetchRatesForCalc();
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
    + TIER3_SECTION              # Market Signals: lead the page with the four
                                 #   national signals that move prices
    + TIER1_SECTION              # California home price indices
    + APPRECIATION_TABLE_SECTION # 5y/10y CAGR snapshot
    + EXPLAINERS_SECTION
    + RATES_CROSSLINK
    + MID_TABS
    + FAQ_SECTION
    + METHODOLOGY_SECTION
    + CROSSLINKS_SECTION
    + CALCULATOR_SECTION         # "Run your numbers" -- mortgage calculator,
                                 #   pre-filled from /api/rates. Sits right
                                 #   above the closing CTA so the journey
                                 #   reads as math -> talk to me.
    + CLOSING_CTA
    + JSON_LD_BLOCKS
    + PRICES_SCRIPT
)


if __name__ == "__main__":
    scaffold_page(
        target="prices/index.html",
        title="California Home Prices and Market Signals -- Live from FRED | Joshua Guerrero, Real Brokerage",
        description="Live LA and San Diego Case-Shiller home price indices, FHFA California statewide HPI, plus the supply, sales, affordability, and employment signals that move them. Pulled from the Federal Reserve, refreshed hourly. Includes 5- and 10-year CAGR per market.",
        canonical="/prices/",
        main_body_html=MAIN_BODY,
        og_title="California Home Prices and Market Signals -- Live from FRED",
        og_description="LA + San Diego Case-Shiller, FHFA California statewide HPI, plus months of supply, existing sales, affordability, and unemployment. Includes 5y + 10y CAGR per market. Refreshed automatically.",
    )
