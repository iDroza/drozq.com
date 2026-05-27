"""One-shot: replace the header nav's "Tips" entry with "Mortgage Rates"
(linked to /rates/) and reorder so the sequence is:
  FAQ -> Mortgage Rates -> For Buyers -> For Sellers -> Home Value

Two structurally identical nav fragments live on every registered page:
  (1) Mobile drawer: <ul data-testid="mobile-nav-items">
  (2) Desktop "More" popup: <ul id="drozq-more-menu">

Both were scaffolded from /index.html via scripts/scaffold_page.py, so the
exact HTML strings are identical across all pages. This script does a
literal find/replace on each known page, plus on /index.html itself so
future re-scaffolds inherit the new nav.

Idempotent: if a page already has the new nav, the find/replace is a
no-op and the file is left untouched. Run safely as many times as you
want.

Usage:
    python scripts/nav_swap_tips_to_rates.py
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "funnels.json"

MOBILE_OLD = (
    '<ul data-testid="mobile-nav-items">'
    '<li><a href="/faq/" class="d_flex ai_center gap_3"><span>FAQ</span></a></li>'
    '<li><a href="/#tab-buy" class="d_flex ai_center gap_3"><span>For Buyers</span></a></li>'
    '<li><a href="/#tab-sell" class="d_flex ai_center gap_3"><span>For Sellers</span></a></li>'
    '<li><a href="/#top" class="d_flex ai_center gap_3"><span>Home Value</span></a></li>'
    '<li><a class="d_flex ai_center gap_3"><span>Tips</span></a></li>'
    '</ul>'
)
MOBILE_NEW = (
    '<ul data-testid="mobile-nav-items">'
    '<li><a href="/faq/" class="d_flex ai_center gap_3"><span>FAQ</span></a></li>'
    '<li><a href="/rates/" class="d_flex ai_center gap_3"><span>Mortgage Rates</span></a></li>'
    '<li><a href="/#tab-buy" class="d_flex ai_center gap_3"><span>For Buyers</span></a></li>'
    '<li><a href="/#tab-sell" class="d_flex ai_center gap_3"><span>For Sellers</span></a></li>'
    '<li><a href="/#top" class="d_flex ai_center gap_3"><span>Home Value</span></a></li>'
    '</ul>'
)

MORE_OLD = (
    '<ul id="drozq-more-menu" role="menu" aria-labelledby="drozq-more-toggle">'
    '<li role="none"><a role="menuitem" href="/faq/">FAQ</a></li>'
    '<li role="none"><a role="menuitem" href="/#tab-buy">For Buyers</a></li>'
    '<li role="none"><a role="menuitem" href="/#tab-sell">For Sellers</a></li>'
    '<li role="none"><a role="menuitem" href="/#top">Home Value</a></li>'
    '<li role="none"><a role="menuitem">Tips</a></li>'
    '</ul>'
)
MORE_NEW = (
    '<ul id="drozq-more-menu" role="menu" aria-labelledby="drozq-more-toggle">'
    '<li role="none"><a role="menuitem" href="/faq/">FAQ</a></li>'
    '<li role="none"><a role="menuitem" href="/rates/">Mortgage Rates</a></li>'
    '<li role="none"><a role="menuitem" href="/#tab-buy">For Buyers</a></li>'
    '<li role="none"><a role="menuitem" href="/#tab-sell">For Sellers</a></li>'
    '<li role="none"><a role="menuitem" href="/#top">Home Value</a></li>'
    '</ul>'
)


def targets():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return ["index.html"] + list(reg.get("pages", []))


def main() -> int:
    changed = 0
    skipped = 0
    missing = 0
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
            # Already updated, or the source markup doesn't match.
            already = MOBILE_NEW in text and MORE_NEW in text
            tag = "OK" if already else "NO-MATCH"
            print(f"{tag:<8} {rel}")
            skipped += 1
    print(f"\nSummary: updated={changed}, skipped={skipped}, missing={missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
