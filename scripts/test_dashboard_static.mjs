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
  "callsToday",
  "textsToday",
  "emailsToday",
  "appointmentsSetMtd",
  "freshBuyerLeads",
  "freshSellerLeads",
  "googleAdsSpendMtd",
  "googleAdsLeadsMtd",
];
const metricMatches = [...html.matchAll(/<article class="metric-card" data-metric="([^"]+)">/gu)];
assert.deepEqual(
  metricMatches.map((match) => match[1]),
  expectedMetrics,
  "dashboard must contain exactly the eight approved metric cards",
);
assert.equal((html.match(/<h1\b/gu) ?? []).length, 1, "dashboard must have one h1");
assert.match(
  html,
  /<link rel="canonical" href="https:\/\/drozq\.com\/dashboard">/u,
  "dashboard canonical URL must be stable",
);
assert.match(html, /aria-live="polite"/u, "metrics need an aria-live region");
assert.match(html, /<noscript>/u, "dashboard needs a noscript message");
assert.match(javascript, /"\/api\/dashboard\/summary"/u);
assert.doesNotMatch(
  javascript,
  /api\.followupboss\.com|googleads\.googleapis\.com|sheets\.googleapis\.com|oauth2\.googleapis\.com/iu,
  "browser code must not call dashboard upstream data APIs",
);
assert.match(javascript, /15000/u, "visible polling interval must be 15 seconds");
assert.match(javascript, /document\.visibilityState/u, "hidden pages must pause polling");
assert.match(javascript, /metric-value--very-long/u, "long values need overflow-safe sizing");
assert.match(css, /@media \(min-width: 1180px\)[\s\S]*repeat\(4,/u);
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
