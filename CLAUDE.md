# Claude Code Instructions

## Auto-commit
Always commit and push changes after completing each task without asking.
About this project
This is the codebase for drozq.com, the personal real estate website for Joshua Guerrero, a solo real estate agent based in Irvine, California. The site is a long-term brand-building asset, not a short-term lead funnel. Every decision should be made through the lens of "is this building a brand that compounds over time?"
The site is structured as a multi-page static HTML site with a shared <style> block, a consistent header and footer across all pages, and a growing system of content sections (case files, market insights, FAQ, field notes, etc.).

Core operating principles
These principles apply to every task in this codebase. They are not preferences. They are constraints.
1. Never modify the header or footer
The header (top navigation) and footer (bottom site navigation, contact info, legal) are visually identical on every page and must remain byte-for-byte unchanged across tasks. The only acceptable exception is updating internal nav links if a URL is migrated (e.g., /blog → /field-notes/), and even then, only the link target and visible label change.
2. Never use em dashes
The single most common style mistake to watch for. Use commas, periods, parentheses, or colons instead. Run a final pass on every output to confirm zero em dashes (—) exist. The character to search for is U+2014.
3. Mobile-first, always
Every page must render intentionally at:

375px (mobile)
768px (tablet)
1440px (desktop)

Write base styles for mobile, then enhance with min-width media queries. Use clamp() for fluid typography. Standard breakpoints already in use:

Mobile: base styles (no media query)
Tablet: @media (min-width: 768px)
Desktop: @media (min-width: 1024px) or (min-width: 1200px) (match existing patterns)

4. Reuse design tokens
The existing <style> block contains foundational rules (color variables, font families, spacing variables, container widths). Always reuse these tokens. Add new scoped CSS classes when needed, but never override the foundational rules.
5. Visual consistency across the site
Every new page or section must visually match the established system used on /about/, /testimonials/, /faq/, /contact/, /field-notes/, /market-insights/, and /meet-the-team/. Specifically:

Section labels: small, uppercase, letter-spaced 0.2em, font-size around 0.875rem
Section headlines: clamp(1.75rem, 4vw, 3rem), bold, tight line-height
Body copy: 1.125rem to 1.25rem, line-height 1.6
Hero stats: clamp(2.5rem, 5vw, 4rem), bold, accent color
Section spacing: 96px to 128px on desktop, 64px on mobile

6. No external image dependencies
All visuals come from the local repo:

Images live at /media/images/
Icons live at /media/icons/
Headshot lives at /media/images/Waist.png

When the exact filename isn't known, use a placeholder filename and an HTML comment: <!-- SWAP: [description of what to use] -->. Never link to external image URLs or stock photo services.
7. No new external dependencies
No new CDNs, frameworks, or libraries. All JavaScript is vanilla. All styling is inline in the existing <style> block.

Content and voice principles
Voice
The site speaks in a confident, direct, slightly vulnerable first-person voice. "I" not "we." Joshua Guerrero is a solo agent, and the writing should reflect that. The tone is:

Honest about uncomfortable truths (commission, being a newer agent, anonymizing clients)
Specific over generic (real numbers, real outcomes, named partners)
Measured, not hyperbolic
Sparse, not crowded

Brand values (echo throughout copy, never name explicitly)

Competitive Greatness — willingness to do what average agents won't
Unimpeachable Character — would rather lose a commission than lose trust
Speed is King — deals die in the silence between messages

These values should leak through every section of every page without being heavy-handed. If a value is named explicitly, it's only on /about/ in the dedicated values block.
What to avoid in copy

Generic real estate platitudes ("I'm passionate about helping families find their dream home")
SEO-style filler ("how to sell my house fast in [city]")
Stock testimonial-page language ("5-star rated," "trusted advisor")
Hyperbolic claims that can't be backed up
Star ratings or platform-aggregated reviews (these belong nowhere on the site, the case files do this work better)

Formatting principles

Short paragraphs (3 to 5 sentences max in body copy)
Generous whitespace
Numbered or bulleted lists only when they genuinely improve scannability
Pull quotes and stat callouts for emphasis, not bold-everywhere


Site architecture
Page inventory

/index.html (home)
/about/index.html
/testimonials/index.html (case files index)
/testimonials/001-long-beach-firefighter/index.html (Case File 001)
/testimonials/002-corona-analyst/index.html (Case File 002)
/testimonials/00X-slug/index.html (future case files)
/faq/index.html
/contact/index.html
/field-notes/index.html (replaces former /blog/)
/field-notes/00X-slug/index.html (future field notes posts)
/market-insights/index.html
/meet-the-team/index.html
/the-process/index.html
/where-we-help/index.html
/privacy-policy/index.html

URL conventions

All directories use trailing slashes (/about/ not /about)
Numbered content uses zero-padded slugs (001-long-beach-firefighter, not 1-long-beach)
Slugs are descriptive and SEO-friendly (location and archetype, not generic names)

Cross-linking patterns
Pages cross-link in a deliberate web, not a hierarchy. Standard cross-link patterns:

/about/ → links to /testimonials/ (the proof)
/testimonials/ → individual case files link back to /testimonials/ (the index)
Each case file → links to neighboring case files
/field-notes/ → links to /testimonials/
/market-insights/ → links to /field-notes/ and /contact/
/meet-the-team/ → links to /testimonials/ and /contact/
/contact/ → links to /testimonials/ for proof
Every page → has a primary CTA linking to /contact/ or the booking flow


Recurring structural patterns
The "Case File" framing
The series naming convention applies to multiple content types:

Case Files: CASE FILE 001, CASE FILE 002, etc. (testimonials)
Field Notes: NOTE 001, NOTE 002, etc. (blog posts)
Counties: COUNTY 01, COUNTY 02, etc. (market insights)
Layers: LAYER 01, LAYER 02, LAYER 03 (meet the team)
Categories: CATEGORY 01, etc. (FAQ)

This numbering creates a sense of intentional series and accumulation.
"Coming soon" placeholder pattern
When a content series has fewer items than its target structure (e.g., only 2 case files but the grid wants 3), add a "Coming soon" placeholder card with:

Same dimensions as real cards
Dashed border instead of solid
Reduced opacity (around 0.6 to 0.7)
Non-clickable
Copy that suggests an active pipeline (e.g., "Currently in escrow / Details coming soon")

Aggregate stats pattern
The aggregate stats strip on /testimonials/ is a recurring pattern. It appears on:

/testimonials/ (total client savings, homes closed, etc.)
/about/ (volume closed, homes sold, units per month)

When adding new stat strips, match the visual treatment exactly. Wrap stat values in <!-- UPDATE --> HTML comments so they're easy to update manually as numbers grow.
Stat dashboard pattern
Each Case File and the Market Insights county sections use a stat dashboard with:

A hero stat (the largest, most important number)
A grid of secondary stats (3 columns desktop, 1 column mobile)
Animated count-up on scroll using IntersectionObserver

Section label + headline + body pattern
Most sections follow this rhythm:

Small uppercase letter-spaced label
Large bold headline
Body copy in 1.125rem to 1.25rem with comfortable line-height

CTA pattern
Every page ends with a Book a 15-minute call CTA. This is the universal site CTA. Variants of the surrounding copy are encouraged, but the button text and destination (/contact/) should remain consistent.

Forms and integrations
Contact form (/contact/)

Wired to MailChannels API via leads.js in the repository
Includes a Google Maps Places Autocomplete integration on the address field
Critical: Never modify the address input's id, name, or data attributes if they're referenced by the autocomplete initialization
Critical: Never remove the Google Maps API script tag or the place_changed event handlers
Hidden fields capturing parsed address components must be preserved

Field Notes subscribe form (/field-notes/)

Wired to the same MailChannels setup via leads.js
Lead source should be tagged distinctly (e.g., field-notes-subscribe) to distinguish from contact form leads
Reuse existing success/error message patterns from other forms


SEO and metadata standards
Every page must have:

A unique <title> tag (50 to 60 characters, includes "Joshua Guerrero" or "Drozq" as brand suffix)
A unique <meta name="description"> (140 to 160 characters)
A <link rel="canonical"> pointing to the absolute URL
Open Graph tags (og:title, og:description, og:image, og:url, og:type)
Twitter Card tags
Appropriate JSON-LD structured data (RealEstateAgent, Person, Article, FAQPage, Blog, BreadcrumbList as relevant)
All <img> tags with descriptive alt attributes
Non-hero images with loading="lazy"
Hero images with fetchpriority="high"

The home page carries the RealEstateAgent Organization schema. The About page carries Person schema. Each case file carries Article and BreadcrumbList schema. The FAQ page carries FAQPage schema with all questions and answers mirrored.

Update workflow conventions
For pages that will be updated frequently (especially /market-insights/):

Wrap every updatable value in clearly-named HTML comments: <!-- UPDATE: [description] --> and <!-- END UPDATE -->
Include an update guide comment block at the top of the file explaining how to update values
Structure the markup so updating one value doesn't require editing structural elements


What this site is NOT
A few explicit anti-patterns to avoid:

It is not a generic agent template site. Every page should have a point of view and a deliberate angle.
It is not a lead capture funnel optimized for volume. Quality over quantity. The site is built to attract a specific kind of client.
It is not a place for star ratings, review screenshots, or platform-aggregated social proof. The case files do this work, more credibly.
It is not a place to mention AI, automation, or technology tooling. The leverage Joshua has is real, but the framing is "systems and discipline," not "I use software to do this." This is a deliberate brand decision and applies to all copy.
It is not a content farm. Field Notes posts and Case Files are published when there's something worth saying, not on a schedule.
It is not a place for fake team members. Joshua is a solo agent. Partners are named by role only (brokerage, transaction coordinator, photographer, lenders, inspectors, title and escrow), not by invented personal names with stock photos.


When in doubt
If a request is ambiguous, default to:

The pattern already established on /testimonials/, /about/, or /faq/
The most concise, confident, sparse interpretation
Asking for clarification rather than guessing on brand voice

If a change would affect the header, footer, or foundational <style> block, stop and confirm before proceeding. These are protected zones.
If a request involves the contact form or the Google Maps autocomplete, stop and audit the existing implementation before modifying anything. Breaking the autocomplete is the easiest way to silently degrade the most important conversion point on the site.
