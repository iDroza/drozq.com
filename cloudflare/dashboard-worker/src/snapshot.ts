import { CONFIG_DEFAULTS } from "./config";
import { getReportingPeriod, isIsoUtcTimestamp, isMetricStale } from "./lib/date";
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
}

export const METRIC_KEYS = [
  "callsToday",
  "textsToday",
  "emailsToday",
  "appointmentsSetMtd",
  "freshBuyerLeads",
  "freshSellerLeads",
  "googleAdsSpendMtd",
  "googleAdsLeadsMtd",
] as const satisfies readonly DashboardMetricKey[];

export const METRIC_SPECS = {
  callsToday: {
    source: "follow_up_boss",
    definition:
      "Outbound calls made today by the authenticated Follow Up Boss user.",
  },
  textsToday: {
    source: "follow_up_boss",
    definition:
      "Manual outbound text messages sent today by the authenticated Follow Up Boss user.",
  },
  emailsToday: {
    source: "follow_up_boss",
    definition:
      "Manual outbound emails sent today by the authenticated Follow Up Boss user.",
  },
  appointmentsSetMtd: {
    source: "follow_up_boss",
    definition:
      "Appointments created this month by the authenticated Follow Up Boss user.",
  },
  freshBuyerLeads: {
    source: "follow_up_boss",
    definition:
      "Accessible non-trash buyer contacts created during the rolling previous four weeks.",
  },
  freshSellerLeads: {
    source: "follow_up_boss",
    definition:
      "Accessible non-trash contacts tagged Seller and created during the rolling previous four weeks.",
  },
  googleAdsSpendMtd: {
    source: "google_ads",
    definition:
      "Total month-to-date Google Ads cost across every accessible non-manager account.",
  },
  googleAdsLeadsMtd: {
    source: "google_ads",
    definition:
      "Total month-to-date primary Google Ads conversions across every accessible non-manager account.",
  },
} as const satisfies Record<DashboardMetricKey, MetricSpec>;

const INTEGER_METRICS = new Set<DashboardMetricKey>([
  "callsToday",
  "textsToday",
  "emailsToday",
  "appointmentsSetMtd",
  "freshBuyerLeads",
  "freshSellerLeads",
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
  const maximum = key === "googleAdsSpendMtd" ? MAX_SPEND_USD : MAX_COUNT;

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

export function sanitizeSnapshot(value: unknown): DashboardSnapshot | null {
  if (
    !isRecord(value) ||
    value["version"] !== 2 ||
    !isRecord(value["metrics"]) ||
    !isRecord(value["reportingPeriod"])
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

  const reportingPeriod = value["reportingPeriod"];
  const startDate = reportingPeriod["startDate"];
  const endDate = reportingPeriod["endDate"];
  const timeZone = reportingPeriod["timeZone"];
  const lastAttemptAt = value["lastAttemptAt"];
  const lastSuccessfulFullSyncAt = value["lastSuccessfulFullSyncAt"];
  if (
    !validIsoDate(startDate) ||
    !validIsoDate(endDate) ||
    startDate > endDate ||
    typeof timeZone !== "string" ||
    timeZone.trim() === "" ||
    timeZone.length > 100 ||
    !isIsoUtcTimestamp(lastAttemptAt) ||
    (lastSuccessfulFullSyncAt !== null &&
      !isIsoUtcTimestamp(lastSuccessfulFullSyncAt))
  ) {
    return null;
  }

  return {
    version: 2,
    metrics,
    reportingPeriod: { startDate, endDate, timeZone },
    lastAttemptAt,
    lastSuccessfulFullSyncAt,
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
    if (metric.status === "ok" && isMetricStale(metric.updatedAt, now)) {
      metric.status = "stale";
    }
  }
  return sanitized;
}
