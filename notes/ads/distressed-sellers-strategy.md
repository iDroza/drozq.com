# Distressed Sellers Strategy

Strategic plan for taking the high-painpoint seller market in Southern California: foreclosure, divorce, probate, inheritance, short sale. Companion to `sellers-max-intent-campaign.md` (which targets traditional move-up sellers and walls this lane off as negatives). The two campaigns are designed to never compete for the same query.

*Last updated: 2026-05-21.*

---

## 0. Strategic frame

This is not one market. It is five markets with different search vocabulary, emotional register, urgency, competitor field, and message-match requirements. Lumping them together kills CVR. Treating them as variants of "sellers" misses what distressed sellers actually need: ONE expert, FAST response, DISCRETION, and a legitimate alternative to predatory cash buyers.

**Joshua's positioning vs. the field:**

- **vs. cash buyers / "we buy houses" investors (Opendoor, Offerpad, local wholesalers):** they take 10 to 30% below market. Joshua lists at market and the seller keeps the equity. This is the central pitch.
- **vs. foreclosure-rescue scammers:** Joshua is a licensed agent representing a sale, not a foreclosure consultant collecting fees. Cleaner regulatory ground and a calmer, more professional voice.
- **vs. other distressed-specialty agents:** Joshua's hook is response speed (sub-5 minutes), partner network (attorneys + CPAs), and Irvine local knowledge. Most "specialists" don't pick up the phone fast.

**Ambition:** number one in Southern California for distressed-seller leads, measured by share of voice on the core query set and by closes per quarter. Realistic solo-agent ceiling: 15 to 25 distressed closes per year.

---

## 1. The lander decision

**Build `/relief/` on the same codebase.** New path, new copy, reused infrastructure.

### Reused (do not rebuild)
- CSS tokens, design variables, breakpoints, mobile-first scaffolding from index.html `<style>` block
- Funnel JS architecture (the IIFE pattern that runs Sell / Buy / Sell&Buy)
- `/functions/api/lead.js` (MailChannels + optional Zapier)
- `/thank-you/` page (with new sessionStorage flag → new confirmation copy)
- GTM container `GTM-KVV3R96P` (with new triggers and tags)
- gclid capture
- PostHog (with new event names)
- Geo personalization (visitor city replaces "Columbus, OH" defaults)
- Google Maps Places autocomplete

### New for /relief/
- Hero, proof, trust, footer copy (entirely different tone)
- A 4th funnel mode: `data-funnel="relief"` with 4 new steps and different question text
- A new `intent=Distressed Sale Inquiry` value passed to `/api/lead`
- A new sessionStorage flag `drozq_lead_mode=relief` set before `/thank-you/?ref=funnel` redirect
- A new GA4 conversion: `generate_lead_distressed` (or `generate_lead` with `funnel_mode` parameter), separately importable into Google Ads for per-segment bid optimization
- Three to five new case files written specifically for distressed situations (or anonymized real outcomes)
- `<meta name="robots" content="noindex,nofollow">` — paid-traffic-only page

### Why not the homepage
- Hero ("Compare Agents. Find a Trusted Expert.") is the literal worst message for a homeowner 14 days from foreclosure auction. Distressed sellers want ONE expert, not a marketplace.
- Funnel step 1 ("Are you looking to sell? No, just curious / Yes, immediately / Yes, in 1-3 months / Yes, 4 or more months out") asks the wrong question. Distressed sellers think in "NTS dated 6/14" terms, not vague timelines.
- "It's a seller's market in Irvine, median $1.48M" is tone-deaf for someone losing equity.
- The 5-card "agent-matching" proof block contradicts the message of "one specialist who picks up the phone."

### Why not a separate site
- Domain authority concentration
- Conversion plumbing already built and tested
- Faster to ship (~2 to 4 days vs. ~2 to 4 weeks for a fresh stack)
- One maintenance surface

---

## 2. Segment breakdown

Five distinct segments. Treat each as its own campaign (separate budgets, separate Smart Bidding pools, separate ad copy themes). All point to the same `/relief/` LP at v1; v2 introduces per-segment dynamic emphasis via URL parameter.

### Segment A: Pre-Foreclosure / Notice of Default (NOD)

**Profile.** Owner is 30 to 120 days behind on mortgage. NOD has been recorded (public record, available from county recorder). High urgency, high emotional load, often shopping NOW because the situation is fresh.

**Search vocab.** "stop foreclosure," "behind on mortgage California," "can I sell my house in foreclosure," "notice of default California," "sell my house before foreclosure."

**Competition.** Cash buyers (Opendoor, We Buy Ugly Houses, local wholesalers), foreclosure-rescue services (some legit, some scam), other distressed-specialty agents. Estimated CPC range: $5 to $15.

**Joshua's hook.** "List it at market and keep the equity. Cash buyers will take 25% below. You have time and you have options."

### Segment B: Foreclosure / Notice of Trustee Sale (NTS)

**Profile.** Auction date is set. Often within 21 days. Owner is in crisis. May still have equity above the loan balance. Last-chance window before bank takes the property.

**Search vocab.** "sell house before auction," "trustee sale California," "save my home from auction," "stop trustee sale," "list house in foreclosure fast."

**Competition.** Same as Segment A, plus auction-attendance services. Estimated CPC range: $8 to $20 (highest urgency keywords).

**Joshua's hook.** "There's still time. I've sold under 21 days from NTS. You don't have to lose what's left."

### Segment C: Divorce sale

**Profile.** Often court-ordered. Privacy is paramount. Both spouses may need to agree. Frequently coordinated with family-law attorney. Variable urgency.

**Search vocab.** "selling house during divorce," "divorce real estate specialist," "divorce home sale California," "selling marital home Orange County," "house sale court order divorce."

**Competition.** Other divorce-specialty agents (REDS-certified), family-law-attorney referrals. Estimated CPC range: $4 to $10.

**Joshua's hook.** "Discretion, attorney coordination, no public listing if either of you wants privacy. Off-market options on the table."

### Segment D: Probate / Inherited Property

**Profile.** Heir(s) selling deceased's property. Often multiple siblings with differing opinions. Court confirmation may be required (depends on whether the estate is full probate, summary probate, or trust). Slow timeline (60 to 180 days).

**Search vocab.** "selling inherited property in California," "probate real estate Orange County," "sell my parents house," "inherited house California taxes," "probate sale process California."

**Competition.** Probate-specialty agents (CPRES-certified), estate attorneys with agent referrals, iBuyers targeting the segment. Estimated CPC range: $3 to $8.

**Joshua's hook.** "Probate-court-confirmed sale handled. Sibling coordination managed. Stepped-up basis tax implications explained. Network of probate attorneys on call."

### Segment E: Short Sale

**Profile.** Owner is underwater (mortgage exceeds market value). Requires lender approval. Slow (90 to 180 days typical). Often paired with financial hardship documentation. Less common in OC due to high home appreciation, more common in IE (Riverside, San Bernardino) where 2008 bubble overhang persists.

**Search vocab.** "short sale California," "owe more than home is worth," "underwater mortgage sell," "short sale agent Orange County," "short sale Riverside."

**Competition.** SFR-certified specialty agents, short-sale negotiation companies. Estimated CPC range: $3 to $10.

**Joshua's hook.** "Lender coordination, no out-of-pocket cost to you, deficiency waiver negotiation. SFR-certified."

### Optional Segment F (v2): Senior / Health-Forced Downsizing

**Profile.** Older homeowner needing to sell due to health, mobility, family pressure. Often coordinated by adult children. Emotional. Long decision cycle.

**Search vocab.** "downsizing for seniors," "selling parents home dementia," "senior home sale California," "estate downsizing services."

**Competition.** Senior Real Estate Specialist (SRES) certified agents, senior-move managers. Estimated CPC range: $2 to $6.

Defer launching this segment until v2. The first four campaigns are higher commercial intent.

---

## 3. Lander architecture

### Hero

| Element | Content |
|---|---|
| Eyebrow | `Confidential help for Orange County homeowners` |
| H1 | `Facing foreclosure, divorce, probate, or a forced sale? Talk to me before the deadline.` |
| Subhead | `I'm a licensed Irvine listing agent who has helped families in OC sell during the hardest situations. Cash buyers will take your equity. I'll help you keep it.` |
| CTA button | `Get a Confidential Game Plan` |
| Tab structure | None. ONE lane, ONE conversation. |
| Background imagery | Calm, residential, not aggressive. Neighborhood-at-dusk or similar. NOT auction-gavel imagery. |

### Proof block

Three named situations (anonymized real cases where possible, "currently in escrow" placeholders otherwise):

```
SITUATION 001 — Anaheim, CA
14 days from auction. Listed and closed in 19 days.
Net to seller after payoff: $87,000 they would have lost
to a cash investor offering well below market.

SITUATION 002 — Tustin, CA  
Sibling-shared probate. Court-confirmed sale in 60 days.
Coordinated with the family's probate attorney and the
named executor. Three siblings, one clean close.

SITUATION 003 — Mission Viejo, CA
Divorce sale. Coordinated with both attorneys and the
court. Sold off-market to preserve privacy. Both
spouses kept their court-ordered share, on time.
```

Use the same `CASE FILE 00N` numbering convention as /testimonials/ for visual consistency, but with a `SITUATION` prefix to distinguish from the celebratory case files.

### Funnel (`data-funnel="relief"`)

Four steps. Lead with the situation (NOT timeline) because that's how distressed sellers self-identify.

**Step 1: "What's going on?"** (single-select, auto-advance)
```
- Behind on my mortgage
- I have a foreclosure notice (NOD or NTS)
- Divorce
- Probate or inherited property
- Other situation
```

**Step 2: "Where is the property?"**
- Address input with Places autocomplete
- No strict validation gate (distressed sellers don't always have clean addresses to type, and we don't want to friction them out)
- Optional override: "I'd rather discuss this on the phone" → skip to step 3

**Step 3: "How can I reach you, in private?"**
- First and last name
- Email
- Phone
- Optional textarea: `Anything I should know before I call? (optional)` — gives distressed sellers a place to dump context (NTS date, divorce decree, executor status) that helps Joshua prep before calling

**Step 4: Submit button**
- Button: `Get Confidential Help`
- Assurance bar: `Free. Confidential. Direct callback within 4 hours.`
- Fine print: `Your inquiry stays between us. No public listing data shared.`

### Trust signals

```
- California DRE #02267255, Real Brokerage
- SFR Certified — Short Sales and Foreclosure Resource (NAR)
  [GET THIS BEFORE LAUNCH if not already held — $109, 7 hours online]
- CPRES Certified — Certified Probate Real Estate Specialist
  [GET WITHIN 60 DAYS — $797, 2 days]
- Coordinates with foreclosure-defense attorneys, family-law
  attorneys, probate attorneys, and CPAs across Orange County
- Sub-5-minute response window on submitted inquiries
- Privacy commitment: no public listing data shared without
  explicit consent, off-market options on the table
```

### What is intentionally NOT on /relief/

- The "It's a seller's market in Irvine, median $1.48M, 35 days" market widget
- The "We work with trusted brands" Compass/BHHS/KW/eXp/Douglas Elliman strip
- The "Real reviews. Real outcomes. From happy homeowners!" stars and aggregate framing
- The 6-card "How we match you with the right agent" agent-locator block
- Star ratings of any kind
- Aggregate stats ("$X saved," "$Y negotiated")
- The "Compare Agents" CTA, or any tab system

These elements are the right call on the homepage. They are the wrong call here.

---

## 4. Tracking integration

### PostHog events (new, mirror the homepage funnel pattern)

| Event | When | Properties |
|---|---|---|
| `relief_funnel_open` | LP loaded | `gclid`, `prefill_provided`, `campaign_source` (from URL param) |
| `relief_step_advance` | `showStep(n)` with `n > prev` | `from_step`, `to_step`, `total_steps=4` |
| `relief_back` | `showStep(n)` with `n < prev` | `from_step`, `to_step` |
| `relief_option_selected` | Step 1 option click | `situation` (one of: pre_foreclosure, foreclosure_nts, divorce, probate, other) |
| `relief_submit_attempt` | Validation passed, fetch starts | (none) |
| `relief_submit_success` | `/api/lead` returned ok | `situation` |
| `relief_submit_error` | API non-ok or fetch rejected | `error_kind` |

Dual-fire to dataLayer via the same `track()` helper pattern used by the homepage. Names get the `relief_` prefix so PostHog dashboards split cleanly between max-intent funnel and distressed funnel.

### GA4 / GTM

Option A (simpler): keep one `generate_lead` event in GA4, add a `funnel_mode` parameter (`sell` / `buy` / `sellandbuy` / `relief`). Pivot in GA4 explorer by `funnel_mode`.

Option B (cleaner Smart Bidding): fire a SEPARATE GA4 event `generate_lead_distressed` for relief-mode submissions, import as a separate Google Ads conversion. Each campaign optimizes to its own conversion. Recommended for "number one in SoCal" rigor.

Either way, the existing pending GTM fix to switch `generate_lead` from /thank-you/ pageview to the `lead_confirmed` custom event must land before launching this campaign. Same fix, same gating logic.

### /thank-you/ confirmation copy variant

The `/thank-you/` page already reads sessionStorage flags set by the homepage funnel. Add a third branch:

```js
const leadMode = sessionStorage.getItem('drozq_lead_mode');
// 'sell' / 'buy' / 'sellandbuy' / 'relief'
if (leadMode === 'relief') {
  // Render the distressed-appropriate confirmation copy:
  //   "Thanks. I'll call you within 4 hours, confidentially.
  //    If you have an auction date or court deadline,
  //    text me directly: (949) 438-5948."
} else {
  // Existing confirmation copy
}
```

Push the existing `lead_confirmed` event with `funnel_mode=relief` in the params, then clear the flag.

---

## 5. Campaign architecture

Four separate campaigns (Foreclosure, Divorce, Probate, Short-Sale). Each has 2 to 4 ad groups internally. All four share a Negative Keyword list and all four point to `/relief/` as Final URL.

```
Search | Distressed-Sellers | Foreclosure | OC+IE+LA
  AG1 | Pre-Foreclosure / NOD
  AG2 | Foreclosure / NTS / Auction
  AG3 | Behind on Mortgage / Late Payments
  AG4 | Sell House Fast Before Foreclosure

Search | Distressed-Sellers | Divorce | OC+IE+LA
  AG1 | Divorce Real Estate
  AG2 | Selling House During Divorce
  AG3 | Court-Ordered Sale

Search | Distressed-Sellers | Probate | OC+IE+LA
  AG1 | Probate Sale / Probate Specialist
  AG2 | Inherited Property
  AG3 | Sibling Sale / Estate Sale

Search | Distressed-Sellers | Short-Sale | OC+IE+LA
  AG1 | Short Sale California
  AG2 | Underwater Mortgage
  AG3 | Owe More Than Home Worth
```

### Bidding

Same Phase 1 / Phase 2 model as the max-intent campaign:
- Phase 1: Maximize Conversions, no tCPA cap, until 15 to 30 conversions land per campaign
- Phase 2: Target CPA at ~1.2x observed CPL

CPLs in distressed search run 2 to 3x higher than max-intent. Expect $200 to $500 per lead. Accept it. Lead value justifies it.

### Budget

Per-campaign starting daily budget:

| Campaign | Daily budget | Rationale |
|---|---|---|
| Foreclosure | $200 | Largest segment, highest CPC, highest commercial value per close |
| Divorce | $100 | Mid-volume, mid-CPC |
| Probate | $80 | Lower CPC, slower funnel, fewer queries per day |
| Short Sale | $60 | Smallest segment in OC (high appreciation), test the IE concentrations |

Total Phase 1 daily: **$440** across the four. Total Phase 1 spend over 21 days: ~$9,200. Expected conversions: 20 to 45 total across all four. Phase 2 starts when each campaign individually hits 15+ conversions (some will get there in 2 weeks, others in 4 to 6 weeks).

### Geo

- **Primary (all 4 campaigns):** Orange County (all cities), South LA County (Long Beach, Lakewood, Cerritos, Whittier, Norwalk, Downey, Bellflower)
- **Foreclosure + Short Sale campaigns only:** add Inland Empire west (Corona, Eastvale, Chino Hills, Chino, Norco, Ontario, Riverside-city, Moreno Valley). Higher distressed concentration.
- **v2 expansion:** rest of LA County, San Bernardino County west (Fontana, Rancho Cucamonga) once Joshua's throughput can support.

Presence-only. NOT interest. Same as max-intent.

### Audience signals (Observation, NOT Targeting)

Constrained by Google's Personal Hardships policy, which bans "financial distress" as a targetable audience. What IS available:

- **In-Market:** Residential Properties (For Sale), Real Estate Services, Real Estate Agents and Brokers, Moving Services
- **Detailed Demographics:** Homeowners, Marital Status: Divorced (for Divorce campaign only), Age 50+ (for Probate, since heirs skew older)
- **Custom Search Segments:** build per-campaign from each campaign's own keyword list
- **Remarketing:** people who visited /relief/ and did not submit. Build in GA4.

### Conversion action

Each campaign optimizes to `generate_lead_distressed` (Option B from §4). All other conversions Secondary.

---

## 6. Keyword sketch per campaign

Full keyword lists get built when each campaign is staged. Sketch for scope:

### Foreclosure campaign keywords (sample)

Exact: `[stop foreclosure california]` `[stop foreclosure orange county]` `[sell house before foreclosure]` `[sell home in foreclosure california]` `[behind on mortgage california]` `[behind on mortgage what to do]` `[notice of default california]` `[trustee sale california]` `[sell house fast before auction]` `[avoid foreclosure california]` `[how to sell house in foreclosure]` `[list home in foreclosure]` `[foreclosure help orange county]` `[pre foreclosure sale california]`

Phrase: `"stop foreclosure"` `"sell house in foreclosure"` `"sell before auction"` `"notice of default"` `"trustee sale"` `"behind on mortgage"` `"foreclosure help"`

### Divorce campaign keywords (sample)

Exact: `[divorce real estate specialist]` `[selling house during divorce]` `[divorce home sale california]` `[divorce real estate agent orange county]` `[selling marital home california]` `[divorce sale realtor]` `[court ordered home sale]` `[divorce real estate irvine]`

Phrase: `"selling house during divorce"` `"divorce real estate"` `"divorce home sale"` `"divorce specialist real estate"`

### Probate campaign keywords (sample)

Exact: `[selling inherited property in california]` `[probate real estate orange county]` `[sell my parents house]` `[inherited house california]` `[probate sale process california]` `[probate specialist real estate california]` `[selling inherited home california]` `[probate court confirmation sale]`

Phrase: `"sell inherited property"` `"probate real estate"` `"inherited house california"` `"selling parents house"` `"probate sale"`

### Short Sale campaign keywords (sample)

Exact: `[short sale california]` `[owe more than home is worth]` `[underwater mortgage sell]` `[short sale agent orange county]` `[short sale realtor riverside]` `[short sale process california]` `[short sale vs foreclosure]`

Phrase: `"short sale agent"` `"underwater mortgage"` `"owe more than home is worth"` `"short sale california"`

(Full lists drafted per campaign when each is built. The pattern matches the max-intent spec.)

---

## 7. Shared negative keyword list: `Negatives | Distressed Sellers`

Attached to all four distressed campaigns. Walls off max-intent territory and consumer-research territory.

```
# Carve out max-intent territory (the OTHER campaign owns these)
compare agents
compare realtors
find a listing agent
home valuation
home value report
free home value
free cma
top listing agent

# Cash buyer side (different product, don't compete on intent)
we buy houses
sell to investor
opendoor
offerpad
ibuyer
zillow offer
cash for my home
quick cash for house
instant offer
sell my house fast cash

# DIY / FSBO (won't hire)
for sale by owner
fsbo
sell house without agent
flat fee mls
flat fee listing
1 percent commission

# Research / consumer info
how does foreclosure work
how does probate work
foreclosure timeline
foreclosure process explained
probate timeline california
divorce process california
real estate license california
real estate school
realtor jobs
foreclosure forum
reddit
youtube
wikipedia

# Wrong product / off-topic
foreclosure cleaning
foreclosure cleaner
foreclosure attorney jobs
divorce attorney jobs
probate attorney jobs
divorce lawyer california
divorce mediation
foreclosure investment
foreclosure flip
foreclosure auction list
buy foreclosure
buy probate
buy short sale

# Out-of-state geo
texas
florida
new york
arizona
phoenix
nevada
las vegas
washington
oregon
georgia
chicago
ohio
columbus

# Rental / wrong owner type
rent
rental
for rent
landlord
tenant
section 8

# Brand defense (competitor agent-matching / cash-buyer brands)
homelight
ideal agent
upnest
clever real estate
rocket homes
opendoor sell
offerpad sell
homevestors
we buy ugly houses
```

---

## 8. Ad copy direction (full RSAs drafted per campaign when each is built)

Cohesion principle: every ad echoes the LP hero, AND speaks to the specific segment. Avoid:

- Panic language: "ACT NOW," "the bank is coming," "DON'T LOSE YOUR HOME!"
- Fear-based imagery in copy
- Cash-buyer language ("instant offer," "cash today," "we buy fast")
- "Guarantee" language around foreclosure or sale outcomes (Google policy)
- Vague "specialist" claims without proof

Use:

- Calm, professional voice. The seller is already panicked; be the calm anchor.
- Concrete situation language ("before the auction date," "court-confirmed probate sale," "off-market divorce sale," "lender-approved short sale")
- Equity-preserving framing ("keep your equity," "list at market, not 25% below")
- Response-time commitment ("I'll call you within 4 hours")
- Real credentials (DRE, SFR, CPRES once held)
- Privacy commitment ("confidential," "no public listing")

Pinning strategy per campaign:
- Foreclosure: pin H1 to `Behind on Your Mortgage? Talk to Me First` or `Foreclosure in OC? List Before the Auction`
- Divorce: pin H1 to `Selling During Divorce in OC` 
- Probate: pin H1 to `Probate Sale Specialist, Orange County`
- Short Sale: pin H1 to `Short Sale in OC? Lender Coordination Handled`

---

## 9. Operational requirements (non-negotiable)

These are the conditions that make this campaign work, not aspirational nice-to-haves.

### 9.1 Sub-5-minute response time on inbound leads

Distressed leads die in silence. The /api/lead webhook already lets you wire Zapier (env var `ZAPIER_WEBHOOK_URL`). Add a Zap that:
- Triggers on every submission where `intent=Distressed Sale Inquiry`
- Sends a Twilio SMS to Joshua's phone immediately with the lead summary (name, situation, address, phone, optional message)
- Optionally posts to a Slack channel for backup awareness

If Joshua can't answer within 5 minutes 90% of the time, the campaign loses to faster competitors. This is the single biggest operational lever.

### 9.2 Partner network in place before launch

At minimum, one named partner in each:
- **Foreclosure-defense attorney** (OC-based, takes referrals)
- **Family-law attorney** (OC-based, divorce-real-estate referrals)
- **Probate attorney** (OC-based, probate sale referrals)
- **CPA** (familiar with stepped-up basis, short-sale 1099-C, capital gains exclusion)
- **Loan-modification specialist** (legitimate, not scam) for cases that should NOT be sold

These don't appear in ads. They appear on the call after the lead converts, when the conversation needs a specialist. Without this network, leads convert but Joshua can't close them well, and word-of-mouth quality drops.

### 9.3 Certifications

| Certification | Cost | Time | Trust lift | Priority |
|---|---|---|---|---|
| **SFR** (Short Sales and Foreclosure Resource) | $109 | 7 hrs online | Large | Before launch |
| **CPRES** (Certified Probate Real Estate Specialist) | $797 | 2 days | Large for Probate segment | Within 60 days |
| **SRES** (Seniors Real Estate Specialist) | $295 | 1 day | Medium | When Segment F (senior) launches |
| **CDPE** (Certified Distressed Property Expert) | $497 | 2 days | Medium, overlaps SFR | Optional |

SFR is the immediate ask. Without it, the Foreclosure and Short Sale campaigns lack the trust signal that lets ad copy say "SFR Certified" and the LP carry the credential on the trust strip.

### 9.4 Content support (Field Notes pillar posts)

Write three pillar posts to /field-notes/ supporting organic capture and lifting the /relief/ trust signal:

1. **"How a foreclosure sale actually works in California, day by day"** — long-form, technical, accurate, deeply useful. Targets "foreclosure process california" research queries.
2. **"Selling an inherited home in California: probate, taxes, siblings"** — same depth, probate angle.
3. **"Selling a home during divorce: timing, court, privacy"** — same depth, divorce angle.

These are not paid-funnel pages. They are long-term SEO + trust assets. Field Notes already exists as the pattern (/field-notes/ replaces /blog/). Don't link to /relief/ heavily from these (would dilute the brand-mode/conversion-mode separation in CLAUDE.md), but DO link to /contact/ and reference the privacy + situations Joshua handles.

---

## 10. Tactical regulatory notes (positioning, not a lecture)

These constrain copy and audience targeting. They're not optional.

### 10.1 California Civil Code §2945 — Foreclosure Consultants Act

This regulates "foreclosure consultants" who promise to help homeowners stop foreclosure for a fee. Licensed real estate agents performing real estate brokerage services (listing the property) are exempt. So Joshua's service IS legal. But ad copy should NOT imply foreclosure-rescue services. The safe framing:
- ✓ "List before the auction date"
- ✓ "Preserve your equity"
- ✓ "Sell during foreclosure"
- ✗ "Stop the bank from taking your home"
- ✗ "Save your home from foreclosure"
- ✗ "We can stop the foreclosure for you"

The second set crosses into foreclosure-consultant territory regardless of license status, and Google's policy reviewers will reject ads using that framing.

### 10.2 Google's Personal Hardships policy

Removed "in financial distress" as a targetable audience in 2020. Effects:
- Cannot target audience segments by hardship
- CAN target by search intent (the keywords themselves)
- CAN target by demographics (homeowners, age, marital status)
- Audience signals limited to In-Market, Detailed Demographics, Custom Search Segments built from keywords

This is fine. Search intent is the strongest signal anyway.

### 10.3 No "instant cash" claims

Joshua isn't a cash buyer. Copy must not imply otherwise:
- ✓ "I'll close fast" (factual when listed properly)
- ✓ "List in 7 days" (factual)
- ✗ "Instant cash for your house"
- ✗ "Cash offer in 24 hours"

This is the cash-buyer lane. Joshua doesn't want that traffic anyway (different product, lower commission, different customer).

---

## 11. Build sequence

### Week 1 (LP)

1. Add `data-funnel="relief"` mode to funnel JS. Port the funnel architecture into a new `/relief/index.html`, importing the same CSS from the homepage style block.
2. Write `/relief/` HTML: hero, proof block with 3 situation case files, funnel section, trust strip, footer.
3. Extend `/functions/api/lead.js` if needed (likely just pass-through with `intent=Distressed Sale Inquiry` value).
4. Extend `/thank-you/` to read `drozq_lead_mode=relief` flag and show the 4-hour-callback confirmation message + push `lead_confirmed` with `funnel_mode=relief`.
5. Add PostHog events (`relief_*`).
6. In GTM: create a new tag for the `generate_lead_distressed` GA4 event (option B). Trigger on `lead_confirmed` event with `funnel_mode=relief`. Publish.
7. Import the new conversion into Google Ads.
8. Joshua starts the SFR certification course (parallel, finishes within the week).

### Week 2 (Foreclosure campaign — biggest segment first)

9. Create the shared `Negatives | Distressed Sellers` list. Paste §7.
10. Stand up `Search | Distressed-Sellers | Foreclosure | OC+IE+LA`. Architecture mirrors the max-intent campaign settings (Max Conversions, English only, Presence-only geo, partners off, AI Max off).
11. Build 4 ad groups (AG1 Pre-Foreclosure / AG2 NTS / AG3 Behind on Mortgage / AG4 Sell Fast Before Foreclosure).
12. RSAs per ad group (drafted as part of this build, not in this strategy doc; will follow the max-intent pattern).
13. Wire `Negatives | Distressed Sellers` shared list.
14. Add account-level assets if needed (the existing max-intent assets work for trust elements; consider campaign-level sitelinks specifically tailored to distressed: "SFR Certified," "Foreclosure Resources," "Privacy First," "Sub-5-min Response").
15. Set conversion to `generate_lead_distressed`.
16. IP exclusions same as max-intent.
17. Launch at $200/day.

### Week 3 (Divorce + Probate campaigns)

18. Stand up `Search | Distressed-Sellers | Divorce | OC+IE+LA` at $100/day.
19. Stand up `Search | Distressed-Sellers | Probate | OC+IE+LA` at $80/day.
20. Build ad groups per §5, RSAs, attach shared negatives.

### Week 4 (Short Sale + iteration)

21. Stand up `Search | Distressed-Sellers | Short-Sale | OC+IE+LA` at $60/day.
22. Begin daily Search Terms Report audits per campaign.
23. Build the first Field Notes pillar post (foreclosure process).
24. Phase 2 tCPA on Foreclosure if 15+ conversions landed.

### Month 2 (iteration)

25. v2 LP variants: per-segment URL params, dynamic case-file emphasis on /relief/.
26. Build CPRES certification (if probate volume justifies).
27. Build remaining two Field Notes pillar posts (probate, divorce).
28. Begin direct-mail follow-up using public NOD records for the Foreclosure segment (separate channel, complements paid).

---

## 12. Success metrics

| Metric | Phase 1 target | Phase 2 target | "Number one in SoCal" target |
|---|---|---|---|
| Conversions per week | 5 to 10 across all 4 campaigns | 15 to 25 | 30+ |
| CPL (blended) | $200 to $400 | $150 to $300 | $100 to $200 |
| Lead-to-call rate (5-min response) | 70% | 85% | 95% |
| Lead-to-listing close rate | 5 to 8% | 10 to 12% | 15%+ |
| Distressed closes per year | 6 to 12 | 15 to 20 | 25+ |
| Listing-side commission revenue / year | $130k+ | $340k+ | $560k+ |
| Share of voice on top 20 distressed queries in OC | n/a | top 5 | top 1 (impression share >50%) |

The "number one" benchmark: top impression share (Google Ads metric) on the top 20 distressed-seller queries across OC. Achievable within 4 to 6 months at $440/day blended Phase 1 budget if response operations hold.

---

## 13. What this strategy is NOT

- It is not a Performance Max campaign. Search only. PMax pollutes the conversion model and breaks message-match cohesion.
- It is not a buyer's-side campaign. Distressed sellers and distressed-property buyers are different audiences with different intent.
- It is not a cash-offer arbitrage play. Joshua is an agent, not a wholesaler.
- It is not "we'll stop your foreclosure." Joshua is not a foreclosure consultant. The pitch is "list and net the equity."
- It is not a fear-based campaign. Calm and professional out-performs panic for these segments. The seller is already panicked.
- It is not a place to test edgy creative or aggressive promises. Reputation in this segment compounds, especially through attorney referrals.
