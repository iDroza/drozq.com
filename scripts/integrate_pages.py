"""
integrate_pages.py
Read subagent HTML outputs from disk transcripts, extract the main body,
scaffold each page, and register in funnels.json.

Avoids ever loading the huge HTML into the main conversation context.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page

TASKS_DIR = Path(
    r"C:\Users\guerr\AppData\Local\Temp\claude\C--Users-guerr-Documents-drozq-com"
    r"\6f20cfd3-7259-47f4-9a4e-6bbc48783875\tasks"
)


def extract_html_from_transcript(transcript_path: Path) -> str:
    """Walk the JSONL transcript, gather all assistant text, find the largest
    ~~~HTML ... ~~~ block, decode escaped chars, return inner of <main>."""
    chunks = []
    with transcript_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # Look for common shapes: {message:{role:"assistant",content:[{type:"text",text:"..."}]}}
            stack = [obj]
            while stack:
                cur = stack.pop()
                if isinstance(cur, dict):
                    for v in cur.values():
                        stack.append(v)
                elif isinstance(cur, list):
                    stack.extend(cur)
                elif isinstance(cur, str):
                    if "~~~HTML" in cur or "~~~html" in cur:
                        chunks.append(cur)

    if not chunks:
        raise RuntimeError(f"No assistant text containing ~~~HTML in {transcript_path}")

    # Concatenate and find the largest fenced block.
    combined = "\n".join(chunks)
    matches = list(re.finditer(r"~~~HTML\s*\n(.*?)~~~", combined, re.DOTALL | re.IGNORECASE))
    if not matches:
        raise RuntimeError(f"No fenced ~~~HTML block found in {transcript_path}")
    best = max(matches, key=lambda m: len(m.group(1)))
    html_block = best.group(1)

    # Extract inner of <main> if wrapped
    m_open = re.search(r"<main\b[^>]*>", html_block, re.IGNORECASE)
    if m_open:
        m_close = html_block.rfind("</main>")
        if m_close > m_open.end():
            return html_block[m_open.end():m_close]
    return html_block


PAGES = [
    {
        "agent_id": "a28d5bfac100e34ec",
        "target": "los-angeles/index.html",
        "title": "Sell Your Los Angeles Home | Joshua Guerrero, Real Brokerage",
        "description": "Selling a home in Los Angeles County? Joshua Guerrero, licensed CA REALTOR® at Real Brokerage. Free CMA, sharp pricing, modern marketing. No 5-star fluff.",
        "canonical": "/los-angeles/",
    },
    {
        "agent_id": "a8dee13e00de4b7da",
        "target": "california/index.html",
        "title": "California Listing Agent | Joshua Guerrero, Real Brokerage",
        "description": "Selling a home in California. Direct service in Orange County and the South Bay. Vetted statewide referral network. CA DRE #02267255.",
        "canonical": "/california/",
    },
    {
        "agent_id": "a98507625fd70afdc",
        "target": "process/index.html",
        "title": "The Process | How I Sell Your Home | Joshua Guerrero",
        "description": "How I sell your home: five steps, six to ten weeks. First call to close, with timing, deliverables, and no surprises.",
        "canonical": "/process/",
    },
    {
        "agent_id": "ab743fc60a2758667",
        "target": "where-we-help/index.html",
        "title": "Where I Help | Service Areas | Joshua Guerrero, Real Brokerage",
        "description": "I list and sell homes across most major Southern California markets: Orange, LA, San Diego, Riverside, San Bernardino, and Ventura counties.",
        "canonical": "/where-we-help/",
    },
    {
        "agent_id": "ade5207ddd476b6a2",
        "target": "market-insights/index.html",
        "title": "Southern California Market Insights | Joshua Guerrero",
        "description": "Where the Southern California market actually is right now. LA, Orange, Riverside, and San Bernardino county dashboards, updated regularly.",
        "canonical": "/market-insights/",
    },
    {
        "agent_id": "ad5d6559c9d82ae85",
        "target": "about/index.html",
        "title": "About Joshua Guerrero | Irvine Real Estate Agent",
        "description": "From Vallejo to Irvine. Twenty units a month in car sales taught me how to negotiate. Licensed since January 2026. CA DRE #02267255.",
        "canonical": "/about/",
    },
    {
        "agent_id": "a5fdd420b38543ae4",
        "target": "meet-the-team/index.html",
        "title": "Meet the Operation | Joshua Guerrero, Real Brokerage",
        "description": "You hire one agent. You get an entire operation. Three layers: Joshua, six partners by role, three running systems.",
        "canonical": "/meet-the-team/",
    },
    {
        "agent_id": "aa2cfc0b4d917b437",
        "target": "faq/index.html",
        "title": "FAQ | Selling and Buying in Irvine | Joshua Guerrero",
        "description": "Twenty-eight real questions, real answers. Timing, pricing, working with Joshua, closing, and what happens after the sale.",
        "canonical": "/faq/",
    },
    {
        "agent_id": "a125aa286f81badd9",
        "target": "contact/index.html",
        "title": "Contact | Joshua Guerrero, Real Brokerage",
        "description": "What's your home actually worth? Free CMA in 24 hours. Direct line and Irvine office. (949) 438-5948.",
        "canonical": "/contact/",
    },
]


def main() -> int:
    for cfg in PAGES:
        transcript = TASKS_DIR / f"{cfg['agent_id']}.output"
        if not transcript.exists():
            print(f"SKIP {cfg['target']} (transcript missing: {transcript})")
            continue
        print(f"--- {cfg['target']} ---")
        try:
            body = extract_html_from_transcript(transcript)
        except Exception as e:
            print(f"  EXTRACT FAILED: {e}")
            continue
        print(f"  Extracted body: {len(body):,} chars")

        scaffold_page(
            target=cfg["target"],
            title=cfg["title"],
            description=cfg["description"],
            canonical=cfg["canonical"],
            main_body_html=body,
        )

        # Register in funnels.json (idempotent)
        subprocess.run(
            ["python", "scripts/sync_funnels.py", "--add", cfg["target"]],
            cwd=ROOT,
            check=False,
        )

    # Final sync to confirm all funnel blocks match
    print()
    print("--- final sync ---")
    subprocess.run(["python", "scripts/sync_funnels.py"], cwd=ROOT, check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
