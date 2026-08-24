import {
  CONFIG_DEFAULTS,
  readGoogleAdsConfig,
  readReportingTimeZone,
} from "./config";
import {
  getFixedStartPeriod,
  getReportingPeriod,
  getRollingPeriod,
  getSearchConsoleThreeMonthPeriod,
  getYearToDatePeriod,
  isIsoUtcTimestamp,
} from "./lib/date";
import { isFiniteNonnegative } from "./lib/numeric";
import {
  METRIC_KEYS,
  METRIC_SPECS,
  sanitizeStoredSnapshot,
  toPublicSnapshot,
} from "./snapshot";
import { fetchFollowUpBossMetrics } from "./sources/follow-up-boss";
import { fetchFollowUpBossTeamMetrics } from "./sources/follow-up-boss-team";
import { fetchActiveRealtyProgressMetrics } from "./sources/active-realty-progress";
import { fetchGoogleAdsMetrics } from "./sources/google-ads";
import { fetchGoogleSearchConsoleMetrics } from "./sources/google-search-console";
import type {
  ActiveRealtyProgressMetricResults,
  DashboardEnv,
  DashboardMetric,
  DashboardMetricKey,
  DashboardSnapshot,
  FollowUpBossMetricResults,
  FollowUpBossTeamMetricResults,
  GoogleAdsMetricResults,
  GoogleSearchConsoleMetricResults,
  MetricFetchResult,
  RuntimeDependencies,
} from "./types";

export const SNAPSHOT_KEY = "dashboard:snapshot:v2";

export type MetricResultMap = Record<DashboardMetricKey, MetricFetchResult>;

function unexpectedResult(): MetricFetchResult {
  return {
    kind: "error",
    category: "unexpected",
    durationMs: 0,
    responseStatus: null,
  };
}

function hasValidPreviousValue(
  metric: DashboardMetric | undefined,
): metric is DashboardMetric & { value: number; updatedAt: string } {
  return (
    metric !== undefined &&
    isFiniteNonnegative(metric.value) &&
    metric.updatedAt !== null
  );
}

function mergeMetric(
  key: DashboardMetricKey,
  previous: DashboardMetric | undefined,
  result: MetricFetchResult,
  synchronizedAt: string,
): DashboardMetric {
  const spec = METRIC_SPECS[key];
  if (result.kind === "ok") {
    if (!isFiniteNonnegative(result.value)) {
      throw new RangeError("invalid_metric_result");
    }
    const updatedAt = result.observedAt ?? synchronizedAt;
    if (!isIsoUtcTimestamp(updatedAt)) {
      throw new RangeError("invalid_metric_timestamp");
    }
    return {
      value: result.value,
      source: spec.source,
      updatedAt,
      status: "ok",
      definition: spec.definition,
    };
  }

  if (result.kind === "unconfigured") {
    return {
      value: null,
      source: spec.source,
      updatedAt: null,
      status: "unconfigured",
      definition: spec.definition,
    };
  }

  if (hasValidPreviousValue(previous)) {
    return {
      value: previous.value,
      source: spec.source,
      updatedAt: previous.updatedAt,
      status: "stale",
      definition: spec.definition,
    };
  }

  return {
    value: null,
    source: spec.source,
    updatedAt: null,
    status: "error",
    definition: spec.definition,
  };
}

export function mergeSnapshot(
  previous: DashboardSnapshot | null,
  results: MetricResultMap,
  now: Date,
  reportingPeriod: DashboardSnapshot["reportingPeriod"],
  rolling90DayPeriod: DashboardSnapshot["rolling90DayPeriod"] =
    getSearchConsoleThreeMonthPeriod(
      reportingPeriod.endDate,
    ),
  yearToDatePeriod: DashboardSnapshot["yearToDatePeriod"] = getYearToDatePeriod(
    now,
    reportingPeriod.timeZone,
  ),
  sellerCampaignPeriod: DashboardSnapshot["sellerCampaignPeriod"] =
    getFixedStartPeriod(
      CONFIG_DEFAULTS.googleAdsSellerCampaignLaunchDate,
      now,
      reportingPeriod.timeZone,
    ),
): DashboardSnapshot {
  const synchronizedAt = now.toISOString();
  const configured = Object.values(results).filter(
    (result) => result.kind !== "unconfigured",
  );
  const fullSyncSucceeded =
    configured.length > 0 && configured.every((result) => result.kind === "ok");
  const metrics = {} as DashboardSnapshot["metrics"];
  for (const key of METRIC_KEYS) {
    metrics[key] = mergeMetric(
      key,
      previous?.metrics[key],
      results[key],
      synchronizedAt,
    );
  }

  return {
    version: 2,
    metrics,
    reportingPeriod,
    rolling90DayPeriod,
    yearToDatePeriod,
    sellerCampaignPeriod,
    lastAttemptAt: synchronizedAt,
    lastSuccessfulFullSyncAt: fullSyncSucceeded
      ? synchronizedAt
      : (previous?.lastSuccessfulFullSyncAt ?? null),
  };
}

async function loadPreviousSnapshot(env: DashboardEnv): Promise<DashboardSnapshot | null> {
  const stored = await env.DASHBOARD_KV.get(SNAPSHOT_KEY);
  if (stored === null) {
    return null;
  }
  try {
    const snapshot = sanitizeStoredSnapshot(JSON.parse(stored) as unknown);
    if (snapshot === null) {
      console.error(
        JSON.stringify({ source: "dashboard_kv", category: "schema", status: null }),
      );
    }
    return snapshot;
  } catch (error) {
    console.error(
      JSON.stringify({
        source: "dashboard_kv",
        category: "malformed_json",
        status: null,
        detail: error instanceof Error
          ? `${error.name}: ${error.message}`
          : String(error),
      }),
    );
    return null;
  }
}

function logMetricResults(results: MetricResultMap): void {
  for (const [metric, result] of Object.entries(results)) {
    console.log(
      JSON.stringify({
        source: METRIC_SPECS[metric as DashboardMetricKey].source,
        metric,
        result: result.kind,
        category: result.kind === "error" ? result.category : null,
        status: result.responseStatus,
        durationMs: result.durationMs,
      }),
    );
  }
}

function fubFailure(): FollowUpBossMetricResults {
  return {
    callsToday: unexpectedResult(),
    textsToday: unexpectedResult(),
    emailsToday: unexpectedResult(),
    appointmentsSetMtd: unexpectedResult(),
    freshBuyerLeads: unexpectedResult(),
    freshSellerLeads: unexpectedResult(),
    totalDialsYtd: unexpectedResult(),
  };
}

function adsFailure(): GoogleAdsMetricResults {
  return {
    googleAdsSpendMtd: unexpectedResult(),
    googleAdsLeadsMtd: unexpectedResult(),
    googleAdsCostPerClickMtd: unexpectedResult(),
    googleAdsCostPerLeadMtd: unexpectedResult(),
    googleAdsSpendYtd: unexpectedResult(),
    googleAdsLeadsYtd: unexpectedResult(),
    googleAdsCostPerLeadYtd: unexpectedResult(),
    sellerCampaignSpend: unexpectedResult(),
    sellerCampaignCostPerClick: unexpectedResult(),
    sellerCampaignCtr: unexpectedResult(),
    sellerCampaignCostPerLead: unexpectedResult(),
  };
}

export function deriveTeamCommissionRoas(
  commission: MetricFetchResult,
  adSpend: MetricFetchResult,
): MetricFetchResult {
  const durationMs = Math.max(commission.durationMs, adSpend.durationMs);
  if (commission.kind === "ok" && adSpend.kind === "ok") {
    if (adSpend.value === 0) {
      return {
        kind: "error",
        category: "no_data",
        durationMs,
        responseStatus: 200,
      };
    }
    const value = commission.value / adSpend.value;
    if (!isFiniteNonnegative(value)) {
      return {
        kind: "error",
        category: "schema",
        durationMs,
        responseStatus: 200,
      };
    }
    return { kind: "ok", value, durationMs, responseStatus: 200 };
  }
  const failedInput = commission.kind === "error"
    ? commission
    : adSpend.kind === "error"
      ? adSpend
      : null;
  if (failedInput !== null) {
    return {
      kind: "error",
      category: failedInput.category,
      durationMs,
      responseStatus: failedInput.responseStatus,
    };
  }
  return { kind: "unconfigured", durationMs, responseStatus: null };
}

function teamFailure(): FollowUpBossTeamMetricResults {
  return {
    teamCommissionYtd: unexpectedResult(),
    teamSalesYtd: unexpectedResult(),
    teamVolumeYtd: unexpectedResult(),
    teamActiveAgentsYtd: unexpectedResult(),
    personalDealsClosedYtd: unexpectedResult(),
  };
}

function searchConsoleFailure(): GoogleSearchConsoleMetricResults {
  return {
    activeRealtyClicksRolling90d: unexpectedResult(),
    activeRealtyImpressionsRolling90d: unexpectedResult(),
    activeRealtyCtrRolling90d: unexpectedResult(),
    activeRealtyPositionRolling90d: unexpectedResult(),
    jtClicksRolling90d: unexpectedResult(),
    jtImpressionsRolling90d: unexpectedResult(),
    jtCtrRolling90d: unexpectedResult(),
    jtPositionRolling90d: unexpectedResult(),
  };
}

function activeRealtyProgressFailure(): ActiveRealtyProgressMetricResults {
  return {
    shellPagesRemaining: unexpectedResult(),
    setsRemaining: unexpectedResult(),
  };
}

export async function synchronizeDashboard(
  env: DashboardEnv,
  dependencies: RuntimeDependencies = {},
): Promise<DashboardSnapshot> {
  const now = dependencies.now ?? new Date();
  const timeZone = readReportingTimeZone(env);
  const reportingPeriod = getReportingPeriod(now, timeZone);
  const rolling90DayPeriod = getRollingPeriod(now, timeZone, 90);
  const yearToDatePeriod = getYearToDatePeriod(now, timeZone);
  const sellerCampaignPeriod = getFixedStartPeriod(
    readGoogleAdsConfig(env).sellerCampaignLaunchDate,
    now,
    timeZone,
  );
  const previous = await loadPreviousSnapshot(env);

  const [fubSettled, adsSettled, searchSettled, teamSettled, progressSettled] =
    await Promise.allSettled([
      fetchFollowUpBossMetrics(env, timeZone, { ...dependencies, now }),
      fetchGoogleAdsMetrics(
        env,
        reportingPeriod,
        yearToDatePeriod,
        { ...dependencies, now },
        sellerCampaignPeriod,
      ),
      fetchGoogleSearchConsoleMetrics(
        env,
        { ...dependencies, now },
      ),
      fetchFollowUpBossTeamMetrics(
        env,
        yearToDatePeriod,
        { ...dependencies, now },
      ),
      fetchActiveRealtyProgressMetrics(env),
    ]);
  const fub = fubSettled.status === "fulfilled" ? fubSettled.value : fubFailure();
  const ads = adsSettled.status === "fulfilled" ? adsSettled.value : adsFailure();
  const search = searchSettled.status === "fulfilled"
    ? searchSettled.value.metrics
    : searchConsoleFailure();
  const searchConsolePeriod = searchSettled.status === "fulfilled"
    ? searchSettled.value.period
    : null;
  const team = teamSettled.status === "fulfilled"
    ? teamSettled.value
    : teamFailure();
  const progress = progressSettled.status === "fulfilled"
    ? progressSettled.value
    : activeRealtyProgressFailure();
  const results: MetricResultMap = {
    ...fub,
    ...ads,
    teamCommissionRoasYtd: deriveTeamCommissionRoas(
      team.teamCommissionYtd,
      ads.googleAdsSpendYtd,
    ),
    ...search,
    ...team,
    ...progress,
  };

  logMetricResults(results);
  const snapshot = mergeSnapshot(
    previous,
    results,
    now,
    reportingPeriod,
    searchConsolePeriod ?? previous?.rolling90DayPeriod ?? rolling90DayPeriod,
    yearToDatePeriod,
    sellerCampaignPeriod,
  );
  await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify(snapshot));
  return toPublicSnapshot(snapshot, now);
}
