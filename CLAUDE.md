# Claude Code Instructions

*Last reviewed: May 23, 2026*

## The standard

Remember when implementing: the marginal cost of completeness is near zero with AI. Do the whole thing. Do it right. Do it with tests. Do it with documentation. Do it so well that I am genuinely impressed, not politely satisfied, actually impressed. Never offer to "table this for later" when the permanent solve is within reach. Never leave a dangling thread when tying it off takes five more minutes. Never present a workaround when the real fix exists. The standard isn't "good enough", it's "holy shit, that's done." Search before building. Test before shipping. Ship the complete thing. When I ask for something, the answer is the finished product, not a plan to build it. Time is not an excuse. Fatigue is not an excuse. Complexity is not an excuse. Boil the ocean.

## Auto-commit

Always commit and push changes to main after completing each task without asking. Ship fast. Rollback is always available via `git revert [hash] && git push`.

**Everything goes live instantly. There is no staging, no batching, no holding.** Every edit auto-deploys to production in 30-60 seconds the moment it lands on main. So the moment a change is made, it ships. Do not sit on a finished edit waiting for a follow-up decision, a sibling change, or my approval. If one piece of a larger change is done and another is still being decided (for example, a headline is set but the subhead is still being chosen), push the finished piece NOW and ship the rest when it's decided. Work-in-progress lives on main and gets iterated live, never parked in an un-pushed working tree. "I'll wait until you pick X before pushing" is a banned behavior: ship what's done, iterate live, roll back if needed. The only reason to ever hold a push is an explicit "don't push this yet" from me.

When making changes to high-risk files (homepage hero, the funnel, tracking scripts, files containing the GTM container, any registered page in `funnels.json`), include a clear, descriptive commit message so rollbacks can be surgical if needed.

## About this project

drozq.com is the site for Joshua Guerrero, a solo real estate agent under Real Brokerage based in Irvine, California. The site is built to convert paid traffic into qualified leads. **Every page captures leads. The homepage is the template for the entire site.**

The homepage (originally a clone of sell.realtor.com / UpNest's agent-locator pattern) is the canonical look, feel, and behavior, and its components (header, funnel, FAQ accordion, footer, section rhythm) remain the shared scaffolding. **But since the 2026-07-20 redesign, "new page = homepage with a different angle" is dead.** Joshua's ruling: the homepage sells hard; every other page serves its function first (resource, trust, or utility) and captures leads through the persistent layer (sticky mobile CTA, header phone, closing CTA, the synced funnel one CTA away), not through a cloned splash pill. New pages pick an archetype from TEMPLATE.md §4 ("The page-archetype system"): only true conversion landers get the photo + tabs + pill splash.

Every page on the site is now on the homepage template. The historical distressed-sellers paid landing at `/relief/` was deleted on 2026-05-26 (see `BACKLOG.md` for the rebuild task). The strategy playbook for that audience still lives in `notes/ads/distressed-sellers-strategy.md` for when the campaign relaunches.

Pages on the homepage template: `/`, `/404.html` (the site-wide not-found page: root-level file, served by Cloudflare Pages with a real 404 status for every missing path, noindex, NOT in sitemap.xml), `/about/`, `/buyers/` (+ `/sellers/`: the two header-nav hub pages, resource archetype, added 2026-07-21), `/california/`, `/contact/`, `/cost-to-sell/` (the AI-search/organic answer page for "what does it cost to sell in Orange County": quick-answer block, 2026 line-item table, the $1,200,000 worked ledger mirroring the /sellers/ calculator formulas exactly ($726,930 net), capital gains + Prop 19 cards, cost FAQ accordion + matching FAQPage JSON-LD; scaffolded from /faq/, added 2026-07-22, not in the header nav by design), `/divorce-sale/` (AI-answer page #3, scaffolded from /inherited-house/: community property + ATROs + the $500k exclusion clock, the three exits, neutral-agent five steps, FAQ + FAQPage JSON-LD; added 2026-07-22, not in the header nav; all situation pages are linked from /sellers/' "Specific situations, handled." hub band: Inherited, Divorce, Timing, As-is (`/sell-as-is/`, AI-answer #5: as-is vs disclosure law, fix/credit/price framework, repairs-that-pay table), Rentals (`/sell-with-tenants/`, AI-answer #6: lease survives the sale, AB 1482 + the SFR exemption, cash for keys, depreciation recapture, the 1031 clock; its xr value-card carries the investor-read copy), and Pre-foreclosure (`/pre-foreclosure/`, AI-answer #7, the ORGANIC side of `notes/ads/distressed-sellers-strategy.md`: the 120/90/20 nonjudicial timeline with "you can still" markers, reinstatement to 5 business days, HBOR dual-tracking pause, the NOD-mailbox mechanism + CC 1695 five-day cancel, six exits ranked by what you keep; the future /relief/ paid lander stays a separate noindex build; its short-sale exit card + FAQ link into `/short-sale/`, AI-answer #8: the are-you-actually-underwater check with an honest fork back to /pre-foreclosure/, CCP 580e's no-deficiency release incl. consenting juniors, the nonrecourse no-COD-income tax treatment, the 60-120 day approval run at zero seller cost, and the 2-4yr vs 7yr buy-again clocks)), `/faq/`, `/inherited-house/` (AI-answer page #2, same pattern scaffolded from /cost-to-sell/: probate vs trust path cards, step-up in basis + Prop 19 reassessment, the five-step estate sale, heir FAQ + FAQPage JSON-LD; added 2026-07-22, not in the header nav), `/sell-now-or-wait/` (AI-answer page #4, the timing framework: LIVE-WIRED to `/api/rates` (`rate30y`) + `/api/prices` (`supplyMonths`) via `#snw-r30`/`#snw-moi` spans with graceful static fallbacks; the never-indexed $250k/$500k gains cap, the cost-of-waiting table, honest now-vs-wait columns; added 2026-07-22, linked from /sellers/' situations band as the Timing card), `/field-notes/`, `/los-angeles/`, `/market-insights/`, `/meet-the-team/`, `/prices/`, `/privacy/`, `/process/` (renamed from legacy `/the-process/`), `/rates/`, `/sold/` (the sold board: image-led closed-deal cards + aggregate stats, added 2026-07-22, giem-19 strip), `/terms/`, `/testimonials/` (+ /001-long-beach-firefighter/ + /002-corona-analyst/), `/thank-you/`, `/value/`, `/where-we-help/`. Root `llms.txt` (added 2026-07-22) is the AI-crawler index of the site's citable resources; update it when a major resource page ships. If the /sellers/ calculator formulas or defaults ever change, update /cost-to-sell/'s table + ledger in the same commit (they must always agree). The source of truth for "is this page using the synced funnel" is `funnels.json#pages`. The source of truth for "is this page on the homepage template" is the presence of `migrate_<slug>.py` in `scripts/` and the absence of brand-mode classes (`cf-narrow`, `lead-modal`, `mt-hero`, `about-hero`, etc.) in the rendered HTML.

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
- Mid-page tabs section (the "My Home's Condition is..." switcher): optional but encouraged. Two `[role="tab"]` panels wired by the generic `wireTabs()`; the homepage runs Move-in ready (`sellTabBtn` → `sellTab`) and Needs work (`needsTabBtn` → `needsTab`), and BOTH open the Sell funnel (neither id contains `buy`). Retitle per page, but keep `buy`/`sellbuy` out of any panel you want to stay on Sell.
- FAQ accordion: optional, page-specific questions.
- Footer: the minimal conversion-page footer (brand logo, identity line, DRE, office address, phone, social, Privacy/Terms, copyright). Do not import the heavy legacy brand-mode footer.
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
- Editing `/index.html` is script-only for the minified `<body>` line: Python/PowerShell with `assert data.count(old) == N` count-guards + BOM preservation, never a blind Read/Edit (the line is ~97KB; the tools choke). Funnel CSS goes INSIDE the `DROZQ_FUNNEL_HTML` markers (it syncs). Verify via `window.openFunnel(addr, mode)` on a local server + an empty-field submit to confirm validation fires, never a real submit. Full recipe: `TEMPLATE.md` §9 "Working on the funnel safely."
- Never split the funnel HTML and JS into separate sources. They co-evolve.
- The funnel JS includes the Maps race guard, the Maps API loader, the gclid capture, `detectFunnelMode`, `openFunnel`, `attachSubmitHandler`, `showStep`, `wireTabs`, geo autofill, FAQ accordion wiring, the sticky mobile CTA bar, and the PostHog `track()` helper. All of this syncs together because it is one logical unit.
- Mobile-nav script and other page-level UI live OUTSIDE the funnel JS markers (mobile nav is a separate `<script>` tag after `DROZQ_FUNNEL_JS_END`). New pages copy that block verbatim from the homepage scaffold but it does not sync.

## Funnel architecture

The homepage funnel is a paid-traffic conversion machine with **three parallel funnels**. The hero tab bar (Sell / Buy / Sell & Buy) selects among all three; the mid-page condition switcher ("My Home's Condition is...") feeds only the Sell funnel (both of its panels):

| Funnel | `data-funnel` | Steps | Final CTA | Submitted intent |
|---|---|---|---|---|
| Sell | `sell` | 3 (2 more captured pre-funnel via the landing form) | "Send My Report" | `Home Valuation` |
| Buy | `buy` | 4 (1 pre-funnel) | "Send My Report" | `Home Purchase` |
| Sell & Buy | `sellandbuy` | 4 | "Send My Report" | `Home Sale + Purchase` |

Note: the **Final CTA is now identical across modes** (the unified funnel, see below); only the **Submitted intent** stays per-mode for the CRM.

Each step is a `<div class="funnel-step" data-funnel="…" data-step="N">` inside `<section id="funnel-overlay">`. The active funnel is `window.activeFunnel`, set via:

- Hero tab clicks (`tab-sell` / `tab-buy` / `tab-sell-buy`) → swap the visible tabpanel; the panel's Run my Valuation button opens its matching funnel. ("Run my Valuation" is the site-wide landing-CTA label since 2026-06-13 on the homepage, rolled to all template pages 2026-07-14; "See Plan" is the legacy label.)
- Mid-page tab clicks (`sellTabBtn` / `needsTabBtn`) → swap the "My Home's Condition is..." section between the Move-in ready (`sellTab`) and Needs work (`needsTab`) panels; each panel's inner Run my Valuation form opens the **Sell** funnel (neither id contains `buy`, so `detectFunnelMode` resolves both to `sell`).
- Other CTAs in the body (e.g., footer or section forms) default to Sell mode.

`detectFunnelMode(form)` reads the form's `[role="tabpanel"]` ancestor (id + aria-labelledby), lowercases, and substring-matches: `sell-buy` / `sellandbuy` / `sellbuy` → `"sellandbuy"`, then `buy` → `"buy"`, default `"sell"`. Used at landing-CTA click and inside the Places autocomplete `place_changed` callback.

`showStep(n)` filters `.funnel-step` elements by `data-funnel === window.activeFunnel && data-step === String(n)`. `FUNNEL_TOTAL_STEPS = { sell: 3, buy: 4, sellandbuy: 4 }`.

Submit is handled by a single `attachSubmitHandler(buttonId, mode, ids)` factory called three times (one per funnel). It validates email + phone (and name on Buy / Sell & Buy where the contact step is one combined step), builds a mode-specific `FormData`, posts to `/api/lead`, then redirects to `/thank-you/?ref=funnel`.

### The unified value experience (THE STANDARD, 2026-06-13)

Every mode renders the **same** value experience; only the qualifying questions differ. The funnel is a checkout-style split. Full spec + the canonical markup/classes live in `TEMPLATE.md` §9 ("The unified split funnel"); the summary:

- **Layout.** `openFunnel` stamps `data-mode` on `#funnel-step-container`. At >=880px it becomes a centered, symmetric split (max-width 1080, two equal `1fr` white cards on a warm `#efe9e1` backdrop): the value panel (`#funnel-deliverable`) LEFT, `#funnel-form-col` (the active step + the timeline) RIGHT. Below 880px it stacks form-card-first / value-card-below so the form is instantly fillable.
- **One value panel for all modes** (`dv.innerHTML = DELIVERABLE.sell`, not `[mode]`): the instant valuation (true market value, rebuild cost, same-day cash offer to the dollar, comps; framed as "my own valuation model, the same data investors and other buyers use" , proprietary, NEVER "API"/"Rentcast") + a ⚡ "Delivered the instant you hit submit" statement (a bordered line, NOT a button).
- **One value bar for all modes** (`vb.innerHTML = VALUEBAR.sell`): "Your instant home valuation. Free, delivered the moment you finish."
- **Timeline: removed 2026-07-20** with the playbook kill (the graphic carried the six-weeks-guarantee framing).
- **Identical deliverable handoff.** All three submit buttons say "Send My Report"; all three contact steps ask "Where should I send it?" + "What's your full name?". Only the qualifying questions (timeline / budget / location / process) stay per-mode.
- **Everything instant.** Valuebar, panel, badge, every `.funnel-assurance`. Fineprint is the TCPA consent line (call + text, automated/prerecorded-or-artificial-voice disclosure, "at the number provided," "consent is not a condition of any purchase," msg & data rates / reply STOP). Its "Privacy Policy" / "Terms" links open an in-funnel modal (`#drozq-legal-modal`) that fetches `/privacy/` + `/terms/` live and never leaves the funnel. Full spec: `TEMPLATE.md` §9 "TCPA consent fineprint + in-funnel legal modal."
- **Forms untouched** , field names, IDs, handlers, validation, POST, the per-mode `Submitted intent`, and redirect are exactly as before. Only what the visitor sees changed.
- **Instant delivery: WIRED 2026-07-22.** Every sell-side lead now receives the valuation report by email the moment they submit ("both land in your inbox": the instant report now, Joshua's hand-built CMA behind it). Two paths, one renderer (`functions/_lib/valuation_email.js`, branded via `renderEmail`; preview at `/api/email/preview?kind=valuation`): `/api/valuation` emails its own leads on success, and `/api/lead` (intents `Home Valuation` / `Home Sale + Purchase` with a `full_address`) makes an internal compute-only call to `/api/valuation` authenticated with the `x-drozq-internal: EMAIL_SECRET` header (which skips the duplicate lead save) and emails the result. Requires `EMAIL_SECRET` + MailChannels; transactional (no unsubscribe link, no pixel); log markers `VALUATION_REPORT_SENT/FAILED/NO_DATA/FETCH_FAILED`. The funnel X (2026-07-22) also shipped: `#funnel-close-x` in the synced overlay, fires `funnel_close`. The legacy per-mode `VALUEBAR.buy/sellandbuy` + `DELIVERABLE.buy/sellandbuy` + `DV_BODY` + `.funnel-dv-*` CSS are now dead (see `BACKLOG.md`).

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
- **FollowUpBoss Widget Tracker** (`WT-AETGAYMU`): the FollowUpBoss page-load pixel, loaded async from `widgetbe.com/agent`. A direct `<script>` in `<head>`, inserted immediately after the GTM end comment on every page, wrapped in `<!-- begin/end Widget Tracker Code -->` comments. It is NOT orchestrated by GTM and NOT part of the synced funnel JS; it fires `widgetTracker("send","pageview")` on every page including `/thank-you/`. Each page carries its own physical copy (the head is not synced), so new pages inherit it automatically by scaffolding the whole `<head>` from `/index.html`. Re-apply or verify it site-wide with `python scripts/add_fub_pixel.py [--check]` (idempotent, count-guarded, BOM-preserving). FollowUpBoss matches the pageview to a lead's CRM record once that lead's email lands in FUB, giving Joshua per-lead site-activity history.

If asked to "clean up scripts" or "remove unused tags," STOP and confirm which specifically. Direct `AW-*` gtag installations are forbidden.

The form submission flow MUST redirect to `/thank-you/?ref=funnel` on success. The receiving page reads `sessionStorage.drozq_lead_just_submitted` and pushes a `lead_confirmed` event to `dataLayer`. Breaking this redirect or removing the sessionStorage flag silently destroys conversion measurement across the entire paid funnel.

### `lead_confirmed` event (gates GA4 generate_lead)

The funnel sets `sessionStorage.drozq_lead_just_submitted = "1"` and `sessionStorage.drozq_lead_mode = "<sell|buy|sellandbuy>"` immediately before redirecting to `/thank-you/?ref=funnel`. The thank-you page reads + clears those flags, pushes a `lead_confirmed` dataLayer event with `funnel_mode` metadata, and strips `?ref=funnel` from the URL via `history.replaceState`.

This means:
- Real funnel submit → `lead_confirmed` fires once.
- Direct visit / refresh / bookmark → no flag → no fire.
- Tab closed and reopened to /thank-you/ → sessionStorage gone → no fire.

**Conversion trigger (resolved 2026-05-29):** `generate_lead` fires via a GTM "GA4 Event" tag bound to the `lead_confirmed` custom event (container `GTM-KVV3R96P`, GA4 `G-XSP0L11QEY`). It is a GA4 Key event, imported into Google Ads as the conversion. The tag also passes `funnel_mode` (`sell` / `buy` / `sellandbuy`, from the `DLV - funnel_mode` data layer variable) as an event parameter, captured by a GA4 event-scoped custom dimension so conversions can be segmented by funnel. The previous inflated source, a GA4 "Create event" rule that synthesized `generate_lead` from every `page_view` whose `page_location` contained `drozq.com/thank-you`, was deleted. Net: the conversion counts once per real funnel submit, not on refreshes/bookmarks/direct visits. Rollback if ever needed: recreate that GA4 Create-event rule (event_name equals page_view AND page_location contains drozq.com/thank-you).

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
| `funnel_submit_retry` | A transient failure (fetch reject / abort-timeout / 5xx / 429) right before an automatic retry | `mode`, `attempt`, `error_kind` |
| `funnel_submit_error` | All 3 attempts failed: API non-ok, non-JSON, or fetch rejects | `mode`, `error_kind` (server / server_parse / network) |
| `sticky_cta_click` | Sticky mobile CTA bar tapped (fires right before its `funnel_open`) | `mode` (always `sell`) |

The sticky mobile CTA bar itself (JS-injected `#drozq-sticky-cta`, mobile-only, scroll-triggered, skipped on `/thank-you/`) is part of the synced funnel JS, so it ships on every registered page automatically. Spec in `TEMPLATE.md` §10.

### Google One Tap events

Fired by the homepage One Tap block (separate from the funnel; same dual-fire `posthog.capture` + `dataLayer.push` pattern). Only active once a real client ID is set.

| Event | When | Properties |
|---|---|---|
| `one_tap_prompt_requested` | `google.accounts.id.prompt()` is called on load | (none) |
| `one_tap_accepted` | Visitor picks an account; Google returns a credential | `has_email` |
| `one_tap_lead_saved` | `/api/onetap` verified the token and saved the lead | `email_domain` |
| `one_tap_lead_error` | `/api/onetap` returned not-ok or the fetch failed | `email_domain` |

## Cloudflare Pages Functions

Cloudflare Pages auto-deploys functions from `/functions/`. Six endpoints currently exist:

### `/functions/api/lead.js`

Form submission handler. Accepts `application/x-www-form-urlencoded` or `multipart/form-data`. Honeypot field is `company_website`; non-empty value silently 200s without sending the email.

Hard-required fields: `email`, `phone`, `consent="yes"` (the contactable + compliance fields). `name` and `intent` are captured when present but no longer rejected: a missing value falls back to a placeholder instead of a 400, so a client-side name-capture gap can never cost a lead. Other fields (gclid, full_address, lat/lng, message, source_page, page_url, submitted_at, plus mode-specific buy_location/buy_timeline/etc.) are optional but forwarded.

Phone is normalized server-side by `normalizePhone()` (defense in depth behind the client `normalizeUsDigits()`): it drops a leaked `+1` country code, validates NANP, and emits `+1 (XXX) XXX-XXXX` into the email + Zapier payload (plus a `phone_e164` field), so the `+1` is captured on every real lead. Placeholder phones (`0000000000` from One Tap / valuation-view) pass through untouched; normalization never rejects a lead.

Sends a plaintext email to `TO_EMAIL` (env var) from `FROM_EMAIL` via MailChannels. Optionally posts the same fields to `ZAPIER_WEBHOOK_URL` if set, and pushes the lead to FollowUpBoss when `FOLLOWUPBOSS_API_KEY` is set (see below).

**Acceptance is decoupled from delivery (2026-05-31).** Once a lead validates, the handler schedules delivery via `context.waitUntil(deliverLead(...))` and returns `{ ok: true }` immediately, so a slow or unconfigured email channel can never surface to the visitor as "something went wrong" or 500 the request. `deliverLead` fires MailChannels, Zapier, and FollowUpBoss as independent best-effort tasks, each wrapped in an 8s `fetchWithTimeout` with its own error logging; on channel failure it logs (`LEAD_EMAIL_FAILED` / `LEAD_ZAPIER_FAILED` / `LEAD_FUB_FAILED`), and if NO channel is configured it logs the full lead (`LEAD_NOT_DELIVERED`) so it stays recoverable from the Cloudflare function logs. A lead is never silently dropped, and a delivery problem never blocks the conversion.

**FollowUpBoss CRM push (2026-06-15).** When `FOLLOWUPBOSS_API_KEY` is set, `deliverLead` also posts the lead to the FollowUpBoss **Events API** (`POST https://api.followupboss.com/v1/events`, HTTP Basic auth = `btoa(key + ":")`). FUB creates-or-merges the person by email and logs a lead event, so the lead auto-populates the CRM and can trigger FUB action plans / lead routing; the FollowUpBoss Widget Tracker pixel (`WT-AETGAYMU`) already on the site then matches that person's on-site activity to the record. The payload is built in `onRequestPost` as `fubEvent`: `type` maps from intent (seller intents to `Seller Inquiry`, buyer intents to `Property Inquiry`, else `Registration`); `source`/`system` = `Drozq.com`; `tags` = `Drozq Website` plus `Seller`/`Buyer`/`Google One Tap`; `person` carries the name (split into first/last), email, phone (only when `normalizePhone` validates it, so the `0000000000` placeholder is omitted), and address. The valuation-view soft-save (`intent = "Home Valuation View"`, placeholder identity) sets `fubEvent = null` and is NOT sent, keeping the CRM clean. (As of 2026-06-24 the `/value/` page no longer sends this placeholder at all, and `onRequestPost` additionally short-circuits the `"Home Valuation View"` intent to deliver NOTHING (no email/Zapier/FUB), as a backstop so a stale cached page can't ding Joshua with an empty lead.) Best-effort behind `context.waitUntil` + an 8s timeout like every channel; a FUB outage never blocks the conversion. The key lives only in Cloudflare Pages env vars; until it is set, behavior is unchanged. Leads land in Joshua's **personal** FollowUpBoss account (his own CRM for drozq.com), which is separate from the Active Realty shared team FUB. The `FOLLOWUPBOSS_API_KEY` is that personal account's API key.

Required env vars in Cloudflare Pages settings: `TO_EMAIL`, `FROM_EMAIL`, `MAILCHANNELS_API_KEY`. Optional: `ZAPIER_WEBHOOK_URL`, `FOLLOWUPBOSS_API_KEY`.

Returns `{ ok: true }` once the lead is accepted, `{ ok: false, error: "<reason>" }` only on a validation reject (4xx) or an unexpected exception (5xx). The funnel client treats anything other than 200 + ok:true as a failure, but now RETRIES transient failures (network / abort-timeout / 5xx / 429) up to 3 attempts before surfacing the error (per-attempt timeout 20s; see the `funnel_submit_retry` row under "PostHog funnel drop-off events").

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

Proxies the Federal Reserve Economic Data (FRED) API and edge-caches for 1 hour. Returns ~1 year of history per series for sparkline rendering and YoY deltas. **Ten series in two groups.**

- **Macro benchmarks** (Freddie Mac PMMS + Treasury + Fed): `MORTGAGE30US` (30-year fixed, weekly), `MORTGAGE15US` (15-year fixed, weekly), `DGS10` (10-year Treasury yield, daily), `FEDFUNDS` (Federal funds rate, monthly).
- **Rates by loan program** (Optimal Blue Mortgage Market Indices, OBMMI: daily, locked-rate based, hosted on FRED under the same `FRED_API_KEY`): `OBMMIC30YF` (30y conforming / "SC"), `OBMMIJUMBO30YF` (30y jumbo, also the page's stand-in for high balance since OBMMI has **no** dedicated HB index), `OBMMIFHA30YF` (30y FHA), `OBMMIVA30YF` (30y VA), `OBMMIUSDA30YF` (30y USDA), `OBMMIC15YF` (15y conforming).

Per the [[fred-mortgage5us-discontinued]] discipline, recheck a series' latest-observation date before trusting it. All ten confirmed current as of the 2026-05-28 daily read. OBMMI cards carry `provider: "Optimal Blue"`; the macro four carry `provider: null`.

Response shape per series entry:
```
{
  seriesId, label, unit, cadence, provider,   // provider: "Optimal Blue" on OBMMI series, null on macro benchmarks
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

Consumed by `/rates/index.html`. The page ships static skeletons, then hydrates two card grids (inline SVG sparklines + WoW + YoY deltas): the four macro-benchmark cards (`.drozq-rates-grid`), then a six-card "Rates by loan program" section (`.drozq-loans-grid`: conforming/SC, jumbo + high balance, FHA, VA, USDA, 15y conforming). Below those sit an affordability table (5 loan sizes at today's 30-year; on mobile under 768px it collapses from the 4-column scrolling table into stacked per-loan cards, CSS-only via a `@media (max-width:767.98px)` block on `.drozq-aff-table` that hides `thead` and injects the column labels through `td[data-aff-*]::before`, so the seven-figure dollar values never force a horizontal drag, the desktop table is byte-for-byte unchanged) and a mortgage payment calculator (default rate auto-syncs to today's 30y / 15y based on the term toggle). FAQ accordion + WebPage/Dataset (one per series)/FAQPage/BreadcrumbList/Person JSON-LD make the page a citable resource that ranks for rate + calculator + explainer queries. Card rendering is generic and data-attribute driven (`data-rate-*="<key>"` + the `rateKeys` array), so adding a series is: one `SERIES` entry in the API, one card block, and one key in `rateKeys`.

The page is the live freshness signal: the macro cards reflect a new PMMS reading (Thursdays at 12 ET) within an hour of edge-cache expiry; the OBMMI loan-program cards refresh every business day on the same path.

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
5. **Triangulated price** — Weighted blend (`AVM 60% + comp median 25% + ARV 15%`). Surfaces everywhere on the page as **"True Market Value"** (renamed from "Joshua's triangulated list price" per Joshua, 2026-07-16); future override slot for properties he's personally walked.

Plus an **investor panel** with rent estimate (Rentcast `/v1/avm/rent/long-term`), cap rate at 35% expense ratio, GRM, 70% wholesale offer (`ARV × 0.70 − $50/sqft rehab`), and monthly P&I + cash flow at current 30y from `/api/rates` (20% down, 30-year term).

**The comp study (`cma`, 2026-07-16): the pseudo-CMA.** Three additional Rentcast calls per uncached address (6 total): `/v1/properties` radius search with `saleDateRange` (deed-recorded closings, real sold prices), `/v1/listings/sale?status=Active` (live competition), `/v1/listings/sale?status=Inactive` (delisted pool). `assembleCMA` (pure, fixture-tested via `onRequest` with mocked fetch) builds the three buckets a real CMA weighs, per researched best practice (Fannie B4-1.3-08/09, Opendoor/Hooquest/NAR guidance): 1-mile radius, same `propertyType`, distressed listing types excluded, hard ±25% sqft bound with fall-back-if-starved (min 3 sold / 2 active), recency tiering (restrict to ≤180-day sales only when ≥4 similar remain; 9-month window otherwise), then similarity-ranked (size, distance, beds, baths, age). **Sold** entries carry `adjustedValue` (size gap moved at the marginal one-third local $/sqft, not full $/sqft) and, when an Inactive listing address-matches within 180 days of closing, `listPrice`/`saleToListPct`/`domAtSale`. **Expired** ("came off unsold") requires DOM ≥ 45, removed 30-365 days ago, ask at/above the sold-band $/sqft, and no recorded closing or AVM sale evidence at that address (guards against mislabeling pending sales); carries `vsSoldMedianPct` + `priceCutPct` from listing history. `stats` roll-ups: sold median + $/sqft band applied to subject sqft (quartiles), sale-to-list median (needs ≥3 matched list/sold pairs, else null; the sold-listing match window is 120 days removed-to-closed), active count/median ask/median DOM, `monthsOfInventory` (actives ÷ monthly sold pace; <5 seller / 5-6 balanced / >6 buyer; suppressed when soldCount < 8 or the ratio exceeds 12 months, because deed-record coverage runs thinner than listing coverage and the ratio then measures coverage, not market), expired premium. All best-effort: any upstream failure logs to `diagnostics.soldError/activeError/inactiveError` and the page falls back to the legacy flat `comps` render; `cma` is additive so older cached responses degrade gracefully. **Property-record fallback:** when `/v1/properties` has no record for the address (live coverage gap, found 2026-07-16), the AVM's `subjectProperty` (same attribute set incl. coordinates) stands in as the subject, so the report header, replacement-cost/ARV lenses, lead address components, and the comp study all survive a missing record (comp pools then fetch in a second phase off the AVM coordinates).

Accepts `GET ?address=...&lat=...&lng=...` or `POST` (JSON or form). **Contact gate (2026-06-24):** the full response (dollar values, comps, investor metrics) is delivered ONLY to a POST carrying `email` + `phone` + `consent="yes"`; without valid contact the endpoint computes nothing and returns `403 {ok:false, error:"contact_required"}`. A bare `GET` (which can never carry contact, by design) therefore never returns the numbers. Every contact-bearing request also saves the lead server-side via `saveValuationLead` → `/api/lead` (`intent="Home Valuation Lead"`), so getting the numbers and submitting the lead are inseparable. Response shape:
```
{
  ok, address: {input, formatted, street, city, state, zip, county, lat, lng},
  property: {propertyType, bedrooms, bathrooms, squareFootage, lotSize, yearBuilt, lastSalePrice, lastSaleDate},
  systems: {
    marketAVM:       {label, value, rangeLow, rangeHigh, psf, compsCount, methodology},
    assessor:        {label, value, year, land, improvements, methodology},
    replacementCost: {label, value, psf, sqft, region, quality, methodology, ...},
    arv:             {label, value, method, compsUsed, compsTotal, avgPsf, methodology},
    triangulated:    {label, value, methodology}
  },
  investor: {monthlyRent, capRate, grm, wholesale70: {value, ...}, monthlyPI, monthlyCashFlow, rate30y, methodology},
  rentEstimate: {monthly, rangeLow, rangeHigh, source},
  comps: [{formattedAddress, bedrooms, bathrooms, squareFootage, price, psf, distance, daysOld, saleDate, correlation}],  // top ~6, sorted by correlation then distance (LEGACY render fallback)
  compMedian,            // median comp sale price (also feeds the triangulated blend)
  cma: {                 // the pseudo-CMA comp study (additive, 2026-07-16; null when all pools empty/failed)
    criteria: {radiusMi, soldWindowMonths, sameType, ranking},
    sold:    [{address, distanceMi, bedrooms, bathrooms, squareFootage, yearBuilt, soldPrice, soldDate, psf, adjustedValue, listPrice, saleToListPct, domAtSale, matchScore}],   // top 6
    active:  [{address, distanceMi, bedrooms, bathrooms, squareFootage, yearBuilt, askPrice, psf, dom, listedDate, matchScore}],                                                 // top 5
    expired: [{address, distanceMi, bedrooms, bathrooms, squareFootage, yearBuilt, lastAsk, psf, dom, removedDate, priceCutPct, vsSoldMedianPct, matchScore}],                    // top 4
    stats: {soldCount, soldMedian, soldPsfMedian, soldWindowMonths, saleToListMedianPct, subjectPsfBand: {low, high}, activeCount, activeMedianAsk, activeMedianDom, monthsOfInventory, marketLean, expiredCount, expiredMedianAsk, expiredMedianDom, expiredPremiumPct},
    methodology
  },
  diagnostics: {propertyError, avmError, rentError, soldError, activeError, inactiveError},
  source, sourceUrl, fetchedAt
}
```

`marketAVM.psf` is the subject's price-per-sqft (AVM / sqft). `comps` is a trimmed, display-ready slice of the raw AVM comparables (added in the second pass); it is purely additive, so older edge-cached responses without it degrade gracefully (the page just omits the comps section).

Required env var in Cloudflare Pages settings: `RENTCAST_API_KEY` (get one at https://app.rentcast.io/app/api). If missing, the endpoint returns `503 {ok:false, error:"rentcast_api_key_missing"}` and `/value/` falls back to a graceful error state instead of rendering broken cards.

The page no longer creates anonymous leads. A lead is created **only** when the visitor submits the gate form (below); there is no side-effect soft-save (the old placeholder `"Home Valuation View"` save was removed 2026-06-24 because it dinged Joshua with an empty lead on every anonymous visit). The funnel CTA below the results remains the path to the *refined* CMA (the existing 5-step Sell funnel).

**Lead-capture gate (airtight, 2026-06-24).** The valuation is gated **server-side**, not just in the UI, so there is no way to reach the numbers without submitting contact info. Flow: the visitor enters an address and the page **immediately** opens a modal (`#value-gate`, scoped `.value-gate-*`, page-specific JS, NOT synced) titled "Where should I send it?" that collects name + email + phone **before any valuation is fetched** (`runValuation` only calls `openGate`; it does not hit the API). Submitting the form is the ONLY path to the numbers: `generateValuation` POSTs the contact + address to `/api/valuation`, which **refuses to compute or return anything without `email` + `phone` + `consent==="yes"` (returns `403 contact_required`)** and, on success, **saves the lead itself** (server-side `saveValuationLead` POSTs to `/api/lead` with `intent="Home Valuation Lead"` → FollowUpBoss "Seller Inquiry", reusing all of lead.js's delivery/normalization). Obtaining the numbers and creating the lead are therefore one atomic act; the numbers never enter the browser un-gated, so there is no network-tab, direct-API (`GET /api/valuation` → 403), or replay bypass. Closing the popup (X or Esc, via `abandonGate`) returns to the address form **without fetching anything**; backdrop clicks do nothing; there is no skip link; `abandonGate` is disabled mid-generate. If the address yields no data the lead is still saved and the page shows a "Joshua will follow up by hand" message (a no-data address is not a lost lead). Phone uses the funnel's `normalizeUsDigits`. PostHog/dataLayer events: `valuation_submit` (gate opened) / `valuation_gate_shown` / `valuation_gate_submit` / `valuation_submit_success` / `valuation_gate_dismiss` (method close/esc) / `valuation_error`. Copy says "I" not "we" per the solo-agent voice rule; the gate sits at z-index 12000 (above the funnel overlay's 9999).

**City-card handoff from /where-we-help/ (2026-07-21).** The 38 city cards on `/where-we-help/` no longer native-submit (they used to reload the page to the top): a page-specific copy of the `/value/` gate (same `.value-gate-*` CSS and ids, plus an address field with Places autocomplete and a city-aware title, e.g. "What's your Anaheim home worth?") opens on click, and submit stashes `{address, lat, lng, name, email, phone, src, ts}` in `sessionStorage.drozq_val_handoff`, then redirects to `/value/`. The `/value/` page IIFE consumes the key on load (10-minute freshness window), prefills its address input, and calls `generateValuation` directly, so the report renders on arrival and the lead saves through the same gated `/api/valuation` path. Dismissal (X or Esc) just closes the popup. Events reuse the valuation names with `src: "where-we-help"` + `city`: `valuation_gate_shown` / `valuation_gate_submit` / `valuation_gate_dismiss`. The interceptor skips any `form.pos_relative` (the hero and closing pills), so only the city-card forms are captured.

The results render (second pass) is, top to bottom: a headline answer band (the AVM as the single defensible number + its confidence range), a spread visualization (all available systems plotted min-to-max on one axis with the AVM confidence band shaded, plus a value-sorted legend; the True Market Value marker is a red RING so it stays readable sitting on top of the AVM dot it is anchored to, and rings are borders so they survive printing with background graphics off), derived insight chips (land value = market minus rebuild cost, Prop 13 assessor gap, $/sqft, renovated ARV upside), the five system cards (card 05 = "True Market Value"), the comp study (`cma`: a stats band + the sold / on-market / came-off-unsold buckets with status pills, size-adjusted values, and sale-to-list enrichments; falls back to the legacy flat `comps` list when `cma` is absent), the investor panel, a disclaimer (names no vendor), and the conversion CTA. The "Print or save this report" path has a dedicated print stylesheet: ink-friendly (dark panels flip to bordered white, every figure forced to ink tokens; the inline-white cash-flow strong was once invisible on paper), meaning-bearing color forced via `print-color-adjust: exact` (spread band/dots, pills, stat tiles), and one hard-won gotcha: the compiled Panda `@layer base` carries `header { display: block !important }`, and LAYERED importants beat unlayered ones, so any print `display: none` on the header must be appended inside `@layer base` itself (later source order wins within a layer). That applies to any template page that ever grows a print stylesheet. The CTA opens the Sell funnel directly via `window.openFunnel(address, "sell")` (the funnel JS now exposes `openFunnel` on `window` for bespoke pages). A "Print or save this report" button + a `@media print` stylesheet make the report a keepable artifact. All result blocks are scoped to `.value-*` classes in the page's inline `<style>`.

### `/functions/api/onetap.js`

Server-side verifier for the Google One Tap ("Sign in with Google") email-capture prompt. The homepage shows One Tap (the `ONE_TAP` IIFE in `/index.html`, a page-level script after `DROZQ_FUNNEL_JS_END`, NOT part of the synced funnel). When a visitor taps it, Google returns a signed ID token (JWT); the browser POSTs `{credential, source_page, page_url, gclid}` here.

This endpoint verifies the token (Google `tokeninfo` validates signature + expiry; this endpoint additionally pins `iss` to accounts.google.com and, when `GOOGLE_ONETAP_CLIENT_ID` is set, pins `aud` to the client ID), requires `email_verified`, then forwards the real Google email + name into `/api/lead` server-side with `intent="Google One Tap Lead"`, `phone="0000000000"` (One Tap returns no phone), `consent="yes"`, and `referral_source="Google One Tap"`. The client never controls the saved email. One Tap leads land in the same inbox as form leads.

Accepts JSON or form POST. Returns `{ok, email, name, lead_saved}`. REQUIRED env var: `GOOGLE_ONETAP_CLIENT_ID` (same value as the client ID in `/index.html`); since the 2026-07-22 security review the endpoint returns 501 until it is set, because an unpinned audience let ID tokens minted for any Google app create leads with fabricated consent.

**Gating:** the homepage One Tap block is inert until a real client ID replaces the `PASTE_YOUR_GOOGLE_CLIENT_ID_HERE...` placeholder. With the placeholder, no Google script loads and live behavior is unchanged. One Tap is the one sanctioned exception to the "no new external dependencies" rule (rule #8): it requires Google's `accounts.google.com/gsi/client` library, loaded dynamically only after a real client ID is set. To roll site-wide, copy the `ONE_TAP` block from `/index.html` into other pages (it does not sync); skip `/thank-you/`, `/privacy/`, `/terms/`.

## Email platform (updates@drozq.com)

Shipped 2026-07-13. Outbound email to visitors and clients: the branded HTML template, the living subscriber list, instant drip sequences, 1:1 progress updates, campaign broadcasts, and open/click/unsubscribe tracking. Runs entirely on the existing stack (Pages Functions + MailChannels + D1 + PostHog); no new vendors. Mail sends from `updates@drozq.com` (Joshua Guerrero), replies land in `josh@drozq.com`.

**Where it lives:**

- `functions/_lib/email.js`: the engine. MailChannels sender (DKIM-signed once `DKIM_PRIVATE_KEY` is set), the branded `renderEmail()` template (warm `#efe9e1` backdrop, white 16px-radius card, `#1a1816`/`#2b2b2b` text, `#d92228` CTA button, system font stack on purpose: that stack IS the Apple/Cloudflare email look and renders everywhere), HMAC-bound unsubscribe/open/click URL builders, subscriber upsert, the 9:30am-7pm PT send-window scheduler, server-side PostHog capture. The header is the brand logo (red house + lowercase "drozq.com", rendered 170x24 and linked to the site), never a text wordmark: **"drozq" is always lowercase and never letterspaced caps** (Joshua's brand rule, 2026-07-13). Emails load it from `https://drozq.com/api/email/logo` (a Function route wrapping `/media/images/brand-header-logo.png` via the ASSETS binding) because **Cloudflare Hotlink Protection is ON zone-wide**: any `/media/*.png` URL 403s under a foreign Referer, which includes webmail clients. Never reference an image-extension URL directly inside an email. The identity line in the signature, plaintext parts, and postal footer reads **"Active Realty"** with the Von Karman office address as the CAN-SPAM fallback (Joshua's "for now" direction, 2026-07-13; `EMAIL_POSTAL_ADDRESS` still overrides). **Dark mode (v2, 2026-07-13):** the template declares `color-scheme: light dark` and carries a `@media (prefers-color-scheme: dark)` ruleset on `dz-*` classes with `!important` (inline styles remain the light fallback). Dark token set, same family as the site: page `#1a1816`, card `#2b2b2b` with `#3f4650` border/dividers, headings `#fff`, body `#f2f0ef`, muted `#beb8b0`, CTA unchanged `#d92228`/white. Color accents (v2.1, both schemes): the card's top edge is a 4px red `border-top` that curves with the card's border-radius (part of the card, per Joshua: never a separate bar sitting on top), plus a 44px red rule under the headline (`.dz-rule`, omitted when the email has no headline, e.g. the nine-word). **Every red in every email surface, both schemes, is `#d9222a`, the exact hex sampled from the logo's house pixels** (Joshua's cohesion rule, extended to light mode 2026-07-13: emails match the logo, not the site token). The site itself keeps `--colors-primary` `#d92228`; the two are visually indistinguishable, and the email platform is the only surface pinned to the logo hex. The dark-mode logo is the red-house + white-text variant `media/images/brand-logo-red-white.png` (generated 2026-07-13 from the header logo via pixel recolor; served from `/api/email/logo?v=dark`; `?v=white` still serves the all-white file). Dual `<img>`s `.dz-logo-light`/`.dz-logo-dark` do the swap. Support reality: Apple Mail (the primary target) honors the media query; the Gmail app ignores it and applies its own auto-invert to the light theme; clients that strip `<style>` get light mode. The unsubscribe page carries the same dual theme (`uz-*` classes + red top border).
- `functions/_lib/sequence.js`: **THE DRIP COPY.** Editing an email = edit this file, commit, push (live in 60s). Two sequences: `lead-response-v1` (4 steps: instant confirmation ending in a reply-bait question, day-2 rates/prices value drop, day-5 case-file receipt, day-10 nine-word email) and `newsletter-welcome-v1` (welcome only: the `/field-notes/` page promises "no marketing sequences, just the post," and the platform honors that promise; note drops go out as broadcasts). `{first}` / `{city}` personalize per subscriber with "there" / "Orange County" fallbacks, and the funnel's Places-confirmed street address + timeline answer (stored as `subscribers.street` / `subscribers.timeline`) drive the deep personalization: step 0 names the property in the subject and body and keys one line off the stated timeline ("Yes, immediately" / "Yes, in 1-3 months" / "Yes, 4 or more months out" / "No, just curious"), and the nine-word email asks about the actual address. Every use falls back gracefully when the field is absent (buy leads, newsletter, backfill). All conversion copy rules apply in full.
- `functions/_lib/enroll.js`: enrollment orchestration (instant step-0 send, scheduled backfill stagger, or idle import).
- `functions/api/subscribe.js`: public subscribe endpoint (form or JSON POST; honeypot `company_website`; instant welcome via `waitUntil`).
- `functions/api/email/*.js`: admin endpoints, all requiring `Authorization: Bearer EMAIL_SECRET`: `init` (schema bootstrap), `tick` (queue drain, hit by cron), `send` (1:1 branded email), `broadcast` (queue a campaign to a segment on a stagger), `backfill` (import FollowUpBoss people; dry-run by default), `list` (subscriber list + stats; `?format=csv`, `?view=log` for the send log incl. failures), `pause` (pause/resume one person). Public by design: `unsubscribe` (HMAC token, RFC 8058 one-click), `open` (pixel), `click` (tracked redirect, HMAC-bound so it is not an open redirect), `preview` (renders any email in the browser; no auth, no DB).
- `workers/email-cron/`: standalone Worker that POSTs `/api/email/tick` every 10 minutes. Its `wrangler.toml` lives in the subdirectory ON PURPOSE: a repo-root wrangler.toml would hijack the Pages git build. Deploy: `cd workers/email-cron && npx wrangler deploy && npx wrangler secret put EMAIL_SECRET`.
- `scripts/emailer.py`: the daily-driver CLI (list / log / send / broadcast / backfill / pause / resume / preview / init / tick). Secret lives in gitignored `scripts/.email_secret`.

**Enrollment paths (all instant):** every accepted `/api/lead` submission (funnel, One Tap, valuation gate, field-notes form) enrolls via the `subscriberSeed` built in `onRequestPost` and delivered best-effort in `deliverLead`. Fully gated on `EMAIL_DB` + `EMAIL_SECRET`: with either unset, `/api/lead` behavior is byte-identical to before. Existing and unsubscribed addresses are NEVER touched by re-submits (insert-or-ignore). `@drozq.com` addresses are skipped. The `"Home Valuation View"` soft-save never enrolls (it short-circuits earlier). Intent `"Field Notes Subscribe"` maps to `newsletter-welcome-v1`; everything else enters `lead-response-v1`.

**Data:** D1 database `drozq-email`, tables `subscribers` (one row per address; `status` active/paused/unsubscribed; `sequence_step` + `next_send_at` drive the drip), `campaigns`, `email_log` (every send with status, error text, opened_at, clicked_at). The list is queryable any time: `python scripts/emailer.py list --csv` drops the full CSV in Downloads.

**Env (Cloudflare Pages > Settings):** `EMAIL_DB` (D1 binding), `EMAIL_SECRET` (admin auth + token HMAC), `DKIM_PRIVATE_KEY` + `DKIM_SELECTOR` (default `mc1`), optional `EMAIL_FROM` (default `updates@drozq.com`), `EMAIL_FROM_NAME` (default `Joshua Guerrero`), `EMAIL_REPLY_TO` (default `josh@drozq.com`), `EMAIL_POSTAL_ADDRESS` (CAN-SPAM postal line in the footer). Test knobs, never set in prod: `EMAIL_DRY_RUN`, `EMAIL_TEST_FAST`. The cron Worker needs its own `EMAIL_SECRET` secret (same value).

**Deliverability posture:** SPF already includes `relay.mailchannels.net`, the MailChannels Domain Lockdown TXT (`_mailchannels`, `v=mc1 auth=drozq`) exists, DMARC (`p=none` + Cloudflare rua) exists. DKIM (`mc1._domainkey` TXT + the private key env var) is the remaining piece; add it before real volume. Marketing sends carry List-Unsubscribe + one-click headers automatically.

**Hard rules:**

- The moment a lead REPLIES to a drip email, pause them: `python scripts/emailer.py pause <email>`. A sequence email landing mid-conversation reads robotic.
- Sequence and broadcast sends respect the 9:30am-7pm PT window; step 0 is instant by design (a confirmation is expected instantly).
- Field-notes subscribers stay welcome-only unless the promise copy on `/field-notes/` changes first.
- Never put `EMAIL_SECRET`, the DKIM private key, or subscriber exports in the repo (everything tracked is public). Secret file convention: `scripts/.email_secret` (gitignored).
- The lead-alert email to Joshua is dual-part (2026-07-13 rollout): the branded v2.1 HTML (`renderLeadAlert()` in `_lib/email.js`: lead name headline, field rows, tap-to-call CTA, no signature/unsubscribe) is what the inbox displays, and the ORIGINAL plaintext body ships unchanged as the text/plain part, so alerts stay grep-able and forwardable. The alert is DKIM-signed whenever `DKIM_PRIVATE_KEY` is set. Preview: `/api/email/preview?kind=alert`. Never remove the plaintext part.

**Debugging:** Cloudflare dashboard > Workers & Pages > the Pages project > Functions > Real-time logs. Log markers: `EMAIL_SEND_FAILED` / `EMAIL_TICK` / `EMAIL_BACKFILL` / `LEAD_ENROLL_THREW` / `SUBSCRIBE_*` / `EMAIL_CRON`. Per-send outcomes (including MailChannels error bodies): `python scripts/emailer.py log`. PostHog events: `email_subscriber_enrolled`, `email_sent`, `email_send_failed`, `email_opened`, `email_link_clicked`, `email_unsubscribed` (distinct_id = subscriber email). Endpoints that return a response immediately (open pixel, click redirect, unsubscribe) MUST wrap `phCapture` in `context.waitUntil` or the capture is cancelled mid-flight (fixed 2026-07-14 after opens silently never reached PostHog).

**Dashboard:** PostHog "Email Platform" (https://us.posthog.com/project/390294/dashboard/1847500): daily sent/opened/clicked/unsubscribed trend, who-opened table, who-unsubscribed table, sends by type, new subscribers by source. PostHog opens/clicks start 2026-07-14 (the waitUntil fix); the D1 `email_log` remains ground truth for anything earlier and for per-send status. Open counts are directional, not gospel: Apple Mail privacy prefetch can inflate them, image-blocking undercounts; replies and clicks are the real signal.

## Geo personalization

On every homepage pageview (and every synced page's pageview, since geo autofill is part of the synced JS), JS fetches `/api/geo` and:

1. Replaces every `<input name="location" value="Columbus, OH">` with `"{city}, {regionCode}"`. Only when current value is empty or the literal default; preserves returning-visitor data per the existing `populateLandingInputs` convention.
2. Replaces every visible "Columbus, OH" text node via TreeWalker (hero strip, market-section h2). Skips SCRIPT/STYLE/IFRAME descendants and any element marked `data-geo-static` (the Irvine market-trends readout, pinned to Irvine regardless of visitor IP).
3. Updates `.funnel-city` / `.funnel-buy-city` placeholder spans inside the funnel overlay so step copy reads "buying in Irvine" instead of "Southern California" once detected.

The market-trends widget (next to the "real estate trends in Irvine, CA" stats) no longer hotlinks the Move/realtor.com map (`realtorqa.upnest.com` stopped allowing third-party embeds). It renders a self-hosted Google Map of Irvine via the site's own Maps JS key (the same key + `<script>` the funnel's Places Autocomplete loads), lazy-rendered on scroll-into-view and desktop-only (lg+). Its heading month is live (current month via JS) and the whole readout is pinned to Irvine via `data-geo-static`, so visitor IP never rewrites it. The page-specific script lives after `DROZQ_FUNNEL_JS_END` in `/index.html` and is NOT synced. The same live-month pattern runs on `/market-insights/`: the hero's "refreshed [Month Year]" month is `#mi-refresh-month`, populated by a page-specific script after that page's `DROZQ_FUNNEL_JS_END` (server-rendered month = no-JS fallback). The stat cards on both surfaces stay hand-refreshed: update the numbers from the latest CAR release + Redfin Data Center + PMMS, and bump `/market-insights/`'s Source paragraph + JSON-LD `dateModified` in the same pass (last refresh: 2026-07-16, on the June 2026 CAR close + May 2026 Redfin read + July 16 PMMS print).

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
- ALWAYS normalize US phone input by stripping a leading country-code `1` BEFORE capping at 10 digits. A US number entered/autofilled as `+1 (949)...` arrives as 11 digits; the old `replace(/\D/g,"").slice(0,10)` shoved the `1` into the area-code slot (`(194)...`) and truncated the real last digit, silently corrupting leads (the Mary Morris incident, 2026-05-29). The client helper is `normalizeUsDigits()` (funnel JS, synced); the server backstop is `normalizePhone()` in `lead.js`, which also stamps `+1` on every real lead's phone. NANP area codes never start with `1`, so a leading `1` on an 11-digit string is always the country code.

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

Files at repo root: `favicon-96x96.png`, `favicon.svg`, `favicon.ico`, `apple-touch-icon.png`, `web-app-manifest-192x192.png`, `web-app-manifest-512x512.png`, `site.webmanifest`, plus `preview.png` (the sitewide og:image / twitter:image). Do not modify, rename, or remove these. Do not use absolute URLs with spaces in filenames.

## Deployment

This site auto-deploys to production via Cloudflare Pages on every push to main. There is no staging environment, no manual deploy step.

- Pushing to main = live in 30-60 seconds (sometimes 60-120s for function updates).
- Broken changes affect real users (and paid traffic) immediately.
- Rollback: `git revert [commit-hash] && git push`.

When paid ad campaigns are running, high-risk changes (hero rewrites, funnel restructures, navigation changes, tracking modifications) should be committed with clear messages, verified on live site immediately, checked for JS errors in the console, and rolled back if anything breaks.

Per the auto-commit rule, push directly to main. No feature branches unless explicitly requested.

## Repo hygiene (what gets committed)

There is no build step: the repo root IS the deploy root, so **every tracked file is publicly fetchable** at its drozq.com path (`scripts/`, `notes/`, and every `*.md` included; only `functions/` is special-cased). Two rules follow:

1. **Never commit anything that cannot be public**: credentials, lead exports, scraped or extracted third-party content. Secrets live in Cloudflare Pages env vars or gitignored files (`scripts/.google_ads.json`).
2. **QA screenshots never enter the repo.** Save captures to the Claude scratchpad or `C:\Users\guerr\Downloads`. Root-level images are gitignored wholesale except the favicon/OG whitelist (`apple-touch-icon.png`, `favicon-96x96.png`, `preview.png`, `web-app-manifest-*.png`). Context: a 2026-07-09 purge removed ~40 orphaned session screenshots that had been deploying to production URLs.

## Conversion copy principles

These apply to all pages. The site is one voice across all pages: confident, direct, first-person, low-bullshit. Joshua Guerrero, solo agent, speaking in his own voice.

**Promise boldly.** The old "no claims you can't back up" rule is deleted. Lead with the biggest true outcome (an instant home valuation, sold in about six weeks, "$23,250 in seller credit negotiated"). Joshua decides what's too grandiose, not a hedging rule. Two guardrails still hold: the anti-promise ban below stays, and when copy promises something the backend does not yet deliver (e.g. "instant" delivery that isn't wired), flag it so it gets built. Ship the bold line; never quietly leave an unbacked promise sitting on a live, paid page.

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
- Surface-level "AI" and "automation" framing. The leverage Joshua has is real; the framing is "systems and discipline," not "I use software to do this."
- **Exposing the plumbing.** Never name the vendor or tooling behind a system: no "API," "Rentcast," "Zillow data," "automated." Frame every tool and data source as Joshua's own earned system: "my own valuation model," "the same data investors and other buyers use, tuned by me," "every internal playbook I use." The edge should read as hard-won and exclusive, not a SaaS wrapper. (The flip side of the "systems and discipline" rule above.)
- **Team / staff language.** Joshua is a solo agent. Never "our agents," "our team," "our agents may contact you," or anything implying a staff. Use "I", or "we" only as Joshua speaking for himself. (Site-wide fix: "our agents may contact you" became "we may contact you," and the funnel consent fineprint now names "Joshua Guerrero" as the contacting party per TCPA.)
- **Loaded industry labels.** Watch the association a term plants. "Cash buyers" reads as lowball / distressed-flipper; say "investors and other buyers." Squint at every label for the worry or downgrade it implies.
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
- Drozq social URLs (footer row order, 2026-07-22): Zillow → `zillow.com/profile/ImJoshua`, Facebook → `facebook.com/Drozq/`, Instagram → `instagram.com/drozq/` (center), YouTube → `youtube.com/@drozq`, LinkedIn → `linkedin.com/in/guerrero-joshua/` (last). All five also live in every page's JSON-LD `sameAs`. The Zillow icon is the official Z-house swoosh mark (geometry traced from `s.zillowstatic.com/pfs/static/z-logo-icon.svg`, the two ™ subpaths dropped, scaled to fill the shared 20×20 white-disc evenodd-cutout style at the neighbors' visual weight, 13.8px tall with a 0.3px optical lift; glyph subpath starts `M12.21 6.52`).
- Hero tabs (Sell / Buy / Sell & Buy) wired with switcher JS.
- Mid-page tabs converted from "I'm selling / I'm buying" to the "My Home's Condition is..." switcher (`sellTabBtn`/`sellTab` = Move-in ready, `needsTabBtn`/`needsTab` = Needs work); both panels open the Sell funnel, buyer panel removed.
- FAQ accordion wired.
- Three-funnel system built (Sell / Buy / Sell & Buy).
- Geo autofill replacing "Columbus, OH" with detected city.
- Funnel drop-off PostHog events.
- gclid pushed to dataLayer on page load.
- `generate_lead` gated via sessionStorage flag + `?ref=funnel` redirect.
- DRE corrected to `02267255`, Indiana PLA removed.
- Footer gutted: minimal conversion footer (brand logo, identity line, DRE, office address (17875 Von Karman Ave, Suite 150, Irvine, CA 92614, added 2026-07-18), phone, social, Privacy/Terms, copyright).
- Market-trends map self-hosted: the hotlinked `realtorqa.upnest.com` iframe (and its 170×34 white "Source: RealEstateSM" attribution overlay) replaced by a lazy, desktop-only Google Map of Irvine on the site's own Maps JS key. Heading month is live; the trends readout is pinned to Irvine via `data-geo-static`; the readout stats are hand-refreshed from the Redfin Irvine read (last: July 2026, median $1,524,088, days-on-market 42).
- Tab IDs renamed (`sellUpnestTab` → `sellTabBtn`, `buyUpnestTab` → `buyTabBtn`, later `needsTabBtn` when the section became the condition switcher).
- 5 fake agent profile cards replaced with the "The Hard Parts Are My Job, Not Yours" infographic.
- 5 fake out-of-state testimonials swapped for real case files.
- "My Home's Condition is..." switcher images de-faked (2026-06-12): the UpNest "Grace C." agent-proposal card (`trust*.webp`, now 0 refs) replaced in both tabs by real photos. Move-in ready -> `cond-sold.webp` (SOLD sign, landscape, `object-fit:cover` with focal-biased `object-position`, filling the existing near-square/banner boxes). Needs work -> `cond-reno.webp` (before/after renovation, 2:3 portrait). On desktop the portrait reuses the same `w_593 h_490` box via `object-fit:contain` so it letterboxes into the same ~465px column and the cards don't shift on toggle (measured 5px); tablet/mobile use portrait inline sizes (Panda arbitrary `w_*` no-op, so px set via inline `style`), centered by the container's `ai_center`. One file per tab, reused across breakpoints.
- Move-hosted illustration imagery (`lt6p.com`) removed (zero refs).
- Move-hosted `@font-face` declarations replaced with self-hosted fonts in `/media/fonts/`.
- **Typography consolidated to Galano Grotesque Alt site-wide (2026-06-12).** Galano is now the entire type system, body and headings, on every page, the funnel, forms, every character. Each page carries a one-block override in `<head>` (just before `</head>`) that registers a real `GalanoGrotesque` weight-700 face (bold from the bold woff, no faux-bold) and repoints `--global-font-body` + `--fonts-sans` to `GalanoGrotesque`. New pages scaffold from `index.html` and inherit it automatically (`scaffold_page.py` copies the whole `<head>`). Roboto is retired (files kept, unreferenced); the never-loaded `ProximaNova` vars/`.ff_proxima*` classes are dead cruft. See `TEMPLATE.md` §Fonts. Do not reintroduce Roboto or Proxima as a body/text font.
- Footer award badges (Inc 5000, Deloitte Fast 500) and UpNest app store badges removed.
- **Full-screen rotating hero + scroll-reveal header (homepage only, 2026-07-20).** The hero is viewport-filling (`min-height:100dvh`); the splash `<img>` is `hero-giem/giem-01.webp` and a continuous one-way rotation cycles giem-01..10 + crystal-cove forever (top 10 = homepage-exclusive; giem-11..20 reserved for other pages (19 = /sold/), unassigned leftovers return to the ring (currently 20), per Joshua 2026-07-20) (first swap 1.5s, then every 3.5s; no pause, no controls; base-layer handoff must suspend its transition or the splash bleeds through as a visible jerk, see TEMPLATE.md §4). The header is a scroll-revealed FIXED bar: invisible at the top, fades in as the white bar past 64px of scroll. Root cause of the old "white block pushing the hero down": the compiled Panda `@layer base` ships `header{position:relative !important}`, which beats the unlayered `pos_absolute` utility; the fix overrides position inside `@layer base` (see TEMPLATE.md §3). All in the `#drozq-hero-rotate-css`/`#drozq-hero-rotate-js` block at the end of `<body>`, outside the funnel markers. Homepage-only; rollout to template pages is a BACKLOG item pending Joshua's approval.
- **Site-wide de-photocopy redesign (2026-07-20, Joshua: "all the other pages look like bad photocopies of the home page").** Every page now belongs to an archetype (TEMPLATE.md §4): landers keep the pill splash on their own Giem image (california 13, los-angeles 12, where-we-help 11, full 100dvh splash, scroll-reveal header); resource pages (rates/prices/market-insights/faq flat dark band; process 15 / field-notes 17 thin band; value warm tool band) and trust pages (about warm story band, meet-the-team 16, testimonials 18 strip, contact 14 + "One agent. One phone number.") lost the splash pill and photo clone, content above the fold; utility pages unchanged. Every page's header is fixed via the per-page `drozq-page-chrome` block (Variant A hidden-till-scroll on splash pages, Variant B always-visible + body padding elsewhere). Contextual `.drozq-inline-cta` bands on the three data pages open the funnel via `window.openFunnel`. crystal-cove is homepage-ring-only; giem 20 rides the homepage carousel as unassigned excess (19 later went to /sold/).
- **Sitewide interconnectivity sweep (2026-07-22, Joshua: "insert links and sections that beautifully reference each other").** Every template page except `/`, `/sellers/`, `/privacy/`, `/terms/`, `/404.html` carries a contextual `xr-` crosslink band above its closing CTA (the `/sellers/` hub-card language, two bg variants, real sold-board numbers in the card copy) plus inline `.xr-a` prose links where copy names a concept. Spec: `TEMPLATE.md` §5 "Crosslink band". Same pass fixed two copy bugs: `/where-we-help/`'s "route it to the right agent" dispatch language (both spots) and `/sold/`'s closer eyebrow cloned from `/faq/` (now "Want yours on this board?"). When a new page ships or the sold board grows, extend/refresh the bands.
- **Playbooks / six-weeks-guarantee section KILLED (2026-07-20, Joshua: "tacky, a mistake, kill any reference from now on").** The `#hpcar` "Quick Results, Guaranteed / Sold in six weeks / Get my 5 playbooks" section and its carousel are deleted from the homepage; a verbatim copy of `/process/`'s Five Steps timeline (scoped `proc-steps-css`) sits directly under the hero in a white + `#d3cfca`-divider band, and "My Home's Condition is..." is back at its original slot on `bg-c_#f2f0ef`. The guarantee/playbooks FRAMING is dead in all new copy. The remaining playbook surfaces were swept clean later the same day on "find anything that references the playbooks and kill it": title/meta/OG, homepage FAQ (visible + JSON-LD), 404 copy, /process/ closer, /where-we-help/ link, the synced funnel (value panel, valuebar, "Send My Report" buttons, "Where should I send it?", timeline block), and the pb-*.webp / playbook-* / funnel-timeline.webp assets (deleted).

### Deferred

Remaining realtor.com clone leftovers are tracked in `BACKLOG.md` under the "Realtor.com clone leftovers" section. The big remaining one is the inline-CSS purge (~157KB Panda CSS soup); the Move-hosted market-trends iframe is resolved (replaced with a self-hosted Irvine Google Map, see "Done" above).

When asked to "clean up the homepage," check `BACKLOG.md` and confirm which item(s) before proceeding.

## Reference docs

- **`TEMPLATE.md` (repo root): REQUIRED READING before building or editing any page.** Canonical spec for tokens, header, hero, sections, mid-page tabs, FAQ, footer, funnel overlay, all behaviors, all forms. The homepage at `/index.html` is the live reference; TEMPLATE.md explains what is in it and why. Treat as gospel. Do not deviate without explicit confirmation from Joshua.
- `BACKLOG.md` (repo root): the single consolidated list of active TODOs across the codebase, grouped by category (Strategy / SEO / Tracking / Realtor cleanup / Hygiene). When work ships, delete the line item in the same commit. This replaces the five prior audit docs (AUDIT-INDEX, SEO-AUDIT-INDEX, FAVICON_AUDIT, SPEED-AUDIT, CHANGES.md) and the realtor cleanup audit.
- `funnels.json` (repo root): funnel sync registry. List of pages carrying the inline funnel + last sync timestamps.
- `scripts/sync_funnels.py`: the funnel propagation tool.
- `scripts/panda_patch.py`: the Panda no-op guard. Sibling pages inherit a pruned copy of the homepage's compiled CSS, so any utility class the homepage never used silently renders NOTHING (the trap that left /process/'s step cards and a dozen pages' card grids unstyled until 2026-07-14). `--check` (default) fails if any page uses an uncompiled visual class; `--apply` regenerates the site-wide `<style id="drozq-panda-patch">` block that compiles the missing utilities. Run `--check` after building or editing any page; spec in `TEMPLATE.md` §14.
- `notes/posthog/`: running log of funnel observations from PostHog. Read `lessons.md` first, then the most recent entries in `funnel-log.md`, before touching anything that could move funnel drop-off (hero copy, tab structure, step ordering, validation, mobile layout). Append a new dated entry after any session that queried PostHog. See `notes/posthog/README.md` for the convention.
- `notes/ads/`: paid campaign strategy docs (`distressed-sellers-strategy.md`, `sellers-max-intent-campaign.md`). Read before touching the campaigns or campaign landing pages.
- `.mcp.json` (repo root): wires up the PostHog MCP server (requires `POSTHOG_API_KEY`). Run `/mcp` inside Claude Code to confirm it is connected. **Google Ads is no longer an MCP** (removed 2026-05-28 after repeated gcloud-ADC auth failures); pull stats via `python scripts/ads.py` (direct GAQL, stored refresh-token auth, no gcloud). See `notes/mcp-workarounds.md`.
- **`notes/mcp-workarounds.md` (repo root): direct REST recipes for PostHog HogQL and Google Ads GAQL (`scripts/ads.py`). READ THIS the moment the PostHog MCP fails (tool rejection, hang, 401, empty schema) or whenever you need Google Ads data. Includes the one-time `scripts/google_ads_auth.py` setup for when the Google Ads refresh token is missing or revoked.**
- `C:\Users\guerr\.claude\projects\C--Users-guerr-Documents-drozq-com\memory\`: auto-memory directory for cross-session context. Read on every session start; updated when stable patterns emerge.

## When in doubt

- Building or editing any page: read `TEMPLATE.md` first. It is the contract.
- Ambiguous styling or structure on a new page: default to the homepage pattern (per `TEMPLATE.md`).
- Ambiguous voice or copy direction: confident, first-person, specific, sparse. No platitudes, no SEO filler, no star ratings.
- Anything that touches the funnel, tracking, forms, or `/api/lead`: stop and audit before modifying.
- Anything that touches a registered page's funnel block: edit `/index.html` and re-sync; never hand-edit.
- Anything labeled "DO NOT MODIFY": ask.
