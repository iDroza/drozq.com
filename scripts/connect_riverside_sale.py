"""Connect the Euclid Court closing to every rendered proof path.

The site keeps several intentionally inlined HTML surfaces. This updater is
count-guarded and idempotent so those rendered pages can be refreshed without
blind edits to their large HTML lines.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _case_file_shared import CF_STYLE_BLOCK
from migrate_testimonial_001 import CROSSLINK as CASE_001_CROSSLINK
from migrate_testimonial_001 import TAKEAWAY as CASE_001_TAKEAWAY
from migrate_testimonial_002 import CROSSLINK as CASE_002_CROSSLINK
from migrate_testimonial_002 import TAKEAWAY as CASE_002_TAKEAWAY
from migrate_testimonials import CARDS, CTA, STATS


def replace_once(text: str, old: str, new: str, label: str) -> str:
    old_count = text.count(old)
    new_count = text.count(new)
    if new != old and new_count >= 1:
        return text
    if old_count == 1:
        return text.replace(old, new, 1)
    if old_count == 0 and new_count >= 1:
        return text
    raise RuntimeError(
        f"{label}: expected one old value or an existing new value, "
        f"found old={old_count}, new={new_count}"
    )


def replace_element(text: str, start_marker: str, end_tag: str, replacement: str, label: str) -> str:
    if replacement.strip() in text:
        return text
    if text.count(start_marker) != 1:
        raise RuntimeError(f"{label}: expected one start marker, found {text.count(start_marker)}")
    start = text.index(start_marker)
    end = text.find(end_tag, start)
    if end < 0:
        raise RuntimeError(f"{label}: closing tag {end_tag} not found")
    end += len(end_tag)
    return text[:start] + replacement.strip() + text[end:]


def replace_first_main_style(text: str, label: str) -> str:
    main = text.find("<main")
    if main < 0:
        raise RuntimeError(f"{label}: main tag not found")
    start = text.find("<style>", main)
    end = text.find("</style>", start)
    if start < 0 or end < 0:
        raise RuntimeError(f"{label}: first main style block not found")
    end += len("</style>")
    if text[start:end] == CF_STYLE_BLOCK:
        return text
    return text[:start] + CF_STYLE_BLOCK + text[end:]


def write(path_name: str, text: str) -> None:
    path = ROOT / path_name
    old = path.read_text(encoding="utf-8")
    if text == old:
        print(f"OK: {path_name}")
        return
    path.write_text(text, encoding="utf-8")
    print(f"UPDATED: {path_name}")


def update_testimonials_index() -> None:
    path_name = "testimonials/index.html"
    path = ROOT / path_name
    text = path.read_text(encoding="utf-8")
    text = replace_first_main_style(text, path_name)
    text = replace_element(text, '<section class="cf-stats-strip">', "</section>", STATS, "testimonial stats")
    text = replace_element(text, '<section class="cf-index-section">', "</section>", CARDS, "testimonial cards")
    text = replace_element(text, '<section class="cf-cta-strip">', "</section>", CTA, "testimonial CTA")
    write(path_name, text)


def update_case(path_name: str, takeaway: str, crosslink: str, takeaway_marker: str) -> None:
    path = ROOT / path_name
    text = path.read_text(encoding="utf-8")
    text = replace_first_main_style(text, path_name)
    text = replace_element(text, takeaway_marker, "</section>", takeaway, path_name + " takeaway")
    text = replace_element(text, '<aside class="cf-crosslink">', "</aside>", crosslink, path_name + " crosslink")
    write(path_name, text)


def update_sold() -> None:
    path_name = "sold/index.html"
    path = ROOT / path_name
    text = path.read_text(encoding="utf-8")

    old_stats = '<div class="sold-stats"><div class="sold-stat-tile"><b>$43,250</b><span>Negotiated for clients</span></div><div class="sold-stat-tile"><b>2 for 2</b><span>Closed early</span></div><div class="sold-stat-tile"><b>23</b><span>Homes walked to find the right 2</span></div></div>'
    new_stats = '<div class="sold-stats"><div class="sold-stat-tile"><b>$58,250</b><span>Negotiated for clients</span></div><div class="sold-stat-tile"><b>3 for 3</b><span>Closed early</span></div><div class="sold-stat-tile"><b>$1.79M</b><span>Closed purchase volume</span></div></div>'
    text = replace_once(text, old_stats, new_stats, "sold stats")

    media_old = """@media (min-width: 768px) {
  .sold-strip { height: 250px; }
  .sold-stats { grid-template-columns: 1fr 1fr 1fr; }
  .sold-grid { grid-template-columns: 1fr 1fr; }
  .sold-addr h3 { font-size: 24px; }
}"""
    media_new = media_old + """
@media (min-width: 992px) {
  .sold-grid { grid-template-columns: repeat(3, 1fr); gap: 20px; }
}"""
    text = replace_once(text, media_old, media_new, "sold desktop grid")

    card_anchor = '<a class="sold-link" href="/testimonials/002-corona-analyst/">Read the full case file &rarr;</a></div></article>'
    euclid_card = """<article class="sold-card"><div class="sold-img" role="img" aria-label="Backyard pool at 4194 Euclid Court" style="background-image:url(/media/images/euclid/pool-dusk.webp);background-position:center 58%"><span class="sold-tag">SOLD</span><div class="sold-addr"><h3>4194 Euclid Ct</h3><p>Riverside, CA 92504</p></div></div><div class="sold-body"><p class="sold-role">Represented the buyer &middot; First-time buyer &middot; Closed early</p><div class="sold-nums"><div class="sold-num"><b>$665,000</b><span>Closed price</span></div><div class="sold-num"><b>$15,000</b><span>Closing-cost credit</span></div><div class="sold-num"><b>Private pool</b><span>Family gathering place</span></div></div><a class="sold-link" href="/testimonials/003-riverside-first-home/">Read Richard's story &rarr;</a></div></article>"""
    if euclid_card not in text:
        text = replace_once(text, card_anchor, card_anchor + euclid_card, "Euclid sold card")

    text = replace_once(text, "The exact sequence both deals ran: price, prep, launch, negotiate, close.", "The exact sequence all three deals ran: price, prep, negotiate, inspect, close.", "sold process crosslink")
    text = replace_once(text, "Tell me what you are thinking about and I'll come back within the hour with a real answer, not a sales pitch.", "Tell me what you are thinking about and I'll come back within the hour with the property records pulled and a clear next step.", "sold closing CTA")
    write(path_name, text)


BUYERS_PROOF = """<section class="bg_#fff py_48px md:py_64px"><div class="hub-wrap"><div class="hub-head"><h2>Proof.</h2><p>Three buyers, three strategies, three closed deals.</p></div><div class="hub-grid hub-grid--2"><a class="hub-card" href="/testimonials/001-long-beach-firefighter/"><p class="hub-eyebrow">Case file 001</p><h3>The Long Beach firefighter</h3><p>A first-time buyer with a long-term plan, closed while his peers kept renting.</p><span class="hub-go">Read the file &rarr;</span></a><a class="hub-card" href="/testimonials/002-corona-analyst/"><p class="hub-eyebrow">Case file 002</p><h3>The Corona analyst</h3><p>He analyzes numbers for the State of California. Then he ran mine on his own purchase.</p><span class="hub-go">Read the file &rarr;</span></a><a class="hub-card" href="/testimonials/003-riverside-first-home/"><p class="hub-eyebrow">Case file 003</p><h3>Richard's Riverside first home</h3><p>$15,000 toward closing costs, a pool for the whole family, and an early close.</p><span class="hub-go">Read Richard's story &rarr;</span></a><a class="hub-card" href="/sold/"><p class="hub-eyebrow">The board</p><h3>Sold</h3><p>All three closings live on the board with the numbers left in, and it keeps growing.</p><span class="hub-go">See the board &rarr;</span></a></div></div></section>"""


def update_buyers() -> None:
    path_name = "buyers/index.html"
    path = ROOT / path_name
    text = path.read_text(encoding="utf-8")
    marker = '<section class="bg_#fff py_48px md:py_64px"><div class="hub-wrap"><div class="hub-head"><h2>Proof.</h2>'
    text = replace_element(text, marker, "</section>", BUYERS_PROOF, "buyers proof section")
    old_first_home = "Low-down-payment paths exist, CalHFA and conventional three percent down among them, and the right answer hangs on your monthly payment, not the sticker. Case File 001 is a Southern California firefighter who bought his first home with a plan built around exactly that."
    new_first_home = 'Low-down-payment paths exist, CalHFA and conventional three percent down among them, and the right answer hangs on your monthly payment, not the sticker. Read how the <a href="/testimonials/001-long-beach-firefighter/" class="c_#d92228 fw_700">Long Beach firefighter</a> and <a href="/testimonials/003-riverside-first-home/" class="c_#d92228 fw_700">Richard in Riverside</a> each turned a first purchase into a long-term plan.'
    text = replace_once(text, old_first_home, new_first_home, "buyers first-home links")
    write(path_name, text)


def refresh_proof_copy() -> None:
    replacements = {
        "2 for 2 closed early, $43,250 negotiated for clients.": "3 for 3 closed early, $58,250 negotiated for clients.",
        "Two closings with the numbers left in: $43,250 negotiated for clients.": "Three closings with the numbers left in: $58,250 negotiated for clients.",
        "Two deals on the board with $43,250 negotiated for clients.": "Three deals on the board with $58,250 negotiated for clients.",
        "$775,000 in Long Beach, $350,000 in Corona, $43,250 negotiated across the two.": "$775,000 in Long Beach, $350,000 in Corona, $665,000 in Riverside, and $58,250 negotiated across all three.",
        "Already proven in two of these cities.": "Already proven in three of these cities.",
        "Sold in Long Beach and Corona": "Sold in Long Beach, Corona, and Riverside",
        "Both closings carry their full numbers on the board: $43,250 negotiated across the two.": "All three closings carry their full numbers on the board: $58,250 negotiated for clients.",
    }
    targets = [
        "about/index.html",
        "california/index.html",
        "meet-the-team/index.html",
        "prices/index.html",
        "process/index.html",
        "testimonials/index.html",
        "thank-you/index.html",
        "value/index.html",
        "where-we-help/index.html",
    ]
    for path_name in targets:
        path = ROOT / path_name
        text = path.read_text(encoding="utf-8")
        old = text
        for before, after in replacements.items():
            if before in text:
                text = text.replace(before, after)
        if "$43,250" in text:
            raise RuntimeError(f"{path_name}: stale $43,250 proof copy remains")
        if text != old:
            path.write_text(text, encoding="utf-8")
            print(f"UPDATED: {path_name} proof copy")
        else:
            print(f"OK: {path_name} proof copy")


def update_project_docs() -> None:
    path_name = "CLAUDE.md"
    path = ROOT / path_name
    text = path.read_text(encoding="utf-8")
    old = "`/testimonials/` (+ /001-long-beach-firefighter/ + /002-corona-analyst/)"
    new = "`/testimonials/` (+ /001-long-beach-firefighter/ + /002-corona-analyst/ + /003-riverside-first-home/)"
    text = replace_once(text, old, new, "CLAUDE page inventory")
    write(path_name, text)


def main() -> None:
    update_testimonials_index()
    update_case(
        "testimonials/001-long-beach-firefighter/index.html",
        CASE_001_TAKEAWAY,
        CASE_001_CROSSLINK,
        '<section class="cf-section">\n  <div class="cf-narrow cf-reveal cf-takeaway">',
    )
    update_case(
        "testimonials/002-corona-analyst/index.html",
        CASE_002_TAKEAWAY,
        CASE_002_CROSSLINK,
        '<section class="cf-section cf-section--alt">\n  <div class="cf-narrow cf-reveal cf-takeaway">',
    )
    update_sold()
    update_buyers()
    refresh_proof_copy()
    update_project_docs()


if __name__ == "__main__":
    main()
