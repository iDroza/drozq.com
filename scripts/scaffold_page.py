"""
scaffold_page.py
Migrate or scaffold a page from the homepage template.

Copies /index.html to a target path, surgically replaces meta tags and the
<main> body content with page-specific values, leaves the funnel sync
markers + footer + mobile-nav + funnel JS intact (the funnel is propagated
separately via scripts/sync_funnels.py).

Usage:
    from scaffold_page import scaffold_page
    scaffold_page(
        target='los-angeles/index.html',
        title='Sell Your Los Angeles Home | Joshua Guerrero, Real Brokerage',
        description='Selling a home in Los Angeles or the South Bay? ...',
        canonical='/los-angeles/',
        main_body_html='<section ...>...</section>',
        noindex=False,
    )

The script is invoked from the project root with `python scripts/scaffold_page.py`
to migrate a hardcoded list of pages, OR imported as a module by another script
to migrate one page at a time.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "index.html"

DROZQ_DOMAIN = "https://drozq.com"


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def replace_meta(text: str, key: str, value: str) -> str:
    """Replace the content="..." on a meta whose property="key" or name="key"."""
    pattern = re.compile(
        rf'(<meta\s+(?:property|name)="{re.escape(key)}"\s+content=")[^"]*(")',
        re.IGNORECASE,
    )
    new_text, n = pattern.subn(rf'\g<1>{html_escape(value)}\g<2>', text, count=1)
    if n == 0:
        # Meta tag doesn't exist; nothing to replace. Caller can choose to handle.
        return text
    return new_text


def scaffold_page(
    *,
    target: str,
    title: str,
    description: str,
    canonical: str,
    main_body_html: str,
    og_title: str | None = None,
    og_description: str | None = None,
    twitter_title: str | None = None,
    twitter_description: str | None = None,
    og_image: str | None = None,
    noindex: bool = False,
) -> None:
    """Build a new page at `target` (relative to repo root) from the homepage scaffold.

    The new page inherits everything from /index.html EXCEPT:
    - <title>, <meta description>, <link canonical>, og:*, twitter:* are page-specific
    - <main>...</main> body is replaced with main_body_html
    - <meta robots> is inserted if noindex=True

    Funnel HTML/JS sync markers are preserved verbatim so the resulting page is
    immediately registerable in funnels.json.
    """
    src = SOURCE.read_text(encoding="utf-8")

    # --- title ---
    src = re.sub(r'<title>[^<]*</title>',
                 f'<title>{html_escape(title)}</title>',
                 src, count=1)

    # --- meta description ---
    src = replace_meta(src, 'description', description)

    # --- canonical ---
    canonical_full = canonical if canonical.startswith('http') else DROZQ_DOMAIN + canonical
    src = re.sub(r'<link\s+rel="canonical"\s+href="[^"]*">',
                 f'<link rel="canonical" href="{html_escape(canonical_full)}">',
                 src, count=1)

    # --- og tags ---
    src = replace_meta(src, 'og:url', canonical_full)
    src = replace_meta(src, 'og:title', og_title or title)
    src = replace_meta(src, 'og:description', og_description or description)
    if og_image:
        src = replace_meta(src, 'og:image', og_image)

    # --- twitter tags ---
    src = replace_meta(src, 'twitter:title', twitter_title or og_title or title)
    src = replace_meta(src, 'twitter:description',
                       twitter_description or og_description or description)

    # --- robots noindex ---
    if noindex:
        if re.search(r'<meta\s+name="robots"\s+content="[^"]*">', src):
            src = re.sub(r'<meta\s+name="robots"\s+content="[^"]*">',
                         '<meta name="robots" content="noindex,follow">',
                         src, count=1)
        else:
            # Insert before canonical link
            src = src.replace(
                '<link rel="canonical"',
                '<meta name="robots" content="noindex,follow"><link rel="canonical"',
                1,
            )

    # --- main body replacement ---
    main_open = src.find('<main ')
    if main_open < 0:
        # Fall back to <main> without attrs
        main_open = src.find('<main>')
        if main_open < 0:
            raise RuntimeError("Could not find <main> tag in /index.html")
        main_open_end = main_open + len('<main>')
    else:
        main_open_end = src.find('>', main_open) + 1

    main_close = src.find('</main>', main_open_end)
    if main_close < 0:
        raise RuntimeError("Could not find </main> tag in /index.html")

    new_src = src[:main_open_end] + main_body_html + src[main_close:]

    # --- write ---
    target_path = ROOT / target
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(new_src, encoding="utf-8")
    print(f"Scaffolded: {target} ({len(new_src):,} chars)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnose", action="store_true",
                    help="Print where <main> opens and closes in /index.html (sanity check).")
    args = ap.parse_args()

    if args.diagnose:
        src = SOURCE.read_text(encoding="utf-8")
        mo = src.find('<main ')
        mc = src.find('</main>', mo)
        print(f"<main opens at byte {mo}")
        print(f"</main> opens at byte {mc}")
        print(f"main body length: {mc - mo:,} chars")
        return 0

    print("scaffold_page is a library. Import it from another script to scaffold a page.")
    print("Use --diagnose to verify the source <main> can be located.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
