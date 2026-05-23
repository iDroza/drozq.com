"""Shared assets for the case-file pages.

Three migration scripts (testimonials index, case 001, case 002) all need
the same cf-* design system, the same landing-form pill, and the same
cross-link strip. This module exports them once.

CSS variables are pre-substituted to literal hex values so the style block
is fully self-contained inside `<main>` and does not depend on a `:root`
declaration on the page.
"""

# Color tokens — remapped from the legacy brand-mode green/navy palette to
# the homepage red/dark palette. Inlined where they appear in the cf-* CSS.
_TOKENS = {
    "var(--color-white)": "#ffffff",
    # Brand-mode green -> homepage primary red.
    "var(--color-green)": "#d92228",
    "var(--color-green-hover)": "#a92e2a",
    # Mint tint -> light red tint, used for accent backgrounds on case-file
    # tab pills.
    "var(--color-mint)": "#fdecec",
    # Navy -> homepage text colors.
    "var(--color-navy)": "#1a1816",
    "var(--color-navy-light)": "#3f4650",
    # Border + light band colors match the homepage convention.
    "var(--color-gray-light)": "#e5e5e5",
    "var(--color-gray-bg)": "#f2f0ef",
    "var(--font)": '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif',
    "var(--radius)": "6px",
    "var(--radius-lg)": "20px",
    "var(--transition)": "0.2s ease",
    # Hardcoded rgba color references in the original cf-* CSS that need to
    # follow the green->red and navy->dark swap.
    "rgba(66, 204, 147, 0.18)": "rgba(217, 34, 40, 0.18)",
    "rgba(66, 204, 147, 0.14)": "rgba(217, 34, 40, 0.14)",
    "rgba(30, 47, 73, 0.25)": "rgba(26, 24, 22, 0.18)",
}


_CF_CSS_RAW = r"""
/* Buttons (scoped to case-file pages). */
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 16px 30px; font-family: var(--font); font-size: 19px;
  font-weight: 600; text-transform: uppercase; line-height: 1.1;
  border: 2px solid transparent; border-radius: var(--radius);
  cursor: pointer; transition: all var(--transition);
  text-decoration: none;
}
.btn--green { background: var(--color-green); color: var(--color-white); border-color: var(--color-green); }
.btn--green:hover { background: var(--color-green-hover); border-color: var(--color-green-hover); color: var(--color-white); }
.btn--full { width: 100%; }

/* cf-* design system. */
.cf-hero, .cf-section { color: var(--color-navy); }

.cf-label {
  display: inline-block; font-size: 0.875rem; font-weight: 600;
  letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--color-green); margin-bottom: 28px;
}

.cf-hero {
  min-height: 60vh; display: flex; align-items: center;
  padding: 120px 0 80px; position: relative;
  background: linear-gradient(180deg, #fafbfa 0%, var(--color-white) 100%);
  overflow: hidden;
}
.cf-hero__inner { width: 100%; max-width: 1100px; margin: 0 auto; padding: 0 30px; }
.cf-hero h1 {
  font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 700;
  line-height: 1.05; letter-spacing: -0.02em;
  color: var(--color-navy); max-width: 18ch; margin: 0;
}
.cf-hero__scroll {
  position: absolute; bottom: 36px; left: 50%; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 14px;
  font-size: 0.75rem; letter-spacing: 0.3em; text-transform: uppercase;
  color: var(--color-navy-light); opacity: 0.75;
}
.cf-hero__scroll::after {
  content: ''; width: 1px; height: 46px;
  background: linear-gradient(to bottom, var(--color-navy-light), transparent);
  animation: cfScroll 2.4s ease-in-out infinite;
}
@keyframes cfScroll {
  0%, 100% { transform: scaleY(0.35); transform-origin: top; opacity: 0.4; }
  50% { transform: scaleY(1); opacity: 1; }
}

.cf-section { padding: 110px 0; background: var(--color-white); }
.cf-section--alt { background: var(--color-gray-bg); }
.cf-narrow { max-width: 720px; margin: 0 auto; padding: 0 30px; text-align: center; }
.cf-wide { max-width: 1100px; margin: 0 auto; padding: 0 30px; }

.cf-body {
  font-size: 1.25rem; line-height: 1.6;
  color: var(--color-navy-light); margin: 0;
}
.cf-body + .cf-body { margin-top: 1.2em; }

.cf-badges {
  display: flex; flex-wrap: wrap; justify-content: center;
  gap: 10px; margin-top: 40px;
}
.cf-badge {
  border: 1px solid var(--color-gray-light);
  border-radius: 999px; padding: 9px 18px;
  font-size: 0.875rem; font-weight: 500;
  color: var(--color-navy); background: var(--color-white);
  letter-spacing: 0.02em;
}

.cf-headline-stat {
  font-size: clamp(2rem, 5vw, 4rem); font-weight: 700;
  line-height: 1.05; letter-spacing: -0.02em;
  color: var(--color-navy); margin: 0 0 50px; text-align: center;
}
.cf-houses {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 18px; max-width: 520px; margin: 0 auto 50px;
}
.cf-house { aspect-ratio: 1/1; display: block; }
.cf-house svg { width: 100%; height: 100%; display: block; }
.cf-house path { fill: #c4cdd8; transition: fill 0.3s ease; }
.cf-house--match { animation: cfHouse 2.6s ease-in-out infinite; transform-origin: center; }
.cf-house--match path { fill: var(--color-green); }
@keyframes cfHouse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.12); }
}

.cf-hero-stat { text-align: center; margin-bottom: 70px; }
.cf-hero-stat__number {
  display: inline-block;
  font-size: clamp(4rem, 12vw, 9rem); font-weight: 800;
  color: var(--color-green); line-height: 1;
  letter-spacing: -0.04em; font-variant-numeric: tabular-nums;
}
.cf-hero-stat__label {
  font-size: 1rem; font-weight: 600; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--color-navy-light);
  margin-top: 22px;
}

.cf-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 18px; max-width: 1000px; margin: 0 auto;
}
.cf-grid__card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-lg);
  padding: 34px 22px; text-align: center;
}
.cf-grid__value {
  font-size: clamp(1.75rem, 3vw, 2.25rem); font-weight: 700;
  color: var(--color-navy); line-height: 1.1; margin: 0 0 10px;
  font-variant-numeric: tabular-nums;
}
.cf-grid__value--accent { color: var(--color-green); font-size: 2.75rem; line-height: 1; }
.cf-grid__label {
  font-size: 0.9rem; font-weight: 500; line-height: 1.4;
  color: var(--color-navy-light); margin: 0;
}

.cf-receipt {
  max-width: 520px; margin: 70px auto 0;
  background: var(--color-white);
  border: 1px dashed #c4cdd8;
  border-radius: var(--radius); padding: 32px 28px;
  font-family: "SF Mono", Monaco, "Cascadia Code", Consolas, "Courier New", monospace;
  font-size: 0.95rem; color: var(--color-navy);
}
.cf-receipt__title {
  font-family: var(--font); font-size: 0.75rem; letter-spacing: 0.25em;
  text-transform: uppercase; color: var(--color-navy-light);
  margin: 0 0 22px; text-align: center; font-weight: 600;
}
.cf-receipt__row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 10px 0; gap: 12px;
  border-bottom: 1px dotted rgba(30, 47, 73, 0.25);
}
.cf-receipt__row:last-of-type { border-bottom: none; }
.cf-receipt__row--total {
  margin-top: 8px; padding-top: 14px; font-weight: 700;
  font-size: 1.05rem; border-top: 2px solid var(--color-navy);
  border-bottom: none;
}
.cf-receipt__label { flex: 0 1 auto; }
.cf-receipt__amount { flex: 0 0 auto; font-variant-numeric: tabular-nums; }

.cf-compare {
  display: grid; grid-template-columns: 1fr auto 1fr;
  gap: 22px; align-items: center;
  max-width: 820px; margin: 50px auto 0;
}
.cf-compare__card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-lg);
  padding: 32px 24px; text-align: center;
}
.cf-compare__card--muted { opacity: 0.55; }
.cf-compare__card--hero {
  border-color: var(--color-green);
  box-shadow: 0 14px 44px rgba(66, 204, 147, 0.18);
}
.cf-compare__cap {
  font-size: 0.75rem; letter-spacing: 0.22em; text-transform: uppercase;
  color: var(--color-navy-light); font-weight: 600;
  margin: 0 0 14px;
}
.cf-compare__card--hero .cf-compare__cap { color: var(--color-green); }
.cf-compare__value {
  font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 700;
  color: var(--color-navy); line-height: 1.1; margin: 0;
  font-variant-numeric: tabular-nums;
}
.cf-compare__card--hero .cf-compare__value {
  font-size: clamp(1.75rem, 3.5vw, 2.5rem);
}
.cf-compare__arrow {
  display: flex; align-items: center; justify-content: center;
  color: var(--color-green);
}
.cf-compare__arrow svg { width: 40px; height: 40px; }

.cf-quote { max-width: 820px; margin: 0 auto; padding: 0 30px; text-align: center; }
.cf-quote__body {
  font-style: italic; font-size: clamp(1.125rem, 2vw, 1.5rem);
  line-height: 1.6; color: var(--color-navy);
  position: relative; padding: 0 10px; margin: 0;
}
.cf-quote__body::before {
  content: "\201C"; position: absolute;
  top: -56px; left: -6px;
  font-family: Georgia, "Times New Roman", serif; font-style: normal;
  font-size: 7rem; line-height: 1; color: var(--color-green);
  opacity: 0.9;
}
.cf-quote__attribution {
  margin-top: 44px; display: flex; flex-direction: column;
  align-items: center; gap: 14px; color: var(--color-navy-light);
  font-size: 1rem; font-weight: 600; letter-spacing: 0.02em;
}
.cf-quote__attribution::before {
  content: ''; display: block; width: 60px; height: 1px;
  background: currentColor; opacity: 0.5;
}

.cf-takeaway { text-align: center; }
.cf-takeaway__headline {
  font-size: clamp(1.75rem, 4vw, 3rem); font-weight: 700;
  line-height: 1.22; letter-spacing: -0.015em;
  color: var(--color-navy); max-width: 28ch;
  margin: 0 auto 28px;
}
.cf-takeaway__sub {
  font-size: 1.125rem; line-height: 1.6; color: var(--color-navy-light);
  max-width: 580px; margin: 0 auto 40px;
}
.cf-takeaway__next {
  margin-top: 32px; font-size: 0.8rem; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--color-navy-light); opacity: 0.65;
}
.cf-takeaway__next a {
  color: inherit; border-bottom: 1px dotted currentColor;
  transition: color var(--transition), border-color var(--transition);
}
.cf-takeaway__next a:hover { color: var(--color-green); border-color: var(--color-green); }

/* .cf-reveal: scroll-fade-in removed; sections render immediately. */
.cf-reveal { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) {
  .cf-hero__scroll::after, .cf-house--match { animation: none; }
}

/* Stats strip (index page). */
.cf-stats-strip { padding: 60px 0; background: var(--color-white); border-top: 1px solid var(--color-gray-light); border-bottom: 1px solid var(--color-gray-light); }
.cf-stats-strip__inner { max-width: 1100px; margin: 0 auto; padding: 0 30px; text-align: center; }
.cf-stats-strip__label { color: var(--color-navy-light); margin-bottom: 30px; }
.cf-stats-strip__grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; }
.cf-stats-strip__item { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.cf-stats-strip__number {
  font-size: clamp(2rem, 4vw, 2.75rem); font-weight: 800; color: var(--color-green);
  line-height: 1; letter-spacing: -0.02em; font-variant-numeric: tabular-nums;
}
.cf-stats-strip__sub { font-size: 0.875rem; font-weight: 500; color: var(--color-navy-light); }

/* Cross-link strip. */
.cf-crosslink {
  padding: 48px 0; background: var(--color-white);
  border-top: 1px solid var(--color-gray-light);
  text-align: center;
}
.cf-crosslink__label {
  display: block; font-size: 0.75rem; letter-spacing: 0.22em;
  text-transform: uppercase; color: var(--color-navy-light);
  margin-bottom: 14px; opacity: 0.7;
}
.cf-crosslink__nav {
  display: inline-flex; flex-wrap: wrap; justify-content: center;
  gap: 10px 22px; font-size: 0.95rem;
}
.cf-crosslink__nav a {
  color: var(--color-navy-light); font-weight: 500;
  transition: color var(--transition);
  text-decoration: none;
}
.cf-crosslink__nav a:hover { color: var(--color-green); }
.cf-crosslink__sep { color: var(--color-navy-light); opacity: 0.35; }

/* Case file index (gallery). */
.cf-index-section { padding: 80px 0; background: var(--color-white); }
.cf-index-section__label { display: block; text-align: center; margin-bottom: 40px; color: var(--color-navy-light); }
.cf-index-grid {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 32px; max-width: 1100px; margin: 0 auto; padding: 0 30px;
}
.cf-card {
  display: flex; flex-direction: column; gap: 14px;
  background: var(--color-white); border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-lg); padding: 40px 36px;
  color: var(--color-navy); text-decoration: none;
  transition: transform var(--transition), border-color var(--transition), box-shadow var(--transition);
  min-height: 320px;
}
.cf-card:hover {
  transform: translateY(-4px); border-color: var(--color-green);
  box-shadow: 0 16px 40px rgba(66, 204, 147, 0.14); color: var(--color-navy);
}
.cf-card__tab {
  display: inline-block; align-self: flex-start;
  font-size: 0.75rem; font-weight: 700; letter-spacing: 0.22em;
  text-transform: uppercase; color: var(--color-green);
  padding: 6px 12px; border: 1px solid var(--color-green);
  border-radius: 4px; background: var(--color-mint);
}
.cf-card__headline {
  font-size: clamp(1.375rem, 2.2vw, 1.75rem); font-weight: 700;
  line-height: 1.2; letter-spacing: -0.01em; margin: 6px 0 0;
  color: var(--color-navy);
}
.cf-card__meta {
  font-size: 0.8rem; font-weight: 600; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--color-navy-light); margin: 0;
}
.cf-card__stat { margin-top: auto; padding-top: 18px; border-top: 1px solid var(--color-gray-light); }
.cf-card__stat-value {
  display: block; font-size: clamp(1.75rem, 3vw, 2.25rem); font-weight: 800;
  color: var(--color-green); line-height: 1; letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums; margin-bottom: 6px;
}
.cf-card__stat-label {
  font-size: 0.85rem; color: var(--color-navy-light); font-weight: 500;
}
.cf-card--soon {
  cursor: default; background: var(--color-gray-bg);
  border-style: dashed; border-color: #d3d8df;
  opacity: 0.85; justify-content: center; align-items: center; text-align: center;
}
.cf-card--soon:hover { transform: none; box-shadow: none; border-color: #d3d8df; }
.cf-card--soon .cf-card__tab {
  color: var(--color-navy-light); border-color: #d3d8df;
  background: var(--color-white);
}
.cf-card--soon .cf-card__headline {
  color: var(--color-navy-light); font-weight: 600;
  font-size: 1.125rem; letter-spacing: 0.02em;
}
.cf-card__escrow-sub {
  font-size: 0.85rem; color: var(--color-navy-light); margin: 8px 0 0;
}

.cf-index-hero { min-height: 55vh; padding: 120px 0 60px; }
.cf-index-hero h1 {
  font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 700;
  line-height: 1.05; letter-spacing: -0.02em;
  color: var(--color-navy); max-width: 20ch; margin: 0 auto 24px;
}
.cf-index-hero__sub {
  font-size: 1.125rem; line-height: 1.6; color: var(--color-navy-light);
  max-width: 640px; margin: 0 auto;
}

/* Closing CTA strip with inline funnel form. */
.cf-cta-strip { padding: 100px 0; background: var(--color-gray-bg); text-align: center; }
.cf-cta-strip h2 {
  font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 700;
  line-height: 1.2; letter-spacing: -0.01em; color: var(--color-navy);
  margin-bottom: 18px;
}
.cf-cta-strip__sub {
  font-size: 1.05rem; line-height: 1.6; color: var(--color-navy-light);
  max-width: 580px; margin: 0 auto 28px;
}
.cf-cta-form { max-width: 540px; margin: 0 auto; }
.cf-cta-pill {
  position: relative; display: flex; flex-direction: column;
  align-items: stretch; background: var(--color-white); border-radius: 30px;
  box-shadow: 0 1px 5px rgba(0,0,0,0.11); border: 1px solid var(--color-gray-light);
  overflow: hidden;
}
.cf-cta-pill input[name="location"] {
  flex: 1; height: 56px; padding: 0 24px; border: none;
  background: transparent; font-size: 16px; color: var(--color-navy);
  outline: none; font-family: var(--font);
}
.cf-cta-pill button[type="submit"] {
  height: 48px; margin: 4px; padding: 0 28px;
  background: var(--color-green); color: var(--color-white); border: none; cursor: pointer;
  border-radius: 9999px; font-size: 16px; font-weight: 700;
  letter-spacing: 0.3px; font-family: var(--font);
  text-transform: none;
}
.cf-cta-pill button[type="submit"]:hover { background: var(--color-green-hover); }
@media (min-width: 560px) {
  .cf-cta-pill { flex-direction: row; align-items: center; }
}

@media (max-width: 768px) {
  .cf-hero { min-height: 50vh; padding: 96px 0 60px; }
  .cf-hero__scroll { bottom: 24px; }
  .cf-section { padding: 64px 0; }
  .cf-narrow, .cf-wide { padding: 0 24px; }
  .cf-grid { grid-template-columns: 1fr; max-width: 360px; }
  .cf-houses { grid-template-columns: repeat(2, 1fr); max-width: 260px; gap: 14px; }
  .cf-compare { grid-template-columns: 1fr; gap: 16px; }
  .cf-compare__arrow { transform: rotate(90deg); }
  .cf-compare__arrow svg { width: 32px; height: 32px; }
  .cf-quote__body::before { top: -40px; left: 0; font-size: 5rem; }
  .cf-hero-stat { margin-bottom: 50px; }
  .cf-receipt { margin-top: 50px; padding: 26px 22px; }
  .cf-stats-strip__grid { grid-template-columns: repeat(2, 1fr); gap: 24px 20px; }
  .cf-index-grid { grid-template-columns: 1fr; gap: 22px; padding: 0 24px; }
  .cf-card { padding: 32px 26px; min-height: 260px; }
  .cf-cta-strip { padding: 64px 0; }
}
@media (max-width: 480px) {
  .cf-badges { gap: 8px; }
  .cf-badge { padding: 8px 14px; font-size: 0.8rem; }
}
"""


def _inline_tokens(css: str) -> str:
    for k, v in _TOKENS.items():
        css = css.replace(k, v)
    return css


CF_STYLE_BLOCK = "<style>\n" + _inline_tokens(_CF_CSS_RAW) + "\n</style>"


# Count-up IIFE. Inlined at the end of <main> on each case-file page.
# Animates any [data-count-target] from 0 to its target the first time it
# scrolls into view. Scroll-fade-in for .cf-reveal blocks was removed per
# feedback; sections render immediately.
COUNT_UP_AND_REVEAL_SCRIPT = """
<script>
(function () {
  if (typeof IntersectionObserver === "undefined") return;

  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

  function animateNumber(el) {
    var target = parseFloat(el.getAttribute("data-count-target"));
    if (isNaN(target)) return;
    var prefix = el.getAttribute("data-count-prefix") || "";
    var suffix = el.getAttribute("data-count-suffix") || "";
    var duration = 1400;
    var startTime = null;
    function step(t) {
      if (!startTime) startTime = t;
      var p = Math.min((t - startTime) / duration, 1);
      var current = Math.floor(target * easeOutCubic(p));
      el.textContent = prefix + current.toLocaleString() + suffix;
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = prefix + Math.round(target).toLocaleString() + suffix;
    }
    requestAnimationFrame(step);
  }

  var numEls = document.querySelectorAll("[data-count-target]");
  if (!numEls.length) return;
  var numIo = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        animateNumber(e.target);
        numIo.unobserve(e.target);
      }
    });
  }, { threshold: 0.4 });
  numEls.forEach(function (el) { numIo.observe(el); });
})();
</script>
"""


# Inline funnel-opening pill (Sell mode). Reusable across all three pages.
def cta_pill(placeholder: str = "Enter your address") -> str:
    return f"""
    <div role="tabpanel" aria-labelledby="tab-sell" class="cf-cta-form">
      <form class="pos_relative">
        <div class="cf-cta-pill">
          <input type="text" name="location" placeholder="{placeholder}"
                 autocomplete="off" aria-label="{placeholder}">
          <button type="submit">Compare Agents</button>
        </div>
        <input type="hidden" name="gclid" value="">
      </form>
    </div>"""
