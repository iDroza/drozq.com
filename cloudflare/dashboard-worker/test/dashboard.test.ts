import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it } from "vitest";
import { CONFIG_DEFAULTS } from "../src/config";
import {
  getActivityWindows,
  getReportingPeriod,
  getRollingPeriod,
  getYearToDatePeriod,
} from "../src/lib/date";
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
  parseGoogleAdsDailyPerformance,
  sumMatchingLeadConversions,
} from "../src/sources/google-ads";
import {
  fetchGoogleSearchConsoleMetrics,
  parseSearchConsoleAggregate,
} from "../src/sources/google-search-console";
import {
  aggregateClosedDeals,
  closedStageIds,
  fetchFollowUpBossTeamMetrics,
} from "../src/sources/follow-up-boss-team";
import {
  countIncompletePageRows,
  fetchGoogleSheetsMetrics,
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
    googleAdsSpendRolling90d: successful(8200.5),
    googleAdsClicksRolling90d: successful(3400),
    googleAdsLeadsRolling90d: successful(321),
    googleAdsCostPerLeadRolling90d: successful(25.546729),
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
    env.DASHBOARD_KV.delete("dashboard:search_console:aggregate:v1"),
    env.DASHBOARD_KV.delete("dashboard:fub:team:v1"),
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

  it("parses daily all-account spend, conversions, and clicks", () => {
    expect(parseGoogleAdsDailyPerformance([{
      segments: { date: "2026-08-14" },
      metrics: { costMicros: "2500000", conversions: "3", clicks: "41" },
    }])).toEqual([{
      date: "2026-08-14",
      costMicros: 2500000n,
      conversions: 3,
      clicks: 41,
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
      getRollingPeriod(NOW, CONFIG_DEFAULTS.reportingTimeZone, 90),
      { fetcher, sleep: noDelay, now: NOW },
    );

    expect(tokenCalls).toBe(1);
    expect(queriedCustomers.sort()).toEqual(["3351363652", "4069972406", "7216252244"]);
    expect(result.googleAdsSpendMtd).toMatchObject({ kind: "ok" });
    expect(result.googleAdsSpendMtd.kind === "ok" ? result.googleAdsSpendMtd.value : null)
      .toBeCloseTo(2362.175313, 6);
    expect(result.googleAdsLeadsMtd).toMatchObject({ kind: "ok", value: 107 });
    expect(result.googleAdsClicksRolling90d).toMatchObject({ kind: "ok", value: 1200 });
    expect(result.googleAdsCostPerLeadRolling90d.kind === "ok"
      ? result.googleAdsCostPerLeadRolling90d.value
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
      getRollingPeriod(NOW, CONFIG_DEFAULTS.reportingTimeZone, 90),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.googleAdsSpendMtd.kind).toBe("error");
    expect(result.googleAdsLeadsMtd.kind).toBe("error");
  });
});

describe("Google Search Console rolling aggregation", () => {
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

  it("uses one OAuth token and queries both configured properties", async () => {
    let tokenCalls = 0;
    const requestedSites: string[] = [];
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
      requestedSites.push(decodeURIComponent(
        pathname.slice(prefix.length, -suffix.length),
      ));
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      expect(body).toMatchObject({
        startDate: "2026-05-17",
        endDate: "2026-08-14",
        aggregationType: "byProperty",
        dataState: "all",
      });
      return jsonResponse({ rows: [{
        clicks: requestedSites.length === 1 ? 11474 : 1200,
        impressions: requestedSites.length === 1 ? 647748 : 88000,
        ctr: 0.02,
        position: 11,
      }] });
    };
    const result = await fetchGoogleSearchConsoleMetrics(
      withSecrets({
        GOOGLE_SEARCH_CONSOLE_CLIENT_ID: "test-client-id",
        GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET: "test-client-secret",
        GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN: "test-refresh-token",
      }),
      getRollingPeriod(NOW, "America/Los_Angeles", 90),
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(tokenCalls).toBe(1);
    expect(result.activeRealtyClicksRolling90d).toMatchObject({ kind: "ok" });
    expect(result.jtClicksRolling90d).toMatchObject({ kind: "ok" });
    expect(allUrls.length).toBe(3);
    expect(requestedSites.sort()).toEqual([
      "https://justintye.com/",
      "sc-domain:activerealty.com",
    ]);
    expect(result.jtImpressionsRolling90d).toMatchObject({ kind: "ok" });
  });

  it("treats a missing aggregate row as no data, never zero", () => {
    expect(() => parseSearchConsoleAggregate({ rows: [] })).toThrow("no_data");
  });
});

describe("Follow Up Boss YTD team aggregation", () => {
  const period = getYearToDatePeriod(NOW, "America/Los_Angeles");
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

  it("normalizes configured closed-stage names and aggregates the requested four totals", () => {
    const stages = closedStageIds(pipelines, ["closed"]);
    expect([...stages]).toEqual([20]);
    expect(aggregateClosedDeals(deals, stages, period)).toEqual({
      commission: 13000,
      sales: 2,
      volume: 1770000,
      activeAgents: 2,
    });
  });

  it("uses the company team split instead of gross commission", () => {
    const stages = closedStageIds(pipelines, ["closed"]);
    const totals = aggregateClosedDeals(deals, stages, period);
    expect(totals.commission).toBe(13000);
    expect(totals.commission).not.toBe(40605);
  });

  it("rejects a closed deal whose company split is missing", () => {
    const stages = closedStageIds(pipelines, ["closed"]);
    const dealWithoutTeamSplit = { ...deals[0], teamCommission: undefined };
    expect(() => aggregateClosedDeals([dealWithoutTeamSplit], stages, period))
      .toThrow();
  });

  it("fetches only sanitized team totals and reuses the five-minute cache", async () => {
    let requests = 0;
    const authorizationHeaders: string[] = [];
    const fetcher = async (
      input: RequestInfo | URL,
      init?: RequestInit,
    ): Promise<Response> => {
      requests += 1;
      const url = new URL(String(input));
      authorizationHeaders.push(new Headers(init?.headers).get("Authorization") ?? "");
      if (url.pathname.endsWith("/me")) {
        return jsonResponse({ id: 1, role: "Broker", isOwner: true });
      }
      return url.pathname.endsWith("/pipelines")
        ? collection("pipelines", pipelines)
        : collection("deals", deals);
    };
    const dashboardEnv = withSecrets({
      FUB_API_KEY: "test-personal-key",
      FUB_TEAM_API_KEY: "test-broker-key",
    });
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
    expect(first.teamCommissionYtd).toMatchObject({ kind: "ok", value: 13000 });
    expect(second.teamVolumeYtd).toMatchObject({ kind: "ok", value: 1770000 });
    expect(requests).toBe(4);
    expect(new Set(authorizationHeaders)).toEqual(
      new Set([`Basic ${btoa("test-broker-key:")}`]),
    );
  });

  it("never treats the personal activity key as account-wide access", async () => {
    const fetcher = async (): Promise<Response> => {
      throw new Error("team source must remain unconfigured");
    };
    const result = await fetchFollowUpBossTeamMetrics(
      withSecrets({ FUB_API_KEY: "test-personal-key" }),
      period,
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.teamSalesYtd).toMatchObject({ kind: "unconfigured" });
  });

  it("rejects a non-broker team key before requesting any deals", async () => {
    const requestedPaths: string[] = [];
    const fetcher = async (input: RequestInfo | URL): Promise<Response> => {
      const url = new URL(String(input));
      requestedPaths.push(url.pathname);
      return jsonResponse({ id: 659, role: "Agent", isOwner: false });
    };
    const result = await fetchFollowUpBossTeamMetrics(
      withSecrets({ FUB_TEAM_API_KEY: "test-agent-key" }),
      period,
      { fetcher, sleep: noDelay, now: NOW },
    );
    expect(result.teamSalesYtd).toMatchObject({
      kind: "error",
      category: "authorization",
    });
    expect(requestedPaths).toEqual(["/v1/me"]);
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

  it("preserves the previous sets value when only that Sheet cell fails", () => {
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

  it("uses error, not zero, when the sets cell fails on the first run", () => {
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

  it("uses the longer team and Search Console freshness policies", () => {
    const snapshot = makeSnapshot(new Date("2026-08-13T12:00:00.000Z"));
    const afterSixteenMinutes = toPublicSnapshot(
      snapshot,
      new Date("2026-08-13T12:16:00.000Z"),
    );
    expect(afterSixteenMinutes.metrics.teamSalesYtd.status).toBe("stale");
    expect(afterSixteenMinutes.metrics.shellPagesRemaining.status).toBe("stale");
    expect(afterSixteenMinutes.metrics.setsRemaining.status).toBe("stale");
    expect(afterSixteenMinutes.metrics.activeRealtyClicksRolling90d.status).toBe("ok");

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
    expect(Object.keys(snapshot.metrics)).toHaveLength(26);
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
    expect(Object.keys(payload.metrics)).toHaveLength(26);
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

  it("uses an exact rolling 90-day inclusive Search Console period", () => {
    expect(getRollingPeriod(NOW, "America/Los_Angeles", 90)).toEqual({
      startDate: "2026-05-17",
      endDate: "2026-08-14",
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
