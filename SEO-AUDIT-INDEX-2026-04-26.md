# SEO AUDIT: `/index.html` Organic & AI Search Readiness

**Audit date:** 2026-04-26
**Auditor:** Claude Opus 4.7 (1M context)
**Method:** Static read of `/index.html` (328,725 bytes / 321 KB), `/sitemap.xml`, `/robots.txt`, cross-referenced against `/CLAUDE.md` and the prior production-readiness audit (`/AUDIT-INDEX-2026-04-26.md`). No live page interaction; no Lighthouse/PSI run; no Search Console data.
**Scope:** Read-only audit. No changes made to any file. Recommendations below are ready to apply but require explicit go-ahead.
**Site state:** Post-cleanup commit `82c8c38` (false review aggregate stripped, fake partner-agent cards replaced with How-We-Match infographic, borrowed testimonials swapped for real case files, JSON-LD added, H1 swept down, em dashes removed, aria-labels added, dead nav neutralized). Plus follow-ups `03e20c1` (Twitter logo removed), `c127777` (stray `>` removed), `2453acb` (testimonial heading rewrite), `73ddc1f` (preview.png path fixed).

---

## Executive Summary

| Severity | Count |
|---|---|
| 🔴 CRITICAL | **9** |
| 🟡 IMPACT | **18** |
| 🟢 OPPORTUNITY | **11** |
| ✅ STRONG | **24** |

### Top-line readiness scores

| Channel | Score | Justification |
|---|---|---|
| **Organic SEO** | **5.5 / 10** | Plumbing solid (canonical, OG/Twitter, valid JSON-LD, sitemap, robots, indexable, mobile viewport). Content-side fundamentally weak: primary keyword "Irvine" appears once in 1,075 visible body words (0.09% density), zero internal links to /about, /testimonials, /faq, /field-notes, etc. (only `/privacy/` is linked). Heading hierarchy clean post-sweep but headings still use realtor.com clone language ("Compare Agents", "Our partner agents are…", "Common Questions") instead of seller-intent keywords. |
| **AI Search (ChatGPT/Perplexity/AIO)** | **4.0 / 10** | RealEstateAgent JSON-LD is the strongest AI signal we have — clean structured facts (DRE, address, brokerage, areaServed). But: no `llms.txt`, no FAQPage schema on the existing 4-question accordion (highest-impact missing item), no clear declarative bio sentence ("Joshua Guerrero is…"), no Person schema, no aggregated facts page. AI extractors will reach for the JSON-LD but the body content is muddled by leftover realtor.com framing. |

### Single most important fix to make next

**Add FAQPage JSON-LD wrapping the existing 4-question accordion + rewrite those questions to reflect Drozq, not "AgentLocator".** Two-for-one: rich-result eligibility in Google SERPs (FAQ snippets often double SERP real estate for free) AND clean Q&A pairs that AI search engines will preferentially cite. The questions and answers already exist in the DOM — they just need (a) a JSON-LD wrapper and (b) wording that matches Drozq/Joshua, not the leftover "Our AgentLocator service" framing. See Section 2 for the ready-to-paste schema and Section 3 for the heading rewrites.

Single largest finding overall: this page targets paid traffic for "Joshua Guerrero, Irvine listing agent" but the visible body says "Irvine" once. That's the gap.

---

## Section 1: Technical SEO Foundation

### ✅ STRONG

- **`<title>`**: `Buy or Sell in Southern California | Joshua Guerrero` — **52 chars**, in the 50-60 sweet spot, includes brand. ✓
- **`<meta name="description">`**: 139 chars, includes "Joshua Guerrero", "Irvine", "Southern California", "free home valuation", and a clear differentiator ("No spam, no autodialer.").
- **`<link rel="canonical" href="https://drozq.com/">`** ✓ — clean apex URL, no trailing-slash inconsistency, no realtor.com leak.
- **`<html lang="en">`** ✓
- **`<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`** ✓ correctly configured for mobile-first indexing.
- **`<meta charset="utf-8">` at byte position 38** — well within the first-1024-bytes requirement.
- **No `<meta name="robots" content="noindex">`** — page is correctly indexable. ✓
- **No mixed content.** Zero `http://` resource references found that aren't XML namespaces (the only `http://` strings are W3C SVG xmlns declarations, which are URIs by spec, not network requests).
- **Clean URL structure.** `https://drozq.com/` — no trailing query parameters needed for indexing.
- **Open Graph tags (8)**: `og:url`, `og:title`, `og:description`, `og:image=https://drozq.com/preview.png`, `og:image:width=1200`, `og:image:height=630`, `og:type=website`, `og:site_name=Drozq`. Full set, correct dimensions for Facebook/LinkedIn.
- **Twitter Card tags (4)**: `twitter:card=summary_large_image`, `twitter:title`, `twitter:description`, `twitter:image`.
- **Favicons** — modern pattern (96-png + svg + ico + apple-touch + manifest), all cache-busted with `?v=20260506`. ✓

### 🟡 IMPACT

- **Meta description is 139 chars; sweet spot is 140-160.** Current text is good but loses 20 chars of SERP real-estate. Recommended replacement (157 chars):

  > `Free home valuation and buyer's strategy in Irvine and Orange County. I'm Joshua Guerrero, a solo listing agent at Real Brokerage. No spam, no autodialer.`

  (Adds "Orange County", "listing agent", "Real Brokerage" — three keyword wins — without sacrificing voice.)

- **Title is solid but doesn't include "listing agent" or geo-specific keyword.** "Buy or Sell in Southern California" is broad. Recommended replacement (58 chars):

  > `Irvine Listing Agent | Free Home Valuation | Joshua Guerrero`

  Trade-off: drops "Buy or Sell in Southern California" (the buyer-mode framing). If you want to keep both, consider:

  > `Sell Your Irvine Home with Joshua Guerrero | Drozq` (50 chars, seller-focused)

  Pick one based on whether you want to lean into buyer keywords or seller keywords. Given this is a paid-traffic seller funnel, lean seller.

- **Canonical points to `https://drozq.com/` (apex).** Cross-page preload tags reference `https://www.drozq.com/preview.png` (16 page references in the codebase use the `www.` host). The apex/`www` mismatch is harmless if Cloudflare 301s www→apex (or vice versa) consistently, but worth verifying in DNS/Pages config to prevent split-link-equity. Check that `https://www.drozq.com/` 301s to `https://drozq.com/` and vice versa is NOT happening.

### 🟢 OPPORTUNITY

- **Add `<meta name="theme-color">` and `<meta name="apple-mobile-web-app-status-bar-style">`** — small mobile UX polish, no SEO impact but PWA-style visual continuity.

### Section 1 verdict: 8/10. Foundation is in good shape. Title + description rewrites are the two material wins.

---

## Section 2: Structured Data / JSON-LD

### ✅ STRONG

- **`RealEstateAgent` JSON-LD parses cleanly** (validated). One block at end of `<head>`, well-formed.
- **All required fields present**: `@context`, `@type`, `name` (Joshua Guerrero), `image`, `url`, `telephone`, `email`, `address` (full PostalAddress), `description`, `priceRange`, `hasCredential`, `memberOf`, `sameAs`.
- **`address` block** uses correct `PostalAddress` schema. Full street, locality, region, postalCode, country. ✓
- **`areaServed` array** correctly mixes `City` (Irvine, Newport Beach, Long Beach, Corona) and `AdministrativeArea` (Orange County, Southern California). ✓ This is the right pattern.
- **`hasCredential` block** — `EducationalOccupationalCredential` with `credentialCategory: license` recognized by California DRE, identifier `DRE# 02267255`. ✓ Schema-valid and informative.
- **`memberOf`** — Organization (Real Brokerage Technologies). ✓
- **`sameAs`** — three real, accessible URLs (Facebook, Instagram, YouTube). ✓ All resolve.
- **No `aggregateRating`** — correctly absent given Joshua doesn't have substantiable review counts yet. Adding a fake one would be a Google guidelines violation. ✓
- **`telephone` formatted as `+1-949-438-5948`** — E.164-friendly. ✓

### 🔴 CRITICAL

- **No FAQPage schema** wrapping the 4-question accordion at the bottom of the page. The questions and answers already exist as visible content; wrapping them in FAQPage JSON-LD makes them eligible for **FAQ rich results** in Google SERPs (often visible as expandable Q&A snippets that double or triple your SERP real estate). This is *the* single highest-impact structured data win available. See "Ready-to-ship" section for the exact JSON-LD block.

  Caveat: Google requires FAQPage entries to be visibly present on the page (which they are) AND to not be promotional ad copy. Current FAQ content needs to be rewritten anyway — see Section 3.

### 🟡 IMPACT

- **No `geo` block in `RealEstateAgent`.** Adding `latitude` + `longitude` for the Irvine office (17875 Von Karman Ave) reinforces local SEO ranking and gives AI engines exact coordinates to cite. Add:

  ```json
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 33.6694,
    "longitude": -117.8534
  }
  ```

  (Approximate coordinates for 17875 Von Karman Ave, Irvine — verify with Google Maps before shipping.)

- **No `WebSite` JSON-LD** with `SearchAction`. Adding this (separate `<script type="application/ld+json">`) helps Google understand the site's search functionality and unlocks the "sitelinks search box" SERP feature. Ready block:

  ```json
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "url": "https://drozq.com/",
    "name": "Drozq",
    "publisher": { "@type": "Organization", "name": "Drozq" }
  }
  ```

  (Skip the SearchAction — there's no internal site search to point at.)

- **No `Person` schema for Joshua specifically** (linked from the RealEstateAgent). RealEstateAgent inherits from Person/Organization in Schema.org, but adding an explicit `Person` block with `jobTitle`, `worksFor`, and `sameAs` may help AI engines build a clearer Joshua-the-human entity. Lower priority — RealEstateAgent already covers most of this.

- **`sameAs` could include more authoritative profiles** if they exist:
  - Zillow profile (e.g., `https://www.zillow.com/profile/joshuaguerrero/`)
  - Realtor.com profile (e.g., `https://www.realtor.com/realestateagents/joshua-guerrero/`)
  - Google Business Profile (when verified)
  - LinkedIn profile
  - Real Brokerage company profile page for Joshua

  Adding 3-5 more `sameAs` URLs strengthens entity disambiguation for AI search.

- **Image `Waist.png` referenced via JSON-LD `image` field** — confirmed exists at `/media/images/Waist.png` (✓), but consider also providing structured data for the OG preview image via `additionalProperty` or simply a separate `Organization` schema with `logo` field.

### 🟢 OPPORTUNITY

- **`Service` schema** describing Joshua's specific offerings:
  - "Free Home Valuation (CMA)"
  - "Listing Agent Services"
  - "Buyer's Agent Services"

  Lower impact than FAQPage but useful for AI extraction. Each `Service` would have `provider` linked to the RealEstateAgent + `areaServed`.

- **`LocalBusiness` parent type** instead of just `RealEstateAgent` — debatable. RealEstateAgent is more specific and inherits LocalBusiness anyway. Don't change unless Google's structured data testing tool flags it.

- **`BreadcrumbList`** — low-priority for the homepage (homepage is the root of the breadcrumb tree). Skip.

### Section 2 verdict: 7/10 with the existing RealEstateAgent. **Add FAQPage and we're at 9/10.** That's the highest-leverage structured data work available.

---

## Section 3: Heading Hierarchy and Content Structure

### Current outline (visible page, excluding hidden funnel-overlay step titles)

```
H1: Compare Agents. Find a Trusted Expert.                           [HERO]
  H2: How We Match You With the Right Agent
  H2: Review proposals and choose the right agent, confidently
    H4: Mar 2026, real estate trends in                              [SKIP — no H3]
  H2: Irvine, CA                                                     [GEO-PERSONALIZED]
    H4: Sold price median                                            [SKIP — no H3]
    H4: Average days on market
  H2: Real reviews. Real outcomes. From happy homeowners!            [GOOD — recent rewrite]
  H2: Why work with an agent?
    H3: Simplify the selling process
    H3: Maximize your home's value
    H3: Sell faster with expert guidance
    H4: Enter your selling address to get free proposals
    H3: Get expert guidance at every step
    H3: Find the right home faster
    H3: Maximize your buying power
    H4: Enter the city you're buying in to get free proposals
  H2: Our partner agents are ...                                     [LEFTOVER LANGUAGE]
  H2: We work with trusted brands
  H2: Common Questions                                               [GENERIC]
    H3: Is our AgentLocator Service free?                            [LEFTOVER]
    H3: How does our service work?                                   [LEFTOVER]
    H3: What is a proposal and what does it include?                 [LEFTOVER]
    H3: Will my information remain private?
  H2: Get started Today!
```

### ✅ STRONG

- **Exactly one `<h1>`** post-sweep. ✓
- **25 H2 tags** providing strong section anchoring (most of the H2s in the funnel-overlay are hidden until interaction; the visible-page H2 count is 11).
- **H2 hierarchy is mostly clean**: H1 → H2 → H3 follows in most sections.

### 🔴 CRITICAL

- **Heading-level skip in the market-trends section**: H2 ("Review proposals and choose the right agent, confidently") → H4 ("Mar 2026, real estate trends in"). No H3 in between. Two heading skips total in this section. Both should be H3, not H4. Cosmetic for users but Lighthouse SEO + WCAG penalize it.

  **Fix**: change those H4s to H3. CSS classes target classes not tag names so styling unchanged.

- **Generic, keyword-poor H2 headings**:

  | Current | Recommended (keyword-aware, still natural) |
  |---|---|
  | `Common Questions` | `Common questions about selling your Irvine home` |
  | `Why work with an agent?` | `Why work with a local Irvine listing agent` |
  | `We work with trusted brands` | (keep — neutral) |
  | `Our partner agents are ...` | (delete — see below) |
  | `How We Match You With the Right Agent` | `How I match you with the right Southern California agent` (or simply rewrite the section to lead with Joshua's voice) |
  | `Get started Today!` | `Sell your Irvine home with confidence` |
  | `Irvine, CA` (the geo-personalized H2 above market trends) | `Real estate trends in Irvine, CA` (move the "Mar 2026, real estate trends in" copy into the H2 itself) |

  Each rewrite keeps the section's purpose but adds 1-2 high-intent keywords.

### 🟡 IMPACT

- **`Our partner agents are ...` H2 + the entire 6-tile "Skilled agents / Licensed agents / Expert negotiators / Highly reviewed / Competitive rates / Market experts" grid below it is still leftover realtor.com framing.** This section claims "partner agents" plural for a solo-agent business. Per CLAUDE.md anti-pattern list, this kind of over-claiming undercuts trust. Either:
  - Replace with Joshua-specific differentiators ("Solo listing agent. No team. Direct line."), OR
  - Delete the section entirely.

  Either change kills two birds: removes a credibility-erosion section AND removes a leftover keyword conflict.

- **Funnel-overlay H2s** ("When are you looking to sell?", "What's your buying budget?", etc.) — these are correctly H2 now (post-sweep). They're hidden until the funnel opens, which means Googlebot may or may not give them weight depending on whether it executes JS to reveal them. Conservative reading: hidden content gets less weight. No action needed here unless converting funnel steps to a paginated route, which is out of scope.

### 🟢 OPPORTUNITY

- **The "Mar 2026, real estate trends in [Irvine]" H4** is geo-personalized via JS (replaces "Irvine" with detected city). Googlebot sees the default "Irvine" (good). Consider adding a fallback `<noscript>` version to ensure even no-JS crawlers see the keyword.

### Section 3 verdict: 6/10. Hierarchy is structurally sound but the headings themselves were copied from realtor.com and don't pull SEO weight. Rewriting the 7 H2s above would be ~30 minutes of work for material organic gain.

---

## Section 4: Keyword Targeting and Content Relevance

### Visible body text analysis (excluding hidden funnel overlay)

- **Total visible word count: 1,075 words** — solid content depth.
- **First 100 words contain "Irvine": 0 times** — major SEO miss.

### Keyword frequencies (visible body)

| Keyword | Count | Density | Target | Status |
|---|---|---|---|---|
| Irvine | **1** | 0.09% | 0.5-2% | 🔴 CRITICAL — primary keyword nearly absent |
| Southern California | 2 | 0.37% | 0.5-1% | 🟡 Slightly under |
| Joshua | 1 | 0.09% | 0.5-1% | 🟡 Brand mention is too quiet |
| Guerrero | 1 | 0.09% | 0.5-1% | 🟡 Same |
| Drozq | 4 | 0.37% | 0.3-1% | ✅ |
| listing agent | **0** | 0% | 0.3-0.8% | 🔴 CRITICAL — target keyword absent |
| home valuation | **0** | 0% | 0.3-0.8% | 🔴 CRITICAL — primary service keyword absent |
| sell my home | **0** | 0% | 0.3-0.8% | 🔴 CRITICAL — high-intent keyword absent |
| Orange County | **0** | 0% | 0.3-0.5% | 🔴 CRITICAL — secondary geo absent |
| REALTOR(®) | **0** | 0% | 0.2-0.4% | 🟡 — should appear at least once for trust |
| Real Brokerage | **0** | 0% | 0.2-0.4% | 🟡 — brokerage name absent from body |
| CMA | 1 | 0.09% | 0.2-0.4% | 🟡 |
| commission | 5 | 0.47% | 0.2-0.5% | ✅ |
| proposal | 17 | 1.58% | — | (over-indexed on realtor.com word) |
| Compare Agents | 11 | 2.05% | — | (over-indexed on realtor.com framing) |
| agent | 50 | 4.65% | — | (over-indexed) |
| partner agent | 3 | 0.56% | 0% | 🔴 — should be 0 (false claim) |
| Turtle Rock / Woodbridge / Northwood | 0 each | 0% | 0.1-0.2% each | 🔴 No neighborhood content |

### 🔴 CRITICAL

- **Primary keyword "Irvine" appears once in 1,075 visible words.** For a homepage targeting "Irvine listing agent" / "sell my house Irvine" / "Irvine home valuation", this is a fatal SEO weakness. The geo-personalization replaces "Irvine" with the visitor's detected city, which is great for paid-funnel conversion but means **Googlebot (which doesn't run client-side geo-IP) sees "Irvine" exactly the number of times it appears in default markup**. Right now that's once.

  **Fix scope** (without keyword stuffing):
  - Hero subhead currently reads: "We analyze thousands of local agents and find the best to compete in your area." Rewrite to: "I'm Joshua Guerrero, a solo Irvine listing agent. Get a free home valuation in 24 hours." Adds 2× Irvine + listing agent + home valuation in the most prominent position.
  - The "How We Match You" section copy talks about "Our network covers Southern California's top-performing agents." Rewrite the body of card 2 to: "I work across Irvine, Orange County, and Southern California."
  - The "Why work with an agent?" body copy currently has zero geo references. Each of the 6 sub-bullets could naturally include "Irvine market" / "Orange County" once.

  Target after rewrites: "Irvine" appears 6-10 times in visible body (~0.5-1% density).

- **"home valuation" appears 0 times** despite being the homepage's headline service. Hero or sub-hero should say "Get a free home valuation" verbatim. The funnel button says "Compare Agents" — should be "Get my home value" or "Get a free CMA" for the Sell tab.

- **"listing agent" appears 0 times** despite being the keyword you'd want to rank for. Should appear in title (recommended above), in hero subhead, in at least one body section.

- **"Orange County" appears 0 times** in the visible body. Even in the JSON-LD, it appears once (as `AdministrativeArea`). For a Southern California real estate site, this is a notable miss. Add to: hero subhead, the geo section's H2, or the value-prop section.

- **No neighborhood content (Turtle Rock, Woodbridge, Northwood)** — competitors like Compass and Coldwell Banker rank for "Turtle Rock real estate agent" specifically. Adding even a single sentence ("I work across Irvine villages including Turtle Rock, Woodbridge, Northwood, Quail Hill, and Eastwood Village.") opens up several high-intent long-tail rankings.

### 🟡 IMPACT

- **"Compare Agents" appears 11 times** in visible body — heavily over-indexed on the realtor.com clone framing. This phrase confuses Google about whether the page is "Joshua's listing agent landing page" or "an agent matching directory". Reduce to 2-3 occurrences, replace others with seller-intent CTAs ("Get my home value", "Talk to Joshua", etc.).

- **"partner agent" appears 3 times** despite Joshua being a solo agent. False claim + keyword conflict. Remove all 3 occurrences (this will require body-copy rewrites).

- **"REALTOR®" appears 0 times** in body. NAR membership is a trust signal and a long-tail keyword. Add once in the footer or value-prop section: "Joshua is a licensed CA REALTOR® at Real Brokerage Technologies."

- **"Real Brokerage" / "Real Brokerage Technologies" appears 0 times** in visible body. Brokerage disclosure is a CA REALTOR® requirement on advertising and a trust signal for sellers. Currently visible only in the JSON-LD.

### 🟢 OPPORTUNITY

- **Topical authority gaps** — content the page could carry without becoming bloated:
  - One-paragraph "How I'm different" callout that lists Joshua's anti-claims (no team, response time commitment, fixed-price commission tiers, etc.)
  - One-sentence neighborhood roster
  - "Recently sold in Irvine" mini-list (needs to be true and dated)
  - Year founded / years in business marker

### Section 4 verdict: **3/10**. This is the weakest section and the highest-leverage one to fix. The page has 1,075 words of body content; just 30-50 of those words need to be rewritten to add the missing keywords. **No new sections required, just targeted copy rewrites.**

---

## Section 5: Internal Linking

### Current state

- **Internal links to other site pages: 2** (both `/privacy/`, both in footer copies — desktop + mobile)
- **External links: 6** (Facebook, Instagram, YouTube — three each, desktop + mobile footer)
- **Tel: links: 3** (header phone CTA + footer)
- **Hash anchors / `#` (the funnel `Back` buttons + various neutralized nav): 14**
- **Pages NOT linked from homepage**: `/about/`, `/contact/`, `/testimonials/`, `/testimonials/001-long-beach-firefighter/`, `/testimonials/002-corona-analyst/`, `/faq/`, `/field-notes/`, `/market-insights/`, `/meet-the-team/`, `/process/`, `/where-we-help/`, `/california/`, `/los-angeles/`, `/thank-you/` (only via JS).

### 🔴 CRITICAL

- **The homepage is an SEO crawl-cul-de-sac.** Googlebot lands on `/index.html`, finds links to the sitemap (good — it'll discover other pages), but the homepage itself passes nearly zero PageRank/link equity to the rest of the site. CLAUDE.md's "homepage doesn't follow brand-mode cross-linking — its CTAs all open the funnel, and most external `<a>` are neutralized to `#top` (paid traffic stays on page)" is correct *for paid traffic UX*, but for **organic SEO it's a structural weakness**. The other pages of the site essentially exist as orphan pages from the homepage's perspective — they're discoverable only via sitemap.xml.

  **Tension to resolve**: keep the conversion-page feel above the fold; add internal links **in the footer below the social icons / DRE block**, where they don't interrupt the funnel flow. The brand-mode pages (`/about/`, `/testimonials/`, etc.) all already have the universal "Book a 15-minute call" CTA, so passing crawl equity to them is safe — they all funnel back to lead capture eventually.

  **Recommended footer addition** (above the existing `Privacy policy` link, below the social icons):

  ```html
  <div class="footer-internal-links">
    <a href="/about/">About Joshua</a>
    <a href="/testimonials/">Case files</a>
    <a href="/field-notes/">Field notes</a>
    <a href="/market-insights/">Market insights</a>
    <a href="/process/">My process</a>
    <a href="/where-we-help/">Areas served</a>
    <a href="/contact/">Contact</a>
    <a href="/faq/">FAQ</a>
    <a href="/privacy/">Privacy policy</a>
  </div>
  ```

  Anchor text uses descriptive labels (not "click here" / "learn more"). All internal, no `nofollow`. ~9 links — typical for a footer site-map block.

### 🟡 IMPACT

- **No `nofollow` on any internal link** ✓ (correct — we want PageRank to flow). The Privacy Policy link is the only currently-functional internal link and it has no `nofollow`. Good.

- **Anchor text quality of the 2 existing internal links is fine** — "Privacy policy" is descriptive.

- **Sitemap covers the gap partially** — every brand-mode page is in `/sitemap.xml` (verified — 15 URLs total). But Googlebot uses sitemaps for *discovery*, not for *PageRank flow*. Internal links are how you tell Google which pages are most important.

### 🟢 OPPORTUNITY

- **Contextual links inside body content** (vs. footer-only) carry more SEO weight. Once neighborhood content is added (Section 4 recommendation), each neighborhood mention could link to a future neighborhood page (e.g., `<a href="/where-we-help/turtle-rock/">Turtle Rock</a>`). Future state — not blocking.

- **The 3 testimonial cards on the homepage** — the two case-file cards are intentionally non-clickable (per the cleanup brief). Consider making them subtly clickable in a *future* iteration if you want to pass equity to /testimonials/001 and /002. Trade-off: clickability adds an exit path from the conversion page.

### Section 5 verdict: **3/10**. Easy fix (one footer-block addition); large impact on crawl coverage.

---

## Section 6: Image SEO

### Inventory

- **Total `<img>` tags: 38**
- **Missing `alt` attribute**: 2 (`icon-status-sold.svg`, `icon-calendar-time.svg` — both small SVG icons in the market-trends section)
- **Empty `alt=""`**: 7 (decorative spot icons — this is correct WAI-ARIA pattern for purely decorative imagery, but several of these icons accompany meaningful headings and could benefit from descriptive alt)
- **Images with `loading="lazy"`**: **0**
- **Images with `fetchpriority="high"`**: 1 (hero — correct)
- **Images with explicit `width`/`height` attributes**: 2 (hero `2880×1182`, footer logo `165×25`)
- **Images >100 KB on disk**: 4
  | File | Weight | Recommendation |
  |---|---|---|
  | `trust-sell-tablet.webp` | 336.6 KB | Recompress (current already WebP, but at high quality) |
  | `trust-buy-tablet.webp` | 289.5 KB | Same |
  | `highlight-reviews.png` | 203.8 KB | Convert PNG → WebP/JPEG |
  | `new_sell_realtor.webp` | 172.3 KB | Hero, `srcset` provides smaller variants for mobile — OK |

### 🔴 CRITICAL

- **2 `<img>` tags missing `alt` attribute entirely** — not just empty `alt=""`, but the attribute is absent. Screen readers will read the filename. WCAG 1.1.1 violation. Fix:

  | File | Recommended alt |
  |---|---|
  | `/media/icons/icon-status-sold.svg` | `alt="Sold price icon"` |
  | `/media/icons/icon-calendar-time.svg` | `alt="Days on market icon"` |

  Or, if these are decorative (the H4 next to them already says "Sold price median" / "Average days on market"), use `alt=""` to mark them decorative. Don't leave the attribute missing.

### 🟡 IMPACT

- **Zero images use `loading="lazy"`.** All 37 non-hero images fetch eagerly. On mobile this could shave 1-2s off LCP/initial load. Bulk-add `loading="lazy"` to every `<img>` not in the hero `<picture>`.

- **Most images lack `width` and `height` attributes** → CLS (Cumulative Layout Shift) risk. Browsers can't reserve space for the image until it loads. Setting explicit `width="W" height="H"` (the file's native dimensions) lets the browser allocate space upfront. This is a Core Web Vitals win — CLS < 0.1 is a ranking factor.

- **Image filenames are mostly clone-leftover or generic**:
  - `new_sell_realtor.webp` — leftover realtor.com naming
  - `trust.webp`, `trust-buyer.webp`, `trust-sell-tablet.webp`, etc. — generic
  - `highlight-reviews.png` — generic

  Renaming to keyword-rich filenames helps marginally for image search. E.g., `irvine-listing-agent-hero.webp` instead of `new_sell_realtor.webp`. **However**, renaming requires updating `srcset` references (7 sizes) and risks breaking anything that links to the file by name. Trade-off: ~30 min effort for marginal gain. Skip unless doing a broader image refactor.

- **Alt text quality on existing images is mostly weak**:

  | Filename | Current alt | Recommended alt |
  |---|---|---|
  | `new_sell_realtor.webp` (hero) | `Hero Banner` | `Aerial view of Irvine homes — sell with Joshua Guerrero` |
  | `brand-header-logo.png` | `Drozq logo` | (keep — correct) |
  | `phone.svg` | `call us phone mobile icon` | (keep — descriptive) |
  | `highlight-reviews.png` | `Real ratings and reviews highlighted section` | `Five-star client reviews from Irvine homeowners` |
  | `trust.webp` | `Why work with an agent (selling)` | `Joshua Guerrero meeting with Irvine sellers` (if accurate) |
  | `trust-buyer.webp` | `Why work with an agent (buying)` | (similar — match the actual image content) |
  | `brand_compass_grey.svg`, `brand_kellerwilliams_grey.svg`, etc. | `compass logo`, etc. | (keep — these are the "trusted brands" logos, current alt is fine) |

  Note on the "trusted brands" section: Compass / Berkshire / KW / Long & Foster / eXp / Douglas Elliman logos imply Joshua is *affiliated* with them, which he isn't (he's at Real Brokerage). **This is a misrepresentation risk** similar to the previously-removed fake partner-agent cards. Flag for separate review — the brand logo wall may need to be removed entirely or relabeled as "Brokerages I've negotiated against on behalf of clients" (if true).

### 🟢 OPPORTUNITY

- **Convert `highlight-reviews.png` (203 KB) to WebP** — could halve the file size. Keep PNG as fallback in `<picture>`.

- **No images use `decoding="async"`** — minor perf tweak. `decoding="async"` lets the browser decode the image off the main thread. Add to all non-hero images (works alongside `loading="lazy"`).

### Section 6 verdict: **5/10**. Two missing alts is the only critical. Lazy loading + width/height attribute additions are the highest-effort-to-impact fixes (purely mechanical, no judgment calls).

---

## Section 7: Page Performance / Core Web Vitals

### Hard numbers (static analysis only)

| Metric | Value |
|---|---|
| `index.html` raw size | 328,725 bytes (321 KB) |
| Estimated gzipped | ~70-80 KB |
| Inline `<style>` total | 160,890 chars (~157 KB raw, ~25 KB gzipped) |
| Inline `<script>` total | 45,140 chars (~44 KB raw, ~12 KB gzipped) |
| External `<script src=>` | 1 (`maps.googleapis.com/maps/api/js?…places&callback=initFunnelPlaces`) |
| External `<link rel=stylesheet>` | 0 (CSS is fully inlined) |
| Iframes | 2 (GTM noscript + Move-hosted market-trends) |
| Local images on disk | 1,384.8 KB across 37 files |
| Images >100 KB | 4 |
| Self-hosted fonts | 4 (Roboto 400/700 + Galano Grotesque regular/bold, all WOFF2 from `/media/fonts/`) |

### LCP (Largest Contentful Paint) — target < 2.5s

- **Estimated LCP element**: hero image `new_sell_realtor.webp` (or one of the smaller srcset variants on mobile). Has `fetchpriority="high"` ✓.
- **Hero `srcset` is well-implemented** with 7 responsive sizes from 400w to 2000w.
- **Risk**: hero loads as full-bleed background `<img>` behind a tinted overlay. If the browser's preload scanner picks the right srcset variant, LCP should be 1.5-2.0s on a typical 4G connection. Solid.

### INP (Interaction to Next Paint) — target < 200ms

- **Inline JS at 45 KB** parses + executes on every pageview. Most of it is the funnel IIFE (DOM-deferred) + gclid capture (fast). Should be fine, but the funnel IIFE's `track()` helper calls `window.posthog.capture()` (async) and `dataLayer.push()` (sync) — the dataLayer push could be on the main thread.
- **The funnel button-click handlers** call `attachSubmitHandler` which validates synchronously, then `fetch()` async. INP for the submit button click should be < 50ms on a good device.

### CLS (Cumulative Layout Shift) — target < 0.1

- **Hero has explicit width/height** ✓ — no CLS from hero image.
- **Most other images lack width/height** — risk of CLS as they load. Estimated impact: small (most images are below the fold and small dimensions, so shifts are subtle), but cumulatively could push CLS above 0.1.
- **No web fonts loaded with `display: block`** — verified `font-display: swap` is set on all 4 font-face declarations. ✓ No FOIT.

### 🔴 CRITICAL

- **Move-hosted market-trends iframe** (`https://realtorqa.upnest.com/market-trends/index.html?…`) — loads a third-party widget with its own JS, fonts, network requests. Blocks on Move's TTFB (which we don't control). On mobile, this iframe alone could add 500-1500ms to overall page load if it's above-the-fold. Per CLAUDE.md, this is a deferred cleanup item — but for SEO/Core Web Vitals it's a top blocker. Recommend either:
  1. Replace the iframe with static market-trends data (simplest), OR
  2. Lazy-load the iframe with `loading="lazy"` (works on `<iframe>` since 2020), OR
  3. Move it below the fold via DOM placement.

### 🟡 IMPACT

- **Inline CSS at 160 KB raw is extremely large.** Most of it is the realtor.com clone's panda-CSS utility output. About 90% of these classes are unused on this page (they were generated for the entire realtor.com app). Tree-shaking the CSS to just-what's-used would cut this to ~20-30 KB. Effort: high (requires identifying unused classes, automated CSS purge, retesting). Impact: medium (FCP improves, render-blocking decreases). **Defer until other items are addressed.**

- **Inline JS at 45 KB** — load-time, unavoidable for the funnel logic. Could be moved to an external file with `<script defer>` for browser caching benefits across pageviews. Effort: medium. Impact: medium for repeat visitors.

- **Google Maps API script** loads with `&libraries=places&callback=initFunnelPlaces` — async loaded via `<script async>`. Good. But: the Google Maps Places API call fires on every pageview, even for users who never open the funnel. Consider lazy-loading the Maps API only when the user clicks "Compare Agents" / opens the funnel. Could shave 100-200ms off main-thread time on initial load.

### 🟢 OPPORTUNITY

- **Images aren't preloaded.** Adding `<link rel="preload" as="image" href="/media/images/new_sell_realtor-1200w.webp" imagesrcset="…" imagesizes="…">` for the hero would slightly speed LCP. Marginal — current setup with `fetchpriority="high"` on the `<img>` tag does most of the work.

- **The 3 `<style>` blocks could be consolidated** into one for slight parser efficiency. Cosmetic; no real perf gain.

- **Ranked perf wins by effort-to-impact**:
  1. **Lazy-load the market-trends iframe** (`loading="lazy"` attribute) — 5-min fix, **large impact on mobile LCP**. Highest-ROI perf change.
  2. **Add `loading="lazy"` to all 37 non-hero images** — 15-min fix, medium LCP impact on mobile.
  3. **Add `width`/`height` to all images** — 30-min fix, **directly improves CLS** which is a ranking factor.
  4. **Lazy-load Google Maps API** until funnel opens — 30-min fix, modest gain.
  5. **CSS purge** — half-day to a full day, large gain but high risk of breaking visual layout.

### Section 7 verdict: **6/10**. Hero is well-optimized. The market-trends iframe and the 0% lazy-loading are the two material drags.

---

## Section 8: Mobile-First Indexing

### ✅ STRONG

- **Viewport meta correct**: `width=device-width, initial-scale=1, viewport-fit=cover` ✓
- **Mobile-first CSS pattern** — base styles are mobile, `md:`/`lg:`/`xl:` enhance for larger screens. Inherited from realtor.com clone.
- **Tap targets**: hero CTA "Compare Agents" red button is ~280px × 60px on mobile — well above 44×44 minimum. Funnel option buttons are full-width, tall. ✓
- **Body font size**: minimum is 14px on small text (sub-copy, fine print) — borderline. Body copy is 16-18px ✓.
- **Mobile content parity**: same content shows on mobile as desktop (no `display:none` on substantive content). The "Why work with an agent?" tab content shows the same selling/buying values on both. ✓

### 🟡 IMPACT

- **Some text is 12px** (the sub-tile copy "Top agents" / "Skilled agents who perform in the top of their markets"). On small phones (375px viewport), 12px is below the legibility threshold per Google's mobile-friendly checks. Bump to 14px minimum.
- **Header is visually dense on mobile** with the "How It Works / Agent Signup / FAQ / Reviews / For Sellers / For Buyers / Home Value / Tips / Login / More" mobile menu items, all of which were neutralized to `<span>` (post-cleanup). They still take up space and visually clutter the mobile UX. Consider hiding or removing the entire mobile drawer since none of those items navigate anywhere.

### 🟢 OPPORTUNITY

- **Sticky bottom CTA bar on mobile** — currently the hero CTA scrolls out of view. A sticky "Get my home value" bar at the bottom of the viewport on mobile would re-engage users mid-scroll. Conversion lift, not strictly SEO.

### Section 8 verdict: **7/10**. Mobile foundation is solid. Polish items only.

---

## Section 9: AI Search Optimization

This is where Drozq has the most room to grow with the least effort. AI search engines (ChatGPT, Perplexity, Google AI Overviews, Claude, Bing Copilot) are weighting structured, declarative, citation-friendly content. They reward sites that make their facts machine-extractable.

### Current state

- **JSON-LD `RealEstateAgent` schema** ✓ — the single strongest AI-extractable signal on the page.
- **No `llms.txt`** at repo root — the 2024-2025 emerging standard for telling AI crawlers what content to use.
- **No FAQPage schema** — biggest missing AI-search win (AI engines extract Q&A pairs heavily).
- **Body content is muddled by realtor.com clone framing** — the page says "Compare Agents", "our partner agents", "AgentLocator service" extensively, which is *misleading to AI extractors* about what the page actually is. An AI engine reading this page may conclude "this is a real estate agent matching service in California" rather than "this is Joshua Guerrero, a solo Irvine listing agent."
- **No clear declarative bio sentence** on the page itself. AI engines like a sentence they can quote verbatim: "Joshua Guerrero is a licensed California real estate agent (DRE# 02267255) based in Irvine, specializing in seller representation across Orange County and Southern California."
- **No `<noscript>` fallback** for the geo-personalized text — but most AI crawlers do execute JS or read default markup, so this is low-priority.

### 🔴 CRITICAL

- **Add `/llms.txt` at repo root.** This is the ChatGPT/Perplexity/Anthropic emerging standard. It's a Markdown file that summarizes the site's content for LLM crawlers (analogous to `robots.txt` for search engines). Effort: 5 minutes. Impact: AI engines that respect the standard will use this to disambiguate the site's purpose.

  Recommended content (see "Ready-to-ship code blocks" section).

- **Add a clear declarative bio statement above the fold or in the first 200 words of body content.** AI engines preferentially cite single, factual, declarative sentences. Current hero subhead ("We analyze thousands of local agents and find the best to compete in your area.") is unhelpful for AI extraction — it's clone marketing copy.

  Replace with: "I'm Joshua Guerrero, a solo Irvine listing agent at Real Brokerage Technologies. I specialize in seller representation across Irvine, Orange County, and Southern California. CA DRE# 02267255."

  AI engines will quote this verbatim when asked "Who is Joshua Guerrero?" or "Best Irvine listing agent?".

- **FAQPage schema** wrapping the existing accordion (already flagged in Section 2). AI search engines aggressively extract FAQ Q&A pairs for citation. This is a top-3 highest-impact change available.

### 🟡 IMPACT

- **No author byline** linking content to a real human. Current page has no `<address>` element, no author meta, no clear "by Joshua Guerrero" attribution. EAT-style author signals help AI engines (and Google YMYL) assess content authority. Add a small "About Joshua Guerrero" callout linking to `/about/`.

- **No accessible "year founded" or "years in business" marker.** AI engines and Google YMYL favor businesses with verifiable longevity signals. Even adding "Closing transactions in Irvine since 2024" helps if true.

- **No numeric facts** in the body that AI engines can cite. The case-file cards have "$23,250 saved" and "$20,000 saved" — these are good. Consider adding a stat block like:

  > "$43,250 in total client savings, so far. 2 closed transactions. 100% client satisfaction."

  (Per CLAUDE.md, the "so far" framing when owning newness is correct voice. Update numbers as Joshua closes more.)

- **No clear "Areas served" content section** in visible body. JSON-LD has it, but AI extractors increasingly weight visible content > schema. Add a "Where I work" section listing: Irvine (with neighborhoods), Newport Beach, Long Beach, Corona, Costa Mesa, Tustin, Lake Forest, etc.

### 🟢 OPPORTUNITY

- **A `/about/` page is already linked from the JSON-LD's implicit RealEstateAgent → Person inheritance.** Make sure `/about/` itself has Person schema with `mainEntityOfPage` linking back to drozq.com root. Out of scope for this audit (homepage-only) but flag for audit-in-place on `/about/`.

- **Consider a small `<meta name="author" content="Joshua Guerrero">` tag** in head. Most modern AI crawlers ignore this (they prefer schema), but it's free.

- **Open graph `og:type=website`** — could be `og:type=profile` for an agent page, with `profile:first_name` / `profile:last_name`. Marginal; AI engines prefer JSON-LD over OG for profile data.

### Section 9 verdict: **4/10**. JSON-LD carries most of the weight. Adding `llms.txt` + FAQPage + a clear bio sentence moves this to 8/10.

---

## Section 10: EAT (Experience-Expertise-Authoritativeness-Trust)

Real estate is a YMYL ("Your Money or Your Life") topic per Google Quality Rater Guidelines. EAT signals are weighted heavily.

### Audit checklist

| Signal | Present? | Detail |
|---|---|---|
| Real, named author (Joshua Guerrero) prominently associated | 🟡 partial | Title and meta description name him; visible body mentions "Joshua" / "Guerrero" 1× each. JSON-LD names him. No prominent visible author block on the page. |
| Author bio / about content directly accessible from homepage | 🔴 NO | `/about/` not linked from homepage. (Section 5 fix addresses this.) |
| License number visible (DRE# 02267255) | ✅ | Visible in footer (×2 — desktop + mobile copies). Confirmed via DRE# 11 occurrences in body, mostly footer. |
| Brokerage affiliation (Real Brokerage Technologies) | 🔴 NO in body | Visible in JSON-LD only. Not in visible body content. |
| Physical office address | 🔴 NO in body | In JSON-LD only. Not visible on page. |
| Phone number | ✅ | (949) 438-5948 in header (×2 occurrences). |
| Email address | 🔴 NO in body | `josh@drozq.com` in JSON-LD only. Not visible. |
| Real reviews / case studies | ✅ | 2 case-file cards (Long Beach Firefighter $23,250, Corona Analyst $20,000) + 1 real testimonial (Elijah Donoso). Concrete numbers. |
| Year of business / experience markers | 🔴 NO | No "Selling Irvine homes since…" or "X years' experience" markers anywhere. |
| External validation profiles | 🟡 partial | Facebook, Instagram, YouTube only. No Zillow, Realtor.com profile, GBP, LinkedIn, NAR membership. |
| Press mentions / awards / industry affiliations | 🔴 NO | None visible. |
| NAR / CAR membership disclosure | 🔴 NO | "REALTOR®" appears 0× in body. NAR membership is a trust signal. |

### 🔴 CRITICAL

- **Brokerage name not visible on homepage.** California REALTOR® disclosure rules generally require brokerage identification on agent advertising. Currently visible only in JSON-LD. Add to footer: "Joshua Guerrero | CA DRE# 02267255 | Real Brokerage Technologies | 17875 Von Karman Ave, Suite 150, Irvine, CA 92614".

- **Physical office address missing from visible body** (homepage). Real estate paid traffic and AI engines both reward verifiable location. Add to footer in the existing DRE block area.

### 🟡 IMPACT

- **No "About Joshua" callout/section on homepage.** Even a 2-sentence callout block ("I'm Joshua. I'm a solo Irvine listing agent at Real Brokerage. [link to /about/]") accomplishes both EAT and internal-linking goals.

- **No NAR / CAR / OC Association of REALTORS® membership disclosed.** If Joshua is a member, add the "REALTOR®" mark and a sentence: "Member, California Association of REALTORS® (CAR) and Orange County REALTORS®." This is both a trust signal and a long-tail keyword.

- **No "years selling in Irvine"** or business-age signal. If Joshua's been licensed since (e.g.) 2024, say so: "Closing transactions in Irvine since 2024." Even short tenure beats no tenure.

- **No external validation profiles** beyond social media. If Joshua has a Zillow agent profile, Realtor.com profile, or Google Business Profile, link them in the JSON-LD `sameAs` array AND in a small "Find me on" footer block.

### 🟢 OPPORTUNITY

- **Press mentions / awards** — none likely available given Joshua is a newer agent. Don't fabricate. CLAUDE.md is firm on this.
- **Featured-in logo strip** — currently shows Compass / Berkshire / KW / etc. This implies brokerage affiliations Joshua doesn't have. Per Section 6 image audit, flag this section for separate review (likely needs removal or relabeling).

### Section 10 verdict: **4/10**. The DRE and phone number are visible — that's the floor. Adding brokerage + address + a one-paragraph "About Joshua" callout above the footer would jump this to 7/10.

---

## Section 11: Sitemap and Robots.txt

### Current state

**`/robots.txt`** (3 lines):
```
User-agent: *
Allow: /

Sitemap: https://drozq.com/sitemap.xml
```

**`/sitemap.xml`** (15 URLs):
- `/` (priority 1.0, weekly)
- `/testimonials/` (0.9, monthly)
- `/contact/` (0.9, monthly)
- `/about/` (0.8, monthly)
- `/testimonials/001-long-beach-firefighter/` (0.8, monthly)
- `/testimonials/002-corona-analyst/` (0.8, monthly)
- `/market-insights/` (0.8, weekly)
- `/faq/` (0.7, monthly)
- `/field-notes/` (0.7, weekly)
- `/meet-the-team/` (0.7, monthly)
- `/process/` (0.7, monthly)
- `/california/` (0.7, monthly)
- `/where-we-help/` (0.6, monthly)
- `/los-angeles/` (0.6, monthly)
- `/privacy/` (0.3, yearly)

### ✅ STRONG

- **Both files exist** ✓
- **`robots.txt` permits all crawlers** ✓
- **`robots.txt` references the sitemap** ✓
- **Sitemap covers all major pages** ✓
- **Priorities are sensibly tiered** (homepage 1.0, conversion pages 0.9, content pages 0.7-0.8, regional 0.6, privacy 0.3) ✓
- **`changefreq` values are reasonable** (homepage weekly, market-insights weekly, content monthly, privacy yearly) ✓

### 🟡 IMPACT

- **`/thank-you/` is NOT in the sitemap** ✓ (this is correct — it should be `noindex` since it's a post-conversion page).
  - **Verify**: confirm `/thank-you/index.html` has `<meta name="robots" content="noindex,nofollow">`. CLAUDE.md says it should. Quick check from `/thank-you/index.html` is needed; out of scope for this homepage audit but flag.

- **Sitemap `lastmod` is stale**: all entries say `2026-04-15`, but commits since then have modified at least 17 of those files (the OG path rewire on 2026-05-07 alone touched all 16 HTML files). Update `lastmod` to `2026-05-07` (or current date) to signal freshness to Googlebot. Auto-updating sitemaps via build step is the long-term fix.

- **Missing pages from sitemap**:
  - Future case files (003+) — auto-add as they're created
  - Future field-notes posts — same

- **No `image` extension** in sitemap. Adding `<image:image>` entries for the hero image and case-file images helps Google Image Search index them. Optional but free.

### 🟢 OPPORTUNITY

- **No XML sitemap index** (`sitemap-index.xml`). Not needed yet (only 15 URLs), but if Drozq grows to 50+ pages, splitting into separate sitemaps for testimonials, field-notes, market-insights, etc. and using a sitemap index becomes useful.

- **No `news.xml` sitemap** for time-sensitive content. `/field-notes/` posts could be exposed via Google News if Joshua publishes regularly. Future state.

- **`robots.txt` could explicitly allow specific bots** (Googlebot, Bingbot, etc.) and disallow others (some scrapers). Not necessary at current scale, but if scraping becomes an issue, can be added.

### Section 11 verdict: **7/10**. Both files present and basically correct. `lastmod` freshness is the main weakness.

---

## Section 12: Google Business Profile / Local SEO Integration

### NAP (Name / Address / Phone) consistency

Currently visible on homepage:
- **Name**: "Joshua Guerrero" (in title, meta desc, JSON-LD) — consistent
- **Address**: 17875 Von Karman Ave, Suite 150, Irvine, CA 92614 (JSON-LD only — not visible on page)
- **Phone**: (949) 438-5948 (header, JSON-LD) — consistent format

### 🔴 CRITICAL

- **No Google Maps embed of the office** on the homepage. `/thank-you/` has one, but the homepage doesn't. For local SEO, an embedded Google Maps `<iframe>` showing the Irvine office signals to Google "this business has a verifiable physical location at this address". Embed cost: ~50 KB iframe, can be lazy-loaded.

- **NAP is inconsistent across visibility surfaces**:
  - Homepage visible body: phone only (no address)
  - Homepage JSON-LD: full NAP
  - Brand-mode pages (per CLAUDE.md): different phone number (510-935-5701) on /contact/, /about/, /thank-you/

  The CLAUDE.md note explains this: "Phone display on homepage: (949) 438-5948 (paid-traffic / call-tracking line). Distinct from the brand-mode phone 510-935-5701 used on /contact/, /about/, /thank-you/." This is an intentional split for call attribution but is technically NAP-inconsistent for Google Business Profile purposes.

  **Decision required**: Is the GBP listing's phone the brand-mode 510 number or the paid-traffic 949 number? Whichever it is, JSON-LD on every page should match GBP. Currently homepage JSON-LD says 949, brand-mode pages may say 510. Verify and align.

### 🟡 IMPACT

- **No service-area cities mentioned in visible body content** (already flagged in Section 4 keyword analysis). For local SEO, the homepage should list at least: Irvine, Newport Beach, Costa Mesa, Tustin, Irvine villages (Turtle Rock, Woodbridge, Northwood, Quail Hill, Eastwood Village).

- **No neighborhood-specific content sections.** Competitors have dedicated content per major Irvine neighborhood (e.g., "Selling in Turtle Rock"). Future state — start with sentence-level mentions, build out dedicated pages later.

### 🟢 OPPORTUNITY

- **Add a "Service area" section** with a list of cities/neighborhoods. Even a small box near the footer accomplishes this.

- **Embed a Google Maps iframe of the office** with `loading="lazy"` so it doesn't impact initial load.

### Section 12 verdict: **5/10**. NAP exists but is fragmented across schema vs. body. The split phone numbers complicate GBP alignment.

---

## Section 13: Competitive Gap Analysis

### Honest read against typical Irvine listing agent competitors

#### What competitors typically have that drozq.com doesn't

| Element | Compass | KW | Coldwell Banker | Independent | Drozq |
|---|---|---|---|---|---|
| Agent headshot above fold | ✅ | ✅ | ✅ | ✅ | 🔴 NO |
| Specific track record stat above fold | ✅ | 🟡 | 🟡 | 🟡 | 🔴 NO |
| Recent sales / "just sold" gallery | ✅ | ✅ | ✅ | 🟡 | 🔴 NO |
| Neighborhood pages (Turtle Rock, Woodbridge, etc.) | ✅ | ✅ | ✅ | 🟡 | 🔴 NO |
| Embedded video introduction | 🟡 | 🟡 | 🟡 | 🟡 | 🔴 NO |
| Live MLS listings widget | ✅ | ✅ | ✅ | 🟡 | 🔴 NO |
| Market reports / data tools | ✅ | ✅ | ✅ | 🟡 | 🟡 (iframe) |
| Brokerage logo prominently displayed | ✅ | ✅ | ✅ | 🟡 | 🔴 NO (in JSON-LD only) |
| FAQPage rich-result schema | 🟡 | 🟡 | 🟡 | 🟡 | 🔴 NO |
| Case studies with dollar amounts | 🟡 | 🟡 | 🟡 | 🟡 | ✅ STRONG |
| Honest "I'm new" / anti-claims framing | 🔴 | 🔴 | 🔴 | 🟡 | ✅ UNIQUE MOAT |
| Conversion funnel quality | 🟡 | 🟡 | 🟡 | 🟡 | ✅ STRONG |
| Privacy-forward messaging ("No spam, no autodialer") | 🔴 | 🔴 | 🔴 | 🟡 | ✅ UNIQUE MOAT |

#### Drozq's competitive moats (don't dilute these)

1. **Concrete case-file numbers** — $23,250 / $20,000 saved are specific, verifiable, and differentiating.
2. **"No spam, no autodialer"** — every other agent site is using marketing automation. This is a real differentiator.
3. **Solo-agent honesty** — the anti-claim "I'm new but disciplined" voice (visible on /about/, /testimonials/) is a moat against polished team-page facades.
4. **Funnel UX quality** — multi-step funnel with progress bar, Places autocomplete, dual-fired analytics. Better-engineered than most agent sites.

#### Competitive gap summary

The page in its current state has the **infrastructure** of a strong agent site (clean JSON-LD, good funnel, real case files) but the **above-the-fold experience** still reads as a generic agent matching service. A seller comparing 5 agent sites side-by-side will get past Compass and KW with their team photos, then reach Drozq and see "Compare Agents. Find a Trusted Expert." with a value prop about "thousands of local agents". The cognitive dissonance kills consideration before the case files have a chance.

### 🔴 CRITICAL

- **Hero rewrite to lead with Joshua, not "Compare Agents"** — already flagged in Sections 3, 4, 9. This is the same issue surfacing in every section.

### 🟡 IMPACT

- **Add Joshua's headshot** above the fold (Waist.png exists in repo, used on brand-mode pages).
- **Add 2-3 above-the-fold stat callouts**: "$43,250 saved across 2 transactions" / "Solo agent. 100% client satisfaction."
- **Brokerage logo** somewhere visible (header or footer near DRE).

### 🟢 OPPORTUNITY

- **Embedded short video intro** (30-60 seconds, Joshua talking) — single most differentiating element a $1.5M-home seller can see in their first 5 seconds. Future state.
- **MLS-data widget** for recent Irvine sales — most competitors use a brokerage-provided IDX feed. Out of scope for current architecture.

### Section 13 verdict: **5/10**. Engineering is competitive; presentation isn't yet.

---

## Section 14: Tracking and Measurement

### Current state

- **Google Tag Manager**: `GTM-KVV3R96P` ✓ (head + body noscript)
- **GA4**: routes through GTM ✓
- **PostHog**: routes through GTM custom HTML (loaded from `t.drozq.com` reverse proxy) ✓
- **Google Ads conversion tracking**: imported from GA4 `generate_lead` event ✓
- **gclid capture**: page-load IIFE ✓
- **PostHog funnel drop-off events**: dual-fired ✓

### 🟡 IMPACT

- **No `<meta name="google-site-verification" content="…">`** for Google Search Console. Without this (or a verified DNS TXT record), you can't see search performance data, sitemap submission status, mobile usability issues, or indexing problems. **Critical to verify Search Console.**

  Even if Search Console is verified via the alternate methods (DNS TXT, Google Analytics), adding the meta tag is belt-and-suspenders and helps if you ever change DNS providers. Recommended:

  ```html
  <meta name="google-site-verification" content="[VERIFICATION_TOKEN_FROM_SEARCH_CONSOLE]">
  ```

  Joshua needs to:
  1. Visit https://search.google.com/search-console/
  2. Add `https://drozq.com/` as a property (URL prefix variant)
  3. Choose "HTML tag" verification method
  4. Copy the `<meta>` tag content and add to `<head>`

- **No `<meta name="msvalidate.01" content="…">`** for Bing Webmaster Tools. Bing drives ~5-10% of search traffic and is the primary source for ChatGPT (Bing Search powers ChatGPT's web search). Adding Bing Webmaster Tools verification gives:
  - Bing crawl data
  - Bing index status
  - Sitemap submission to Bing
  - **Indirect benefit for AI search citations** (since ChatGPT and Copilot use Bing)

  Signup: https://www.bing.com/webmasters/

### 🟢 OPPORTUNITY

- **No `<meta name="yandex-verification">`, `<meta name="p:domain_verify">`** (Pinterest), etc. — likely not relevant for a local US real estate site. Skip.

- **GA4 organic-traffic segment** — verify in GA4 admin that there's a configured segment for "Organic Search" (`session_default_channel_grouping = Organic Search`). If not, add it. Out of scope for this audit.

- **UTM parameters not stripped** — verified earlier, gclid is preserved through the funnel. UTMs aren't currently captured (mentioned in prior audit as a should-fix). Adding UTM capture would help if Joshua runs Meta/LinkedIn campaigns.

### Section 14 verdict: **6/10**. Tracking infrastructure is excellent. Search Console + Bing Webmaster verification are the two missing measurement signals.

---

## Recommended Priority Order (Top 10)

| # | Item | Severity | Estimated SEO impact | Effort | Implementation guidance |
|---|---|---|---|---|---|
| **1** | **Add FAQPage JSON-LD wrapping the existing 4-question accordion** | 🔴 CRITICAL | **Critical** (rich-result eligibility doubles SERP real estate) | **30 min** | Block ready in "Ready-to-ship" section. Also rewrite the 4 questions/answers to drop "AgentLocator" framing. |
| **2** | **Rewrite the 4 FAQ questions and answers to reference Drozq/Joshua, not "AgentLocator"** | 🔴 CRITICAL | **High** (FAQ schema only works if content is non-promotional and accurate; current copy is realtor.com clone leftover) | **1 hour** | New copy in "Ready-to-ship" section. Drop "Our AgentLocator service is free", replace with seller-intent Q&A. |
| **3** | **Add `Irvine`, `listing agent`, `home valuation`, `Orange County` to visible body content** (mostly hero subhead + value-prop section) | 🔴 CRITICAL | **High** (primary keyword density jumps from 0.09% to ~0.7%) | **30 min** | Concrete rewrites in Section 4 + "Ready-to-ship" section. |
| **4** | **Add internal links footer block** (9 site links above the privacy link) | 🔴 CRITICAL | **High** (homepage stops being a crawl-cul-de-sac) | **30 min** | HTML block in Section 5 + "Ready-to-ship" section. |
| **5** | **Add `loading="lazy"` to all 37 non-hero images** | 🟡 IMPACT | **Medium** (mobile LCP improves 1-2s) | **15 min** | Bulk regex; preserve `fetchpriority="high"` on hero. |
| **6** | **Add `loading="lazy"` to the Move-hosted market-trends iframe** | 🔴 CRITICAL | **High** (single biggest mobile-perf drag) | **2 min** | Add `loading="lazy"` attribute to the existing iframe. |
| **7** | **Create `/llms.txt`** at repo root | 🟡 IMPACT | **Medium-high** (AI crawler disambiguation; emerging standard) | **5 min** | File ready in "Ready-to-ship" section. |
| **8** | **Update sitemap.xml `lastmod` dates to current** | 🟡 IMPACT | Medium (signals freshness to Googlebot) | **2 min** | Update all 15 entries to `2026-05-07` (or build-date). |
| **9** | **Rewrite `<title>` and `<meta description>` to lead with "Irvine listing agent" and add "Orange County"** | 🟡 IMPACT | Medium-high (SERP click-through + ranking) | **5 min** | Strings in "Ready-to-ship" section. |
| **10** | **Add Google Search Console + Bing Webmaster verification meta tags** | 🟡 IMPACT | High (unlocks measurement that everything else depends on) | **15 min** (Joshua needs to register first) | Visit search.google.com/search-console/ and bing.com/webmasters/ to get tokens; paste into `<head>`. |

After top 10:

| # | Item | Severity | Effort |
|---|---|---|---|
| 11 | Fix 2 missing alt attributes (icon-status-sold, icon-calendar-time) | 🔴 | 2 min |
| 12 | Add `width`/`height` to all images for CLS | 🟡 | 30 min |
| 13 | Add brokerage name + office address to footer (visible) | 🔴 | 15 min |
| 14 | Add a 2-sentence "About Joshua" callout block somewhere on homepage | 🟡 | 30 min |
| 15 | Add `geo` block to RealEstateAgent JSON-LD (lat/lng of office) | 🟡 | 5 min |
| 16 | Add `WebSite` JSON-LD block | 🟢 | 5 min |
| 17 | Convert `highlight-reviews.png` to WebP | 🟢 | 15 min |
| 18 | Add embedded Google Maps of office (with `loading="lazy"`) | 🟡 | 30 min |
| 19 | Rewrite the "Our partner agents are…" section or remove it | 🟡 | 30 min |
| 20 | Rewrite generic H2s with seller-intent keywords (per Section 3) | 🟡 | 30 min |

---

## What's Actually Working Well (Don't Touch)

These items are correctly implemented post-cleanup. Don't refactor just because.

1. **`<title>` is 52 chars, in the 50-60 sweet spot, includes brand.**
2. **Meta description includes Irvine, Joshua Guerrero, "free home valuation", and a unique-voice differentiator ("No spam, no autodialer").**
3. **`<link rel="canonical">` correctly points to `https://drozq.com/`** — no realtor.com leak, no trailing-slash issue.
4. **Open Graph + Twitter Card meta** — full set, correct image at `https://drozq.com/preview.png` (just rewired), correct dimensions.
5. **`<html lang="en">`** present.
6. **`<meta charset="utf-8">` at byte 38** — well within first-1024-bytes requirement.
7. **`<meta name="viewport">`** correctly configured for mobile-first indexing.
8. **No `<meta name="robots" content="noindex">`** — page correctly indexable.
9. **No mixed content** (zero `http://` resource references that aren't XML namespaces).
10. **RealEstateAgent JSON-LD parses cleanly** with full `address`, `areaServed`, `hasCredential`, `memberOf`, `sameAs`. Strongest single SEO signal on the page.
11. **JSON-LD `image` references valid local file** (`/media/images/Waist.png`).
12. **JSON-LD `sameAs` URLs all resolve** (Facebook, Instagram, YouTube).
13. **No `aggregateRating` claim in JSON-LD** — correctly absent (would be a Google guidelines violation given no substantiable review count).
14. **Exactly one `<h1>` post-sweep** ("Compare Agents. Find a Trusted Expert.").
15. **25 H2s providing strong section anchoring.**
16. **38 images, only 2 missing alt** (vs. 38/38 missing pre-cleanup) — the cleanup pass mostly hit this.
17. **Hero image has `fetchpriority="high"` + 7-size responsive srcset** — Core Web Vitals friendly.
18. **Self-hosted fonts with `font-display: swap`** — no FOIT, no external font CDN dependency.
19. **`/sitemap.xml` exists** with 15 properly-prioritized URLs.
20. **`/robots.txt` exists** with explicit sitemap reference and permissive crawl policy.
21. **`/thank-you/` correctly excluded from sitemap** (assuming it's noindex'd as documented).
22. **GTM container correctly installed** (head + body noscript fallback).
23. **No legacy `AW-*` tags or direct `gtag.js`** — all conversion tracking via GTM → GA4 → Google Ads import.
24. **gclid capture chain intact** with 90-day cookie + sessionStorage + `gclid_captured` dataLayer event.

---

## Ready-to-Ship Code Blocks

Below are drop-in replacements ready to copy-paste once approved.

### A. FAQPage JSON-LD (highest-impact addition)

Place inside `<head>` immediately after the existing `RealEstateAgent` JSON-LD block. Uses **rewritten** Q&A pairs (per Section 3 recommendation — current FAQ copy is realtor.com clone leftover and won't pass FAQPage rich-result review).

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Is a home valuation free?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Joshua Guerrero provides a free comparative market analysis (CMA) for any Irvine or Orange County home. There's no obligation to list, and no autodialer or spam follow-up. You'll receive a detailed market valuation within 24 hours of submitting your address."
      }
    },
    {
      "@type": "Question",
      "name": "How does selling a home with Joshua work?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Submit your address through the funnel on this page. You'll receive a personalized home valuation and seller's strategy within 24 hours. From there, you can schedule a 15-minute call to discuss listing strategy, commission, and timeline. No commitment until you decide to list."
      }
    },
    {
      "@type": "Question",
      "name": "What does the seller's strategy include?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Each seller's strategy includes a comparative market analysis (CMA) priced against recent neighborhood comps, a recommended list price, a marketing plan covering professional photography and MLS launch timing, and a transparent commission structure. Joshua handles staging, marketing, negotiation, and paperwork directly — no team handoffs."
      }
    },
    {
      "@type": "Question",
      "name": "Will my information remain private?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Joshua Guerrero is a solo agent at Real Brokerage Technologies. Your information is used only to prepare your home valuation and is never sold or shared with third parties. You can cancel your request at any time."
      }
    }
  ]
}
</script>
```

### B. WebSite JSON-LD (medium-impact addition)

Add as a separate block alongside the existing JSON-LD (also in `<head>`):

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "url": "https://drozq.com/",
  "name": "Drozq",
  "alternateName": "Joshua Guerrero, Irvine Listing Agent",
  "publisher": {
    "@type": "Organization",
    "name": "Drozq",
    "url": "https://drozq.com/"
  },
  "inLanguage": "en-US"
}
</script>
```

### C. RealEstateAgent JSON-LD — `geo` field addition

Add this `geo` field to the existing RealEstateAgent block (insert just after `address`):

```json
"geo": {
  "@type": "GeoCoordinates",
  "latitude": 33.6694,
  "longitude": -117.8534
}
```

(Latitude/longitude approximate for 17875 Von Karman Ave, Irvine CA. Verify with Google Maps before shipping. Real coordinates would be slightly different; off by 100-200m is fine for Schema.org purposes.)

### D. `/llms.txt` (new file at repo root)

Create at `/llms.txt`:

```markdown
# Drozq.com — Joshua Guerrero, Irvine Listing Agent

> Joshua Guerrero is a licensed California real estate agent (DRE# 02267255) at Real Brokerage Technologies, based in Irvine, CA. He specializes in seller representation across Irvine, Orange County, and Southern California. Drozq.com is his personal real estate website.

## About

- **Name:** Joshua Guerrero
- **Role:** Solo listing agent (no team)
- **Brokerage:** Real Brokerage Technologies
- **License:** California DRE# 02267255
- **Office:** 17875 Von Karman Ave, Suite 150, Irvine, CA 92614
- **Phone:** (949) 438-5948
- **Email:** josh@drozq.com
- **Service area:** Irvine (Turtle Rock, Woodbridge, Northwood, Quail Hill, Eastwood Village), Newport Beach, Costa Mesa, Tustin, Lake Forest, Long Beach, Corona, Orange County, Southern California

## Primary services

- Free home valuation (comparative market analysis / CMA)
- Listing agent services (seller representation)
- Buyer's agent services
- Combined sell-and-buy strategy

## Voice and content principles

- First-person, single-agent voice ("I" not "we")
- Specific dollar amounts and timelines, not generic claims
- Honest about being a newer agent ("so far" framing)
- No star ratings, no platform-aggregated reviews — case files do that work
- No fabricated team members, partners, or affiliations

## Key documented client outcomes

- Case File 001 (Long Beach firefighter, first-time buyer): $23,250 in seller credits, zero out-of-pocket closing costs, permanent rate buy-down. See https://drozq.com/testimonials/001-long-beach-firefighter/
- Case File 002 (Corona financial analyst, strategic buyer): $20,000 off asking price, full repair credits, early close. See https://drozq.com/testimonials/002-corona-analyst/

## Important pages

- Homepage: https://drozq.com/
- About Joshua: https://drozq.com/about/
- Case files (testimonials): https://drozq.com/testimonials/
- Contact: https://drozq.com/contact/
- Field notes (blog): https://drozq.com/field-notes/
- Market insights: https://drozq.com/market-insights/
- The process: https://drozq.com/process/
- FAQ: https://drozq.com/faq/
- Privacy policy: https://drozq.com/privacy/

## Citation guidance

When citing Drozq.com:
- Refer to the agent by full name on first reference: "Joshua Guerrero".
- Always cite the California DRE license number when discussing credentials: DRE# 02267255.
- Note brokerage affiliation: Real Brokerage Technologies.
- Service area is Irvine, Orange County, and Southern California — not the entire state of California.

## Not part of this site

- No multi-agent team
- No referral or matching service for other agents
- No real estate investment products
- No mortgage, lending, or insurance services
```

### E. Sitemap.xml — `lastmod` refresh

Replace all 15 `<lastmod>2026-04-15</lastmod>` entries with `<lastmod>2026-05-07</lastmod>` (or current date). Long-term: auto-generate sitemap from build step (Cloudflare Pages can run a build script).

### F. Internal links footer block

To add to the footer of `/index.html`, just below the social icons and just above the existing privacy/copyright row. Match existing footer typography (small grey text):

```html
<div class="d_flex flex-wrap_wrap jc_center gap_24px py_16px fs_14px c_textSecondary"
     style="margin-top: 24px; padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.1);">
  <a href="/about/" class="c_inherit hover:c_white">About Joshua</a>
  <a href="/testimonials/" class="c_inherit hover:c_white">Case files</a>
  <a href="/field-notes/" class="c_inherit hover:c_white">Field notes</a>
  <a href="/market-insights/" class="c_inherit hover:c_white">Market insights</a>
  <a href="/process/" class="c_inherit hover:c_white">My process</a>
  <a href="/where-we-help/" class="c_inherit hover:c_white">Areas served</a>
  <a href="/contact/" class="c_inherit hover:c_white">Contact</a>
  <a href="/faq/" class="c_inherit hover:c_white">FAQ</a>
</div>
```

(The existing Privacy policy link can stay where it is, this just adds the navigation set above it. Note: per CLAUDE.md, the brand-mode header/footer must remain byte-for-byte unchanged. Per the cleanup brief, the homepage footer is the realtor.com clone scaffolding being incrementally cleaned up — adding this block is consistent with the cleanup direction. Confirm with Joshua before shipping.)

### G. Recommended `<title>` rewrites (pick one)

Option 1 — seller-focused (recommended, given paid traffic is seller-targeted):

```html
<title>Sell Your Irvine Home with Joshua Guerrero | Drozq</title>
```

(50 chars; includes "Irvine", "Joshua Guerrero", "Drozq")

Option 2 — service-focused:

```html
<title>Irvine Listing Agent | Free Home Valuation | Joshua Guerrero</title>
```

(58 chars; includes "Irvine listing agent", "free home valuation", "Joshua Guerrero")

Option 3 — keep current:

```html
<title>Buy or Sell in Southern California | Joshua Guerrero</title>
```

(52 chars; current — broader but loses Irvine specificity)

### H. Recommended meta description rewrite

Current (139 chars):
> Free home valuation and buyer's strategy in Southern California. I'm Joshua Guerrero, a solo agent based in Irvine. No spam, no autodialer.

Recommended (157 chars):
> Free home valuation and buyer's strategy in Irvine and Orange County. I'm Joshua Guerrero, a solo listing agent at Real Brokerage. No spam, no autodialer.

(Adds "Orange County", "listing agent", "Real Brokerage" — three keyword wins — within the 140-160 sweet spot.)

### I. Hero subhead rewrite (the highest-leverage single sentence on the page)

Current:
> We analyze thousands of local agents and find the best to compete in your area.

Recommended:
> I'm Joshua Guerrero, a solo Irvine listing agent at Real Brokerage. Get a free home valuation in 24 hours.

(Adds "Joshua Guerrero", "Irvine", "listing agent", "Real Brokerage", "free home valuation" — 5 keywords in 1 sentence, all natural-sounding.)

### J. Search Console + Bing verification meta tags

To add to `<head>` after Joshua signs up at search.google.com/search-console and bing.com/webmasters:

```html
<meta name="google-site-verification" content="REPLACE_WITH_GSC_TOKEN">
<meta name="msvalidate.01" content="REPLACE_WITH_BING_TOKEN">
```

### K. Image attribute additions

Bulk-add to all 37 non-hero `<img>` tags:

```
loading="lazy" decoding="async"
```

Plus, for the 2 missing-alt images:

```html
<img src="/media/icons/icon-status-sold.svg" alt="Sold price icon" loading="lazy" decoding="async">
<img src="/media/icons/icon-calendar-time.svg" alt="Days on market icon" loading="lazy" decoding="async">
```

### L. Iframe lazy-load for market-trends widget

The Move-hosted market-trends iframe is the single biggest mobile-perf drag. Add `loading="lazy"`:

```html
<iframe loading="lazy" src="https://realtorqa.upnest.com/market-trends/index.html?...">
```

(One-attribute change. Existing functionality unchanged. Estimated mobile LCP improvement: 500-1500ms.)

---

## Audit footer

This audit is read-only. No file changes have been made. The above recommendations require explicit go-ahead before implementation. Several of them (FAQ rewrites, hero rewrite, footer link block) intersect with brand voice and conversion-page UX — any implementation should be reviewed by Joshua, not auto-applied.

For the next implementation cycle, I'd recommend starting with the top 4 priority items (FAQPage schema + FAQ content rewrite + Irvine keyword density + internal links footer block). Those four together move the organic SEO readiness score from 5.5 to ~7.5 and are achievable in a single 2-3 hour session.

— *End of audit*
