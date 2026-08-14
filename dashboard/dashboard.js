(function () {
  "use strict";

  var SUMMARY_URL = "/api/dashboard/summary";
  var POLL_INTERVAL_MS = 15000;
  var REQUEST_TIMEOUT_MS = 10000;
  var STALE_AFTER_MS = 5 * 60 * 1000;
  var TEAM_STALE_AFTER_MS = 15 * 60 * 1000;
  var SEARCH_STALE_AFTER_MS = 26 * 60 * 60 * 1000;
  var metricConfig = {
    callsToday: { source: "Follow Up Boss", format: "count" },
    textsToday: { source: "Follow Up Boss", format: "count" },
    emailsToday: { source: "Follow Up Boss", format: "count" },
    appointmentsSetMtd: { source: "Follow Up Boss", format: "count" },
    freshBuyerLeads: { source: "Follow Up Boss", format: "count" },
    freshSellerLeads: { source: "Follow Up Boss", format: "count" },
    googleAdsSpendMtd: { source: "Google Ads", format: "currency" },
    googleAdsLeadsMtd: { source: "Google Ads", format: "conversion" },
    googleAdsSpendRolling90d: { source: "Google Ads", format: "currency" },
    googleAdsClicksRolling90d: { source: "Google Ads", format: "count" },
    googleAdsLeadsRolling90d: { source: "Google Ads", format: "conversion" },
    googleAdsCostPerLeadRolling90d: { source: "Google Ads", format: "currency" },
    activeRealtyClicksRolling90d: { source: "Search Console", format: "count", staleAfterMs: SEARCH_STALE_AFTER_MS },
    activeRealtyImpressionsRolling90d: { source: "Search Console", format: "count", staleAfterMs: SEARCH_STALE_AFTER_MS },
    activeRealtyCtrRolling90d: { source: "Search Console", format: "percent", staleAfterMs: SEARCH_STALE_AFTER_MS },
    activeRealtyPositionRolling90d: { source: "Search Console", format: "decimal", staleAfterMs: SEARCH_STALE_AFTER_MS },
    jtClicksRolling90d: { source: "Search Console", format: "count", staleAfterMs: SEARCH_STALE_AFTER_MS },
    jtImpressionsRolling90d: { source: "Search Console", format: "count", staleAfterMs: SEARCH_STALE_AFTER_MS },
    jtCtrRolling90d: { source: "Search Console", format: "percent", staleAfterMs: SEARCH_STALE_AFTER_MS },
    jtPositionRolling90d: { source: "Search Console", format: "decimal", staleAfterMs: SEARCH_STALE_AFTER_MS },
    teamCommissionYtd: { source: "Follow Up Boss", format: "currencyWhole", staleAfterMs: TEAM_STALE_AFTER_MS },
    teamSalesYtd: { source: "Follow Up Boss", format: "count", staleAfterMs: TEAM_STALE_AFTER_MS },
    teamVolumeYtd: { source: "Follow Up Boss", format: "currencyWhole", staleAfterMs: TEAM_STALE_AFTER_MS },
    teamActiveAgentsYtd: { source: "Follow Up Boss", format: "count", staleAfterMs: TEAM_STALE_AFTER_MS }
  };
  var countFormatter = new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0
  });
  var currencyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
  var conversionFormatter = new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  });
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
  var decimalFormatter = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });
  var pollTimer = null;
  var inFlight = false;
  var currentSnapshot = null;

  var grids = document.querySelectorAll(".metrics-grid");
  var syncStatus = document.getElementById("sync-status");
  var networkError = document.getElementById("network-error");
  var retryButton = document.getElementById("retry-dashboard");

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

  function isSnapshot(value) {
    if (!isObject(value) || value.version !== 2 || !isObject(value.metrics)) {
      return false;
    }
    return Object.keys(metricConfig).every(function (key) {
      return isMetric(value.metrics[key]);
    }) && isTimestamp(value.lastAttemptAt);
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
    if (format === "decimal") {
      return decimalFormatter.format(value);
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
    var badge = card.querySelector("[data-badge]");
    var displayValue = formatValue(metric.value, config.format);
    var stale = metric.status === "stale" ||
      (metric.updatedAt !== null && ageInMilliseconds(metric.updatedAt) > (config.staleAfterMs || STALE_AFTER_MS));

    valueNode.classList.toggle("metric-value--long", displayValue.length >= 11 && displayValue.length < 17);
    valueNode.classList.toggle("metric-value--very-long", displayValue.length >= 17);
    valueNode.textContent = displayValue;
    valueNode.setAttribute("aria-label", displayValue);
    if (metric.value === null) {
      sourceNode.textContent = config.source + " \u00b7 not available";
    } else {
      sourceNode.textContent = config.source + " \u00b7 " + relativeAge(metric.updatedAt);
    }
    badge.hidden = !stale;
  }

  function markGridsReady() {
    grids.forEach(function (grid) {
      grid.classList.remove("is-loading");
      grid.setAttribute("aria-busy", "false");
    });
  }

  function renderSnapshot(snapshot) {
    currentSnapshot = snapshot;
    Object.keys(metricConfig).forEach(function (key) {
      renderMetric(key, snapshot.metrics[key]);
    });
    markGridsReady();

    if (snapshot.lastAttemptAt === "1970-01-01T00:00:00.000Z") {
      syncStatus.textContent = "Synchronization pending";
    } else {
      syncStatus.textContent = "Last synchronized " + relativeAge(snapshot.lastAttemptAt).replace(/^updated /, "");
    }
    networkError.hidden = true;
  }

  function renderUnavailable() {
    Object.keys(metricConfig).forEach(function (key) {
      renderMetric(key, { value: null, updatedAt: null, status: "error" });
    });
    markGridsReady();
    syncStatus.textContent = "Synchronization unavailable";
  }

  function showNetworkError() {
    if (!currentSnapshot) {
      renderUnavailable();
    } else {
      syncStatus.textContent = "Last saved snapshot shown";
    }
    networkError.hidden = false;
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
    var controller = new AbortController();
    var timeout = window.setTimeout(function () {
      controller.abort();
    }, REQUEST_TIMEOUT_MS);

    try {
      var response = await fetch(SUMMARY_URL, {
        method: "GET",
        headers: { "Accept": "application/json" },
        credentials: "same-origin",
        signal: controller.signal
      });
      var payload = await response.json();
      if ((response.ok || response.status === 503) && isSnapshot(payload)) {
        renderSnapshot(payload);
      } else {
        throw new Error("dashboard_unavailable");
      }
    } catch (_error) {
      showNetworkError();
    } finally {
      window.clearTimeout(timeout);
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

  void refreshDashboard();
})();
