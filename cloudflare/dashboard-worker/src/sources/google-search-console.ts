import {
  readGoogleSearchConsoleConfig,
  type GoogleSearchConsoleConfig,
} from "../config";
import { exchangeRefreshToken } from "../lib/google-auth";
import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import { requireCount, requireNonnegativeNumber } from "../lib/numeric";
import { fetchWithRetry, UpstreamRequestError } from "../lib/retry";
import type {
  DashboardEnv,
  DashboardSnapshot,
  ErrorCategory,
  GoogleSearchConsoleMetricResults,
  MetricFetchResult,
  RuntimeDependencies,
} from "../types";

const SEARCH_ANALYTICS_BASE_URL =
  "https://www.googleapis.com/webmasters/v3/sites";
const SEARCH_CONSOLE_CACHE_KEY = "dashboard:search_console:aggregate:v1";

export interface SearchConsoleAggregate {
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

interface SearchConsoleCache {
  version: 1;
  configHash: string;
  fetchedAt: string;
  activeRealty: SearchConsoleAggregate;
  jt: SearchConsoleAggregate;
}

function validSiteUrl(value: string): boolean {
  return value.length <= 2_048 &&
    (/^sc-domain:[a-z0-9.-]+$/iu.test(value) || /^https?:\/\//iu.test(value));
}

function validConfig(config: GoogleSearchConsoleConfig): boolean {
  return config.clientId !== "" &&
    config.clientSecret !== "" &&
    config.refreshToken !== "" &&
    validSiteUrl(config.activeRealtySiteUrl) &&
    validSiteUrl(config.jtSiteUrl);
}

function validAggregate(value: unknown): value is SearchConsoleAggregate {
  if (!isRecord(value)) {
    return false;
  }
  const clicks = value["clicks"];
  const impressions = value["impressions"];
  const ctr = value["ctr"];
  const position = value["position"];
  return typeof clicks === "number" && Number.isSafeInteger(clicks) && clicks >= 0 &&
    typeof impressions === "number" && Number.isSafeInteger(impressions) && impressions > 0 &&
    typeof ctr === "number" && Number.isFinite(ctr) && ctr >= 0 && ctr <= 1 &&
    typeof position === "number" && Number.isFinite(position) &&
    position > 0 && position <= 1_000;
}

export function parseSearchConsoleAggregate(
  payload: unknown,
): SearchConsoleAggregate {
  if (!isRecord(payload) || !Array.isArray(payload["rows"])) {
    throw new UpstreamRequestError("schema");
  }
  const rows = payload["rows"];
  if (rows.length === 0) {
    throw new UpstreamRequestError("no_data");
  }
  if (rows.length !== 1 || !isRecord(rows[0])) {
    throw new UpstreamRequestError("schema");
  }
  const row = rows[0];
  const aggregate = {
    clicks: requireCount(row["clicks"], "search_console_clicks"),
    impressions: requireCount(
      row["impressions"],
      "search_console_impressions",
    ),
    ctr: requireNonnegativeNumber(row["ctr"], "search_console_ctr"),
    position: requireNonnegativeNumber(
      row["position"],
      "search_console_position",
    ),
  };
  if (!validAggregate(aggregate)) {
    throw new UpstreamRequestError("schema");
  }
  return aggregate;
}

async function configHash(config: GoogleSearchConsoleConfig): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(
      `${config.activeRealtySiteUrl}\n${config.jtSiteUrl}`,
    ),
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function parseCache(
  value: unknown,
  expectedHash: string,
  now: Date,
  refreshMs: number,
): SearchConsoleCache | null {
  if (
    !isRecord(value) ||
    value["version"] !== 1 ||
    value["configHash"] !== expectedHash ||
    typeof value["fetchedAt"] !== "string" ||
    !Number.isFinite(Date.parse(value["fetchedAt"])) ||
    now.getTime() - Date.parse(value["fetchedAt"]) < 0 ||
    now.getTime() - Date.parse(value["fetchedAt"]) > refreshMs ||
    !validAggregate(value["activeRealty"]) ||
    !validAggregate(value["jt"])
  ) {
    return null;
  }
  return {
    version: 1,
    configHash: expectedHash,
    fetchedAt: value["fetchedAt"],
    activeRealty: value["activeRealty"],
    jt: value["jt"],
  };
}

async function loadCache(
  env: DashboardEnv,
  expectedHash: string,
  now: Date,
  refreshMs: number,
): Promise<SearchConsoleCache | null> {
  try {
    const stored = await env.DASHBOARD_KV.get(SEARCH_CONSOLE_CACHE_KEY);
    return stored === null
      ? null
      : parseCache(JSON.parse(stored) as unknown, expectedHash, now, refreshMs);
  } catch {
    console.warn(JSON.stringify({
      source: "google_search_console_cache",
      category: "storage",
      status: null,
    }));
    return null;
  }
}

async function querySearchConsole(
  accessToken: string,
  siteUrl: string,
  reportingPeriod: DashboardSnapshot["rolling90DayPeriod"],
  source: string,
  dependencies: RuntimeDependencies,
): Promise<SearchConsoleAggregate> {
  const endpoint = `${SEARCH_ANALYTICS_BASE_URL}/${encodeURIComponent(siteUrl)}/searchAnalytics/query`;
  const response = await fetchWithRetry(
    endpoint,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        startDate: reportingPeriod.startDate,
        endDate: reportingPeriod.endDate,
        type: "web",
        aggregationType: "byProperty",
        dataState: "all",
        rowLimit: 1,
      }),
    },
    {
      source,
      fetcher: dependencies.fetcher,
      sleep: dependencies.sleep,
    },
  );
  if (!response.ok) {
    throw classifyHttpStatus(response.status);
  }
  return parseSearchConsoleAggregate(await readBoundedJson(response));
}

function okResult(
  value: number,
  started: number,
  observedAt: string,
): MetricFetchResult {
  return {
    kind: "ok",
    value,
    observedAt,
    durationMs: Date.now() - started,
    responseStatus: 200,
  };
}

function errorResult(error: unknown, started: number): MetricFetchResult {
  const category: ErrorCategory = error instanceof UpstreamRequestError
    ? error.category
    : error instanceof RangeError
      ? "schema"
      : "unexpected";
  return {
    kind: "error",
    category,
    durationMs: Date.now() - started,
    responseStatus:
      error instanceof UpstreamRequestError ? error.responseStatus : null,
  };
}

function unavailable(kind: "unconfigured" | "error", started: number): MetricFetchResult {
  return kind === "unconfigured"
    ? { kind, durationMs: Date.now() - started, responseStatus: null }
    : {
        kind,
        category: "unexpected",
        durationMs: Date.now() - started,
        responseStatus: null,
      };
}

function siteResults(
  prefix: "activeRealty" | "jt",
  aggregate: SearchConsoleAggregate,
  started: number,
  observedAt: string,
): Pick<GoogleSearchConsoleMetricResults, keyof GoogleSearchConsoleMetricResults> {
  const results: Partial<GoogleSearchConsoleMetricResults> = {};
  results[`${prefix}ClicksRolling90d`] = okResult(
    aggregate.clicks,
    started,
    observedAt,
  );
  results[`${prefix}ImpressionsRolling90d`] = okResult(
    aggregate.impressions,
    started,
    observedAt,
  );
  results[`${prefix}CtrRolling90d`] = okResult(
    aggregate.ctr,
    started,
    observedAt,
  );
  results[`${prefix}PositionRolling90d`] = okResult(
    aggregate.position,
    started,
    observedAt,
  );
  return results as Pick<
    GoogleSearchConsoleMetricResults,
    keyof GoogleSearchConsoleMetricResults
  >;
}

function allUnavailable(
  kind: "unconfigured" | "error",
  started: number,
): GoogleSearchConsoleMetricResults {
  const value = (): MetricFetchResult => unavailable(kind, started);
  return {
    activeRealtyClicksRolling90d: value(),
    activeRealtyImpressionsRolling90d: value(),
    activeRealtyCtrRolling90d: value(),
    activeRealtyPositionRolling90d: value(),
    jtClicksRolling90d: value(),
    jtImpressionsRolling90d: value(),
    jtCtrRolling90d: value(),
    jtPositionRolling90d: value(),
  };
}

function siteError(
  prefix: "activeRealty" | "jt",
  error: unknown,
  started: number,
): Partial<GoogleSearchConsoleMetricResults> {
  const result = errorResult(error, started);
  return {
    [`${prefix}ClicksRolling90d`]: result,
    [`${prefix}ImpressionsRolling90d`]: result,
    [`${prefix}CtrRolling90d`]: result,
    [`${prefix}PositionRolling90d`]: result,
  };
}

export async function fetchGoogleSearchConsoleMetrics(
  env: DashboardEnv,
  reportingPeriod: DashboardSnapshot["rolling90DayPeriod"],
  dependencies: RuntimeDependencies = {},
): Promise<GoogleSearchConsoleMetricResults> {
  const started = Date.now();
  const config = readGoogleSearchConsoleConfig(env);
  if (!validConfig(config)) {
    return allUnavailable("unconfigured", started);
  }

  const now = dependencies.now ?? new Date();
  const hash = await configHash(config);
  const cached = await loadCache(env, hash, now, config.refreshMs);
  if (cached !== null) {
    return {
      ...siteResults("activeRealty", cached.activeRealty, started, cached.fetchedAt),
      ...siteResults("jt", cached.jt, started, cached.fetchedAt),
    };
  }

  let accessToken: string;
  try {
    accessToken = await exchangeRefreshToken(
      {
        clientId: config.clientId,
        clientSecret: config.clientSecret,
        refreshToken: config.refreshToken,
      },
      dependencies,
      "google_search_console_oauth",
    );
  } catch (error) {
    const result = errorResult(error, started);
    return {
      activeRealtyClicksRolling90d: result,
      activeRealtyImpressionsRolling90d: result,
      activeRealtyCtrRolling90d: result,
      activeRealtyPositionRolling90d: result,
      jtClicksRolling90d: result,
      jtImpressionsRolling90d: result,
      jtCtrRolling90d: result,
      jtPositionRolling90d: result,
    };
  }

  const [activeSettled, jtSettled] = await Promise.allSettled([
    querySearchConsole(
      accessToken,
      config.activeRealtySiteUrl,
      reportingPeriod,
      "google_search_console_active_realty",
      dependencies,
    ),
    querySearchConsole(
      accessToken,
      config.jtSiteUrl,
      reportingPeriod,
      "google_search_console_jt",
      dependencies,
    ),
  ]);
  const observedAt = now.toISOString();
  const results: Partial<GoogleSearchConsoleMetricResults> = {
    ...(activeSettled.status === "fulfilled"
      ? siteResults("activeRealty", activeSettled.value, started, observedAt)
      : siteError("activeRealty", activeSettled.reason, started)),
    ...(jtSettled.status === "fulfilled"
      ? siteResults("jt", jtSettled.value, started, observedAt)
      : siteError("jt", jtSettled.reason, started)),
  };

  if (
    activeSettled.status === "fulfilled" &&
    jtSettled.status === "fulfilled"
  ) {
    try {
      await env.DASHBOARD_KV.put(
        SEARCH_CONSOLE_CACHE_KEY,
        JSON.stringify({
          version: 1,
          configHash: hash,
          fetchedAt: observedAt,
          activeRealty: activeSettled.value,
          jt: jtSettled.value,
        } satisfies SearchConsoleCache),
        { expirationTtl: 48 * 60 * 60 },
      );
    } catch {
      console.warn(JSON.stringify({
        source: "google_search_console_cache",
        category: "storage",
        status: null,
      }));
    }
  }
  return results as GoogleSearchConsoleMetricResults;
}
