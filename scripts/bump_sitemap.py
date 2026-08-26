"""
bump_sitemap.py
Stamp every <lastmod> in sitemap.xml from git: the commit date of the last
change to that URL's HTML file (or today's date for a file with uncommitted
changes, since it is about to be committed).

Why: lastmod was hand-maintained and drifted behind sitewide edits (the
2026-08-25 copy pass and the 2026-08-26 chrome sync touched every page while
every lastmod still read July/early August). Search engines treat a stale
lastmod as "nothing new here".

Usage:
    python scripts/bump_sitemap.py            # rewrite sitemap.xml
    python scripts/bump_sitemap.py --check    # exit 1 if any lastmod is stale
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"


def url_to_file(url: str) -> Path | None:
    path = url.replace("https://drozq.com", "").lstrip("/")
    if path == "":
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path / "index.html"
    if path.endswith(".html"):
        return ROOT / path
    # slash-less entries (e.g. /dashboard) map to the directory index
    return ROOT / path / "index.html"


def git_date(path: Path) -> str | None:
    rel = path.relative_to(ROOT).as_posix()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        return dt.date.today().isoformat()
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    return out or None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    raw = SITEMAP.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    stale = []

    def repl(m: re.Match) -> str:
        url, old = m.group(1), m.group(2)
        f = url_to_file(url)
        if not f or not f.exists():
            print(f"WARN no file for {url}", file=sys.stderr)
            return m.group(0)
        new = git_date(f) or old
        if new != old:
            stale.append((url, old, new))
        return m.group(0).replace(f"<lastmod>{old}</lastmod>", f"<lastmod>{new}</lastmod>")

    new_text = re.sub(r"<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>", repl, text, flags=re.S)
    for url, old, new in stale:
        print(f"{'STALE ' if args.check else 'BUMP  '}{url}: {old} -> {new}")
    if args.check:
        return 1 if stale else 0
    if stale:
        SITEMAP.write_bytes((b"\xef\xbb\xbf" if bom else b"") + new_text.encode("utf-8"))
    print(f"{len(stale)} lastmod(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
