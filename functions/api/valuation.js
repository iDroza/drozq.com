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
// flow at current 30y from our own /api/rates), and the comp study (`cma`):
// the three buckets of a real CMA (recorded closings, active competition,
// came-off-unsold listings), similarity-ranked with size-adjusted values,
// sale-to-list ratios, and radius-level months-of-inventory. See assembleCMA.
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
// Trim the raw AVM comparables down to a clean, display-ready set. These are
// the actual recent sales the model leaned on; surfacing them is the single
// biggest trust lever the page has (no Zestimate competitor shows its work).
// Sorted by correlation (Rentcast's similarity score) so the closest matches
// lead, with distance as the tiebreak. Every field is null-guarded.
function trimComps(avm, limit) {
  limit = limit || 6;
  const raw = Array.isArray(avm?.comparables) ? avm.comparables : [];
  const mapped = raw.map(c => {
    const price = numberOrNull(c?.price);
    const sqft  = numberOrNull(c?.squareFootage);
    return {
      formattedAddress: c?.formattedAddress || c?.addressLine1 || null,
      bedrooms:      numberOrNull(c?.bedrooms),
      bathrooms:     numberOrNull(c?.bathrooms),
      squareFootage: sqft,
      price,
      psf:        (price && sqft) ? Math.round(price / sqft) : null,
      distance:   c?.distance    != null ? Number(Number(c.distance).toFixed(2)) : null,
      daysOld:    numberOrNull(c?.daysOld),
      saleDate:   c?.removedDate || c?.lastSeenDate || c?.listedDate || null,
      correlation: c?.correlation != null ? Number(Number(c.correlation).toFixed(3)) : null
    };
  }).filter(c => c.price > 0);

  mapped.sort((a, b) => {
    const ca = a.correlation, cb = b.correlation;
    if (ca != null && cb != null && cb !== ca) return cb - ca;
    if (a.distance != null && b.distance != null) return a.distance - b.distance;
    return 0;
  });
  return mapped.slice(0, limit);
}

// ---------------------------------------------------------------------------
// The comp study (pseudo-CMA). A real CMA weighs three sets of comps, and this
// builds all three the way an agent would for a listing appointment:
//
//   sold    - recorded closings nearby (the evidence). Deed data from property
//             records (real closed prices), enriched with the matching listing
//             record when one exists so we can show list price, sale-to-list,
//             and days on market for the sale.
//   active  - live listings nearby (the competition the seller lists against).
//   expired - listings that sat and came off the market unsold at an ask above
//             the sold band (the ceiling: the price the market refused).
//
// Selection follows standard CMA practice: same property type, tight radius,
// recent window, distressed listing types excluded, then similarity-ranked on
// size, distance, beds, baths, and age. Everything here is additive to the
// response (`cma`) and best-effort: any upstream failure degrades to the
// legacy `comps` list, never breaks the valuation.
const CMA = {
  RADIUS_MI: 1.0,                 // tight comp radius (standard suburban CMA range)
  SOLD_WINDOW_DAYS: 270,          // recorded closings from the last ~9 months
  LISTING_WINDOW_DAYS: 540,       // how far back the delisted pool reaches (listed date)
  EXPIRED_MIN_DOM: 45,            // shorter delistings are usually sales going pending
  EXPIRED_MIN_REMOVED_DAYS: 30,   // very recent delistings may be pending closings
  EXPIRED_MAX_REMOVED_DAYS: 365,  // older failures stop being market evidence
  SOLD_SHOWN: 6,
  ACTIVE_SHOWN: 5,
  EXPIRED_SHOWN: 4,
  POOL_LIMIT: 50                  // upstream fetch size per bucket before ranking
};

// Distressed listing types are excluded from every bucket, per standard comp
// practice (they price the seller's situation, not the home).
const CMA_EXCLUDED_LISTING_TYPES = ["Foreclosure", "Short Sale"];

function addressKey(s) {
  return (s || "").toString().toLowerCase().replace(/[^a-z0-9]/g, "");
}

function haversineMiles(lat1, lng1, lat2, lng2) {
  if (lat1 == null || lng1 == null || lat2 == null || lng2 == null) return null;
  const toRad = d => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.pow(Math.sin(dLat / 2), 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.pow(Math.sin(dLng / 2), 2);
  return 3958.8 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function daysSince(dateStr) {
  if (!dateStr) return null;
  const t = Date.parse(dateStr);
  if (!Number.isFinite(t)) return null;
  return Math.max(0, Math.round((Date.now() - t) / 86400000));
}

function medianOf(nums) {
  const v = (nums || []).filter(n => Number.isFinite(n)).sort((a, b) => a - b);
  if (!v.length) return null;
  const mid = Math.floor(v.length / 2);
  return v.length % 2 ? v[mid] : (v[mid - 1] + v[mid]) / 2;
}

function quantileOf(nums, q) {
  const v = (nums || []).filter(n => Number.isFinite(n)).sort((a, b) => a - b);
  if (!v.length) return null;
  const pos = (v.length - 1) * q;
  const lo = Math.floor(pos), hi = Math.ceil(pos);
  return v[lo] + (v[hi] - v[lo]) * (pos - lo);
}

// Similarity ranking, 0-100. Encodes the comp-selection instinct: closest in
// size first, then distance, bed/bath count, and age; different property type
// is heavily penalized. Deterministic and disclosed ("matched on size,
// distance, beds, baths, and age").
function similarityScore(subject, cand) {
  let score = 100;
  const sSqft = numberOrNull(subject?.squareFootage);
  const cSqft = numberOrNull(cand?.squareFootage);
  if (sSqft && cSqft) score -= Math.min(Math.abs(cSqft - sSqft) / sSqft, 0.5) * 60;
  else score -= 8;
  if (cand?.distanceMi != null) score -= (Math.min(cand.distanceMi, 1.5) / 1.5) * 25;
  const sb = numberOrNull(subject?.bedrooms), cb = numberOrNull(cand?.bedrooms);
  if (sb && cb) score -= Math.min(Math.abs(cb - sb) * 6, 12);
  const sba = numberOrNull(subject?.bathrooms), cba = numberOrNull(cand?.bathrooms);
  if (sba && cba) score -= Math.min(Math.abs(cba - sba) * 4, 8);
  const sy = numberOrNull(subject?.yearBuilt), cy = numberOrNull(cand?.yearBuilt);
  if (sy && cy) score -= (Math.min(Math.abs(cy - sy), 40) / 40) * 10;
  if (subject?.propertyType && cand?.propertyType && subject.propertyType !== cand.propertyType) score -= 15;
  return Math.max(0, Math.round(score));
}

// Recorded closings near the subject (deed data -> real closed prices).
async function lookupSoldRecords(lat, lng, propertyType, apiKey) {
  const params = {
    latitude: lat, longitude: lng, radius: CMA.RADIUS_MI,
    saleDateRange: `*:${CMA.SOLD_WINDOW_DAYS}`, limit: CMA.POOL_LIMIT
  };
  if (propertyType) params.propertyType = propertyType;
  const result = await rcFetch("/properties", params, apiKey);
  if (!result.ok) return { error: result.error, data: [] };
  return { error: null, data: Array.isArray(result.data) ? result.data : [] };
}

// Sale listings near the subject. status "Active" = the live competition;
// status "Inactive" = the delisted pool (expired/withdrawn candidates + the
// listing records that let us enrich solds with list price and DOM).
async function lookupSaleListings(lat, lng, propertyType, status, apiKey) {
  const params = {
    latitude: lat, longitude: lng, radius: CMA.RADIUS_MI,
    status, limit: CMA.POOL_LIMIT
  };
  if (status === "Inactive") params.daysOld = `1:${CMA.LISTING_WINDOW_DAYS}`;
  if (propertyType) params.propertyType = propertyType;
  const result = await rcFetch("/listings/sale", params, apiKey);
  if (!result.ok) return { error: result.error, data: [] };
  return { error: null, data: Array.isArray(result.data) ? result.data : [] };
}

// Hard similarity bound: comps within +/-25% of the subject's living area
// (the appraiser outer guideline). Applied only when it leaves enough sample;
// otherwise fall back to the unfiltered pool (standard practice: expand
// criteria only when the tight net comes up short).
function sqftTolerancePool(list, subjSqft, keepMin) {
  if (!subjSqft) return list;
  const tight = list.filter(n => !n.squareFootage || Math.abs(n.squareFootage - subjSqft) / subjSqft <= 0.25);
  return tight.length >= keepMin ? tight : list;
}

// Pure assembly of the three buckets + roll-up stats from the raw pools.
// Never throws: any surprise in upstream shapes degrades to null (the page
// falls back to the legacy flat comp list).
function assembleCMA(property, subjLat, subjLng, subjAddressKey, avm, soldPool, activePool, inactivePool) {
  try {
    const subject = {
      squareFootage: numberOrNull(property?.squareFootage),
      bedrooms:      numberOrNull(property?.bedrooms),
      bathrooms:     numberOrNull(property?.bathrooms),
      yearBuilt:     numberOrNull(property?.yearBuilt),
      propertyType:  property?.propertyType || null
    };
    const subjSqft = subject.squareFootage;

    const normalize = (r) => {
      const price = numberOrNull(r?.price);
      const sqft  = numberOrNull(r?.squareFootage);
      const distanceMi = haversineMiles(subjLat, subjLng, numberOrNull(r?.latitude), numberOrNull(r?.longitude));
      return {
        key: addressKey(r?.formattedAddress || r?.id),
        address: r?.formattedAddress || null,
        propertyType: r?.propertyType || null,
        bedrooms:  numberOrNull(r?.bedrooms),
        bathrooms: numberOrNull(r?.bathrooms),
        squareFootage: sqft,
        yearBuilt: numberOrNull(r?.yearBuilt),
        price,
        rawPsf: (price > 0 && sqft > 0) ? price / sqft : null,
        distanceMi: distanceMi != null ? Number(distanceMi.toFixed(2)) : null,
        listingType: r?.listingType || null,
        listedDate: r?.listedDate || null,
        removedDate: r?.removedDate || null,
        daysOnMarket: numberOrNull(r?.daysOnMarket),
        history: r?.history || null
      };
    };

    const isDistressed = (n) => n.listingType && CMA_EXCLUDED_LISTING_TYPES.indexOf(n.listingType) !== -1;

    // --- Sold bucket: deed-recorded closings, enriched from the delisted pool.
    const inactiveNorm = (inactivePool || []).map(normalize);
    const inactiveByKey = {};
    for (const n of inactiveNorm) { if (n.key && !inactiveByKey[n.key]) inactiveByKey[n.key] = n; }

    const soldSeen = {};
    let soldNorm = [];
    for (const r of (soldPool || [])) {
      const soldPrice = numberOrNull(r?.lastSalePrice);
      if (!(soldPrice > 0) || !r?.lastSaleDate) continue;
      const n = normalize(r);
      if (!n.key || n.key === subjAddressKey || soldSeen[n.key]) continue;
      soldSeen[n.key] = true;
      n.soldPrice = soldPrice;
      n.soldDate = r.lastSaleDate;
      n.soldAgeDays = daysSince(r.lastSaleDate);
      soldNorm.push(n);
    }
    // Similarity first, then recency tiering: 90-180 day sales are the
    // professional standard and the 9-month window is the thin-market
    // fallback, but the window only tightens when enough SIMILAR comps
    // remain (tolerance-filtered pool), never on raw counts.
    soldNorm = sqftTolerancePool(soldNorm, subjSqft, 3);
    const recentSolds = soldNorm.filter(n => n.soldAgeDays != null && n.soldAgeDays <= 180);
    if (recentSolds.length >= 4) soldNorm = recentSolds;

    // Sold-band $/sqft from the filtered pool: the reference for adjusted
    // values, the expired-overpricing test, and the subject's comp band.
    const soldPsfList = soldNorm.map(n => (n.squareFootage > 0) ? n.soldPrice / n.squareFootage : null).filter(v => v != null);
    const soldPsfMedian = medianOf(soldPsfList);
    // Marginal $/sqft for size adjustments: one third of the local $/sqft
    // (full $/sqft embeds land + kitchens/baths; marginal living area does
    // not, so appraiser practice adjusts size gaps at roughly a third).
    const marginalPsf = soldPsfMedian ? soldPsfMedian / 3 : null;

    const soldAll = soldNorm.map(n => {
      const psfRaw = (n.squareFootage > 0) ? n.soldPrice / n.squareFootage : null;
      const entry = {
        address: n.address,
        distanceMi: n.distanceMi,
        bedrooms: n.bedrooms,
        bathrooms: n.bathrooms,
        squareFootage: n.squareFootage,
        yearBuilt: n.yearBuilt,
        soldPrice: n.soldPrice,
        soldDate: n.soldDate,
        psf: psfRaw ? Math.round(psfRaw) : null,
        // Size-adjusted value: what this comp says the SUBJECT would have
        // closed at, adjusting the size gap at the marginal (not full) $/sqft.
        adjustedValue: (marginalPsf && subjSqft && n.squareFootage)
          ? Math.round(n.soldPrice + (subjSqft - n.squareFootage) * marginalPsf)
          : null,
        listPrice: null, saleToListPct: null, domAtSale: null,
        matchScore: 0
      };
      // Enrich with the listing episode that produced this sale, when the
      // delisted pool has it and the dates line up (removed within ~6 months
      // of the recorded closing).
      const listing = inactiveByKey[n.key];
      if (listing && listing.price > 0 && listing.removedDate) {
        const gapDays = Math.abs((Date.parse(n.soldDate) - Date.parse(listing.removedDate)) / 86400000);
        if (Number.isFinite(gapDays) && gapDays <= 180) {
          entry.listPrice = listing.price;
          entry.saleToListPct = Math.round((n.soldPrice / listing.price) * 1000) / 10;
          entry.domAtSale = listing.daysOnMarket;
        }
      }
      let score = similarityScore(subject, n);
      if (n.soldAgeDays != null) score -= (Math.min(n.soldAgeDays, CMA.SOLD_WINDOW_DAYS) / CMA.SOLD_WINDOW_DAYS) * 8;
      entry.matchScore = Math.max(0, Math.round(score));
      return entry;
    });
    soldAll.sort((a, b) => b.matchScore - a.matchScore);
    const soldKeys = soldSeen;

    // --- Active bucket: the live competition.
    let activeNorm = [];
    const activeSeen = {};
    for (const n of (activePool || []).map(normalize)) {
      if (!(n.price > 0) || !n.key || n.key === subjAddressKey || activeSeen[n.key] || isDistressed(n)) continue;
      activeSeen[n.key] = true;
      activeNorm.push(n);
    }
    activeNorm = sqftTolerancePool(activeNorm, subjSqft, 2);
    const activeAll = activeNorm.map(n => ({
      address: n.address,
      distanceMi: n.distanceMi,
      bedrooms: n.bedrooms,
      bathrooms: n.bathrooms,
      squareFootage: n.squareFootage,
      yearBuilt: n.yearBuilt,
      askPrice: n.price,
      psf: n.rawPsf ? Math.round(n.rawPsf) : null,
      dom: n.daysOnMarket,
      listedDate: n.listedDate,
      matchScore: similarityScore(subject, n)
    }));
    activeAll.sort((a, b) => b.matchScore - a.matchScore);

    // --- Expired bucket: sat, came off unsold, asked at/above the sold band.
    // Guards against mislabeling a pending sale as a failure: minimum days on
    // market, minimum days since removal, and no recorded closing at that
    // address in the sold pool (nor treatment as sale evidence by the model).
    const avmComps = Array.isArray(avm?.comparables) ? avm.comparables : [];
    const avmSoldKeys = {};
    for (const c of avmComps) { if (c?.removedDate) avmSoldKeys[addressKey(c?.formattedAddress || c?.id)] = true; }

    const expiredAll = [];
    for (const n of sqftTolerancePool(inactiveNorm, subjSqft, 2)) {
      if (!(n.price > 0) || !n.key || n.key === subjAddressKey || isDistressed(n)) continue;
      if (soldKeys[n.key] || avmSoldKeys[n.key]) continue;
      const removedAgo = daysSince(n.removedDate);
      if (removedAgo == null || removedAgo < CMA.EXPIRED_MIN_REMOVED_DAYS || removedAgo > CMA.EXPIRED_MAX_REMOVED_DAYS) continue;
      if (!(n.daysOnMarket >= CMA.EXPIRED_MIN_DOM)) continue;
      if (soldPsfMedian && n.rawPsf && n.rawPsf < soldPsfMedian * 0.98) continue;
      // Price-cut evidence from the listing history, when present.
      let priceCutPct = null;
      if (n.history && typeof n.history === "object") {
        const histPrices = Object.keys(n.history).map(k => numberOrNull(n.history[k]?.price)).filter(v => v > 0);
        const maxHist = histPrices.length ? Math.max.apply(null, histPrices) : null;
        if (maxHist && maxHist > n.price * 1.02) priceCutPct = Math.round((1 - n.price / maxHist) * 100);
      }
      expiredAll.push({
        address: n.address,
        distanceMi: n.distanceMi,
        bedrooms: n.bedrooms,
        bathrooms: n.bathrooms,
        squareFootage: n.squareFootage,
        yearBuilt: n.yearBuilt,
        lastAsk: n.price,
        psf: n.rawPsf ? Math.round(n.rawPsf) : null,
        dom: n.daysOnMarket,
        removedDate: n.removedDate,
        priceCutPct,
        vsSoldMedianPct: (soldPsfMedian && n.rawPsf) ? Math.round((n.rawPsf / soldPsfMedian - 1) * 100) : null,
        matchScore: similarityScore(subject, n)
      });
    }
    expiredAll.sort((a, b) => b.matchScore - a.matchScore);

    const sold    = soldAll.slice(0, CMA.SOLD_SHOWN);
    const active  = activeAll.slice(0, CMA.ACTIVE_SHOWN);
    const expired = expiredAll.slice(0, CMA.EXPIRED_SHOWN);
    if (!sold.length && !active.length && !expired.length) return null;

    // Roll-up stats across the full pools (what the section's read-outs show).
    const psfLow  = soldPsfList.length >= 4 ? quantileOf(soldPsfList, 0.25) : (soldPsfList.length ? Math.min.apply(null, soldPsfList) : null);
    const psfHigh = soldPsfList.length >= 4 ? quantileOf(soldPsfList, 0.75) : (soldPsfList.length ? Math.max.apply(null, soldPsfList) : null);
    // Months of inventory inside the comp radius: actives divided by the
    // monthly closed-sale pace of the sold window. <5 leans seller, 5-6
    // balanced, >6 leans buyer (standard absorption thresholds).
    const windowMonths = Math.round(CMA.SOLD_WINDOW_DAYS / 30);
    const monthlySoldPace = soldAll.length ? soldAll.length / windowMonths : null;
    const monthsOfInventory = (monthlySoldPace && activeAll.length)
      ? Number((activeAll.length / monthlySoldPace).toFixed(1))
      : null;
    const stats = {
      soldCount: soldAll.length,
      soldMedian: medianOf(soldAll.map(s => s.soldPrice)),
      soldPsfMedian: soldPsfMedian != null ? Math.round(soldPsfMedian) : null,
      soldWindowMonths: windowMonths,
      saleToListMedianPct: medianOf(soldAll.map(s => s.saleToListPct).filter(v => v != null)),
      subjectPsfBand: (psfLow != null && psfHigh != null && subjSqft)
        ? { low: Math.round(psfLow * subjSqft), high: Math.round(psfHigh * subjSqft) }
        : null,
      activeCount: activeAll.length,
      activeMedianAsk: medianOf(activeAll.map(a => a.askPrice)),
      activeMedianDom: medianOf(activeAll.map(a => a.dom).filter(v => v != null)),
      monthsOfInventory,
      marketLean: monthsOfInventory == null ? null
        : (monthsOfInventory < 5 ? "seller" : (monthsOfInventory <= 6 ? "balanced" : "buyer")),
      expiredCount: expiredAll.length,
      expiredMedianAsk: medianOf(expiredAll.map(e => e.lastAsk)),
      expiredMedianDom: medianOf(expiredAll.map(e => e.dom).filter(v => v != null)),
      expiredPremiumPct: medianOf(expiredAll.map(e => e.vsSoldMedianPct).filter(v => v != null))
    };

    return {
      criteria: {
        radiusMi: CMA.RADIUS_MI,
        soldWindowMonths: stats.soldWindowMonths,
        sameType: !!subject.propertyType,
        ranking: "size, distance, beds, baths, age"
      },
      sold, active, expired, stats,
      methodology: "Comps matched on property type, size (within 25% of living area), distance, and age within " + CMA.RADIUS_MI + " mi, most recent closings preferred. Sold set comes from recorded closings; the competition and came-off-unsold sets come from live listing records, with distressed listing types excluded. Adjusted values move each closing to the subject's square footage at the marginal (one-third) local $/sqft, the standard size-adjustment method."
    };
  } catch (err) {
    return null;
  }
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

// Save the valuation lead by POSTing to our own /api/lead (same deployment), so
// all delivery (email, Zapier, FollowUpBoss, phone normalization) stays in one
// place. intent "Home Valuation Lead" maps to a FollowUpBoss Seller Inquiry.
// Best-effort: a failure logs but never affects the valuation response.
async function saveValuationLead(request, contact, addr) {
  try {
    const form = new URLSearchParams();
    form.set("name", contact.name || "");
    form.set("email", contact.email);
    form.set("phone", contact.phone);
    form.set("consent", "yes");
    form.set("intent", "Home Valuation Lead");
    form.set("referral_source", "Home Valuation Gate");
    form.set("source_page", contact.sourcePage || "/value/");
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
    form.set("message", "Lead generated from the /value/ gate (contact collected before the valuation was computed or returned).");
    const leadUrl = new URL("/api/lead", request.url).toString();
    await fetch(leadUrl, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString()
    });
  } catch (e) {
    console.error("VALUATION_LEAD_SAVE_FAILED " + ((e && e.message) || e));
  }
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

  // Accept GET (?address=...) and POST (form or JSON). Contact (name/email/phone/
  // consent) is read ONLY from POST bodies, never from the URL: both for privacy
  // and because the contact gate below requires a POST. A bare GET can never
  // carry contact, so it can never get the numbers.
  let address = "";
  let lat = null, lng = null;
  let contact = { name: "", email: "", phone: "", consent: "", gclid: "", sourcePage: "", pageUrl: "" };

  try {
    if (request.method === "POST") {
      const ctype = request.headers.get("Content-Type") || "";
      if (ctype.includes("application/json")) {
        const body = await request.json();
        address = (body?.address || "").toString().trim();
        lat = numberOrNull(body?.lat ?? body?.latitude);
        lng = numberOrNull(body?.lng ?? body?.longitude);
        contact.name       = (body?.name ?? body?.full_name ?? "").toString().trim();
        contact.email      = (body?.email ?? "").toString().trim();
        contact.phone      = (body?.phone ?? "").toString().trim();
        contact.consent    = (body?.consent ?? "").toString().trim();
        contact.gclid      = (body?.gclid ?? "").toString().trim();
        contact.sourcePage = (body?.source_page ?? "").toString().trim();
        contact.pageUrl    = (body?.page_url ?? "").toString().trim();
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

  // ---- Contact gate: the server-side lock behind the /value/ popup ----
  // The valuation (dollar values, comps, investor metrics) is delivered ONLY to
  // a contact-bearing POST. No email + phone + consent => no compute, no data,
  // 403. This is what actually gates the numbers: the page popup is just the UI;
  // THIS is the enforcement. It cannot be bypassed by hitting the API directly,
  // reading the network tab, or replaying the request, because nothing is ever
  // computed or returned without contact, and obtaining the numbers always saves
  // the lead (below).
  const hasContact = !!(contact.email && contact.phone && contact.consent === "yes");
  if (!hasContact) {
    return json({
      ok: false,
      error: "contact_required",
      message: "Submit your name, email, and phone to generate the valuation."
    }, 403);
  }

  // Fan out: property lookup first (need attributes + coordinates for the
  // comp-targeted AVM, rent, and comp-study calls), then everything else in
  // parallel: AVM + rent + the three comp-study pools (recorded closings,
  // active competition, delisted listings).
  const propertyResult = await lookupProperty(address, apiKey);
  const property = propertyResult?.data || null;

  const subjLat = numberOrNull(property?.latitude)  ?? lat;
  const subjLng = numberOrNull(property?.longitude) ?? lng;
  const canComps = subjLat != null && subjLng != null;
  const noCoords = Promise.resolve({ error: "no_coordinates", data: [] });

  const [avmResult, rentResult, soldResult, activeResult, inactiveResult] = await Promise.all([
    lookupAVM(address, property, apiKey),
    lookupRent(address, property, apiKey),
    canComps ? lookupSoldRecords(subjLat, subjLng, property?.propertyType, apiKey)               : noCoords,
    canComps ? lookupSaleListings(subjLat, subjLng, property?.propertyType, "Active", apiKey)    : noCoords,
    canComps ? lookupSaleListings(subjLat, subjLng, property?.propertyType, "Inactive", apiKey)  : noCoords
  ]);
  const avm  = avmResult?.data  || null;
  const rent = rentResult?.data || null;

  // Property-record fallback: when /properties has no record for the address
  // (a coverage gap, seen live 2026-07-16), the AVM response's subjectProperty
  // carries the same attribute set (address parts, coordinates, type, beds,
  // baths, sqft, lot, year). Use it so the replacement-cost and ARV lenses,
  // the report header, the lead's address components, and the comp study all
  // survive a missing record instead of silently degrading.
  const subjectRecord = property || (avm && avm.subjectProperty) || null;

  let soldR = soldResult, activeR = activeResult, inactiveR = inactiveResult;
  if (!canComps) {
    const fbLat = numberOrNull(subjectRecord?.latitude);
    const fbLng = numberOrNull(subjectRecord?.longitude);
    if (fbLat != null && fbLng != null) {
      [soldR, activeR, inactiveR] = await Promise.all([
        lookupSoldRecords(fbLat, fbLng, subjectRecord?.propertyType, apiKey),
        lookupSaleListings(fbLat, fbLng, subjectRecord?.propertyType, "Active", apiKey),
        lookupSaleListings(fbLat, fbLng, subjectRecord?.propertyType, "Inactive", apiKey)
      ]);
    }
  }
  const cmaLat = numberOrNull(subjectRecord?.latitude)  ?? lat;
  const cmaLng = numberOrNull(subjectRecord?.longitude) ?? lng;

  const marketValue  = numberOrNull(avm?.price);
  const marketLow    = numberOrNull(avm?.priceRangeLow);
  const marketHigh   = numberOrNull(avm?.priceRangeHigh);
  const monthlyRent  = numberOrNull(rent?.rent);

  const subjectSqft  = numberOrNull(subjectRecord?.squareFootage);
  const replacement  = computeReplacementCost(subjectRecord, marketValue);
  const arv          = computeARV(avm, subjectRecord);
  const assessor     = pickAssessorValue(subjectRecord);
  const compMedian   = compMedianPrice(avm);
  const triangulated = computeTriangulated(marketValue, arv?.value, compMedian);
  const investor     = await computeInvestorMetrics(marketValue, monthlyRent, request.url);
  const wholesale    = computeWholesaleOffer(arv?.value, subjectSqft);
  const comps        = trimComps(avm);
  const subjectPsf   = (marketValue && subjectSqft) ? Math.round(marketValue / subjectSqft) : null;
  const cma          = assembleCMA(
    subjectRecord, cmaLat, cmaLng,
    addressKey(subjectRecord?.formattedAddress || address),
    avm, soldR.data, activeR.data, inactiveR.data
  );

  // Getting the valuation IS submitting the lead. Every contact-bearing request
  // that reaches this point saves the lead (with the Rentcast-parsed address
  // components), so there is no way to obtain the numbers without Joshua getting
  // the lead. Best-effort + decoupled: it never blocks or fails the response.
  context.waitUntil(saveValuationLead(request, contact, {
    fullAddress: subjectRecord?.formattedAddress || address,
    street: subjectRecord?.addressLine1 || "",
    city:   subjectRecord?.city || "",
    state:  subjectRecord?.state || "",
    zip:    subjectRecord?.zipCode || "",
    lat, lng
  }));

  const anyData = marketValue || replacement?.value || arv?.value || assessor?.value;

  return json({
    ok: !!anyData,
    address: {
      input: address,
      lat, lng,
      formatted: subjectRecord?.formattedAddress || address,
      street:    subjectRecord?.addressLine1 || null,
      city:      subjectRecord?.city || null,
      state:     subjectRecord?.state || null,
      zip:       subjectRecord?.zipCode || null,
      county:    subjectRecord?.county || null
    },
    property: subjectRecord ? {
      propertyType:  subjectRecord.propertyType || null,
      bedrooms:      numberOrNull(subjectRecord.bedrooms),
      bathrooms:     numberOrNull(subjectRecord.bathrooms),
      squareFootage: numberOrNull(subjectRecord.squareFootage),
      lotSize:       numberOrNull(subjectRecord.lotSize),
      yearBuilt:     numberOrNull(subjectRecord.yearBuilt),
      lastSalePrice: numberOrNull(subjectRecord.lastSalePrice),
      lastSaleDate:  subjectRecord.lastSaleDate || null
    } : null,
    systems: {
      marketAVM: marketValue ? {
        label: "Market AVM",
        value: marketValue,
        rangeLow:  marketLow,
        rangeHigh: marketHigh,
        psf: subjectPsf,
        compsCount: Array.isArray(avm?.comparables) ? avm.comparables.length : 0,
        source: "Rentcast AVM",
        methodology: "Statistical model trained on recent local sales of properties matching beds, baths, sqft, age, and lot. Updated daily as new sales close."
      } : null,
      assessor: assessor ? { label: "Tax assessor value", ...assessor } : null,
      replacementCost: replacement ? { label: "Replacement cost", ...replacement } : null,
      arv: arv ? { label: "Investor ARV (after repair value)", ...arv } : null,
      triangulated: triangulated ? { label: "True Market Value", ...triangulated } : null
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
    comps,
    compMedian,
    cma,
    diagnostics: {
      propertyError: propertyResult?.error || null,
      avmError:      avmResult?.error || null,
      rentError:     rentResult?.error || null,
      soldError:     soldR?.error || null,
      activeError:   activeR?.error || null,
      inactiveError: inactiveR?.error || null
    },
    source: "Rentcast Property API + Drozq replacement cost model",
    sourceUrl: "https://www.rentcast.io/api",
    fetchedAt: new Date().toISOString()
  });
}
