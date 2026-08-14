import { readReportingTimeZone } from "./config";
import {
  getReportingPeriod,
  getRollingPeriod,
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
import { fetchGoogleAdsMetrics } from "./sources/google-ads";
import { fetchGoogleSearchConsoleMetrics } from "./sources/google-search-console";
import type {
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
  rolling90DayPeriod: DashboardSnapshot["rolling90DayPeriod"] = getRollingPeriod(
    now,
    reportingPeriod.timeZone,
    90,
  ),
  yearToDatePeriod: DashboardSnapshot["yearToDatePeriod"] = getYearToDatePeriod(
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
  } catch {
    console.error(
      JSON.stringify({ source: "dashboard_kv", category: "malformed_json", status: null }),
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
  };
}

function adsFailure(): GoogleAdsMetricResults {
  return {
    googleAdsSpendMtd: unexpectedResult(),
    googleAdsLeadsMtd: unexpectedResult(),
    googleAdsSpendRolling90d: unexpectedResult(),
    googleAdsClicksRolling90d: unexpectedResult(),
    googleAdsLeadsRolling90d: unexpectedResult(),
    googleAdsCostPerLeadRolling90d: unexpectedResult(),
  };
}

function teamFailure(): FollowUpBossTeamMetricResults {
  return {
    teamCommissionYtd: unexpectedResult(),
    teamSalesYtd: unexpectedResult(),
    teamVolumeYtd: unexpectedResult(),
    teamActiveAgentsYtd: unexpectedResult(),
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

export async function synchronizeDashboard(
  env: DashboardEnv,
  dependencies: RuntimeDependencies = {},
): Promise<DashboardSnapshot> {
  const now = dependencies.now ?? new Date();
  const timeZone = readReportingTimeZone(env);
  const reportingPeriod = getReportingPeriod(now, timeZone);
  const rolling90DayPeriod = getRollingPeriod(now, timeZone, 90);
  const yearToDatePeriod = getYearToDatePeriod(now, timeZone);
  const previous = await loadPreviousSnapshot(env);

  const [fubSettled, adsSettled, searchSettled, teamSettled] =
    await Promise.allSettled([
      fetchFollowUpBossMetrics(env, timeZone, { ...dependencies, now }),
      fetchGoogleAdsMetrics(
        env,
        reportingPeriod,
        rolling90DayPeriod,
        { ...dependencies, now },
      ),
      fetchGoogleSearchConsoleMetrics(
        env,
        rolling90DayPeriod,
        { ...dependencies, now },
      ),
      fetchFollowUpBossTeamMetrics(
        env,
        yearToDatePeriod,
        { ...dependencies, now },
      ),
    ]);
  const fub = fubSettled.status === "fulfilled" ? fubSettled.value : fubFailure();
  const ads = adsSettled.status === "fulfilled" ? adsSettled.value : adsFailure();
  const search = searchSettled.status === "fulfilled"
    ? searchSettled.value
    : searchConsoleFailure();
  const team = teamSettled.status === "fulfilled"
    ? teamSettled.value
    : teamFailure();
  const results: MetricResultMap = {
    ...fub,
    ...ads,
    ...search,
    ...team,
  };

  logMetricResults(results);
  const snapshot = mergeSnapshot(
    previous,
    results,
    now,
    reportingPeriod,
    rolling90DayPeriod,
    yearToDatePeriod,
  );
  await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify(snapshot));
  return toPublicSnapshot(snapshot, now);
}
