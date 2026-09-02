# Backlog

*Last reviewed: August 26, 2026*

Active TODOs across drozq.com. Consolidated from prior audit docs (deleted as of this rev: `AUDIT-INDEX-2026-04-26.md`, `SEO-AUDIT-INDEX-2026-04-26.md`, `FAVICON_AUDIT.md`, `SPEED-AUDIT.md`, `CHANGES.md`, `REALTOR_CLEANUP_AUDIT.md`). Findings that were already DONE at consolidation time are not listed.

When something ships, remove the item from this file in the same commit. Don't leave done items hanging.

---

## Paid campaigns (parked)

- **Paste keywords into AG7 + AG8 of the Sellers campaign (they have never served).** Found 2026-07-02 while evaluating the June window: `AG7 | Free-Home-Valuation` and `AG8 | How-Much-Is-My-House-Worth` in "Home Sellers - Agent Locator Lander" are ENABLED with approved RSAs but carry **zero keywords**, so they logged 0 impressions all June (Ad Strength stuck on "Pending" is the tell). Their themes leak to looser phrase matches in AG5/AG6: the #1 June search term, "how much is my house worth" (93 impressions), is literally AG8's theme served by another ad group's ad. The keyword lists already exist in `C:\Users\guerr\Downloads\drozq-google-ads-keywords.csv` (per `notes/ads/sellers-valuation-rebuild-2026-06.md` §3). Paste them in when un-pausing the campaign (paused 2026-07-02 10:25 by Joshua; June read: $389 spend, 8 leads, $48 CPL, rank-lost IS 76%).

- **Rebuild `/relief/`, the distressed-sellers paid landing.** The original page was deleted on 2026-05-26 (commit pending) because it was the last surviving bespoke page and was not actively serving traffic at the time. The strategy playbook still exists at `notes/ads/distressed-sellers-strategy.md`. When relaunching: build the new `/relief/` on the homepage template (per the workflow in `TEMPLATE.md` section 13), with a distinct multi-step funnel for the distressed audience (foreclosure / divorce / probate / inheritance / short sale) and a confidential-callback intake. Continue posting to `/api/lead`. Companion campaign doc: `notes/ads/sellers-max-intent-campaign.md`. Note before re-running ads: no `_redirects` file exists, so any historical `/relief/` ad clicks are currently 404'ing; pause campaigns OR add a Cloudflare redirect rule before the relaunch.

---

## Conversion / strategy (high-leverage)

These move the needle the most. They are concentrated on `/index.html`.

- **Headshot above the fold.** Joshua's `Waist.png` is referenced in JSON-LD schema but does not appear in the visible body. Add a hero block or aside that puts a face on the page.
- **"About Joshua" callout.** Short bio block somewhere on the homepage. Year started (2024), brokerage (Real Brokerage), DRE, one-line philosophy. Builds trust + EAT signal.
- **IDX home search (the Buy tab's "See Homes" currently opens a form, not homes).** Plan + paperwork map in `notes/idx/idx-access-plan.md` (2026-09-02). Step 1 is free and same-day: a Matrix IDX frame on a new `/homes/` page. Step 2 is the Trestle RESO feed (about $100/mo) with Real's broker approval, then a native `/homes/` search + indexable listing pages on the template.
- **Service-area body section.** Visible content section naming Irvine + Orange County neighborhoods (Turtle Rock, Woodbridge, Northwood, Crystal Cove, etc.). Currently only in JSON-LD `areaServed`. Helps local SEO + visitor confidence.
---

## SEO / AI search

- **Internal links footer block.** Only `/privacy/`, `/terms/`, and `/faq/` (via header) are linked from the homepage. Add a small internal-links section linking `/about/`, `/testimonials/`, `/field-notes/`, `/market-insights/`, `/process/`, `/where-we-help/`, `/contact/`. Important for crawl coverage. (Note: these are legacy brand-mode pages; they still exist and accept traffic.)
- **Submit the sitemap in Search Console (Joshua, 30 seconds).** GSC ownership confirmed 2026-07-22 (domain already verified). In the drozq.com property: Sitemaps → enter `sitemap.xml` → Submit. The sitemap was refreshed the same day (22 URLs incl. `/terms/`, honest lastmod dates); robots.txt already advertises it.
- **Bing Webmaster (30 seconds, after the sitemap).** bing.com/webmasters offers "Import from Google Search Console": one click, no token, imports the verified property and its sitemap.

---

## Email platform (shipped + ACTIVATED 2026-07-13; remaining)

- **Personal FollowUpBoss account is cancelled/expired.** Discovered 2026-07-13: the FUB API returns 403 "Account cancelled or expired", so the `/api/lead` CRM push (`FOLLOWUPBOSS_API_KEY`) has been failing silently since it lapsed and the email-platform FUB backfill path is dead (the lead-alert emails in Gmail were used as the backfill source instead). Decide: reactivate the personal FUB subscription (push resumes automatically, key unchanged) or remove the channel + env var.
- **Confirm the footer postal address.** The footer now defaults to "Active Realty, 17875 Von Karman Ave Suite 150, Irvine, CA 92614" (per Joshua's 2026-07-13 "Active Realty for now" direction). Confirm that address is current; `EMAIL_POSTAL_ADDRESS` overrides without a code change.
- **Reply-detection auto-pause: paste-ready, awaiting the 3-minute install.** The Apps Script watcher is written (`notes/email/auto-pause-apps-script.md`; secret-filled copy in `Downloads\drozq-auto-pause-setup.md`). Joshua installs it at script.google.com AS josh@drozq.com (paste, authorize, 5-minute trigger). Until installed, a reply requires the manual `python scripts/emailer.py pause <email>`.
- **First note-drop broadcast.** When the first Field Note publishes, send it with `python scripts/emailer.py broadcast --segment newsletter --subject ... --cta-url https://drozq.com/field-notes/...`.

---

## Code review 2026-07-22: remaining item

Joshua ruled on the review's flagged decisions 2026-07-22: the funnel X shipped (quiet close, `funnel_close` event), the aggressive autofill-open listener stays (conversion play, accepted), and duplicate-lead retries stay as designed. Remaining:

- (Reaper + per-step retries shipped 2026-08-26; see CLAUDE.md "Email platform".)

---

## Tracking & measurement

- **UTM parameter capture.** The funnel IIFE captures `gclid` but not `utm_source` / `utm_medium` / `utm_campaign` / `utm_content` / `utm_term`. Mirror the gclid pattern: read from URL → cookie → sessionStorage, persist to 90-day cookies, push to dataLayer, forward to `/api/lead` as hidden fields.

---

## Realtor.com clone leftovers (still on /index.html)

These were tracked in the now-deleted `REALTOR_CLEANUP_AUDIT.md`. The Done items have been folded into the "Realtor.com clone state" section of `CLAUDE.md`. What remains:

- **Panda CSS tree-shake.** The soup is now ONE cached stylesheet (`/media/css/panda.css`, extracted 2026-08-26, so every navigation after the first is free), but it is still ~152 KB with most utilities unused. Tree-shake it against actual class usage across all pages (keep `@layer base` + the tokens), then re-run `scripts/extract_panda_css.py` and `panda_patch.py --check`.
- **Header nav markup cleanup.** Dead `#top` links remain in the DOM even when the header is hidden for new visitors. Reduce DOM clutter by deleting the unused nav items (`Login`, dead "Reviews" link, etc.) rather than just hiding them.
- **6-tile partner-agent grid.** Tracked under "Conversion / strategy" above (item: "Our partner agents are…" section). Reflagged here because it is also a clone leftover.

---

## Hygiene & polish

- **Prune dead funnel code.** Since the unified funnel (2026-06-13) always renders the sell entries, these are unused: `VALUEBAR.buy` / `VALUEBAR.sellandbuy`, `DELIVERABLE.buy` / `DELIVERABLE.sellandbuy`, the `DV_BODY` helper, and the `#funnel-overlay .funnel-dv-*` CSS block. Safe to delete from `/index.html` (between the funnel markers) and re-sync. Also unused: the dead `.funnel-h2-fit` CSS rule (its only usage was removed) can go too. (The never-referenced `trust*.webp` files were deleted in the 2026-07-09 declutter.)
- **Skip-to-content link.** No `class="skip-link"` or skip-to-content anchor at the top of the body. Add for keyboard / screen-reader users.
- **`<img>` width/height coverage.** Most images have explicit `width`/`height` attrs (good for CLS), but not 100%. Audit images that load without dimensions and add them.
- **12px body font on sub-tiles.** Some content sub-tiles still render at 12px, below the recommended 14px floor for body text. Bump to 14px.
- **CLAUDE.md "Realtor.com clone state" section.** Currently flags `BRE #01928572` and Indiana PLA as deferred. Both are already DONE. Refresh that section to match current state when this backlog is acted on.
- **Internal docs are publicly served.** No build step means everything tracked deploys: `CLAUDE.md`, `TEMPLATE.md`, `BACKLOG.md`, `notes/` (including the ad-strategy docs), and `scripts/*.py` are all fetchable at their drozq.com paths. No secrets are exposed (keys live in Cloudflare env vars / gitignored files), but the campaign strategy notes are competitive intel sitting on public URLs. Decide: accept as-is, or add a deploy exclusion (a build step or output-dir restructure that strips `notes/`, `scripts/`, and root `*.md` from the published site).

---

## Joshua to-dos from the 2026-08-26 fix pass (dashboard side, not code)

- **Enable "Places API (New)"** on the Maps key in Google Cloud (APIs & Services > Enable; add it to the key's API restrictions). Until then every page makes one failing autocomplete request and falls back to the legacy class (still works, still warns once).
- **Cloudflare WAF rate-limiting rule** (Security > WAF > Rate limiting rules): `http.request.uri.path in {"/api/valuation" "/api/netsheet" "/api/subscribe"}` and method POST, e.g. 10 requests per 10 s per IP, block 10 minutes. The code-level limiter enforces the per-10-minute / per-day / global budgets the WAF cannot express.
- `python scripts/emailer.py init` once, so the new email columns and the `rate_limits` / `lead_submissions` tables exist up front.
- Optional GTM trigger exception `funnel_mode equals newsletter` if Field Notes sign-ups should not count as an Ads conversion.
- The gate-page `lead_confirmed` events (valuation / net_sheet / newsletter) now flow into the GA4 `funnel_mode` dimension; check the Ads conversion column for the new modes after a week.

## When something here ships

In the same commit:

1. Delete the line item from this file.
2. Reference the deletion in the commit message: e.g., `BACKLOG: ship FAQPage JSON-LD`.
3. If the change touches the homepage funnel (HTML or JS between `DROZQ_FUNNEL_*` markers), run `python scripts/sync_funnels.py` to propagate to every page in `funnels.json`.
