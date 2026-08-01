"""Build /net-sheet/ : the seller net sheet that starts with the county record.

Scaffolded from short-sale/index.html (a current AI-answer page already carrying
the Variant B fixed-header chrome block, the Panda patch, the funnel markers,
the footer, and the mobile-nav script). This script replaces:

  - <title> / meta description / canonical / og:* / twitter:*
  - the <style id="drozq-page-chrome"> block (warm tool band, print rules)
  - everything between <main ...> and </main>

Everything else (head boilerplate, GTM, FUB pixel, Panda soup + patch, funnel
markers, footer, mobile nav) rides along untouched, so the page is immediately
registerable in funnels.json.

Run:  python scripts/build_net_sheet.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "short-sale" / "index.html"
TARGET = ROOT / "net-sheet" / "index.html"

TITLE = "Seller Net Sheet Calculator: Your Real Net in California | Joshua Guerrero"
DESCRIPTION = (
    "A California seller net sheet built on your county record: real tax history, Mello-Roos, "
    "escrow proration, and a payoff solved from your monthly payment."
)
CANONICAL = "https://drozq.com/net-sheet/"
OG_TITLE = "Seller Net Sheet Calculator: your real net, to the dollar"
OG_DESCRIPTION = (
    "Pull your county tax record, back into your payoff from your monthly payment, and watch "
    "every California closing line resolve to one number."
)

# ---------------------------------------------------------------------------
# Page chrome: Variant B fixed header + the warm tool band + print rules.
#
# The print block hides the header from INSIDE @layer base: the compiled Panda
# base layer ships `header { display: block !important }`, and layered
# importants beat unlayered ones, so an unlayered print `display:none` loses
# (the /value/ print-stylesheet lesson, TEMPLATE.md section 4).
CHROME = (
    '<style id="drozq-page-chrome">'
    '@layer base{#__next>header{position:fixed !important;top:0;left:0;right:0}}'
    '#__next>header{box-shadow:0 1px 5px rgba(0,0,0,.11)}'
    'body{padding-top:48px}@media(min-width:768px){body{padding-top:64px}}'
    'section[aria-labelledby=ns-hero-title]{background:#f2f0ef;padding-top:56px;padding-bottom:28px}'
    'section[aria-label="Seller net sheet calculator"]{background:#f2f0ef;padding-bottom:56px}'
    '@media(min-width:768px){section[aria-labelledby=ns-hero-title]{padding-top:84px;padding-bottom:36px}}'
    'main.ov_hidden{overflow:visible}'
    '[id]{scroll-margin-top:80px}'
    '@media print{'
    '@layer base{#__next>header{display:none !important}}'
    'body{padding-top:0}'
    '#footer,#drozq-sticky-cta,.ns-hide-print,.xr-band{display:none !important}'
    '.ns-card,.ns-panel{break-inside:avoid;box-shadow:none !important}'
    '.ns-out{position:static !important}'
    '}'
    "</style>"
)

# ---------------------------------------------------------------------------
# Hero: headline + one short subhead. No opener eyebrow (TEMPLATE.md section 4).
HERO = """
<div class="pos_relative ov_hidden">
  <section aria-labelledby="ns-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="ns-hero-title" class="fw_800 op_0.87 c_#2b2b2b lh_36px md:lh_44px fs_28px md:fs_36px ls_0.3px mb_16px">Know your net before you list.</h1>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px max-w_640px m_0_auto">Your county tax record, your real payoff, and every closing line, resolved to one number.</p>
    </div>
  </section>
</div>
"""

# ---------------------------------------------------------------------------
# Scoped CSS. Every color resolves to a TEMPLATE.md section 1 token or an
# established /index.html value. Nothing here relies on the Panda soup.
CSS = """<style id="ns-css">
.ns-wrap{max-width:1035px;margin:0 auto;padding:0 20px;box-sizing:border-box}
.ns-narrow{max-width:760px;margin:0 auto;padding:0 32px;box-sizing:border-box}
.ns-h2{font-weight:800;opacity:.87;color:#2b2b2b;font-size:26px;line-height:34px;letter-spacing:.3px;margin:0 0 12px;text-align:center}
.ns-sub{color:#3f4650;font-size:16px;line-height:26px;margin:0 0 28px;text-align:center}
.ns-eyebrow{color:#d92228;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 8px}
.ns-a{color:#d92228;font-weight:700;text-decoration:underline;text-underline-offset:2px}

/* ---- step 1: the county lookup ------------------------------------------
   Its own bordered card with a red accent so the address reads as the required
   first action rather than decoration. The pill is a bespoke Places input, so
   it also carries its own copy of the "input-pill-flattens" pattern
   (TEMPLATE.md section 4): the pill supplies the rounded top, the dropdown
   supplies the rounded bottom, one seamless container. The WRAPPER has to
   flatten too, not just the input, or its rounded corner shows through under
   the square-topped dropdown. Below 480px the input is its own pill with the
   button stacked beneath, so the dropdown never opens across the button. */
.ns-step1{background:#fff;border:1px solid #e5e5e5;border-left:4px solid #d92228;border-radius:20px;padding:22px 20px;max-width:760px;margin:0 auto 18px;box-sizing:border-box}
.ns-step1 h2{color:#1a1816;font-size:22px;line-height:29px;font-weight:800;letter-spacing:.2px;margin:0 0 8px}
.ns-step1-sub{color:#3f4650;font-size:15px;line-height:23px;margin:0 0 18px}
.ns-step1-sub b{color:#1a1816;font-weight:700}
.ns-lookup{margin:0}
.ns-pill{display:flex;flex-direction:column;align-items:stretch;gap:10px;background:transparent;border-radius:0;overflow:visible}
.ns-pill input{border:none;outline:none;background:#fff;width:100%;height:56px;padding:0 20px;font-size:16px;font-family:inherit;color:#1a1816;border-radius:30px;box-shadow:0 1px 5px rgba(0,0,0,.11);box-sizing:border-box}
.ns-pill input::placeholder{color:#9a948c}
.ns-pill button{border:none;cursor:pointer;background:#d92228;color:#fff;font-family:inherit;font-weight:700;font-size:16px;height:52px;margin:0;border-radius:9999px}
.ns-pill button:hover{background:#a92e2a}
.ns-pill.is-pac-open input{border-radius:30px 30px 0 0}
.pac-container{border-radius:0 0 16px 16px}
.ns-lookup-note{color:#757575;font-size:13px;line-height:20px;margin:12px 0 0}
.ns-lookup-err{display:none;color:#d92228;font-size:14px;font-weight:700;margin:12px 0 0}
.ns-lookup-err.is-shown{display:block}
/* Accuracy strip: says out loud that everything below is generic until the
   record is pulled, then flips to name the address it was built on. */
.ns-acc{display:flex;align-items:flex-start;gap:10px;max-width:760px;margin:0 auto;padding:13px 16px;border-radius:14px;background:#fbe9ea;font-size:14px;line-height:21px;box-sizing:border-box}
.ns-acc.is-ok{background:#e7f5e9}
.ns-acc i{font-style:normal;flex-shrink:0;color:#b81d22;font-size:15px;line-height:21px}
.ns-acc.is-ok i{color:#0a801f}
.ns-acc b{color:#b81d22;font-weight:800}
.ns-acc.is-ok b{color:#0a801f}
.ns-acc span{color:#3f4650}
@media (min-width:480px){
  .ns-pill{flex-direction:row;align-items:center;gap:0;background:#fff;border-radius:30px;box-shadow:0 1px 5px rgba(0,0,0,.11);height:62px}
  .ns-pill input{background:transparent;box-shadow:none;height:62px;border-radius:30px 0 0 30px}
  .ns-pill button{width:auto;padding:0 26px;margin:0 4px 0 0;flex-shrink:0}
  /* The dropdown spans the input only and stops before the button, so the
     wrapper AND the input flatten their bottom-LEFT corner. Button stays a pill. */
  .ns-pill.is-pac-open{border-bottom-left-radius:0}
  .ns-pill.is-pac-open input{border-radius:30px 0 0 0}
}
@media (min-width:768px){
  .ns-step1{padding:30px 32px}
  .ns-step1 h2{font-size:26px;line-height:34px}
}

/* ---- the record (revealed after a lookup) ---- */
.ns-record{display:none;margin:28px auto 0;max-width:1035px}
.ns-record.is-on{display:block}
.ns-rec-grid{display:grid;grid-template-columns:1fr;gap:16px}
.ns-card{background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:20px}
.ns-card h3{color:#1a1816;font-size:16px;line-height:23px;font-weight:700;margin:0 0 12px}
.ns-kv{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid #ece8e2;font-size:14px;line-height:20px}
.ns-kv:last-child{border-bottom:none}
.ns-kv span{color:#3f4650}
.ns-kv b{color:#1a1816;font-weight:700;text-align:right}
.ns-flag{border-left:4px solid #d92228;background:#fbf8f4;border:1px solid #ece8e2;border-left:4px solid #d92228;border-radius:14px;padding:18px 20px}
.ns-flag.ns-flag--clear{border-left-color:#0a801f}
.ns-flag p{margin:0;color:#3f4650;font-size:14px;line-height:22px}
.ns-flag .ns-flag-t{color:#1a1816;font-weight:800;font-size:17px;line-height:24px;margin:0 0 6px}
.ns-pill-tag{display:inline-block;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:3px 9px;border-radius:9999px;background:#fbe9ea;color:#b81d22;margin-bottom:8px}
.ns-pill-tag--ok{background:#e7f5e9;color:#0a801f}
.ns-bills{width:100%;border-collapse:collapse;font-size:14px}
.ns-bills th{text-align:left;color:#757575;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:0 0 8px;border-bottom:1px solid #ece8e2}
.ns-bills th:last-child,.ns-bills td:last-child{text-align:right}
.ns-bills td{color:#2b2b2b;padding:8px 0;border-bottom:1px solid #ece8e2}
.ns-bills tr:last-child td{border-bottom:none}
.ns-bills td b{font-weight:700;color:#1a1816}
.ns-up{color:#b81d22;font-weight:700}
.ns-dn{color:#0a801f;font-weight:700}

/* ---- the calculator ---- */
.ns-tool{display:grid;grid-template-columns:1fr;gap:20px;margin:28px auto 0;max-width:1035px;align-items:start}
.ns-panel{background:#fff;border:1px solid #e5e5e5;border-radius:20px;padding:20px}
.ns-group{border-bottom:1px solid #ece8e2;padding:0 0 18px;margin:0 0 18px}
.ns-group:last-child{border-bottom:none;padding-bottom:0;margin-bottom:0}
.ns-group-h{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin:0 0 14px}
.ns-group-h h3{color:#1a1816;font-size:15px;font-weight:800;letter-spacing:.3px;margin:0;text-transform:uppercase}
.ns-group-h b{color:#3f4650;font-size:14px;font-weight:700;white-space:nowrap}
.ns-f{margin:0 0 12px}
.ns-f:last-child{margin-bottom:0}
.ns-lab{display:block;color:#1a1816;font-size:13px;font-weight:700;letter-spacing:.2px;margin:0 0 5px}
.ns-hint{display:block;color:#757575;font-size:12px;line-height:17px;margin:5px 0 0}
.ns-in{display:flex;align-items:center;border:1px solid #d3cfca;border-radius:12px;background:#fff;height:46px;padding:0 12px;box-sizing:border-box}
.ns-in:focus-within{border-color:#d92228}
.ns-in i{font-style:normal;color:#757575;font-size:14px;margin-right:5px;flex-shrink:0}
.ns-in em{font-style:normal;color:#757575;font-size:14px;margin-left:5px;flex-shrink:0}
.ns-in input,.ns-in select{border:none;outline:none;width:100%;font-size:16px;font-weight:700;color:#1a1816;font-family:inherit;background:transparent;-webkit-appearance:none;appearance:none;min-width:0}
.ns-in select{cursor:pointer}
.ns-in--sel{position:relative}
.ns-in--sel:after{content:"";position:absolute;right:14px;width:7px;height:7px;border-right:2px solid #757575;border-bottom:2px solid #757575;transform:rotate(45deg) translateY(-2px);pointer-events:none}
.ns-row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.ns-check{display:flex;align-items:flex-start;gap:9px;margin:0 0 10px;cursor:pointer}
.ns-check input{width:19px;height:19px;margin:1px 0 0;accent-color:#d92228;flex-shrink:0}
.ns-check span{color:#3f4650;font-size:14px;line-height:20px}
.ns-seg{display:flex;gap:6px;background:#f2f0ef;border-radius:9999px;padding:4px;margin:0 0 14px;flex-wrap:wrap}
.ns-seg button{flex:1 1 30%;border:none;background:transparent;color:#2b2b2b;font-family:inherit;font-weight:700;font-size:13px;padding:9px 8px;border-radius:9999px;cursor:pointer;min-height:38px}
.ns-seg button[aria-pressed="true"]{background:#2b2b2b;color:#fff}
.ns-mode{display:none}
.ns-mode.is-on{display:block}
.ns-solved{background:#fbf8f4;border:1px solid #ece8e2;border-radius:12px;padding:14px;margin:12px 0 0}
.ns-solved p{margin:0 0 6px;color:#3f4650;font-size:13px;line-height:19px}
.ns-solved p:last-child{margin-bottom:0}
.ns-solved b{color:#1a1816;font-weight:800}
.ns-solved .ns-warn{color:#b81d22;font-weight:700}
.ns-more{width:100%;background:transparent;border:1px dashed #d3cfca;color:#3f4650;font-family:inherit;font-weight:700;font-size:13px;padding:11px;border-radius:12px;cursor:pointer;margin:14px 0 0;min-height:44px}
.ns-more:hover{border-color:#d92228;color:#d92228}
.ns-adv{display:none;margin:14px 0 0}
.ns-adv.is-on{display:block}

/* ---- the output ---- */
.ns-out{background:#1a1816;border-radius:20px;padding:22px;color:#fff}
.ns-out h3{color:#f0c9ca;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 14px}
.ns-line{display:flex;justify-content:space-between;gap:10px;padding:7px 0;font-size:14px;line-height:20px;border-bottom:1px solid rgba(255,255,255,.1)}
.ns-line span{color:#beb8b0}
.ns-line b{color:#fff;font-weight:700;white-space:nowrap}
.ns-line--sub{padding-left:12px;font-size:13px}
.ns-line--sub span{color:#beb8b0}
.ns-line--tot{border-bottom:none;border-top:1px solid rgba(255,255,255,.22);margin-top:6px;padding-top:12px}
.ns-line--tot span,.ns-line--tot b{color:#fff;font-weight:800;font-size:15px}
.ns-big{margin:18px 0 0;padding:18px 0 0;border-top:2px solid #d92228}
.ns-big p{margin:0 0 4px;color:#f0c9ca;font-size:12px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase}
.ns-big b{display:block;color:#fff;font-weight:800;font-size:38px;line-height:44px;letter-spacing:-1px}
.ns-big b.ns-neg{color:#f0c9ca}
.ns-big em{display:block;font-style:normal;color:#beb8b0;font-size:13px;line-height:19px;margin:8px 0 0}
.ns-after{margin:16px 0 0;padding:14px 0 0;border-top:1px solid rgba(255,255,255,.18)}
.ns-out-cta{margin:18px 0 0}
.ns-out-cta button{width:100%;background:#d92228;color:#fff;border:none;border-radius:9999px;font-family:inherit;font-weight:700;font-size:16px;padding:15px;cursor:pointer;min-height:52px}
.ns-out-cta button:hover{background:#a92e2a}
.ns-out-cta .ns-print{background:transparent;border:1px solid rgba(255,255,255,.3);color:#fff;font-size:14px;padding:12px;margin-top:9px;min-height:44px}
.ns-out-cta .ns-print:hover{background:rgba(255,255,255,.08)}
.ns-out-foot{color:#beb8b0;font-size:12px;line-height:18px;margin:14px 0 0}

@media (min-width:768px){
  .ns-h2{font-size:32px;line-height:40px}
  .ns-wrap{padding:0 32px}
  .ns-panel{padding:28px}
  .ns-out{padding:26px}
  .ns-rec-grid{grid-template-columns:1fr 1fr}
  .ns-rec-grid .ns-span2{grid-column:1 / -1}
}
@media (min-width:992px){
  .ns-tool{grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:24px}
  .ns-out{position:sticky;top:88px}
  .ns-out.ns-out--tall{position:static}
  .ns-rec-grid{grid-template-columns:1fr 1fr 1fr}
}

/* ---- content tables ---- */
.ns-tablewrap{overflow-x:auto;max-width:920px;margin:0 auto;-webkit-overflow-scrolling:touch;background:#fff;border:1px solid #e5e5e5;border-radius:16px}
.ns-tablewrap--white{background:#fbf8f4;border-color:#ece8e2}
.ns-table{width:100%;border-collapse:collapse;font-size:14px;min-width:620px}
.ns-table th{background:#1a1816;color:#fff;text-align:left;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:12px 14px}
.ns-table td{color:#3f4650;padding:12px 14px;border-bottom:1px solid #ece8e2;line-height:21px;vertical-align:top}
.ns-table tr:last-child td{border-bottom:none}
.ns-table tr:nth-child(even) td{background:#fbf8f4}
.ns-tablewrap--white .ns-table tr:nth-child(even) td{background:#fff}
.ns-table td:first-child{color:#1a1816;font-weight:700;white-space:nowrap}
.ns-table td:nth-child(2){white-space:nowrap;font-weight:700;color:#1a1816}
.ns-cols{display:grid;grid-template-columns:1fr;gap:16px;max-width:920px;margin:0 auto}
.ns-cols .ns-card p{color:#3f4650;font-size:15px;line-height:24px;margin:0}
.ns-steps{max-width:760px;margin:0 auto}
.ns-step{display:flex;gap:16px;padding:16px 0;border-bottom:1px solid #ece8e2}
.ns-step:last-child{border-bottom:none}
.ns-num{flex-shrink:0;width:40px;height:40px;border-radius:9999px;background:#fbe9ea;color:#d92228;font-weight:800;font-size:16px;display:flex;align-items:center;justify-content:center}
.ns-step h3{color:#1a1816;font-size:16px;line-height:23px;font-weight:700;margin:0 0 4px}
.ns-step p{color:#3f4650;font-size:15px;line-height:23px;margin:0}
.ns-note{color:#757575;font-size:13px;line-height:21px;text-align:center;max-width:680px;margin:22px auto 0}
.ns-answer{background:#fbf8f4;border:1px solid #ece8e2;border-left:4px solid #d92228;border-radius:16px;padding:24px 26px;max-width:760px;margin:0 auto}
.ns-answer p{color:#2b2b2b;font-size:17px;line-height:29px;margin:0}
.ns-answer .ns-upd{color:#757575;font-size:12px;letter-spacing:.6px;text-transform:uppercase;margin:14px 0 0;font-weight:700}
@media (min-width:768px){.ns-cols{grid-template-columns:1fr 1fr}.ns-cols--3{grid-template-columns:1fr 1fr 1fr}}
</style>"""


def money_field(fid, label, hint="", value="0", prefix="$", suffix=""):
    pre = f"<i>{prefix}</i>" if prefix else ""
    suf = f"<em>{suffix}</em>" if suffix else ""
    hint_html = f'<span class="ns-hint">{hint}</span>' if hint else ""
    return (
        f'<div class="ns-f"><label class="ns-lab" for="{fid}">{label}</label>'
        f'<div class="ns-in">{pre}<input type="text" inputmode="decimal" id="{fid}" value="{value}">{suf}</div>'
        f"{hint_html}</div>"
    )


# ---------------------------------------------------------------------------
# The tool section.
TOOL = (
    '<section aria-label="Seller net sheet calculator" class="pos_relative z_1" id="calculator">'
    '<div class="ns-wrap">'

    # --- step 1: the county lookup ------------------------------------------
    '<div class="ns-step1 ns-hide-print">'
    '<p class="ns-eyebrow">Step 1</p>'
    "<h2>Start with your address.</h2>"
    '<p class="ns-step1-sub">Without it, every number below is a generic Orange County estimate. '
    "With it, I pull your county record and fill in <b>what you paid and when</b>, <b>your last several "
    "tax bills</b>, <b>whether a Mello-Roos rides on them</b>, and enough of your loan to back into your "
    "payoff.</p>"
    '<div class="ns-lookup">'
    '<form id="ns-lookup-form" autocomplete="off">'
    '<label class="ns-lab" for="ns-address">Your property address</label>'
    '<div class="ns-pill" id="ns-pill">'
    '<input type="text" id="ns-address" name="ns_address" placeholder="Start typing, then pick your address" '
    'autocomplete="off" aria-label="Your property address">'
    '<button type="submit" id="ns-lookup-btn">Pull my county record</button>'
    "</div></form>"
    '<p class="ns-lookup-err" id="ns-lookup-err" role="alert"></p>'
    '<p class="ns-lookup-note">Rather not? Skip it and type every number yourself below.</p>'
    "</div></div>"
    '<div class="ns-acc" id="ns-acc"><i>&#9888;</i><div><b>Generic defaults right now.</b> '
    '<span>Property taxes, Mello-Roos, HOA dues, and your loan payoff are all guesses until you pull '
    "the record above.</span></div></div>"

    # --- the record ---------------------------------------------------------
    '<div class="ns-record" id="ns-record" aria-live="polite">''<p class="ns-eyebrow" style="text-align:center">Pulled from the county record</p>''<div class="ns-rec-grid" id="ns-rec-grid"></div></div>'

    # --- the calculator -----------------------------------------------------
    '<div class="ns-tool">'
    '<div class="ns-panel">'

    # Group: the sale
    '<div class="ns-group">'
    '<p class="ns-eyebrow">Step 2</p>'
    '<div class="ns-group-h"><h3>The sale</h3></div>'
    + money_field("ns-price", "Sale price", "Start from my estimate, then price it where the comps say.", "1,200,000")
    + '<div class="ns-f"><label class="ns-lab" for="ns-close">Estimated close date</label>'
      '<div class="ns-in"><input type="date" id="ns-close"></div>'
      '<span class="ns-hint">Drives the property tax proration and the interest on your payoff.</span></div>'
    + "</div>"

    # Group: commission
    '<div class="ns-group">'
    '<div class="ns-group-h"><h3>Commission</h3><b id="ns-o-comm-h">&minus;$60,000</b></div>'
    '<div class="ns-row2">'
    '<div class="ns-f"><label class="ns-lab" for="ns-comm-l">My listing fee</label>'
    '<div class="ns-in"><input type="text" inputmode="decimal" id="ns-comm-l" value="2.5"><em>%</em></div></div>'
    '<div class="ns-f"><label class="ns-lab" for="ns-comm-b">Offered to buyer side</label>'
    '<div class="ns-in"><input type="text" inputmode="decimal" id="ns-comm-b" value="2.5"><em>%</em></div></div>'
    "</div>"
    '<span class="ns-hint">Both are negotiated, and since 2024 nothing is automatic. What you offer the buyer\'s '
    "side is a per-deal strategy call, not a default.</span>"
    "</div>"

    # Group: escrow, title, transfer tax
    '<div class="ns-group">'
    '<div class="ns-group-h"><h3>Escrow, title, transfer tax</h3><b id="ns-o-close-h">&minus;$8,070</b></div>'
    + money_field("ns-escrow", "Escrow fee (your half)", "Southern California custom: roughly $1,200 base plus $1 per $1,000, split with the buyer.", "2,400")
    + money_field("ns-title", "Owner's title policy", "About $500 plus $2.50 per $1,000. Seller-paid by Southern California custom.", "3,500")
    + money_field("ns-tt-county", "County transfer tax", "$1.10 per $1,000. Statewide, every California county.", "1,320")
    + money_field("ns-tt-city", "City transfer tax", "Auto-filled once I know the city. Zero in every Orange County city.", "0")
    + money_field("ns-misc", "Recording, notary, wire, doc fees", "The small fixed items that appear on every closing statement.", "850")
    + "</div>"

    # Group: seller-paid items
    '<div class="ns-group">'
    '<div class="ns-group-h"><h3>Seller-paid items</h3><b id="ns-o-items-h">&minus;$875</b></div>'
    + money_field("ns-nhd", "Natural hazard disclosure report", "Required in California. Flood, fire, seismic, and the tax-district disclosure that names any Mello-Roos.", "150")
    + money_field("ns-warranty", "Home warranty for the buyer", "Common ask in escrow. Cheap insurance against a repair request at the eleventh hour.", "600")
    + money_field("ns-termite", "Termite inspection", "", "125")
    + money_field("ns-termite-work", "Section 1 termite work", "Active infestation and damage. Only known after the inspection; leave at zero until then.", "0")
    + money_field("ns-hoa-fees", "HOA demand and document fees", "The demand statement plus the resale package. Auto-filled at $400 when the record shows an association.", "0")
    + money_field("ns-retrofit", "Retrofit and point-of-sale compliance", "Smoke and CO alarms, water heater strapping, and any city report or low-flow requirement.", "0")
    + money_field("ns-prep", "Prep, repairs, staging", "Your call. I tell you which dollars come back at sale and which never do.", "0")
    + money_field("ns-concessions", "Credits to the buyer", "Only exists if we negotiate it. Often the cheapest way to close a repair-request gap.", "0")
    + "</div>"

    # Group: prorations
    '<div class="ns-group">'
    '<div class="ns-group-h"><h3>Prorations</h3><b id="ns-o-pro-h">$0</b></div>'
    + money_field("ns-tax-annual", "Your annual property tax bill", "Auto-filled from your county record, special assessments included.", "0")
    + '<label class="ns-check"><input type="checkbox" id="ns-inst1"><span>First installment paid '
      '(covers July 1 to December 31, due November 1)</span></label>'
      '<label class="ns-check"><input type="checkbox" id="ns-inst2"><span>Second installment paid '
      '(covers January 1 to June 30, due February 1)</span></label>'
    + money_field("ns-hoa-monthly", "Monthly HOA dues", "Prorated to the day like taxes. Auto-filled from the record.", "0")
    + '<div class="ns-solved" id="ns-pro-out"><p>Enter an annual tax bill to see the proration.</p></div>'
    + "</div>"

    # Group: payoff
    '<div class="ns-group">'
    '<div class="ns-group-h"><h3>What you owe</h3><b id="ns-o-payoff-h">&minus;$0</b></div>'
    '<div class="ns-seg" role="group" aria-label="How to figure your payoff">'
    '<button type="button" data-mode="known" aria-pressed="true">I know it</button>'
    '<button type="button" data-mode="payment" aria-pressed="false">From my payment</button>'
    '<button type="button" data-mode="terms" aria-pressed="false">From my loan</button>'
    "</div>"

    '<div class="ns-mode is-on" id="ns-mode-known">'
    + money_field("ns-payoff", "Loan payoff balance", "The number on your latest statement, or the payoff demand if you have one.", "0")
    + "</div>"

    '<div class="ns-mode" id="ns-mode-payment">'
    '<p class="ns-hint" style="margin:0 0 12px">Most owners do not know their payoff, but everybody knows their '
    "payment. Give me the payment and when it started and I will solve for the rate and amortize it forward.</p>"
    + money_field("ns-p-orig", "Original loan amount", "Purchase price minus your down payment. Auto-filled from the recorded sale.", "0")
    + '<div class="ns-f"><label class="ns-lab" for="ns-p-start">First payment date</label>'
      '<div class="ns-in"><input type="date" id="ns-p-start"></div>'
      '<span class="ns-hint">Roughly a month after you closed. Auto-filled from the recorded sale date.</span></div>'
    + money_field("ns-p-pay", "Your monthly payment", "", "0")
    + '<label class="ns-check"><input type="checkbox" id="ns-p-piti"><span>That payment includes taxes and '
      'insurance (an impound account)</span></label>'
      '<div id="ns-p-piti-fields" style="display:none">'
    + money_field("ns-p-ins", "Monthly homeowners insurance", "", "175")
    + money_field("ns-p-pmi", "Monthly mortgage insurance", "FHA or conventional PMI, if you carry it.", "0")
    + "</div>"
    + '<div class="ns-f"><label class="ns-lab" for="ns-p-term">Loan term</label>'
      '<div class="ns-in ns-in--sel"><select id="ns-p-term">'
      '<option value="360" selected>30 years</option><option value="180">15 years</option>'
      '<option value="240">20 years</option><option value="120">10 years</option></select></div></div>'
    + '<div class="ns-solved" id="ns-solve-out"><p>Fill in the loan amount, start date, and payment.</p></div>'
    + "</div>"

    '<div class="ns-mode" id="ns-mode-terms">'
    + money_field("ns-t-orig", "Original loan amount", "", "0")
    + '<div class="ns-row2">'
      '<div class="ns-f"><label class="ns-lab" for="ns-t-rate">Interest rate</label>'
      '<div class="ns-in"><input type="text" inputmode="decimal" id="ns-t-rate" value="0"><em>%</em></div></div>'
      '<div class="ns-f"><label class="ns-lab" for="ns-t-term">Term</label>'
      '<div class="ns-in ns-in--sel"><select id="ns-t-term">'
      '<option value="360" selected>30 yr</option><option value="180">15 yr</option>'
      '<option value="240">20 yr</option><option value="120">10 yr</option></select></div></div></div>'
    + '<div class="ns-f"><label class="ns-lab" for="ns-t-start">First payment date</label>'
      '<div class="ns-in"><input type="date" id="ns-t-start"></div></div>'
    + '<div class="ns-solved" id="ns-terms-out"><p>Fill in the loan amount, rate, and start date.</p></div>'
    + "</div>"

    '<button type="button" class="ns-more" id="ns-payoff-more" aria-expanded="false">'
    "Second loan, HELOC, and payoff charges &plus;</button>"
    '<div class="ns-adv" id="ns-payoff-adv">'
    + money_field("ns-payoff2", "Second loan or HELOC payoff", "Every lien on title gets paid at close, in recording order.", "0")
    + money_field("ns-payoff-extra", "Payoff interest and lender charges", "Interest runs to the day the wire lands, plus the reconveyance, statement, and wire fees. Escrow over-collects on purpose and the lender refunds the difference.", "0")
    + "</div>"
    + "</div>"

    # Group: withholding
    '<div class="ns-group">'
    '<div class="ns-group-h"><h3>Withholding at close</h3><b id="ns-o-wh-h">$0</b></div>'
    '<label class="ns-check"><input type="checkbox" id="ns-593"><span>Withhold California 3 1/3% '
    "(Form 593). Skip it if this was your principal residence, which exempts most sellers.</span></label>"
    '<label class="ns-check"><input type="checkbox" id="ns-firpta"><span>Withhold federal 15% (FIRPTA). '
    "Applies when the seller is a foreign person for tax purposes.</span></label>"
    '<span class="ns-hint">Withholding is not a tax. It is a prepayment held out of your proceeds at close and '
    "credited against what you actually owe when you file.</span>"
    "</div>"

    # Group: capital gains
    '<div class="ns-group">'
    '<div class="ns-group-h"><h3>Capital gains</h3><b id="ns-o-cg-h">$0</b></div>'
    '<label class="ns-check"><input type="checkbox" id="ns-cg-on"><span>Estimate my capital gains tax</span></label>'
    '<div class="ns-adv" id="ns-cg-fields">'
    + money_field("ns-cg-basis", "What you paid for the home", "Auto-filled from the recorded sale.", "0")
    + money_field("ns-cg-improve", "Capital improvements since", "Additions, a new roof, a remodel, solar you own. Not paint and not repairs.", "0")
    + '<div class="ns-f"><label class="ns-lab" for="ns-cg-filing">Filing status</label>'
      '<div class="ns-in ns-in--sel"><select id="ns-cg-filing">'
      '<option value="mfj" selected>Married filing jointly</option><option value="single">Single</option>'
      "</select></div></div>"
    + '<label class="ns-check"><input type="checkbox" id="ns-cg-primary" checked><span>I lived here as my main '
      "home for at least 2 of the last 5 years</span></label>"
    + money_field("ns-cg-income", "Your other taxable income this year", "Wages and everything else, after deductions. It sets which capital gains bracket the gain lands in.", "150,000")
    + '<div class="ns-solved" id="ns-cg-out"><p>Turn the estimate on to see the breakdown.</p></div>'
    + '<span class="ns-hint">I am your agent, not your tax preparer. These are planning numbers to hand your CPA '
      "before we price, not after we close.</span>"
    + "</div>"
    + "</div>"

    "</div>"  # /ns-panel

    # --- output -------------------------------------------------------------
    '<div class="ns-out" id="ns-out">'
    "<h3>Your net sheet</h3>"
    '<div class="ns-line"><span>Sale price</span><b id="ns-o-price">$1,200,000</b></div>'
    '<div class="ns-line"><span>Commission</span><b id="ns-o-comm">&minus;$60,000</b></div>'
    '<div class="ns-line"><span>Escrow, title, transfer tax</span><b id="ns-o-close">&minus;$8,070</b></div>'
    '<div class="ns-line"><span>Seller-paid items</span><b id="ns-o-items">&minus;$875</b></div>'
    '<div class="ns-line"><span>Property tax proration</span><b id="ns-o-tax">$0</b></div>'
    '<div class="ns-line"><span>HOA proration</span><b id="ns-o-hoa">$0</b></div>'
    '<div class="ns-line ns-line--tot"><span>Cost of sale</span><b id="ns-o-cos">&minus;$68,945</b></div>'
    '<div class="ns-line"><span>Loan payoff</span><b id="ns-o-payoff">$0</b></div>'
    '<div class="ns-line" id="ns-o-wh-row" style="display:none"><span>Withheld at close</span><b id="ns-o-wh">$0</b></div>'
    '<div class="ns-big"><p>Cash to you at close</p><b id="ns-o-net">$1,131,055</b>'
    '<em id="ns-o-pct">Cost of sale: 5.7% of the sale price.</em></div>'
    '<div class="ns-after" id="ns-after" style="display:none">'
    '<div class="ns-line"><span>Estimated capital gains tax, due when you file</span><b id="ns-o-cg">$0</b></div>'
    '<div class="ns-line ns-line--tot"><span>After that tax</span><b id="ns-o-aftertax">$0</b></div>'
    "</div>"
    '<div class="ns-out-cta ns-hide-print">'
    '<button type="button" id="ns-cta">Get the written net sheet</button>'
    '<button type="button" class="ns-print" id="ns-print">Print or save this net sheet</button>'
    "</div>"
    '<p class="ns-out-foot">Planning numbers built on California custom and current county data. Escrow issues the '
    "binding estimated closing statement once we are in contract, and I reconcile the two line by line.</p>"
    "</div>"  # /ns-out
    "</div>"  # /ns-tool
    "</div></section>"
)

# ---------------------------------------------------------------------------
# Content sections (the AI-answer + SEO surface).

QUICK_ANSWER = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
  <div class="ns-narrow">
    <h2 class="ns-h2">What is a seller net sheet?</h2>
    <div class="ns-answer">
      <p>A seller net sheet is the line-by-line estimate of what you actually walk away with: sale price, minus commission, escrow, title, transfer tax, seller-paid items, and prorations, minus every loan payoff. In California the honest version has to answer four questions a blank calculator cannot: what your property tax bill really is, whether a Mello-Roos special tax rides on top of it, how escrow will prorate that bill on your close date, and what your mortgage payoff will be on the day the wire goes out rather than what the statement said last month. On a $1,200,000 Orange County sale, cost of sale typically lands near 6% of the price before your payoff.</p>
      <p class="ns-upd">Current for 2026 California closings</p>
    </div>
  </div>
</section>
"""

LINE_ITEMS = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="ns-wrap">
    <h2 class="ns-h2">Every line on a California closing statement.</h2>
    <p class="ns-sub">What each cost is, who customarily pays it, and what it runs in 2026.</p>
    <div class="ns-tablewrap">
      <table class="ns-table">
        <thead><tr><th>Line item</th><th>Typical 2026</th><th>What it actually is</th></tr></thead>
        <tbody>
          <tr><td>Listing fee</td><td>Negotiated</td><td>Agreed between us in writing before we launch. It is not a fixed rate and never was.</td></tr>
          <tr><td>Buyer-side compensation</td><td>Negotiated</td><td>Since the 2024 rule change, nothing is offered automatically. Whether you offer anything is a per-deal call driven by what nets you more.</td></tr>
          <tr><td>Escrow fee</td><td>$1,200 base plus $1 per $1,000</td><td>The neutral third party that holds funds and documents. Split evenly with the buyer by Southern California custom.</td></tr>
          <tr><td>Owner's title policy</td><td>$500 plus $2.50 per $1,000</td><td>Insures the buyer's ownership against defects in the chain of title. Seller-paid in Southern California; the buyer pays their lender's policy.</td></tr>
          <tr><td>County transfer tax</td><td>$1.10 per $1,000</td><td>The statewide documentary transfer tax, collected at recording. Customarily the seller's.</td></tr>
          <tr><td>City transfer tax</td><td>$0 in Orange County</td><td>A handful of cities stack their own on top. In Los Angeles County the recorder lists five: Los Angeles, Culver City, Santa Monica, Pomona, and Redondo Beach.</td></tr>
          <tr><td>Recording and notary</td><td>$850 all in</td><td>Deed recording, the reconveyance, mobile notary, courier, wire fees, and e-doc charges.</td></tr>
          <tr><td>Natural hazard disclosure</td><td>$100 to $250</td><td>The report that discloses flood, fire, seismic, and tax-district status. Its tax section is where a Mello-Roos gets disclosed in writing.</td></tr>
          <tr><td>Home warranty</td><td>$450 to $900</td><td>A year of coverage for the buyer. Frequently requested, and often cheaper than the repair credit it prevents.</td></tr>
          <tr><td>Termite inspection and work</td><td>$100 to $175, plus repairs</td><td>The inspection is small. Section 1 work (active infestation and damage) is the line that moves, and it is negotiable.</td></tr>
          <tr><td>HOA demand and documents</td><td>$300 to $600</td><td>The management company charges for the demand statement and the resale disclosure package. Delivery timing is a real closing-delay risk.</td></tr>
          <tr><td>Retrofit and point-of-sale</td><td>$0 to $600</td><td>California requires working smoke and carbon monoxide alarms and a strapped water heater. Some cities add an inspection or report of their own.</td></tr>
          <tr><td>Property tax proration</td><td>Either direction</td><td>Escrow divides the fiscal-year bill by the day. Depending on your close date and which installments you paid, this is a credit or a debit.</td></tr>
          <tr><td>HOA dues proration</td><td>Usually a credit</td><td>Dues are paid ahead, so the buyer reimburses you for the unused part of the month.</td></tr>
          <tr><td>Loan payoff</td><td>Your balance, plus</td><td>Principal plus interest through the day the wire lands, plus the reconveyance, demand, and wire fees. Escrow over-collects and the lender refunds.</td></tr>
          <tr><td>Buyer credits</td><td>Only if negotiated</td><td>Closing cost credits or repair credits agreed in the contract or after inspections.</td></tr>
        </tbody>
      </table>
    </div>
    <p class="ns-note">Escrow and title pricing varies by company and deal size; these are the planning numbers I use, and they track Orange County quotes closely. Every line here is a custom, not a law, so all of it is negotiable in the contract. Compare against the full <a class="ns-a" href="/cost-to-sell/">cost to sell in Orange County</a>.</p>
  </div>
</section>
"""

PRORATION = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
  <div class="ns-wrap">
    <h2 class="ns-h2">How escrow prorates your property taxes.</h2>
    <p class="ns-sub">The single most misunderstood line on a California closing statement, and the reason two sellers at the same price walk away with different numbers.</p>
    <div class="ns-cols ns-cols--3">
      <div class="ns-card">
        <p class="ns-eyebrow">The calendar</p>
        <h3>The tax year is not the calendar year</h3>
        <p>California's fiscal year runs July 1 through June 30. The first installment covers July 1 to December 31 and is due November 1, delinquent December 10. The second covers January 1 to June 30, due February 1, delinquent April 10.</p>
      </div>
      <div class="ns-card">
        <p class="ns-eyebrow">The split</p>
        <h3>You pay for the days you owned it</h3>
        <p>Escrow charges you taxes through the day before recording and the buyer from recording forward. Then it compares that share against what you already paid. The difference is the line on your statement.</p>
      </div>
      <div class="ns-card">
        <p class="ns-eyebrow">The direction</p>
        <h3>Credit or debit, and it swings hard</h3>
        <p>Close in May with both installments paid and you are credited for June. Close in October with neither paid and you are debited for July through October. On a $14,000 bill that is a four-figure swing either way.</p>
      </div>
    </div>
    <p class="ns-note">One more piece nobody warns you about: the supplemental bill. California reassesses to the purchase price on a change of ownership, so the county issues a separate supplemental bill after close, outside escrow. That one lands on the buyer. If your Prop 13 base was well under the sale price, expect a supplemental refund on your side too.</p>
  </div>
</section>
"""

MELLO = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="ns-wrap">
    <h2 class="ns-h2">Mello-Roos, and what it does to your sale.</h2>
    <p class="ns-sub">A special tax that never shows up in an online estimate, and a buyer question you should never have to guess at.</p>
    <div class="ns-cols">
      <div class="ns-card">
        <p class="ns-eyebrow">How to tell</p>
        <h3>Your bill outruns the rate</h3>
        <p>California's ad valorem rate is Prop 13's 1% plus voter-approved bond debt, so a bill normally lands near 1.05% to 1.25% of assessed value depending on the county. When the billed total runs meaningfully above that, the gap is a special tax: a Mello-Roos community facilities district, a 1915 Act improvement bond, or a lighting and landscape district. That is exactly the comparison the calculator above runs on your record, and the tax bill itself confirms it under Special Assessment Charges.</p>
      </div>
      <div class="ns-card">
        <p class="ns-eyebrow">Where it lives</p>
        <h3>Newer construction, mostly</h3>
        <p>Districts only exist under the 1982 Mello-Roos Act, so pre-1983 homes were never wrapped in one. In Orange County the familiar names are the newer Irvine villages, Ladera Ranch, Rancho Mission Viejo, Talega in San Clemente, and Tustin Legacy. Annual charges range from a few hundred dollars in older districts to well over $5,000 in the newest ones, and each district has its own bond payoff year.</p>
      </div>
      <div class="ns-card">
        <p class="ns-eyebrow">At closing</p>
        <h3>It prorates, it discloses, it prices</h3>
        <p>The special tax is billed on the same statement as your ad valorem tax, so it prorates with it. It gets disclosed in writing through the Natural Hazard Disclosure report's tax section, and the buyer's lender counts it against their debt-to-income. A buyer comparing your home against one without a district is really comparing monthly payments, which is a pricing conversation worth having before we list, not after.</p>
      </div>
      <div class="ns-card">
        <p class="ns-eyebrow">The one thing to do</p>
        <h3>Get the payoff year in writing</h3>
        <p>Mello-Roos bonds end. A district with four years left is a very different story to a buyer than one with twenty-two, and the difference is worth real money in negotiation. The district's annual disclosure and the county tax collector both carry the term. I pull it before we price, so the number is on our side of the table.</p>
      </div>
    </div>
  </div>
</section>
"""

PAYOFF_EXPLAINER = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
  <div class="ns-wrap">
    <h2 class="ns-h2">Don't know your payoff? Back into it.</h2>
    <p class="ns-sub">You know your monthly payment and roughly when you bought. That is enough to get within a few hundred dollars.</p>
    <div class="ns-steps">
      <div class="ns-step"><div class="ns-num">1</div><div>
        <h3>Start from the recorded sale</h3>
        <p>The county already records what you paid and the date it closed. The calculator pulls both, so the original loan amount is just your purchase price minus what you put down, and the first payment date is about a month after closing.</p>
      </div></div>
      <div class="ns-step"><div class="ns-num">2</div><div>
        <h3>Strip your payment down to principal and interest</h3>
        <p>If your payment includes an impound account, the taxes and insurance inside it are not paying down the loan. Your actual tax bill comes back with your record, so the calculator subtracts the real number rather than a guess, along with insurance, mortgage insurance, and HOA dues.</p>
      </div></div>
      <div class="ns-step"><div class="ns-num">3</div><div>
        <h3>Solve for the rate you locked</h3>
        <p>Loan amount, term, and principal-and-interest payment have exactly one interest rate that satisfies them. The calculator solves for it, so you do not have to dig up the note. If the solved rate looks nothing like what you remember, the payment probably includes something extra.</p>
      </div></div>
      <div class="ns-step"><div class="ns-num">4</div><div>
        <h3>Amortize forward to your close date</h3>
        <p>From there it is arithmetic: every payment since you started, split between interest and principal, run out to the day you close. What is left is your balance.</p>
      </div></div>
      <div class="ns-step"><div class="ns-num">5</div><div>
        <h3>Add what the demand statement will</h3>
        <p>A payoff is never just the balance. Interest runs to the day the wire lands, not the day you sign, and the lender adds a reconveyance fee, a statement fee, and a wire fee. Escrow deliberately over-collects a few days of interest and the lender refunds the difference weeks later.</p>
      </div></div>
    </div>
    <p class="ns-note">Extra principal payments, a recast, or a loan modification will move the answer. Treat the estimate as a planning number and order the real payoff demand once you are in contract, which escrow does automatically.</p>
  </div>
</section>
"""

TWO_TAXES = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="ns-wrap">
    <h2 class="ns-h2">The two numbers a title net sheet leaves off.</h2>
    <p class="ns-sub">Closing costs are predictable. These are where six figures actually move.</p>
    <div class="ns-cols">
      <div class="ns-card">
        <p class="ns-eyebrow">Owed later</p>
        <h3>Capital gains, and the exclusion that usually eats it</h3>
        <p>Live in the home 2 of the last 5 years and the IRS excludes up to $250,000 of gain filing single, $500,000 married filing jointly. Gain above that is federal long-term capital gains at 0%, 15%, or 20% depending on your total taxable income, plus the 3.8% net investment income tax over $200,000 single or $250,000 joint, and California taxes the whole gain as ordinary income at up to 13.3%. Your basis is what you paid plus capital improvements, and your selling costs come off the sale price first. On long-held Orange County homes the gain is routinely bigger than owners expect, which is why the estimate belongs in front of your CPA before we price. Inherited the home instead? <a class="ns-a" href="/inherited-house/">The step-up in basis usually erases the gain.</a></p>
      </div>
      <div class="ns-card">
        <p class="ns-eyebrow">Held at close</p>
        <h3>Franchise Tax Board withholding, and how to avoid it</h3>
        <p>California requires 3 1/3% of the sale price to be withheld from your proceeds at closing and sent to the Franchise Tax Board, unless you certify an exemption on Form 593 before escrow closes. The principal residence exemption covers most sellers, and there are others for a sale at a loss, a 1031 exchange, and a price at or under $100,000. On a $1,200,000 sale, forgetting the form means $40,000 leaves escrow that you have to wait until you file to get back. Sign it during escrow, not after. Foreign sellers face a separate 15% federal withholding under FIRPTA.</p>
      </div>
    </div>
    <p class="ns-note">I am your agent, not your tax preparer. These are planning numbers to bring to your CPA, and I coordinate with them directly on every sale that needs it.</p>
  </div>
</section>
"""

DIFFERENCE = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg_#fff">
  <div class="ns-wrap">
    <h2 class="ns-h2">Why this one gets closer.</h2>
    <p class="ns-sub">Most net sheet calculators multiply your sale price by a few percentages. This one starts with your parcel.</p>
    <div class="ns-tablewrap ns-tablewrap--white">
      <table class="ns-table">
        <thead><tr><th>The question</th><th>Typical calculator</th><th>Here</th></tr></thead>
        <tbody>
          <tr><td>Property taxes</td><td>Blank field, or 1.25% of price</td><td>Your actual billed totals for the last several years, straight off the county roll</td></tr>
          <tr><td>Mello-Roos</td><td>Not asked</td><td>Detected by comparing your bill against the ad valorem rate, with the annual dollars called out</td></tr>
          <tr><td>Tax proration</td><td>Ignored, or a flat guess</td><td>Computed from your close date against the July-to-June fiscal year and which installments you paid</td></tr>
          <tr><td>Your payoff</td><td>You have to know it</td><td>Solved from your monthly payment, your recorded purchase, and the impound your real tax bill implies</td></tr>
          <tr><td>Payoff extras</td><td>Not included</td><td>Interest to the wire date plus reconveyance, statement, and wire fees</td></tr>
          <tr><td>City transfer tax</td><td>One statewide rate</td><td>County $1.10 per $1,000 plus the actual city rule, including Measure ULA tiers in the City of Los Angeles</td></tr>
          <tr><td>Capital gains</td><td>Not modeled</td><td>Basis from your recorded purchase, the exclusion, federal brackets, the 3.8% surtax, and California as ordinary income</td></tr>
          <tr><td>FTB withholding</td><td>Not mentioned</td><td>The 3 1/3% Form 593 line, with the principal residence exemption</td></tr>
          <tr><td>Your starting price</td><td>You guess</td><td>Pre-filled from a market model, then priced properly with a <a class="ns-a" href="/value/">full valuation</a></td></tr>
        </tbody>
      </table>
    </div>
    <p class="ns-note">The number that actually binds is the estimated closing statement escrow issues once you are in contract. This gets you close enough to make the decision months earlier, which is the whole point.</p>
  </div>
</section>
"""


def faq_item(idx, question, answer_html):
    return (
        '<section data-expanded="false" class="m_0">'
        f'<button type="button" data-expanded="false" aria-expanded="false" aria-controls="ns-faq-{idx}-content" '
        f'id="ns-faq-{idx}-header" data-has-custom-icon="true" '
        'class="d_flex ai_center jc_space-between w_100% p_10px_40px_16px_0 bg-c_transparent bd_none cursor_pointer '
        'fs_14px md:fs_16px lh_24px md:lh_32px ta_left pos_relative '
        'bd-b_1px_solid_rgba(75,_92,_117,_0.1019607843) focus:ring_none">'
        f'<h3 class="flex_1 fw_400 fs_16px">{question}</h3>'
        '<div class="pos_absolute right_0 d_flex ai_center jc_center w_20px h_20px">'
        '<svg width="14" height="14" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M2 6L10 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>'
        '<path class="faq-icon-vertical" d="M6 2L6 10" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round"></path></svg></div></button>'
        f'<div class="ov_hidden max-h_0 trs_max-height_0.2s_ease-out" id="ns-faq-{idx}-content" role="region" '
        f'aria-labelledby="ns-faq-{idx}-header" style="max-height: 0px;">'
        '<div class="accordion-inner-content ov_hidden fs_16px fw_400 lh_24px bdr_16px mt_16px p_16px '
        f'bg-c_#f7f7f7">{answer_html}</div></div></section>'
    )


# (question, plain-text answer for JSON-LD, html answer for the accordion)
FAQS = [
    (
        "How much will I actually net selling my house in California?",
        "On a typical Orange County sale, cost of sale lands near 6% of the price before your mortgage payoff: total commission (negotiated, often around 5%), roughly $1,200 plus $1 per $1,000 in escrow, about $500 plus $2.50 per $1,000 for the owner's title policy, $1.10 per $1,000 in county transfer tax, about $850 in recording and doc fees, and a few hundred each for the natural hazard report, a home warranty, and termite. On $1,200,000 that is roughly $68,000 to $78,000 all in. Subtract your loan payoff and adjust for the property tax proration and you have your net. The variable that moves the answer most is not the closing costs, it is your payoff.",
        "On a typical Orange County sale, cost of sale lands near 6% of the price before your mortgage payoff: total commission (negotiated, often around 5%), roughly $1,200 plus $1 per $1,000 in escrow, about $500 plus $2.50 per $1,000 for the owner's title policy, $1.10 per $1,000 in county transfer tax, about $850 in recording and doc fees, and a few hundred each for the natural hazard report, a home warranty, and termite. On $1,200,000 that is roughly $68,000 to $78,000 all in. Subtract your loan payoff and adjust for the property tax proration and you have your net. The variable that moves the answer most is not the closing costs, it is your payoff.",
    ),
    (
        "How do I find my mortgage payoff if I don't have a statement?",
        "Back into it. Your original loan amount is your recorded purchase price minus your down payment, and your first payment came about a month after closing. Strip your monthly payment down to principal and interest by removing the taxes and insurance in your impound account, and there is exactly one interest rate that produces that payment on that loan over that term. Solve for it, amortize forward to your close date, and you have the balance. That is what the calculator on this page does automatically, using your actual county tax bill for the impound piece. Then add what the demand statement adds: interest to the day the wire lands plus the reconveyance, statement, and wire fees. Extra principal payments or a recast will move it, so order the real payoff demand once you are in contract.",
        "Back into it. Your original loan amount is your recorded purchase price minus your down payment, and your first payment came about a month after closing. Strip your monthly payment down to principal and interest by removing the taxes and insurance in your impound account, and there is exactly one interest rate that produces that payment on that loan over that term. Solve for it, amortize forward to your close date, and you have the balance. That is what the calculator on this page does automatically, using your actual county tax bill for the impound piece. Then add what the demand statement adds: interest to the day the wire lands plus the reconveyance, statement, and wire fees. Extra principal payments or a recast will move it, so order the real payoff demand once you are in contract.",
    ),
    (
        "Who pays property taxes at closing in California?",
        "Both of you, split by the day. California's fiscal year runs July 1 through June 30, billed in two installments: the first covers July 1 to December 31 and is due November 1, the second covers January 1 to June 30 and is due February 1. Escrow charges you for every day you owned the home in the current fiscal year and the buyer for the rest, then compares your share against what you already paid. If you prepaid past your close date you get a credit; if you closed before an installment was paid you get a debit. The swing on a $14,000 bill is easily four figures depending on the month you close.",
        "Both of you, split by the day. California's fiscal year runs July 1 through June 30, billed in two installments: the first covers July 1 to December 31 and is due November 1, the second covers January 1 to June 30 and is due February 1. Escrow charges you for every day you owned the home in the current fiscal year and the buyer for the rest, then compares your share against what you already paid. If you prepaid past your close date you get a credit; if you closed before an installment was paid you get a debit. The swing on a $14,000 bill is easily four figures depending on the month you close.",
    ),
    (
        "How do I know if my house has Mello-Roos?",
        "Compare your billed total against your assessed value. California's ad valorem rate is Prop 13's 1% plus voter-approved bonds, so a normal bill lands around 1.05% to 1.25% of assessed value depending on the county. When your bill runs meaningfully above that, the difference is a special tax line: a Mello-Roos community facilities district, a 1915 Act improvement bond, or a lighting and landscape district. Your tax bill itself confirms it under Special Assessment Charges, and the county tax collector publishes district lookups. Homes built before 1983 predate the Mello-Roos Act entirely. Districts do end, so the payoff year is worth getting in writing before you price.",
        "Compare your billed total against your assessed value. California's ad valorem rate is Prop 13's 1% plus voter-approved bonds, so a normal bill lands around 1.05% to 1.25% of assessed value depending on the county. When your bill runs meaningfully above that, the difference is a special tax line: a Mello-Roos community facilities district, a 1915 Act improvement bond, or a lighting and landscape district. Your tax bill itself confirms it under Special Assessment Charges, and the county tax collector publishes district lookups. Homes built before 1983 predate the Mello-Roos Act entirely. Districts do end, so the payoff year is worth getting in writing before you price.",
    ),
    (
        "What is the transfer tax when selling a house in California?",
        "Every California county charges $1.10 per $1,000 of the sale price ($0.55 per $500), customarily paid by the seller. On $1,200,000 that is $1,320. A small number of cities add their own on top. No Orange County city does. In Los Angeles County the recorder lists five: the City of Los Angeles at $4.50 per $1,000 plus Measure ULA at 4% of the full price above $5.4M and 5.5% above $10.9M as of July 1, 2026; Culver City on a 0.45% to 4% tiered scale; Santa Monica at $3 per $1,000 rising to 5.6% at $8M under Measure GS; and Pomona and Redondo Beach at $2.20 per $1,000. The ULA and GS tiers apply to the entire price once the threshold is crossed, not just the amount above it.",
        "Every California county charges $1.10 per $1,000 of the sale price ($0.55 per $500), customarily paid by the seller. On $1,200,000 that is $1,320. A small number of cities add their own on top. No Orange County city does. In Los Angeles County the recorder lists five: the City of Los Angeles at $4.50 per $1,000 plus Measure ULA at 4% of the full price above $5.4M and 5.5% above $10.9M as of July 1, 2026; Culver City on a 0.45% to 4% tiered scale; Santa Monica at $3 per $1,000 rising to 5.6% at $8M under Measure GS; and Pomona and Redondo Beach at $2.20 per $1,000. The ULA and GS tiers apply to the entire price once the threshold is crossed, not just the amount above it.",
    ),
    (
        "Will California withhold 3 1/3% of my sale price?",
        "Only if you don't certify an exemption. California requires escrow to withhold 3 1/3% of the total sale price and remit it to the Franchise Tax Board, unless the seller signs Form 593 before the close of escrow claiming an exemption. The principal residence exemption under IRC Section 121 covers most home sellers, and there are exemptions for a sale at a loss, a 1031 exchange, and a sale price at or under $100,000. On a $1,200,000 sale that form is worth $40,000 of cash flow at the table. Withholding is not an extra tax, it is a prepayment credited when you file, but you wait months to see it. Sellers who are foreign persons for tax purposes face a separate 15% federal withholding under FIRPTA.",
        "Only if you don't certify an exemption. California requires escrow to withhold 3 1/3% of the total sale price and remit it to the Franchise Tax Board, unless the seller signs Form 593 before the close of escrow claiming an exemption. The principal residence exemption under IRC Section 121 covers most home sellers, and there are exemptions for a sale at a loss, a 1031 exchange, and a sale price at or under $100,000. On a $1,200,000 sale that form is worth $40,000 of cash flow at the table. Withholding is not an extra tax, it is a prepayment credited when you file, but you wait months to see it. Sellers who are foreign persons for tax purposes face a separate 15% federal withholding under FIRPTA.",
    ),
    (
        "How accurate is this net sheet compared to the one from escrow?",
        "Close, and for the reasons that matter. The costs escrow controls (escrow fee, title premium, transfer tax, recording) are formula-driven, so those land within a couple hundred dollars. The tax proration is exact once your close date and installment status are right, which is why this calculator asks. The two lines that can move are your payoff, which depends on extra principal you have paid and the exact wire date, and any repair credits negotiated after inspections, which have not happened yet. Escrow's estimated closing statement is the binding version and arrives once you are in contract. I reconcile the two line by line before you sign.",
        "Close, and for the reasons that matter. The costs escrow controls (escrow fee, title premium, transfer tax, recording) are formula-driven, so those land within a couple hundred dollars. The tax proration is exact once your close date and installment status are right, which is why this calculator asks. The two lines that can move are your payoff, which depends on extra principal you have paid and the exact wire date, and any repair credits negotiated after inspections, which have not happened yet. Escrow's estimated closing statement is the binding version and arrives once you are in contract. I reconcile the two line by line before you sign.",
    ),
    (
        "Do I pay capital gains tax on the sale of my home?",
        "Usually not, and when you do it is on less than you think. If you owned and lived in the home as your main residence for at least 2 of the last 5 years, you exclude up to $250,000 of gain filing single or $500,000 married filing jointly. Gain is the sale price minus your selling costs minus your basis, and your basis is what you paid plus capital improvements, so a remodel, an addition, or a new roof all reduce the gain. Anything above the exclusion is federal long-term capital gains at 0%, 15%, or 20% depending on your total taxable income, plus 3.8% net investment income tax over $200,000 single or $250,000 joint, and California taxes the gain as ordinary income at up to 13.3%. The estimator on this page runs all of it, and it belongs in front of your CPA before you price.",
        "Usually not, and when you do it is on less than you think. If you owned and lived in the home as your main residence for at least 2 of the last 5 years, you exclude up to $250,000 of gain filing single or $500,000 married filing jointly. Gain is the sale price minus your selling costs minus your basis, and your basis is what you paid plus capital improvements, so a remodel, an addition, or a new roof all reduce the gain. Anything above the exclusion is federal long-term capital gains at 0%, 15%, or 20% depending on your total taxable income, plus 3.8% net investment income tax over $200,000 single or $250,000 joint, and California taxes the gain as ordinary income at up to 13.3%. The estimator on this page runs all of it, and it belongs in front of your CPA before you price.",
    ),
    (
        "Who pays escrow and title fees in Southern California?",
        "By Southern California custom, escrow fees are split evenly between buyer and seller, the seller pays the owner's title policy that insures the buyer's ownership, the buyer pays their own lender's policy, and the seller pays the county documentary transfer tax. Northern California runs differently, which is why a statewide calculator gets it wrong. None of this is law. Every line is a custom that the purchase contract can reassign, and in a competitive market who pays what becomes a negotiating lever worth real money.",
        "By Southern California custom, escrow fees are split evenly between buyer and seller, the seller pays the owner's title policy that insures the buyer's ownership, the buyer pays their own lender's policy, and the seller pays the county documentary transfer tax. Northern California runs differently, which is why a statewide calculator gets it wrong. None of this is law. Every line is a custom that the purchase contract can reassign, and in a competitive market who pays what becomes a negotiating lever worth real money.",
    ),
    (
        "What if I owe more than the house is worth?",
        "Then the net sheet comes out negative, and that is useful information rather than a dead end. Run the real payoff against a real valuation first, because a meaningful share of owners who believe they are underwater are not once the current value is in front of them. If the math truly is upside down, a short sale is a documented exit with real protections in California, and the calculator's negative number is the first page of that conversation. Start with what the home is worth, then decide.",
        "Then the net sheet comes out negative, and that is useful information rather than a dead end. Run the real payoff against a real valuation first, because a meaningful share of owners who believe they are underwater are not once the current value is in front of them. If the math truly is upside down, <a class=\"ns-a\" href=\"/short-sale/\">a short sale</a> is a documented exit with real protections in California, and the calculator's negative number is the first page of that conversation. Start with <a class=\"ns-a\" href=\"/value/\">what the home is worth</a>, then decide.",
    ),
]

FAQ_SECTION = (
    '<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">'
    '<div class="max-w_720px w_100% m_0_auto pl_32px pr_32px">'
    '<h2 class="ns-h2">Net sheet questions, answered straight.</h2>'
    '<p class="ns-sub">The money questions sellers actually ask, with the mechanics attached.</p>'
    + "".join(faq_item(i + 1, q, html) for i, (q, _plain, html) in enumerate(FAQS))
    + "</div></section>"
)

XREF_CSS = (
    '<style id="drozq-xref-css">'
    ".xr-band{padding:48px 0}.xr--warm{background:#f2f0ef}.xr--white{background:#fff}"
    ".xr-wrap{max-width:1035px;margin:0 auto;padding:0 32px;box-sizing:border-box}"
    ".xr-head{max-width:720px;margin:0 auto 28px;text-align:center}"
    ".xr-head h2{font-weight:800;opacity:.87;color:#2b2b2b;font-size:26px;line-height:34px;letter-spacing:.3px;margin:0 0 10px}"
    ".xr-head p{color:#3f4650;font-size:16px;line-height:26px;margin:0}"
    ".xr-grid{display:grid;grid-template-columns:1fr;gap:16px}"
    ".xr-card{display:block;background:#fff;border:1px solid #e5e5e5;border-radius:16px;padding:24px;text-decoration:none;"
    "color:inherit;transition:border-color .15s ease,transform .15s ease,box-shadow .15s ease;text-align:left;box-sizing:border-box}"
    ".xr--white .xr-card{background:#fbf8f4;border-color:#ece8e2}"
    ".xr-card:hover{border-color:#d92228;transform:translateY(-2px);box-shadow:0 8px 20px rgba(26,24,22,.08)}"
    ".xr-eyebrow{color:#d92228;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 8px}"
    ".xr-card h3{color:#1a1816;font-size:19px;line-height:26px;font-weight:700;margin:0 0 8px}"
    ".xr-card p{color:#3f4650;font-size:15px;line-height:23px;margin:0 0 10px}"
    ".xr-go{color:#d92228;font-weight:700;font-size:14px}"
    ".xr-a{color:#d92228;font-weight:700;text-decoration:underline;text-underline-offset:2px}"
    "@media (min-width:768px){.xr-band{padding:64px 0}.xr-head h2{font-size:32px;line-height:40px}"
    ".xr-grid--2{grid-template-columns:1fr 1fr;gap:20px}.xr-grid--3{grid-template-columns:1fr 1fr 1fr;gap:20px}}"
    "</style>"
)

XREF = (
    '<section class="xr-band xr--white"><div class="xr-wrap"><div class="xr-head">'
    "<h2>Both halves of the answer.</h2>"
    "<p>A net sheet needs a price on one side and a plan on the other.</p></div>"
    '<div class="xr-grid xr-grid--3">'
    '<a class="xr-card" href="/value/"><p class="xr-eyebrow">The price</p>'
    "<h3>What your home is worth</h3>"
    "<p>True market value, rebuild cost, the renovated ceiling, and the comps behind them, for your address, instantly.</p>"
    '<span class="xr-go">Run the valuation &rarr;</span></a>'
    '<a class="xr-card" href="/cost-to-sell/"><p class="xr-eyebrow">The costs</p>'
    "<h3>Cost to sell in Orange County</h3>"
    "<p>Every 2026 line item priced, with a worked $1,200,000 sale that nets $726,930.</p>"
    '<span class="xr-go">See the breakdown &rarr;</span></a>'
    '<a class="xr-card" href="/process/"><p class="xr-eyebrow">The plan</p>'
    "<h3>How the sale actually runs</h3>"
    "<p>Five steps from first call to closing day, with a written valuation in 24 hours and launch in 48 to 72.</p>"
    '<span class="xr-go">See the process &rarr;</span></a>'
    "</div></div></section>"
)

CLOSING_CTA = """
<section class="d_block pt_48px lg:pt_64px pb_48px lg:pb_64px bg-c_#f2f0ef">
  <div class="max-w_1035px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <div class="ta_center max-w_640px m_0_auto">
      <p class="c_#d92228 fs_11px md:fs_12px fw_700 ls_1.5px mb_12px" style="text-transform:uppercase">One number, in writing.</p>
      <h2 class="fw_800 op_0.87 c_#2b2b2b lh_40px md:lh_48px fs_28px md:fs_36px ls_0.3px ta_center mb_16px">See what your home nets before you decide anything.</h2>
      <p class="c_#3f4650 fs_16px md:fs_18px lh_28px md:lh_32px mb_32px">Drop your address and I'll come back with the valuation and the net sheet built on your actual record.</p>

      <div id="ns-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
        <div style="width:100%; max-width: 540px;">
    <form class="pos_relative">
      <div class="pos_relative d_flex flex-d_column xs:flex-d_row ai_center bg-c_#fff mb_16px xs:mb_0 h_48px sm:h_auto bdr_30px bx-sh_0_1px_5px_rgba(0,_0,_0,_.11)">
        <input name="location" placeholder="Enter your address" title="Enter your address" autocomplete="off"
               class="w_100% bd_none bg-c_transparent -webkit-appearance_none flex_1 focus:ring_none h_48px md:h_60px lh_48px md:lh_60px pt_16px md:pt_0 pb_16px md:pb_0 pl_16px md:pl_32px pr_32px xs:pr_8px mb_16px xs:mb_0 bdr-tl_30px bdr-bl_30px fs_14px md:fs_18px"
               value="" aria-label="Enter your address">
        <div class="w_100% xs:w_auto mr_0 md:mr_3px h_48px md:h_60px lh_48px md:lh_60px pos_absolute xs:pos_static top_60px xs:top_0">
          <button type="submit"
                  class="bg_primary c_white cursor_pointer w_100% xs:w_145px md:w_auto h_48px md:h_54px fs_13px md:fs_18px fw_bold bdr_full px_0px md:px_28px ls_0.5px d_block md:d_inline-flex ai_center gap_0px md:gap_10px hover:bg_primaryHover">
            Run my Valuation<span class="d_none md:d_inline-flex ai_center"><svg fill="none" height="20" viewBox="0 0 20 20" width="20" xmlns="http://www.w3.org/2000/svg"><path clip-rule="evenodd" d="m4.34063 10.8292h9.30837l-4.06671 4.0667c-.325.325-.325.8583 0 1.1833s.85001.325 1.17501 0l5.4917-5.4916c.325-.325.325-.85002 0-1.17502l-5.4917-5.49166c-.325-.32501-.85001-.32501-1.17501 0-.325.325-.325.85 0 1.17499l4.06671 4.06667h-9.30837c-.45834 0-.83334.375-.83334.83333 0 .45829.375.83329.83334.83329z" fill="#fff" fill-rule="evenodd"></path></svg></span>
          </button>
        </div>
      </div>
      <input type="hidden" name="gclid" value="">
    </form></div>
      </div>

      <p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
    </div>
  </div>
</section>
"""

# ---------------------------------------------------------------------------
# The lead-capture gate. Same posture and class vocabulary as /value/, scoped
# to .ns-gate-* so the two never collide.
GATE = """
<div id="ns-gate" class="ns-gate-overlay" aria-hidden="true">
  <div class="ns-gate-card" role="dialog" aria-modal="true" aria-labelledby="ns-gate-title" aria-describedby="ns-gate-sub">
    <button type="button" id="ns-gate-close" class="ns-gate-close" aria-label="Close">&times;</button>
    <p class="ns-gate-eyebrow">&#10003; Your county record is ready</p>
    <h2 id="ns-gate-title" class="ns-gate-title">Where should I send it?</h2>
    <p id="ns-gate-sub" class="ns-gate-sub">Purchase history, tax bills, and the net sheet for <span id="ns-gate-address" class="ns-gate-addr-em">your home</span>. Tell me where to send the written version and I'll open it right now.</p>
    <form id="ns-gate-form" novalidate>
      <div class="ns-gate-field"><input type="text" id="ns-gate-name" name="full_name" class="ns-gate-input" placeholder="Full name" autocomplete="name" autocapitalize="words" aria-label="Full name"></div>
      <div class="ns-gate-field"><input type="email" id="ns-gate-email" name="email" class="ns-gate-input" placeholder="Email" autocomplete="email" inputmode="email" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="Email"></div>
      <div class="ns-gate-field"><input type="tel" id="ns-gate-phone" name="phone" class="ns-gate-input" placeholder="Phone" autocomplete="tel" inputmode="tel" autocapitalize="off" aria-label="Phone"></div>
      <div aria-hidden="true" style="position:absolute;left:-9999px;top:-9999px;height:1px;width:1px;overflow:hidden"><input type="text" id="ns-gate-hp" name="company_website" tabindex="-1" autocomplete="off"></div>
      <p id="ns-gate-error" class="ns-gate-error" role="alert"></p>
      <button type="submit" id="ns-gate-submit" class="ns-gate-submit">Show my record</button>
    </form>
    <p class="ns-gate-fineprint">By submitting you agree Joshua Guerrero may call and text you about your home, including by automated means, at the number provided. Consent is not a condition of any purchase. Msg &amp; data rates may apply. <a href="/privacy/" target="_blank" rel="noopener">Privacy Policy</a>.</p>
  </div>
</div>
<style id="ns-gate-css">
.ns-gate-overlay{display:none;position:fixed;inset:0;z-index:12000;background:rgba(26,24,22,.62);opacity:0;transition:opacity .18s ease;align-items:center;justify-content:center;padding:20px;box-sizing:border-box;overflow-y:auto}
.ns-gate-overlay.is-open{display:flex;opacity:1}
.ns-gate-card{position:relative;background:#fff;border-radius:20px;width:100%;max-width:440px;padding:32px 24px 22px;box-shadow:0 24px 60px rgba(0,0,0,.35);transform:translateY(12px);transition:transform .18s ease;box-sizing:border-box}
.ns-gate-overlay.is-open .ns-gate-card{transform:translateY(0)}
.ns-gate-close{position:absolute;top:10px;right:12px;width:36px;height:36px;border:none;background:transparent;color:#757575;font-size:26px;line-height:1;cursor:pointer;border-radius:9999px}
.ns-gate-close:hover{color:#1a1816;background:#f2efea}
.ns-gate-eyebrow{color:#d92228;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 10px}
.ns-gate-title{color:#1a1816;font-size:26px;line-height:32px;font-weight:800;margin:0 0 10px}
.ns-gate-sub{color:#3f4650;font-size:14px;line-height:21px;margin:0 0 18px}
.ns-gate-addr-em{font-weight:700;color:#1a1816}
.ns-gate-field{margin:0 0 12px}
.ns-gate-input{width:100%;height:50px;border:1px solid #d3cfca;border-radius:12px;padding:0 14px;font-size:16px;font-family:inherit;color:#1a1816;background:#fff;box-sizing:border-box;outline:none}
.ns-gate-input::placeholder{color:#9a948c}
.ns-gate-input:focus{border-color:#d92228}
.ns-gate-input.is-error{border-color:#d92228;background:#fdf3f3}
.ns-gate-error{display:none;color:#d92228;font-size:13px;font-weight:700;margin:0 0 10px}
.ns-gate-error.is-shown{display:block}
.ns-gate-submit{width:100%;height:52px;border:none;border-radius:9999px;background:#d92228;color:#fff;font-family:inherit;font-weight:700;font-size:16px;cursor:pointer}
.ns-gate-submit:hover{background:#a92e2a}
.ns-gate-submit:disabled{opacity:.7;cursor:default}
.ns-gate-fineprint{color:#757575;font-size:11px;line-height:16px;margin:14px 0 0}
.ns-gate-fineprint a{color:#757575;text-decoration:underline}
@media (min-width:480px){.ns-gate-card{padding:38px 32px 26px}.ns-gate-title{font-size:29px;line-height:35px}}
</style>
"""

# ---------------------------------------------------------------------------
# Structured data. BreadcrumbList + WebApplication (the calculator is the
# primary entity on this page) + FAQPage. The global RealEstateAgent /
# LocalBusiness / WebSite blocks ride along in the inherited <head>.

BREADCRUMB_LD = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://drozq.com/"},
        {"@type": "ListItem", "position": 2, "name": "For Sellers", "item": "https://drozq.com/sellers/"},
        {"@type": "ListItem", "position": 3, "name": "Seller Net Sheet", "item": CANONICAL},
    ],
}

APP_LD = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "@id": "https://drozq.com/net-sheet/#tool",
    "name": "Drozq Seller Net Sheet Calculator",
    "url": CANONICAL,
    "applicationCategory": "FinanceApplication",
    "operatingSystem": "All",
    "browserRequirements": "Requires JavaScript.",
    "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    "isAccessibleForFree": True,
    "description": (
        "A California seller net sheet calculator that starts from the county record: recorded "
        "purchase price and date, multi-year property tax bills, assessed value, Mello-Roos and "
        "special assessment detection, escrow tax proration on your close date, a mortgage payoff "
        "solved from your monthly payment, county and city documentary transfer tax, FTB Form 593 "
        "withholding, and a capital gains estimate."
    ),
    "featureList": [
        "County property tax bill history",
        "Assessed value and effective tax rate",
        "Mello-Roos and special assessment detection",
        "Recorded purchase price and date",
        "Owner of record",
        "California property tax proration by close date",
        "Mortgage payoff solved from your monthly payment",
        "Loan amortization from original terms",
        "County and city documentary transfer tax including Measure ULA",
        "Escrow, title, and seller-paid closing costs",
        "HOA dues proration and demand fees",
        "California Form 593 and FIRPTA withholding",
        "Capital gains estimate with the Section 121 exclusion",
        "Printable net sheet",
    ],
    "provider": {"@id": "https://drozq.com/#realestateagent"},
    "areaServed": {"@type": "AdministrativeArea", "name": "California"},
    "inLanguage": "en-US",
}


def build_faq_ld():
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": "https://drozq.com/net-sheet/#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": plain},
            }
            for (q, plain, _html) in FAQS
        ],
    }


def ld_script(obj):
    import json

    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


# ---------------------------------------------------------------------------


def main() -> int:
    from net_sheet_js import JS

    src = BASE.read_text(encoding="utf-8")

    # --- head: title / description / canonical / og / twitter ---------------
    def sub_once(pattern, repl, text, what):
        new, n = re.subn(pattern, lambda _m: repl, text, count=1)
        if n != 1:
            raise SystemExit(f"build_net_sheet: expected exactly 1 {what}, got {n}")
        return new

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

    # --- main body ----------------------------------------------------------
    main_open = src.find("<main ")
    if main_open < 0:
        raise SystemExit("build_net_sheet: could not find <main> in the base page")
    main_open_end = src.find(">", main_open) + 1
    main_close = src.find("</main>", main_open_end)
    if main_close < 0:
        raise SystemExit("build_net_sheet: could not find </main> in the base page")

    body = (
        HERO
        + CSS
        + TOOL
        + QUICK_ANSWER
        + LINE_ITEMS
        + PRORATION
        + MELLO
        + PAYOFF_EXPLAINER
        + TWO_TAXES
        + DIFFERENCE
        + FAQ_SECTION
        + XREF_CSS
        + XREF
        + CLOSING_CTA
        + GATE
        + JS
        + ld_script(BREADCRUMB_LD)
        + ld_script(APP_LD)
        + ld_script(build_faq_ld())
    )

    out = src[:main_open_end] + body + src[main_close:]

    # --- guardrails ---------------------------------------------------------
    if "—" in body:
        raise SystemExit("build_net_sheet: em dash (U+2014) found in the page body. Banned.")
    for marker in ("DROZQ_FUNNEL_HTML_BEGIN", "DROZQ_FUNNEL_HTML_END",
                   "DROZQ_FUNNEL_JS_BEGIN", "DROZQ_FUNNEL_JS_END"):
        if out.count(marker) != 1:
            raise SystemExit(f"build_net_sheet: funnel marker {marker} count is {out.count(marker)}, expected 1")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(out, encoding="utf-8")
    print(f"Built: net-sheet/index.html ({len(out):,} chars, body {len(body):,})")
    return 0


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
