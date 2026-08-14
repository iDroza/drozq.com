import { CONFIG_DEFAULTS } from "./config";
import {
  getReportingPeriod,
  getRollingPeriod,
  getYearToDatePeriod,
  isIsoUtcTimestamp,
  isMetricStale,
} from "./lib/date";
import { isFiniteNonnegative, MAX_COUNT, MAX_SPEND_USD } from "./lib/numeric";
import type {
  DashboardMetric,
  DashboardMetricKey,
  DashboardSnapshot,
  MetricSource,
  MetricStatus,
} from "./types";

interface MetricSpec {
  source: MetricSource;
  definition: string;
  staleAfterMs: number;
}

const FAST_STALE_MS = 5 * 60 * 1_000;
const TEAM_STALE_MS = 15 * 60 * 1_000;
const SHEETS_STALE_MS = 15 * 60 * 1_000;
const SEARCH_STALE_MS = 26 * 60 * 60 * 1_000;

export const METRIC_KEYS = [
  "callsToday",
  "textsToday",
  "emailsToday",
  "appointmentsSetMtd",
  "freshBuyerLeads",
  "freshSellerLeads",
  "googleAdsSpendMtd",
  "googleAdsLeadsMtd",
  "googleAdsSpendRolling90d",
  "googleAdsClicksRolling90d",
  "googleAdsLeadsRolling90d",
  "googleAdsCostPerLeadRolling90d",
  "activeRealtyClicksRolling90d",
  "activeRealtyImpressionsRolling90d",
  "activeRealtyCtrRolling90d",
  "activeRealtyPositionRolling90d",
  "jtClicksRolling90d",
  "jtImpressionsRolling90d",
  "jtCtrRolling90d",
  "jtPositionRolling90d",
  "teamCommissionYtd",
  "teamSalesYtd",
  "teamVolumeYtd",
  "teamActiveAgentsYtd",
  "shellPagesRemaining",
  "setsRemaining",
] as const satisfies readonly DashboardMetricKey[];

export const METRIC_SPECS = {
  callsToday: {
    source: "follow_up_boss",
    definition: "Outbound calls made today by the authenticated Follow Up Boss user.",
    staleAfterMs: FAST_STALE_MS,
  },
  textsToday: {
    source: "follow_up_boss",
    definition: "Manual outbound text messages sent today by the authenticated Follow Up Boss user.",
    staleAfterMs: FAST_STALE_MS,
  },
  emailsToday: {
    source: "follow_up_boss",
    definition: "Manual outbound emails sent today by the authenticated Follow Up Boss user.",
    staleAfterMs: FAST_STALE_MS,
  },
  appointmentsSetMtd: {
    source: "follow_up_boss",
    definition: "Appointments created this month by the authenticated Follow Up Boss user.",
    staleAfterMs: FAST_STALE_MS,
  },
  freshBuyerLeads: {
    source: "follow_up_boss",
    definition: "Accessible non-trash buyer contacts created during the rolling previous four weeks.",
    staleAfterMs: FAST_STALE_MS,
  },
  freshSellerLeads: {
    source: "follow_up_boss",
    definition: "Accessible non-trash contacts tagged Seller and created during the rolling previous four weeks.",
    staleAfterMs: FAST_STALE_MS,
  },
  googleAdsSpendMtd: {
    source: "google_ads",
    definition: "Total month-to-date Google Ads cost across every accessible non-manager account.",
    staleAfterMs: FAST_STALE_MS,
  },
  googleAdsLeadsMtd: {
    source: "google_ads",
    definition: "Total month-to-date primary Google Ads conversions across every accessible non-manager account.",
    staleAfterMs: FAST_STALE_MS,
  },
  googleAdsSpendRolling90d: {
    source: "google_ads",
    definition: "Total Google Ads cost during the rolling previous 90 days across every accessible non-manager account.",
    staleAfterMs: FAST_STALE_MS,
  },
  googleAdsClicksRolling90d: {
    source: "google_ads",
    definition: "Total Google Ads clicks during the rolling previous 90 days across every accessible non-manager account.",
    staleAfterMs: FAST_STALE_MS,
  },
  googleAdsLeadsRolling90d: {
    source: "google_ads",
    definition: "Total primary Google Ads conversions during the rolling previous 90 days across every accessible non-manager account.",
    staleAfterMs: FAST_STALE_MS,
  },
  googleAdsCostPerLeadRolling90d: {
    source: "google_ads",
    definition: "Rolling 90-day Google Ads cost divided by primary conversions across every accessible non-manager account.",
    staleAfterMs: FAST_STALE_MS,
  },
  activeRealtyClicksRolling90d: {
    source: "google_search_console",
    definition: "Total Google Search clicks for activerealty.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  activeRealtyImpressionsRolling90d: {
    source: "google_search_console",
    definition: "Total Google Search impressions for activerealty.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  activeRealtyCtrRolling90d: {
    source: "google_search_console",
    definition: "Average Google Search click-through rate for activerealty.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  activeRealtyPositionRolling90d: {
    source: "google_search_console",
    definition: "Average Google Search result position for activerealty.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  jtClicksRolling90d: {
    source: "google_search_console",
    definition: "Total Google Search clicks for justintye.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  jtImpressionsRolling90d: {
    source: "google_search_console",
    definition: "Total Google Search impressions for justintye.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  jtCtrRolling90d: {
    source: "google_search_console",
    definition: "Average Google Search click-through rate for justintye.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  jtPositionRolling90d: {
    source: "google_search_console",
    definition: "Average Google Search result position for justintye.com during the rolling previous 90 days.",
    staleAfterMs: SEARCH_STALE_MS,
  },
  teamCommissionYtd: {
    source: "follow_up_boss",
    definition: "Company Team Split recorded on year-to-date closed Follow Up Boss deals across all configured pipelines.",
    staleAfterMs: TEAM_STALE_MS,
  },
  teamSalesYtd: {
    source: "follow_up_boss",
    definition: "Number of year-to-date closed Follow Up Boss deals across all configured pipelines.",
    staleAfterMs: TEAM_STALE_MS,
  },
  teamVolumeYtd: {
    source: "follow_up_boss",
    definition: "Total price of year-to-date closed Follow Up Boss deals across all configured pipelines.",
    staleAfterMs: TEAM_STALE_MS,
  },
  teamActiveAgentsYtd: {
    source: "follow_up_boss",
    definition: "Distinct Follow Up Boss users attached to at least one year-to-date closed deal.",
    staleAfterMs: TEAM_STALE_MS,
  },
  shellPagesRemaining: {
    source: "google_sheets",
    definition: "Incomplete shell pages remaining in the configured Google Sheet.",
    staleAfterMs: SHEETS_STALE_MS,
  },
  setsRemaining: {
    source: "google_sheets",
    definition: "Work sets remaining in the configured Google Sheet.",
    staleAfterMs: SHEETS_STALE_MS,
  },
} as const satisfies Record<DashboardMetricKey, MetricSpec>;

const INTEGER_METRICS = new Set<DashboardMetricKey>([
  "callsToday",
  "textsToday",
  "emailsToday",
  "appointmentsSetMtd",
  "freshBuyerLeads",
  "freshSellerLeads",
  "googleAdsClicksRolling90d",
  "activeRealtyClicksRolling90d",
  "activeRealtyImpressionsRolling90d",
  "jtClicksRolling90d",
  "jtImpressionsRolling90d",
  "teamSalesYtd",
  "teamActiveAgentsYtd",
  "shellPagesRemaining",
  "setsRemaining",
]);

const CURRENCY_METRICS = new Set<DashboardMetricKey>([
  "googleAdsSpendMtd",
  "googleAdsSpendRolling90d",
  "googleAdsCostPerLeadRolling90d",
  "teamCommissionYtd",
  "teamVolumeYtd",
]);

const RATE_METRICS = new Set<DashboardMetricKey>([
  "activeRealtyCtrRolling90d",
  "jtCtrRolling90d",
]);

const POSITION_METRICS = new Set<DashboardMetricKey>([
  "activeRealtyPositionRolling90d",
  "jtPositionRolling90d",
]);

const VALID_STATUSES = new Set<MetricStatus>([
  "ok",
  "stale",
  "error",
  "unconfigured",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validIsoDate(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/u.test(value)) {
    return false;
  }
  const parsed = Date.parse(`${value}T00:00:00.000Z`);
  return Number.isFinite(parsed) && new Date(parsed).toISOString().startsWith(value);
}

function sanitizeMetric(
  value: unknown,
  key: DashboardMetricKey,
): DashboardMetric | null {
  if (!isRecord(value)) {
    return null;
  }
  const spec = METRIC_SPECS[key];
  const rawValue = value["value"];
  const status = value["status"];
  const updatedAt = value["updatedAt"];
  const maximum = CURRENCY_METRICS.has(key)
    ? MAX_SPEND_USD
    : RATE_METRICS.has(key)
      ? 1
      : POSITION_METRICS.has(key)
        ? 1_000
        : MAX_COUNT;

  if (
    value["source"] !== spec.source ||
    typeof status !== "string" ||
    !VALID_STATUSES.has(status as MetricStatus) ||
    (rawValue !== null &&
      (!isFiniteNonnegative(rawValue) ||
        rawValue > maximum ||
        (INTEGER_METRICS.has(key) && !Number.isSafeInteger(rawValue)))) ||
    (updatedAt !== null && !isIsoUtcTimestamp(updatedAt))
  ) {
    return null;
  }

  const typedStatus = status as MetricStatus;
  if ((rawValue === null) !== (updatedAt === null)) {
    return null;
  }
  if ((typedStatus === "ok" || typedStatus === "stale") && rawValue === null) {
    return null;
  }
  if (
    (typedStatus === "error" || typedStatus === "unconfigured") &&
    rawValue !== null
  ) {
    return null;
  }

  return {
    value: rawValue,
    source: spec.source,
    updatedAt,
    status: typedStatus,
    definition: spec.definition,
  };
}

function sanitizePeriod(
  value: unknown,
): DashboardSnapshot["reportingPeriod"] | null {
  if (!isRecord(value)) {
    return null;
  }
  const startDate = value["startDate"];
  const endDate = value["endDate"];
  const timeZone = value["timeZone"];
  if (
    !validIsoDate(startDate) ||
    !validIsoDate(endDate) ||
    startDate > endDate ||
    typeof timeZone !== "string" ||
    timeZone.trim() === "" ||
    timeZone.length > 100
  ) {
    return null;
  }
  return { startDate, endDate, timeZone };
}

function snapshotTimestamps(value: Record<string, unknown>): {
  lastAttemptAt: string;
  lastSuccessfulFullSyncAt: string | null;
} | null {
  const lastAttemptAt = value["lastAttemptAt"];
  const lastSuccessfulFullSyncAt = value["lastSuccessfulFullSyncAt"];
  if (
    !isIsoUtcTimestamp(lastAttemptAt) ||
    (lastSuccessfulFullSyncAt !== null &&
      !isIsoUtcTimestamp(lastSuccessfulFullSyncAt))
  ) {
    return null;
  }
  return { lastAttemptAt, lastSuccessfulFullSyncAt };
}

export function sanitizeSnapshot(value: unknown): DashboardSnapshot | null {
  if (
    !isRecord(value) ||
    value["version"] !== 2 ||
    !isRecord(value["metrics"])
  ) {
    return null;
  }
  const metrics = {} as DashboardSnapshot["metrics"];
  for (const key of METRIC_KEYS) {
    const metric = sanitizeMetric(value["metrics"][key], key);
    if (metric === null) {
      return null;
    }
    metrics[key] = metric;
  }
  const reportingPeriod = sanitizePeriod(value["reportingPeriod"]);
  const rolling90DayPeriod = sanitizePeriod(value["rolling90DayPeriod"]);
  const yearToDatePeriod = sanitizePeriod(value["yearToDatePeriod"]);
  const timestamps = snapshotTimestamps(value);
  if (
    reportingPeriod === null ||
    rolling90DayPeriod === null ||
    yearToDatePeriod === null ||
    timestamps === null
  ) {
    return null;
  }
  return {
    version: 2,
    metrics,
    reportingPeriod,
    rolling90DayPeriod,
    yearToDatePeriod,
    ...timestamps,
  };
}

function unavailableMetric(key: DashboardMetricKey): DashboardMetric {
  const spec = METRIC_SPECS[key];
  return {
    value: null,
    source: spec.source,
    updatedAt: null,
    status: "unconfigured",
    definition: spec.definition,
  };
}

export function sanitizeStoredSnapshot(value: unknown): DashboardSnapshot | null {
  const strict = sanitizeSnapshot(value);
  if (strict !== null) {
    return strict;
  }
  if (
    !isRecord(value) ||
    value["version"] !== 2 ||
    !isRecord(value["metrics"])
  ) {
    return null;
  }
  const reportingPeriod = sanitizePeriod(value["reportingPeriod"]);
  const timestamps = snapshotTimestamps(value);
  if (reportingPeriod === null || timestamps === null) {
    return null;
  }
  const metrics = {} as DashboardSnapshot["metrics"];
  for (const key of METRIC_KEYS) {
    const raw = value["metrics"][key];
    if (raw === undefined) {
      metrics[key] = unavailableMetric(key);
      continue;
    }
    const metric = sanitizeMetric(raw, key);
    if (metric === null) {
      return null;
    }
    metrics[key] = metric;
  }
  const referenceDate = new Date(`${reportingPeriod.endDate}T12:00:00.000Z`);
  return {
    version: 2,
    metrics,
    reportingPeriod,
    rolling90DayPeriod: getRollingPeriod(
      referenceDate,
      reportingPeriod.timeZone,
      90,
    ),
    yearToDatePeriod: getYearToDatePeriod(
      referenceDate,
      reportingPeriod.timeZone,
    ),
    ...timestamps,
  };
}

export function createUnconfiguredSnapshot(
  now: Date,
  timeZone: string = CONFIG_DEFAULTS.reportingTimeZone,
): DashboardSnapshot {
  const metrics = {} as DashboardSnapshot["metrics"];
  for (const key of METRIC_KEYS) {
    metrics[key] = unavailableMetric(key);
  }
  return {
    version: 2,
    metrics,
    reportingPeriod: getReportingPeriod(now, timeZone),
    rolling90DayPeriod: getRollingPeriod(now, timeZone, 90),
    yearToDatePeriod: getYearToDatePeriod(now, timeZone),
    lastAttemptAt: "1970-01-01T00:00:00.000Z",
    lastSuccessfulFullSyncAt: null,
  };
}

export function toPublicSnapshot(
  snapshot: DashboardSnapshot,
  now: Date,
): DashboardSnapshot {
  const sanitized = sanitizeSnapshot(snapshot);
  if (sanitized === null) {
    throw new TypeError("invalid_snapshot");
  }
  for (const key of METRIC_KEYS) {
    const metric = sanitized.metrics[key];
    if (
      metric.status === "ok" &&
      isMetricStale(metric.updatedAt, now, METRIC_SPECS[key].staleAfterMs)
    ) {
      metric.status = "stale";
    }
  }
  return sanitized;
}
