// /api/valuation - the 5-system home valuation aggregator powering /value/.
//
// One paid upstream (Rentcast) gives us property attributes + AVM market value +
// comparable sales + rent estimate. From those we synthesize five different
// "what is this home worth?" answers, each anchored to a defensible methodology:
//
//   1) Market AVM            - Rentcast statistical model on recent local sales
//   2) Tax assessor value    - County recorder data (from Rentcast property record)
//   3) Replacement cost      - sqft x regional construction cost x quality tier
//                              (NAHB 2024 cost-of-constructing-a-home + CA labor adj.)
//   4) Investor ARV          - top-third $/sqft of comps applied to subject's sqft,
//                              with AVM-times-renovation-premium fallback
//   5) Triangulated price    - weighted blend; what Joshua would list at by default
//
// Plus a small investor panel (cap rate, GRM, 70% wholesale offer, monthly cash
// flow at current 30y from our own /api/rates).
//
// Env var required:
//   RENTCAST_API_KEY  - get one at https://app.rentcast.io/app/api
//
// Returns 503 with structured error when the key is missing so the page can
// degrade gracefully (same pattern as /api/rates and /api/prices).

const RENTCAST_BASE = "https://api.rentcast.io/v1";

// Edge cache valuation responses per address for 7 days. AVMs don't move daily
// and the marginal cost saving is real once paid traffic is hitting this.
const CACHE_TTL_SECONDS = 60 * 60 * 24 * 7;

const json = (body, status = 200, extra = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=UTF-8",
      "cache-control": status === 200
        ? `public, max-age=${CACHE_TTL_SECONDS}, s-maxage=${CACHE_TTL_SECONDS}`
        : "no-store",
      ...extra
    }
  });

// ---------------------------------------------------------------------------
// Regional construction cost table.
//
// Source baseline: NAHB 2024 "Cost of Constructing a Home" national median of
// ~$284/sqft (hard construction only, no land). California labor + permit
// multipliers from RSMeans City Cost Index (LA ~1.30, SD ~1.27, SF ~1.45,
// OC ~1.32, Inland Empire ~1.18). Quality tier multipliers reflect tract
// (entry), production (mid), and custom (luxury) builds in 2024-2026 SoCal.
//
// Methodology disclosed in the response so the page can show its work.
const NATIONAL_BASE_PSF = 284;

const REGION_FACTORS = {
  // California sub-regions, keyed by county or city heuristic from address text.
  "los angeles":     1.30,
  "orange":          1.32,
  "san diego":       1.27,
  "san francisco":   1.45,
  "san mateo":       1.42,
  "santa clara":     1.42,
  "alameda":         1.38,
  "marin":           1.42,
  "ventura":         1.28,
  "santa barbara":   1.32,
  "riverside":       1.18,
  "san bernardino":  1.18,
  "kern":            1.10,
  "fresno":          1.08,
  "sacramento":      1.15,
  "ca_default":      1.25,
  "us_default":      1.00
};

const QUALITY_FACTORS = {
  entry:  0.85,   // tract / production starter
  mid:    1.00,   // standard production with upgrades
  upper:  1.35,   // semi-custom, premium finishes
  luxury: 1.85    // full custom, top-tier finishes
};

function pickRegionFactor(addressText, state) {
  const t = (addressText || "").toLowerCase();
  for (const key of Object.keys(REGION_FACTORS)) {
    if (key === "ca_default" || key === "us_default") continue;
    if (t.includes(key)) return { factor: REGION_FACTORS[key], region: key };
  }
  if ((state || "").toUpperCase() === "CA") {
    return { factor: REGION_FACTORS.ca_default, region: "california (default)" };
  }
  return { factor: REGION_FACTORS.us_default, region: "national" };
}

// Quality tier inferred from the subject's current $/sqft relative to the
// regional baseline cost. Properties priced way above local construction cost
// signal upper-end finishes and lot premium; below baseline signals entry.
function pickQualityTier(avmValue, sqft, regionalPsf) {
  if (!avmValue || !sqft || !regionalPsf) return { tier: "mid", factor: QUALITY_FACTORS.mid };
  const subjectPsf = avmValue / sqft;
  const ratio = subjectPsf / regionalPsf;
  if (ratio < 0.85)  return { tier: "entry",  factor: QUALITY_FACTORS.entry  };
  if (ratio < 1.55)  return { tier: "mid",    factor: QUALITY_FACTORS.mid    };
  if (ratio < 2.30)  return { tier: "upper",  factor: QUALITY_FACTORS.upper  };
  return                    { tier: "luxury", factor: QUALITY_FACTORS.luxury };
}

function computeReplacementCost(property, avmValue) {
  const sqft = numberOrNull(property?.squareFootage);
  if (!sqft) return null;
  const region = pickRegionFactor(property?.formattedAddress, property?.state);
  const regionalPsf = NATIONAL_BASE_PSF * region.factor;
  const quality = pickQualityTier(avmValue, sqft, regionalPsf);
  const psf = regionalPsf * quality.factor;
  const value = Math.round(sqft * psf);
  return {
    value,
    psf: Math.round(psf),
    sqft,
    region: region.region,
    regionFactor: region.factor,
    quality: quality.tier,
    qualityFactor: quality.factor,
    baseline: NATIONAL_BASE_PSF,
    methodology: "NAHB 2024 national median construction cost ($284/sqft) x regional cost-of-construction factor x quality tier. Hard build only, excludes land."
  };
}

// ---------------------------------------------------------------------------
// ARV = After Repair Value. Method: take the top third of comps by $/sqft
// (proxy for "recently updated" -- the renovated comps in any market sit at
// the top of the local $/sqft distribution), average them, apply to subject
// sqft. Fall back to AVM x renovation premium if too few comps.
function computeARV(avm, property) {
  const sqft = numberOrNull(property?.squareFootage);
  const comps = Array.isArray(avm?.comparables) ? avm.comparables : [];
  const validComps = comps
    .map(c => ({
      price: numberOrNull(c?.price),
      sqft:  numberOrNull(c?.squareFootage)
    }))
    .filter(c => c.price > 0 && c.sqft > 0)
    .map(c => ({ ...c, psf: c.price / c.sqft }));

  const FALLBACK_PREMIUM = 1.18;
  if (validComps.length < 5 || !sqft) {
    const avmValue = numberOrNull(avm?.price);
    if (!avmValue) return null;
    return {
      value: Math.round(avmValue * FALLBACK_PREMIUM),
      method: "premium_fallback",
      premium: FALLBACK_PREMIUM,
      methodology: `Insufficient renovated comps; estimated as AVM x ${FALLBACK_PREMIUM} typical light-renovation premium.`
    };
  }

  validComps.sort((a, b) => b.psf - a.psf);
  const topThird = validComps.slice(0, Math.max(3, Math.ceil(validComps.length / 3)));
  const avgTopPsf = topThird.reduce((s, c) => s + c.psf, 0) / topThird.length;
  const value = Math.round(avgTopPsf * sqft);
  return {
    value,
    method: "top_third_comps",
    compsUsed: topThird.length,
    compsTotal: validComps.length,
    avgPsf: Math.round(avgTopPsf),
    methodology: `Average $/sqft of the top third of ${validComps.length} local comparable sales (proxy for renovated condition), applied to subject's ${sqft} sqft.`
  };
}

// ---------------------------------------------------------------------------
// Tax assessor value -- pull the most recent year from the property record's
// taxAssessments map. Falls back to lastSalePrice when no assessor data.
function pickAssessorValue(property) {
  const assessments = property?.taxAssessments;
  if (assessments && typeof assessments === "object") {
    const years = Object.keys(assessments)
      .map(y => parseInt(y, 10))
      .filter(Number.isFinite)
      .sort((a, b) => b - a);
    for (const y of years) {
      const v = numberOrNull(assessments[y]?.value ?? assessments[String(y)]?.value);
      if (v) {
        return {
          value: v,
          year: y,
          land:         numberOrNull(assessments[y]?.land),
          improvements: numberOrNull(assessments[y]?.improvements),
          source: "county_assessor",
          methodology: `County assessor's recorded value for tax year ${y}. In California (Prop 13), assessed value often lags market by 30-70% on long-held homes.`
        };
      }
    }
  }
  const lastSale = numberOrNull(property?.lastSalePrice);
  if (lastSale) {
    return {
      value: lastSale,
      year: (property?.lastSaleDate || "").slice(0, 4) || null,
      source: "last_sale",
      methodology: "No current assessor value available; showing last recorded sale price as a tax-floor proxy."
    };
  }
  return null;
}

// ---------------------------------------------------------------------------
// Triangulated price -- weighted blend favoring the AVM (most data-rich)
// with a partial pull from ARV (upside) and a comp median sanity check.
function computeTriangulated(avmValue, arvValue, compMedian) {
  const parts = [];
  if (avmValue)    parts.push({ value: avmValue,    weight: 0.60 });
  if (compMedian)  parts.push({ value: compMedian,  weight: 0.25 });
  if (arvValue)    parts.push({ value: arvValue,    weight: 0.15 });
  if (parts.length === 0) return null;
  const totalWeight = parts.reduce((s, p) => s + p.weight, 0);
  const weighted = parts.reduce((s, p) => s + p.value * p.weight, 0) / totalWeight;
  return {
    value: Math.round(weighted),
    methodology: "Weighted blend (AVM 60%, comp median 25%, ARV-adjusted 15%). Joshua reviews each pull and overrides when his on-the-ground read of the home calls for a different list price."
  };
}

function compMedianPrice(avm) {
  const comps = Array.isArray(avm?.comparables) ? avm.comparables : [];
  const prices = comps.map(c => numberOrNull(c?.price)).filter(v => v > 0).sort((a, b) => a - b);
  if (prices.length === 0) return null;
  const mid = Math.floor(prices.length / 2);
  return prices.length % 2 ? prices[mid] : Math.round((prices[mid - 1] + prices[mid]) / 2);
}

// ---------------------------------------------------------------------------
// Investor metrics. Cap rate uses a coarse expense estimate (35% of gross
// rent for ops + vacancy + maintenance + taxes + insurance); cash flow uses
// the current 30y mortgage rate from our own /api/rates.
async function computeInvestorMetrics(value, rentEstimate, requestUrl) {
  if (!value || !rentEstimate) return null;
  const monthlyRent = rentEstimate;
  const annualRent  = monthlyRent * 12;
  const grm = Number((value / annualRent).toFixed(1));
  const noi = annualRent * 0.65; // 35% expense ratio
  const capRate = Number(((noi / value) * 100).toFixed(2));

  const rate30y = await fetch30yRate(requestUrl);

  let monthlyCashFlow = null;
  let monthlyPI       = null;
  if (rate30y && rate30y > 0) {
    const downPct = 0.20;
    const loan = value * (1 - downPct);
    const r = (rate30y / 100) / 12;
    const n = 30 * 12;
    monthlyPI = Math.round((loan * r) / (1 - Math.pow(1 + r, -n)));
    const monthlyExpenses = Math.round((annualRent * 0.35) / 12);
    monthlyCashFlow = monthlyRent - monthlyPI - monthlyExpenses;
  }

  return {
    monthlyRent,
    annualRent,
    grm,
    capRate,
    expenseRatio: 0.35,
    noi: Math.round(noi),
    wholesaleOffer: Math.round((value * 0.70) - (40 * 250)),  // ARV * 0.70 - placeholder rehab; refined below
    rate30y,
    downPct: 0.20,
    monthlyPI,
    monthlyCashFlow,
    methodology: "Cap rate uses 35% expense ratio (taxes + insurance + ops + vacancy + maintenance). Cash flow assumes 20% down at today's 30-year fixed from FRED."
  };
}

// 70% rule: max wholesale offer = ARV * 0.70 - estimated rehab. Standard
// SoCal rehab estimate is $40-80/sqft for cosmetic + kitchen + baths;
// using $50/sqft midpoint. Disclosed in the response.
function computeWholesaleOffer(arvValue, sqft) {
  if (!arvValue) return null;
  const rehabPsf = 50;
  const rehabCost = (sqft || 1500) * rehabPsf;
  const offer = Math.round(arvValue * 0.70 - rehabCost);
  return {
    value: offer,
    arvValue,
    rehabPsf,
    rehabCost,
    formula: "(ARV x 0.70) - rehab estimate",
    methodology: `Standard flipper 70% rule. ARV times 0.70 minus rehab at $${rehabPsf}/sqft (cosmetic + kitchen + baths typical for SoCal). Negative numbers mean the deal won't pencil at retail.`
  };
}

async function fetch30yRate(requestUrl) {
  try {
    const u = new URL(requestUrl);
    const ratesUrl = `${u.protocol}//${u.host}/api/rates`;
    const resp = await fetch(ratesUrl, { cf: { cacheTtl: 3600, cacheEverything: true } });
    if (!resp.ok) return null;
    const data = await resp.json();
    return numberOrNull(data?.series?.rate30y?.latest?.value);
  } catch (err) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Rentcast clients

async function rcFetch(path, params, apiKey) {
  const qs = new URLSearchParams(params).toString();
  const url = `${RENTCAST_BASE}${path}?${qs}`;
  const resp = await fetch(url, {
    headers: { "X-Api-Key": apiKey, "Accept": "application/json" },
    cf: { cacheTtl: CACHE_TTL_SECONDS, cacheEverything: true }
  });
  if (!resp.ok) {
    return { ok: false, status: resp.status, error: `rentcast_http_${resp.status}` };
  }
  try {
    const data = await resp.json();
    return { ok: true, data };
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
  if (property?.propertyType)   params.propertyType   = property.propertyType;
  if (property?.bedrooms)       params.bedrooms       = property.bedrooms;
  if (property?.bathrooms)      params.bathrooms      = property.bathrooms;
  if (property?.squareFootage)  params.squareFootage  = property.squareFootage;
  const result = await rcFetch("/avm/value", params, apiKey);
  if (!result.ok) return { error: result.error };
  return { data: result.data };
}

async function lookupRent(address, property, apiKey) {
  const params = { address };
  if (property?.propertyType)   params.propertyType   = property.propertyType;
  if (property?.bedrooms)       params.bedrooms       = property.bedrooms;
  if (property?.bathrooms)      params.bathrooms      = property.bathrooms;
  if (property?.squareFootage)  params.squareFootage  = property.squareFootage;
  const result = await rcFetch("/avm/rent/long-term", params, apiKey);
  if (!result.ok) return { error: result.error };
  return { data: result.data };
}

// ---------------------------------------------------------------------------
// Utilities

function numberOrNull(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = typeof v === "number" ? v : parseFloat(v);
  return Number.isFinite(n) ? n : null;
}

function normalizeAddressInput(form) {
  const direct = (form.get("address") || "").toString().trim();
  if (direct) return direct;
  const street = (form.get("street") || form.get("street_address") || "").toString().trim();
  const city   = (form.get("city") || "").toString().trim();
  const state  = (form.get("state") || "").toString().trim();
  const zip    = (form.get("zip") || "").toString().trim();
  const parts = [street, city, state, zip].filter(Boolean);
  return parts.length >= 2 ? parts.join(", ") : "";
}

// ---------------------------------------------------------------------------
// Handler

export async function onRequest(context) {
  const { request, env } = context;
  const apiKey = env && env.RENTCAST_API_KEY;

  if (!apiKey) {
    return json({
      ok: false,
      error: "rentcast_api_key_missing",
      message: "Set RENTCAST_API_KEY in Cloudflare Pages environment variables."
    }, 503);
  }

  // Accept GET (?address=...) and POST (form or JSON).
  let address = "";
  let lat = null, lng = null;

  try {
    if (request.method === "POST") {
      const ctype = request.headers.get("Content-Type") || "";
      if (ctype.includes("application/json")) {
        const body = await request.json();
        address = (body?.address || "").toString().trim();
        lat = numberOrNull(body?.lat ?? body?.latitude);
        lng = numberOrNull(body?.lng ?? body?.longitude);
      } else if (ctype.includes("application/x-www-form-urlencoded") || ctype.includes("multipart/form-data")) {
        const form = await request.formData();
        address = normalizeAddressInput(form);
        lat = numberOrNull(form.get("lat") ?? form.get("latitude"));
        lng = numberOrNull(form.get("lng") ?? form.get("longitude"));
      }
    } else {
      const u = new URL(request.url);
      address = (u.searchParams.get("address") || "").trim();
      lat = numberOrNull(u.searchParams.get("lat") ?? u.searchParams.get("latitude"));
      lng = numberOrNull(u.searchParams.get("lng") ?? u.searchParams.get("longitude"));
    }
  } catch (err) {
    return json({ ok: false, error: "bad_request", message: "Could not parse request body." }, 400);
  }

  if (!address) {
    return json({ ok: false, error: "missing_address", message: "Provide an `address` (string) or lat/lng pair." }, 400);
  }

  // Fan out: property lookup first (need attributes for the comp-targeted AVM
  // and rent calls), then AVM + rent in parallel.
  const propertyResult = await lookupProperty(address, apiKey);
  const property = propertyResult?.data || null;

  const [avmResult, rentResult] = await Promise.all([
    lookupAVM(address, property, apiKey),
    lookupRent(address, property, apiKey)
  ]);
  const avm  = avmResult?.data  || null;
  const rent = rentResult?.data || null;

  const marketValue  = numberOrNull(avm?.price);
  const marketLow    = numberOrNull(avm?.priceRangeLow);
  const marketHigh   = numberOrNull(avm?.priceRangeHigh);
  const monthlyRent  = numberOrNull(rent?.rent);

  const replacement  = computeReplacementCost(property, marketValue);
  const arv          = computeARV(avm, property);
  const assessor     = pickAssessorValue(property);
  const compMedian   = compMedianPrice(avm);
  const triangulated = computeTriangulated(marketValue, arv?.value, compMedian);
  const investor     = await computeInvestorMetrics(marketValue, monthlyRent, request.url);
  const wholesale    = computeWholesaleOffer(arv?.value, numberOrNull(property?.squareFootage));

  const anyData = marketValue || replacement?.value || arv?.value || assessor?.value;

  return json({
    ok: !!anyData,
    address: {
      input: address,
      lat, lng,
      formatted: property?.formattedAddress || address,
      street:    property?.addressLine1 || null,
      city:      property?.city || null,
      state:     property?.state || null,
      zip:       property?.zipCode || null,
      county:    property?.county || null
    },
    property: property ? {
      propertyType:  property.propertyType || null,
      bedrooms:      numberOrNull(property.bedrooms),
      bathrooms:     numberOrNull(property.bathrooms),
      squareFootage: numberOrNull(property.squareFootage),
      lotSize:       numberOrNull(property.lotSize),
      yearBuilt:     numberOrNull(property.yearBuilt),
      lastSalePrice: numberOrNull(property.lastSalePrice),
      lastSaleDate:  property.lastSaleDate || null
    } : null,
    systems: {
      marketAVM: marketValue ? {
        label: "Market AVM",
        value: marketValue,
        rangeLow:  marketLow,
        rangeHigh: marketHigh,
        compsCount: Array.isArray(avm?.comparables) ? avm.comparables.length : 0,
        source: "Rentcast AVM",
        methodology: "Statistical model trained on recent local sales of properties matching beds, baths, sqft, age, and lot. Updated daily as new sales close."
      } : null,
      assessor: assessor ? { label: "Tax assessor value", ...assessor } : null,
      replacementCost: replacement ? { label: "Replacement cost", ...replacement } : null,
      arv: arv ? { label: "Investor ARV (after repair value)", ...arv } : null,
      triangulated: triangulated ? { label: "Joshua's triangulated price", ...triangulated } : null
    },
    investor: investor ? {
      ...investor,
      wholesale70: wholesale
    } : null,
    rentEstimate: rent ? {
      monthly: monthlyRent,
      rangeLow: numberOrNull(rent?.rentRangeLow),
      rangeHigh: numberOrNull(rent?.rentRangeHigh),
      source: "Rentcast rent AVM"
    } : null,
    diagnostics: {
      propertyError: propertyResult?.error || null,
      avmError:      avmResult?.error || null,
      rentError:     rentResult?.error || null
    },
    source: "Rentcast Property API + Drozq replacement cost model",
    sourceUrl: "https://www.rentcast.io/api",
    fetchedAt: new Date().toISOString()
  });
}
