# Drozq Operating Dashboard

Last updated: August 14, 2026

## 1. Architecture

`/dashboard` is a static Cloudflare Pages page. It requests only the sanitized `GET /api/dashboard/summary` endpoint and never contacts Follow Up Boss, Google Ads, or Google OAuth from the browser.

The separate `drozq-operating-dashboard` Cloudflare Worker owns all credentials and upstream requests. Its production route is restricted to `drozq.com/api/dashboard*`, so it cannot intercept the rest of the Pages site or the existing `/api/lead` and `/api/geo` Pages Functions.

The Worker runs every minute, which is the fastest Cloudflare Cron Trigger interval:

```text
* * * * *
```

Each synchronization queries Follow Up Boss and Google Ads concurrently, merges successful results with the previous snapshot, and writes `dashboard:snapshot:v2` to Workers KV. A failed metric retains its last valid value and becomes stale. A first-run failure is unavailable, never a false zero.

The public contract contains exactly eight aggregate metrics:

1. Calls sent today
2. Texts sent today
3. Emails sent today
4. Appointments set month to date
5. Fresh buyer leads from the rolling previous four weeks
6. Fresh seller leads from the rolling previous four weeks
7. Google Ads spend month to date across all linked leaf accounts
8. Google Ads primary conversions month to date across all linked leaf accounts

The page polls the saved summary every 15 seconds while visible. The public response has a 10-second cache policy. External APIs are still contacted only by the one-minute schedule or the protected manual sync endpoint. A metric becomes stale after five minutes without a successful source update.

There is no Claude, OpenAI, AI inference, model call, or other nondeterministic runtime dependency. This is a direct API-to-KV-to-dashboard pipeline.

## 2. Install and verify

Use the repository's existing npm workspace and lockfile:

```powershell
npm ci
npm run dashboard:test
npm run dashboard:typecheck
npm run dashboard:build
```

Do not add another package manager or lockfile.

## 3. Follow Up Boss setup

Create a dedicated API key in Follow Up Boss for the user whose personal activity should appear on the dashboard. The key's `/me` identity defines "I" for calls, texts, emails, and appointments.

Store the required key:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put FUB_API_KEY
Set-Location ../..
```

If the Follow Up Boss account requires partner identification, also store:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put FUB_X_SYSTEM
npx wrangler secret put FUB_X_SYSTEM_KEY
Set-Location ../..
```

The `Seller` tag is configured in `wrangler.jsonc` as `FUB_SELLER_TAG`. Tag matching ignores capitalization and surrounding whitespace. A fresh contact with the Seller tag is counted as a seller. Other accessible fresh contacts are counted as buyers.

`FUB_ASSIGNED_USER_ID` is optional. If set, it scopes only the two fresh-lead counts. Leave it unset to count all accessible fresh contacts:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put FUB_ASSIGNED_USER_ID
Set-Location ../..
```

The activity definitions are deliberate:

- Calls are outbound call records whose `userId` matches the API-key user.
- Texts are manual outbound text records for that user. Incoming and action-plan messages are excluded.
- Emails are sent manual email records for that user. Drafts, other users, action plans, and campaigns are excluded.
- Appointments are records created during the current local month whose `createdById` matches the API-key user. The assignee does not change who set the appointment.
- Today and month boundaries use `REPORTING_TIME_ZONE`, currently `America/Los_Angeles`.

Follow Up Boss does not permit this non-owner key to use the account-level agent-activity report or webhooks. The Worker therefore uses the documented REST resources directly. Text and email IDs are hashed before the daily deduplication state is stored in KV. No message content, person name, email address, phone number, or contact record is persisted. A full daily reconciliation runs at least hourly, with incremental scans between reconciliations. This avoids the Follow Up Boss report's roughly 10-minute cache while controlling API volume.

## 4. Google Ads setup

The OAuth user must be able to access the manager account and every advertising account that should be included. Obtain:

- A Google Ads developer token
- An OAuth client ID and client secret
- An offline refresh token for the authorized Google user
- The manager customer ID, without hyphens

Store the credentials:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put GOOGLE_ADS_DEVELOPER_TOKEN
npx wrangler secret put GOOGLE_ADS_CLIENT_ID
npx wrangler secret put GOOGLE_ADS_CLIENT_SECRET
npx wrangler secret put GOOGLE_ADS_REFRESH_TOKEN
npx wrangler secret put GOOGLE_ADS_LOGIN_CUSTOMER_ID
npx wrangler secret put GOOGLE_ADS_CUSTOMER_ID
Set-Location ../..
```

`GOOGLE_ADS_LOGIN_CUSTOMER_ID` must be the manager account for the production all-account view. `GOOGLE_ADS_CUSTOMER_ID` is the fallback single account used only when a manager ID is not configured. The original known fallback is `8004133723`, stored without hyphens. Do not put either value into business logic.

At runtime the Worker recursively discovers all accessible, non-hidden, non-test leaf accounts beneath the manager. It caches only the leaf account IDs for ten minutes. New linked accounts are picked up automatically. If any child query fails, neither Ads metric publishes a partial total. The prior complete total remains visible as stale.

One OAuth access token is reused for the complete synchronization. Each leaf account receives one aggregate GAQL query:

```sql
SELECT
  metrics.cost_micros,
  metrics.conversions
FROM customer
WHERE segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
```

Spend is the exact sum of `cost_micros` divided by 1,000,000. Leads are the sum of the Google Ads `Conversions` column, represented by `metrics.conversions`, across all linked leaf accounts. This intentionally includes every primary conversion in account performance and no longer filters to one action name or one child account. It does not use `metrics.all_conversions`, which can include local actions and other secondary engagement events.

The configured API version is `v25`. Review Google Ads API sunset notices before that version is retired and update only `GOOGLE_ADS_API_VERSION` after tests pass.

### Conversion action diagnostic

The local diagnostic lists non-removed conversion actions across every discovered leaf account. It prints no OAuth credential, developer token, or refresh token:

```powershell
$env:GOOGLE_ADS_DEVELOPER_TOKEN = Read-Host "Developer token"
$env:GOOGLE_ADS_CLIENT_ID = Read-Host "OAuth client ID"
$env:GOOGLE_ADS_CLIENT_SECRET = Read-Host "OAuth client secret"
$env:GOOGLE_ADS_REFRESH_TOKEN = Read-Host "OAuth refresh token"
$env:GOOGLE_ADS_LOGIN_CUSTOMER_ID = Read-Host "Manager customer ID without hyphens"
npm run dashboard:list-google-ads-actions
Remove-Item Env:GOOGLE_ADS_DEVELOPER_TOKEN, Env:GOOGLE_ADS_CLIENT_ID, Env:GOOGLE_ADS_CLIENT_SECRET, Env:GOOGLE_ADS_REFRESH_TOKEN, Env:GOOGLE_ADS_LOGIN_CUSTOMER_ID
```

The legacy `GOOGLE_ADS_LEAD_CONVERSION_ACTION_NAMES` secret is no longer read by production. It may be deleted:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret delete GOOGLE_ADS_LEAD_CONVERSION_ACTION_NAMES
Set-Location ../..
```

Changing a conversion action from `generate_lead` to `lead_confirmed` no longer requires a dashboard code or configuration change because the dashboard follows the account's primary conversion configuration. During a migration, ensure Google Ads does not mark both actions primary if that would double-count the same submission.

## 5. Google Sheets adapter status

The earlier Shell Pages Remaining card was replaced by the current operating metrics. The tested Google Sheets service-account adapter remains isolated in the Worker source for rollback compatibility, but the production synchronization does not call it and no Sheet data is in the public contract.

Legacy Sheets secrets may be deleted without affecting the current dashboard:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret delete GOOGLE_SERVICE_ACCOUNT_EMAIL
npx wrangler secret delete GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY
npx wrangler secret delete GOOGLE_SHEETS_SPREADSHEET_ID
npx wrangler secret delete GOOGLE_SHEETS_REMAINING_RANGE
npx wrangler secret delete GOOGLE_SHEETS_PAGES_RANGE
Set-Location ../..
```

If the card is deliberately restored later, the adapter supports a nonnegative direct cell or a `Page` and `Status` table, uses a read-only Google service account, normalizes escaped private-key newlines, and stores only the aggregate count.

## 6. Workers KV

The production namespace is already bound as `DASHBOARD_KV` in `wrangler.jsonc`. To provision a separate environment:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler kv namespace create DASHBOARD_KV
Set-Location ../..
```

Put the returned namespace ID into the `DASHBOARD_KV` binding. Do not rename these stable keys:

- `dashboard:snapshot:v2`: sanitized public snapshot
- `dashboard:fub:activity:v2`: counts, checkpoints, and hashed daily message IDs only
- `dashboard:google_ads:accounts:v2`: short-lived leaf account ID cache
- `dashboard:sync:lease:v2`: short-lived best-effort overlap guard

KV never stores API keys, OAuth access tokens, refresh tokens, private keys, response bodies, message bodies, or contact details.

## 7. Manual synchronization token

Generate a high-entropy token, save it in the approved password manager, and store it as a Worker secret:

```powershell
$dashboardTokenBytes = New-Object byte[] 32
$dashboardTokenRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$dashboardTokenRng.GetBytes($dashboardTokenBytes)
$dashboardTokenRng.Dispose()
$dashboardAdminToken = [Convert]::ToBase64String($dashboardTokenBytes)
$dashboardAdminToken | Set-Clipboard
Set-Location cloudflare/dashboard-worker
npx wrangler secret put ADMIN_SYNC_TOKEN
Set-Location ../..
Remove-Variable dashboardTokenBytes, dashboardTokenRng, dashboardAdminToken
```

Paste the generated value only into Wrangler's hidden prompt. Invalid tokens return `401`. A valid request made while another synchronization is active returns `409` rather than starting overlapping upstream work.

## 8. Local development

Copy `.dev.vars.example` to `.dev.vars`, replace placeholders, and never commit the local file:

```powershell
Copy-Item cloudflare/dashboard-worker/.dev.vars.example cloudflare/dashboard-worker/.dev.vars
Set-Location cloudflare/dashboard-worker
npm run dev
```

In another terminal:

```powershell
Invoke-RestMethod http://localhost:8787/api/dashboard/health
Invoke-WebRequest http://localhost:8787/api/dashboard/summary
```

The summary request never contacts upstream services. It returns a saved snapshot or a valid sanitized `503` first-run payload.

Test the scheduled handler locally:

```powershell
Set-Location cloudflare/dashboard-worker
npm run dev:scheduled
```

Then, from another terminal:

```powershell
Invoke-WebRequest "http://localhost:8787/cdn-cgi/handler/scheduled?cron=%2A%20%2A%20%2A%20%2A%20%2A"
```

## 9. Production deployment

Run the complete gate, then deploy only the Worker:

```powershell
npm run dashboard:check
Set-Location cloudflare/dashboard-worker
npx wrangler deploy
Set-Location ../..
```

The route must remain exactly `drozq.com/api/dashboard*`. Never broaden it to `drozq.com/*`. `workers_dev` and preview URLs remain disabled. Cloudflare can take up to roughly 15 minutes to propagate a Cron change, so use one protected manual sync immediately after a deployment.

Verify scope and headers:

```powershell
curl.exe -I https://drozq.com/dashboard
curl.exe -I https://drozq.com/Dashboard
curl.exe -i https://drozq.com/api/dashboard/health
curl.exe -i https://drozq.com/api/dashboard/summary
curl.exe -i https://drozq.com/api/dashboard/not-a-route
curl.exe -i https://drozq.com/api/geo
```

Expected results are `200`, `301` to `/dashboard`, `200`, `200` or first-run `503`, `404`, and the existing geo endpoint's normal response. The summary must include JSON content type, `nosniff`, and the documented 10-second cache policy. It must not include wildcard CORS.

## 10. Protected manual synchronization

```powershell
$dashboardSecureToken = Read-Host "ADMIN_SYNC_TOKEN" -AsSecureString
$dashboardTokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($dashboardSecureToken)
$dashboardSyncToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($dashboardTokenPointer)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($dashboardTokenPointer)
$dashboardHeaders = @{ Authorization = "Bearer $dashboardSyncToken" }
Invoke-RestMethod -Method Post -Uri "https://drozq.com/api/dashboard/admin/sync" -Headers $dashboardHeaders
Remove-Variable dashboardSecureToken, dashboardTokenPointer, dashboardSyncToken, dashboardHeaders
```

The response is the same sanitized snapshot contract as the public endpoint.

## 11. Troubleshooting and durability runbook

### Follow Up Boss `401` or `403`

- Confirm the dedicated key still exists and belongs to the intended user.
- Update `FUB_API_KEY` after any key rotation.
- Confirm the key user can access people, calls, appointments, text messages, emails, and `/me`.
- Account-level reports and webhooks require owner privileges and are not used.

### Google Ads `401` or `403`

- Confirm client ID, client secret, and refresh token belong together.
- Reauthorize with offline access if Google returns `invalid_grant`.
- Confirm the OAuth user still has access to the configured manager and children.
- Confirm the developer token remains approved for the account hierarchy.
- Confirm the login manager ID contains ten digits and no hyphens.

### `429` or transient `5xx`

Upstream requests retry no more than three times, respect `Retry-After`, and otherwise use bounded exponential backoff with jitter. Persistent failure retains the last complete value as stale. Do not shorten the one-minute Cron because Cloudflare does not support a faster schedule and higher manual frequency can cause rate limits.

### Google Ads spend or leads look low

- Check that every advertising account is linked beneath the configured manager.
- Wait ten minutes for the hierarchy cache, or run a manual sync after deleting `dashboard:google_ads:accounts:v2` from KV.
- Compare the Google Ads UI with the same reporting timezone and the `Conversions` column, not `All conversions`.
- Inspect Worker logs for a child-account error. The Worker refuses partial totals.

### Follow Up Boss activity looks low

- Verify the API key belongs to the intended agent.
- Confirm records are being saved to Follow Up Boss under that user's ID.
- Automated action-plan and campaign messages are intentionally excluded.
- Run a protected sync. The hourly full reconciliation corrects late-arriving or edited message records.

### Stale or missing metrics

A metric becomes stale after five minutes. Check structured Worker logs for source, HTTP status, duration, and sanitized error category. A missing metric with no prior value is shown as unavailable, not zero. A partial failure does not erase other sources.

### 30 to 180 day maintenance risks

- Google refresh tokens can be revoked by password, consent, or security changes. Monitor `authentication` errors.
- Google Ads API versions are sunset periodically. Review the version before `v25` retirement.
- Follow Up Boss keys are user-scoped. Role or ownership changes can change accessible records.
- New Google Ads leaf accounts are automatic, but OAuth and developer-token access must cover them.
- Changing Google Ads primary conversion settings changes the Leads number by design. Audit primary actions during tracking migrations.
- Worker Cron configuration changes can take time to propagate. Manual sync verifies deployment immediately.
- Upstream schema drift fails closed and preserves last-known-good values. Keep tests and observability enabled.
- The daily activity state resets at Los Angeles midnight and the date utility has rollover, leap-year, and DST coverage.

Review Worker errors and credential age monthly. Run `npm run dashboard:check` before any API-version or schema update.

## 12. Security and rotation

Never commit `.dev.vars`, `.env`, downloaded service-account JSON, API keys, OAuth tokens, private keys, Cloudflare API tokens, or `ADMIN_SYNC_TOKEN`. The public serializer uses an explicit allowlist and cannot return contact details, account names, campaign names, Sheet contents, credentials, or raw upstream errors.

Any credential pasted into chat, committed, logged, or shown in a screenshot must be treated as exposed and rotated. Removing it from a file or deleting a message does not revoke it.

The marketing funnel uses a browser-side Google Maps key for Places autocomplete, including in `faq/index.html`. Browser keys are public by design, but the Google Cloud key must be restricted to only the necessary Maps APIs and exact production HTTP referrers. Rotate any version that was ever unrestricted. Do not remove it without a replacement because that would break funnel address validation.

## 13. GitHub Actions

`.github/workflows/dashboard-worker.yml` runs only when Worker-related files change. It tests, type checks, builds, and then deploys only the dashboard Worker on `main` when these repository secrets exist:

- `CLOUDFLARE_API_TOKEN`, limited to the required Worker script and route permissions
- `CLOUDFLARE_ACCOUNT_ID`

Runtime API credentials remain Worker secrets and are not managed by GitHub Actions. The workflow does not touch Cloudflare Pages deployment.

## 14. Rollback

List and roll back Worker versions:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler deployments list
npx wrangler rollback <prior-version-id>
Set-Location ../..
```

Revert the exact repository release for the static page or configuration:

```powershell
git revert <release-commit-hash>
git push origin main
```

If the Worker must be removed, first remove only the narrow `drozq.com/api/dashboard*` route. Do not alter the Pages routes or existing Pages Functions.

## Official references

- https://developers.cloudflare.com/workers/configuration/cron-triggers/
- https://developers.cloudflare.com/workers/configuration/routing/routes/
- https://developers.cloudflare.com/kv/api/
- https://developers.google.com/google-ads/api/docs/oauth/overview
- https://developers.google.com/google-ads/api/docs/reporting/overview
- https://docs.followupboss.com/reference/authentication
