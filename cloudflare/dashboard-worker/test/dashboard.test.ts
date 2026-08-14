import { env } from "cloudflare:workers";
import { describe, expect, it } from "vitest";
import { CONFIG_DEFAULTS } from "../src/config";
import { getReportingPeriod } from "../src/lib/date";
import { fetchWithRetry, parseRetryAfter } from "../src/lib/retry";
import {
  createUnconfiguredSnapshot,
  sanitizeSnapshot,
  toPublicSnapshot,
} from "../src/snapshot";
import { parseFollowUpBossTotal, fetchSellerLeads } from "../src/sources/follow-up-boss";
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
    sellerLeads: successful(41),
    googleAdsSpendMtd: successful(1234.56),
    googleAdsLeadsMtd: successful(12),
    shellPagesRemaining: successful(8),
  };
}

function makeSnapshot(now = new Date("2026-08-14T19:00:00.000Z")): DashboardSnapshot {
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

describe("Follow Up Boss", () => {
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

  it("uses the aggregate people query without retrieving contacts", async () => {
    let requestedUrl = "";
    let authorization = "";
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      requestedUrl = String(input);
      authorization = new Headers(init?.headers).get("Authorization") ?? "";
      return jsonResponse({ _metadata: { total: 19 }, people: [{ id: 1 }] });
    };
    const result = await fetchSellerLeads(
      withSecrets({ FUB_API_KEY: "test-fub-key" }),
      { fetcher, sleep: noDelay },
    );

    const url = new URL(requestedUrl);
    expect(result.kind).toBe("ok");
    expect(result.kind === "ok" ? result.value : null).toBe(19);
    expect(url.searchParams.get("tags")).toBe("Seller");
    expect(url.searchParams.get("includeTrash")).toBe("false");
    expect(url.searchParams.get("limit")).toBe("1");
    expect(url.searchParams.get("fields")).toBe("id");
    expect(authorization.startsWith("Basic ")).toBe(true);
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

describe("Google Ads normalization", () => {
  it("converts cost_micros to USD", () => {
    expect(costMicrosToUsd("123456789")).toBeCloseTo(123.456789, 6);
  });

  it("rejects malformed or negative spend", () => {
    expect(() => costMicrosToUsd("-1")).toThrow();
    expect(() => costMicrosToUsd(Number.POSITIVE_INFINITY)).toThrow();
  });

  it("filters conversions to configured action names", () => {
    const result = sumMatchingLeadConversions(
      [
        { segments: { conversionActionName: "generate_lead" }, metrics: { conversions: 3 } },
        { segments: { conversionActionName: "purchase" }, metrics: { conversions: 99 } },
      ],
      ["generate_lead"],
    );
    expect(result).toEqual({ value: 3, matchedRows: 1 });
  });

  it("matches conversion-action names case-insensitively", () => {
    const result = sumMatchingLeadConversions(
      [
        { segments: { conversionActionName: "Generate_Lead" }, metrics: { conversions: "2" } },
      ],
      ["generate_lead"],
    );
    expect(result.value).toBe(2);
  });

  it("does not count unrelated conversion actions", () => {
    const result = sumMatchingLeadConversions(
      [
        { segments: { conversionActionName: "page_view" }, metrics: { conversions: 8 } },
        { segments: { conversionActionName: "phone_call" }, metrics: { conversions: 4 } },
      ],
      ["generate_lead"],
    );
    expect(result).toEqual({ value: 0, matchedRows: 0 });
  });

  it("reuses one OAuth token while fetching both metrics", async () => {
    let tokenCalls = 0;
    let adsCalls = 0;
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url === "https://oauth2.googleapis.com/token") {
        tokenCalls += 1;
        return jsonResponse({ access_token: "test-access-token-value", expires_in: 3600 });
      }
      adsCalls += 1;
      const body = JSON.parse(String(init?.body)) as { query: string };
      if (body.query.includes("metrics.cost_micros")) {
        return jsonResponse({ results: [{ metrics: { costMicros: "5500000" } }] });
      }
      if (body.query.includes("segments.conversion_action_name")) {
        return jsonResponse({
          results: [
            { segments: { conversionActionName: "generate_lead" }, metrics: { conversions: 2 } },
            { segments: { conversionActionName: "page_view" }, metrics: { conversions: 100 } },
          ],
        });
      }
      return jsonResponse({
        results: [
          { conversionAction: { name: "generate_lead", status: "ENABLED", type: "GOOGLE_ANALYTICS_4_CUSTOM" } },
        ],
      });
    };
    const dashboardEnv = withSecrets({
      GOOGLE_ADS_DEVELOPER_TOKEN: "test-developer-token",
      GOOGLE_ADS_CLIENT_ID: "test-client-id",
      GOOGLE_ADS_CLIENT_SECRET: "test-client-secret",
      GOOGLE_ADS_REFRESH_TOKEN: "test-refresh-token",
    });
    const now = new Date("2026-08-14T19:00:00.000Z");
    const result = await fetchGoogleAdsMetrics(
      dashboardEnv,
      getReportingPeriod(now, CONFIG_DEFAULTS.reportingTimeZone),
      { fetcher, sleep: noDelay },
    );

    expect(tokenCalls).toBe(1);
    expect(adsCalls).toBe(3);
    expect(result.googleAdsSpendMtd.kind === "ok" ? result.googleAdsSpendMtd.value : null).toBe(5.5);
    expect(result.googleAdsLeadsMtd.kind === "ok" ? result.googleAdsLeadsMtd.value : null).toBe(2);
  });
});

describe("Google Sheets normalization", () => {
  it("parses direct-cell mode", () => {
    expect(parseDirectCell([["14"]])).toBe(14);
  });

  it("rejects negative and fractional direct-cell values", () => {
    expect(() => parseDirectCell([[-1]])).toThrow();
    expect(() => parseDirectCell([[1.5]])).toThrow();
  });

  it("counts incomplete rows in table mode", () => {
    const rows = [
      ["Page", "Status"],
      ["About", "complete"],
      ["Sellers", "draft"],
      ["Buyers", ""],
    ];
    expect(
      countIncompletePageRows(rows, "Page", "Status", ["complete", "done"]),
    ).toBe(2);
  });

  it("normalizes complete-status capitalization and whitespace", () => {
    const rows = [
      ["Page", "Status"],
      ["One", " Completed "],
      ["Two", "LIVE"],
      ["Three", "working"],
    ];
    expect(
      countIncompletePageRows(rows, "page", "status", ["completed", "live"]),
    ).toBe(1);
  });

  it("ignores blank rows and rows without a page name", () => {
    const rows = [
      ["Page", "Status"],
      ["", ""],
      [null, null],
      ["", "draft"],
      ["Real page", "draft"],
    ];
    expect(countIncompletePageRows(rows, "Page", "Status", ["done"])).toBe(1);
  });

  it("uses service-account OAuth and a mocked Sheets request", async () => {
    const privateKey = await generateEscapedTestPrivateKey();
    let tokenCalls = 0;
    let sheetsCalls = 0;
    const fetcher = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url === "https://oauth2.googleapis.com/token") {
        tokenCalls += 1;
        expect(String(init?.body)).toContain("assertion=");
        return jsonResponse({ access_token: "test-sheets-access-token", expires_in: 3600 });
      }
      sheetsCalls += 1;
      expect(url).toContain("sheets.googleapis.com/v4/spreadsheets/test-sheet-id/values/");
      expect(new Headers(init?.headers).get("Authorization")).toBe(
        "Bearer test-sheets-access-token",
      );
      return jsonResponse({ values: [["9"]] });
    };
    const result = await fetchShellPagesRemaining(
      withSecrets({
        GOOGLE_SERVICE_ACCOUNT_EMAIL: "dashboard@test-project.iam.gserviceaccount.com",
        GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: privateKey,
        GOOGLE_SHEETS_SPREADSHEET_ID: "test-sheet-id",
        GOOGLE_SHEETS_REMAINING_RANGE: "Dashboard Inputs!B2",
      }),
      { fetcher, sleep: noDelay, now: new Date("2026-08-14T19:00:00.000Z") },
    );

    expect(tokenCalls).toBe(1);
    expect(sheetsCalls).toBe(1);
    expect(result.kind === "ok" ? result.value : null).toBe(9);
  });
});

describe("snapshot merging and public contract", () => {
  it("preserves a previous valid value after a partial failure", () => {
    const previousTime = new Date("2026-08-14T18:00:00.000Z");
    const previous = makeSnapshot(previousTime);
    const now = new Date("2026-08-14T19:00:00.000Z");
    const results = allSuccessfulResults();
    results.sellerLeads = failed();
    results.shellPagesRemaining = successful(7);
    const merged = mergeSnapshot(
      previous,
      results,
      now,
      getReportingPeriod(now, "America/Los_Angeles"),
    );

    expect(merged.metrics.sellerLeads.value).toBe(41);
    expect(merged.metrics.sellerLeads.updatedAt).toBe(previousTime.toISOString());
    expect(merged.metrics.sellerLeads.status).toBe("stale");
    expect(merged.metrics.shellPagesRemaining.value).toBe(7);
    expect(merged.metrics.shellPagesRemaining.status).toBe("ok");
  });

  it("uses error, not zero, for a first-run failure", () => {
    const now = new Date("2026-08-14T19:00:00.000Z");
    const results = allSuccessfulResults();
    results.sellerLeads = failed();
    const merged = mergeSnapshot(
      null,
      results,
      now,
      getReportingPeriod(now, "America/Los_Angeles"),
    );
    expect(merged.metrics.sellerLeads).toMatchObject({
      value: null,
      updatedAt: null,
      status: "error",
    });
  });

  it("marks an ok metric stale after more than 15 minutes", () => {
    const snapshot = makeSnapshot(new Date("2026-08-14T18:00:00.000Z"));
    const publicSnapshot = toPublicSnapshot(
      snapshot,
      new Date("2026-08-14T18:15:00.001Z"),
    );
    expect(publicSnapshot.metrics.sellerLeads.status).toBe("stale");
  });

  it("keeps a metric ok at exactly 15 minutes", () => {
    const snapshot = makeSnapshot(new Date("2026-08-14T18:00:00.000Z"));
    const publicSnapshot = toPublicSnapshot(
      snapshot,
      new Date("2026-08-14T18:15:00.000Z"),
    );
    expect(publicSnapshot.metrics.sellerLeads.status).toBe("ok");
  });

  it("strips every non-allowlisted public field", () => {
    const snapshot = makeSnapshot();
    const tainted = {
      ...snapshot,
      accessToken: "must-not-leak",
      metrics: {
        ...snapshot.metrics,
        sellerLeads: {
          ...snapshot.metrics.sellerLeads,
          contacts: [{ email: "private@example.invalid" }],
          definition: "untrusted definition",
        },
      },
    };
    const sanitized = sanitizeSnapshot(tainted);
    const serialized = JSON.stringify(sanitized);
    expect(sanitized?.metrics.sellerLeads.definition).not.toBe("untrusted definition");
    expect(serialized).not.toContain("must-not-leak");
    expect(serialized).not.toContain("private@example.invalid");
    expect(Object.keys(sanitized ?? {})).toEqual([
      "version",
      "metrics",
      "reportingPeriod",
      "lastAttemptAt",
      "lastSuccessfulFullSyncAt",
    ]);
    expect(Object.keys(sanitized?.metrics.sellerLeads ?? {})).toEqual([
      "value",
      "source",
      "updatedAt",
      "status",
      "definition",
    ]);
  });

  it("rejects absurd or non-finite values from stored snapshots", () => {
    const snapshot = makeSnapshot();
    expect(
      sanitizeSnapshot({
        ...snapshot,
        metrics: {
          ...snapshot.metrics,
          sellerLeads: { ...snapshot.metrics.sellerLeads, value: 1.5 },
        },
      }),
    ).toBeNull();
    expect(
      sanitizeSnapshot({
        ...snapshot,
        metrics: {
          ...snapshot.metrics,
          googleAdsSpendMtd: {
            ...snapshot.metrics.googleAdsSpendMtd,
            value: Number.POSITIVE_INFINITY,
          },
        },
      }),
    ).toBeNull();
  });

  it("represents explicitly unconfigured metrics without false zeros", () => {
    const now = new Date("2026-08-14T19:00:00.000Z");
    const results = allSuccessfulResults();
    results.shellPagesRemaining = unconfigured();
    const merged = mergeSnapshot(
      null,
      results,
      now,
      getReportingPeriod(now, "America/Los_Angeles"),
    );
    expect(merged.metrics.shellPagesRemaining).toMatchObject({
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

  it("creates a valid unconfigured first-run payload", () => {
    const snapshot = createUnconfiguredSnapshot(
      new Date("2026-08-14T19:00:00.000Z"),
      "America/Los_Angeles",
    );
    expect(sanitizeSnapshot(snapshot)).not.toBeNull();
    expect(snapshot.metrics.googleAdsSpendMtd.value).toBeNull();
  });

  it("serves only a cached sanitized summary with hardened headers", async () => {
    const snapshot = makeSnapshot();
    await env.DASHBOARD_KV.put(SNAPSHOT_KEY, JSON.stringify(snapshot));
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/summary"),
      withSecrets({}),
    );
    const payload = (await response.json()) as DashboardSnapshot;

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("application/json");
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(response.headers.get("Cache-Control")).toBe(
      "public, max-age=60, s-maxage=60, stale-while-revalidate=60",
    );
    expect(response.headers.has("Access-Control-Allow-Origin")).toBe(false);
    expect(Object.keys(payload)).toEqual([
      "version",
      "metrics",
      "reportingPeriod",
      "lastAttemptAt",
      "lastSuccessfulFullSyncAt",
    ]);
  });

  it("returns a valid 503 payload when no snapshot exists", async () => {
    await env.DASHBOARD_KV.delete(SNAPSHOT_KEY);
    const response = await handleRequest(
      new Request("https://drozq.com/api/dashboard/summary"),
      withSecrets({}),
    );
    const payload = (await response.json()) as DashboardSnapshot;

    expect(response.status).toBe(503);
    expect(sanitizeSnapshot(payload)).not.toBeNull();
    expect(payload.metrics.sellerLeads.value).toBeNull();
    expect(payload.metrics.sellerLeads.status).toBe("unconfigured");
  });
});

describe("America/Los_Angeles reporting dates", () => {
  it("uses the prior local month before midnight at a UTC month boundary", () => {
    expect(
      getReportingPeriod(
        new Date("2026-01-01T07:30:00.000Z"),
        "America/Los_Angeles",
      ),
    ).toEqual({
      startDate: "2025-12-01",
      endDate: "2025-12-31",
      timeZone: "America/Los_Angeles",
    });
  });

  it("rolls December into January after local midnight", () => {
    expect(
      getReportingPeriod(
        new Date("2026-01-01T08:30:00.000Z"),
        "America/Los_Angeles",
      ),
    ).toEqual({
      startDate: "2026-01-01",
      endDate: "2026-01-01",
      timeZone: "America/Los_Angeles",
    });
  });

  it("handles leap-year February", () => {
    expect(
      getReportingPeriod(
        new Date("2024-03-01T07:59:59.000Z"),
        "America/Los_Angeles",
      ),
    ).toEqual({
      startDate: "2024-02-01",
      endDate: "2024-02-29",
      timeZone: "America/Los_Angeles",
    });
  });
});
