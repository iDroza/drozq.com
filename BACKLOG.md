# Backlog

*Last reviewed: May 22, 2026*

Active TODOs across drozq.com. Consolidated from prior audit docs (deleted as of this rev: `AUDIT-INDEX-2026-04-26.md`, `SEO-AUDIT-INDEX-2026-04-26.md`, `FAVICON_AUDIT.md`, `SPEED-AUDIT.md`, `CHANGES.md`, `REALTOR_CLEANUP_AUDIT.md`). Findings that were already DONE at consolidation time are not listed.

When something ships, remove the item from this file in the same commit. Don't leave done items hanging.

---

## Conversion / strategy (high-leverage)

These move the needle the most. They are concentrated on `/index.html`.

- **Hero rewrite.** H1 still says "Compare Agents. Find a Trusted Expert." This is realtor.com clone framing. Replace with Joshua-specific positioning. The Sell / Buy / Sell & Buy tab structure stays; only hero copy changes. "Compare Agents" appears 4x in the homepage body.
- **"Our partner agents are..." section.** 6-tile grid (Skilled / Licensed / Expert negotiators / Highly reviewed / Competitive rates / Market experts) still framed as plural agents. Either rewrite as Joshua's differentiators or delete the section. CLAUDE.md voice rules apply.
- **Trusted-brands logo grid.** Compass / Keller Williams / Berkshire Hathaway / Long & Foster / eXp / Douglas Elliman logos still embedded. Misrepresentation risk: Joshua is not affiliated with these. Delete or relabel as "Brokerages we have closed deals with" (only if true).
- **"AgentLocator" copy.** 1 leftover reference in homepage body + appears in 4 FAQ questions. Rewrite to drop the framing entirely.
- **Headshot above the fold.** Joshua's `Waist.png` is referenced in JSON-LD schema but does not appear in the visible body. Add a hero block or aside that puts a face on the page.
- **Stat callouts.** No specific Joshua stats on the homepage ("$43,250 in client savings so far," "7 days to MLS," etc.). Pull from case files. Three callouts max.
- **Sticky mobile CTA bar.** Bottom-of-viewport persistent CTA on mobile (≤767px) that opens the funnel in Sell mode. Increases mobile conversion materially per the prior audit.
- **"About Joshua" callout.** Short bio block somewhere on the homepage. Year started (2024), brokerage (Real Brokerage), DRE, one-line philosophy. Builds trust + EAT signal.
- **Service-area body section.** Visible content section naming Irvine + Orange County neighborhoods (Turtle Rock, Woodbridge, Northwood, Crystal Cove, etc.). Currently only in JSON-LD `areaServed`. Helps local SEO + visitor confidence.

---

## SEO / AI search

- **FAQPage JSON-LD.** Wrap the existing FAQ accordion in a FAQPage schema block. Each question + answer pair becomes a `Question` node. Currently 0 FAQPage matches in `index.html`.
- **Internal links footer block.** Only `/privacy/`, `/terms/`, and `/faq/` (via header) are linked from the homepage. Add a small internal-links section linking `/about/`, `/testimonials/`, `/field-notes/`, `/market-insights/`, `/the-process/`, `/where-we-help/`, `/contact/`. Important for crawl coverage. (Note: these are legacy brand-mode pages; they still exist and accept traffic.)
- **Rewrite generic H2s.** "Common Questions" → "Frequently asked: selling and buying in Irvine." "Why work with an agent?" → "Why work with a local Irvine agent?" Targets seller intent keywords.
- **Heading hierarchy.** Market-trends section has H2 → H4 skip. Either bump H4 to H3 or add an intermediate H3.
- **`google-site-verification` token.** Current `<meta>` is the literal placeholder `REPLACE-WITH-SEARCH-CONSOLE-TOKEN`. Replace with the real token from Search Console.
- **Bing Webmaster verification.** Add `<meta name="msvalidate.01" content="...">` next to the Google one.
- **`<meta name="theme-color">`.** Not present. Add at least `<meta name="theme-color" content="#d92228">` for browser chrome on mobile.
- **Sitemap `lastmod` refresh.** Homepage entry in `sitemap.xml` is current (2026-05-07), but the other 14 URLs are still dated 2026-04-15. Update lastmod on any URL with real edits since.

---

## Tracking & measurement

- **GTM trigger update.** GA4 `generate_lead` is still triggered on "Page View on /thank-you/" instead of "Custom Event = `lead_confirmed`." This is a GTM-side change (off-repo). Until it ships, conversions are inflated by direct/refresh/bookmark visits to the thank-you page. CLAUDE.md flags this as an outstanding Joshua action.
- **UTM parameter capture.** The funnel IIFE captures `gclid` but not `utm_source` / `utm_medium` / `utm_campaign` / `utm_content` / `utm_term`. Mirror the gclid pattern: read from URL → cookie → sessionStorage, persist to 90-day cookies, push to dataLayer, forward to `/api/lead` as hidden fields.
- **Funnel input `name=` attributes.** Funnel steps' inputs (`#funnel-step5-name`, `#buy-step5-email`, etc.) have IDs but no `name=` attrs. Graceful degradation: if JS fails, the form should still submit identifiable fields. Add `name="full_name"`, `name="email"`, `name="phone"`.

---

## Realtor.com clone leftovers (still on /index.html)

These were tracked in the now-deleted `REALTOR_CLEANUP_AUDIT.md`. The Done items have been folded into the "Realtor.com clone state" section of `CLAUDE.md`. What remains:

- **Move-hosted market-trends iframe.** `https://realtorqa.upnest.com/market-trends/index.html?map_only=true&slug_id=Irvine_CA&...` still embedded. UpNest attribution is currently masked with a white overlay (commit `b58f7c5`). Long-term: replace with a static stat block you control, or drop the section entirely. Removing it leaves a ~472px desktop gap to fill.
- **Inline CSS purge.** The inline `<style>` block is ~157KB of Panda CSS utilities. Probably ~80% unused. Tree-shake against actual class usage and inline only what is needed. Biggest remaining perf win.
- **Header nav markup cleanup.** Dead `#top` links remain in the DOM even when the header is hidden for new visitors. Reduce DOM clutter by deleting the unused nav items (`Login`, dead "Reviews" link, etc.) rather than just hiding them.
- **Orphan files on disk.** Delete: `/media/icons/realtor-com-logo.png` (0 refs in HTML). Delete: `/media/images/Joshua Guerrero - Transparent Headshot.png` (1.81MB, 0 refs).
- **6-tile partner-agent grid.** Tracked under "Conversion / strategy" above (item: "Our partner agents are…" section). Reflagged here because it is also a clone leftover.

---

## Hygiene & polish

- **Two `TODO: confirm Drozq red` comments.** In the inline funnel `<style>` block. The current red is `#d92228`. Either confirm and remove the TODOs or pick a different shade.
- **`highlight-reviews.png` (204KB).** 1 ref on homepage. Convert to WebP or remove if the section is being rewritten.
- **`/404.html`.** Not present. Cloudflare Pages currently serves index.html (or a generic 404) for missing paths, which can cause soft-404s in Google's index. Create a real 404 page following the homepage template (minimal funnel-equipped scaffold + "Page not found" hero copy).
- **Funnel error accessibility.** Only 1 `role="alert"`/`aria-live` match in index.html. The funnel's `.funnel-error` divs should have `role="alert"` (transient errors) or `aria-live="polite"` so screen readers announce validation failures.
- **Skip-to-content link.** No `class="skip-link"` or skip-to-content anchor at the top of the body. Add for keyboard / screen-reader users.
- **`<img>` width/height coverage.** Most images have explicit `width`/`height` attrs (good for CLS), but not 100%. Audit images that load without dimensions and add them.
- **12px body font on sub-tiles.** Some content sub-tiles still render at 12px, below the recommended 14px floor for body text. Bump to 14px.
- **CLAUDE.md "Realtor.com clone state" section.** Currently flags `BRE #01928572` and Indiana PLA as deferred. Both are already DONE. Refresh that section to match current state when this backlog is acted on.

---

## When something here ships

In the same commit:

1. Delete the line item from this file.
2. Reference the deletion in the commit message: e.g., `BACKLOG: ship FAQPage JSON-LD`.
3. If the change touches the homepage funnel (HTML or JS between `DROZQ_FUNNEL_*` markers), run `python scripts/sync_funnels.py` to propagate to every page in `funnels.json`.
