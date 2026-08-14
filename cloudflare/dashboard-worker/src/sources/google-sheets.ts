import { readGoogleSheetsConfig } from "../config";
import { exchangeServiceAccountToken } from "../lib/google-auth";
import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import { requireCount } from "../lib/numeric";
import { fetchWithRetry, UpstreamRequestError } from "../lib/retry";
import type {
  DashboardEnv,
  ErrorCategory,
  MetricFetchResult,
  RuntimeDependencies,
} from "../types";

type SheetCell = string | number | boolean | null;
type SheetRows = SheetCell[][];

function normalizeCell(value: SheetCell | undefined): string {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value).trim().toLocaleLowerCase("en-US");
}

function assertSheetRows(value: unknown): SheetRows {
  if (!Array.isArray(value)) {
    throw new UpstreamRequestError("schema");
  }
  const rows: SheetRows = [];
  for (const row of value) {
    if (!Array.isArray(row)) {
      throw new UpstreamRequestError("schema");
    }
    const cells: SheetCell[] = [];
    for (const cell of row) {
      if (
        typeof cell !== "string" &&
        typeof cell !== "number" &&
        typeof cell !== "boolean" &&
        cell !== null
      ) {
        throw new UpstreamRequestError("schema");
      }
      cells.push(cell);
    }
    rows.push(cells);
  }
  return rows;
}

export function parseDirectCell(rows: unknown): number {
  const parsedRows = assertSheetRows(rows);
  const first = parsedRows[0]?.[0];
  return requireCount(first, "google_sheets_remaining");
}

export function countIncompletePageRows(
  rows: unknown,
  pageHeader: string,
  statusHeader: string,
  completeValues: string[],
): number {
  const parsedRows = assertSheetRows(rows);
  const expectedPage = pageHeader.trim().toLocaleLowerCase("en-US");
  const expectedStatus = statusHeader.trim().toLocaleLowerCase("en-US");
  const completed = new Set(completeValues.map((value) => normalizeCell(value)));

  let headerIndex = -1;
  let pageColumn = -1;
  let statusColumn = -1;
  for (let rowIndex = 0; rowIndex < parsedRows.length; rowIndex += 1) {
    const row = parsedRows[rowIndex] ?? [];
    const normalized = row.map(normalizeCell);
    const candidatePage = normalized.indexOf(expectedPage);
    const candidateStatus = normalized.indexOf(expectedStatus);
    if (candidatePage >= 0 && candidateStatus >= 0) {
      headerIndex = rowIndex;
      pageColumn = candidatePage;
      statusColumn = candidateStatus;
      break;
    }
  }

  if (headerIndex < 0 || pageColumn < 0 || statusColumn < 0) {
    throw new UpstreamRequestError("schema");
  }

  let count = 0;
  for (const row of parsedRows.slice(headerIndex + 1)) {
    if (row.every((cell) => normalizeCell(cell) === "")) {
      continue;
    }
    const page = normalizeCell(row[pageColumn]);
    if (page === "") {
      continue;
    }
    const status = normalizeCell(row[statusColumn]);
    if (!completed.has(status)) {
      count += 1;
    }
  }
  return requireCount(count, "google_sheets_page_count");
}

function parseValuesPayload(payload: unknown): SheetRows {
  if (!isRecord(payload) || payload["values"] === undefined) {
    throw new UpstreamRequestError("schema");
  }
  return assertSheetRows(payload["values"]);
}

function metricError(error: unknown, started: number): MetricFetchResult {
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
      error instanceof UpstreamRequestError ? error.responseStatus : null,
  };
}

export async function fetchShellPagesRemaining(
  env: DashboardEnv,
  dependencies: RuntimeDependencies = {},
): Promise<MetricFetchResult> {
  const started = Date.now();
  const config = readGoogleSheetsConfig(env);
  const range = config.remainingRange || config.pagesRange;
  if (range === "") {
    return {
      kind: "unconfigured",
      durationMs: Date.now() - started,
      responseStatus: null,
    };
  }
  if (
    config.serviceAccountEmail === "" ||
    config.serviceAccountPrivateKey === "" ||
    config.spreadsheetId === ""
  ) {
    return {
      kind: "unconfigured",
      durationMs: Date.now() - started,
      responseStatus: null,
    };
  }

  try {
    const accessToken = await exchangeServiceAccountToken(
      {
        email: config.serviceAccountEmail,
        privateKey: config.serviceAccountPrivateKey,
      },
      dependencies,
    );
    const endpoint = new URL(
      `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(config.spreadsheetId)}/values/${encodeURIComponent(range)}`,
    );
    endpoint.searchParams.set("majorDimension", "ROWS");
    endpoint.searchParams.set("valueRenderOption", "UNFORMATTED_VALUE");
    const response = await fetchWithRetry(
      endpoint,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: "application/json",
        },
      },
      {
        source: "google_sheets",
        fetcher: dependencies.fetcher,
        sleep: dependencies.sleep,
      },
    );
    if (!response.ok) {
      throw classifyHttpStatus(response.status);
    }
    const rows = parseValuesPayload(await readBoundedJson(response));
    const value =
      config.remainingRange !== ""
        ? parseDirectCell(rows)
        : countIncompletePageRows(
            rows,
            config.pageHeader,
            config.statusHeader,
            config.completeValues,
          );
    return {
      kind: "ok",
      value,
      durationMs: Date.now() - started,
      responseStatus: response.status,
    };
  } catch (error) {
    return metricError(error, started);
  }
}
