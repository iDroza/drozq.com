"""
wrap_chrome_markers.py
One-shot (idempotent) marker installer for the shared page chrome.

Until 2026-08-26 the header, footer, mobile-nav script and the head-level
"hide the header for new desktop visitors" script were hand-copied onto every
page. They happened to be byte-identical everywhere, but nothing enforced it.
This script wraps each of those four blocks in DROZQ_* marker comments on
/index.html and on every page registered in funnels.json, so the existing
sync tool (scripts/sync_funnels.py) can own them exactly like the funnel:

    <!-- DROZQ_HEADER_JS_BEGIN --> ... <!-- DROZQ_HEADER_JS_END -->   (in <head>)
    <!-- DROZQ_HEADER_BEGIN -->    ... <!-- DROZQ_HEADER_END -->      (the <header>)
    <!-- DROZQ_FOOTER_BEGIN -->    ... <!-- DROZQ_FOOTER_END -->      (the <footer>)
    <!-- DROZQ_NAV_JS_BEGIN -->    ... <!-- DROZQ_NAV_JS_END -->      (mobile drawer /
                                                                      More popup script)

Safety:
  * count-guarded: every anchor must match exactly once or the page is skipped
    with an error and NOTHING is written for it;
  * every sibling block must be byte-identical to /index.html's block before it
    is wrapped (a drifted page is reported, not silently adopted);
  * idempotent: a page that already carries a marker pair is left untouched;
  * BOM + line endings preserved (bytes in, bytes out).

Usage:
    python scripts/wrap_chrome_markers.py            # wrap
    python scripts/wrap_chrome_markers.py --check    # report only, write nothing
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "funnels.json"
BOM = b"\xef\xbb\xbf"

# name -> (begin comment, end comment, locator)
# locator(text) -> (start, end) of the block to wrap, or raises ValueError.


def _one(text: str, needle: str, label: str) -> int:
    n = text.count(needle)
    if n != 1:
        raise ValueError(f"{label}: expected exactly 1 match of {needle!r}, found {n}")
    return text.find(needle)


def locate_header(text: str):
    start = _one(text, '<div id="__next"><header ', "header") + len('<div id="__next">')
    end = text.find("</header>", start)
    if end < 0:
        raise ValueError("header: no </header> after the open tag")
    return start, end + len("</header>")


def locate_footer(text: str):
    start = _one(text, "<footer", "footer")
    _one(text, "</footer>", "footer close")
    end = text.find("</footer>", start) + len("</footer>")
    return start, end


def locate_nav_js(text: str):
    key = 'document.getElementById("drozq-hamburger")'
    at = _one(text, key, "nav js")
    start = text.rfind("<script", 0, at)
    if start < 0:
        raise ValueError("nav js: no <script before the hamburger wiring")
    end = text.find("</script>", at)
    if end < 0:
        raise ValueError("nav js: no </script> after the hamburger wiring")
    return start, end + len("</script>")


def locate_header_js(text: str):
    key = "localStorage.getItem('drozq_header_revealed')"
    at = _one(text, key, "header js")
    start = text.rfind("<script", 0, at)
    end = text.find("</script>", at)
    if start < 0 or end < 0:
        raise ValueError("header js: script tag not bounded")
    return start, end + len("</script>")


BLOCKS = {
    "header_js": ("<!-- DROZQ_HEADER_JS_BEGIN -->", "<!-- DROZQ_HEADER_JS_END -->", locate_header_js),
    "header":    ("<!-- DROZQ_HEADER_BEGIN -->",    "<!-- DROZQ_HEADER_END -->",    locate_header),
    "footer":    ("<!-- DROZQ_FOOTER_BEGIN -->",    "<!-- DROZQ_FOOTER_END -->",    locate_footer),
    "nav_js":    ("<!-- DROZQ_NAV_JS_BEGIN -->",    "<!-- DROZQ_NAV_JS_END -->",    locate_nav_js),
}


def read(path: Path):
    raw = path.read_bytes()
    bom = raw.startswith(BOM)
    return bom, raw[len(BOM):].decode("utf-8") if bom else raw.decode("utf-8")


def write(path: Path, bom: bool, text: str) -> None:
    path.write_bytes((BOM if bom else b"") + text.encode("utf-8"))


def block_inner(text: str, name: str) -> str:
    """The block content, whether or not it is already wrapped."""
    begin, end, locate = BLOCKS[name]
    if begin in text:
        b = text.find(begin) + len(begin)
        e = text.find(end, b)
        if e < 0:
            raise ValueError(f"{name}: begin marker without end marker")
        return text[b:e]
    s, e = locate(text)
    return text[s:e]


def wrap(text: str, name: str):
    """Return (new_text, changed)."""
    begin, end, locate = BLOCKS[name]
    if begin in text:
        if end not in text:
            raise ValueError(f"{name}: begin marker present but end marker missing")
        return text, False
    s, e = locate(text)
    return text[:s] + begin + text[s:e] + end + text[e:], True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Report only; write nothing.")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    source_rel = reg["source"]
    pages = [source_rel] + [p for p in reg["pages"] if p != source_rel]

    _, source_text = read(ROOT / source_rel)
    source_inner = {}
    for name in BLOCKS:
        try:
            source_inner[name] = block_inner(source_text, name)
        except ValueError as e:
            print(f"ERROR source {source_rel}: {e}", file=sys.stderr)
            return 2

    rc = 0
    for rel in pages:
        path = ROOT / rel
        if not path.exists():
            print(f"MISSING {rel}")
            rc = 2
            continue
        bom, text = read(path)
        new_text = text
        changed = []
        errors = []
        for name in BLOCKS:
            try:
                inner = block_inner(new_text, name)
                if rel != source_rel and inner != source_inner[name]:
                    errors.append(f"{name}:drift-vs-source")
                    continue
                new_text, did = wrap(new_text, name)
                if did:
                    changed.append(name)
            except ValueError as e:
                errors.append(f"{name}:{e}")
        if errors:
            rc = 2
            print(f"ERROR  {rel}: {'; '.join(errors)}  (not written)", file=sys.stderr)
            continue
        if not changed:
            print(f"OK     {rel}")
        elif args.check:
            print(f"WOULD  {rel}: {', '.join(changed)}")
        else:
            write(path, bom, new_text)
            print(f"WRAPPED {rel}: {', '.join(changed)}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
