"""Build /homes/ : the live CRMLS home search (IDX, step 1 of notes/idx/idx-access-plan.md).

Scaffolded from buyers/index.html (the buy-side hub: Variant B fixed-header
chrome, the Panda patch, the funnel markers, the footer, the mobile-nav
script, and a closing CTA already wired to the BUY funnel). This script
replaces:

  - <title> / meta description / canonical / og:* / twitter:*
  - the <style id="drozq-page-chrome"> block
  - everything between <main ...> and </main>
  - strips the buyers-only <script id="bcc-js"> after the nav script

The search itself is the CRMLS Matrix IDX frame Joshua configured in Matrix
(Settings > IDX Configuration > "drozq.com Homes", IDX id 131c38ac, Map Search
/ Portal form, sign-up form on, sign-up message in his voice). It is the ONE
sanctioned third-party iframe on the site until the Trestle RESO feed lands
and the native search replaces it (plan step 3). Rule 19.2 of the CRMLS Rules
& Policies drives the strip under the frame: source MLS + refresh, brokerage +
agent identification, the personal non-commercial use notice, and a
corrections channel.

Run:  python scripts/build_homes.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "buyers" / "index.html"
TARGET = ROOT / "homes" / "index.html"

IDX_SRC = "https://matrix.crmls.org/Matrix/public/IDX.aspx?idx=131c38ac"

TITLE = "Homes for Sale in Orange County and LA | Live MLS Search"
DESCRIPTION = (
    "Every home for sale in Orange County and Los Angeles, live from the MLS: "
    "search by city, price, beds, and map, then get your first showing within 24 hours."
)
CANONICAL = "https://drozq.com/homes/"
OG_TITLE = "Homes for sale, live from the MLS | Joshua Guerrero"
OG_DESCRIPTION = (
    "Search every Orange County and Los Angeles listing the day it hits the MLS, "
    "then tell me which ones you want to see."
)

# ---------------------------------------------------------------------------
# Page chrome: Variant B fixed header + the warm masthead band + the frame
# and card styles (scoped .hm-* so nothing rides on an uncompiled Panda
# utility, the /process/ step-card lesson in TEMPLATE.md section 14).
CHROME = (
    '<style id="drozq-page-chrome">'
    '@layer base{#__next>header{position:fixed !important;top:0;left:0;right:0}}'
    '#__next>header{box-shadow:0 1px 5px rgba(0,0,0,.11)}'
    'body{padding-top:48px}@media(min-width:768px){body{padding-top:64px}}'
    'section[aria-labelledby=homes-hero-title]{background:#f2f0ef;padding-top:56px;padding-bottom:40px}'
    '@media(min-width:768px){section[aria-labelledby=homes-hero-title]{padding-top:84px;padding-bottom:56px}}'
    '[id]{scroll-margin-top:80px}'
    '.hm-wrap{max-width:1180px;margin:0 auto;padding:0 16px;box-sizing:border-box}'
    '.hm-how{max-width:720px;margin:0 auto 16px;text-align:center;color:#3f4650;font-size:15px;line-height:24px}'
    '.hm-how strong{color:#1a1816}'
    '.hm-frame{position:relative;width:100%;height:640px;border:1px solid #e5e5e5;border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.04)}'
    '.hm-frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:block}'
    '@media(min-width:768px){.hm-frame{height:760px}}'
    '@media(min-width:1024px){.hm-frame{height:820px}}'
    '.hm-legal{max-width:960px;margin:20px auto 0;color:#3f4650;font-size:13px;line-height:20px;text-align:center}'
    '.hm-legal p{margin:0 0 6px}'
    '.hm-legal a{color:#d92228;font-weight:700}'
    '.hm-steps{display:grid;grid-template-columns:1fr;gap:16px;max-width:1035px;margin:0 auto}'
    '.hm-step{background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:24px}'
    '.hm-step .hm-n{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:9999px;background:#fbe9ea;color:#d92228;font-weight:700;margin-bottom:12px}'
    '.hm-step h3{color:#1a1816;font-size:19px;line-height:26px;font-weight:700;margin:0 0 8px}'
    '.hm-step p{color:#3f4650;font-size:15px;line-height:23px;margin:0}'
    '@media(min-width:768px){.hm-steps{grid-template-columns:1fr 1fr 1fr;gap:20px}}'
    '</style>'
)

HERO = """
<div class="pos_relative ov_hidden">
  <section aria-labelledby="homes-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="homes-hero-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px mb_16px">Every home for sale. Live from the MLS.</h1>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px max-w_640px m_0_auto">Orange County and Los Angeles, every listing the day it goes live, and your first showing within 24 hours.</p>
    </div>
  </section>
</div>
"""

SEARCH = f"""
<section id="search" aria-label="Live MLS home search" class="bg_#fff py_48px md:py_64px">
  <div class="hm-wrap">
    <p class="hm-how"><strong>Type a city or neighborhood, set your filters, then zoom in.</strong> Tap any home for photos, price history, and the numbers; save the ones you like and I will set up the showings.</p>
    <div class="hm-frame">
      <iframe src="{IDX_SRC}" title="Live CRMLS home search, displayed by Joshua Guerrero, Real Brokerage" allow="geolocation" referrerpolicy="strict-origin-when-cross-origin"></iframe>
    </div>
    <div class="hm-legal">
      <p>Listing data from the California Regional Multiple Listing Service (CRMLS), updated continuously as listings change. Each listing shows its listing agent and listing office. Displayed by Joshua Guerrero, Real Brokerage, California DRE #02267255.</p>
      <p>This information is for consumers' personal, non-commercial use and may not be used for any purpose other than to identify prospective properties consumers may be interested in purchasing. Information deemed reliable but not guaranteed. See something wrong on a listing? <a href="mailto:josh@drozq.com">josh@drozq.com</a> or <a href="tel:9494385948">(949) 438-5948</a>.</p>
    </div>
  </div>
</section>
"""

NEXT = """
<section aria-labelledby="homes-next-title" class="bg-c_#f2f0ef py_48px md:py_64px">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_720px m_0_auto mb_32px md:mb_40px">
      <h2 id="homes-next-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px mb_12px">Found one? Here is what happens next.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px m_0">One text from you and the search stops being a hobby.</p>
    </div>
    <div class="hm-steps">
      <div class="hm-step"><span class="hm-n" aria-hidden="true">1</span><h3>Showing within 24 hours</h3><p>Send me the address. I confirm with the listing agent and you are standing in it the next day.</p></div>
      <div class="hm-step"><span class="hm-n" aria-hidden="true">2</span><h3>The real number before you fall for it</h3><p>Cash to close and the true monthly on that exact home, with today's rate, before we write anything. <a href="/buyers/#closing-costs" class="c_#d92228 fw_700">Run it now.</a></p></div>
      <div class="hm-step"><span class="hm-n" aria-hidden="true">3</span><h3>An offer built to win</h3><p>Tight contingencies, clean appraisal language, and seller credits used where they move price. $58,250 negotiated for clients across my first three closings.</p></div>
    </div>
    <div class="ta_center mt_32px">
      <button type="button" class="hub-cta" onclick="window.openFunnel('','buy')">Tell me what you want</button>
      <p class="c_#3f4650 fs_13px md:fs_14px lh_20px mt_8px">Budget, area, and timing. I bring the homes that actually fit, and every call is returned in 15 minutes, 7 days a week.</p>
    </div>
  </div>
</section>
<style id="hub-css">.hub-cta{background:#d92228;color:#fff;border:none;cursor:pointer;border-radius:9999px;font-weight:700;font-size:16px;height:52px;padding:0 30px;font-family:inherit}.hub-cta:hover{background:#a92e2a}</style>
"""

XREF_CSS = (
    '<style id="drozq-xref-css">.xr-band{padding:48px 0}.xr--warm{background:#f2f0ef}.xr--white{background:#fff}'
    '.xr-wrap{max-width:1035px;margin:0 auto;padding:0 32px;box-sizing:border-box}.xr-head{max-width:720px;margin:0 auto 28px;text-align:center}'
    '.xr-head h2{font-weight:800;opacity:.87;color:#2b2b2b;font-size:26px;line-height:34px;letter-spacing:.3px;margin:0 0 10px}'
    '.xr-head p{color:#3f4650;font-size:16px;line-height:26px;margin:0}.xr-grid{display:grid;grid-template-columns:1fr;gap:16px}'
    '.xr-card{display:block;background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:24px;text-decoration:none;color:inherit;'
    'transition:border-color .15s ease,transform .15s ease,box-shadow .15s ease;text-align:left;box-sizing:border-box}'
    '.xr--white .xr-card{background:#fbf8f4;border-color:#ece8e2}.xr-card:hover{border-color:#d92228;transform:translateY(-2px);box-shadow:0 8px 20px rgba(26,24,22,.08)}'
    '.xr-eyebrow{color:#d92228;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 8px}'
    '.xr-card h3{color:#1a1816;font-size:19px;line-height:26px;font-weight:700;margin:0 0 8px}.xr-card p{color:#3f4650;font-size:15px;line-height:23px;margin:0 0 10px}'
    '.xr-go{color:#d92228;font-weight:700;font-size:14px}.xr-a{color:#d92228;font-weight:700;text-decoration:underline;text-underline-offset:2px}'
    '@media (min-width:768px){.xr-band{padding:64px 0}.xr-head h2{font-size:32px;line-height:40px}.xr-grid--2{grid-template-columns:1fr 1fr;gap:20px}.xr-grid--3{grid-template-columns:1fr 1fr 1fr;gap:20px}}</style>'
)

XREF = """
<section class="xr-band xr--white"><div class="xr-wrap"><div class="xr-head"><h2>Know the market before you write.</h2><p>The numbers behind every listing on the map.</p></div><div class="xr-grid xr-grid--3">
<a class="xr-card" href="/buyers/#closing-costs"><p class="xr-eyebrow">Cash to close</p><h3>The closing-cost estimator</h3><p>Today's 30-year feeds it live: lender fees, escrow, title, and your all-in monthly.</p><span class="xr-go">Run it &rarr;</span></a>
<a class="xr-card" href="/rates/"><p class="xr-eyebrow">Live data</p><h3>Today's mortgage rates</h3><p>30-year, 15-year, jumbo, FHA, and VA, refreshed every business day.</p><span class="xr-go">Open &rarr;</span></a>
<a class="xr-card" href="/sold/"><p class="xr-eyebrow">Proof</p><h3>The sold board</h3><p>3 for 3 closed early, $58,250 negotiated for clients. Numbers left in.</p><span class="xr-go">See the board &rarr;</span></a>
</div></div></section>
"""

CLOSING_HEAD = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">Ready when you are</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">Tell me where you want to live.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">City, neighborhood, or ZIP. I come back within 15 minutes with the homes that fit and the first showing on the calendar.</p>

      <div id="homes-closing-cta" role="tabpanel" aria-labelledby="tab-buy" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">
"""

CLOSING_TAIL = """
        </div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""

WEBPAGE_LD = (
    '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"Homes for Sale",'
    '"url":"https://drozq.com/homes/","description":"Every home for sale in Orange County and Los Angeles, live from the MLS, '
    'displayed by Joshua Guerrero, Real Brokerage.","isPartOf":{"@type":"WebSite","@id":"https://drozq.com/#website"}}</script>'
)
BREADCRUMB_LD = (
    '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Home","item":"https://drozq.com/"},'
    '{"@type":"ListItem","position":2,"name":"For Buyers","item":"https://drozq.com/buyers/"},'
    '{"@type":"ListItem","position":3,"name":"Homes for Sale","item":"https://drozq.com/homes/"}]}</script>'
)


def main() -> int:
    src = BASE.read_text(encoding="utf-8")

    def sub_once(pattern, repl, text, what):
        new, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"build_homes: expected exactly 1 {what}, got {n}")
        return new

    # --- the buy-mode closing pill, lifted verbatim from /buyers/ and relabeled
    i = src.find('id="buyers-closing-cta"')
    j = src.find("</form>", i)
    if i < 0 or j < 0:
        raise SystemExit("build_homes: could not find the /buyers/ closing form to reuse")
    form = src[src.find("<form", i):j + len("</form>")]
    if form.count("Run my Valuation") != 1:
        raise SystemExit("build_homes: closing form label drifted; check /buyers/")
    form = form.replace("Run my Valuation", "See Homes")

    # --- head ---------------------------------------------------------------
    src = sub_once(r"<title>[^<]*</title>", f"<title>{TITLE}</title>", src, "<title>")
    src = sub_once(r'<meta name="description" content="[^"]*">',
                   f'<meta name="description" content="{DESCRIPTION}">', src, "meta description")
    src = sub_once(r'<link rel="canonical" href="[^"]*">',
                   f'<link rel="canonical" href="{CANONICAL}">', src, "canonical")
    src = sub_once(r'<meta property="og:url" content="[^"]*">',
                   f'<meta property="og:url" content="{CANONICAL}">', src, "og:url")
    src = sub_once(r'<meta property="og:title" content="[^"]*">',
                   f'<meta property="og:title" content="{OG_TITLE}">', src, "og:title")
    src = sub_once(r'<meta property="og:description" content="[^"]*">',
                   f'<meta property="og:description" content="{OG_DESCRIPTION}">', src, "og:description")
    src = sub_once(r'<meta name="twitter:title" content="[^"]*">',
                   f'<meta name="twitter:title" content="{OG_TITLE}">', src, "twitter:title")
    src = sub_once(r'<meta name="twitter:description" content="[^"]*">',
                   f'<meta name="twitter:description" content="{OG_DESCRIPTION}">', src, "twitter:description")

    # --- page chrome --------------------------------------------------------
    src = sub_once(r'<style id="drozq-page-chrome">.*?</style>', CHROME, src, "page chrome block")

    # --- drop the buyers-only estimator script -------------------------------
    src = sub_once(r'<script id="bcc-js">.*?</script>', "", src, "bcc-js script")

    # --- main body ----------------------------------------------------------
    main_open = src.find("<main ")
    if main_open < 0:
        raise SystemExit("build_homes: could not find <main> in the base page")
    main_open_end = src.find(">", main_open) + 1
    main_close = src.find("</main>", main_open_end)
    if main_close < 0:
        raise SystemExit("build_homes: could not find </main> in the base page")

    body = (
        HERO + SEARCH + NEXT + XREF_CSS + XREF
        + CLOSING_HEAD + form + CLOSING_TAIL
        + WEBPAGE_LD + BREADCRUMB_LD
    )
    out = src[:main_open_end] + "\n" + body + src[main_close:]

    # --- guardrails ---------------------------------------------------------
    if "—" in body:
        raise SystemExit("build_homes: em dash (U+2014) found in the page body. Banned.")
    for marker in ("DROZQ_FUNNEL_HTML_BEGIN", "DROZQ_FUNNEL_HTML_END",
                   "DROZQ_FUNNEL_JS_BEGIN", "DROZQ_FUNNEL_JS_END",
                   "DROZQ_HEADER_BEGIN", "DROZQ_HEADER_END",
                   "DROZQ_FOOTER_BEGIN", "DROZQ_FOOTER_END",
                   "DROZQ_NAV_JS_BEGIN", "DROZQ_NAV_JS_END",
                   "DROZQ_HEADER_JS_BEGIN", "DROZQ_HEADER_JS_END"):
        if out.count(marker) != 1:
            raise SystemExit(f"build_homes: marker {marker} count is {out.count(marker)}, expected 1")
    if out.count("bcc-") != 0:
        raise SystemExit("build_homes: buyers estimator residue found")
    if out.count(IDX_SRC) != 1:
        raise SystemExit("build_homes: IDX frame src count is not 1")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(out, encoding="utf-8")
    print(f"Built: homes/index.html ({len(out):,} chars, body {len(body):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
