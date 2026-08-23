(function () {
  "use strict";

  var SUMMARY_URL = "/api/dashboard/active-summary";
  var BOOTSTRAP_URL = "/api/dashboard/active-bootstrap.js";
  var POLL_INTERVAL_MS = 15000;
  var REQUEST_TIMEOUT_MS = 10000;
  // Realtor MVIP is a flat retainer with no API; its spend and its 115
  // leads/mo program average fold into the aggregate YTD numbers here,
  // client-side, on top of the worker snapshot.
  var MVIP_MONTHLY_SPEND_USD = 15000;
  var MVIP_MONTHLY_LEADS_AVG = 115;
  // Sales attribution: repeat business / referrals = 10%, advertising = 90%.
  var ADVERTISING_SALES_SHARE = 0.9;
  var metricConfig = {
    googleAdsSpendMtd: { source: "Google Ads", format: "currency" },
    googleAdsLeadsMtd: { source: "Google Ads", format: "conversion" },
    googleAdsCostPerClickMtd: { source: "Google Ads", format: "currency" },
    googleAdsCostPerLeadMtd: { source: "Google Ads", format: "currency" },
    googleAdsSpendYtd: { source: "Google Ads + Realtor MVIP", format: "currency" },
    googleAdsLeadsYtd: { source: "Google Ads + Realtor MVIP", format: "conversion" },
    googleAdsCostPerLeadYtd: { source: "Google Ads + Realtor MVIP", format: "currency" },
    teamCommissionRoasYtd: { source: "FUB + ad channels", format: "ratio" },
    // Derived client-side in adjustMetrics (never present in the worker snapshot).
    // CAC = all YTD ad spend (Google Ads + MVIP) / advertising-attributed sales (90%).
    advertisingCacYtd: { source: "FUB + ad channels", format: "currency", derived: true },
    closeRateYtd: { source: "FUB + ad channels", format: "percentFine", derived: true },
    commissionPerSaleYtd: { source: "FUB Deals Leaderboard", format: "currencyWhole", derived: true },
    advertisingNetYtd: { source: "FUB + ad channels", format: "currencyWhole", derived: true },
    activeRealtyClicksRolling90d: { source: "Search Console", format: "count" },
    activeRealtyImpressionsRolling90d: { source: "Search Console", format: "count" },
    activeRealtyCtrRolling90d: { source: "Search Console", format: "percent" },
    activeRealtyPositionRolling90d: { source: "Search Console", format: "decimal" },
    jtClicksRolling90d: { source: "Search Console", format: "count" },
    jtImpressionsRolling90d: { source: "Search Console", format: "count" },
    jtCtrRolling90d: { source: "Search Console", format: "percent" },
    jtPositionRolling90d: { source: "Search Console", format: "decimal" },
    teamCommissionYtd: { source: "FUB Deals Leaderboard", format: "currencyWhole" },
    teamSalesYtd: { source: "FUB Deals Leaderboard", format: "count" },
    teamVolumeYtd: { source: "FUB Deals Leaderboard", format: "currencyWhole" },
    teamActiveAgentsYtd: { source: "FUB Deals Leaderboard", format: "count" },
    shellPagesRemaining: { source: "Active Realty", format: "count" },
    setsRemaining: { source: "Active Realty", format: "count" }
  };
  var metricKeys = Object.keys(metricConfig);
  var snapshotMetricKeys = metricKeys.filter(function (key) { return metricConfig[key].derived !== true; });
  var countFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
  var currencyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
  var conversionFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
  var wholeCurrencyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  });
  var percentFormatter = new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });
  var finePercentFormatter = new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
  var decimalFormatter = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });
  var pollTimer = null;
  var inFlight = false;
  var currentSnapshot = null;
  var bootstrapScript = null;

  var grids = document.querySelectorAll(".metrics-grid");
  var syncStatus = document.getElementById("active-sync-status");
  var networkError = document.getElementById("active-network-error");
  var retryButton = document.getElementById("retry-active");
  var searchConsolePeriod = document.getElementById("active-search-console-period");

  function isObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function isTimestamp(value) {
    return typeof value === "string" && Number.isFinite(Date.parse(value));
  }

  function isMetric(value) {
    return isObject(value) &&
      (value.value === null || (typeof value.value === "number" && Number.isFinite(value.value) && value.value >= 0)) &&
      (value.updatedAt === null || isTimestamp(value.updatedAt)) &&
      ["ok", "stale", "error", "unconfigured"].indexOf(value.status) !== -1;
  }

  function isPeriod(value) {
    return isObject(value) &&
      typeof value.startDate === "string" &&
      /^\d{4}-\d{2}-\d{2}$/.test(value.startDate) &&
      typeof value.endDate === "string" &&
      /^\d{4}-\d{2}-\d{2}$/.test(value.endDate) &&
      value.startDate <= value.endDate;
  }

  function isSnapshot(value) {
    if (!isObject(value) || value.version !== 2 || !isObject(value.metrics)) {
      return false;
    }
    return Object.keys(value.metrics).length === snapshotMetricKeys.length &&
      isPeriod(value.rolling90DayPeriod) &&
      snapshotMetricKeys.every(function (key) { return isMetric(value.metrics[key]); }) &&
      isTimestamp(value.lastAttemptAt);
  }

  function periodDate(value) {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      timeZone: "UTC"
    }).format(new Date(value + "T12:00:00.000Z"));
  }

  function formatValue(value, format) {
    if (value === null) {
      return "\u2013";
    }
    if (format === "currency") {
      return currencyFormatter.format(value);
    }
    if (format === "currencyWhole") {
      return wholeCurrencyFormatter.format(value);
    }
    if (format === "percent") {
      return percentFormatter.format(value);
    }
    if (format === "percentFine") {
      return finePercentFormatter.format(value);
    }
    if (format === "decimal") {
      return decimalFormatter.format(value);
    }
    if (format === "ratio") {
      return decimalFormatter.format(value) + "\u00d7";
    }
    return format === "conversion"
      ? conversionFormatter.format(value)
      : countFormatter.format(value);
  }

  function ageInMilliseconds(timestamp) {
    if (!isTimestamp(timestamp)) {
      return Number.POSITIVE_INFINITY;
    }
    return Math.max(0, Date.now() - Date.parse(timestamp));
  }

  function relativeAge(timestamp) {
    var age = ageInMilliseconds(timestamp);
    if (!Number.isFinite(age)) {
      return "not available";
    }
    var minutes = Math.floor(age / 60000);
    if (minutes < 1) {
      return "updated just now";
    }
    if (minutes < 60) {
      return "updated " + minutes + "m ago";
    }
    var hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return "updated " + hours + "h ago";
    }
    return "updated " + Math.floor(hours / 24) + "d ago";
  }

  function renderMetric(key, metric) {
    var card = document.querySelector('[data-metric="' + key + '"]');
    if (!card) {
      return;
    }
    var config = metricConfig[key];
    var valueNode = card.querySelector("[data-value]");
    var sourceNode = card.querySelector("[data-source]");
    var displayValue = formatValue(metric.value, config.format);
    valueNode.classList.toggle("metric-value--long", displayValue.length >= 11 && displayValue.length < 17);
    valueNode.classList.toggle("metric-value--very-long", displayValue.length >= 17);
    valueNode.textContent = displayValue;
    valueNode.setAttribute("aria-label", displayValue);
    sourceNode.textContent = metric.value === null
      ? config.source + " \u00b7 not available"
      : config.source + " \u00b7 " + relativeAge(metric.updatedAt);
  }

  function markGridsReady() {
    grids.forEach(function (grid) {
      grid.classList.remove("is-loading");
      grid.setAttribute("aria-busy", "false");
    });
  }

  function mvipSpendYtd() {
    return MVIP_MONTHLY_SPEND_USD * (new Date().getMonth() + 1);
  }

  function mvipLeadsYtd() {
    return MVIP_MONTHLY_LEADS_AVG * (new Date().getMonth() + 1);
  }

  function adjustMetrics(metrics) {
    var adjusted = {};
    Object.keys(metrics).forEach(function (key) {
      adjusted[key] = metrics[key];
    });
    var adsSpend = metrics.googleAdsSpendYtd;
    var totalSpend = null;
    if (isMetric(adsSpend) && adsSpend.value !== null) {
      totalSpend = adsSpend.value + mvipSpendYtd();
      adjusted.googleAdsSpendYtd = {
        value: totalSpend,
        updatedAt: adsSpend.updatedAt,
        status: adsSpend.status
      };
    }
    var adsLeads = metrics.googleAdsLeadsYtd;
    var totalLeads = null;
    if (isMetric(adsLeads) && adsLeads.value !== null) {
      totalLeads = adsLeads.value + mvipLeadsYtd();
      adjusted.googleAdsLeadsYtd = {
        value: totalLeads,
        updatedAt: adsLeads.updatedAt,
        status: adsLeads.status
      };
    }
    var costPerLead = metrics.googleAdsCostPerLeadYtd;
    if (isMetric(costPerLead) && totalSpend !== null && totalLeads !== null && totalLeads > 0) {
      adjusted.googleAdsCostPerLeadYtd = {
        value: totalSpend / totalLeads,
        updatedAt: costPerLead.updatedAt || adsLeads.updatedAt,
        status: costPerLead.status
      };
    }
    var commission = metrics.teamCommissionYtd;
    var roas = metrics.teamCommissionRoasYtd;
    if (isMetric(commission) && commission.value !== null && isMetric(roas) && totalSpend !== null && totalSpend > 0) {
      adjusted.teamCommissionRoasYtd = {
        value: (commission.value * ADVERTISING_SALES_SHARE) / totalSpend,
        updatedAt: roas.updatedAt || commission.updatedAt,
        status: roas.status
      };
    }
    // CAC: every YTD advertising dollar / the advertising-attributed share of sales.
    adjusted.advertisingCacYtd = { value: null, updatedAt: null, status: "error" };
    var sales = metrics.teamSalesYtd;
    if (isMetric(sales) && sales.value !== null && sales.value > 0 && totalSpend !== null) {
      adjusted.advertisingCacYtd = {
        value: totalSpend / (sales.value * ADVERTISING_SALES_SHARE),
        updatedAt: sales.updatedAt || adsSpend.updatedAt,
        status: sales.status
      };
    }
    // Close rate: every YTD closed sale / every YTD lead.
    adjusted.closeRateYtd = { value: null, updatedAt: null, status: "error" };
    if (isMetric(sales) && sales.value !== null && totalLeads !== null && totalLeads > 0) {
      adjusted.closeRateYtd = {
        value: sales.value / totalLeads,
        updatedAt: sales.updatedAt || adsLeads.updatedAt,
        status: sales.status
      };
    }
    // Commission per sale: YTD gross commission / YTD closed sales.
    adjusted.commissionPerSaleYtd = { value: null, updatedAt: null, status: "error" };
    if (isMetric(commission) && commission.value !== null && isMetric(sales) && sales.value !== null && sales.value > 0) {
      adjusted.commissionPerSaleYtd = {
        value: commission.value / sales.value,
        updatedAt: commission.updatedAt || sales.updatedAt,
        status: commission.status
      };
    }
    // Net from advertising: attributed commission minus every advertising dollar.
    adjusted.advertisingNetYtd = { value: null, updatedAt: null, status: "error" };
    if (isMetric(commission) && commission.value !== null && totalSpend !== null) {
      adjusted.advertisingNetYtd = {
        value: commission.value * ADVERTISING_SALES_SHARE - totalSpend,
        updatedAt: commission.updatedAt || adsSpend.updatedAt,
        status: commission.status
      };
    }
    return adjusted;
  }

  function renderSnapshot(snapshot) {
    currentSnapshot = snapshot;
    var metrics = adjustMetrics(snapshot.metrics);
    metricKeys.forEach(function (key) {
      renderMetric(key, metrics[key]);
    });
    markGridsReady();
    syncStatus.textContent = snapshot.lastAttemptAt === "1970-01-01T00:00:00.000Z"
      ? "Synchronization pending"
      : "Last synchronized " + relativeAge(snapshot.lastAttemptAt).replace(/^updated /, "");
    searchConsolePeriod.textContent = "Last 3 months \u00b7 " +
      periodDate(snapshot.rolling90DayPeriod.startDate) + " to " +
      periodDate(snapshot.rolling90DayPeriod.endDate);
    networkError.hidden = true;
  }

  function renderUnavailable() {
    metricKeys.forEach(function (key) {
      renderMetric(key, { value: null, updatedAt: null, status: "error" });
    });
    markGridsReady();
    syncStatus.textContent = "Synchronization unavailable";
  }

  function showNetworkError() {
    if (!currentSnapshot) {
      renderUnavailable();
      networkError.hidden = false;
      return;
    }
    syncStatus.textContent = "Last synchronized " +
      relativeAge(currentSnapshot.lastAttemptAt).replace(/^updated /, "");
    networkError.hidden = true;
  }

  function loadBootstrapSnapshot() {
    return new Promise(function (resolve, reject) {
      if (bootstrapScript) {
        bootstrapScript.remove();
      }
      var script = document.createElement("script");
      var timeout = window.setTimeout(function () {
        script.remove();
        if (bootstrapScript === script) {
          bootstrapScript = null;
        }
        reject(new Error("active_bootstrap_timeout"));
      }, REQUEST_TIMEOUT_MS);

      bootstrapScript = script;
      script.async = true;
      script.referrerPolicy = "no-referrer";
      script.src = BOOTSTRAP_URL + "?refresh=" + Date.now();
      script.onload = function () {
        window.clearTimeout(timeout);
        script.remove();
        if (bootstrapScript === script) {
          bootstrapScript = null;
        }
        var payload = window.__ACTIVE_REALTY_DASHBOARD_SNAPSHOT__;
        if (isSnapshot(payload)) {
          resolve(payload);
        } else {
          reject(new Error("active_bootstrap_invalid"));
        }
      };
      script.onerror = function () {
        window.clearTimeout(timeout);
        script.remove();
        if (bootstrapScript === script) {
          bootstrapScript = null;
        }
        reject(new Error("active_bootstrap_unavailable"));
      };
      document.head.appendChild(script);
    });
  }

  async function requestSnapshot() {
    if (typeof window.fetch !== "function" || typeof window.AbortController !== "function") {
      return loadBootstrapSnapshot();
    }
    var controller = new window.AbortController();
    var timeout = window.setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS);
    try {
      var response = await window.fetch(SUMMARY_URL, {
        method: "GET",
        headers: { "Accept": "application/json" },
        credentials: "same-origin",
        signal: controller.signal
      });
      var payload = await response.json();
      if ((response.ok || response.status === 503) && isSnapshot(payload)) {
        return payload;
      }
      throw new Error("active_dashboard_unavailable");
    } finally {
      window.clearTimeout(timeout);
    }
  }

  function clearPollTimer() {
    if (pollTimer !== null) {
      window.clearTimeout(pollTimer);
      pollTimer = null;
    }
  }

  function schedulePoll() {
    clearPollTimer();
    if (document.visibilityState === "visible") {
      pollTimer = window.setTimeout(refreshDashboard, POLL_INTERVAL_MS);
    }
  }

  async function refreshDashboard() {
    if (inFlight || document.visibilityState === "hidden") {
      schedulePoll();
      return;
    }
    inFlight = true;
    retryButton.disabled = true;
    try {
      var payload;
      try {
        payload = await requestSnapshot();
      } catch (_requestError) {
        payload = await loadBootstrapSnapshot();
      }
      renderSnapshot(payload);
    } catch (_error) {
      showNetworkError();
    } finally {
      retryButton.disabled = false;
      inFlight = false;
      schedulePoll();
    }
  }

  retryButton.addEventListener("click", function () {
    clearPollTimer();
    void refreshDashboard();
  });

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") {
      clearPollTimer();
    } else {
      void refreshDashboard();
    }
  });

  if (isSnapshot(window.__ACTIVE_REALTY_DASHBOARD_SNAPSHOT__)) {
    renderSnapshot(window.__ACTIVE_REALTY_DASHBOARD_SNAPSHOT__);
  }
  void refreshDashboard();
})();
