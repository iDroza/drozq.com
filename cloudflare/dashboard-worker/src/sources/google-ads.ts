import { readGoogleAdsConfig, type GoogleAdsConfig } from "../config";
import { exchangeRefreshToken } from "../lib/google-auth";
import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import {
  requireNonnegativeNumber,
  requireSpend,
} from "../lib/numeric";
import { fetchWithRetry, UpstreamRequestError } from "../lib/retry";
import type {
  DashboardEnv,
  DashboardSnapshot,
  ErrorCategory,
  GoogleAdsMetricResults,
  MetricFetchResult,
  RuntimeDependencies,
} from "../types";

const MAX_PAGES = 100;

export interface ConversionActionCatalogItem {
  name: string;
  status: string;
  type: string;
}

export const CONVERSION_ACTION_CATALOG_QUERY = `
SELECT
  conversion_action.name,
  conversion_action.status,
  conversion_action.type
FROM conversion_action
WHERE conversion_action.status != 'REMOVED'
ORDER BY conversion_action.name
`.trim();

export function buildSpendQuery(
  reportingPeriod: DashboardSnapshot["reportingPeriod"],
): string {
  return `
SELECT
  metrics.cost_micros
FROM customer
WHERE segments.date BETWEEN '${reportingPeriod.startDate}' AND '${reportingPeriod.endDate}'
`.trim();
}

export function buildLeadQuery(
  reportingPeriod: DashboardSnapshot["reportingPeriod"],
): string {
  return `
SELECT
  segments.conversion_action_name,
  metrics.conversions
FROM customer
WHERE segments.date BETWEEN '${reportingPeriod.startDate}' AND '${reportingPeriod.endDate}'
`.trim();
}

function parseMicros(value: unknown): bigint {
  if (typeof value === "bigint") {
    if (value < 0n) {
      throw new UpstreamRequestError("schema");
    }
    return value;
  }
  if (typeof value === "number" && Number.isSafeInteger(value) && value >= 0) {
    return BigInt(value);
  }
  if (typeof value === "string" && /^\d+$/u.test(value)) {
    return BigInt(value);
  }
  throw new UpstreamRequestError("schema");
}

export function costMicrosToUsd(value: unknown): number {
  const micros = parseMicros(value);
  const whole = micros / 1_000_000n;
  const fraction = micros % 1_000_000n;
  return requireSpend(Number(whole) + Number(fraction) / 1_000_000);
}

export function parseGoogleAdsSpend(rows: unknown[]): number {
  if (rows.length === 0) {
    return 0;
  }
  if (rows.length !== 1 || !isRecord(rows[0]) || !isRecord(rows[0]["metrics"])) {
    throw new UpstreamRequestError("schema");
  }
  return costMicrosToUsd(rows[0]["metrics"]["costMicros"]);
}

function normalizeActionName(value: string): string {
  return value.trim().toLocaleLowerCase("en-US");
}

export function sumMatchingLeadConversions(
  rows: unknown[],
  configuredNames: string[],
): { value: number; matchedRows: number } {
  const allowed = new Set(configuredNames.map(normalizeActionName));
  let value = 0;
  let matchedRows = 0;

  for (const row of rows) {
    if (!isRecord(row) || !isRecord(row["segments"])) {
      throw new UpstreamRequestError("schema");
    }
    const name = row["segments"]["conversionActionName"];
    if (typeof name !== "string") {
      throw new UpstreamRequestError("schema");
    }
    if (!allowed.has(normalizeActionName(name))) {
      continue;
    }
    if (!isRecord(row["metrics"])) {
      throw new UpstreamRequestError("schema");
    }
    value += requireNonnegativeNumber(
      row["metrics"]["conversions"],
      "google_ads_conversions",
    );
    matchedRows += 1;
  }

  return {
    value: requireNonnegativeNumber(value, "google_ads_conversions_total"),
    matchedRows,
  };
}

export function parseConversionActionCatalog(
  rows: unknown[],
): ConversionActionCatalogItem[] {
  const items: ConversionActionCatalogItem[] = [];
  for (const row of rows) {
    if (!isRecord(row) || !isRecord(row["conversionAction"])) {
      throw new UpstreamRequestError("schema");
    }
    const action = row["conversionAction"];
    const name = action["name"];
    const status = action["status"];
    const type = action["type"];
    if (
      typeof name !== "string" ||
      name.trim() === "" ||
      typeof status !== "string" ||
      typeof type !== "string"
    ) {
      throw new UpstreamRequestError("schema");
    }
    items.push({ name, status, type });
  }
  return items;
}

export function catalogContainsConfiguredAction(
  catalog: ConversionActionCatalogItem[],
  configuredNames: string[],
): boolean {
  const available = new Set(catalog.map((item) => normalizeActionName(item.name)));
  return configuredNames.some((name) => available.has(normalizeActionName(name)));
}

function validateGoogleAdsConfig(config: GoogleAdsConfig): boolean {
  return (
    config.developerToken !== "" &&
    config.clientId !== "" &&
    config.clientSecret !== "" &&
    config.refreshToken !== "" &&
    /^\d{10}$/u.test(config.customerId) &&
    (config.loginCustomerId === "" || /^\d{10}$/u.test(config.loginCustomerId)) &&
    /^v\d+$/u.test(config.apiVersion) &&
    config.leadConversionActionNames.length > 0
  );
}

export async function queryGoogleAds(
  accessToken: string,
  config: GoogleAdsConfig,
  query: string,
  source: string,
  dependencies: RuntimeDependencies = {},
): Promise<unknown[]> {
  const endpoint = `https://googleads.googleapis.com/${config.apiVersion}/customers/${config.customerId}/googleAds:search`;
  const headers = new Headers({
    Authorization: `Bearer ${accessToken}`,
    "developer-token": config.developerToken,
    "Content-Type": "application/json",
    Accept: "application/json",
  });
  if (config.loginCustomerId !== "") {
    headers.set("login-customer-id", config.loginCustomerId);
  }

  const rows: unknown[] = [];
  let pageToken = "";
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const body: { query: string; pageToken?: string } = { query };
    if (pageToken !== "") {
      body.pageToken = pageToken;
    }
    const response = await fetchWithRetry(
      endpoint,
      { method: "POST", headers, body: JSON.stringify(body) },
      {
        source,
        fetcher: dependencies.fetcher,
        sleep: dependencies.sleep,
      },
    );
    if (!response.ok) {
      throw classifyHttpStatus(response.status);
    }
    const payload = await readBoundedJson(response);
    if (!isRecord(payload)) {
      throw new UpstreamRequestError("schema", response.status);
    }
    const results = payload["results"];
    if (results !== undefined && !Array.isArray(results)) {
      throw new UpstreamRequestError("schema", response.status);
    }
    rows.push(...(results ?? []));
    const nextPageToken = payload["nextPageToken"];
    if (nextPageToken === undefined || nextPageToken === "") {
      return rows;
    }
    if (typeof nextPageToken !== "string" || nextPageToken.length > 8_192) {
      throw new UpstreamRequestError("schema", response.status);
    }
    pageToken = nextPageToken;
  }
  throw new UpstreamRequestError("schema");
}

function metricError(error: unknown, started: number): MetricFetchResult {
  const category: ErrorCategory =
    error instanceof UpstreamRequestError
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

function unconfigured(started: number): MetricFetchResult {
  return {
    kind: "unconfigured",
    durationMs: Date.now() - started,
    responseStatus: null,
  };
}

export async function fetchGoogleAdsMetrics(
  env: DashboardEnv,
  reportingPeriod: DashboardSnapshot["reportingPeriod"],
  dependencies: RuntimeDependencies = {},
): Promise<GoogleAdsMetricResults> {
  const started = Date.now();
  const config = readGoogleAdsConfig(env);
  if (!validateGoogleAdsConfig(config)) {
    return {
      googleAdsSpendMtd: unconfigured(started),
      googleAdsLeadsMtd: unconfigured(started),
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
    );
  } catch (error) {
    return {
      googleAdsSpendMtd: metricError(error, started),
      googleAdsLeadsMtd: metricError(error, started),
    };
  }

  const [spendSettled, leadsSettled, catalogSettled] = await Promise.allSettled([
    queryGoogleAds(
      accessToken,
      config,
      buildSpendQuery(reportingPeriod),
      "google_ads_spend",
      dependencies,
    ),
    queryGoogleAds(
      accessToken,
      config,
      buildLeadQuery(reportingPeriod),
      "google_ads_leads",
      dependencies,
    ),
    queryGoogleAds(
      accessToken,
      config,
      CONVERSION_ACTION_CATALOG_QUERY,
      "google_ads_actions",
      dependencies,
    ),
  ]);

  let googleAdsSpendMtd: MetricFetchResult;
  try {
    if (spendSettled.status === "rejected") {
      throw spendSettled.reason;
    }
    googleAdsSpendMtd = {
      kind: "ok",
      value: parseGoogleAdsSpend(spendSettled.value),
      durationMs: Date.now() - started,
      responseStatus: 200,
    };
  } catch (error) {
    googleAdsSpendMtd = metricError(error, started);
  }

  let googleAdsLeadsMtd: MetricFetchResult;
  try {
    if (leadsSettled.status === "rejected") {
      throw leadsSettled.reason;
    }
    const matching = sumMatchingLeadConversions(
      leadsSettled.value,
      config.leadConversionActionNames,
    );
    if (matching.matchedRows === 0) {
      if (catalogSettled.status === "rejected") {
        throw catalogSettled.reason;
      }
      const catalog = parseConversionActionCatalog(catalogSettled.value);
      if (!catalogContainsConfiguredAction(catalog, config.leadConversionActionNames)) {
        throw new UpstreamRequestError("conversion_action_not_found");
      }
    }
    googleAdsLeadsMtd = {
      kind: "ok",
      value: matching.value,
      durationMs: Date.now() - started,
      responseStatus: 200,
    };
  } catch (error) {
    googleAdsLeadsMtd = metricError(error, started);
  }

  return { googleAdsSpendMtd, googleAdsLeadsMtd };
}
