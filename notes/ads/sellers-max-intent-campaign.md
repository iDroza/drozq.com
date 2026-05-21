# Sellers, Max-Intent Search Campaign

Build spec for a Google Search campaign that targets **high-intent home sellers in Irvine and Orange County**. Optimized for **conversion rate over volume**: every keyword, every word of ad copy, and every asset is anchored to what the landing page (drozq.com) actually promises and what the on-page funnel actually delivers. Cohesion is the entire thesis: ad query = ad copy = landing-page hero = funnel CTA. Zero message gap.

This is **NOT** the high-painpoint campaign (pre-foreclosure, divorce, probate, inheritance). That campaign is built next and intentionally carved out as negatives here so the two cannot cannibalize.

*Last updated: 2026-05-20.*

---

## 0. The cohesion contract (the thing every ad must echo)

What a cold visitor sees on drozq.com (per the live accessibility snapshot, 2026-05-18):

- **H1:** "Compare Agents. Find a Trusted Expert."
- **Subhead:** "We analyze thousands of local agents and find the best to compete in your area."
- **First CTA:** address box + button "Compare Agents." Tab defaults to **Sell**.
- **Proof block 1:** "How we match you: Tell us about your home, We find the best match, Vetted on track record, Compare real proposals, Free, no commitment."
- **Proof block 2:** "Review proposals and choose the right agent, confidently... AgentLocator by drozq.com offers free proposals... to pick the agent who can help you sell for top dollar."
- **Market widget:** "Mar 2026, real estate trends in Irvine, CA. It's a seller's market. Sold price median $1,488,000. Average days on market 35 days."
- **FAQ:** "Free for home sellers... Submit request under 2 minutes... 3 to 5 personalized proposals within 24 hours... no obligation."
- **Funnel terminal step:** button "Send My Home Value Report." Value bar: "Free, no obligation. Reviewed personally by Joshua Guerrero." Assurance: "Your valuation lands within 24 hours. Licensed in California, DRE #02267255."

**The four cohesion promises every ad MUST contain:**

1. **Compare / find a vetted local agent** (the hero, seen first)
2. **Free, no obligation, walk away anytime**
3. **3 to 5 proposals within 24 hours**
4. **Sell for top dollar in a seller's market** (median $1.48M, 35 days)

Anything outside those four breaks message match. Anything inside them compounds it.

---

## 1. Pre-flight (do these BEFORE launching, gates clean signal)

These are not optional. They directly affect Smart Bidding accuracy.

1. **Fix the GA4 `generate_lead` GTM trigger.** Per `CLAUDE.md`, the trigger still fires on `/thank-you/` pageview, which over-counts refreshes/bookmarks/direct visits. Change the trigger to `Custom Event = lead_confirmed` in GTM and publish, BEFORE switching from Max Conversions to tCPA. Until this lands, expect ~20-30% inflation in reported conversions, and stay on Max Conversions only (do not move to tCPA on dirty signal).
2. **Confirm Google Ads ↔ GA4 link is healthy.** Settings → Linked accounts → Google Analytics 4. Confirm `generate_lead` is showing in the Conversions table with recent counts.
3. **Auto-tagging ON.** Settings → Account settings → Auto-tagging → ON. (Confirms `gclid` lands on the URL; the page already captures it to cookie + sessionStorage.)
4. **IP exclude your own networks.** Settings → IP exclusions → add your home IP, office IP, and any VPN exit you use. Real-estate budgets get destroyed by self-clicks.
5. **Sign Joshua's verified advertiser identity** is in place (UI confirms it as "Joshua A Guerrero"). Submit "Drozq" as the business-name asset for review; fall back to "Joshua A Guerrero" if rejected.

---

## 2. Campaign settings

| Field | Value |
|---|---|
| **Campaign name** | `Search \| Sellers \| Max-Intent \| Irvine+OC` |
| **Goal** | Leads |
| **Type** | Search |
| **Conversion goals** | `Leads` only. Inside Leads, ONLY `generate_lead` checked as account-default. All other conversions Secondary. |
| **Networks** | Search Network: ON. **Search Partners: OFF**. **Display Expansion: OFF**. |
| **Locations (Presence, NOT Interest)** | "People in or regularly in your targeted locations" |
| **Location targets** | Irvine; Tustin; Newport Beach; Newport Coast; Corona del Mar; Costa Mesa; Lake Forest; Mission Viejo; Aliso Viejo; Laguna Hills; Laguna Niguel; Laguna Beach; Orange (city); Yorba Linda; Villa Park; Rancho Santa Margarita; Coto de Caza; Ladera Ranch; Dana Point. **Add ZIPs** for unincorporated/named-community pockets: 92807, 92808 (Anaheim Hills); 92610 (Foothill Ranch); 92676 (Silverado/Modjeska). |
| **Location exclusions** | None at launch. Add UCI dorm ZIP (92697) after 14 days if search-terms data shows student-housing intent. |
| **Languages** | English only. (Page is English; do not let Spanish-browser users in until you have a Spanish LP.) |
| **Audiences** | **Observation, NOT Targeting.** See §6. |
| **Devices** | All. No bid adjustment at launch. |
| **Ad rotation** | Optimize. |
| **Ad schedule** | All hours, all days. Trim from data at week 3. |
| **AI Max for Search** | **OFF** at launch on every ad group. (We want intent purity; AI Max broadens. Test in a controlled experiment after tCPA stabilizes.) |
| **Bidding strategy** | Phase 1 (week 0 to ~30 conversions): **Maximize Conversions**, no tCPA cap. Phase 2: **Target CPA**, set at ~1.2x observed CPL from Phase 1. |
| **Daily budget** | $150/day floor (recommended). Real-estate Irvine CPC runs $5 to $15; at $10 CPC and ~7% lead rate, expected CPL ~$140. $150/day x 21 days seeds ~22 conversions, enough to start tCPA. Compress to $250/day if you want Phase 1 in 2 weeks. |
| **Start/end date** | Start ASAP (after pre-flight). No end date. |
| **Campaign URL options - Tracking template** | Leave blank. Auto-tagging handles `gclid`. |
| **Campaign URL options - Final URL suffix** | `utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_content={creative}&utm_term={keyword}&utm_matchtype={matchtype}&gad_campaign={campaignid}` |

---

## 3. Ad group structure

Four single-theme ad groups. Tight themes are how message match stays clean and Quality Score stays high.

| Ad group name | Intent it captures | Page anchor |
|---|---|---|
| `AG1 \| Compare-Listing-Agent` | "they want an agent now" | H1: "Compare Agents. Find a Trusted Expert." |
| `AG2 \| Home-Value-Report` | "they want their number, becomes a lead via the report" | Funnel CTA: "Send My Home Value Report" + market widget |
| `AG3 \| Sell-My-House-OC` | "they want to sell, looking for who" | Proof: "sell for top dollar," seller's market |
| `AG4 \| Compare-Commission` | rate-shoppers (the page literally promises rate transparency) | "Side-by-side commission rates" |

Final URL for every ad group: `https://drozq.com/`

Display paths per ad group below.

---

## 4. Keywords per ad group

**Match-type policy at launch:** Exact-heavy with a small Phrase set. NO Broad until after Phase 2 launches and the negative list is locked. Then test Broad only in AG1 and AG3.

Notation: `[exact]`, `"phrase"`.

### AG1 — Compare-Listing-Agent

Display path: `/Irvine` `/Compare-Agents`

Keywords (Exact):
```
[compare real estate agents irvine]
[compare realtors irvine]
[best listing agent irvine]
[best real estate agent to sell my house]
[top real estate agents irvine]
[top listing agent orange county]
[find a realtor to sell my house]
[realtor to sell my house near me]
[best realtor near me to sell house]
[find a listing agent]
[best agent to sell my home]
[best agents in irvine]
[compare real estate agents orange county]
[top real estate agent newport beach]
[best listing agent newport beach]
[best listing agent tustin]
[best listing agent mission viejo]
```

Keywords (Phrase):
```
"compare realtors to sell"
"find a listing agent"
"best agent to sell my home"
"top listing agents in irvine"
"compare local realtors"
"find best real estate agent"
```

### AG2 — Home-Value-Report

Display path: `/Irvine` `/Home-Value`

Keywords (Exact):
```
[what is my home worth irvine]
[what's my house worth irvine]
[home value estimate irvine]
[free home valuation irvine]
[free home value report]
[free home value report irvine]
[home value report]
[free cma irvine]
[free comparative market analysis]
[home valuation irvine]
[home valuation newport beach]
[home valuation tustin]
[what is my home worth in orange county]
[my home value]
```

Keywords (Phrase):
```
"what is my home worth"
"free home value report"
"home valuation near me"
"free home valuation"
"what's my house worth"
"free cma"
```

### AG3 — Sell-My-House-OC

Display path: `/Sell` `/Top-Dollar`

Keywords (Exact):
```
[sell my house irvine]
[sell my home irvine]
[selling my home in irvine]
[sell my house in irvine]
[list my house irvine]
[i want to sell my house irvine]
[sell my house newport beach]
[sell my house tustin]
[sell my house costa mesa]
[sell my house lake forest]
[sell my house mission viejo]
[sell my house aliso viejo]
[sell my house orange county]
[sell my home orange county]
[list my home in orange county]
```

Keywords (Phrase):
```
"sell my house in irvine"
"sell my home in orange county"
"list my home in irvine"
"how to sell my home in irvine"
"selling a home in orange county"
```

### AG4 — Compare-Commission

Display path: `/Compare` `/Commission`

Keywords (Exact):
```
[real estate agent commission rates]
[real estate commission rates california]
[realtor commission to sell house]
[compare agent commission]
[compare realtor commission]
[listing agent fees irvine]
[realtor fees to sell a house]
[realtor commission orange county]
[how much do realtors charge to sell]
[listing agent commission rate]
```

Keywords (Phrase):
```
"real estate commission rates"
"how much do realtors charge to sell"
"realtor commission to sell a house"
"compare listing agent commission"
"listing agent fees"
```

---

## 5. Negative keywords (this is where conversion rate is actually defended)

Create a **shared negative keyword list** in Tools → Shared Library → Negative keyword lists → name it `Negatives | Sellers Funnel`. Attach it to this campaign now and to the future high-painpoint campaign later. Both directions of cannibalization will be walled off.

### `Negatives | Sellers Funnel` (campaign-attached, shared)

**Industry / jobs / education (kills tire-kickers and career searches):**
```
realtor jobs
real estate license
real estate license california
real estate license cost
agent salary
real estate agent salary
become a real estate agent
real estate school
real estate exam
real estate broker license
how to become a realtor
realtor near me hiring
real estate continuing education
realtor commission split
real estate agent reviews of brokerages
```

**DIY / won't hire an agent:**
```
for sale by owner
fsbo
sell house without agent
sell my house myself
how to sell a house
how to sell a house by owner
flat fee mls
flat fee listing
discount broker
1 percent commission realtor
sell my house without realtor
do i need a realtor to sell
```

**iBuyers / cash buyers (different product, different mindset):**
```
zillow offer
opendoor
offerpad
ibuyer
cash offer
we buy houses
sell to investor
cash for my home
quick cash for house
instant offer
```

**Research tools / not-ready-to-engage:**
```
zillow
redfin
zestimate
realtor.com
trulia
home value calculator
free instant estimate
home value estimator app
home value app
```

**Rentals / wrong product:**
```
rent
rental
for rent
apartment
apartments
lease
property management
rent my house
how to rent out my house
landlord
section 8
```

**Buyers (out of scope for this campaign):**
```
buy a home
buy my first home
homes for sale
houses for sale
homes for rent
buyer's agent
first time home buyer
buyers agent commission
```

**High-painpoint carve-out (saves these for the next campaign):**
```
foreclosure
pre foreclosure
preforeclosure
short sale
divorce sale
divorce real estate
probate
probate sale
inherited property
inheritance house
estate sale house
behind on mortgage
stop foreclosure
avoid foreclosure
sell house fast cash
distressed property
loan modification
bankruptcy house sale
```

**Out-of-state geo (block accidental search-network mismatches even though geo is set):**
```
texas
florida
new york
chicago
ohio
columbus ohio
arizona
phoenix
nevada
las vegas
washington
oregon
```

**Brand defense for competing platforms (don't pay to lose):**
```
redfin agents
homelight
ideal agent
upnest
clever real estate
rocket homes
listingspark
yelp
realtor.com find agent
```

### Campaign-level negatives (not in the shared list)

These are specific to THIS campaign:
```
agent locator login
agentlocator login
drozq login
drozq jobs
drozq careers
joshua guerrero salary
```

---

## 6. Audience signals (Observation, NOT Targeting)

Add as **Observation** so we collect performance data without restricting reach. Bid up the winning segments at week 3+.

**In-market:**
- Residential Properties (For Sale)
- Residential Properties / Selling
- Real Estate Agents and Brokers
- Real Estate Services
- Home & Garden / Home Improvement
- Home Decor (proxy for "about to move")
- Moving Services

**Detailed Demographics:**
- Homeowners (Google has this segment under Homeownership status)
- Marital Status: Married
- Parental Status: Parent
- Education: Bachelor's degree+
- Household Income: Top 10%, 11-20%, 21-30%

**Affinity (low priority, but free observation data):**
- Avid Investors
- Luxury Travelers (proxy for OC luxury bracket)
- Banking & Finance / Avid Investors

**Custom segments (build these in Audience Manager):**
- Custom segment: `Sellers - Search Intent`
  - Type: "People who searched for any of these terms"
  - Terms: what is my home worth, sell my house, compare real estate agents, listing agent, home value report, free cma, sell my home for top dollar, realtor commission rates
- Custom segment: `Sellers - URL Intent`
  - Type: "People who browsed these types of websites"
  - URLs: zillow.com/homevalues/, redfin.com/what-is-my-home-worth, realtor.com/sell, homelight.com, opendoor.com/sell, offerpad.com/sell

**Remarketing (build now in GA4, layer as Observation when list size > 1,000):**
- Audience: `drozq.com visitors who did NOT submit lead in 30 days`
  - In GA4: condition includes page_view, excludes `lead_confirmed`, lookback 30 days.
  - Import to Google Ads.

**Demographic exclusions:** none at launch. After 21 days, exclude age 18-24 and HH income bottom 50% if SVR (submission rate) data justifies.

---

## 7. Ads (RSA per ad group)

Each ad group gets ONE RSA at launch, all 15 headlines populated, all 4 descriptions populated, pinned headlines as noted. (Google reduces Ad Strength penalty when most slots are filled and pins are minimal.) Add a second RSA per ad group in week 3 with rotated copy.

### AG1 RSA — Compare-Listing-Agent

**Pin:** Headline #1 → Position 1. Headline #2 → Position 2. All others unpinned.

**Headlines (15):**
1. `Compare Agents in Irvine` *(pin pos 1)*
2. `3-5 Proposals in 24 Hours` *(pin pos 2)*
3. `Free & No Commitment`
4. `Sell Your {LOCATION(City):Irvine} Home`
5. `Find a Trusted Listing Agent`
6. `Top Orange County Agents`
7. `Side-by-Side Proposals`
8. `Vetted on Sales Volume`
9. `It's a Seller's Market in OC`
10. `Reviewed Personally`
11. `You Stay in Control`
12. `Walk Away Anytime, No Fees`
13. `Compare Commission Rates`
14. `Top Local Listing Agents`
15. `Under 2 Minutes, No Obligation`

**Descriptions (4):**
1. `We analyze thousands of top local agents and find the best to compete in your area.`
2. `Get 3 to 5 personalized proposals within 24 hours. Compare rates and plans side by side.`
3. `Vetted on sales volume, expertise, and real client outcomes. Free, no obligation.`
4. `Irvine is a seller's market: median $1.48M, 35 days. The right agent gets you more.`

**Display path:** `/Irvine` / `/Compare-Agents`

### AG2 RSA — Home-Value-Report

**Pin:** Headline #1 → Position 1. Headline #2 → Position 2.

**Headlines (15):**
1. `What's Your Irvine Home Worth?` *(pin pos 1)*
2. `Free Home Value Report` *(pin pos 2)*
3. `Personally Reviewed in 24 Hrs`
4. `Irvine Median Sale: $1.48M`
5. `It's a Seller's Market in OC`
6. `Sell for Top Dollar`
7. `Compare Top Local Agents Free`
8. `No Obligation, You Stay Free`
9. `Get Your Valuation Today`
10. `Free CMA from Top OC Agents`
11. `35 Days on Market in Irvine`
12. `Takes Under 2 Minutes`
13. `Vetted on Real Outcomes`
14. `{LOCATION(City):Irvine} Home Value`
15. `Walk Away Anytime`

**Descriptions (4):**
1. `Free, no-obligation home value report, personally reviewed and back within 24 hours.`
2. `Irvine is a seller's market: median $1.48M, 35 days on market. See what yours brings.`
3. `We match you with top local agents to sell for top dollar. Free, no commitment.`
4. `Get 3 to 5 personalized proposals in 24 hours. Compare commission rates side by side.`

**Display path:** `/Irvine` / `/Home-Value`

### AG3 RSA — Sell-My-House-OC

**Pin:** Headline #1 → Position 1. Headline #2 → Position 2.

**Headlines (15):**
1. `Sell Your {LOCATION(City):Irvine} Home` *(pin pos 1)*
2. `Top Dollar in Seller's Market` *(pin pos 2)*
3. `Free, No-Obligation Strategy`
4. `Compare 3-5 Local Agents Free`
5. `Reviewed Personally in 24 Hrs`
6. `Irvine Median Sale: $1.48M`
7. `35 Days on Market in Irvine`
8. `Vetted on Real Outcomes`
9. `Under 2 Minutes to Start`
10. `Side-by-Side Proposals`
11. `Top Real Estate Agents in OC`
12. `No Commitment Ever`
13. `Walk Away Anytime`
14. `Newport, Tustin, Irvine, OC`
15. `Sell My House for Top Dollar`

**Descriptions (4):**
1. `Sell your Irvine home for top dollar. Free agent proposals in 24 hours, no obligation.`
2. `We analyze top local agents and find the best to compete to list your home. Free.`
3. `Irvine seller's market: median $1.48M, 35 days on market. The right agent gets more.`
4. `Compare commission rates and marketing plans side by side. Reviewed personally.`

**Display path:** `/Sell` / `/Top-Dollar`

### AG4 RSA — Compare-Commission

**Pin:** Headline #1 → Position 1. Headline #2 → Position 2.

**Headlines (15):**
1. `Compare Realtor Commissions` *(pin pos 1)*
2. `Side-by-Side Rates, Free` *(pin pos 2)*
3. `Compare Real Estate Commission`
4. `Negotiable, Not Fixed`
5. `Free Agent Proposals`
6. `3-5 Proposals in 24 Hours`
7. `Top Irvine & OC Listing Agents`
8. `No Commitment Ever`
9. `Sell for Top Dollar`
10. `Vetted on Real Outcomes`
11. `Personally Reviewed`
12. `Walk Away Anytime`
13. `Under 2 Minutes to Apply`
14. `Commission Transparency`
15. `It's a Seller's Market in OC`

**Descriptions (4):**
1. `Compare real estate commission rates side by side from top local agents. Free.`
2. `Get 3 to 5 personalized proposals in 24 hours with rates and marketing plans clear.`
3. `Commissions are negotiable. See what top Irvine agents offer, no obligation.`
4. `Vetted on sales volume and outcomes. Reviewed personally within 24 hours.`

**Display path:** `/Compare` / `/Commission`

---

## 8. Account / campaign-level assets

These render with every ad. Strong asset coverage = more SERP real estate = better CTR.

### Sitelinks (8, account-level)

| Link text (≤25) | Description line 1 (≤35) | Description line 2 (≤35) |
|---|---|---|
| Free Agent Proposals | 3 to 5 within 24 hours | No obligation, ever |
| How It Works | 4 steps, under 2 minutes | We do the agent search for you |
| Why Use an Agent | Sell faster, for more | Marketing + negotiation handled |
| Your Privacy First | Never sold or shared | Cancel any time |
| Irvine Market Trends | Median sale $1.48M | 35 days on market |
| Compare Commission | Rates side by side | Negotiable, not fixed |
| Vetted Local Agents | Top of their market | Sales volume + outcomes |
| Real Client Outcomes | $23,250 credit negotiated | $20,000 off asking price |

All sitelinks → Final URL `https://drozq.com/`. (Optional polish in week 4: build dedicated `/how-it-works/` `/privacy/` anchored sections and re-point sitelinks to anchors. Privacy already exists at `/privacy/`.)

### Callouts (10, account-level, ≤25 each)

```
Free & No Commitment
3-5 Proposals in 24 Hrs
Commission Transparency
Top Local Agents
Reviewed Personally
Licensed CA DRE #02267255
Vetted on Track Record
Local Irvine Experts
Walk Away Anytime
Under 2 Minutes to Apply
```

### Structured snippets (2, account-level)

**Snippet A:** Header = `Services`
Values (≤25 each):
```
CMA
Professional Photography
Virtual Tours
Staging
Open Houses
Marketing
Negotiation
Paperwork
```

**Snippet B:** Header = `Neighborhoods`
Values:
```
Irvine
Newport Beach
Tustin
Costa Mesa
Lake Forest
Mission Viejo
Aliso Viejo
Orange County
```

### Call asset (account-level)

| Field | Value |
|---|---|
| Phone | `(949) 438-5948` (the paid-traffic / call-tracking line; matches site header) |
| Country | United States |
| Call reporting | ON (uses Google forwarding number) |
| Conversion action | Create a separate `Phone call from ads (45s+)` conversion, mark Secondary (not for bidding) |
| Schedule | Mon-Sun, 7am-9pm PT |

### Lead form asset

**OFF.** Sending submissions through the on-page funnel preserves `gclid`, PostHog drop-off events, and `lead_confirmed`. A native Google lead form bypasses all three.

### Image assets (4 minimum, ideally 8: half landscape 1.91:1, half square 1:1)

Upload from `/media/images/`:

- Hero aerial of Irvine / Southern California neighborhood (already on the site, see `<img alt="Aerial view of Southern California neighborhood served by Joshua Guerrero, Irvine listing agent">`)
- Drozq logo (square + horizontal lockup)
- Irvine-skyline or recognizable OC landmark
- Professional headshot (Waist.png exists in repo, use the cleanest crop)
- Stylized "compare proposals" mockup (3 cards with name/commission redacted)
- A genuine real-home shot from a past listing if rights permit (or a tasteful stock with watermark allowed)

**Avoid:** any image with text overlay, blurry/poorly cropped images, GIFs, logo overlays. Google rejects these.

### Business name

Try `Drozq` first (matches the URL drozq.com). If Google rejects on verification, fall back to `Joshua A Guerrero` (the verified advertiser name).

### Business logo

Square Drozq logo, 1:1, minimum 128 x 128 px.

### Promotion / Price / App assets

Not applicable. Skip.

---

## 9. Tracking (sanity-checks before going live)

1. **Auto-tagging ON.** Settings → Account settings.
2. **Final URL suffix** (campaign-level) set as in §2. ValueTrack placeholders populate at click.
3. **GA4 ↔ Google Ads link** active. `generate_lead` imports as a conversion. Marked Primary for this campaign's Leads goal.
4. **Pre-launch live test.** Click a preview ad through to drozq.com. Confirm:
   - `gclid=` lands in the URL on first hit.
   - PostHog records `funnel_open` when you click Compare Agents.
   - Submitting reaches `/thank-you/?ref=funnel`.
   - GA4 DebugView shows `lead_confirmed` fired once.
   - Google Ads conversion column eventually credits the click (1 to 48 hr lag is normal).
5. **The GTM trigger fix** in §1 is the gate for Phase 2 tCPA. Until then, optimize on Max Conversions only.

---

## 10. Launch sequence (run top to bottom)

1. Pre-flight items §1 complete.
2. Create the shared negative list `Negatives | Sellers Funnel` in Shared Library. Paste the full block from §5.
3. Create the campaign with §2 settings. **Do NOT enable yet.** Save as draft.
4. Attach the shared negative list to the campaign.
5. Add campaign-level negatives from §5.
6. Build AG1, AG2, AG3, AG4 with keyword lists from §4 and display paths from §7.
7. Build one RSA per ad group with the full headline/description set from §7. Pin only Headlines #1 and #2 per ad group.
8. Add account-level assets from §8 (sitelinks, callouts, structured snippets, call, images, business name, logo).
9. Set audience signals as Observation per §6.
10. Final URL suffix per §2. Confirm auto-tagging ON.
11. Add IP exclusions (§1 item 4).
12. Enable the campaign. Watch the first 100 clicks.

---

## 11. Phase 1 → Phase 2 optimization plan

### Phase 1 (week 0 to ~30 conversions, est. 14 to 21 days at $150/day)

Goal: seed Smart Bidding with clean conversion signal, surface the real CPL, harvest negative keywords.

Daily for the first 5 days, then every 2-3 days:
- **Search Terms Report.** Tools → Insights and reports → Search terms. Tag every irrelevant term as a negative on the spot. Add to the shared list if applicable across both seller campaigns; campaign-level if specific.
- **Auction Insights.** Note who is competing (Redfin, HomeLight, UpNest, Ideal Agent, local team brokerages). Add their brand terms to negatives (already in §5; add any new ones).
- **Quality Score per keyword.** If any keyword is QS < 5, audit landing-page relevance and click-through rate.

End of Phase 1 checklist:
- 15 to 30 `generate_lead` conversions accumulated.
- GTM trigger fix landed (§1).
- CPL stabilized (5-day rolling).

### Phase 2 (Target CPA)

1. Switch bidding from `Maximize Conversions` to `Target CPA`. Set target at **1.2 × observed CPL** from Phase 1.
2. Add the **second RSA per ad group** (rotate copy, swap the secondary proof headline).
3. **Layer bid adjustments on audience Observation segments** that converted at ≥1.5x baseline: bump +20%.
4. **Location bid adjustments:** +20% on Irvine and Newport Beach; +10% on Tustin and Costa Mesa; baseline elsewhere.
5. **Dayparting:** review hour-of-day report. Most real-estate seller conversions skew weeknights 5-9pm PT and Saturday mornings. Bid-adjust +15% in those windows after 21 days of data.
6. **Test AI Max** in a Google Ads Experiment on AG1 only. 50/50 split, 21 days, measure CPL delta. Adopt only if CPL drops ≥10% with conversions held flat.
7. **Test Broad match** in AG1 and AG3 only, in a separate Experiment, after the negative list has 100+ entries.
8. **N-gram analysis on search terms (week 6+).** Export 90 days of search terms. Group by 1, 2, 3-word stems. Promote winning new variants into Exact in their respective ad groups. Demote losers to negatives.

---

## 12. Budget reality check (Irvine real estate seller search)

| Assumption | Value |
|---|---|
| Avg CPC (Exact, seller-intent, Irvine) | $8 to $14 |
| LP submit rate (max-intent click → form submit) | 5 to 10% |
| Expected CPL (Phase 1) | $100 to $250 |
| Conversions needed to seed tCPA | 15 to 30 |
| Phase 1 spend to seed | $1,500 to $7,500 |
| Recommended daily budget for ~21-day Phase 1 | **$150/day** floor, $250/day to compress |
| Time to clean Phase 2 tCPA | 14 to 21 days post-switch |

After Phase 2 stabilizes, expect CPL to **drop 20 to 35%** as Smart Bidding learns and as the negative list tightens. Re-budget then.

---

## 13. What is intentionally NOT in this campaign

- **Performance Max.** Different conversion model, different traffic mix, would muddle attribution and message match. Build a separate PMax later targeting the same audience signals if asset depth grows.
- **Brand defense ("drozq" keyword).** Separate brand campaign, $5/day, exact-only. Build after this campaign is live; do not let competitors cherry-pick brand searches.
- **Buyers and Sell & Buy funnels.** Sellers only here. The page supports those funnels and they share the LP, but ad copy and keywords for those run in their own campaigns to keep CVR clean.
- **High-painpoint sellers** (pre-foreclosure, divorce, probate, inheritance, distressed). Carved out as negatives so the next-session campaign can own them with bespoke copy and a (likely) dedicated LP.
- **Spanish-language traffic.** English-only LP. Build a Spanish campaign after a Spanish LP exists.

---

## 14. Rollback / kill switches

- Pause the entire campaign with one click if CPL spikes >3x expected.
- If Search Terms Report shows >20% irrelevant queries after 5 days, pause AG with worst signal, audit, re-launch.
- If `lead_confirmed` stops firing in GA4 DebugView for >12 hours, pause the campaign immediately. Conversion signal is dead.
- If the LP `/api/lead` MailChannels endpoint 5xx rate exceeds 2% for >1 hour, pause the campaign until the function is healthy.
