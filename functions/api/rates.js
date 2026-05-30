// /api/rates - proxy + edge cache for FRED (Federal Reserve Economic Data).
//
// Returns the latest observation plus a ~1-year history per series so the
// /rates/ page can render sparklines, year-over-year deltas, and a "what the
// rate has done this year" story.
//
// Benchmarks (Freddie Mac PMMS + Treasury + Fed, the macro story):
//   - MORTGAGE30US   (weekly Thursdays) -> 30-year fixed mortgage
//   - MORTGAGE15US   (weekly Thursdays) -> 15-year fixed mortgage
//   - DGS10          (daily business)   -> 10-year Treasury yield
//   - FEDFUNDS       (monthly)          -> Federal funds rate
//
// Rates by loan program (Optimal Blue Mortgage Market Indices, OBMMI -- daily
// locked-rate based, the actual programs a SoCal buyer shops). All hosted on
// FRED under the same key; verified current (latest obs 2026-05-28, daily
// business-day cadence). See the [[fred-mortgage5us-discontinued]] discipline:
// recheck latest-observation date before trusting any FRED series.
//   - OBMMIC30YF     (daily) -> 30-year conforming (standard)
//   - OBMMIJUMBO30YF (daily) -> 30-year jumbo / high balance
//   - OBMMIFHA30YF   (daily) -> 30-year FHA
//   - OBMMIVA30YF    (daily) -> 30-year VA
//   - OBMMIUSDA30YF  (daily) -> 30-year USDA
//   - OBMMIC15YF     (daily) -> 15-year conforming
//
// Env var required:
//   FRED_API_KEY -- get one at https://fred.stlouisfed.org/docs/api/api_key.html
//
// Edge-cached for 1 hour. Free FRED tier is 120 req/min, ten requests per
// cache miss is trivially fine. Returns 503 with structured error when the
// key is missing so /rates/ degrades gracefully.

const FRED = "https://api.stlouisfed.org/fred/series/observations";

// Per-cadence observation limits sized to cover roughly one year of history.
const SERIES = [
  // Macro benchmarks (Freddie Mac PMMS + Treasury + Fed).
  { key: "rate30y",     id: "MORTGAGE30US", label: "30-year fixed mortgage",  unit: "%", cadence: "weekly",  limit: 53  },
  { key: "rate15y",     id: "MORTGAGE15US", label: "15-year fixed mortgage",  unit: "%", cadence: "weekly",  limit: 53  },
  { key: "treasury10y", id: "DGS10",        label: "10-year Treasury yield",  unit: "%", cadence: "daily",   limit: 260 },
  { key: "fedFunds",    id: "FEDFUNDS",     label: "Federal funds rate",      unit: "%", cadence: "monthly", limit: 13  },
  // Rates by loan program (Optimal Blue OBMMI, daily). limit ~260 business days ~= 1 year.
  { key: "conforming30", id: "OBMMIC30YF",     label: "30-year conforming",          unit: "%", cadence: "daily", limit: 260, provider: "Optimal Blue" },
  { key: "jumbo30",      id: "OBMMIJUMBO30YF", label: "30-year jumbo / high balance", unit: "%", cadence: "daily", limit: 260, provider: "Optimal Blue" },
  { key: "fha30",        id: "OBMMIFHA30YF",   label: "30-year FHA",                  unit: "%", cadence: "daily", limit: 260, provider: "Optimal Blue" },
  { key: "va30",         id: "OBMMIVA30YF",    label: "30-year VA",                   unit: "%", cadence: "daily", limit: 260, provider: "Optimal Blue" },
  { key: "usda30",       id: "OBMMIUSDA30YF",  label: "30-year USDA",                 unit: "%", cadence: "daily", limit: 260, provider: "Optimal Blue" },
  { key: "conforming15", id: "OBMMIC15YF",     label: "15-year conforming",           unit: "%", cadence: "daily", limit: 260, provider: "Optimal Blue" }
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

function summarize(observations) {
  // observations come from FRED sorted desc (newest first).
  const cleaned = observations
    .map((o) => ({ date: o.date, value: parseValue(o.value) }))
    .filter((o) => o.value != null);

  if (cleaned.length === 0) {
    return { latest: { value: null, date: null }, previous: { value: null, date: null },
             yearAgo: { value: null, date: null }, history: [], delta: null, deltaYoY: null };
  }

  const latest = cleaned[0];
  const previous = cleaned[1] || { value: null, date: null };
  // The last item in the desc-sorted list is the oldest we have (~1 year back).
  const yearAgo = cleaned[cleaned.length - 1] || { value: null, date: null };

  const delta = previous.value != null
    ? Number((latest.value - previous.value).toFixed(2))
    : null;
  const deltaYoY = yearAgo.value != null && cleaned.length > 4
    ? Number((latest.value - yearAgo.value).toFixed(2))
    : null;

  // For sparkline rendering, return the cleaned history sorted ascending so
  // the consumer can render left-to-right without reversing.
  const history = cleaned.slice().reverse();

  return { latest, previous, yearAgo, history, delta, deltaYoY };
}

async function fetchSeries(spec, apiKey) {
  const url = `${FRED}?series_id=${encodeURIComponent(spec.id)}&api_key=${encodeURIComponent(apiKey)}&file_type=json&sort_order=desc&limit=${spec.limit}`;
  try {
    const resp = await fetch(url, {
      cf: { cacheTtl: 3600, cacheEverything: true }
    });
    if (!resp.ok) {
      return [spec.key, {
        seriesId: spec.id, label: spec.label, unit: spec.unit, cadence: spec.cadence, provider: spec.provider || null,
        latest: { value: null, date: null }, previous: { value: null, date: null },
        yearAgo: { value: null, date: null }, history: [], delta: null, deltaYoY: null,
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
      provider: spec.provider || null,
      ...summary
    }];
  } catch (err) {
    return [spec.key, {
      seriesId: spec.id, label: spec.label, unit: spec.unit, cadence: spec.cadence,
      latest: { value: null, date: null }, previous: { value: null, date: null },
      yearAgo: { value: null, date: null }, history: [], delta: null, deltaYoY: null,
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
