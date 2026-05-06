# AUDIT: `/index.html` Production Readiness

**Audit date:** 2026-04-26
**Auditor:** Claude Opus 4.7 (1M context)
**Method:** Static read of `/index.html` (338,760 bytes), `/functions/api/lead.js`, `/functions/api/geo.js`, `/thank-you/index.html`, `/site.webmanifest`, cross-referenced against `/CLAUDE.md`. No live page interaction.
**Scope:** Read-only audit. No changes made to `index.html`.

---

## Executive Summary

| Severity | Count |
|---|---|
| 🔴 BLOCKER | **8** |
| 🟡 SHOULD-FIX | **12** |
| 🟢 NICE-TO-HAVE | **3** |
| ✅ WORKING | **22** |

**Top-line recommendation: 🛑 STOP — SIGNIFICANT WORK NEEDED**

The plumbing is solid. GTM is installed correctly, the funnel posts to `/api/lead` with the right payload, the `/thank-you/` redirect carries the `?ref=funnel` flag and pushes `lead_confirmed` cleanly, and the gclid capture chain is intact. Tracking is the strongest part of this page.

What kills it for paid traffic is **above the fold and below it**:

1. **The homepage is still architecturally an agent-matching service**, not Joshua's landing page. A Long Beach homeowner clicking a "Joshua Guerrero, Irvine listing agent" ad lands on a page whose hero says "Compare Agents. Find a Trusted Expert. We analyze thousands of local agents…" with five fake agent cards (Debbie Harr / Marci Press / Eric Seagle / Kristina Murphy / Omar El Mejjaty). This is a brand-promise mismatch and the single biggest conversion risk on the page.
2. **A "4.8 Out of 5 — Average of 2k+ Customer Reviews" star aggregate is visible**, plus three new testimonials, on what is supposed to be a solo-agent page with two real case files. CLAUDE.md is explicit that this site is "not a place for star ratings." This is also a Google Ads policy risk (unsubstantiated claim).
3. **Form has zero `<label>` elements and zero honeypot field**, despite the backend supporting both. Honeypot absence specifically means bots will produce real emails.
4. **17 `<h1>` tags** on a single page. SEO will not parse this cleanly and screen readers definitely won't.
5. **Three em dashes** in body copy — explicit CLAUDE.md violation (U+2014 forbidden).

If ad spend launches today, the funnel itself works (so leads will land), but the page will under-convert against the cost-per-click and the email inbox will get junk. Address blockers 1, 4, 5, 6, 7 in the priority list at the bottom and the page will be ready.

---

## Section 1: Tracking Stack Integrity

### ✅ WORKING

- **GTM container `GTM-KVV3R96P`** present in `<head>` (lines start of file, immediately after `<meta charset>`) and in `<body>` `<noscript>` fallback. Container ID matches CLAUDE.md.
- **GTM is the very first script in `<head>`** (after `<meta charset>` only) — placement is ideal.
- **Zero direct `gtag.js` installations**, zero `gtag(` calls, zero `AW-*` legacy tags. CLAUDE.md compliance confirmed: all conversion tracking flows through GTM → GA4 → Google Ads import.
- **Zero direct PostHog `posthog.init`** calls inline. PostHog is referenced only via `posthog.capture(…)` (2 occurrences inside the funnel `track()` helper), which is the correct pattern when PostHog is loaded via GTM custom HTML tag from the `t.drozq.com` reverse proxy.
- **`gclid_captured` event** is pushed to `dataLayer` on every page load (1 occurrence in funnel IIFE). This means GA4 Custom Definitions can surface `gclid` on every event, not just conversions.
- **No duplicate GTM containers**, no Facebook Pixel `fbq()`, no Bing UET `uetq()` scripts. All Move/realtor pixels successfully purged from CLAUDE.md's "Done" list.

### 🟡 SHOULD-FIX

- **Dead DOM remnant from Bing UET**: `<iframe height="0" width="0" style="display:none">…</iframe> <div id="batBeacon695533934547" style="width:0;height:0;display:none">…</div>` is sitting in the body (around line ~2666). The Bing UET *script* was removed per CLAUDE.md, but this DOM artifact wasn't. Harmless (the script that populated it is gone), but it's clutter and could confuse a future audit. Strip the iframe and the `batBeacon` div.

### 🟢 NICE-TO-HAVE

None.

---

## Section 2: Form Integrity

The "form" is a multi-step funnel overlay with three modes: Sell (5 steps), Buy (5 steps), Sell & Buy (6 steps). The final step in each mode submits via `attachSubmitHandler` → `fetch('/api/lead')` → redirect to `/thank-you/?ref=funnel`. Eight `<form class="pos_relative">` elements exist (the various landing-CTA address inputs around the page) but only the funnel's final-step inputs are actually submitted; the landing inputs serve as funnel openers.

### ✅ WORKING

- **`FUNNEL_ENDPOINT = "/api/lead"`** correctly wired.
- **FormData payload posted to `/api/lead`** includes every field the backend expects:
  - `name`, `email`, `phone`, `consent="yes"`, `intent`, `source_page`, `gclid`, `page_url`, `submitted_at`, `timeline`, `message`
  - Sell address parts: `street_address`, `city`, `state`, `zip`, `full_address`, `lat`, `lng`
  - Buy fields: `buy_location`, `buy_timeline`, `buy_budget`, `buy_home_type`, `buy_process`
  - Server-side validation in `/functions/api/lead.js` requires `name`, `email`, `phone`, `intent`, `consent==="yes"` — all are provided.
- **Three `attachSubmitHandler` registrations** (one per funnel mode): `funnel-step6-submit` (sell), `buy-step5-submit` (buy), `sellandbuy-step6-submit` (sellandbuy). Each captures email + phone validation (and name on Buy / Sell&Buy).
- **Google Maps Places API** loaded with `libraries=places&callback=initFunnelPlaces`. Found 10 references to `validAddressMap` (per-input WeakMap tracking Places-confirmed inputs), 2 `place_changed` handlers, 1 `getPlace()` call, 3 `street_number` references (Sell address validation requires `street_number + route`).
- **`window.location.href = "/thank-you/?ref=funnel"`** redirect on success — preserves the GA4 generate_lead trigger flag.
- **`sessionStorage.setItem("drozq_lead_just_submitted", "1")`** + `drozq_lead_mode` set immediately before redirect. The `/thank-you/` page reads + clears these to push `lead_confirmed` exactly once per real submit.
- **Funnel timeline options match CLAUDE.md spec exactly**:
  - Sell + Sell&Buy: `Right away` / `1 to 3 months` / `4 or more months` / `Already listed` (4 options)
  - Buy: `Right away` / `1 to 3 months` / `4 or more months` / `Just looking` (4 options)
  - Note: the audit prompt mentioned "5 expected options" — actual is 4 per CLAUDE.md, which is correct.
- **Buy "process" step** has 3 options: `Just started` / `Pre-approved, ready to tour` / `Already making offers` — matches CLAUDE.md.
- **Funnel error/loading states**: `btn.disabled = true; btn.textContent = "Sending…"; …; btn.disabled = false; btn.textContent = origLabel;` — minimal but present. Error messages displayed inline.

### 🔴 BLOCKER

- **Honeypot field is missing.** The backend `/functions/api/lead.js` lines 23–27 explicitly checks for a `company_website` field and silently 200s if it's non-empty, but the homepage forms never include it. Result: the bot-protection layer is **non-functional**. Bots that POST to `/api/lead` will trigger MailChannels emails and (worse) inflate `lead_confirmed` events when they hit the redirect with the sessionStorage flag. Add `<input type="text" name="company_website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">` to the funnel's contact step (or just inside the `<section id="funnel-overlay">`).

### 🟡 SHOULD-FIX

- **No `<label>` elements anywhere on the page.** Every funnel input relies on a `placeholder` for visual guidance. Placeholders are not labels — they vanish on focus and screen readers may or may not announce them depending on browser. This is a Section 508 / WCAG 2.1 1.3.1 + 4.1.2 concern, and Google Ads housing-vertical advertisers can be flagged for accessibility issues. Wrap each input in a `<label>` (visually-hidden if you don't want the layout shift) or add `aria-label` to every input.
- **No UTM parameter capture.** Only `gclid` is preserved on landing. CLAUDE.md mentions UTM as something the funnel "may add" but it's not in the FormData. If Joshua runs Meta/LinkedIn/email campaigns alongside Google Ads, attribution will collapse. Capture `utm_source/medium/campaign/term/content` from the URL on load → cookie → hidden field, mirror of the gclid pattern.
- **Funnel inputs lack `name=` attributes** (only `id=` is set, e.g., `funnel-step6-email`). The funnel JS reads them by ID and explicitly appends to FormData with the right server-expected keys, so this works *only because the JS runs*. If JS fails or is blocked (rare but possible — corporate proxies, very old browsers), the form would submit but with no usable fields. Adding `name="email"`, `name="phone"`, `name="first_name"+"last_name"` would create a graceful degradation path. Low-risk improvement.

### 🟢 NICE-TO-HAVE

None.

---

## Section 3: Conversion Tracking Flow

Full path verified end-to-end:

1. **Ad click → `/index.html?gclid=…`** ✓
2. **gclid captured on landing**: URL → 90-day cookie → sessionStorage. Pushed as `gclid_captured` event to `dataLayer` on every page load (so GA4 Custom Definitions surface gclid on all events, not only conversions).
3. **User completes funnel → submit** → fetch `/api/lead` with FormData carrying `gclid`.
4. **Backend** `/functions/api/lead.js` accepts the payload, validates, sends MailChannels email with `GCLID: <value>` in body, optionally forwards to Zapier. Returns `{ok:true}`.
5. **Client receives ok** → sets `sessionStorage.drozq_lead_just_submitted = "1"` + `drozq_lead_mode` → redirects to `/thank-you/?ref=funnel`.
6. **`/thank-you/` page** reads + clears the flag, strips `?ref=funnel` from URL via `history.replaceState`, pushes `lead_confirmed` to `dataLayer` with `funnel_mode` metadata.
7. **GTM** picks up `lead_confirmed` → forwards to GA4 → GA4 imports to Google Ads as `generate_lead` conversion.

### ✅ WORKING

- **Every step of the chain is intact in code.**
- **Direct visit / refresh / bookmark of `/thank-you/`** does NOT fire `lead_confirmed` (sessionStorage flag is single-use). Verified in `/thank-you/index.html` lines 380–403.
- **No redirect chains, no query-string strippers** in the funnel-→-thank-you path. The `?ref=funnel` is preserved through the redirect.
- **Backend** sends `X-Api-Key` to MailChannels (env-var driven), uses `reply_to` set to the lead's email, includes IP + UA + gclid in email body.

### 🔴 BLOCKER

- **GTM-side action item is still pending (per CLAUDE.md).** The GA4 `generate_lead` trigger in GTM is currently set to "Page View on `/thank-you/`", which fires on **every visit** — including direct, refresh, and bookmark visits. Until Joshua updates the GTM trigger to "Custom Event = `lead_confirmed`" and turns off the old pageview trigger in the same publish, **conversions will be inflated**. This is a CLAUDE.md-flagged item; it's a tracking blocker for clean attribution but is fixed in GTM, not in `index.html`. Mention to confirm before launch.

### 🟡 SHOULD-FIX

- **Bot-triggered conversions risk** (compounds with Section 2's missing honeypot): if a bot can complete a fetch to `/api/lead` and then visit `/thank-you/?ref=funnel` with the sessionStorage flag, it counts as a conversion. The honeypot fix in Section 2 closes this hole at the form layer; without it, the conversion path is open to anyone.

---

## Section 4: Page Performance

### Hard numbers

| Metric | Value |
|---|---|
| `index.html` size | **338,760 bytes** (330 KB raw, ~70 KB gzipped) |
| Local `/media/…` asset references in HTML | 57 |
| Total weight of referenced local assets on disk | **2,791,051 bytes (~2.7 MB)** |
| Images > 200 KB | **4** (see below) |
| Images > 500 KB | **1** (`highlight-reviews@2x.png`, 524 KB) |
| `<img>` tags total | 44 |
| `<img loading="lazy">` count | **0** |
| `<img fetchpriority="high">` count | 1 |
| External script domains | 1 (`maps.googleapis.com`) |
| External stylesheets | 0 (CSS is inline) |
| Inline `<script>` blocks | 2 (GTM + funnel/IIFE: 44,393 chars) |
| Iframes | 1 visible (Move-hosted market-trends), 1 hidden (Bing UET DOM remnant), 1 GTM noscript |

### Heavy images (> 200 KB)

| File | Size |
|---|---|
| `media/images/highlight-reviews@2x.png` | **523.5 KB** |
| `media/images/trust-sell-tablet.webp` | 336.6 KB |
| `media/images/trust-buy-tablet.webp` | 289.5 KB |
| `media/images/highlight-reviews.png` | 203.8 KB |

### 🟡 SHOULD-FIX

- **Zero images use `loading="lazy"`.** All 44 `<img>` tags fetch eagerly. The hero (`new_sell_realtor` srcset) correctly uses `fetchpriority="high"` (1 occurrence), but everything else — agent headshots, brand grid SVGs, trust panels, highlight-reviews, spot icons — should be `loading="lazy"`. On mobile this could shave 1–2s off LCP. Quick fix: bulk add `loading="lazy"` to every `<img>` not in the hero `<picture>`.
- **`highlight-reviews@2x.png` is 524 KB.** Joshua's PNG upload replaced the 359-KB CDN JPG. PNG isn't the right format for a photographic review-page image — should be a JPEG or WebP. Re-export at ~100–150 KB JPEG quality 80; you'll lose nothing visible and gain ~400 KB on a single image.
- **`highlight-reviews.png` (1x) is 204 KB.** Same recommendation — convert to JPEG/WebP.
- **Hero `srcset` includes 7 sizes from 400w to 2000w**: that's well-implemented for responsive bandwidth but a full `2000w` ships as 76 KB which is fine. Don't change.
- **The 44 KB inline funnel script runs at parse-time** (no `defer`). It's inside the `<body>` after the markup, which is the right pattern (parser-blocking only after DOM is mostly built), so this is acceptable. Could be moved to an external file with `defer` for caching benefits, but that's a refactor, not a fix.
- **Move-hosted market-trends iframe** (`realtorqa.upnest.com/market-trends/...?slug_id=Irvine_CA&lat=33.6846&lon=-117.8265`) — this is the deferred CLAUDE.md item. It fetches a third-party widget, blocking on its TTFB. Mobile-impact unknown without measurement; flag for the broader cleanup.

### 🟢 NICE-TO-HAVE

- **CSS is inline** — good for first paint, but it's a *lot* of CSS (the realtor.com clone's panda-CSS shipped as inline). Eventually extracting + minifying would help, but the inlining itself isn't broken.

---

## Section 5: Mobile Responsiveness

### ✅ WORKING

- **`<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`** is present in `<head>` — correctly configured.
- **Mobile-first CSS** from the realtor.com clone uses panda-CSS responsive-utility classes (`md:`, `lg:`, `xl:`, `xs:`, `sm:`) extensively. Layout adapts at the standard breakpoints.
- **Hero CTA** ("Compare Agents" red button) is large (~280 px wide × 60 px tall on mobile) — well above 44×44 px tap-target minimum.
- **Funnel options** are tap-target-sized rectangles, full-width on mobile.
- **Sticky behavior** on the funnel progress bar is wired (`#funnel-overlay #funnel-progress-bar` has `position: sticky; top: 0;`), so the user always sees their progress as they scroll within a step.

### 🟡 SHOULD-FIX

- **No native `<select>` for the funnel timeline step.** The timeline is presented as a stack of clickable `.funnel-option` cards, which is a CONVERSION choice (visual buttons feel lighter than a dropdown). Native select would be more mobile-ergonomic but loses the visual polish — leave as-is unless mobile completion data shows a drop. Not a blocker.
- **No dedicated sticky mobile CTA bar.** On mobile, the hero's CTA is visible above the fold but disappears on scroll. A sticky bottom bar (e.g., "Get Started Today!" floating CTA) would re-engage scrolled users. Not present in current markup. CLAUDE.md doesn't require it but conversion best practice does.

### 🟢 NICE-TO-HAVE

- **Some realtor.com clone copy has long lines** that break awkwardly at 375 px (e.g., the agent profile cards' `Sold in the last year` text). Visible-text inspection didn't surface horizontal scroll though.

---

## Section 6: SEO and Metadata

### ✅ WORKING

- **`<title>`**: "Buy or Sell in Southern California | Joshua Guerrero" — **51 chars**, includes brand. ✓
- **`<meta name="description">`**: "Free home valuation and buyer's strategy in Southern California. I'm Joshua Guerrero, a solo agent based in Irvine. No spam, no autodialer." — **138 chars** (just under the 140–160 sweet spot, but good content).
- **`<link rel="canonical" href="https://drozq.com/">`** ✓ (correct canonical, points to drozq, not realtor.com).
- **Open Graph**: `og:url`, `og:title`, `og:description`, `og:image`, `og:image:width=1200`, `og:image:height=630`, `og:type=website`, `og:site_name=Drozq` — full set. ✓
- **Twitter Card**: `twitter:card=summary_large_image`, `twitter:title`, `twitter:description`, `twitter:image`. ✓
- **`<html lang="en">`** ✓
- **No `<meta name="robots" content="noindex">`** on homepage — it's correctly indexable. ✓
- **Favicons fully wired**: 96×96 PNG, SVG, ICO, apple-touch-icon, manifest. All cache-busted with `?v=20260506`. ✓
- **Hero image uses `fetchpriority="high"`** ✓

### 🔴 BLOCKER

- **No JSON-LD structured data on the homepage.** CLAUDE.md explicitly states: "The homepage carries the RealEstateAgent Organization schema (still pending — flagged in the cleanup audit)." `RealEstateAgent` schema is missing. This is also a Google Ads landing-page-quality signal for housing verticals. Add a JSON-LD block in `<head>` with `@type: RealEstateAgent` + `name`, `image`, `url`, `telephone`, `address` (the Irvine office), `areaServed`, `priceRange`, `sameAs` (social URLs), and a `Person` reference for Joshua.

### 🟡 SHOULD-FIX

- **Meta description is 138 chars.** Add 15–20 chars to land in the 140–160 sweet spot for SERP truncation. Suggestion: append something concrete like "Direct line to Joshua." → ~160 chars total.
- **Image `alt` attributes are weak.** The homepage inherits realtor.com clone alt text like `alt="Brand Logo normal"`, `alt="Hero Banner"`, `alt="Real ratings and reviews highlighted section"`. These don't describe the content for SEO or screen readers. They're not actively wrong, but they're not earning their place either.
- **No `<img loading="lazy">`** on non-hero images — also impacts Lighthouse SEO score, mentioned in Section 4.

### 🟢 NICE-TO-HAVE

None.

---

## Section 7: Accessibility (A11y)

### ✅ WORKING

- **`<html lang="en">`** ✓
- **Funnel buttons** have meaningful text content (e.g., "Right away", "Send My CMA").
- **Social links in footer** have `aria-label` (Facebook / Instagram / YouTube). ✓
- **FAQ accordion** uses `aria-controls`, `aria-expanded`, `aria-labelledby` correctly. The exclusive-accordion JS sets both `aria-expanded` and `data-expanded` on toggle.
- **The `<picture>` element** for `highlight-reviews` has fallback `<img alt="…">`.

### 🔴 BLOCKER

- **17 `<h1>` tags on a single page.** Should be exactly **one** `<h1>`. This is inherited from the realtor.com clone, which used `<h1>` liberally as a styling/heading-weight choice rather than a document-outline choice. Screen readers announce one `<h1>` per page; 17 confuses navigation. SEO crawlers also expect one. **Sweep all but the hero `<h1>` ("Compare Agents.\nFind a Trusted Expert.") down to `<h2>` or `<h3>`.**
- **Zero `<label>` elements on the page** (also flagged in Section 2). 21 input fields, 0 labels. Even with `placeholder`, this fails WCAG 2.1 SC 1.3.1 (Info and Relationships) and 4.1.2 (Name, Role, Value). Google Ads housing-vertical reviewers can flag this. Either add `<label>` (visually-hidden if needed) or `aria-label` to every input.

### 🟡 SHOULD-FIX

- **No "skip to main content" link.** Standard a11y polish; helps keyboard / screen-reader users bypass the long header.
- **Color contrast on the secondary tab text** (e.g., the "Buy" tab when not selected, white text on a subtle hover state) should be spot-checked against WCAG AA contrast (4.5:1 for normal text). Without rendering I can't measure precisely, but `[aria-selected="false"]:hover { background-color: #a92e2a !important; }` plus white text gives ~5:1 — borderline OK.
- **Funnel error states** (e.g., the "We couldn't reach our server. Try again or call (949) 438-5948." message in the script) display inline but don't appear to use `role="alert"` or `aria-live="polite"`, so a screen-reader user submitting and hitting a validation error may not be announced to them. Add `role="alert"` to the error display elements.

### 🟢 NICE-TO-HAVE

- A skip-to-content link is the only material polish item left after labels + h1 collapse.

---

## Section 8: Google Ads Policy Compliance (Real Estate / Housing)

### ✅ WORKING

- **No "#1 agent" / "best in Irvine" / "top agent in Orange County"** unsubstantiated superlatives in homepage copy. ✓ Verified by regex sweep: 0 matches for `#1\s+(agent|listing)`, 0 matches for `best\s+in\s+(irvine|...)`.
- **No income guarantees** ("I'll get you $X over asking", "guaranteed sale"). ✓
- **No housing-discrimination language** detected (no references to "good schools", "good neighborhood", demographics, "family-friendly", etc.).
- **CA DRE #02267255 visible** in the footer (2 occurrences — desktop + mobile footer copies). ✓
- **No false pricing claims** (the `$1,488,000` median is presented as a market-trend figure, not a property-price promise). ✓
- **The "Southern California's Top-Rated Listing Agent" banner is NOT on `index.html`.** This banner appears on `/thank-you/index.html` (line 219, inside the brand-mode chrome). The audit prompt asked to flag it on the homepage — confirming it's not there. **However, it IS still on `/thank-you/`** and on every other brand-mode page, where it's an unsubstantiated superlative claim. Flag for separate brand-mode cleanup, not this audit's scope.

### 🔴 BLOCKER

- **The "4.8 Out of 5 — Average of 2k+ Customer Reviews" star aggregate** is rendered prominently above the testimonial cards. This is **(a)** a CLAUDE.md violation ("not a place for star ratings"), **(b)** an unsubstantiated rating that can't be backed up (Joshua doesn't have 2,000+ reviews — this is realtor.com's aggregate), and **(c)** a Google Ads policy risk for misrepresentation. The entire "4.8 Out of 5" + "Average of 2k+ Customer Reviews" line should be deleted. The three testimonial cards beneath it (now Elijah Donoso / Connie Stone / Kevin Brierton) should also be vetted — those names + locations exist but without verified provenance, they're at risk too.
- **Five fake "partner agent" cards visible** at the top of the body: Debbie Harr, Marci Press, Eric Seagle, Kristina Murphy, Omar El Mejjaty, with sold counts ("112 Sold in the last year") and license #s ("#449174"). These are realtor.com clone leftovers and **misrepresent partnerships that don't exist**. Per Google Ads' "Misrepresentation" policy, this could trigger ad disapproval. Per REALTOR® Code of Ethics Article 12, advertising must be truthful and not misleading — these cards imply partnership with five named agents who are not actually Joshua's partners. **Remove entirely** (CLAUDE.md / `REALTOR_CLEANUP_AUDIT.md` already flag this).

### 🟡 SHOULD-FIX

- **No physical office address on the homepage.** Drozq's office (17875 Von Karman Ave, Suite 150, Irvine, CA 92614) appears on `/thank-you/` and brand-mode pages but not on `index.html`. Real estate paid traffic benefits from a verifiable physical location. Add to the footer near the DRE# (or as a small line below it).
- **Brokerage name not visible on homepage.** Joshua's brokerage is "Real Brokerage Technologies" / "Real Broker" (per `/thank-you/` footer, which has the Real Broker logo). California REALTOR® disclosure rules generally require the brokerage to be identified on agent advertising. Add brokerage name + logo near the DRE# in the footer.
- **"Compare agents in Irvine, find a trusted expert"** mid-page headline. The geo-personalised version is fine. But the surrounding context still implies *multiple* agents to compare — see Section 12 for the strategic conversation about this.
- **"AgentLocator Selling by drozq.com offers free proposals…"** sub-heading. The "Selling" word leftover from the realtor.com brand still reads oddly. Either rebrand to a coherent product name (e.g., "Drozq Agent Match" / "AgentLocator™") or simplify to "We offer free proposals for Irvine homeowners…".

### 🟢 NICE-TO-HAVE

None.

---

## Section 9: Copy / Conversion Elements

### Inventory

| Element | Status |
|---|---|
| Hero headline | ✅ "Compare Agents. Find a Trusted Expert." |
| Hero subhead | ✅ "We analyze thousands of local agents and find the best to compete in your area." |
| Hero CTA | ✅ "Compare Agents" red button |
| Trust signals near form | 🟡 5 fake agent cards (BLOCKER), "4.8 Out of 5" (BLOCKER), real DRE# (footer only) |
| Specific numbers | ✅ "$1,488,000" Irvine median, "35 days" avg DOM (in market trends section) |
| Urgency / scarcity | 🟡 None on homepage. Some implicit ("Free, no commitment" badge) |
| Social proof | 🟡 3 testimonials present (now Elijah / Connie / Kevin), but locations lack city specificity, and 5 fake partner agents undercut everything |
| Risk reversal | ✅ "Free, no commitment" green badge above the funnel |
| "What happens next" | ✅ 3-step strip: "Enter your selling address → View proposals, no commitment → Choose the right agent" — but reinforces the multi-agent framing |
| Phone visible | ✅ (949) 438-5948 in header (×2 occurrences) |

### 🔴 BLOCKER

- **Hero headline + subhead promise the WRONG product.** "Compare Agents. Find a Trusted Expert. We analyze thousands of local agents and find the best to compete in your area." This is realtor.com's RealChoice value prop, not Joshua's. A user who clicked a Joshua Guerrero ad expects "Sell your Irvine home with Joshua, a solo listing agent who…". They land on what reads as a generic referral-shopping page. **This single change is the highest-leverage conversion fix on the page.**

### 🟡 SHOULD-FIX

- **"Our partner agents are…" section** lists 6 generic value props ("Top agents", "Licensed Agents", "Expert negotiators", "Highly reviewed", "Competitive rates", "Market experts"). Reinforces the matching-service framing. If the homepage is going to keep the funnel as the conversion mechanism, this section should be replaced with Joshua-specific differentiators (e.g., specific neighborhoods served, response time commitment, anti-claims like "I don't take more than 4 listings at a time").
- **No specific case-file numbers** ($23,250 in seller credit, 7 days to MLS, etc. that CLAUDE.md identifies as Joshua's strong concrete patterns). The homepage has been so thoroughly inherited from realtor.com that none of Joshua's actual track record is visible.
- **Three testimonials** — Elijah Donoso (Long Beach), Connie Stone (Newport Beach), Kevin Brierton (Irvine) — exist now. Each is a 5-star card with a paragraph review. **Verify each of these is from a real client** before launch. CLAUDE.md is firm on truthfulness.

### 🟢 NICE-TO-HAVE

- **No "Book a 15-min call" CTA** on the homepage. CLAUDE.md notes that the homepage doesn't follow the brand-mode universal CTA — the funnel is the conversion mechanism. That's an intentional design choice, no change needed. But adding a small "or call (949) 438-5948 directly" link below the funnel CTA could capture call-preference users who don't want to fill a form.

---

## Section 10: Technical Hygiene

### ✅ WORKING

- **No mixed content.** Zero `http://` resource references found. All assets are HTTPS or relative.
- **No `<meta name="robots">` tag** on homepage — correctly indexable by default.
- **No console errors** detectable from static read (live verification needed for runtime errors, but code structure looks clean).
- **No 404 risk on local refs.** All 59 `/media/…` paths in HTML resolve to existing files on disk (verified earlier this session).
- **`<style>` block is inline**, no inline `style="…"` attributes detected on individual elements other than the iframe widget (acceptable).

### 🔴 BLOCKER

- **Three em dashes (U+2014) in the page.** CLAUDE.md is explicit: "Never use em dashes." All three are in a single sentence inside the "Why work with an agent?" / I'm selling tab:

  > "An agent handles everything**—**from staging and marketing to negotiating and paperwork**—**so you don't have to."

  Two em dashes in that sentence (around `from staging and marketing to negotiating and paperwork`) plus one more elsewhere in the same block. Replace with commas, parentheses, or rewrite the sentence. Search for U+2014 in the file and fix every occurrence.

### 🟡 SHOULD-FIX

- **Two `TODO` comments** in the inline funnel `<style>` block:
  - `background: #d92228; /* TODO: confirm Drozq red */` (around the `#funnel-progress-bar` rule)
  - `background: #d92228; /* TODO: confirm Drozq red */` (around the funnel submit button rule)

  Either confirm the color and remove the comment, or change the color and remove the comment. Don't ship TODOs to production.
- **Dead `batBeacon` DOM remnant** from the deleted Bing UET pixel. See Section 1.

### 🟢 NICE-TO-HAVE

- The 44-KB inline funnel script is a single IIFE; it's well-commented but it's also load-time code. Could be deferred via external file + `<script defer>` for marginal performance gain. Not urgent.

---

## Section 11: Cross-Page Link Integrity

### Findings

- **Internal links from `index.html` (excluding favicon/canonical refs): essentially zero.** The homepage doesn't link to `/about/`, `/contact/`, `/testimonials/`, `/faq/`, `/field-notes/`, `/market-insights/`, `/thank-you/` (except via the funnel JS), `/process/`, `/where-we-help/`, `/meet-the-team/`, `/los-angeles/`, `/california/`, or `/privacy/`.

This is **by design** per CLAUDE.md:

> "The homepage doesn't follow brand-mode cross-linking — its CTAs all open the funnel, and most external `<a>` are neutralized to `#top` (paid traffic stays on page)."

### ✅ WORKING

- **All external `<a href>` neutralized to `#top`** as designed. Sweep confirms no leaks to `realtor.com`, `upnest.com`, or other off-site URLs that would lose paid traffic. The only off-site links are the social URLs in the footer (`facebook.com/Drozq`, `instagram.com/drozq`, `youtube.com/@drozq`) and `tel:9494385948` — all expected.
- **Form action**: `/api/lead` resolves to `/functions/api/lead.js` Cloudflare Pages Function, which exists and is functional.
- **`/thank-you/` redirect target exists** — verified `/thank-you/index.html` is in place, has GTM, has the `lead_confirmed` script.
- **Map iframe in `/thank-you/`** points at a Google Maps embed of "Joshua Guerrero - Realtor". Working external link, expected.

### 🟡 SHOULD-FIX

- **The "How It Works", "Agent Signup", "FAQ", "Reviews", "For Sellers", "For Buyers", "Home Value", "Tips", "Login", "More" header nav links** are all present (inherited from realtor.com clone) but all point to `#top`. They're decorative and confusing — a user clicking "FAQ" expects to land on a FAQ section/page; instead they go nowhere. Either remove the irrelevant nav items, or wire the meaningful ones (FAQ → the existing `#common-questions` accordion, Login → remove). This is a UX-polish issue, not a tracking issue.

### 🟢 NICE-TO-HAVE

None.

---

## Section 12: Competitive Readiness

### Honest read

**Does the page look professional enough to charge a 3% commission on a $1.5M home?**

In its current state — **no, not quite**. The plumbing is fine but the surface still reads as a realtor.com referral page wearing a Drozq paint job. The headline says "Compare Agents", five non-existent agents are listed prominently, a fake star aggregate sits above the testimonials, and the value prop section talks about "our partner agents" plural. A $1.5M-home seller compares agent sites side-by-side — with Compass, Coldwell Banker, KW, or even another Real Brokerage agent — and the bar is high: clean photography, sharp positioning, evidence of expertise, clear point of view.

**What's working in Drozq's favor:**

- **Clean header logo** (drozq.com red house wordmark) — looks intentional, not amateur.
- **Real Drozq favicon and brand assets** are now local; visual identity is consistent with brand-mode pages.
- **Professional typography** (Galano Grotesque + Roboto from local fonts).
- **The geo-personalised "Compare agents in Irvine"** headline is actually a sharp paid-landing-page touch — most KW/Compass agents don't do this.
- **The funnel itself feels modern** — multi-step, progress bar, validation messages, proper Places autocomplete on the address.
- **Footer DRE + brokerage logo (`/thank-you/`)** are professional.

**What's eroding trust:**

- **Five fake agent profile cards** at the top — instant amateur-template tell.
- **"4.8 Out of 5 — 2k+ Customer Reviews"** unsubstantiated aggregate — instant skeptic-mode trigger for a sophisticated seller.
- **The "Compare Agents" framing fights the "Joshua Guerrero" ad copy.** A user who clicked Joshua's ad gets cognitive dissonance on landing.
- **No specific Joshua track record visible.** No case-file numbers ($23,250 in negotiated credit, 7 days to MLS, $43,250 in client savings — the strong concrete patterns CLAUDE.md identifies).
- **Three testimonials are present but no city/property specificity** that would help a seller who's evaluating "is this person actually selling in MY neighborhood?"
- **No photo of Joshua** on the homepage. Brand-mode pages have his Waist.png headshot. The conversion page should also.
- **Move-hosted market-trends iframe** still pulls realtor.com data and renders its own UI/styling — visually inconsistent with the rest of the page.

**Side-by-side with a Compass agent page** (the realistic competitor for a $1.5M Irvine seller): the Compass agent's page would lead with a striking lifestyle photo, a specific dollar-result claim (e.g., "Closed $32M+ in Irvine in 2025"), a clear named-agent identity, and a simple "Tell me about your home" form. Drozq's homepage in its current state will look generic by comparison — solid execution on the form, but the framing isn't competing on Joshua's terms.

### 🔴 BLOCKER

- **Strategic mismatch**: the homepage is structurally a referral-matching service. To compete on conversions for paid traffic that already mentions Joshua's name, the page needs to be a Joshua landing page. This is bigger than a copy edit; it likely means deprecating the agent-comparison framing and moving to a "Sell your Irvine home with Joshua" hero with the funnel as the secondary CTA.

### 🟡 SHOULD-FIX

- **Add Joshua's headshot somewhere above the fold** on the homepage. Even a small inline avatar near the form CTA changes the page's identity from "service" to "person".
- **Add 2–3 Joshua-specific stat callouts.** $43,250 in total client savings, 7-day list-to-MLS, etc. Concrete numbers > generic value props.
- **Replace the realtor.com clone tab labels** in the header (How It Works / Agent Signup / FAQ / Reviews / For Sellers / For Buyers / Home Value / Tips / Login / More) with either Drozq's nav or nothing at all. They're noise.

### 🟢 NICE-TO-HAVE

- A small 30-second video (Joshua talking) embedded near the funnel would be the single most differentiating element for a $1.5M-home seller comparing agent sites.

---

## Recommended Priority Order (Top 5)

| # | Action | Severity | Impact-to-effort |
|---|---|---|---|
| **1** | **Remove the 5 fake "partner agent" cards** + the "4.8 Out of 5 — 2k+ Customer Reviews" aggregate. Single largest credibility / Google Ads compliance fix. | 🔴 BLOCKER | High impact / Low effort |
| **2** | **Add the `<input type="text" name="company_website" …>` honeypot** to the funnel contact step. Closes the bot-spam vector and prevents inflated `lead_confirmed` events. | 🔴 BLOCKER | High impact / Trivial effort (5-min fix) |
| **3** | **Rewrite the 3 em-dash sentence** + remove the 2 TODO comments. CLAUDE.md compliance + production-cleanliness, both 1-min fixes. | 🔴 BLOCKER + 🟡 | Easy + ships |
| **4** | **Sweep `<h1>` → `<h2>`/`<h3>`** everywhere except the hero, and add `aria-label` to every funnel input. SEO + accessibility two-for-one. | 🔴 BLOCKER | Medium effort, large quality bump |
| **5** | **Add JSON-LD `RealEstateAgent` schema** in `<head>`. Required by CLAUDE.md, fast to add, improves Google Ads landing-page-quality signals + organic SEO. | 🔴 BLOCKER | Easy, durable |

After these five, the page is broadly *launch-safe*. To make it actually *competitive* against Compass / KW / Coldwell at the $1.5M-Irvine-seller level, the strategic Section 12 work needs a follow-up cycle.

---

## What's Actually Working Well (Don't Touch)

These are the items I confirmed are correctly implemented. Don't refactor them just because.

1. **GTM container `GTM-KVV3R96P`** — head + body noscript, both present, both correct.
2. **No legacy `AW-*` tags or direct `gtag.js` installations.** The "all conversion tracking flows through GTM → GA4 → Google Ads import" pattern is intact.
3. **PostHog routed through GTM** (no inline `posthog.init`). Funnel uses `posthog.capture()` for drop-off events, dual-fired through `dataLayer.push()`.
4. **gclid capture chain**: URL → 90-day cookie → sessionStorage. `gclid_captured` event pushed on every pageview to dataLayer.
5. **Funnel → `/api/lead` → `/thank-you/?ref=funnel` → `lead_confirmed` event** — full conversion path is intact in code. Single-use sessionStorage flag prevents direct/refresh/bookmark pollution.
6. **Backend `/functions/api/lead.js`** has consent gate, length guards, MailChannels integration, optional Zapier fan-out, honeypot logic (just needs the form field).
7. **Three funnel modes (Sell / Buy / Sell&Buy)** correctly registered with `attachSubmitHandler`. Funnel-mode detection via `[role=tabpanel]` ancestors works.
8. **Address validation**: `validAddressMap` WeakMap tracks Places-confirmed inputs; Sell flow requires `street_number + route` per CLAUDE.md.
9. **Funnel timeline options** match CLAUDE.md spec exactly (Sell + Sell&Buy: 4 options; Buy: 4 options including "Just looking").
10. **Open Graph + Twitter Card meta** — full set, correct image, correct site_name.
11. **Canonical** points to `https://drozq.com/` (not realtor.com).
12. **Favicons** — modern pattern (96-png + svg + ico + apple-touch + manifest), all cache-busted with `?v=20260506`.
13. **`<html lang="en">`** present.
14. **No mixed content** (zero `http://` refs).
15. **Page is indexable** (no `<meta name="robots" content="noindex">`).
16. **No `#1 agent` / `best in Irvine` / income-guarantee unsubstantiated claims** in homepage copy (the "Top-Rated Listing Agent" banner is on `/thank-you/` and brand-mode pages, not on `index.html`).
17. **CA DRE #02267255** visible in footer (×2 — desktop + mobile copies).
18. **Phone (949) 438-5948** visible in header (×2 occurrences).
19. **Local-only asset hosting** — `index.html` references zero `lt6p.com` or `static.rdc.moveaws.com` URLs (only the deferred `realtorqa.upnest.com` market-trends iframe remains, per CLAUDE.md).
20. **FAQ exclusive accordion** — opens one closes others, both directions use the same `transition: max-height 0.3s ease` so timings stay in sync.
21. **Drozq logos (header + footer)** are now local PNGs with `alt="Drozq logo"`. Header preserved at natural size; footer constrained to `25h × 165w` for layout consistency.
22. **Geo personalisation chain**: `/api/geo` → `applyGeoCity(cityState, city)` updates the headline `.geo-city` span (city only, red), the form input defaults, the visible "Irvine, CA" text nodes (hero strip + market H2), and the funnel-overlay placeholder spans. Fallback to "Irvine" / "Irvine, CA" if the API doesn't return.
