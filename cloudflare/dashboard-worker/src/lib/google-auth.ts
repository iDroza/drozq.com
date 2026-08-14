import { classifyHttpStatus, isRecord, readBoundedJson } from "./http";
import { fetchWithRetry, UpstreamRequestError } from "./retry";
import type { RuntimeDependencies } from "../types";

const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";
const SHEETS_READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly";

export interface RefreshTokenCredentials {
  clientId: string;
  clientSecret: string;
  refreshToken: string;
}

export interface ServiceAccountCredentials {
  email: string;
  privateKey: string;
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    const chunk = bytes.subarray(offset, offset + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

function base64Url(bytes: Uint8Array): string {
  return bytesToBase64(bytes)
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replace(/=+$/u, "");
}

function base64UrlJson(value: object): string {
  return base64Url(new TextEncoder().encode(JSON.stringify(value)));
}

function pemToBytes(privateKey: string): Uint8Array {
  const normalized = privateKey.replaceAll("\\n", "\n").trim();
  const base64 = normalized
    .replace("-----BEGIN PRIVATE KEY-----", "")
    .replace("-----END PRIVATE KEY-----", "")
    .replace(/\s+/gu, "");

  if (base64 === "" || !/^[A-Za-z0-9+/]+={0,2}$/u.test(base64)) {
    throw new UpstreamRequestError("configuration");
  }

  try {
    const binary = atob(base64);
    return Uint8Array.from(binary, (character) => character.charCodeAt(0));
  } catch {
    throw new UpstreamRequestError("configuration");
  }
}

function parseAccessToken(payload: unknown): string {
  if (!isRecord(payload)) {
    throw new UpstreamRequestError("schema");
  }
  const token = payload["access_token"];
  if (typeof token !== "string" || token.length < 16 || token.length > 8_192) {
    throw new UpstreamRequestError("schema");
  }
  return token;
}

export async function exchangeRefreshToken(
  credentials: RefreshTokenCredentials,
  dependencies: RuntimeDependencies = {},
): Promise<string> {
  const body = new URLSearchParams({
    client_id: credentials.clientId,
    client_secret: credentials.clientSecret,
    refresh_token: credentials.refreshToken,
    grant_type: "refresh_token",
  });
  const response = await fetchWithRetry(
    GOOGLE_TOKEN_URL,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    },
    {
      source: "google_ads_oauth",
      fetcher: dependencies.fetcher,
      sleep: dependencies.sleep,
    },
  );
  if (!response.ok) {
    throw classifyHttpStatus(response.status);
  }
  return parseAccessToken(await readBoundedJson(response));
}

export async function createServiceAccountJwt(
  credentials: ServiceAccountCredentials,
  now: Date,
): Promise<string> {
  const issuedAt = Math.floor(now.getTime() / 1_000);
  if (!Number.isFinite(issuedAt)) {
    throw new UpstreamRequestError("configuration");
  }

  const header = base64UrlJson({ alg: "RS256", typ: "JWT" });
  const claims = base64UrlJson({
    iss: credentials.email,
    scope: SHEETS_READONLY_SCOPE,
    aud: GOOGLE_TOKEN_URL,
    iat: issuedAt,
    exp: issuedAt + 3_600,
  });
  const unsigned = `${header}.${claims}`;
  const key = await crypto.subtle.importKey(
    "pkcs8",
    pemToBytes(credentials.privateKey),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    key,
    new TextEncoder().encode(unsigned),
  );
  return `${unsigned}.${base64Url(new Uint8Array(signature))}`;
}

export async function exchangeServiceAccountToken(
  credentials: ServiceAccountCredentials,
  dependencies: RuntimeDependencies = {},
): Promise<string> {
  const now = dependencies.now ?? new Date();
  const assertion = await createServiceAccountJwt(credentials, now);
  const body = new URLSearchParams({
    grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
    assertion,
  });
  const response = await fetchWithRetry(
    GOOGLE_TOKEN_URL,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    },
    {
      source: "google_sheets_oauth",
      fetcher: dependencies.fetcher,
      sleep: dependencies.sleep,
    },
  );
  if (!response.ok) {
    throw classifyHttpStatus(response.status);
  }
  return parseAccessToken(await readBoundedJson(response));
}
