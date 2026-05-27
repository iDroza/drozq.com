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

const SERIES = [
  // Tier 1
  { key: "hpiLA",         id: "LXXRSA",        label: "LA Metro Home Price Index",         unit: "index",     cadence: "monthly",   limit: 36, tier: 1 },
  { key: "hpiSD",         id: "SDXRSA",        label: "San Diego Metro Home Price Index",  unit: "index",     cadence: "monthly",   limit: 36, tier: 1 },
  { key: "hpiCA",         id: "CASTHPI",       label: "California Statewide HPI",          unit: "index",     cadence: "quarterly", limit: 20, tier: 1 },
  // Tier 3
  { key: "supplyMonths",  id: "MSACSR",        label: "Months of Supply, New Homes",       unit: "months",    cadence: "monthly",   limit: 36, tier: 3 },
  { key: "existingSales", id: "EXHOSLUSM495S", label: "Existing Home Sales",               unit: "thousands", cadence: "monthly",   limit: 36, tier: 3 },
  { key: "affordIdx",     id: "FIXHAI",        label: "Housing Affordability Index",       unit: "index",     cadence: "monthly",   limit: 36, tier: 3 },
  { key: "unemployment",  id: "UNRATE",        label: "US Unemployment Rate",              unit: "%",         cadence: "monthly",   limit: 36, tier: 3 },
  // Tier 2
  { key: "rate5_1ARM",    id: "MORTGAGE5US",   label: "5/1 ARM Rate",                      unit: "%",         cadence: "weekly",    limit: 52, tier: 2 }
];

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

function summarize(observations) {
  const cleaned = observations
    .map((o) => ({ date: o.date, value: parseValue(o.value) }))
    .filter((o) => o.value != null);

  if (cleaned.length === 0) {
    return {
      latest: { value: null, date: null },
      previous: { value: null, date: null },
      yearAgo: { value: null, date: null },
      history: [],
      delta: null, deltaPct: null,
      deltaYoY: null, deltaYoYPct: null
    };
  }

  const latest = cleaned[0];
  const previous = cleaned[1] || { value: null, date: null };
  const yearAgo = cleaned.length > 4 ? cleaned[cleaned.length - 1] : { value: null, date: null };

  return {
    latest,
    previous,
    yearAgo,
    history: cleaned.slice().reverse(),
    delta:       abs(latest.value, previous.value),
    deltaPct:    pct(latest.value, previous.value),
    deltaYoY:    abs(latest.value, yearAgo.value),
    deltaYoYPct: pct(latest.value, yearAgo.value)
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
    const summary = summarize(obs);
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
