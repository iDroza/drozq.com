// /api/prices - second FRED-backed data product (sibling of /api/rates).
//
// Returns California-focused home-price indices + national market signals
// + a single rate complement (5/1 ARM). All eight series come from FRED
// with ~1 year of history for sparklines and YoY context.
//
// Series:
//   Tier 1 -- California home prices:
//     LXXRSA       Case-Shiller Home Price Index, Los Angeles Metro     (monthly)
//     SDXRSA       Case-Shiller Home Price Index, San Diego Metro       (monthly)
//     CASTHPI      FHFA All-Transactions House Price Index, California  (quarterly)
//   Tier 3 -- broader market signals:
//     MSACSR          Monthly Supply of New Houses, United States       (monthly)
//     EXHOSLUSM495S   Existing Home Sales, United States                (monthly, SAAR thousands)
//     FIXHAI          NAR Housing Affordability Composite Index         (monthly)
//     UNRATE          US Unemployment Rate                              (monthly)
//   Tier 2 -- cost-of-money complement:
//     MORTGAGE5US  5/1 Adjustable Rate Mortgage Average, US             (weekly)
//
// Env: requires FRED_API_KEY (already set on this Cloudflare Pages project).
// Cache: edge-cached 1h via cf.cacheTtl + cache-control headers.

const FRED = "https://api.stlouisfed.org/fred/series/observations";

// NOTE: We dropped the original Tier 2 series (MORTGAGE5US, the 5/1 ARM rate)
// because Freddie Mac discontinued it in their PMMS survey in November 2022.
// FRED still serves the series but every observation past 2022-11-10 is null.
// If a replacement ARM benchmark surfaces on FRED we can wire it back in here.
// Tier 1 limits are set to ~10 years so the page can render long-term
// appreciation (5y + 10y CAGR) for the California home price indices. The
// extra payload is small (each obs is one date + one number) and the response
// is edge-cached for 1h so the cost is negligible. Tier 3 limits stay at 36
// (3 years, monthly) -- enough for sparkline + YoY context.
//
// FIXHAI uses a wider limit because the NAR composite index has historically
// had monthly gaps in FRED's mirror. Pulling 60 obs typically gives 24+
// non-null points, enough to reliably resolve YoY at offset=12.
const SERIES = [
  // Tier 1 -- California home prices (10y of history for CAGR)
  { key: "hpiLA",         id: "LXXRSA",        label: "LA Metro Home Price Index",         unit: "index",     cadence: "monthly",   limit: 121, tier: 1 },
  { key: "hpiSD",         id: "SDXRSA",        label: "San Diego Metro Home Price Index",  unit: "index",     cadence: "monthly",   limit: 121, tier: 1 },
  { key: "hpiCA",         id: "CASTHPI",       label: "California Statewide HPI",          unit: "index",     cadence: "quarterly", limit:  41, tier: 1 },
  // Tier 3 -- broader market signals
  { key: "supplyMonths",  id: "MSACSR",        label: "Months of Supply, New Homes",       unit: "months",    cadence: "monthly",   limit:  36, tier: 3 },
  { key: "existingSales", id: "EXHOSLUSM495S", label: "Existing Home Sales",               unit: "thousands", cadence: "monthly",   limit:  36, tier: 3 },
  { key: "affordIdx",     id: "FIXHAI",        label: "Housing Affordability Index",       unit: "index",     cadence: "monthly",   limit:  60, tier: 3 },
  { key: "unemployment",  id: "UNRATE",        label: "US Unemployment Rate",              unit: "%",         cadence: "monthly",   limit:  36, tier: 3 }
];

// Cadence -> index in the descending observation list at N years prior to
// latest. Used for honest YoY/5y/10y labels regardless of how much history
// the limit pulls.
const YEAR_AGO_OFFSET = {
  daily:     252,   // approx business days/year
  weekly:     52,
  monthly:    12,
  quarterly:   4
};
const FIVE_YEAR_OFFSET = {
  daily:    1260,
  weekly:    260,
  monthly:    60,
  quarterly:  20
};
const TEN_YEAR_OFFSET = {
  daily:    2520,
  weekly:    520,
  monthly:   120,
  quarterly:  40
};

const json = (body, status = 200, extra = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=UTF-8",
      "cache-control": status === 200
        ? "public, max-age=3600, s-maxage=3600"
        : "no-store",
      ...extra
    }
  });

function parseValue(v) {
  if (v === "." || v === undefined || v === null) return null;
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : null;
}

function pct(a, b) {
  if (a == null || b == null || b === 0 || !Number.isFinite(a) || !Number.isFinite(b)) return null;
  return Number((((a - b) / b) * 100).toFixed(2));
}

function abs(a, b) {
  if (a == null || b == null || !Number.isFinite(a) || !Number.isFinite(b)) return null;
  return Number((a - b).toFixed(2));
}

function cagr(latestValue, pastValue, years) {
  if (latestValue == null || pastValue == null || pastValue <= 0 || years <= 0) return null;
  if (!Number.isFinite(latestValue) || !Number.isFinite(pastValue)) return null;
  const r = Math.pow(latestValue / pastValue, 1 / years) - 1;
  if (!Number.isFinite(r)) return null;
  return Number((r * 100).toFixed(2));
}

function pickAt(cleaned, offsetMap, cadence) {
  if (offsetMap == null) return { value: null, date: null };
  const offset = offsetMap[cadence];
  if (offset == null) return { value: null, date: null };
  return cleaned[offset] || { value: null, date: null };
}

function summarize(observations, spec) {
  const cleaned = observations
    .map((o) => ({ date: o.date, value: parseValue(o.value) }))
    .filter((o) => o.value != null);

  const empty = {
    latest: { value: null, date: null },
    previous: { value: null, date: null },
    yearAgo: { value: null, date: null },
    fiveYearAgo: { value: null, date: null },
    tenYearAgo: { value: null, date: null },
    history: [],
    delta: null, deltaPct: null,
    deltaYoY: null, deltaYoYPct: null,
    cagr5y: null, cagr10y: null
  };

  if (cleaned.length === 0) return empty;

  const latest = cleaned[0];
  const previous = cleaned[1] || { value: null, date: null };
  const yearAgo     = pickAt(cleaned, YEAR_AGO_OFFSET,  spec.cadence);
  const fiveYearAgo = pickAt(cleaned, FIVE_YEAR_OFFSET, spec.cadence);
  const tenYearAgo  = pickAt(cleaned, TEN_YEAR_OFFSET,  spec.cadence);

  return {
    latest,
    previous,
    yearAgo,
    fiveYearAgo,
    tenYearAgo,
    history: cleaned.slice().reverse(),
    delta:       abs(latest.value, previous.value),
    deltaPct:    pct(latest.value, previous.value),
    deltaYoY:    abs(latest.value, yearAgo.value),
    deltaYoYPct: pct(latest.value, yearAgo.value),
    cagr5y:      cagr(latest.value, fiveYearAgo.value, 5),
    cagr10y:     cagr(latest.value, tenYearAgo.value, 10)
  };
}

async function fetchSeries(spec, apiKey) {
  const url = `${FRED}?series_id=${encodeURIComponent(spec.id)}&api_key=${encodeURIComponent(apiKey)}&file_type=json&sort_order=desc&limit=${spec.limit}`;
  try {
    const resp = await fetch(url, { cf: { cacheTtl: 3600, cacheEverything: true } });
    if (!resp.ok) {
      return [spec.key, {
        seriesId: spec.id, label: spec.label, unit: spec.unit, cadence: spec.cadence, tier: spec.tier,
        latest: { value: null, date: null }, previous: { value: null, date: null },
        yearAgo: { value: null, date: null }, history: [],
        delta: null, deltaPct: null, deltaYoY: null, deltaYoYPct: null,
        error: `fred_http_${resp.status}`
      }];
    }
    const data = await resp.json();
    const obs = Array.isArray(data?.observations) ? data.observations : [];
    const summary = summarize(obs, spec);
    return [spec.key, {
      seriesId: spec.id,
      label: spec.label,
      unit: spec.unit,
      cadence: spec.cadence,
      tier: spec.tier,
      ...summary
    }];
  } catch (err) {
    return [spec.key, {
      seriesId: spec.id, label: spec.label, unit: spec.unit, cadence: spec.cadence, tier: spec.tier,
      latest: { value: null, date: null }, previous: { value: null, date: null },
      yearAgo: { value: null, date: null }, history: [],
      delta: null, deltaPct: null, deltaYoY: null, deltaYoYPct: null,
      error: `fetch_failed`
    }];
  }
}

export async function onRequest(context) {
  const apiKey = context.env && context.env.FRED_API_KEY;
  if (!apiKey) {
    return json({
      ok: false,
      error: "fred_api_key_missing",
      message: "Set FRED_API_KEY in Cloudflare Pages environment variables."
    }, 503);
  }

  const results = await Promise.all(SERIES.map((s) => fetchSeries(s, apiKey)));
  const series = Object.fromEntries(results);

  const dates = Object.values(series)
    .map((s) => s && s.latest && s.latest.date)
    .filter(Boolean)
    .sort();
  const lastUpdated = dates.length ? dates[dates.length - 1] : null;
  const anyData = Object.values(series).some((s) => s && s.latest && s.latest.value != null);

  return json({
    ok: anyData,
    series,
    lastUpdated,
    fetchedAt: new Date().toISOString(),
    source: "Federal Reserve Economic Data (FRED), St. Louis Fed",
    sourceUrl: "https://fred.stlouisfed.org/"
  });
}
