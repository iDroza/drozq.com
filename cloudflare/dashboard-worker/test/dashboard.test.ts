import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it } from "vitest";
import { CONFIG_DEFAULTS } from "../src/config";
import { getActivityWindows, getReportingPeriod } from "../src/lib/date";
import { fetchWithRetry, parseRetryAfter } from "../src/lib/retry";
import {
  createUnconfiguredSnapshot,
  sanitizeSnapshot,
  toPublicSnapshot,
} from "../src/snapshot";
import {
  countAppointmentsCreatedByUser,
  countFreshLeads,
  countOutboundCalls,
  fetchFollowUpBossMetrics,
  outboundActivityIds,
  parseFollowUpBossTotal,
} from "../src/sources/follow-up-boss";
import {
  costMicrosToUsd,
  fetchGoogleAdsMetrics,
  sumMatchingLeadConversions,
} from "../src/sources/google-ads";
import {
  countIncompletePageRows,
  fetchShellPagesRemaining,
  parseDirectCell,
} from "../src/sources/google-sheets";
import { handleRequest } from "../src/index";
import { mergeSnapshot, SNAPSHOT_KEY, type MetricResultMap } from "../src/sync";
import type {
  DashboardEnv,
  DashboardSnapshot,
  MetricFetchResult,
  SecretBindings,
} from "../src/types";

const NOW = new Date("2026-08-14T19:00:00.000Z");
const DAY_START = "2026-08-14T07:00:00.000Z";
const MONTH_START = "2026-08-01T07:00:00.000Z";

function successful(value: number): MetricFetchResult {
  return { kind: "ok", value, durationMs: 5, responseStatus: 200 };
}

function failed(): MetricFetchResult {
  return {
    kind: "error",
    category: "upstream",
    durationMs: 5,
    responseStatus: 503,
  };
}

function unconfigured(): MetricFetchResult {
  return { kind: "unconfigured", durationMs: 0, responseStatus: null };
}

function allSuccessfulResults(): MetricResultMap {
  return {
    callsToday: successful(12),
    textsToday: successful(24),
    emailsToday: successful(7),
    appointmentsSetMtd: successful(5),
    freshBuyerLeads: successful(141),
    freshSellerLeads: successful(3),
    googleAdsSpendMtd: successful(2362.175313),
    googleAdsLeadsMtd: successful(107),
  };
}

function makeSnapshot(now = NOW): DashboardSnapshot {
  return mergeSnapshot(
    null,
    allSuccessfulResults(),
    now,
    getReportingPeriod(now, "America/Los_Angeles"),
  );
}

function withSecrets(secrets: SecretBindings): DashboardEnv {
  return { ...env, ...secrets };
}

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function collection(name: string, rows: unknown[]): Response {
  return jsonResponse({
    [name]: rows,
    _metadata: { total: rows.length, limit: 100, offset: 0 },
  });
}

function noDelay(): Promise<void> {
  return Promise.resolve();
}

async function generateEscapedTestPrivateKey(): Promise<string> {
  const keyPair = (await crypto.subtle.generateKey(
    {
      name: "RSASSA-PKCS1-v1_5",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true,
    ["sign", "verify"],
  )) as CryptoKeyPair;
  const exportedKey = await crypto.subtle.exportKey("pkcs8", keyPair.privateKey);
  const exported = new Uint8Array(exportedKey as ArrayBuffer);
  let binary = "";
  for (const byte of exported) {
    binary += String.fromCharCode(byte);
  }
  const body = btoa(binary).match(/.{1,64}/gu)?.join("\n") ?? "";
  return `-----BEGIN PRIVATE KEY-----\n${body}\n-----END PRIVATE KEY-----\n`.replaceAll(
    "\n",
    "\\n",
  );
}

beforeEach(async () => {
  await Promise.all([
    env.DASHBOARD_KV.delete(SNAPSHOT_KEY),
    env.DASHBOARD_KV.delete("dashboard:fub:activity:v2"),
    env.DASHBOARD_KV.delete("dashboard:google_ads:accounts:v2"),
    env.DASHBOARD_KV.delete("dashboard:sync:lease:v2"),
  ]);
});

describe("Follow Up Boss normalization", () => {
  it("parses _metadata.total", () => {
    expect(parseFollowUpBossTotal({ _metadata: { total: 37 }, people: [] })).toBe(37);
  });

  it("rejects missing metadata", () => {
    expect(() => parseFollowUpBossTotal({ people: [] })).toThrow("schema");
  });

  it("rejects negative and non-finite totals", () => {
    expect(() => parseFollowUpBossTotal({ _metadata: { total: -1 } })).toThrow();
    expect(() => parseFollowUpBossTotal({ _metadata: { total: Number.NaN } })).toThrow();
  });

  it("splits rolling leads into seller-tagged and buyer contacts", () => {
    expect(countFreshLeads([
      { id: 1, tags: ["Website Lead"] },
      { id: 2, tags: [" seller "] },
      { id: 3, tags: [{ name: "SELLER" }] },
    ], "Seller")).toEqual({ buyers: 1, sellers: 2 });
  });

  it("counts only the authenticated user's outbound calls", () => {
    expect(countOutboundCalls([
      { id: 1, created: "2026-08-14T18:00:00.000Z", userId: 659, isIncoming: false },
      { id: 2, created: "2026-08-14T18:01:00.000Z", userId: 659, isIncoming: true },
      { id: 3, created: "2026-08-14T18:02:00.000Z", userId: 42, isIncoming: false },
    ], "659", DAY_START, NOW.toISOString())).toBe(1);
  });

  it("counts appointments by creator, not assignee", () => {
    expect(countAppointmentsCreatedByUser([
      { id: 1, created: "2026-08-10T18:00:00.000Z", createdById: 659, userId: 42 },
      { id: 2, created: "2026-08-10T18:00:00.000Z", createdById: 42, userId: 659 },
    ], "659", MONTH_START, NOW.toISOString())).toBe(1);
  });

  it("excludes inbound and automated text or email activity", () => {
    const rows = [
      { id: 1, created: "2026-08-14T18:00:00.000Z", userId: 659, isIncoming: false, status: "sent" },
      { id: 2, created: "2026-08-14T18:01:00.000Z", userId: 659, isIncoming: true, status: "sent" },
      { id: 3, created: "2026-08-14T18:02:00.000Z", userId: 659, isIncoming: false, status: "sent", actionPlanId: 8 },
      { id: 4, created: "2026-08-14T18:03:00.000Z", userId: 42, isIncoming: false, status: "sent" },
    ];
    expect(outboundActivityIds(rows, "texts", "659", DAY_START, NOW.toISOString())).toEqual(["1"]);
    expect(outboundActivityIds(rows, "emails", "659", DAY_START, NOW.toISOString())).toEqual(["1", "2"]);
  });

  it("fetches all six FUB metrics and deduplicates incremental message scans", async () => {
    let authorization = "";
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = new URL(String(input));
      authorization = new Headers(init?.headers).get("Authorization") ?? "";
      if (url.pathname.endsWith("/me")) {
        return jsonResponse({ id: 659 });
      }
      if (url.pathname.endsWith("/calls")) {
        return collection("calls", [
          { id: 1, created: "2026-08-14T18:00:00.000Z", userId: 659, isIncoming: false },
          { id: 2, created: "2026-08-14T18:01:00.000Z", userId: 659, isIncoming: true },
        ]);
      }
      if (url.pathname.endsWith("/appointments")) {
        return collection("appointments", [
          { id: 3, created: "2026-08-10T18:00:00.000Z", createdById: 659 },
        ]);
      }
      if (url.pathname.endsWith("/textMessages")) {
        return collection("textmessages", [
          { id: 4, created: "2026-08-14T18:05:00.000Z", userId: 659, isIncoming: false },
          { id: 5, created: "2026-08-14T18:06:00.000Z", userId: 659, isIncoming: false, actionPlanId: 9 },
        ]);
      }
      if (url.pathname.endsWith("/emails")) {
        return collection("emails", [
          { id: 6, created: "2026-08-14T18:07:00.000Z", userId: 659, status: "SENT" },
          { id: 7, created: "2026-08-14T18:08:00.000Z", userId: 659, status: "draft" },
        ]);
      }
      if (url.pathname.endsWith("/people") && url.searchParams.get("sortBy") === "lastSentText") {
        return collection("people", [{ id: 10, lastSentText: "2026-08-14T18:05:00.000Z" }]);
      }
      if (url.pathname.endsWith("/people") && url.searchParams.get("sortBy") === "lastSentEmail") {
        return collection("people", [{ id: 11, lastSentEmail: "2026-08-14T18:07:00.000Z" }]);
      }
      if (url.pathname.endsWith("/people")) {
        expect(url.searchParams.get("includeTrash")).toBe("false");
        expect(url.searchParams.get("createdAfter")).toBe("2026-07-17T19:00:00.000Z");
        return collection("people", [
          { id: 12, tags: ["Buyer"] },
          { id: 13, tags: ["Seller"] },
        ]);
      }
      return new Response("", { status: 404 });
    };
    const dashboardEnv = withSecrets({ FUB_API_KEY: "test-fub-key" });
    const first = await fetchFollowUpBossMetrics(
      dashboardEnv,
      "America/Los_Angeles",
      { fetcher, sleep: noDelay, now: NOW },
    );
    const second = await fetchFollowUpBossMetrics(
      dashboardEnv,
      "America/Los_Angeles",
      { fetcher, sleep: noDelay, now: NOW },
    );

    expect(authorization.startsWith("Basic ")).toBe(true);
    expect(first.callsToday).toMatchObject({ kind: "ok", value: 1 });
    expect(first.textsToday).toMatchObject({ kind: "ok", value: 1 });
    expect(first.emailsToday).toMatchObject({ kind: "ok", value: 1 });
    expect(first.appointmentsSetMtd).toMatchObject({ kind: "ok", value: 1 });
    expect(first.freshBuyerLeads).toMatchObject({ kind: "ok", value: 1 });
    expect(first.freshSellerLeads).toMatchObject({ kind: "ok", value: 1 });
    expect(second.textsToday).toMatchObject({ kind: "ok", value: 1 });
    expect(second.emailsToday).toMatchObject({ kind: "ok", value: 1 });
  });
});

describe("upstream retry policy", () => {
  it("honors retryable statuses for at most three attempts", async () => {
    let calls = 0;
    const delays: number[] = [];
    const response = await fetchWithRetry(
      "https://example.invalid/upstream",
      { method: "GET" },
      {
        source: "test_source",
        fetcher: async () => {
          calls += 1;
          return calls < 3
            ? new Response("", { status: 429, headers: { "Retry-After": "0" } })
            : new Response("ok", { status: 200 });
        },
        sleep: (milliseconds) => {
          delays.push(milliseconds);
          return Promise.resolve();
        },
      },
    );
    expect(response.status).toBe(200);
    expect(calls).toBe(3);
    expect(delays).toEqual([0, 0]);
  });

  it("does not retry ordinary authentication failures", async () => {
    let calls = 0;
    const response = await fetchWithRetry(
      "https://example.invalid/upstream",
      { method: "GET" },
      {
        source: "test_source",
        fetcher: async () => {
          calls += 1;
          return new Response("", { status: 401 });
        },
        sleep: noDelay,
      },
    );
    expect(response.status).toBe(401);
    expect(calls).toBe(1);
    expect(parseRetryAfter("2")).toBe(2_000);
  });
});

describe("Google Ads all-account aggregation", () => {
  it("converts cost_micros to USD", () => {
    expect(costMicrosToUsd("123456789")).toBeCloseTo(123.456789, 6);
  });

  it("rejects malformed or negative spend", () => {
    expect(() => costMicrosToUsd("-1")).toThrow();
    expect(() => costMicrosToUsd(Number.POSITIVE_INFINITY)).toThrow();
  });

  it("retains case-insensitive action filtering for diagnostics", () => {
    const result = sumMatchingLeadConversions([
      { segments: { conversionActionName: "Generate_Lead" }, metrics: { conversions: "2" } },
      { segments: { conversionActionName: "page_view" }, metrics: { conversions: 99 } },
    ], ["generate_lead"]);
    expect(result).toEqual({ value: 2, matchedRows: 1 });
  });

  it("discovers every leaf account and sums spend and primary conversions", async () => {
    let tokenCalls = 0;
    const queriedCustomers: string[] = [];
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url === "https://oauth2.googleapis.com/token") {
        tokenCalls += 1;
        return jsonResponse({ access_token: "test-access-token-value", expires_in: 3600 });
      }
      const customerId = /customers\/(\d{10})\/googleAds:search/u.exec(url)?.[1];
      if (customerId === undefined) {
        return new Response("", { status: 404 });
      }
      const headers = new Headers(init?.headers);
      expect(headers.get("login-customer-id")).toBe("1975174499");
      const body = JSON.parse(String(init?.body)) as { query: string };
      if (body.query.includes("customer_client.client_customer")) {
        expect(customerId).toBe("1975174499");
        return jsonResponse({ results: [
          { customerClient: { clientCustomer: "customers/1975174499", manager: true } },
          { customerClient: { clientCustomer: "customers/3351363652" } },
          { customerClient: { clientCustomer: "customers/7216252244" } },
          { customerClient: { clientCustomer: "customers/4069972406" } },
        ] });
      }
      queriedCustomers.push(customerId);
      const performance: Record<string, [string, number]> = {
        "3351363652": ["0", 0],
        "7216252244": ["1352715303", 102],
        "4069972406": ["1009460010", 5],
      };
      const values = performance[customerId];
      if (values === undefined) {
        return new Response("", { status: 404 });
      }
      return jsonResponse({ results: [{ metrics: {
        costMicros: values[0],
        conversions: values[1],
      } }] });
    };
    const result = await fetchGoogleAdsMetrics(
      withSecrets({
        GOOGLE_ADS_DEVELOPER_TOKEN: "test-developer-token",
        GOOGLE_ADS_CLIENT_ID: "test-client-id",
        GOOGLE_ADS_CLIENT_SECRET: "test-client-secret",
        GOOGLE_ADS_REFRESH_TOKEN: "test-refresh-token",
        GOOGLE_ADS_LOGIN_CUSTOMER_ID: "1975174499",
      }),
      getReportingPeriod(NOW, CONFIG_DEFAULTS.reportingTimeZone),
      { fetcher, sleep: noDelay, now: NOW },
    );

    expect(tokenCalls).toBe(1);
    expect(queriedCustomers.sort()).toEqual(["3351363652", "4069972406", "7216252244"]);
    expect(result.googleAdsSpendMtd).toMatchObject({ kind: "ok" });
    expect(result.googleAdsSpendMtd.kind === "ok" ? result.googleAdsSpendMtd.value : null)
      .toBeCloseTo(2362.175313, 6);
    expect(result.googleAdsLeadsMtd).toMatchObject({ kind: "ok", value: 107 });
  });

  it("does not publish a partial all-account total when one child fails", async () => {
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url === "https://oauth2.googleapis.com/token") {
        return jsonResponse({ access_token: "test-access-token-value" });
      }
      const body = JSON.parse(String(init?.body)) as { query: string };
      if (body.query.includes("customer_client.client_customer")) {
        return jsonResponse({ results: [
          { customerClient: { clientCustomer: "customers/1975174499", manager: true } },
          { customerClient: { clientCustomer: "customers/3351363652" } },
          { customerClient: { clientCustomer: "customers/7216252244" } },
        ] });
      }
      return url.includes("7216252244")
        ? new Response("", { status: 503 })
        : jsonResponse({ results: [{ metrics: { costMicros: "1000000", conversions: 1 } }] });
    };
    const result = await fetchGoogleAdsMetrics(
      withSecrets({
        GOOGLE_ADS_DEVELOPER_TOKEN: "test-developer-token",
        GOOGLE_ADS_CLIENT_ID: "test-client-id",
        GOOGLE_ADS_CLIENT_SECRET: "test-client-secret",
        GOOGLE_ADS_REFRESH_TOKEN: "test-refresh-token",
        GOOGLE_ADS_LOGIN_CUSTOMER_ID: "1975174499",
      }),
      getReportingPeriod(NOW, CONFIG_DEFAULTS.reportingTimeZone),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.googleAdsSpendMtd.kind).toBe("error");
    expect(result.googleAdsLeadsMtd.kind).toBe("error");
  });
});

describe("Google Sheets normalization retained for the source adapter", () => {
  it("parses direct-cell mode", () => {
    expect(parseDirectCell([["14"]])).toBe(14);
  });

  it("rejects negative and fractional direct-cell values", () => {
    expect(() => parseDirectCell([[-1]])).toThrow();
    expect(() => parseDirectCell([[1.5]])).toThrow();
  });

  it("counts incomplete rows and normalizes statuses", () => {
    const rows = [
      ["Page", "Status"],
      ["About", " Completed "],
      ["Sellers", "LIVE"],
      ["Buyers", "working"],
      ["", "draft"],
      [null, null],
    ];
    expect(countIncompletePageRows(rows, "page", "status", ["completed", "live"]))
      .toBe(1);
  });

  it("uses service-account OAuth with escaped private-key newlines", async () => {
    const privateKey = await generateEscapedTestPrivateKey();
    let tokenCalls = 0;
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url === "https://oauth2.googleapis.com/token") {
        tokenCalls += 1;
        expect(String(init?.body)).toContain("assertion=");
        return jsonResponse({ access_token: "test-sheets-access-token" });
      }
      expect(url).toContain("sheets.googleapis.com/v4/spreadsheets/test-sheet-id/values/");
      return jsonResponse({ values: [["9"]] });
    };
    const result = await fetchShellPagesRemaining(
      withSecrets({
        GOOGLE_SERVICE_ACCOUNT_EMAIL: "dashboard@test-project.iam.gserviceaccount.com",
        GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: privateKey,
        GOOGLE_SHEETS_SPREADSHEET_ID: "test-sheet-id",
        GOOGLE_SHEETS_REMAINING_RANGE: "Dashboard Inputs!B2",
      }),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(tokenCalls).toBe(1);
    expect(result).toMatchObject({ kind: "ok", value: 9 });
  });
});

describe("snapshot merging and public contract", () => {
  it("preserves a previous valid value after a partial failure", () => {
    const previousTime = new Date("2026-08-14T18:00:00.000Z");
    const previous = makeSnapshot(previousTime);
    const results = allSuccessfulResults();
    results.callsToday = failed();
    results.freshSellerLeads = successful(4);
    const merged = mergeSnapshot(
      previous,
      results,
      NOW,
      getReportingPeriod(NOW, "America/Los_Angeles"),
    );
    expect(merged.metrics.callsToday).toMatchObject({
      value: 12,
      updatedAt: previousTime.toISOString(),
      status: "stale",
    });
    expect(merged.metrics.freshSellerLeads).toMatchObject({ value: 4, status: "ok" });
  });

  it("uses error, not zero, for a first-run failure", () => {
    const results = allSuccessfulResults();
    results.callsToday = failed();
    const merged = mergeSnapshot(
      null,
      results,
      NOW,
      getReportingPeriod(NOW, "America/Los_Angeles"),
    );
    expect(merged.metrics.callsToday).toMatchObject({
      value: null,
      updatedAt: null,
      status: "error",
    });
  });

  it("marks an ok metric stale after more than five minutes", () => {
    const snapshot = makeSnapshot(new Date("2026-08-14T18:00:00.000Z"));
    const publicSnapshot = toPublicSnapshot(
      snapshot,
      new Date("2026-08-14T18:05:00.001Z"),
    );
    expect(publicSnapshot.metrics.callsToday.status).toBe("stale");
  });

  it("keeps a metric ok at exactly five minutes", () => {
    const snapshot = makeSnapshot(new Date("2026-08-14T18:00:00.000Z"));
    const publicSnapshot = toPublicSnapshot(
      snapshot,
      new Date("2026-08-14T18:05:00.000Z"),
    );
    expect(publicSnapshot.metrics.callsToday.status).toBe("ok");
  });

  it("strips every non-allowlisted public field", () => {
    const snapshot = makeSnapshot();
    const tainted = {
      ...snapshot,
      accessToken: "must-not-leak",
      metrics: {
        ...snapshot.metrics,
        callsToday: {
          ...snapshot.metrics.callsToday,
          contacts: [{ email: "private@example.invalid" }],
          definition: "untrusted definition",
        },
      },
    };
    const sanitized = sanitizeSnapshot(tainted);
    const serialized = JSON.stringify(sanitized);
    expect(sanitized?.metrics.callsToday.definition).not.toBe("untrusted definition");
    expect(serialized).not.toContain("must-not-leak");
    expect(serialized).not.toContain("private@example.invalid");
    expect(Object.keys(sanitized ?? {})).toEqual([
      "version",
      "metrics",
      "reportingPeriod",
      "lastAttemptAt",
      "lastSuccessfulFullSyncAt",
    ]);
    expect(Object.keys(sanitized?.metrics.callsToday ?? {})).toEqual([
      "value",
      "source",
      "updatedAt",
      "status",
      "definition",
    ]);
  });

  it("rejects absurd, fractional FUB, and non-finite values", () => {
    const snapshot = makeSnapshot();
    expect(sanitizeSnapshot({
      ...snapshot,
      metrics: {
        ...snapshot.metrics,
        callsToday: { ...snapshot.metrics.callsToday, value: 1.5 },
      },
    })).toBeNull();
    expect(sanitizeSnapshot({
      ...snapshot,
      metrics: {
        ...snapshot.metrics,
        googleAdsSpendMtd: {
          ...snapshot.metrics.googleAdsSpendMtd,
          value: Number.POSITIVE_INFINITY,
        },
      },
    })).toBeNull();
  });

  it("represents explicitly unconfigured metrics without false zeros", () => {
    const results = allSuccessfulResults();
    results.emailsToday = unconfigured();
    const merged = mergeSnapshot(
      null,
      results,
      NOW,
      getReportingPeriod(NOW, "America/Los_Angeles"),
    );
    expect(merged.metrics.emailsToday).toMatchObject({
      value: null,
      updatedAt: null,
      status: "unconfigured",
    });
  });

  it("rejects an invalid manual-sync token", async () => {
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/admin/sync", {
        method: "POST",
        headers: { Authorization: "Bearer wrong-token" },
      }),
      withSecrets({ ADMIN_SYNC_TOKEN: "correct-token" }),
    );
    expect(response.status).toBe(401);
    expect(await response.json()).toEqual({ ok: false, error: "unauthorized" });
  });

  it("rejects an overlapping authorized manual sync", async () => {
    await env.DASHBOARD_KV.put("dashboard:sync:lease:v2", "held", { expirationTtl: 120 });
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/admin/sync", {
        method: "POST",
        headers: { Authorization: "Bearer correct-token" },
      }),
      withSecrets({ ADMIN_SYNC_TOKEN: "correct-token" }),
    );
    expect(response.status).toBe(409);
    expect(await response.json()).toEqual({ ok: false, error: "sync_in_progress" });
  });

  it("creates a valid unconfigured first-run payload", () => {
    const snapshot = createUnconfiguredSnapshot(NOW, "America/Los_Angeles");
    expect(sanitizeSnapshot(snapshot)).not.toBeNull();
    expect(snapshot.metrics.googleAdsSpendMtd.value).toBeNull();
    expect(Object.keys(snapshot.metrics)).toHaveLength(8);
  });

  it("serves only a cached sanitized summary with hardened headers", async () => {
    await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify(makeSnapshot()));
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/summary"),
      withSecrets({}),
    );
    const payload = (await response.json()) as DashboardSnapshot;
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("application/json");
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(response.headers.get("Cache-Control")).toBe(
      "public, max-age=10, s-maxage=10, stale-while-revalidate=20",
    );
    expect(response.headers.has("Access-Control-Allow-Origin")).toBe(false);
    expect(payload.version).toBe(2);
    expect(Object.keys(payload.metrics)).toHaveLength(8);
  });

  it("returns a valid 503 payload when no snapshot exists", async () => {
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/summary"),
      withSecrets({}),
    );
    const payload = (await response.json()) as DashboardSnapshot;
    expect(response.status).toBe(503);
    expect(sanitizeSnapshot(payload)).not.toBeNull();
    expect(payload.metrics.callsToday).toMatchObject({ value: null, status: "unconfigured" });
  });
});

describe("America/Los_Angeles reporting dates", () => {
  it("uses the prior local month before midnight at a UTC month boundary", () => {
    expect(getReportingPeriod(
      new Date("2026-01-01T07:30:00.000Z"),
      "America/Los_Angeles",
    )).toEqual({
      startDate: "2025-12-01",
      endDate: "2025-12-31",
      timeZone: "America/Los_Angeles",
    });
  });

  it("rolls December into January after local midnight", () => {
    expect(getReportingPeriod(
      new Date("2026-01-01T08:30:00.000Z"),
      "America/Los_Angeles",
    )).toEqual({
      startDate: "2026-01-01",
      endDate: "2026-01-01",
      timeZone: "America/Los_Angeles",
    });
  });

  it("handles leap-year February", () => {
    expect(getReportingPeriod(
      new Date("2024-03-01T07:59:59.000Z"),
      "America/Los_Angeles",
    )).toEqual({
      startDate: "2024-02-01",
      endDate: "2024-02-29",
      timeZone: "America/Los_Angeles",
    });
  });

  it("computes local daily and monthly UTC boundaries across DST", () => {
    expect(getActivityWindows(
      new Date("2026-03-09T19:00:00.000Z"),
      "America/Los_Angeles",
    )).toMatchObject({
      localDate: "2026-03-09",
      dayStartAt: "2026-03-09T07:00:00.000Z",
      monthStartAt: "2026-03-01T08:00:00.000Z",
    });
  });

  it("uses an exact rolling 28-day fresh-lead window", () => {
    expect(getActivityWindows(NOW, "America/Los_Angeles").rollingFourWeeksStartAt)
      .toBe("2026-07-17T19:00:00.000Z");
  });
});
