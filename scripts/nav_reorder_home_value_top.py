"""One-shot: reorder the header nav on every page so "Home Value" is first and
"FAQ" is last. The four middle items keep their order. Final order:
  Home Value -> Mortgage Rates -> Home Prices -> For Buyers -> For Sellers -> FAQ

Same structural pattern as scripts/nav_add_home_prices.py:
  (1) Mobile drawer:       <ul data-testid="mobile-nav-items">
  (2) Desktop "More" popup: <ul id="drozq-more-menu">

Both fragments are literal find/replace on the exact HTML shipped by
scaffold_page.py from /index.html, so the OLD strings here match every
registered page byte-for-byte (including the minified /index.html line; the
﻿ BOM, if present, lives at the start of the file and is preserved by the
utf-8 read/write round-trip). Idempotent: if a page already has the new order,
the find/replace is a no-op and the file is left untouched.

Usage:
    python scripts/nav_reorder_home_value_top.py
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "funnels.json"

# ---- Mobile drawer list -----------------------------------------------------
_M = '<ul data-testid="mobile-nav-items">'
_M_FAQ    = '<li><a href="/faq/" class="d_flex ai_center gap_3"><span>FAQ</span></a></li>'
_M_RATES  = '<li><a href="/rates/" class="d_flex ai_center gap_3"><span>Mortgage Rates</span></a></li>'
_M_PRICES = '<li><a href="/prices/" class="d_flex ai_center gap_3"><span>Home Prices</span></a></li>'
_M_BUY    = '<li><a href="/#tab-buy" class="d_flex ai_center gap_3"><span>For Buyers</span></a></li>'
_M_SELL   = '<li><a href="/#tab-sell" class="d_flex ai_center gap_3"><span>For Sellers</span></a></li>'
_M_VALUE  = '<li><a href="/value/" class="d_flex ai_center gap_3"><span>Home Value</span></a></li>'

MOBILE_OLD = _M + _M_FAQ   + _M_RATES + _M_PRICES + _M_BUY + _M_SELL + _M_VALUE + '</ul>'
MOBILE_NEW = _M + _M_VALUE + _M_RATES + _M_PRICES + _M_BUY + _M_SELL + _M_FAQ   + '</ul>'

# ---- Desktop "More" popup list ----------------------------------------------
_D = '<ul id="drozq-more-menu" role="menu" aria-labelledby="drozq-more-toggle">'
_D_FAQ    = '<li role="none"><a role="menuitem" href="/faq/">FAQ</a></li>'
_D_RATES  = '<li role="none"><a role="menuitem" href="/rates/">Mortgage Rates</a></li>'
_D_PRICES = '<li role="none"><a role="menuitem" href="/prices/">Home Prices</a></li>'
_D_BUY    = '<li role="none"><a role="menuitem" href="/#tab-buy">For Buyers</a></li>'
_D_SELL   = '<li role="none"><a role="menuitem" href="/#tab-sell">For Sellers</a></li>'
_D_VALUE  = '<li role="none"><a role="menuitem" href="/value/">Home Value</a></li>'

MORE_OLD = _D + _D_FAQ   + _D_RATES + _D_PRICES + _D_BUY + _D_SELL + _D_VALUE + '</ul>'
MORE_NEW = _D + _D_VALUE + _D_RATES + _D_PRICES + _D_BUY + _D_SELL + _D_FAQ   + '</ul>'


def targets():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return ["index.html"] + list(reg.get("pages", []))


def _apply(text, old, new, label, rel, problems):
    """Replace `old` with `new` exactly once; tolerate already-applied files."""
    if new in text:
        return text  # idempotent: already reordered
    n = text.count(old)
    if n == 1:
        return text.replace(old, new)
    problems.append(f"{rel}: {label} matched {n} times (expected 1)")
    return text


def main() -> int:
    changed = ok = missing = 0
    problems = []
    for rel in targets():
        p = ROOT / rel
        if not p.exists():
            print(f"MISSING  {rel}")
            missing += 1
            continue
        text = p.read_text(encoding="utf-8")  # preserves a leading ﻿ BOM
        original = text
        text = _apply(text, MOBILE_OLD, MOBILE_NEW, "mobile", rel, problems)
        text = _apply(text, MORE_OLD, MORE_NEW, "more", rel, problems)
        if text != original:
            p.write_text(text, encoding="utf-8")
            print(f"UPDATED  {rel}")
            changed += 1
        else:
            print(f"OK       {rel}")
            ok += 1
    print(f"\nSummary: updated={changed}, ok={ok}, missing={missing}")
    if problems:
        print("\nPROBLEMS (no file written for these):")
        for pr in problems:
            print("  " + pr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
