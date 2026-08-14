export type MetricStatus = "ok" | "stale" | "error" | "unconfigured";

export type MetricSource =
  | "follow_up_boss"
  | "google_ads"
  | "google_search_console"
  | "google_sheets";

export interface DashboardMetric {
  value: number | null;
  source: MetricSource;
  updatedAt: string | null;
  status: MetricStatus;
  definition: string;
}

export interface DashboardSnapshot {
  version: 2;
  metrics: {
    callsToday: DashboardMetric;
    textsToday: DashboardMetric;
    emailsToday: DashboardMetric;
    appointmentsSetMtd: DashboardMetric;
    freshBuyerLeads: DashboardMetric;
    freshSellerLeads: DashboardMetric;
    googleAdsSpendMtd: DashboardMetric;
    googleAdsLeadsMtd: DashboardMetric;
    googleAdsSpendRolling90d: DashboardMetric;
    googleAdsClicksRolling90d: DashboardMetric;
    googleAdsLeadsRolling90d: DashboardMetric;
    googleAdsCostPerLeadRolling90d: DashboardMetric;
    activeRealtyClicksRolling90d: DashboardMetric;
    activeRealtyImpressionsRolling90d: DashboardMetric;
    activeRealtyCtrRolling90d: DashboardMetric;
    activeRealtyPositionRolling90d: DashboardMetric;
    jtClicksRolling90d: DashboardMetric;
    jtImpressionsRolling90d: DashboardMetric;
    jtCtrRolling90d: DashboardMetric;
    jtPositionRolling90d: DashboardMetric;
    teamCommissionYtd: DashboardMetric;
    teamSalesYtd: DashboardMetric;
    teamVolumeYtd: DashboardMetric;
    teamActiveAgentsYtd: DashboardMetric;
    shellPagesRemaining: DashboardMetric;
    setsRemaining: DashboardMetric;
  };
  reportingPeriod: {
    startDate: string;
    endDate: string;
    timeZone: string;
  };
  rolling90DayPeriod: {
    startDate: string;
    endDate: string;
    timeZone: string;
  };
  yearToDatePeriod: {
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
  | "no_data"
  | "conversion_action_not_found"
  | "storage"
  | "unexpected";

export interface MetricResultMeta {
  durationMs: number;
  responseStatus: number | null;
}

export type MetricFetchResult =
  | ({ kind: "ok"; value: number; observedAt?: string } & MetricResultMeta)
  | ({ kind: "error"; category: ErrorCategory } & MetricResultMeta)
  | ({ kind: "unconfigured" } & MetricResultMeta);

export interface GoogleAdsMetricResults {
  googleAdsSpendMtd: MetricFetchResult;
  googleAdsLeadsMtd: MetricFetchResult;
  googleAdsSpendRolling90d: MetricFetchResult;
  googleAdsClicksRolling90d: MetricFetchResult;
  googleAdsLeadsRolling90d: MetricFetchResult;
  googleAdsCostPerLeadRolling90d: MetricFetchResult;
}

export interface GoogleSearchConsoleMetricResults {
  activeRealtyClicksRolling90d: MetricFetchResult;
  activeRealtyImpressionsRolling90d: MetricFetchResult;
  activeRealtyCtrRolling90d: MetricFetchResult;
  activeRealtyPositionRolling90d: MetricFetchResult;
  jtClicksRolling90d: MetricFetchResult;
  jtImpressionsRolling90d: MetricFetchResult;
  jtCtrRolling90d: MetricFetchResult;
  jtPositionRolling90d: MetricFetchResult;
}

export interface GoogleSheetsMetricResults {
  shellPagesRemaining: MetricFetchResult;
  setsRemaining: MetricFetchResult;
}

export interface FollowUpBossTeamMetricResults {
  teamCommissionYtd: MetricFetchResult;
  teamSalesYtd: MetricFetchResult;
  teamVolumeYtd: MetricFetchResult;
  teamActiveAgentsYtd: MetricFetchResult;
}

export interface FollowUpBossMetricResults {
  callsToday: MetricFetchResult;
  textsToday: MetricFetchResult;
  emailsToday: MetricFetchResult;
  appointmentsSetMtd: MetricFetchResult;
  freshBuyerLeads: MetricFetchResult;
  freshSellerLeads: MetricFetchResult;
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
  FUB_CLOSED_DEAL_STAGE_NAMES?: string;
  FUB_TEAM_REFRESH_MINUTES?: string;
  GOOGLE_ADS_DEVELOPER_TOKEN?: string;
  GOOGLE_ADS_CLIENT_ID?: string;
  GOOGLE_ADS_CLIENT_SECRET?: string;
  GOOGLE_ADS_REFRESH_TOKEN?: string;
  GOOGLE_ADS_CUSTOMER_ID?: string;
  GOOGLE_ADS_LOGIN_CUSTOMER_ID?: string;
  GOOGLE_ADS_LEAD_CONVERSION_ACTION_NAMES?: string;
  GOOGLE_SEARCH_CONSOLE_CLIENT_ID?: string;
  GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET?: string;
  GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN?: string;
  GOOGLE_SEARCH_CONSOLE_ACTIVE_REALTY_SITE_URL?: string;
  GOOGLE_SEARCH_CONSOLE_JT_SITE_URL?: string;
  GOOGLE_SEARCH_CONSOLE_REFRESH_MINUTES?: string;
  GOOGLE_SERVICE_ACCOUNT_EMAIL?: string;
  GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY?: string;
  GOOGLE_SHEETS_SPREADSHEET_ID?: string;
  GOOGLE_SHEETS_REMAINING_RANGE?: string;
  GOOGLE_SHEETS_SETS_REMAINING_RANGE?: string;
  GOOGLE_SHEETS_PAGES_RANGE?: string;
  GOOGLE_SHEETS_PAGE_HEADER?: string;
  GOOGLE_SHEETS_STATUS_HEADER?: string;
  GOOGLE_SHEETS_COMPLETE_VALUES?: string;
}

export type DashboardEnv = Env & SecretBindings;
