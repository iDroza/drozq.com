#!/usr/bin/env python3
"""Insert the FollowUpBoss Widget Tracker pixel (WT-AETGAYMU) into the <head> of
every Drozq page, immediately after the GTM container snippet.

The pixel is part of the tracking stack: it ships on every real page (each is an
index.html that carries the GTM container). Partials with no <head>
(header.html / footer.html) are excluded automatically because they lack the GTM
anchor.

Idempotent, count-guarded, BOM-preserving:
  - the GTM end comment is a unique per-page anchor, so the pixel lands in exactly
    one spot, grouped with the rest of the tracking stack;
  - re-running is a no-op on any page that already carries the pixel;
  - a leading UTF-8 BOM is preserved byte-for-byte.

Usage:
    python scripts/add_fub_pixel.py          # patch every page (default)
    python scripts/add_fub_pixel.py --check   # exit non-zero if any page lacks the pixel
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Unique per-page anchor: the closing comment of the GTM head snippet.
ANCHOR = "<!-- End Google Tag Manager -->"

# FollowUpBoss Widget Tracker, whitespace-collapsed from the support snippet so the
# minified <head> line stays a single line. The JS is logically identical to the
# original (every collapsed newline sat between tokens where whitespace is
# insignificant). Wrapped in the begin/end comments FUB ships with so it stays
# greppable and surgically removable.
PIXEL = (
    "<!-- begin Widget Tracker Code -->"
    "<script>"
    '(function(w,i,d,g,e,t){w["WidgetTrackerObject"]=g;(w[g]=w[g]||function()'
    '{(w[g].q=w[g].q||[]).push(arguments);}),(w[g].ds=1*new Date());(e="script"),'
    "(t=d.createElement(e)),(e=d.getElementsByTagName(e)[0]);t.async=1;t.src=i;"
    "e.parentNode.insertBefore(t,e);})"
    '(window,"https://widgetbe.com/agent",document,"widgetTracker");'
    'window.widgetTracker("create", "WT-AETGAYMU");'
    'window.widgetTracker("send", "pageview");'
    "</script>"
    "<!-- end Widget Tracker Code -->"
)

# Presence of the FUB account id is the idempotency check.
MARKER = "WT-AETGAYMU"


def pages():
    """Every real page: an index.html that carries the GTM container."""
    out = []
    for p in ROOT.rglob("index.html"):
        if ANCHOR in p.read_text(encoding="utf-8"):
            out.append(p)
    return sorted(out)


def main():
    check = "--check" in sys.argv
    rel = lambda p: p.relative_to(ROOT).as_posix()
    patched, present, missing = [], [], []

    for path in pages():
        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig") if bom else raw.decode("utf-8")

        if MARKER in text:
            present.append(path)
            continue
        if check:
            missing.append(path)
            continue

        n = text.count(ANCHOR)
        assert n == 1, f"{rel(path)}: expected exactly 1 GTM anchor, found {n}"
        text = text.replace(ANCHOR, ANCHOR + PIXEL)
        out = text.encode("utf-8")
        if bom:
            out = b"\xef\xbb\xbf" + out
        path.write_bytes(out)
        patched.append(path)

    if check:
        for p in present:
            print(f"OK       {rel(p)}")
        for p in missing:
            print(f"MISSING  {rel(p)}")
        if missing:
            print(f"\n{len(missing)} page(s) missing the FUB pixel.")
            sys.exit(1)
        print(f"\nAll {len(present)} page(s) carry the FUB pixel.")
        return

    for p in patched:
        print(f"PATCHED  {rel(p)}")
    for p in present:
        print(f"SKIP     {rel(p)} (already present)")
    print(f"\n{len(patched)} patched, {len(present)} already present, "
          f"{len(patched) + len(present)} total pages.")


if __name__ == "__main__":
    main()
