# Claude Code Instructions

*Last reviewed: April 21, 2026*

## Auto-commit

Always commit and push changes to main after completing each task without asking. Ship fast. Rollback is always available via `git revert [hash] && git push`.

When making changes to high-risk files (homepage hero, main form, tracking scripts, files containing the GTM container), include a clear, descriptive commit message so rollbacks can be surgical if needed.

## About this project

This is the codebase for drozq.com, the personal real estate website for Joshua Guerrero, a solo real estate agent based in Irvine, California. The site serves two functions that must coexist:

1. **Long-term brand asset.** Content pages (/about/, /field-notes/, /market-insights/, /testimonials/, /meet-the-team/, /faq/, /the-process/) are written and designed to compound in value over years. They are not optimized for immediate conversion. Voice, specificity, and long-tail SEO matter most here.

2. **Paid traffic conversion funnel.** The homepage and any purpose-built landing pages are optimized for Google Ads paid traffic to convert into leads. Form submission rate is the primary KPI. These pages test, iterate, and measure.

When in doubt about which mode applies: check the file path. Homepage and landing pages = conversion mode. Everything else = brand mode.

## Core operating principles

These principles apply to every task in this codebase. They are not preferences. They are constraints.

### 1. Never modify the header or footer

The header (top navigation) and footer (bottom site navigation, contact info, legal) are visually identical on every page and must remain byte-for-byte unchanged across tasks. The only acceptable exception is updating internal nav links if a URL is migrated (e.g., /blog → /field-notes/), and even then, only the link target and visible label change.

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

Every new page or section must visually match the established system used on /about/, /testimonials/, /faq/, /contact/, /field-notes/, /market-insights/, and /meet-the-team/. Specifically:

- Section labels: small, uppercase, letter-spaced 0.2em, font-size around 0.875rem
- Section headlines: clamp(1.75rem, 4vw, 3rem), bold, tight line-height
- Body copy: 1.125rem to 1.25rem, line-height 1.6
- Hero stats: clamp(2.5rem, 5vw, 4rem), bold, accent color
- Section spacing: 96px to 128px on desktop, 64px on mobile

### 6. No external image dependencies

All visuals come from the local repo:

- Images live at /media/images/
- Icons live at /media/icons/
- Headshot lives at /media/images/Waist.png

When the exact filename isn't known, use a placeholder filename and an HTML comment: `<!-- SWAP: [description of what to use] -->`. Never link to external image URLs or stock photo services.

### 7. No new external dependencies

No new CDNs, frameworks, or libraries. All JavaScript is vanilla. All styling is inline in the existing `<style>` block.

## Tracking stack (DO NOT MODIFY without explicit instruction)

The following tracking is wired into every page. Do not remove, modify, or "clean up" these without explicit instruction, even if they look like dead code:

- **Google Tag Manager container** (`GTM-KVV3R96P`): head + body snippets on every HTML page. This is the orchestrator for all other tracking.
- **GA4** (`G-XSP0L11QEY`): fires via GTM. Do not install direct gtag.js on the site. All GA4 events flow through GTM.
- **PostHog**: loads via GTM custom HTML tag, routed through reverse proxy at t.drozq.com for ad-blocker evasion. Session replay, product analytics, and web analytics are enabled.
- **Google Ads conversion tracking**: imports the `generate_lead` event from GA4. Do not install direct AW-* tags on the site. Conversion tracking is managed entirely through the GA4 → Google Ads import pipeline.
- **gclid capture script**: present on forms. Reads the `gclid` URL parameter, stores it in sessionStorage and a 90-day cookie, and populates a hidden field on form submit. This enables click-to-conversion attribution in Google Ads.

If asked to "clean up scripts" or "remove unused tags," STOP and confirm which specifically. Do not make assumptions. Direct `AW-*` gtag installations are forbidden (conversion tracking is handled via GTM + GA4 import).

The form submission flow MUST redirect to /thank-you/ on success. This redirect is what fires the `generate_lead` conversion event in GA4. Breaking this redirect silently destroys conversion measurement across the entire paid funnel.

## Form integrity (conversion-critical)

Forms are the primary conversion mechanism of the site. Breaking them is the single worst thing that can happen, and because the error mode is silent (the form appears to work but no data flows), it can go undetected for days.

For ANY page with a form (homepage, /contact/, /field-notes/, future landing pages):

- NEVER modify field names, IDs, or data attributes without verifying downstream dependencies in leads.js, the MailChannels backend, and any Google Tag Manager event triggers
- NEVER remove hidden fields (gclid, utm_*, address component parsing, lead_source)
- NEVER remove the Google Maps Places Autocomplete initialization or place_changed event handlers
- ALWAYS preserve form submission → /thank-you/ redirect
- ALWAYS preserve the timeline dropdown field on the homepage form (this is used for lead qualification)

The home page form in particular carries the bulk of paid traffic conversion. Changes there require extra caution and should be visually inspected on live site within 5 minutes of deploy.

## Forms and integrations

### Contact form (/contact/)

- Wired to MailChannels API via leads.js in the repository
- Includes a Google Maps Places Autocomplete integration on the address field
- Hidden fields capture parsed address components (street, city, state, zip) for CRM routing
- Critical: Never modify the address input's id, name, or data attributes if referenced by autocomplete initialization
- Critical: Never remove the Google Maps API script tag or place_changed event handlers

### Homepage form (main conversion form)

- Wired to the same MailChannels setup via leads.js
- Contains fields: property address, name, email, phone, timeline (dropdown), plus hidden gclid and utm_* fields
- Timeline field options: "Ready to list now" / "1-3 months" / "3-6 months" / "6+ months" / "Just curious / browsing"
- Submission redirects to /thank-you/ which fires `generate_lead` in GA4

### Field Notes subscribe form (/field-notes/)

- Wired to the same MailChannels setup via leads.js
- Lead source should be tagged distinctly (e.g., field-notes-subscribe) to distinguish from contact form leads
- Reuse existing success/error message patterns from other forms

## Favicon

Every page includes these favicon link tags in the `<head>`:

```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="shortcut icon" href="/favicon.ico">
```

Files live at the repo root: `/favicon.ico` and `/favicon.png`. Both exist. Do not modify, rename, or remove these references. Do not use absolute URLs with spaces in filenames (this was an old pattern that broke the favicon in Google Ads SERP results).

An orphan file at `/media/icons/Joshua Guerrero Favicon.png` may exist on disk. It's not referenced anywhere. Leave it alone.

## Deployment

This site auto-deploys to production via Cloudflare Pages on every push to main. There is no staging environment, no manual deploy step.

Implications:

- Pushing to main = live in 30-60 seconds
- Broken changes affect real users (and paid traffic) immediately
- Rollback is fast: `git revert [commit-hash] && git push`

When paid ad campaigns are actively running, high-risk changes (hero rewrites, form restructures, navigation changes, tracking modifications) should be:

- Committed with clear, descriptive messages
- Verified on the live site immediately after deploy
- Checked for JS errors in the browser console
- Ready to revert if anything breaks

Per the auto-commit instruction at the top of this file, commit and push directly to main. Do not create feature branches unless explicitly requested.

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

## Seller audience

The site speaks to Irvine homeowners considering selling. Under that umbrella, several archetypes exist that should be subtly acknowledged without fragmenting the site:

- **Strategic move-up / move-down** (primary): dual-income, 5 to 15 years in home, data-oriented
- **Life-event forced sellers** (divorce, relocation, medical, bankruptcy): value privacy and discretion over speed
- **Inherited-property heirs** (probate): value empathy, coordination with attorneys and siblings
- **Long-term cashing out** (retirement, downsizing): value capital gains awareness and patience
- **Investor / rental owners**: value 1031 experience and tenant-occupied listing expertise

Copy should include specific-situation acknowledgments ("Navigating probate? Divorce? Investment property with tenants?") without dedicating entire pages to each. One-sentence callouts, not sections. The goal is for each archetype to feel seen without fragmenting the copy.

## Site architecture

### Page inventory

- /index.html (home)
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
- /the-process/index.html
- /where-we-help/index.html
- /privacy-policy/index.html
- /thank-you/index.html

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
- Every page → has a primary CTA linking to /contact/ or the booking flow

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

Most sections follow this rhythm:

- Small uppercase letter-spaced label
- Large bold headline
- Body copy in 1.125rem to 1.25rem with comfortable line-height

### CTA pattern

Every page ends with a "Book a 15-minute call" CTA. This is the universal site CTA. Variants of the surrounding copy are encouraged, but the button text and destination (/contact/) should remain consistent.

On the homepage and future conversion landing pages, the primary CTA may deviate (e.g., "Get My FREE Valuation" on the hero form) but the "Book a 15-minute call" CTA should still appear near the bottom of the page as a secondary option.

## SEO and metadata standards

Every page must have:

- A unique `<title>` tag (50 to 60 characters, includes "Joshua Guerrero" or "Drozq" as brand suffix)
- A unique `<meta name="description">` (140 to 160 characters)
- A `<link rel="canonical">` pointing to the absolute URL
- Open Graph tags (og:title, og:description, og:image, og:url, og:type)
- Twitter Card tags
- Appropriate JSON-LD structured data (RealEstateAgent, Person, Article, FAQPage, Blog, BreadcrumbList as relevant)
- All `<img>` tags with descriptive alt attributes
- Non-hero images with `loading="lazy"`
- Hero images with `fetchpriority="high"`

The home page carries the RealEstateAgent Organization schema. The About page carries Person schema. Each case file carries Article and BreadcrumbList schema. The FAQ page carries FAQPage schema with all questions and answers mirrored.

Future conversion-optimized landing pages (if built) should include `<meta name="robots" content="noindex">` to prevent organic indexing, since their purpose is paid traffic only.

## Update workflow conventions

For pages that will be updated frequently (especially /market-insights/):

- Wrap every updatable value in clearly-named HTML comments: `<!-- UPDATE: [description] -->` and `<!-- END UPDATE -->`
- Include an update guide comment block at the top of the file explaining how to update values
- Structure the markup so updating one value doesn't require editing structural elements

## What this site is NOT

A few explicit anti-patterns to avoid:

- It is not a generic agent template site. Every page should have a point of view and a deliberate angle.
- It is not a volume-first lead funnel. Conversion optimization on the homepage and landing pages is welcome and intentional, but quality-of-lead matters more than quantity. The timeline qualification field on the main form is specifically designed to surface intent, not just volume.
- It is not a place for star ratings, review screenshots, or platform-aggregated social proof. The case files do this work, more credibly.
- It is not a place to mention AI, automation, or technology tooling in promotional copy. The leverage Joshua has is real, but the framing is "systems and discipline," not "I use software to do this." Technical discussions in /field-notes/ that serve the reader are fine.
- It is not a content farm. Field Notes posts and Case Files are published when there's something worth saying, not on a schedule.
- It is not a place for fake team members. Joshua is a solo agent. Partners are named by role only (brokerage, transaction coordinator, photographer, lenders, inspectors, title and escrow), not by invented personal names with stock photos.
- It is not a site where inline script tags, `gtag()` calls, or third-party pixels should appear outside the GTM container. All third-party tracking goes through GTM.
- It is not a site that should collect sensitive data in forms beyond what an agent needs to provide a valuation (address, name, contact info, timeline). No SSN, no income, no financials.

## When in doubt

If a request is ambiguous, default to:

- The pattern already established on /testimonials/, /about/, or /faq/
- The most concise, confident, sparse interpretation
- Asking for clarification rather than guessing on brand voice

If a change would affect the header, footer, or foundational `<style>` block, stop and confirm before proceeding. These are protected zones.

If a request involves the contact form, the homepage form, or the Google Maps autocomplete, stop and audit the existing implementation before modifying anything. Breaking these is the easiest way to silently degrade the most important conversion point on the site.

If a request involves "cleaning up" tracking scripts, GTM tags, gtag calls, or pixel installations, stop and confirm specifically which elements to touch. Assume nothing is dead code without verification.
