import { readReportingTimeZone } from "./config";
import {
  createUnconfiguredSnapshot,
  sanitizeSnapshot,
  toPublicSnapshot,
} from "./snapshot";
import { SNAPSHOT_KEY, synchronizeDashboard } from "./sync";
import type { DashboardEnv, DashboardSnapshot } from "./types";

const SUMMARY_CACHE_CONTROL =
  "public, max-age=10, s-maxage=10, stale-while-revalidate=20";
const SYNC_LEASE_KEY = "dashboard:sync:lease:v2";
const SYNC_LEASE_TTL_SECONDS = 120;

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

async function readSnapshot(env: DashboardEnv): Promise<DashboardSnapshot | null> {
  const stored = await env.DASHBOARD_KV.get(SNAPSHOT_KEY);
  if (stored === null) {
    return null;
  }
  try {
    return sanitizeSnapshot(JSON.parse(stored) as unknown);
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
  } catch {
    console.error(
      JSON.stringify({ source: "dashboard_sync_lease", category: "storage", status: null }),
    );
    return null;
  }
}

async function releaseSyncLease(env: DashboardEnv, token: string): Promise<void> {
  try {
    if ((await env.DASHBOARD_KV.get(SYNC_LEASE_KEY)) === token) {
      await env.DASHBOARD_KV.delete(SYNC_LEASE_KEY);
    }
  } catch {
    console.error(
      JSON.stringify({ source: "dashboard_sync_lease", category: "storage", status: null }),
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
  if (request.method === "GET" && url.pathname === "/api/dashboard/health") {
    return healthResponse(env);
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
  } catch {
    console.error(
      JSON.stringify({ source: "dashboard_sync", category: "unexpected", status: null }),
    );
  } finally {
    await releaseSyncLease(env, lease);
  }
}

export default {
  async fetch(request: Request, env: DashboardEnv): Promise<Response> {
    try {
      return await handleRequest(request, env);
    } catch {
      console.error(
        JSON.stringify({ source: "dashboard_worker", category: "unexpected", status: null }),
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
