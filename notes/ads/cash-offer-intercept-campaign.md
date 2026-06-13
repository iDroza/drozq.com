# Cash-Offer Intercept Campaign (the wholesaler-competitor)

Build spec for a Google Search campaign that **intercepts the "we buy houses / sell my house fast / cash offer / sell as-is" searcher** and converts them with the equity-preservation wedge. This is the third seller lane. It is deliberately walled off from the other two:

- `sellers-max-intent-campaign.md` owns traditional intent (compare agents, home value report, commission). LP = homepage.
- `distressed-sellers-strategy.md` owns high-painpoint intent (foreclosure, divorce, probate, short sale). LP = `/relief/`.
- **This campaign owns the convenience / cash-curious seller.** LP = `/value/`.

Both existing campaigns already list `we buy houses`, `cash offer`, `sell my house fast cash`, `instant offer` as **negatives**, so this intent is currently unclaimed and waiting. This campaign claims it.

**Origin:** reverse-engineered from the Wholesaling PPC agency and its top advertisers (Property Sell Wise 74 ads, 4 Brothers 14, Dynamic Home Buyers 14, GTA House Buyers 13). Full teardown in `Downloads/wholesaling-ppc-teardown.md`. Plan per Joshua: **replicate their setup first, run a month of testing, then iterate.**

*Created: 2026-06-13.*

---

## 0. The strategy in one paragraph (read this first)

The wholesalers win the click with **speed-to-a-number** ("Get an offer in 60 seconds," "Cash offer in 7 minutes," "How much is your house worth?") and a **cash + as-is + no-fees** offer. We cannot and will not pretend to be a cash buyer (Joshua is a licensed agent, see §14). Instead we **take their exact keywords and their exact hook, and point it at a better, honest payoff**: drozq.com/value returns an *instant* valuation that shows the seller their true market value, a same-day cash-offer number, AND what they would net listing on the market. That single screen exposes the wholesaler's lowball. We use their copy structure verbatim; we swap the one claim we can't make ("we buy your house") for the one that beats it ("see what your house is really worth, then choose"). Per the distressed-sellers doc, this equity-preservation framing is "the central pitch."

### The four cohesion promises every ad MUST echo

1. **Your instant home valuation** (the `/value/` hero: "Your instant home valuation," "Estimated market value today")
2. **Cash offer AND market value, side by side** (the wedge that exposes the lowball)
3. **Keep your equity** (cash buyers pay 10 to 30% under market; list and keep the difference)
4. **Free, no obligation, on your timeline** (matches the live funnel assurance + DRE #02267255)

Anything outside those four breaks message match with `/value/`. Anything inside compounds it.

---

## 1. Pre-flight (gates clean Smart Bidding signal, do before launch)

Same gates as the max-intent campaign. Do not skip.

1. **GTM `generate_lead` trigger fix must be live** (fire on `lead_confirmed` custom event, not `/thank-you/` pageview). Until it lands, stay on Maximize Conversions; do NOT move to tCPA on inflated signal.
2. **Google Ads <-> GA4 link healthy**, `generate_lead` importing with recent counts.
3. **Auto-tagging ON** (gclid lands; the page already captures it).
4. **IP-exclude** Joshua's home/office/VPN IPs. Cash-term CPCs are high; self-clicks are expensive here.
5. **Verified advertiser** identity in place ("Joshua A Guerrero"); submit "Drozq" as business-name asset.
6. **Confirm `/value/` is the funnel-synced Sell mode** and that an address submit fires `generate_lead` with `funnel_mode=sell`. (It opens the Sell funnel via `openFunnel(address,"sell")`.)

---

## 2. Campaign settings

| Field | Value |
|---|---|
| **Campaign name** | `Search \| Sellers \| Cash-Offer-Intercept \| Irvine+OC` |
| **Goal** | Leads |
| **Type** | Search |
| **Conversion goals** | `Leads` only. Account-default `generate_lead` Primary. Everything else Secondary. (Segmentation by campaign is automatic in Ads; optional dedicated conversion in §11 iteration.) |
| **Networks** | Search: ON. **Search Partners: OFF. Display Expansion: OFF.** |
| **Locations (Presence, NOT Interest)** | "People in or regularly in your targeted locations" |
| **Location targets** | Irvine; Tustin; Newport Beach; Costa Mesa; Lake Forest; Mission Viejo; Aliso Viejo; Laguna Hills; Laguna Niguel; Orange; Yorba Linda; Rancho Santa Margarita; Ladera Ranch; Dana Point; Santa Ana; Anaheim; Huntington Beach; Fountain Valley; Garden Grove; Westminster. (Broader than max-intent: cash/fast intent skews to a wider, less-luxury slice of OC. Add ZIPs 92807/92808 Anaheim Hills; 92610 Foothill Ranch.) |
| **Languages** | English only. |
| **Audiences** | Observation, NOT Targeting. See §6. |
| **Devices** | All, no adjustment at launch. (Expect mobile-heavy; cash-seller traffic is ~70% mobile.) |
| **Ad rotation** | Optimize. |
| **Bidding** | Phase 1 (week 0 to ~30 conv): **Maximize Conversions**, no cap. Phase 2: **Target CPA** at ~1.2x observed CPL. |
| **Daily budget** | **$120/day** floor. Cash terms in SoCal run $20 to $55 CPC; at ~$35 CPC and ~8% lead rate, expected CPL ~$440. $120/day x ~21 days seeds ~5 to 7 conv/wk. Compress to $200/day to reach Phase 2 faster. |
| **Final URL suffix** | `utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_content={creative}&utm_term={keyword}&utm_matchtype={matchtype}` |
| **Start/end** | ASAP after pre-flight. No end date. |

Final URL for every ad group: **`https://drozq.com/value/`**

---

## 3. Ad group structure (mirrors the wholesalers' four ad themes)

Reverse-engineered from their accounts: they cluster ads into (1) cash/we-buy-houses, (2) sell-fast, (3) as-is/any-condition, (4) cash-offer-for-house. We mirror it exactly, theme-per-ad-group, geo via keyword + `{LOCATION(City)}` insertion.

| Ad group | Intercepts their theme | Their hook we're swiping | `/value/` anchor |
|---|---|---|---|
| `AG1 \| We-Buy-Houses` | "we buy houses [city]," "cash home buyers" | "We Buy Houses, Any Condition" | "Estimated market value today" |
| `AG2 \| Sell-My-House-Fast` | "sell my house fast [city]" | "Sell Your House Fast, 7 Days" | "Your instant home valuation" |
| `AG3 \| Sell-As-Is` | "sell my house as is," "no repairs" | "Sell As-Is, We Pay Closing" | cash-offer + fix-and-list upside |
| `AG4 \| Cash-Offer-For-House` | "cash offer for my house" | "Get a Fair Cash Offer Today" | cash offer vs. market spread |

Display paths per ad group below in §7.

---

## 4. Keywords per ad group

**Match-type policy at launch:** Exact-heavy + small Phrase. NO Broad until the negative list is locked and Phase 2 is live (then test Broad in AG1/AG2 only). Notation: `[exact]`, `"phrase"`.

### AG1 - We-Buy-Houses  (display path `/Irvine` `/Home-Value`)

Exact:
```
[we buy houses irvine]
[we buy houses orange county]
[cash home buyers irvine]
[cash home buyers orange county]
[companies that buy houses irvine]
[home buyers irvine]
[sell my house to investor irvine]
[we buy houses santa ana]
[we buy houses anaheim]
[we buy houses huntington beach]
[cash for houses orange county]
[house buying companies orange county]
```
Phrase:
```
"we buy houses orange county"
"cash home buyers near me"
"companies that buy houses"
"cash for my house"
```

### AG2 - Sell-My-House-Fast  (display path `/Irvine` `/Sell-Fast`)

Exact:
```
[sell my house fast irvine]
[sell my house fast orange county]
[sell house fast irvine]
[need to sell my house fast]
[sell my house quickly irvine]
[sell my home fast orange county]
[how to sell my house fast]
[sell my house fast santa ana]
[sell my house fast anaheim]
[sell my house fast huntington beach]
[sell house fast for cash orange county]
[quick house sale irvine]
```
Phrase:
```
"sell my house fast"
"sell house fast orange county"
"need to sell my house fast"
"sell my home quickly"
```

### AG3 - Sell-As-Is  (display path `/Irvine` `/Sell-As-Is`)

Exact:
```
[sell my house as is irvine]
[sell house as is orange county]
[sell my house without repairs]
[sell house any condition orange county]
[sell house that needs work irvine]
[sell my house as is for cash]
[sell ugly house orange county]
[sell fixer upper irvine]
[as is home sale orange county]
[sell my house no repairs orange county]
```
Phrase:
```
"sell my house as is"
"sell house any condition"
"sell house without repairs"
"sell house that needs work"
```

### AG4 - Cash-Offer-For-House  (display path `/Irvine` `/Cash-Offer`)

Exact:
```
[cash offer for my house irvine]
[cash offer for house orange county]
[get a cash offer on my house]
[fair cash offer for my home]
[cash offer my house irvine]
[instant cash offer house orange county]
[sell house for cash irvine]
[cash offer house santa ana]
[cash offer house anaheim]
[how much will a cash buyer pay]
```
Phrase:
```
"cash offer for my house"
"get a cash offer on my home"
"sell my house for cash"
"fair cash offer house"
```

---

## 5. Negative keywords

Create shared list **`Negatives | Cash-Offer Funnel`**. Attach to this campaign. It walls off the OTHER two campaigns and the usual junk.

### Wall off Max-Intent territory (the homepage campaign owns these)
```
compare agents
compare realtors
listing agent
best real estate agent
realtor commission
agent commission rates
home value report
free cma
what is my home worth
top listing agent
```

### Wall off Distressed territory (the /relief/ campaign owns these)
```
foreclosure
pre foreclosure
stop foreclosure
behind on mortgage
trustee sale
notice of default
short sale
underwater mortgage
divorce
probate
inherited property
sell my parents house
```

### Investor / wholesaler-side (we want SELLERS, not buyers or competitors)
```
how to wholesale real estate
wholesale real estate
cash buyers list
become a cash home buyer
real estate investor course
how to flip houses
investment property for sale
buy houses cheap
sell my house fast jobs
real estate wholesaling
```

### DIY / FSBO / won't hire
```
for sale by owner
fsbo
sell house without agent
sell my house myself
flat fee mls
flat fee listing
1 percent commission
```

### Research / not ready
```
how does selling a house work
how to sell a house
home selling process
closing costs calculator
realtor fees explained
zillow
redfin
zestimate
trulia
reddit
youtube
```

### Rentals / wrong owner type
```
rent
rental
for rent
landlord
tenant
section 8
property management
```

### Buyers (out of scope)
```
buy a home
homes for sale
houses for sale
first time home buyer
buyers agent
homes for rent
```

### Out-of-state geo (block search-network mismatch)
```
texas
florida
new york
arizona
phoenix
nevada
las vegas
georgia
chicago
ohio
columbus
```

### Brand defense (don't pay to lose / don't fund competitors)
```
opendoor
offerpad
homevestors
we buy ugly houses
homelight
ideal agent
upnest
clever real estate
```
*(Note: iBuyer brand intercept - bidding ON `opendoor`/`offerpad` with the equity wedge - is a deliberate Month-2 test, see §11. At launch we exclude them to keep QS and CPL clean.)*

### Campaign-level negatives
```
drozq jobs
drozq careers
joshua guerrero salary
agent locator login
```

---

## 6. Audience signals (Observation, NOT Targeting)

Collect data without restricting reach. Bid up winners in Phase 2.

**In-Market:** Residential Properties (For Sale); Residential Properties / Selling; Moving Services; Real Estate Services.
**Detailed Demographics:** Homeowners; Household Income all tiers (cash/fast intent is income-broad, unlike max-intent which skews top-30%); Age 35 to 64+.
**Custom segment `Cash-Curious Sellers`:** People who searched: we buy houses, sell my house fast, cash offer for my house, sell house as is, companies that buy houses, sell house for cash.
**Custom segment `iBuyer Researchers`:** People who browsed opendoor.com/sell, offerpad.com, homelight.com/simple-sale, zillow.com (sell).
**Remarketing:** `/value/` visitors who did NOT submit in 30 days (build in GA4, layer when >1,000).

**Demographic exclusions:** none at launch.

---

## 7. Ads (RSA per ad group)

One RSA per ad group at launch, all 15 headlines and 4 descriptions filled, pin only #1 and #2. Add a second RSA per ad group in week 3. **Every headline <=30 chars, every description <=90 chars (verified).** `{LOCATION(City):Irvine}` defaults to "Irvine."

### AG1 RSA - We-Buy-Houses
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `What's Your Home Really Worth?` *(pin 1)*
2. `See Your Cash Offer + Value` *(pin 2)*
3. `Don't Take a Lowball Offer`
4. `Instant Home Valuation`
5. `We Buy Houses? See Real Value`
6. `Cash Offer vs. Market Price`
7. `Sell Fast, Keep Your Equity`
8. `Sell Your {LOCATION(City):Irvine} Home As-Is`
9. `Cash Buyers Pay Less. See.`
10. `Free Home Value Report`
11. `Know Your Number First`
12. `Sell On Your Own Timeline`
13. `Orange County Home Values`
14. `A Real Offer, Not a Lowball`
15. `Reviewed by a Licensed Agent`

**Descriptions (4):**
1. `See your home's true market value and a real cash-offer number, free and instant.`
2. `Cash buyers pay 10-30% below market. See what you'd net listing it instead.`
3. `Enter your address and get your instant valuation. Keep your equity. Sell for more.`
4. `Free, no obligation, reviewed personally by a licensed Irvine agent. DRE #02267255.`

**Display path:** `/Irvine` `/Home-Value`

### AG2 RSA - Sell-My-House-Fast
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `Sell Your {LOCATION(City):Irvine} Home Fast` *(pin 1)*
2. `Cash Offer + Market Value` *(pin 2)*
3. `Sell Fast Without Selling Low`
4. `Your Instant Home Valuation`
5. `Sell On Your Timeline`
6. `Fast Sale, Full Value`
7. `See Your Cash Offer Today`
8. `Don't Leave Equity Behind`
9. `Need to Sell Fast? Start Here`
10. `Free, No-Obligation Valuation`
11. `Sell for More Than a Lowball`
12. `Skip the Cash-Buyer Discount`
13. `Top Dollar, On Your Schedule`
14. `Orange County Home Selling`
15. `Reviewed by Joshua, DRE Lic.`

**Descriptions (4):**
1. `Need to sell fast? See your instant valuation and your options before you decide.`
2. `A fast cash sale costs you 10-30%. See what you'd net listing, then choose.`
3. `Enter your address for an instant home value plus a real cash-offer number. Free.`
4. `Sell on your timeline with a licensed Irvine agent. No obligation. DRE #02267255.`

**Display path:** `/Irvine` `/Sell-Fast`

### AG3 RSA - Sell-As-Is
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `Sell Your House As-Is` *(pin 1)*
2. `See Your Cash Offer + Value` *(pin 2)*
3. `No Repairs. Keep Your Equity.`
4. `Sell {LOCATION(City):Irvine} Home As-Is`
5. `What's It Worth As-Is?`
6. `Skip Repairs, Not the Profit`
7. `Cash Offer vs. Fix-and-List`
8. `Any Condition, Real Value`
9. `Instant Home Valuation`
10. `Don't Take a Lowball Offer`
11. `Free As-Is Home Value Report`
12. `Sell On Your Own Timeline`
13. `See Both Numbers, Then Decide`
14. `Orange County As-Is Sales`
15. `Reviewed by a Licensed Agent`

**Descriptions (4):**
1. `Sell as-is and still keep your equity. See your cash offer and your list value.`
2. `Repairs not required. See what your home is worth as-is vs. fixed up, instantly.`
3. `Enter your address for an instant valuation and a real cash-offer number. Free.`
4. `A licensed Irvine agent, reviewed personally. No obligation. DRE #02267255.`

**Display path:** `/Irvine` `/Sell-As-Is`

### AG4 RSA - Cash-Offer-For-House
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `Get a Real Cash Offer` *(pin 1)*
2. `Cash Offer vs. Market Value` *(pin 2)*
3. `See Both Before You Sell`
4. `What's Your Home Worth?`
5. `Don't Take the First Lowball`
6. `Cash Offer on Your {LOCATION(City):Irvine} Home`
7. `Instant Valuation + Cash Offer`
8. `Keep Your Equity`
9. `A Fair Number, Not a Lowball`
10. `Cash Buyers Pay Less. See.`
11. `Free, No-Obligation Offer`
12. `Sell On Your Own Timeline`
13. `Know Your Real Number`
14. `Orange County Cash Offers`
15. `Reviewed by Joshua, DRE Lic.`

**Descriptions (4):**
1. `Get a real cash-offer number and your true market value, side by side. Free.`
2. `Most cash offers come in 10-30% under market. See the gap before you sign.`
3. `Enter your address for an instant valuation plus a cash-offer estimate. Free.`
4. `Reviewed personally by a licensed Irvine agent. No obligation. DRE #02267255.`

**Display path:** `/Irvine` `/Cash-Offer`

---

## 8. Account / campaign-level assets (mirror the wholesalers' SERP domination)

The wholesalers run a heavy sitelink + callout stack (Reviews, How It Works, We Buy Any Condition AS-IS, Get A Quote Within 60 Seconds, Get Your Cash Offer, About Us). We mirror the stack, truthful, pointed at real pages.

### Sitelinks (8, campaign-level) -> their swiped equivalent
| Link text (<=25) | Desc 1 (<=35) | Desc 2 (<=35) | Final URL |
|---|---|---|---|
| See Your Cash Offer | A real number, not a lowball | Plus your market value | /value/ |
| Instant Home Value | Your number in seconds | Free, no obligation | /value/ |
| Cash Offer vs. Market | See the gap before you sell | Keep your equity | /value/ |
| How I Sell Your Home | Five steps, six to ten weeks | More money than a lowball | /process/ |
| Real Client Outcomes | $23,250 credit negotiated | Real OC closings | /testimonials/ |
| Sell As-Is | No repairs required | See as-is vs. fixed value | /value/ |
| Meet Joshua | Licensed Irvine agent | DRE #02267255, Real Brokerage | /about/ |
| Your Privacy First | Never sold or shared | Walk away anytime | /privacy/ |

### Callouts (10, <=25 each) -> swiped from their "no fees / as-is / fast" stack, made truthful
```
Instant Home Valuation
Cash Offer + Market Value
Keep Your Equity
Sell As-Is, No Repairs
Sell On Your Timeline
Free & No Obligation
Reviewed Personally
Licensed CA DRE #02267255
Real Local Closings
A Real Offer, Not a Lowball
```

### Structured snippets (2)
**Header `Services`:** Instant Valuation; Cash Offer Comparison; As-Is Sales; Market Listing; Staging; Photography; Negotiation; Fast Close.
**Header `Neighborhoods`:** Irvine; Tustin; Santa Ana; Anaheim; Huntington Beach; Costa Mesa; Mission Viejo; Orange County.

### Call asset
| Field | Value |
|---|---|
| Phone | `(949) 438-5948` (matches site header) |
| Call reporting | ON (Google forwarding number) |
| Conversion | `Phone call from ads (45s+)`, Secondary (not for bidding) |
| Schedule | Mon-Sun 7am to 9pm PT |

### Lead form asset
**OFF.** On-page funnel preserves gclid, PostHog drop-off events, and `lead_confirmed`. A native Google lead form bypasses all three.

### Image assets (>=4)
From `/media/images/`: Southern California aerial; Drozq logo (square + horizontal); a clean OC home exterior; Joshua headshot. No text overlays, no GIFs (Google rejects).

### Business name / logo
`Drozq` (fallback `Joshua A Guerrero`); square logo 1:1 >=128px.

---

## 9. Tracking sanity checks (before enabling)

1. Auto-tagging ON.
2. Final URL suffix set (campaign-level).
3. GA4 <-> Ads link active, `generate_lead` imported Primary.
4. **Live click test:** preview ad -> `/value/`. Confirm gclid lands, PostHog fires `funnel_open` on address entry, submit reaches `/thank-you/?ref=funnel`, GA4 DebugView shows `lead_confirmed` once with `funnel_mode=sell`.
5. GTM trigger fix (the `lead_confirmed` gating) is the gate for Phase 2 tCPA.

---

## 10. Launch sequence

1. Pre-flight §1 complete.
2. Create shared negative list `Negatives | Cash-Offer Funnel` (§5).
3. Create campaign with §2 settings, save as draft (do not enable).
4. Attach shared negatives + add campaign-level negatives.
5. Build AG1 to AG4 with §4 keywords and §7 display paths. Final URL `/value/` on all.
6. Build one RSA per ad group (§7), pin only H1 and H2.
7. Add campaign-level assets (§8).
8. Set audience signals as Observation (§6).
9. Final URL suffix + auto-tagging ON + IP exclusions.
10. Enable. Watch the first 100 clicks.

---

## 11. The month-of-testing plan, then iterate (the explicit ask)

### Phase 1 = the replica month (week 0 to ~30 conversions, ~21 to 28 days at $120/day)

Goal: prove the intercept converts, surface the real SoCal cash-term CPL, harvest negatives. Run the replica as-built. **Do not touch copy mid-flight beyond adding negatives** (changing creative resets learning).

Cadence:
- **Daily first 5 days, then every 2 to 3 days: Search Terms Report.** Tag junk as negatives on the spot. Expect heavy investor/wholesaler-course and FSBO bleed; wall it fast.
- **Auction Insights:** log who shows up (the actual wholesalers from the teardown, Opendoor, Offerpad, HomeVestors, local "we buy houses" operators). 
- **Quality Score per keyword:** any QS < 5, the LP message-match is off. `/value/` should score well on valuation terms, weaker on pure "we buy houses." Note which terms drag.

End-of-Phase-1 checklist: 15 to 30 `generate_lead` conversions, GTM fix confirmed live, 5-day rolling CPL stable.

### Then iterate (Month 2+). The levers, in priority order:

1. **Kill the dead ad groups, double the winners.** If AG1 (we-buy-houses) converts at 2x the CPL of AG4 (cash-offer), cut AG1 budget and pour into AG4. Likely outcome: the **valuation-framed** groups (AG4, AG2) beat the **we-buy-houses** group, because `/value/` message-matches them and because "we buy houses" searchers self-select for the cash lane we can't fully serve.
2. **Switch to Target CPA** at 1.2x observed CPL once 30+ conversions and the GTM fix are confirmed.
3. **Swap copy by data, A/B per ad group.** Add RSA #2 per group rotating the runner-up hooks. Test the two strongest wedges head to head: *"Don't take a lowball offer"* (loss-aversion) vs. *"See your cash offer + market value"* (curiosity). Pin-test: pin the valuation hook vs. let Google optimize.
4. **Build the dedicated LP** if `/value/` underperforms on the pure "sell fast / we buy houses" terms. A `/cash-offer/` or rebuilt `/relief/`-style page whose hero is literally "See your cash offer and what you'd net listing, side by side" + address-first form (the wholesalers' exact funnel shape). Re-point AG1/AG2 to it, keep AG4 on `/value/`. Measure CVR delta.
5. **iBuyer brand intercept test (Experiment).** Bid on `opendoor` / `offerpad` / `sell to opendoor` with "See what Opendoor pays vs. market" copy. Separate ad group, tight budget, watch QS and policy. High-value if it clears.
6. **Geo split if CPCs diverge.** If Santa Ana/Anaheim cash terms are half the CPC of Irvine/Newport, split into per-city ad groups (the wholesalers do this) so budget follows the cheap, high-intent metros.
7. **Add a dedicated conversion** `generate_lead_cash` (GA4 event with `funnel_mode` + campaign param) so Smart Bidding optimizes this lane independently of the homepage home-value group.
8. **Layer bid adjustments** on the audience Observation segments and dayparts that converted >=1.5x baseline.
9. **N-gram the search terms at week 6+.** Promote winning new stems to Exact; demote losers to negatives.

### Replica-vs-iterate scorecard (what "working" looks like)
| Metric | Phase 1 (replica) target | Post-iteration target |
|---|---|---|
| CPC (blended, SoCal cash terms) | $20 to $55 | $18 to $40 |
| LP submit rate (`/value/`) | 6 to 10% | 10 to 14% |
| CPL | $300 to $550 | $200 to $400 |
| Conversions / week | 5 to 8 | 12 to 20 |
| Cost per listing taken | justify vs. a $20k+ OC commission | the whole point |

---

## 12. Budget reality (SoCal cash-term search)

| Assumption | Value |
|---|---|
| Avg CPC ("we buy houses / cash offer," OC) | $20 to $55 (higher than max-intent's $8 to $14) |
| LP submit rate (`/value/`) | 6 to 10% |
| Expected CPL Phase 1 | $300 to $550 |
| Conversions to seed tCPA | 15 to 30 |
| Phase 1 spend to seed | ~$4,500 to $12,000 |
| Recommended daily | **$120/day** floor, $200/day to compress |

This lane is more expensive per lead than the homepage campaign. It is justified two ways: (a) it intercepts sellers the homepage campaign deliberately excludes (incremental, not cannibalized), and (b) one OC listing commission (~2.5% of a ~$1M+ median = $25k+) dwarfs the per-deal economics the wholesalers survive on ($3k to $8k cost per deal for a $10k to $15k assignment fee). Joshua can outbid them on their own keywords and still hand the seller more money.

---

## 13. The swipe map (their copy -> Joshua's, 1:1)

This is the "use all their copy" deliverable. Left = verbatim from the teardown. Right = the truthful Joshua line we run, same psychology, legal for an agent.

| Their line (verbatim) | Our swiped line | Why it still wins |
|---|---|---|
| "How Much Is Your House Worth?" | "What's Your Home Really Worth?" | Same curiosity hook; we actually return the number on `/value/` |
| "Get An Offer Within 60 Seconds" | "Your Instant Home Valuation" | Same speed promise, on a real on-page result (not an unkept email promise) |
| "Cash Offer In 7 Minutes. Simple Process." | "See Your Cash Offer + Value" | We show a cash-offer number AND the market number |
| "We'll Buy Your [State] House" | "Sell Your [City] Home Fast" | We can't say "we'll buy"; "sell your home fast" is true and matches intent |
| "We'll Beat Any Serious Offers" | "Don't Take a Lowball Offer" | Reframes the same competitiveness as equity protection |
| "We Pay Cash For All Kinds Of Properties. Any Condition." | "Sell As-Is. No Repairs. Keep Your Equity." | Same as-is promise, plus the equity wedge they can't match |
| "Don't Fix It Sell It" | "Skip Repairs, Not the Profit" | Same effort-reduction, adds the value angle |
| "No Commitment Or Pressure" | "Free, No Obligation" | Keep the cost-concern reassurance; drop "pressure" (house style bans naming it) |
| "Skip Agents And Sell Direct" | "Cash Offer vs. Market Value" | Flips their anti-agent jab into the comparison that exposes the lowball |
| "Boston #1 Home Buyers. A+ BBB." | "Reviewed by a Licensed Agent. DRE #02267255." | Real, verifiable authority instead of self-proclaimed rank |
| "Get Your Cash Offer" (sitelink) | "See Your Cash Offer" (sitelink) | One word: we show it, we don't make it |
| "We Buy Any Condition, AS-IS" (sitelink) | "Sell As-Is" (sitelink) | Truthful agent version |

Hooks we adopt wholesale (they're true for us): **speed-to-a-number, as-is, free/no-obligation, your-timeline, address-first.**
Hooks we invert into our advantage: **"we buy / cash buyer" -> "see your cash offer AND market value," "skip agents" -> "the agent who shows you the lowball."**

---

## 14. Compliance guardrails (non-negotiable, from Joshua's own docs)

Per `distressed-sellers-strategy.md` §10.3 and §13, and DRE/Google policy:

1. **Joshua is a licensed agent, NOT a cash buyer.** No ad may say or imply "we buy your house," "we'll pay cash for it," or that Joshua is the principal buyer. We **show** a cash-offer number and compare it to market; we never claim to **make** the purchase. ("See your cash offer," not "Get cash from us.")
2. **No "instant cash" / hard-cash claims.** Banned: "Instant cash for your house," "Cash in 24 hours," "Guaranteed cash offer." Allowed: "instant valuation" (true, on-page), "see a cash-offer estimate," "sell fast."
3. **No foreclosure-rescue framing** (that intent belongs to `/relief/` anyway and is negatived here). Banned: "stop the bank," "save your home." 
4. **DRE #02267255 + licensed-agent disclosure** present in copy/assets and on `/value/` (already there).
5. **Solo voice.** "I" / "Joshua," never "our agents / our team." Fineprint: "we may contact you."
6. **No exposing the plumbing.** The valuation is "my own valuation model," never "API/Rentcast/automated."
7. **No em dashes** (house rule). **No anti-promise copy** beyond the accepted cost-concern set ("free / no obligation / walk away anytime"); never "no pressure / no spam / no autodialer / no sales pitch."
8. **Flag unbacked promises.** The `/value/` funnel currently says report + playbooks "hit your inbox the instant you submit." If the auto-delivery isn't wired end-to-end (open backlog item), keep ad copy to the on-screen instant result ("see your number instantly") and get the email delivery built before scaling spend, so paid traffic never hits a broken promise.

---

## 15. What is intentionally NOT in this campaign / kill switches

**Not included:** Performance Max (pollutes attribution + message match); Broad match at launch; iBuyer brand bidding at launch (Month-2 test); buyers; Spanish (no Spanish LP); distressed terms (the `/relief/` campaign owns them).

**Kill switches:**
- Pause instantly if CPL spikes >3x expected ($550 -> $1,650).
- If Search Terms shows >25% investor/FSBO/wholesale-course bleed after 5 days, pause the worst ad group, wall it, relaunch.
- If `lead_confirmed` stops firing in GA4 DebugView >12h, pause the campaign (conversion signal dead).
- If `/api/lead` 5xx rate >2% for >1h, pause until the function is healthy.
- If Google disapproves ads for "unreliable claims" or "misrepresentation," it is the cash-buyer line creeping in. Re-check against §14 and resubmit with the valuation framing.
