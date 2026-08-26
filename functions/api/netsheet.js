import { validEmail } from "../_lib/email.js";
import { maskEmail, maskAddress } from "../_lib/redact.js";
import { enforceRateLimits, RATE_RULES } from "../_lib/ratelimit.js";

// /api/netsheet - the property + tax intelligence behind /net-sheet/.
//
// A title company's net sheet starts with a blank "sale price" box. This one
// starts with the county's own record of the home: who owns it, what they paid
// and when, the last several years of actual property tax bills, the assessed
// value behind them, and whether the bill carries a Mello-Roos / special
// assessment on top of the ad valorem rate. Those four facts are what make a
// net sheet real instead of a guess:
//
//   1) purchase price + date  -> capital gains basis AND the loan back-solve
//   2) annual tax bill        -> the escrow proration line, to the dollar
//   3) assessed value         -> the Mello-Roos delta, and the buyer's new bill
//   4) AVM                    -> a defensible default sale price to start from
//
// The math (net sheet, payoff amortization, proration, capital gains) all runs
// client-side in /net-sheet/ so the calculator works with or without a lookup.
// This endpoint supplies DATA, not a net sheet.
//
// Contact gate: same posture as /api/valuation. The record is delivered only to
// a POST carrying email + phone + consent="yes"; a bare GET returns 403 and
// computes nothing. Every contact-bearing request saves the lead server-side.
//
// Env var required:
//   RENTCAST_API_KEY  - get one at https://app.rentcast.io/app/api

const RENTCAST_BASE = "https://api.rentcast.io/v1";

// Rentcast subrequests are edge-cached per upstream URL for 7 days. Assessor
// rolls and deed records move once a year; the response itself is per-lead and
// never publicly cacheable.
const CACHE_TTL_SECONDS = 60 * 60 * 24 * 7;

const json = (body, status = 200, extra = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=UTF-8",
      "cache-control": "private, no-store",
      ...extra
    }
  });

function numberOrNull(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function norm(s) {
  return String(s || "").trim().toLowerCase();
}

// ---------------------------------------------------------------------------
// County closing customs + typical ad valorem rates.
//
// Ad valorem rate = Prop 13's 1% base plus voter-approved bond debt for the
// tax rate area. It varies parcel to parcel; these are the county-typical
// values used ONLY as the baseline for detecting a special assessment on top
// (see deriveTaxPicture). The seller's actual bill is authoritative and we
// always show it.
//
// Escrow / title customs are Southern California standard: escrow split 50/50,
// seller pays the owner's title policy, seller pays the county documentary
// transfer tax.
const COUNTY_PROFILES = {
  "orange":          { label: "Orange County",         adValorem: 0.0105, escrowSplit: 0.5, sellerPaysOwnersTitle: true },
  "los angeles":     { label: "Los Angeles County",    adValorem: 0.0120, escrowSplit: 0.5, sellerPaysOwnersTitle: true },
  "san diego":       { label: "San Diego County",      adValorem: 0.0110, escrowSplit: 0.5, sellerPaysOwnersTitle: true },
  "riverside":       { label: "Riverside County",      adValorem: 0.0125, escrowSplit: 0.5, sellerPaysOwnersTitle: true },
  "san bernardino":  { label: "San Bernardino County", adValorem: 0.0120, escrowSplit: 0.5, sellerPaysOwnersTitle: true },
  "ventura":         { label: "Ventura County",        adValorem: 0.0115, escrowSplit: 0.5, sellerPaysOwnersTitle: true },
  "santa barbara":   { label: "Santa Barbara County",  adValorem: 0.0110, escrowSplit: 0.5, sellerPaysOwnersTitle: true },
  "kern":            { label: "Kern County",           adValorem: 0.0115, escrowSplit: 0.5, sellerPaysOwnersTitle: true }
};

const COUNTY_DEFAULT = { label: "California", adValorem: 0.0115, escrowSplit: 0.5, sellerPaysOwnersTitle: true };

function countyProfile(county) {
  const key = norm(county).replace(/\s+county$/, "");
  return COUNTY_PROFILES[key] || COUNTY_DEFAULT;
}

// ---------------------------------------------------------------------------
// City documentary transfer tax.
//
// Every California county charges $1.10 per $1,000 ($0.55 per $500). A handful
// of cities stack their own on top. In Los Angeles County the Registrar-
// Recorder lists exactly five: Culver City, Los Angeles, Pomona, Redondo Beach
// and Santa Monica. No Orange County city levies one.
//
// Rules are returned as data so the page can render the label and the client
// can recompute live as the sale price changes.
//   kind "none"    -> no city tax
//   kind "flat"    -> rate applies to the full price
//   kind "tiered"  -> the FIRST bracket whose min the price meets applies to
//                     the full price (gross-receipts style, not marginal)
//   kind "stacked" -> base rate on the full price, plus a bracket rate on the
//                     full price when the price clears a threshold (LA + ULA)
const CITY_TRANSFER_TAX = {
  "los angeles": {
    kind: "stacked",
    label: "City of Los Angeles",
    base: 0.0045,                       // $4.50 per $1,000 ($2.25 per $500)
    baseNote: "$4.50 per $1,000 city documentary transfer tax",
    tiers: [
      { min: 10900000, rate: 0.055, note: "Measure ULA, 5.5% of the full price at $10.9M and above" },
      { min: 5400000,  rate: 0.04,  note: "Measure ULA, 4% of the full price from $5.4M to $10.9M" }
    ],
    tierNote: "Measure ULA thresholds index every July 1; these are the values effective July 1, 2026."
  },
  "culver city": {
    kind: "tiered",
    label: "Culver City",
    tiers: [
      { min: 10000000, rate: 0.04,   note: "4% at $10M and above" },
      { min: 3000000,  rate: 0.03,   note: "3% from $3M to $10M" },
      { min: 1500000,  rate: 0.015,  note: "1.5% from $1.5M to $3M" },
      { min: 0,        rate: 0.0045, note: "0.45% below $1.5M" }
    ]
  },
  "santa monica": {
    kind: "tiered",
    label: "Santa Monica",
    tiers: [
      { min: 8000000, rate: 0.056,  note: "Measure GS, 5.6% of the full price at $8M and above" },
      { min: 5000000, rate: 0.006,  note: "$6.00 per $1,000 from $5M to $8M" },
      { min: 0,       rate: 0.003,  note: "$3.00 per $1,000 below $5M" }
    ]
  },
  "pomona":        { kind: "flat", label: "Pomona",        rate: 0.0022, baseNote: "$2.20 per $1,000" },
  "redondo beach": { kind: "flat", label: "Redondo Beach", rate: 0.0022, baseNote: "$2.20 per $1,000" }
};

function cityTransferRule(city, county) {
  const rule = CITY_TRANSFER_TAX[norm(city)];
  if (rule) return rule;
  const prof = norm(county).replace(/\s+county$/, "");
  const noneNote = prof === "orange"
    ? "No Orange County city levies a city transfer tax. The county's $1.10 per $1,000 is the whole documentary transfer tax."
    : "No city documentary transfer tax on record for this city. The county's $1.10 per $1,000 applies.";
  return { kind: "none", label: city || "", note: noneNote };
}

// ---------------------------------------------------------------------------
// Ownership: who is on title, what they paid, and how long they have held it.
// Rentcast's property record carries the deed-recorded last sale plus a
// keyed `history` map of prior events.
//
// The owner's MAILING address is deliberately not returned. Owner names and the
// recorded sale are county public record and are the point of the lookup; a
// separate residence address for an absentee owner is not, so only the derived
// occupancy flag ships.
function deriveOwnership(property, estimateValue, nowMs) {
  if (!property) return null;
  const lastSalePrice = numberOrNull(property.lastSalePrice);
  const lastSaleDate  = property.lastSaleDate || null;

  let yearsHeld = null, monthsHeld = null;
  if (lastSaleDate) {
    const t = Date.parse(lastSaleDate);
    if (Number.isFinite(t)) {
      const days = (nowMs - t) / 86400000;
      if (days >= 0) {
        yearsHeld  = Math.round((days / 365.25) * 10) / 10;
        monthsHeld = Math.round(days / 30.44);
      }
    }
  }

  let gain = null, gainPct = null, annualizedPct = null;
  if (lastSalePrice > 0 && estimateValue > 0) {
    gain = Math.round(estimateValue - lastSalePrice);
    gainPct = Math.round((gain / lastSalePrice) * 1000) / 10;
    if (yearsHeld && yearsHeld >= 0.5) {
      annualizedPct = Math.round(((Math.pow(estimateValue / lastSalePrice, 1 / yearsHeld) - 1) * 100) * 10) / 10;
    }
  }

  const priorSales = [];
  const hist = property.history;
  if (hist && typeof hist === "object") {
    for (const key of Object.keys(hist)) {
      const h = hist[key] || {};
      const price = numberOrNull(h.price);
      const date  = h.date || key;
      if (!price || !date) continue;
      priorSales.push({ date, price, event: h.event || "Sale" });
    }
    priorSales.sort((a, b) => String(b.date).localeCompare(String(a.date)));
  }

  const names = Array.isArray(property.owner?.names)
    ? property.owner.names.filter(Boolean).map(n => String(n).trim()).slice(0, 4)
    : [];

  return {
    ownerNames: names,
    ownerType: property.owner?.type || null,
    ownerOccupied: property.ownerOccupied === true ? true : (property.ownerOccupied === false ? false : null),
    lastSaleDate,
    lastSalePrice,
    yearsHeld,
    monthsHeld,
    gainSincePurchase: gain,
    gainPct,
    annualizedPct,
    priorSales: priorSales.slice(0, 6),
    source: "County recorder deed records"
  };
}

// ---------------------------------------------------------------------------
// The tax picture. This is the part no online net sheet has.
//
// From the assessed value and the actual billed total we back out the special
// assessment (Mello-Roos CFD, 1915 Act bond, landscape/lighting district) that
// rides on top of the ad valorem rate:
//
//   adValoremEstimate = assessedValue x county-typical rate
//   excess            = billedTotal - adValoremEstimate
//
// An excess above roughly a quarter point of assessed value is not explainable
// by tax-rate-area bond variance; it is a special tax line. Mello-Roos only
// exists for districts formed under the 1982 Act, so a pre-1983 home with no
// excess gets an explicit all-clear instead of a shrug.
function deriveTaxPicture(property, profile, saleEstimate) {
  const assessments = property?.taxAssessments;
  const taxes = property?.propertyTaxes;

  let assessed = null;
  if (assessments && typeof assessments === "object") {
    const years = Object.keys(assessments).map(y => parseInt(y, 10)).filter(Number.isFinite).sort((a, b) => b - a);
    for (const y of years) {
      const row = assessments[y] || assessments[String(y)] || {};
      const v = numberOrNull(row.value);
      if (v) {
        assessed = {
          year: y,
          value: v,
          land: numberOrNull(row.land),
          improvements: numberOrNull(row.improvements)
        };
        break;
      }
    }
  }

  const bills = [];
  if (taxes && typeof taxes === "object") {
    const years = Object.keys(taxes).map(y => parseInt(y, 10)).filter(Number.isFinite).sort((a, b) => b - a);
    for (const y of years) {
      const row = taxes[y] || taxes[String(y)] || {};
      const total = numberOrNull(row.total);
      if (total) bills.push({ year: y, total: Math.round(total) });
    }
  }
  const latestBill = bills[0] || null;

  // Year-over-year change on the most recent two bills.
  let billChange = null;
  if (bills.length >= 2 && bills[1].total > 0) {
    billChange = {
      dollars: bills[0].total - bills[1].total,
      pct: Math.round(((bills[0].total - bills[1].total) / bills[1].total) * 1000) / 10,
      fromYear: bills[1].year,
      toYear: bills[0].year
    };
  }

  let effectiveRate = null, adValoremEstimate = null, special = null;
  if (latestBill && assessed?.value > 0) {
    effectiveRate = latestBill.total / assessed.value;
    adValoremEstimate = Math.round(assessed.value * profile.adValorem);
    const excess = latestBill.total - adValoremEstimate;
    const materialFloor = Math.max(600, assessed.value * 0.0025);
    const strongFloor = assessed.value * 0.0045;
    const yearBuilt = numberOrNull(property?.yearBuilt);

    if (excess >= strongFloor) {
      special = {
        detected: true, confidence: "high", annual: Math.round(excess),
        note: "The billed total sits well above the ad valorem rate for this county. That gap is a special tax line: a Mello-Roos CFD, a 1915 Act improvement bond, or a lighting and landscape district."
      };
    } else if (excess >= materialFloor) {
      special = {
        detected: true, confidence: "likely", annual: Math.round(excess),
        note: "The billed total runs above the ad valorem rate by more than tax-rate-area bond variance explains. Expect a special assessment line on the bill."
      };
    } else if (yearBuilt && yearBuilt < 1983) {
      special = {
        detected: false, confidence: "high", annual: 0,
        note: "The bill tracks the ad valorem rate, and the home predates the 1982 Mello-Roos Act, so no CFD was ever formed around it."
      };
    } else {
      special = {
        detected: false, confidence: "likely", annual: 0,
        note: "The bill tracks the ad valorem rate for this county, so there is no meaningful special assessment riding on it."
      };
    }
  }

  // What the buyer's bill becomes. California reassesses to the purchase price
  // at close (Prop 13's change-in-ownership event), so the buyer inherits the
  // same special assessment on a new, higher ad valorem base. Sellers get asked
  // this on every showing and almost never have the number.
  let buyerNewBill = null;
  if (saleEstimate > 0) {
    const adValorem = Math.round(saleEstimate * profile.adValorem);
    const specialAnnual = special?.annual || 0;
    buyerNewBill = {
      assessedAt: Math.round(saleEstimate),
      adValorem,
      special: specialAnnual,
      total: adValorem + specialAnnual,
      note: "California reassesses to the purchase price on a change in ownership, so the buyer's first full-year bill is built on the sale price, not on your Prop 13 base."
    };
  }

  return {
    assessed,
    bills: bills.slice(0, 6),
    latestBill,
    billChange,
    effectiveRate: effectiveRate != null ? Math.round(effectiveRate * 100000) / 100000 : null,
    countyAdValoremRate: profile.adValorem,
    adValoremEstimate,
    specialAssessment: special,
    buyerNewBill,
    source: "County assessor and tax collector records",
    methodology: "Assessed value and billed totals come from the county roll. The special assessment is the billed total minus the county-typical ad valorem rate applied to the assessed value; verify the exact line on the tax bill under Special Assessment Charges."
  };
}

// ---------------------------------------------------------------------------
// Rentcast clients. Network + parse failures degrade to { ok:false }; nothing
// throws out of the handler, because past that point the lead is already paid
// for with contact info.

async function rcFetch(path, params, apiKey) {
  const qs = new URLSearchParams(params).toString();
  const url = `${RENTCAST_BASE}${path}?${qs}`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 10000);
  let resp;
  try {
    resp = await fetch(url, {
      headers: { "X-Api-Key": apiKey, "Accept": "application/json" },
      cf: { cacheTtl: CACHE_TTL_SECONDS, cacheEverything: true },
      signal: ctrl.signal
    });
  } catch (err) {
    clearTimeout(timer);
    return { ok: false, status: 0, error: "rentcast_network" };
  }
  clearTimeout(timer);
  if (!resp.ok) return { ok: false, status: resp.status, error: `rentcast_http_${resp.status}` };
  try {
    return { ok: true, data: await resp.json() };
  } catch (err) {
    return { ok: false, status: resp.status, error: "rentcast_parse_failed" };
  }
}

async function lookupProperty(address, apiKey) {
  const result = await rcFetch("/properties", { address, limit: 1 }, apiKey);
  if (!result.ok) return { error: result.error };
  const data = Array.isArray(result.data) ? result.data[0] : result.data;
  return { data: data || null };
}

async function lookupAVM(address, property, apiKey) {
  const params = { address };
  if (property?.propertyType)  params.propertyType  = property.propertyType;
  if (property?.bedrooms)      params.bedrooms      = property.bedrooms;
  if (property?.bathrooms)     params.bathrooms     = property.bathrooms;
  if (property?.squareFootage) params.squareFootage = property.squareFootage;
  const result = await rcFetch("/avm/value", params, apiKey);
  if (!result.ok) return { error: result.error };
  return { data: result.data };
}

// Save the lead by POSTing to our own /api/lead, so delivery (email, Zapier,
// FollowUpBoss, phone normalization, drip enrollment) stays in one place.
// intent "Seller Net Sheet" maps to a FollowUpBoss Seller Inquiry.
async function saveNetSheetLead(request, contact, addr) {
  try {
    const form = new URLSearchParams();
    form.set("name", contact.name || "");
    form.set("email", contact.email);
    form.set("phone", contact.phone);
    form.set("consent", "yes");
    form.set("intent", "Seller Net Sheet");
    form.set("referral_source", "Net Sheet Property Lookup");
    form.set("source_page", contact.sourcePage || "/net-sheet/");
    if (contact.pageUrl) form.set("page_url", contact.pageUrl);
    if (addr.fullAddress) form.set("full_address", addr.fullAddress);
    if (addr.street) form.set("street_address", addr.street);
    if (addr.city)   form.set("city", addr.city);
    if (addr.state)  form.set("state", addr.state);
    if (addr.zip)    form.set("zip", addr.zip);
    if (addr.lat != null) form.set("lat", String(addr.lat));
    if (addr.lng != null) form.set("lng", String(addr.lng));
    if (contact.gclid) form.set("gclid", contact.gclid);
    form.set("submitted_at", new Date().toISOString());
    form.set("message", "Lead generated from the /net-sheet/ property lookup (contact collected before the county record was pulled or returned).");
    const leadUrl = new URL("/api/lead", request.url).toString();
    const resp = await fetch(leadUrl, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString()
    });
    if (!resp.ok) {
      let body = "";
      try { body = await resp.text(); } catch (e) {}
      console.error("NETSHEET_LEAD_SAVE_REJECTED status=" + resp.status + " body=" + body.slice(0, 300) +
        " email=" + maskEmail(contact.email) + " address=" + maskAddress(addr.fullAddress));
    }
  } catch (e) {
    console.error("NETSHEET_LEAD_SAVE_FAILED " + ((e && e.message) || e));
  }
}

function normalizeAddressInput(source) {
  const get = (k) => {
    const v = typeof source.get === "function" ? source.get(k) : source[k];
    return v == null ? "" : String(v).trim();
  };
  const single = get("address") || get("full_address") || get("formatted_address");
  if (single) return single;
  const street = get("street") || get("street_address") || get("addressLine1");
  const city   = get("city");
  const state  = get("state");
  const zip    = get("zip") || get("postal_code") || get("zipCode");
  const parts = [street, city, [state, zip].filter(Boolean).join(" ")].filter(Boolean);
  return parts.join(", ");
}

// ---------------------------------------------------------------------------

export async function onRequest(context) {
  const { request, env } = context;

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: { "allow": "GET, POST, OPTIONS" } });
  }

  const apiKey = env.RENTCAST_API_KEY;
  if (!apiKey) {
    return json({ ok: false, error: "rentcast_api_key_missing", message: "Property lookup is not configured." }, 503);
  }

  let address = "";
  let lat = null, lng = null;
  const contact = { name: "", email: "", phone: "", consent: "", gclid: "", sourcePage: "", pageUrl: "", honeypot: "" };

  try {
    if (request.method === "POST") {
      const ctype = (request.headers.get("content-type") || "").toLowerCase();
      if (ctype.includes("application/json")) {
        const body = await request.json();
        address = normalizeAddressInput(body || {});
        lat = numberOrNull(body?.lat ?? body?.latitude);
        lng = numberOrNull(body?.lng ?? body?.longitude);
        contact.name       = (body?.name ?? body?.full_name ?? "").toString().trim();
        contact.email      = (body?.email ?? "").toString().trim();
        contact.phone      = (body?.phone ?? "").toString().trim();
        contact.consent    = (body?.consent ?? "").toString().trim();
        contact.gclid      = (body?.gclid ?? "").toString().trim();
        contact.sourcePage = (body?.source_page ?? "").toString().trim();
        contact.pageUrl    = (body?.page_url ?? "").toString().trim();
        contact.honeypot   = (body?.company_website ?? "").toString().trim();
      } else if (ctype.includes("application/x-www-form-urlencoded") || ctype.includes("multipart/form-data")) {
        const form = await request.formData();
        address = normalizeAddressInput(form);
        lat = numberOrNull(form.get("lat") ?? form.get("latitude"));
        lng = numberOrNull(form.get("lng") ?? form.get("longitude"));
        contact.name       = (form.get("name") || form.get("full_name") || "").toString().trim();
        contact.email      = (form.get("email") || "").toString().trim();
        contact.phone      = (form.get("phone") || "").toString().trim();
        contact.consent    = (form.get("consent") || "").toString().trim();
        contact.gclid      = (form.get("gclid") || "").toString().trim();
        contact.sourcePage = (form.get("source_page") || "").toString().trim();
        contact.pageUrl    = (form.get("page_url") || "").toString().trim();
        contact.honeypot   = (form.get("company_website") || "").toString().trim();
      }
    } else {
      const u = new URL(request.url);
      address = (u.searchParams.get("address") || "").trim();
    }
  } catch (err) {
    return json({ ok: false, error: "bad_request", message: "Could not parse request body." }, 400);
  }

  if (!address) {
    return json({ ok: false, error: "missing_address", message: "Provide an `address` (string)." }, 400);
  }

  // ---- Contact gate ----
  // The county record is delivered only to a contact-bearing POST. A bare GET
  // can never carry contact by design, so it never returns the data. Bots that
  // fill the invisible honeypot get the identical 403: no Rentcast spend, no
  // lead, and no way to tell the two rejections apart.
  if (contact.honeypot) {
    return json({ ok: false, error: "contact_required" }, 403);
  }
  const hasContact = !!(contact.email && contact.phone && contact.consent === "yes");
  if (!hasContact) {
    return json({
      ok: false,
      error: "contact_required",
      message: "Submit your name, email, and phone to pull the property record."
    }, 403);
  }
  // A malformed email saves nothing and spends nothing; the visitor retries.
  if (!validEmail(contact.email)) {
    return json({ ok: false, error: "invalid_email", message: "That email doesn't look right. Check it and try again." }, 400);
  }
  // Rate limit (per IP, plus the Rentcast spend cap shared with /api/valuation).
  // After the honeypot + contact gate, BEFORE any upstream call or lead save.
  {
    const limited = await enforceRateLimits(context, RATE_RULES.netsheet);
    if (limited) return limited;
  }

  // Past this point the visitor has paid with contact info, so the lead must
  // survive anything the lookup does: success, empty record, or upstream fire.
  let leadSaved = false;
  const saveLeadOnce = (addr) => {
    if (leadSaved) return;
    leadSaved = true;
    context.waitUntil(saveNetSheetLead(request, contact, addr));
  };

  try {
    const propertyResult = await lookupProperty(address, apiKey);
    const property = propertyResult?.data || null;

    const avmResult = await lookupAVM(address, property, apiKey);
    const avm = avmResult?.data || null;

    // Property-record fallback: when /properties has no row for the address,
    // the AVM's subjectProperty carries the same attribute set. Tax history and
    // ownership only live on the property record, so those degrade to null,
    // but the header, the estimate, and the county-specific cost defaults all
    // survive (same fallback as /api/valuation).
    const subject = property || avm?.subjectProperty || null;

    if (!subject) {
      saveLeadOnce({
        fullAddress: address, street: "", city: "", state: "", zip: "", lat, lng
      });
      return json({
        ok: false,
        error: "no_data",
        message: "Thanks, I've got your details. I couldn't pull a county record for that address automatically, so I'll build your net sheet by hand and send it over. Or call me direct at (949) 438-5948."
      }, 200);
    }

    const county   = subject.county || "";
    const city     = subject.city || "";
    const profile  = countyProfile(county);
    const cityRule = cityTransferRule(city, county);

    const estimate = numberOrNull(avm?.price);
    const nowMs = Date.now();

    const ownership = deriveOwnership(property, estimate, nowMs);
    const taxPicture = deriveTaxPicture(property, profile, estimate);

    const addr = {
      input: address,
      formatted: subject.formattedAddress || address,
      street: subject.addressLine1 || "",
      city,
      state: subject.state || "",
      zip: subject.zipCode || "",
      county,
      lat: numberOrNull(subject.latitude) ?? lat,
      lng: numberOrNull(subject.longitude) ?? lng
    };
    saveLeadOnce({
      fullAddress: addr.formatted, street: addr.street, city: addr.city,
      state: addr.state, zip: addr.zip, lat: addr.lat, lng: addr.lng
    });

    const feat = subject.features || {};
    const hoaMonthly = numberOrNull(subject.hoa?.fee);

    return json({
      ok: true,
      address: addr,
      property: {
        propertyType: subject.propertyType || null,
        bedrooms: numberOrNull(subject.bedrooms),
        bathrooms: numberOrNull(subject.bathrooms),
        squareFootage: numberOrNull(subject.squareFootage),
        lotSize: numberOrNull(subject.lotSize),
        yearBuilt: numberOrNull(subject.yearBuilt),
        subdivision: subject.subdivision || null,
        assessorID: subject.assessorID || null,
        pool: feat.pool === true ? true : null,
        garageSpaces: numberOrNull(feat.garageSpaces),
        hoaMonthly
      },
      ownership,
      taxes: taxPicture,
      estimate: estimate ? {
        value: Math.round(estimate),
        rangeLow: numberOrNull(avm?.priceRangeLow),
        rangeHigh: numberOrNull(avm?.priceRangeHigh),
        psf: (estimate && numberOrNull(subject.squareFootage))
          ? Math.round(estimate / numberOrNull(subject.squareFootage)) : null,
        source: "Market model on recent local closings",
        note: "A starting number for the net sheet, not a list price. Joshua's written valuation is the one you price from."
      } : null,
      costs: {
        county: profile.label,
        countyTransferRate: 0.0011,
        countyTransferNote: "$1.10 per $1,000 of price. California's statewide county documentary transfer tax, customarily paid by the seller.",
        cityTransfer: cityRule,
        escrowSplit: profile.escrowSplit,
        sellerPaysOwnersTitle: profile.sellerPaysOwnersTitle,
        custom: "Southern California custom: escrow split evenly, seller pays the owner's title policy and the county transfer tax. Every line is negotiable in the contract."
      },
      diagnostics: {
        propertyError: propertyResult?.error || null,
        avmError: avmResult?.error || null,
        recordSource: property ? "property_record" : "avm_subject_fallback"
      },
      fetchedAt: new Date().toISOString()
    });
  } catch (err) {
    saveLeadOnce({ fullAddress: address, street: "", city: "", state: "", zip: "", lat, lng });
    console.error("NETSHEET_FAILED " + ((err && err.message) || err));
    return json({
      ok: false,
      error: "upstream_failed",
      message: "Thanks, I've got your details. The county lookup failed on my end, so I'll pull your record by hand and send the net sheet over."
    }, 502);
  }
}
