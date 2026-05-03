# Claude Code Instructions

*Last reviewed: May 03, 2026*

## Auto-commit

Always commit and push changes to main after completing each task without asking. Ship fast. Rollback is always available via `git revert [hash] && git push`.

When making changes to high-risk files (homepage hero, main funnel form, tracking scripts, files containing the GTM container), include a clear, descriptive commit message so rollbacks can be surgical if needed.

## About this project

This is the codebase for drozq.com, the personal real estate website for Joshua Guerrero, a solo real estate agent based in Irvine, California. The site serves two functions that must coexist:

1. **Long-term brand asset.** Content pages (/about/, /field-notes/, /market-insights/, /testimonials/, /meet-the-team/, /faq/, /the-process/) are written and designed to compound in value over years. They are not optimized for immediate conversion. Voice, specificity, and long-tail SEO matter most here.

2. **Paid traffic conversion funnel.** The homepage and any purpose-built landing pages are optimized for Google Ads paid traffic to convert into leads. Form submission rate is the primary KPI. These pages test, iterate, and measure.

When in doubt about which mode applies: check the file path. Homepage and landing pages = conversion mode. Everything else = brand mode.

## Core operating principles

These principles apply to every task in this codebase. They are not preferences. They are constraints.

### 1. Never modify the brand-mode header or footer

The header (top navigation) and footer (bottom site navigation, contact info, legal) on brand-mode pages (/about/, /testimonials/, /faq/, /contact/, /field-notes/, /market-insights/, /meet-the-team/, /the-process/, /thank-you/, etc.) are visually identical on every page and must remain byte-for-byte unchanged across tasks. The only acceptable exception is updating internal nav links if a URL is migrated (e.g., /blog → /field-notes/), and even then, only the link target and visible label change.

The homepage (/index.html) is a separate beast (see "Homepage funnel architecture" below). Its header and footer are the realtor.com clone scaffolding being incrementally cleaned up — not the brand-mode chrome.

### 2. Never use em dashes

The single most common style mistake to watch for. Use commas, periods, parentheses, or colons instead. Run a final pass on every output to confirm zero em dashes exist. The character to search for is U+2014.

### 3. Mobile-first, always

Every page must render intentionally at:

- 375px (mobile)
- 768px (tablet)
- 1440px (desktop)

Write base styles for mobile, then enhance with min-width media queries. Use clamp() for fluid typography. Standard breakpoints already in use:

- Mobile: base styles (no media query)
- Tablet: @media (min-width: 768px)
- Desktop: @media (min-width: 1024px) or (min-width: 1200px) (match existing patterns)

### 4. Reuse design tokens

The existing `<style>` block contains foundational rules (color variables, font families, spacing variables, container widths). Always reuse these tokens. Add new scoped CSS classes when needed, but never override the foundational rules.

### 5. Visual consistency across the site

Every new brand-mode page or section must visually match the established system used on /about/, /testimonials/, /faq/, /contact/, /field-notes/, /market-insights/, and /meet-the-team/. Specifically:

- Section labels: small, uppercase, letter-spaced 0.2em, font-size around 0.875rem
- Section headlines: clamp(1.75rem, 4vw, 3rem), bold, tight line-height
- Body copy: 1.125rem to 1.25rem, line-height 1.6
- Hero stats: clamp(2.5rem, 5vw, 4rem), bold, accent color
- Section spacing: 96px to 128px on desktop, 64px on mobile

The homepage uses a separate Panda-CSS utility-class system inherited from the realtor.com clone; do not mix the two.

### 6. No external image dependencies (brand-mode pages)

For brand-mode pages, all visuals come from the local repo:

- Images live at /media/images/
- Icons live at /media/icons/
- Headshot lives at /media/images/Waist.png

When the exact filename isn't known, use a placeholder filename and an HTML comment: `<!-- SWAP: [description of what to use] -->`. Never link to external image URLs or stock photo services.

The homepage still loads imagery from Move CDNs (`lt6p.com`, `static.rdc.moveaws.com`) — that's part of the deferred realtor cleanup tracked in `REALTOR_CLEANUP_AUDIT.md`. Do not add new external image refs; only the realtor-clone leftovers are tolerated until cleanup.

### 7. No new external dependencies

No new CDNs, frameworks, or libraries. All JavaScript is vanilla. All styling is inline in the existing `<style>` block.

## Homepage funnel architecture

The homepage (/index.html) is a paid-traffic conversion machine built on top of the sell.realtor.com clone. There are **three parallel funnels** controlled by hero tabs and mid-page tabs:

| Funnel | `data-funnel` | Steps | Final CTA | Submitted intent |
|---|---|---|---|---|
| Sell | `sell` | 5 | "Send My CMA" | `Home Valuation` |
| Buy | `buy` | 5 | "Send My Buyer's Strategy" | `Home Purchase` |
| Sell & Buy | `sellandbuy` | 6 | "Send My Move Plan" | `Home Sale + Purchase` |

Each step is a `<div class="funnel-step" data-funnel="…" data-step="N">` inside `<section id="funnel-overlay">`. The active funnel is `window.activeFunnel`, set via:

- Hero tab clicks (`tab-sell` / `tab-buy` / `tab-sell-buy`) → swap the visible tabpanel; the panel's Compare Agents button opens its matching funnel.
- Mid-page tab clicks (`sellUpnestTab` / `buyUpnestTab`) → swap copy in the "Why work with an agent?" section between `sellTab` and `buyTab` panels; their inner Compare Agents form opens the matching funnel.
- Other CTAs in the body (e.g., "Get Started Today" footer form) default to Sell mode.

`detectFunnelMode(form)` reads the form's `[role="tabpanel"]` ancestor (id + aria-labelledby) and returns `"sell"`, `"buy"`, or `"sellandbuy"`. Used both at landing-CTA click and inside the Places autocomplete `place_changed` callback.

`showStep(n)` filters all `.funnel-step` elements by `data-funnel === window.activeFunnel && data-step === String(n)`. `FUNNEL_TOTAL_STEPS = { sell: 5, buy: 5, sellandbuy: 6 }`.

Submit is handled by a single `attachSubmitHandler(buttonId, mode, ids)` factory called three times (one per funnel). It validates email + phone (and name on Buy / Sell&Buy where the contact step is one combined step), builds a mode-specific `FormData`, posts to `/api/lead`, then redirects to `/thank-you/?ref=funnel`.

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
- The geo autofill (see below) pre-fills inputs but never marks them as Places-validated, so Sell users still need to pick from the dropdown.

## Tracking stack (DO NOT MODIFY without explicit instruction)

The following tracking is wired into every page including the homepage. Do not remove, modify, or "clean up" these without explicit instruction, even if they look like dead code:

- **Google Tag Manager container** (`GTM-KVV3R96P`): head + body noscript snippets on every HTML page. This is the orchestrator for all other tracking.
- **GA4** (`G-XSP0L11QEY`): fires via GTM. Do not install direct gtag.js on the site. All GA4 events flow through GTM.
- **PostHog**: loads via GTM custom HTML tag, routed through reverse proxy at `t.drozq.com` for ad-blocker evasion. Session replay, product analytics, and web analytics are enabled. PostHog project ID: `phc_Aa6GdWNbL9Kc9PhrnqR3Zq7Fc4zv2GxB2sPS59QamhyW`.
- **Google Ads conversion tracking**: imports the `generate_lead` event from GA4. Do not install direct AW-* tags on the site. Conversion tracking is managed entirely through the GA4 → Google Ads import pipeline.
- **gclid capture**: lives in the homepage funnel IIFE. On page load, reads gclid from URL → cookie → sessionStorage (priority order). If sourced from URL, persists to a 90-day cookie + sessionStorage. **Pushes a `gclid_captured` event to `dataLayer` on every pageview** so any GA4 Custom Definition can surface gclid on every event, not only on conversions.

If asked to "clean up scripts" or "remove unused tags," STOP and confirm which specifically. Do not make assumptions. Direct `AW-*` gtag installations are forbidden (conversion tracking is handled via GTM + GA4 import).

The form submission flow MUST redirect to `/thank-you/?ref=funnel` on success. The receiving page reads a sessionStorage flag set just before redirect and pushes a `lead_confirmed` event to `dataLayer`. **Breaking this redirect or removing the sessionStorage flag silently destroys conversion measurement** across the entire paid funnel.

### `lead_confirmed` event (gates GA4 generate_lead)

The funnel sets `sessionStorage.drozq_lead_just_submitted = "1"` and `sessionStorage.drozq_lead_mode = "<sell|buy|sellandbuy>"` immediately before redirecting to `/thank-you/?ref=funnel`. The thank-you page's inline script reads + clears those flags, pushes a `lead_confirmed` dataLayer event with `funnel_mode` metadata, and strips `?ref=funnel` from the URL via `history.replaceState`.

This means:
- **Real funnel submit** → `lead_confirmed` fires once.
- **Direct visit / refresh / bookmark** → no flag → no fire.
- **Tab closed and reopened to /thank-you/** → sessionStorage gone → no fire.

**Outstanding GTM action item for Joshua**: The GA4 `generate_lead` trigger in GTM is still set to "Page View on /thank-you/", which fires on every visit. To stop double-counting, change it to "Custom Event = `lead_confirmed`" and turn off the old pageview trigger in the same GTM publish. Until that lands, conversions will be inflated by direct/bookmark/refresh visits.

### PostHog funnel drop-off events

The homepage funnel JS dual-fires every transition through a `track(event, props)` helper that calls both `window.posthog.capture(event, props)` and `dataLayer.push({event, ...props})`. Both calls are null-safe so missing tracking never breaks the funnel.

| Event | When | Properties |
|---|---|---|
| `funnel_open` | Funnel overlay opens | `mode`, `prefill_provided`, `gclid` |
| `funnel_step_advance` | `showStep(n)` with `n > prev` | `mode`, `from_step`, `to_step`, `total_steps` |
| `funnel_back` | `showStep(n)` with `n < prev` | `mode`, `from_step`, `to_step` |
| `funnel_option_selected` | Auto-advance option click | `mode`, `step`, `value` |
| `funnel_submit_attempt` | Validation passes, fetch starts | `mode` |
| `funnel_submit_success` | `/api/lead` returns ok, before redirect | `mode` |
| `funnel_submit_error` | API non-ok or fetch rejects | `mode`, `error_kind` (server / server_parse / network) |

PostHog funnel viz: chain `funnel_open` → `funnel_step_advance(to_step=2)` → `… =3` → … → `funnel_submit_success`, breakdown by `mode`.

### Tracking architecture quick reference

| Concern | Where it lives |
|---|---|
| GTM head + body noscript | Every HTML page (homepage included) |
| PostHog (recorder + capture) | Loaded by GTM custom HTML tag, served from t.drozq.com |
| GA4 page_view | Auto-fired by GTM container on every page |
| GA4 generate_lead | Currently fires on /thank-you/ pageview; should fire on `lead_confirmed` event (GTM update pending) |
| Google Ads conversion | Imports `generate_lead` from GA4 (no AW-* tags on site) |
| gclid capture | Page-load IIFE in homepage `<script>`, sessionStorage + 90-day cookie |
| Funnel drop-off events | Homepage funnel IIFE via `track()` helper, dual-fires PostHog + dataLayer |
| `lead_confirmed` push | Inline script at end of `/thank-you/index.html` |

## Cloudflare Pages Functions

Cloudflare Pages auto-deploys functions from `/functions/`. Two endpoints currently exist:

### `/functions/api/lead.js`

Form submission handler. Accepts `application/x-www-form-urlencoded` or `multipart/form-data`. Honeypot field is `company_website` — non-empty value silently 200s without sending the email.

Required fields: `name`, `email`, `phone`, `intent`, `consent="yes"`. Other fields (gclid, full_address, lat/lng, message, source_page, page_url, submitted_at, plus mode-specific buy_location/buy_timeline/etc.) are optional but forwarded.

Sends a plaintext email to `TO_EMAIL` (env var) from `FROM_EMAIL` via MailChannels. Optionally posts the same fields to `ZAPIER_WEBHOOK_URL` if set.

Required env vars in Cloudflare Pages settings: `TO_EMAIL`, `FROM_EMAIL`, `MAILCHANNELS_API_KEY`. Optional: `ZAPIER_WEBHOOK_URL`.

Returns `{ ok: true }` on success, `{ ok: false, error: "<reason>" }` with appropriate status on failure. The funnel client treats anything other than 200 + ok:true as an error.

### `/functions/api/geo.js`

Returns the visitor's geolocation from Cloudflare's `request.cf` object (Cloudflare populates this automatically from the request IP — no third-party service is called). Response shape:

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

## Geo personalization

On every homepage pageview, JS fetches `/api/geo` and:

1. Replaces every `<input name="location" value="Columbus, OH">` with `"{city}, {regionCode}"`. Only when current value is empty or the literal default — preserves returning-visitor data per the existing `populateLandingInputs` convention.
2. Replaces every visible "Columbus, OH" text node via TreeWalker (hero strip, market-section h2). Skips SCRIPT/STYLE/IFRAME descendants.
3. Updates `.funnel-city` / `.funnel-buy-city` placeholder spans inside the funnel overlay so step copy reads "buying in Irvine" instead of "Southern California" once detected.

The Move-hosted Columbus market-trends iframe (`realtorqa.upnest.com/market-trends`) is **not** rewritten — it's deferred to the broader cleanup.

If `/api/geo` 500s or returns empty, all defaults remain.

## Form integrity (conversion-critical)

Forms are the primary conversion mechanism of the site. Breaking them is the single worst thing that can happen, and because the error mode is silent (the form appears to work but no data flows), it can go undetected for days.

For ANY page with a form (homepage, /contact/, /field-notes/, future landing pages):

- NEVER modify field names, IDs, or data attributes without verifying downstream dependencies in `/functions/api/lead.js` (the MailChannels backend) and any GTM event triggers
- NEVER remove hidden fields (gclid, utm_*, address component parsing, lead_source)
- NEVER remove the Google Maps Places Autocomplete initialization or place_changed event handlers
- ALWAYS preserve form submission → `/thank-you/?ref=funnel` redirect (the `?ref=funnel` is what gates the GA4 generate_lead event after the GTM update)
- ALWAYS preserve `sessionStorage.drozq_lead_just_submitted = "1"` set immediately before the redirect
- ALWAYS preserve the timeline question on the homepage funnel (lead qualification signal)

The homepage funnel in particular carries the bulk of paid traffic conversion. Changes there require extra caution and should be visually inspected on live site within 5 minutes of deploy.

## Forms and integrations

### Homepage funnel (main conversion form)

- Three parallel funnels (Sell / Buy / Sell & Buy) — see "Homepage funnel architecture" above
- Wired to MailChannels via `/functions/api/lead.js`
- Submission redirects to `/thank-you/?ref=funnel` which fires `lead_confirmed` (and via GTM, `generate_lead` in GA4 once Joshua updates the trigger)
- Timeline options vary by funnel:
  - Sell + Sell & Buy: `Right away` / `1 to 3 months` / `4 or more months` / `Already listed`
  - Buy: `Right away` / `1 to 3 months` / `4 or more months` / `Just looking`
- Buying process options (Buy step 4): `Just started` / `Pre-approved, ready to tour` / `Already making offers`
- Phone display on homepage: `(949) 438-5948` (paid-traffic / call-tracking line). Distinct from the brand-mode phone `510-935-5701` used on /contact/, /about/, /thank-you/.

### Contact form (/contact/)

- Wired to MailChannels via `/functions/api/lead.js`
- Includes a Google Maps Places Autocomplete integration on the address field
- Hidden fields capture parsed address components (street, city, state, zip) for CRM routing
- Critical: Never modify the address input's id, name, or data attributes if referenced by autocomplete initialization
- Critical: Never remove the Google Maps API script tag or place_changed event handlers

### Field Notes subscribe form (/field-notes/)

- Wired to the same `/functions/api/lead.js` setup
- Lead source should be tagged distinctly via `source_page` (e.g., `field-notes-subscribe`) to distinguish from contact form leads
- Reuse existing success/error message patterns from other forms

## Favicon

Modern pattern, used on /thank-you/ and now the homepage:

```html
<link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="Drozq">
<link rel="manifest" href="/site.webmanifest">
```

Files at the repo root (all exist): `favicon-96x96.png`, `favicon.svg`, `favicon.ico`, `favicon.png` (legacy fallback), `apple-touch-icon.png`, `site.webmanifest`. Do not modify, rename, or remove these references. Do not use absolute URLs with spaces in filenames (this was an old pattern that broke the favicon in Google Ads SERP results).

An orphan file at `/media/icons/Joshua Guerrero Favicon.png` may exist on disk. It's not referenced anywhere. Leave it alone.

## Deployment

This site auto-deploys to production via Cloudflare Pages on every push to main. There is no staging environment, no manual deploy step.

Implications:

- Pushing to main = live in 30-60 seconds (sometimes 60-120s for function updates)
- Broken changes affect real users (and paid traffic) immediately
- Rollback is fast: `git revert [commit-hash] && git push`

When paid ad campaigns are actively running, high-risk changes (hero rewrites, funnel restructures, navigation changes, tracking modifications) should be:

- Committed with clear, descriptive messages
- Verified on the live site immediately after deploy (Playwright is the standard verification path used in this repo)
- Checked for JS errors in the browser console
- Ready to revert if anything breaks

Per the auto-commit instruction at the top of this file, commit and push directly to main. Do not create feature branches unless explicitly requested.

## Realtor.com clone state (homepage)

The homepage (/index.html) is structurally still a clone of sell.realtor.com that is being incrementally cleaned up. Knowing what's been done vs. what's deferred matters for understanding the current state of the file.

### Done (do not redo)

- All external `<a href="http(s)://…">` redirected to `#top` so paid clicks don't leak off-site (excludes `tel:`, `mailto:`, relative paths, and the funnel's internal `href="#"` back buttons)
- Phone numbers replaced: `tel:9494385948` / display `(949) 438-5948` (was UpNest's 800-419-0261 in header and 800-692-5010 in footer)
- Move Inc tracking pixels destroyed: Facebook pixel `754678604575607`, DoubleClick advertiser `10291144` (3 iframes), Bing UET `25046895`, Adobe/Everest `5154` (2 imgs + 1 iframe + cm.everesttech.net), `<meta property="fb:app_id" content="390296427710609">`
- GTM-KVV3R96P installed (head + body noscript)
- Drozq SEO/social meta installed (title, description, canonical, og:*, twitter:*, favicons → all drozq.com)
- Drozq social URLs in footer: Facebook → `facebook.com/Drozq/`, Instagram → `instagram.com/drozq/`, YouTube → `youtube.com/@drozq` (Twitter stays `#top` — no drozq Twitter)
- Hero tabs (Sell / Buy / Sell & Buy) wired with switcher JS + lift styling
- Mid-page "I'm selling / I'm buying" tabs wired (added missing `<div id="buyTab">` panel; `wireTabs` toggles `data-selected` for Panda CSS)
- FAQ accordion wired (delegated click handler, +/- icon toggle via SVG path split)
- Three-funnel system built (Sell / Buy / Sell & Buy) replacing the single funnel
- Geo autofill on page load (replaces "Columbus, OH" with detected city)
- Funnel drop-off PostHog events wired
- gclid pushed to dataLayer on page load
- `generate_lead` gated via sessionStorage flag + `?ref=funnel` redirect

### Deferred (in REALTOR_CLEANUP_AUDIT.md)

The full backlog lives in `REALTOR_CLEANUP_AUDIT.md` (untracked, repo root). Highlights still pending:

- Wrong DRE license still showing in footer: `California BRE #01928572` (UpNest's). Should be `California DRE #02267255` (Joshua's).
- Wrong jurisdiction: `Indiana PLA RC51800184` in footer. Drozq is CA-only.
- 5 fake agent profile cards near top of body
- 5 fake out-of-state testimonials (Avondale AZ, Colts Neck NJ, Coral Springs FL, etc.) and "4.8 Out of 5" star aggregate
- Move-hosted illustration imagery (`lt6p.com/re/img/buysell/...`)
- The Columbus market-trends iframe (`realtorqa.upnest.com/market-trends/...?slug_id=Columbus_OH&lat=40.1113&lon=-82.9717`)
- Move-hosted `@font-face` declarations (Roboto + Galano Grotesque from `static.rdc.moveaws.com/fonts/...`) inside the inline `<style>` block
- Award badges in footer (Inc 5000, Deloitte Fast 500, goo.gl Google reviews redirect — UpNest-only, no drozq equivalents) — currently `#top` placeholders
- App store badges (iTunes UpNest agent app, Play Store UpNest agent app) — currently `#top` placeholders

When asked to "clean up the homepage," confirm which item(s) before proceeding. The audit document is the source of truth.

## Content and voice principles

### Voice

The site speaks in a confident, direct, slightly vulnerable first-person voice. "I" not "we." Joshua Guerrero is a solo agent, and the writing should reflect that. The tone is:

- Honest about uncomfortable truths (commission, being a newer agent, anonymizing clients)
- Specific over generic (real numbers, real outcomes, named partners)
- Measured, not hyperbolic
- Sparse, not crowded

### Brand values (echo throughout copy, never name explicitly)

- **Competitive Greatness**: willingness to do what average agents won't
- **Unimpeachable Character**: would rather lose a commission than lose trust
- **Speed is King**: deals die in the silence between messages

These values should leak through every section of every page without being heavy-handed. If a value is named explicitly, it's only on /about/ in the dedicated values block.

### What to avoid in copy

- Generic real estate platitudes ("I'm passionate about helping families find their dream home")
- SEO-style filler ("how to sell my house fast in [city]")
- Stock testimonial-page language ("5-star rated," "trusted advisor")
- Hyperbolic claims that can't be backed up
- Star ratings or platform-aggregated reviews (these belong nowhere on the site, the case files do this work better)
- Surface-level "AI" and "automation" framing in customer-facing copy. The leverage Joshua has is real, but the framing is systems, discipline, and transparency, not "I use software to do this." Technical posts in /field-notes/ can discuss tooling when directly relevant to readers, but promotional and marketing copy should lead with systems thinking, not tech-stack name-dropping.

### Copy patterns to use

When writing copy, prefer these concrete patterns observed in existing strong pages:

- Specific dollar amounts ("$23,250 in seller credit negotiated," not "significant savings")
- Specific timelines ("7 days to MLS," not "quick turnaround")
- Specific neighborhoods named ("Turtle Rock," "Woodbridge," "Northwood," not "Irvine neighborhoods")
- "So far" framing when owning newness ("$43,250 total client savings, so far," not "extensive savings")
- First-person honesty about constraints ("I'm not from here, which is exactly why I work harder than the agents who are," not "proud to serve Irvine")
- Case file numbering ("CASE FILE 001") for implied accumulation
- Anti-claims (things YOU don't do) as differentiators
- "What you do vs. what I do" split structure for effort communication

### Formatting principles

- Short paragraphs (3 to 5 sentences max in body copy)
- Generous whitespace
- Numbered or bulleted lists only when they genuinely improve scannability
- Pull quotes and stat callouts for emphasis, not bold-everywhere

## Copy framework: Value Equation (for conversion pages)

All conversion-page copy (homepage, future landing pages) should optimize the four terms of the Value Equation:

- **Dream Outcome (↑):** specific outcome states, not generic promises. Examples: "sold at X% over neighborhood median," "sold in under 45 days," dollar amounts earned or saved.
- **Perceived Likelihood (↑):** case files, specific market data, systems over experience, credentials. Anti-claims (things YOU don't do) are powerful here.
- **Time Delay (↓):** response time commitments, list-to-MLS speed, step-by-step timelines with numbers.
- **Effort and Sacrifice (↓):** explicit "I handle X, you handle Y" structure, privacy protections, removing decisions from the seller.

When writing new conversion copy, name which term(s) the copy is strengthening. If copy doesn't clearly pull at least one of these levers, it's probably filler.

The Effort and Sacrifice lever is the most underdeveloped in current copy and the single biggest opportunity for differentiation. Most competing agents compete on Dream Outcome and Perceived Likelihood. Few commit to reducing the seller's actual workload.

## Audience archetypes

### Sellers (primary)

The site speaks to Irvine homeowners considering selling. Under that umbrella:

- **Strategic move-up / move-down** (primary): dual-income, 5 to 15 years in home, data-oriented
- **Life-event forced sellers** (divorce, relocation, medical, bankruptcy): value privacy and discretion over speed
- **Inherited-property heirs** (probate): value empathy, coordination with attorneys and siblings
- **Long-term cashing out** (retirement, downsizing): value capital gains awareness and patience
- **Investor / rental owners**: value 1031 experience and tenant-occupied listing expertise

### Buyers (secondary)

The Buy funnel and homepage Buy tab serve buyers. Archetypes:

- **First-time buyers**: value patience, education, financing guidance
- **Move-up buyers** (often the same person as the strategic-move-up seller): often combined into the Sell & Buy funnel
- **Investors / 1031 exchange buyers**: value market knowledge, deal flow access
- **Out-of-area / relocation buyers**: value local-expert framing

Copy should include specific-situation acknowledgments ("Navigating probate? Divorce? Investment property with tenants? Out-of-area relocation?") without dedicating entire pages to each. One-sentence callouts, not sections. The goal is for each archetype to feel seen without fragmenting the copy.

## Site architecture

### Page inventory

- /index.html (home — paid-traffic 3-funnel)
- /about/index.html
- /testimonials/index.html (case files index)
- /testimonials/001-long-beach-firefighter/index.html (Case File 001)
- /testimonials/002-corona-analyst/index.html (Case File 002)
- /testimonials/00X-slug/index.html (future case files)
- /faq/index.html
- /contact/index.html
- /field-notes/index.html (replaces former /blog/)
- /field-notes/00X-slug/index.html (future field notes posts)
- /market-insights/index.html
- /meet-the-team/index.html
- /the-process/index.html (also reachable as /process/)
- /where-we-help/index.html
- /privacy/index.html (privacy policy)
- /thank-you/index.html
- /california/index.html, /los-angeles/index.html (regional landing pages)

### Cloudflare Pages Functions

- /functions/api/lead.js — form submissions → MailChannels (+ optional Zapier)
- /functions/api/geo.js — visitor geolocation from `request.cf`

### URL conventions

- All directories use trailing slashes (/about/ not /about)
- Numbered content uses zero-padded slugs (001-long-beach-firefighter, not 1-long-beach)
- Slugs are descriptive and SEO-friendly (location and archetype, not generic names)

### Cross-linking patterns

Pages cross-link in a deliberate web, not a hierarchy. Standard cross-link patterns:

- /about/ → links to /testimonials/ (the proof)
- /testimonials/ → individual case files link back to /testimonials/ (the index)
- Each case file → links to neighboring case files
- /field-notes/ → links to /testimonials/
- /market-insights/ → links to /field-notes/ and /contact/
- /meet-the-team/ → links to /testimonials/ and /contact/
- /contact/ → links to /testimonials/ for proof
- Every brand-mode page → has a primary CTA linking to /contact/ or the booking flow

The homepage doesn't follow brand-mode cross-linking — its CTAs all open the funnel, and most external `<a>` are neutralized to `#top` (paid traffic stays on page).

## Recurring structural patterns

### The "Case File" framing

The series naming convention applies to multiple content types:

- **Case Files**: CASE FILE 001, CASE FILE 002, etc. (testimonials)
- **Field Notes**: NOTE 001, NOTE 002, etc. (blog posts)
- **Counties**: COUNTY 01, COUNTY 02, etc. (market insights)
- **Layers**: LAYER 01, LAYER 02, LAYER 03 (meet the team)
- **Categories**: CATEGORY 01, etc. (FAQ)

This numbering creates a sense of intentional series and accumulation.

### "Coming soon" placeholder pattern

When a content series has fewer items than its target structure (e.g., only 2 case files but the grid wants 3), add a "Coming soon" placeholder card with:

- Same dimensions as real cards
- Dashed border instead of solid
- Reduced opacity (around 0.6 to 0.7)
- Non-clickable
- Copy that suggests an active pipeline (e.g., "Currently in escrow / Details coming soon")

### Aggregate stats pattern

The aggregate stats strip on /testimonials/ is a recurring pattern. It appears on:

- /testimonials/ (total client savings, homes closed, etc.)
- /about/ (volume closed, homes sold, units per month)

When adding new stat strips, match the visual treatment exactly. Wrap stat values in `<!-- UPDATE -->` HTML comments so they're easy to update manually as numbers grow.

### Stat dashboard pattern

Each Case File and the Market Insights county sections use a stat dashboard with:

- A hero stat (the largest, most important number)
- A grid of secondary stats (3 columns desktop, 1 column mobile)
- Animated count-up on scroll using IntersectionObserver

### Section label + headline + body pattern

Most brand-mode sections follow this rhythm:

- Small uppercase letter-spaced label
- Large bold headline
- Body copy in 1.125rem to 1.25rem with comfortable line-height

### CTA pattern

Every brand-mode page ends with a "Book a 15-minute call" CTA. This is the universal site CTA. Variants of the surrounding copy are encouraged, but the button text and destination (/contact/) should remain consistent.

The homepage uses the funnel as its primary CTA across multiple form instances; the universal "Book a 15-minute call" CTA does not currently appear there (the entire page is one big CTA).

## SEO and metadata standards

Every page must have:

- A unique `<title>` tag (50 to 60 characters, includes "Joshua Guerrero" or "Drozq" as brand suffix)
- A unique `<meta name="description">` (140 to 160 characters)
- A `<link rel="canonical">` pointing to the absolute URL on drozq.com (NOT to a third-party site, even when a page is structurally based on one — see realtor.com clone notes)
- Open Graph tags (og:title, og:description, og:image, og:url, og:type, og:site_name)
- Twitter Card tags (twitter:card, twitter:title, twitter:description, twitter:image)
- Appropriate JSON-LD structured data (RealEstateAgent, Person, Article, FAQPage, Blog, BreadcrumbList as relevant)
- All `<img>` tags with descriptive alt attributes
- Non-hero images with `loading="lazy"`
- Hero images with `fetchpriority="high"`

The homepage carries the RealEstateAgent Organization schema (still pending — flagged in the cleanup audit). The About page carries Person schema. Each case file carries Article and BreadcrumbList schema. The FAQ page carries FAQPage schema with all questions and answers mirrored.

`/thank-you/` is `noindex,nofollow` by design. Other pages should be indexable.

Future conversion-optimized landing pages (if built) should include `<meta name="robots" content="noindex">` to prevent organic indexing, since their purpose is paid traffic only.

## Update workflow conventions

For pages that will be updated frequently (especially /market-insights/):

- Wrap every updatable value in clearly-named HTML comments: `<!-- UPDATE: [description] -->` and `<!-- END UPDATE -->`
- Include an update guide comment block at the top of the file explaining how to update values
- Structure the markup so updating one value doesn't require editing structural elements

## What this site is NOT

A few explicit anti-patterns to avoid:

- It is not a generic agent template site. Every page should have a point of view and a deliberate angle.
- It is not a volume-first lead funnel. Conversion optimization on the homepage and landing pages is welcome and intentional, but quality-of-lead matters more than quantity. The timeline qualification field on the funnel is specifically designed to surface intent, not just volume.
- It is not a place for star ratings, review screenshots, or platform-aggregated social proof. The case files do this work, more credibly.
- It is not a place to mention AI, automation, or technology tooling in promotional copy. The leverage Joshua has is real, but the framing is "systems and discipline," not "I use software to do this." Technical discussions in /field-notes/ that serve the reader are fine.
- It is not a content farm. Field Notes posts and Case Files are published when there's something worth saying, not on a schedule.
- It is not a place for fake team members. Joshua is a solo agent. Partners are named by role only (brokerage, transaction coordinator, photographer, lenders, inspectors, title and escrow), not by invented personal names with stock photos.
- It is not a site where inline script tags, `gtag()` calls, or third-party pixels should appear outside the GTM container. All third-party tracking goes through GTM.
- It is not a site that should collect sensitive data in forms beyond what an agent needs to provide a valuation (address, name, contact info, timeline). No SSN, no income, no financials.

## Reference docs

- `REALTOR_CLEANUP_AUDIT.md` (untracked, repo root) — the comprehensive list of remaining realtor.com clone leftovers on the homepage. Source of truth when "clean up the homepage" lands as a task.
- `C:\Users\guerr\.claude\projects\C--Users-guerr-Documents-drozq-com\memory\` — auto-memory directory for cross-session context (preferences, project state, references). Read on every session start; updated when stable patterns emerge.

## When in doubt

If a request is ambiguous, default to:

- The pattern already established on /testimonials/, /about/, or /faq/ (brand-mode) or the homepage funnel IIFE (conversion-mode)
- The most concise, confident, sparse interpretation
- Asking for clarification rather than guessing on brand voice

If a change would affect the brand-mode header, footer, or foundational `<style>` block, stop and confirm before proceeding. These are protected zones.

If a request involves the homepage funnel, the contact form, or the Google Maps autocomplete, stop and audit the existing implementation before modifying anything. Breaking these is the easiest way to silently degrade the most important conversion point on the site.

If a request involves "cleaning up" tracking scripts, GTM tags, gtag calls, or pixel installations, stop and confirm specifically which elements to touch. Assume nothing is dead code without verification. Cross-reference against `REALTOR_CLEANUP_AUDIT.md` if it's the homepage.
