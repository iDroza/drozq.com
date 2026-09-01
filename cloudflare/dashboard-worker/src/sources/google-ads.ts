import { readGoogleAdsConfig, type GoogleAdsConfig } from "../config";
import { exchangeRefreshToken } from "../lib/google-auth";
import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import { getSellerCampaignPeriod } from "../lib/date";
import { requireNonnegativeNumber, requireSpend } from "../lib/numeric";
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
const MAX_CUSTOMERS = 100;
const ACCOUNT_CACHE_KEY = "dashboard:google_ads:accounts:v2";
const ACCOUNT_CACHE_MS = 10 * 60 * 1_000;

export interface ConversionActionCatalogItem {
  name: string;
  status: string;
  type: string;
}

interface GoogleAdsPerformance {
  costMicros: bigint;
  conversions: number;
  clicks: number;
}

interface GoogleAdsDailyPerformance extends GoogleAdsPerformance {
  date: string;
}

export interface GoogleAdsCampaignDailyPerformance extends GoogleAdsDailyPerformance {
  campaignId: string;
  campaignName: string;
  impressions: number;
}

export interface SellerCampaignTotals {
  campaignNames: string[];
  costMicros: bigint;
  clicks: number;
  impressions: number;
  conversions: number;
}

interface CustomerClient {
  customerId: string;
  manager: boolean;
  hidden: boolean;
  testAccount: boolean;
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

export const CUSTOMER_CLIENT_QUERY = `
SELECT
  customer_client.client_customer,
  customer_client.manager,
  customer_client.level,
  customer_client.status,
  customer_client.hidden,
  customer_client.test_account
FROM customer_client
WHERE customer_client.level <= 1
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

export function buildAccountPerformanceQuery(
  reportingPeriod: DashboardSnapshot["reportingPeriod"],
): string {
  return `
SELECT
  segments.date,
  metrics.cost_micros,
  metrics.conversions,
  metrics.clicks
FROM customer
WHERE segments.date BETWEEN '${reportingPeriod.startDate}' AND '${reportingPeriod.endDate}'
`.trim();
}

export function buildCampaignPerformanceQuery(
  period: DashboardSnapshot["sellerCampaignPeriod"],
): string {
  return `
SELECT
  campaign.id,
  campaign.name,
  segments.date,
  metrics.cost_micros,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions
FROM campaign
WHERE segments.date BETWEEN '${period.startDate}' AND '${period.endDate}'
  AND campaign.status != 'REMOVED'
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
  return costMicrosToUsd(rows[0]["metrics"]["costMicros"] ?? "0");
}

export function parseGoogleAdsPerformance(rows: unknown[]): GoogleAdsPerformance {
  if (rows.length === 0) {
    return { costMicros: 0n, conversions: 0, clicks: 0 };
  }
  if (rows.length !== 1 || !isRecord(rows[0]) || !isRecord(rows[0]["metrics"])) {
    throw new UpstreamRequestError("schema");
  }
  const metrics = rows[0]["metrics"];
  return {
    costMicros: parseMicros(metrics["costMicros"] ?? "0"),
    conversions: requireNonnegativeNumber(
      metrics["conversions"] ?? 0,
      "google_ads_conversions",
    ),
    clicks: parseClicks(metrics["clicks"] ?? 0),
  };
}

function parseClicks(value: unknown): number {
  const clicks = requireNonnegativeNumber(value, "google_ads_clicks");
  if (!Number.isSafeInteger(clicks)) {
    throw new UpstreamRequestError("schema");
  }
  return clicks;
}

export function parseGoogleAdsDailyPerformance(
  rows: unknown[],
): GoogleAdsDailyPerformance[] {
  return rows.map((row) => {
    if (
      !isRecord(row) ||
      !isRecord(row["segments"]) ||
      !isRecord(row["metrics"])
    ) {
      throw new UpstreamRequestError("schema");
    }
    const date = row["segments"]["date"];
    if (
      typeof date !== "string" ||
      !/^\d{4}-\d{2}-\d{2}$/u.test(date) ||
      !Number.isFinite(Date.parse(`${date}T00:00:00.000Z`))
    ) {
      throw new UpstreamRequestError("schema");
    }
    const metrics = row["metrics"];
    return {
      date,
      costMicros: parseMicros(metrics["costMicros"] ?? "0"),
      conversions: requireNonnegativeNumber(
        metrics["conversions"] ?? 0,
        "google_ads_conversions",
      ),
      clicks: parseClicks(metrics["clicks"] ?? 0),
    };
  });
}

export function parseGoogleAdsCampaignDailyPerformance(
  rows: unknown[],
): GoogleAdsCampaignDailyPerformance[] {
  return rows.map((row) => {
    if (!isRecord(row) || !isRecord(row["campaign"])) {
      throw new UpstreamRequestError("schema");
    }
    const [daily] = parseGoogleAdsDailyPerformance([row]);
    if (daily === undefined || !isRecord(row["metrics"])) {
      throw new UpstreamRequestError("schema");
    }
    const campaignId = row["campaign"]["id"];
    const campaignName = row["campaign"]["name"];
    if (
      (typeof campaignId !== "string" && typeof campaignId !== "number") ||
      typeof campaignName !== "string" ||
      campaignName.trim() === ""
    ) {
      throw new UpstreamRequestError("schema");
    }
    return {
      ...daily,
      campaignId: String(campaignId),
      campaignName,
      impressions: parseClicks(row["metrics"]["impressions"] ?? 0),
    };
  });
}

function normalizeCampaignName(value: string): string {
  return value
    .split("|")
    .map((segment) => segment.trim().replace(/\s+/gu, " ").toLocaleLowerCase("en-US"))
    .join(" | ");
}

/**
 * The seller block follows the two "Sell | OC" search campaigns (JT + AR), one
 * lander on two domains. With explicit names configured only those match;
 * otherwise a "|"-delimited campaign name qualifies when it carries a JT or AR
 * segment, an OC segment, and a segment starting with "sell" (Sell, Sellers).
 */
export function isSellerCampaignName(
  name: string,
  configuredNames: string[],
): boolean {
  const normalized = normalizeCampaignName(name);
  if (configuredNames.length > 0) {
    return configuredNames.some(
      (configured) => normalizeCampaignName(configured) === normalized,
    );
  }
  const segments = normalized.split(" | ");
  return (
    segments.some((segment) => segment === "jt" || segment === "ar") &&
    segments.includes("oc") &&
    segments.some((segment) => segment.startsWith("sell"))
  );
}

export function sumSellerCampaignPerformance(
  rows: GoogleAdsCampaignDailyPerformance[],
  configuredNames: string[],
  period: DashboardSnapshot["sellerCampaignPeriod"],
): SellerCampaignTotals {
  const campaignNames = new Set<string>();
  let costMicros = 0n;
  let clicks = 0;
  let impressions = 0;
  let conversions = 0;
  for (const row of rows) {
    if (row.date < period.startDate || row.date > period.endDate) {
      throw new UpstreamRequestError("schema");
    }
    if (!isSellerCampaignName(row.campaignName, configuredNames)) {
      continue;
    }
    campaignNames.add(row.campaignName);
    costMicros += row.costMicros;
    clicks += row.clicks;
    impressions += row.impressions;
    conversions += row.conversions;
  }
  return {
    campaignNames: [...campaignNames].sort(),
    costMicros,
    clicks: parseClicks(clicks),
    impressions: parseClicks(impressions),
    conversions: requireNonnegativeNumber(conversions, "google_ads_seller_conversions"),
  };
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
    /^v\d+$/u.test(config.apiVersion)
  );
}

export async function queryGoogleAds(
  accessToken: string,
  config: GoogleAdsConfig,
  customerId: string,
  query: string,
  source: string,
  dependencies: RuntimeDependencies = {},
): Promise<unknown[]> {
  if (!/^\d{10}$/u.test(customerId)) {
    throw new UpstreamRequestError("configuration");
  }
  const endpoint = `https://googleads.googleapis.com/${config.apiVersion}/customers/${customerId}/googleAds:search`;
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

function parseCustomerClients(rows: unknown[]): CustomerClient[] {
  return rows.map((row) => {
    if (!isRecord(row) || !isRecord(row["customerClient"])) {
      throw new UpstreamRequestError("schema");
    }
    const client = row["customerClient"];
    const resource = client["clientCustomer"];
    if (typeof resource !== "string") {
      throw new UpstreamRequestError("schema");
    }
    const match = /^customers\/(\d{10})$/u.exec(resource);
    if (match?.[1] === undefined) {
      throw new UpstreamRequestError("schema");
    }
    for (const field of ["manager", "hidden", "testAccount"] as const) {
      if (client[field] !== undefined && typeof client[field] !== "boolean") {
        throw new UpstreamRequestError("schema");
      }
    }
    return {
      customerId: match[1],
      manager: client["manager"] === true,
      hidden: client["hidden"] === true,
      testAccount: client["testAccount"] === true,
    };
  });
}

export async function discoverGoogleAdsCustomerIds(
  accessToken: string,
  config: GoogleAdsConfig,
  dependencies: RuntimeDependencies = {},
): Promise<string[]> {
  const rootCustomerId = config.loginCustomerId || config.customerId;
  const managers = [rootCustomerId];
  const visitedManagers = new Set<string>();
  const customerIds = new Set<string>();

  while (managers.length > 0) {
    const managerId = managers.shift();
    if (managerId === undefined || visitedManagers.has(managerId)) {
      continue;
    }
    visitedManagers.add(managerId);
    if (visitedManagers.size + customerIds.size > MAX_CUSTOMERS) {
      throw new UpstreamRequestError("schema");
    }
    const rows = await queryGoogleAds(
      accessToken,
      config,
      managerId,
      CUSTOMER_CLIENT_QUERY,
      "google_ads_accounts",
      dependencies,
    );
    for (const client of parseCustomerClients(rows)) {
      if (client.hidden || client.testAccount) {
        continue;
      }
      if (client.manager) {
        if (client.customerId !== managerId && !visitedManagers.has(client.customerId)) {
          managers.push(client.customerId);
        }
      } else {
        customerIds.add(client.customerId);
      }
    }
  }

  if (customerIds.size === 0) {
    throw new UpstreamRequestError("schema");
  }
  return [...customerIds].sort();
}

function parseCachedCustomerIds(
  value: unknown,
  rootCustomerId: string,
  now: Date,
): string[] | null {
  if (
    !isRecord(value) ||
    value["version"] !== 2 ||
    value["rootCustomerId"] !== rootCustomerId ||
    typeof value["discoveredAt"] !== "string" ||
    !Number.isFinite(Date.parse(value["discoveredAt"])) ||
    now.getTime() - Date.parse(value["discoveredAt"]) > ACCOUNT_CACHE_MS ||
    !Array.isArray(value["customerIds"]) ||
    value["customerIds"].length === 0 ||
    value["customerIds"].length > MAX_CUSTOMERS ||
    !value["customerIds"].every(
      (customerId) => typeof customerId === "string" && /^\d{10}$/u.test(customerId),
    )
  ) {
    return null;
  }
  return [...new Set(value["customerIds"] as string[])].sort();
}

async function resolveCustomerIds(
  env: DashboardEnv,
  accessToken: string,
  config: GoogleAdsConfig,
  now: Date,
  dependencies: RuntimeDependencies,
): Promise<string[]> {
  const rootCustomerId = config.loginCustomerId || config.customerId;
  try {
    const stored = await env.DASHBOARD_KV.get(ACCOUNT_CACHE_KEY);
    if (stored !== null) {
      const cached = parseCachedCustomerIds(
        JSON.parse(stored) as unknown,
        rootCustomerId,
        now,
      );
      if (cached !== null) {
        return cached;
      }
    }
  } catch {
    console.warn(JSON.stringify({
      source: "google_ads_account_cache",
      category: "storage",
      status: null,
    }));
  }

  const customerIds = await discoverGoogleAdsCustomerIds(
    accessToken,
    config,
    dependencies,
  );
  try {
    await env.DASHBOARD_KV.put(
      ACCOUNT_CACHE_KEY,
      JSON.stringify({
        version: 2,
        rootCustomerId,
        discoveredAt: now.toISOString(),
        customerIds,
      }),
      { expirationTtl: 3_600 },
    );
  } catch {
    console.warn(JSON.stringify({
      source: "google_ads_account_cache",
      category: "storage",
      status: null,
    }));
  }
  return customerIds;
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

type SellerCampaignMetricResults = Pick<
  GoogleAdsMetricResults,
  | "sellerCampaignSpend"
  | "sellerCampaignCostPerClick"
  | "sellerCampaignLeads"
  | "sellerCampaignCostPerLead"
>;

function sellerResults(result: MetricFetchResult): SellerCampaignMetricResults {
  return {
    sellerCampaignSpend: result,
    sellerCampaignCostPerClick: result,
    sellerCampaignLeads: result,
    sellerCampaignCostPerLead: result,
  };
}

function ratioResult(
  numerator: number,
  denominator: number,
  durationMs: number,
): MetricFetchResult {
  if (denominator <= 0) {
    return { kind: "error", category: "no_data", durationMs, responseStatus: 200 };
  }
  const value = numerator / denominator;
  if (!Number.isFinite(value) || value < 0) {
    throw new UpstreamRequestError("schema");
  }
  return { kind: "ok", value, durationMs, responseStatus: 200 };
}

/**
 * Seller-campaign metrics are best-effort on top of the all-account totals:
 * a failed campaign query in any account makes only the seller block
 * unavailable (the previous values stay visible as stale), and a sweep that
 * matches no campaign publishes no_data rather than a false $0.
 */
export function deriveSellerCampaignMetrics(
  campaignSettled: PromiseSettledResult<unknown[]>[],
  configuredNames: string[],
  period: DashboardSnapshot["sellerCampaignPeriod"],
  started: number,
): SellerCampaignMetricResults {
  const durationMs = Date.now() - started;
  try {
    const rows: GoogleAdsCampaignDailyPerformance[] = [];
    for (const item of campaignSettled) {
      if (item.status === "rejected") {
        throw item.reason;
      }
      rows.push(...parseGoogleAdsCampaignDailyPerformance(item.value));
    }
    const totals = sumSellerCampaignPerformance(rows, configuredNames, period);
    console.log(JSON.stringify({
      source: "google_ads_seller_campaigns",
      matchedCampaigns: totals.campaignNames,
      startDate: period.startDate,
      endDate: period.endDate,
      clicks: totals.clicks,
      impressions: totals.impressions,
      conversions: totals.conversions,
    }));
    if (totals.campaignNames.length === 0) {
      return sellerResults({
        kind: "error",
        category: "no_data",
        durationMs,
        responseStatus: 200,
      });
    }
    const spend = costMicrosToUsd(totals.costMicros);
    return {
      sellerCampaignSpend: { kind: "ok", value: spend, durationMs, responseStatus: 200 },
      sellerCampaignCostPerClick: ratioResult(spend, totals.clicks, durationMs),
      sellerCampaignLeads: {
        kind: "ok",
        value: totals.conversions,
        durationMs,
        responseStatus: 200,
      },
      sellerCampaignCostPerLead: ratioResult(spend, totals.conversions, durationMs),
    };
  } catch (error) {
    return sellerResults(metricError(error, started));
  }
}

export async function fetchGoogleAdsMetrics(
  env: DashboardEnv,
  reportingPeriod: DashboardSnapshot["reportingPeriod"],
  yearToDatePeriod: DashboardSnapshot["yearToDatePeriod"],
  dependencies: RuntimeDependencies = {},
  sellerCampaignPeriod?: DashboardSnapshot["sellerCampaignPeriod"],
): Promise<GoogleAdsMetricResults> {
  const started = Date.now();
  const config = readGoogleAdsConfig(env);
  if (!validateGoogleAdsConfig(config)) {
    return {
      googleAdsSpendMtd: unconfigured(started),
      googleAdsLeadsMtd: unconfigured(started),
      googleAdsCostPerClickMtd: unconfigured(started),
      googleAdsCostPerLeadMtd: unconfigured(started),
      googleAdsSpendYtd: unconfigured(started),
      googleAdsLeadsYtd: unconfigured(started),
      googleAdsCostPerLeadYtd: unconfigured(started),
      sellerCampaignSpend: unconfigured(started),
      sellerCampaignCostPerClick: unconfigured(started),
      sellerCampaignLeads: unconfigured(started),
      sellerCampaignCostPerLead: unconfigured(started),
    };
  }

  try {
    const accessToken = await exchangeRefreshToken(
      {
        clientId: config.clientId,
        clientSecret: config.clientSecret,
        refreshToken: config.refreshToken,
      },
      dependencies,
    );
    const now = dependencies.now ?? new Date();
    const customerIds = await resolveCustomerIds(
      env,
      accessToken,
      config,
      now,
      dependencies,
    );
    const sellerPeriod = sellerCampaignPeriod ?? getSellerCampaignPeriod(
      config.sellerCampaignLaunchDate,
      now,
      yearToDatePeriod.timeZone,
    );
    const query = buildAccountPerformanceQuery(yearToDatePeriod);
    const campaignQuery = buildCampaignPerformanceQuery(sellerPeriod);
    // Before launch day there is nothing to sum: skip the campaign sweep and
    // publish no_data instead of a false $0.
    const sellerLaunched = sellerPeriod.startDate <= yearToDatePeriod.endDate;
    const [settled, campaignSettled] = await Promise.all([
      Promise.allSettled(
        customerIds.map((customerId) => queryGoogleAds(
          accessToken,
          config,
          customerId,
          query,
          "google_ads_performance",
          dependencies,
        )),
      ),
      sellerLaunched
        ? Promise.allSettled(
            customerIds.map((customerId) => queryGoogleAds(
              accessToken,
              config,
              customerId,
              campaignQuery,
              "google_ads_seller_campaigns",
              dependencies,
            )),
          )
        : Promise.resolve(null),
    ]);
    const rejected = settled.find(
      (item): item is PromiseRejectedResult => item.status === "rejected",
    );
    if (rejected !== undefined) {
      try {
        await env.DASHBOARD_KV.delete(ACCOUNT_CACHE_KEY);
      } catch {
        // The next cache expiry will force account discovery if deletion fails.
      }
      throw rejected.reason;
    }
    const seller = campaignSettled === null
      ? sellerResults({
          kind: "error",
          category: "no_data",
          durationMs: Date.now() - started,
          responseStatus: 200,
        })
      : deriveSellerCampaignMetrics(
          campaignSettled,
          config.sellerCampaignNames,
          sellerPeriod,
          started,
        );

    let mtdCostMicros = 0n;
    let mtdConversions = 0;
    let mtdClicks = 0;
    let yearToDateCostMicros = 0n;
    let yearToDateConversions = 0;
    for (const item of settled) {
      if (item.status !== "fulfilled") {
        throw new UpstreamRequestError("unexpected");
      }
      for (const performance of parseGoogleAdsDailyPerformance(item.value)) {
        if (
          performance.date < yearToDatePeriod.startDate ||
          performance.date > yearToDatePeriod.endDate
        ) {
          throw new UpstreamRequestError("schema");
        }
        yearToDateCostMicros += performance.costMicros;
        yearToDateConversions += performance.conversions;
        if (
          performance.date >= reportingPeriod.startDate &&
          performance.date <= reportingPeriod.endDate
        ) {
          mtdCostMicros += performance.costMicros;
          mtdConversions += performance.conversions;
          mtdClicks += performance.clicks;
        }
      }
    }
    const durationMs = Date.now() - started;
    const monthToDateSpend = costMicrosToUsd(mtdCostMicros);
    const monthToDateLeads = requireNonnegativeNumber(
      mtdConversions,
      "google_ads_month_to_date_conversions",
    );
    const monthToDateClicks = parseClicks(mtdClicks);
    const monthToDateCostPerClick = monthToDateClicks > 0
      ? requireSpend(monthToDateSpend / monthToDateClicks)
      : null;
    const monthToDateCostPerLead = monthToDateLeads > 0
      ? requireSpend(monthToDateSpend / monthToDateLeads)
      : null;
    const yearToDateSpend = costMicrosToUsd(yearToDateCostMicros);
    const yearToDateLeads = requireNonnegativeNumber(
      yearToDateConversions,
      "google_ads_year_to_date_conversions",
    );
    const yearToDateCostPerLead = yearToDateLeads > 0
      ? requireSpend(yearToDateSpend / yearToDateLeads)
      : null;
    return {
      googleAdsSpendMtd: {
        kind: "ok",
        value: monthToDateSpend,
        durationMs,
        responseStatus: 200,
      },
      googleAdsLeadsMtd: {
        kind: "ok",
        value: monthToDateLeads,
        durationMs,
        responseStatus: 200,
      },
      googleAdsCostPerClickMtd: monthToDateCostPerClick === null
        ? {
            kind: "error",
            category: "no_data",
            durationMs,
            responseStatus: 200,
          }
        : {
            kind: "ok",
            value: monthToDateCostPerClick,
            durationMs,
            responseStatus: 200,
          },
      googleAdsCostPerLeadMtd: monthToDateCostPerLead === null
        ? {
            kind: "error",
            category: "no_data",
            durationMs,
            responseStatus: 200,
          }
        : {
            kind: "ok",
            value: monthToDateCostPerLead,
            durationMs,
            responseStatus: 200,
          },
      googleAdsSpendYtd: {
        kind: "ok",
        value: yearToDateSpend,
        durationMs,
        responseStatus: 200,
      },
      googleAdsLeadsYtd: {
        kind: "ok",
        value: requireNonnegativeNumber(
          yearToDateLeads,
          "google_ads_year_to_date_conversions",
        ),
        durationMs,
        responseStatus: 200,
      },
      googleAdsCostPerLeadYtd: yearToDateCostPerLead === null
        ? {
            kind: "error",
            category: "no_data",
            durationMs,
            responseStatus: 200,
          }
        : {
            kind: "ok",
            value: yearToDateCostPerLead,
            durationMs,
            responseStatus: 200,
          },
      ...seller,
    };
  } catch (error) {
    const metric = metricError(error, started);
    return {
      googleAdsSpendMtd: metric,
      googleAdsLeadsMtd: metric,
      googleAdsCostPerClickMtd: metric,
      googleAdsCostPerLeadMtd: metric,
      googleAdsSpendYtd: metric,
      googleAdsLeadsYtd: metric,
      googleAdsCostPerLeadYtd: metric,
      sellerCampaignSpend: metric,
      sellerCampaignCostPerClick: metric,
      sellerCampaignLeads: metric,
      sellerCampaignCostPerLead: metric,
    };
  }
}
