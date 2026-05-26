# MCP workarounds: direct REST when MCPs fail

Both the PostHog MCP and the Google Ads MCP have failed mid-session in the past (PostHog auth flakiness; Google Ads MCP cold-start timeouts / `user-cancel` errors / revoked ADC tokens). When that happens, **do not retry the MCP** — go straight to the direct REST API. Both services have working credentials in env vars on this machine.

Always prefer these direct calls over MCP retries when you see:
- MCP returns a tool-rejection / `user-cancel` immediately
- MCP `list_accessible_customers` / `tools` hangs past ~30s
- `gcloud auth application-default print-access-token` says `invalid_grant`
- PostHog MCP returns 401 or empty schema responses

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

## Google Ads: direct GAQL

**Customer ID (drozq operating account):** `3351363652`.
**Login (MCC manager):** `1975174499`.
**Developer token:** `$GOOGLE_ADS_DEVELOPER_TOKEN` (already set as a user env var).
**Access token:** comes from `gcloud auth application-default print-access-token`. The OAuth client is in "Testing" mode under the `drozq-ads-mcp` GCP project, which means **refresh tokens expire every 7 days**. When they do, you'll see `invalid_grant: Token has been expired or revoked.` and have to ask Joshua to re-auth:

```
! "C:\Users\guerr\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" auth application-default login --scopes=https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform
```

(Joshua signs in as `guerrerojoshua720@gmail.com`. The "unverified app" warning is expected — click Advanced → Continue. Token persists for another 7 days.)

**Endpoint:** `POST https://googleads.googleapis.com/v20/customers/3351363652/googleAds:search`

```bash
TOKEN=$("/c/Users/guerr/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd" auth application-default print-access-token 2>/dev/null)

curl -s -X POST "https://googleads.googleapis.com/v20/customers/3351363652/googleAds:search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "developer-token: $GOOGLE_ADS_DEVELOPER_TOKEN" \
  -H "login-customer-id: 1975174499" \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT search_term_view.search_term, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM search_term_view WHERE segments.date DURING LAST_7_DAYS ORDER BY metrics.cost_micros DESC LIMIT 50"}' \
  | python -c "import sys, json; d=json.loads(sys.stdin.read()); print(json.dumps(d, indent=2)[:5000])"
```

### Useful resources

- `campaign` — campaign-level rollup. Fields: `campaign.id/name/status/advertising_channel_type`, `campaign_budget.amount_micros`.
- `ad_group` — ad-group rollup.
- `search_term_view` — the live search-terms report. Fields: `search_term_view.search_term`, `segments.keyword.info.text`, all `metrics.*`.
- `keyword_view` — keyword-level performance.
- `customer` — account-level info.

### Date ranges

- `DURING LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS`, `TODAY`, `YESTERDAY`.
- Or explicit: `BETWEEN '2026-05-22' AND '2026-05-26'`.

### Cost conversion

All money is `metrics.cost_micros` in micros: divide by `1_000_000` to get USD.

```python
import sys, json
d = json.loads(sys.stdin.read())
for row in d.get('results', []):
    cost = int(row.get('metrics', {}).get('costMicros', 0)) / 1_000_000
    print(row.get('searchTermView', {}).get('searchTerm'), '|', cost)
```

## When the workaround should ALSO fail and we genuinely need help

- PostHog: `phx_...` key revoked or rotated. Joshua needs to regenerate at `/settings/user-api-keys?preset=mcp_server` and re-set the env var.
- Google Ads: developer token revoked OR Joshua hasn't logged into Google Ads in the project for so long that the OAuth client got hard-deleted. The developer token is in `$GOOGLE_ADS_DEVELOPER_TOKEN`; if Google says "developer token is invalid," ask Joshua to confirm the token at <https://ads.google.com/aw/apicenter>.

Otherwise: **do not retry the MCP. Use these calls.**
