# Bidding decisions log

Running log of Google Ads bid-strategy decisions for the Sellers campaign(s). Newest entry on top. Append a dated entry whenever the bid strategy, target, cap, or budget changes. Read before touching bidding so prior reasoning is not relitigated.

Companion docs: `sellers-max-intent-campaign.md` (the campaign build spec, see §11 Phase 1/2 plan and §12 budget reality check) and `distressed-sellers-strategy.md`.

Data is pulled with `python scripts/ads.py` (see `notes/mcp-workarounds.md`).

---

## 2026-06-13 — Valuation rebuild keeps the bid strategy UNCHANGED

### Decision

The Sellers campaign is being rebuilt to the new homepage (positioning flipped from "compare agents" to the **instant home valuation + 5 playbooks** lead magnet; see `sellers-valuation-rebuild-2026-06.md`). The **bid strategy does not change.** Keep the portfolio **Target CPA `Sellers Conversions + $15 cap`** (target $400, max CPC $15) and apply that same portfolio strategy to the new campaign(s). Max Clicks remains rejected (Joshua, "that strategy doesn't work"). The rebuild changes copy / keywords / landing-page match, not the economics decision from 2026-05-28.

### Why nothing changes on bidding

The 05-28 decision was about *controlling per-click cost while staying on conversion bidding* given thin conversion data. That situation still holds: the old window banked ~0,1 clean conversions, so we are still seeding. A new campaign with a new LP starts cold either way; the cap is still the right guardrail.

### What the rebuild SHOULD change (downstream)

- **CVR should rise well above the old ~2.86%.** The new homepage is a purpose-built instant-valuation lead magnet (address , value + 5 playbooks instantly), and message match is now tight (valuation query , "instant valuation" ad , valuation homepage). Higher CVR at the same ~$9,11 effective CPC means **lower CPL and faster conversion accumulation.**
- **Conversion signal is clean** since the 2026-05-29 GTM trigger fix (`generate_lead` fires on `lead_confirmed`, confirmed working). So tCPA can be trusted as data accumulates.
- **Reaching the exit criteria faster.** Per the 05-28 exit criteria, once ~15,30 conversions bank in a trailing 30 days, set a real data-driven Target CPA at ~1.2x the observed clean CPL and loosen/remove the $15 cap. The rebuild should get us there in weeks, not months.

### Watch items

1. Apply the **same portfolio strategy** to the new campaign(s) (portfolio strategies span campaigns) , do not create a fresh strategy and reset learning needlessly.
2. If CPL drops fast (likely), don't prematurely yank the cap; wait for the 15,30 conversion threshold, then graduate.
3. Geo widened to **all of Orange County** (county-level) per Joshua, vs the old city+ZIP list , watch that county-level reach doesn't pull lower-intent fringe; the search-terms report + negatives are the control, not the bid.

---

## 2026-05-28 — Cap CPC at $15 via portfolio Target CPA (stay on conversion bidding)

### Decision

Keep conversion-based bidding, but put a hard ceiling on per-click cost. Implemented as a **portfolio Target CPA** strategy with a **Maximum CPC bid limit of $15**. This is the only way to cap CPC without leaving conversion-optimized bidding: standard Maximize Conversions has no bid-limit field, and standard (campaign-level) Target CPA has no bid-limit field either. Bid limits exist only on Manual CPC, Maximize Clicks, and **portfolio** tCPA / tROAS strategies.

Maximize Clicks was explicitly rejected by Joshua ("that strategy doesn't work"). Pure Maximize Conversions cannot cap a click. So: portfolio tCPA + cap.

### Exact configuration

| Field | Value |
|---|---|
| Strategy type | Portfolio bid strategy, Target CPA |
| Name | `Sellers Conversions + $15 cap` |
| Target CPA | $400.00 |
| Maximum bid limit (max CPC) | $15.00 |
| Minimum bid limit | blank |
| Currency | USD |
| Applied to | the Sellers max-intent Search campaign (only) |

Tuning rule: the **$15 cap is the hard guardrail**; the target is the loose steering input. If weekly volume is too thin after the learning period, raise the **target** toward $500 to $600 to let the strategy enter more auctions. Never raise the cap to chase volume. At ~2.86% CVR a $400 target implies an average bid near $11, so the cap mostly binds on the high-intent auctions where tCPA wants to bid up; that is the intended behavior.

### The data that forced it (May 23 to 28, ~6 days, first real delivery)

Source: Search terms report + impressions time series, May 21 to 28, 2026.

| Metric | Value |
|---|---|
| Spend | $1,216 |
| Clicks | 35 |
| Avg CPC | $34.74 |
| Leads (conversions) | 1 |
| Cost per lead | $1,216 |
| Worst single clicks | $210.63 (`most accurate home value estimator`), $146.29 (`what is my home worth`), $85.76 (`flat fee realtor`) |
| Impressions/day | ~250 to 330 (implies ~$200/day budget; delivery began May 23) |

Two clicks ate ~30% of total spend. Avg CPC ran 2.5x to 4x the $8 to $14 this vertical should cost (per `sellers-max-intent-campaign.md` §12). On 1 conversion, conversion bidding had no signal and was overbidding individual auctions.

### Why not the alternatives

- **Standard Maximize Conversions:** no max-CPC field exists. Cannot cap a click. Hard product limit.
- **Standard / campaign-level Target CPA:** bid limits are not offered. Must be a *portfolio* strategy to get the cap.
- **Maximize Clicks + bid limit:** would cap, but rejected by Joshua and tends to buy cheap low-intent clicks.
- **Manual CPC:** caps per keyword but abandons conversion bidding and is high-maintenance for a solo operator.
- **Target CPA as the real fix (data-driven target, no cap):** premature. tCPA wants ~15 to 30 conversions in 30 days to be reliable; we have 1.

### Expected effect

A $15 ceiling should pull blended avg CPC from ~$34.74 toward ~$9 to $11 (actual CPC usually lands below the cap). Same ~$200/day then buys roughly 3x the clicks, which is the point: get to 15 to 30 conversions in ~3 to 5 weeks instead of ~5 months, then graduate to a real data-driven target.

### Caveats / watch items

1. **Learning period:** applying a new portfolio strategy resets learning (~1 to 2 weeks of volatility). Do not tinker daily. We lose nothing because there was no real learning on 1 conversion.
2. **Conversion-tracking health gates everything downstream.** The one "conversion" came from a research keyword, which is suspect. Per `CLAUDE.md`, the GA4 `generate_lead` GTM trigger may still fire on `/thank-you/` pageview instead of the `lead_confirmed` custom event, which inflates/garbles conversions. tCPA now bids ON this data, so confirm the trigger is `Custom Event = lead_confirmed` before trusting any tCPA result or moving to a real target.
3. **Confirm the campaign optimizes to `generate_lead` only.** If pageviews or phone-call conversions are also primary, tCPA chases the wrong goal.
4. **Apply the strategy to the campaign.** Creating the portfolio strategy in Shared Library does nothing until it is applied to the Sellers campaign (and only that campaign).

### The other half of the fix: negatives (intent, not price)

The cap stops overpaying; it does not fix that most traffic is research/tool intent, not sellers. Highest-value negatives straight from the search-terms report:

- `flat fee` (phrase) — `flat fee realtor` cost $85.76, DIY/discount intent.
- `ownerly` (phrase) — `ownerly free` still cost $60.82; the existing exact exclusion missed the variant.
- Tool/brand seekers: `quantarium`, `housecanary`, `corelogic`, `realavm`, `rocket mortgage`, `freedom mortgage`, `kelley blue book`.
- Brokerage brands: `keller williams` / `kw`, `john l scott`, `first team`, `realty one group`, `exp realty`, `serhant`, plus `zillow` / `redfin` / `zestimate` if not already excluded.
- The flood of `[agent name] realtor` terms means phrase-match close variants are drifting. Go exact-heavy.

Deliberately NOT negated: the `home value estimator` family. The lone conversion came from one, so the cap (not a negative) is the right tool there.

### Exit criteria (when to revisit this decision)

Revisit when BOTH are true:
1. `generate_lead` is confirmed firing on `lead_confirmed` (clean conversion signal), AND
2. the campaign has accumulated ~15 to 30 conversions in a trailing 30 days.

Then: remove or loosen the $15 cap and set a real Target CPA at ~1.2x the observed clean CPL (per `sellers-max-intent-campaign.md` §11 Phase 2).
