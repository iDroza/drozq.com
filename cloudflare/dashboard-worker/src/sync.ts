import { readReportingTimeZone } from "./config";
import { getReportingPeriod } from "./lib/date";
import { isFiniteNonnegative } from "./lib/numeric";
import { METRIC_SPECS, sanitizeSnapshot, toPublicSnapshot } from "./snapshot";
import { fetchSellerLeads } from "./sources/follow-up-boss";
import { fetchGoogleAdsMetrics } from "./sources/google-ads";
import { fetchShellPagesRemaining } from "./sources/google-sheets";
import type {
  DashboardEnv,
  DashboardMetric,
  DashboardMetricKey,
  DashboardSnapshot,
  GoogleAdsMetricResults,
  MetricFetchResult,
  RuntimeDependencies,
} from "./types";

export const SNAPSHOT_KEY = "dashboard:snapshot:v1";

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
    return {
      value: result.value,
      source: spec.source,
      updatedAt: synchronizedAt,
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
): DashboardSnapshot {
  const synchronizedAt = now.toISOString();
  const configured = Object.values(results).filter(
    (result) => result.kind !== "unconfigured",
  );
  const fullSyncSucceeded =
    configured.length > 0 && configured.every((result) => result.kind === "ok");

  return {
    version: 1,
    metrics: {
      sellerLeads: mergeMetric(
        "sellerLeads",
        previous?.metrics.sellerLeads,
        results.sellerLeads,
        synchronizedAt,
      ),
      googleAdsSpendMtd: mergeMetric(
        "googleAdsSpendMtd",
        previous?.metrics.googleAdsSpendMtd,
        results.googleAdsSpendMtd,
        synchronizedAt,
      ),
      googleAdsLeadsMtd: mergeMetric(
        "googleAdsLeadsMtd",
        previous?.metrics.googleAdsLeadsMtd,
        results.googleAdsLeadsMtd,
        synchronizedAt,
      ),
      shellPagesRemaining: mergeMetric(
        "shellPagesRemaining",
        previous?.metrics.shellPagesRemaining,
        results.shellPagesRemaining,
        synchronizedAt,
      ),
    },
    reportingPeriod,
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
    const snapshot = sanitizeSnapshot(JSON.parse(stored) as unknown);
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

function adsFailure(reason: unknown): GoogleAdsMetricResults {
  void reason;
  return {
    googleAdsSpendMtd: unexpectedResult(),
    googleAdsLeadsMtd: unexpectedResult(),
  };
}

export async function synchronizeDashboard(
  env: DashboardEnv,
  dependencies: RuntimeDependencies = {},
): Promise<DashboardSnapshot> {
  const now = dependencies.now ?? new Date();
  const reportingPeriod = getReportingPeriod(now, readReportingTimeZone(env));
  const previous = await loadPreviousSnapshot(env);

  const [fubSettled, adsSettled, sheetsSettled] = await Promise.allSettled([
    fetchSellerLeads(env, dependencies),
    fetchGoogleAdsMetrics(env, reportingPeriod, dependencies),
    fetchShellPagesRemaining(env, dependencies),
  ]);

  const fub =
    fubSettled.status === "fulfilled" ? fubSettled.value : unexpectedResult();
  const ads =
    adsSettled.status === "fulfilled"
      ? adsSettled.value
      : adsFailure(adsSettled.reason);
  const sheets =
    sheetsSettled.status === "fulfilled"
      ? sheetsSettled.value
      : unexpectedResult();
  const results: MetricResultMap = {
    sellerLeads: fub,
    googleAdsSpendMtd: ads.googleAdsSpendMtd,
    googleAdsLeadsMtd: ads.googleAdsLeadsMtd,
    shellPagesRemaining: sheets,
  };

  logMetricResults(results);
  const snapshot = mergeSnapshot(previous, results, now, reportingPeriod);
  await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify(snapshot));
  return toPublicSnapshot(snapshot, now);
}
