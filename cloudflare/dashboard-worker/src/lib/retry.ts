import type { ErrorCategory } from "../types";

const DEFAULT_ATTEMPTS = 3;
const DEFAULT_TIMEOUT_MS = 12_000;
const MAX_RETRY_AFTER_MS = 60_000;

export class UpstreamRequestError extends Error {
  readonly category: ErrorCategory;
  readonly responseStatus: number | null;

  constructor(category: ErrorCategory, responseStatus: number | null = null) {
    super(category);
    this.name = "UpstreamRequestError";
    this.category = category;
    this.responseStatus = responseStatus;
  }
}

export interface RetryOptions {
  source: string;
  fetcher?: typeof fetch | undefined;
  sleep?: ((milliseconds: number) => Promise<void>) | undefined;
  attempts?: number | undefined;
  timeoutMs?: number | undefined;
}

function defaultSleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

function randomFraction(): number {
  const bytes = new Uint32Array(1);
  crypto.getRandomValues(bytes);
  return (bytes[0] ?? 0) / 0xffffffff;
}

export function parseRetryAfter(value: string | null, now = Date.now()): number | null {
  if (value === null || value.trim() === "") {
    return null;
  }

  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds >= 0) {
    return Math.min(seconds * 1_000, MAX_RETRY_AFTER_MS);
  }

  const date = Date.parse(value);
  if (!Number.isFinite(date)) {
    return null;
  }
  return Math.min(Math.max(0, date - now), MAX_RETRY_AFTER_MS);
}

function retryDelay(response: Response | null, attempt: number): number {
  const retryAfter = parseRetryAfter(response?.headers.get("Retry-After") ?? null);
  if (retryAfter !== null) {
    return retryAfter;
  }
  const exponential = 250 * 2 ** Math.max(0, attempt - 1);
  return exponential + Math.floor(randomFraction() * 250);
}

function isRetryableStatus(status: number): boolean {
  return status === 429 || (status >= 500 && status <= 599);
}

function responseCategory(status: number): ErrorCategory | "ok" {
  if (status >= 200 && status <= 299) {
    return "ok";
  }
  if (status === 401) {
    return "authentication";
  }
  if (status === 403) {
    return "authorization";
  }
  if (status === 429) {
    return "rate_limit";
  }
  return "upstream";
}

function logAttempt(
  source: string,
  attempt: number,
  status: number | null,
  durationMs: number,
  category: ErrorCategory | "ok",
): void {
  const payload = { source, attempt, status, durationMs, category };
  const serialized = JSON.stringify(payload);
  if (category === "ok") {
    console.log(serialized);
  } else {
    console.warn(serialized);
  }
}

export async function fetchWithRetry(
  input: RequestInfo | URL,
  init: RequestInit,
  options: RetryOptions,
): Promise<Response> {
  const fetcher = options.fetcher ?? fetch;
  const sleep = options.sleep ?? defaultSleep;
  const attempts = options.attempts ?? DEFAULT_ATTEMPTS;
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const started = Date.now();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort("upstream_timeout"), timeoutMs);

    try {
      const response = await fetcher(input, { ...init, signal: controller.signal });
      const durationMs = Date.now() - started;
      const category = responseCategory(response.status);
      if (!isRetryableStatus(response.status) || attempt === attempts) {
        logAttempt(options.source, attempt, response.status, durationMs, category);
        return response;
      }

      logAttempt(options.source, attempt, response.status, durationMs, category);
      try {
        await response.body?.cancel();
      } catch {
        // The response is already being discarded before the retry.
      }
      await sleep(retryDelay(response, attempt));
    } catch (error) {
      const durationMs = Date.now() - started;
      const timedOut = controller.signal.aborted;
      const category: ErrorCategory = timedOut ? "timeout" : "network";
      logAttempt(options.source, attempt, null, durationMs, category);
      if (attempt === attempts) {
        throw new UpstreamRequestError(category);
      }
      await sleep(retryDelay(null, attempt));
      void error;
    } finally {
      clearTimeout(timeout);
    }
  }

  throw new UpstreamRequestError("unexpected");
}
