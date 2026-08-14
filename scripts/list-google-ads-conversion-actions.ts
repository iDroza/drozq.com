import { CONFIG_DEFAULTS, normalizeCustomerId } from "../cloudflare/dashboard-worker/src/config";
import { exchangeRefreshToken } from "../cloudflare/dashboard-worker/src/lib/google-auth";
import { UpstreamRequestError } from "../cloudflare/dashboard-worker/src/lib/retry";
import {
  CONVERSION_ACTION_CATALOG_QUERY,
  discoverGoogleAdsCustomerIds,
  parseConversionActionCatalog,
  queryGoogleAds,
} from "../cloudflare/dashboard-worker/src/sources/google-ads";
import type { GoogleAdsConfig } from "../cloudflare/dashboard-worker/src/config";

function setting(name: string): string {
  return process.env[name]?.trim() ?? "";
}

function required(name: string): string {
  const value = setting(name);
  if (value === "") {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

async function main(): Promise<void> {
  const config: GoogleAdsConfig = {
    developerToken: required("GOOGLE_ADS_DEVELOPER_TOKEN"),
    clientId: required("GOOGLE_ADS_CLIENT_ID"),
    clientSecret: required("GOOGLE_ADS_CLIENT_SECRET"),
    refreshToken: required("GOOGLE_ADS_REFRESH_TOKEN"),
    customerId: normalizeCustomerId(
      setting("GOOGLE_ADS_CUSTOMER_ID") || CONFIG_DEFAULTS.googleAdsCustomerId,
    ),
    loginCustomerId: normalizeCustomerId(setting("GOOGLE_ADS_LOGIN_CUSTOMER_ID")),
    apiVersion:
      setting("GOOGLE_ADS_API_VERSION") || CONFIG_DEFAULTS.googleAdsApiVersion,
  };

  if (!/^\d{10}$/u.test(config.customerId)) {
    throw new Error("GOOGLE_ADS_CUSTOMER_ID must contain exactly 10 digits");
  }
  if (config.loginCustomerId !== "" && !/^\d{10}$/u.test(config.loginCustomerId)) {
    throw new Error("GOOGLE_ADS_LOGIN_CUSTOMER_ID must contain exactly 10 digits");
  }

  const accessToken = await exchangeRefreshToken({
    clientId: config.clientId,
    clientSecret: config.clientSecret,
    refreshToken: config.refreshToken,
  });
  const customerIds = await discoverGoogleAdsCustomerIds(accessToken, config);
  console.log(`Available Google Ads conversion actions across ${customerIds.length} account(s):`);
  for (const customerId of customerIds) {
    const rows = await queryGoogleAds(
      accessToken,
      config,
      customerId,
      CONVERSION_ACTION_CATALOG_QUERY,
      "google_ads_actions_diagnostic",
    );
    const actions = parseConversionActionCatalog(rows).sort((left, right) =>
      left.name.localeCompare(right.name, "en-US", { sensitivity: "base" }),
    );
    console.log(`Customer ${customerId}:`);
    if (actions.length === 0) {
      console.log("  No non-removed conversion actions were returned.");
      continue;
    }
    for (const action of actions) {
      console.log(`  ${action.name}\t${action.status}\t${action.type}`);
    }
  }
}

main().catch((error: unknown) => {
  const category =
    error instanceof UpstreamRequestError ? error.category : "configuration_or_request";
  console.error(`Unable to list conversion actions (${category}).`);
  process.exitCode = 1;
});
