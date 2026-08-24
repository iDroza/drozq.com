import type { DashboardEnv } from "./types";

export const CONFIG_DEFAULTS = Object.freeze({
  fubSellerTag: "Seller",
  fubAccountHost: "activerealty.followupboss.com",
  fubClosedDealStageNames: "Closed",
  fubTeamExcludedUserNames: "Active Agents",
  fubTeamRefreshMinutes: 5,
  googleAdsApiVersion: "v25",
  googleAdsCustomerId: "8004133723",
  googleAdsLeadConversionActionNames: "generate_lead",
  // The JT + AR "Sell | OC" search campaigns share one lander on two domains
  // (justintye.com/sell + activerealty.com/sell) and launched together.
  googleAdsSellerCampaignLaunchDate: "2026-08-17",
  googleSearchConsoleActiveRealtySiteUrl: "sc-domain:activerealty.com",
  googleSearchConsoleJtSiteUrl: "https://justintye.com/",
  googleSearchConsoleRefreshMinutes: 60,
  reportingTimeZone: "America/Los_Angeles",
  googleSheetsPageHeader: "Page",
  googleSheetsStatusHeader: "Status",
  googleSheetsCompleteValues: "complete,completed,done,published,live",
});

export interface FollowUpBossConfig {
  apiKey: string;
  teamApiKey: string;
  accountHost: string;
  sellerTag: string;
  assignedUserId: string;
  system: string;
  systemKey: string;
  closedDealStageNames: string[];
  teamExcludedUserNames: string[];
  teamRefreshMs: number;
}

export interface GoogleAdsConfig {
  developerToken: string;
  clientId: string;
  clientSecret: string;
  refreshToken: string;
  customerId: string;
  loginCustomerId: string;
  apiVersion: string;
  sellerCampaignNames: string[];
  sellerCampaignLaunchDate: string;
}

export interface GoogleSheetsConfig {
  serviceAccountEmail: string;
  serviceAccountPrivateKey: string;
  spreadsheetId: string;
  remainingRange: string;
  setsRemainingRange: string;
  pagesRange: string;
  pageHeader: string;
  statusHeader: string;
  completeValues: string[];
}

export interface GoogleSearchConsoleConfig {
  clientId: string;
  clientSecret: string;
  refreshToken: string;
  activeRealtySiteUrl: string;
  jtSiteUrl: string;
  refreshMs: number;
}

function clean(value: string | undefined): string {
  return value?.trim() ?? "";
}

function boundedMinutes(value: string | undefined, fallback: number): number {
  const cleaned = clean(value);
  if (cleaned === "") {
    return fallback;
  }
  const parsed = Number(cleaned);
  return Number.isSafeInteger(parsed) && parsed >= 1 && parsed <= 24 * 60
    ? parsed
    : fallback;
}

function isoCalendarDate(value: string | undefined, fallback: string): string {
  const cleaned = clean(value);
  if (!/^\d{4}-\d{2}-\d{2}$/u.test(cleaned)) {
    return fallback;
  }
  const parsed = Date.parse(`${cleaned}T12:00:00.000Z`);
  return Number.isFinite(parsed) && new Date(parsed).toISOString().startsWith(cleaned)
    ? cleaned
    : fallback;
}

export function normalizeCustomerId(value: string): string {
  return value.replaceAll("-", "").trim();
}

export function parseCommaSeparated(value: string): string[] {
  const unique = new Map<string, string>();
  for (const item of value.split(",")) {
    const normalized = item.trim();
    if (normalized !== "") {
      unique.set(normalized.toLocaleLowerCase("en-US"), normalized);
    }
  }
  return [...unique.values()];
}

export function readFollowUpBossConfig(env: DashboardEnv): FollowUpBossConfig {
  const requestedAccountHost = clean(env.FUB_ACCOUNT_HOST).toLocaleLowerCase("en-US");
  const accountHost = requestedAccountHost === ""
    ? CONFIG_DEFAULTS.fubAccountHost
    : /^[a-z0-9-]+\.followupboss\.com$/u.test(requestedAccountHost)
      ? requestedAccountHost
      : "";
  return {
    apiKey: clean(env.FUB_API_KEY),
    teamApiKey: clean(env.FUB_TEAM_API_KEY) || clean(env.FUB_API_KEY),
    accountHost,
    sellerTag: clean(env.FUB_SELLER_TAG) || CONFIG_DEFAULTS.fubSellerTag,
    assignedUserId: clean(env.FUB_ASSIGNED_USER_ID),
    system: clean(env.FUB_X_SYSTEM),
    systemKey: clean(env.FUB_X_SYSTEM_KEY),
    closedDealStageNames: parseCommaSeparated(
      clean(env.FUB_CLOSED_DEAL_STAGE_NAMES) ||
        CONFIG_DEFAULTS.fubClosedDealStageNames,
    ),
    teamExcludedUserNames: parseCommaSeparated(
      clean(env.FUB_TEAM_EXCLUDED_USER_NAMES) ||
        CONFIG_DEFAULTS.fubTeamExcludedUserNames,
    ),
    teamRefreshMs:
      boundedMinutes(
        env.FUB_TEAM_REFRESH_MINUTES,
        CONFIG_DEFAULTS.fubTeamRefreshMinutes,
      ) * 60 * 1_000,
  };
}

export function readGoogleSearchConsoleConfig(
  env: DashboardEnv,
): GoogleSearchConsoleConfig {
  return {
    clientId:
      clean(env.GOOGLE_SEARCH_CONSOLE_CLIENT_ID) || clean(env.GOOGLE_ADS_CLIENT_ID),
    clientSecret:
      clean(env.GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET) ||
      clean(env.GOOGLE_ADS_CLIENT_SECRET),
    refreshToken: clean(env.GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN),
    activeRealtySiteUrl:
      clean(env.GOOGLE_SEARCH_CONSOLE_ACTIVE_REALTY_SITE_URL) ||
      CONFIG_DEFAULTS.googleSearchConsoleActiveRealtySiteUrl,
    jtSiteUrl:
      clean(env.GOOGLE_SEARCH_CONSOLE_JT_SITE_URL) ||
      CONFIG_DEFAULTS.googleSearchConsoleJtSiteUrl,
    refreshMs:
      boundedMinutes(
        env.GOOGLE_SEARCH_CONSOLE_REFRESH_MINUTES,
        CONFIG_DEFAULTS.googleSearchConsoleRefreshMinutes,
      ) * 60 * 1_000,
  };
}

export function readGoogleAdsConfig(env: DashboardEnv): GoogleAdsConfig {
  return {
    developerToken: clean(env.GOOGLE_ADS_DEVELOPER_TOKEN),
    clientId: clean(env.GOOGLE_ADS_CLIENT_ID),
    clientSecret: clean(env.GOOGLE_ADS_CLIENT_SECRET),
    refreshToken: clean(env.GOOGLE_ADS_REFRESH_TOKEN),
    customerId: normalizeCustomerId(
      clean(env.GOOGLE_ADS_CUSTOMER_ID) || CONFIG_DEFAULTS.googleAdsCustomerId,
    ),
    loginCustomerId: normalizeCustomerId(clean(env.GOOGLE_ADS_LOGIN_CUSTOMER_ID)),
    apiVersion:
      clean(env.GOOGLE_ADS_API_VERSION) || CONFIG_DEFAULTS.googleAdsApiVersion,
    sellerCampaignNames: parseCommaSeparated(
      clean(env.GOOGLE_ADS_SELLER_CAMPAIGN_NAMES),
    ),
    sellerCampaignLaunchDate: isoCalendarDate(
      env.GOOGLE_ADS_SELLER_CAMPAIGN_LAUNCH_DATE,
      CONFIG_DEFAULTS.googleAdsSellerCampaignLaunchDate,
    ),
  };
}

export function readGoogleSheetsConfig(env: DashboardEnv): GoogleSheetsConfig {
  return {
    serviceAccountEmail: clean(env.GOOGLE_SERVICE_ACCOUNT_EMAIL),
    serviceAccountPrivateKey: clean(env.GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY),
    spreadsheetId: clean(env.GOOGLE_SHEETS_SPREADSHEET_ID),
    remainingRange: clean(env.GOOGLE_SHEETS_REMAINING_RANGE),
    setsRemainingRange: clean(env.GOOGLE_SHEETS_SETS_REMAINING_RANGE),
    pagesRange: clean(env.GOOGLE_SHEETS_PAGES_RANGE),
    pageHeader:
      clean(env.GOOGLE_SHEETS_PAGE_HEADER) || CONFIG_DEFAULTS.googleSheetsPageHeader,
    statusHeader:
      clean(env.GOOGLE_SHEETS_STATUS_HEADER) ||
      CONFIG_DEFAULTS.googleSheetsStatusHeader,
    completeValues: parseCommaSeparated(
      clean(env.GOOGLE_SHEETS_COMPLETE_VALUES) ||
        CONFIG_DEFAULTS.googleSheetsCompleteValues,
    ),
  };
}

export function readReportingTimeZone(env: DashboardEnv): string {
  return clean(env.REPORTING_TIME_ZONE) || CONFIG_DEFAULTS.reportingTimeZone;
}
