"""
extract_panda_css.py
Move the compiled Panda utility soup out of every page's <head> into ONE
cacheable stylesheet.

Before 2026-08-26 every template page carried the identical ~152 KB
<style data-inlined="desktop"> block inline, so every navigation re-downloaded
it (render-blocking, zero cross-page caching: ~180 KB of CSS per page view).
This script writes that block (taken from /index.html, the source of truth) to
/media/css/panda.css and replaces the inline block on every registered page
with <link rel="stylesheet" href="/media/css/panda.css?v=<hash>"> at the SAME
position, so cascade + @layer order are unchanged. The per-page
drozq-page-chrome / Galano override / drozq-panda-patch blocks stay inline.

Safety: a page whose soup differs from index.html's (beyond whitespace) is
reported and left untouched. Idempotent: pages already on the <link> are
re-pointed to the current hash only. Bytes in, bytes out (BOM + EOL kept).

Usage:
    python scripts/extract_panda_css.py            # extract / refresh
    python scripts/extract_panda_css.py --check    # report only
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = ROOT / "media" / "css" / "panda.css"
HREF = "/media/css/panda.css"
BOM = b"\xef\xbb\xbf"
STYLE_RE = re.compile(r'<style data-inlined="desktop">(.*?)</style>', re.S)
LINK_RE = re.compile(r'<link rel="stylesheet" href="' + re.escape(HREF) + r'(?:\?v=[0-9a-f]+)?">')


def norm(css: str) -> str:
    return re.sub(r"\s+", " ", css).strip()


def read(p: Path):
    raw = p.read_bytes()
    bom = raw.startswith(BOM)
    return bom, (raw[len(BOM):] if bom else raw).decode("utf-8")


def write(p: Path, bom: bool, text: str) -> None:
    p.write_bytes((BOM if bom else b"") + text.encode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    reg = json.loads((ROOT / "funnels.json").read_text(encoding="utf-8"))
    pages = [reg["source"]] + [p for p in reg["pages"] if p != reg["source"]]

    # Source of truth: index.html's inline soup, or the already-extracted file.
    _, src = read(ROOT / reg["source"])
    m = STYLE_RE.search(src)
    if m:
        css = m.group(1)
    elif CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")
    else:
        print("ERROR: no inline soup on index.html and no media/css/panda.css", file=sys.stderr)
        return 2
    digest = hashlib.sha256(css.encode("utf-8")).hexdigest()[:10]
    link = f'<link rel="stylesheet" href="{HREF}?v={digest}">'
    ref = norm(css)

    if not args.check:
        CSS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not CSS_PATH.exists() or CSS_PATH.read_text(encoding="utf-8") != css:
            CSS_PATH.write_text(css, encoding="utf-8")
            print(f"WROTE  {CSS_PATH.relative_to(ROOT).as_posix()} ({len(css):,} chars, v={digest})")

    rc = 0
    for rel in pages:
        p = ROOT / rel
        bom, text = read(p)
        m = STYLE_RE.search(text)
        if m:
            if norm(m.group(1)) != ref:
                print(f"ERROR  {rel}: inline soup differs from index.html (not touched)", file=sys.stderr)
                rc = 2
                continue
            new = text[:m.start()] + link + text[m.end():]
            action = "EXTRACT"
        elif LINK_RE.search(text):
            new = LINK_RE.sub(link, text, count=1)
            action = "REPOINT" if new != text else "OK     "
        else:
            print(f"ERROR  {rel}: neither inline soup nor stylesheet link found", file=sys.stderr)
            rc = 2
            continue
        if new == text:
            print(f"OK      {rel}")
            continue
        if args.check:
            print(f"WOULD {action} {rel}")
        else:
            write(p, bom, new)
            print(f"{action} {rel}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
