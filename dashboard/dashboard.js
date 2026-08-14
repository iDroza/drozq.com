(function () {
  "use strict";

  var SUMMARY_URL = "/api/dashboard/summary";
  var POLL_INTERVAL_MS = 60000;
  var REQUEST_TIMEOUT_MS = 10000;
  var STALE_AFTER_MS = 15 * 60 * 1000;
  var metricConfig = {
    sellerLeads: { source: "Follow Up Boss", format: "count" },
    googleAdsSpendMtd: { source: "Google Ads", format: "currency" },
    googleAdsLeadsMtd: { source: "Google Ads", format: "count" },
    shellPagesRemaining: { source: "Google Sheets", format: "count" }
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
  var pollTimer = null;
  var inFlight = false;
  var currentSnapshot = null;

  var grid = document.getElementById("metrics-grid");
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
    if (!isObject(value) || value.version !== 1 || !isObject(value.metrics)) {
      return false;
    }
    return Object.keys(metricConfig).every(function (key) {
      return isMetric(value.metrics[key]);
    }) && isTimestamp(value.lastAttemptAt);
  }

  function formatValue(value, format) {
    if (value === null) {
      return "\u2014";
    }
    return format === "currency"
      ? currencyFormatter.format(value)
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
      (metric.updatedAt !== null && ageInMilliseconds(metric.updatedAt) > STALE_AFTER_MS);

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

  function renderSnapshot(snapshot) {
    currentSnapshot = snapshot;
    Object.keys(metricConfig).forEach(function (key) {
      renderMetric(key, snapshot.metrics[key]);
    });
    grid.classList.remove("is-loading");
    grid.setAttribute("aria-busy", "false");

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
    grid.classList.remove("is-loading");
    grid.setAttribute("aria-busy", "false");
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
