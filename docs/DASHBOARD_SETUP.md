# Drozq Operating Dashboard

Last updated: August 20, 2026

## 1. Architecture

`/dashboard` is a static Cloudflare Pages page. It reads only sanitized aggregate data from the dashboard Worker and never contacts Follow Up Boss, Google Ads, Google Search Console, the Active Realty publisher, Google Sheets, or Google OAuth from the browser. Normal refreshes use `GET /api/dashboard/summary`. A same-origin `GET /api/dashboard/bootstrap.js` transport loads the same allowlisted snapshot before the controller runs and provides an automatic fallback when a browser, extension, or privacy layer blocks `fetch`.

`/active` is the company-facing Active Realty view. It uses the same saved snapshot and visual system, but reads a separate explicit allowlist through `GET /api/dashboard/active-summary` and `GET /api/dashboard/active-bootstrap.js`. Those responses exclude calls, texts, emails, appointments, fresh buyer leads, fresh seller leads, personal year-to-date dials, and personal year-to-date closings at the Worker serialization boundary. The page is `noindex,nofollow,noarchive`, has no Drozq or individual-agent branding, and is not linked from public navigation or the sitemap.

The separate `drozq-operating-dashboard` Cloudflare Worker owns all credentials and upstream requests. Its production route is restricted to `drozq.com/api/dashboard*`, so it cannot intercept the rest of the Pages site or the existing `/api/lead` and `/api/geo` Pages Functions.

The Worker runs every ten minutes:

```text
*/10 * * * *
```

The cadence is a Workers KV write budget, not a Cloudflare scheduling limit. The account is on the free plan, and KV allows 1,000 writes per day account-wide, resetting at 00:00 UTC. Each sync run writes the lease, the snapshot, and the Follow Up Boss activity and dial checkpoints (~4 writes), so `*/10` spends roughly 650 writes per day and leaves headroom for source-cache refreshes, ingest deliveries, and manual syncs. Tightening the schedule past `*/5` without Workers Paid exhausts the quota mid-day and every subsequent KV write fails until midnight UTC (see the 2026-08-20 incident in the troubleshooting runbook). The schedule lives in `wrangler.jsonc`, so `npx wrangler deploy` always reasserts it; never change the cadence only in the Cloudflare dashboard.

Each synchronization runs five integrations concurrently: Follow Up Boss personal activity, the Follow Up Boss Deals Leaderboard, Google Ads, Google Search Console, and the KV-backed Active Realty repository publication. It merges successful results with the previous snapshot and writes `dashboard:snapshot:v2` to Workers KV. A failed metric retains its last valid value and becomes stale. A first-run failure is unavailable, never a false zero. The prior Google Sheets reader remains in the Worker as dormant rollback code, but normal synchronization does not call it.

The desktop splash contains two black-card rows and ends exactly at the viewport fold:

1. Top row: Google Ads spend, leads, cost per click, and cost per lead, all month to date across all linked leaf accounts
2. Second row: fresh seller leads, fresh buyer leads, the authenticated user's outbound dials year to date, and that user's credited closed deals year to date

A third black row starts after the desktop fold so it appears only on scroll. It preserves calls made today, appointments set month to date, texts sent today, and emails sent today. Mobile keeps the same semantic order in a single-column flow without a forced viewport-height spacer.

Below it are five fixed rows, each capped at four metrics:

1. Year-to-date Google Ads spend, primary conversions, cost per conversion, and blended gross-commission ROAS across all linked leaf accounts
2. Search Console past-three-month clicks, impressions, CTR, and average position for `activerealty.com`, matching the Performance overview
3. The same four Search Console metrics for `justintye.com`
4. Year-to-date Follow Up Boss Deals Leaderboard gross commission, closed sales, volume, and active agents
5. Active Realty repository shell pages remaining and work sets remaining

The Active Realty view contains 22 company metrics. Its first row is month-to-date Google Ads spend, primary conversions, cost per click, and cost per conversion across all linked leaf accounts. Directly below it are both Search Console rows, followed by the year-to-date Ads row, the team row, and the two production values. Production Queue is enlarged and is always the final visible section.

The page polls the saved summary every 15 seconds while visible. The public response has a 10-second cache policy. External APIs are still contacted only by the ten-minute schedule or the protected manual sync endpoint. Personal and Ads metrics become stale after 25 minutes (two missed runs), team metrics after 75 minutes, Active Realty repository progress after 12 hours, and Search Console metrics after 26 hours. Staleness is a Worker-side status only: neither page renders a STALE badge (removed 2026-08-22, see "Metric freshness display" below); the per-card source line carries the relative age instead. The Active Realty workflow publishes every six hours as a heartbeat. Search Console is source-cached for 60 minutes because its reporting data is not real time. Team deal aggregates are source-cached for 30 minutes.

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

Create a dedicated API key in Follow Up Boss for the user whose personal activity should appear on the dashboard. The key's `/me` identity defines "I" for calls, texts, emails, appointments, year-to-date dials, and credited year-to-date closings.

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
- Total dials are the same outbound-call definition accumulated from Los Angeles midnight on January 1 through the current synchronization.
- Texts are manual outbound text records for that user. Incoming and action-plan messages are excluded.
- Emails are sent manual email records for that user. Drafts, other users, action plans, and campaigns are excluded.
- Appointments are records created during the current local month whose `createdById` matches the API-key user. The assignee does not change who set the appointment.
- Today, month, and year boundaries use `REPORTING_TIME_ZONE`, currently `America/Los_Angeles`.

Follow Up Boss does not permit this non-owner key to use the account-level agent-activity report or webhooks. The Worker therefore uses the documented REST resources directly. Collection scans prefer Follow Up Boss keyset `next` cursors and retain guarded offset pagination only for endpoints that omit a cursor. This is required for annual call histories beyond the API's deep-offset boundary. Call, text, and email IDs are hashed before deduplication state is stored in KV. No message content, person name, email address, phone number, or contact record is persisted. Daily message activity fully reconciles at least hourly. The year-to-date dial counter fully reconciles every six hours and uses 15-minute-overlap incremental scans between reconciliations. Full dial reconciliations are resumable and process at most eight call pages per cron invocation, safely below Cloudflare's per-invocation external-subrequest ceiling after the other dashboard sources are included. KV temporarily retains the opaque FUB page cursor, a candidate running count, and hashed call IDs only from the 15-minute overlap edge. A candidate count is promoted atomically only after the fixed year-to-date window is complete, so the dashboard never displays a partial annual total. This keeps the annual count correct without rescanning the whole year on every invocation.

The year-to-date team row uses the same all-pipeline, Everyone view as:

```text
https://activerealty.followupboss.com/2/reporting/leaderboard/deals
```

The Worker requests the report's aggregate endpoint with `FUB_API_KEY`, using `FUB_ACCOUNT_HOST=activerealty.followupboss.com`. It reads the report-level totals directly. It never sums the per-agent rows because one deal can credit several users and that would double-count volume, commission, and sales. The four company outputs are:

- Gross commission: `totals.closedCommissionTotal`
- Sales: `totals.closedDealCount`
- Volume: `totals.closedPriceTotal`
- Active agents: positive per-user closed counts, excluding lenders and names in `FUB_TEAM_EXCLUDED_USER_NAMES`

The personal dashboard also reads the authenticated user's own `closedDealCount` from the same leaderboard response. The user ID comes from `FUB_API_KEY` through `/v1/me`. This avoids mistaking the company total for Joshua's individual result. The Active Realty serializer excludes this personal metric.

The default excluded service-account name is `Active Agents`. Change the comma-separated non-secret variable if the FUB user directory changes. Names are used only in memory for exclusion and are never stored in KV or exposed publicly.

The Deals Leaderboard endpoint is part of the FUB web application and is not in FUB's public API reference. To reduce that maintenance risk, the Worker also has an official `/v1/deals` fallback. The fallback is enabled only when a separate Owner or Admin key is stored in `FUB_TEAM_API_KEY`; it verifies that `/v1/me` returns the `Broker` role before scanning deals. Add that optional resilience credential with:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret put FUB_TEAM_API_KEY
Set-Location ../..
```

The fallback uses `FUB_CLOSED_DEAL_STAGE_NAMES`, which defaults to `Closed`, and sums `commissionValue` so its definition matches the leaderboard's gross commission. It is not used while the leaderboard endpoint is healthy. If both sources fail, previous valid team values become stale instead of silently shrinking to the current user's visible deals.

Team aggregates and the authenticated user's credited closing count are cached for 30 minutes to avoid hammering the report endpoint and to keep the cache rewrite inside the KV write budget. Change the cache interval with `FUB_TEAM_REFRESH_MINUTES`. The cache key includes the YTD date range, account host, and exclusion list, while the cache payload records the resolved personal user ID, so a year rollover or configuration change cannot reuse the wrong aggregate.

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

At runtime the Worker recursively discovers all accessible, non-hidden, non-test leaf accounts beneath the manager. It caches only the leaf account IDs for ten minutes. New linked accounts are picked up automatically. If any child query fails, no Ads metric publishes a partial total. The prior complete totals remain visible as stale.

One OAuth access token is reused for the complete synchronization. Each leaf account receives one daily GAQL query covering the complete current calendar year:

```sql
SELECT
  segments.date,
  metrics.cost_micros,
  metrics.conversions,
  metrics.clicks
FROM customer
WHERE segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
```

The Worker derives month-to-date and year-to-date totals from those non-overlapping daily rows. Spend is the exact sum of `cost_micros` divided by 1,000,000. Conversions are the sum of the Google Ads `Conversions` column, represented by `metrics.conversions`, across all linked leaf accounts. The Active Realty CPC is MTD spend divided by MTD clicks. Its CPL is MTD spend divided by MTD primary conversions. The aggregate cost per conversion is YTD spend divided by YTD primary conversions. This intentionally includes every primary conversion in account performance and no longer filters to one action name or one child account. It does not use `metrics.all_conversions`, which can include local actions and other secondary engagement events. A zero click or conversion denominator makes only the applicable rate unavailable rather than publishing zero or Infinity.

Blended ROAS uses matching calendar-year periods:

```text
FUB Deals Leaderboard YTD gross commission / Google Ads YTD spend
```

It is a business-level blended ratio, not campaign-attributed incremental ROAS. It includes closed commission from every FUB source, including organic, repeat, and referral business. A zero or unavailable Ads denominator produces an unavailable metric, never Infinity or zero.

The configured API version is `v25`. Review Google Ads API sunset notices before that version is retired and update only `GOOGLE_ADS_API_VERSION` after tests pass.

### Seller campaign block (JT + AR "Sell | OC")

`/dashboard` carries a second dark row directly under the Google Ads row: **SELLERS SPEND / CPC / CTR / CPL**. It is the combined performance of the two seller search campaigns, `JT | Sell | OC | Search` (justintye.com/sell) and `AR | Sell | OC | Search` (activerealty.com/sell), which are one lander on two domains, so they are reported as one campaign. The window is **since launch** (`GOOGLE_ADS_SELLER_CAMPAIGN_LAUNCH_DATE`, default `2026-08-17`, a non-secret var in `wrangler.jsonc`) through today; the snapshot exposes it as `sellerCampaignPeriod` and the cards print "Since Aug 17". `/active` does not receive these four metrics (they are omitted from `ACTIVE_METRIC_KEYS`).

Each leaf account gets one extra GAQL query per sync alongside the account query:

```sql
SELECT
  campaign.id,
  campaign.name,
  segments.date,
  metrics.cost_micros,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions
FROM campaign
WHERE segments.date BETWEEN '<launch>' AND '<today>'
  AND campaign.status != 'REMOVED'
```

Campaign selection (`isSellerCampaignName` in `src/sources/google-ads.ts`): with `GOOGLE_ADS_SELLER_CAMPAIGN_NAMES` set (comma-separated exact names, compared case- and whitespace-insensitively segment by segment) only those names count. Unset, the built-in rule accepts any `|`-delimited campaign name that carries a `JT` or `AR` segment, an `OC` segment, and a segment starting with `sell` (so `JT | Sell | OC | Search`, `AR | OC | Sellers`, and a future `AR | Sell | OC | Display` all qualify; `AR | Buy | OC | Search`, `JT Call Ads`, and `DSA General Site` do not). Spend is the exact `cost_micros` sum; CPC = spend / clicks; CTR = clicks / impressions; CPL = spend / primary `metrics.conversions`. Every ratio fails closed on a zero denominator.

Failure posture is isolated from the all-account row: a rejected campaign query in any child makes only the four seller metrics unavailable (the previous values stay visible as stale), while a rejected account query still fails the whole Google Ads row as before. A sweep that matches no campaign publishes `no_data` (the cards show a dash), never a false `$0.00`, and before launch day the sweep is skipped entirely. Every sync logs `{"source":"google_ads_seller_campaigns","matchedCampaigns":[...]}` so a rename that breaks the match is visible in the Worker logs without exposing anything publicly (campaign names never enter KV or the public payload).

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

## 5. Google Search Console setup

The Search Console integration uses a separate OAuth refresh token with only the `webmasters.readonly` scope. Search Console's Performance overview defaults to the past three months, which is not the same as a strict 90-day window ending today. The Worker first queries recent finalized data grouped by date, detects the latest finalized date shared by both properties, then builds the same inclusive past-three-month range used by the UI. For example, an end date of August 12 produces May 13 through August 12. It then requests one property-level aggregate row containing clicks, impressions, CTR, and average position. The browser receives only those four numeric aggregates and the sanitized reporting dates.

Production properties:

- Active Realty: `sc-domain:activerealty.com`
- JT: `https://justintye.com/`

The OAuth user must have read access to both exact Search Console properties. Domain and URL-prefix properties are different resources, so preserve the strings exactly.

Enable the API in the Google Cloud project that owns the OAuth client:

```powershell
gcloud auth login
gcloud services enable searchconsole.googleapis.com --project=<google-cloud-project-id>
```

Create or reuse a Desktop OAuth client, then generate the read-only refresh token locally. The helper uses PKCE, opens the consent screen, and writes credentials only to the gitignored `scripts/.google_search_console.json` file:

```powershell
$env:GOOGLE_OAUTH_CLIENT_ID = Read-Host "OAuth client ID"
$env:GOOGLE_OAUTH_CLIENT_SECRET = Read-Host "OAuth client secret"
python scripts/google_search_console_auth.py
Remove-Item Env:GOOGLE_OAUTH_CLIENT_ID, Env:GOOGLE_OAUTH_CLIENT_SECRET
```

Install the three resulting values as Worker secrets without printing them:

```powershell
$gsc = Get-Content -Raw scripts/.google_search_console.json | ConvertFrom-Json
Set-Location cloudflare/dashboard-worker
$gsc.client_id | npx wrangler secret put GOOGLE_SEARCH_CONSOLE_CLIENT_ID
$gsc.client_secret | npx wrangler secret put GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET
$gsc.refresh_token | npx wrangler secret put GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN
Set-Location ../..
Remove-Variable gsc
```

The two property URLs and the 60-minute source refresh are non-secret variables in `wrangler.jsonc`. The ten-minute Worker schedule can safely reuse the sanitized KV aggregate between upstream refreshes. The availability probe uses `dataState: final` so partial same-day rows do not shift the window ahead of the Search Console card. The property aggregate uses `dataState: all` within that finalized end date and refreshes the complete three-month window instead of incrementally adding daily values. The dashboard prints the exact start and end dates beneath the Organic Search heading so the comparison window is auditable.

## 6. Active Realty shell-progress bridge

The final dashboard row is published by the `iDroza/activerealty-com` main-branch workflow. The publisher sends one authenticated heartbeat every six hours to:

```text
POST https://drozq.com/api/dashboard/admin/shell-progress
```

The receiver requires `Authorization: Bearer <token>`, accepts at most 4 KiB, applies `Cache-Control: no-store` to every response, and does not enable CORS. The JSON body must contain exactly these fields:

```json
{
  "schemaVersion": 1,
  "sourceRepo": "iDroza/activerealty-com",
  "sourceRef": "refs/heads/main",
  "sourceSha": "0123456789abcdef0123456789abcdef01234567",
  "runId": "1234567890",
  "publishedAt": "2026-08-15T12:00:00.000Z",
  "shellPagesRemaining": 37,
  "setsRemaining": 4
}
```

The SHA must be 40 lowercase hexadecimal characters. The run ID must be a positive decimal string and is compared by decimal-string length and lexical order, never by JavaScript `Number`. Timestamps must be valid RFC3339 UTC values and are normalized to canonical millisecond UTC form. Both counts must be nonnegative safe integers. Missing fields, extra fields, wrong repository identity, malformed values, and oversized bodies fail before KV is written.

The receiver stores only the validated record at `dashboard:active-realty-progress:v1`. A retry with the same run ID and identical record succeeds with `idempotent: true`. The same run ID with different content and any lower run ID return `409` without replacing the record. The publisher workflow is the primary single writer, while the receiver check is defense in depth.

The ten-minute dashboard synchronization reads that KV record, revalidates it, and emits only `shellPagesRemaining`, `setsRemaining`, and the publication time into the existing metric merge. Missing or corrupt progress data is an error, never zero. Existing valid snapshot values remain visible as stale. Ingest metadata, repository fields, run IDs, and SHAs never enter either public dashboard response.

Generate one 256-bit token and install the same value through stdin in both systems. Do not print it or save it to either repository:

```powershell
$progressTokenBytes = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($progressTokenBytes)
$progressToken = [Convert]::ToBase64String($progressTokenBytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
try {
  Push-Location cloudflare/dashboard-worker
  $progressToken | npx wrangler secret put ACTIVE_REALTY_PROGRESS_TOKEN
  Pop-Location
  $progressToken | gh secret set DROZQ_SHELL_PROGRESS_TOKEN --repo iDroza/activerealty-com
} finally {
  if ((Get-Location).Path -like '*cloudflare\\dashboard-worker') { Pop-Location }
  [Array]::Clear($progressTokenBytes, 0, $progressTokenBytes.Length)
  Remove-Variable progressTokenBytes, progressToken -ErrorAction SilentlyContinue
}
```

Confirm only the secret names with `npx wrangler secret list` and `gh secret list --repo iDroza/activerealty-com`. Never send a valid payload by hand and never seed the progress KV key. The first valid production record must come from the Active Realty GitHub workflow.

### Dormant Google Sheets rollback

The prior read-only Google Sheets consumer, configuration, credentials, and tests remain intact but are not called by normal synchronization. Reverting the receiver cutover restores these inputs:

- Shell Pages Remaining, read from the direct cell configured by `GOOGLE_SHEETS_REMAINING_RANGE`, or calculated from the optional page table mode
- Sets Remaining, read from the direct cell configured by `GOOGLE_SHEETS_SETS_REMAINING_RANGE`

The retained native tracker Sheet uses these ranges:

- Shell pages: `Summary!B5`
- Work sets: `Summary!B8`

The second cell is the tracker's `Work sets left (10/set)` output, so the dashboard labels it as 10 pages per set. Both values must be nonnegative whole numbers. A blank, negative, fractional, non-finite, or malformed value fails only that metric and preserves its prior valid value.

Enable the Sheets API in the Google Cloud project that owns the service account:

```powershell
gcloud auth login
gcloud services enable sheets.googleapis.com --project=<google-cloud-project-id>
```

For a new environment, create a dedicated service account and key. Download the key only long enough to install its email and private key as Worker secrets:

```powershell
gcloud iam service-accounts create drozq-dashboard-sheets --project=<google-cloud-project-id> --display-name="Drozq Dashboard Sheets"
gcloud iam service-accounts keys create .dashboard-sheets-key.json --iam-account=drozq-dashboard-sheets@<google-cloud-project-id>.iam.gserviceaccount.com --project=<google-cloud-project-id>
```

Share only the tracker Sheet with the service-account email as Viewer. Do not grant Editor access and do not make the Sheet public.

Install the production secrets without printing their values:

```powershell
$sheetKey = Get-Content -Raw .dashboard-sheets-key.json | ConvertFrom-Json
Set-Location cloudflare/dashboard-worker
$sheetKey.client_email | npx wrangler secret put GOOGLE_SERVICE_ACCOUNT_EMAIL
$sheetKey.private_key | npx wrangler secret put GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY
npx wrangler secret put GOOGLE_SHEETS_SPREADSHEET_ID
'Summary!B5' | npx wrangler secret put GOOGLE_SHEETS_REMAINING_RANGE
'Summary!B8' | npx wrangler secret put GOOGLE_SHEETS_SETS_REMAINING_RANGE
Set-Location ../..
Remove-Variable sheetKey
Remove-Item -LiteralPath .dashboard-sheets-key.json -Force
```

Paste only the raw spreadsheet ID into the hidden `GOOGLE_SHEETS_SPREADSHEET_ID` prompt. Never paste a full private Sheet URL into source code.

### Optional shell-page table mode

Instead of a direct shell count, the Worker can calculate it from a bounded range containing `Page` and `Status` headers. Delete only the shell direct-cell range, then configure the table range:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler secret delete GOOGLE_SHEETS_REMAINING_RANGE
npx wrangler secret put GOOGLE_SHEETS_PAGES_RANGE
Set-Location ../..
```

Default completed values are `complete,completed,done,published,live`. Header names and complete values can be changed with `GOOGLE_SHEETS_PAGE_HEADER`, `GOOGLE_SHEETS_STATUS_HEADER`, and `GOOGLE_SHEETS_COMPLETE_VALUES`. Matching ignores capitalization and surrounding whitespace. Fully blank rows and rows without a page value are ignored. Sets Remaining remains direct-cell only.

The Worker normalizes escaped newlines before Web Crypto signs the service-account JWT. One OAuth access token and one Sheets `values:batchGet` request serve both metrics per synchronization. Sheet cells and rows are never stored or returned. Only the two validated counts enter the sanitized KV snapshot.

## 7. Workers KV

The production namespace is already bound as `DASHBOARD_KV` in `wrangler.jsonc`. To provision a separate environment:

```powershell
Set-Location cloudflare/dashboard-worker
npx wrangler kv namespace create DASHBOARD_KV
Set-Location ../..
```

Put the returned namespace ID into the `DASHBOARD_KV` binding. Do not rename these stable keys:

- `dashboard:snapshot:v2`: sanitized public snapshot
- `dashboard:active-realty-progress:v1`: the exact validated repository progress record and no other publisher data
- `dashboard:fub:activity:v2`: counts, checkpoints, and hashed daily message IDs only
- `dashboard:fub:dials:v2`: the current year, stable checkpoints and count, hashed outbound-call IDs, and resumable reconciliation cursor state
- `dashboard:fub:team:v4`: five-minute sanitized team totals, resolved personal user ID, and personal closed-deal count only
- `dashboard:google_ads:accounts:v2`: short-lived leaf account ID cache
- `dashboard:search_console:aggregate:v1`: hourly sanitized property aggregates only
- `dashboard:sync:lease:v2`: short-lived best-effort overlap guard

KV never stores API keys, bearer tokens, OAuth access tokens, refresh tokens, private keys, raw request bodies, request headers, page content, assignment data, message bodies, or contact details.

## 8. Manual synchronization token

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

## 9. Local development

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

## 10. Production deployment

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
curl.exe -I https://drozq.com/active
curl.exe -I https://drozq.com/Active
curl.exe -i https://drozq.com/api/dashboard/health
curl.exe -i https://drozq.com/api/dashboard/summary
curl.exe -i https://drozq.com/api/dashboard/active-summary
curl.exe -i https://drozq.com/api/dashboard/active-bootstrap.js
curl.exe -i -X POST https://drozq.com/api/dashboard/admin/shell-progress
curl.exe -i https://drozq.com/api/dashboard/not-a-route
curl.exe -i https://drozq.com/api/geo
```

Both pages return `200`; uppercase page paths return `301` to their lowercase canonical paths. Health returns `200`. Summary endpoints return `200` or a first-run `503`, the JavaScript bootstrap returns `200`, the unauthenticated shell-progress POST returns `401` with `Cache-Control: no-store`, unknown dashboard routes return `404`, and the existing geo endpoint keeps its normal response. JSON summaries must include JSON content type, `nosniff`, and the documented 10-second cache policy without wildcard CORS. The Active Realty responses must contain exactly the 22 documented company metrics and none of the eight personal metric keys or any shell-progress ingest metadata.

## 11. Protected manual synchronization

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

## 12. Troubleshooting and durability runbook

### Follow Up Boss `401` or `403`

- Confirm the personal key still exists and belongs to the intended user.
- Update `FUB_API_KEY` after any key rotation.
- Confirm the key user can access people, calls, appointments, text messages, emails, and `/me`.
- Confirm the key user can open the Deals Leaderboard with All Pipelines, Everyone, and This Year selected.
- Confirm `FUB_ACCOUNT_HOST` is the account's exact `*.followupboss.com` host.
- If using the optional fallback, confirm `FUB_TEAM_API_KEY` belongs to an Owner or Admin and `/v1/me` returns the `Broker` role.
- Account-level activity reports and webhooks require owner privileges and are not used for personal metrics.

### Google Ads `401` or `403`

- Confirm client ID, client secret, and refresh token belong together.
- Reauthorize with offline access if Google returns `invalid_grant`. If Ads and Search Console fail together seven days after a mint, see the `invalid_grant` runbook entry below: the OAuth consent screen is in Testing.
- Confirm the OAuth user still has access to the configured manager and children.
- Confirm the developer token remains approved for the account hierarchy.
- Confirm the login manager ID contains ten digits and no hyphens.

### Google OAuth `400 invalid_grant` on both Ads and Search Console (7-day refresh tokens)

Symptom: `google_ads_oauth` and `google_search_console_oauth` both log `status: 400, category: upstream` on every sync, every Google card goes stale at the same minute, and `lastSuccessfulFullSyncAt` stops advancing. This happened on 2026-08-21, exactly seven days after the 2026-08-14 token mint.

Cause: both refresh tokens come from the same Desktop OAuth client (`scripts/.google_ads.json` + `scripts/.google_search_console.json`, project `220779520969`). While that project's OAuth consent screen has publishing status **Testing**, Google expires every refresh token after seven days by policy. `scripts/ads.py` (the drozq Google Ads pulls) dies at the same moment because it shares the token.

Fix, in this order (re-minting alone only buys another seven days):

1. Google Cloud Console > APIs & Services > OAuth consent screen (Google Auth Platform > Audience) for the project that owns the client > **Publish app** so the status reads **In production**. Verification is not required for the tokens to stop expiring; the consent screen simply shows the unverified-app interstitial to the authorizing user.
2. Re-mint both tokens locally (each opens a consent screen in the browser, writes only the gitignored JSON file, prints nothing secret): `python scripts/google_ads_auth.py` and `python scripts/google_search_console_auth.py`.
3. Install them without printing them:

```powershell
$ads = Get-Content -Raw scripts/.google_ads.json | ConvertFrom-Json
$gsc = Get-Content -Raw scripts/.google_search_console.json | ConvertFrom-Json
Set-Location cloudflare/dashboard-worker
$ads.refresh_token | npx wrangler secret put GOOGLE_ADS_REFRESH_TOKEN
$gsc.refresh_token | npx wrangler secret put GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN
Set-Location ../..
Remove-Variable ads, gsc
```

4. Wait for the next ten-minute cron (or run the authorized manual sync) and confirm the Google cards' age lines reset.

### `429` or transient `5xx`

Upstream requests retry no more than three times, respect `Retry-After`, and otherwise use bounded exponential backoff with jitter. Persistent failure retains the last complete value as stale. Do not shorten the ten-minute Cron on the free plan: the constraint is the KV 1,000-writes-per-day budget (see the architecture section and the 503 runbook entry below), and higher manual frequency can also cause upstream rate limits.

### Google Ads spend or leads look low

- Check that every advertising account is linked beneath the configured manager.
- Wait ten minutes for the hierarchy cache, or run a manual sync after deleting `dashboard:google_ads:accounts:v2` from KV.
- Compare the Google Ads UI with the same reporting timezone and the `Conversions` column, not `All conversions`.
- Inspect Worker logs for a child-account error. The Worker refuses partial totals.

### Search Console `401`, `403`, or missing metrics

- Confirm `searchconsole.googleapis.com` is enabled in the OAuth client's Google Cloud project.
- Confirm the refresh token was authorized with `webmasters.readonly` and has not been revoked.
- Confirm the OAuth user can open both exact configured properties in Search Console.
- Keep `sc-domain:activerealty.com` and `https://justintye.com/` exact. A domain property and a URL-prefix property are not interchangeable.
- Search Console metrics legitimately trail live traffic. Their saved values become stale only after 26 hours.

### Shell-progress POST or sync returns `503 storage_unavailable` (KV write quota)

A `503` from the authenticated shell-progress receiver while unauthenticated requests still return a fast `401` means the handler itself failed after auth, and the most likely cause is that `DASHBOARD_KV.put` is throwing. Since the logging fix of 2026-08-20 the rejection log line (`source: active_realty_progress_ingest`, `category: storage_write`) carries a `detail` field with the real exception text; read it in Workers Observability before assuming anything.

`KV PUT failed ... limit exceeded` / error code `10048` means the account's Workers KV free-tier write quota (1,000 writes per day, account-wide, resets 00:00 UTC) is exhausted. Reads keep working, so auth, `GET` endpoints, and idempotent replays still succeed while every fresh write fails until midnight UTC.

**Incident record, 2026-08-20.** The `iDroza/activerealty-com` "Publish shell progress to Drozq" workflow delivered successfully at 07:09 UTC and failed with `503` on every run from 13:13 UTC onward. No deploy, config, or code change was involved: the worker (then on a `*/2` schedule) was writing lease + snapshot + Follow Up Boss activity + dial checkpoints on every run, roughly 2,400 to 2,900 KV writes per day against the 1,000-per-day free cap, exhausting the quota around 11:00 UTC daily. Prior days had exceeded the cap without enforcement (an account-level Workers Paid entitlement had covered it); once the account was purely free-tier the cap became real and every afternoon delivery died. The receiver's bare `catch` collapsed the quota error into an anonymous `503`, which is why the failure looked like a mystery. Fix: cron `*/2` to `*/10`, `FUB_TEAM_REFRESH_MINUTES` 5 to 30, staleness thresholds raised to match (fast 25 min, team 75 min), and every storage `catch` now logs the underlying exception in `detail`. Alternative if faster refresh is ever needed again: Workers Paid ($5/month) removes the daily write cap, after which `*/2` and the five-minute policies can return.

### Active Realty progress is stale or missing

- Confirm `ACTIVE_REALTY_PROGRESS_TOKEN` exists on `drozq-operating-dashboard` and `DROZQ_SHELL_PROGRESS_TOKEN` exists in `iDroza/activerealty-com`. Compare names only, never values.
- Confirm the Active Realty publication workflow is enabled on `main` and its most recent scheduled or push run completed.
- Confirm the workflow sends `sourceRepo=iDroza/activerealty-com`, `sourceRef=refs/heads/main`, the lowercase 40-character commit SHA, the decimal GitHub run ID, and an RFC3339 UTC publication time.
- A `401` means the publisher and receiver secrets do not match or one is missing. Rotate both together with one new 256-bit value.
- A `400` means the payload failed schema validation. Inspect the receiver's secret-free rejection category and the publisher's generated JSON keys and types.
- A `409` means a duplicate run ID changed content or an older workflow tried to replace a newer publication. The stored record remains untouched.
- A `413` means the publisher sent more than 4 KiB. The bridge must contain only the eight documented fields.
- Missing or corrupt KV preserves the last valid dashboard values as stale. It never publishes zero as a fallback.

### Dormant Google Sheets rollback diagnostics

If the cutover commit is reverted, confirm the Sheets API, Viewer share, service-account key pair, raw spreadsheet ID, and the two `Summary` ranges remain valid. The retained reader still rejects blank, negative, fractional, non-finite, or malformed values without replacing the prior snapshot.

### Follow Up Boss activity looks low

- Verify the API key belongs to the intended agent.
- Confirm records are being saved to Follow Up Boss under that user's ID.
- Compare total dials against outbound call records only. Incoming calls do not count.
- Automated action-plan and campaign messages are intentionally excluded.
- Run a protected sync. The hourly message reconciliation and six-hour year-to-date dial reconciliation correct late-arriving or edited records. A full annual dial scan may need several cron invocations; its prior complete value stays stale until the candidate scan is atomically promoted.

### Follow Up Boss team totals look low

- Open `/2/reporting/leaderboard/deals`, select All Pipelines, Everyone, and This Year, then compare its report-level totals. Do not add the agent rows because credited users overlap.
- Confirm the selected report shows the current year and the account's pipelines are marked closed correctly.
- Gross commission, closed sales, and volume should match the report-level totals, not the current user's regular Deals list.
- Active agents count positive leaderboard users after excluding lenders and `FUB_TEAM_EXCLUDED_USER_NAMES`. Keep the service-account exclusion list current.
- Compare Joshua's personal closed-deal card with his own leaderboard row, not the 56-deal report total. `/v1/me` from `FUB_API_KEY` chooses that row.
- If the web report endpoint changes, configure `FUB_TEAM_API_KEY` with an Owner or Admin key so the documented Deals API fallback can take over.
- The fallback alone uses `FUB_CLOSED_DEAL_STAGE_NAMES`; add renamed or alternate closed stages there.
- If the brokerage transaction ledger is not maintained in FUB, do not configure this source. Move the team metrics to an authoritative ledger integration instead of publishing partial CRM data.

### Stale or missing metrics

The Worker marks a metric stale after 25 minutes for personal and Ads values, 75 minutes for team values, 12 hours for Active Realty repository progress, and 26 hours for Search Console. Check structured Worker logs for source, HTTP status, duration, and sanitized error category. A missing metric with no prior value is shown as unavailable, not zero. A partial failure does not erase other sources.

### Metric freshness display

Neither `/dashboard` nor `/active` renders a STALE badge. Both pages show freshness as the relative age on each card's source line ("Google Ads - updated 12m ago"), which is the honest read and never contradicts the sync row.

The badge was removed on 2026-08-22. It had a second, duplicated staleness rule living client-side in `dashboard/dashboard.js` and `active/active.js` (`STALE_AFTER_MS` / `ADS_STALE_AFTER_MS` at five minutes, plus per-metric `staleAfterMs` overrides). When the 2026-08-20 KV write-quota incident moved the cron from `*/2` to `*/10` and raised the Worker thresholds to 25 / 75 minutes, that client copy was never raised, so every fast metric badged STALE for most of each ten-minute cycle even though the data was current and the age line said so. Both client copies of the thresholds are deleted; `MetricStatus` still carries `"stale"` end to end (`src/types.ts`, `snapshot.ts`, `sync.ts`) and both clients still accept it in the payload validator, so the API contract and the failed-source retention behavior are unchanged.

If a visible freshness signal is ever wanted again, drive it from `metric.status` alone (one rule, Worker-side) rather than reintroducing a client-side clock.

### 30 to 180 day maintenance risks

- Google refresh tokens can be revoked by password, consent, or security changes. Monitor `authentication` errors. A consent screen left in Testing status expires every refresh token after seven days (the 2026-08-21 outage); keep it published.
- The seller campaign block depends on campaign names matching the JT / AR + OC + Sell* segment rule (or `GOOGLE_ADS_SELLER_CAMPAIGN_NAMES`). A rename shows up as `matchedCampaigns: []` in the logs and a dash on the cards.
- Search Console property permissions or canonical property changes can revoke one site's data while the other remains healthy.
- Search Console data availability can move by hours and recent values can remain preliminary. The Worker discovers the latest finalized date on every source refresh and re-queries the full Performance window, so it follows revisions without date-lag configuration.
- Google Ads API versions are sunset periodically. Review the version before `v25` retirement.
- The FUB Deals Leaderboard endpoint is an internal web-app endpoint. Its response schema is validated, failures preserve old values, and an optional role-checked broker-key fallback uses documented endpoints.
- FUB can rename the account host or service-account users. Both are configuration-only changes through `FUB_ACCOUNT_HOST` and `FUB_TEAM_EXCLUDED_USER_NAMES`.
- Follow Up Boss fallback deal-stage renames and commission-field omissions fail closed instead of publishing an understated team total.
- New Google Ads leaf accounts are automatic, but OAuth and developer-token access must cover them.
- Changing Google Ads primary conversion settings changes the Leads number by design. Audit primary actions during tracking migrations.
- CPC and CPL intentionally fail closed when clicks or primary conversions are zero, so a missing denominator never appears as a misleading `$0.00`.
- The Active Realty publisher token can be deleted or rotated on only one side. Monitor `authentication` rejections and always rotate both secret names together.
- A disabled workflow, changed repository/ref identity, malformed SHA, timestamp, run ID, or count fails closed and keeps the last valid progress values.
- The dormant Google Sheets service-account key and Viewer access should remain available for rollback. Do not delete or rotate those credentials as part of the repository cutover.
- Worker Cron configuration changes can take time to propagate. Manual sync verifies deployment immediately.
- Upstream schema drift fails closed and preserves last-known-good values. Keep tests and observability enabled.
- The daily activity state resets at Los Angeles midnight, the dial state resets on January 1, and the date utility has rollover, leap-year, and DST coverage.

Review Worker errors and credential age monthly. Run `npm run dashboard:check` before any API-version or schema update.

## 13. Security and rotation

Never commit `.dev.vars`, `.env`, downloaded service-account JSON, API keys, OAuth tokens, private keys, Cloudflare API tokens, `ADMIN_SYNC_TOKEN`, or `ACTIVE_REALTY_PROGRESS_TOKEN`. The public serializer uses an explicit allowlist and cannot return contact details, account names, campaign names, Sheet contents, shell-progress ingest metadata, credentials, or raw upstream errors.

Any credential pasted into chat, committed, logged, or shown in a screenshot must be treated as exposed and rotated. Removing it from a file or deleting a message does not revoke it.

The marketing funnel uses a browser-side Google Maps key for Places autocomplete, including in `faq/index.html`. Browser keys are public by design, but the Google Cloud key must be restricted to only the necessary Maps APIs and exact production HTTP referrers. Rotate any version that was ever unrestricted. Do not remove it without a replacement because that would break funnel address validation.

## 14. GitHub Actions

`.github/workflows/dashboard-worker.yml` runs only when Worker-related files change. It tests, type checks, builds, and then deploys only the dashboard Worker on `main` when these repository secrets exist:

- `CLOUDFLARE_API_TOKEN`, limited to the required Worker script and route permissions
- `CLOUDFLARE_ACCOUNT_ID`

Runtime API credentials remain Worker secrets and are not managed by this repository's GitHub Actions. The workflow does not touch Cloudflare Pages deployment. The separate `iDroza/activerealty-com` publisher stores only its matching bearer value under the repository secret name `DROZQ_SHELL_PROGRESS_TOKEN`.

## 15. Rollback

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
- https://developers.google.com/webmaster-tools/v1/searchanalytics/query
- https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchGet
- https://developers.google.com/identity/protocols/oauth2/service-account
- https://docs.followupboss.com/reference/authentication
- https://docs.followupboss.com/reference/calls-get
- https://docs.followupboss.com/reference/deals-get
- https://docs.followupboss.com/docs/inbox-apps-installation-lifecycle
- https://docs.followupboss.com/reference/deals-post
