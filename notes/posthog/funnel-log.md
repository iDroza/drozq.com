# Funnel log

Chronological observations from PostHog about the homepage funnel. Newest at top. See `README.md` for the format.

---

## 2026-05-12, Baseline, before PostHog MCP was connected

PostHog MCP was wired into this repo today. Nothing has been queried yet. The funnel as it stands:

- Three modes: Sell (5 steps), Buy (5 steps), Sell&Buy (6 steps).
- Hero tabs and mid-page tabs both open the funnel in the correct mode via `detectFunnelMode(form)`.
- `gclid` is captured on page load and persisted (URL → cookie → sessionStorage) and pushed to dataLayer.
- Geo replaces "Columbus, OH" everywhere except the Move-hosted market-trends iframe (deferred).
- Submission redirects to `/thank-you/?ref=funnel`, which fires `lead_confirmed` once on the genuine submission path.
- GA4 `generate_lead` is still on the old pageview trigger (cleanup pending in GTM, not in this repo).

Open questions to ask PostHog in the next session, in priority order:

1. Drop-off rate per step per mode for the last 30 days. Where do users actually leave?
2. Mode mix. What fraction of `funnel_open` events fire in each mode? Are we under-investing in Buy or Sell&Buy copy?
3. Mobile vs. desktop drop-off split. Mobile is the dominant device for paid clicks and the deepest source of conversion loss historically.
4. Distribution of `funnel_submit_error` by `error_kind` (server, server_parse, network). Anything > 1% is a real issue.
5. How often does `funnel_back` fire? Users who back up at least once, do they convert at a different rate than the linear path?
6. Time between `funnel_open` and `funnel_submit_success` for completed sessions. If the median is climbing, that's a regression signal.
7. Gclid-attributed sessions vs. organic. Confirm `gclid_captured` is landing on every paid session.

Nothing actionable yet. Next entry should be the first real query.
