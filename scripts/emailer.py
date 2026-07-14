#!/usr/bin/env python3
"""Drozq email platform CLI. Thin client for the /api/email/* endpoints, so the
MailChannels key and the database never leave Cloudflare.

Auth: the shared secret comes from the DROZQ_EMAIL_SECRET env var or the
gitignored file scripts/.email_secret (single line).

Commands:
  init                          create the D1 tables (safe to re-run)
  tick                          run one queue drain manually
  list [--status S] [--source S] [--csv]
                                subscriber list + stats; --csv saves to Downloads
  log [--limit N]               recent sends with open/click stamps
  send --to a@b.com --subject "..." --p "para" [--p "para" ...]
       [--headline "..."] [--preheader "..."] [--first Name]
       [--cta-label "..." --cta-url https://...] [--with-unsub]
                                1:1 branded email (buyer progress updates)
  broadcast --subject "..." --p "..." [--p ...] [--headline ...]
       [--segment all|leads|newsletter] [--stagger N] [--dry-run]
                                queue a campaign to the list
  backfill [--live] [--no-enroll] [--stagger N]
                                import FollowUpBoss leads (dry run by default)
  pause EMAIL / resume EMAIL    stop/restart one person's sequence
  preview [--step N] [--mode sell|buy|neutral] [--kind update] [--seq ID]
                                open the rendered email in the browser

Paragraphs support **bold** and [label](https://url). {first} and {city}
personalize per recipient.
"""

import argparse
import json
import os
import sys
import urllib.request
import webbrowser
from pathlib import Path

BASE_DEFAULT = "https://drozq.com"
SECRET_FILE = Path(__file__).parent / ".email_secret"
DOWNLOADS = Path.home() / "Downloads"


def get_secret():
    s = os.environ.get("DROZQ_EMAIL_SECRET", "").strip()
    if not s and SECRET_FILE.exists():
        s = SECRET_FILE.read_text(encoding="utf-8").strip()
    if not s:
        sys.exit(
            "No secret found. Put the EMAIL_SECRET value in scripts/.email_secret "
            "(gitignored) or set DROZQ_EMAIL_SECRET."
        )
    return s


def call(base, path, method="POST", payload=None, auth=True, raw=False):
    url = base.rstrip("/") + path
    # Cloudflare Browser Integrity Check 403s (error 1010) the default
    # python-urllib user agent; a named tool UA passes.
    headers = {"Content-Type": "application/json", "User-Agent": "drozq-emailer/1.0"}
    if auth:
        headers["Authorization"] = "Bearer " + get_secret()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"HTTP {e.code}: {body[:2000]}")
        sys.exit(1)
    if raw:
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body}


def pretty(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="Drozq email platform CLI")
    ap.add_argument("--base", default=BASE_DEFAULT, help="API base (default: production)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("tick")

    p = sub.add_parser("list")
    p.add_argument("--status")
    p.add_argument("--source")
    p.add_argument("--csv", action="store_true")

    p = sub.add_parser("log")
    p.add_argument("--limit", type=int, default=30)

    for name in ("send", "update"):
        p = sub.add_parser(name)
        p.add_argument("--to", required=True)
        p.add_argument("--subject", required=True)
        p.add_argument("--p", action="append", required=True, dest="paragraphs")
        p.add_argument("--headline", default="")
        p.add_argument("--preheader", default="")
        p.add_argument("--first", default="")
        p.add_argument("--cta-label", default="")
        p.add_argument("--cta-url", default="")
        p.add_argument("--with-unsub", action="store_true")

    p = sub.add_parser("broadcast")
    p.add_argument("--subject", required=True)
    p.add_argument("--p", action="append", required=True, dest="paragraphs")
    p.add_argument("--headline", default="")
    p.add_argument("--preheader", default="")
    p.add_argument("--cta-label", default="")
    p.add_argument("--cta-url", default="")
    p.add_argument("--segment", default="all", choices=["all", "leads", "newsletter"])
    p.add_argument("--stagger", type=int, default=90)
    p.add_argument("--slug", default="")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("backfill")
    p.add_argument("--live", action="store_true", help="actually enroll (default is dry run)")
    p.add_argument("--no-enroll", action="store_true", help="import to list only, no sequence")
    p.add_argument("--stagger", type=int, default=240)

    for name in ("pause", "resume"):
        p = sub.add_parser(name)
        p.add_argument("email")

    p = sub.add_parser("preview")
    p.add_argument("--seq", default="lead-response-v1")
    p.add_argument("--step", type=int, default=0)
    p.add_argument("--mode", default="sell")
    p.add_argument("--kind", default="")
    p.add_argument("--first", default="Sam")
    p.add_argument("--city", default="Irvine")

    a = ap.parse_args()

    if a.cmd == "init":
        pretty(call(a.base, "/api/email/init"))
    elif a.cmd == "tick":
        pretty(call(a.base, "/api/email/tick"))
    elif a.cmd == "list":
        qs = []
        if a.status:
            qs.append("status=" + a.status)
        if a.source:
            qs.append("source=" + a.source)
        if a.csv:
            qs.append("format=csv")
            body = call(a.base, "/api/email/list?" + "&".join(qs), method="GET", raw=True)
            out = DOWNLOADS / "drozq-subscribers.csv"
            out.write_text(body, encoding="utf-8")
            print(f"Saved {out} ({body.count(chr(10))} rows)")
        else:
            data = call(a.base, "/api/email/list" + ("?" + "&".join(qs) if qs else ""), method="GET")
            if len(json.dumps(data)) > 20000:
                data["subscribers"] = data.get("subscribers", [])[:25]
                data["note"] = "truncated to 25 rows; use --csv for the full list"
            pretty(data)
    elif a.cmd == "log":
        pretty(call(a.base, f"/api/email/list?view=log&limit={a.limit}", method="GET"))
    elif a.cmd in ("send", "update"):
        payload = {
            "to": a.to,
            "subject": a.subject,
            "paragraphs": a.paragraphs,
            "headline": a.headline,
            "preheader": a.preheader,
            "first_name": a.first,
            "cta_label": getattr(a, "cta_label"),
            "cta_url": getattr(a, "cta_url"),
            "include_unsub": a.with_unsub,
        }
        pretty(call(a.base, "/api/email/send", payload=payload))
    elif a.cmd == "broadcast":
        payload = {
            "subject": a.subject,
            "paragraphs": a.paragraphs,
            "headline": a.headline,
            "preheader": a.preheader,
            "cta_label": getattr(a, "cta_label"),
            "cta_url": getattr(a, "cta_url"),
            "segment": a.segment,
            "stagger_seconds": a.stagger,
            "dry_run": a.dry_run,
        }
        if a.slug:
            payload["slug"] = a.slug
        pretty(call(a.base, "/api/email/broadcast", payload=payload))
    elif a.cmd == "backfill":
        payload = {"dry_run": not a.live, "enroll": not a.no_enroll, "stagger_seconds": a.stagger}
        pretty(call(a.base, "/api/email/backfill", payload=payload))
    elif a.cmd in ("pause", "resume"):
        pretty(call(a.base, "/api/email/pause", payload={"email": a.email, "action": a.cmd}))
    elif a.cmd == "preview":
        if a.kind:
            url = f"{a.base}/api/email/preview?kind={a.kind}&first={a.first}&city={a.city}"
        else:
            url = f"{a.base}/api/email/preview?seq={a.seq}&step={a.step}&mode={a.mode}&first={a.first}&city={a.city}"
        print(url)
        webbrowser.open(url)


if __name__ == "__main__":
    main()
