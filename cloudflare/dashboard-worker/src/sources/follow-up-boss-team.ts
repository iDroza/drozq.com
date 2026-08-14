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

const FUB_BASE_URL = "https://api.followupboss.com/v1";
const TEAM_CACHE_KEY = "dashboard:fub:team:v1";
const PAGE_LIMIT = 100;
const MAX_PAGES = 100;

export interface TeamDealTotals {
  commission: number;
  sales: number;
  volume: number;
  activeAgents: number;
}

interface TeamCache extends TeamDealTotals {
  version: 1;
  stageKey: string;
  fetchedAt: string;
}

function headersFor(config: FollowUpBossConfig): Headers {
  const headers = new Headers({
    Authorization: `Basic ${btoa(`${config.apiKey}:`)}`,
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
    const url = new URL(`${FUB_BASE_URL}/${endpoint}`);
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
    let total: number | null = null;
    if (isRecord(payload["_metadata"]) && payload["_metadata"]["total"] !== undefined) {
      total = requireCount(payload["_metadata"]["total"], "fub_team_total");
    }
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

function normalize(value: string): string {
  return value.trim().toLocaleLowerCase("en-US");
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
  if (
    match?.[1] === undefined ||
    !Number.isFinite(Date.parse(`${match[1]}T00:00:00.000Z`))
  ) {
    throw new UpstreamRequestError("schema");
  }
  return match[1];
}

function userIds(value: unknown): string[] {
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

function requiredMoney(value: unknown, field: string): number {
  void field;
  if (
    (typeof value !== "number" && typeof value !== "string") ||
    String(value).trim() === ""
  ) {
    throw new UpstreamRequestError("schema");
  }
  const parsed = Number(value);
  try {
    return requireSpend(parsed);
  } catch {
    throw new UpstreamRequestError("schema");
  }
}

export function aggregateClosedDeals(
  deals: unknown[],
  stageIds: Set<number>,
  reportingPeriod: DashboardSnapshot["yearToDatePeriod"],
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
    if (
      closeDate < reportingPeriod.startDate ||
      closeDate > reportingPeriod.endDate
    ) {
      continue;
    }
    requireCount(deal["id"], "fub_deal_id");
    sales += 1;
    volume += requiredMoney(deal["price"], "fub_deal_price");
    const commissionValue = deal["commissionValue"] ?? deal["commission"];
    commission += requiredMoney(commissionValue, "fub_deal_commission");
    for (const id of userIds(deal["users"])) {
      agents.add(id);
    }
  }

  return {
    commission: requireSpend(commission),
    sales: requireCount(sales, "fub_team_sales"),
    volume: requireSpend(volume),
    activeAgents: requireCount(agents.size, "fub_team_active_agents"),
  };
}

function validTotals(value: unknown): value is TeamDealTotals {
  if (!isRecord(value)) {
    return false;
  }
  const commission = value["commission"];
  const sales = value["sales"];
  const volume = value["volume"];
  const activeAgents = value["activeAgents"];
  return typeof commission === "number" &&
    Number.isFinite(commission) && commission >= 0 &&
    typeof sales === "number" && Number.isSafeInteger(sales) && sales >= 0 &&
    typeof volume === "number" && Number.isFinite(volume) && volume >= 0 &&
    typeof activeAgents === "number" &&
    Number.isSafeInteger(activeAgents) && activeAgents >= 0;
}

function parseCache(
  value: unknown,
  stageKey: string,
  now: Date,
  refreshMs: number,
): TeamCache | null {
  if (
    !isRecord(value) ||
    value["version"] !== 1 ||
    value["stageKey"] !== stageKey ||
    typeof value["fetchedAt"] !== "string" ||
    !Number.isFinite(Date.parse(value["fetchedAt"])) ||
    now.getTime() - Date.parse(value["fetchedAt"]) < 0 ||
    now.getTime() - Date.parse(value["fetchedAt"]) > refreshMs ||
    !validTotals(value)
  ) {
    return null;
  }
  return value as unknown as TeamCache;
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
    responseStatus:
      error instanceof UpstreamRequestError ? error.responseStatus : null,
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

export async function fetchFollowUpBossTeamMetrics(
  env: DashboardEnv,
  reportingPeriod: DashboardSnapshot["yearToDatePeriod"],
  dependencies: RuntimeDependencies = {},
): Promise<FollowUpBossTeamMetricResults> {
  const started = Date.now();
  const config = readFollowUpBossConfig(env);
  if (config.apiKey === "" || config.closedDealStageNames.length === 0) {
    return allSame({
      kind: "unconfigured",
      durationMs: Date.now() - started,
      responseStatus: null,
    });
  }

  const now = dependencies.now ?? new Date();
  const stageKey = config.closedDealStageNames.map(normalize).sort().join(",");
  try {
    const stored = await env.DASHBOARD_KV.get(TEAM_CACHE_KEY);
    if (stored !== null) {
      const cached = parseCache(
        JSON.parse(stored) as unknown,
        stageKey,
        now,
        config.teamRefreshMs,
      );
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

  try {
    const headers = headersFor(config);
    const [pipelines, deals] = await Promise.all([
      listCollection("pipelines", "pipelines", {}, headers, dependencies),
      listCollection(
        "deals",
        "deals",
        { includeArchived: "1" },
        headers,
        dependencies,
      ),
    ]);
    const totals = aggregateClosedDeals(
      deals,
      closedStageIds(pipelines, config.closedDealStageNames),
      reportingPeriod,
    );
    const observedAt = now.toISOString();
    try {
      await env.DASHBOARD_KV.put(
        TEAM_CACHE_KEY,
        JSON.stringify({
          version: 1,
          stageKey,
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
    return toResults(totals, started, observedAt);
  } catch (error) {
    return allSame(errorResult(error, started));
  }
}
