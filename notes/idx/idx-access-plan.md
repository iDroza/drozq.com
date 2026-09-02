# IDX on drozq.com: how to get it, what it costs, what the build looks like

*Researched 2026-09-02. Nothing here is built yet; this is the plan and the paperwork map.*

## The one-paragraph answer

IDX (the right to show every other broker's CRMLS listings on drozq.com) is granted by CRMLS to the **Participant** (the broker), not to the agent. Joshua is a Subscriber under **Real Brokerage Technologies** (DRE 02022092, 1420 Kettner Blvd #100, San Diego, per the DRE public license lookup for 02267255), so every path below needs one signature or approval from Real's California broker team. CRMLS offers four ways in; two are free frameable links that work today, one is a licensed vendor, and one is a raw RESO Web API feed through Trestle (Cotality, formerly CoreLogic) that lets us build the search natively on the existing Cloudflare stack with no third-party script on the page. The recommendation is at the bottom: ship the free frame this week so the Buy tab's "See Homes" button stops dead-ending, and start the raw-feed paperwork in parallel because the paperwork is the long pole.

## Who has to sign what

CRMLS Rules & Policies section 19.2 (Internet Data Exchange) is the governing text. The parts that decide the paperwork:

- **19.2.1 Authorization.** Participants AND Subscribers may display Coming Soon, Active, Active Under Contract, Pending and Sold/Leased listings, by download or by framing the MLS public site. Sold data goes back to 2012-01-01. "The downloading of raw data will be through the Participant only." That sentence is why the RESO feed needs Real, not just Joshua.
- **19.2.3 Control.** The display must be under Joshua's actual and apparent control and presented as his display. A vendor site is fine as long as the agreement gives him control over what shows and how.
- **19.2.13 Website Identification.** The brokerage name and the subscriber's name must be readily visible on any IDX display. drozq.com currently identifies as "Real Brokerage" in the footer identity line; that stays.
- **19.2.18 Notification.** Must notify CRMLS BEFORE displaying other brokers' listings and give CRMLS (and other Participants) access to monitor. This is what the IDX Request Form and the Trestle license do.
- **19.2.17 Compliance.** CRMLS audits IDX sites; violations must be cured within 10 calendar days of notice or the feed is cut.

The **CRMLS IDX Request Form** (go.crmls.org/wp-content/uploads/2018/10/IDX_Request_Form.pdf) is the vendor-path instrument. Fields: Agent Name, Agent User ID (Matrix ID), Agent DRE#, Agent Phone, Agent E-Mail, Office Name, Office ID, Office DRE#, Website(s), the requestor attestation (active member in good standing, will abide by the rules, has broker permission), then a **Broker of Record** block (name + signature: "I have given permission to the Requestor to have CRMLS IDX listings on the Requestor's website"), then the vendor block (Company, Phone, Contact, E-Mail). Submit to **Licensing@crmls.org** or fax 909-978-3165. CRMLS support: (800) 925-1525, Mon-Fri 8:30am-9pm, Sat-Sun 10am-5pm.

Real Brokerage: broker signatures on MLS/vendor forms go through Real's support (support.therealbrokerage.com has a dedicated article, "What email address should I use to request a signature from the Broker"; the page 403s to scripted fetches, so open it logged in). Real's California designated broker signs as broker of record for Real Brokerage Technologies. Open the ticket with the form pre-filled; they sign, you forward to Licensing@crmls.org.

## The four CRMLS paths (from go.crmls.org/idx-resources)

| | What it is | Cost | Paperwork | Fit for drozq.com |
|---|---|---|---|---|
| **1. IDX Standard** | Frameable Matrix search (My Listings or Map Search, optional sign-up form). Generated in Matrix: Settings > IDX Configuration > pick form > set map area > IDX Enabled > copy the HTML. | Free | None beyond being a CRMLS member; broker permission is presumed for framing | Stopgap. Ugly, not indexable, an iframe on our page. Fine for a `/homes/` page behind the Buy tab this week. |
| **2. IDX Plus** | The IDX Link Generator (go.crmls.org/idx-link-generator): public search, agent listings, office listings, Google Maps, 12 languages, school data. Needs Public ID (Matrix ID) + Office Code. | Free | None | Same as 1, slightly nicer. |
| **3. Approved IDX vendor** | A vendor licensed to receive the CRMLS feed hosts the search (on a subdomain or embedded widgets). 78 vendors on the 2026 list, including RealScout, Lofty, IDX Broker, Showcase IDX, iHomefinder, Luxury Presence, Real Geeks, Sierra Interactive, SimplyRETS, Placester, Inside Real Estate. | CRMLS charges nothing; vendor fees (roughly $50-$100/mo for IDX Broker / Showcase / iHomefinder; **Lofty is $50/mo for Real agents** via the Real enterprise deal, normally $499) | IDX Request Form with Real's signature, emailed to Licensing@crmls.org, then the vendor's own MLS authorization | Fastest "real" search. Costs a third-party script or a subdomain. RealScout is already in Joshua's toolset (Active Realty account, so check which brokerage that account is licensed under before pointing it at drozq.com). |
| **4. RESO Web API feed (Trestle)** | Raw data license. We pull listings + photos and render them ourselves. | CRMLS's page says $85/mo Trestle platform fee + $7/mo per website URL after the first two (so $0 for drozq.com). Trestle's current pricing page says the Small tier (1-50 contracts) RESO feed is **$100/mo per connection**; budget $100. | Trestle Technology Provider account (cotality.com/products/trestle) > request a CRMLS IDX connection > CRMLS data license agreement e-signed in the Trestle dashboard > Real, as Participant, approves the feed for Joshua's site | The one that matches the site's rules: no new external dependency, our template, our funnel, indexable listing pages. Also the most work. |

There is also a fifth listing, "IDX Premium with Full Website" (Absolute Strategic Agent, a CRMLS Marketplace vendor). It is a whole hosted site; not relevant, drozq.com is the site.

CRMLS additionally runs its own RESO endpoint (`https://h.api.crmls.org/Reso/OData/`, staging at `staging.h.api.crmls.org`, RESO Web API 1.0.3, Identity Server auth) for vendors that already hold a RETS/API account: contact **licensing@crmls.org** first, then **api@crmls.org** to have the account created. Worth one email to ask whether an agent-controlled site can license directly and skip the Trestle fee; the public docs only describe the vendor route.

## Display rules any build has to meet (checklist)

From 19.2 plus the CRMLS IDX Standards of Practice (the 2021 IDX Transparency Initiative):

1. **Listing credit on every listing (19.2.5).** A reasonable consumer must see who the listing agent and broker are, who the advertising broker is (Joshua / Real), and how to contact the listing broker. Display the CRMLS `IDXContactInfo` field in the listing's contact area.
2. **Attribution placement and weight.** Directly adjacent to the price, bed/bath, square footage, or photo. Font no smaller and no lighter than the property description. Wording must say "Listing Agent:" / "Listing Office:" (never "Courtesy of").
3. **Call-to-action buttons name who answers.** "Ask Joshua Guerrero about this home" is compliant; a bare "Contact Agent" is not, and the button must make clear the inquiry does not go to the listing agent.
4. **Source + freshness (19.2.6).** Show "Listing data: California Regional MLS, last updated <date/time>". Downloads and displays refreshed at least every 7 days (we will do minutes).
5. **Personal, non-commercial use notice (19.2.7)** on every full display; thumbnails under 200 characters are exempt if they link to a page that carries it.
6. **Brokerage + agent name visible (19.2.13).** Footer identity line already does this.
7. **Anti-scraping (19.2.8).** Rate limit the listing endpoints like `/api/valuation` already is (`_lib/ratelimit.js`), no bulk export, bot-hostile pagination.
8. **No AVM next to a listing without an opt-out path (19.2.15).** Our `/value/` model is an automated estimate; do not print it beside another broker's listing unless we also honor seller-requested disable flags. Keep the valuation CTA generic ("What's your home worth?"), not "this listing is worth X".
9. **Corrections channel (19.2.16).** A visible email/phone for accuracy comments (the header phone + josh@drozq.com already qualify).
10. **No modification of other brokers' data (19.2.20).** Augmented data (our market stats, school data) must sit clearly separated and labeled with its source.
11. **Seller opt-outs.** Listings flagged no-internet-display or no-address-display never render; the feed carries the flags.
12. **Excluded listings are fine if objective (19.2.12)**: restricting to Orange + Los Angeles County, residential only, is allowed.

## Build sketch for path 4 (Trestle) on the existing stack

Trestle facts from the Cotality docs (trestle-documentation.corelogic.com/web-api): OAuth2 `client_credentials` at `https://api.cotality.com/trestle/oidc/connect/token`, scope `api`, tokens live 8 hours; OData base `https://api.cotality.com/trestle/odata/`; resources Property, Media, Member, Office; `$top` max 1,000; incremental sync on `ModificationTimestamp`, photos on `PhotosChangeTimestamp`; deletions by reconciling `Property?$select=ListingKey`; quotas 7,200 API queries/hour (180/min burst) and 18,000 media requests/hour (480/min), 429 on overrun with `Hour-Quota-*` headers. The FAQ says Web API is appropriate for live queries as well as replication, but replicate anyway: it is cheaper, faster, and survives a Trestle outage.

- **Sync worker** (`workers/idx-sync/`, same pattern as `workers/email-cron/`): cron every 10 minutes pulls `Property` where `ModificationTimestamp gt <last>` and `StandardStatus in (Coming Soon, Active, Active Under Contract, Pending)` and county in (Orange, Los Angeles), upserts into a D1 `listings` table (RESO field names, keep the raw JSON blob too), stores the primary photo in R2 and lazy-fetches the rest on first detail view (the media quota is the one to respect). Nightly full-key reconciliation removes withdrawn listings. Optional: closed sales since 2012 into a `sold` table for the sold board and the CMA tool later.
- **Read API** (`functions/api/listings.js` + `functions/api/listing/[key].js`): search by city/zip/price/beds/baths/type/status with map bounds, paged, rate-limited via `_lib/ratelimit.js`, edge-cached 5 minutes. Never proxies Trestle live.
- **Pages** on the homepage template (TEMPLATE.md archetypes): `/homes/` (resource archetype, map + card grid, filters, the sticky CTA and funnel one tap away) and `/homes/<city>/<slug>-<ListingKey>/` detail pages (gallery, facts, attribution block per the checklist, "Ask Joshua Guerrero about this home" opening the Buy funnel with the address prefilled via `window.openFunnel(addr, "buy")`, schema.org `RealEstateListing` JSON-LD). Indexing is allowed (19.2.9) and the detail pages are the SEO upside: thousands of long-tail address pages under our domain.
- **Wire the existing promises.** The Buy tab's "See Homes" button and `/buyers/` route to `/homes/` with the visitor's city prefilled from `/api/geo`. Saved-search email alerts can ride the email platform (`_lib/email.js`) later.
- **Effort.** Sync worker + D1 schema + read API: 2 days. Search page + detail page on the template, mobile-first, compliance block, tests: 3 days. Paperwork (Trestle account, CRMLS license, Real approval): 1-3 weeks of waiting, so start it first.

## Recommendation and the order of operations

1. **Today (free, ~30 min):** In Matrix, Settings > IDX Configuration > Map Search, set the map to Orange + LA County, enable the sign-up form, copy the HTML. Build `/homes/` on the template with that frame in the body and point the Buy tab's "See Homes" + `/buyers/` at it. It is the one sanctioned iframe until path 4 lands; note it in CLAUDE.md as such.
2. **This week:** Open the Trestle Technology Provider account, request the CRMLS IDX connection, and file a Real support ticket asking the California broker to approve the CRMLS data license for drozq.com (attach the pre-filled IDX Request Form as well so either instrument is ready). Email licensing@crmls.org the same day asking (a) whether an agent-controlled site can license the RESO feed directly at h.api.crmls.org, and (b) to confirm the current Trestle fee ($85 on their page vs $100 on Trestle's).
3. **When the feed is approved:** build path 4 as sketched. Swap the iframe out of `/homes/` for the native search in the same commit that ships the sync worker.
4. **Skip the vendor path** unless the paperwork stalls past a month. If it does, Lofty at $50/mo through Real on `search.drozq.com` is the cheapest compliant fallback, and RealScout widgets are the zero-new-vendor option if the RealScout account can be licensed under Real.

## Contacts and links

- CRMLS IDX resources: https://go.crmls.org/idx-resources/
- IDX Link Generator: https://go.crmls.org/idx-link-generator/
- IDX Request Form (PDF): https://go.crmls.org/wp-content/uploads/2018/10/IDX_Request_Form.pdf, to Licensing@crmls.org / fax 909-978-3165
- 2026 vendor list: https://kb.crmls.org/wp-content/uploads/2019/04/2026_CRMLS_IDX_Vendors.pdf
- IDX Standards of Practice: https://kb.crmls.org/knowledgebase/idx-standards-of-practice/
- Rules & Policies (section 19.2): https://www.ocrealtors.org/sites/default/files/2024-01/CRMLS%20Rules%20and%20Regulations.pdf
- CRMLS dev docs (own API): https://devdocs.crmls.org/start/ (licensing@crmls.org, then api@crmls.org)
- Trestle: https://www.cotality.com/products/trestle, docs https://trestle-documentation.corelogic.com/web-api/, pricing https://trestle-documentation.corelogic.com/data-pricing/, support trestlesupport@cotality.com
- Real Brokerage support (broker signature): https://support.therealbrokerage.com/
- DRE record confirming the responsible broker: https://www2.dre.ca.gov/PublicASP/pplinfo.asp?License_id=02267255

## Decision and status (2026-09-02, Joshua): no vendor, straight from CRMLS

Joshua's ruling: no IDX vendor and no reseller. The feed comes from CRMLS directly (the CRMLS RESO OData Web API, token endpoint `https://soc.crmls.org/connect/token`, client-credentials grant, production `https://h.api.crmls.org/Reso/OData/`, docs at devdocs.crmls.org). Trestle is the fallback only if CRMLS says direct is not offered.

Identifiers (from the Matrix roster, 2026-09-02): agent login ID **LGGUERJOS**, AOR Laguna, DRE 02267255; office **LGRBT**, Real Brokerage Technologies, Inc., office DRE 02022092, office contact on the CRMLS roster bob.watson@therealbrokerage.com (619-248-6434, 8030 La Mesa Blvd #502, La Mesa). Real's signature desk: casign@therealbrokerage.com; California broker team cabroker@therealbrokerage.com; designated broker Rachel Stalnaker.

Two drafts sit in guerrerojoshua720@gmail.com, ready to send, each with the pre-filled CRMLS IDX Request Form attached (`Downloads/CRMLS_IDX_Request_Form_drozq_prefilled.pdf`):

1. To licensing@crmls.org, cc api@crmls.org: the direct RESO Web API IDX license request (agreement + Participant authorization, API account, fee, Trestle-not-required confirmation, non-display field list), the 19.2 compliance commitments, and the 19.2.18 notice that `/homes/` already displays the Matrix IDX frame (ID 131c38ac).
2. To casign@therealbrokerage.com, cc cabroker@ + bob.watson@: the broker-of-record signature on the form and, later, the data license agreement; states that Joshua owns compliance and every fee.

When CRMLS answers: sign whatever they send the same day, forward the license to casign@ for Real's countersignature, then build step 3 of the plan (sync worker, D1, `/homes/` native search) against the CRMLS endpoint instead of Trestle.
