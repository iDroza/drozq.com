# Drozq Operating Dashboard Setup

Last reviewed: August 14, 2026

This runbook deploys the public operating dashboard at `https://drozq.com/dashboard` and its isolated Worker at `https://drozq.com/api/dashboard*`.

## 1. Architecture

The browser loads three static Cloudflare Pages files:

- `dashboard/index.html`
- `dashboard/dashboard.css`
- `dashboard/dashboard.js`

The page reads only `GET /api/dashboard/summary`. It never uses dashboard credentials and never requests Follow Up Boss, Google Ads, Google Sheets, or Google OAuth data directly.

The separate `drozq-operating-dashboard` Worker owns all data access. Its `scheduled()` handler runs every five minutes, requests the three sources concurrently, normalizes four numbers, merges failures with the prior valid snapshot, and writes one sanitized object to Workers KV under `dashboard:snapshot:v1`. The public summary handler reads KV only. `POST /api/dashboard/admin/sync` runs the same synchronization function after bearer-token authentication.

The existing Cloudflare Pages project and its `/functions/api/lead.js`, `/functions/api/geo.js`, and other endpoints are separate. The Worker route is deliberately limited to `drozq.com/api/dashboard*`.

No AI model, inference endpoint, Claude API, OpenAI API, or other paid model call exists in this runtime. This is a deterministic API-to-KV-to-dashboard pipeline.

## 2. Prerequisites and install

Use Node.js 22 or newer and log Wrangler into the Cloudflare account that owns the `drozq.com` zone.

```powershell
Set-Location C:\Users\guerr\Documents\drozq.com
npm install
npx wrangler login
npm run dashboard:check
```

For local development, copy the placeholder file and replace every angle-bracket value that applies:

```powershell
Copy-Item cloudflare/dashboard-worker/.dev.vars.example cloudflare/dashboard-worker/.dev.vars
```

`.dev.vars`, `.env`, Wrangler state, build output, and installed packages are ignored by Git. Never put real credentials in `.dev.vars.example` or `wrangler.jsonc`.

## 3. Follow Up Boss

Create or retrieve an API key for the Follow Up Boss user whose accessible contacts should be counted. The Worker calls `GET https://api.followupboss.com/v1/people` with Basic authentication, a blank password, `tags=Seller`, `includeTrash=false`, `limit=1`, and `fields=id`. It stores only `_metadata.total`.

Defaults and options:

- `FUB_SELLER_TAG` defaults to `Seller`.
- `FUB_ASSIGNED_USER_ID` is optional. Set it to narrow the count to one assigned user.
- `FUB_X_SYSTEM` and `FUB_X_SYSTEM_KEY` are optional paired integration headers. Set them only when Follow Up Boss has issued them.
- Trash is always excluded.

Set production credentials from the Worker directory:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put FUB_API_KEY
npx wrangler secret put FUB_X_SYSTEM
npx wrangler secret put FUB_X_SYSTEM_KEY
npx wrangler secret put FUB_ASSIGNED_USER_ID
Set-Location ../..
```

Skip the three optional commands when they do not apply. To change the public tag without code changes, edit `FUB_SELLER_TAG` in `wrangler.jsonc` and deploy.

Follow Up Boss currently needs an active account and API access. A `403` from this source commonly means the authenticated user cannot access the requested records, the API key is invalid for the account, or the account is inactive.

## 4. Google Ads developer token and OAuth

The requested dashboard default is customer `800-413-3723`. The Worker stores and sends it as `8004133723`. That default lives in typed configuration, not business-logic code, and production can override it with the `GOOGLE_ADS_CUSTOMER_ID` secret.

Production note, August 14, 2026: Google Ads returned `CUSTOMER_NOT_FOUND` for `8004133723`, and that customer was absent from the authenticated manager hierarchy. The live Worker therefore uses the verified active real-estate customer `7216252244` through an encrypted override. Once `8004133723` is linked to the manager and accessible to the OAuth identity, update only `GOOGLE_ADS_CUSTOMER_ID` and rerun the diagnostic before synchronizing.

1. In the Google Ads manager account, open API Center and obtain an approved developer token.
2. In Google Cloud, configure an OAuth consent screen and create an OAuth client.
3. Authorize a Google user that can access customer `800-413-3723` with the `https://www.googleapis.com/auth/adwords` scope and offline access.
4. Capture the OAuth client ID, client secret, and refresh token. Never commit them.
5. Set `GOOGLE_ADS_LOGIN_CUSTOMER_ID` only when requests must pass through a manager account. Store it without hyphens.

The repository's existing `scripts/google_ads_auth.py` can mint an offline Google Ads refresh token, but it belongs to an older reporting workflow with different account defaults. Do not copy those account IDs into this dashboard. The refresh token may be reused only if its Google user has access to the dashboard customer.

Set the Worker secrets:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put GOOGLE_ADS_DEVELOPER_TOKEN
npx wrangler secret put GOOGLE_ADS_CLIENT_ID
npx wrangler secret put GOOGLE_ADS_CLIENT_SECRET
npx wrangler secret put GOOGLE_ADS_REFRESH_TOKEN
npx wrangler secret put GOOGLE_ADS_CUSTOMER_ID
npx wrangler secret put GOOGLE_ADS_LOGIN_CUSTOMER_ID
npx wrangler secret put GOOGLE_ADS_LEAD_CONVERSION_ACTION_NAMES
Set-Location ../..
```

Skip `GOOGLE_ADS_LOGIN_CUSTOMER_ID` when the customer can be addressed directly. The current API version is configured as `v25`.

### List conversion-action names

The diagnostic prints only action name, status, and type. It never prints credentials, access tokens, customer names, or raw API responses. Provide credentials in the current process, run it, then clear them:

```powershell
$env:GOOGLE_ADS_DEVELOPER_TOKEN = "<developer-token>"
$env:GOOGLE_ADS_CLIENT_ID = "<oauth-client-id>"
$env:GOOGLE_ADS_CLIENT_SECRET = "<oauth-client-secret>"
$env:GOOGLE_ADS_REFRESH_TOKEN = "<oauth-refresh-token>"
$env:GOOGLE_ADS_CUSTOMER_ID = "8004133723"
$env:GOOGLE_ADS_LOGIN_CUSTOMER_ID = "<optional-manager-id>"
npm run dashboard:list-google-ads-actions
Remove-Item Env:GOOGLE_ADS_DEVELOPER_TOKEN, Env:GOOGLE_ADS_CLIENT_ID, Env:GOOGLE_ADS_CLIENT_SECRET, Env:GOOGLE_ADS_REFRESH_TOKEN, Env:GOOGLE_ADS_CUSTOMER_ID, Env:GOOGLE_ADS_LOGIN_CUSTOMER_ID -ErrorAction SilentlyContinue
```

The intended lead event is `generate_lead`. Google Ads can prefix imported GA4 action names with the property or stream name, so configure the exact name printed by the diagnostic. The live `7216252244` override is `ActiveRealty.com (web) generate_lead`. The Worker compares names case-insensitively and counts only configured names. A configured action that does not exist is reported as unavailable, never as a false zero.

To migrate later to `lead_confirmed`, first list the available actions, then update only the encrypted configuration:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put GOOGLE_ADS_LEAD_CONVERSION_ACTION_NAMES
Set-Location ../..
```

Comma-separated names are supported. During an overlapping migration, do not configure both `generate_lead` and `lead_confirmed` unless both represent distinct leads. If both fire for the same submission, configuring both will double-count.

## 5. Google Sheets service account

1. In a Google Cloud project, enable Google Sheets API v4.
2. Create a service account with no broad project role. The Sheet itself grants access.
3. Create a JSON key for that account.
4. Copy only `client_email` and `private_key` into the matching Worker secrets.
5. Share the target Google Sheet with the service-account email as Viewer.
6. Delete or securely archive the downloaded JSON key. Never place it in this repository.

The Worker normalizes either real newlines or escaped `\n` characters in the private key before Web Crypto signing.

Set the core secrets:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put GOOGLE_SERVICE_ACCOUNT_EMAIL
npx wrangler secret put GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY
npx wrangler secret put GOOGLE_SHEETS_SPREADSHEET_ID
Set-Location ../..
```

### Sheet mode A: direct cell

Set one A1 range whose first value is a nonnegative whole number. Example: `Dashboard Inputs!B2`.

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put GOOGLE_SHEETS_REMAINING_RANGE
Set-Location ../..
```

When this value is present, it takes priority over table mode.

The live production Sheet uses direct-cell range `Summary!B5`. The service account `drozq-dashboard-sheets@drozq-ads-mcp.iam.gserviceaccount.com` has Viewer access only. Its downloaded JSON key was removed after the private key was stored as a Worker secret.

### Sheet mode B: page table

Do not set the direct-cell range. Set a range that includes the header row and all page rows, for example `Shell Pages!A:B`:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret delete GOOGLE_SHEETS_REMAINING_RANGE
npx wrangler secret put GOOGLE_SHEETS_PAGES_RANGE
Set-Location ../..
```

Default headers are `Page` and `Status`. Default complete values are `complete,completed,done,published,live`. Matching ignores capitalization and surrounding whitespace. Every nonblank page row whose status is not complete is counted. Fully blank rows and rows without a page value are ignored.

Change headers or complete values through `GOOGLE_SHEETS_PAGE_HEADER`, `GOOGLE_SHEETS_STATUS_HEADER`, and `GOOGLE_SHEETS_COMPLETE_VALUES` in `wrangler.jsonc`. If neither range is configured, the public metric is `unconfigured`, not zero.

## 6. Workers KV

The live namespace is already provisioned and its non-secret namespace ID is committed in `wrangler.jsonc`. To deploy into another Cloudflare account, create a replacement namespace:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler kv namespace create DASHBOARD_KV
Set-Location ../..
```

Wrangler prints a 32-character namespace ID. Replace the existing production ID in `cloudflare/dashboard-worker/wrangler.jsonc` only when moving the Worker to another account:

```json
"kv_namespaces": [
  {
    "binding": "DASHBOARD_KV",
    "id": "<production-kv-namespace-id>"
  }
]
```

Do not rename the `DASHBOARD_KV` binding or the stable `dashboard:snapshot:v1` key.

## 7. Admin synchronization token

Generate a high-entropy token locally, copy it, and store it with Wrangler:

```powershell
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$token = [Convert]::ToBase64String($bytes)
$token | Set-Clipboard
Set-Location cloudflare/dashboard-worker
npx wrangler secret put ADMIN_SYNC_TOKEN
Set-Location ../..
Remove-Variable token, bytes, rng
```

Paste the generated value only into Wrangler's hidden prompt. Store it in the approved password manager. The endpoint compares SHA-256 digests with a timing-safe primitive when available in Workers.

## 8. Local development

After filling `cloudflare/dashboard-worker/.dev.vars`:

```powershell
Set-Location cloudflare/dashboard-worker
npm run dev
```

In another terminal:

```powershell
Invoke-RestMethod http://localhost:8787/api/dashboard/health
Invoke-WebRequest http://localhost:8787/api/dashboard/summary
```

The summary request never contacts upstream services. It returns the current local KV snapshot or a valid `503` unconfigured payload when none exists.

To test the scheduled handler locally:

```powershell
Set-Location cloudflare/dashboard-worker
npm run dev:scheduled
```

Then call Wrangler's scheduled-test endpoint from another terminal:

```powershell
Invoke-WebRequest "http://localhost:8787/cdn-cgi/handler/scheduled?cron=%2A%2F5%20%2A%20%2A%20%2A%20%2A"
```

Inspect structured logs for source, HTTP status, duration, result, and sanitized error category. Logs must never contain tokens, authorization headers, private keys, full response bodies, or contact data.

## 9. Test and production build

From the repository root:

```powershell
npm run dashboard:test
npm run dashboard:typecheck
npm run dashboard:build
```

The tests mock every external request. They do not call live APIs.

## 10. Production deployment

Confirm the KV ID has replaced the placeholder and all required secrets are set, then deploy only the dashboard Worker:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler deploy
Set-Location ../..
```

Wrangler deploys `drozq-operating-dashboard`, installs the `*/5 * * * *` Cron Trigger, and routes only `drozq.com/api/dashboard*`. `workers_dev` and preview URLs are disabled. Cloudflare Pages remains responsible for every other path.

The Pages side deploys through the repository's existing main-branch auto-deployment. `_redirects` sends `/Dashboard`, `/Dashboard/`, and `/dashboard/` to the canonical `/dashboard` with HTTP 301, then internally serves the directory index at the no-slash canonical path.

Verify route scope and health:

```powershell
curl.exe -I https://drozq.com/dashboard
curl.exe -I https://drozq.com/Dashboard
curl.exe -i https://drozq.com/api/dashboard/health
curl.exe -i https://drozq.com/api/dashboard/summary
curl.exe -i https://drozq.com/api/dashboard/not-a-route
curl.exe -i https://drozq.com/api/geo
```

Expected results are `200`, `301` to `/dashboard`, `200`, `200` or first-run `503`, `404`, and the existing geo endpoint's normal response. The summary response should include `Content-Type: application/json`, `X-Content-Type-Options: nosniff`, and the documented 60-second cache policy. It should not include `Access-Control-Allow-Origin: *`.

## 11. Manual synchronization

Run one protected synchronization after the first deploy so the dashboard does not wait for the next Cron Trigger:

```powershell
$secureToken = Read-Host "ADMIN_SYNC_TOKEN" -AsSecureString
$tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
$syncToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
$headers = @{ Authorization = "Bearer $syncToken" }
Invoke-RestMethod -Method Post -Uri "https://drozq.com/api/dashboard/admin/sync" -Headers $headers
Remove-Variable secureToken, tokenPointer, syncToken, headers
```

The response is the same sanitized aggregate contract as the public summary. An incorrect or missing token returns `401`.

## 12. Troubleshooting

### `401`

- Follow Up Boss: recreate the API key and update `FUB_API_KEY`.
- Google OAuth: confirm client ID, client secret, and refresh token belong together. Reauthorize with offline access if Google returns `invalid_grant`.
- Manual sync: confirm the bearer value exactly matches `ADMIN_SYNC_TOKEN`.

### `403`

- Follow Up Boss: confirm the account is active and the API-key user can access the tagged contacts. The repository notes that the prior personal Follow Up Boss subscription may be inactive, so reactivation may be required.
- Google Ads: verify the OAuth user can access customer `800-413-3723`, the developer token has sufficient access, and the optional login customer is the correct manager.
- Google Sheets: share the Sheet with the exact service-account email as Viewer and confirm Sheets API v4 is enabled.

### `429`

The Worker retries up to three attempts, honors `Retry-After`, and otherwise uses exponential backoff with jitter. Persistent rate limiting leaves the prior value visible as stale. Do not shorten the five-minute Cron interval.

### Stale data

A value becomes stale after more than 15 minutes without a successful source update. Check Worker logs, then invoke the protected manual sync. A partial failure never erases a prior valid number.

### Missing Google Ads leads

Run `npm run dashboard:list-google-ads-actions`. Confirm the exact action exists and set `GOOGLE_ADS_LEAD_CONVERSION_ACTION_NAMES`. An action can exist with a legitimate zero month-to-date count. A name that does not exist is not displayed as zero.

### Missing Sheet metric

Configure exactly one intended input mode, confirm the range includes readable values, and check that direct-cell data is a nonnegative integer. For table mode, ensure the range includes both configured headers.

## 13. Security and secret rotation

Never commit `.dev.vars`, `.env`, downloaded service-account JSON, OAuth tokens, API keys, Cloudflare tokens, or `ADMIN_SYNC_TOKEN`. Worker secrets are encrypted bindings and are never stored in KV. KV contains only the four normalized numbers, source identifiers, definitions, statuses, dates, and timestamps.

The existing marketing funnel loads a browser-side Google Maps key for Places autocomplete, including on `faq/index.html`. A browser key is necessarily public, but any key that may have been exposed without strict restrictions must be rotated in Google Cloud. Restrict its replacement to the required Maps APIs and the exact production HTTP referrers. Removing it without a replacement would break address validation in the lead funnel, so this dashboard change does not remove it.

Rotate any credential immediately if it has appeared in source control, logs, chat, screenshots, or an untrusted machine. Removing a credential from the current file does not revoke it. After rotation, update the Wrangler secret and deploy again.

## 14. Optional GitHub Actions deployment

`.github/workflows/dashboard-worker.yml` runs only when dashboard Worker or related package files change. It installs dependencies, runs tests, type checking, and the production dry-run build. On pushes to `main`, it deploys only the dashboard Worker when these repository settings exist:

- Secret: `CLOUDFLARE_API_TOKEN`, scoped to `Workers Scripts:Edit` for the production account and `Workers Routes:Edit` for the `drozq.com` zone. KV permission is not required for deployment because the namespace already exists and its binding ID is committed.
- Secret: `CLOUDFLARE_ACCOUNT_ID`.
- Repository variable: `DASHBOARD_KV_NAMESPACE_ID`, required only while the all-zero placeholder remains in the committed Wrangler file. It can be omitted after the real namespace ID is committed.

Runtime API credentials remain Wrangler secrets. GitHub Actions does not create, replace, or manage them. If either Cloudflare credential secret is absent, verification still runs and deployment is skipped.

As of August 14, 2026, both GitHub secrets are configured and a complete CI deployment has succeeded.

## 15. Rollback

List Worker deployments and roll back to the prior version:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler deployments list
npx wrangler rollback <prior-version-id>
Set-Location ../..
```

For the static dashboard or configuration committed to Git, revert the exact release commit and push it:

```powershell
git revert <release-commit-hash>
git push origin main
```

If the Worker must be removed entirely, first remove or disable the narrow `drozq.com/api/dashboard*` route in Cloudflare, then remove the Worker. Do not broaden, alter, or delete the Cloudflare Pages routes or existing Pages Functions.

## Official references

- [Cloudflare Workers routes](https://developers.cloudflare.com/workers/configuration/routing/routes/)
- [Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
- [Cloudflare Workers KV bindings](https://developers.cloudflare.com/kv/api/)
- [Google Ads API OAuth](https://developers.google.com/google-ads/api/docs/oauth/overview)
- [Google Ads API REST](https://developers.google.com/google-ads/api/rest/overview)
- [Google service-account OAuth](https://developers.google.com/identity/protocols/oauth2/service-account)
- [Google Sheets values API](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/get)
- [Follow Up Boss API authentication](https://docs.followupboss.com/reference/authentication)
