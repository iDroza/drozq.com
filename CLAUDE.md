# Claude Code Instructions

*Last reviewed: May 22, 2026*

## The standard

Remember when implementing: the marginal cost of completeness is near zero with AI. Do the whole thing. Do it right. Do it with tests. Do it with documentation. Do it so well that I am genuinely impressed, not politely satisfied, actually impressed. Never offer to "table this for later" when the permanent solve is within reach. Never leave a dangling thread when tying it off takes five more minutes. Never present a workaround when the real fix exists. The standard isn't "good enough", it's "holy shit, that's done." Search before building. Test before shipping. Ship the complete thing. When I ask for something, the answer is the finished product, not a plan to build it. Time is not an excuse. Fatigue is not an excuse. Complexity is not an excuse. Boil the ocean.

## Auto-commit

Always commit and push changes to main after completing each task without asking. Ship fast. Rollback is always available via `git revert [hash] && git push`.

When making changes to high-risk files (homepage hero, the funnel, tracking scripts, files containing the GTM container, any registered page in `funnels.json`), include a clear, descriptive commit message so rollbacks can be surgical if needed.

## About this project

drozq.com is the site for Joshua Guerrero, a solo real estate agent under Real Brokerage based in Irvine, California. The site is built to convert paid traffic into qualified leads. **Every page captures leads. The homepage is the template for the entire site.**

The homepage (originally a clone of sell.realtor.com / UpNest's agent-locator pattern) is the canonical look, feel, and behavior. Visual style, hero structure, mid-page tabs, FAQ accordion, footer, and funnel are all reusable as scaffolding for new pages. When asked to build a new page, the default is "homepage with a different angle," not "different design."

Legacy brand-mode pages (`/about/`, `/testimonials/`, `/faq/`, `/contact/`, `/field-notes/`, `/market-insights/`, `/meet-the-team/`, `/the-process/`, `/where-we-help/`) still exist and still capture leads (their CTAs route to `/contact/` or the funnel), but they are not the template. Do not propagate their styling, voice, or structure into new work. They will be migrated to homepage-style over time.

## Core operating principles

1. **Every page captures leads.** No exceptions. New pages either embed the inline funnel (the default) or carry a CTA that opens it. Removing or breaking the lead path is a critical regression.

2. **The homepage is the template.** New pages start by copying index.html scaffolding (head, hero with funnel tabs, mid-page tabs, FAQ accordion, footer) and then swapping page-specific copy. They do not start from a brand-mode page.

3. **The funnel is inlined, not redirected.** Redirects cost conversions. Every page that needs the funnel carries its own physical copy of the HTML and JS. Sync is managed by the funnel registry (see below); never hand-edit a synced page's funnel block.

4. **Tracking is sacred.** GTM-KVV3R96P + GA4 + PostHog (via t.drozq.com proxy) + Google Maps Places + gclid capture + the `lead_confirmed` event on /thank-you/. Do not modify, remove, or "clean up" any tracking element without explicit instruction.

5. **Form integrity is sacred.** All forms POST to `/api/lead`, redirect to `/thank-you/?ref=funnel`, and set `sessionStorage.drozq_lead_just_submitted = "1"` immediately before the redirect. Breaking the redirect or the flag silently destroys conversion measurement.

6. **Mobile-first, always.** Render intentionally at 375px, 768px, 1440px. Base styles for mobile, enhance with min-width media queries.

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

Cloudflare Pages auto-deploys functions from `/functions/`. Two endpoints currently exist:

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

### Deferred

Tracked in `REALTOR_CLEANUP_AUDIT.md` (untracked, repo root). Highlights still pending:

- 5 fake agent profile cards near top of body.
- 5 fake out-of-state testimonials (Avondale AZ, Colts Neck NJ, Coral Springs FL, etc.).
- Move-hosted illustration imagery (`lt6p.com/re/img/buysell/...`).
- Move-hosted `@font-face` declarations (Roboto + Galano Grotesque from `static.rdc.moveaws.com/fonts/...`) inside the inline `<style>` block.
- Award badges in footer placeholders (Inc 5000, Deloitte Fast 500 — already neutralized to `#top`).
- App store badges (UpNest agent app links — already neutralized to `#top`).

When asked to "clean up the homepage," confirm which item(s) before proceeding.

## Reference docs

- **`TEMPLATE.md` (repo root): REQUIRED READING before building or editing any page.** Canonical spec for tokens, header, hero, sections, mid-page tabs, FAQ, footer, funnel overlay, all behaviors, all forms. The homepage at `/index.html` is the live reference; TEMPLATE.md explains what is in it and why. Treat as gospel. Do not deviate without explicit confirmation from Joshua.
- `REALTOR_CLEANUP_AUDIT.md` (repo root): the comprehensive list of remaining realtor.com clone leftovers. Source of truth when "clean up the homepage" lands as a task.
- `funnels.json` (repo root): funnel sync registry. List of pages carrying the inline funnel + last sync timestamps.
- `scripts/sync_funnels.py`: the funnel propagation tool.
- `notes/posthog/`: running log of funnel observations from PostHog. Read `lessons.md` first, then the most recent entries in `funnel-log.md`, before touching anything that could move funnel drop-off (hero copy, tab structure, step ordering, validation, mobile layout). Append a new dated entry after any session that queried PostHog. See `notes/posthog/README.md` for the convention.
- `notes/ads/`: paid campaign strategy docs (`distressed-sellers-strategy.md`, `sellers-max-intent-campaign.md`). Read before touching the campaigns or campaign landing pages.
- `.mcp.json` (repo root): wires up the PostHog remote MCP server. Activation requires a `POSTHOG_API_KEY` env var. Run `/mcp` inside Claude Code to confirm the server is connected.
- `C:\Users\guerr\.claude\projects\C--Users-guerr-Documents-drozq-com\memory\`: auto-memory directory for cross-session context. Read on every session start; updated when stable patterns emerge.
- Other audit docs (`AUDIT-INDEX-2026-04-26.md`, `SEO-AUDIT-INDEX-2026-04-26.md`, `FAVICON_AUDIT.md`, `SPEED-AUDIT.md`, `CHANGES.md`): legacy / partial overlap with the docs above. Will be consolidated in a future pass.

## When in doubt

- Building or editing any page: read `TEMPLATE.md` first. It is the contract.
- Ambiguous styling or structure on a new page: default to the homepage pattern (per `TEMPLATE.md`).
- Ambiguous voice or copy direction: confident, first-person, specific, sparse. No platitudes, no SEO filler, no star ratings.
- Anything that touches the funnel, tracking, forms, or `/api/lead`: stop and audit before modifying.
- Anything that touches a registered page's funnel block: edit `/index.html` and re-sync; never hand-edit.
- Anything labeled "DO NOT MODIFY": ask.
