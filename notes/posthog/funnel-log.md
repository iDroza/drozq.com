# Funnel log

Chronological observations from PostHog about the homepage funnel. Newest at top. See `README.md` for the format.

---

## 2026-05-31: sell-funnel "something went wrong" on submit (network dead-end) fixed

Joshua reported a visitor who got "Something went wrong" after submitting the
Sell funnel; the lead did not go through. PostHog (raw HogQL, internal traffic
counted), 45 days: funnel_open 127 -> submit_attempt 11 -> submit_success 9 ->
submit_error 2. Both errors were error_kind=network, mode=sell, clustered
2026-05-31 07:51:01 to 07:51:16 UTC (one person, two tries 15s apart). Last
success 2026-05-28 19:54, which matches the last real lead email exactly.

Root cause: NOT a dead endpoint. Honeypot probe returned 200, MailChannels was
delivering (lead emails confirmed arriving in Gmail from leads@drozq.com), the
server was healthy. The client fetch hit a network blip or the aggressive 10s
AbortController timeout, and the catch branch dead-ended the lead with no retry,
so the lead was lost and the visitor saw the generic error.

Fix (commit a897a2d, synced to all funnel pages + functions/api/lead.js):
- Client: retry up to 3 attempts on transient failure (fetch reject, abort/
  timeout, 5xx/429); a 4xx stays terminal; per-attempt timeout 10s -> 20s; new
  funnel_submit_retry event (mode, attempt, error_kind).
- Server: decouple acceptance from delivery (validate -> waitUntil(deliver) ->
  return 200), redundant MailChannels + Zapier each with an 8s timeout + error
  logging, never 500 on missing email config, name/intent default to a
  placeholder instead of a 400 (a client name-capture gap can't cost a lead).

Verified live: new retry code present on homepage + /rates/, honeypot still 200.

Side note (separate issue): several recent leads show corrupted phones
((194) 941-2137, (109) 992-0200, (165) 735-2940), the +1 truncation signature.
normalizePhone / normalizeUsDigits are preserved here; worth confirming the
e2e5f1d fix actually deployed before those leads landed.

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
