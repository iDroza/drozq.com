import { isRecord } from "../lib/http";
import type {
  ActiveRealtyProgressMetricResults,
  DashboardEnv,
  ErrorCategory,
  MetricFetchResult,
} from "../types";

export const ACTIVE_REALTY_PROGRESS_KEY =
  "dashboard:active-realty-progress:v1";
export const ACTIVE_REALTY_PROGRESS_MAX_BODY_BYTES = 4 * 1024;

const ACTIVE_REALTY_REPOSITORY = "iDroza/activerealty-com";
const ACTIVE_REALTY_MAIN_REF = "refs/heads/main";
const PROGRESS_FIELDS = [
  "schemaVersion",
  "sourceRepo",
  "sourceRef",
  "sourceSha",
  "runId",
  "publishedAt",
  "shellPagesRemaining",
  "setsRemaining",
] as const;
const PROGRESS_FIELD_SET = new Set<string>(PROGRESS_FIELDS);
const LOWERCASE_SHA_PATTERN = /^[0-9a-f]{40}$/u;
const POSITIVE_DECIMAL_PATTERN = /^[1-9]\d*$/u;
const UTC_TIMESTAMP_PATTERN =
  /^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,9})?(?:Z|\+00:00)$/u;

export interface ActiveRealtyProgressRecord {
  schemaVersion: 1;
  sourceRepo: "iDroza/activerealty-com";
  sourceRef: "refs/heads/main";
  sourceSha: string;
  runId: string;
  publishedAt: string;
  shellPagesRemaining: number;
  setsRemaining: number;
}

export type ActiveRealtyProgressValidationCategory =
  | "payload_type"
  | "fields"
  | "schema_version"
  | "source_repository"
  | "source_ref"
  | "source_sha"
  | "run_id"
  | "published_at"
  | "shell_pages_remaining"
  | "sets_remaining";

export type ActiveRealtyProgressValidationResult =
  | { ok: true; record: ActiveRealtyProgressRecord }
  | { ok: false; category: ActiveRealtyProgressValidationCategory };

function canonicalUtcTimestamp(value: unknown): string | null {
  if (typeof value !== "string" || !UTC_TIMESTAMP_PATTERN.test(value)) {
    return null;
  }
  const normalized = value.endsWith("+00:00")
    ? `${value.slice(0, -6)}Z`
    : value;
  const parsed = Date.parse(normalized);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  const canonical = new Date(parsed).toISOString();
  return canonical.slice(0, 19) === normalized.slice(0, 19)
    ? canonical
    : null;
}

function hasExactProgressFields(value: Record<string, unknown>): boolean {
  const keys = Object.keys(value);
  return keys.length === PROGRESS_FIELDS.length &&
    keys.every((key) => PROGRESS_FIELD_SET.has(key));
}

export function validateActiveRealtyProgressRecord(
  value: unknown,
): ActiveRealtyProgressValidationResult {
  if (!isRecord(value)) {
    return { ok: false, category: "payload_type" };
  }
  if (!hasExactProgressFields(value)) {
    return { ok: false, category: "fields" };
  }
  if (value["schemaVersion"] !== 1) {
    return { ok: false, category: "schema_version" };
  }
  if (value["sourceRepo"] !== ACTIVE_REALTY_REPOSITORY) {
    return { ok: false, category: "source_repository" };
  }
  if (value["sourceRef"] !== ACTIVE_REALTY_MAIN_REF) {
    return { ok: false, category: "source_ref" };
  }
  const sourceSha = value["sourceSha"];
  if (typeof sourceSha !== "string" || !LOWERCASE_SHA_PATTERN.test(sourceSha)) {
    return { ok: false, category: "source_sha" };
  }
  const runId = value["runId"];
  if (typeof runId !== "string" || !POSITIVE_DECIMAL_PATTERN.test(runId)) {
    return { ok: false, category: "run_id" };
  }
  const publishedAt = canonicalUtcTimestamp(value["publishedAt"]);
  if (publishedAt === null) {
    return { ok: false, category: "published_at" };
  }
  const shellPagesRemaining = value["shellPagesRemaining"];
  if (
    typeof shellPagesRemaining !== "number" ||
    !Number.isSafeInteger(shellPagesRemaining) ||
    shellPagesRemaining < 0
  ) {
    return { ok: false, category: "shell_pages_remaining" };
  }
  const setsRemaining = value["setsRemaining"];
  if (
    typeof setsRemaining !== "number" ||
    !Number.isSafeInteger(setsRemaining) ||
    setsRemaining < 0
  ) {
    return { ok: false, category: "sets_remaining" };
  }

  return {
    ok: true,
    record: {
      schemaVersion: 1,
      sourceRepo: ACTIVE_REALTY_REPOSITORY,
      sourceRef: ACTIVE_REALTY_MAIN_REF,
      sourceSha,
      runId,
      publishedAt,
      shellPagesRemaining,
      setsRemaining,
    },
  };
}

export function sanitizeActiveRealtyProgressRecord(
  value: unknown,
): ActiveRealtyProgressRecord | null {
  const validated = validateActiveRealtyProgressRecord(value);
  return validated.ok ? validated.record : null;
}

export function compareActiveRealtyRunIds(left: string, right: string): number {
  if (left.length !== right.length) {
    return left.length < right.length ? -1 : 1;
  }
  if (left === right) {
    return 0;
  }
  return left < right ? -1 : 1;
}

export function activeRealtyProgressRecordsEqual(
  left: ActiveRealtyProgressRecord,
  right: ActiveRealtyProgressRecord,
): boolean {
  return PROGRESS_FIELDS.every((field) => left[field] === right[field]);
}

function failedMetrics(
  category: ErrorCategory,
  started: number,
): ActiveRealtyProgressMetricResults {
  const result: MetricFetchResult = {
    kind: "error",
    category,
    durationMs: Date.now() - started,
    responseStatus: null,
  };
  return {
    shellPagesRemaining: result,
    setsRemaining: { ...result },
  };
}

export async function fetchActiveRealtyProgressMetrics(
  env: DashboardEnv,
): Promise<ActiveRealtyProgressMetricResults> {
  const started = Date.now();
  let stored: string | null;
  try {
    stored = await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY);
  } catch {
    return failedMetrics("storage", started);
  }
  if (stored === null) {
    return failedMetrics("no_data", started);
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(stored) as unknown;
  } catch {
    return failedMetrics("malformed_json", started);
  }
  const record = sanitizeActiveRealtyProgressRecord(parsed);
  if (record === null) {
    return failedMetrics("schema", started);
  }

  const durationMs = Date.now() - started;
  return {
    shellPagesRemaining: {
      kind: "ok",
      value: record.shellPagesRemaining,
      observedAt: record.publishedAt,
      durationMs,
      responseStatus: null,
    },
    setsRemaining: {
      kind: "ok",
      value: record.setsRemaining,
      observedAt: record.publishedAt,
      durationMs,
      responseStatus: null,
    },
  };
}
