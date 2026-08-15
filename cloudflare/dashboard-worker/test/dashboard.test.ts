import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it } from "vitest";
import { CONFIG_DEFAULTS } from "../src/config";
import {
  getActivityWindows,
  getReportingPeriod,
  getRollingPeriod,
  getSearchConsoleThreeMonthPeriod,
  getYearToDatePeriod,
} from "../src/lib/date";
import { fetchWithRetry, parseRetryAfter } from "../src/lib/retry";
import {
  ACTIVE_METRIC_KEYS,
  createUnconfiguredSnapshot,
  sanitizeSnapshot,
  sanitizeStoredSnapshot,
  type ActiveDashboardSnapshot,
  toPublicSnapshot,
} from "../src/snapshot";
import {
  countAppointmentsCreatedByUser,
  countFreshLeads,
  countOutboundCalls,
  fetchFollowUpBossMetrics,
  outboundCallIds,
  outboundActivityIds,
  parseFollowUpBossTotal,
} from "../src/sources/follow-up-boss";
import {
  costMicrosToUsd,
  fetchGoogleAdsMetrics,
  parseGoogleAdsDailyPerformance,
  sumMatchingLeadConversions,
} from "../src/sources/google-ads";
import {
  fetchGoogleSearchConsoleMetrics,
  parseLatestSearchConsoleDate,
  parseSearchConsoleAggregate,
} from "../src/sources/google-search-console";
import {
  aggregateClosedDeals,
  closedStageIds,
  countActiveLeaderboardAgents,
  countPersonalClosedDeals,
  fetchFollowUpBossTeamMetrics,
  parseDealsLeaderboard,
} from "../src/sources/follow-up-boss-team";
import {
  countIncompletePageRows,
  fetchGoogleSheetsMetrics,
  parseDirectCell,
} from "../src/sources/google-sheets";
import {
  ACTIVE_REALTY_PROGRESS_KEY,
  ACTIVE_REALTY_PROGRESS_MAX_BODY_BYTES,
  fetchActiveRealtyProgressMetrics,
  type ActiveRealtyProgressRecord,
} from "../src/sources/active-realty-progress";
import { handleRequest } from "../src/index";
import {
  deriveTeamCommissionRoas,
  mergeSnapshot,
  SNAPSHOT_KEY,
  type MetricResultMap,
} from "../src/sync";
import type {
  DashboardEnv,
  DashboardSnapshot,
  MetricFetchResult,
  SecretBindings,
} from "../src/types";

const NOW = new Date("2026-08-14T19:00:00.000Z");
const DAY_START = "2026-08-14T07:00:00.000Z";
const MONTH_START = "2026-08-01T07:00:00.000Z";
const PROGRESS_TOKEN = "test-active-realty-progress-token";
const VALID_PROGRESS_RECORD = {
  schemaVersion: 1,
  sourceRepo: "iDroza/activerealty-com",
  sourceRef: "refs/heads/main",
  sourceSha: "abcdef0123456789abcdef0123456789abcdef01",
  runId: "9876543210",
  publishedAt: "2026-08-14T18:30:00.000Z",
  shellPagesRemaining: 37,
  setsRemaining: 4,
} as const satisfies ActiveRealtyProgressRecord;

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
    totalDialsYtd: successful(1842),
    personalDealsClosedYtd: successful(3),
    googleAdsSpendMtd: successful(2362.175313),
    googleAdsLeadsMtd: successful(107),
    googleAdsCostPerClickMtd: successful(1.968479),
    googleAdsCostPerLeadMtd: successful(22.076405),
    googleAdsSpendYtd: successful(18400.5),
    googleAdsLeadsYtd: successful(721),
    googleAdsCostPerLeadYtd: successful(25.520804),
    teamCommissionRoasYtd: successful(51.781207),
    activeRealtyClicksRolling90d: successful(11474),
    activeRealtyImpressionsRolling90d: successful(647748),
    activeRealtyCtrRolling90d: successful(0.0177168),
    activeRealtyPositionRolling90d: successful(10.5),
    jtClicksRolling90d: successful(1200),
    jtImpressionsRolling90d: successful(88000),
    jtCtrRolling90d: successful(0.013636),
    jtPositionRolling90d: successful(17.2),
    teamCommissionYtd: successful(40605),
    teamSalesYtd: successful(3),
    teamVolumeYtd: successful(1770000),
    teamActiveAgentsYtd: successful(2),
    shellPagesRemaining: successful(1191),
    setsRemaining: successful(120),
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
  return { ...env, ...secrets } as DashboardEnv;
}

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function progressRequest(
  body: string,
  token: string | null = PROGRESS_TOKEN,
): Request {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (token !== null) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return new Request(
    "https://drozq.com/api/dashboard/admin/shell-progress",
    { method: "POST", headers, body },
  );
}

function progressJsonRequest(
  payload: unknown,
  token: string | null = PROGRESS_TOKEN,
): Request {
  return progressRequest(JSON.stringify(payload), token);
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
    env.DASHBOARD_KV.delete("dashboard:fub:dials:v1"),
    env.DASHBOARD_KV.delete("dashboard:fub:dials:v2"),
    env.DASHBOARD_KV.delete("dashboard:google_ads:accounts:v2"),
    env.DASHBOARD_KV.delete("dashboard:search_console:aggregate:v1"),
    env.DASHBOARD_KV.delete("dashboard:fub:team:v1"),
    env.DASHBOARD_KV.delete("dashboard:fub:team:v2"),
    env.DASHBOARD_KV.delete("dashboard:fub:team:v3"),
    env.DASHBOARD_KV.delete("dashboard:fub:team:v4"),
    env.DASHBOARD_KV.delete("dashboard:sync:lease:v2"),
    env.DASHBOARD_KV.delete(ACTIVE_REALTY_PROGRESS_KEY),
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
    const calls = [
      { id: 1, created: "2026-08-14T18:00:00.000Z", userId: 659, isIncoming: false },
      { id: 2, created: "2026-08-14T18:01:00.000Z", userId: 659, isIncoming: true },
      { id: 3, created: "2026-08-14T18:02:00.000Z", userId: 42, isIncoming: false },
    ];
    expect(countOutboundCalls(calls, "659", DAY_START, NOW.toISOString())).toBe(1);
    expect(outboundCallIds(calls, "659", DAY_START, NOW.toISOString())).toEqual(["1"]);
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

  it("fetches all personal FUB activity metrics and deduplicates incremental scans", async () => {
    let authorization = "";
    const callStarts: string[] = [];
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = new URL(String(input));
      authorization = new Headers(init?.headers).get("Authorization") ?? "";
      if (url.pathname.endsWith("/me")) {
        return jsonResponse({ id: 659 });
      }
      if (url.pathname.endsWith("/calls")) {
        callStarts.push(url.searchParams.get("createdAfter") ?? "");
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
    expect(first.totalDialsYtd).toMatchObject({ kind: "ok", value: 1 });
    expect(second.totalDialsYtd).toMatchObject({ kind: "ok", value: 1 });
    expect(second.textsToday).toMatchObject({ kind: "ok", value: 1 });
    expect(second.emailsToday).toMatchObject({ kind: "ok", value: 1 });
    expect(callStarts).toContain("2026-01-01T08:00:00.000Z");
    expect(callStarts).toContain("2026-08-14T18:45:00.000Z");
  });

  it("uses FUB keyset cursors for deep YTD dial pagination", async () => {
    const dialRequests: Array<{ next: string | null; offset: string | null }> = [];
    const totalDials = 801;
    const fetcher = async (input: RequestInfo | URL): Promise<Response> => {
      const url = new URL(String(input));
      if (url.pathname.endsWith("/me")) {
        return jsonResponse({ id: 659 });
      }
      if (
        url.pathname.endsWith("/calls") &&
        url.searchParams.get("createdAfter") === "2026-01-01T08:00:00.000Z"
      ) {
        const request = {
          next: url.searchParams.get("next"),
          offset: url.searchParams.get("offset"),
        };
        dialRequests.push(request);
        const pageIndex = request.next === null
          ? 0
          : Number(/^cursor-page-(\d+)$/u.exec(request.next)?.[1]);
        if (!Number.isSafeInteger(pageIndex) || pageIndex < 0) {
          return new Response("", { status: 400 });
        }
        const firstId = pageIndex * 100 + 1;
        const pageSize = Math.min(100, totalDials - pageIndex * 100);
        const calls = Array.from({ length: pageSize }, (_, index) => ({
          id: firstId + index,
          created: "2026-08-14T18:00:00.000Z",
          userId: 659,
          isIncoming: false,
        }));
        const next = firstId + pageSize - 1 < totalDials
          ? `cursor-page-${pageIndex + 1}`
          : null;
        return jsonResponse({
          calls,
          _metadata: { total: totalDials, limit: 100, next },
        });
      }
      if (url.pathname.endsWith("/calls")) {
        return collection("calls", []);
      }
      if (url.pathname.endsWith("/appointments")) {
        return collection("appointments", []);
      }
      if (url.pathname.endsWith("/people")) {
        return collection("people", []);
      }
      return new Response("", { status: 404 });
    };
    const dashboardEnv = withSecrets({ FUB_API_KEY: "test-fub-key" });
    const first = await fetchFollowUpBossMetrics(
      dashboardEnv,
      "America/Los_Angeles",
      { fetcher, sleep: noDelay, now: NOW },
    );
    const partialState = JSON.parse(
      (await env.DASHBOARD_KV.get("dashboard:fub:dials:v2")) ?? "null",
    ) as {
      version?: number;
      reconciliation?: {
        pagesScanned?: number;
        nextCursor?: string;
        count?: number;
        seen?: string[];
      };
    } | null;
    const second = await fetchFollowUpBossMetrics(
      dashboardEnv,
      "America/Los_Angeles",
      { fetcher, sleep: noDelay, now: NOW },
    );

    expect(first.totalDialsYtd).toMatchObject({
      kind: "error",
      category: "in_progress",
    });
    expect(partialState?.version).toBe(2);
    expect(partialState?.reconciliation).toMatchObject({
      pagesScanned: 8,
      nextCursor: "cursor-page-8",
      count: 800,
    });
    expect(partialState?.reconciliation?.seen).toHaveLength(0);
    expect(second.totalDialsYtd).toMatchObject({ kind: "ok", value: 801 });
    expect(dialRequests).toHaveLength(9);
    expect(dialRequests[0]).toEqual({ next: null, offset: "0" });
    expect(dialRequests[8]).toEqual({ next: "cursor-page-8", offset: null });
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

  it("parses daily all-account spend and conversions", () => {
    expect(parseGoogleAdsDailyPerformance([{
      segments: { date: "2026-08-14" },
      metrics: { costMicros: "2500000", conversions: "3", clicks: "11" },
    }])).toEqual([{
      date: "2026-08-14",
      costMicros: 2500000n,
      conversions: 3,
      clicks: 11,
    }]);
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
      expect(body.query).toContain("BETWEEN '2026-01-01' AND '2026-08-14'");
      queriedCustomers.push(customerId);
      const performance: Record<string, [string, number, number]> = {
        "3351363652": ["0", 0, 100],
        "7216252244": ["1352715303", 102, 900],
        "4069972406": ["1009460010", 5, 200],
      };
      const values = performance[customerId];
      if (values === undefined) {
        return new Response("", { status: 404 });
      }
      return jsonResponse({ results: [{
        segments: { date: "2026-08-14" },
        metrics: {
          costMicros: values[0],
          conversions: values[1],
          clicks: values[2],
        },
      }] });
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
      getYearToDatePeriod(NOW, CONFIG_DEFAULTS.reportingTimeZone),
      { fetcher, sleep: noDelay, now: NOW },
    );

    expect(tokenCalls).toBe(1);
    expect(queriedCustomers.sort()).toEqual(["3351363652", "4069972406", "7216252244"]);
    expect(result.googleAdsSpendMtd).toMatchObject({ kind: "ok" });
    expect(result.googleAdsSpendMtd.kind === "ok" ? result.googleAdsSpendMtd.value : null)
      .toBeCloseTo(2362.175313, 6);
    expect(result.googleAdsLeadsMtd).toMatchObject({ kind: "ok", value: 107 });
    expect(result.googleAdsCostPerClickMtd.kind === "ok"
      ? result.googleAdsCostPerClickMtd.value
      : null).toBeCloseTo(1.9684794275, 6);
    expect(result.googleAdsCostPerLeadMtd.kind === "ok"
      ? result.googleAdsCostPerLeadMtd.value
      : null).toBeCloseTo(22.076404794, 6);
    expect(result.googleAdsLeadsYtd).toMatchObject({ kind: "ok", value: 107 });
    expect(result.googleAdsCostPerLeadYtd.kind === "ok"
      ? result.googleAdsCostPerLeadYtd.value
      : null).toBeCloseTo(22.076404794, 6);
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
        : jsonResponse({ results: [{
            segments: { date: "2026-08-14" },
            metrics: { costMicros: "1000000", conversions: 1, clicks: 2 },
          }] });
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
      getYearToDatePeriod(NOW, CONFIG_DEFAULTS.reportingTimeZone),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.googleAdsSpendMtd.kind).toBe("error");
    expect(result.googleAdsLeadsMtd.kind).toBe("error");
    expect(result.googleAdsCostPerClickMtd.kind).toBe("error");
    expect(result.googleAdsCostPerLeadMtd.kind).toBe("error");
  });

  it("derives period-matched blended commission ROAS", () => {
    const result = deriveTeamCommissionRoas(
      successful(952812),
      successful(39125.5),
    );
    expect(result.kind === "ok" ? result.value : null).toBeCloseTo(24.3527, 4);
  });

  it("does not publish Infinity when YTD ad spend is zero", () => {
    expect(deriveTeamCommissionRoas(successful(952812), successful(0)))
      .toMatchObject({ kind: "error", category: "no_data" });
  });
});

describe("Google Search Console Performance aggregation", () => {
  it("parses one property-level aggregate row", () => {
    expect(parseSearchConsoleAggregate({ rows: [{
      clicks: 11474,
      impressions: 647748,
      ctr: 0.0177168,
      position: 10.5,
    }] })).toEqual({
      clicks: 11474,
      impressions: 647748,
      ctr: 0.0177168,
      position: 10.5,
    });
  });

  it("discovers the newest available Search Console date", () => {
    expect(parseLatestSearchConsoleDate({ rows: [
      { keys: ["2026-08-10"], clicks: 100, impressions: 1000 },
      { keys: ["2026-08-12"], clicks: 120, impressions: 1200 },
      { keys: ["2026-08-11"], clicks: 110, impressions: 1100 },
    ] })).toBe("2026-08-12");
  });

  it("matches the Search Console UI's latest past-three-month range", async () => {
    let tokenCalls = 0;
    const availabilitySites: string[] = [];
    const aggregateSites: string[] = [];
    const allUrls: string[] = [];
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      allUrls.push(url);
      if (url === "https://oauth2.googleapis.com/token") {
        tokenCalls += 1;
        return jsonResponse({ access_token: "gsc-test-access-token" });
      }
      const pathname = new URL(url).pathname;
      const prefix = "/webmasters/v3/sites/";
      const suffix = "/searchAnalytics/query";
      expect(pathname.startsWith(prefix)).toBe(true);
      expect(pathname.endsWith(suffix)).toBe(true);
      const site = decodeURIComponent(
        pathname.slice(prefix.length, -suffix.length),
      );
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      if (Array.isArray(body["dimensions"])) {
        availabilitySites.push(site);
        expect(body).toMatchObject({
          startDate: "2026-08-01",
          endDate: "2026-08-14",
          dimensions: ["date"],
          type: "web",
          aggregationType: "byProperty",
          dataState: "final",
          rowLimit: 14,
        });
        return jsonResponse({ rows: [
          { keys: ["2026-08-11"], clicks: 20, impressions: 400 },
          { keys: ["2026-08-12"], clicks: 22, impressions: 420 },
        ] });
      }
      aggregateSites.push(site);
      expect(body).toMatchObject({
        startDate: "2026-05-13",
        endDate: "2026-08-12",
        type: "web",
        aggregationType: "byProperty",
        dataState: "all",
        rowLimit: 1,
      });
      return jsonResponse({ rows: [{
        clicks: site === "sc-domain:activerealty.com" ? 11474 : 307,
        impressions: site === "sc-domain:activerealty.com" ? 647748 : 43400,
        ctr: site === "sc-domain:activerealty.com" ? 0.0177168 : 0.0070737,
        position: site === "sc-domain:activerealty.com" ? 10.5 : 11.5,
      }] });
    };
    const result = await fetchGoogleSearchConsoleMetrics(
      withSecrets({
        GOOGLE_SEARCH_CONSOLE_CLIENT_ID: "test-client-id",
        GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET: "test-client-secret",
        GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN: "test-refresh-token",
      }),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(tokenCalls).toBe(1);
    expect(result.period).toEqual({
      startDate: "2026-05-13",
      endDate: "2026-08-12",
      timeZone: "America/Los_Angeles",
    });
    expect(result.metrics.activeRealtyClicksRolling90d).toMatchObject({
      kind: "ok",
      value: 11474,
    });
    expect(result.metrics.jtClicksRolling90d).toMatchObject({
      kind: "ok",
      value: 307,
    });
    expect(allUrls.length).toBe(5);
    expect(availabilitySites.sort()).toEqual([
      "https://justintye.com/",
      "sc-domain:activerealty.com",
    ]);
    expect(aggregateSites.sort()).toEqual([
      "https://justintye.com/",
      "sc-domain:activerealty.com",
    ]);
    expect(result.metrics.jtImpressionsRolling90d).toMatchObject({ kind: "ok" });
  });

  it("treats a missing aggregate row as no data, never zero", () => {
    expect(() => parseSearchConsoleAggregate({ rows: [] })).toThrow("no_data");
    expect(() => parseLatestSearchConsoleDate({ rows: [] })).toThrow("no_data");
  });
});

describe("Follow Up Boss YTD team aggregation", () => {
  const period = getYearToDatePeriod(NOW, "America/Los_Angeles");
  const leaderboard = {
    totals: {
      closedPriceTotal: "43198750",
      closedCommissionTotal: "952812",
      closedDealCount: "56",
      closedPriceAverage: "771406",
    },
    users: [
      { userId: 1, closedDealCount: "39" },
      { userId: 2, closedDealCount: "4" },
      { userId: 3, closedDealCount: "1" },
      { userId: 4, closedDealCount: "0" },
    ],
  };
  const pipelines = [
    { stages: [{ id: 10, name: " Active " }, { id: 20, name: "CLOSED" }] },
  ];
  const deals = [
    {
      id: 1,
      status: "active",
      stageId: 20,
      projectedCloseDate: "2026-02-10",
      price: "750000",
      commissionValue: "18000",
      teamCommission: "5000",
      users: [{ id: 659 }],
    },
    {
      id: 2,
      status: "active",
      stageId: 20,
      projectedCloseDate: "2026-07-11T00:00:00Z",
      price: 1020000,
      commissionValue: 22605,
      teamCommission: 8000,
      users: [{ id: 659 }, { id: 777 }],
    },
    {
      id: 3,
      status: "active",
      stageId: 10,
      projectedCloseDate: "2026-06-01",
      price: 500000,
      commissionValue: 12000,
      teamCommission: 3000,
      users: [{ id: 888 }],
    },
  ];

  it("parses the authoritative leaderboard totals without summing duplicate user rows", () => {
    expect(parseDealsLeaderboard(leaderboard)).toEqual({
      commission: 952812,
      sales: 56,
      volume: 43198750,
      activeUserIds: ["1", "2", "3"],
      closedDealsByUserId: { "1": 39, "2": 4, "3": 1, "4": 0 },
    });
  });

  it("rejects malformed leaderboard totals instead of publishing false zeros", () => {
    expect(() => parseDealsLeaderboard({ totals: {}, users: [] })).toThrow();
  });

  it("counts positive leaderboard users while excluding lenders and service accounts", () => {
    const directory = new Map([
      ["1", { id: "1", name: "Justin Tye", role: "Agent" }],
      ["2", { id: "2", name: "Active Agents", role: "Agent" }],
      ["3", { id: "3", name: "Trusted Rate", role: "Lender" }],
    ]);
    expect(countActiveLeaderboardAgents(["1", "2", "3"], directory, ["active agents"]))
      .toBe(1);
  });

  it("keeps a broker-key fallback and matches the leaderboard's gross commission", () => {
    const stages = closedStageIds(pipelines, ["closed"]);
    expect([...stages]).toEqual([20]);
    expect(aggregateClosedDeals(deals, stages, period)).toEqual({
      commission: 40605,
      sales: 2,
      volume: 1770000,
      activeAgents: 2,
    });
    expect(countPersonalClosedDeals(deals, stages, period, "659")).toBe(2);
    expect(countPersonalClosedDeals(deals, stages, period, "777")).toBe(1);
  });

  it("rejects a closed deal whose gross commission is missing", () => {
    const stages = closedStageIds(pipelines, ["closed"]);
    const dealWithoutCommission = { ...deals[0], commissionValue: undefined };
    expect(() => aggregateClosedDeals([dealWithoutCommission], stages, period))
      .toThrow();
  });

  it("fetches the same all-pipeline leaderboard as the UI and reuses its five-minute cache", async () => {
    let requests = 0;
    const authorizationHeaders: string[] = [];
    const fetcher = async (
      input: RequestInfo | URL,
      init?: RequestInit,
    ): Promise<Response> => {
      requests += 1;
      const url = new URL(String(input));
      authorizationHeaders.push(new Headers(init?.headers).get("Authorization") ?? "");
      if (url.pathname.endsWith("/deals/leaderboard")) {
        expect(url.searchParams.get("start")).toBe("2026-01-01");
        expect(url.searchParams.get("end")).toBe("2026-08-14");
        return jsonResponse(leaderboard);
      }
      if (url.pathname.endsWith("/me")) {
        return jsonResponse({ id: 1 });
      }
      if (url.pathname.endsWith("/users")) {
        return collection("users", [
          { id: 1, name: "Justin Tye", role: "Agent" },
          { id: 2, name: "Active Agents", role: "Agent" },
          { id: 3, name: "Derek Liu", role: "Agent" },
          { id: 4, name: "Trusted Rate", role: "Lender" },
        ]);
      }
      return new Response("", { status: 404 });
    };
    const dashboardEnv = withSecrets({ FUB_API_KEY: "test-personal-key" });
    const first = await fetchFollowUpBossTeamMetrics(
      dashboardEnv,
      period,
      { fetcher, sleep: noDelay, now: NOW },
    );
    const second = await fetchFollowUpBossTeamMetrics(
      dashboardEnv,
      period,
      { fetcher, sleep: noDelay, now: new Date(NOW.getTime() + 60_000) },
    );
    expect(first.teamCommissionYtd).toMatchObject({ kind: "ok", value: 952812 });
    expect(first.teamSalesYtd).toMatchObject({ kind: "ok", value: 56 });
    expect(first.teamActiveAgentsYtd).toMatchObject({ kind: "ok", value: 2 });
    expect(first.personalDealsClosedYtd).toMatchObject({ kind: "ok", value: 39 });
    expect(second.teamVolumeYtd).toMatchObject({ kind: "ok", value: 43198750 });
    expect(second.personalDealsClosedYtd).toMatchObject({ kind: "ok", value: 39 });
    expect(requests).toBe(3);
    expect(new Set(authorizationHeaders)).toEqual(
      new Set([`Basic ${btoa("test-personal-key:")}`]),
    );
  });

  it("leaves team metrics unconfigured when no Follow Up Boss key exists", async () => {
    const result = await fetchFollowUpBossTeamMetrics(
      withSecrets({}),
      period,
      { sleep: noDelay, now: NOW },
    );
    expect(result.teamSalesYtd).toMatchObject({ kind: "unconfigured" });
  });

  it("preserves the three authoritative totals when only the user directory fails", async () => {
    const fetcher = async (input: RequestInfo | URL): Promise<Response> => {
      const url = new URL(String(input));
      if (url.pathname.endsWith("/deals/leaderboard")) {
        return jsonResponse(leaderboard);
      }
      return new Response("", { status: 403 });
    };
    const result = await fetchFollowUpBossTeamMetrics(
      withSecrets({ FUB_API_KEY: "test-agent-key" }),
      period,
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.teamCommissionYtd).toMatchObject({ kind: "ok", value: 952812 });
    expect(result.teamSalesYtd).toMatchObject({ kind: "ok", value: 56 });
    expect(result.teamVolumeYtd).toMatchObject({ kind: "ok", value: 43198750 });
    expect(result.teamActiveAgentsYtd).toMatchObject({ kind: "error" });
    expect(result.personalDealsClosedYtd).toMatchObject({ kind: "error" });
  });
});

describe("Google Sheets production queue", () => {
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

  it("uses one service-account token and one batch read for both direct cells", async () => {
    const privateKey = await generateEscapedTestPrivateKey();
    let tokenCalls = 0;
    let sheetCalls = 0;
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url === "https://oauth2.googleapis.com/token") {
        tokenCalls += 1;
        expect(String(init?.body)).toContain("assertion=");
        return jsonResponse({ access_token: "test-sheets-access-token" });
      }
      sheetCalls += 1;
      const endpoint = new URL(url);
      expect(endpoint.pathname).toBe(
        "/v4/spreadsheets/test-sheet-id/values:batchGet",
      );
      expect(endpoint.searchParams.getAll("ranges")).toEqual([
        "Summary!B5",
        "Summary!B8",
      ]);
      return jsonResponse({
        valueRanges: [
          { range: "Summary!B5", values: [["1191"]] },
          { range: "Summary!B8", values: [[120]] },
        ],
      });
    };
    const result = await fetchGoogleSheetsMetrics(
      withSecrets({
        GOOGLE_SERVICE_ACCOUNT_EMAIL: "dashboard@test-project.iam.gserviceaccount.com",
        GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: privateKey,
        GOOGLE_SHEETS_SPREADSHEET_ID: "test-sheet-id",
        GOOGLE_SHEETS_REMAINING_RANGE: "Summary!B5",
        GOOGLE_SHEETS_SETS_REMAINING_RANGE: "Summary!B8",
      }),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(tokenCalls).toBe(1);
    expect(sheetCalls).toBe(1);
    expect(result.shellPagesRemaining).toMatchObject({ kind: "ok", value: 1191 });
    expect(result.setsRemaining).toMatchObject({ kind: "ok", value: 120 });
  });

  it("supports a shell page table and a direct sets cell in the same batch", async () => {
    const privateKey = await generateEscapedTestPrivateKey();
    const fetcher = async (input: RequestInfo | URL): Promise<Response> => {
      if (String(input) === "https://oauth2.googleapis.com/token") {
        return jsonResponse({ access_token: "test-sheets-access-token" });
      }
      return jsonResponse({
        valueRanges: [
          {
            values: [
              ["Page", "Status"],
              ["About", " complete "],
              ["Buyers", "Working"],
              ["", "draft"],
              [null, null],
              ["Sellers", "LIVE"],
            ],
          },
          { values: [[1]] },
        ],
      });
    };
    const result = await fetchGoogleSheetsMetrics(
      withSecrets({
        GOOGLE_SERVICE_ACCOUNT_EMAIL: "dashboard@test-project.iam.gserviceaccount.com",
        GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: privateKey,
        GOOGLE_SHEETS_SPREADSHEET_ID: "test-sheet-id",
        GOOGLE_SHEETS_PAGES_RANGE: "Shell Pages!A:B",
        GOOGLE_SHEETS_SETS_REMAINING_RANGE: "Summary!B8",
        GOOGLE_SHEETS_COMPLETE_VALUES: "complete,live",
      }),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.shellPagesRemaining).toMatchObject({ kind: "ok", value: 1 });
    expect(result.setsRemaining).toMatchObject({ kind: "ok", value: 1 });
  });

  it("isolates a malformed sets cell without erasing the valid shell count", async () => {
    const privateKey = await generateEscapedTestPrivateKey();
    const fetcher = async (input: RequestInfo | URL): Promise<Response> => {
      if (String(input) === "https://oauth2.googleapis.com/token") {
        return jsonResponse({ access_token: "test-sheets-access-token" });
      }
      return jsonResponse({
        valueRanges: [
          { values: [[1191]] },
          {},
        ],
      });
    };
    const result = await fetchGoogleSheetsMetrics(
      withSecrets({
        GOOGLE_SERVICE_ACCOUNT_EMAIL: "dashboard@test-project.iam.gserviceaccount.com",
        GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: privateKey,
        GOOGLE_SHEETS_SPREADSHEET_ID: "test-sheet-id",
        GOOGLE_SHEETS_REMAINING_RANGE: "Summary!B5",
        GOOGLE_SHEETS_SETS_REMAINING_RANGE: "Summary!B8",
      }),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.shellPagesRemaining).toMatchObject({ kind: "ok", value: 1191 });
    expect(result.setsRemaining).toMatchObject({
      kind: "error",
      category: "schema",
      responseStatus: 200,
    });
  });

  it("marks a missing sets range unconfigured instead of displaying zero", async () => {
    const result = await fetchGoogleSheetsMetrics(withSecrets({}));
    expect(result.shellPagesRemaining).toMatchObject({ kind: "unconfigured" });
    expect(result.setsRemaining).toMatchObject({ kind: "unconfigured" });
  });
});

describe("Active Realty shell-progress receiver", () => {
  it("rejects missing and invalid authentication without writing", async () => {
    for (const token of [null, "wrong-progress-token"]) {
      const response = await handleRequest(
        progressJsonRequest(VALID_PROGRESS_RECORD, token),
        withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
      );
      expect(response.status).toBe(401);
      expect(response.headers.get("Cache-Control")).toBe("no-store");
      expect(response.headers.has("Access-Control-Allow-Origin")).toBe(false);
      expect(await response.json()).toEqual({ ok: false, error: "unauthorized" });
      expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY)).toBeNull();
    }
  });

  it("rejects malformed, non-object, and incomplete JSON without writing", async () => {
    const incomplete = { ...VALID_PROGRESS_RECORD } as Record<string, unknown>;
    delete incomplete["setsRemaining"];
    const requests = [
      progressRequest("{"),
      progressJsonRequest([]),
      progressJsonRequest(incomplete),
    ];
    for (const request of requests) {
      const response = await handleRequest(
        request,
        withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
      );
      expect(response.status).toBe(400);
      expect(response.headers.get("Cache-Control")).toBe("no-store");
      expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY)).toBeNull();
    }
  });

  it("rejects oversized bodies before parsing without writing", async () => {
    const response = await handleRequest(
      progressRequest("x".repeat(ACTIVE_REALTY_PROGRESS_MAX_BODY_BYTES + 1)),
      withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
    );
    expect(response.status).toBe(413);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(await response.json()).toEqual({
      ok: false,
      error: "payload_too_large",
    });
    expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY)).toBeNull();
  });

  it("rejects additional fields without writing", async () => {
    const response = await handleRequest(
      progressJsonRequest({ ...VALID_PROGRESS_RECORD, unexpected: true }),
      withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
    );
    expect(response.status).toBe(400);
    expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY)).toBeNull();
  });

  it("rejects negative, fractional, and unsafe counts without writing", async () => {
    const invalidCounts = [
      { shellPagesRemaining: -1 },
      { shellPagesRemaining: 1.5 },
      { shellPagesRemaining: Number.MAX_SAFE_INTEGER + 1 },
      { setsRemaining: -1 },
      { setsRemaining: 1.5 },
      { setsRemaining: Number.MAX_SAFE_INTEGER + 1 },
    ];
    for (const invalid of invalidCounts) {
      const response = await handleRequest(
        progressJsonRequest({ ...VALID_PROGRESS_RECORD, ...invalid }),
        withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
      );
      expect(response.status).toBe(400);
      expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY)).toBeNull();
    }
  });

  it("rejects wrong schema version, repository, ref, SHA, timestamp, and run ID", async () => {
    const invalidPayloads = [
      { ...VALID_PROGRESS_RECORD, schemaVersion: 2 },
      { ...VALID_PROGRESS_RECORD, sourceRepo: "iDroza/not-active-realty" },
      { ...VALID_PROGRESS_RECORD, sourceRef: "refs/heads/develop" },
      { ...VALID_PROGRESS_RECORD, sourceSha: "ABCDEF0123456789ABCDEF0123456789ABCDEF01" },
      { ...VALID_PROGRESS_RECORD, publishedAt: "2026-02-30T12:00:00.000Z" },
      { ...VALID_PROGRESS_RECORD, publishedAt: "2026-08-14T12:00:00-07:00" },
      { ...VALID_PROGRESS_RECORD, runId: "0" },
      { ...VALID_PROGRESS_RECORD, runId: "01" },
      { ...VALID_PROGRESS_RECORD, runId: 123 },
    ];
    for (const payload of invalidPayloads) {
      const response = await handleRequest(
        progressJsonRequest(payload),
        withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
      );
      expect(response.status).toBe(400);
      expect(response.headers.get("Cache-Control")).toBe("no-store");
      expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY)).toBeNull();
    }
  });

  it("writes exactly the sanitized record for a valid delivery", async () => {
    const response = await handleRequest(
      progressJsonRequest(VALID_PROGRESS_RECORD),
      withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
    );
    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(response.headers.has("Access-Control-Allow-Origin")).toBe(false);
    expect(await response.json()).toEqual({
      ok: true,
      idempotent: false,
      record: VALID_PROGRESS_RECORD,
    });
    const stored = await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY);
    expect(stored).toBe(JSON.stringify(VALID_PROGRESS_RECORD));
    expect(Object.keys(JSON.parse(stored ?? "null") as object)).toEqual([
      "schemaVersion",
      "sourceRepo",
      "sourceRef",
      "sourceSha",
      "runId",
      "publishedAt",
      "shellPagesRemaining",
      "setsRemaining",
    ]);
  });

  it("treats an identical retry as idempotent", async () => {
    const dashboardEnv = withSecrets({
      ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN,
    });
    const first = await handleRequest(
      progressJsonRequest(VALID_PROGRESS_RECORD),
      dashboardEnv,
    );
    const second = await handleRequest(
      progressJsonRequest(VALID_PROGRESS_RECORD),
      dashboardEnv,
    );
    expect(first.status).toBe(200);
    expect(second.status).toBe(200);
    expect(await second.json()).toEqual({
      ok: true,
      idempotent: true,
      record: VALID_PROGRESS_RECORD,
    });
    expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY))
      .toBe(JSON.stringify(VALID_PROGRESS_RECORD));
  });

  it("rejects changed content for the same run ID without replacing KV", async () => {
    const dashboardEnv = withSecrets({
      ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN,
    });
    await handleRequest(progressJsonRequest(VALID_PROGRESS_RECORD), dashboardEnv);
    const changed = {
      ...VALID_PROGRESS_RECORD,
      shellPagesRemaining: VALID_PROGRESS_RECORD.shellPagesRemaining + 1,
    };
    const response = await handleRequest(progressJsonRequest(changed), dashboardEnv);
    expect(response.status).toBe(409);
    expect(await response.json()).toEqual({
      ok: false,
      error: "run_id_conflict",
    });
    expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY))
      .toBe(JSON.stringify(VALID_PROGRESS_RECORD));
  });

  it("compares run IDs losslessly and rejects an older delivery", async () => {
    const dashboardEnv = withSecrets({
      ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN,
    });
    const newer = { ...VALID_PROGRESS_RECORD, runId: "9007199254740993" };
    const older = {
      ...VALID_PROGRESS_RECORD,
      runId: "9007199254740992",
      sourceSha: "1234567890abcdef1234567890abcdef12345678",
    };
    const accepted = await handleRequest(progressJsonRequest(newer), dashboardEnv);
    const rejected = await handleRequest(progressJsonRequest(older), dashboardEnv);
    expect(accepted.status).toBe(200);
    expect(rejected.status).toBe(409);
    expect(await rejected.json()).toEqual({ ok: false, error: "stale_run_id" });
    expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY))
      .toBe(JSON.stringify(newer));
  });

  it("accepts increased counts from a newer run", async () => {
    const dashboardEnv = withSecrets({
      ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN,
    });
    await handleRequest(
      progressJsonRequest({ ...VALID_PROGRESS_RECORD, runId: "100" }),
      dashboardEnv,
    );
    const increased = {
      ...VALID_PROGRESS_RECORD,
      runId: "101",
      sourceSha: "1234567890abcdef1234567890abcdef12345678",
      shellPagesRemaining: VALID_PROGRESS_RECORD.shellPagesRemaining + 10,
      setsRemaining: VALID_PROGRESS_RECORD.setsRemaining + 2,
    };
    const response = await handleRequest(
      progressJsonRequest(increased),
      dashboardEnv,
    );
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      ok: true,
      idempotent: false,
      record: increased,
    });
    expect(await env.DASHBOARD_KV.get(ACTIVE_REALTY_PROGRESS_KEY))
      .toBe(JSON.stringify(increased));
  });

  it("reads both metrics from KV with publishedAt as observedAt", async () => {
    await env.DASHBOARD_KV.put(
      ACTIVE_REALTY_PROGRESS_KEY,
      JSON.stringify(VALID_PROGRESS_RECORD),
    );
    const result = await fetchActiveRealtyProgressMetrics(withSecrets({}));
    expect(result.shellPagesRemaining).toMatchObject({
      kind: "ok",
      value: VALID_PROGRESS_RECORD.shellPagesRemaining,
      observedAt: VALID_PROGRESS_RECORD.publishedAt,
    });
    expect(result.setsRemaining).toMatchObject({
      kind: "ok",
      value: VALID_PROGRESS_RECORD.setsRemaining,
      observedAt: VALID_PROGRESS_RECORD.publishedAt,
    });
  });

  it("preserves prior values as stale when progress KV is missing or corrupt", async () => {
    const previous = makeSnapshot(new Date("2026-08-14T17:00:00.000Z"));
    const invalidSchema = JSON.stringify({
      ...VALID_PROGRESS_RECORD,
      sourceRepo: "iDroza/not-active-realty",
    });
    for (const stored of [null, "{not-json", invalidSchema] as const) {
      if (stored === null) {
        await env.DASHBOARD_KV.delete(ACTIVE_REALTY_PROGRESS_KEY);
      } else {
        await env.DASHBOARD_KV.put(ACTIVE_REALTY_PROGRESS_KEY, stored);
      }
      const progress = await fetchActiveRealtyProgressMetrics(withSecrets({}));
      const results = allSuccessfulResults();
      results.shellPagesRemaining = progress.shellPagesRemaining;
      results.setsRemaining = progress.setsRemaining;
      const merged = mergeSnapshot(
        previous,
        results,
        NOW,
        getReportingPeriod(NOW, "America/Los_Angeles"),
      );
      expect(merged.metrics.shellPagesRemaining).toMatchObject({
        value: previous.metrics.shellPagesRemaining.value,
        updatedAt: previous.metrics.shellPagesRemaining.updatedAt,
        status: "stale",
      });
      expect(merged.metrics.setsRemaining).toMatchObject({
        value: previous.metrics.setsRemaining.value,
        updatedAt: previous.metrics.setsRemaining.updatedAt,
        status: "stale",
      });
    }
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

  it("preserves the previous sets value when only that progress metric fails", () => {
    const previousTime = new Date("2026-08-14T18:00:00.000Z");
    const previous = makeSnapshot(previousTime);
    const results = allSuccessfulResults();
    results.shellPagesRemaining = successful(1187);
    results.setsRemaining = failed();
    const merged = mergeSnapshot(
      previous,
      results,
      NOW,
      getReportingPeriod(NOW, "America/Los_Angeles"),
    );
    expect(merged.metrics.shellPagesRemaining).toMatchObject({
      value: 1187,
      status: "ok",
    });
    expect(merged.metrics.setsRemaining).toMatchObject({
      value: 120,
      updatedAt: previousTime.toISOString(),
      status: "stale",
    });
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

  it("uses error, not zero, when the sets metric fails on the first run", () => {
    const results = allSuccessfulResults();
    results.setsRemaining = failed();
    const merged = mergeSnapshot(
      null,
      results,
      NOW,
      getReportingPeriod(NOW, "America/Los_Angeles"),
    );
    expect(merged.metrics.setsRemaining).toMatchObject({
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

  it("uses the longer team, repository, and Search Console freshness policies", () => {
    const snapshot = makeSnapshot(new Date("2026-08-13T12:00:00.000Z"));
    const afterSixteenMinutes = toPublicSnapshot(
      snapshot,
      new Date("2026-08-13T12:16:00.000Z"),
    );
    expect(afterSixteenMinutes.metrics.teamSalesYtd.status).toBe("stale");
    expect(afterSixteenMinutes.metrics.shellPagesRemaining.status).toBe("ok");
    expect(afterSixteenMinutes.metrics.setsRemaining.status).toBe("ok");
    expect(afterSixteenMinutes.metrics.activeRealtyClicksRolling90d.status).toBe("ok");

    const atTwelveHours = toPublicSnapshot(
      snapshot,
      new Date("2026-08-14T00:00:00.000Z"),
    );
    expect(atTwelveHours.metrics.shellPagesRemaining.status).toBe("ok");
    expect(atTwelveHours.metrics.setsRemaining.status).toBe("ok");

    const afterTwelveHours = toPublicSnapshot(
      snapshot,
      new Date("2026-08-14T00:00:00.001Z"),
    );
    expect(afterTwelveHours.metrics.shellPagesRemaining.status).toBe("stale");
    expect(afterTwelveHours.metrics.setsRemaining.status).toBe("stale");

    const afterTwentySevenHours = toPublicSnapshot(
      snapshot,
      new Date("2026-08-14T15:00:00.001Z"),
    );
    expect(afterTwentySevenHours.metrics.activeRealtyClicksRolling90d.status).toBe("stale");
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
      "rolling90DayPeriod",
      "yearToDatePeriod",
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

  it("migrates a saved snapshot without losing its audited reporting windows", () => {
    const snapshot = makeSnapshot();
    const legacy = JSON.parse(JSON.stringify(snapshot)) as {
      metrics: Record<string, unknown>;
      rolling90DayPeriod: DashboardSnapshot["rolling90DayPeriod"];
    };
    delete legacy.metrics["googleAdsCostPerClickMtd"];
    delete legacy.metrics["googleAdsCostPerLeadMtd"];
    delete legacy.metrics["totalDialsYtd"];
    delete legacy.metrics["personalDealsClosedYtd"];
    const migrated = sanitizeStoredSnapshot(legacy);

    expect(migrated?.rolling90DayPeriod).toEqual(snapshot.rolling90DayPeriod);
    expect(migrated?.metrics.googleAdsCostPerClickMtd).toMatchObject({
      value: null,
      status: "unconfigured",
    });
    expect(migrated?.metrics.googleAdsCostPerLeadMtd).toMatchObject({
      value: null,
      status: "unconfigured",
    });
    expect(migrated?.metrics.totalDialsYtd).toMatchObject({
      value: null,
      status: "unconfigured",
    });
    expect(migrated?.metrics.personalDealsClosedYtd).toMatchObject({
      value: null,
      status: "unconfigured",
    });
  });

  it("normalizes legacy Google Sheets progress sources only in stored snapshots", () => {
    const snapshot = makeSnapshot();
    const legacy = JSON.parse(JSON.stringify(snapshot)) as DashboardSnapshot;
    legacy.metrics.shellPagesRemaining.source = "google_sheets";
    legacy.metrics.setsRemaining.source = "google_sheets";

    expect(sanitizeSnapshot(legacy)).toBeNull();
    const migrated = sanitizeStoredSnapshot(legacy);
    expect(migrated?.metrics.shellPagesRemaining).toMatchObject({
      value: snapshot.metrics.shellPagesRemaining.value,
      source: "active_realty_repository",
    });
    expect(migrated?.metrics.setsRemaining).toMatchObject({
      value: snapshot.metrics.setsRemaining.value,
      source: "active_realty_repository",
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
    expect(Object.keys(snapshot.metrics)).toHaveLength(30);
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
    expect(Object.keys(payload.metrics)).toHaveLength(30);
  });

  it("serves the same sanitized snapshot through the browser bootstrap", async () => {
    const snapshot = makeSnapshot();
    await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify({
      ...snapshot,
      privateField: "must-not-ship",
      metrics: {
        ...snapshot.metrics,
        callsToday: {
          ...snapshot.metrics.callsToday,
          rawResponse: "must-not-ship",
        },
      },
    }));
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/bootstrap.js"),
      withSecrets({}),
    );
    const source = await response.text();
    const prefix = '"use strict";window.__DROZQ_DASHBOARD_SNAPSHOT__=';

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe(
      "application/javascript; charset=utf-8",
    );
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(response.headers.get("Cache-Control")).toBe(
      "public, max-age=10, s-maxage=10, stale-while-revalidate=20",
    );
    expect(source.startsWith(prefix)).toBe(true);
    expect(source.endsWith(";")).toBe(true);
    expect(source).not.toContain("must-not-ship");
    const payload = JSON.parse(source.slice(prefix.length, -1)) as DashboardSnapshot;
    expect(sanitizeSnapshot(payload)).not.toBeNull();
    expect(Object.keys(payload.metrics)).toHaveLength(30);
  });

  it("serves an explicit company-safe metric allowlist for Active Realty", async () => {
    await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify(makeSnapshot()));
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/active-summary"),
      withSecrets({}),
    );
    const payload = (await response.json()) as ActiveDashboardSnapshot;

    expect(response.status).toBe(200);
    expect(Object.keys(payload.metrics)).toEqual([...ACTIVE_METRIC_KEYS]);
    expect(payload.metrics.googleAdsCostPerClickMtd.value).toBeCloseTo(1.968479, 6);
    expect(payload.metrics.googleAdsCostPerLeadMtd.value).toBeCloseTo(22.076405, 6);
    for (const personalKey of [
      "callsToday",
      "textsToday",
      "emailsToday",
      "appointmentsSetMtd",
      "freshBuyerLeads",
      "freshSellerLeads",
      "totalDialsYtd",
      "personalDealsClosedYtd",
    ]) {
      expect(personalKey in payload.metrics).toBe(false);
    }
  });

  it("never exposes shell-progress ingest metadata in public summaries", async () => {
    const snapshot = makeSnapshot();
    await env.DASHBOARD_KV.put(
      SNAPSHOT_KEY,
      JSON.stringify({
        ...snapshot,
        sourceRepo: VALID_PROGRESS_RECORD.sourceRepo,
        sourceRef: VALID_PROGRESS_RECORD.sourceRef,
        sourceSha: VALID_PROGRESS_RECORD.sourceSha,
        runId: VALID_PROGRESS_RECORD.runId,
        publishedAt: VALID_PROGRESS_RECORD.publishedAt,
        schemaVersion: VALID_PROGRESS_RECORD.schemaVersion,
        token: PROGRESS_TOKEN,
        metrics: {
          ...snapshot.metrics,
          shellPagesRemaining: {
            ...snapshot.metrics.shellPagesRemaining,
            sourceSha: VALID_PROGRESS_RECORD.sourceSha,
            runId: VALID_PROGRESS_RECORD.runId,
          },
        },
      }),
    );
    await env.DASHBOARD_KV.put(
      ACTIVE_REALTY_PROGRESS_KEY,
      JSON.stringify(VALID_PROGRESS_RECORD),
    );

    for (const pathname of ["summary", "active-summary"]) {
      const response = await handleRequest(
        new Request(`https://drozq.com/api/dashboard/${pathname}`),
        withSecrets({ ACTIVE_REALTY_PROGRESS_TOKEN: PROGRESS_TOKEN }),
      );
      expect(response.status).toBe(200);
      const serialized = JSON.stringify(await response.json());
      for (const privateField of [
        "schemaVersion",
        "sourceRepo",
        "sourceRef",
        "sourceSha",
        "runId",
        "publishedAt",
        "token",
      ]) {
        expect(serialized).not.toContain(`\"${privateField}\"`);
      }
      expect(serialized).not.toContain(PROGRESS_TOKEN);
      expect(serialized).not.toContain(VALID_PROGRESS_RECORD.sourceSha);
    }
  });

  it("serves the company-safe allowlist through the Active Realty bootstrap", async () => {
    await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify(makeSnapshot()));
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/active-bootstrap.js"),
      withSecrets({}),
    );
    const source = await response.text();
    const prefix = '"use strict";window.__ACTIVE_REALTY_DASHBOARD_SNAPSHOT__=';
    expect(source.startsWith(prefix)).toBe(true);
    const payload = JSON.parse(
      source.slice(prefix.length, -1),
    ) as ActiveDashboardSnapshot;
    expect(Object.keys(payload.metrics)).toEqual([...ACTIVE_METRIC_KEYS]);
    expect(source).not.toContain("callsToday");
    expect(source).not.toContain("freshSellerLeads");
    expect(source).not.toContain("totalDialsYtd");
    expect(source).not.toContain("personalDealsClosedYtd");
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
      yearStartAt: "2026-01-01T08:00:00.000Z",
    });
  });

  it("uses an exact rolling 28-day fresh-lead window", () => {
    expect(getActivityWindows(NOW, "America/Los_Angeles").rollingFourWeeksStartAt)
      .toBe("2026-07-17T19:00:00.000Z");
  });

  it("keeps the generic rolling 90-day helper inclusive", () => {
    expect(getRollingPeriod(NOW, "America/Los_Angeles", 90)).toEqual({
      startDate: "2026-05-17",
      endDate: "2026-08-14",
      timeZone: "America/Los_Angeles",
    });
  });

  it("matches Search Console's past-three-month UI range", () => {
    expect(getSearchConsoleThreeMonthPeriod("2026-08-12")).toEqual({
      startDate: "2026-05-13",
      endDate: "2026-08-12",
      timeZone: "America/Los_Angeles",
    });
  });

  it("clamps past-three-month ranges across leap-year month ends", () => {
    expect(getSearchConsoleThreeMonthPeriod("2024-05-31")).toEqual({
      startDate: "2024-03-01",
      endDate: "2024-05-31",
      timeZone: "America/Los_Angeles",
    });
  });

  it("builds a year-to-date period in the reporting time zone", () => {
    expect(getYearToDatePeriod(NOW, "America/Los_Angeles")).toEqual({
      startDate: "2026-01-01",
      endDate: "2026-08-14",
      timeZone: "America/Los_Angeles",
    });
  });
});
