# Drozq Page Template — Required Reading

> **READ THIS BEFORE BUILDING OR EDITING ANY PAGE.** This is the canonical specification of what makes a Drozq page a Drozq page. The homepage at `/index.html` is the live reference; this doc explains what is in it and why. If you are spinning up a new page, follow the workflow at the bottom of this doc.

*Last reviewed: May 23, 2026*

---

## 0. TL;DR builder's checklist

A new page passes the bar when all of these are true.

- [ ] DOCTYPE, `<html lang="en-US">`, `<meta charset="utf-8">`
- [ ] GTM head snippet + body noscript (container `GTM-KVV3R96P`)
- [ ] FollowUpBoss Widget Tracker pixel (`WT-AETGAYMU`) in `<head>`, right after the GTM end comment
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
- [ ] **Designed mobile-first.** Renders pristine at 375px before anything else. Tablet (768px) and desktop (1440px) are enhancements, not the starting point. If mobile and desktop disagree on a tradeoff, mobile wins.
- [ ] Verified at 375px, 768px, and 1440px, in that order. Hero CTA, mid-page CTA, FAQ accordion, mobile drawer, More popup hover, submit → `/thank-you/?ref=funnel`, console clean.

---

## 1. Design tokens (Panda CSS)

These tokens are declared in the inline `<style>` block at the top of `/index.html` under `@layer tokens`. Use them verbatim. Do not redefine.

### Colors

| Token | Hex | Use |
|---|---|---|
| `--colors-primary` | `#d92228` | Primary CTA red. Hero tabs (selected fg), See Plan button bg, funnel CTA bg, funnel progress fill, focus borders, accent strokes. |
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

### Color discipline (every color maps to a token, no exceptions)

Every color in a page's CSS and JS must resolve to a **named token from the table above**, or to a value **already established in `/index.html`** (the funnel ships a few non-table values: `#f0c9ca` light-red accent, `#ece8e2` warm divider/track, `#d3cfca` control border). **No ad-hoc hex codes.** "It looked about right" is how an off-brand brown (`#b08968`) once shipped as a chart color, alongside one-off grays (`#cfccc7`, `#8a8a8a`, `#efefef`); the tokens already cover every role, so an invented hex is never necessary, only drift.

Pick by role, not by eye:

- **Text:** body `#2b2b2b`, secondary `#3f4650`, muted / fine-print `#757575`, darkest `#1a1816`.
- **Borders / dividers:** card border `#e5e5e5`, control border `#d3cfca`, ultra-light internal divider `#ece8e2`.
- **Surfaces:** white `#fff`, warm section band `#f2f0ef`, dark block `#1a1816` (optionally graded to `#2b2b2b`), footer-only navy `#141f2a`.
- **Red accents / CTAs:** `#d92228`, hover `#a92e2a`; light-red tint (e.g. an eyebrow on a dark block) `#f7d3d4` (`--colors-light-primary`) or the funnel's `#f0c9ca`.
- **Multi-series data viz** (charts, the `/value/` spread): use the market-trends palette as the categorical set, in this order: `#d92228` (red), `#5184e1` (buyer blue), `#0a801f` (positive green), `#beb8b0` (balanced taupe), `#1a1816` (dark). Never invent a hue for "one more series" (no browns, oranges, purples, teals).

**Self-check before commit:** grep the page's new CSS/JS for hex literals and reconcile each against this section.

```
grep -oiE "#[0-9a-f]{6}" your-page/index.html | sort -u
```

Every result must be a token value above or an established `/index.html` value (ignore the large inherited Panda token block, which is the source of truth itself). Anything else is off-brand and blocks the commit.

### Card-on-section contrast (legibility rule, no exceptions)

White cards (`bg_#fff`) MUST sit on a non-white section background. White cards on a white section produce a white-on-white blunder where only a 1px `#e5e5e5` border separates the card from the page — invisible at a glance, especially on glossy displays and at mobile distances.

The canonical pattern (see `/california/` "Proof", `/about/` "Receipts", `/testimonials/` cards):

- **Section bg:** `bg-c_#f2f0ef` (warm light gray)
- **Card bg:** `bg_#fff` with `bd_1px_solid_#e5e5e5`
- **Hover lift:** `translateY(-4px)` + `box-shadow: 0 16px 40px rgba(217,34,40,0.14)` + `border-color: #d92228`

If a section MUST stay white for rhythm reasons, the cards inside it MUST switch to `bg-c_#f2f0ef` (or warmer) so the contrast direction inverts but is preserved. Either direction is fine; same-on-same is never fine.

**Self-check before shipping any card grid:** look at the rendered page, squint at the cards. If the cards visually dissolve into the section, the contrast is wrong. Fix it before commit, not after the user spots it.

### Fonts

| Token | Stack (effective) |
|---|---|
| `--global-font-body` | `GalanoGrotesque, "Helvetica Neue", Helvetica, Arial, sans-serif` |
| `--fonts-sans` | `GalanoGrotesque, "Helvetica Neue", Helvetica, Arial, sans-serif` |
| `--fonts-galano-regular` | `GalanoGrotesque, "Helvetica Neue", Helvetica, Arial, sans-serif` |
| `--fonts-galano-bold` | `GalanoGrotesqueAltBold, "Helvetica Neue", Helvetica, Arial, sans-serif` |

Self-hosted at `/media/fonts/`:
- `galano-grotesque-alt-regular.woff2` + `.woff` (weight 400)
- `galano-grotesque-alt-bold.woff2` + `.woff` (weight 700)
- `roboto-400.woff2` + `.woff`, `roboto-700.woff2` + `.woff` (retired, see below)

**Galano Grotesque Alt is the entire type system, body included (2026-06-12).** Every page carries a one-block override in `<head>` right before `</head>`: it registers a real `GalanoGrotesque` weight-700 face (so bold pulls the bold woff, never a synthesized faux-bold) and repoints `--global-font-body` + `--fonts-sans` to `GalanoGrotesque`. Result: all body copy, headings, the funnel, forms, every character renders in Galano. `ff_galanoBold` (bold) and `ff_galanoRegular` (regular) utility classes still work as before. Copy that override block verbatim onto any new page (or just scaffold from `index.html`, which carries it).

`@font-face` declarations are at the top of the inline `<style>` block; the Galano-700 face + var override is the appended `<style>` before `</head>`. Copy both verbatim.

Note: anywhere this doc still says "Roboto" for a specific element's font (hero H1, tabs, buttons, etc.), it now resolves to Galano via the global override; the size/weight/line-height in those rows still hold. Roboto is retired (files kept for now, no longer referenced). The phantom `ProximaNova` layer (vars + `.ff_proxima*` classes, never loaded, never used) is realtor-clone cruft slated for deletion.

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

### Mobile is the primary canvas

The majority of paid traffic and organic visits to drozq.com land on **mobile**. Every page is designed at **375px first**, then enhanced upward for tablet (**768px**) and desktop (**1440px**).

Hard rules:

- **Base styles are mobile.** Use `min-width` media queries (Panda's `md:` / `lg:` / `xl:` prefixes) to add complexity for larger screens. Never use `max-width` queries to subtract from a desktop-first design.
- **Mobile wins ties.** When mobile and desktop disagree on a layout, copy length, image crop, grid column count, type scale, CTA placement, or tap-target size — mobile is correct. Desktop is the variant.
- **Hero must be pristine at 375px.** The 3-tab CTA, address input, and See Plan button are the conversion engine. They must look intentional at 375px before any tablet/desktop polish.
- **Tap targets ≥ 44 × 44 px.** Apple HIG / Material both. CTAs, tabs, accordion toggles, mobile drawer items all comply.
- **No horizontal scroll at 375px, ever.** A scrollbar at mobile width is a regression. Constrain widths, wrap long URLs, audit `min-width` declarations.
- **Type scale must read on a phone.** Body ≥ 16px (no iOS zoom on input focus), section headlines ≥ 24px, hero ≥ 32px at 375px.
- **Verify in a real mobile viewport.** Don't certify a page as "works on mobile" by resizing a desktop browser. Use DevTools device emulation at 375 × 812 (iPhone) at minimum, and a real phone for any page touching the funnel.

When all three breakpoints can't share the same content, the order of priority is mobile > tablet > desktop. Cut copy on desktop before you cut copy on mobile.

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

  <!-- begin Widget Tracker Code (FollowUpBoss pixel, required, do not modify) -->
  <script>(function(w,i,d,g,e,t){w["WidgetTrackerObject"]=g;(w[g]=w[g]||function()
  {(w[g].q=w[g].q||[]).push(arguments);}),(w[g].ds=1*new Date());(e="script"),
  (t=d.createElement(e)),(e=d.getElementsByTagName(e)[0]);t.async=1;t.src=i;
  e.parentNode.insertBefore(t,e);})
  (window,"https://widgetbe.com/agent",document,"widgetTracker");
  window.widgetTracker("create","WT-AETGAYMU");window.widgetTracker("send","pageview");</script>
  <!-- end Widget Tracker Code -->

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
    <li><a href="/rates/">Mortgage Rates</a></li>
    <li><a href="/prices/">Home Prices</a></li>
    <li><a href="/#tab-buy">For Buyers</a></li>
    <li><a href="/#tab-sell">For Sellers</a></li>
    <li><a href="/value/">Home Value</a></li>
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
    <li><a href="/rates/">Mortgage Rates</a></li>
    <li><a href="/prices/">Home Prices</a></li>
    <li><a href="/#tab-buy">For Buyers</a></li>
    <li><a href="/#tab-sell">For Sellers</a></li>
    <li><a href="/value/">Home Value</a></li>
  </ul>
</li>
```

Opens on hover (`@media (hover: hover)`) and on `.is-open` class toggle. Min-width 200px, white bg, 1px `--colors-border-light` border, subtle shadow.

### Phone CTA

Header carries a phone CTA on desktop showing `(949) 438-5948` (paid-traffic line). The brand-mode line `510-935-5701` does not belong on conversion pages.

---

## 4. Hero

The hero is the top of every page. It contains three things, top to bottom: the **transaction-type tab bar**, the **landing form pill** (address/location + See Plan button), and the **hero copy/visual**.

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

Inside each tabpanel: a `<form>` with the landing input + See Plan submit button.

### Landing form pill

```html
<form class="pos_relative ...">
  <div class="...">  <!-- white pill wrapper -->
    <input type="text" name="location" placeholder="Enter the address you are selling"
           value="" autocomplete="off" ...>
    <button type="submit" class="...">See Plan</button>
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
| Button | Text | "See Plan" |

Placeholders by mode:
- Sell: "Enter the address you are selling"
- Buy: "Enter city, neighborhood, or ZIP"
- Sell & Buy: "Enter the address you are selling" (sell address; buy location captured inside the funnel)

Google Places Autocomplete is bound to every landing `input[name="location"]` for Sell + Sell&Buy modes; Buy mode is free-text.

### Places dropdown polish (the input-pill-flattens pattern, no exceptions)

The Google Places suggestions box (`.pac-container`) must merge into the pill as one seamless container: the pill supplies the rounded **top**, the dropdown supplies the rounded **bottom** (`.pac-container { border-radius: 0 0 16px 16px }`). If the pill keeps its full rounding while the dropdown opens, the square-topped dropdown reads as "cut off" below the rounded pill (the exact bug fixed on `/value/`, 2026-06-30).

The fix is a class, `is-pac-open`, added to the pill while the dropdown is visible, which flattens the pill's bottom corners:
- **Mobile** (input is its own full-width pill): flatten **both** bottom corners of the input.
- **>=480px** (input + button share one pill, dropdown spans the input portion only and stops before the button): flatten the **bottom-left** of the pill wrapper + input; the button keeps `border-radius: 9999px`.

The synced funnel JS (`alignVisiblePac` inside `initFunnelPlaces`) owns this for every landing `form.pos_relative input[name="location"]`: on focus it snaps `.pac-container`'s `left`/`top`/`width` to the input (killing Google's default gap/inset) and toggles `is-pac-open` on the parent `form.pos_relative`. You get it for free by scaffolding the standard hero pill; do not hand-wire it.

**Bespoke address inputs carry their own copy.** A page-specific address field with its **own** `google.maps.places.Autocomplete` (not a `form.pos_relative input[name="location"]`) is invisible to the synced aligner, so it needs the pattern re-implemented locally: the flatten CSS on its own pill class + a focus/observer aligner that toggles the class and snaps its `.pac-container`. The only instance today is `/value/`'s `#value-address-input` (`.value-pill.is-pac-open` CSS + the aligner in `bindPlaces()`), gated so it only touches its own dropdown and cedes repositioning to the synced aligner once a landing pill has been focused (so the two never ping-pong). Any future bespoke address input must copy that.

### Hero pill width (canonical)

The hero pill on the homepage uses a two-layer width scaffold. Reuse it verbatim on every page that ships a hero with the 3-tab CTA.

| Layer | Class (homepage) | Class (non-homepage) | Effect |
|---|---|---|---|
| Outer hero CTA stack | `pos_relative w_100% max-w_772px m_0_auto` | `pos_relative w_100% max-w_700px m_0_auto` | **Homepage:** 772px (extra room for the 2-column layout). **Non-homepage:** 700px so the outer matches the pill exactly. |
| Inner per-tabpanel form container | `w_326px xs:w_361px md:w_700px pt_0px bg-c_transparent` | `w_326px xs:w_361px md:w_700px pt_0px bg-c_transparent m_0_auto` | 326px on phones, 361px on larger phones, 700px on desktop. `m_0_auto` on non-homepage centers the pill on mobile when the outer is content-sized. |

Do not change these widths. The pill is the most-clicked element on the page; resizing it changes hero engagement.

### Hero structure (canonical, non-homepage pages)

The non-homepage hero must be **split into two sibling sections inside a shared background wrapper**. The text section and the pill section each have their own centering context, so the pill is centered as a true block in the viewport and doesn't inherit any layout pull from the text container above it.

```html
<div class="pos_relative ov_hidden">                          <!-- shared bg wrapper -->
  <div class="pos_absolute inset_0 z_-1 ov_hidden [&_img]:pos_absolute [&_img]:inset_0 [&_img]:w_100% [&_img]:h_100% [&_img]:d_block [&_img]:obj-f_cover [&_img]:obj-p_100%_60% [&_img]:[@media_(max-width:_480px)]:obj-p_left">
    <img src="/media/images/crystal-cove.webp" alt="..." width="1280" height="640" fetchpriority="high">
    <div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.4)"></div>
  </div>

  <!-- 1) TEXT SECTION: h1 + subhead only, simple block layout, ta_center.
       NO opener eyebrow. The hero is value-per-second: one short headline +
       one short subhead sentence. Body eyebrows are fine; opener is not. -->
  <section aria-labelledby="page-hero-title" class="pos_relative z_1 c_textBody pt_48px xs:pt_80px pb_24px md:pb_32px">
    <div class="w_100% max-w_860px pl_32px pr_32px bx-s_border-box mx_auto ta_center">
      <h1 id="page-hero-title" class="fw_700 ls_1.5px c_#fff lh_40px md:lh_64px fs_32px md:fs_56px mb_16px">Headline.</h1>
      <p class="op_0.9 c_#fff ls_.5px fs_14px md:fs_16px lg:fs_20px m_0">One short subhead sentence.</p>
    </div>
  </section>

  <!-- 2) PILL SECTION: own d_flex jc_center context, tabs jc_center above 700px pill, trust line below -->
  <section aria-label="Start your home valuation" class="pos_relative z_1 pb_48px xs:pb_64px md:pb_80px">
    <div class="d_flex jc_center pl_32px pr_32px bx-s_border-box mb_24px">
      <div class="pos_relative w_100% max-w_700px">
        <div class="pos_relative" role="button" tabindex="0" aria-label="Property transaction type selector">
          <div class="d_flex jc_center gap_6px mb_0px">
            <div role="tablist" class="d_flex jc_center bdr_8px_8px_0_0 ov_hidden">
              <button id="tab-sell">Sell</button>
              <button id="tab-buy">Buy</button>
              <button id="tab-sell-buy">Sell &amp; Buy</button>
            </div>
          </div>
          <div class="w_100% bdr_30px pos_relative min-h_60px">
            <div id="tabpanel-sell" role="tabpanel" aria-labelledby="tab-sell" class="d_block">
              <div class="w_100% max-w_700px pt_0px bg-c_transparent m_0_auto">
                <!-- landing form pill -->
              </div>
            </div>
            <!-- repeat for buy / sell-buy panels -->
          </div>
        </div>
      </div>
    </div>
    <p class="ta_center op_0.85 c_#fff fs_12px md:fs_13px ls_1.5px fw_700" style="text-transform:uppercase">Trust line (DRE, etc).</p>
  </section>
</div>
```

Why two sections instead of one:

1. **Independent centering contexts.** Earlier hero versions used a single `d_flex flex-d_column ai_center` parent for eyebrow + h1 + subhead + pill + trust. Because flex-column `ai_center` doesn't stretch children, the pill wrapper would shrink-to-content and the tab row above the pill would inherit a left-leaning alignment from the text container's shrink behavior. The pill ended up visually pulled to the left even when its computed center matched the viewport center.
2. **Pill is unambiguously centered.** The pill section uses `d_flex jc_center` on its outer wrapper, so the 700px pill block is centered in the viewport with no inheritance from anything above it. Tabs (`jc_center`) sit directly above the pill's geometric center.
3. **Background remains cohesive.** The image is on a shared wrapper that contains BOTH sections, with `inset: 0` so it spans the entire hero block. The 0.4 dark tint overlay also spans both. Visually it reads as one hero with one background image, even though it's structurally two sections.

Do **NOT** revert this to a single section. Three prior fix attempts (`md:jc_left`, `jc_center md:jc_center`, `md:jc_flex-start md:pl_28px`) all kept the single-section layout and all produced different visible regressions. The two-section split is the structural fix.

### Hero (homepage exception)

The homepage hero is a different layout — a 2-column block where the tabs+pill sit on the left and an image sits on the right. It uses the original `max-w_772px` + `md:jc_left` + `md:pl_28px` pattern and is **not** subject to the split-hero rule. Treat the homepage hero as exempt; all other pages follow the two-section pattern above.

### Hero typography

| Element | Mobile | Desktop |
|---|---|---|
| H1 | clamp ~32px to 40px / 700 / Roboto | 56px / 700 / 64px line-height / Roboto |
| Hero subhead | 18px / 400 | 24px / 400 |
| Geo callout ("Irvine, CA") | 24px / 400 / GalanoGrotesqueAltBold | 32px / 400 / GalanoGrotesqueAltBold |

The H1 on the current homepage reads "Irvine Homeowners! Do You Want Every Dollar It's Worth?", a seller-focused avatar call-out. New pages should rewrite the H1 to a page-specific angle (e.g., for a paid distressed-sellers landing: "Sell your Irvine home, on your timeline.").

### Hero opener copy rule (no exceptions)

The hero is the first thing a visitor sees and the highest-leverage real estate on the page. Two elements only: a short **headline** and a short **subhead**. Nothing else above, between, or below them inside the text section.

- **No opener eyebrow.** The 11-12px uppercase "kicker" line above the H1 (`<p class="op_0.9 c_#fff ls_2px fs_11px ...">EYEBROW</p>`) is banned on the opener of every page. It eats visual budget for label text the headline already implies — a value-per-second loss. Body sections downstream can use the eyebrow pattern freely; it is only the opener where the eyebrow is forbidden.
- **Headline is short.** A single tight line. Two short lines max (with an intentional `<br>`) when the rhythm earns it (`/process/`'s "How I sell your home. / Five steps. Six to ten weeks." is the ceiling, not the average).
- **Subhead is one sentence.** Short. Concise. To the point. A desire, a question, or a value statement. Comma-separated lists are fine. Two sentences is wrong: cut to one. Anything longer than ~20 words on desktop probably needs to be cut in half. If the page needs to explain methodology or scope, that belongs in a body section, not the opener.
- **Value per second.** A visitor scanning the splash should leave with one promise, not a paragraph. Everything that survives must earn its place.

The homepage hero (a different layout entirely) is the exception. The rule binds every other page using the canonical two-section hero structure.

### Hero background

The homepage hero uses a flat light background. Hero imagery is not currently part of the homepage (it was deferred). If a new page wants a hero image, treat it as additive on top of the existing scaffolding rather than replacing the structure.

For non-homepage pages on the new template, the default hero background is **`/media/images/crystal-cove.webp`** (a Southern California coastal shot) with a 0.4 dark tint overlay so the white hero copy stays readable. Used on `/california/`, `/los-angeles/`, `/where-we-help/`, `/meet-the-team/`, `/contact/`. Swap to a page-specific image only when there's a real reason (e.g., `/faq/` uses `outside-home-pic1.webp` to signal "home interior" rather than coastline). Always lazy-load any background image that isn't the hero's `fetchpriority="high"` element, always include a meaningful `alt` text, and always carry the dark tint overlay (`<div class="pos_absolute top_0 w_100% h_100% z_2" style="background:rgba(26,24,22,0.4)"></div>`) so hero copy contrast survives the image swap.

### Joshua's portrait placement (Waist.png)

The legacy /about/ and /meet-the-team/ pages used `/media/images/Waist.png` (Joshua's waist-up portrait) prominently in the hero. The new template hero is text-only (background image + centered copy + tab CTA), so the portrait does NOT go in the hero. Move it into a **body section as a 2-column split** beside the most personal copy on the page. Examples:

- `/meet-the-team/` Layer 01 (Joshua as point of contact).
- `/about/` Backstory section (Vallejo origin story).

The 2-column split itself uses a scoped `.drozq-portrait-split` class, NOT the Panda utility `md:grid-tc_280px_1fr`. The Panda CSS soup inherited from `/index.html` only ships classes referenced in the homepage source; the arbitrary `grid-tc_280px_1fr` value is not in that set, so the utility resolves to nothing and the section silently stacks at desktop. Same pitfall as the `.btn-secondary-outline` button (see Section 5). Include this `<style>` block once on every page that uses the portrait split, and apply `class="drozq-portrait-split"` to the grid container:

```html
<style>
.drozq-portrait-split {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  align-items: center;
}
@media (min-width: 768px) {
  .drozq-portrait-split {
    grid-template-columns: 280px 1fr;
    gap: 48px;
  }
}
</style>

<div class="drozq-portrait-split">
  <!-- portrait + copy -->
</div>
```

The portrait wrapper:

```html
<div class="ta_center md:ta_left">
  <img src="/media/images/Waist.png" alt="Joshua Guerrero, Real Estate Agent" width="280" height="380" loading="lazy"
       class="d_inline-block w_220px md:w_280px h_auto bdr_16px ov_hidden bx-sh_0_16px_40px_rgba(30,_47,_73,_0.12)">
</div>
```

220px on mobile, 280px on desktop, 16px border-radius, soft drop shadow. The face belongs next to the personal copy, not floating in the hero.

---

## 5. Body sections

Below the hero, the homepage runs a vertical rhythm of alternating bands. The pattern:

```
[white hero: 2-col, tabs + pill left, image right]
[light gray band #f2f0ef]: "The Hard Parts Are My Job, Not Yours" infographic
[band]: playbook carousel, "Get my 5 playbooks (that sell your home), free.", 5 auto-advancing image slides (left image / right copy)
[wide centered div max-w 1035]: market-trends map (self-hosted Irvine Google Map) + "real estate trends in Irvine, CA" stats
[white band]: review carousel #hpcar, "Real reviews. Real outcomes."
[light gray band #f2f0ef]: "My Home's Condition is..." condition switcher (Move-in ready / Needs work, both open Sell)
[white band]: "What I owe you"
[band]: brand wall, "Seen by every buyer, everywhere" (6 grayscale platform logos)
[band]: FAQ, "Frequently asked: selling and buying in Irvine" (3 offer-aligned tabs)
[light gray band #f2f0ef]: closing CTA, "Get started Today!"
[dark footer #141f2a]
```

Standard section conventions:

| Property | Mobile | Tablet | Desktop |
|---|---|---|---|
| Vertical padding | `py_32px` | `sm:py_48px` | `lg:py_64px` |
| Container max-width | `max-w_100%` | `md:max-w_972px` | `lg:max-w_1035px` or `xl:max-w_1035px` |
| Horizontal padding | `px_32px` | (same) | `lg:px_16px` |
| Section background | white or `#f2f0ef` | (same) | (same) |

### Button hierarchy (canonical, the only two authorized styles)

Two button styles exist on the site. **No third style is authorized.** Do not introduce new button variants without first updating this section.

**1. Primary CTA pill** — only ever used for the inline funnel ("See Plan" or equivalent action that opens the funnel overlay). Filled red. This is the conversion mechanism; reserve it.

```html
<button type="submit"
        class="bg_primary c_white cursor_pointer w_100% xs:w_145px md:w_auto h_48px md:h_54px fs_13px md:fs_18px fw_bold bdr_full px_0px md:px_28px ls_0.5px d_block md:d_inline-flex ai_center gap_0px md:gap_10px hover:bg_primaryHover">
  See Plan
</button>
```

| Token | Value |
|---|---|
| Background | `#d92228` |
| Color | `#fff` |
| Height | 48px mobile / 54px desktop |
| Font | Roboto 700, 13px mobile / 18px desktop |
| Border-radius | `9999px` (pill) |
| Hover | `bg_primaryHover` (`#a92e2a`) |

**2. Secondary outlined link** — used for navigation, related-content links, and "see more" links. Outlined red on transparent bg, fills red on hover. Smaller and lighter than the primary so it never visually competes with the funnel CTA.

The inherited Panda CSS soup does **not** ship rules like `.bd_1px_solid_#d92228` or `.hover:bg_#d92228` (Panda only generates classes referenced in `/index.html`). So a secondary button cannot be expressed in Panda utility classes alone — it needs a real scoped CSS rule. Include this `<style>` block once on every page that uses a secondary button, and apply `class="btn-secondary-outline"`:

```html
<style>
.btn-secondary-outline {
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent; color: #d92228;
  border: 1px solid #d92228;
  font-weight: 700; font-size: 14px; letter-spacing: 0.3px;
  padding: 10px 22px; border-radius: 9999px;
  text-decoration: none;
  transition: background-color .2s ease, color .2s ease;
}
.btn-secondary-outline:hover { background: #d92228; color: #fff; }
@media (min-width: 768px) { .btn-secondary-outline { font-size: 15px; } }
</style>

<a href="..." class="btn-secondary-outline">Read more case files &rarr;</a>
```

| Token | Value |
|---|---|
| Background | `transparent` |
| Border | `1px solid #d92228` |
| Color | `#d92228` |
| Padding | `10px 22px` |
| Font | Roboto 700, 14px mobile / 15px desktop |
| Border-radius | `9999px` (pill) |
| Hover | fills red bg + white text |
| Trailing arrow | `&rarr;` (`→`) |

Use cases that warrant the secondary outlined style:
- Cross-page nav from a related-content section (e.g., "Read more case files →" linking to `/testimonials/`).
- "See more data" or "Read the full X" linking from a summary section to a deeper page.
- "Read the full Los Angeles listing playbook →" on `/where-we-help/`.

Do **NOT** use the primary red filled pill for navigation. It visually competes with the funnel CTA and tells the user "this is the conversion action" when it isn't. A nav link that looks like a See Plan pill steals attention from the actual lead-capture button on the page.

### Closing CTA pill width (canonical)

Every page's bottom-of-page closing CTA wraps its landing form pill in a 540px-max container so the pill reads centered and comfortable, not stretched.

```html
<div id="page-closing-cta" role="tabpanel" aria-labelledby="tab-sell" class="d_flex jc_center">
  <div style="width:100%; max-width: 540px;">
    <!-- landing form pill here -->
  </div>
</div>
```

The wrapping `<div role="tabpanel" aria-labelledby="tab-sell">` is what tells the funnel JS that this pill opens the Sell funnel. Drop this in on every conversion page exactly as-is; only the outer ID may vary per page.

### Closing CTA fineprint (every page except the homepage)

Every page's bottom-of-page closing CTA carries the same single line below the funnel form pill:

```html
<p class="c_#757575 fs_13px md:fs_14px lh_20px mt_24px ta_center">Or call direct: <a href="tel:9494385948" class="c_#d92228 fw_700"><strong>(949) 438-5948</strong></a></p>
```

Just the alternate path: call the line. Do NOT add anti-promise language ("no autodialer," "no spam," "no pressure," "no call center," "no script," "no pitch," "no obligation"). Those phrases plant a negative the prospect wasn't worrying about and turn warm visitors cold. See [Anti-patterns](#14-anti-patterns) for the full ban list. The homepage is the exception to the closing-CTA-pill rule itself (its hero already commits to the timeline; an extra phone CTA at the bottom dilutes the inline funnel).

### Section headlines (H2)

Standard h2:
- Roboto 700 or 800
- 32px / 40px line-height on desktop
- Scale down on mobile

Examples observed:
- "The Hard Parts Are My Job, Not Yours" — 32px / 800
- "My Home's Condition is..." — 32px / 800
- "Real reviews. Real outcomes." — 20px / 800

### Body copy

- Default body: `18px` / 1.6 (h2 body), Roboto 400
- Captions and labels: `14px`
- Eyebrows: `11-12px` / 700 / `letter-spacing: 1.5px` / uppercase / `#d92228` (red eyebrow)

### Reusable building blocks (used across migrated pages)

These section patterns are reused 2+ times across the migrated content pages. Treat them as the vocabulary for any future migration. Copy the matching `migrate_*.py` constant verbatim and just retitle.

| Block | Used on | What it is |
|---|---|---|
| **Narrow centered copy block** | `/about/` (Backstory copy, School, Pattern, Mission, Closer), `/meet-the-team/` Outcome, `/contact/` Why-pricing | Single `<section>` with `max-w_560` to `max-w_720px` container, eyebrow + h2 + 2-4 body paragraphs, all centered. Mobile 16px / desktop 18px body, lh_28/32. Alternates `bg_#fff` and `bg-c_#f2f0ef` to keep section rhythm. **Don't go wider than 720px** or the paragraph reads as a wall of text. |
| **Numbered principle card grid** | `/about/` Values (3 cards), `/meet-the-team/` Layer 03 Systems (3 cards) | `d_grid grid-tc_1fr md:grid-tc_repeat(3,_1fr) gap_16px md:gap_20px`. Each card: red eyebrow with "Principle 01" / "System 01" pattern, h3 title, body. White bg, 16px radius, 1px gray border. |
| **6-card partner grid** | `/meet-the-team/` Layer 02, `/where-we-help/` Why-work-with-me (3 cards, similar) | `grid-tc_1fr md:grid-tc_repeat(2,_1fr) lg:grid-tc_repeat(3,_1fr)`. Each card: red inline SVG icon, gray subtitle eyebrow, h3 title, body. Use when listing trusted partners, area-served counties, or other parallel sets. |
| **Stats strip** | `/about/` By-the-Numbers (3 stats) | `bg-c_#f2f0ef` band, `max-w_780px`, small uppercase label centered above a `grid-tc_1fr_1fr_1fr` of stat items. Each item: red `fs_36px md:fs_44px fw_800` number + 13-14px uppercase sublabel. **Do not** reintroduce the legacy `cf-count-up` animation; the brand-mode JS that drove it is dropped. Static numbers only. |
| **Case-file mini-cards** | `/about/` The Receipts (2 cards) | `grid-tc_1fr md:grid-tc_repeat(2,_1fr)`. Each card is an `<a>` linking to a `/testimonials/<slug>/`. Red eyebrow ("Case File 001"), big `fs_30px md:fs_36px fw_800` stat ("$23,250"), small meta line ("Long Beach &middot; First-Time Buyer"). White bg, hover border `#d92228`. |
| **Crosslink-to-case-files** | `/faq/`, `/meet-the-team/`, `/contact/`, `/about/` | Small narrow centered section near the bottom: red eyebrow, h2, single-paragraph body, single secondary-outlined button linking to `/testimonials/`. Use the `.btn-secondary-outline` style block defined in section 5 (Button hierarchy). |
| **Two-column portrait split** | `/meet-the-team/` Layer 01, `/about/` Backstory | Use the scoped `.drozq-portrait-split` class, NOT the Panda `md:grid-tc_280px_1fr` utility (the latter isn't compiled in the inline CSS soup and silently stacks at desktop). Single column + 32px gap on mobile, two columns `280px 1fr` + 48px gap at >=768px. Joshua's portrait (220px mobile, 280px desktop, 16px radius, soft shadow) on one side; eyebrow + h2 + 2-3 body paragraphs on the other. Full `<style>` block + markup in section 4 "Joshua's portrait placement." |
| **Jump-nav pills + smooth scroll** | `/faq/` only | If a page has 4+ scrolled sections worth jumping between, add a sticky-ish band of `.faq-jump-pill` anchors at the top. Pair with the 30-line vanilla JS smooth-scroll snippet from `migrate_faq.py` (`SMOOTH_SCROLL_SCRIPT` const): 350ms easeOutCubic tween, 24px top offset, respects `prefers-reduced-motion`, replaces history hash without polluting back-button. Scope the JS to `.faq-jump-pill` so it doesn't interfere with header `/#tab-buy` style anchors. |

### Homepage signature sections (playbook carousel + brand wall)

Two homepage-only sections built during the seller rebuild. Both are page-specific (custom imagery + their own JS after `DROZQ_FUNNEL_JS_END`, NOT synced), but they are canonical homepage furniture: copy them when a new page wants the same beat.

- **Playbook carousel** ("Get my 5 playbooks (that sell your home), free."). A left-image / right-copy block whose left image cycles 5 slides: THE SYSTEM, THE TIMELINE, THE FIVE LEVERS, DO NOT RISK, DO THIS TODAY. Each slide's text is baked into the image (desktop + mobile variants in `/media/images/playbook-*.{jpg,png}`), so the slide copy is not live HTML. Auto-advances every 8s and **starts on slide 5** (DO THIS TODAY, the address CTA), so a visitor who lands and reads it has already cycled back to slide 1 by the time they finish. Page-specific JS, not part of the synced funnel.
- **Brand wall** ("Seen by every buyer, everywhere"). A single centered row of 6 grayscale platform logos (`brand_zillow`, `brand_redfin`, `brand_realtorcom`, `brand_google`, `brand_instagram`, `brand_youtube` in `/media/images/`), real official marks desaturated via CSS `filter: grayscale`. Container widens to ~1280px on desktop; logos render at 1.3x base. The promise: your listing is seen everywhere buyers look, no marketplace tax.

---

## 6. Mid-page tabs (the condition switcher)

A two-panel `[role="tab"]` switcher inside a content section, wired by the generic `wireTabs()` (no bespoke handler). Each panel holds its own See Plan landing form plus a left-image column. The homepage instance is **"My Home's Condition is..."**: the visitor self-selects by home condition (Move-in ready / Needs work) and **both panels open the Sell funnel**. There is no buyer panel here, the homepage speaks only to sellers in this section; Buy / Sell & Buy still live in the hero tab bar.

```html
<div role="tablist">                                <!-- ~360px white pill -->
  <button id="sellTabBtn"  role="tab" aria-controls="sellTab"  aria-selected="true"  data-selected="true"  style="max-width:175px;white-space:nowrap">Move-in ready</button>
  <button id="needsTabBtn" role="tab" aria-controls="needsTab" aria-selected="false" data-selected="false" style="max-width:175px;white-space:nowrap">Needs work</button>
</div>

<div id="sellTab"  role="tabpanel" aria-labelledby="sellTabBtn">
  <!-- left: cond-sold.webp (SOLD sign) | right: 3 cards + See Plan address pill -->
</div>
<div id="needsTab" role="tabpanel" aria-labelledby="needsTabBtn" class="d_none" hidden>
  <!-- left: cond-reno.webp (before/after) | right: 3 cards + See Plan address pill -->
</div>
```

| State | Background | Color |
|---|---|---|
| Selected | `#2b2b2b` (charcoal) | `#fff` |
| Unselected | `transparent` | `#2b2b2b` |

Font: GalanoGrotesque 700 16px. Padding 10px 16px. Border-radius `999px` (pill). The two-button strip sits in a ~360px white pill container (`style="max-width:360px"`); each button is capped at 175px with `white-space:nowrap` so "Move-in ready" never wraps. (The old 251px container fit the narrower "I'm selling / I'm buying" labels.)

`detectFunnelMode(form)` reads the form's `[role="tabpanel"]` ancestor (id + aria-labelledby) and substring-matches:
- contains `"sell-buy"` / `"sellandbuy"` / `"sellbuy"` → `sellandbuy`
- contains `"buy"` → `buy`
- default → `sell`

Neither `sellTab`/`sellTabBtn` nor `needsTab`/`needsTabBtn` contains `buy`, so **every form in this section opens the Sell funnel**. The `needs*` naming is the canonical "second Sell panel" pattern: to add a panel that opens a different funnel, put `buy` (→ buy) or `sellbuy` (→ sell & buy) in its id/`aria-labelledby`; to keep a panel on Sell, keep `buy` out of its ids.

**Left-image column.** Each panel carries a real photo in a responsive 3-`<img>` column (desktop near-square box / tablet + mobile banner), one file per panel reused across breakpoints. Move-in ready = `cond-sold.webp` (SOLD sign, `object-fit:cover` with focal-biased `object-position`); Needs work = `cond-reno.webp` (2:3 before/after, `object-fit:contain` on desktop so it letterboxes into the same ~465px box and the cards hold position on tab toggle, measured 5px). Arbitrary Panda `w_*` values no-op, so portrait sizes are set with inline `style`. Full spec in the `CLAUDE.md` "My Home's Condition is..." Done entry.

### Mid-page tab pill width (canonical)

Inside each `#sellTab` / `#needsTab` tabpanel, the landing form pill MUST be wrapped in a 540px-max container — never full-width. A full-width pill at desktop reads as broken layout (the input + See Plan button stretch into ~780px of horizontal space and look wrong).

Both the heading and the pill container MUST be centered within the 780px tabpanel. The h4 uses `ta_center`, and the wrapper div carries `margin: 0 auto`. Earlier versions used `ta_left` with no auto margin on the wrapper, which pinned the heading and the 540px pill flush against the left edge of the tabpanel.

```html
<h4 class="c_#1a1816 fs_16px sm:fs_20px fw_700 lh_24px sm:lh_30px ta_center pb_8px m_0">Enter your address to start the home value report.</h4>
<div style="width:100%; max-width: 540px; margin: 0 auto;">
  <!-- landing form pill here -->
</div>
```

Same container width as the closing CTA pill (below). The mid-tab pill must match the closing CTA pill width exactly.

---

## 7. FAQ accordion

### Container: centered, single column, reading width (no exceptions)

The FAQ is **reading content**, so the whole section (eyebrow + h2 + every question row) lives in a **centered, single-column** block at a **reading width**, never the full-width or wide body container. Wrap it like this:

```html
<section aria-labelledby="page-faq-title" class="... bg-c_#f2f0ef">
  <div class="max-w_720px w_100% m_0_auto pl_32px lg:pl_16px pr_32px lg:pr_16px">
    <!-- centered FAQ header + accordion items -->
  </div>
</section>
```

- `max-w_720px` + `m_0_auto` is a centered ~720px column, so each question sits next to its +/- toggle instead of the toggle flying to the far right of a 1000px-wide row. `720px` is the reading-width ceiling (§5) and the standard for FAQs going forward; some older migrated pages still use the wider `max-w_1035px` body container.
- **The `max-w_*` value MUST be a class that is actually compiled in the inherited Panda soup.** The soup only ships utilities referenced in `/index.html`, so an arbitrary width silently no-ops: a container with `max-w_780px` (not compiled) gets **no** `max-width`, so `w_100%` wins and the FAQ stretches **edge-to-edge across the whole page**: the exact "spread out" bug this rule prevents. Known-compiled widths: `max-w_720px`, `max-w_700px`, `max-w_640px`, `max-w_540px`, `max-w_972px`, `max-w_1035px`. Known **no-ops** (do not use): `max-w_780px`, `max-w_760px`, `max-w_800px`, `max-w_860px`. This is the same compiled-classes-only pitfall as `.btn-secondary-outline` / `.drozq-portrait-split` / `grid-tc_280px_1fr` (§4-5): an uncompiled Panda value fails silently.
- **Verify before commit:** confirm the chosen width is a real rule, and eyeball the result.

```
grep -o "max-width: 720px" your-page/index.html   # must return a hit, else the class is a no-op
```

**Self-check at 1440px:** the FAQ column is visibly centered with margins on both sides, never edge-to-edge.

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
        <div>Drozq.com &middot; Real Brokerage</div>
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

**Working on the funnel safely (hard-won):**
- **Funnel CSS is synced too.** The funnel `<style>` block sits INSIDE the `DROZQ_FUNNEL_HTML` markers, so new funnel classes added there propagate to every page. Put funnel CSS there, never in the page's main style block.
- **Editing `/index.html`.** The funnel block has real newlines (Edit-tool friendly), but the rest of the `<body>` is one ~97KB minified line that the Read/Edit tools choke on. For the body line, or for guarded multi-spot funnel edits, use a Python/PowerShell script: read bytes, detect + preserve the BOM (currently none), `data.replace(old, new)` with `assert data.count(old) == N` BEFORE each replace (a mismatch aborts instead of silently doing a partial edit), assemble all edits in memory, write once with `newline=""`. Always assert the functional funnel IDs survived (`funnel-step5-name`, `funnel-step6-email/phone/submit`, etc.). After a Python write the Edit tool says "File has been modified since read" , re-Read or keep editing in Python.
- **Verify without creating a lead.** Serve locally (`python -m http.server`), open the funnel via `window.openFunnel(address, mode)` (it's exposed on `window`), step through, force-load lazy images, and click submit with an empty field to confirm validation FIRES (don't actually submit, that posts a real lead). The JS submit handler reads `btn.textContent` dynamically, so changing a button label is safe. `fullPage` screenshots flatten the `position:fixed` overlay (shows the page behind) , use viewport screenshots. Cloudflare deploys in ~20s; poll a unique string to confirm before live-verifying.

### Overlay container

```css
#funnel-overlay {
  display: none;            /* opens via .is-open class */
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #efe9e1;       /* warm backdrop; the white value + form cards sit on it */
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
| Step container | `#funnel-step-container` | Mobile: flex column. Desktop (`[data-mode]`, >=880px): centered symmetric split, `max-width:1080px`, two equal `1fr` cards. |
| Form column | `#funnel-form-col` | Wraps all step divs + the timeline. RIGHT card in the desktop split. |
| Steps | `.funnel-step[data-funnel][data-step]` | One div per step per funnel. Active step gets `.active`. |
| Value panel | `#funnel-deliverable` | The unified value panel, identical for every mode: instant valuation + 5-playbook bonus bundle + instant statement. LEFT card in the desktop split. See "unified split funnel" below. |
| Timeline | `.funnel-timeline-sec` | "Your path to sold" graphic (`funnel-timeline.webp`) in its own section under the form, persistent across steps. |

### The unified split funnel (THE STANDARD, 2026-06-13)

Every funnel mode (Sell / Buy / Sell & Buy) renders the **same** value experience; only the form *questions* differ per mode (different data collected). The look is a checkout-style split.

- **Layout.** `openFunnel` stamps `data-mode` on `#funnel-step-container`. At `>=880px` that container becomes a centered **symmetric split** (`max-width:1080px`, two equal `1fr` columns, measured ~502/502): the **value panel** (`#funnel-deliverable`) is the LEFT card (`order:-1`), `#funnel-form-col` (wraps the step divs + the timeline) is the RIGHT card. Below 880px it stacks **form card first, value card below** so the form is instantly fillable. Both are white cards (`border 1px #ece7e1`, `radius 18px`, soft shadow) on a warm `#efe9e1` backdrop.
- **Value panel = ONE JS string for ALL modes** (`dv.innerHTML = DELIVERABLE.sell`, not `DELIVERABLE[mode]`). Top to bottom: red eyebrow "FREE, THE INSTANT YOU FINISH"; an **instant valuation** block (`.funnel-vp-title` "What your home is really worth, to the penny" + a 4-item `.funnel-vp-list`: true market value, rebuild cost, same-day cash offer to the dollar (if you want it), comps + a `.funnel-vp-note`: "Run through my own valuation model: the same data investors and other buyers use, tuned by me. Not a Zestimate guess." , proprietary framing, NEVER say "API"/"Rentcast"); a **bonus bundle** block at the same header size ("Every internal document I use to get a home sold" + the 5 covers `pb-*.webp` in `.funnel-vp-covers` + an upsell-then-free note); and a `.funnel-vp-badge` instant statement ("Delivered the instant you hit submit") , a bordered line with a red bolt, deliberately NOT a filled pill (a pill reads as a button).
- **Valuebar = ONE bar for all modes** (`vb.innerHTML = VALUEBAR.sell`): "Your instant home valuation + BONUS 5 seller playbooks. Free, delivered the moment you finish."
- **Everything is instant.** Valuebar, panel, badge, and every step's `.funnel-assurance` say "the instant you submit" (never "24 hours"). Fineprint is the TCPA consent line (see "TCPA consent fineprint + in-funnel legal modal" below).
- **Forms untouched.** Field names, IDs (`funnel-step5-name`, `funnel-step6-email/phone/submit`, etc.), handlers, validation, POST, redirect: all exactly as before. Only what the visitor SEES changed.
- **Assets.** `/media/images/funnel-timeline.webp`; `/media/images/pb-{pricing,marketing,negotiation,speed,concierge}.webp` (trimmed 3D mockups).
- **CSS classes** (in the synced funnel `<style>`): `.funnel-vp-head/-block/-eyebrow/-title/-list/-note/-covers/-badge`, `.funnel-timeline-sec/-cap`, and the `#funnel-step-container[data-mode]` / `#funnel-form-col` split rules at `>=880px`.
- **Open follow-up:** the "instant" copy runs ahead of the backend (the form emails the lead; nothing auto-delivers the report + playbook PDFs yet). Wiring real instant delivery is pending.
- **Dead code:** the legacy per-mode `VALUEBAR.buy/sellandbuy`, `DELIVERABLE.buy/sellandbuy`, the `DV_BODY` helper, and the `.funnel-dv-*` CSS are now unused (the funnel always uses the sell entries). Safe to prune; tracked in BACKLOG.

### TCPA consent fineprint + in-funnel legal modal (2026-06-15)

The `.funnel-fineprint` under each mode's submit button is the **consent disclosure** (submit = written consent; `lead.js` appends `consent="yes"`, there is no checkbox). It must carry the TCPA elements: who is contacting them (Joshua Guerrero), the channels (**call and text**), the **automated technology and prerecorded or artificial voice** disclosure, "at the number provided," "**consent is not a condition of any purchase**," and the SMS line ("Message and data rates may apply; reply STOP to opt out"). Only the subject differs per mode: home value (Sell) / home search (Buy) / home sale + home search (Sell & Buy). The "Consent is not a condition..." and "reply STOP..." phrases are the **one sanctioned exception** to the no-anti-promise rule: they are required legal elements, not voice choices.

"Privacy Policy" and "Terms" in the fineprint are `<a href="/privacy/" data-legal="privacy" class="funnel-legal-link">` / `<a href="/terms/" data-legal="terms" ...>` links that do **not** navigate away. A delegated click handler `preventDefault`s and opens an in-funnel modal (`#drozq-legal-modal`, `z-index 100001`, above the funnel overlay and the Places dropdown). The modal **fetches the live `/privacy/` and `/terms/` pages**, extracts `.legal-inner` (stripping the page's `.legal-cta` form), retargets any inner links to `target="_blank"`, and renders them as scrollable tiny text. Single source of truth: edit `/privacy/` or `/terms/` and the modal reflects it with no re-sync. Closes via the X, a backdrop tap, or Esc; focus returns to the trigger. HTML + CSS + JS all live inside the funnel markers, so the whole thing syncs to every page. CSS classes: `.drozq-legal-modal/-backdrop/-panel/-head/-title/-x/-body/-meta/-loading` + `.funnel-legal-link`. Fallback: if the fetch fails, the modal shows an "open in a new tab" link instead of breaking.

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
| Fineprint | `.funnel-fineprint` | Style | 11px, `#6b6864`, centered. Content = TCPA consent line + `data-legal` Privacy/Terms modal links (see §TCPA consent fineprint) |
| Back button | `.funnel-back` | Style | 14px, `#6b6864`, transparent, hover `#2b2b2b` |

### The three funnels

| Funnel | `data-funnel` | Steps | Final CTA | Submitted intent |
|---|---|---|---|---|
| Sell | `sell` | 5 (3 in funnel, 2 captured pre-funnel via landing form) | "Send My Report + 5 Playbooks" | `Home Valuation` |
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
- Phone: `normalizeUsDigits()` strips non-digits, drops a leading country-code `1` (an 11-digit string starting with `1` is a leaked `+1`; NANP area codes never start with `1`), then caps at 10. Must be exactly 10 after that. The validated number is canonicalized to `(XXX) XXX-XXXX` and written back to the input so the visitor sees the corrected value and `funnelState.phone` stores it clean. **Never re-introduce the old `value.replace(/\D/g,"").slice(0,10)` shortcut: it shoves the country code into the area-code slot (`(194)...`) and truncates the real last digit, silently corrupting leads.** The formatter and the validator both call `normalizeUsDigits` so a programmatic value drop (autofill / returning-visitor prefill) that never fires the `input` listener is still normalized at submit.
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
| `openFunnel(prefill, mode)` | Opens the overlay. Sets `window.activeFunnel`, reveals header, captures gclid, fires `funnel_open`. Exposed as `window.openFunnel` so bespoke pages (e.g. `/value/`) can open the funnel programmatically: `window.openFunnel(address, "sell")`. `prefill` is the address/location string, `mode` is `sell`/`buy`/`sellandbuy`. |
| `closeFunnel()` | Closes overlay, restores body scroll. |
| `showStep(n)` | Filters `.funnel-step` by `data-funnel === activeFunnel && data-step === String(n)`. Fires `funnel_step_advance` or `funnel_back`. |
| `attachSubmitHandler(btnId, mode, ids)` | Wires the final-step submit per mode. |
| `wireTabs()` | Wires every `[role="tab"]` element generically (works for hero tabs AND mid-page tabs). Toggles aria-selected, data-selected, panel visibility. |
| `initFunnelPlaces()` | Maps Places callback. Real impl is in the IIFE; the race-guard stub at line 3277 of /index.html exists for the Maps async script. |
| Geo autofill | `fetch('/api/geo')` → replace "Columbus, OH" defaults across page + funnel placeholders. |
| FAQ accordion | Delegated click handler on `button[aria-controls$="-content"]`. Toggles aria-expanded + animates max-height. Exclusive: opens one closes others. |
| `track(event, props)` | Dual-fires PostHog (`window.posthog.capture`) + dataLayer (`dataLayer.push({event, ...props})`). Null-safe. |
| Sticky mobile CTA bar | JS-injected `#drozq-sticky-cta` (fixed bottom bar + "What's my home worth?" pill button). Mobile only (`max-width: 767.98px`). Appears once the visitor scrolls past ~0.75 viewport heights (the hero pill stays the only above-the-fold CTA), hides while an input outside the overlay has focus (on-screen keyboard), skipped entirely on `/thank-you/`. Tap fires `sticky_cta_click` {mode:"sell"} then `openFunnel("", "sell")`. z-index 900: under the funnel overlay (9999) and mobile drawer (1100). Safe-area padding via `env(safe-area-inset-bottom)`. Do not add a second bottom-fixed element on mobile; this slot is taken. |

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
| FollowUpBoss Widget Tracker (`WT-AETGAYMU`) | Direct `<script>` in `<head>` after the GTM end comment. Async, from `widgetbe.com/agent`. Not via GTM; not synced (re-apply/verify with `python scripts/add_fub_pixel.py`). |
| PostHog | Loaded by GTM custom HTML tag, served from `t.drozq.com` reverse proxy |
| GA4 (`G-XSP0L11QEY`) | Fires via GTM. No direct gtag on the site. |
| Google Ads conversion tracking | Imports `generate_lead` from GA4. No AW-* tags on the site. |
| gclid capture | Funnel IIFE on page load. Persists to 90-day cookie + sessionStorage. |
| Funnel drop-off events | Funnel IIFE `track()` helper. Dual-fires PostHog + dataLayer. |
| `sticky_cta_click` | Funnel IIFE sticky mobile CTA bar (mode always `sell`). Fires right before `funnel_open`. |
| `lead_confirmed` event | Inline script at end of `/thank-you/index.html`. Gated by sessionStorage flag. |

Do not install AW-* tags, direct gtag, or new pixels beyond the two sanctioned head scripts (the GTM container and the FollowUpBoss Widget Tracker `WT-AETGAYMU`). Any other tracking goes through the GTM container.

---

## 12. Forms (every page)

**The inline 3-funnel is the only lead-capture form on the site.** Do not introduce page-specific intake forms (legacy /contact/ had a 7-field intake form; that's now gone). If the page's conversion intent is "give me a home valuation" or "tell me where you want to buy," the Sell / Buy / Sell&Buy funnels already collect every field (`name`, `email`, `phone`, `address` or `buyLocation`, `timeline`, plus mode-specific qualifiers like `priceRange`, `propertyType`, `buyBudget`, `buyHomeType`). Build the page so the 3-tab CTA + closing address pill are the lead path. Don't rebuild a parallel intake.

The only exception: paid landing pages with a different qualification need (e.g., a future distressed-sellers landing would warrant a distinct multi-step funnel with a confidential-callback intake; see `notes/ads/distressed-sellers-strategy.md`). Those still post to `/api/lead` and follow the same endpoint contract below.

Every form on the site posts to `/api/lead`. The endpoint:
- Accepts `application/x-www-form-urlencoded` or `multipart/form-data`.
- Required fields: `name`, `email`, `phone`, `intent`, `consent="yes"`.
- Honeypot: `company_website`. Non-empty value silently 200s without sending email.
- Returns `{ok:true}` on success, `{ok:false, error}` on failure.
- Normalizes the phone server-side via `normalizePhone()` (defense in depth behind the client formatter): drops a leaked `+1` country code and stamps `+1` on every real lead's phone, so the email Joshua reads and the Zapier payload always carry the full `+1 (XXX) XXX-XXXX` plus a `phone_e164` field. Placeholder phones (`0000000000` from One Tap / valuation-view) pass through untouched; it never rejects a lead.
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

### Step 2: Scaffold via `scripts/migrate_<slug>.py`

The canonical way to scaffold a new page (or re-scaffold an existing one after a copy revision) is a per-page migration script in `scripts/`. Every existing migrated page has one: `migrate_california.py`, `migrate_los_angeles.py`, `migrate_where_we_help.py`, `migrate_process.py`, `migrate_faq.py`, `migrate_meet_the_team.py`, `migrate_contact.py`, etc. Follow this shape:

```python
"""Migrate /<slug>/ to the homepage template scaffold.

KILLED: ... (what brand-mode bits the migration drops)
PRESERVED + reframed: ... (what copy / structure carries over verbatim)
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scaffold_page import scaffold_page

def landing_form_pill(placeholder, value=""): ...   # copy verbatim from any existing migrate_*.py

HERO            = f"..."   # two-section hero per section 4
SECTION_A       = "..."    # body sections per section 5 building blocks
SECTION_B       = "..."
MID_TABS        = f"..."   # per section 6
CROSSLINK       = "..."    # crosslink-to-case-files block
CLOSING_CTA     = f"..."   # closing address pill per section 5
JSON_LD         = "..."    # Person / BreadcrumbList / FAQPage / etc.

MAIN_BODY = HERO + SECTION_A + SECTION_B + MID_TABS + CROSSLINK + CLOSING_CTA + JSON_LD

if __name__ == "__main__":
    scaffold_page(
        target="<slug>/index.html",
        title="...",
        description="...",
        canonical="/<slug>/",
        main_body_html=MAIN_BODY,
        og_title="...",
        og_description="...",
    )
```

`scaffold_page()` (in `scripts/scaffold_page.py`) reads `/index.html`, surgically replaces `<title>` / meta description / canonical / OG tags / Twitter tags / `<main>...</main>` body, leaves the funnel markers + footer + mobile-nav + funnel JS untouched, and writes the result to the target path. The funnel block is later filled in by the sync step (Step 3).

Then run:

```
python scripts/migrate_<slug>.py
```

If you're editing an existing page on the template, edit its `migrate_*.py` constants (NOT the generated HTML), then re-run the script. Edits made directly to the generated HTML get clobbered the next time the migration script runs.

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
- **Introduce an ad-hoc hex color.** Every color in a page's CSS/JS must resolve to a named token in §1 or an established `/index.html` value. No invented hues. For multi-series data viz use the market-trends palette (`#d92228` / `#5184e1` / `#0a801f` / `#beb8b0` / `#1a1816`), never a new color. Self-check: `grep -oiE "#[0-9a-f]{6}"` the page and reconcile each hit against §1 before commit. See §1 "Color discipline."
- **Put the FAQ in a full-width or wide container.** The FAQ accordion is a centered, single-column reading block (`max-w_720px` + `m_0_auto`), not the full-width body. And the `max-w_*` must be a COMPILED class: arbitrary values like `max-w_780px` are not in the Panda soup, silently no-op, and let the FAQ stretch edge-to-edge across the page. Verify it renders constrained (grep the soup / check centered at 1440px). See §7 "Container."
- **Use an uncompiled Panda utility and assume it works.** The inherited soup only ships classes referenced in `/index.html`. Arbitrary values (`max-w_780px`, `grid-tc_280px_1fr`, `bd_1px_solid_#d92228`, etc.) generate no rule and fail silently. If a new arbitrary value is genuinely needed, add a scoped `<style>` rule for it (as with `.btn-secondary-outline` / `.drozq-portrait-split`); never rely on the class existing.
- **Use anti-promise / negative-association copy anywhere.** Banned phrases (non-exhaustive): "no autodialer," "no spam," "no pressure," "no call center," "no script," "no pitch," "no obligation," "no team," "no sales script." These phrases plant a worry the prospect wasn't carrying and turn warm visitors cold. Reframe with positive value: "direct callback within X hours," "from me, with the records pulled," "an honest read on whether to list," "you walk away with better information." Exception: pricing statements that address a real cost concern with positive framing are fine ("No fee unless we list," "free CMA"). The rule is: never name the bad thing, even to deny it.
- Add a separate footer style per page. The minimal footer is the convention.
- Build a new page without registering it in `funnels.json`. The sync is the propagation mechanism; an unregistered page silently drifts from the source.
- **Design desktop-first and "make it responsive" after.** Mobile is the primary canvas, not a downstream port. Start at 375px.
- **Use `max-width` media queries to override a desktop layout for mobile.** Base styles are mobile; use `min-width` queries to add complexity upward.
- **Ship a page you only verified at 1440px.** A page is not done until it has been verified at 375px first, and any layout that fails there blocks the deploy.
- **Stuff desktop copy onto a mobile hero.** Cut copy on desktop before you cut copy on mobile. The mobile hero is the constraint that shapes every headline.
- **Put an eyebrow on the opener.** The hero text section is headline + subhead only. The 11-12px uppercase "kicker" line above the H1 is forbidden on the opener of every page (homepage hero is the exception; it has its own layout). Body eyebrows are fine; opener eyebrows are not. See section 4 "Hero opener copy rule" for the reasoning.
- **Bloat the hero subhead.** One sentence. Short. Concise. If the subhead is two sentences, cut to one. If it lists methodology, sources, or scope, that belongs in a body section. The opener is value per second.

---

If a request requires changing anything in this doc, stop and confirm with Joshua before editing. This is the gospel.
