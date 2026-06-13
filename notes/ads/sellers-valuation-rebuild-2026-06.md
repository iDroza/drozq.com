# Sellers, Instant-Valuation Rebuild (2026-06)

**This supersedes the positioning in `sellers-max-intent-campaign.md`.** That doc was built (2026-05-20) for the old "Compare Agents / agent-marketplace" homepage. The homepage has since been rebuilt into the **instant home valuation + 5 seller playbooks** lead magnet, so the campaign's cohesion contract, ad copy, and sitelinks all change. The *operational* sections of the old doc that are still valid (pre-flight tracking checks §1, audience signals §6, launch sequence §10, budget math §12, kill switches §14) still apply , reuse them.

Companion docs: `bidding-decisions.md` (bid strategy, do not re-litigate), `sellers-max-intent-campaign.md` (old build, kept for history).
Implementation export (for hand-building in the UI / Ads Editor): `C:\Users\guerr\Downloads\drozq-google-ads-campaign-build.md` + `drozq-google-ads-keywords.csv` + `drozq-google-ads-negatives.txt`.

*Last updated: 2026-06-13.*

---

## 0. The new cohesion contract (every ad must echo this)

Live homepage (drozq.com) as of 2026-06-13:

- **Eyebrow:** "Irvine Homeowners"
- **H1:** "Get your instant home valuation and the BONUS 5 Home Selling Playbooks"
- **Subhead:** "We use these internally to sell homes for top dollar"
- **Primary CTA:** address box + "Run my Valuation" (Sell tab default)
- **3-step:** Enter your selling address , Get your home's value , I handle the rest
- **Playbooks:** pricing, marketing, negotiation, concierge, speed , "the exact systems behind every home I sell," "yours to keep whether or not we ever talk"
- **Proof:** sold in about six weeks; live on MLS in 7 days; open house every weekend; 15-minute callback 7 days a week; Friday written report; every offer scored; my crews at wholesale, zero markup; net on paper before listing; no check to me, fee at closing
- **Market widget:** "June 2026, Irvine, CA. Seller's market. Median $1,488,000. 45 days on market."
- **Testimonial:** "$23,250 seller credit negotiated" (Long Beach firefighter, first-time buyer)

**The promises every ad MUST carry (in priority order):**
1. **Instant home valuation** (by address, free, in seconds) , the hook
2. **+ 5 free seller playbooks** , the bonus that separates us from a faceless estimator
3. **A real local Orange County agent** who sells for top dollar in about six weeks
4. **No cost to start; fee at closing** (positive cost framing, never an anti-promise)

Banned in copy (site voice rules): team "we" voice, "no obligation/pressure/spam/script" anti-promises, vendor/tool names ("API/Rentcast/Zillow data"), em dashes. First-person Joshua only.

### Critical landing-page fix (blocks Quality Score)
The homepage `<title>` still reads **"Compare Top Irvine Listing Agents | Drozq"** , the dead angle Google reads for ad,landing relevance. Proposed:
- Title: `Instant Irvine Home Valuation + 5 Free Seller Playbooks | Drozq`
- Meta description: `Enter your address for your Orange County home's value instantly, plus the 5 playbooks I use to sell for top dollar. Free, from a local agent. Sold in about six weeks.`
(Needs Joshua's yes , homepage is a sacred surface.)

---

## 1. What changed vs the old build

| | Old build (2026-05-20) | This rebuild (2026-06-13) |
|---|---|---|
| Angle | Compare agents / commission marketplace | Instant home valuation + 5 playbooks lead magnet |
| Ad groups | Compare-Listing-Agent, Home-Value-Report, Sell-My-House-OC, Compare-Commission | Valuation-first (What's-My-Home-Worth, Value-Estimator, Free-Valuation/CMA, How-Much, OC-by-City) + a lean Sell-My-House campaign |
| Killed | , | Compare-Listing-Agent + Compare-Commission ad groups (didn't convert, off-strategy) |
| Landing | old "Compare Agents" homepage | same URL, now the instant-valuation homepage |
| Sitelinks | "Free Agent Proposals / How It Works / Why Use an Agent" + a **Zillow Agents** auto-sitelink | valuation/value-first set (see §6); remove the Zillow auto-sitelink |
| Bidding | (see bidding-decisions.md) | **unchanged** , keep portfolio tCPA + $15 cap |
| Geo | Irvine + named OC cities + ZIPs | **all of Orange County** (per Joshua, 2026-06-13) |

Data that drove it (May 23,31 window, the old campaign): valuation intent (`AG2 Home-Value-Report`) took **81% of spend** and the best CTR (`free home valuation` 9.5%, `my home value` 6.9%); the three non-valuation ad groups barely spent and never converted; blended CPC ~$27 from message mismatch (valuation searches , "compare agents" page). 76% mobile, audience 45+, OC core.

---

## 2. Campaign settings (both new campaigns)

Reuse the old doc's §2 settings, with these deltas:

- **Locations:** Orange County, California (county-level). Option: **Presence** ("people in or regularly in"), not interest.
- **Bidding:** apply the existing portfolio **Target CPA `Sellers Conversions + $15 cap`** (target $400, max CPC $15) from Shared Library. **Not Max Clicks** (rejected, see bidding-decisions.md). The new LP should raise CVR above the old ~2.9%; once 15,30 conversions bank on clean signal, graduate to a data-driven tCPA at ~1.2x observed CPL and loosen the cap.
- **Conversions:** lead action (`generate_lead`/`lead_confirmed`) Primary only. Signal is clean since the 2026-05-29 GTM trigger fix (confirmed working).
- **Networks:** Search only; Partners OFF; Display OFF.
- **Negatives:** attach the existing shared list **`Negatives | Sellers Funnel`**; add `flat fee`, the `ownerly` variant, and tool/brokerage brands flagged 2026-05-28 if missing.
- **Final URL:** `https://drozq.com/` for all ads. Auto-tagging ON. Keep the established Final URL suffix.
- **Audiences:** Observation per old doc §6.

---

## 3. CAMPAIGN 1 , `Drozq | OC Home Valuation - Search` (primary)

Display paths: `Home-Value` / `Orange-County`. Final URL `https://drozq.com/` for all ad groups.

Full keyword lists: `drozq-google-ads-keywords.csv`. Phrase + Exact at launch (no Broad until on data-driven tCPA + locked negatives). Ad-group themes:

- **AG1 , What's My Home Worth** , `what is my home worth`, `what's my house worth`, `value of my home`, `my home value`, `home value` (the core value cluster; `my home value` exact was the old top spender at 6.9% CTR).
- **AG2 , Home Value Estimator** , `home value estimator`, `house value estimator`, `property value estimator`, `home value by address`, `instant/free home value estimator` (tool intent , the instant valuation IS the tool).
- **AG3 , Free Home Valuation / CMA** , `free home valuation` (old 9.5% CTR), `free home value report`, `home valuation`, `free cma`, `comparative market analysis`.
- **AG4 , How Much Is My House Worth** , `how much is my house/home/property worth` (natural-language question intent).
- **AG5 , OC Home Value by City** , phrase, geo-modified across OC (`home value irvine/newport beach/mission viejo/huntington beach/costa mesa/tustin/anaheim`, `... orange county`). Coverage play for the all-OC geo.

### RSA copy (one per ad group; <=30 char headlines, <=90 char descriptions; light pins keep Ad Strength high)

Shared benefit/proof headline pool (reused across the valuation ad groups):
```
Instant Home Valuation        Built on Your Street's Sales   + 5 Free Seller Playbooks
Know Your Value in Seconds    Your Home's Real Value         Home Value By Address
Free, No Cost to You          Sold in About Six Weeks        Priced for Top Dollar
Local Orange County Agent     It's a Seller's Market         Real Comps, Real Pricing
Run My Valuation
```
Shared description pool:
```
1. Enter your address, get your value instantly, plus my 5 seller playbooks, free.   (pin D1)
2. See what your home is really worth, built from what's actually selling near you.
3. I price it right, handle repairs and showings, and sell it in about six weeks.
4. Know your number in seconds, then decide. Real comps, real data, priced to sell.
```
Per-ad-group **Position-1 pins** (the message-match headlines that mirror the keyword):
- AG1: `What's My Home Worth?` + `Your Home's Real Value` + `Instant Home Valuation`
- AG2: `Home Value Estimator` + `Value Estimate By Address` + `Instant Home Valuation`
- AG3: `Free Home Valuation` + `Free Home Value Report` + `Instant & Free, By Address`
- AG4: `How Much Is My Home Worth?` + `How Much Is It Worth?` + `Instant Home Valuation`
- AG5: `Orange County Home Value` + `What's My OC Home Worth?` + `Instant Home Valuation`
Pin `Run My Valuation` to Position 3 in every ad group. Everything else unpinned. (Full 15-headline lists per ad group: the Downloads build doc §4.)

---

## 4. CAMPAIGN 2 , `Drozq | OC Sell My Home - Search` (secondary)

Lower volume in the data but high intent; the homepage serves it. Launch second, own budget, so it never starves Campaign 1. Display paths `Sell` / `Orange-County`.

- **AG1 , Sell My House (OC)** , `sell my house/home orange county`, `sell my house/home irvine`, `list my house irvine`, `i want to sell my house irvine`. P1 pins: `Sell Your Orange County Home`, `Sell My House, Irvine`, `Sell for Top Dollar`. Descriptions lead with "start with your home's value + 5 playbooks, free, then we get it sold," plus the 7-days/six-weeks/offer-scored proof.
- **AG2 , Best Agent to Sell** , `best agent to sell my home`, `find a realtor to sell my house`, `top listing agent orange county`, `best listing agent irvine`. Frame on Joshua's selling **system**, NOT agent comparison/commission. P1 pins: `Top Irvine Listing Agent`, `Sell With a Local Pro`, `Sell for Top Dollar`. Description D1: "The exact system behind every home I sell, yours free before we ever talk."

(Full headline/description lists: Downloads build doc §5.)

---

## 5. Negative keywords

Attach the existing shared list **`Negatives | Sellers Funnel`** to both campaigns. Confirm/append: `flat fee`, `flat fee realtor`, `ownerly`, `quantarium`, `corelogic`, `realavm`, `kelley blue book`, `housecanary`, `rocket mortgage`, `freedom mortgage`, brokerage brands (`keller williams`, `exp realty`, `first team`, `john l scott`, `realty one group`, `serhant`, `compass`, `redfin`, `zillow`). Do NOT negate: free, value, worth, estimate, valuation, "home value", "near me". Full list: `drozq-google-ads-negatives.txt`. Weekly: search-terms report , move junk into the list; promote converters to exact.

---

## 6. Assets (replace the old agent-marketplace set)

Remove the generic auto-sitelinks (incl. **"Zillow Agents Near You"** , points at a competitor) and the "Free Agent Proposals / How It Works / Why Use an Agent" set.

**Sitelinks** (deep-link to real pages): `See All 5 Home Values` (/value/) , `5 Free Seller Playbooks` (/) , `How I Sell in 6 Weeks` (/process/) , `Real Client Results` (/testimonials/) , `Today's Irvine Market` (/market-insights/) , `What Selling Costs` (/prices/).
**Callouts:** Instant Home Valuation · Free, No Cost to You · 5 Seller Playbooks Free · Local Orange County Agent · Sold in About Six Weeks · 15-Minute Callback · Top-Dollar Pricing · Real Brokerage, DRE 02267255 · I Handle Repairs & Showings · Net on Paper Before Listing.
**Structured snippet , Services:** Instant Home Valuation, Comparative Market Analysis, Listing & Marketing, Negotiation, Cash Offer Estimate, Seller Concierge.
**Call asset:** (949) 438-5948 (secondary to the form).
**Location asset , ACTION:** the live ads render `<Rating (Reviews)>`/`<Open Hours>` as empty placeholders , the Google Business Profile isn't populating. Wire the GBP (hours + reviews) before attaching a location asset, or omit it so empty placeholders never show.

---

## 7. Launch checklist (deltas from old doc §10)

- [ ] Pause the old Compare-Listing-Agent + Compare-Commission ad groups and the legacy local "Call Us Now" + March video creatives
- [ ] Homepage `<title>`/meta fixed to the valuation angle (§0) , before launch
- [ ] Build Campaign 1 (5 valuation ad groups) + Campaign 2 (2 sell ad groups); paste keywords from the CSV; build the RSAs with the §3/§4 pins; Ad Strength Good/Excellent before enabling
- [ ] Apply portfolio tCPA + $15 cap; attach `Negatives | Sellers Funnel`; Search-only; Presence; auto-tagging ON; lead action Primary
- [ ] Swap sitelinks/callouts/snippet (kill the Zillow sitelink); verify a preview click lands gclid + fires `funnel_open` , `lead_confirmed`
