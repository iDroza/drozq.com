// Fixture test for /functions/api/netsheet.js.
//
// Drives onRequest end to end with a mocked Rentcast and a mocked /api/lead, so
// the whole handler (parse, contact gate, derive, respond, save-once) is
// exercised with no network call and no real lead. The fixture is synthetic:
// no real parcel, owner, or address.
//
// Run:  node scripts/test_netsheet.mjs
//
// Rerun this after touching the county profiles, the city transfer tax table
// (Measure ULA and Measure GS thresholds index every July 1), or the
// special-assessment detection thresholds.
import { onRequest } from "../functions/api/netsheet.js";

const PROPERTY = {
  id: "1-Example-Way,-Irvine,-CA-92620",
  formattedAddress: "1 Example Way, Irvine, CA 92620",
  addressLine1: "1 Example Way", city: "Irvine", state: "CA", zipCode: "92620", county: "Orange",
  latitude: 33.7043, longitude: -117.7712,
  propertyType: "Single Family", bedrooms: 4, bathrooms: 3,
  squareFootage: 2450, lotSize: 4200, yearBuilt: 2006,
  assessorID: "530-421-17", subdivision: "Woodbury",
  lastSaleDate: "2014-06-27T00:00:00.000Z", lastSalePrice: 812000,
  hoa: { fee: 215 },
  features: { garageSpaces: 2, pool: false },
  ownerOccupied: true,
  owner: { names: ["SAMPLE, PAT A", "SAMPLE, ALEX B"], type: "Individual",
           mailingAddress: { formattedAddress: "1 Example Way, Irvine, CA 92620" } },
  taxAssessments: {
    "2023": { year: 2023, value: 957600, land: 500000, improvements: 457600 },
    "2024": { year: 2024, value: 976700, land: 510000, improvements: 466700 },
    "2025": { year: 2025, value: 996400, land: 520000, improvements: 476400 }
  },
  propertyTaxes: {
    "2022": { year: 2022, total: 15220 },
    "2023": { year: 2023, total: 15690 },
    "2024": { year: 2024, total: 16050 },
    "2025": { year: 2025, total: 16480 }
  },
  history: {
    "2014-06-27": { event: "Sale", date: "2014-06-27", price: 812000 },
    "2006-09-15": { event: "Sale", date: "2006-09-15", price: 689000 }
  }
};
const AVM = { price: 1438000, priceRangeLow: 1372000, priceRangeHigh: 1504000, subjectProperty: PROPERTY };

function makeEnv() { return { RENTCAST_API_KEY: "test-key" }; }

let leadPosts = [];
function installFetch({ propertyRows = [PROPERTY], avm = AVM } = {}) {
  globalThis.fetch = async (url, opts) => {
    const u = String(url);
    if (u.includes("/api/lead")) { leadPosts.push(opts && opts.body); return new Response("{}", { status: 200 }); }
    if (u.includes("/properties")) return new Response(JSON.stringify(propertyRows), { status: 200, headers: { "content-type": "application/json" } });
    if (u.includes("/avm/value"))  return new Response(JSON.stringify(avm),          { status: 200, headers: { "content-type": "application/json" } });
    throw new Error("unexpected fetch: " + u);
  };
}

function ctx(body, { method = "POST", url = "https://drozq.com/api/netsheet" } = {}) {
  const waits = [];
  return {
    request: new Request(url, method === "POST" ? {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body)
    } : { method }),
    env: makeEnv(),
    waitUntil: (p) => waits.push(p),
    _waits: waits
  };
}

const CONTACT = { email: "seller@example.com", phone: "(949) 555-0134", consent: "yes", name: "Pat Sample" };
let pass = 0, fail = 0;
function check(label, cond, extra) {
  if (cond) { pass++; console.log("  ok   " + label); }
  else { fail++; console.log("  FAIL " + label + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
}

console.log("\n== happy path: full Orange County record ==");
installFetch();
let c = ctx({ address: "1 Example Way, Irvine, CA 92620", ...CONTACT });
let res = await onRequest(c);
let d = await res.json();
await Promise.all(c._waits);

check("200 ok", res.status === 200 && d.ok === true, { status: res.status, err: d.error });
check("address parsed", d.address.city === "Irvine" && d.address.county === "Orange", d.address);
check("owner names returned", JSON.stringify(d.ownership.ownerNames) === JSON.stringify(["SAMPLE, PAT A", "SAMPLE, ALEX B"]), d.ownership.ownerNames);
check("mailing address NOT leaked", !JSON.stringify(d).toLowerCase().includes("mailingaddress"));
check("purchase price + date", d.ownership.lastSalePrice === 812000 && String(d.ownership.lastSaleDate).startsWith("2014-06-27"), d.ownership);
check("years held ~12", d.ownership.yearsHeld > 11.5 && d.ownership.yearsHeld < 12.5, d.ownership.yearsHeld);
check("gain since purchase = 626000", d.ownership.gainSincePurchase === 626000, d.ownership.gainSincePurchase);
check("annualized ~4.8%", Math.abs(d.ownership.annualizedPct - 4.8) < 0.3, d.ownership.annualizedPct);
check("prior sales listed newest first", d.ownership.priorSales.length === 2 && d.ownership.priorSales[0].price === 812000, d.ownership.priorSales);

check("4 tax bills, newest first", d.taxes.bills.length === 4 && d.taxes.bills[0].year === 2025, d.taxes.bills);
check("latest bill 16480", d.taxes.latestBill.total === 16480, d.taxes.latestBill);
check("YoY change +430 / +2.7%", d.taxes.billChange.dollars === 430 && Math.abs(d.taxes.billChange.pct - 2.7) < 0.05, d.taxes.billChange);
check("assessed 2025 = 996400", d.taxes.assessed.year === 2025 && d.taxes.assessed.value === 996400, d.taxes.assessed);
check("effective rate ~1.654%", Math.abs(d.taxes.effectiveRate - 0.01654) < 0.00002, d.taxes.effectiveRate);
check("OC ad valorem rate 1.05%", d.taxes.countyAdValoremRate === 0.0105, d.taxes.countyAdValoremRate);
check("ad valorem estimate = 10462", d.taxes.adValoremEstimate === 10462, d.taxes.adValoremEstimate);
check("Mello-Roos detected, high confidence", d.taxes.specialAssessment.detected === true && d.taxes.specialAssessment.confidence === "high", d.taxes.specialAssessment);
check("special assessment ~6018/yr", d.taxes.specialAssessment.annual === 6018, d.taxes.specialAssessment.annual);
check("buyer reassessed at the AVM", d.taxes.buyerNewBill.assessedAt === 1438000, d.taxes.buyerNewBill);
check("buyer bill = ad valorem + special", d.taxes.buyerNewBill.total === d.taxes.buyerNewBill.adValorem + d.taxes.buyerNewBill.special, d.taxes.buyerNewBill);

check("estimate returned", d.estimate.value === 1438000 && d.estimate.psf === 587, d.estimate);
check("no OC city transfer tax", d.costs.cityTransfer.kind === "none" && /Orange County/.test(d.costs.cityTransfer.note), d.costs.cityTransfer);
check("hoa monthly surfaced", d.property.hoaMonthly === 215, d.property.hoaMonthly);
check("response is private/no-store", (res.headers.get("cache-control") || "").includes("no-store"));
check("exactly one lead saved", leadPosts.length === 1, leadPosts.length);
check("lead intent = Seller Net Sheet", String(leadPosts[0]).includes("intent=Seller+Net+Sheet"), String(leadPosts[0]).slice(0, 200));
const leadForm = new URLSearchParams(String(leadPosts[0]));
check("lead carries the formatted address", leadForm.get("full_address") === "1 Example Way, Irvine, CA 92620", leadForm.get("full_address"));
check("lead carries the address components", leadForm.get("city") === "Irvine" && leadForm.get("state") === "CA" && leadForm.get("zip") === "92620");
check("lead consent recorded", leadForm.get("consent") === "yes");

console.log("\n== City of Los Angeles: base DTT + Measure ULA tiers ==");
leadPosts = [];
const laProp = { ...PROPERTY, city: "Los Angeles", county: "Los Angeles", formattedAddress: "1 Example Blvd, Los Angeles, CA 90012" };
installFetch({ propertyRows: [laProp], avm: { ...AVM, subjectProperty: laProp } });
c = ctx({ address: "1 Example Blvd, Los Angeles, CA 90012", ...CONTACT });
d = await (await onRequest(c)).json();
await Promise.all(c._waits);
const rule = d.costs.cityTransfer;
check("LA rule is stacked", rule.kind === "stacked", rule.kind);
check("LA base is $4.50 per $1,000", rule.base === 0.0045, rule.base);
check("ULA tiers at 10.9M then 5.4M", rule.tiers[0].min === 10900000 && rule.tiers[1].min === 5400000, rule.tiers.map(t => t.min));
check("ULA rates 5.5% / 4%", rule.tiers[0].rate === 0.055 && rule.tiers[1].rate === 0.04, rule.tiers.map(t => t.rate));
check("LA county ad valorem 1.20%", d.taxes.countyAdValoremRate === 0.0120, d.taxes.countyAdValoremRate);

// mirror the client's cityTransferTax() against the rule the API ships
function cityTax(r, price) {
  if (r.kind === "flat") return price * r.rate;
  if (r.kind === "tiered") { for (const t of r.tiers) if (price >= t.min) return price * t.rate; return 0; }
  if (r.kind === "stacked") { let x = price * r.base; for (const t of r.tiers) if (price >= t.min) { x += price * t.rate; break; } return x; }
  return 0;
}
check("$1.2M in LA = $5,400 (base only)", cityTax(rule, 1200000) === 5400, cityTax(rule, 1200000));
check("$5.5M in LA = $24,750 + $220,000 ULA", Math.round(cityTax(rule, 5500000)) === 244750, cityTax(rule, 5500000));
check("$11M in LA = $49,500 + $605,000 ULA", Math.round(cityTax(rule, 11000000)) === 654500, cityTax(rule, 11000000));
check("$5.39M stays under ULA", Math.round(cityTax(rule, 5390000)) === 24255, cityTax(rule, 5390000));

console.log("\n== pre-1983 home, ad valorem only: explicit all-clear ==");
const oldProp = {
  ...PROPERTY, yearBuilt: 1968, city: "Tustin",
  taxAssessments: { "2025": { year: 2025, value: 400000, land: 250000, improvements: 150000 } },
  propertyTaxes: { "2025": { year: 2025, total: 4230 } }
};
installFetch({ propertyRows: [oldProp], avm: { ...AVM, price: 1100000, subjectProperty: oldProp } });
c = ctx({ address: "1 Example Ct, Tustin, CA 92780", ...CONTACT });
d = await (await onRequest(c)).json();
await Promise.all(c._waits);
check("no special assessment", d.taxes.specialAssessment.detected === false, d.taxes.specialAssessment);
check("all-clear cites the 1982 Act", /1982 Mello-Roos Act/.test(d.taxes.specialAssessment.note), d.taxes.specialAssessment.note);
check("confidence high on a pre-1983 home", d.taxes.specialAssessment.confidence === "high", d.taxes.specialAssessment.confidence);

console.log("\n== gate: no record found still saves the lead ==");
leadPosts = [];
installFetch({ propertyRows: [], avm: { subjectProperty: null } });
c = ctx({ address: "1 Nonexistent Rd, Irvine, CA", ...CONTACT });
let r2 = await onRequest(c); let d2 = await r2.json();
await Promise.all(c._waits);
check("200 with ok:false no_data", r2.status === 200 && d2.ok === false && d2.error === "no_data", d2);
check("lead still saved", leadPosts.length === 1, leadPosts.length);

console.log("\n== gate: upstream on fire still saves the lead ==");
leadPosts = [];
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  if (u.includes("/api/lead")) { leadPosts.push(opts && opts.body); return new Response("{}", { status: 200 }); }
  throw new Error("upstream down");
};
c = ctx({ address: "1 Example Way, Irvine, CA 92620", ...CONTACT });
let r3 = await onRequest(c); let d3 = await r3.json();
await Promise.all(c._waits);
check("no_data or 502, never a 500 crash", r3.status === 200 || r3.status === 502, { status: r3.status, err: d3.error });
check("lead saved anyway", leadPosts.length === 1, leadPosts.length);

console.log("\n== gate rejections spend nothing ==");
let rentcastCalls = 0;
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  if (u.includes("rentcast")) rentcastCalls++;
  if (u.includes("/api/lead")) { leadPosts.push(opts && opts.body); return new Response("{}", { status: 200 }); }
  return new Response("[]", { status: 200 });
};
leadPosts = []; rentcastCalls = 0;
for (const [label, body] of [
  ["missing consent", { address: "x", email: "a@b.co", phone: "9495550000" }],
  ["missing phone",   { address: "x", email: "a@b.co", consent: "yes" }],
  ["honeypot filled", { address: "x", email: "a@b.co", phone: "9495550000", consent: "yes", company_website: "bot" }]
]) {
  const cc = ctx(body);
  const rr = await onRequest(cc);
  const dd = await rr.json();
  await Promise.all(cc._waits);
  check(label + " -> 403 contact_required", rr.status === 403 && dd.error === "contact_required", { status: rr.status, dd });
}
const cg = ctx(null, { method: "GET", url: "https://drozq.com/api/netsheet?address=1+Example+Way" });
const rg = await onRequest(cg);
check("bare GET -> 403", rg.status === 403, rg.status);
check("no Rentcast spend on any rejection", rentcastCalls === 0, rentcastCalls);
check("no lead saved on any rejection", leadPosts.length === 0, leadPosts.length);

console.log(`\n${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
