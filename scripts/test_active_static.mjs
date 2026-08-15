import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Script } from "node:vm";

const html = readFileSync(new URL("../active/index.html", import.meta.url), "utf8");
const css = readFileSync(new URL("../active/active.css", import.meta.url), "utf8");
const sharedCss = readFileSync(
  new URL("../dashboard/dashboard.css", import.meta.url),
  "utf8",
);
const javascript = readFileSync(
  new URL("../active/active.js", import.meta.url),
  "utf8",
);
const redirects = readFileSync(new URL("../_redirects", import.meta.url), "utf8");

const expectedMetrics = [
  "googleAdsSpendMtd",
  "googleAdsLeadsMtd",
  "googleAdsCostPerClickMtd",
  "googleAdsCostPerLeadMtd",
  "activeRealtyClicksRolling90d",
  "activeRealtyImpressionsRolling90d",
  "activeRealtyCtrRolling90d",
  "activeRealtyPositionRolling90d",
  "jtClicksRolling90d",
  "jtImpressionsRolling90d",
  "jtCtrRolling90d",
  "jtPositionRolling90d",
  "googleAdsSpendYtd",
  "googleAdsLeadsYtd",
  "googleAdsCostPerLeadYtd",
  "teamCommissionRoasYtd",
  "teamCommissionYtd",
  "teamSalesYtd",
  "teamVolumeYtd",
  "teamActiveAgentsYtd",
  "shellPagesRemaining",
  "setsRemaining",
];
const personalMetrics = [
  "callsToday",
  "textsToday",
  "emailsToday",
  "appointmentsSetMtd",
  "freshBuyerLeads",
  "freshSellerLeads",
];
const metricMatches = [
  ...html.matchAll(/<article class="[^"]*\bmetric-card\b[^"]*" data-metric="([^"]+)">/gu),
];

assert.deepEqual(
  metricMatches.map((match) => match[1]),
  expectedMetrics,
  "Active Realty metric cards must preserve the company dashboard row order",
);
assert.equal(metricMatches.length, 22, "company dashboard must contain exactly 22 cards");
assert.deepEqual(
  metricMatches.slice(0, 4).map((match) => match[1]),
  expectedMetrics.slice(0, 4),
  "the first row must be MTD spend, leads, CPC, and CPL",
);
assert.match(html, /<h2>GOOGLE ADS CPC<\/h2>/u);
assert.match(html, /<h2>GOOGLE ADS CPL<\/h2>/u);
assert.equal((html.match(/<h1\b/gu) ?? []).length, 1, "company dashboard must have one h1");
assert.match(html, /<h1 id="active-title">Operating Dashboard<\/h1>/u);
assert.match(html, /ACTIVE REALTY/u);
assert.doesNotMatch(
  html,
  /Operating Dashboard \| Drozq|brand-header-logo|alt="Drozq\.com"/iu,
  "personal branding must be absent",
);
assert.match(html, /<meta name="robots" content="noindex,nofollow,noarchive">/u);
assert.match(html, /<link rel="canonical" href="https:\/\/drozq\.com\/active">/u);
assert.match(html, /aria-live="polite"/u);
assert.match(html, /<noscript>/u);

for (const personalMetric of personalMetrics) {
  assert.doesNotMatch(
    `${html}\n${javascript}`,
    new RegExp(personalMetric, "u"),
    `${personalMetric} must not enter the company-facing browser bundle`,
  );
}
assert.doesNotMatch(
  `${html}\n${javascript}`,
  /FRESH (?:SELLER|BUYER) LEADS|CALLS MADE|APPOINTMENTS SET|TEXTS SENT|EMAILS SENT/iu,
  "personal card labels must be absent",
);

const sectionTitles = [
  ...html.matchAll(/<h2 id="active-[^"]+">([^<]+)<\/h2>/gu),
].map((match) => match[1]);
assert.deepEqual(sectionTitles, [
  "Organic Search",
  "Aggregate Advertising",
  "Team Performance",
  "Production Queue",
]);
assert.match(
  html,
  /class="dashboard-section dashboard-section--production"[\s\S]*class="metrics-grid metrics-grid--two metrics-grid--production is-loading"/u,
  "production queue must be the enlarged final section",
);
assert.match(
  html,
  /data-metric="teamActiveAgentsYtd"[\s\S]*data-metric="shellPagesRemaining"[\s\S]*data-metric="setsRemaining"[\s\S]*<\/div>\s*<\/section>\s*<\/div>\s*<noscript>/u,
  "shell production must be the last visible dashboard content",
);

assert.match(javascript, /"\/api\/dashboard\/active-summary"/u);
assert.match(javascript, /"\/api\/dashboard\/active-bootstrap\.js"/u);
assert.match(javascript, /__ACTIVE_REALTY_DASHBOARD_SNAPSHOT__/u);
assert.match(javascript, /Object\.keys\(value\.metrics\)\.length === metricKeys\.length/u);
assert.match(javascript, /15000/u, "visible polling interval must be 15 seconds");
assert.match(
  javascript,
  /ACTIVE_REALTY_STALE_AFTER_MS = 12 \* 60 \* 60 \* 1000/u,
  "repository progress must use the 12-hour freshness policy",
);
assert.doesNotMatch(
  `${html}\n${javascript}`,
  /Google Sheets/iu,
  "the live production source must no longer be labeled Google Sheets",
);
assert.match(javascript, /document\.visibilityState/u, "hidden pages must pause polling");
assert.doesNotMatch(
  javascript,
  /api\.followupboss\.com|googleads\.googleapis\.com|sheets\.googleapis\.com|oauth2\.googleapis\.com|webmasters\/v3/iu,
  "company browser code must never call upstream data APIs",
);
assert.match(sharedCss, /@media \(min-width: 1180px\)[\s\S]*repeat\(4,/u);
assert.match(sharedCss, /@media \(prefers-reduced-motion: reduce\)/u);
assert.match(css, /\.metric-card--production/u);
assert.match(redirects, /^\/Active \/active 301$/mu);
assert.match(redirects, /^\/Active\/ \/active 301$/mu);
assert.match(redirects, /^\/active\/ \/active 301$/mu);
assert.match(redirects, /^\/active \/active\/ 200$/mu);
assert.doesNotMatch(
  `${html}\n${css}\n${javascript}\n${redirects}`,
  /\u2014/u,
  "company dashboard source must not contain a literal em dash",
);

new Script(javascript, { filename: "active/active.js" });

console.log("Active Realty dashboard static contract: passed");
