// /api/rates - proxy + edge cache for FRED (Federal Reserve Economic Data).
// Returns the latest observation (and previous, for delta) for a small set of
// rate series that frame US housing finance: 30y / 15y fixed mortgages, the
// 10y Treasury yield (the canonical leading indicator for mortgage rates),
// and the Fed Funds rate.
//
// Env var required:
//   FRED_API_KEY -- get one at https://fred.stlouisfed.org/docs/api/api_key.html
//
// Edge-cached for 1 hour. FRED publishes the weekly PMMS mortgage series
// every Thursday at 12 ET, so 1h cache keeps the page fresh without hammering
// FRED. If FRED_API_KEY is missing, returns 503 with a structured error so
// the page can show a graceful "data unavailable" state.

const FRED = "https://api.stlouisfed.org/fred/series/observations";

const SERIES = [
  { key: "rate30y",     id: "MORTGAGE30US", label: "30-year fixed mortgage",  unit: "%", cadence: "weekly" },
  { key: "rate15y",     id: "MORTGAGE15US", label: "15-year fixed mortgage",  unit: "%", cadence: "weekly" },
  { key: "treasury10y", id: "DGS10",        label: "10-year Treasury yield",  unit: "%", cadence: "daily"  },
  { key: "fedFunds",    id: "FEDFUNDS",     label: "Federal funds rate",      unit: "%", cadence: "monthly" }
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

function parseObs(obs) {
  if (!obs || obs.value === "." || obs.value === undefined || obs.value === null) {
    return { value: null, date: obs?.date || null };
  }
  const v = parseFloat(obs.value);
  return {
    value: Number.isFinite(v) ? v : null,
    date: obs.date || null
  };
}

async function fetchSeries(spec, apiKey) {
  const url = `${FRED}?series_id=${encodeURIComponent(spec.id)}&api_key=${encodeURIComponent(apiKey)}&file_type=json&sort_order=desc&limit=2`;
  try {
    const resp = await fetch(url, {
      cf: { cacheTtl: 3600, cacheEverything: true }
    });
    if (!resp.ok) {
      return [spec.key, {
        ...spec,
        latest: null, previous: null, delta: null,
        error: `fred_http_${resp.status}`
      }];
    }
    const data = await resp.json();
    const obs = Array.isArray(data?.observations) ? data.observations : [];
    const latest = parseObs(obs[0]);
    const previous = parseObs(obs[1]);
    const delta = (latest.value != null && previous.value != null)
      ? Number((latest.value - previous.value).toFixed(2))
      : null;
    return [spec.key, {
      seriesId: spec.id,
      label: spec.label,
      unit: spec.unit,
      cadence: spec.cadence,
      latest,
      previous,
      delta
    }];
  } catch (err) {
    return [spec.key, {
      ...spec,
      latest: null, previous: null, delta: null,
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
    source: "Federal Reserve Economic Data (FRED), St. Louis Fed"
  });
}
