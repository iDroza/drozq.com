#!/usr/bin/env python3
"""Create a local Search Console read-only OAuth refresh token.

The token is written to scripts/.google_search_console.json, which is
gitignored. The script never prints credentials or tokens.
"""

import base64
import hashlib
import http.server
import json
import os
from pathlib import Path
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser


HERE = Path(__file__).resolve().parent
ADS_CREDS = HERE / ".google_ads.json"
OUTPUT = HERE / ".google_search_console.json"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
PORT = 8766
REDIRECT = f"http://localhost:{PORT}/"


def load_client():
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    if client_id and client_secret:
        return client_id, client_secret
    if ADS_CREDS.exists():
        credentials = json.loads(ADS_CREDS.read_text(encoding="utf-8"))
        client_id = str(credentials.get("client_id", "")).strip()
        client_secret = str(credentials.get("client_secret", "")).strip()
        if client_id and client_secret:
            return client_id, client_secret
    raise SystemExit(
        "No OAuth client found. Set GOOGLE_OAUTH_CLIENT_ID and "
        "GOOGLE_OAUTH_CLIENT_SECRET, or restore scripts/.google_ads.json."
    )


class Callback(http.server.BaseHTTPRequestHandler):
    code = None
    error = None

    def do_GET(self):
        parameters = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        Callback.code = (parameters.get("code") or [None])[0]
        Callback.error = (parameters.get("error") or [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        message = (
            "Search Console authorization complete. You can close this tab."
            if Callback.code
            else "Search Console authorization did not complete."
        )
        self.wfile.write(f"<html><body><h2>{message}</h2></body></html>".encode())

    def log_message(self, *_args):
        return


def wait_for_callback(server, timeout_seconds=300):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline and not Callback.code and not Callback.error:
        server.timeout = min(1, max(0, deadline - time.monotonic()))
        server.handle_request()


def main():
    client_id, client_secret = load_client()
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(40)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    authorization_url = AUTH_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )

    server = http.server.HTTPServer(("127.0.0.1", PORT), Callback)
    callback_thread = threading.Thread(target=wait_for_callback, args=(server,))
    callback_thread.start()
    print("Opening Google authorization for read-only Search Console access.")
    print("Sign in as the Search Console property owner and approve read access.")
    webbrowser.open(authorization_url)

    callback_thread.join(timeout=300)
    server.server_close()
    if Callback.error:
        raise SystemExit(f"Authorization failed: {Callback.error}")
    if not Callback.code:
        raise SystemExit("Authorization timed out before Google returned a code.")

    body = urllib.parse.urlencode(
        {
            "code": Callback.code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT,
            "grant_type": "authorization_code",
            "code_verifier": verifier,
        }
    ).encode()
    try:
        response = json.loads(
            urllib.request.urlopen(
                urllib.request.Request(TOKEN_URL, data=body), timeout=30
            ).read()
        )
    except urllib.error.HTTPError as error:
        raise SystemExit(f"Token exchange failed with HTTP {error.code}.") from error

    refresh_token = response.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise SystemExit("Google did not return a refresh token. Revoke and retry consent.")
    OUTPUT.write_text(
        json.dumps(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved read-only Search Console credentials to {OUTPUT}.")


if __name__ == "__main__":
    main()
