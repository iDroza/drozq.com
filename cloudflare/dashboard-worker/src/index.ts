import { readReportingTimeZone } from "./config";
import {
  createUnconfiguredSnapshot,
  sanitizeStoredSnapshot,
  toActivePublicSnapshot,
  toPublicSnapshot,
} from "./snapshot";
import {
  ACTIVE_REALTY_PROGRESS_KEY,
  ACTIVE_REALTY_PROGRESS_MAX_BODY_BYTES,
  activeRealtyProgressRecordsEqual,
  compareActiveRealtyRunIds,
  sanitizeActiveRealtyProgressRecord,
  validateActiveRealtyProgressRecord,
  type ActiveRealtyProgressRecord,
} from "./sources/active-realty-progress";
import { SNAPSHOT_KEY, synchronizeDashboard } from "./sync";
import type { DashboardEnv, DashboardSnapshot } from "./types";

const SUMMARY_CACHE_CONTROL =
  "public, max-age=10, s-maxage=10, stale-while-revalidate=20";
const DASHBOARD_BOOTSTRAP_GLOBAL = "__DROZQ_DASHBOARD_SNAPSHOT__";
const ACTIVE_BOOTSTRAP_GLOBAL = "__ACTIVE_REALTY_DASHBOARD_SNAPSHOT__";
const SYNC_LEASE_KEY = "dashboard:sync:lease:v2";
const SYNC_LEASE_TTL_SECONDS = 120;

class RequestBodyTooLargeError extends Error {}

function responseHeaders(cacheControl: string): Headers {
  return new Headers({
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": cacheControl,
    "Referrer-Policy": "no-referrer",
  });
}

function jsonResponse(
  payload: object,
  status: number,
  cacheControl = "no-store",
): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: responseHeaders(cacheControl),
  });
}

function javascriptResponse(source: string): Response {
  return new Response(source, {
    status: 200,
    headers: {
      "Content-Type": "application/javascript; charset=utf-8",
      "X-Content-Type-Options": "nosniff",
      "Cache-Control": SUMMARY_CACHE_CONTROL,
      "Referrer-Policy": "no-referrer",
    },
  });
}

async function readSnapshot(env: DashboardEnv): Promise<DashboardSnapshot | null> {
  const stored = await env.DASHBOARD_KV.get(SNAPSHOT_KEY);
  if (stored === null) {
    return null;
  }
  try {
    return sanitizeStoredSnapshot(JSON.parse(stored) as unknown);
  } catch {
    return null;
  }
}

async function constantTimeEquals(provided: string, expected: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [providedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(provided)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  return crypto.subtle.timingSafeEqual(providedHash, expectedHash);
}

function bearerToken(request: Request): string {
  const authorization = request.headers.get("Authorization") ?? "";
  const match = /^Bearer ([^\s]+)$/u.exec(authorization);
  return match?.[1] ?? "";
}

function decimalStringExceeds(value: string, maximum: number): boolean {
  if (!/^\d+$/u.test(value)) {
    return false;
  }
  const normalized = value.replace(/^0+(?=\d)/u, "");
  const limit = String(maximum);
  return normalized.length > limit.length ||
    (normalized.length === limit.length && normalized > limit);
}

async function readBoundedRequestBody(
  request: Request,
  maximumBytes: number,
): Promise<string> {
  const declaredLength = request.headers.get("Content-Length");
  if (
    declaredLength !== null &&
    decimalStringExceeds(declaredLength, maximumBytes)
  ) {
    throw new RequestBodyTooLargeError();
  }
  if (request.body === null) {
    return "";
  }

  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let totalBytes = 0;
  while (true) {
    const chunk = await reader.read();
    if (chunk.done) {
      break;
    }
    totalBytes += chunk.value.byteLength;
    if (totalBytes > maximumBytes) {
      try {
        await reader.cancel();
      } catch {
        // The size rejection remains authoritative if stream cancellation fails.
      }
      throw new RequestBodyTooLargeError();
    }
    chunks.push(chunk.value);
  }

  const body = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder("utf-8", { fatal: true, ignoreBOM: false }).decode(body);
}

function progressDeliveryLog(
  outcome: "accepted" | "rejected",
  category: string,
  record: ActiveRealtyProgressRecord | null = null,
  idempotent: boolean | null = null,
  detail: string | null = null,
): Record<string, string | number | boolean | null> {
  return {
    source: "active_realty_progress_ingest",
    outcome,
    category,
    idempotent,
    detail,
    sourceSha: record?.sourceSha ?? null,
    runId: record?.runId ?? null,
    shellPagesRemaining: record?.shellPagesRemaining ?? null,
    setsRemaining: record?.setsRemaining ?? null,
  };
}

function errorDetail(error: unknown): string {
  return error instanceof Error
    ? `${error.name}: ${error.message}`
    : String(error);
}

function logProgressRejection(
  category: string,
  record: ActiveRealtyProgressRecord | null = null,
  severity: "warning" | "error" = "warning",
  detail: string | null = null,
): void {
  const serialized = JSON.stringify(
    progressDeliveryLog("rejected", category, record, null, detail),
  );
  if (severity === "error") {
    console.error(serialized);
  } else {
    console.warn(serialized);
  }
}

function progressSuccessResponse(
  record: ActiveRealtyProgressRecord,
  idempotent: boolean,
): Response {
  console.log(
    JSON.stringify(
      progressDeliveryLog(
        "accepted",
        idempotent ? "idempotent" : "stored",
        record,
        idempotent,
      ),
    ),
  );
  return jsonResponse({ ok: true, idempotent, record }, 200);
}

async function activeRealtyProgressResponse(
  request: Request,
  env: DashboardEnv,
): Promise<Response> {
  const expected = env.ACTIVE_REALTY_PROGRESS_TOKEN?.trim() ?? "";
  const authorized = expected !== "" &&
    (await constantTimeEquals(bearerToken(request), expected));
  if (!authorized) {
    logProgressRejection("authentication");
    const response = jsonResponse({ ok: false, error: "unauthorized" }, 401);
    response.headers.set("WWW-Authenticate", "Bearer");
    return response;
  }

  let body: string;
  try {
    body = await readBoundedRequestBody(
      request,
      ACTIVE_REALTY_PROGRESS_MAX_BODY_BYTES,
    );
  } catch (error) {
    if (error instanceof RequestBodyTooLargeError) {
      logProgressRejection("oversized_body");
      return jsonResponse({ ok: false, error: "payload_too_large" }, 413);
    }
    logProgressRejection("body_read", null, "error", errorDetail(error));
    return jsonResponse({ ok: false, error: "invalid_payload" }, 400);
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(body) as unknown;
  } catch {
    logProgressRejection("malformed_json");
    return jsonResponse({ ok: false, error: "invalid_payload" }, 400);
  }
  const validated = validateActiveRealtyProgressRecord(parsed);
  if (!validated.ok) {
    logProgressRejection(validated.category);
    return jsonResponse({ ok: false, error: "invalid_payload" }, 400);
  }
  const record = validated.record;

  let stored: string | null;
  try {
    stored = await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY);
  } catch (error) {
    logProgressRejection("storage_read", record, "error", errorDetail(error));
    return jsonResponse({ ok: false, error: "storage_unavailable" }, 503);
  }
  if (stored !== null) {
    let existing: ActiveRealtyProgressRecord | null = null;
    let storedFailure = "stored record failed validation";
    try {
      existing = sanitizeActiveRealtyProgressRecord(
        JSON.parse(stored) as unknown,
      );
    } catch (error) {
      // Invalid stored JSON is handled as a storage failure below.
      storedFailure = errorDetail(error);
    }
    if (existing === null) {
      logProgressRejection("stored_record_invalid", record, "error", storedFailure);
      return jsonResponse({ ok: false, error: "storage_unavailable" }, 503);
    }

    const ordering = compareActiveRealtyRunIds(record.runId, existing.runId);
    if (ordering === 0) {
      if (activeRealtyProgressRecordsEqual(record, existing)) {
        return progressSuccessResponse(existing, true);
      }
      logProgressRejection("run_id_conflict", record);
      return jsonResponse({ ok: false, error: "run_id_conflict" }, 409);
    }
    if (ordering < 0) {
      logProgressRejection("stale_run_id", record);
      return jsonResponse({ ok: false, error: "stale_run_id" }, 409);
    }
  }

  try {
    await env.DASHBOARD_KV.put(
      ACTIVE_REALTY_PROGRESS_KEY,
      JSON.stringify(record),
    );
  } catch (error) {
    logProgressRejection("storage_write", record, "error", errorDetail(error));
    return jsonResponse({ ok: false, error: "storage_unavailable" }, 503);
  }
  return progressSuccessResponse(record, false);
}

async function acquireSyncLease(env: DashboardEnv): Promise<string | null> {
  try {
    if ((await env.DASHBOARD_KV.get(SYNC_LEASE_KEY)) !== null) {
      return null;
    }
    const token = crypto.randomUUID();
    await env.DASHBOARD_KV.put(SYNC_LEASE_KEY, token, {
      expirationTtl: SYNC_LEASE_TTL_SECONDS,
    });
    return (await env.DASHBOARD_KV.get(SYNC_LEASE_KEY)) === token ? token : null;
  } catch (error) {
    console.error(
      JSON.stringify({
        source: "dashboard_sync_lease",
        category: "storage",
        status: null,
        detail: errorDetail(error),
      }),
    );
    return null;
  }
}

async function releaseSyncLease(env: DashboardEnv, token: string): Promise<void> {
  try {
    if ((await env.DASHBOARD_KV.get(SYNC_LEASE_KEY)) === token) {
      await env.DASHBOARD_KV.delete(SYNC_LEASE_KEY);
    }
  } catch (error) {
    console.error(
      JSON.stringify({
        source: "dashboard_sync_lease",
        category: "storage",
        status: null,
        detail: errorDetail(error),
      }),
    );
  }
}

async function summaryResponse(env: DashboardEnv): Promise<Response> {
  const now = new Date();
  const snapshot = await readSnapshot(env);
  if (snapshot === null) {
    const unavailable = createUnconfiguredSnapshot(now, readReportingTimeZone(env));
    return jsonResponse(unavailable, 503, SUMMARY_CACHE_CONTROL);
  }
  return jsonResponse(toPublicSnapshot(snapshot, now), 200, SUMMARY_CACHE_CONTROL);
}

async function bootstrapResponse(env: DashboardEnv): Promise<Response> {
  const now = new Date();
  const snapshot = await readSnapshot(env);
  const payload = snapshot === null
    ? createUnconfiguredSnapshot(now, readReportingTimeZone(env))
    : toPublicSnapshot(snapshot, now);
  return javascriptResponse(
    `"use strict";window.${DASHBOARD_BOOTSTRAP_GLOBAL}=${JSON.stringify(payload)};`,
  );
}

async function activeSummaryResponse(env: DashboardEnv): Promise<Response> {
  const now = new Date();
  const snapshot = await readSnapshot(env);
  const source = snapshot ?? createUnconfiguredSnapshot(
    now,
    readReportingTimeZone(env),
  );
  return jsonResponse(
    toActivePublicSnapshot(source, now),
    snapshot === null ? 503 : 200,
    SUMMARY_CACHE_CONTROL,
  );
}

async function activeBootstrapResponse(env: DashboardEnv): Promise<Response> {
  const now = new Date();
  const snapshot = await readSnapshot(env);
  const source = snapshot ?? createUnconfiguredSnapshot(
    now,
    readReportingTimeZone(env),
  );
  const payload = toActivePublicSnapshot(source, now);
  return javascriptResponse(
    `"use strict";window.${ACTIVE_BOOTSTRAP_GLOBAL}=${JSON.stringify(payload)};`,
  );
}

async function healthResponse(env: DashboardEnv): Promise<Response> {
  const snapshot = await readSnapshot(env);
  return jsonResponse({ ok: true, snapshotExists: snapshot !== null }, 200);
}

async function manualSyncResponse(
  request: Request,
  env: DashboardEnv,
): Promise<Response> {
  const expected = env.ADMIN_SYNC_TOKEN?.trim() ?? "";
  const authorized =
    expected !== "" && (await constantTimeEquals(bearerToken(request), expected));
  if (!authorized) {
    const response = jsonResponse({ ok: false, error: "unauthorized" }, 401);
    response.headers.set("WWW-Authenticate", "Bearer");
    return response;
  }

  const lease = await acquireSyncLease(env);
  if (lease === null) {
    return jsonResponse({ ok: false, error: "sync_in_progress" }, 409);
  }
  try {
    const snapshot = await synchronizeDashboard(env);
    return jsonResponse(snapshot, 200);
  } finally {
    await releaseSyncLease(env, lease);
  }
}

export async function handleRequest(
  request: Request,
  env: DashboardEnv,
): Promise<Response> {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname === "/api/dashboard/summary") {
    return summaryResponse(env);
  }
  if (
    request.method === "GET" &&
    url.pathname === "/api/dashboard/active-summary"
  ) {
    return activeSummaryResponse(env);
  }
  if (
    request.method === "GET" &&
    url.pathname === "/api/dashboard/bootstrap.js"
  ) {
    return bootstrapResponse(env);
  }
  if (
    request.method === "GET" &&
    url.pathname === "/api/dashboard/active-bootstrap.js"
  ) {
    return activeBootstrapResponse(env);
  }
  if (request.method === "GET" && url.pathname === "/api/dashboard/health") {
    return healthResponse(env);
  }
  if (
    request.method === "POST" &&
    url.pathname === "/api/dashboard/admin/shell-progress"
  ) {
    return activeRealtyProgressResponse(request, env);
  }
  if (
    request.method === "POST" &&
    url.pathname === "/api/dashboard/admin/sync"
  ) {
    return manualSyncResponse(request, env);
  }
  return jsonResponse({ ok: false, error: "not_found" }, 404);
}

async function runScheduledSync(env: DashboardEnv): Promise<void> {
  const lease = await acquireSyncLease(env);
  if (lease === null) {
    console.log(
      JSON.stringify({ source: "dashboard_sync", category: "already_running", status: null }),
    );
    return;
  }
  try {
    await synchronizeDashboard(env);
  } catch (error) {
    console.error(
      JSON.stringify({
        source: "dashboard_sync",
        category: "unexpected",
        status: null,
        detail: errorDetail(error),
      }),
    );
  } finally {
    await releaseSyncLease(env, lease);
  }
}

export default {
  async fetch(request: Request, env: DashboardEnv): Promise<Response> {
    try {
      return await handleRequest(request, env);
    } catch (error) {
      console.error(
        JSON.stringify({
          source: "dashboard_worker",
          category: "unexpected",
          status: null,
          detail: errorDetail(error),
        }),
      );
      return jsonResponse({ ok: false, error: "service_unavailable" }, 503);
    }
  },

  scheduled(
    _controller: ScheduledController,
    env: DashboardEnv,
    ctx: ExecutionContext,
  ): void {
    ctx.waitUntil(runScheduledSync(env));
  },
} satisfies ExportedHandler<DashboardEnv>;
