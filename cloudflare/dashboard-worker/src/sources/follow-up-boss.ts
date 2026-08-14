import { readFollowUpBossConfig, type FollowUpBossConfig } from "../config";
import { getActivityWindows, isIsoUtcTimestamp } from "../lib/date";
import { classifyHttpStatus, isRecord, readBoundedJson } from "../lib/http";
import { requireCount } from "../lib/numeric";
import { fetchWithRetry, UpstreamRequestError } from "../lib/retry";
import type {
  DashboardEnv,
  ErrorCategory,
  FollowUpBossMetricResults,
  MetricFetchResult,
  RuntimeDependencies,
} from "../types";

const FUB_BASE_URL = "https://api.followupboss.com/v1";
const FUB_ACTIVITY_STATE_KEY = "dashboard:fub:activity:v2";
const PAGE_LIMIT = 100;
const MAX_PAGES = 100;
const MAX_ACTIVITY_CONTACTS = 250;
const ACTIVITY_OVERLAP_MS = 15 * 60 * 1_000;
const FULL_RECONCILIATION_MS = 60 * 60 * 1_000;
const MAX_SEEN_ACTIVITY_IDS = 100_000;

type ActivityKind = "texts" | "emails";

interface ActivityChannelState {
  count: number;
  checkpointAt: string;
  lastFullScanAt: string;
  seen: string[];
}

interface FollowUpBossActivityState {
  version: 2;
  localDate: string;
  texts: ActivityChannelState;
  emails: ActivityChannelState;
}

interface ActivityUpdate {
  result: MetricFetchResult;
  state: ActivityChannelState | null;
}

interface FreshLeadCounts {
  buyers: number;
  sellers: number;
}

function headersFor(config: FollowUpBossConfig): Headers {
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
  return headers;
}

function responseCollection(
  payload: unknown,
  collectionNames: string[],
): unknown[] {
  if (!isRecord(payload)) {
    throw new UpstreamRequestError("schema");
  }
  for (const name of collectionNames) {
    const collection = payload[name];
    if (Array.isArray(collection)) {
      return collection;
    }
  }
  throw new UpstreamRequestError("schema");
}

async function requestJson(
  url: URL,
  headers: Headers,
  source: string,
  dependencies: RuntimeDependencies,
): Promise<unknown> {
  const response = await fetchWithRetry(
    url,
    { method: "GET", headers },
    {
      source,
      fetcher: dependencies.fetcher,
      sleep: dependencies.sleep,
    },
  );
  if (!response.ok) {
    throw classifyHttpStatus(response.status);
  }
  return readBoundedJson(response);
}

async function listCollection(
  endpoint: string,
  collectionNames: string[],
  parameters: Record<string, string>,
  headers: Headers,
  source: string,
  dependencies: RuntimeDependencies,
): Promise<unknown[]> {
  const rows: unknown[] = [];
  let offset = 0;

  for (let page = 0; page < MAX_PAGES; page += 1) {
    const url = new URL(`${FUB_BASE_URL}/${endpoint}`);
    for (const [name, value] of Object.entries(parameters)) {
      url.searchParams.set(name, value);
    }
    url.searchParams.set("limit", String(PAGE_LIMIT));
    url.searchParams.set("offset", String(offset));

    const payload = await requestJson(url, headers, source, dependencies);
    const pageRows = responseCollection(payload, collectionNames);
    rows.push(...pageRows);

    let total: number | null = null;
    if (isRecord(payload) && isRecord(payload["_metadata"])) {
      const rawTotal = payload["_metadata"]["total"];
      if (rawTotal !== undefined) {
        total = requireCount(rawTotal, "fub_collection_total");
      }
    }
    if (
      pageRows.length === 0 ||
      pageRows.length < PAGE_LIMIT ||
      (total !== null && rows.length >= total)
    ) {
      return rows;
    }
    offset += pageRows.length;
  }

  throw new UpstreamRequestError("schema");
}

export function parseFollowUpBossTotal(payload: unknown): number {
  if (!isRecord(payload) || !isRecord(payload["_metadata"])) {
    throw new UpstreamRequestError("schema");
  }
  return requireCount(payload["_metadata"]["total"], "fub_total");
}

function normalizedId(value: unknown, field: string): string {
  if (
    (typeof value !== "string" && typeof value !== "number") ||
    String(value).trim() === "" ||
    String(value).length > 100
  ) {
    throw new UpstreamRequestError("schema");
  }
  void field;
  return String(value);
}

export function parseFollowUpBossUserId(payload: unknown): string {
  if (!isRecord(payload)) {
    throw new UpstreamRequestError("schema");
  }
  return normalizedId(payload["id"], "fub_user_id");
}

function falseLike(value: unknown): boolean {
  return value === false || value === 0 || value === "0" || value === "false";
}

function belongsToUser(value: unknown, userId: string): boolean {
  return (typeof value === "string" || typeof value === "number") &&
    String(value) === userId;
}

function withinWindow(value: unknown, startAt: string, endAt: string): boolean {
  if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) {
    throw new UpstreamRequestError("schema");
  }
  const timestamp = Date.parse(value);
  return timestamp >= Date.parse(startAt) && timestamp <= Date.parse(endAt);
}

export function countOutboundCalls(
  rows: unknown[],
  userId: string,
  startAt: string,
  endAt: string,
): number {
  let count = 0;
  for (const row of rows) {
    if (!isRecord(row)) {
      throw new UpstreamRequestError("schema");
    }
    if (!withinWindow(row["created"], startAt, endAt)) {
      continue;
    }
    if (belongsToUser(row["userId"], userId) && falseLike(row["isIncoming"])) {
      count += 1;
    }
  }
  return requireCount(count, "fub_calls_today");
}

export function countAppointmentsCreatedByUser(
  rows: unknown[],
  userId: string,
  startAt: string,
  endAt: string,
): number {
  let count = 0;
  for (const row of rows) {
    if (!isRecord(row)) {
      throw new UpstreamRequestError("schema");
    }
    if (!withinWindow(row["created"], startAt, endAt)) {
      continue;
    }
    if (belongsToUser(row["createdById"], userId)) {
      count += 1;
    }
  }
  return requireCount(count, "fub_appointments_set_mtd");
}

function tagNames(value: unknown): string[] {
  if (value === undefined || value === null) {
    return [];
  }
  if (!Array.isArray(value)) {
    throw new UpstreamRequestError("schema");
  }
  return value.map((tag) => {
    if (typeof tag === "string") {
      return tag;
    }
    if (isRecord(tag) && typeof tag["name"] === "string") {
      return tag["name"];
    }
    throw new UpstreamRequestError("schema");
  });
}

export function countFreshLeads(
  rows: unknown[],
  sellerTag: string,
): FreshLeadCounts {
  const normalizedSellerTag = sellerTag.trim().toLocaleLowerCase("en-US");
  let buyers = 0;
  let sellers = 0;
  for (const row of rows) {
    if (!isRecord(row)) {
      throw new UpstreamRequestError("schema");
    }
    normalizedId(row["id"], "fub_person_id");
    const isSeller = tagNames(row["tags"]).some(
      (tag) => tag.trim().toLocaleLowerCase("en-US") === normalizedSellerTag,
    );
    if (isSeller) {
      sellers += 1;
    } else {
      buyers += 1;
    }
  }
  return {
    buyers: requireCount(buyers, "fub_fresh_buyers"),
    sellers: requireCount(sellers, "fub_fresh_sellers"),
  };
}

function isAutomated(row: Record<string, unknown>): boolean {
  const actionPlanId = row["actionPlanId"];
  return actionPlanId !== undefined &&
    actionPlanId !== null &&
    actionPlanId !== 0 &&
    actionPlanId !== "0";
}

export function outboundActivityIds(
  rows: unknown[],
  kind: ActivityKind,
  userId: string,
  startAt: string,
  endAt: string,
): string[] {
  const ids = new Set<string>();
  for (const row of rows) {
    if (!isRecord(row)) {
      throw new UpstreamRequestError("schema");
    }
    if (!withinWindow(row["created"] ?? row["date"], startAt, endAt)) {
      continue;
    }
    if (!belongsToUser(row["userId"], userId) || isAutomated(row)) {
      continue;
    }
    const wasSent = kind === "texts"
      ? falseLike(row["isIncoming"])
      : typeof row["status"] === "string" &&
        row["status"].trim().toLocaleLowerCase("en-US") === "sent";
    if (wasSent) {
      ids.add(normalizedId(row["id"], `fub_${kind}_id`));
    }
  }
  return [...ids];
}

function errorResult(error: unknown, started: number): MetricFetchResult {
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

function unconfiguredResult(started: number): MetricFetchResult {
  return {
    kind: "unconfigured",
    durationMs: Date.now() - started,
    responseStatus: null,
  };
}

function okResult(value: number, started: number): MetricFetchResult {
  return {
    kind: "ok",
    value,
    durationMs: Date.now() - started,
    responseStatus: 200,
  };
}

function errorResults(error: unknown, started: number): FollowUpBossMetricResults {
  return {
    callsToday: errorResult(error, started),
    textsToday: errorResult(error, started),
    emailsToday: errorResult(error, started),
    appointmentsSetMtd: errorResult(error, started),
    freshBuyerLeads: errorResult(error, started),
    freshSellerLeads: errorResult(error, started),
  };
}

function unconfiguredResults(started: number): FollowUpBossMetricResults {
  return {
    callsToday: unconfiguredResult(started),
    textsToday: unconfiguredResult(started),
    emailsToday: unconfiguredResult(started),
    appointmentsSetMtd: unconfiguredResult(started),
    freshBuyerLeads: unconfiguredResult(started),
    freshSellerLeads: unconfiguredResult(started),
  };
}

function blankChannel(dayStartAt: string): ActivityChannelState {
  return {
    count: 0,
    checkpointAt: dayStartAt,
    lastFullScanAt: dayStartAt,
    seen: [],
  };
}

function validChannel(value: unknown): value is ActivityChannelState {
  if (!isRecord(value)) {
    return false;
  }
  const seen = value["seen"];
  return (
    Number.isSafeInteger(value["count"]) &&
    (value["count"] as number) >= 0 &&
    isIsoUtcTimestamp(value["checkpointAt"]) &&
    isIsoUtcTimestamp(value["lastFullScanAt"]) &&
    Array.isArray(seen) &&
    seen.length <= MAX_SEEN_ACTIVITY_IDS &&
    seen.every((item) => typeof item === "string" && /^[a-f0-9]{64}$/u.test(item))
  );
}

function parseActivityState(
  value: unknown,
  localDate: string,
): FollowUpBossActivityState | null {
  if (
    !isRecord(value) ||
    value["version"] !== 2 ||
    value["localDate"] !== localDate ||
    !validChannel(value["texts"]) ||
    !validChannel(value["emails"])
  ) {
    return null;
  }
  return {
    version: 2,
    localDate,
    texts: value["texts"],
    emails: value["emails"],
  };
}

async function loadActivityState(
  env: DashboardEnv,
  localDate: string,
  dayStartAt: string,
): Promise<FollowUpBossActivityState> {
  try {
    const stored = await env.DASHBOARD_KV.get(FUB_ACTIVITY_STATE_KEY);
    if (stored !== null) {
      const parsed = parseActivityState(JSON.parse(stored) as unknown, localDate);
      if (parsed !== null) {
        return parsed;
      }
    }
  } catch {
    console.warn(JSON.stringify({
      source: "follow_up_boss_state",
      category: "storage",
      status: null,
    }));
  }
  return {
    version: 2,
    localDate,
    texts: blankChannel(dayStartAt),
    emails: blankChannel(dayStartAt),
  };
}

async function hashActivityId(kind: ActivityKind, id: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(`${kind}:${id}`),
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function mapWithConcurrency<T, R>(
  items: T[],
  concurrency: number,
  callback: (item: T) => Promise<R>,
): Promise<R[]> {
  const results = new Array<R>(items.length);
  let next = 0;
  async function worker(): Promise<void> {
    while (next < items.length) {
      const index = next;
      next += 1;
      const item = items[index];
      if (item !== undefined) {
        results[index] = await callback(item);
      }
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, items.length) }, () => worker()),
  );
  return results;
}

async function touchedPersonIds(
  kind: ActivityKind,
  cutoffAt: string,
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<string[]> {
  const field = kind === "texts" ? "lastSentText" : "lastSentEmail";
  const ids = new Set<string>();
  let offset = 0;

  for (let page = 0; page < MAX_PAGES; page += 1) {
    const url = new URL(`${FUB_BASE_URL}/people`);
    url.searchParams.set("includeTrash", "false");
    url.searchParams.set("fields", `id,${field}`);
    url.searchParams.set("sortBy", field);
    url.searchParams.set("sortDirection", "desc");
    url.searchParams.set("limit", String(PAGE_LIMIT));
    url.searchParams.set("offset", String(offset));
    const payload = await requestJson(
      url,
      headers,
      `follow_up_boss_${kind}_contacts`,
      dependencies,
    );
    const people = responseCollection(payload, ["people"]);
    let reachedCutoff = false;
    for (const person of people) {
      if (!isRecord(person)) {
        throw new UpstreamRequestError("schema");
      }
      const lastSent = person[field];
      if (lastSent === null || lastSent === undefined || lastSent === "") {
        reachedCutoff = true;
        break;
      }
      if (typeof lastSent !== "string" || !Number.isFinite(Date.parse(lastSent))) {
        throw new UpstreamRequestError("schema");
      }
      if (Date.parse(lastSent) < Date.parse(cutoffAt)) {
        reachedCutoff = true;
        break;
      }
      ids.add(normalizedId(person["id"], "fub_person_id"));
      if (ids.size > MAX_ACTIVITY_CONTACTS) {
        throw new UpstreamRequestError("upstream");
      }
    }
    if (reachedCutoff || people.length < PAGE_LIMIT || people.length === 0) {
      return [...ids];
    }
    offset += people.length;
  }
  throw new UpstreamRequestError("schema");
}

async function fetchPersonActivityIds(
  personId: string,
  kind: ActivityKind,
  userId: string,
  dayStartAt: string,
  endAt: string,
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<string[]> {
  const endpoint = kind === "texts" ? "textMessages" : "emails";
  const fields = kind === "texts"
    ? "id,created,userId,isIncoming,actionPlanId"
    : "id,date,userId,status,actionPlanId";
  const rows = await listCollection(
    endpoint,
    kind === "texts" ? ["textmessages", "textMessages"] : ["emails"],
    {
      personId,
      createdAfter: dayStartAt,
      createdBefore: endAt,
      fields,
    },
    headers,
    `follow_up_boss_${kind}_detail`,
    dependencies,
  );
  return outboundActivityIds(rows, kind, userId, dayStartAt, endAt);
}

async function updateActivity(
  kind: ActivityKind,
  previous: ActivityChannelState,
  userId: string,
  dayStartAt: string,
  endAt: string,
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<ActivityUpdate> {
  const started = Date.now();
  try {
    const nowMs = Date.parse(endAt);
    const shouldReconcile =
      nowMs - Date.parse(previous.lastFullScanAt) >= FULL_RECONCILIATION_MS;
    const incrementalCutoff = new Date(
      Math.max(
        Date.parse(dayStartAt),
        Date.parse(previous.checkpointAt) - ACTIVITY_OVERLAP_MS,
      ),
    ).toISOString();
    const cutoffAt = shouldReconcile ? dayStartAt : incrementalCutoff;
    const personIds = await touchedPersonIds(
      kind,
      cutoffAt,
      headers,
      dependencies,
    );
    const activityIdGroups = await mapWithConcurrency(
      personIds,
      3,
      (personId) => fetchPersonActivityIds(
        personId,
        kind,
        userId,
        dayStartAt,
        endAt,
        headers,
        dependencies,
      ),
    );
    const seen = shouldReconcile ? new Set<string>() : new Set(previous.seen);
    for (const id of activityIdGroups.flat()) {
      seen.add(await hashActivityId(kind, id));
    }
    if (seen.size > MAX_SEEN_ACTIVITY_IDS) {
      throw new UpstreamRequestError("schema");
    }
    const state: ActivityChannelState = {
      count: requireCount(seen.size, `fub_${kind}_today`),
      checkpointAt: endAt,
      lastFullScanAt: shouldReconcile ? endAt : previous.lastFullScanAt,
      seen: [...seen],
    };
    return { result: okResult(state.count, started), state };
  } catch (error) {
    return { result: errorResult(error, started), state: null };
  }
}

async function fetchUserId(
  headers: Headers,
  dependencies: RuntimeDependencies,
): Promise<string> {
  const payload = await requestJson(
    new URL(`${FUB_BASE_URL}/me`),
    headers,
    "follow_up_boss_user",
    dependencies,
  );
  return parseFollowUpBossUserId(payload);
}

async function fetchFreshLeadCounts(
  config: FollowUpBossConfig,
  headers: Headers,
  startAt: string,
  endAt: string,
  dependencies: RuntimeDependencies,
): Promise<FreshLeadCounts> {
  const parameters: Record<string, string> = {
    includeTrash: "false",
    createdAfter: startAt,
    createdBefore: endAt,
    fields: "id,tags",
  };
  if (config.assignedUserId !== "") {
    parameters["assignedUserId"] = config.assignedUserId;
  }
  const rows = await listCollection(
    "people",
    ["people"],
    parameters,
    headers,
    "follow_up_boss_fresh_leads",
    dependencies,
  );
  return countFreshLeads(rows, config.sellerTag);
}

export async function fetchFollowUpBossMetrics(
  env: DashboardEnv,
  timeZone: string,
  dependencies: RuntimeDependencies = {},
): Promise<FollowUpBossMetricResults> {
  const started = Date.now();
  const config = readFollowUpBossConfig(env);
  if (config.apiKey === "") {
    return unconfiguredResults(started);
  }

  const now = dependencies.now ?? new Date();
  const windows = getActivityWindows(now, timeZone);
  const headers = headersFor(config);
  const freshPromise = fetchFreshLeadCounts(
    config,
    headers,
    windows.rollingFourWeeksStartAt,
    windows.endAt,
    dependencies,
  );

  const [userSettled, initialFreshSettled] = await Promise.allSettled([
    fetchUserId(headers, dependencies),
    freshPromise,
  ]);
  if (userSettled.status === "rejected") {
    const result = errorResults(userSettled.reason, started);
    if (initialFreshSettled.status === "fulfilled") {
      result.freshBuyerLeads = okResult(initialFreshSettled.value.buyers, started);
      result.freshSellerLeads = okResult(initialFreshSettled.value.sellers, started);
    } else {
      result.freshBuyerLeads = errorResult(initialFreshSettled.reason, started);
      result.freshSellerLeads = errorResult(initialFreshSettled.reason, started);
    }
    return result;
  }
  const userId = userSettled.value;

  const state = await loadActivityState(
    env,
    windows.localDate,
    windows.dayStartAt,
  );
  const callsPromise = listCollection(
    "calls",
    ["calls"],
    {
      createdAfter: windows.dayStartAt,
      createdBefore: windows.endAt,
      fields: "id,created,userId,isIncoming",
    },
    headers,
    "follow_up_boss_calls",
    dependencies,
  );
  const appointmentsPromise = listCollection(
    "appointments",
    ["appointments"],
    {
      createdAfter: windows.monthStartAt,
      createdBefore: windows.endAt,
      fields: "id,created,createdById",
    },
    headers,
    "follow_up_boss_appointments",
    dependencies,
  );
  const settled = await Promise.allSettled([
    callsPromise,
    appointmentsPromise,
    updateActivity(
      "texts",
      state.texts,
      userId,
      windows.dayStartAt,
      windows.endAt,
      headers,
      dependencies,
    ),
    updateActivity(
      "emails",
      state.emails,
      userId,
      windows.dayStartAt,
      windows.endAt,
      headers,
      dependencies,
    ),
    freshPromise,
  ]);

  const result = errorResults(new UpstreamRequestError("unexpected"), started);
  const calls = settled[0];
  if (calls?.status === "fulfilled") {
    try {
      result.callsToday = okResult(
        countOutboundCalls(
          calls.value,
          userId,
          windows.dayStartAt,
          windows.endAt,
        ),
        started,
      );
    } catch (error) {
      result.callsToday = errorResult(error, started);
    }
  } else {
    result.callsToday = errorResult(calls?.reason, started);
  }

  const appointments = settled[1];
  if (appointments?.status === "fulfilled") {
    try {
      result.appointmentsSetMtd = okResult(
        countAppointmentsCreatedByUser(
          appointments.value,
          userId,
          windows.monthStartAt,
          windows.endAt,
        ),
        started,
      );
    } catch (error) {
      result.appointmentsSetMtd = errorResult(error, started);
    }
  } else {
    result.appointmentsSetMtd = errorResult(appointments?.reason, started);
  }

  const texts = settled[2];
  const emails = settled[3];
  result.textsToday = texts?.status === "fulfilled"
    ? texts.value.result
    : errorResult(texts?.reason, started);
  result.emailsToday = emails?.status === "fulfilled"
    ? emails.value.result
    : errorResult(emails?.reason, started);

  const fresh = settled[4];
  if (fresh?.status === "fulfilled") {
    result.freshBuyerLeads = okResult(fresh.value.buyers, started);
    result.freshSellerLeads = okResult(fresh.value.sellers, started);
  } else {
    result.freshBuyerLeads = errorResult(fresh?.reason, started);
    result.freshSellerLeads = errorResult(fresh?.reason, started);
  }

  const nextTexts = texts?.status === "fulfilled" ? texts.value.state : null;
  const nextEmails = emails?.status === "fulfilled" ? emails.value.state : null;
  if (nextTexts !== null || nextEmails !== null) {
    const nextState: FollowUpBossActivityState = {
      version: 2,
      localDate: windows.localDate,
      texts: nextTexts ?? state.texts,
      emails: nextEmails ?? state.emails,
    };
    try {
      await env.DASHBOARD_KV.put(
        FUB_ACTIVITY_STATE_KEY,
        JSON.stringify(nextState),
      );
    } catch {
      const storageError = {
        kind: "error",
        category: "storage",
        durationMs: Date.now() - started,
        responseStatus: null,
      } as const;
      if (nextTexts !== null) {
        result.textsToday = storageError;
      }
      if (nextEmails !== null) {
        result.emailsToday = storageError;
      }
    }
  }

  return result;
}
