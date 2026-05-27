"""Migrate /rates/ to the homepage template scaffold.

The /rates/ page is the first auto-refreshing data product on the site.
The page renders four mortgage-finance benchmarks:
  - 30-year fixed mortgage (Freddie Mac PMMS, FRED series MORTGAGE30US)
  - 15-year fixed mortgage (Freddie Mac PMMS, FRED series MORTGAGE15US)
  - 10-year Treasury yield (FRED series DGS10) -- leading indicator for
    mortgage rates
  - Federal funds rate (FRED series FEDFUNDS)

Server side: /functions/api/rates.js proxies FRED, edge-caches 1h, returns
JSON {ok, series, lastUpdated, fetchedAt, source}. Requires the
FRED_API_KEY env var in Cloudflare Pages settings.

Client side: this page ships static placeholder cards (em-dashes) and a
small inline <script> that fetches /api/rates on DOMContentLoaded and
fills in the live numbers + per-card observation dates + a single
"last updated" line below the grid.

First-pass scope: functionality only. Hero + 4 cards + timestamp +
funnel CTA per the template. No extra commentary sections, no JSON-LD
Dataset block, no crosslinks. Iterate from here.
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
    <img src="/media/images/crystal-cove.webp" alt="Southern California coastline" width="1280" height="640" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.62)"></div>
  </div>

  <section aria-labelledby="rates-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <p class="op_0.9 c_#fff ls_2px fs_11px md:fs_12px fw_700 mb_8px" style="text-transform:uppercase">Live Rates &middot; Auto-refreshed from FRED</p>
      <h1 id="rates-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">Today's mortgage and benchmark rates.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">Pulled live from the Federal Reserve Economic Data (FRED). The four numbers that frame every offer, refinance, and pricing conversation in Southern California.</p>
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


RATES_STYLE = """
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
.drozq-rate-card__delta {
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  font-variant-numeric: tabular-nums;
  color: #757575;
}
.drozq-rate-card__delta--up   { color: #b81d22; }
.drozq-rate-card__delta--down { color: #0a801f; }
.drozq-rate-card__delta--flat { color: #757575; }
.drozq-rate-card__date {
  font-size: 0.8rem;
  color: #757575;
  margin: 0;
}
.drozq-rates-meta {
  text-align: center;
  color: #757575;
  font-size: 0.875rem;
  margin: 24px 0 0;
}
.drozq-rates-meta strong { color: #2b2b2b; font-weight: 700; }
</style>
"""


def rate_card(key: str, label: str, cadence_hint: str) -> str:
    return f"""
      <div class="drozq-rate-card" data-rate-card="{key}">
        <p class="drozq-rate-card__label">{label}</p>
        <span class="drozq-rate-card__value" data-rate-value="{key}">&hellip;</span>
        <span class="drozq-rate-card__delta drozq-rate-card__delta--flat" data-rate-delta="{key}">Loading {cadence_hint} data&hellip;</span>
        <p class="drozq-rate-card__date" data-rate-date="{key}">&nbsp;</p>
      </div>"""


RATES_SECTION = f"""
<section aria-labelledby="rates-title" class="bg_#fff py_48px md:py_64px lg:py_72px">
  <div class="max-w_1035px m_0_auto pl_32px md:pl_24px pr_32px md:pr_24px">

    <div class="ta_center mb_32px md:mb_40px max-w_720px mx_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">The Rates</p>
      <h2 id="rates-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Mortgage and benchmark rates, refreshed automatically.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">Each card shows the latest weekly (mortgage) or daily (Treasury) reading from FRED, with the change since the prior observation. The page refreshes the moment a new FRED release lands.</p>
    </div>

    <div class="drozq-rates-grid" id="drozq-rates-grid">
{rate_card("rate30y",     "30-year fixed mortgage",  "weekly")}
{rate_card("rate15y",     "15-year fixed mortgage",  "weekly")}
{rate_card("treasury10y", "10-year Treasury yield",  "daily")}
{rate_card("fedFunds",    "Federal funds rate",      "monthly")}
    </div>

    <p class="drozq-rates-meta" id="drozq-rates-meta">
      <strong>Loading&hellip;</strong>
    </p>
  </div>
</section>
"""


RATES_SCRIPT = """
<script>
(function(){
  var endpoint = '/api/rates';
  var dateFmt = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });

  function setText(selector, text) {
    document.querySelectorAll(selector).forEach(function(el){ el.textContent = text; });
  }

  function fmtRate(v) {
    if (v == null || !isFinite(v)) return '...';
    return v.toFixed(2) + '%';
  }

  function fmtDelta(d) {
    if (d == null || !isFinite(d)) return { text: 'No change data', cls: 'flat' };
    if (d === 0) return { text: 'No change vs. prior', cls: 'flat' };
    var sign = d > 0 ? '+' : '';
    return {
      text: sign + d.toFixed(2) + ' vs. prior',
      cls: d > 0 ? 'up' : 'down'
    };
  }

  function fmtDate(iso) {
    if (!iso) return '';
    var d = new Date(iso + 'T00:00:00Z');
    if (isNaN(d.getTime())) return '';
    return dateFmt.format(d);
  }

  function render(payload) {
    var series = (payload && payload.series) || {};
    Object.keys(series).forEach(function(key){
      var s = series[key];
      var valEl   = document.querySelector('[data-rate-value="' + key + '"]');
      var deltaEl = document.querySelector('[data-rate-delta="' + key + '"]');
      var dateEl  = document.querySelector('[data-rate-date="' + key + '"]');
      if (!s || !s.latest) {
        if (valEl) valEl.textContent = '...';
        if (deltaEl) {
          deltaEl.textContent = 'Data unavailable';
          deltaEl.className = 'drozq-rate-card__delta drozq-rate-card__delta--flat';
        }
        if (dateEl) dateEl.innerHTML = '&nbsp;';
        return;
      }
      if (valEl) valEl.textContent = fmtRate(s.latest.value);
      if (deltaEl) {
        var d = fmtDelta(s.delta);
        deltaEl.textContent = d.text;
        deltaEl.className = 'drozq-rate-card__delta drozq-rate-card__delta--' + d.cls;
      }
      if (dateEl) {
        dateEl.textContent = s.latest.date ? 'As of ' + fmtDate(s.latest.date) : '';
      }
    });

    var meta = document.getElementById('drozq-rates-meta');
    if (!meta) return;
    if (payload && payload.lastUpdated) {
      meta.innerHTML = 'Last update: <strong>' + fmtDate(payload.lastUpdated) + '</strong> &middot; Source: Federal Reserve Economic Data (FRED), St. Louis Fed';
    } else if (payload && payload.error) {
      meta.innerHTML = '<strong>Data temporarily unavailable.</strong> Refresh the page in a few minutes.';
    } else {
      meta.innerHTML = 'Source: Federal Reserve Economic Data (FRED), St. Louis Fed';
    }
  }

  function fail(err) {
    ['rate30y','rate15y','treasury10y','fedFunds'].forEach(function(key){
      var valEl   = document.querySelector('[data-rate-value="' + key + '"]');
      var deltaEl = document.querySelector('[data-rate-delta="' + key + '"]');
      var dateEl  = document.querySelector('[data-rate-date="' + key + '"]');
      if (valEl) valEl.textContent = '...';
      if (deltaEl) {
        deltaEl.textContent = 'Data unavailable';
        deltaEl.className = 'drozq-rate-card__delta drozq-rate-card__delta--flat';
      }
      if (dateEl) dateEl.innerHTML = '&nbsp;';
    });
    render({ error: (err && err.message) || 'fetch_failed' });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', go);
  } else { go(); }

  function go() {
    fetch(endpoint, { headers: { 'accept': 'application/json' }})
      .then(function(r){ if (!r.ok && r.status !== 200) return r.json().then(function(j){ throw new Error(j.error || ('http_' + r.status)); }); return r.json(); })
      .then(render)
      .catch(fail);
  }
})();
</script>
"""


MID_TABS = f"""
<section class="d_block pt_48px lg:pt_64px pb_72px xs:pb_48px lg:pb_64px ls_0.01em h_auto bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">

    <div class="ta_center">
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px fs_32px ls_1px pb_16px ta_center">What today's rate means for your offer.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px max-w_640px m_0_auto pb_8px">Rates frame the math, not the decision. The decision is the home, the block, and the timing. Pick a side and I'll run the read.</p>
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


CLOSING_CTA = f"""
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Your home, your number</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Rates are a number. Your home is a strategy.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Whether you're refinancing math or running a sell-then-buy, the conversation starts with your specific home. Free CMA delivered within 24 hours.</p>

      <div id="rates-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">{landing_form_pill("Enter your address")}</div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""


MAIN_BODY = (
    HERO
    + RATES_STYLE
    + RATES_SECTION
    + RATES_SCRIPT
    + MID_TABS
    + CLOSING_CTA
)


if __name__ == "__main__":
    scaffold_page(
        target="rates/index.html",
        title="Today's Mortgage Rates | Joshua Guerrero, Real Brokerage",
        description="Live 30-year and 15-year mortgage rates, 10-year Treasury yield, and Fed funds rate, refreshed automatically from FRED. The four numbers that frame every Southern California offer and refinance.",
        canonical="/rates/",
        main_body_html=MAIN_BODY,
        og_title="Today's Mortgage Rates | Joshua Guerrero",
        og_description="Live mortgage and benchmark rates, refreshed automatically from the Federal Reserve. 30-year fixed, 15-year fixed, 10-year Treasury, Fed funds.",
    )
