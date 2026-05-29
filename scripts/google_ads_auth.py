#!/usr/bin/env python3
"""One-time Google Ads OAuth setup. NO gcloud, NO MCP.

Mints a long-lived refresh token via a loopback OAuth flow using the
drozq-ads-mcp Desktop OAuth client, then writes scripts/.google_ads.json
(gitignored). Run this ONCE. After that, scripts/ads.py works forever.

Before running, publish the consent screen to Production so the token does
NOT expire every 7 days (that 7-day expiry is the whole reason this kept
breaking):
    https://console.cloud.google.com/auth/audience?project=drozq-ads-mcp
    -> "PUBLISH APP" -> confirm.

Then:  python scripts/google_ads_auth.py
"""
import os, sys, json, base64, hashlib, secrets, webbrowser
import urllib.parse, urllib.request, urllib.error
import http.server, threading

HERE      = os.path.dirname(os.path.abspath(__file__))
CREDS_OUT = os.path.join(HERE, ".google_ads.json")
ADC       = os.path.join(os.environ.get("APPDATA", ""), "gcloud",
                         "application_default_credentials.json")

SCOPE    = "https://www.googleapis.com/auth/adwords"   # adwords only; no cloud-platform
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
PORT      = 8765
REDIRECT  = f"http://localhost:{PORT}/"

LOGIN_CID   = "1975174499"   # MCC manager
CUSTOMER_ID = "3351363652"   # drozq operating account


def load_client():
    """OAuth client_id/secret: env override, else the existing ADC file."""
    cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    sec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if cid and sec:
        return cid, sec
    if os.path.exists(ADC):
        d = json.load(open(ADC))
        if d.get("client_id") and d.get("client_secret"):
            return d["client_id"], d["client_secret"]
    sys.exit("No OAuth client found. Set GOOGLE_OAUTH_CLIENT_ID / "
             "GOOGLE_OAUTH_CLIENT_SECRET, or restore the gcloud ADC file.")


class Catch(http.server.BaseHTTPRequestHandler):
    code = None
    err  = None
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        Catch.code = (params.get("code") or [None])[0]
        Catch.err  = (params.get("error") or [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        msg = ("Auth complete. Close this tab and return to the terminal."
               if Catch.code else f"Auth failed: {Catch.err}")
        self.wfile.write(f"<html><body><h2>{msg}</h2></body></html>".encode())
    def log_message(self, *a):
        pass


def main():
    client_id, client_secret = load_client()
    dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")

    # PKCE (harmless extra safety on top of the client secret)
    verifier  = base64.urlsafe_b64encode(secrets.token_bytes(40)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()

    params = {
        "client_id": client_id, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent",
        "code_challenge": challenge, "code_challenge_method": "S256",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    srv = http.server.HTTPServer(("127.0.0.1", PORT), Catch)
    t = threading.Thread(target=srv.handle_request)
    t.start()

    print("\nOpening your browser for Google sign-in...")
    print("If it does not open, paste this URL manually:\n\n" + url + "\n")
    print("  1. Sign in as guerrerojoshua720@gmail.com")
    print("  2. If you see 'Google hasn't verified this app': Advanced -> Continue")
    print("  3. Allow.\n")
    webbrowser.open(url)

    t.join(timeout=300)
    srv.server_close()

    if Catch.err:
        extra = ""
        if Catch.err == "redirect_uri_mismatch":
            extra = ("\nThe OAuth client is not a 'Desktop app' type. Either change it to "
                     "Desktop, or add this redirect URI to it:\n  " + REDIRECT)
        sys.exit(f"Auth failed: {Catch.err}{extra}")
    if not Catch.code:
        sys.exit("No auth code received (timeout, or 'This app is blocked').\n"
                 "Publish the consent screen to Production and rerun:\n"
                 "  https://console.cloud.google.com/auth/audience?project=drozq-ads-mcp")

    data = urllib.parse.urlencode({
        "code": Catch.code, "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code",
        "code_verifier": verifier,
    }).encode()
    try:
        resp = json.loads(urllib.request.urlopen(
            urllib.request.Request(TOKEN_URL, data=data)).read())
    except urllib.error.HTTPError as e:
        sys.exit("Token exchange failed: " + e.read().decode()[:1000])

    rt = resp.get("refresh_token")
    if not rt:
        sys.exit("No refresh_token returned. Response: " + json.dumps(resp)[:500])

    out = {
        "client_id": client_id, "client_secret": client_secret, "refresh_token": rt,
        "developer_token": dev_token, "login_customer_id": LOGIN_CID,
        "customer_id": CUSTOMER_ID,
    }
    json.dump(out, open(CREDS_OUT, "w"), indent=2)
    print("\nSaved credentials to", CREDS_OUT)
    print("Done. Now run:  python scripts/ads.py")
    if not dev_token:
        print("WARNING: GOOGLE_ADS_DEVELOPER_TOKEN was empty in env; "
              "add a 'developer_token' value to", CREDS_OUT)


if __name__ == "__main__":
    main()
