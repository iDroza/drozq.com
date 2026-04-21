# Speed Audit — drozq.com Homepage

**Date:** 2026-04-20
**Scope:** Homepage (`/` → `index.html`) and supporting media
**Nature:** Report only. No files were modified, compressed, or converted.

---

## 1. Hero headshot (LCP candidate)

| Property | Value |
|---|---|
| File | `/media/images/Waist.png` |
| Weight | **1,759,628 bytes (1.68 MB)** |
| Dimensions | 1050 × 1243 (PNG, 8-bit RGBA, non-interlaced) |
| Displayed at | `max-width: 200px` (desktop, after P2); hidden on viewports ≤1024px via `<picture><source>` trick |
| Effective need | ~200–400px wide even at 2× DPR (~80–150 KB compressed WebP would suffice) |
| Format served | PNG only |
| Responsive | No `srcset`/`sizes` — single fixed asset for all desktop clients |
| Preload | Yes, scoped to `(min-width: 1025px)` with `fetchpriority="high"` (line 36) |

**Relevant observation:** the file is ~11× heavier than needed for the new 200px display. The preload is correctly media-gated so mobile users do not pay for this download. Mobile uses a 1×1 transparent GIF via `<source media="(max-width: 1024px)">` — zero cost.

There is also an unused duplicate at `/media/images/Joshua Guerrero - Transparent Headshot.png` (1,900,813 bytes / 1200 × 1420) that is not referenced from `index.html`.

---

## 2. Other images > 100 KB on the homepage

Homepage inventory (images actually rendered on `/`):

| File | Weight | Dimensions | Used for | Format |
|---|---:|---|---|---|
| `/media/images/Waist.png` | 1.68 MB | 1050 × 1243 | Hero headshot (desktop only) | PNG |
| `/media/icons/Zillow.png` | 54 KB | 3124 × 656 | "Find Me On" row (displayed ~40px tall) | PNG |
| `/media/icons/Google.png` | 44 KB | 1280 × 433 | "Find Me On" row | PNG |
| `/media/icons/real/real-broker-logo.png` | 32 KB | 2500 × 1151 | Footer | PNG |
| `/media/icons/Joshua Guerrero Favicon.png` | 29 KB | — | `<link rel="icon">` | PNG |
| `/media/icons/realtor-com-logo.png` | 28 KB | 949 × 190 | "Find Me On" row | PNG |
| `/media/icons/Joshua Guerrero Logo Rectangle Stacked.png` | 21 KB | 489 × 154 | Footer logo | PNG |
| `/media/icons/Joshua Guerrero Rectangle in line.png` | 20 KB | 500 × 100 | Header logo | PNG |
| `/media/icons/Redfin.png` | 14 KB | 961 × 232 | "Find Me On" row | PNG |

Only **one** image on the homepage exceeds 100 KB: the hero headshot (Waist.png, 1.68 MB).

The "Find Me On" brand logos (Zillow, Google, Realtor.com, Redfin) are all under 100 KB individually, but their source dimensions are 5–8× larger than the displayed size (max 40px tall with the current CSS), representing modest waste each.

---

## 3. Other >100 KB images elsewhere in the repo (not homepage)

These do not affect the `/` LCP but will affect the pages that reference them (Market Insights, city landing pages, Los Angeles, etc.):

| File | Weight |
|---|---:|
| `Joshua Guerrero - Transparent Headshot.png` | 1.81 MB (orphan — not referenced from `index.html`) |
| `simi-valley.jpg` | 1.57 MB |
| `Murrieta.webp` | 785 KB |
| `outside-home-pic3.jpg` | 553 KB |
| `pasadena.jpeg` | 508 KB |
| `burbank.webp` | 467 KB |
| `huntington-beach.webp` | 417 KB |
| `santa-monica.jpg` | 321 KB |
| `glendale.webp` | 298 KB |
| `outside-home-pic4.jpg` | 267 KB |
| `torrance.jpg` | 233 KB |
| `malibu.jpeg` | 212 KB |
| `santa-ana.jpg` | 184 KB |
| `redondo-beach.jpg` | 153 KB |
| (and ~12 more between 100–150 KB) | — |

---

## 4. Modern image format coverage

Counts across `/media/**`:

| Format | Count |
|---|---:|
| JPG / JPEG | 27 |
| WebP | 25 |
| PNG | 12 |
| AVIF | 1 (`temecula.avif`) |

**Homepage specifically:** every image on the homepage is PNG. No WebP, no AVIF, no `<picture>` / `<source type="image/avif">` fallbacks. The existing `<picture>` on the hero is used as a mobile-hide trick, not for format negotiation.

Site-wide, WebP is adopted for about half the city-landing-page photography, but the homepage stack has not been converted.

---

## 5. Responsive image loading (`srcset` / `sizes`)

**`srcset` usage across `index.html`:** one occurrence (line 1456). It is **not** a true responsive-set — it's the mobile-hide hack that points a `<source media="(max-width: 1024px)">` at a 1×1 transparent GIF data URI.

**`sizes` attribute:** zero occurrences.

**Implication:** the browser always downloads the single declared `src` for every image, regardless of viewport or DPR. The hero headshot ships the same 1.68 MB PNG to a 13″ laptop and a 4K display.

---

## 6. Render-blocking resources in `<head>`

| Resource | Type | Blocking? | Notes |
|---|---|---|---|
| GTM bootstrap inline `<script>` (line 6–10) | inline JS | Parser-blocking (sync), very small | Loads `gtm.js` async itself |
| `<style>` inline block (lines 93–1180) | inline CSS | Parser + render blocking | ~45 KB of CSS. No external stylesheet request — trade-off: one less round trip, but the entire sheet is on the critical path |
| JSON-LD `<script type="application/ld+json">` × 2 | inline, non-executing | Not blocking for paint | Metadata only |
| `<link rel="preload" as="image" ...>` for headshot | hint | Not blocking | Correctly media-gated to desktop |
| `<link rel="icon">` | hint | Not blocking | — |
| Meta tags (charset, viewport, OG, Twitter) | — | — | — |

**External resources in `<head>`:** none. No Google Fonts, no external CSS, no render-blocking JS bundles.

**External resources elsewhere:**

| Resource | Location | Behavior |
|---|---|---|
| `https://maps.googleapis.com/maps/api/js?...libraries=places&callback=initGooglePlaces` | end of `<body>` (line ~1469) | `async defer` — not render-blocking |
| `https://www.googletagmanager.com/gtm.js` | injected by GTM bootstrap | `async` — not render-blocking |

---

## Summary of the top opportunities (for future work — not applied here)

1. **Hero headshot:** compress + convert to WebP/AVIF and ship through a `<picture>` with a responsive `srcset`. A 200px-display asset at 2× DPR would be ~50–80 KB, saving ~1.6 MB on desktop LCP.
2. **"Find Me On" logos:** resize to 2× display resolution (roughly 160–320px wide) and convert to WebP. Each logo is currently 5–8× oversized.
3. **Orphan headshot** (`Joshua Guerrero - Transparent Headshot.png`, 1.81 MB): safe to remove if confirmed unreferenced site-wide.
4. **Inline CSS block:** ~45 KB on the critical path. Splitting into above-the-fold critical CSS + deferred stylesheet is only worth it if LCP instrumentation flags CSS as a bottleneck.

No changes were made to the images, formats, or the `<head>` as part of this audit.
