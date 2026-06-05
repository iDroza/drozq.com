# Google Ads Scripts (the automation layer)

*Created 2026-06-05.*

Google Ads **Scripts** are JavaScript that runs *inside* Google Ads on Google's servers, on a schedule, with the authorizing user's account permissions. No local machine, no refresh token, no infrastructure. They can **read and write** the account (add negatives, adjust bids, label, pause, email, fetch URLs).

This is a different tool from `scripts/ads.py`:

| | `scripts/ads.py` (Google Ads **API**) | Google Ads **Scripts** |
|---|---|---|
| Runs | locally, on demand | in Google's cloud, on a schedule |
| Auth | stored OAuth refresh token (`notes/mcp-workarounds.md`) | one-click authorize inside the UI |
| Best for | ad-hoc investigation, decision pulls | unattended daily automation + alerts + writes |
| Can write? | yes, but we use it read-only | yes — this is the point |

Use them together: `ads.py` to investigate a question now; a Script to act on the same data every morning.

## Built: `scripts/google-ads-scripts/lead-gen-guardian.js`

A daily guardian for the `Search | Sellers | Max-Intent | Irvine+OC` campaign. Three jobs:

1. **Negative-keyword miner** — scans the search-terms report, classifies each term against a real-estate junk dictionary (jobs/license, FSBO/DIY, iBuyer/cash, rentals, out-of-state geo, competitor + brokerage brands, research-tool AVMs, distressed carve-out), recommends phrase negatives, and (only when `AUTO_APPLY_NEGATIVES = true`) adds the high-confidence ones to the `Negatives | Sellers Funnel` shared list. Automates the `sellers-max-intent-campaign.md` §11 daily ritual.
2. **Wasted-spend watch** — terms that spent over a threshold with zero conversions, and any term whose avg CPC breached the expensive-click line (the documented $210 / $146 / $85 clicks).
3. **Funnel + account guardian** — landing pages return 200 *and* still contain the funnel markup (silent-break alarm), no ENABLED ad is DISAPPROVED, and conversions haven't flatlined. Plus surfaces converting terms not yet promoted to keywords.

Emails one HTML digest. **Dry-run by default** (recommend-only; writes nothing).

### Project-specific correctness baked in

- Excludes the `home value estimator` / `calculator` family from the junk dictionary, per `bidding-decisions.md` (the early conversion came from there; the $15 cap handles it, not a negative).
- Never recommends negating one of the account's own active keywords.
- Skips search terms already excluded, and tokens already on the shared list.
- High-confidence vs medium-confidence tiers; only high-confidence is auto-apply-eligible, capped per run.

Install + config: see `scripts/google-ads-scripts/README.md`.

Companion docs: `sellers-max-intent-campaign.md` (§5 negatives, §11 plan), `bidding-decisions.md` (the $15 cap + terms not to negate), `notes/mcp-workarounds.md` (`ads.py`).
