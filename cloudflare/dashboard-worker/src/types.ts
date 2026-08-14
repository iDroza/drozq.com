export type MetricStatus = "ok" | "stale" | "error" | "unconfigured";

export type MetricSource =
  | "follow_up_boss"
  | "google_ads"
  | "google_sheets";

export interface DashboardMetric {
  value: number | null;
  source: MetricSource;
  updatedAt: string | null;
  status: MetricStatus;
  definition: string;
}

export interface DashboardSnapshot {
  version: 1;
  metrics: {
    sellerLeads: DashboardMetric;
    googleAdsSpendMtd: DashboardMetric;
    googleAdsLeadsMtd: DashboardMetric;
    shellPagesRemaining: DashboardMetric;
  };
  reportingPeriod: {
    startDate: string;
    endDate: string;
    timeZone: string;
  };
  lastAttemptAt: string;
  lastSuccessfulFullSyncAt: string | null;
}

export type DashboardMetricKey = keyof DashboardSnapshot["metrics"];

export type ErrorCategory =
  | "authentication"
  | "authorization"
  | "configuration"
  | "rate_limit"
  | "timeout"
  | "network"
  | "upstream"
  | "malformed_json"
  | "schema"
  | "conversion_action_not_found"
  | "storage"
  | "unexpected";

export interface MetricResultMeta {
  durationMs: number;
  responseStatus: number | null;
}

export type MetricFetchResult =
  | ({ kind: "ok"; value: number } & MetricResultMeta)
  | ({ kind: "error"; category: ErrorCategory } & MetricResultMeta)
  | ({ kind: "unconfigured" } & MetricResultMeta);

export interface GoogleAdsMetricResults {
  googleAdsSpendMtd: MetricFetchResult;
  googleAdsLeadsMtd: MetricFetchResult;
}

export interface RuntimeDependencies {
  fetcher?: typeof fetch | undefined;
  now?: Date | undefined;
  sleep?: ((milliseconds: number) => Promise<void>) | undefined;
}

export interface SecretBindings {
  ADMIN_SYNC_TOKEN?: string;
  FUB_API_KEY?: string;
  FUB_X_SYSTEM?: string;
  FUB_X_SYSTEM_KEY?: string;
  FUB_ASSIGNED_USER_ID?: string;
  GOOGLE_ADS_DEVELOPER_TOKEN?: string;
  GOOGLE_ADS_CLIENT_ID?: string;
  GOOGLE_ADS_CLIENT_SECRET?: string;
  GOOGLE_ADS_REFRESH_TOKEN?: string;
  GOOGLE_ADS_CUSTOMER_ID?: string;
  GOOGLE_ADS_LOGIN_CUSTOMER_ID?: string;
  GOOGLE_ADS_LEAD_CONVERSION_ACTION_NAMES?: string;
  GOOGLE_SERVICE_ACCOUNT_EMAIL?: string;
  GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY?: string;
  GOOGLE_SHEETS_SPREADSHEET_ID?: string;
  GOOGLE_SHEETS_REMAINING_RANGE?: string;
  GOOGLE_SHEETS_PAGES_RANGE?: string;
}

export type DashboardEnv = Env & SecretBindings;
