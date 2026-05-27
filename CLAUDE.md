# Claude Code Instructions

*Last reviewed: May 23, 2026*

## The standard

Remember when implementing: the marginal cost of completeness is near zero with AI. Do the whole thing. Do it right. Do it with tests. Do it with documentation. Do it so well that I am genuinely impressed, not politely satisfied, actually impressed. Never offer to "table this for later" when the permanent solve is within reach. Never leave a dangling thread when tying it off takes five more minutes. Never present a workaround when the real fix exists. The standard isn't "good enough", it's "holy shit, that's done." Search before building. Test before shipping. Ship the complete thing. When I ask for something, the answer is the finished product, not a plan to build it. Time is not an excuse. Fatigue is not an excuse. Complexity is not an excuse. Boil the ocean.

## Auto-commit

Always commit and push changes to main after completing each task without asking. Ship fast. Rollback is always available via `git revert [hash] && git push`.

When making changes to high-risk files (homepage hero, the funnel, tracking scripts, files containing the GTM container, any registered page in `funnels.json`), include a clear, descriptive commit message so rollbacks can be surgical if needed.

## About this project

drozq.com is the site for Joshua Guerrero, a solo real estate agent under Real Brokerage based in Irvine, California. The site is built to convert paid traffic into qualified leads. **Every page captures leads. The homepage is the template for the entire site.**

The homepage (originally a clone of sell.realtor.com / UpNest's agent-locator pattern) is the canonical look, feel, and behavior. Visual style, hero structure, mid-page tabs, FAQ accordion, footer, and funnel are all reusable as scaffolding for new pages. When asked to build a new page, the default is "homepage with a different angle," not "different design."

Every page on the site is now on the homepage template. The historical distressed-sellers paid landing at `/relief/` was deleted on 2026-05-26 (see `BACKLOG.md` for the rebuild task). The strategy playbook for that audience still lives in `notes/ads/distressed-sellers-strategy.md` for when the campaign relaunches.

Pages on the homepage template: `/`, `/about/`, `/california/`, `/contact/`, `/faq/`, `/field-notes/`, `/los-angeles/`, `/market-insights/`, `/meet-the-team/`, `/prices/`, `/privacy/`, `/process/` (renamed from legacy `/the-process/`), `/rates/`, `/terms/`, `/testimonials/` (+ /001-long-beach-firefighter/ + /002-corona-analyst/), `/thank-you/`, `/value/`, `/where-we-help/`. The source of truth for "is this page using the synced funnel" is `funnels.json#pages`. The source of truth for "is this page on the homepage template" is the presence of `migrate_<slug>.py` in `scripts/` and the absence of brand-mode classes (`cf-narrow`, `lead-modal`, `mt-hero`, `about-hero`, etc.) in the rendered HTML.

## Core operating principles

1. **Every page captures leads.** No exceptions. New pages either embed the inline funnel (the default) or carry a CTA that opens it. Removing or breaking the lead path is a critical regression.

2. **The homepage is the template.** New pages start by copying index.html scaffolding (head, hero with funnel tabs, mid-page tabs, FAQ accordion, footer) and then swapping page-specific copy. They do not start from a brand-mode page.

3. **The funnel is inlined, not redirected.** Redirects cost conversions. Every page that needs the funnel carries its own physical copy of the HTML and JS. Sync is managed by the funnel registry (see below); never hand-edit a synced page's funnel block.

4. **Tracking is sacred.** GTM-KVV3R96P + GA4 + PostHog (via t.drozq.com proxy) + Google Maps Places + gclid capture + the `lead_confirmed` event on /thank-you/. Do not modify, remove, or "clean up" any tracking element without explicit instruction.

5. **Form integrity is sacred.** All forms POST to `/api/lead`, redirect to `/thank-you/?ref=funnel`, and set `sessionStorage.drozq_lead_just_submitted = "1"` immediately before the redirect. Breaking the redirect or the flag silently destroys conversion measurement.

6. **Mobile is the primary canvas, not a responsive afterthought.** The majority of paid traffic and organic visits land on mobile. Every page is designed at 375px first, then enhanced upward for tablet (768px) and desktop (1440px). If a layout decision forces a tradeoff between mobile and desktop, **mobile wins** — including hero copy length, CTA placement, grid column count, image crop, type scale, and tap-target size. Base styles are mobile; use `min-width` media queries to add complexity, never `max-width` to subtract from a desktop-first design. Verify in a real mobile viewport (not just a resized desktop browser) before claiming a page works.

7. **No em dashes.** U+2014 is banned. Use commas, periods, parens, or colons. Final-pass every output to confirm zero em dashes.

8. **No new external dependencies.** No new CDNs, frameworks, or libraries. All JS is vanilla; all styling lives in the inline `<style>` blocks of each page (Panda CSS utility classes on homepage-style pages, a small CSS reset + scoped classes on legacy brand-mode pages).

## Creating a new page

**STOP. Before doing anything else, read `TEMPLATE.md` (repo root) front to back.** It is the canonical spec for every visual element, behavior, token, and form pattern that makes a Drozq page a Drozq page. The summary below is just a pointer. The contract is in `TEMPLATE.md`.

When asked to create a new page, follow this protocol:

### 1. Default to the homepage as scaffolding

`index.html` is the source-of-truth template. A new page starts as a stripped copy of it, with these sections preserved:

- Head: GTM container snippet, favicons, viewport meta, canonical, OG/Twitter tags (rewrite the values).
- Page-level `<style>` block (the Panda CSS utility-class soup at the top of the body line) — keep verbatim unless the page genuinely needs new styles.
- Header (the realtor.com-clone nav with hamburger and More popup). Note: per `692fb46`, `a7fabbd`, `2cb191f`, the header for new visitors is hidden on desktop until they engage; this should carry across.
- Hero: the 3-tab funnel CTA bar (Sell / Buy / Sell & Buy). Page-specific copy and imagery go here.
- Mid-page tabs section ("I'm selling / I'm buying"): optional but encouraged. Same data attributes (`sellTabBtn` / `buyTabBtn` controlling `sellTab` / `buyTab`).
- FAQ accordion: optional, page-specific questions.
- Footer: the minimal conversion-page footer (brand logo, identity line, DRE, phone, social, Privacy/Terms, copyright). Do not import the heavy legacy brand-mode footer.
- Funnel overlay + funnel JS: inlined between the four `DROZQ_FUNNEL_*` markers. After scaffolding, register the page (see "Funnel sync registry" below).

### 2. Register the page in funnels.json

```
python scripts/sync_funnels.py --add path/to/new-page/index.html
```

This adds the page to the registry without syncing yet. The new page must already contain the four `DROZQ_FUNNEL_*_BEGIN/END` markers in the same order as `/index.html` (which it will if it was copied from `index.html`).

### 3. Run a first sync to confirm the new page's funnel block matches the source

```
python scripts/sync_funnels.py
```

The script reads `/index.html` and writes its funnel HTML and JS into every registered page. If the new page's block already matches the source, it reports `OK`. Otherwise it reports `SYNCED` and updates the page.

### 4. Customize page-specific content OUTSIDE the funnel markers

Everything between `DROZQ_FUNNEL_HTML_BEGIN/END` and `DROZQ_FUNNEL_JS_BEGIN/END` is synced from the homepage automatically. Anything outside those markers is page-specific and stays untouched by syncs. Hero copy, hero images, mid-page tab content, FAQ questions, meta tags, and page-level styles all live outside the markers.

### 5. Set noindex,follow for paid-traffic landing pages

Paid landing pages (campaign destinations like `/relief/`) should carry `<meta name="robots" content="noindex,follow">` so they don't compete with brand pages in organic search.

### 6. Verify on live after deploy

Cloudflare auto-deploys in 30-60s. Verify the page renders, the funnel opens from every CTA (hero tabs + mid-page tabs + any extra CTAs), submit redirects to `/thank-you/?ref=funnel`, and PostHog events fire (`funnel_open`, `funnel_step_advance`, `funnel_submit_success`).

## Funnel sync registry

The funnel exists in exactly one place: `/index.html`, between the markers `<!-- DROZQ_FUNNEL_HTML_BEGIN -->` ... `<!-- DROZQ_FUNNEL_HTML_END -->` and `<!-- DROZQ_FUNNEL_JS_BEGIN -->` ... `<!-- DROZQ_FUNNEL_JS_END -->`. Every other page that carries the funnel imports those two blocks via the sync script.

**Files:**

- `funnels.json` (repo root): registry. Lists the source path, the markers, the registered pages, the last sync timestamp, and per-page sync timestamps.
- `scripts/sync_funnels.py`: the propagation tool.

**Workflow:**

| When | What to do |
|---|---|
| Changing the funnel (steps, validation, submit, tracking, copy) | Edit `/index.html` between the markers. Run `python scripts/sync_funnels.py` to push to all registered pages. Commit + push. |
| Adding a new page that needs the funnel | Scaffold from `index.html`, copy the marker blocks verbatim, then `python scripts/sync_funnels.py --add <path>` and `python scripts/sync_funnels.py`. |
| Confirming the registry is clean before a release | `python scripts/sync_funnels.py --check`. Exits non-zero if any registered page has drifted. |

**Hard rules:**

- Never hand-edit a synced page's funnel block. If you discover drift, fix `/index.html` and re-sync. Drift caught by `--check` is a regression, not a feature.
- Never split the funnel HTML and JS into separate sources. They co-evolve.
- The funnel JS includes the Maps race guard, the Maps API loader, the gclid capture, `detectFunnelMode`, `openFunnel`, `attachSubmitHandler`, `showStep`, `wireTabs`, geo autofill, FAQ accordion wiring, and the PostHog `track()` helper. All of this syncs together because it is one logical unit.
- Mobile-nav script and other page-level UI live OUTSIDE the funnel JS markers (mobile nav is a separate `<script>` tag after `DROZQ_FUNNEL_JS_END`). New pages copy that block verbatim from the homepage scaffold but it does not sync.

## Funnel architecture

The homepage funnel is a paid-traffic conversion machine with **three parallel funnels** controlled by hero tabs and mid-page tabs:

| Funnel | `data-funnel` | Steps | Final CTA | Submitted intent |
|---|---|---|---|---|
| Sell | `sell` | 5 | "Send My CMA" | `Home Valuation` |
| Buy | `buy` | 5 | "Send My Buyer's Strategy" | `Home Purchase` |
| Sell & Buy | `sellandbuy` | 6 | "Send My Move Plan" | `Home Sale + Purchase` |

Each step is a `<div class="funnel-step" data-funnel="…" data-step="N">` inside `<section id="funnel-overlay">`. The active funnel is `window.activeFunnel`, set via:

- Hero tab clicks (`tab-sell` / `tab-buy` / `tab-sell-buy`) → swap the visible tabpanel; the panel's Compare Agents button opens its matching funnel.
- Mid-page tab clicks (`sellTabBtn` / `buyTabBtn`) → swap copy in the "Why work with an agent?" section between `sellTab` and `buyTab` panels; their inner Compare Agents form opens the matching funnel.
- Other CTAs in the body (e.g., footer or section forms) default to Sell mode.

`detectFunnelMode(form)` reads the form's `[role="tabpanel"]` ancestor (id + aria-labelledby), lowercases, and substring-matches: `sell-buy` / `sellandbuy` / `sellbuy` → `"sellandbuy"`, then `buy` → `"buy"`, default `"sell"`. Used at landing-CTA click and inside the Places autocomplete `place_changed` callback.

`showStep(n)` filters `.funnel-step` elements by `data-funnel === window.activeFunnel && data-step === String(n)`. `FUNNEL_TOTAL_STEPS = { sell: 5, buy: 5, sellandbuy: 6 }`.

Submit is handled by a single `attachSubmitHandler(buttonId, mode, ids)` factory called three times (one per funnel). It validates email + phone (and name on Buy / Sell & Buy where the contact step is one combined step), builds a mode-specific `FormData`, posts to `/api/lead`, then redirects to `/thank-you/?ref=funnel`.

### Funnel state shape

```js
window.funnelState = {
  // Sell + Sell&Buy use these:
  address: { street, city, state, zip, lat, lng, formatted },
  timeline, priceRange, propertyType,
  // Buy uses these:
  buyLocation, buyTimeline, buyBudget, buyHomeType, buyProcess,
  // All funnels:
  fullName, email, phone,
  gclid, pageUrl, timestamp
};
```

### Address validation

- Sell + Sell&Buy: require Places-confirmed full street address (street_number + route present). The `validAddressMap` WeakMap tracks per-input validity.
- Buy: requires only a non-empty input value (city/area input).
- The geo autofill pre-fills inputs but never marks them as Places-validated, so Sell users still need to pick from the dropdown.

## Tracking stack (DO NOT MODIFY without explicit instruction)

The following tracking is wired into every page including the homepage. Do not remove, modify, or "clean up" these without explicit instruction, even if they look like dead code:

- **Google Tag Manager container** (`GTM-KVV3R96P`): head + body noscript snippets on every HTML page. Orchestrator for all other tracking.
- **GA4** (`G-XSP0L11QEY`): fires via GTM. Do not install direct gtag.js on the site.
- **PostHog**: loads via GTM custom HTML tag, routed through reverse proxy at `t.drozq.com` for ad-blocker evasion. Session replay, product analytics, and web analytics are enabled. Project ID: `phc_Aa6GdWNbL9Kc9PhrnqR3Zq7Fc4zv2GxB2sPS59QamhyW`.
- **Google Ads conversion tracking**: imports the `generate_lead` event from GA4. No direct AW-* tags on the site.
- **gclid capture**: lives in the homepage funnel IIFE (and therefore on every synced page). On page load, reads gclid from URL → cookie → sessionStorage (priority order). If sourced from URL, persists to a 90-day cookie + sessionStorage. Pushes a `gclid_captured` event to `dataLayer` on every pageview.

If asked to "clean up scripts" or "remove unused tags," STOP and confirm which specifically. Direct `AW-*` gtag installations are forbidden.

The form submission flow MUST redirect to `/thank-you/?ref=funnel` on success. The receiving page reads `sessionStorage.drozq_lead_just_submitted` and pushes a `lead_confirmed` event to `dataLayer`. Breaking this redirect or removing the sessionStorage flag silently destroys conversion measurement across the entire paid funnel.

### `lead_confirmed` event (gates GA4 generate_lead)

The funnel sets `sessionStorage.drozq_lead_just_submitted = "1"` and `sessionStorage.drozq_lead_mode = "<sell|buy|sellandbuy>"` immediately before redirecting to `/thank-you/?ref=funnel`. The thank-you page reads + clears those flags, pushes a `lead_confirmed` dataLayer event with `funnel_mode` metadata, and strips `?ref=funnel` from the URL via `history.replaceState`.

This means:
- Real funnel submit → `lead_confirmed` fires once.
- Direct visit / refresh / bookmark → no flag → no fire.
- Tab closed and reopened to /thank-you/ → sessionStorage gone → no fire.

**Outstanding GTM action item for Joshua**: change the GA4 `generate_lead` trigger from "Page View on /thank-you/" to "Custom Event = `lead_confirmed`" and turn off the old pageview trigger. Until that lands, conversions are inflated by direct/bookmark/refresh visits.

### PostHog funnel drop-off events

The funnel JS dual-fires every transition through a `track(event, props)` helper that calls both `window.posthog.capture(event, props)` and `dataLayer.push({event, ...props})`. Both calls are null-safe.

| Event | When | Properties |
|---|---|---|
| `funnel_open` | Funnel overlay opens | `mode`, `prefill_provided`, `gclid` |
| `funnel_step_advance` | `showStep(n)` with `n > prev` | `mode`, `from_step`, `to_step`, `total_steps` |
| `funnel_back` | `showStep(n)` with `n < prev` | `mode`, `from_step`, `to_step` |
| `funnel_option_selected` | Auto-advance option click | `mode`, `step`, `value` |
| `funnel_submit_attempt` | Validation passes, fetch starts | `mode` |
| `funnel_submit_success` | `/api/lead` returns ok, before redirect | `mode` |
| `funnel_submit_error` | API non-ok or fetch rejects | `mode`, `error_kind` (server / server_parse / network) |

## Cloudflare Pages Functions

Cloudflare Pages auto-deploys functions from `/functions/`. Five endpoints currently exist:

### `/functions/api/lead.js`

Form submission handler. Accepts `application/x-www-form-urlencoded` or `multipart/form-data`. Honeypot field is `company_website`; non-empty value silently 200s without sending the email.

Required fields: `name`, `email`, `phone`, `intent`, `consent="yes"`. Other fields (gclid, full_address, lat/lng, message, source_page, page_url, submitted_at, plus mode-specific buy_location/buy_timeline/etc.) are optional but forwarded.

Sends a plaintext email to `TO_EMAIL` (env var) from `FROM_EMAIL` via MailChannels. Optionally posts the same fields to `ZAPIER_WEBHOOK_URL` if set.

Required env vars in Cloudflare Pages settings: `TO_EMAIL`, `FROM_EMAIL`, `MAILCHANNELS_API_KEY`. Optional: `ZAPIER_WEBHOOK_URL`.

Returns `{ ok: true }` on success, `{ ok: false, error: "<reason>" }` on failure. The funnel client treats anything other than 200 + ok:true as an error.

### `/functions/api/geo.js`

Returns the visitor's geolocation from Cloudflare's `request.cf` object (populated from the request IP, no third-party service is called). Response:

```json
{
  "city": "Irvine",
  "region": "California",
  "regionCode": "CA",
  "country": "US",
  "postalCode": "92612",
  "timezone": "America/Los_Angeles"
}
```

Cache header: `private, max-age=3600`. The homepage fetches this on `DOMContentLoaded` and replaces "Columbus, OH" defaults across the page.

### `/functions/api/rates.js`

Proxies the Federal Reserve Economic Data (FRED) API and edge-caches for 1 hour. Returns ~1 year of history per series for sparkline rendering and YoY deltas. Four series: `MORTGAGE30US` (30-year fixed, weekly), `MORTGAGE15US` (15-year fixed, weekly), `DGS10` (10-year Treasury yield, daily), `FEDFUNDS` (Federal funds rate, monthly).

Response shape per series entry:
```
{
  seriesId, label, unit, cadence,
  latest:   {value, date},     // newest observation
  previous: {value, date},     // observation before latest
  yearAgo:  {value, date},     // oldest observation in ~1y window
  history:  [{date, value}, ...],   // ascending order, ~1 year
  delta,                       // latest - previous
  deltaYoY                     // latest - yearAgo
}
```

Top-level fields: `ok`, `series`, `lastUpdated` (most recent observation date across all series), `fetchedAt`, `source`, `sourceUrl`.

Required env var in Cloudflare Pages settings: `FRED_API_KEY` (get one free at https://fred.stlouisfed.org/docs/api/api_key.html). If missing, the endpoint returns `503 {ok:false, error:"fred_api_key_missing"}` and `/rates/` falls back to a graceful "data temporarily unavailable" state.

Consumed by `/rates/index.html`. The page ships static skeletons, then hydrates four rate cards (with inline SVG sparklines + WoW + YoY deltas), an affordability table (5 loan sizes at today's 30-year), and a mortgage payment calculator (default rate auto-syncs to today's 30y / 15y based on the term toggle). FAQ accordion + WebPage/Dataset/FAQPage/BreadcrumbList/Person JSON-LD make the page a citable resource that ranks for rate + calculator + explainer queries.

The page is the live freshness signal: the moment FRED publishes a new PMMS reading (Thursdays at 12 ET), the next `/api/rates` response after edge-cache expiry (within 1h) reflects it.

### `/functions/api/prices.js`

Sibling of `/api/rates.js`. Same FRED-backed pattern, same 1h edge cache, same `FRED_API_KEY` env var. Returns seven series organized into two tiers:

- **California home prices** (Tier 1): `LXXRSA` (LA Metro Case-Shiller, monthly), `SDXRSA` (San Diego Metro Case-Shiller, monthly), `CASTHPI` (FHFA California Statewide HPI, quarterly).
- **Market signals** (Tier 3): `MSACSR` (months of supply, new homes, monthly), `EXHOSLUSM495S` (existing home sales, monthly SAAR thousands), `FIXHAI` (NAR housing affordability index, monthly), `UNRATE` (US unemployment, monthly).

Response shape per series matches `/api/rates` plus two extra fields for index/count series: `deltaPct` (percent change vs. previous observation) and `deltaYoYPct` (percent change vs. one year ago). The YoY observation is picked via a cadence-specific offset (`{daily:252, weekly:52, monthly:12, quarterly:4}`) instead of "oldest in window", so YoY stays YoY regardless of how much history we fetch.

Originally included a Tier 2 series (`MORTGAGE5US`, the 5/1 ARM rate) as a "cost of money" complement, but Freddie Mac discontinued the 5/1 ARM in their PMMS survey in November 2022. FRED still exposes the series but every observation past 2022-11-10 is null. Until a replacement ARM benchmark surfaces on FRED, `/prices/` carries a thin crosslink band to `/rates/` instead. See the [[fred-mortgage5us-discontinued]] memory for the recheck criteria.

Consumed by `/prices/index.html`. Same render pattern as `/rates/`: static skeletons hydrate on `DOMContentLoaded` with per-unit value formatting (index → integer, percent → `X.XX%`, months → `X.X mo`, thousands → `X.XM` annualized), inline SVG sparklines, and a primary delta + YoY delta per card.

### `/functions/api/valuation.js`

Powers the `/value/` page. Aggregates a single paid upstream (Rentcast) into five different "what is this home worth?" answers, plus an investor metrics panel. Edge-cached per address for 7 days.

The five systems:

1. **Market AVM** — Rentcast `/v1/avm/value`. Statistical model on recent local sales (effectively what Zestimate/Redfin Estimate is). Returns value + range + comps.
2. **Tax assessor value** — Picked from the `taxAssessments` map on the Rentcast `/v1/properties` record (newest year). Falls back to `lastSalePrice` when no assessor entry exists. In CA, this lags market by 30-70% on long-held homes (Prop 13).
3. **Replacement cost** — Computed in-house from sqft × `REGION_FACTORS[county]` × `QUALITY_FACTORS[tier]` × NAHB 2024 national baseline ($284/sqft). Quality tier inferred from subject's $/sqft vs. regional baseline. Methodology disclosed in the response.
4. **Investor ARV (after repair value)** — Avg $/sqft of the top third of Rentcast's comparable sales (proxy for "recently renovated"), applied to subject's sqft. Falls back to `AVM × 1.18` premium if fewer than 5 valid comps.
5. **Triangulated price** — Weighted blend (`AVM 60% + comp median 25% + ARV 15%`). Marked as Joshua's recommended list price; future override slot for properties he's personally walked.

Plus an **investor panel** with rent estimate (Rentcast `/v1/avm/rent/long-term`), cap rate at 35% expense ratio, GRM, 70% wholesale offer (`ARV × 0.70 − $50/sqft rehab`), and monthly P&I + cash flow at current 30y from `/api/rates` (20% down, 30-year term).

Accepts `GET ?address=...&lat=...&lng=...` or `POST` (JSON or form). Response shape:
```
{
  ok, address: {input, formatted, street, city, state, zip, county, lat, lng},
  property: {propertyType, bedrooms, bathrooms, squareFootage, lotSize, yearBuilt, lastSalePrice, lastSaleDate},
  systems: {
    marketAVM:       {label, value, rangeLow, rangeHigh, compsCount, methodology},
    assessor:        {label, value, year, land, improvements, methodology},
    replacementCost: {label, value, psf, sqft, region, quality, methodology, ...},
    arv:             {label, value, method, compsUsed, compsTotal, avgPsf, methodology},
    triangulated:    {label, value, methodology}
  },
  investor: {monthlyRent, capRate, grm, wholesale70: {value, ...}, monthlyPI, monthlyCashFlow, rate30y, methodology},
  rentEstimate: {monthly, rangeLow, rangeHigh, source},
  diagnostics: {propertyError, avmError, rentError},
  source, sourceUrl, fetchedAt
}
```

Required env var in Cloudflare Pages settings: `RENTCAST_API_KEY` (get one at https://app.rentcast.io/app/api). If missing, the endpoint returns `503 {ok:false, error:"rentcast_api_key_missing"}` and `/value/` falls back to a graceful error state instead of rendering broken cards.

The page does a side-effect soft lead-save on every valuation submit: POSTs the address (with placeholder name/email/phone) to `/api/lead` with `intent="Home Valuation View"`, so the visitor's address lands in Joshua's CRM even before they hit the funnel CTA. The funnel CTA below the results is the gate for the *refined* CMA (real name + email + phone via the existing 5-step Sell funnel).

## Geo personalization

On every homepage pageview (and every synced page's pageview, since geo autofill is part of the synced JS), JS fetches `/api/geo` and:

1. Replaces every `<input name="location" value="Columbus, OH">` with `"{city}, {regionCode}"`. Only when current value is empty or the literal default; preserves returning-visitor data per the existing `populateLandingInputs` convention.
2. Replaces every visible "Columbus, OH" text node via TreeWalker (hero strip, market-section h2). Skips SCRIPT/STYLE/IFRAME descendants.
3. Updates `.funnel-city` / `.funnel-buy-city` placeholder spans inside the funnel overlay so step copy reads "buying in Irvine" instead of "Southern California" once detected.

The Move-hosted Columbus market-trends iframe (`realtorqa.upnest.com/market-trends`) is not rewritten; it is fed `slug_id=Irvine_CA` directly in the iframe URL.

If `/api/geo` 500s or returns empty, all defaults remain.

## Form integrity (conversion-critical)

Forms are the primary conversion mechanism. Breaking them is the single worst thing that can happen, and the error mode is silent (the form appears to work but no data flows).

For ANY page with a form:

- NEVER modify field names, IDs, or data attributes without verifying downstream dependencies in `/functions/api/lead.js` and any GTM event triggers.
- NEVER remove hidden fields (gclid, utm_*, address component parsing, lead_source).
- NEVER remove the Google Maps Places Autocomplete initialization or place_changed handlers.
- ALWAYS preserve submission → `/thank-you/?ref=funnel` redirect.
- ALWAYS preserve `sessionStorage.drozq_lead_just_submitted = "1"` set immediately before the redirect.
- ALWAYS preserve the timeline question on the funnel (lead qualification signal).

Changes to the funnel require extra caution and should be visually inspected on the live site within 5 minutes of deploy.

## Favicon

Modern pattern, used on every page:

```html
<link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="Drozq">
<link rel="manifest" href="/site.webmanifest">
```

Files at repo root: `favicon-96x96.png`, `favicon.svg`, `favicon.ico`, `favicon.png`, `apple-touch-icon.png`, `site.webmanifest`. Do not modify, rename, or remove these. Do not use absolute URLs with spaces in filenames.

## Deployment

This site auto-deploys to production via Cloudflare Pages on every push to main. There is no staging environment, no manual deploy step.

- Pushing to main = live in 30-60 seconds (sometimes 60-120s for function updates).
- Broken changes affect real users (and paid traffic) immediately.
- Rollback: `git revert [commit-hash] && git push`.

When paid ad campaigns are running, high-risk changes (hero rewrites, funnel restructures, navigation changes, tracking modifications) should be committed with clear messages, verified on live site immediately, checked for JS errors in the console, and rolled back if anything breaks.

Per the auto-commit rule, push directly to main. No feature branches unless explicitly requested.

## Conversion copy principles

These apply to all pages. The site is one voice across all pages: confident, direct, first-person, low-bullshit. Joshua Guerrero, solo agent, speaking in his own voice.

### Hero opener: headline + one-sentence subhead, no eyebrow

Every page on the homepage template (every page except the homepage itself) opens with a hero text section that has exactly **two** elements: a short headline and a short subhead. No eyebrow above the H1, no extra labels, no second paragraph. Body sections downstream can use the 11-12px uppercase eyebrow pattern freely; the opener cannot.

The reasoning: the opener is the highest-leverage real estate on the page, and an eyebrow eats visual budget for label text the headline already implies. Subheads longer than one sentence dilute the read. The standard is **value per second**: a visitor scanning the splash should leave with one promise, not a paragraph.

Concretely:
- **Headline:** one tight line. Two short lines max with an intentional `<br>` (e.g. `/process/`'s "How I sell your home. / Five steps. Six to ten weeks.").
- **Subhead:** one sentence. Short. Concise. To the point. A desire, a question, or a value statement. Comma-separated lists are fine; two sentences is wrong. If methodology, sources, or scope need explaining, put them in a body section, not the opener.
- **No opener eyebrow.** Banned: `<p class="op_0.9 c_#fff ls_2px fs_11px ...">EYEBROW</p>` directly above the H1.

Codified in `TEMPLATE.md` §4 ("Hero opener copy rule") and §14 ("Anti-patterns").

### Optimize the Value Equation

Every page should pull at least one of these levers. If copy doesn't, it's filler.

- **Dream Outcome (↑):** specific outcome states. "$23,250 in seller credit negotiated," not "significant savings."
- **Perceived Likelihood (↑):** systems, data, anti-claims (things you don't do). Concrete process beats vague experience.
- **Time Delay (↓):** response-time commitments, list-to-MLS speed, step-by-step timelines with numbers.
- **Effort and Sacrifice (↓):** explicit "I handle X, you handle Y." The most underdeveloped lever in current copy; biggest differentiation opportunity.

### What to avoid

- Generic real estate platitudes ("I'm passionate about helping families find their dream home").
- SEO-style filler ("how to sell my house fast in [city]").
- Stock testimonial language ("5-star rated," "trusted advisor").
- Star ratings or platform-aggregated reviews. The funnel and real numbers do this work better.
- Hyperbolic claims that can't be backed up.
- Surface-level "AI" and "automation" framing. The leverage Joshua has is real; the framing is "systems and discipline," not "I use software to do this."
- Em dashes (U+2014). Banned everywhere.
- **Anti-promise / negative-association copy.** Banned phrases: "no autodialer," "no spam," "no pressure," "no call center," "no script," "no pitch," "no obligation," "no team," "no sales script." The reasoning: most prospects aren't worrying about these things; explicitly denying them plants the worry. The rule is "never name the bad thing, even to deny it." Reframe with positive value: "direct callback within X hours," "an honest read on whether to list," "you walk away with better information." Exception: pricing statements that frame a real cost concern positively are fine ("No fee unless we list," "free CMA").

### Audience archetypes

Sellers (primary):
- Strategic move-up / move-down (dual-income, 5 to 15 years in home, data-oriented).
- Life-event forced sellers (divorce, relocation, medical, bankruptcy) — value privacy and discretion.
- Inherited-property heirs (probate) — value empathy, coordination with attorneys/siblings.
- Long-term cashing out (retirement, downsizing) — value capital gains awareness.
- Investor / rental owners — value 1031 experience.

Buyers (secondary):
- First-time buyers — value patience, education, financing guidance.
- Move-up buyers — often combined with the Sell&Buy funnel.
- Investors / 1031 exchange buyers.
- Out-of-area / relocation buyers.

Page copy should include specific-situation acknowledgments without dedicating whole pages to each. One-sentence callouts beat sections.

## Realtor.com clone state

The homepage was a clone of sell.realtor.com that has been incrementally cleaned. Knowing what's been done vs. what's deferred matters when interpreting the existing markup.

### Done (do not redo)

- External `<a href="http(s)://…">` redirected to `#top` so paid clicks don't leak off-site (excludes `tel:`, `mailto:`, relative paths, internal funnel `href="#"` back buttons).
- Phone numbers replaced: header/footer display `(949) 438-5948` (was UpNest's 800-419-0261 and 800-692-5010).
- Move Inc tracking pixels destroyed: Facebook pixel `754678604575607`, DoubleClick advertiser `10291144` (3 iframes), Bing UET `25046895`, Adobe/Everest `5154`, `<meta property="fb:app_id">`.
- GTM-KVV3R96P installed (head + body noscript).
- Drozq SEO/social meta installed (title, description, canonical, og:*, twitter:*, favicons).
- Drozq social URLs: Facebook → `facebook.com/Drozq/`, Instagram → `instagram.com/drozq/`, YouTube → `youtube.com/@drozq`. Twitter stays `#top`.
- Hero tabs (Sell / Buy / Sell & Buy) wired with switcher JS.
- Mid-page "I'm selling / I'm buying" tabs wired (`sellTabBtn` / `buyTabBtn` controlling `sellTab` / `buyTab`).
- FAQ accordion wired.
- Three-funnel system built (Sell / Buy / Sell & Buy).
- Geo autofill replacing "Columbus, OH" with detected city.
- Funnel drop-off PostHog events.
- gclid pushed to dataLayer on page load.
- `generate_lead` gated via sessionStorage flag + `?ref=funnel` redirect.
- DRE corrected to `02267255`, Indiana PLA removed.
- Footer gutted: minimal conversion footer (brand logo, identity line, DRE, phone, social, Privacy/Terms, copyright).
- "Source: RealEstateSM" attribution masked on the market-trends iframe (170×34 white overlay, click-blocking).
- Tab IDs renamed (`sellUpnestTab` → `sellTabBtn`, `buyUpnestTab` → `buyTabBtn`).
- 5 fake agent profile cards replaced with the "How We Match You" infographic.
- 5 fake out-of-state testimonials swapped for real case files.
- Move-hosted illustration imagery (`lt6p.com`) removed (zero refs).
- Move-hosted `@font-face` declarations replaced with self-hosted fonts in `/media/fonts/`.
- Footer award badges (Inc 5000, Deloitte Fast 500) and UpNest app store badges removed.

### Deferred

Remaining realtor.com clone leftovers are tracked in `BACKLOG.md` under the "Realtor.com clone leftovers" section. The big ones are the Move-hosted Irvine market-trends iframe (still embedded, currently attribution-masked) and the inline-CSS purge (~157KB Panda CSS soup).

When asked to "clean up the homepage," check `BACKLOG.md` and confirm which item(s) before proceeding.

## Reference docs

- **`TEMPLATE.md` (repo root): REQUIRED READING before building or editing any page.** Canonical spec for tokens, header, hero, sections, mid-page tabs, FAQ, footer, funnel overlay, all behaviors, all forms. The homepage at `/index.html` is the live reference; TEMPLATE.md explains what is in it and why. Treat as gospel. Do not deviate without explicit confirmation from Joshua.
- `BACKLOG.md` (repo root): the single consolidated list of active TODOs across the codebase, grouped by category (Strategy / SEO / Tracking / Realtor cleanup / Hygiene). When work ships, delete the line item in the same commit. This replaces the five prior audit docs (AUDIT-INDEX, SEO-AUDIT-INDEX, FAVICON_AUDIT, SPEED-AUDIT, CHANGES.md) and the realtor cleanup audit.
- `funnels.json` (repo root): funnel sync registry. List of pages carrying the inline funnel + last sync timestamps.
- `scripts/sync_funnels.py`: the funnel propagation tool.
- `notes/posthog/`: running log of funnel observations from PostHog. Read `lessons.md` first, then the most recent entries in `funnel-log.md`, before touching anything that could move funnel drop-off (hero copy, tab structure, step ordering, validation, mobile layout). Append a new dated entry after any session that queried PostHog. See `notes/posthog/README.md` for the convention.
- `notes/ads/`: paid campaign strategy docs (`distressed-sellers-strategy.md`, `sellers-max-intent-campaign.md`). Read before touching the campaigns or campaign landing pages.
- `.mcp.json` (repo root): wires up the PostHog and Google Ads MCP servers. Activation requires `POSTHOG_API_KEY` and Google ADC. Run `/mcp` inside Claude Code to confirm the servers are connected.
- **`notes/mcp-workarounds.md` (repo root): direct REST recipes for PostHog HogQL and Google Ads GAQL. READ THIS the moment either MCP fails (tool rejection, hang, `invalid_grant`, 401, empty schema). Do not retry the MCP — use the direct call. Includes the re-auth one-liner for when the gcloud ADC token expires (every 7 days in OAuth testing mode).**
- `C:\Users\guerr\.claude\projects\C--Users-guerr-Documents-drozq-com\memory\`: auto-memory directory for cross-session context. Read on every session start; updated when stable patterns emerge.

## When in doubt

- Building or editing any page: read `TEMPLATE.md` first. It is the contract.
- Ambiguous styling or structure on a new page: default to the homepage pattern (per `TEMPLATE.md`).
- Ambiguous voice or copy direction: confident, first-person, specific, sparse. No platitudes, no SEO filler, no star ratings.
- Anything that touches the funnel, tracking, forms, or `/api/lead`: stop and audit before modifying.
- Anything that touches a registered page's funnel block: edit `/index.html` and re-sync; never hand-edit.
- Anything labeled "DO NOT MODIFY": ask.
