# Drozq Page Template — Required Reading

> **READ THIS BEFORE BUILDING OR EDITING ANY PAGE.** This is the canonical specification of what makes a Drozq page a Drozq page. The homepage at `/index.html` is the live reference; this doc explains what is in it and why. If you are spinning up a new page, follow the workflow at the bottom of this doc.

*Last reviewed: May 22, 2026*

---

## 0. TL;DR builder's checklist

A new page passes the bar when all of these are true.

- [ ] DOCTYPE, `<html lang="en-US">`, `<meta charset="utf-8">`
- [ ] GTM head snippet + body noscript (container `GTM-KVV3R96P`)
- [ ] Standard meta (title, description, viewport, canonical, OG, Twitter card)
- [ ] Favicon stack (PNG, SVG, ICO, apple-touch, manifest)
- [ ] `noindex,follow` for paid-traffic landing pages, indexable otherwise
- [ ] The Panda CSS utility-class soup from `/index.html` (do not strip)
- [ ] Header (white bar, 48/64px, absolute) with hamburger + More popup + hidden-by-default for new visitors
- [ ] Hero with the 3-tab funnel CTA (Sell / Buy / Sell & Buy) — page-specific copy, same structure
- [ ] At least one mid-page section that re-presents a CTA. Page must always have a path into the funnel.
- [ ] FAQ accordion (optional but recommended)
- [ ] Minimal conversion footer (`#141f2a`, identity stack, Privacy/Terms, copyright)
- [ ] Four `DROZQ_FUNNEL_*` markers bracketing the funnel overlay HTML and JS, in the same order as `/index.html`
- [ ] Mobile-nav script outside the funnel JS markers
- [ ] Page registered in `funnels.json` (`python scripts/sync_funnels.py --add <path>`)
- [ ] `python scripts/sync_funnels.py` reports `OK` for the page
- [ ] Tested at 375px, 768px, 1440px (mobile, tablet, desktop)
- [ ] Verified on live: hero CTA opens funnel, mid-page CTA opens funnel, mid-page tabs swap copy, FAQ accordion expands, mobile drawer opens, More popup hovers, submit redirects to `/thank-you/?ref=funnel`, console clean

---

## 1. Design tokens (Panda CSS)

These tokens are declared in the inline `<style>` block at the top of `/index.html` under `@layer tokens`. Use them verbatim. Do not redefine.

### Colors

| Token | Hex | Use |
|---|---|---|
| `--colors-primary` | `#d92228` | Primary CTA red. Hero tabs (selected fg), Compare Agents button bg, funnel CTA bg, funnel progress fill, focus borders, accent strokes. |
| `--colors-primary-hover` | `#a92e2a` | Primary CTA hover state. |
| `--colors-secondary` | `#d41f24` | Secondary red, near-identical to primary; rarely used. |
| `--colors-light-primary` | `#f7d3d4` | Light red tint. |
| `--colors-text-body` | `#2b2b2b` | Body copy, primary text. |
| `--colors-text-dark` | `#333` | Slightly lighter body. |
| `--colors-text-secondary` | `#3f4650` | Secondary text. |
| `--colors-text-secondary-light` | `#757575` | Muted text. |
| `--colors-text-primary` | `#1a1816` | Darkest text. |
| `--colors-footer-bg` | `#141f2a` | Footer background only. |
| `--colors-background-light-gray` | `#f2f2f2` | Light section band background. |
| `--colors-background-lighter-gray` | `#f0f0f0` | Hover backgrounds. |
| `--colors-background-lightest-gray` | `#f7f7f7` | Subtle hover. |
| `--colors-border-light` | `#e5e5e5` | Borders, dividers. |
| `--colors-overlay-color` | `rgba(0,0,0,0.5)` | Mobile drawer overlay. |
| `--colors-color-tag-positive` | `#0a801f` | Positive market trends, success states. |
| `--colors-color-tag-negative` | `#b81d22` | Negative tags, errors. |
| `--colors-background-tag-positive` | `#e7f5e9` | Positive tag pill bg. |
| `--colors-background-tag-negative` | `#fbe9ea` | Negative tag pill bg. |
| `--colors-buyer-market-trends` | `#5184e1` | Blue, buyer market on heatmap. |
| `--colors-seller-market-trends` | `#e04a4f` | Red, seller market on heatmap. |
| `--colors-balanced-market-trends` | `#beb8b0` | Neutral on heatmap. |

Section background bands you will see on the homepage: `#f2f0ef` (slightly warmer light gray, used as alternating section bg) and white. The standard rhythm is white → `#f2f0ef` → white.

### Fonts

| Token | Stack |
|---|---|
| `--global-font-body` | `Roboto, sans-serif` |
| `--fonts-sans` | `Roboto, sans-serif` |
| `--fonts-galano-regular` | `GalanoGrotesque, "Helvetica Neue", Helvetica, Arial, sans-serif` |
| `--fonts-galano-bold` | `GalanoGrotesqueAltBold, "Helvetica Neue", Helvetica, Arial, sans-serif` |
| `--fonts-proxima-nova` | `ProximaNova, "Helvetica Neue", Helvetica, Arial, sans-serif` |

Self-hosted at `/media/fonts/`:
- `roboto-400.woff2` + `.woff`, `roboto-700.woff2` + `.woff`
- `galano-grotesque-alt-regular.woff2` + `.woff`
- `galano-grotesque-alt-bold.woff2` + `.woff`

`@font-face` declarations are at the top of the inline `<style>` block. Copy them verbatim.

Default body font is Roboto. GalanoGrotesque appears in one place on the homepage: the geo-personalized location callout in the hero ("Irvine, CA"). It is a display font, not a body font.

### Breakpoints

| Name | Pixels |
|---|---|
| xs | 480 |
| sm | 640 |
| md | 768 |
| lg | 992 |
| xl | 1200 |
| 2xl | 1536 |

Panda CSS class prefix maps directly: `md:py_48px` means "at min-width 768px, padding-y 48px."

Design at: **375px (mobile)**, **768px (tablet)**, **1440px (desktop)**. Test at all three.

### Spacing

Tailwind-like scale: `--spacing-0` = 0, `--spacing-1` = 0.25rem (4px), `--spacing-2` = 0.5rem (8px), …, `--spacing-16` = 4rem (64px), `--spacing-24` = 6rem (96px), `--spacing-32` = 8rem (128px). Half-steps exist at `--spacing-0\.5`, `--spacing-1\.5`, etc.

Standard section padding on the homepage:
- Mobile: `py_32px` to `py_48px` (32-48px top/bottom)
- Tablet: `sm:py_48px`
- Desktop: `lg:py_64px`

Standard container max-widths used on the homepage:
- `max-w_972px` (tablet)
- `max-w_1035px` (desktop main content)
- `max-w_8xl` (footer wrapper, with `lg:max-w_1069px`)

### Radii

| Token | Value | Use |
|---|---|---|
| `--radii-sm` (0.25rem) | 4px | Subtle |
| `--radii-md` (0.375rem) | 6px | Buttons (legacy) |
| `--radii-lg` (0.5rem) | 8px | Cards, hero tab tops |
| `--radii-xl` (0.75rem) | 12px | Funnel option cards |
| `--radii-2xl` (1rem) | 16px | Card containers, deliverable card |
| `--radii-full` (9999px) | pill | Primary CTAs, mid-page tab buttons, pill chips |

---

## 2. Page boilerplate (head block)

```html
<!DOCTYPE html>
<html lang="en-US"><head>
  <meta charset="utf-8">

  <!-- Google Tag Manager (required, do not modify) -->
  <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
  new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
  j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
  'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
  })(window,document,'script','dataLayer','GTM-KVV3R96P');</script>
  <!-- End Google Tag Manager -->

  <title>[Page title] | Joshua Guerrero, Real Brokerage</title>
  <meta name="description" content="[Page description, 140-160 chars]">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <link rel="canonical" href="https://drozq.com/[path]/">

  <meta property="og:url" content="https://drozq.com/[path]/">
  <meta property="og:title" content="[Page OG title]">
  <meta property="og:description" content="[Page OG description]">
  <meta property="og:image" content="https://drozq.com/preview.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="en_US">
  <meta property="og:site_name" content="Drozq">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="[Twitter title]">
  <meta name="twitter:description" content="[Twitter description]">
  <meta name="twitter:image" content="https://drozq.com/preview.png">

  <!-- Paid landing pages: <meta name="robots" content="noindex,follow"> -->

  <link rel="icon" type="image/png" href="/favicon-96x96.png?v=20260506" sizes="96x96">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg?v=20260506">
  <link rel="shortcut icon" href="/favicon.ico?v=20260506">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png?v=20260506">
  <meta name="apple-mobile-web-app-title" content="Drozq">
  <link rel="manifest" href="/site.webmanifest?v=20260506">

  <!-- The Panda CSS utility-class soup + @layer reset/base/tokens/recipes
       /utilities goes here verbatim from /index.html. Do not strip. -->
  <style data-inlined="desktop">
    @font-face { font-family: Roboto; font-style: normal; font-weight: 400; ... }
    @font-face { font-family: Roboto; font-style: normal; font-weight: 700; ... }
    @font-face { font-family: GalanoGrotesqueAltBold; ... }
    @font-face { font-family: GalanoGrotesque; ... }

    @layer reset, base, tokens, recipes, utilities;
    @layer reset { /* CSS reset (~30 rules) */ }
    @layer base { /* :root tokens, body font, header position */ }
    @layer tokens { /* all the design tokens above */ }
    @layer utilities { /* the thousands of Panda utility classes */ }
  </style>

  <!-- Inline head script: hide header for new desktop visitors. Must run
       before paint to avoid flash. -->
  <script>
    (function() {
      try {
        if (localStorage.getItem('drozq_header_revealed') !== '1') {
          document.documentElement.setAttribute('data-drozq-header-hidden', '1');
        }
      } catch(e) {}
    })();
  </script>
</head>
<body>
  <!-- GTM body noscript (required) -->
  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-KVV3R96P"
    height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>

  <!-- Header -->
  <!-- Main content -->
  <!-- DROZQ_FUNNEL_HTML_BEGIN ... -->
  <!-- DROZQ_FUNNEL_HTML_END -->
  <!-- DROZQ_FUNNEL_JS_BEGIN ... -->
  <!-- DROZQ_FUNNEL_JS_END -->
  <!-- Mobile-nav script -->
</body></html>
```

---

## 3. Header

```html
<header class="pos_absolute top_0 left_0 right_0 bg_white h_48px md:h_64px
               ml_auto mr_auto ta_center z_100 fs_14px lh_1.5">
  <!-- nav -->
</header>
```

| Property | Value |
|---|---|
| Position | `absolute` (sits over the hero, not sticky) |
| Background | `white` |
| Height | `48px` mobile, `64px` desktop |
| Z-index | `100` |
| Font | Roboto 14px / 1.5 |
| Padding | `0` |

### Logo (header and footer)

**The Drozq logo, wherever it appears, is wrapped in `<a href="/" aria-label="Drozq home">`.** This applies to both the header logo (`brand-header-logo.png`) and the footer logo (`brand-logo-white.png`). On the homepage itself the link is a no-op (it scrolls to top); on every other page it is the universal escape hatch back to the conversion-first homepage. Shipping an unlinked logo is a regression.

### Behavior 1: hidden by default for new desktop visitors

```css
@media (min-width: 768px) {
  html[data-drozq-header-hidden="1"] .drozq-header-content {
    visibility: hidden !important;
    pointer-events: none !important;
  }
}
```

The inline head script sets `data-drozq-header-hidden="1"` before paint when `localStorage.drozq_header_revealed !== '1'`. `openFunnel()` removes the attribute and sets `localStorage.drozq_header_revealed = '1'`. Returning visitors always see the full header. Mobile is untouched.

### Behavior 2: mobile drawer

```html
<button id="drozq-hamburger" ...> <!-- hamburger icon (menu_icon.svg) --> </button>
<aside data-testid="sidebar" data-active="false" class="...">
  <ul data-testid="mobile-nav-items">
    <li><a href="/faq/">FAQ</a></li>
    <li><a href="/#tab-buy">For Buyers</a></li>
    <li><a href="/#tab-sell">For Sellers</a></li>
    <li><a href="/#top">Home Value</a></li>
    <li><a>Tips</a></li>            <!-- no href: page coming soon -->
  </ul>
</aside>
```

Drawer toggle wired in the mobile-nav script (the `<script>` block after `DROZQ_FUNNEL_JS_END`). `[data-testid="sidebar"][data-active="true"]` slides the drawer in. Body scroll is locked while open.

### Behavior 3: desktop "More" popup

```html
<li id="drozq-more-li" class="...">
  <span id="drozq-more-toggle">More</span>
  <ul id="drozq-more-menu">
    <li><a href="/faq/">FAQ</a></li>
    <li><a href="/#tab-buy">For Buyers</a></li>
    <li><a href="/#tab-sell">For Sellers</a></li>
    <li><a href="/#top">Home Value</a></li>
    <li><a>Tips</a></li>
  </ul>
</li>
```

Opens on hover (`@media (hover: hover)`) and on `.is-open` class toggle. Min-width 200px, white bg, 1px `--colors-border-light` border, subtle shadow.

### Phone CTA

Header carries a phone CTA on desktop showing `(949) 438-5948` (paid-traffic line). The brand-mode line `510-935-5701` does not belong on conversion pages.

---

## 4. Hero

The hero is the top of every page. It contains three things, top to bottom: the **transaction-type tab bar**, the **landing form pill** (address/location + Compare Agents button), and the **hero copy/visual**.

### Tab bar (Sell / Buy / Sell & Buy)

```html
<div role="tablist">
  <button id="tab-sell"     role="tab" aria-controls="tabpanel-sell"     aria-selected="true">Sell</button>
  <button id="tab-buy"      role="tab" aria-controls="tabpanel-buy"      aria-selected="false">Buy</button>
  <button id="tab-sell-buy" role="tab" aria-controls="tabpanel-sell-buy" aria-selected="false">Sell &amp; Buy</button>
</div>
```

Style (set via ID-scoped rules in the inline funnel `<style>` block):

| State | Background | Color | Padding | Border-radius |
|---|---|---|---|---|
| Selected | `#fff` | `#d92228` | `12px 16px` | `8px 8px 0 0` |
| Unselected | `#d92228` | `#fff` | `8px 16px` | `8px 8px 0 0` |
| Unselected hover | `#a92e2a` | `#fff` | `8px 16px` | `8px 8px 0 0` |

Font: Roboto 700 13px / 16px. The selected tab pops up because of the 4px taller padding; tabs share a flex-end baseline.

### Tabpanels

Each tab has a sibling `<div role="tabpanel" id="tabpanel-{sell|buy|sell-buy}">` whose visibility is toggled by `wireTabs()` (sets `aria-selected` + `data-selected` + adds/removes `d_none` class + `hidden` attribute).

Inside each tabpanel: a `<form>` with the landing input + Compare Agents submit button.

### Landing form pill

```html
<form class="pos_relative ...">
  <div class="...">  <!-- white pill wrapper -->
    <input type="text" name="location" placeholder="Enter the address you are selling"
           value="" autocomplete="off" ...>
    <button type="submit" class="...">Compare Agents</button>
  </div>
  <input type="hidden" name="gclid" value="">
</form>
```

Style:

| Element | Property | Value |
|---|---|---|
| Input | Height | `60px` |
| Input | Font size | `16px` |
| Input | Padding | `0 8px 0 32px` (left padding aligns with PAC dropdown items) |
| Input | Border-radius | `30px 0 0 30px` (left half of pill) |
| Input | Background | transparent (sits in white pill wrapper) |
| Button | Background | `#d92228` |
| Button | Color | `#fff` |
| Button | Font | Roboto 700 18px |
| Button | Height | `54px` |
| Button | Border-radius | `9999px` (right pill cap) |
| Button | Text | "Compare Agents" |

Placeholders by mode:
- Sell: "Enter the address you are selling"
- Buy: "Enter city, neighborhood, or ZIP"
- Sell & Buy: "Enter the address you are selling" (sell address; buy location captured inside the funnel)

Google Places Autocomplete is bound to every landing `input[name="location"]` for Sell + Sell&Buy modes; Buy mode is free-text.

### Hero typography

| Element | Mobile | Desktop |
|---|---|---|
| H1 | clamp ~32px to 40px / 700 / Roboto | 56px / 700 / 64px line-height / Roboto |
| Hero subhead | 18px / 400 | 24px / 400 |
| Geo callout ("Irvine, CA") | 24px / 400 / GalanoGrotesqueAltBold | 32px / 400 / GalanoGrotesqueAltBold |

The H1 on the current homepage reads "Compare Agents. Find a Trusted Expert." — this is realtor-clone copy. New pages should rewrite the H1 to a page-specific angle (e.g., for `/relief/`: "Sell your Irvine home, on your timeline.").

### Hero background

The homepage hero uses a flat light background. Hero imagery is not currently part of the homepage (it was deferred). If a new page wants a hero image, treat it as additive on top of the existing scaffolding rather than replacing the structure.

---

## 5. Body sections

Below the hero, the homepage runs a vertical rhythm of alternating bands. The pattern:

```
[white hero]
[light gray band #f2f0ef] — "How We Match You" / agent profiles
[white band] — review carousel #hpcar
[white band max-w 972/1035] — content
[wide centered div max-w 1035] — market trends iframe + Irvine stats
[light gray band #f2f0ef] — "Why work with an agent?" with mid-page tabs
[white band] — content
[max-w 1035 band] — content
[centered div with margin] — content
[light gray band #f2f0ef] — closing CTA
[dark footer #141f2a]
```

Standard section conventions:

| Property | Mobile | Tablet | Desktop |
|---|---|---|---|
| Vertical padding | `py_32px` | `sm:py_48px` | `lg:py_64px` |
| Container max-width | `max-w_100%` | `md:max-w_972px` | `lg:max-w_1035px` or `xl:max-w_1035px` |
| Horizontal padding | `px_32px` | (same) | `lg:px_16px` |
| Section background | white or `#f2f0ef` | (same) | (same) |

### Closing CTA fineprint (every page except the homepage)

Every page's bottom-of-page closing CTA carries the same single line below the funnel form pill:

```html
<p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
```

No "free CMA," no "no autodialer, no spam" boilerplate. Just the alternate path: call the line. The homepage is the exception (its hero already commits to the timeline; an extra phone CTA at the bottom dilutes the inline funnel).

### Section headlines (H2)

Standard h2:
- Roboto 700 or 800
- 32px / 40px line-height on desktop
- Scale down on mobile

Examples observed:
- "How We Match You With the Right Agent" — 32px / 800
- "Why work with an agent?" — 32px / 800
- "Real reviews. Real outcomes." — 20px / 800

### Body copy

- Default body: `18px` / 1.6 (h2 body), Roboto 400
- Captions and labels: `14px`
- Eyebrows: `11-12px` / 700 / `letter-spacing: 1.5px` / uppercase / `#d92228` (red eyebrow)

---

## 6. Mid-page tabs ("I'm selling / I'm buying")

Used inside a content section that needs to swap copy between seller and buyer messaging. Each tab opens a panel that contains its own Compare Agents form, which opens the funnel in the matching mode.

```html
<div role="tablist">
  <button id="sellTabBtn" role="tab" aria-controls="sellTab" aria-selected="true"  data-selected="true">I'm selling</button>
  <button id="buyTabBtn"  role="tab" aria-controls="buyTab"  aria-selected="false" data-selected="false">I'm buying</button>
</div>

<div id="sellTab" role="tabpanel" aria-labelledby="sellTabBtn">
  <!-- seller-targeted copy + a landing form -->
</div>
<div id="buyTab"  role="tabpanel" aria-labelledby="buyTabBtn"  class="d_none" hidden>
  <!-- buyer-targeted copy + a landing form -->
</div>
```

| State | Background | Color |
|---|---|---|
| Selected | `#2b2b2b` (charcoal) | `#fff` |
| Unselected | `transparent` | `#2b2b2b` |

Font: Roboto 700 16px. Padding 10px 16px. Border-radius `999px` (pill). The tab strip itself sits in a 251px-wide white pill container.

`detectFunnelMode(form)` reads the form's `[role="tabpanel"]` ancestor (id + aria-labelledby) and substring-matches:
- contains `"sell-buy"` / `"sellandbuy"` / `"sellbuy"` → `sellandbuy`
- contains `"buy"` → `buy`
- default → `sell`

So `aria-labelledby="buyTabBtn"` on `#buyTab` resolves to buy mode. Renaming the IDs is safe as long as `buy` appears in the buy-mode IDs and not in the sell-mode IDs.

---

## 7. FAQ accordion

```html
<button aria-controls="faq-1-content" aria-expanded="false" id="faq-1-header">
  <span>Is our AgentLocator Service free?</span>
  <svg class="faq-icon" viewBox="...">
    <path class="faq-icon-horizontal" />
    <path class="faq-icon-vertical" />
  </svg>
</button>
<div role="region" aria-labelledby="faq-1-header" id="faq-1-content" style="max-height: 0;">
  <p>Answer copy here.</p>
</div>
```

Style:

| Element | Property | Value |
|---|---|---|
| Question button | Font size | `16px` |
| Question button | Font weight | `400` (normal, not bold) |
| Question button | Padding | `10px 40px 16px 0` (40px right reserves space for icon) |
| Region | Transition | `max-height 0.3s ease` |
| Region | Overflow | `hidden` |
| Icon vertical stroke | Hidden when expanded | `[aria-expanded="true"] .faq-icon-vertical { display: none }` |

Wiring is delegated and exclusive (opening one closes the others sharing the same `role="region"` pattern). Defined in the funnel JS (`wireFAQ` block).

Default state: all collapsed (`aria-expanded="false"`, inline `max-height: 0`).

---

## 8. Footer (minimal conversion footer)

```html
<footer id="footer" class="pt_48px md:pt_64px pb_48px md:pb_64px c_white bg_footerBg
                           ls_0.5px fs_10px lh_normal
                           [&_a]:c_white [&_a]:td_none [&_a]:bg-c_transparent
                           [&_a:hover]:td_underline ...">
  <div class="pos_relative max-w_8xl mx_auto px_16px md:px_24px lg:max-w_1069px">
    <div class="d_flex flex-d_column ai_center jc_center ta_center gap_24px">
      <a href="/" aria-label="Drozq home"><img src="/media/images/brand-logo-white.png" alt="..." width="165" height="25"></a>

      <div class="d_flex flex-d_column gap_8px fs_14px lh_2">
        <div>Joshua Guerrero &middot; Real Brokerage</div>
        <div>California DRE #02267255</div>
        <div><a href="tel:9494385948" class="fw_bold">(949) 438-5948</a></div>
      </div>

      <div class="d_flex gap_24px ai_center jc_center mt_8px">
        <a href="https://www.facebook.com/Drozq/" ...> [FB SVG] </a>
        <a href="https://www.instagram.com/drozq/" ...> [IG SVG] </a>
        <a href="https://www.youtube.com/@drozq" ...> [YT SVG] </a>
      </div>

      <div class="d_flex flex-wrap_wrap gap_16px ai_center jc_center fs_14px lh_2 fw_normal">
        <a href="/privacy/">Privacy Policy</a>
        <span aria-hidden="true" class="op_0.5">&middot;</span>
        <a href="/terms/">Terms of Service</a>
      </div>

      <div class="fs_12px lh_2 op_0.7 mt_8px">&copy; 2026 Drozq. All rights reserved.</div>
    </div>
  </div>
</footer>
```

| Property | Value |
|---|---|
| Background | `#141f2a` (`--colors-footer-bg`) |
| Text color | `white` |
| Padding | `48px 0` mobile, `64px 0` desktop |
| Layout | Single column, centered, gap 24px |

Do **not** import the heavier legacy brand-mode footer with site-wide nav links. The minimal footer is the convention.

---

## 9. Funnel overlay (the lead capture)

Full structure lives between `DROZQ_FUNNEL_HTML_BEGIN/END` in `/index.html` and is synced to every registered page by `scripts/sync_funnels.py`. Do not hand-edit on synced pages.

### Overlay container

```css
#funnel-overlay {
  display: none;            /* opens via .is-open class */
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #ffffff;
  overflow-y: auto;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, ...;
}
#funnel-overlay.is-open { display: flex; }
```

### Anatomy (top to bottom)

| Element | ID | Purpose |
|---|---|---|
| Progress bar | `#funnel-progress` | 4px sticky top, `#f1efec` track, `#d92228` fill, width transitions over 250ms |
| Valuebar (sticky) | `#funnel-valuebar` | One-line value reminder. Bg `#fbf8f4`, 12px text. Persists across steps. |
| Step container | `#funnel-step-container` | `max-width: 720px`, padding `64px 24px 80px` (96px top desktop). |
| Steps | `.funnel-step[data-funnel][data-step]` | One div per step per funnel. Active step gets `.active`. |
| Deliverable card | `#funnel-deliverable` | Mode-specific "what you get" card, injected on every step. Hidden when empty. |

### Form elements (consistent across all steps)

| Element | Class | Property | Value |
|---|---|---|---|
| H2 | (default) | Font | 28px mobile / 36px desktop, 700, `#2b2b2b` |
| H2 (fit) | `.funnel-h2-fit` | Font | 27px nowrap (Buy submit-step only) |
| Subtitle | `.funnel-subtitle` | Font | 14px, `#6b6864`, ls 0.5px |
| Input | `.funnel-input` | Height | 56px, border `1px #d3cfca`, radius `10px`, focus border `#d92228` |
| CTA button | `.funnel-cta` | Height | 56px, bg `#d92228`, color white, radius `999px`, 17px / 700 |
| CTA hover | `.funnel-cta:hover` | Bg | `#b81d22` |
| Option card | `.funnel-option` | Size | min-height 64px, white bg, border `1px #e6e3df`, radius `12px` |
| Option hover | `.funnel-option:hover` | Border + shadow | red border + light red shadow |
| Option selected | `.funnel-option.is-selected` | Bg + scale | `#fff5f5` bg, red border, scale(0.99) |
| Error | `.funnel-error` | Style | 13px, `#d92228` |
| Fineprint | `.funnel-fineprint` | Style | 11px, `#6b6864`, centered |
| Back button | `.funnel-back` | Style | 14px, `#6b6864`, transparent, hover `#2b2b2b` |

### The three funnels

| Funnel | `data-funnel` | Steps | Final CTA | Submitted intent |
|---|---|---|---|---|
| Sell | `sell` | 5 (3 in funnel, 2 captured pre-funnel via landing form) | "Send My Home Value Report" | `Home Valuation` |
| Buy | `buy` | 5 (4 in funnel, 1 pre-funnel) | "Send My Buyer's Strategy" | `Home Purchase` |
| Sell & Buy | `sellandbuy` | 6 | "Send My Move Plan" | `Home Sale + Purchase` |

Sell funnel steps (in-funnel): timeline → name → email/phone+submit.
Buy funnel steps (in-funnel): timeline → buying process → name → email/phone+submit.
Sell & Buy steps (in-funnel): buy location → buy timeline → buy budget → buy home type → buy process → email/phone+submit.

### Funnel state shape

```js
window.funnelState = {
  // Sell + Sell&Buy:
  address: { street, city, state, zip, lat, lng, formatted },
  timeline, priceRange, propertyType,
  // Buy:
  buyLocation, buyTimeline, buyBudget, buyHomeType, buyProcess,
  // All:
  fullName, email, phone,
  gclid, pageUrl, timestamp
};
```

### Validation rules

- Sell / Sell&Buy address: must be Places-confirmed (street_number + route present). Tracked via `validAddressMap` WeakMap.
- Buy location: free-text, just non-empty.
- Email: standard regex.
- Phone: digit count + standard regex.
- Name: non-empty.

### Submit flow

`attachSubmitHandler(buttonId, mode, ids)` is called three times (one per funnel). On click:

1. Validate. On fail, show inline error, fire `funnel_submit_error`.
2. On pass, fire `funnel_submit_attempt`.
3. Build `FormData` (mode-specific fields, plus gclid + pageUrl + timestamp + intent + consent=yes).
4. POST to `/api/lead`.
5. On 200 + `{ok:true}`, fire `funnel_submit_success`.
6. Set `sessionStorage.drozq_lead_just_submitted = "1"` and `sessionStorage.drozq_lead_mode = mode`.
7. Redirect to `/thank-you/?ref=funnel`.

The redirect + sessionStorage flag pair gates the GA4 `generate_lead` conversion downstream. Breaking either silently destroys conversion measurement.

---

## 10. Behaviors (the homepage JS)

All of this lives in the big `<script>` between `DROZQ_FUNNEL_JS_BEGIN/END`. One IIFE. Synced everywhere.

| Function | Purpose |
|---|---|
| `captureGclid()` | Reads gclid from URL → cookie → sessionStorage. URL wins; persists to 90-day cookie + sessionStorage. Pushes `gclid_captured` to dataLayer on every pageview. |
| `detectFunnelMode(form)` | Returns `"sell"` / `"buy"` / `"sellandbuy"` based on form's tabpanel ancestor. |
| `openFunnel(prefill, mode)` | Opens the overlay. Sets `window.activeFunnel`, reveals header, captures gclid, fires `funnel_open`. |
| `closeFunnel()` | Closes overlay, restores body scroll. |
| `showStep(n)` | Filters `.funnel-step` by `data-funnel === activeFunnel && data-step === String(n)`. Fires `funnel_step_advance` or `funnel_back`. |
| `attachSubmitHandler(btnId, mode, ids)` | Wires the final-step submit per mode. |
| `wireTabs()` | Wires every `[role="tab"]` element generically (works for hero tabs AND mid-page tabs). Toggles aria-selected, data-selected, panel visibility. |
| `initFunnelPlaces()` | Maps Places callback. Real impl is in the IIFE; the race-guard stub at line 3277 of /index.html exists for the Maps async script. |
| Geo autofill | `fetch('/api/geo')` → replace "Columbus, OH" defaults across page + funnel placeholders. |
| FAQ accordion | Delegated click handler on `button[aria-controls$="-content"]`. Toggles aria-expanded + animates max-height. Exclusive: opens one closes others. |
| `track(event, props)` | Dual-fires PostHog (`window.posthog.capture`) + dataLayer (`dataLayer.push({event, ...props})`). Null-safe. |

The mobile-nav IIFE (separate `<script>` tag, OUTSIDE the funnel JS markers) wires:
- `#drozq-hamburger` click → toggle drawer (`[data-testid="sidebar"][data-active="true"]`).
- Overlay click → close drawer.
- `#drozq-more-toggle` click → toggle `.is-open` on `#drozq-more-li`.
- `hashchange` listener → re-apply hash-based tab selection (`/#tab-buy` opens buy tab).

---

## 11. Tracking essentials (every page)

| Concern | Where it lives |
|---|---|
| GTM head snippet + body noscript | Every HTML page (container `GTM-KVV3R96P`) |
| PostHog | Loaded by GTM custom HTML tag, served from `t.drozq.com` reverse proxy |
| GA4 (`G-XSP0L11QEY`) | Fires via GTM. No direct gtag on the site. |
| Google Ads conversion tracking | Imports `generate_lead` from GA4. No AW-* tags on the site. |
| gclid capture | Funnel IIFE on page load. Persists to 90-day cookie + sessionStorage. |
| Funnel drop-off events | Funnel IIFE `track()` helper. Dual-fires PostHog + dataLayer. |
| `lead_confirmed` event | Inline script at end of `/thank-you/index.html`. Gated by sessionStorage flag. |

Do not install AW-* tags, direct gtag, additional pixels, or any tracking outside the GTM container.

---

## 12. Forms (every page)

Every form, including non-funnel page forms, posts to `/api/lead`. The endpoint:
- Accepts `application/x-www-form-urlencoded` or `multipart/form-data`.
- Required fields: `name`, `email`, `phone`, `intent`, `consent="yes"`.
- Honeypot: `company_website`. Non-empty value silently 200s without sending email.
- Returns `{ok:true}` on success, `{ok:false, error}` on failure.
- Sends plaintext email to `TO_EMAIL` via MailChannels.
- Optionally POSTs to `ZAPIER_WEBHOOK_URL` if set.

Every form must include:
- Hidden `<input name="gclid">` (populated by `captureGclid`)
- Hidden `<input name="source_page">` (the URL path, e.g., `homepage-funnel`, `relief-landing`)
- Hidden `<input name="intent">` (`Home Valuation` / `Home Purchase` / `Home Sale + Purchase`)
- Hidden `<input name="consent" value="yes">`

Every form submit must redirect to `/thank-you/?ref=funnel` after success AND set `sessionStorage.drozq_lead_just_submitted = "1"` immediately before the redirect.

---

## 13. New page workflow (gospel)

When asked to build a new page, do this in order. No shortcuts.

### Step 0: Read this doc first

If you skipped here, go back. This entire doc is the spec.

### Step 1: Pick a path and create the directory

```
/new-page-slug/index.html
```

### Step 2: Scaffold from /index.html

Copy `/index.html` to the new path. Then:

- Update `<title>`, `<meta description>`, `<link rel="canonical">`, OG tags, Twitter tags to the new page's values.
- If paid landing: add `<meta name="robots" content="noindex,follow">`.
- Update the H1 in the hero to a page-specific angle.
- Update mid-page section copy as needed.
- Update FAQ questions/answers as needed.
- Leave the four `DROZQ_FUNNEL_*` markers in place. Do not touch their content.
- Leave the mobile-nav script in place (outside the funnel JS markers).

### Step 3: Register the page with the funnel sync

```
python scripts/sync_funnels.py --add new-page-slug/index.html
```

The script appends the path to `funnels.json#pages`.

### Step 4: Run a sync to confirm alignment

```
python scripts/sync_funnels.py
```

Expected output: `OK new-page-slug/index.html` (the new page's funnel block already matches /index.html because you copied it).

If you see `SYNCED`, that means the new page's funnel block had drift. The script overwrote it from /index.html. Fine.

### Step 5: Commit and push

Auto-commit per CLAUDE.md. Push to main. Cloudflare auto-deploys.

### Step 6: Verify on live within 5 minutes

- Page renders correctly at 375px, 768px, 1440px.
- Header reveals on `openFunnel`, hides for new visitors.
- Hero CTA opens funnel.
- Mid-page CTA opens funnel.
- Mid-page tabs swap copy.
- FAQ accordion expands.
- Mobile drawer opens.
- "More" popup hovers.
- Submit a test lead. Verify redirect to `/thank-you/?ref=funnel`, `lead_confirmed` event in dataLayer, email arrives.
- Console: 0 errors.

### Step 7: When the homepage funnel changes later

```
python scripts/sync_funnels.py
```

Pushes the updated funnel from /index.html to every page in `funnels.json`. One command. Commit + push.

---

## 14. Anti-patterns

Do not.

- Ship an unlinked logo. The Drozq logo in the header AND the footer must be wrapped in `<a href="/" aria-label="Drozq home">`. Universal back-to-home escape hatch.
- Strip the Panda CSS utility-class soup. Even unused classes stay; the layer architecture depends on declaration order.
- Use brand-mode patterns on new pages: mint hero block, navy footer with full nav grid, "Case File N" framing, brand-mode `<style>` system. That's the legacy look; it does not propagate to new work.
- Hand-edit a synced page's funnel block. Edit `/index.html` instead and re-sync.
- Add a CTA that goes to a different lead-capture path. The funnel is the lead-capture path.
- Add a redirect-based CTA (e.g., `<a href="/?intent=sell">`). The funnel is inlined; there is no redirect strategy. Open the funnel from the page directly.
- Install direct `gtag.js`, AW-* conversion tags, or any tracking outside the GTM container.
- Remove the `?ref=funnel` from any submit redirect. It is a load-bearing query string for the `lead_confirmed` event gating.
- Remove the `sessionStorage.drozq_lead_just_submitted` flag set before the redirect. Same reason.
- Modify field names, IDs, or `data-funnel` / `data-step` attributes on funnel steps. Downstream JS hardcodes them.
- Add em dashes (U+2014) anywhere in output. Banned.
- Add a separate footer style per page. The minimal footer is the convention.
- Build a new page without registering it in `funnels.json`. The sync is the propagation mechanism; an unregistered page silently drifts from the source.

---

If a request requires changing anything in this doc, stop and confirm with Joshua before editing. This is the gospel.
