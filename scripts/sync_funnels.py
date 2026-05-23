"""
sync_funnels.py
Source-of-truth funnel propagation.

Reads /index.html (the canonical homepage), extracts the funnel HTML and JS
blocks between DROZQ_FUNNEL_*_BEGIN / END markers, and writes those blocks
into every page registered in funnels.json.

Usage:
    python scripts/sync_funnels.py            # sync all registered pages
    python scripts/sync_funnels.py --check    # report drift only, do not write
    python scripts/sync_funnels.py --add path # add a page to the registry

Each registered page MUST already contain the same four markers. The script
will not insert markers into a page that doesn't have them, to avoid silent
damage to surrounding markup.

Run after any change to the homepage funnel HTML or JS. The script updates
funnels.json with a `lastSync` timestamp and a per-page `syncedAt`.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "funnels.json"


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save_registry(reg: dict) -> None:
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")


def extract_block(text: str, begin_marker: str, end_marker: str) -> Tuple[int, int, str]:
    """Return (begin_idx, end_idx_exclusive, inner_text) for the block bounded
    by the begin/end markers in `text`. Markers themselves are NOT included
    in inner_text. Raises ValueError if markers are missing or out of order."""
    b = text.find(begin_marker)
    if b < 0:
        raise ValueError(f"begin marker not found: {begin_marker!r}")
    # The begin marker line may carry extra metadata before "-->", so advance
    # to the end of the marker line (the next "-->" after the marker start).
    b_close = text.find("-->", b)
    if b_close < 0:
        raise ValueError(f"begin marker not terminated: {begin_marker!r}")
    b_close += len("-->")
    e = text.find(end_marker, b_close)
    if e < 0:
        raise ValueError(f"end marker not found after begin: {end_marker!r}")
    return b_close, e, text[b_close:e]


def replace_block(text: str, begin_marker: str, end_marker: str, new_inner: str) -> str:
    b_close, e, _ = extract_block(text, begin_marker, end_marker)
    return text[:b_close] + new_inner + text[e:]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="Report drift only; do not write any files.")
    ap.add_argument("--add", metavar="PATH",
                    help="Add PATH (relative to repo root) to the registry "
                         "and exit. Does not sync.")
    args = ap.parse_args()

    reg = load_registry()

    if args.add:
        rel = args.add.replace("\\", "/").lstrip("/")
        if rel in reg["pages"] or any(p == rel for p in reg.get("pages", [])):
            print(f"Already registered: {rel}")
            return 0
        target = ROOT / rel
        if not target.exists():
            print(f"ERROR: {rel} does not exist", file=sys.stderr)
            return 2
        reg.setdefault("pages", []).append(rel)
        save_registry(reg)
        print(f"Added: {rel}")
        print("Run `python scripts/sync_funnels.py` to push the funnel into it. "
              "Note: the target file must already contain the four DROZQ_FUNNEL "
              "markers in the same order as index.html.")
        return 0

    source_path = ROOT / reg["source"]
    source_text = source_path.read_text(encoding="utf-8")

    blocks = {b["name"]: b for b in reg["blocks"]}
    source_blocks = {}
    for name, b in blocks.items():
        try:
            _, _, inner = extract_block(source_text, b["beginMarker"], b["endMarker"])
        except ValueError as e:
            print(f"ERROR extracting {name!r} from {reg['source']}: {e}", file=sys.stderr)
            return 2
        source_blocks[name] = inner

    pages = reg.get("pages", [])
    if not pages:
        print(f"No pages registered. Source: {reg['source']}.")
        print(f"Block hashes: " + ", ".join(f"{n}={sha(v)}" for n, v in source_blocks.items()))
        return 0

    any_drift = False
    per_page = {}
    for rel in pages:
        target_path = ROOT / rel
        if not target_path.exists():
            print(f"MISSING {rel}")
            any_drift = True
            continue
        text = target_path.read_text(encoding="utf-8")
        new_text = text
        drift = []
        for name, b in blocks.items():
            try:
                _, _, target_inner = extract_block(new_text, b["beginMarker"], b["endMarker"])
            except ValueError as e:
                print(f"ERROR in {rel} [{name}]: {e}", file=sys.stderr)
                drift.append(name + ":missing-markers")
                continue
            if target_inner != source_blocks[name]:
                drift.append(name)
                new_text = replace_block(new_text, b["beginMarker"], b["endMarker"], source_blocks[name])
        if drift:
            any_drift = True
            if args.check:
                print(f"DRIFT  {rel}: {', '.join(drift)}")
            else:
                target_path.write_text(new_text, encoding="utf-8")
                print(f"SYNCED {rel}: {', '.join(drift)}")
                per_page[rel] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
        else:
            print(f"OK     {rel}")
            per_page.setdefault(rel, None)

    if args.check:
        return 1 if any_drift else 0

    reg["lastSync"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    reg["pageSync"] = {**reg.get("pageSync", {}), **{k: v for k, v in per_page.items() if v}}
    reg["sourceHashes"] = {n: sha(v) for n, v in source_blocks.items()}
    save_registry(reg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
