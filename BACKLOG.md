# Backlog

*Last reviewed: May 26, 2026*

Active TODOs across drozq.com. Consolidated from prior audit docs (deleted as of this rev: `AUDIT-INDEX-2026-04-26.md`, `SEO-AUDIT-INDEX-2026-04-26.md`, `FAVICON_AUDIT.md`, `SPEED-AUDIT.md`, `CHANGES.md`, `REALTOR_CLEANUP_AUDIT.md`). Findings that were already DONE at consolidation time are not listed.

When something ships, remove the item from this file in the same commit. Don't leave done items hanging.

---

## Paid campaigns (parked)

- **Paste keywords into AG7 + AG8 of the Sellers campaign (they have never served).** Found 2026-07-02 while evaluating the June window: `AG7 | Free-Home-Valuation` and `AG8 | How-Much-Is-My-House-Worth` in "Home Sellers - Agent Locator Lander" are ENABLED with approved RSAs but carry **zero keywords**, so they logged 0 impressions all June (Ad Strength stuck on "Pending" is the tell). Their themes leak to looser phrase matches in AG5/AG6: the #1 June search term, "how much is my house worth" (93 impressions), is literally AG8's theme served by another ad group's ad. The keyword lists already exist in `C:\Users\guerr\Downloads\drozq-google-ads-keywords.csv` (per `notes/ads/sellers-valuation-rebuild-2026-06.md` §3). Paste them in when un-pausing the campaign (paused 2026-07-02 10:25 by Joshua; June read: $389 spend, 8 leads, $48 CPL, rank-lost IS 76%).

- **Rebuild `/relief/`, the distressed-sellers paid landing.** The original page was deleted on 2026-05-26 (commit pending) because it was the last surviving bespoke page and was not actively serving traffic at the time. The strategy playbook still exists at `notes/ads/distressed-sellers-strategy.md`. When relaunching: build the new `/relief/` on the homepage template (per the workflow in `TEMPLATE.md` section 13), with a distinct multi-step funnel for the distressed audience (foreclosure / divorce / probate / inheritance / short sale) and a confidential-callback intake. Continue posting to `/api/lead`. Companion campaign doc: `notes/ads/sellers-max-intent-campaign.md`. Note before re-running ads: no `_redirects` file exists, so any historical `/relief/` ad clicks are currently 404'ing; pause campaigns OR add a Cloudflare redirect rule before the relaunch.

---

## Conversion / strategy (high-leverage)

These move the needle the most. They are concentrated on `/index.html`.

- **Wire instant delivery of the funnel deliverable.** The funnel promises the home valuation report "the instant you submit" / "delivered the moment you finish," but `/api/lead` currently only emails the lead to Joshua; nothing auto-delivers to the visitor. Wire real instant delivery (auto-email the valuation, and/or render it inline from `/api/valuation`) so the promise is backed. Until then the instant copy runs ahead of the backend. (The old 5-playbook PDF half of this promise died with the 2026-07-20 playbook kill.)
- **Headshot above the fold.** Joshua's `Waist.png` is referenced in JSON-LD schema but does not appear in the visible body. Add a hero block or aside that puts a face on the page.
- **Stat callouts.** No specific Joshua stats on the homepage ("$43,250 in client savings so far," "7 days to MLS," etc.). Pull from case files. Three callouts max.
- **"About Joshua" callout.** Short bio block somewhere on the homepage. Year started (2024), brokerage (Real Brokerage), DRE, one-line philosophy. Builds trust + EAT signal.
- **Service-area body section.** Visible content section naming Irvine + Orange County neighborhoods (Turtle Rock, Woodbridge, Northwood, Crystal Cove, etc.). Currently only in JSON-LD `areaServed`. Helps local SEO + visitor confidence.
- **Closing-CTA offer framing on 4 pages (Joshua's call).** `/field-notes/`, `/market-insights/`, `/prices/`, `/rates/` close with the human-CMA promise ("Free CMA, delivered within 24 hours" or equivalent) directly above forms that open the instant-valuation funnel. Decide per page: re-anchor to the instant valuation (as `/process/`'s closing now does), or keep the hand-built-CMA angle as the closer. `/thank-you/` (reply-time commitment) and `/value/` (refined-CMA tier) are intentional and stay. The 2026-07-14 sweep already moved every landing CTA to "Run my Valuation" + the instant H4 line site-wide; only these four closer paragraphs remain on the old framing.

---

## SEO / AI search

- **Internal links footer block.** Only `/privacy/`, `/terms/`, and `/faq/` (via header) are linked from the homepage. Add a small internal-links section linking `/about/`, `/testimonials/`, `/field-notes/`, `/market-insights/`, `/the-process/`, `/where-we-help/`, `/contact/`. Important for crawl coverage. (Note: these are legacy brand-mode pages; they still exist and accept traffic.)
- **`google-site-verification` token.** Current `<meta>` is the literal placeholder `REPLACE-WITH-SEARCH-CONSOLE-TOKEN`. Replace with the real token from Search Console. (Needs the token from Joshua's Search Console account; not automatable.)
- **Bing Webmaster verification.** Add `<meta name="msvalidate.01" content="...">` next to the Google one. (Same: needs the real token.)

---

## Email platform (shipped + ACTIVATED 2026-07-13; remaining)

- **Personal FollowUpBoss account is cancelled/expired.** Discovered 2026-07-13: the FUB API returns 403 "Account cancelled or expired", so the `/api/lead` CRM push (`FOLLOWUPBOSS_API_KEY`) has been failing silently since it lapsed and the email-platform FUB backfill path is dead (the lead-alert emails in Gmail were used as the backfill source instead). Decide: reactivate the personal FUB subscription (push resumes automatically, key unchanged) or remove the channel + env var.
- **Confirm the footer postal address.** The footer now defaults to "Active Realty, 17875 Von Karman Ave Suite 150, Irvine, CA 92614" (per Joshua's 2026-07-13 "Active Realty for now" direction). Confirm that address is current; `EMAIL_POSTAL_ADDRESS` overrides without a code change.
- **Reply-detection auto-pause: paste-ready, awaiting the 3-minute install.** The Apps Script watcher is written (`notes/email/auto-pause-apps-script.md`; secret-filled copy in `Downloads\drozq-auto-pause-setup.md`). Joshua installs it at script.google.com AS josh@drozq.com (paste, authorize, 5-minute trigger). Until installed, a reply requires the manual `python scripts/emailer.py pause <email>`.
- **First note-drop broadcast.** When the first Field Note publishes, send it with `python scripts/emailer.py broadcast --segment newsletter --subject ... --cta-url https://drozq.com/field-notes/...`.

---

## Code review 2026-07-22: flagged for Joshua's call (not auto-fixed)

- **The funnel overlay has no close path.** No X, no Escape, no backdrop dismiss; only submit, browser-back, or reload exit it. May be deliberate hard-commit design, but combined with the autofill-open listener below an accidental open traps a paid visitor. Decide: add a quiet X / Escape handler, or keep the hard commit.
- **The landing input's change-listener opens the funnel on any edit + blur.** Typing one character and clicking anywhere opens the full-screen funnel with an unvalidated address 60ms later, bypassing the Places gate (junk sell-lead addresses; the funnel re-asks nothing). Decide: restrict the auto-open to real autofill signals, or accept the aggressive open as a conversion play.
- **Duplicate-lead retries are by design.** The funnel retries a submit up to 3x on network/5xx; a processed-but-unacknowledged request delivers the lead 2-3x (email/Zapier/FUB). An idempotency key (client-generated UUID deduped in lead.js) would end it; noting since the code comment accepts duplicates deliberately.
- **Email rows stuck in 'sending' have no reaper** if an isolate dies mid-send, and a failed sequence send skips that step permanently (claim-before-send has no retry queue). Both rare; add a reaper/requeue if send failures ever show up in `emailer.py log`.

---

## Tracking & measurement

- **UTM parameter capture.** The funnel IIFE captures `gclid` but not `utm_source` / `utm_medium` / `utm_campaign` / `utm_content` / `utm_term`. Mirror the gclid pattern: read from URL → cookie → sessionStorage, persist to 90-day cookies, push to dataLayer, forward to `/api/lead` as hidden fields.

---

## Realtor.com clone leftovers (still on /index.html)

These were tracked in the now-deleted `REALTOR_CLEANUP_AUDIT.md`. The Done items have been folded into the "Realtor.com clone state" section of `CLAUDE.md`. What remains:

- **Inline CSS purge.** The inline `<style>` block is ~157KB of Panda CSS utilities. Probably ~80% unused. Tree-shake against actual class usage and inline only what is needed. Biggest remaining perf win.
- **Header nav markup cleanup.** Dead `#top` links remain in the DOM even when the header is hidden for new visitors. Reduce DOM clutter by deleting the unused nav items (`Login`, dead "Reviews" link, etc.) rather than just hiding them.
- **6-tile partner-agent grid.** Tracked under "Conversion / strategy" above (item: "Our partner agents are…" section). Reflagged here because it is also a clone leftover.

---

## Hygiene & polish

- **`highlight-reviews.png` (204KB).** 1 ref on homepage. Convert to WebP or remove if the section is being rewritten.
- **Prune dead funnel code.** Since the unified funnel (2026-06-13) always renders the sell entries, these are unused: `VALUEBAR.buy` / `VALUEBAR.sellandbuy`, `DELIVERABLE.buy` / `DELIVERABLE.sellandbuy`, the `DV_BODY` helper, and the `#funnel-overlay .funnel-dv-*` CSS block. Safe to delete from `/index.html` (between the funnel markers) and re-sync. Also unused: the dead `.funnel-h2-fit` CSS rule (its only usage was removed) can go too. (The never-referenced `trust*.webp` files were deleted in the 2026-07-09 declutter.)
- **Skip-to-content link.** No `class="skip-link"` or skip-to-content anchor at the top of the body. Add for keyboard / screen-reader users.
- **`<img>` width/height coverage.** Most images have explicit `width`/`height` attrs (good for CLS), but not 100%. Audit images that load without dimensions and add them.
- **12px body font on sub-tiles.** Some content sub-tiles still render at 12px, below the recommended 14px floor for body text. Bump to 14px.
- **CLAUDE.md "Realtor.com clone state" section.** Currently flags `BRE #01928572` and Indiana PLA as deferred. Both are already DONE. Refresh that section to match current state when this backlog is acted on.
- **Internal docs are publicly served.** No build step means everything tracked deploys: `CLAUDE.md`, `TEMPLATE.md`, `BACKLOG.md`, `notes/` (including the ad-strategy docs), and `scripts/*.py` are all fetchable at their drozq.com paths. No secrets are exposed (keys live in Cloudflare env vars / gitignored files), but the campaign strategy notes are competitive intel sitting on public URLs. Decide: accept as-is, or add a deploy exclusion (a build step or output-dir restructure that strips `notes/`, `scripts/`, and root `*.md` from the published site).

---

## When something here ships

In the same commit:

1. Delete the line item from this file.
2. Reference the deletion in the commit message: e.g., `BACKLOG: ship FAQPage JSON-LD`.
3. If the change touches the homepage funnel (HTML or JS between `DROZQ_FUNNEL_*` markers), run `python scripts/sync_funnels.py` to propagate to every page in `funnels.json`.
