# Google Ads Scripts

JavaScript automations that run **inside Google Ads** (Tools & Settings -> Bulk actions -> Scripts), on Google's servers, on a schedule, with your account's own permissions. No server, no refresh token, no infrastructure to babysit.

> These are NOT `scripts/ads.py`. That's the **API** layer: read-only reporting you run locally on demand (refresh-token auth, see `notes/mcp-workarounds.md`). Google Ads **Scripts** are the **always-on automation** layer: they run unattended on a schedule and can *write* to the account (add negatives, adjust bids, label, email). Use both: `ads.py` to investigate, a Script to act every day.

## What's here

| File | What it does |
|---|---|
| `lead-gen-guardian.js` | Daily account guardian for the Sellers campaign: mines negative keywords from the search-terms report (real-estate junk dictionary), watches wasted spend + expensive clicks, guards the funnel (landing page 200 + funnel markup present, disapproved ads, conversion flatline), surfaces converting terms not yet promoted to keywords. Emails one digest. **Dry-run by default.** |

## Install (one time, ~3 minutes)

1. Google Ads -> **Tools & Settings** -> **Bulk actions** -> **Scripts** -> **( + )**.
2. Name it `Drozq Lead-Gen Guardian`. Paste the contents of `lead-gen-guardian.js`.
3. Click **Authorize** (grants the script your account's permissions + email/URL-fetch).
4. Click **Preview**. On a dry-run this writes nothing; it scans and logs the digest it *would* email. Read the log.
5. Click **Run** once to receive the email for real, then **Schedule -> Daily** (early AM, e.g. 6am PT, before you check the account).

## Configure

Everything is in the `CONFIG` block at the top of the file. The knobs that matter:

| Setting | Default | Notes |
|---|---|---|
| `EMAIL_TO` | `guerrerojoshua720@gmail.com` | Comma-separate for more recipients. The Google account that authorizes the script is the sender. |
| `AUTO_APPLY_NEGATIVES` | `false` | **Leave false until you trust it.** `true` = it adds high-confidence junk to the shared list automatically. |
| `NEG_LIST_NAME` | `Negatives \| Sellers Funnel` | Must match your existing shared negative-keyword list exactly. |
| `MAX_AUTO_NEGATIVES_PER_RUN` | `25` | Safety cap. It can never dump hundreds of negatives in one run. |
| `EXPENSIVE_CLICK_ALERT` | `40` | Avg CPC at/above this on any term is flagged (your $210 / $146 / $85 clicks). |
| `ZERO_CONV_SPEND_ALERT` | `50` | Non-junk term that spent this much with zero conversions -> review list. |
| `LANDING_PAGES` / `REQUIRED_PAGE_MARKERS` | `['https://drozq.com/']` / `['funnel-overlay']` | Funnel-break guard: 200 **and** the markup is still present. |

## Why it's built the way it is

- **Dry-run first.** It recommends before it touches anything. The default run is read-only.
- **Two confidence tiers.** Only *high-confidence* junk (jobs, FSBO, iBuyer, rentals, out-of-state, competitor/brokerage brands, research-tool AVMs) is eligible for auto-apply, as **phrase** negatives that kill variants. Medium-confidence buckets (buyers, mortgage, generic research) are recommend-only.
- **It respects the bidding log.** The `home value estimator` / `calculator` family is deliberately excluded from the junk dictionary, because per `notes/ads/bidding-decisions.md` the lone early conversion came from that family — the $15 CPC cap is the right tool there, not a negative. Those terms only ever appear on the zero-conversion review list, never auto-negated.
- **It won't negate your own keywords.** Active keyword texts are loaded and excluded from negation suggestions.
- **It de-dupes.** Terms already excluded (search-term status) and tokens already on the shared list are skipped.

## What else a Script could do here (ideas, not built)

- **Bid-cap sentinel:** alert/auto-pause if blended avg CPC drifts above the $15 portfolio cap intent.
- **Budget pacing:** email if month-to-date spend is tracking to over/under budget.
- **Dayparting report:** hour-of-day conversion heatmap to feed the §11 Phase-2 schedule bid adjustments.
- **Auction Insights watch:** flag new competitors so their brand terms get negated.

See `notes/ads/google-ads-scripts.md` for the companion write-up.
