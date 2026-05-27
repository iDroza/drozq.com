"""One-shot: insert "Home Prices" -> /prices/ into the header nav on every
page, positioned directly after "Mortgage Rates" so the final order is:
  FAQ -> Mortgage Rates -> Home Prices -> For Buyers -> For Sellers -> Home Value

Same structural pattern as scripts/nav_swap_tips_to_rates.py:
  (1) Mobile drawer: <ul data-testid="mobile-nav-items">
  (2) Desktop "More" popup: <ul id="drozq-more-menu">

Both fragments are literal find/replace on the exact HTML shipped by
scaffold_page.py from /index.html, so the OLD strings here match every
registered page byte-for-byte. Idempotent: if a page already has the
new nav, the find/replace is a no-op and the file is left untouched.

Usage:
    python scripts/nav_add_home_prices.py
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "funnels.json"

MOBILE_OLD = (
    '<li><a href="/faq/" class="d_flex ai_center gap_3"><span>FAQ</span></a></li>'
    '<li><a href="/rates/" class="d_flex ai_center gap_3"><span>Mortgage Rates</span></a></li>'
    '<li><a href="/#tab-buy" class="d_flex ai_center gap_3"><span>For Buyers</span></a></li>'
)
MOBILE_NEW = (
    '<li><a href="/faq/" class="d_flex ai_center gap_3"><span>FAQ</span></a></li>'
    '<li><a href="/rates/" class="d_flex ai_center gap_3"><span>Mortgage Rates</span></a></li>'
    '<li><a href="/prices/" class="d_flex ai_center gap_3"><span>Home Prices</span></a></li>'
    '<li><a href="/#tab-buy" class="d_flex ai_center gap_3"><span>For Buyers</span></a></li>'
)

MORE_OLD = (
    '<li role="none"><a role="menuitem" href="/faq/">FAQ</a></li>'
    '<li role="none"><a role="menuitem" href="/rates/">Mortgage Rates</a></li>'
    '<li role="none"><a role="menuitem" href="/#tab-buy">For Buyers</a></li>'
)
MORE_NEW = (
    '<li role="none"><a role="menuitem" href="/faq/">FAQ</a></li>'
    '<li role="none"><a role="menuitem" href="/rates/">Mortgage Rates</a></li>'
    '<li role="none"><a role="menuitem" href="/prices/">Home Prices</a></li>'
    '<li role="none"><a role="menuitem" href="/#tab-buy">For Buyers</a></li>'
)


def targets():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return ["index.html"] + list(reg.get("pages", []))


def main() -> int:
    changed = skipped = missing = 0
    for rel in targets():
        p = ROOT / rel
        if not p.exists():
            print(f"MISSING {rel}")
            missing += 1
            continue
        text = p.read_text(encoding="utf-8")
        original = text
        if MOBILE_OLD in text:
            text = text.replace(MOBILE_OLD, MOBILE_NEW)
        if MORE_OLD in text:
            text = text.replace(MORE_OLD, MORE_NEW)
        if text != original:
            p.write_text(text, encoding="utf-8")
            print(f"UPDATED {rel}")
            changed += 1
        else:
            already = MOBILE_NEW in text and MORE_NEW in text
            tag = "OK" if already else "NO-MATCH"
            print(f"{tag:<8} {rel}")
            skipped += 1
    print(f"\nSummary: updated={changed}, skipped={skipped}, missing={missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
