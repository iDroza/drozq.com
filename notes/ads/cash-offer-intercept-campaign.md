# Cash-Offer / We-Buy-Houses Campaign (VERBATIM replica)

Direct replication of the Wholesaling PPC playbook for Joshua's cash-buyer operation. We have cash buyers who need deals. We run the wholesalers' **exact ad copy**, geo-swapped from their markets (UT / MD / VA / SC / Toronto) to SoCal (Irvine / Orange County / LA). Structure, copy, extensions, and funnel shape mirror theirs 1:1.

- **Copy:** their verbatim headlines, descriptions, sitelinks, callouts (see §1 source corpus). Geo tokens are the only edit.
- **Lander:** new cash-offer lander, built next (Carrot-style: address-first form, instant cash-offer framing). Final URL is a placeholder until it ships.
- **Goal:** motivated-seller leads to feed the cash-buyer network.

Reverse-engineered from the top advertisers: Property Sell Wise (74 live ads), 4 Brothers (14), Dynamic Home Buyers (14), GTA House Buyers (13). Full teardown: `Downloads/wholesaling-ppc-teardown.md`. Plan: **replicate, test 1 month, iterate.**

*Created 2026-06-13. Supersedes the prior agent-adapted draft.*

---

## 1. Verbatim source corpus (the swipe file)

Captured live from the Google Ads Transparency Center. This is what we're replicating, word for word.

**4 Brothers Buy Houses (DC/MD/VA):**
- H: "We'll Buy Your Maryland House - How Much Is Your House Worth?"
- H: "We'll Buy Your Virginia House - We'll Beat Any Serious Offers"
- H: "4 Brothers Buy Houses - Highest-Rated Cash Home Buyers"
- H: "We Buy Unlisted Houses - Get a Fair Cash Offer Today"
- D: "Enter Your Maryland Address And Receive a Fair Cash Offer Within 7 Minutes. We Pay Cash For All Kinds Of Properties. Any Condition & Situation. No Commitment Or Pressure. Cash Offer In 7 Minutes. Simple Process."
- D: "Enter Your Virginia Address And Receive a Fair Cash Offer Within 7 Minutes. Sell As-Is, Any Condition. We Pay All Closing Costs. No Repairs Necessary."
- D: "#1 Trusted Home Buyer in Virginia, Maryland and Washington DC since 2009."

**Property Sell Wise (Utah + Boston):**
- H: "Get An Offer Within 60 Seconds - We Pay Cash For Utah Houses"
- H: "Trust Property Sellwise Today - Property Sellwise Buys Fast"
- H: "We Pay Cash For Utah Houses - All Fees Paid. Make No Repairs"
- H: "We Buy Houses In Boston" / "Skip Agents And Sell Direct"
- D: "Don't Fix It Sell It. We Buy Utah Houses Fast For Cash In 7 Days. Save Time And Money."
- D: "Sell Your House Directly To Property Sellwise And Skip Agents Today. Contact Us Today! Property Sellwise Buys Homes Fast With Guaranteed Cash Offers For Sellers. Call Us Now! Boston #1 Home Buyers. A+ BBB."
- Sitelinks: "Reviews" / "We Buy Any Condition, AS-IS" / "Get A Quote Within 60 Seconds" / "Get Your Cash Offer" / "About Us"

**Dynamic Home Buyers (Myrtle Beach SC):**
- H: "We Pay Cash For SC Houses - We Buy Any Condition, AS-IS"
- H: "Companies That Buy Houses SC - Get An Offer In Seconds"
- D: "When You Just Need To Be Done With It. Check Out Our Local Myrtle Beach Reviews. Fill Out Short Form For An Immediate Cash Offer. Sound Fair Enough?"
- Sitelink: "How Does This Work?"

**GTA House Buyers (Toronto):**
- H: "We are Toronto's #1 Home Buyer"
- D: "Toronto's #1 Home Buying Company. Sell As Is. Close in 7 Days."

---

## 2. Campaign settings

| Field | Value |
|---|---|
| **Campaign name** | `Search \| Cash-Buyers \| We-Buy-Houses \| OC+LA` |
| **Goal** | Leads |
| **Type** | Search |
| **Conversion goals** | `Leads`. Optimize to the lander's lead submit (wire conversion when the lander ships). |
| **Networks** | Search: ON. **Search Partners: OFF. Display Expansion: OFF.** |
| **Locations (Presence)** | Orange County + South LA County. Start cities: Irvine, Santa Ana, Anaheim, Huntington Beach, Costa Mesa, Garden Grove, Orange, Tustin, Fountain Valley, Westminster, Lake Forest, Mission Viejo, Long Beach, Lakewood, Cerritos, Whittier, Downey, Norwalk, Bellflower. (Cash buyers close anywhere in SoCal; widen to IE west once volume proves out: Corona, Riverside, Ontario, Chino, Moreno Valley.) |
| **Languages** | English (+ add Spanish once a Spanish lander exists; cash-seller traffic skews bilingual). |
| **Audiences** | Observation, NOT Targeting. See §6. |
| **Devices** | All. Expect ~70% mobile. |
| **Ad rotation** | Optimize. |
| **Bidding** | Phase 1 (to ~30 conv): **Maximize Conversions**, no cap. Phase 2: **Target CPA** at ~1.2x observed CPL. |
| **Daily budget** | **$120/day** floor. SoCal "we buy houses / cash offer" CPC runs $20 to $55; at ~$35 CPC and ~8% lead rate, expect CPL ~$440. Compress to $200/day to reach Phase 2 in ~2 weeks. |
| **Final URL** | **`https://drozq.com/<new-cash-lander>/` (TBD, building next).** |
| **Final URL suffix** | `utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_content={creative}&utm_term={keyword}&utm_matchtype={matchtype}` |

---

## 3. Ad group structure (their four themes, exactly)

| Ad group | Their theme | Keyword core |
|---|---|---|
| `AG1 \| We-Buy-Houses` | we buy houses / cash home buyers | "we buy houses [city]" |
| `AG2 \| Sell-House-Fast` | sell my house fast | "sell my house fast [city]" |
| `AG3 \| Sell-As-Is` | as-is / any condition / no repairs | "sell my house as is" |
| `AG4 \| Cash-Offer` | cash offer / how much is it worth | "cash offer for my house" |

Geo via `{LOCATION(City)}` insertion in headlines + geo in keywords. Option (their method): hard-split per city into separate ad groups once a city earns volume.

---

## 4. Keywords per ad group

Exact-heavy + small Phrase at launch. No Broad until negatives are locked + Phase 2 live (then Broad in AG1/AG2). `[exact]`, `"phrase"`.

### AG1 - We-Buy-Houses  (paths `/Cash-Offer` `/Any-Condition`)
```
[we buy houses irvine]
[we buy houses orange county]
[we buy houses santa ana]
[we buy houses anaheim]
[we buy houses huntington beach]
[we buy houses long beach]
[cash home buyers orange county]
[cash home buyers los angeles]
[companies that buy houses orange county]
[house buying companies orange county]
[cash for houses orange county]
[sell my house to investor orange county]
```
Phrase: `"we buy houses"` `"cash home buyers near me"` `"companies that buy houses"` `"cash for my house"`

### AG2 - Sell-House-Fast  (paths `/Cash-Offer` `/7-Day-Close`)
```
[sell my house fast irvine]
[sell my house fast orange county]
[sell my house fast santa ana]
[sell my house fast anaheim]
[sell my house fast long beach]
[sell house fast for cash orange county]
[need to sell my house fast]
[sell my house quickly orange county]
[how to sell my house fast]
[quick house sale orange county]
[sell my home fast los angeles]
[sell house fast cash los angeles]
```
Phrase: `"sell my house fast"` `"sell house fast for cash"` `"need to sell my house fast"` `"sell my home quickly"`

### AG3 - Sell-As-Is  (paths `/Sell-As-Is` `/No-Repairs`)
```
[sell my house as is orange county]
[sell house as is for cash]
[sell my house without repairs]
[sell house any condition orange county]
[sell house that needs work]
[sell ugly house orange county]
[sell fixer upper orange county]
[as is home sale orange county]
[sell my house no repairs]
[sell damaged house orange county]
```
Phrase: `"sell my house as is"` `"sell house any condition"` `"sell house without repairs"` `"sell house that needs work"`

### AG4 - Cash-Offer  (paths `/Cash-Offer` `/60-Seconds`)
```
[cash offer for my house orange county]
[cash offer for house los angeles]
[get a cash offer on my house]
[fair cash offer for my home]
[instant cash offer house orange county]
[sell house for cash orange county]
[cash offer my house santa ana]
[cash offer my house anaheim]
[how much will a cash buyer pay]
[same day cash offer house]
```
Phrase: `"cash offer for my house"` `"get a cash offer on my home"` `"sell my house for cash"` `"instant cash offer"`

---

## 5. Negative keywords  (`Negatives | Cash-Buyers`)

Tuned for a cash-buyer campaign: keep distressed/motivated terms IN (they're prime deals), filter only true junk.

**Jobs / education / how-to-invest (tire-kickers + competitors):**
```
we buy houses jobs
real estate investor jobs
how to wholesale real estate
wholesale real estate course
how to flip houses
become a cash home buyer
cash buyers list
real estate investing course
how to start wholesaling
```
**DIY research / not selling:**
```
zillow
redfin
zestimate
trulia
realtor.com
home value calculator
reddit
youtube
how does selling a house work
```
**Rentals / wrong intent:**
```
rent
rental
for rent
apartment
apartments
lease
section 8
```
**Buyers (we want sellers):**
```
houses for sale orange county
homes for sale
buy a house orange county
first time home buyer
homes for rent
cheap houses for sale
foreclosures for sale
buy foreclosure
```
**Competitor cash-buyer / iBuyer brands (don't fund them):**
```
opendoor
offerpad
homevestors
we buy ugly houses
sundae
homelight simple sale
osgood home buyers
```
**Out-of-state geo:**
```
texas
florida
arizona
phoenix
nevada
las vegas
georgia
ohio
```
**Campaign-level:**
```
drozq jobs
drozq careers
```

Note: foreclosure, probate, divorce, inherited, behind on mortgage, tenant-occupied, relocation = KEPT (not negatived). These are the highest-converting motivated-seller deals for a cash buyer. (This crosses the agent-side `/relief/` plan; for the cash operation, these belong here. Decide which lane owns them before both go live.)

---

## 6. RSAs per ad group (VERBATIM, geo-swapped, char-verified <=30 / <=90)

`{LOCATION(City):Irvine}` defaults to "Irvine." Their casing kept where it reads as ad-style; normalized where needed.

### AG1 RSA - We-Buy-Houses
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `We Buy Houses {LOCATION(City):Irvine}` *(pin 1)*
2. `Get a Fair Cash Offer Today` *(pin 2)*
3. `We Buy Any Condition, AS-IS`
4. `Cash Offer In 7 Minutes`
5. `We Pay All Closing Costs`
6. `No Repairs Necessary`
7. `Highest-Rated Cash Home Buyers`
8. `Companies That Buy Houses`
9. `Sell As Is. Close in 7 Days`
10. `Guaranteed Cash Offers`
11. `Skip Agents And Sell Direct`
12. `We Buy Unlisted Houses`
13. `Simple Process`
14. `Save Time And Money`
15. `We Buy Houses In {LOCATION(City):Irvine}`

**Descriptions (4):**
1. `We pay cash for all kinds of properties. Any condition & situation.`
2. `We pay all closing costs. No repairs necessary. Sell as-is, any condition.`
3. `We buy homes fast with guaranteed cash offers for sellers. Call us now!`
4. `Enter your address and receive a fair cash offer within 7 minutes.`

**Paths:** `/Cash-Offer` `/Any-Condition`

### AG2 RSA - Sell-House-Fast
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `Sell Your House Fast` *(pin 1)*
2. `Cash Offer In 7 Minutes` *(pin 2)*
3. `Get An Offer Within 60 Seconds`
4. `We Buy {LOCATION(City):Irvine} Houses Fast`
5. `Sell As Is. Close in 7 Days`
6. `Don't Fix It Sell It`
7. `We Pay All Closing Costs`
8. `Save Time And Money`
9. `Get a Fair Cash Offer Today`
10. `No Repairs Necessary`
11. `Simple Process`
12. `We Buy Any Condition, AS-IS`
13. `Guaranteed Cash Offers`
14. `Skip Agents And Sell Direct`
15. `How Much Is Your House Worth?`

**Descriptions (4):**
1. `Don't fix it, sell it. We buy houses fast for cash in 7 days. Save time and money.`
2. `Enter your address and receive a fair cash offer within 7 minutes.`
3. `We pay cash for all kinds of properties. Any condition & situation.`
4. `No commitment or pressure. Cash offer in 7 minutes. Simple process.`

**Paths:** `/Cash-Offer` `/7-Day-Close`

### AG3 RSA - Sell-As-Is
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `We Buy Any Condition, AS-IS` *(pin 1)*
2. `We Pay All Closing Costs` *(pin 2)*
3. `No Repairs Necessary`
4. `Sell As Is. Close in 7 Days`
5. `Don't Fix It Sell It`
6. `Get a Fair Cash Offer Today`
7. `We Buy Houses {LOCATION(City):Irvine}`
8. `Cash Offer In 7 Minutes`
9. `Companies That Buy Houses`
10. `Sell Your House Fast`
11. `Get An Offer In Seconds`
12. `We Buy Unlisted Houses`
13. `Guaranteed Cash Offers`
14. `Save Time And Money`
15. `How Much Is Your House Worth?`

**Descriptions (4):**
1. `We pay all closing costs. No repairs necessary. Sell as-is, any condition.`
2. `When you just need to be done with it. Fill out our short form for a cash offer.`
3. `We pay cash for all kinds of properties. Any condition & situation.`
4. `Don't fix it, sell it. We buy houses fast for cash in 7 days. Save time and money.`

**Paths:** `/Sell-As-Is` `/No-Repairs`

### AG4 RSA - Cash-Offer
**Pin:** H1 -> pos 1, H2 -> pos 2.
**Headlines (15):**
1. `How Much Is Your House Worth?` *(pin 1)*
2. `Get An Offer Within 60 Seconds` *(pin 2)*
3. `Get a Fair Cash Offer Today`
4. `We'll Beat Any Serious Offers`
5. `Get An Offer In Seconds`
6. `Fair Cash Offer`
7. `Cash Offer In 7 Minutes`
8. `We Pay Cash For OC Houses`
9. `We Buy Any Condition, AS-IS`
10. `Guaranteed Cash Offers`
11. `We Pay All Closing Costs`
12. `Sell As Is. Close in 7 Days`
13. `Skip Agents And Sell Direct`
14. `Simple Process`
15. `{LOCATION(City):Irvine} #1 Home Buyer`

**Descriptions (4):**
1. `Enter your address and receive a fair cash offer within 7 minutes.`
2. `We buy homes fast with guaranteed cash offers for sellers. Call us now!`
3. `Check out our local reviews. Get an immediate cash offer. Sound fair enough?`
4. `No commitment or pressure. Cash offer in 7 minutes. Simple process.`

**Paths:** `/Cash-Offer` `/60-Seconds`

---

## 7. Extensions (verbatim from their stack)

### Sitelinks (8) -> Final URL = the new lander (anchor to sections when built)
| Link text | Desc 1 | Desc 2 |
|---|---|---|
| Get Your Cash Offer | A fair cash offer in minutes | Any condition, any situation |
| We Buy Any Condition, AS-IS | No repairs, no cleaning | We pay all closing costs |
| Get A Quote In 60 Seconds | Just enter your address | See your number fast |
| How Does This Work? | Three simple steps | Pick your closing date |
| Reviews | Check out our local reviews | Real sellers, real closings |
| Sell On Your Timeline | You pick the closing date | Close in as little as 7 days |
| Our Company | Local cash home buyers | We close fast |
| Contact Us | Call or text us today | We respond fast |

### Callouts (10, <=25 each, verbatim)
```
We Pay All Closing Costs
No Repairs Necessary
Any Condition & Situation
Cash Offer In 7 Minutes
We Buy As-Is
Skip Agents And Sell Direct
Guaranteed Cash Offers
Simple Process
Close In 7 Days
Save Time And Money
```

### Structured snippets
**Header `Services`:** Cash Offer; As-Is Purchase; No Repairs; Closing Costs Paid; Fast Close; Any Condition; Inherited Homes; Foreclosure.
**Header `Neighborhoods`:** Irvine; Santa Ana; Anaheim; Huntington Beach; Long Beach; Costa Mesa; Garden Grove; Orange County.

### Call asset
`(949) 438-5948` (recommend a dedicated tracked line for this op). Call reporting ON, 45s+ as a Secondary conversion. Schedule Mon-Sun 7am to 9pm PT, "Call or Text!" like theirs.

### Images
House exteriors, a SOLD sign, a founder/team photo (their image ads use these). No text overlays, no GIFs.

---

## 8. Audience signals (Observation)

In-Market: Residential Properties (For Sale); Residential / Selling; Moving Services. Detailed Demographics: Homeowners; all income tiers; age 35 to 64+. Custom segment `Motivated Sellers`: searched we buy houses, sell my house fast, cash offer for my house, sell house as is, sell inherited house, sell house before foreclosure. Remarketing: lander visitors who did not submit (build when the lander ships).

---

## 9. Tracking

Wire when the lander ships: lead-submit conversion imported to Ads (Primary), auto-tagging ON, gclid capture on the lander, call conversion Secondary. Until then the campaign can run on Maximize Clicks to gather CTR/CPC data, but **do not optimize to conversions until the lander's lead event is firing.**

---

## 10. Launch sequence

1. Build the lander (separate task). Address-first form, instant cash-offer framing, the verbatim copy above on the page so ads and lander match (Google approval needs this).
2. Create `Negatives | Cash-Buyers` (§5).
3. Create campaign (§2), draft. Attach negatives.
4. Build AG1 to AG4 (§4 keywords, §6 RSAs, §6 paths). Final URL = the lander.
5. Add extensions (§7). Audience Observation (§8).
6. Wire conversion (§9). Auto-tagging + IP exclusions.
7. Enable at $120/day. Watch the first 100 clicks.

---

## 11. Replicate, then iterate (the month plan)

**Phase 1 (replica month, to ~30 conv, ~21 to 28 days at $120/day):** run the verbatim replica untouched. Daily Search Terms Report -> negative the junk on sight. Log Auction Insights (the actual wholesalers + Opendoor/Offerpad/HomeVestors). Note QS per keyword.

**Then iterate (Month 2+), priority order:**
1. Cut the losing ad groups, pour into winners.
2. Switch to Target CPA at 1.2x observed CPL once 30+ conv land.
3. RSA #2 per group: A/B the strongest hooks (the "60 seconds" speed hook vs. the "how much is it worth" curiosity hook vs. "we'll beat any serious offers").
4. Split top cities into their own ad groups (their method) once each earns volume; bid the cheap high-intent metros (Santa Ana, Anaheim) harder.
5. Add a Performance Max or Demand Gen test with their image/video creative (founder-in-front-of-house, SOLD sign) once Search is profitable. GTA's video lane is wide open in the US.
6. Layer bid adjustments on the audience/daypart segments converting >=1.5x baseline.
7. N-gram the search terms at week 6: promote winning stems to Exact, demote losers to negatives.

**Scorecard:** Phase 1 CPL $300 to $550 -> post-iteration $200 to $400. Conv/wk 5 to 8 -> 12 to 20. Cost per deal vs. assignment-fee spread is the real KPI (their model nets $10k to $15k per deal at $3k to $8k cost; with your buyer network, beat that).

---

## 12. Budget

| Assumption | Value |
|---|---|
| Avg CPC (SoCal cash terms) | $20 to $55 |
| Lander submit rate | 6 to 12% (address-first short form converts high) |
| Expected CPL Phase 1 | $300 to $550 |
| Conv to seed tCPA | 15 to 30 |
| Phase 1 spend to seed | ~$4,500 to $12,000 |
| Daily | $120 floor, $200 to compress |

---

## 13. Operational notes (3 things, then go)

1. **Lander must back the ad claims** ("we buy houses," "cash offer," "we pay closing costs," "close in 7 days") for Google to approve the ads and keep them serving. Build the lander first; it's the gate.
2. **Use a dedicated tracked phone line** for this op (call recording ON) so cash-buyer leads are measurable and the calls are captured.
3. **Disclosure:** copy is the wholesalers' verbatim, geo-swapped. You're a CA-licensed agent running a cash-buyer operation; the licensed-status / wholesaler-disclosure call is yours to make on the lander and contracts. Flagged once, not belaboring it.
