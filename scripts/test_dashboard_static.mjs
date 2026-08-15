import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Script } from "node:vm";

const html = readFileSync(new URL("../dashboard/index.html", import.meta.url), "utf8");
const css = readFileSync(new URL("../dashboard/dashboard.css", import.meta.url), "utf8");
const javascript = readFileSync(
  new URL("../dashboard/dashboard.js", import.meta.url),
  "utf8",
);
const redirects = readFileSync(new URL("../_redirects", import.meta.url), "utf8");

const expectedMetrics = [
  "googleAdsSpendMtd",
  "googleAdsLeadsMtd",
  "googleAdsCostPerClickMtd",
  "googleAdsCostPerLeadMtd",
  "callsToday",
  "appointmentsSetMtd",
  "totalDialsYtd",
  "personalDealsClosedYtd",
  "freshSellerLeads",
  "freshBuyerLeads",
  "textsToday",
  "emailsToday",
  "googleAdsSpendYtd",
  "googleAdsLeadsYtd",
  "googleAdsCostPerLeadYtd",
  "teamCommissionRoasYtd",
  "activeRealtyClicksRolling90d",
  "activeRealtyImpressionsRolling90d",
  "activeRealtyCtrRolling90d",
  "activeRealtyPositionRolling90d",
  "jtClicksRolling90d",
  "jtImpressionsRolling90d",
  "jtCtrRolling90d",
  "jtPositionRolling90d",
  "teamCommissionYtd",
  "teamSalesYtd",
  "teamVolumeYtd",
  "teamActiveAgentsYtd",
  "shellPagesRemaining",
  "setsRemaining",
];
const metricMatches = [...html.matchAll(/<article class="[^"]*\bmetric-card\b[^"]*" data-metric="([^"]+)">/gu)];
assert.deepEqual(
  metricMatches.map((match) => match[1]),
  expectedMetrics,
  "dashboard metric cards must preserve the required row order",
);
assert.equal(metricMatches.length, 30, "dashboard must contain exactly 30 metric cards");
assert.deepEqual(
  metricMatches.slice(0, 4).map((match) => match[1]),
  [
    "googleAdsSpendMtd",
    "googleAdsLeadsMtd",
    "googleAdsCostPerClickMtd",
    "googleAdsCostPerLeadMtd",
  ],
  "the top row must be Google Ads spend, leads, CPC, and CPL",
);
assert.deepEqual(
  metricMatches.slice(4, 8).map((match) => match[1]),
  ["callsToday", "appointmentsSetMtd", "totalDialsYtd", "personalDealsClosedYtd"],
  "the second row must be calls, appointments, YTD dials, and Joshua's YTD closed deals",
);
assert.deepEqual(
  metricMatches.slice(8, 12).map((match) => match[1]),
  ["freshSellerLeads", "freshBuyerLeads", "textsToday", "emailsToday"],
  "the third black row must be seller leads, buyer leads, texts, and emails",
);
assert.equal(
  (html.match(/class="metrics-grid metrics-grid--compact is-loading"/gu) ?? []).length,
  4,
  "each lower dashboard row must be capped at four cards",
);
assert.equal((html.match(/<h1\b/gu) ?? []).length, 1, "dashboard must have one h1");
assert.match(html, /<h2>CALLS MADE<\/h2>/u, "calls card must say CALLS MADE");
assert.match(html, /<h2>GOOGLE ADS SPEND<\/h2>/u);
assert.match(html, /<h2>GOOGLE ADS LEADS<\/h2>/u);
assert.match(html, /<h2>GOOGLE ADS CPC<\/h2>/u);
assert.match(html, /<h2>GOOGLE ADS CPL<\/h2>/u);
assert.match(html, /<h2>TOTAL DIALS MADE THIS YEAR<\/h2>/u);
assert.match(html, /<h2>DEALS CLOSED THIS YEAR<\/h2>/u);
assert.match(html, /Year to date &middot; Correlated to deals/u);
assert.match(html, /Year to date &middot; Joshua only/u);
assert.match(html, /<h2>TEXTS SENT<\/h2>/u, "texts card must keep TEXTS SENT");
assert.match(html, /<h2>EMAILS SENT<\/h2>/u, "emails card must keep EMAILS SENT");
assert.match(html, /<h2 id="advertising-title">Aggregate Advertising<\/h2>/u);
assert.match(html, /<h3>BLENDED ROAS<\/h3>/u);
assert.match(html, /<h3>GROSS COMMISSION<\/h3>/u);
assert.match(html, /<h3 class="metric-row__title">ACTIVEREALTY\.COM<\/h3>/u);
assert.match(html, /<h3 class="metric-row__title">JUSTINTYE\.COM<\/h3>/u);
assert.match(html, /<h2 id="team-performance-title">Team Performance<\/h2>/u);
assert.match(html, /<h2 id="production-queue-title">Production Queue<\/h2>/u);
assert.match(html, /<h3>SHELL PAGES REMAINING<\/h3>/u);
assert.match(html, /<h3>SETS REMAINING<\/h3>/u);
assert.match(
  html,
  /data-metric="teamActiveAgentsYtd"[\s\S]*data-metric="shellPagesRemaining"[\s\S]*data-metric="setsRemaining"/u,
  "Google Sheets metrics must remain the final dashboard row",
);
assert.equal(
  (html.match(/class="metrics-grid metrics-grid--compact metrics-grid--two is-loading"/gu) ?? []).length,
  1,
  "the final Google Sheets row must contain the two requested cards",
);
assert.match(
  html,
  /<link rel="canonical" href="https:\/\/drozq\.com\/dashboard">/u,
  "dashboard canonical URL must be stable",
);
assert.match(html, /aria-live="polite"/u, "metrics need an aria-live region");
assert.match(html, /<noscript>/u, "dashboard needs a noscript message");
assert.match(javascript, /"\/api\/dashboard\/summary"/u);
assert.match(javascript, /"\/api\/dashboard\/bootstrap\.js"/u);
assert.match(javascript, /loadBootstrapSnapshot/u);
assert.match(
  html,
  /<script src="\/api\/dashboard\/bootstrap\.js" defer><\/script>[\s\S]*<script src="\/dashboard\/dashboard\.js\?v=20260815a" defer><\/script>/u,
  "the resilient snapshot bootstrap must load before the dashboard controller",
);
assert.doesNotMatch(
  javascript,
  /api\.followupboss\.com|googleads\.googleapis\.com|sheets\.googleapis\.com|oauth2\.googleapis\.com|webmasters\/v3/iu,
  "browser code must not call dashboard upstream data APIs",
);
assert.match(javascript, /15000/u, "visible polling interval must be 15 seconds");
assert.match(javascript, /document\.visibilityState/u, "hidden pages must pause polling");
assert.match(html, /id="search-console-period">Last 3 months<\/p>/u);
assert.doesNotMatch(html, /Rolling 90 days/iu);
assert.match(javascript, /snapshot\.rolling90DayPeriod\.startDate/u);
assert.match(javascript, /metric-value--very-long/u, "long values need overflow-safe sizing");
assert.match(css, /@media \(min-width: 1180px\)[\s\S]*repeat\(4,/u);
const googleAdsCardRule = css.match(
  /\.metrics-grid--top \.metric-card\s*\{([^}]*)\}/u,
)?.[1] ?? "";
assert.match(googleAdsCardRule, /background:\s*#dff6e8/u);
assert.match(googleAdsCardRule, /border-top-color:\s*#42cc93/u);
assert.doesNotMatch(googleAdsCardRule, /#d92228|#a92e2a/u);
assert.match(
  css,
  /@media \(min-width: 1180px\)[\s\S]*\.dashboard-splash\s*\{[\s\S]*min-height: calc\(100vh - 136px\)/u,
  "desktop splash must hold the third black row below the fold",
);
assert.match(
  html,
  /<div class="dashboard-splash">[\s\S]*metrics-grid--focus[\s\S]*<\/div>\s*<div class="metrics-grid metrics-grid--continuation is-loading"/u,
  "daily activity must sit outside the desktop splash",
);
assert.match(css, /@media \(prefers-reduced-motion: reduce\)/u);
assert.match(redirects, /^\/Dashboard \/dashboard 301$/mu);
assert.match(redirects, /^\/Dashboard\/ \/dashboard 301$/mu);
assert.match(redirects, /^\/dashboard\/ \/dashboard 301$/mu);
assert.match(redirects, /^\/dashboard \/dashboard\/ 200$/mu);
assert.doesNotMatch(
  `${html}\n${css}\n${javascript}\n${redirects}`,
  /\u2014/u,
  "repository source must not contain a literal em dash",
);

new Script(javascript, { filename: "dashboard/dashboard.js" });

console.log("Dashboard static contract: passed");
