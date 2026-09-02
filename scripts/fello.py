"""fello.py : the daily-driver CLI for the Fello API (api.fello.ai/public/v1).

Credentials live in the gitignored scripts/.fello_secret (JSON with api_key,
client_secret). Generate / rotate them in Fello > Settings > Connected Apps >
the "drozq.com" Custom App. The API key is full account access; the client
secret is ONLY used to verify the HMAC on inbound webhooks.

Reference: notes/fello/fello-api-brief.md (what the API can and cannot do),
/fello/ on the site (the same brief, rendered).

Usage (run from the repo root):

    python scripts/fello.py probe                       # key check + live rate-limit budget
    python scripts/fello.py webhooks                    # list subscriptions
    python scripts/fello.py webhooks add FormSubmission https://drozq.com/api/fello/webhook
    python scripts/fello.py webhooks add-all https://drozq.com/api/fello/webhook   # every supported event
    python scripts/fello.py webhooks rm <subscriptionId>
    python scripts/fello.py contact get <email | contactId>
    python scripts/fello.py contact add <email> [--name "Full Name"] [--phone 9495551234]
                                        [--address "1 Main St, Irvine, CA 92614"] [--tag X --tag Y]
                                        [--assign josh@drozq.com] [--crm-url URL] [--crm-source S] [--crm-stage S]
    python scripts/fello.py contact update <contactId> [--name ..] [--phone ..] [--email ..]
                                        [--assign ..] [--status Active|Monitored]
    python scripts/fello.py contact delete <contactId> --yes
    python scripts/fello.py tags add|replace|rm <contactId> TAG [TAG ...]
    python scripts/fello.py property add <contactId> "<address>"
    python scripts/fello.py property archive <propertyId>
    python scripts/fello.py verify <signature-header> < body.json   # HMAC check for a captured webhook
    python scripts/fello.py calllist [--days 90] [--limit 100] [--fresh] [--csv]
                                        # the ranked Fello engagement call list (hot first) via
                                        # https://drozq.com/api/fello/engagement; needs the EMAIL_SECRET
                                        # in scripts/.email_secret (or DROZQ_EMAIL_SECRET)

Every command prints the JSON response plus the rate-limit headers Fello
returns (X-RateLimit-Remaining-10 / -Day). Exit code 1 on any non-2xx.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRET_FILE = ROOT / "scripts" / ".fello_secret"

WEBHOOK_EVENTS = [
    "FormSubmission",
    "ContactEnriched",
    "DashboardClick",
    "EmailClick",
    "PostcardScan",
    "ContactUnsubscribed",
    "ContactDetailsUpdated",
    "TagsAdded",
    "TagsRemoved",
    "FelixAIHandoff",
]

RATE_HEADERS = (
    "X-RateLimit-Limit-10",
    "X-RateLimit-Remaining-10",
    "X-RateLimit-Limit-Day",
    "X-RateLimit-Remaining-Day",
    "RateLimit-Reset",
)


def load_secret() -> dict:
    if not SECRET_FILE.exists():
        sys.exit(
            f"fello.py: missing {SECRET_FILE}. Create it as JSON with api_key + client_secret "
            "(Fello > Settings > Connected Apps > your Custom App)."
        )
    data = json.loads(SECRET_FILE.read_text(encoding="utf-8"))
    if not data.get("api_key"):
        sys.exit("fello.py: .fello_secret has no api_key")
    data.setdefault("base_url", "https://api.fello.ai/public/v1")
    return data


class Fello:
    def __init__(self, secret: dict):
        self.key = secret["api_key"]
        self.base = secret["base_url"].rstrip("/")
        self.client_secret = secret.get("client_secret", "")

    def call(self, method: str, path: str, body: dict | None = None, query: dict | None = None):
        url = self.base + path
        if query:
            url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        data = None
        headers = {"x-api-key": self.key, "Accept": "application/json", "User-Agent": "drozq-fello-cli/1.0"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                hdrs = dict(resp.headers)
                raw = resp.read()
        except urllib.error.HTTPError as e:
            status = e.code
            hdrs = dict(e.headers)
            raw = e.read()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = {"raw": raw.decode("utf-8", "replace")}
        return status, payload, hdrs

    # --- webhooks -----------------------------------------------------------
    def webhooks(self):
        return self.call("GET", "/webhooks")

    def webhook_add(self, event: str, url: str):
        return self.call("POST", "/webhooks", {"url": url, "eventType": event})

    def webhook_rm(self, sub_id: str):
        return self.call("DELETE", f"/webhooks/{urllib.parse.quote(sub_id)}")

    # --- contacts -----------------------------------------------------------
    def contact_get(self, ident: str):
        q = {"emailId": ident} if "@" in ident else {"contactId": ident}
        return self.call("GET", "/contact", query=q)

    def contact_add(self, body: dict):
        return self.call("POST", "/contact", body)

    def contact_update(self, contact_id: str, body: dict):
        return self.call("PATCH", f"/contact/{urllib.parse.quote(contact_id)}", body)

    def contact_delete(self, contact_id: str):
        return self.call("DELETE", f"/contact/{urllib.parse.quote(contact_id)}")

    def tags(self, op: str, contact_id: str, tags: list[str]):
        method = {"add": "POST", "replace": "PUT", "rm": "DELETE"}[op]
        return self.call(method, f"/contact/{urllib.parse.quote(contact_id)}/tags", {"tags": tags})

    # --- properties ---------------------------------------------------------
    def property_add(self, contact_id: str, address: str):
        return self.call("POST", f"/contact/{urllib.parse.quote(contact_id)}/property", {"address": address})

    def property_archive(self, property_id: str):
        return self.call("POST", f"/contact/property/{urllib.parse.quote(property_id)}/archive")

    # --- webhook signature --------------------------------------------------
    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Fello signs the raw request body with HMAC-SHA256 keyed by the
        base64-DECODED client secret and sends the base64 digest in the
        fello-webhook-signature header (docs.fello.ai/webhooks)."""
        key = base64.b64decode(self.client_secret)
        digest = base64.b64encode(hmac.new(key, body, hashlib.sha256).digest()).decode("ascii")
        return hmac.compare_digest(digest, signature.strip())


def load_admin_secret() -> str:
    import os
    s = os.environ.get("DROZQ_EMAIL_SECRET", "").strip()
    if s:
        return s
    f = ROOT / "scripts" / ".email_secret"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    sys.exit("fello.py calllist: needs the EMAIL_SECRET in scripts/.email_secret or DROZQ_EMAIL_SECRET")


def calllist(args) -> int:
    """The ranked engagement list from /api/fello/engagement, printed as a table."""
    url = f"{args.base.rstrip('/')}/api/fello/engagement?days={args.days}&limit={args.limit}" + ("&fresh=1" if args.fresh else "")
    # The zone blocks python-urllib's default browser signature (Cloudflare 1010); name the client like emailer.py does.
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + load_admin_secret(), "Accept": "application/json", "User-Agent": "drozq-fello-cli/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode("utf-8", "replace")[:500])
        return 1
    if not data.get("ok"):
        print(json.dumps(data, indent=2))
        return 1
    s = data["summary"]
    print(f"Fello engagement ({'cached' if data.get('cached') else 'fresh'}, generated {data.get('generatedAt')}): "
          f"{s['leadsChecked']} leads checked, {s['matched']} in Fello, {s['hot']} hot, {s['warm']} warm, avg score {s['avgLeadScore']}")
    rows = data.get("leads", [])
    if args.csv:
        import csv
        out = Path.home() / "Downloads" / f"fello-calllist-{data.get('generatedAt','')[:10]}.csv"
        cols = ["hot", "warm", "leadScore", "name", "email", "phone", "lastClickAt", "lastActivityAt", "dashboardClicks", "emailClicks", "dashboardViews", "signals", "properties", "intent", "city", "createdAt", "crmFields"]
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for l in rows:
                w.writerow([l.get("hot"), l.get("warm"), l.get("leadScore"), l.get("name"), l.get("email"), l.get("phone"),
                            l.get("lastClickAt"), l.get("lastActivityAt"), l.get("dashboardClicks"), l.get("emailClicks"), l.get("dashboardViews"),
                            "; ".join(l.get("signals") or []), "; ".join(l.get("properties") or []), l.get("intent"), l.get("city"), l.get("createdAt"),
                            json.dumps((l.get("crm") or {}).get("fields") or {})])
        print("CSV:", out)
    print(f"{'':2} {'score':>5} {'name':24} {'email':30} {'phone':15} {'last click':20} {'signals / values'}")
    for l in rows:
        flag = "HOT" if l.get("hot") else ("warm" if l.get("warm") else ("" if l.get("matched") else "n/a"))
        vals = dict((l.get("crm") or {}).get("fields") or {})
        extra = "; ".join((l.get("signals") or []) + [f"{k}={v}" for k, v in vals.items()])
        print(f"{flag:4} {str(l.get('leadScore') if l.get('leadScore') is not None else '-'):>5} {str(l.get('name') or '')[:24]:24} {str(l.get('email'))[:30]:30} "
              f"{str(l.get('phone') or '')[:15]:15} {str(l.get('lastClickAt') or '')[:20]:20} {extra[:80]}")
    return 0


def report(status: int, payload, hdrs: dict) -> int:
    print(f"HTTP {status}")
    if payload is not None:
        print(json.dumps(payload, indent=2))
    rl = {h: hdrs.get(h) for h in RATE_HEADERS if hdrs.get(h) is not None}
    if rl:
        print("rate-limit: " + ", ".join(f"{k}={v}" for k, v in rl.items()))
    return 0 if 200 <= status < 300 else 1


def build_crm_fields(args) -> dict | None:
    crm = {}
    if getattr(args, "crm_url", None):
        crm["url"] = args.crm_url
    if getattr(args, "crm_source", None):
        crm["source"] = args.crm_source
    if getattr(args, "crm_stage", None):
        crm["stage"] = args.crm_stage
    if getattr(args, "crm_name", None):
        crm["name"] = args.crm_name
    return crm or None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fello.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("probe", help="key check + live rate-limit budget")

    wh = sub.add_parser("webhooks", help="list / add / add-all / rm")
    wh_sub = wh.add_subparsers(dest="wcmd")
    w_add = wh_sub.add_parser("add")
    w_add.add_argument("event", choices=WEBHOOK_EVENTS)
    w_add.add_argument("url")
    w_all = wh_sub.add_parser("add-all")
    w_all.add_argument("url")
    w_rm = wh_sub.add_parser("rm")
    w_rm.add_argument("subscription_id")

    c = sub.add_parser("contact", help="get / add / update / delete")
    c_sub = c.add_subparsers(dest="ccmd", required=True)
    c_get = c_sub.add_parser("get")
    c_get.add_argument("ident", help="email or contactId")
    c_add = c_sub.add_parser("add")
    c_add.add_argument("email")
    c_add.add_argument("--name")
    c_add.add_argument("--phone")
    c_add.add_argument("--address")
    c_add.add_argument("--tag", action="append", default=[])
    c_add.add_argument("--assign", help="assignedUserEmailId")
    c_add.add_argument("--crm-url")
    c_add.add_argument("--crm-source")
    c_add.add_argument("--crm-stage")
    c_add.add_argument("--crm-name")
    c_upd = c_sub.add_parser("update")
    c_upd.add_argument("contact_id")
    c_upd.add_argument("--name")
    c_upd.add_argument("--phone")
    c_upd.add_argument("--email")
    c_upd.add_argument("--assign")
    c_upd.add_argument("--status", choices=["Active", "Monitored"])
    c_upd.add_argument("--crm-url")
    c_upd.add_argument("--crm-source")
    c_upd.add_argument("--crm-stage")
    c_upd.add_argument("--crm-name")
    c_del = c_sub.add_parser("delete")
    c_del.add_argument("contact_id")
    c_del.add_argument("--yes", action="store_true", help="required: deletion is permanent")

    t = sub.add_parser("tags", help="add / replace / rm tags on a contact")
    t.add_argument("op", choices=["add", "replace", "rm"])
    t.add_argument("contact_id")
    t.add_argument("tags", nargs="+")

    pr = sub.add_parser("property", help="add / archive")
    pr_sub = pr.add_subparsers(dest="pcmd", required=True)
    pr_add = pr_sub.add_parser("add")
    pr_add.add_argument("contact_id")
    pr_add.add_argument("address")
    pr_arc = pr_sub.add_parser("archive")
    pr_arc.add_argument("property_id")

    v = sub.add_parser("verify", help="verify a webhook signature against a body on stdin")
    v.add_argument("signature", help="value of the fello-webhook-signature header")

    cl = sub.add_parser("calllist", help="ranked Fello engagement call list (hot first)")
    cl.add_argument("--days", type=int, default=90)
    cl.add_argument("--limit", type=int, default=100)
    cl.add_argument("--fresh", action="store_true", help="bypass the 8-minute server cache")
    cl.add_argument("--csv", action="store_true", help="write the list to Downloads as CSV")
    cl.add_argument("--base", default="https://drozq.com")

    args = p.parse_args(argv)
    if args.cmd == "calllist":
        return calllist(args)
    api = Fello(load_secret())

    if args.cmd == "probe":
        status, payload, hdrs = api.webhooks()
        if status == 401:
            print("HTTP 401: the API key is not accepted. Rotate it in Fello > Settings > Connected Apps.")
            return 1
        n = len((payload or {}).get("webhooks", [])) if isinstance(payload, dict) else 0
        print(f"Key OK. {n} webhook subscription(s) registered.")
        return report(status, None, hdrs)

    if args.cmd == "webhooks":
        if args.wcmd == "add":
            return report(*api.webhook_add(args.event, args.url))
        if args.wcmd == "add-all":
            rc = 0
            for ev in WEBHOOK_EVENTS:
                print(f"--- {ev}")
                rc |= report(*api.webhook_add(ev, args.url))
            return rc
        if args.wcmd == "rm":
            return report(*api.webhook_rm(args.subscription_id))
        return report(*api.webhooks())

    if args.cmd == "contact":
        if args.ccmd == "get":
            return report(*api.contact_get(args.ident))
        if args.ccmd == "add":
            body: dict = {"email": args.email}
            if args.name:
                body["name"] = args.name
            if args.phone:
                body["phone"] = args.phone
            if args.address:
                body["address"] = args.address
            if args.tag:
                body["tags"] = args.tag
            if args.assign:
                body["assignedUserEmailId"] = args.assign
            crm = build_crm_fields(args)
            if crm:
                body["crmFields"] = crm
            return report(*api.contact_add(body))
        if args.ccmd == "update":
            body = {}
            if args.name:
                body["name"] = args.name
            if args.phone:
                body["phone"] = args.phone
            if args.email:
                body["email"] = args.email
            if args.assign:
                body["assignedUserEmailId"] = args.assign
            if args.status:
                body["recordStatus"] = args.status
            crm = build_crm_fields(args)
            if crm:
                body["crmFields"] = crm
            if not body:
                sys.exit("fello.py: nothing to update")
            return report(*api.contact_update(args.contact_id, body))
        if args.ccmd == "delete":
            if not args.yes:
                sys.exit("fello.py: contact delete is permanent; re-run with --yes")
            return report(*api.contact_delete(args.contact_id))

    if args.cmd == "tags":
        return report(*api.tags(args.op, args.contact_id, args.tags))

    if args.cmd == "property":
        if args.pcmd == "add":
            return report(*api.property_add(args.contact_id, args.address))
        return report(*api.property_archive(args.property_id))

    if args.cmd == "verify":
        body = sys.stdin.buffer.read()
        ok = api.verify_signature(body, args.signature)
        print("signature OK" if ok else "signature MISMATCH")
        return 0 if ok else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
