import { CONFIG_DEFAULTS } from "./config";
import { getReportingPeriod, isIsoUtcTimestamp, isMetricStale } from "./lib/date";
import {
  isFiniteNonnegative,
  MAX_COUNT,
  MAX_SPEND_USD,
} from "./lib/numeric";
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

export const METRIC_SPECS = {
  sellerLeads: {
    source: "follow_up_boss",
    definition:
      'All accessible Follow Up Boss contacts tagged "Seller", excluding Trash.',
  },
  googleAdsSpendMtd: {
    source: "google_ads",
    definition:
      "Total Google Ads cost from the first day of the current month through today.",
  },
  googleAdsLeadsMtd: {
    source: "google_ads",
    definition:
      "Month-to-date Google Ads conversions matching the configured lead conversion action names.",
  },
  shellPagesRemaining: {
    source: "google_sheets",
    definition:
      "Incomplete shell-page rows in the configured Google Sheet, or the configured remaining-count cell.",
  },
} as const satisfies Record<DashboardMetricKey, MetricSpec>;

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
  const requiresInteger = key === "sellerLeads" || key === "shellPagesRemaining";

  if (
    value["source"] !== spec.source ||
    typeof status !== "string" ||
    !VALID_STATUSES.has(status as MetricStatus) ||
    (rawValue !== null &&
      (!isFiniteNonnegative(rawValue) ||
        rawValue > maximum ||
        (requiresInteger && !Number.isSafeInteger(rawValue)))) ||
    (updatedAt !== null && !isIsoUtcTimestamp(updatedAt))
  ) {
    return null;
  }

  const typedStatus = status as MetricStatus;
  if ((rawValue === null) !== (updatedAt === null)) {
    return null;
  }
  if (
    (typedStatus === "ok" || typedStatus === "stale") &&
    rawValue === null
  ) {
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
    value["version"] !== 1 ||
    !isRecord(value["metrics"]) ||
    !isRecord(value["reportingPeriod"])
  ) {
    return null;
  }

  const sellerLeads = sanitizeMetric(value["metrics"]["sellerLeads"], "sellerLeads");
  const googleAdsSpendMtd = sanitizeMetric(
    value["metrics"]["googleAdsSpendMtd"],
    "googleAdsSpendMtd",
  );
  const googleAdsLeadsMtd = sanitizeMetric(
    value["metrics"]["googleAdsLeadsMtd"],
    "googleAdsLeadsMtd",
  );
  const shellPagesRemaining = sanitizeMetric(
    value["metrics"]["shellPagesRemaining"],
    "shellPagesRemaining",
  );
  const reportingPeriod = value["reportingPeriod"];
  const startDate = reportingPeriod["startDate"];
  const endDate = reportingPeriod["endDate"];
  const timeZone = reportingPeriod["timeZone"];
  const lastAttemptAt = value["lastAttemptAt"];
  const lastSuccessfulFullSyncAt = value["lastSuccessfulFullSyncAt"];

  if (
    sellerLeads === null ||
    googleAdsSpendMtd === null ||
    googleAdsLeadsMtd === null ||
    shellPagesRemaining === null ||
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
    version: 1,
    metrics: {
      sellerLeads,
      googleAdsSpendMtd,
      googleAdsLeadsMtd,
      shellPagesRemaining,
    },
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
  return {
    version: 1,
    metrics: {
      sellerLeads: unavailableMetric("sellerLeads"),
      googleAdsSpendMtd: unavailableMetric("googleAdsSpendMtd"),
      googleAdsLeadsMtd: unavailableMetric("googleAdsLeadsMtd"),
      shellPagesRemaining: unavailableMetric("shellPagesRemaining"),
    },
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

  for (const key of Object.keys(sanitized.metrics) as DashboardMetricKey[]) {
    const metric = sanitized.metrics[key];
    if (metric.status === "ok" && isMetricStale(metric.updatedAt, now)) {
      metric.status = "stale";
    }
  }
  return sanitized;
}
