# MCP workarounds: direct REST when MCPs fail

The PostHog MCP has flaked mid-session before (auth flakiness, 401s, empty schema responses). The Google Ads MCP was worse: cold-start timeouts, immediate `user-cancel` rejections, and a gcloud-ADC access token that expired every 7 days (Testing-mode OAuth consent screen) and eventually started hard-blocking consent ("This app is blocked").

**The Google Ads MCP was removed on 2026-05-28.** Google Ads is now REST-only via `scripts/ads.py`, which authenticates with a stored, long-lived OAuth **refresh token** (no gcloud, no ADC, no MCP). For PostHog, if the MCP fails, go straight to the direct HogQL REST call below.

Always prefer the direct calls over MCP retries when you see:
- PostHog MCP returns a tool-rejection / hang past ~30s / 401 / empty schema
- Google Ads: there is no MCP to retry. Use `scripts/ads.py`.

## PostHog: direct HogQL query

**Project ID:** `390294` (Default project under Drozq.com org).
**Auth:** `POSTHOG_API_KEY` is set as a user env var (`phx_...`). Generated at <https://app.posthog.com/settings/user-api-keys?preset=mcp_server>.
**Endpoint:** `POST https://us.posthog.com/api/projects/390294/query/`

```bash
curl -s -X POST "https://us.posthog.com/api/projects/390294/query/" \
  -H "Authorization: Bearer $POSTHOG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":{"kind":"HogQLQuery","query":"SELECT event, count() AS n FROM events WHERE timestamp >= toDate('"'"'2026-05-22'"'"') AND timestamp < toDate('"'"'2026-05-27'"'"') GROUP BY event ORDER BY n DESC LIMIT 20"}}' \
  | python -c "import sys, json; d=json.loads(sys.stdin.read()); print('cols:', d.get('columns')); [print(r) for r in d.get('results', [])]"
```

### Patterns that work

- **Date filtering:** use `toDate('YYYY-MM-DD')` in `WHERE timestamp >= ... AND timestamp < ...`. The `'YYYY-MM-DD'` literal must be single-quoted, so escape it as `'"'"'YYYY-MM-DD'"'"'` inside a bash single-quoted JSON body.
- **Properties:** `properties.mode`, `properties.to_step`, `properties.gclid`, `properties.$session_id`, `properties.$current_url`, `properties.$session_entry_url`.
- **Session aggregation:** `count(DISTINCT properties.$session_id)` rather than `count()` when you want sessions, not events.
- **Paid traffic filter:**
  ```sql
  WITH paid AS (
    SELECT DISTINCT properties.$session_id AS sid
    FROM events
    WHERE timestamp >= toDate('2026-05-22')
      AND (properties.$current_url LIKE '%gclid=%'
           OR properties.gclid IS NOT NULL
           OR properties.$session_entry_url LIKE '%gclid=%')
  )
  SELECT ... WHERE properties.$session_id IN (SELECT sid FROM paid)
  ```
- **Funnel events** (per `CLAUDE.md`): `funnel_open`, `funnel_step_advance`, `funnel_back`, `funnel_option_selected`, `funnel_submit_attempt`, `funnel_submit_success`, `funnel_submit_error`, `lead_confirmed`. Mode: `sell` | `buy` | `sellandbuy`.

### Output post-processing

The JSON shape is `{"columns": [...], "results": [[...], [...], ...]}`. Quick line-by-line view:

```bash
| python -c "import sys, json; d=json.loads(sys.stdin.read()); print('cols:', d.get('columns')); [print(r) for r in d.get('results', [])]"
```

For raw debug (e.g. when results is empty), pipe to `head -300` instead of the python one-liner.

## Google Ads: scripts/ads.py (refresh-token auth, no gcloud)

**Customer ID (drozq operating account):** `3351363652`.
**Login (MCC manager):** `1975174499`.
**Developer token:** `$GOOGLE_ADS_DEVELOPER_TOKEN` (user env var; also copied into the creds file at setup).
**Auth:** a long-lived OAuth **refresh token** stored in `scripts/.google_ads.json` (gitignored). `scripts/ads.py` exchanges it for an access token against `https://oauth2.googleapis.com/token` on every run. No gcloud, no ADC, no MCP. This replaced the old `gcloud auth application-default` flow, which broke roughly weekly (Testing-mode refresh tokens expire every 7 days) and then started hard-blocking consent.

### Run a pull

```
python scripts/ads.py                  # full decision pull: account, bidding strategy, 30-day perf, impression share, keywords (bid vs top-of-page estimate + QS), search terms, devices
python scripts/ads.py "SELECT campaign.name, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_7_DAYS"
```

The script paginates, converts micros to USD, and derives CPC / CPL / CVR itself (it does not trust `cost_per_conversion` units).

### One-time setup (only if scripts/.google_ads.json is missing or the token was revoked)

1. **Publish the OAuth consent screen to Production** so the refresh token does NOT expire every 7 days (Testing mode is exactly what kept breaking this, and it eventually hard-blocks consent):
   <https://console.cloud.google.com/auth/audience?project=drozq-ads-mcp> then **PUBLISH APP** and confirm.
2. Mint a fresh refresh token. This opens a browser; Joshua signs in as `guerrerojoshua720@gmail.com`, clicks **Advanced -> Continue** on the "Google hasn't verified this app" warning, then **Allow**:
   ```
   python scripts/google_ads_auth.py
   ```
   It reuses the OAuth client_id/secret from the old gcloud ADC file (`%APPDATA%\gcloud\application_default_credentials.json`) and writes `scripts/.google_ads.json`. It requests only the `adwords` scope (no `cloud-platform`).
3. Re-run `python scripts/ads.py`.

If `ads.py` prints `invalid_grant`, the refresh token was revoked (someone hit "Remove access" on the Google account, or the app slipped back to Testing and aged out). Re-run step 2; if it recurs, confirm the app is still **In production** in step 1.

**Endpoint (what ads.py calls):** `POST https://googleads.googleapis.com/<API_VERSION>/customers/3351363652/googleAds:search` with headers `Authorization: Bearer <access_token>`, `developer-token: <token>`, `login-customer-id: 1975174499`. The version is pinned in `ads.py` (`API_VERSION`, default `v24` as of 2026-07-01; override with the `GOOGLE_ADS_API_VERSION` env var). Google hard-blocks deprecated versions (`UNSUPPORTED_VERSION` on every query, seen 2026-07-01 when v20 died); when that happens, probe upward (`$env:GOOGLE_ADS_API_VERSION='v25'; python scripts/ads.py "SELECT customer.id FROM customer LIMIT 1"`) and bump the default in `ads.py`.

### Useful resources

- `campaign` - campaign-level rollup. Fields: `campaign.id/name/status/advertising_channel_type/bidding_strategy_type`, `campaign_budget.amount_micros`, plus impression-share metrics.
- `ad_group` - ad-group rollup, incl. `ad_group.cpc_bid_micros`.
- `keyword_view` - keyword performance + `ad_group_criterion.quality_info.quality_score` and `ad_group_criterion.position_estimates.top_of_page_cpc_micros` (the bid estimate used to set a CPC cap).
- `search_term_view` - the live search-terms report. Fields: `search_term_view.search_term`, `segments.keyword.info.text`, all `metrics.*`.
- `customer` - account-level info.

### Date ranges

- `DURING LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS`, `TODAY`, `YESTERDAY`.
- Or explicit: `BETWEEN '2026-05-22' AND '2026-05-26'`.

### Cost conversion

All money is in micros: divide by `1_000_000` to get USD. Impression-share metrics are fractions in `[0,1]` (e.g. `0.83` = 83%).

```python
import sys, json
d = json.loads(sys.stdin.read())
for row in d.get('results', []):
    cost = int(row.get('metrics', {}).get('costMicros', 0)) / 1_000_000
    print(row.get('searchTermView', {}).get('searchTerm'), '|', cost)
```

## When the workaround should ALSO fail and we genuinely need help

- PostHog: `phx_...` key revoked or rotated. Joshua needs to regenerate at `/settings/user-api-keys?preset=mcp_server` and re-set the env var.
- Google Ads:
  - `invalid_grant` from `ads.py` -> refresh token revoked. Re-run `scripts/google_ads_auth.py` (one-time setup above).
  - `google_ads_auth.py` says "This app is blocked" / no code received -> the consent screen is back in Testing or the project's OAuth client was deleted. Publish to Production (step 1) and, if needed, recreate a Desktop OAuth client under `drozq-ads-mcp` and set `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` before rerunning.
  - "developer token is invalid" -> confirm `$GOOGLE_ADS_DEVELOPER_TOKEN` at <https://ads.google.com/aw/apicenter>.

Otherwise: **do not retry the PostHog MCP. Use these calls.**
