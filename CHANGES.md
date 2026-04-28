# index.html funnel rebuild

*Date: 2026-04-27*

The previous `/index.html` was a static, minified clone of `sell.realtor.com/re/`
(2,666 lines, no Drozq tracking, no GTM, no Maps, no GCLID capture, no canonical
to drozq.com). It has been replaced with a 6-step lead-capture funnel built from
the canonical Drozq pattern in `/contact/index.html`.

---

## What was added

- **Single-page 6-step funnel** at `/index.html`. Step 1 (address + CTA) lives
  on a landing hero. Steps 2-6 live in `#funnel` and swap one at a time via
  a `.funnel__step.active` class with a 250ms slide-in animation
  (disabled under `prefers-reduced-motion`).
- **State object** `window.funnelState` with `gclid`, `address` (street, city,
  state, zip, lat, lng, formatted), `timeline`, `priceRange`, `propertyType`,
  `fullName`, `email`, `phone`, `pageUrl`, `timestamp`, `userAgent`, `referrer`.
- **Auto-advance** on steps 2/3/4 (150ms delay so the click animation plays).
  Manual continue on steps 5 and 6.
- **Sticky 6-segment progress bar** at the top of the funnel viewport,
  width = `(currentStep / 6) * 100%`.
- **GCLID capture script** (URL param to sessionStorage to 90-day cookie to
  state object). Reads on every page load so users who arrived via Ads days ago
  still attribute correctly.
- **Google Places Autocomplete** wired to step 1 hero address input AND step 5
  address re-confirm input. A single `maps.googleapis.com` script tag at the
  end of `<body>` loads the API once with `callback=initFunnelPlaces`. Step 5's
  autocomplete attaches lazily the first time step 5 is shown.
- **City personalization** on step 4: the `{city}` token in the subtitle and
  question is replaced from `address.city` (falls back to `administrative_area_level_2`
  with the trailing " County" stripped, then to "Southern California").
- **History + back-button handling** via `history.pushState({step: n}, '', '#step-n')`
  and a `popstate` listener. Back button rewinds one step without wiping state.
- **Exit intent popup**: desktop fires on `mouseout` with `clientY < 0` and
  `relatedTarget === null`. Mobile fires on rapid scroll-up (>250px in <250ms,
  step 3+) AND on browser back-button at step 3+ (the popstate handler shows
  the popup instead of navigating, then re-pushes the current step). Once shown
  it never re-shows in the same session (sessionStorage `drozqExitShown=1`).
- **Phone mask** on step 6: input is reformatted to `(xxx) xxx-xxxx` on every
  keystroke. Validation requires exactly 10 digits.
- **Email regex** validation on step 6 before submit.
- **TCPA-style consent text** below the step 6 submit button. Submitting the
  form sets the hidden `consent=yes` field that `/api/lead` requires.
- **Submit handler** with 10-second timeout. Posts FormData to
  `FUNNEL_ENDPOINT` (configurable JS const at top of script block, defaults to
  `/api/lead`). On success, fires `lead_submitted` to dataLayer and redirects
  to `/thank-you/`. On failure or timeout, shows an inline error above the
  button: "Something went wrong. Please call or text Joshua directly at
  (510) 935-5701." (no data lost, console.error logs the failure).
- **GTM events fired** to `window.dataLayer`:
  - `funnel_started` (step 1 place_changed or manual submit)
  - `funnel_step_view` (every step display, with `step` + `step_name`)
  - `funnel_step_answered` (every answer save, with `step`, `step_name`, `answer_value`)
  - `funnel_exit_intent_shown` / `_continue` / `_dismiss`
  - `lead_submitted` (full payload summary on success)
- **Honeypot** field `company_website` (off-screen via absolute positioning,
  not display:none, so bots see it). `/api/lead` already returns ok=true if
  this field is filled (trap path).
- **Minimal footer**: `(510) 935-5701`, `Josh@Drozq.com`, `DRE# 02267255`,
  legal line. Navy bg, white text, centered.
- **Drozq text logo** (top-left "Drozq" in `--color-green`, 800 weight,
  -0.02em tracking). No image asset was needed.
- **`RealEstateAgent` JSON-LD** on the homepage (per CLAUDE.md, "the home
  page carries the RealEstateAgent Organization schema"). Includes
  `address`, `areaServed`, `hasCredential` (DRE), `telephone`, `email`, `image`.

## What was preserved (matches `/contact/index.html` verbatim)

- **Google Tag Manager container** `GTM-KVV3R96P` head snippet (lines 6-11).
  GA4 (`G-XSP0L11QEY`) and PostHog continue to fire via GTM, not via direct
  tags on the page.
- **Drozq design tokens**: `--color-green` (`#42cc93`), `--color-green-hover`,
  `--color-mint`, `--color-navy`, `--color-navy-light`, `--color-gray-light`,
  `--color-gray-bg`, `--color-red`, `--font`, `--site-width`, `--radius`,
  `--radius-lg`, `--transition`, `--shadow`. All values match the existing
  `/contact/` system.
- **Google Maps API key** `AIzaSyAO__0suXD6CDECevon18renbKLmCF-0ks` and the
  `places` library load. Single script tag, deferred, end-of-body, with our
  callback name `initFunnelPlaces`.
- **Address parsing pattern** from `/contact/index.html` (street_number +
  route, locality, sublocality_level_1 fallback, administrative_area_level_1
  short_name for state, postal_code, formatted_address, geometry.location).
- **Form submission target** `/api/lead` (the existing Cloudflare Pages
  Function in `functions/api/lead.js`). Submitted as FormData with the field
  names that handler expects: `name`, `email`, `phone`, `intent`, `timeline`,
  `referral_source`, `source_page`, `consent`, `gclid`, `page_url`,
  `submitted_at`, `street_address`, `city`, `state`, `zip`, `full_address`,
  `lat`, `lng`, `message`, `company_website`.
- **`/thank-you/` redirect** on successful submit. This is the trigger that
  fires `generate_lead` in GA4 via GTM.
- **All Drozq favicons + manifest** (`/favicon-96x96.png`, `/favicon.svg`,
  `/favicon.ico`, `/apple-touch-icon.png`, `/site.webmanifest`).

## What was removed (realtor.com clone artifacts)

- Realtor.com `<head>` (RealChoice OG tags, lt6p.com hero image,
  static.rdc.moveaws.com favicon, sell.realtor.com canonical,
  rcs-consumer:version meta, twitter:creator @realtordotcom, etc.).
- Realtor.com Panda CSS (133KB minified single line) and the Roboto / Galano
  Grotesque @font-face declarations pointing at static.rdc.moveaws.com.
- Realtor.com landing UI (RealChoice hero, "Trusted by..." strip,
  agent-comparison sections, "Realtor.com Coordinator" copy).
- All `realtor.com`, `RealChoice`, `lt6p.com`, `static.rdc.moveaws.com`,
  `rdc.moveaws.com` strings (verified via grep, zero remaining).
- Old non-canonical realtor.com favicon links and OG/Twitter image references.

---

## Configuration TODOs (please verify before going live with paid traffic)

1. **Confirm `/api/lead` is the intended endpoint.** The prompt mentioned
   `https://forms.drozq.com/lead` as a TODO. The existing repo has a working
   `/api/lead` Cloudflare Pages Function (`functions/api/lead.js`) wired to
   MailChannels and Zapier, so the funnel POSTs there. If you'd rather hit a
   separate Worker URL or Formspree endpoint, edit one line:
   ```js
   var FUNNEL_ENDPOINT = '/api/lead';   // change here
   ```
   Note: the existing handler accepts `application/x-www-form-urlencoded`
   or `multipart/form-data` and **rejects** `application/json`. If you swap
   to a Worker that wants JSON, also change the submit handler to
   `JSON.stringify(funnelState)` with `Content-Type: application/json`.

2. **Verify GTM tags exist for the new event names.** The funnel pushes these
   to `dataLayer`. If GTM is not already configured to listen for them, the
   data flows but nothing acts on it. Event names:
   - `funnel_started`
   - `funnel_step_view`
   - `funnel_step_answered`
   - `funnel_exit_intent_shown` / `_continue` / `_dismiss`
   - `lead_submitted`

3. **Confirm the agent avatar load weight.** `/media/images/Waist.png` is
   1.7MB. It's `loading="lazy"` so it only fires when step 5 is reached, but
   even at 56x56 it ships 1.7MB to the user. Consider exporting a 200x200
   crop (call it `/media/images/Waist-avatar.png`) and updating the two
   `<img class="funnel__avatar">` `src` attributes.

4. **CTA color choice.** The prompt asked for "Drozq red" buttons. The actual
   Drozq brand uses GREEN (`#42cc93`) for every primary CTA across `/contact/`,
   `/about/`, `/testimonials/`, etc. I used green to match the rest of the
   site (per CLAUDE.md "Visual consistency across the site"). If you want
   red instead, change `.hero__cta`, `.funnel__cta`, and `.modal__cta`
   `background` values from `var(--color-green)` to `var(--color-red)`.

5. **Step 4 city fallback.** If a user types an address without picking
   from the Places dropdown AND clicks "Get My Estimate," the Place object
   never resolves and `address.city` stays empty. Step 4 then says
   "homes in Southern California" which reads fine but is less personalized.
   No fix needed unless you want to force a Place selection (would hurt
   conversion).

---

## QA checklist (walk through before promoting to paid traffic)

1. **Step 1 → 2 via Places dropdown.** Load `/`, type "1 World Way Los Angeles",
   click a suggestion. Funnel should advance to step 2 within 150ms. Confirm
   `funnel_started` fires in the GTM Preview / dataLayer.

2. **Step 1 → 2 via manual button.** Load `/`, type "irvine ca" without
   picking, click "Get My Estimate." Should still advance to step 2 (raw text
   stored in `address.formatted`).

3. **Steps 2/3/4 auto-advance.** Click each option. Selected card briefly
   shows mint background + scaled-down state, then funnel advances. Confirm
   `funnel_step_answered` fires with the correct `answer_value` for each.

4. **Step 4 city personalization.** Pick "Irvine, CA" on step 1, advance to
   step 4. Headline should read "What type of home are you selling in Irvine?"
   (not "Southern California").

5. **Step 5 validation.** Try submitting with one name word ("John"). Inline
   error shows. Try with empty address. Inline error shows. Submit "John Doe"
   + valid address: advances to step 6.

6. **Step 6 phone mask + validation.** Type `5109355701` into phone. It should
   reformat to `(510) 935-5701`. Try submitting with an invalid email
   (`foo@bar`). Inline error shows. Try a 9-digit phone. Inline error shows.

7. **Step 6 successful submit.** Fill valid email + phone, click Send My CMA.
   Button shows "Sending..." then redirects to `/thank-you/`. Lead email
   arrives via MailChannels (check inbox tied to `TO_EMAIL` env var) with
   the price expectation, property type, and gclid in the body.

8. **GCLID capture.** Visit `/?gclid=TEST_CLAUDE_123`, complete the funnel,
   verify the lead email's `META → GCLID:` line shows `TEST_CLAUDE_123`.
   Then close the tab, reopen `/` (no gclid in URL) within 90 days, complete
   the funnel: GCLID should still be `TEST_CLAUDE_123` (cookie path).

9. **Browser back button.** Advance to step 4. Press browser back. URL hash
   should drop to `#step-3` and step 3 should show with the previously selected
   card NOT auto-re-selected (state preserved but UI is fresh). Forward
   button advances back to step 4.

10. **Exit intent.** On desktop, advance past step 1, then quickly drag the
    cursor toward the address bar (mouse leaves through top). Modal appears
    with the 3 bullets. Click "Finish My Estimate" and the modal closes; you
    stay on the same step. Reload, and the modal should NOT re-trigger
    (sessionStorage flag). On mobile (or DevTools mobile emulator), advance
    to step 3+, hit browser back: modal appears instead of navigating.

---

## Files changed in this commit

- `index.html`: fully replaced (was 2,666 lines of realtor.com clone, now
  1,321 lines of Drozq funnel).
- `CHANGES.md`: new file (this document).

No other files modified. The header/footer of `/contact/`, `/about/`, etc.
were not touched (per CLAUDE.md "Never modify the header or footer"). The
new `index.html` uses its own self-contained minimal header per the funnel
spec, since paid landing pages and content pages have always had different
chrome on this site.
