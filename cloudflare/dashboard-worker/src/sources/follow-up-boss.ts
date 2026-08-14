import { readFollowUpBossConfig } from "../config";
import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import { requireCount } from "../lib/numeric";
import { fetchWithRetry, UpstreamRequestError } from "../lib/retry";
import type {
  DashboardEnv,
  ErrorCategory,
  MetricFetchResult,
  RuntimeDependencies,
} from "../types";

const FUB_PEOPLE_URL = "https://api.followupboss.com/v1/people";

export function parseFollowUpBossTotal(payload: unknown): number {
  if (!isRecord(payload) || !isRecord(payload["_metadata"])) {
    throw new UpstreamRequestError("schema");
  }
  return requireCount(payload["_metadata"]["total"], "fub_total");
}

function errorResult(
  error: unknown,
  started: number,
  responseStatus: number | null = null,
): MetricFetchResult {
  const category: ErrorCategory =
    error instanceof UpstreamRequestError
      ? error.category
      : error instanceof RangeError
        ? "schema"
        : "unexpected";
  return {
    kind: "error",
    category,
    durationMs: Date.now() - started,
    responseStatus:
      error instanceof UpstreamRequestError
        ? error.responseStatus
        : responseStatus,
  };
}

export async function fetchSellerLeads(
  env: DashboardEnv,
  dependencies: RuntimeDependencies = {},
): Promise<MetricFetchResult> {
  const started = Date.now();
  const config = readFollowUpBossConfig(env);
  if (config.apiKey === "") {
    return {
      kind: "unconfigured",
      durationMs: Date.now() - started,
      responseStatus: null,
    };
  }

  const url = new URL(FUB_PEOPLE_URL);
  url.searchParams.set("tags", config.sellerTag);
  url.searchParams.set("includeTrash", "false");
  url.searchParams.set("limit", "1");
  url.searchParams.set("fields", "id");
  if (config.assignedUserId !== "") {
    url.searchParams.set("assignedUserId", config.assignedUserId);
  }

  const headers = new Headers({
    Authorization: `Basic ${btoa(`${config.apiKey}:`)}`,
    Accept: "application/json",
  });
  if (config.system !== "") {
    headers.set("X-System", config.system);
  }
  if (config.systemKey !== "") {
    headers.set("X-System-Key", config.systemKey);
  }

  try {
    const response = await fetchWithRetry(
      url,
      { method: "GET", headers },
      {
        source: "follow_up_boss",
        fetcher: dependencies.fetcher,
        sleep: dependencies.sleep,
      },
    );
    if (!response.ok) {
      throw classifyHttpStatus(response.status);
    }
    const value = parseFollowUpBossTotal(await readBoundedJson(response));
    return {
      kind: "ok",
      value,
      durationMs: Date.now() - started,
      responseStatus: response.status,
    };
  } catch (error) {
    return errorResult(error, started);
  }
}
