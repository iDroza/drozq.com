# Fello API: what the keys can do, and what they cannot

*Researched 2026-09-02 against docs.fello.ai (rendered), the Fello help center, the integrations hub, and a live probe of the key. Rendered for Joshua at `/fello/` (noindex). CLI: `scripts/fello.py`. Credentials: gitignored `scripts/.fello_secret` (never in the repo).*

## The one-paragraph version

Fello's public API is a **contact-sync API, not a data API**. It lets an outside system push contacts, tags and property addresses INTO Fello, read one contact back at a time (by email or id) with its engagement counters and lead score, and subscribe to ten webhook events that Fello pushes OUT when a contact does something. It does not expose home values, equity, property facts, lists, searches, exports, email sending, or workflow triggers. Everything Fello is good at (the home-value dashboards, the nurture email, the postcards, Felix AI calling) runs inside Fello; the API is how you feed it and how you hear back.

## Credentials

- **API key**: sent as the `x-api-key` header on every request. Full account access, no scopes, no OAuth. Rotate in Fello > Settings > Connected Apps > the Custom App.
- **Client secret**: NOT used for API calls. It is the HMAC key for verifying inbound webhooks: `base64(HMAC_SHA256(base64decode(secret), raw_body))` must equal the `fello-webhook-signature` header.
- Base URL: `https://api.fello.ai/public/v1` (`api.hifello.com` answers identically; `api-dev.fello.ai` is listed in the docs but there is no documented sandbox account).
- Live probe 2026-09-02: key accepted, `GET /webhooks` returned `{"webhooks":[]}` (nothing registered yet), unauthenticated requests get 401.

## Endpoints (all twelve)

| Method | Path | What it does |
|---|---|---|
| POST | `/contact` | Create a contact: `email` (required), `name`, `phone`, `tags[]`, `address` (one property), `crmFields{name,url,source,stage,createdDate}`, `assignedUserEmailId`. Returns the full contact + `warnings[]` (e.g. `InvalidInputAddress`). |
| GET | `/contact?emailId=` or `?contactId=` | Read ONE contact: identity, `emailStatus` (Valid / Invalid / Pending), `recordStatus` (Active / Monitored), `createdAt`, `tags`, `engagement{}` counters, `properties[]` (parsed address incl. county), `crmFields`, `leadScore`, `assignedUserEmailId`, `proofOfConsentUrl`. |
| PATCH | `/contact/{contactId}` | Update name / phone / email / crmFields / assigned user / recordStatus. Only fields sent are touched. |
| DELETE | `/contact/{contactId}` | Permanent delete of the contact and all its data. |
| POST | `/contact/{contactId}/tags` | Append tags. |
| PUT | `/contact/{contactId}/tags` | Replace the whole tag set. |
| DELETE | `/contact/{contactId}/tags` | Remove listed tags. |
| POST | `/contact/{contactId}/property` | Attach a property by free-text address (max 128 chars). Fello parses + enriches it asynchronously. |
| POST | `/contact/property/{propertyId}/archive` | Archive a property so it leaves active workflows. |
| GET | `/webhooks` | List subscriptions (`subscriptionId`, `url`, `eventType`, `status` Active / Removed / Failing). |
| POST | `/webhooks` | Subscribe `{url, eventType}`; HTTPS only; max 3 per event. |
| DELETE | `/webhooks/{subscriptionId}` | Unsubscribe. |

## Engagement counters on every contact read

`numOfFormSubmissions` / `lastFormSubmissionDate`, `numOfEmailSends` / `lastEmailSentDate`, `numOfEmailOpens` / `lastEmailOpenDate`, `numOfEmailClicks` / `lastEmailClickDate`, `numOfDashboardViews` / `lastDashboardViewedDate`, `numOfDashboardClicks` / `lastDashboardClickedDate`, plus `leadScore` (0-100). This is the only "intelligence" the API returns.

## Webhook events (Fello -> you)

Live: `FormSubmission`, `DashboardClick`, `EmailClick`, `PostcardScan`, `ContactUnsubscribed`, `ContactEnriched`, `ContactDetailsUpdated`, `TagsAdded`, `TagsRemoved`, `FelixAIHandoff`.
Announced, not yet available: Dashboard Viewed, Assigned User Changed, Note Added.

Delivery contract: JSON `{events:[{eventType, eventDate, data{...}}]}` POSTed to your HTTPS URL. Respond 2xx fast (the docs say 10 seconds in one place and 5 seconds in another: design for 5). Non-2xx is retried "at varying intervals" for up to 8 hours (one section says 4), then the message is lost. Repeatedly failing URLs are auto-unsubscribed with an email notice. The docs only publish a sample payload shape (`data.formData.firstName/lastName/phone...` for FormSubmission); capture real payloads with Webhook.site before coding parsers.

## Rate limits (confirmed live)

- App level, sliding 10-second window: GET 100 / 10s, writes (POST/PATCH/PUT/DELETE) 50 / 10s. Headers `X-RateLimit-Limit-10`, `X-RateLimit-Remaining-10`.
- Account level: 350,000 requests per day. Headers `X-RateLimit-Limit-Day`, `X-RateLimit-Remaining-Day` (plus `RateLimit-Reset` seconds).
- 429 on breach; back off exponentially. Limits can be raised by asking Fello.

## Errors

`{code, message}`; codes: `ContactDoesNotExist` (404), `PropertyDoesNotExist` (404), `InvalidAddress` (400), `DuplicateProperty` (400), `DuplicateContact` (400, same email already exists), `InvalidRequest` (400, with a `data` object explaining the validation). Server faults are 5xx.

## The limitations, honestly

1. **No list, search, filter, or export.** You cannot enumerate contacts. Reads are one-at-a-time by email or contactId, so any "pull my whole Fello database" job is impossible via the API (use the in-app CSV export or the FUB sync).
2. **No home value, equity, mortgage, or property facts.** Fello's AVM, the equity estimate, the "likely to sell" signal, and the enriched home facts never leave Fello through this API; `properties[]` carries the parsed address only. The native Follow Up Boss sync and the FUB embedded app are the only ways to see them outside Fello.
3. **No outbound actions.** Nothing here sends an email, a postcard, or a Felix call, and nothing starts a workflow directly. Tags are the only handle into Fello's segments and automations.
4. **No notes, no timeline writes, no lead-score writes.** `leadScore` is read-only. `crmFields` is a five-field bag (name, url, source, stage, createdDate) meant to link back to the CRM record, not a custom-field store.
5. **No sandbox.** `api-dev.fello.ai` appears in the docs but no test account is documented; every call hits the live account. `DuplicateContact` is keyed on email, so re-posting a lead is safe-ish (400, nothing created) but a changed email creates a second person.
6. **Webhooks: 3 subscriptions per event, HTTPS only, sample payloads only, retry window measured in hours.** A down receiver loses events after the window. Signature verification needs the base64-decoded secret (an easy off-by-one when porting the sample).
7. **One key = the whole account.** No scopes, no per-app permissions, no IP allow-list. Keep it in Cloudflare env vars and the gitignored secret file only.
8. **Enrichment is asynchronous.** After `POST /contact` with an address, home facts and `emailStatus` appear seconds later; a read immediately after the write can show `Pending` and an empty enrichment.
9. **Phone regex is NANP-shaped** (`^(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$`); the funnel's `+1 (949) 438-5948` format passes, the `0000000000` One Tap placeholder passes the regex but is useless in Fello (send no phone instead).
10. **Deletes are permanent and do not propagate** to the FUB sync (Fello's own guide says deletes never cross platforms).

## What the native FUB integration already covers (so the API does not have to)

Fello > App Marketplace > Follow Up Boss, using the FUB account OWNER's API key: two-way contact sync with per-field overwrite rules, user mapping, event mapping (Fello events -> FUB field / note updates), sync-limit filters. New Fello leads land in FUB as a "New Lead from Fello" note with lead type, contact details, property address, form details and a link to the Fello contact; source "Fello", tag by lead type (e.g. "Fello Home Value Lead"). The FUB embedded app shows Fello's contact + property intelligence inside FUB. Deletes never sync.

## What to build on drozq.com (in priority order)

1. **Every drozq lead into Fello.** In `functions/api/lead.js` `deliverLead`, add a best-effort `POST /contact` (email, name, phone, the Places-confirmed `full_address`, tags `Drozq Website` + `Seller` / `Buyer` + the funnel mode + timeline answer, `crmFields{name:"FollowUpBoss", url:<FUB person url when known>, source:"drozq.com", stage:"Lead", createdDate}`), gated on a `FELLO_API_KEY` env var exactly like `FOLLOWUPBOSS_API_KEY`. `DuplicateContact` then means "already nurturing", and Fello's home-value dashboard + monthly nurture takes over the long tail.
2. **`/api/fello/webhook` receiver** (HMAC-verified with `FELLO_CLIENT_SECRET`, 2xx in under 5 seconds, work behind `waitUntil`): `FormSubmission` -> the same lead pipeline as `/api/lead` (alert email, FUB event, drip enrollment) so Fello landing-page / widget leads are drozq leads; `DashboardClick` / `EmailClick` / `PostcardScan` / `FelixAIHandoff` -> a "hot" alert to Joshua + a FUB tag; `ContactUnsubscribed` -> `emailer pause` on the drozq drip; `ContactEnriched` / `ContactDetailsUpdated` -> refresh the FUB person. Register with `python scripts/fello.py webhooks add-all https://drozq.com/api/fello/webhook`.
3. **Tag discipline.** Decide the tag vocabulary once (mode, timeline, page of origin, campaign) because tags are the only lever into Fello segments and workflows.
4. **Lead-score readback for the dashboard.** The operating dashboard can read `leadScore` + engagement counters for the leads it already knows by email (one GET each, well inside 100 / 10s) and rank the call list by Fello engagement.

## Sources

- https://docs.fello.ai/ (Introduction, Authentication, Rate Limiting, Webhooks, Error Responses, Failure Handling, the twelve operation pages)
- https://fello.ai/knowledge/how-to-generate-a-fello-api-key
- https://fello.ai/knowledge/fello-follow-up-boss-integration-complete-guide
- https://fello.ai/knowledge/what-does-a-new-fello-lead-look-like-when-it-comes-into-your-crm
- https://integrations.fello.ai/
- https://fello.ai/pricing (Growth $499/mo, Scale $799/mo, Enterprise $2,000/mo; API access is not listed as tier-gated)
