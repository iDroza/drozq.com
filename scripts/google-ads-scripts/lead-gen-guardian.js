/**
 * ============================================================================
 *  DROZQ LEAD-GEN GUARDIAN  —  Google Ads Script (runs INSIDE Google Ads)
 * ============================================================================
 *  One scheduled script that automates the three things that actually move
 *  real-estate lead cost and protect the conversion signal on the drozq.com
 *  Sellers campaign. It runs on Google's servers on a daily schedule and emails
 *  you a single digest. It is the always-on automation layer; scripts/ads.py is
 *  the on-demand read-only reporting layer. They complement each other.
 *
 *  WHAT IT DOES
 *  ------------
 *   1. NEGATIVE-KEYWORD MINER (the centerpiece). Scans the search-terms report
 *      and classifies each term against a real-estate junk dictionary: jobs /
 *      license, FSBO + DIY, iBuyers + cash, rentals, research tools, out-of-state
 *      geo, competitor + brokerage brands, and the distressed carve-out (saved
 *      for the painpoint campaign). It recommends negatives and — only when you
 *      flip AUTO_APPLY_NEGATIVES to true — adds the high-confidence ones to your
 *      existing "Negatives | Sellers Funnel" shared list. This automates the
 *      daily ritual in sellers-max-intent-campaign.md §11.
 *
 *   2. WASTED-SPEND WATCH. Flags terms that burned >= $X with zero conversions,
 *      and any single search term whose average CPC breached your expensive-click
 *      line (the $210 "most accurate home value estimator" click, the $146
 *      "what is my home worth", the $85 "flat fee realtor").
 *
 *   3. FUNNEL + ACCOUNT GUARDIAN. Confirms every landing page returns 200 AND
 *      still contains the funnel markup (the silent-funnel-break alarm), that no
 *      ENABLED ad is DISAPPROVED, and that conversions have not flatlined. Plus:
 *      surfaces converting search terms you have NOT yet promoted to keywords.
 *
 *  SAFETY: dry-run by default. With AUTO_APPLY_NEGATIVES = false it changes
 *  NOTHING in the account; it only reads and emails. Every module is wrapped so
 *  one API hiccup can't kill the digest. Auto-applied negatives are capped per
 *  run and always itemized in the email.
 *
 *  INSTALL
 *  -------
 *   Google Ads -> Tools & Settings -> Bulk actions -> Scripts -> ( + ) New script
 *   Paste this file. Click "Authorize". Click "Preview" (safe; no writes on a
 *   dry-run). Read the digest in the logs. Then "Schedule" -> Daily, early AM.
 *
 *  Companion docs (in this repo):
 *   notes/ads/sellers-max-intent-campaign.md  — §5 negative list, §11 Phase plan
 *   notes/ads/bidding-decisions.md            — the $15 cap + terms NOT to negate
 *   notes/mcp-workarounds.md                  — scripts/ads.py (the API sibling)
 * ============================================================================
 */

var CONFIG = {
  // --- Reporting / email -----------------------------------------------------
  EMAIL_TO: 'guerrerojoshua720@gmail.com', // comma-separate for multiple recipients
  EMAIL_ALWAYS: false,                     // true = email even on a clean run
  ACCOUNT_LABEL: 'Drozq Sellers',          // shown in the email subject

  // --- Scan windows (GAQL date constants) ------------------------------------
  LOOKBACK: 'LAST_30_DAYS',                // search-terms scan window
  CONVERSION_LOOKBACK: 'LAST_7_DAYS',      // window for the flatline alarm

  // --- 1) Negative-keyword miner ---------------------------------------------
  NEG_LIST_NAME: 'Negatives | Sellers Funnel', // existing shared list to write into
  AUTO_APPLY_NEGATIVES: false,             // SAFE DEFAULT. true = actually add negatives.
  MAX_AUTO_NEGATIVES_PER_RUN: 25,          // hard cap on auto-added negatives per run
  MIN_SPEND_TO_FLAG: 0.01,                 // ignore impression-only ($0) terms

  // --- 2) Wasted-spend watch -------------------------------------------------
  ZERO_CONV_SPEND_ALERT: 50,               // term spent >= $X with 0 conv -> review
  EXPENSIVE_CLICK_ALERT: 40,               // term avg CPC >= $X -> alarm

  // --- 3a) Winners -----------------------------------------------------------
  PROMOTE_MIN_CONVERSIONS: 1,              // converting non-keyword term -> promote rec

  // --- 3b) Funnel + account guardian -----------------------------------------
  CHECK_LANDING_PAGES: true,
  LANDING_PAGES: ['https://drozq.com/'],   // health-checked for 200 + markers below
  REQUIRED_PAGE_MARKERS: ['funnel-overlay'], // substrings that MUST be present
  CHECK_DISAPPROVED_ADS: true,
  CHECK_ZERO_CONVERSIONS: true,
  MIN_CLICKS_FOR_FLATLINE_ALARM: 20,       // only alarm on 0 conv if >= N clicks happened

  // --- Optional audit log ----------------------------------------------------
  SHEET_URL: ''                            // '' = off. Paste a Sheet URL to log each run.
};

/**
 * Real-estate junk dictionary. Each match in a term classifies it.
 * confidence 'high' = eligible for AUTO_APPLY as a phrase negative.
 * confidence 'med'  = recommend only, NEVER auto-applied (overlap risk).
 *
 * Short / ambiguous tokens are space-padded (' kw ', ' rent ') so they match on
 * a word boundary instead of as a substring. Multi-word tokens match as-is.
 *
 * DELIBERATELY ABSENT: 'estimator' / 'calculator' / 'home value estimator'.
 * Per notes/ads/bidding-decisions.md the lone early conversion came from that
 * family, so the $15 CPC cap (not a negative) is the right tool there. Those
 * terms only ever surface via the zero-conversion review list, never negation.
 */
var JUNK = {
  JOBS_CAREER: { confidence: 'high', label: 'Jobs / license / career', tokens: [
    ' job ', ' jobs ', 'hiring', 'salary', 'career', 'how to become', 'license',
    'real estate exam', 'real estate school', 'real estate class', 'real estate course',
    'continuing education', 'commission split', 'recruiting', 'sponsor my license'
  ]},
  DISTRESSED: { confidence: 'high', label: 'Distressed (carved out for painpoint campaign)', tokens: [
    'foreclosure', 'pre foreclosure', 'preforeclosure', 'short sale', 'probate',
    'inherited', 'inheritance', 'divorce', 'behind on mortgage', 'stop foreclosure',
    'avoid foreclosure', 'distressed', 'bankruptcy', 'loan modification', 'lien'
  ]},
  DIY_FSBO: { confidence: 'high', label: 'FSBO / DIY / discount', tokens: [
    'fsbo', 'for sale by owner', 'sell by owner', 'without agent', 'without realtor',
    'without a realtor', 'by myself', 'sell my house myself', 'flat fee', 'flat-fee',
    'do i need a realtor', 'discount broker', 'discount realtor', '1 percent', 'one percent',
    '2 percent', '1% commission', 'mls only', 'list on mls myself'
  ]},
  IBUYER_CASH: { confidence: 'high', label: 'iBuyer / cash buyer', tokens: [
    'ibuyer', 'opendoor', 'offerpad', 'we buy houses', 'cash offer', 'cash for my house',
    'cash for house', 'sell to investor', 'sell to an investor', 'instant offer',
    'quick cash', 'sell house fast cash', 'cash home buyer'
  ]},
  RENTALS: { confidence: 'high', label: 'Rentals / wrong product', tokens: [
    'for rent', ' rent ', 'rental', 'rent out', ' lease ', 'apartment', 'apartments',
    'landlord', 'section 8', 'property management', 'tenant', 'how to rent'
  ]},
  OUT_OF_STATE: { confidence: 'high', label: 'Out-of-state geo', tokens: [
    'texas', 'florida', 'new york', 'chicago', 'ohio', 'columbus', 'arizona', 'phoenix',
    'nevada', 'las vegas', 'washington', 'oregon', 'georgia', 'atlanta', 'colorado',
    'denver', 'seattle', 'dallas', 'houston', 'austin', 'miami', 'tampa', 'san antonio'
  ]},
  COMPETITOR_PLATFORMS: { confidence: 'high', label: 'Competitor lead platform', tokens: [
    'upnest', 'homelight', 'ideal agent', 'clever real estate', 'rocket homes',
    'listingspark', 'fastexpert', 'fast expert', 'effective agents', 'referralexchange'
  ]},
  BROKERAGE_BRANDS: { confidence: 'high', label: 'Other brokerage brand', tokens: [
    'keller williams', ' kw ', 'john l scott', 'first team', 'realty one', 'exp realty',
    'serhant', 'coldwell', 'century 21', 're/max', 'remax', 'compass real estate',
    'sotheby', 'berkshire hathaway', 'douglas elliman'
  ]},
  RESEARCH_TOOLS: { confidence: 'high', label: 'Research tool / AVM brand', tokens: [
    'zillow', 'zestimate', 'redfin', 'trulia', 'realtor.com', 'realtor com', 'ownerly',
    'quantarium', 'housecanary', 'corelogic', 'realavm', 'eppraisal', 'kelley blue book',
    ' kbb '
    // NOTE: 'estimator' / 'calculator' intentionally excluded — see header.
  ]},
  BUYERS: { confidence: 'med', label: 'Buyer intent (own campaign)', tokens: [
    'homes for sale', 'houses for sale', 'buy a home', 'buy a house', 'first time home buyer',
    'first time buyer', 'buyers agent', 'buyer agent', 'open houses near me', 'down payment assistance'
  ]},
  MORTGAGE_FINANCE: { confidence: 'med', label: 'Mortgage / finance', tokens: [
    'rocket mortgage', 'freedom mortgage', 'refinance', 'mortgage rate', 'mortgage calculator',
    'heloc', 'loan officer', 'interest rate', 'pre approval', 'preapproval'
  ]},
  GENERIC_INFO: { confidence: 'med', label: 'Low-intent research', tokens: [
    'what is a', 'how does', 'meaning of', 'definition', 'wikipedia', 'reddit', ' vs '
  ]}
};

// ============================================================================
//  ENTRY POINT
// ============================================================================
function main() {
  var ctx = {
    started: new Date(),
    errors: [],
    negFindings: {},     // token -> { category, label, confidence, spend, conv, terms[] }
    negReviewOnly: {},   // medium-confidence token -> same shape
    autoAdded: [],       // tokens actually added this run
    zeroConvTerms: [],   // {term, spend, clicks, campaign}
    expensiveTerms: [],  // {term, cpc, clicks, spend, campaign}
    winners: [],         // {term, conv, spend, campaign, adGroup}
    pageIssues: [],      // {url, reason}
    disapproved: [],     // {campaign, adGroup, adId}
    flatline: null,      // {clicks, spend} or null
    scanned: 0
  };

  guard(ctx, 'search-terms scan', function () { scanSearchTerms(ctx); });
  guard(ctx, 'apply negatives',  function () { applyNegatives(ctx); });
  guard(ctx, 'landing pages',    function () { if (CONFIG.CHECK_LANDING_PAGES) checkLandingPages(ctx); });
  guard(ctx, 'disapproved ads',  function () { if (CONFIG.CHECK_DISAPPROVED_ADS) checkDisapprovedAds(ctx); });
  guard(ctx, 'flatline alarm',   function () { if (CONFIG.CHECK_ZERO_CONVERSIONS) checkFlatline(ctx); });
  guard(ctx, 'audit log',        function () { logToSheet(ctx); });

  sendDigest(ctx);
}

// ----------------------------------------------------------------------------
//  1) SEARCH-TERM SCAN: classify, collect, recommend
// ----------------------------------------------------------------------------
function scanSearchTerms(ctx) {
  var activeKeywords = getActiveKeywordTexts();

  var query =
    'SELECT search_term_view.search_term, search_term_view.status, ' +
    'campaign.name, ad_group.name, ' +
    'metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.impressions ' +
    'FROM search_term_view ' +
    'WHERE segments.date DURING ' + CONFIG.LOOKBACK + ' ' +
    "AND campaign.status = 'ENABLED' " +
    'ORDER BY metrics.cost_micros DESC';

  var rows = AdsApp.report(query).rows();
  while (rows.hasNext()) {
    var row = rows.next();
    var term = String(row['search_term_view.search_term'] || '').toLowerCase().trim();
    if (!term) continue;

    var status = String(row['search_term_view.status'] || '');
    // Skip terms already excluded as negatives — no point re-flagging them.
    if (status === 'EXCLUDED' || status === 'ADDED_EXCLUDED') continue;

    var spend = micros(row['metrics.cost_micros']);
    var clicks = parseFloat(row['metrics.clicks'] || 0);
    var conv = parseFloat(row['metrics.conversions'] || 0);
    if (spend < CONFIG.MIN_SPEND_TO_FLAG) continue;
    ctx.scanned++;

    var campaign = String(row['campaign.name'] || '');
    var adGroup = String(row['ad_group.name'] || '');

    // Expensive single-click alarm (independent of relevance).
    var cpc = clicks > 0 ? spend / clicks : 0;
    if (cpc >= CONFIG.EXPENSIVE_CLICK_ALERT) {
      ctx.expensiveTerms.push({ term: term, cpc: cpc, clicks: clicks, spend: spend, campaign: campaign });
    }

    // Winner: it converted and isn't an active keyword yet -> promote it.
    if (conv >= CONFIG.PROMOTE_MIN_CONVERSIONS && !activeKeywords[term]) {
      ctx.winners.push({ term: term, conv: conv, spend: spend, campaign: campaign, adGroup: adGroup });
    }

    // Never recommend negating one of our own active keywords.
    if (activeKeywords[term]) continue;

    var hit = classify(term);
    if (hit) {
      var bucket = (hit.confidence === 'high') ? ctx.negFindings : ctx.negReviewOnly;
      var rec = bucket[hit.token] || (bucket[hit.token] = {
        category: hit.category, label: hit.label, confidence: hit.confidence,
        spend: 0, conv: 0, terms: []
      });
      rec.spend += spend; rec.conv += conv;
      if (rec.terms.length < 8) rec.terms.push(term); // keep the email readable
    } else if (conv === 0 && spend >= CONFIG.ZERO_CONV_SPEND_ALERT) {
      // Not obvious junk, but it ate budget and never converted -> human review.
      ctx.zeroConvTerms.push({ term: term, spend: spend, clicks: clicks, campaign: campaign });
    }
  }
}

/** Returns {category, label, confidence, token} for the first junk match, else null. */
function classify(term) {
  var padded = ' ' + term + ' ';
  for (var cat in JUNK) {
    var def = JUNK[cat];
    for (var i = 0; i < def.tokens.length; i++) {
      if (padded.indexOf(def.tokens[i]) !== -1) {
        return { category: cat, label: def.label, confidence: def.confidence, token: def.tokens[i].trim() };
      }
    }
  }
  return null;
}

// ----------------------------------------------------------------------------
//  2) APPLY NEGATIVES (only when AUTO_APPLY_NEGATIVES = true)
// ----------------------------------------------------------------------------
function applyNegatives(ctx) {
  if (!CONFIG.AUTO_APPLY_NEGATIVES) return;

  var list = getNegativeList(CONFIG.NEG_LIST_NAME);
  if (!list) {
    ctx.errors.push('Negative list "' + CONFIG.NEG_LIST_NAME + '" not found — nothing auto-applied. ' +
                    'Create it in Shared Library or fix NEG_LIST_NAME.');
    return;
  }

  var existing = existingNegativeTokens(list);

  // Highest-spend tokens first, up to the per-run cap.
  var tokens = Object.keys(ctx.negFindings).sort(function (a, b) {
    return ctx.negFindings[b].spend - ctx.negFindings[a].spend;
  });

  var toAdd = [];
  for (var i = 0; i < tokens.length && toAdd.length < CONFIG.MAX_AUTO_NEGATIVES_PER_RUN; i++) {
    var token = tokens[i];
    if (existing[token]) continue;             // already on the list
    toAdd.push('"' + token + '"');             // phrase-match negative (kills variants)
    ctx.autoAdded.push(token);
  }

  if (toAdd.length) list.addNegativeKeywords(toAdd);
}

// ----------------------------------------------------------------------------
//  3a) FUNNEL HEALTH: 200 + required markup present
// ----------------------------------------------------------------------------
function checkLandingPages(ctx) {
  for (var i = 0; i < CONFIG.LANDING_PAGES.length; i++) {
    var url = CONFIG.LANDING_PAGES[i];
    var resp;
    try {
      resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: true });
    } catch (e) {
      ctx.pageIssues.push({ url: url, reason: 'fetch failed: ' + e });
      continue;
    }
    var code = resp.getResponseCode();
    if (code !== 200) {
      ctx.pageIssues.push({ url: url, reason: 'HTTP ' + code });
      continue;
    }
    var body = resp.getContentText() || '';
    for (var m = 0; m < CONFIG.REQUIRED_PAGE_MARKERS.length; m++) {
      if (body.indexOf(CONFIG.REQUIRED_PAGE_MARKERS[m]) === -1) {
        ctx.pageIssues.push({ url: url, reason: 'missing marker "' + CONFIG.REQUIRED_PAGE_MARKERS[m] + '" (funnel may be broken)' });
      }
    }
  }
}

// ----------------------------------------------------------------------------
//  3b) DISAPPROVED ADS
// ----------------------------------------------------------------------------
function checkDisapprovedAds(ctx) {
  var query =
    'SELECT campaign.name, ad_group.name, ad_group_ad.ad.id ' +
    'FROM ad_group_ad ' +
    "WHERE ad_group_ad.policy_summary.approval_status = 'DISAPPROVED' " +
    "AND ad_group_ad.status = 'ENABLED' AND campaign.status = 'ENABLED'";
  var rows = AdsApp.report(query).rows();
  while (rows.hasNext()) {
    var row = rows.next();
    ctx.disapproved.push({
      campaign: String(row['campaign.name'] || ''),
      adGroup: String(row['ad_group.name'] || ''),
      adId: String(row['ad_group_ad.ad.id'] || '')
    });
  }
}

// ----------------------------------------------------------------------------
//  3c) CONVERSION FLATLINE: clicks happening, zero conversions
// ----------------------------------------------------------------------------
function checkFlatline(ctx) {
  var query =
    'SELECT metrics.clicks, metrics.conversions, metrics.cost_micros ' +
    'FROM campaign ' +
    'WHERE segments.date DURING ' + CONFIG.CONVERSION_LOOKBACK + ' ' +
    "AND campaign.status = 'ENABLED'";
  var clicks = 0, conv = 0, spend = 0;
  var rows = AdsApp.report(query).rows();
  while (rows.hasNext()) {
    var row = rows.next();
    clicks += parseFloat(row['metrics.clicks'] || 0);
    conv += parseFloat(row['metrics.conversions'] || 0);
    spend += micros(row['metrics.cost_micros']);
  }
  if (conv === 0 && clicks >= CONFIG.MIN_CLICKS_FOR_FLATLINE_ALARM) {
    ctx.flatline = { clicks: clicks, spend: spend };
  }
}

// ----------------------------------------------------------------------------
//  OPTIONAL: append a row to an audit Sheet
// ----------------------------------------------------------------------------
function logToSheet(ctx) {
  if (!CONFIG.SHEET_URL) return;
  var sheet = SpreadsheetApp.openByUrl(CONFIG.SHEET_URL).getActiveSheet();
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['run_at', 'terms_scanned', 'junk_tokens', 'auto_added', 'wasted_$', 'page_issues', 'disapproved', 'flatline']);
  }
  var wasted = 0, t;
  for (t in ctx.negFindings) wasted += ctx.negFindings[t].spend;
  for (var i = 0; i < ctx.zeroConvTerms.length; i++) wasted += ctx.zeroConvTerms[i].spend;
  sheet.appendRow([
    ctx.started, ctx.scanned, Object.keys(ctx.negFindings).length, ctx.autoAdded.length,
    Math.round(wasted), ctx.pageIssues.length, ctx.disapproved.length, ctx.flatline ? 'YES' : 'no'
  ]);
}

// ============================================================================
//  EMAIL DIGEST
// ============================================================================
function sendDigest(ctx) {
  var critical = ctx.pageIssues.length || ctx.disapproved.length || ctx.flatline;
  var hasFindings = critical || Object.keys(ctx.negFindings).length ||
    Object.keys(ctx.negReviewOnly).length || ctx.zeroConvTerms.length ||
    ctx.expensiveTerms.length || ctx.winners.length || ctx.errors.length;

  if (!hasFindings && !CONFIG.EMAIL_ALWAYS) {
    Logger.log('Clean run, nothing to report. (Set EMAIL_ALWAYS=true to email anyway.)');
    return;
  }

  var flag = critical ? '🔴 ' : (Object.keys(ctx.negFindings).length ? '🟡 ' : '🟢 ');
  var mode = CONFIG.AUTO_APPLY_NEGATIVES ? 'AUTO-APPLY' : 'DRY-RUN';
  var subject = flag + 'Drozq Lead-Gen Guardian (' + CONFIG.ACCOUNT_LABEL + ') — ' +
    Object.keys(ctx.negFindings).length + ' negatives, ' +
    ctx.pageIssues.length + ' page issues [' + mode + ']';

  var h = [];
  h.push('<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:720px;color:#1a1a1a">');
  h.push('<h2 style="margin:0 0 4px">Drozq Lead-Gen Guardian</h2>');
  h.push('<p style="margin:0 0 16px;color:#666;font-size:13px">' + ctx.started +
    ' · window ' + CONFIG.LOOKBACK + ' · ' + ctx.scanned + ' paid search terms scanned · mode <b>' + mode + '</b></p>');

  // --- CRITICAL first -------------------------------------------------------
  if (ctx.flatline) {
    h.push(card('#fdecea', '#b71c1c', '🔴 CONVERSION FLATLINE',
      '<b>' + ctx.flatline.clicks + ' clicks</b> and <b>$' + money(ctx.flatline.spend) +
      '</b> over ' + CONFIG.CONVERSION_LOOKBACK + ' with <b>0 conversions</b>. ' +
      'Check the funnel and the <code>lead_confirmed</code> trigger immediately — this is a kill-switch condition.'));
  }
  if (ctx.pageIssues.length) {
    var pi = ctx.pageIssues.map(function (p) { return '<li><code>' + esc(p.url) + '</code> — ' + esc(p.reason) + '</li>'; }).join('');
    h.push(card('#fdecea', '#b71c1c', '🔴 LANDING PAGE / FUNNEL', '<ul style="margin:6px 0 0;padding-left:18px">' + pi + '</ul>'));
  }
  if (ctx.disapproved.length) {
    var da = ctx.disapproved.map(function (d) { return '<li>' + esc(d.campaign) + ' › ' + esc(d.adGroup) + ' (ad ' + esc(d.adId) + ')</li>'; }).join('');
    h.push(card('#fdecea', '#b71c1c', '🔴 DISAPPROVED ADS', '<ul style="margin:6px 0 0;padding-left:18px">' + da + '</ul>'));
  }

  // --- Negatives ------------------------------------------------------------
  if (ctx.autoAdded.length) {
    h.push(card('#e8f5e9', '#1b5e20', '✅ AUTO-ADDED ' + ctx.autoAdded.length + ' NEGATIVES to "' + esc(CONFIG.NEG_LIST_NAME) + '"',
      '<code>' + ctx.autoAdded.map(esc).join('</code>, <code>') + '</code>'));
  }
  var hiTokens = Object.keys(ctx.negFindings).sort(function (a, b) { return ctx.negFindings[b].spend - ctx.negFindings[a].spend; });
  if (hiTokens.length) {
    var verb = CONFIG.AUTO_APPLY_NEGATIVES ? 'High-confidence junk (auto-applied above when new)' : 'High-confidence junk — recommend adding as phrase negatives';
    h.push('<h3 style="margin:18px 0 6px">' + verb + '</h3>');
    h.push(negTable(hiTokens, ctx.negFindings));
  }
  var medTokens = Object.keys(ctx.negReviewOnly).sort(function (a, b) { return ctx.negReviewOnly[b].spend - ctx.negReviewOnly[a].spend; });
  if (medTokens.length) {
    h.push('<h3 style="margin:18px 0 6px">Review-only (never auto-applied — overlap risk)</h3>');
    h.push(negTable(medTokens, ctx.negReviewOnly));
  }

  // --- Wasted spend ---------------------------------------------------------
  if (ctx.expensiveTerms.length) {
    h.push('<h3 style="margin:18px 0 6px">💸 Expensive clicks (avg CPC ≥ $' + CONFIG.EXPENSIVE_CLICK_ALERT + ')</h3>');
    h.push(simpleTable(['Search term', 'Avg CPC', 'Clicks', 'Spend'],
      ctx.expensiveTerms.sort(function (a, b) { return b.cpc - a.cpc; }).slice(0, 20).map(function (t) {
        return [t.term, '$' + money(t.cpc), t.clicks, '$' + money(t.spend)];
      })));
  }
  if (ctx.zeroConvTerms.length) {
    h.push('<h3 style="margin:18px 0 6px">🧐 Spent ≥ $' + CONFIG.ZERO_CONV_SPEND_ALERT + ', zero conversions (not auto-junk — your call)</h3>');
    h.push(simpleTable(['Search term', 'Spend', 'Clicks', 'Campaign'],
      ctx.zeroConvTerms.sort(function (a, b) { return b.spend - a.spend; }).slice(0, 20).map(function (t) {
        return [t.term, '$' + money(t.spend), t.clicks, t.campaign];
      })));
  }

  // --- Winners --------------------------------------------------------------
  if (ctx.winners.length) {
    h.push('<h3 style="margin:18px 0 6px">🏆 Converting terms you have NOT promoted to keywords</h3>');
    h.push(simpleTable(['Search term', 'Conv', 'Spend', 'Saw it in'],
      ctx.winners.sort(function (a, b) { return b.conv - a.conv; }).slice(0, 20).map(function (t) {
        return [t.term, t.conv, '$' + money(t.spend), t.campaign + ' › ' + t.adGroup];
      })));
  }

  if (ctx.errors.length) {
    h.push(card('#fff8e1', '#8d6e00', '⚠️ Module errors (digest still sent)',
      '<ul style="margin:6px 0 0;padding-left:18px"><li>' + ctx.errors.map(esc).join('</li><li>') + '</li></ul>'));
  }

  h.push('<p style="margin:20px 0 0;color:#999;font-size:12px">Dry-run changes nothing. To let it add high-confidence negatives automatically, set <code>AUTO_APPLY_NEGATIVES = true</code>. Companion: notes/ads/bidding-decisions.md.</p>');
  h.push('</div>');

  MailApp.sendEmail({ to: CONFIG.EMAIL_TO, subject: subject, htmlBody: h.join('\n') });
  Logger.log('Digest emailed to ' + CONFIG.EMAIL_TO);
}

// ============================================================================
//  HELPERS
// ============================================================================
function guard(ctx, name, fn) {
  try { fn(); } catch (e) { ctx.errors.push(name + ': ' + e); Logger.log('ERROR in ' + name + ': ' + e); }
}

function micros(v) { return (parseInt(v, 10) || 0) / 1000000; }
function money(n) { return (Math.round(n * 100) / 100).toFixed(2); }
function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function getActiveKeywordTexts() {
  var set = {};
  try {
    var rows = AdsApp.report(
      'SELECT ad_group_criterion.keyword.text FROM keyword_view ' +
      "WHERE ad_group_criterion.status = 'ENABLED' AND campaign.status = 'ENABLED'").rows();
    while (rows.hasNext()) {
      var t = String(rows.next()['ad_group_criterion.keyword.text'] || '').toLowerCase().trim();
      if (t) set[t] = true;
    }
  } catch (e) { /* non-fatal: worst case we recommend negating a live keyword, caught on review */ }
  return set;
}

function getNegativeList(name) {
  var it = AdsApp.negativeKeywordLists().get();
  while (it.hasNext()) { var l = it.next(); if (l.getName() === name) return l; }
  return null;
}

function existingNegativeTokens(list) {
  var set = {};
  var it = list.negativeKeywords().get();
  while (it.hasNext()) {
    var t = String(it.next().getText()).toLowerCase().replace(/[\[\]"]/g, '').trim();
    if (t) set[t] = true;
  }
  return set;
}

function card(bg, fg, title, html) {
  return '<div style="background:' + bg + ';border-left:4px solid ' + fg + ';padding:12px 14px;margin:10px 0;border-radius:4px">' +
    '<div style="font-weight:700;color:' + fg + ';margin-bottom:4px">' + title + '</div>' +
    '<div style="font-size:14px">' + html + '</div></div>';
}

function negTable(tokens, data) {
  var rows = tokens.map(function (tok) {
    var r = data[tok];
    return [tok, r.label, '$' + money(r.spend), r.conv.toFixed(1), r.terms.join(', ')];
  });
  return simpleTable(['Negative (phrase)', 'Why', 'Spend', 'Conv', 'Example terms'], rows);
}

function simpleTable(headers, rows) {
  var th = headers.map(function (x) { return '<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #ddd;font-size:12px;color:#555">' + esc(x) + '</th>'; }).join('');
  var tr = rows.map(function (r) {
    var tds = r.map(function (c) { return '<td style="padding:6px 10px;border-bottom:1px solid #eee;font-size:13px;vertical-align:top">' + esc(c) + '</td>'; }).join('');
    return '<tr>' + tds + '</tr>';
  }).join('');
  return '<table style="border-collapse:collapse;width:100%;margin:4px 0"><thead><tr>' + th + '</tr></thead><tbody>' + tr + '</tbody></table>';
}
