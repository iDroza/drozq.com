import { UpstreamRequestError } from "./retry";

const MAX_JSON_BYTES = 2 * 1024 * 1024;

export async function readBoundedJson(response: Response): Promise<unknown> {
  const declaredLength = Number(response.headers.get("Content-Length"));
  if (Number.isFinite(declaredLength) && declaredLength > MAX_JSON_BYTES) {
    throw new UpstreamRequestError("schema", response.status);
  }

  const body = await response.text();
  if (new TextEncoder().encode(body).byteLength > MAX_JSON_BYTES) {
    throw new UpstreamRequestError("schema", response.status);
  }

  try {
    return JSON.parse(body) as unknown;
  } catch {
    throw new UpstreamRequestError("malformed_json", response.status);
  }
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function classifyHttpStatus(status: number): UpstreamRequestError {
  if (status === 401) {
    return new UpstreamRequestError("authentication", status);
  }
  if (status === 403) {
    return new UpstreamRequestError("authorization", status);
  }
  if (status === 429) {
    return new UpstreamRequestError("rate_limit", status);
  }
  return new UpstreamRequestError("upstream", status);
}
