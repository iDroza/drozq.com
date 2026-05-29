#!/usr/bin/env python3
"""Durable Google Ads pull. NO gcloud, NO MCP.

Auth: stored refresh token in scripts/.google_ads.json (run
scripts/google_ads_auth.py once to create it), exchanged for an access token
directly against oauth2.googleapis.com on every run.

Usage:
  python scripts/ads.py                  # full decision pull (8 sections)
  python scripts/ads.py "SELECT ..."     # run an ad-hoc GAQL query, print JSON
"""
import os, sys, json, urllib.request, urllib.error, urllib.parse

HERE  = os.path.dirname(os.path.abspath(__file__))
CREDS = os.path.join(HERE, ".google_ads.json")
TOKEN_URL = "https://oauth2.googleapis.com/token"


def die(msg, code=1):
    print(msg)
    sys.exit(code)


if not os.path.exists(CREDS):
    die("No credentials at scripts/.google_ads.json.\n"
        "Run this once first:  python scripts/google_ads_auth.py")

C = json.load(open(CREDS))
DEV   = C.get("developer_token") or os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
LOGIN = C.get("login_customer_id", "1975174499")
CID   = C.get("customer_id", "3351363652")


def access_token():
    data = urllib.parse.urlencode({
        "client_id": C["client_id"], "client_secret": C["client_secret"],
        "refresh_token": C["refresh_token"], "grant_type": "refresh_token",
    }).encode()
    try:
        d = json.loads(urllib.request.urlopen(
            urllib.request.Request(TOKEN_URL, data=data)).read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "invalid_grant" in body:
            die("Refresh token rejected (invalid_grant).\n"
                "Re-run:  python scripts/google_ads_auth.py\n"
                "If it keeps happening, publish the consent screen to Production:\n"
                "  https://console.cloud.google.com/auth/audience?project=drozq-ads-mcp")
        die("Token refresh failed: " + body[:800])
    return d["access_token"]


TOKEN = access_token()
URL = f"https://googleads.googleapis.com/v20/customers/{CID}/googleAds:search"


def gaql(q):
    rows, page = [], None
    while True:
        body = {"query": q}
        if page:
            body["pageToken"] = page
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
            "Authorization": f"Bearer {TOKEN}", "developer-token": DEV,
            "login-customer-id": LOGIN, "Content-Type": "application/json"})
        try:
            d = json.loads(urllib.request.urlopen(req).read())
        except urllib.error.HTTPError as e:
            return {"__error__": f"HTTP {e.code}: {e.read().decode()[:1500]}"}
        rows += d.get("results", [])
        page = d.get("nextPageToken")
        if not page:
            break
    return rows


# ----- ad-hoc query mode -----
if len(sys.argv) > 1:
    print(json.dumps(gaql(sys.argv[1]), indent=2))
    sys.exit(0)


# ----- formatting helpers -----
def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0
def usd(m): return num(m) / 1_000_000
def pct(x): return f"{num(x)*100:5.1f}%"
def g(row, *path):
    cur = row
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur
def block(title):
    print("\n" + "=" * 100 + f"\n{title}\n" + "=" * 100)


# ---------- 1. ACCOUNT ----------
block("1. ACCOUNT")
r = gaql("SELECT customer.id, customer.descriptive_name, customer.currency_code, "
         "customer.time_zone, customer.auto_tagging_enabled FROM customer")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    for row in r:
        c = row.get("customer", {})
        print(f"id={c.get('id')}  name={c.get('descriptiveName')}  cur={c.get('currencyCode')}  "
              f"tz={c.get('timeZone')}  autotag={c.get('autoTaggingEnabled')}")

# ---------- 2. CAMPAIGN CONFIG / BIDDING ----------
block("2. CAMPAIGN CONFIG + BIDDING STRATEGY")
r = gaql("SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, "
         "campaign.bidding_strategy_type, campaign.start_date, campaign_budget.amount_micros, "
         "campaign.maximize_conversions.target_cpa_micros, campaign.target_cpa.target_cpa_micros, "
         "campaign.target_spend.cpc_bid_ceiling_micros, campaign.manual_cpc.enhanced_cpc_enabled "
         "FROM campaign WHERE campaign.status != 'REMOVED'")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    for row in r:
        c = row.get("campaign", {}); b = row.get("campaignBudget", {})
        print(f"\n[{c.get('status')}] {c.get('name')}  (id {c.get('id')})")
        print(f"   channel={c.get('advertisingChannelType')}  start={c.get('startDate')}")
        print(f"   bidStrategy={c.get('biddingStrategyType')}  dailyBudget=${usd(b.get('amountMicros')):.2f}")
        mc = g(c, 'maximizeConversions', 'targetCpaMicros'); tc = g(c, 'targetCpa', 'targetCpaMicros')
        ceil = g(c, 'targetSpend', 'cpcBidCeilingMicros'); ecpc = g(c, 'manualCpc', 'enhancedCpcEnabled')
        if mc:   print(f"   maxConv.targetCPA=${usd(mc):.2f}")
        if tc:   print(f"   tCPA.target=${usd(tc):.2f}")
        if ceil: print(f"   maxClicks.cpcCeiling=${usd(ceil):.2f}")
        if ecpc is not None: print(f"   manualCPC.enhanced={ecpc}")

# ---------- 3. CAMPAIGN 30-DAY PERFORMANCE ----------
block("3. CAMPAIGN PERFORMANCE (LAST 30 DAYS, aggregated)")
r = gaql("SELECT campaign.name, metrics.impressions, metrics.clicks, metrics.cost_micros, "
         "metrics.average_cpc, metrics.ctr, metrics.conversions, metrics.conversions_value, "
         "metrics.search_impression_share, metrics.search_budget_lost_impression_share, "
         "metrics.search_rank_lost_impression_share, metrics.search_top_impression_share, "
         "metrics.search_absolute_top_impression_share, metrics.search_exact_match_impression_share "
         "FROM campaign WHERE segments.date DURING LAST_30_DAYS AND campaign.status != 'REMOVED'")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    for row in r:
        c = row.get("campaign", {}); m = row.get("metrics", {})
        cost = usd(m.get('costMicros')); clk = num(m.get('clicks')); imp = num(m.get('impressions'))
        conv = num(m.get('conversions'))
        cpc = cost / clk if clk else 0
        cpl = cost / conv if conv else 0
        cvr = conv / clk if clk else 0
        print(f"\n{c.get('name')}")
        print(f"   impr={imp:.0f}  clicks={clk:.0f}  cost=${cost:.2f}  CTR={pct(m.get('ctr'))}")
        print(f"   avgCPC=${cpc:.2f} (api ${usd(m.get('averageCpc')):.2f})  conv={conv:.1f}  "
              f"CPL=${cpl:.2f}  CVR={pct(cvr)}")
        print(f"   IS: search={pct(m.get('searchImpressionShare'))}  top={pct(m.get('searchTopImpressionShare'))}  "
              f"absTop={pct(m.get('searchAbsoluteTopImpressionShare'))}  "
              f"exactMatchIS={pct(m.get('searchExactMatchImpressionShare'))}")
        print(f"   LOST IS: rank={pct(m.get('searchRankLostImpressionShare'))}  "
              f"budget={pct(m.get('searchBudgetLostImpressionShare'))}")

# ---------- 4. DAILY TREND ----------
block("4. DAILY TREND (LAST 30 DAYS)")
r = gaql("SELECT segments.date, metrics.impressions, metrics.clicks, metrics.cost_micros, "
         "metrics.conversions, metrics.search_impression_share, "
         "metrics.search_rank_lost_impression_share, metrics.search_budget_lost_impression_share "
         "FROM campaign WHERE segments.date DURING LAST_30_DAYS AND campaign.status != 'REMOVED' "
         "ORDER BY segments.date")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    print(f"{'date':12} {'impr':>6} {'clk':>5} {'cost':>9} {'conv':>5} {'CPC':>7}  "
          f"{'IS':>6} {'rankLost':>8} {'budLost':>8}")
    for row in r:
        s = row.get("segments", {}); m = row.get("metrics", {})
        cost = usd(m.get('costMicros')); clk = num(m.get('clicks'))
        cpc = cost / clk if clk else 0
        print(f"{s.get('date'):12} {num(m.get('impressions')):6.0f} {clk:5.0f} {cost:9.2f} "
              f"{num(m.get('conversions')):5.1f} {cpc:7.2f}  {pct(m.get('searchImpressionShare'))} "
              f"{pct(m.get('searchRankLostImpressionShare')):>8} "
              f"{pct(m.get('searchBudgetLostImpressionShare')):>8}")

# ---------- 5. AD GROUPS ----------
block("5. AD GROUP PERFORMANCE (LAST 30 DAYS)")
r = gaql("SELECT campaign.name, ad_group.name, ad_group.cpc_bid_micros, metrics.impressions, "
         "metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.search_impression_share, "
         "metrics.search_rank_lost_impression_share, metrics.search_budget_lost_impression_share "
         "FROM ad_group WHERE segments.date DURING LAST_30_DAYS AND ad_group.status != 'REMOVED' "
         "AND campaign.status != 'REMOVED' ORDER BY metrics.cost_micros DESC")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    for row in r:
        ag = row.get("adGroup", {}); m = row.get("metrics", {})
        cost = usd(m.get('costMicros')); clk = num(m.get('clicks')); conv = num(m.get('conversions'))
        cpc = cost / clk if clk else 0; cpl = cost / conv if conv else 0
        print(f"{(ag.get('name') or '')[:34]:34} bid=${usd(ag.get('cpcBidMicros')):5.2f}  "
              f"imp={num(m.get('impressions')):5.0f} clk={clk:4.0f} cost=${cost:7.2f} cpc=${cpc:5.2f} "
              f"conv={conv:4.1f} cpl=${cpl:7.2f} IS={pct(m.get('searchImpressionShare'))} "
              f"rankLost={pct(m.get('searchRankLostImpressionShare'))}")

# ---------- 6. KEYWORDS ----------
block("6. KEYWORDS (LAST 30 DAYS, by cost) - bid vs top-of-page estimate + QS")
r = gaql("SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, "
         "ad_group_criterion.cpc_bid_micros, ad_group_criterion.effective_cpc_bid_micros, "
         "ad_group_criterion.quality_info.quality_score, "
         "ad_group_criterion.position_estimates.top_of_page_cpc_micros, "
         "ad_group_criterion.position_estimates.first_position_cpc_micros, "
         "metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.average_cpc, "
         "metrics.conversions, metrics.search_impression_share, metrics.search_top_impression_share, "
         "metrics.search_rank_lost_impression_share "
         "FROM keyword_view WHERE segments.date DURING LAST_30_DAYS "
         "AND ad_group_criterion.status != 'REMOVED' ORDER BY metrics.cost_micros DESC LIMIT 200")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    print(f"{'keyword':38} {'mt':4} {'QS':>3} {'bid':>6} {'topEst':>7} {'1stEst':>7} {'imp':>5} "
          f"{'clk':>4} {'cost':>8} {'cpc':>6} {'conv':>4} {'IS':>6} {'topIS':>6} {'rankLost':>8}")
    for row in r:
        k = row.get("adGroupCriterion", {}); m = row.get("metrics", {})
        kw = g(k, 'keyword', 'text') or ''; mt = (g(k, 'keyword', 'matchType') or '')[:4]
        qs = g(k, 'qualityInfo', 'qualityScore')
        bid = usd(k.get('cpcBidMicros') or k.get('effectiveCpcBidMicros'))
        topEst = usd(g(k, 'positionEstimates', 'topOfPageCpcMicros'))
        firstEst = usd(g(k, 'positionEstimates', 'firstPositionCpcMicros'))
        cost = usd(m.get('costMicros')); clk = num(m.get('clicks'))
        cpc = cost / clk if clk else 0
        print(f"{kw[:38]:38} {mt:4} {str(qs or '-'):>3} {bid:6.2f} {topEst:7.2f} {firstEst:7.2f} "
              f"{num(m.get('impressions')):5.0f} {clk:4.0f} {cost:8.2f} {cpc:6.2f} "
              f"{num(m.get('conversions')):4.1f} {pct(m.get('searchImpressionShare')):>6} "
              f"{pct(m.get('searchTopImpressionShare')):>6} "
              f"{pct(m.get('searchRankLostImpressionShare')):>8}")

# ---------- 7. SEARCH TERMS ----------
block("7. SEARCH TERMS (LAST 30 DAYS, top 60 by cost)")
r = gaql("SELECT search_term_view.search_term, metrics.impressions, metrics.clicks, "
         "metrics.cost_micros, metrics.conversions FROM search_term_view "
         "WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC LIMIT 60")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    print(f"{'search term':50} {'imp':>5} {'clk':>4} {'cost':>8} {'cpc':>6} {'conv':>5}")
    for row in r:
        st = g(row, 'searchTermView', 'searchTerm') or ''; m = row.get("metrics", {})
        cost = usd(m.get('costMicros')); clk = num(m.get('clicks'))
        cpc = cost / clk if clk else 0
        print(f"{st[:50]:50} {num(m.get('impressions')):5.0f} {clk:4.0f} {cost:8.2f} {cpc:6.2f} "
              f"{num(m.get('conversions')):5.1f}")

# ---------- 8. DEVICE ----------
block("8. DEVICE SPLIT (LAST 30 DAYS)")
r = gaql("SELECT segments.device, metrics.impressions, metrics.clicks, metrics.cost_micros, "
         "metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS "
         "AND campaign.status != 'REMOVED'")
if isinstance(r, dict):
    print("ERR:", r["__error__"])
else:
    for row in r:
        s = row.get("segments", {}); m = row.get("metrics", {})
        cost = usd(m.get('costMicros')); clk = num(m.get('clicks')); conv = num(m.get('conversions'))
        cpc = cost / clk if clk else 0; cpl = cost / conv if conv else 0
        print(f"{s.get('device'):10} imp={num(m.get('impressions')):6.0f} clk={clk:4.0f} "
              f"cost=${cost:7.2f} cpc=${cpc:5.2f} conv={conv:4.1f} cpl=${cpl:7.2f}")

print("\n\n--- DONE ---")
