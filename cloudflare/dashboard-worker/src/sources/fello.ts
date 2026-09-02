// Fello engagement metrics, read through the site's own admin endpoint
// (GET https://drozq.com/api/fello/engagement, Bearer DROZQ_EMAIL_SECRET).
// That endpoint sweeps the newest drozq leads through Fello's contact read
// and caches the ranked result for eight minutes, so this Worker never talks
// to Fello directly and never learns the Fello API key.
//
// Three numbers surface on the dashboard (names, never; the dashboard is
// public): hot leads inside the seven-day window, leads Fello knows at all,
// and their average Fello lead score.

import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import { requireCount, requireNonnegativeNumber } from "../lib/numeric";
import { fetchWithRetry, UpstreamRequestError } from "../lib/retry";
import type {
  DashboardEnv,
  FelloMetricResults,
  MetricFetchResult,
  RuntimeDependencies,
} from "../types";

export const FELLO_ENGAGEMENT_URL = "https://drozq.com/api/fello/engagement?days=90&limit=100";
const FELLO_TIMEOUT_MS = 40_000;

export interface FelloEngagementSummary {
  hot: number;
  matched: number;
  avgLeadScore: number | null;
}

export function parseFelloEngagement(payload: unknown): FelloEngagementSummary {
  if (!isRecord(payload) || payload["ok"] !== true || !isRecord(payload["summary"])) {
    throw new UpstreamRequestError("schema");
  }
  const summary = payload["summary"];
  const hot = requireCount(summary["hot"], "fello_hot");
  const matched = requireCount(summary["matched"], "fello_matched");
  const rawScore = summary["avgLeadScore"];
  let avgLeadScore: number | null = null;
  if (rawScore !== null && rawScore !== undefined) {
    avgLeadScore = requireNonnegativeNumber(rawScore, "fello_avg_lead_score");
    if (avgLeadScore > 100) {
      throw new UpstreamRequestError("schema");
    }
  }
  if (hot > matched) {
    throw new UpstreamRequestError("schema");
  }
  return { hot, matched, avgLeadScore };
}

function unconfigured(started: number): MetricFetchResult {
  return { kind: "unconfigured", durationMs: Date.now() - started, responseStatus: null };
}

function errorResult(error: unknown, started: number): MetricFetchResult {
  const durationMs = Date.now() - started;
  if (error instanceof UpstreamRequestError) {
    return { kind: "error", category: error.category, durationMs, responseStatus: error.responseStatus };
  }
  if (error instanceof RangeError) {
    return { kind: "error", category: "schema", durationMs, responseStatus: 200 };
  }
  return { kind: "error", category: "unexpected", durationMs, responseStatus: null };
}

export async function fetchFelloMetrics(
  env: DashboardEnv,
  dependencies: RuntimeDependencies = {},
): Promise<FelloMetricResults> {
  const started = Date.now();
  const secret = env.DROZQ_EMAIL_SECRET?.trim() ?? "";
  if (secret === "") {
    return {
      felloHotLeads7d: unconfigured(started),
      felloLeadsScored: unconfigured(started),
      felloAvgLeadScore: unconfigured(started),
    };
  }
  try {
    const response = await fetchWithRetry(
      FELLO_ENGAGEMENT_URL,
      { method: "GET", headers: { Authorization: `Bearer ${secret}`, Accept: "application/json" } },
      { source: "fello_engagement", fetcher: dependencies.fetcher, sleep: dependencies.sleep, timeoutMs: FELLO_TIMEOUT_MS },
    );
    if (!response.ok) {
      throw classifyHttpStatus(response.status);
    }
    const summary = parseFelloEngagement(await readBoundedJson(response));
    const durationMs = Date.now() - started;
    const ok = (value: number): MetricFetchResult => ({ kind: "ok", value, durationMs, responseStatus: 200 });
    return {
      felloHotLeads7d: ok(summary.hot),
      felloLeadsScored: ok(summary.matched),
      felloAvgLeadScore: summary.avgLeadScore === null
        ? { kind: "error", category: "no_data", durationMs, responseStatus: 200 }
        : ok(summary.avgLeadScore),
    };
  } catch (error) {
    const result = errorResult(error, started);
    return { felloHotLeads7d: result, felloLeadsScored: result, felloAvgLeadScore: result };
  }
}
