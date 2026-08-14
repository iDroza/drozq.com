import { readFollowUpBossConfig, type FollowUpBossConfig } from "../config";
import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import { requireCount, requireSpend } from "../lib/numeric";
import { fetchWithRetry, UpstreamRequestError } from "../lib/retry";
import type {
  DashboardEnv,
  DashboardSnapshot,
  ErrorCategory,
  FollowUpBossTeamMetricResults,
  MetricFetchResult,
  RuntimeDependencies,
} from "../types";

const FUB_API_BASE_URL = "https://api.followupboss.com/v1";
const TEAM_CACHE_KEY = "dashboard:fub:team:v3";
const PAGE_LIMIT = 100;
const MAX_PAGES = 100;

export interface TeamDealTotals {
  commission: number;
  sales: number;
  volume: number;
  activeAgents: number;
}

export interface LeaderboardTotals {
  commission: number;
  sales: number;
  volume: number;
  activeUserIds: string[];
}

interface DirectoryUser {
  id: string;
  name: string;
  role: string;
}

interface TeamCache extends TeamDealTotals {
  version: 3;
  configKey: string;
  fetchedAt: string;
}

function normalize(value: string): string {
  return value.trim().toLocaleLowerCase("en-US");
}

function requiredMoney(value: unknown): number {
  if (
    (typeof value !== "number" && typeof value !== "string") ||
    String(value).trim() === ""
  ) {
    throw new UpstreamRequestError("schema");
  }
  try {
    return requireSpend(Number(value));
  } catch {
    throw new UpstreamRequestError("schema");
  }
}

function headersFor(config: FollowUpBossConfig, apiKey: string): Headers {
  const headers = new Headers({
    Authorization: `Basic ${btoa(`${apiKey}:`)}`,
    Accept: "application/json",
  });
  if (config.system !== "") {
    headers.set("X-System", config.system);
  }
  if (config.systemKey !== "") {
    headers.set("X-System-Key", config.systemKey);
  }
  return headers;
}

export function parseDealsLeaderboard(payload: unknown): LeaderboardTotals {
  if (
    !isRecord(payload) ||
    !isRecord(payload["totals"]) ||
    !Array.isArray(payload["users"])
  ) {
    throw new UpstreamRequestError("schema");
  }
  const totals = payload["totals"];
  const activeUserIds = new Set<string>();
  for (const row of payload["users"]) {
    if (!isRecord(row)) {
      throw new UpstreamRequestError("schema");
    }
    const userId = requireCount(row["userId"], "fub_leaderboard_user_id");
    const closedDeals = requireCount(
      row["closedDealCount"],
      "fub_leaderboard_user_closed_deals",
    );
    if (closedDeals > 0) {
      activeUserIds.add(String(userId));
    }
  }
  return {
    commission: requiredMoney(totals["closedCommissionTotal"]),
    sales: requireCount(totals["closedDealCount"], "fub_leaderboard_closed_deals"),
    volume: requiredMoney(totals["closedPriceTotal"]),
    activeUserIds: [...activeUserIds],
  };
}

function displayName(row: Record<string, unknown>): string {
  if (typeof row["name"] === "string") {
    return row["name"].trim();
  }
  const firstName = typeof row["firstName"] === "string" ? row["firstName"].trim() : "";
  const lastName = typeof row["lastName"] === "string" ? row["lastName"].trim() : "";
  return `${firstName} ${lastName}`.trim();
}

function parseUserDirectory(rows: unknown[]): Map<string, DirectoryUser> {
  const users = new Map<string, DirectoryUser>();
  for (const row of rows) {
    if (!isRecord(row)) {
      throw new UpstreamRequestError("schema");
    }
    const id = String(requireCount(row["id"], "fub_user_id"));
    users.set(id, {
      id,
      name: displayName(row),
      role: typeof row["role"] === "string" ? row["role"].trim() : "",
    });
  }
  return users;
}

export function countActiveLeaderboardAgents(
  activeUserIds: string[],
  directory: Map<string, DirectoryUser>,
  excludedUserNames: string[],
): number {
  const excludedNames = new Set(excludedUserNames.map(normalize));
  let count = 0;
  for (const userId of new Set(activeUserIds)) {
    const user = directory.get(userId);
    if (
      user !== undefined &&
      (normalize(user.role) === "lender" || excludedNames.has(normalize(user.name)))
    ) {
      continue;
    }
    count += 1;
  }
  return requireCount(count, "fub_team_active_agents");
}

async function listCollection(
  endpoint: string,
  collectionName: string,
  parameters: Record<string, string>,
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<unknown[]> {
  const rows: unknown[] = [];
  let offset = 0;
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const url = new URL(`${FUB_API_BASE_URL}/${endpoint}`);
    for (const [key, value] of Object.entries(parameters)) {
      url.searchParams.set(key, value);
    }
    url.searchParams.set("limit", String(PAGE_LIMIT));
    url.searchParams.set("offset", String(offset));
    const response = await fetchWithRetry(
      url,
      { method: "GET", headers },
      {
        source: `follow_up_boss_${endpoint}`,
        fetcher: dependencies.fetcher,
        sleep: dependencies.sleep,
      },
    );
    if (!response.ok) {
      throw classifyHttpStatus(response.status);
    }
    const payload = await readBoundedJson(response);
    if (!isRecord(payload) || !Array.isArray(payload[collectionName])) {
      throw new UpstreamRequestError("schema", response.status);
    }
    const pageRows = payload[collectionName];
    rows.push(...pageRows);
    const total = isRecord(payload["_metadata"]) && payload["_metadata"]["total"] !== undefined
      ? requireCount(payload["_metadata"]["total"], "fub_collection_total")
      : null;
    if (
      pageRows.length === 0 ||
      pageRows.length < PAGE_LIMIT ||
      (total !== null && rows.length >= total)
    ) {
      return rows;
    }
    offset += pageRows.length;
  }
  throw new UpstreamRequestError("schema");
}

async function fetchUserDirectory(
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<Map<string, DirectoryUser>> {
  const rows = await listCollection(
    "users",
    "users",
    {},
    headers,
    dependencies,
  );
  return parseUserDirectory(rows);
}

function leaderboardUrls(
  config: FollowUpBossConfig,
  reportingPeriod: DashboardSnapshot["yearToDatePeriod"],
): URL[] {
  const parameters = new URLSearchParams({
    start: reportingPeriod.startDate,
    end: reportingPeriod.endDate,
  });
  return [
    new URL(`https://${config.accountHost}/api/v1/deals/leaderboard?${parameters}`),
    new URL(`${FUB_API_BASE_URL}/deals/leaderboard?${parameters}`),
  ];
}

async function fetchLeaderboard(
  config: FollowUpBossConfig,
  reportingPeriod: DashboardSnapshot["yearToDatePeriod"],
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<LeaderboardTotals> {
  let lastError: unknown = new UpstreamRequestError("upstream");
  for (const [index, url] of leaderboardUrls(config, reportingPeriod).entries()) {
    try {
      const response = await fetchWithRetry(
        url,
        { method: "GET", headers, redirect: "manual" },
        {
          source: index === 0
            ? "follow_up_boss_deals_leaderboard_tenant"
            : "follow_up_boss_deals_leaderboard_api",
          fetcher: dependencies.fetcher,
          sleep: dependencies.sleep,
        },
      );
      if (!response.ok) {
        lastError = classifyHttpStatus(response.status);
        continue;
      }
      return parseDealsLeaderboard(await readBoundedJson(response));
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

async function assertAccountWideAccess(
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<void> {
  const response = await fetchWithRetry(
    new URL(`${FUB_API_BASE_URL}/me`),
    { method: "GET", headers },
    {
      source: "follow_up_boss_team_identity",
      fetcher: dependencies.fetcher,
      sleep: dependencies.sleep,
    },
  );
  if (!response.ok) {
    throw classifyHttpStatus(response.status);
  }
  const payload = await readBoundedJson(response);
  if (!isRecord(payload) || typeof payload["role"] !== "string") {
    throw new UpstreamRequestError("schema", response.status);
  }
  if (normalize(payload["role"]) !== "broker") {
    throw new UpstreamRequestError("authorization");
  }
}

export function closedStageIds(
  pipelines: unknown[],
  configuredStageNames: string[],
): Set<number> {
  const allowed = new Set(configuredStageNames.map(normalize));
  const ids = new Set<number>();
  for (const pipeline of pipelines) {
    if (!isRecord(pipeline) || !Array.isArray(pipeline["stages"])) {
      throw new UpstreamRequestError("schema");
    }
    for (const stage of pipeline["stages"]) {
      if (!isRecord(stage) || typeof stage["name"] !== "string") {
        throw new UpstreamRequestError("schema");
      }
      if (allowed.has(normalize(stage["name"]))) {
        ids.add(requireCount(stage["id"], "fub_closed_stage_id"));
      }
    }
  }
  if (ids.size === 0) {
    throw new UpstreamRequestError("configuration");
  }
  return ids;
}

function dateOnly(value: unknown): string {
  if (typeof value !== "string") {
    throw new UpstreamRequestError("schema");
  }
  const match = /^(\d{4}-\d{2}-\d{2})(?:T.*)?$/u.exec(value.trim());
  if (match?.[1] === undefined || !Number.isFinite(Date.parse(`${match[1]}T00:00:00.000Z`))) {
    throw new UpstreamRequestError("schema");
  }
  return match[1];
}

function dealUserIds(value: unknown): string[] {
  if (!Array.isArray(value)) {
    throw new UpstreamRequestError("schema");
  }
  return value.map((user) => {
    if (!isRecord(user)) {
      throw new UpstreamRequestError("schema");
    }
    return String(requireCount(user["id"], "fub_deal_user_id"));
  });
}

export function aggregateClosedDeals(
  deals: unknown[],
  stageIds: Set<number>,
  reportingPeriod: DashboardSnapshot["yearToDatePeriod"],
  excludedUserIds: Set<string> = new Set(),
): TeamDealTotals {
  let commission = 0;
  let volume = 0;
  let sales = 0;
  const agents = new Set<string>();
  for (const deal of deals) {
    if (!isRecord(deal) || typeof deal["status"] !== "string") {
      throw new UpstreamRequestError("schema");
    }
    if (normalize(deal["status"]) === "deleted") {
      continue;
    }
    const stageId = requireCount(deal["stageId"], "fub_deal_stage_id");
    if (!stageIds.has(stageId)) {
      continue;
    }
    const closeDate = dateOnly(deal["projectedCloseDate"]);
    if (closeDate < reportingPeriod.startDate || closeDate > reportingPeriod.endDate) {
      continue;
    }
    requireCount(deal["id"], "fub_deal_id");
    sales += 1;
    volume += requiredMoney(deal["price"]);
    commission += requiredMoney(deal["commissionValue"]);
    for (const id of dealUserIds(deal["users"])) {
      if (!excludedUserIds.has(id)) {
        agents.add(id);
      }
    }
  }
  return {
    commission: requireSpend(commission),
    sales: requireCount(sales, "fub_team_sales"),
    volume: requireSpend(volume),
    activeAgents: requireCount(agents.size, "fub_team_active_agents"),
  };
}

function excludedUserIds(
  directory: Map<string, DirectoryUser>,
  excludedUserNames: string[],
): Set<string> {
  const excludedNames = new Set(excludedUserNames.map(normalize));
  const ids = new Set<string>();
  for (const user of directory.values()) {
    if (normalize(user.role) === "lender" || excludedNames.has(normalize(user.name))) {
      ids.add(user.id);
    }
  }
  return ids;
}

function validTotals(value: unknown): value is TeamDealTotals {
  return isRecord(value) &&
    typeof value["commission"] === "number" && Number.isFinite(value["commission"]) && value["commission"] >= 0 &&
    typeof value["sales"] === "number" && Number.isSafeInteger(value["sales"]) && value["sales"] >= 0 &&
    typeof value["volume"] === "number" && Number.isFinite(value["volume"]) && value["volume"] >= 0 &&
    typeof value["activeAgents"] === "number" && Number.isSafeInteger(value["activeAgents"]) && value["activeAgents"] >= 0;
}

function parseCache(
  value: unknown,
  configKey: string,
  now: Date,
  refreshMs: number,
): TeamCache | null {
  if (
    !isRecord(value) || value["version"] !== 3 || value["configKey"] !== configKey ||
    typeof value["fetchedAt"] !== "string" || !Number.isFinite(Date.parse(value["fetchedAt"])) ||
    now.getTime() - Date.parse(value["fetchedAt"]) < 0 ||
    now.getTime() - Date.parse(value["fetchedAt"]) > refreshMs || !validTotals(value)
  ) {
    return null;
  }
  return value as unknown as TeamCache;
}

function okResult(value: number, started: number, observedAt: string): MetricFetchResult {
  return {
    kind: "ok",
    value,
    observedAt,
    durationMs: Date.now() - started,
    responseStatus: 200,
  };
}

function toResults(
  totals: TeamDealTotals,
  started: number,
  observedAt: string,
): FollowUpBossTeamMetricResults {
  return {
    teamCommissionYtd: okResult(totals.commission, started, observedAt),
    teamSalesYtd: okResult(totals.sales, started, observedAt),
    teamVolumeYtd: okResult(totals.volume, started, observedAt),
    teamActiveAgentsYtd: okResult(totals.activeAgents, started, observedAt),
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
    responseStatus: error instanceof UpstreamRequestError ? error.responseStatus : null,
  };
}

function allSame(result: MetricFetchResult): FollowUpBossTeamMetricResults {
  return {
    teamCommissionYtd: result,
    teamSalesYtd: result,
    teamVolumeYtd: result,
    teamActiveAgentsYtd: result,
  };
}

async function writeCache(
  env: DashboardEnv,
  configKey: string,
  observedAt: string,
  totals: TeamDealTotals,
): Promise<void> {
  try {
    await env.DASHBOARD_KV.put(
      TEAM_CACHE_KEY,
      JSON.stringify({
        version: 3,
        configKey,
        fetchedAt: observedAt,
        ...totals,
      } satisfies TeamCache),
      { expirationTtl: 48 * 60 * 60 },
    );
  } catch {
    console.warn(JSON.stringify({
      source: "follow_up_boss_team_cache",
      category: "storage",
      status: null,
    }));
  }
}

async function fetchBrokerFallback(
  env: DashboardEnv,
  config: FollowUpBossConfig,
  reportingPeriod: DashboardSnapshot["yearToDatePeriod"],
  dependencies: RuntimeDependencies,
): Promise<TeamDealTotals> {
  const dedicatedKey = env.FUB_TEAM_API_KEY?.trim() ?? "";
  if (dedicatedKey === "" || config.closedDealStageNames.length === 0) {
    throw new UpstreamRequestError("configuration");
  }
  const headers = headersFor(config, dedicatedKey);
  await assertAccountWideAccess(headers, dependencies);
  const [pipelines, deals, directory] = await Promise.all([
    listCollection("pipelines", "pipelines", {}, headers, dependencies),
    listCollection("deals", "deals", { includeArchived: "1" }, headers, dependencies),
    fetchUserDirectory(headers, dependencies),
  ]);
  return aggregateClosedDeals(
    deals,
    closedStageIds(pipelines, config.closedDealStageNames),
    reportingPeriod,
    excludedUserIds(directory, config.teamExcludedUserNames),
  );
}

export async function fetchFollowUpBossTeamMetrics(
  env: DashboardEnv,
  reportingPeriod: DashboardSnapshot["yearToDatePeriod"],
  dependencies: RuntimeDependencies = {},
): Promise<FollowUpBossTeamMetricResults> {
  const started = Date.now();
  const config = readFollowUpBossConfig(env);
  if (config.teamApiKey === "" || config.accountHost === "") {
    return allSame({ kind: "unconfigured", durationMs: 0, responseStatus: null });
  }
  const now = dependencies.now ?? new Date();
  const configKey = [
    reportingPeriod.startDate,
    reportingPeriod.endDate,
    config.accountHost,
    ...config.teamExcludedUserNames.map(normalize).sort(),
  ].join("|");
  try {
    const stored = await env.DASHBOARD_KV.get(TEAM_CACHE_KEY);
    if (stored !== null) {
      const cached = parseCache(JSON.parse(stored) as unknown, configKey, now, config.teamRefreshMs);
      if (cached !== null) {
        return toResults(cached, started, cached.fetchedAt);
      }
    }
  } catch {
    console.warn(JSON.stringify({
      source: "follow_up_boss_team_cache",
      category: "storage",
      status: null,
    }));
  }

  const headers = headersFor(config, config.teamApiKey);
  try {
    const leaderboard = await fetchLeaderboard(config, reportingPeriod, headers, dependencies);
    const observedAt = now.toISOString();
    try {
      const directory = await fetchUserDirectory(headers, dependencies);
      const totals: TeamDealTotals = {
        commission: leaderboard.commission,
        sales: leaderboard.sales,
        volume: leaderboard.volume,
        activeAgents: countActiveLeaderboardAgents(
          leaderboard.activeUserIds,
          directory,
          config.teamExcludedUserNames,
        ),
      };
      await writeCache(env, configKey, observedAt, totals);
      return toResults(totals, started, observedAt);
    } catch (directoryError) {
      console.warn(JSON.stringify({
        source: "follow_up_boss_team_directory",
        category: directoryError instanceof UpstreamRequestError
          ? directoryError.category
          : directoryError instanceof RangeError
            ? "schema"
            : "unexpected",
        status: directoryError instanceof UpstreamRequestError
          ? directoryError.responseStatus
          : null,
      }));
      const activeAgentsError = errorResult(directoryError, started);
      return {
        teamCommissionYtd: okResult(leaderboard.commission, started, observedAt),
        teamSalesYtd: okResult(leaderboard.sales, started, observedAt),
        teamVolumeYtd: okResult(leaderboard.volume, started, observedAt),
        teamActiveAgentsYtd: activeAgentsError,
      };
    }
  } catch (leaderboardError) {
    console.warn(JSON.stringify({
      source: "follow_up_boss_team_leaderboard",
      category: leaderboardError instanceof UpstreamRequestError
        ? leaderboardError.category
        : "unexpected",
      status: leaderboardError instanceof UpstreamRequestError
        ? leaderboardError.responseStatus
        : null,
    }));
    try {
      const totals = await fetchBrokerFallback(
        env,
        config,
        reportingPeriod,
        dependencies,
      );
      const observedAt = now.toISOString();
      await writeCache(env, configKey, observedAt, totals);
      return toResults(totals, started, observedAt);
    } catch (fallbackError) {
      return allSame(errorResult(
        (env.FUB_TEAM_API_KEY?.trim() ?? "") === ""
          ? leaderboardError
          : fallbackError,
        started,
      ));
    }
  }
}
