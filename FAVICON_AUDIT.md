# Favicon Audit — drozq.com

**Audited:** 2026-04-21
**Auditor:** Claude (read-only audit, no code changes)
**Deploy target:** Cloudflare Pages (static HTML, served from repo root)

---

## Executive Summary

**Verdict: The favicon is largely set up correctly. Google HAS successfully indexed the correct favicon.** The globe icon you see in Google Ads / Search is almost certainly a **cache/re-crawl lag problem**, not a setup failure.

**Evidence:** Google's own favicon service (`https://t1.gstatic.com/faviconV2?...&url=http://drozq.com&size=128`) returns the correct green "JG" house icon for drozq.com at 16px, 64px, and 128px.

**But there are real, fixable problems worth cleaning up** that may be contributing or may cause future issues:

| # | Severity | Problem |
|---|----------|---------|
| 1 | **HIGH** | `/favicon.ico` is NOT a real ICO file — it's a PNG renamed with `.ico`. MIME-type mismatch: Cloudflare serves it as `image/vnd.microsoft.icon` but the bytes are PNG. |
| 2 | **HIGH** | Cloudflare Pages returns **HTTP 200 + HTML** for missing favicon paths (`/apple-touch-icon.png`, `/site.webmanifest`, `/manifest.json`, any 404). Crawlers requesting these paths get the homepage HTML, not a 404. |
| 3 | **MEDIUM** | Google's cached favicon (seen via `Content-Location` header) was found at the OLD path `https://www.drozq.com/media/icons/Joshua%20Guerrero%20Favicon.png` — a URL with spaces that was marked "fragile" in commit `21f6c12`. Google hasn't re-crawled since the fix landed yesterday (Apr 20, 2026). |
| 4 | **LOW** | No `apple-touch-icon.png` (180x180) — mobile Safari and some Google surfaces prefer this. |
| 5 | **LOW** | No `site.webmanifest` / `manifest.json` — PWA / Android Chrome metadata. |
| 6 | **LOW** | No `favicon.svg` — SVG favicons scale crisply and support dark mode. |

**Root-cause hypothesis for the globe icon:** Combination of (a) recent change (Apr 20 — yesterday), SERP cache still warm; (b) Google Ads uses a separate verification pipeline that may be stricter about `.ico` MIME validity than Search; (c) the old referenced path contained literal spaces, which may have failed strict Google Ads verification even if browsers and Google Search were lenient.

---

## 1. Site Structure Discovery

| Property | Value |
|----------|-------|
| Repo root | `C:\Users\guerr\Documents\drozq.com\` |
| Deploy platform | Cloudflare Pages |
| Server (confirmed via `Server` header) | `cloudflare` |
| Build step | **None** — static HTML files served directly from repo root |
| Build output dir | **None** (no `public/`, `dist/`, `static/`, `out/`) |
| Framework | **None** — hand-written HTML |
| `_redirects` | Not present |
| `_headers` | Not present |
| `_routes.json` | Not present |
| `wrangler.toml` / `wrangler.json` | Not present |
| `_worker.js` | Not present |
| `package.json` | Not present |
| `functions/` | Present (contains `api/` — unrelated to favicon) |
| Root HTML file | `index.html` (96,315 bytes) |
| Total HTML pages | 17 (index + 16 sub-page `index.html` files) |

**Implication:** Because there is no build step, every file in the repo maps 1:1 to a URL on the deployed site. `/favicon.ico` in the repo = `https://www.drozq.com/favicon.ico` on the live site.

**Cloudflare Pages default 404 behavior:** Without a `_redirects` rule or `404.html`, Cloudflare Pages appears to be configured in SPA-fallback mode — ANY missing path returns `/index.html` with HTTP 200 (verified with `GET /not-a-real-path-12345` → 200 OK, `Content-Type: text/html`). This is a **soft-404** and affects the favicon analysis because requests for `/apple-touch-icon.png`, `/site.webmanifest`, etc. return HTML-as-image.

---

## 2. Favicon File Inventory

### Files found in repo

| Path | File Size | Reported Format | Pixel Dimensions | MD5 |
|------|-----------|-----------------|------------------|-----|
| `/favicon.ico` | 29,230 bytes | **PNG (not ICO)** | 512 x 512 RGBA | `811075e1970e47751ff33c7063cfac54` |
| `/favicon.png` | 29,230 bytes | PNG | 512 x 512 RGBA | `811075e1970e47751ff33c7063cfac54` |
| `/media/icons/Joshua Guerrero Favicon.png` | 29,230 bytes | PNG | 512 x 512 RGBA | (same source file — byte-identical copy) |

**`favicon.ico` and `favicon.png` are byte-for-byte identical.** Both root-level favicons are copies of the source file `media/icons/Joshua Guerrero Favicon.png`. The `.ico` file is a PNG with its extension renamed — not a valid Microsoft Icon container.

Verified via `file` command:
```
/favicon.ico: PNG image data, 512 x 512, 8-bit/color RGBA, non-interlaced
/favicon.png: PNG image data, 512 x 512, 8-bit/color RGBA, non-interlaced
```

### Files NOT found (but should exist for best coverage)

| Path | Purpose | Required by |
|------|---------|-------------|
| `/favicon-16x16.png` | Small rendering hint | Older browsers (legacy) |
| `/favicon-32x32.png` | Browser tab icon | Chrome, Firefox (legacy) |
| `/favicon-48x48.png` | Windows taskbar | IE/Edge (legacy) |
| `/apple-touch-icon.png` (180x180) | iOS home-screen, some Google mobile surfaces | iOS Safari, Google mobile SERP |
| `/android-chrome-192x192.png` | Android home-screen | Android Chrome (via manifest) |
| `/android-chrome-512x512.png` | Android splash screen | Android Chrome (via manifest) |
| `/site.webmanifest` OR `/manifest.json` | PWA metadata | Android Chrome, PWA installs |
| `/favicon.svg` | Scalable favicon with dark-mode support | Modern Chrome, Firefox, Safari |

### Favicon image content review

Visual inspection of `/favicon.png`: a **green house outline with the initials "JG" inside**, on transparent background.

| Check | Result |
|-------|--------|
| Is it square (1:1)? | ✅ 512x512 — square |
| Is it ≥ 48x48 (Google's current recommendation)? | ✅ 512x512 is much larger than 48x48 |
| Is it pure text? | ✅ No — it's a graphic (house outline) + text |
| Is it a flag? | ✅ No |
| Is it a hate symbol? | ✅ No |
| Contrast at 16x16 rendering | ⚠️ Concern: light green on transparent background may disappear on light SERPs. The green is `~#42cc93`-ish, which has poor contrast against Google's white SERP background. |

> **Sidebar — outdated myth debunked:** An older version of Google's docs stated the favicon must be "a multiple of 48 pixels." The current (verified 2026-04-21) docs say: *"minimum 8x8, recommended larger than 48x48."* The 512x512 file easily satisfies the current rule. This is NOT contributing to the globe-icon issue.

---

## 3. HTML `<head>` Audit

All 17 HTML files were scanned for favicon-related `<link>` tags. **All 17 files contain the same three favicon declarations**, applied consistently.

### Tags found on homepage (`/index.html`, lines 34-36)

```html
<link rel="icon" type="image/x-icon" href="/favicon.ico" />
<link rel="icon" type="image/png" href="/favicon.png" />
<link rel="shortcut icon" href="/favicon.ico" />
```

### Tag-by-tag breakdown

| Tag | `href` | `type` | `sizes` | File exists? | Notes |
|-----|--------|--------|---------|--------------|-------|
| `<link rel="icon" type="image/x-icon">` | `/favicon.ico` | `image/x-icon` | (none) | ✅ Yes | But the bytes are PNG — `type` attribute does not match file content. |
| `<link rel="icon" type="image/png">` | `/favicon.png` | `image/png` | (none) | ✅ Yes | Correctly typed. |
| `<link rel="shortcut icon">` | `/favicon.ico` | (none) | (none) | ✅ Yes | Legacy alias for `rel="icon"`. Redundant with line 1 but harmless. |

### Tags NOT present (but expected for full coverage)

| Missing tag | Why it matters |
|-------------|----------------|
| `<link rel="apple-touch-icon" href="/apple-touch-icon.png">` | iOS home-screen icon; some Google mobile surfaces look for this. |
| `<link rel="manifest" href="/site.webmanifest">` | Android Chrome & PWA. |
| `<link rel="icon" type="image/svg+xml" href="/favicon.svg">` | Scalable, dark-mode-aware favicon. |
| `<link rel="icon" sizes="..." ...>` | `sizes` attribute absent — browsers must guess which file fits each context. |

### Other `<head>` metadata — homepage

| Item | Value | Status |
|------|-------|--------|
| `<meta name="viewport">` | `width=device-width, initial-scale=1` | ✅ Present |
| `<meta name="robots">` | `index, follow` | ✅ Indexable |
| `<link rel="canonical">` | `https://drozq.com/` (APEX, not www) | ⚠️ Canonical is the apex; but site serves from both www and apex with 200. Not a blocker but worth noting — Google will treat apex as primary. |
| `<title>` | "Irvine Listing Agent \| Free Home Valuation \| Joshua Guerrero" | ✅ Present |
| `<meta name="description">` | Present | ✅ |
| Open Graph / Twitter Card | Present | ✅ |
| JSON-LD RealEstateAgent schema | Present | ✅ |

---

## 4. Live Deployment Check

### HTTP HEAD responses (tested against live site)

| URL | HTTP | Content-Type | Content-Length | Observation |
|-----|------|--------------|----------------|-------------|
| `https://www.drozq.com/favicon.ico` | 200 | `image/vnd.microsoft.icon` | (not sent; `Accept-Ranges: bytes`) | ⚠️ **MIME mismatch** — body is PNG bytes |
| `https://drozq.com/favicon.ico` | 200 | `image/vnd.microsoft.icon` | (not sent) | Same content, same issue (29,230 bytes downloaded, ETag matches) |
| `https://www.drozq.com/favicon.png` | 200 | `image/png` | 29,230 | ✅ Correct |
| `https://drozq.com/favicon.png` | 200 | `image/png` | 29,230 | ✅ Correct |
| `https://www.drozq.com/` | 200 | `text/html; charset=utf-8` | (streamed) | ✅ Homepage OK |
| `https://drozq.com/` | 200 | `text/html; charset=utf-8` | (streamed) | ✅ Homepage OK (both hosts serve) |
| `https://www.drozq.com/apple-touch-icon.png` | **200** | `text/html; charset=utf-8` | (streamed) | 🛑 **Soft-404** — returns homepage HTML |
| `https://www.drozq.com/apple-touch-icon-precomposed.png` | **200** | `text/html; charset=utf-8` | (streamed) | 🛑 **Soft-404** |
| `https://www.drozq.com/site.webmanifest` | **200** | `text/html; charset=utf-8` | (streamed) | 🛑 **Soft-404** |
| `https://www.drozq.com/manifest.json` | **200** | `text/html; charset=utf-8` | (streamed) | 🛑 **Soft-404** |
| `https://www.drozq.com/media/icons/Joshua%20Guerrero%20Favicon.png` | 200 | `image/png` | 29,230 | ✅ Old path still accessible (URL-encoded space works) |
| `https://www.drozq.com/not-a-real-path-12345` (control) | **200** | `text/html; charset=utf-8` | (streamed) | 🛑 Confirms CF is SPA-fallback for ALL missing paths |

### MIME vs. bytes — forensic check

I downloaded the live `/favicon.ico` and inspected the bytes:

```
file /tmp/live-favicon.ico
→ PNG image data, 512 x 512, 8-bit/color RGBA, non-interlaced

md5sum of live file:     811075e1970e47751ff33c7063cfac54
md5sum of repo favicon.ico: 811075e1970e47751ff33c7063cfac54
```

The live file matches the repo file exactly. The **Cloudflare `Content-Type: image/vnd.microsoft.icon` is based purely on the `.ico` extension** — CF doesn't content-sniff. Modern browsers tolerate this because they content-sniff themselves, but:

- **Strict crawlers and ad-verification systems may reject** a PNG payload that claims to be an ICO.
- The `<link rel="icon" type="image/x-icon">` further compounds the lie: the HTML asserts `image/x-icon`, the server asserts `image/vnd.microsoft.icon`, and the bytes are PNG.

### Test as Googlebot (UA spoofing)

```
GET /favicon.ico  UA: "Googlebot/2.1"         → 200, image/vnd.microsoft.icon
GET /favicon.ico  UA: "Googlebot-Image/1.0"   → 200, image/vnd.microsoft.icon
GET /              UA: "Googlebot/2.1"         → 200, text/html
```

No UA-specific blocking. ✅

### Google's own favicon service verification

```
GET https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://drozq.com&size=128
→ 200, image/png, 1108 bytes, 128x128 PNG
→ Content-Location: https://www.drozq.com/media/icons/Joshua%20Guerrero%20Favicon.png
```

**Critical insight:** The `Content-Location` header reveals that Google's favicon cache is keyed to the **OLD** path (`/media/icons/Joshua%20Guerrero%20Favicon.png`), not the NEW path (`/favicon.ico`). This is from the site state BEFORE commit `21f6c12` (landed 2026-04-20, i.e., yesterday). **Google Search has not re-crawled the homepage since the favicon HTML was updated.**

Visually confirmed — Google's service returns the correct green "JG" house icon at 128x128 and 64x64.

---

## 5. robots.txt and Crawlability

### Repo `robots.txt`

```
User-agent: *
Allow: /

Sitemap: https://drozq.com/sitemap.xml
```

### Live `robots.txt` (as served by Cloudflare — augmented)

Cloudflare Pages injects a managed preamble. The live response includes:

```
# BEGIN Cloudflare Managed content
User-agent: *
Content-Signal: search=yes,ai-train=no
Allow: /

User-agent: Amazonbot    → Disallow: /
User-agent: Applebot-Extended    → Disallow: /
User-agent: Bytespider    → Disallow: /
User-agent: CCBot    → Disallow: /
User-agent: ClaudeBot    → Disallow: /
User-agent: CloudflareBrowserRenderingCrawler    → Disallow: /
User-agent: Google-Extended    → Disallow: /
User-agent: GPTBot    → Disallow: /
User-agent: meta-externalagent    → Disallow: /
# END Cloudflare Managed Content

User-agent: *
Allow: /

Sitemap: https://drozq.com/sitemap.xml
```

### Crawlability verdict

| Bot | Allowed? |
|-----|----------|
| `Googlebot` | ✅ Allowed (falls under `User-agent: *` → `Allow: /`) |
| `Googlebot-Image` | ✅ Allowed |
| `AdsBot-Google` | ✅ Allowed |
| `Google-Extended` (AI training bot) | ❌ Disallowed (does not affect Search) |

**Neither favicon.ico nor favicon.png is blocked.** Homepage is not blocked. No `noindex` meta tag on homepage (verified: `<meta name="robots" content="index, follow">`). ✅

Sitemap references 16 URLs; none are `noindex`.

---

## 6. Google Favicon Requirements Checklist

Based on Google's current documentation (verified 2026-04-21 at https://developers.google.com/search/docs/appearance/favicon-in-search).

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Favicon file exists at a crawlable URL | ✅ PASS | `/favicon.ico` and `/favicon.png` both return 200 |
| 2 | Favicon is a square image | ✅ PASS | 512 x 512 (1:1) |
| 3 | Favicon is ≥ 8x8 (minimum); recommended > 48x48 | ✅ PASS | 512x512 ≫ 48x48 |
| 4 | Favicon is referenced in homepage `<head>` via supported `rel` value | ✅ PASS | `rel="icon"` and `rel="shortcut icon"` both used |
| 5 | Favicon URL is stable (doesn't change frequently) | ⚠️ **CONCERN** | URL changed on 2026-04-20 from `/media/icons/Joshua Guerrero Favicon.png` to `/favicon.ico` — Google may temporarily treat as unstable |
| 6 | Homepage is indexable (`index, follow`) | ✅ PASS | Verified in HTML + HTTP response |
| 7 | Both `Googlebot` and `Googlebot-Image` can reach it | ✅ PASS | No robots.txt blocking; no UA-specific blocking |
| 8 | Valid image format (ICO/PNG/GIF/JPG/SVG) | ⚠️ **CONCERN** | PNG is valid; but `/favicon.ico` has mismatched extension (bytes are PNG, extension and `type` attr claim ICO) |
| 9 | Not a pure text/letter, flag, or inappropriate content | ✅ PASS | Graphic icon (house outline with "JG") — well within guidelines |
| 10 | URL returns correct MIME type | ⚠️ **FAIL** | `/favicon.ico` serves `image/vnd.microsoft.icon` but bytes are PNG |

**Score: 7 PASS / 3 CONCERN — no hard fails.**

---

## 7. Why the globe icon — ranked hypotheses

1. **(Most likely) Cache lag + recent change.** The favicon HTML was updated on 2026-04-20 (yesterday). Google SERP typically refreshes favicons in 3–30 days after a homepage re-crawl. Google Ads uses its own cache that may lag further.
2. **(Likely contributing) Historical "fragile" URL.** The prior favicon URL contained literal spaces (`Joshua Guerrero Favicon.png`). Browsers auto-encode, but strict validators (Google Ads verification, some SEO tools) may have flagged it as broken. Verified: the fix commit message literally calls it "fragile."
3. **(Likely contributing) `.ico` with PNG bytes.** The current `/favicon.ico` is a PNG renamed. Modern browsers don't care, but Google Ads verification is stricter about MIME/magic-byte consistency.
4. **(Possible) Soft-404s confuse crawlers.** When Google probes `/apple-touch-icon.png` or `/site.webmanifest` as part of favicon auto-discovery, it gets `200 OK` + `text/html` (Cloudflare SPA fallback). A crawler expecting an image and receiving HTML may downgrade confidence in the whole favicon setup.
5. **(Low likelihood) Contrast at 16x16.** Light green strokes on transparent may render poorly against Google's white SERP background. This would cause a *faint* icon, not a globe.

---

## 8. Prioritized Fix List

Apply these in order. Each step is independently beneficial.

---

### Fix #1 — Generate a real multi-size ICO file (HIGH)

**Why:** The current `/favicon.ico` is a PNG renamed. Strict crawlers and Google Ads verification may reject it. A real `.ico` contains multiple sizes embedded in a single file (16, 32, 48).

**How:** Use an online converter or CLI tool. Best option for this project:

1. Open https://realfavicongenerator.net/ in a browser.
2. Upload `media/icons/Joshua Guerrero Favicon.png` (the 512x512 source).
3. On the settings page:
   - **iOS Web Clip**: check "Dedicated picture for iOS"
   - **Android Chrome**: keep defaults (will generate 192x192 and 512x512)
   - **Windows Metro Tiles**: keep defaults
   - **macOS Safari**: keep defaults
   - **Favicon Generator Options**: use path `/`, app name "Drozq", theme color `#42cc93` (or your brand green)
4. Download the generated zip.
5. Extract to repo root — overwriting `favicon.ico` and `favicon.png`. Add new files: `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png`, `site.webmanifest`, `favicon-16x16.png`, `favicon-32x32.png`, `favicon.svg` (if offered).

**Alternative CLI** (Node required):
```bash
npm install -g cli-real-favicon
cli-real-favicon generate favicon-config.json favicon-data.json .
```

---

### Fix #2 — Update HTML `<head>` on all 17 pages (HIGH)

**Why:** Adding `sizes` hints and `apple-touch-icon` gives crawlers explicit metadata instead of making them guess.

**Replace these lines** on every page that has the 3-line favicon block (17 files total — same block in each):

```html
<!-- OLD (on all 17 pages) -->
<link rel="icon" type="image/x-icon" href="/favicon.ico" />
<link rel="icon" type="image/png" href="/favicon.png" />
<link rel="shortcut icon" href="/favicon.ico" />
```

**With:**

```html
<!-- NEW -->
<link rel="icon" href="/favicon.ico" sizes="any" />
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
<meta name="theme-color" content="#42cc93" />
```

Files to update (all contain the same three favicon lines — see Section 3):
- `index.html`
- `about/index.html`
- `california/index.html`
- `contact/index.html`
- `faq/index.html`
- `field-notes/index.html`
- `los-angeles/index.html`
- `market-insights/index.html`
- `meet-the-team/index.html`
- `privacy/index.html`
- `process/index.html`
- `testimonials/index.html`
- `testimonials/001-long-beach-firefighter/index.html`
- `testimonials/002-corona-analyst/index.html`
- `thank-you/index.html`
- `where-we-help/index.html`

---

### Fix #3 — Create `site.webmanifest` (MEDIUM)

**Why:** Android Chrome and the `<link rel="manifest">` tag need it. Also removes one of the soft-404 paths.

**File:** `/site.webmanifest` (new file)

```json
{
  "name": "Drozq — Joshua Guerrero Real Estate",
  "short_name": "Drozq",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "theme_color": "#42cc93",
  "background_color": "#ffffff",
  "display": "standalone",
  "start_url": "/"
}
```

---

### Fix #4 — Kill the soft-404 (MEDIUM)

**Why:** Cloudflare Pages currently serves `/index.html` with HTTP 200 for every missing path. This (a) creates SEO soft-404s, (b) means crawlers probing `/apple-touch-icon.png` before the file existed got HTML, (c) will affect any future unreachable resource.

**Option A (recommended):** Add a real `404.html` at the repo root:

```html
<!-- /404.html -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex, follow" />
  <title>Page not found | Drozq</title>
  <link rel="icon" href="/favicon.ico" sizes="any" />
</head>
<body>
  <h1>Page not found</h1>
  <p>The page you're looking for doesn't exist. <a href="/">Return home</a>.</p>
</body>
</html>
```

Cloudflare Pages auto-serves `/404.html` with HTTP 404 for missing routes when this file is present.

**Option B:** Add a `_redirects` file at repo root to explicitly 404 everything unmatched (only if Option A doesn't work):

```
/* /404.html 404
```

---

### Fix #5 — Add `favicon.svg` for dark-mode support (LOW)

**Why:** SVG favicons can embed `prefers-color-scheme` media queries, letting the icon adapt to Google's dark-mode SERP.

Can be generated from the same source by realfavicongenerator.net if you check "SVG favicon" in the generator settings. Otherwise skip.

---

## 9. Next Steps After the Fix

### Immediate (after deploy)

1. **Validate server responses:**
   ```bash
   curl -I https://www.drozq.com/favicon.ico    # Expect: image/x-icon or image/vnd.microsoft.icon — but the BYTES must now be a real ICO
   curl -I https://www.drozq.com/apple-touch-icon.png   # Expect: 200, image/png
   curl -I https://www.drozq.com/site.webmanifest       # Expect: 200, application/manifest+json
   curl -I https://www.drozq.com/nonexistent             # Expect: 404, text/html (soft-404 fixed)

   # Sanity-check the ICO bytes are a real ICO
   curl -s https://www.drozq.com/favicon.ico | head -c 4 | xxd
   # Expect: `00000000: 0000 0100` (ICO magic number). NOT `89504e47` (PNG).
   ```

2. **Validate in Google Search Console:**
   - Open https://search.google.com/search-console/
   - Use **URL Inspection** → enter `https://drozq.com/`
   - Click **Request Indexing** → confirms re-crawl
   - Also inspect `https://drozq.com/favicon.ico` and `https://drozq.com/apple-touch-icon.png` → verify "URL is indexable" or "Inspected URL"

3. **Validate in RealFaviconGenerator's checker:** https://realfavicongenerator.net/favicon_checker?protocol=https&site=www.drozq.com — free, comprehensive audit.

4. **Validate with Google Rich Results Test:** https://search.google.com/test/rich-results?url=https%3A%2F%2Fdrozq.com — confirms the homepage renders cleanly and the structured-data + head are parseable.

### Google Ads specifically

Google Ads favicon verification is separate from Search. After deploying the fix:

1. Log in to Google Ads.
2. Navigate to **Tools & Settings → Setup → Business identity → Logos**.
3. Upload the same 512x512 source (or a 1:1 crop ≥ 144x144) directly in the Ads UI — this gives Ads a **direct** verified logo rather than relying on favicon auto-discovery.
4. For the domain-level favicon to refresh in Ads: this is cache-based; typically 48–72 hours after your Search Console re-crawl completes.

### Expected timeline

| Event | Typical time after deploy |
|-------|--------------------------|
| Search Console shows re-crawl of homepage | 1–3 days (faster if you request indexing) |
| Google Search SERP favicon updates | 3–14 days after re-crawl |
| Google Ads SERP favicon updates | 7–30 days (or immediate if you upload directly via Ads → Business identity → Logos) |
| Mobile SERPs pick up `apple-touch-icon` | 1–2 weeks after re-crawl |
| Full propagation across all Google surfaces | Up to 30 days |

### If the globe icon persists > 30 days after the fix

Re-run this audit. Probable causes at that point would be:
- Site penalty (check Search Console → Manual actions)
- Ads policy flag on logo content (check Ads account notifications)
- A different underlying issue (e.g., domain reputation, IP-level blocking). Run https://transparencyreport.google.com/safe-browsing/search?url=drozq.com to check domain health.

---

## Appendix A — Commands used in this audit

```bash
# Repo structure
ls -la
find . -name "favicon*" -o -name "apple-touch-icon*" -o -name "*.webmanifest" -o -name "manifest.json"

# Image analysis
file favicon.ico favicon.png
md5sum favicon.ico favicon.png

# HTML scan
grep -riE "favicon|apple-touch-icon|rel=.icon|shortcut icon|manifest" --include="*.html"

# Live deployment
curl -sI https://www.drozq.com/favicon.ico
curl -sI https://drozq.com/favicon.ico
curl -sI https://www.drozq.com/favicon.png
curl -sI https://www.drozq.com/apple-touch-icon.png
curl -sI https://www.drozq.com/site.webmanifest
curl -sI https://www.drozq.com/not-a-real-path-12345
curl -s https://www.drozq.com/ | grep -iE "favicon|apple-touch|manifest|noindex|canonical"
curl -s https://drozq.com/robots.txt

# Googlebot emulation
curl -sI https://drozq.com/favicon.ico -H "User-Agent: Googlebot/2.1 (+http://www.google.com/bot.html)"
curl -sI https://drozq.com/favicon.ico -H "User-Agent: Googlebot-Image/1.0"

# Google favicon service
curl -sL "https://www.google.com/s2/favicons?domain=drozq.com&sz=128" -o /tmp/google-fav.bin
curl -sI "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://drozq.com&size=128"
```

## Appendix B — Files / paths referenced

- Repo: `C:\Users\guerr\Documents\drozq.com\`
- Homepage: `C:\Users\guerr\Documents\drozq.com\index.html`
- Favicons: `C:\Users\guerr\Documents\drozq.com\favicon.ico`, `favicon.png`
- Source icon: `C:\Users\guerr\Documents\drozq.com\media\icons\Joshua Guerrero Favicon.png`
- Robots: `C:\Users\guerr\Documents\drozq.com\robots.txt`
- Sitemap: `C:\Users\guerr\Documents\drozq.com\sitemap.xml`
- Relevant commits: `3443d60` (added root-level favicons, Apr 20), `21f6c12` (fixed HTML references, Apr 20)
- Google's cached favicon snapshot (saved for review): `.claude/google-serp-favicon-64.png`, `.claude/google-serp-favicon-128.png`

---

*End of audit. No code changes were made as part of this report.*
