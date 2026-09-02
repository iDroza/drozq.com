// Tests for the Fello integration: the tag vocabulary, the outbound push from
// /api/lead (create, duplicate, skip rules), the webhook receiver (signature,
// dedupe, FormSubmission -> /api/lead, hot signals -> alert + FUB, unsubscribe
// -> paused drip, refresh -> FUB PUT), and the engagement readback (gate,
// ranking, cache). Mocked fetch, real-SQLite D1 stand-in, no network.
//
// Run:  node scripts/test_fello.mjs
import { createHmac } from "node:crypto";
import { onRequestPost as leadPost } from "../functions/api/lead.js";
import { onRequestPost as webhookPost, extractContactRef, formSubmissionToLead, describeEvent } from "../functions/api/fello/webhook.js";
import { onRequestGet as engagementGet, pickFelloFubFields } from "../functions/api/fello/engagement.js";
import { felloTagsFor, felloShouldPush, buildFelloContact, verifyFelloSignature, summarizeFelloContact, FELLO_TAGS } from "../functions/_lib/fello.js";
import { memoryD1, makeContext, checker } from "./_test_d1.mjs";
import { onRequestPost as emailInit } from "../functions/api/email/init.js";

// Bootstrap the email platform schema (subscribers etc.) the way /api/email/init does.
async function initSchema(db, secret) {
  const c = makeContext(new Request("https://drozq.com/api/email/init", { method: "POST", headers: { authorization: "Bearer " + secret } }), { EMAIL_DB: db, EMAIL_SECRET: secret });
  const r = await emailInit(c);
  if (r.status !== 200) throw new Error("init failed " + r.status);
}

const { check, done } = checker();

const SECRET_B64 = Buffer.from("0123456789abcdef0123456789abcdef").toString("base64");
const CHANNELS = { TO_EMAIL: "josh@drozq.com", FROM_EMAIL: "leads@drozq.com", MAILCHANNELS_API_KEY: "k" };

// --- fetch mock ---------------------------------------------------------------
let calls = [];
let felloContacts = {};   // email -> contact payload for GET /contact
let felloCreateStatus = 200;
let fubPeople = {};       // email -> person
globalThis.fetch = async (url, opts) => {
  const u = String(url);
  const method = (opts && opts.method) || "GET";
  const body = opts && opts.body ? String(opts.body) : "";
  calls.push({ u, method, body, headers: (opts && opts.headers) || {} });
  if (u.includes("mailchannels")) return new Response("{}", { status: 202 });
  if (u.startsWith("https://api.fello.ai/public/v1/contact") && method === "POST" && !/\/tags|\/property/.test(u)) {
    const b = JSON.parse(body);
    if (felloCreateStatus === 400) return new Response(JSON.stringify({ code: "DuplicateContact", message: "exists" }), { status: 400 });
    return new Response(JSON.stringify({ contact: { contactId: "cid-new", email: b.email, tags: b.tags }, warnings: [] }), { status: 200 });
  }
  if (u.startsWith("https://api.fello.ai/public/v1/contact?") && method === "GET") {
    const email = decodeURIComponent((/emailId=([^&]+)/.exec(u) || [])[1] || "");
    const id = (/contactId=([^&]+)/.exec(u) || [])[1] || "";
    const c = felloContacts[email] || Object.values(felloContacts).find((x) => x.contactId === id);
    if (!c) return new Response(JSON.stringify({ code: "ContactDoesNotExist", message: "nf" }), { status: 404 });
    return new Response(JSON.stringify(c), { status: 200 });
  }
  if (/api\.fello\.ai\/public\/v1\/contact\/[^/]+\/(tags|property)$/.test(u)) return new Response(JSON.stringify({ tags: [] }), { status: 200 });
  if (u.startsWith("https://api.followupboss.com/v1/events")) return new Response("{}", { status: 201 });
  if (u.startsWith("https://api.followupboss.com/v1/people?")) {
    const email = decodeURIComponent((/email=([^&]+)/.exec(u) || [])[1] || "");
    const p = fubPeople[email];
    return new Response(JSON.stringify({ people: p ? [p] : [] }), { status: 200 });
  }
  if (/api\.followupboss\.com\/v1\/people\/\d+$/.test(u) && method === "PUT") return new Response("{}", { status: 200 });
  if (u.includes("/api/lead")) {
    // the webhook's internal lead post: run the real handler
    const c = makeContext(new Request(u, { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body }), currentEnv);
    const r = await leadPost(c);
    await Promise.all(c._waits);
    return r;
  }
  if (u.includes("posthog") || u.includes("t.drozq.com")) return new Response("{}", { status: 200 });
  return new Response("{}", { status: 200 });
};
let currentEnv = {};

function formRequest(fields) {
  const body = new URLSearchParams();
  for (const [k, v] of Object.entries(fields)) body.set(k, v);
  return new Request("https://drozq.com/api/lead", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: body.toString() });
}
async function submitLead(env, fields) {
  currentEnv = env;
  const c = makeContext(formRequest(fields), env);
  const r = await leadPost(c);
  const d = await r.json();
  await Promise.all(c._waits);
  return { status: r.status, d };
}
function sign(raw) {
  return createHmac("sha256", Buffer.from(SECRET_B64, "base64")).update(raw).digest("base64");
}
async function postWebhook(env, payload, sigOverride) {
  currentEnv = env;
  const raw = JSON.stringify(payload);
  const req = new Request("https://drozq.com/api/fello/webhook", {
    method: "POST", headers: { "content-type": "application/json", "fello-webhook-signature": sigOverride === undefined ? sign(raw) : sigOverride }, body: raw
  });
  const c = makeContext(req, env);
  const r = await webhookPost(c);
  const d = await r.json();
  await Promise.all(c._waits);
  return { status: r.status, d, waits: c._waits.length };
}
function captureConsole() {
  const lines = [];
  const oe = console.error, ol = console.log;
  console.error = (m) => lines.push(String(m));
  console.log = (m) => lines.push(String(m));
  return { lines, restore() { console.error = oe; console.log = ol; } };
}
const felloCalls = () => calls.filter((c) => c.u.startsWith("https://api.fello.ai"));
const fubCalls = () => calls.filter((c) => c.u.startsWith("https://api.followupboss.com"));
const mailCalls = () => calls.filter((c) => c.u.includes("mailchannels"));

const LEAD = { name: "Pat Sample", email: "seller@example.com", phone: "(949) 555-0134", consent: "yes", intent: "Home Valuation", city: "Irvine", state: "CA", source_page: "/sellers/", full_address: "1 Example Way, Irvine, CA 92620", timeline: "Yes, in 1-3 months", gclid: "abc" };

console.log("\n== tag vocabulary ==");
{
  const tags = felloTagsFor({ intent: "Home Valuation", timeline: "Yes, in 1-3 months", sourcePage: "/sellers/", gclid: "x" });
  check("sell funnel lead tags", JSON.stringify(tags) === JSON.stringify(["Drozq Website", "Seller", "Drozq: Sell", "Timeline: 1-3 mo", "Page: sellers", "Paid: Google"]), tags);
  const buy = felloTagsFor({ intent: "Home Purchase", timeline: "", sourcePage: "https://drozq.com/", gclid: "" });
  check("buy lead tags (home page, organic)", JSON.stringify(buy) === JSON.stringify(["Drozq Website", "Buyer", "Drozq: Buy", "Page: home"]), buy);
  const both = felloTagsFor({ intent: "Home Sale + Purchase", timeline: "Yes, immediately", sourcePage: "/california/index.html" });
  check("sell + buy carries both roles", both.includes("Seller") && both.includes("Buyer") && both.includes("Drozq: Sell + Buy") && both.includes("Timeline: Now") && both.includes("Page: california"), both);
  check("valuation / net sheet / one tap modes", felloTagsFor({ intent: "Home Valuation Lead" }).includes("Drozq: Valuation") && felloTagsFor({ intent: "Seller Net Sheet" }).includes("Drozq: Net Sheet") && felloTagsFor({ intent: "Google One Tap Lead" }).includes("Drozq: One Tap"), null);
  check("newsletter never pushes", felloShouldPush({ email: "a@b.co", intent: "Field Notes Subscribe" }) === false, null);
  check("Fello-originated leads never loop", felloShouldPush({ email: "a@b.co", intent: "Fello Seller Lead: Home Value Lead" }) === false && felloShouldPush({ email: "a@b.co", intent: "Home Valuation", referralSource: "Fello" }) === false, null);
  check("ordinary lead pushes", felloShouldPush({ email: "a@b.co", intent: "Home Valuation" }) === true, null);
  const body = buildFelloContact({ email: "A@B.co", name: "Pat Sample", phone: "+1 (949) 555-0134", address: "1 Example Way, Irvine, CA 92620", intent: "Home Valuation", createdAt: "2026-09-02T00:00:00.000Z" });
  check("contact body: lowercased email, E.164 phone, crm link fields", body.email === "a@b.co" && body.phone === "+19495550134" && body.name === "Pat Sample" && body.address === "1 Example Way, Irvine, CA 92620" && body.crmFields.source === "drozq.com" && body.crmFields.name === "FollowUpBoss", body);
  const ph = buildFelloContact({ email: "a@b.co", phone: "0000000000", name: "Website Lead (name not provided)", intent: "Google One Tap Lead" });
  check("placeholder phone + placeholder name are dropped", ph.phone === undefined && ph.name === undefined, ph);
}

console.log("\n== /api/lead NEVER pushes to Fello (Joshua's order, 2026-09-02) ==");
{
  calls = []; felloCreateStatus = 200;
  const env = Object.assign({ EMAIL_DB: memoryD1() }, CHANNELS);
  const r0 = await submitLead(env, LEAD);
  check("no FELLO_API_KEY -> lead accepted, no Fello call", r0.status === 200 && felloCalls().length === 0, felloCalls().length);

  calls = [];
  const envF = Object.assign({ EMAIL_DB: memoryD1(), FELLO_API_KEY: "fk" }, CHANNELS);
  const cap = captureConsole();
  const r = await submitLead(envF, LEAD);
  cap.restore();
  check("WITH FELLO_API_KEY -> lead accepted, still no Fello call", r.status === 200 && felloCalls().length === 0, felloCalls().map((c) => c.method + " " + c.u));
  check("no LEAD_FELLO_* marker logged", !cap.lines.some((l) => l.startsWith("LEAD_FELLO")), cap.lines.filter((l) => l.includes("FELLO")));
  calls = [];
  await submitLead(envF, Object.assign({}, LEAD, { intent: "Home Purchase", email: "buyer@example.com" }));
  await submitLead(envF, Object.assign({}, LEAD, { intent: "Home Valuation Lead", email: "val@example.com" }));
  await submitLead(envF, Object.assign({}, LEAD, { intent: "Seller Net Sheet", email: "ns@example.com" }));
  check("buy / valuation / net sheet leads: no Fello call either", felloCalls().length === 0, felloCalls().length);

  // The library function still works for the CLI, and still refuses the loops.
  check("pushLeadToFello skip rules stay intact for CLI use", felloShouldPush({ email: "a@b.co", intent: "Field Notes Subscribe" }) === false && felloShouldPush({ email: "a@b.co", intent: "Fello Seller Lead: x" }) === false, null);
}

console.log("\n== webhook: signature + dedupe ==");
{
  const env = Object.assign({ EMAIL_DB: memoryD1(), FELLO_CLIENT_SECRET: SECRET_B64, FELLO_API_KEY: "fk" }, CHANNELS);
  check("HMAC verifier matches the docs' node sample", await verifyFelloSignature(SECRET_B64, '{"events":[]}', sign('{"events":[]}')) === true && await verifyFelloSignature(SECRET_B64, '{"events":[]}', "nope") === false, null);
  const bad = await postWebhook(env, { events: [] }, "bad");
  check("bad signature -> 401, nothing scheduled", bad.status === 401 && bad.waits === 0, bad);
  const none = await postWebhook(Object.assign({}, env, { FELLO_CLIENT_SECRET: "" }), { events: [] });
  check("missing client secret -> 503", none.status === 503, none);
  const empty = await postWebhook(env, { events: [] });
  check("valid empty batch -> 200 received:0", empty.status === 200 && empty.d.received === 0, empty);
  calls = [];
  const ev = { events: [{ eventType: "TagsRemoved", eventDate: "2026-09-02T00:00:00.000Z", data: { contactInfo: { contactId: "c1", emailId: "x@example.com" }, tagsRemovedInfo: { tagsRemoved: ["OLD"] } } }] };
  const cap = captureConsole();
  const a = await postWebhook(env, ev);
  const b = await postWebhook(env, ev);
  cap.restore();
  check("same event replayed is deduped", a.status === 200 && b.status === 200 && cap.lines.some((l) => l.startsWith("FELLO_WEBHOOK_DUPLICATE")), cap.lines);
}

console.log("\n== webhook: FormSubmission -> the lead pipeline ==");
{
  calls = []; felloCreateStatus = 200;
  const env = Object.assign({ EMAIL_DB: memoryD1(), FELLO_CLIENT_SECRET: SECRET_B64, FELLO_API_KEY: "fk", FOLLOWUPBOSS_API_KEY: "fub" }, CHANNELS);
  const event = { eventType: "FormSubmission", eventDate: "2026-09-02T01:02:03.000Z", data: {
    contactInfo: { contactId: "c-form", propertyId: "", emailId: "john@example.com", assignedUserEmailId: "josh@drozq.com" },
    formSubmissionInfo: { leadType: "Home Value Lead", sourceType: "Landing Page", sourceDetail: "My Home Value Landing Page", referrerUrl: "https://homes.drozq.com/value",
      formData: { firstName: "John", lastName: "Doe", phone: "(949) 555-0199", emailId: "john@example.com", address: "2 Sample Ct, Irvine, CA 92620",
        addressComponents: { streetAddress: "2 Sample Ct", city: "Irvine", state: "CA", zip: "92620" }, beds: 3, sqft: 1800, saleTimeline: "Less than 3 months", homeWorth: "1250000", message: "Call me" } } } };
  const fields = formSubmissionToLead(event, "abc123");
  check("form maps to a seller intent with Fello source + consent", fields.intent === "Fello Seller Lead: Home Value Lead" && fields.email === "john@example.com" && fields.first_name === "John" && fields.full_address === "2 Sample Ct, Irvine, CA 92620" && fields.timeline === "Less than 3 months" && fields.referral_source === "Fello" && fields.consent === "yes" && fields.submission_id === "fello-abc123" && fields.message.includes("homeWorth: 1250000"), fields);
  const cap = captureConsole();
  const r = await postWebhook(env, { events: [event] });
  cap.restore();
  const leadCall = calls.find((c) => c.u.includes("/api/lead"));
  check("webhook 200 and the lead was posted internally", r.status === 200 && Boolean(leadCall), r);
  check("lead pipeline ran: alert email + FUB Seller Inquiry", mailCalls().length === 1 && fubCalls().some((c) => c.body.includes("Seller Inquiry")), { mail: mailCalls().length, fub: fubCalls().map((c) => c.u) });
  check("no Fello contact write of any kind from the lead pipeline", !felloCalls().some((c) => c.method === "POST"), felloCalls().map((c) => c.method + " " + c.u));
  check("FELLO_WEBHOOK_FORM_LEAD logged", cap.lines.some((l) => l.startsWith("FELLO_WEBHOOK_FORM_LEAD status=200")), cap.lines.filter((l) => l.includes("FELLO")));
  const noEmail = { eventType: "FormSubmission", eventDate: "2026-09-02T01:02:04.000Z", data: { formSubmissionInfo: { formData: { firstName: "No", lastName: "Mail" } } } };
  calls = [];
  const cap2 = captureConsole();
  await postWebhook(env, { events: [noEmail] });
  cap2.restore();
  check("a form without an email is skipped, not posted", !calls.some((c) => c.u.includes("/api/lead")) && cap2.lines.some((l) => l.startsWith("FELLO_WEBHOOK_FORM_NO_EMAIL")), cap2.lines);
}

console.log("\n== webhook: hot signals ==");
{
  calls = [];
  felloContacts = { "hot@example.com": { contactId: "c-hot", name: "Hot Lead", email: "hot@example.com", phone: "+19495550101", leadScore: 88, tags: ["FELLO HIGH OWNER MATCH"],
    engagement: { numOfDashboardClicks: 2, lastDashboardClickedDate: new Date().toISOString(), numOfEmailClicks: 1, numOfDashboardViews: 5, numOfEmailOpens: 3 },
    properties: [{ propertyId: "p1", address: { streetAddress: "9 Hot St", city: "Irvine", state: "CA", zip: "92620" } }] } };
  const env = Object.assign({ EMAIL_DB: memoryD1(), FELLO_CLIENT_SECRET: SECRET_B64, FELLO_API_KEY: "fk", FOLLOWUPBOSS_API_KEY: "fub" }, CHANNELS);
  const ev = { eventType: "DashboardClick", eventDate: "2026-09-02T02:00:00.000Z", data: { contactInfo: { contactId: "c-hot", emailId: "hot@example.com" }, dashboardClickInfo: { source: "Dashboard", sourceDetail: "cash_offer_cta" } } };
  const cap = captureConsole();
  const r = await postWebhook(env, { events: [ev] });
  cap.restore();
  const mail = mailCalls()[0] && JSON.parse(mailCalls()[0].body);
  check("hot signal -> alert email to TO_EMAIL with name, score, phone, property", r.status === 200 && mail && mail.personalizations[0].to[0].email === "josh@drozq.com" && /Fello hot: Hot Lead/.test(mail.subject) && mail.content.some((c) => c.value.includes("88") && c.value.includes("9 Hot St") && c.value.includes("+19495550101")), mail && mail.subject);
  const fub = fubCalls().find((c) => c.u.endsWith("/events"));
  const fubBody = fub && JSON.parse(fub.body);
  check("hot signal -> FUB General Inquiry tagged Fello Hot", fubBody && fubBody.type === "General Inquiry" && fubBody.person.tags.includes(FELLO_TAGS.hot) && fubBody.person.emails[0].value === "hot@example.com" && /cash_offer_cta/.test(fubBody.message), fubBody);
  check("describeEvent names the CTA", describeEvent(ev).includes("cash_offer_cta"), describeEvent(ev));
  check("FELLO_WEBHOOK_HOT logged with masked email", cap.lines.some((l) => l.startsWith("FELLO_WEBHOOK_HOT") && l.includes("h***@example.com")), cap.lines);

  calls = [];
  const felix = { eventType: "FelixAIHandoff", eventDate: "2026-09-02T02:01:00.000Z", data: { contactInfo: { contactId: "c-hot", emailId: "hot@example.com" }, felixAIHandoffInfo: { reason: "wants to list" } } };
  await postWebhook(env, { events: [felix] });
  const fub2 = fubCalls().find((c) => c.u.endsWith("/events"));
  check("Felix handoff adds the Fello Handoff tag", fub2 && JSON.parse(fub2.body).person.tags.includes("Fello Handoff"), fub2 && fub2.body);
}

console.log("\n== webhook: unsubscribe pauses the drip, refresh patches FUB ==");
{
  const db = memoryD1();
  await initSchema(db, "adm");
  const env = Object.assign({ EMAIL_DB: db, EMAIL_SECRET: "adm", EMAIL_DRY_RUN: "1", FELLO_CLIENT_SECRET: SECRET_B64, FELLO_API_KEY: "fk", FOLLOWUPBOSS_API_KEY: "fub" }, CHANNELS);
  await submitLead(env, Object.assign({}, LEAD, { email: "drip@example.com" }));
  const before = await db.prepare("SELECT status FROM subscribers WHERE email = 'drip@example.com'").first();
  const ev = { eventType: "ContactUnsubscribed", eventDate: "2026-09-02T03:00:00.000Z", data: { contactInfo: { contactId: "c-u", emailId: "drip@example.com" }, unsubscribedInfo: { emailUnsubscribedAt: "2026-09-02T03:00:00.000Z" } } };
  await postWebhook(env, { events: [ev] });
  const after = await db.prepare("SELECT status FROM subscribers WHERE email = 'drip@example.com'").first();
  check("ContactUnsubscribed -> subscriber paused (was active)", before && before.status === "active" && after && after.status === "paused", { before, after });

  calls = [];
  fubPeople = { "drip@example.com": { id: 4242, tags: ["Drozq Website"] } };
  felloContacts = { "drip@example.com": { contactId: "c-u", name: "Drip Lead", email: "drip@example.com", phone: "+19495550177", tags: ["FELLO HIGH EQUITY", "Drozq Website"], engagement: {}, properties: [] } };
  const enr = { eventType: "ContactEnriched", eventDate: "2026-09-02T03:01:00.000Z", data: { contactInfo: { contactId: "c-u", emailId: "drip@example.com" } } };
  await postWebhook(env, { events: [enr] });
  const put = fubCalls().find((c) => c.method === "PUT");
  const putBody = put && JSON.parse(put.body);
  check("ContactEnriched -> FUB person PUT with merged tags + phone, no timeline event", put && put.u.endsWith("/people/4242") && putBody.tags.includes("Drozq Website") && putBody.tags.includes("FELLO HIGH EQUITY") && putBody.tags.includes("Fello") && putBody.phones[0].value === "+19495550177" && !fubCalls().some((c) => c.u.endsWith("/events")), putBody);

  calls = [];
  const tg = { eventType: "TagsAdded", eventDate: "2026-09-02T03:02:00.000Z", data: { contactInfo: { contactId: "c-u", emailId: "drip@example.com" }, tagsAddedInfo: { tagsAdded: ["HOT LEAD"] } } };
  await postWebhook(env, { events: [tg] });
  const put2 = fubCalls().find((c) => c.method === "PUT");
  check("TagsAdded mirrors onto the FUB person", put2 && JSON.parse(put2.body).tags.includes("HOT LEAD"), put2 && put2.body);
}

console.log("\n== engagement readback ==");
{
  const db = memoryD1();
  await initSchema(db, "adm");
  const env = Object.assign({ EMAIL_DB: db, EMAIL_SECRET: "adm", EMAIL_DRY_RUN: "1", FELLO_API_KEY: "fk", FOLLOWUPBOSS_API_KEY: "fub" }, CHANNELS);
  for (const e of ["a@example.com", "b@example.com", "c@example.com"]) await submitLead(env, Object.assign({}, LEAD, { email: e }));
  await submitLead(env, Object.assign({}, LEAD, { email: "news@example.com", intent: "Field Notes Subscribe" }));
  const now = Date.now();
  felloContacts = {
    "a@example.com": { contactId: "ca", name: "A Lead", email: "a@example.com", leadScore: 40, tags: [], engagement: { numOfDashboardViews: 1, lastDashboardViewedDate: new Date(now - 2 * 86400000).toISOString() }, properties: [] },
    "b@example.com": { contactId: "cb", name: "B Lead", email: "b@example.com", leadScore: 90, tags: ["FELLO HIGH EQUITY"], engagement: { numOfEmailClicks: 1, lastEmailClickDate: new Date(now - 3600000).toISOString() }, properties: [] }
  };
  fubPeople = { "b@example.com": { id: 77, tags: [], customFelloHomeValue: 1450000, customFelloEstimatedEquity: 620000, customUnrelated: "x", stage: "Lead" } };
  calls = [];
  const denied = await engagementGet(makeContext(new Request("https://drozq.com/api/fello/engagement"), env));
  check("no bearer -> 401", denied.status === 401, denied.status);
  const req = () => new Request("https://drozq.com/api/fello/engagement?days=30&limit=50", { headers: { authorization: "Bearer adm" } });
  const r = await engagementGet(makeContext(req(), env));
  const d = await r.json();
  check("summary counts: 3 leads checked (newsletter excluded), 2 matched, 1 hot, 1 warm, avg 65", r.status === 200 && d.summary.leadsChecked === 3 && d.summary.matched === 2 && d.summary.hot === 1 && d.summary.warm === 1 && d.summary.avgLeadScore === 65, d.summary);
  check("ranked hot first, unmatched last", d.leads[0].email === "b@example.com" && d.leads[0].hot === true && d.leads[1].email === "a@example.com" && d.leads[2].matched === false, d.leads.map((l) => l.email));
  check("hot lead decorated with the Fello-fed FUB custom fields only", d.leads[0].crm && d.leads[0].crm.fubId === 77 && d.leads[0].crm.fields.customFelloHomeValue === 1450000 && d.leads[0].crm.fields.customUnrelated === undefined, d.leads[0].crm);
  check("signals ride along", d.leads[0].signals.includes("FELLO HIGH EQUITY"), d.leads[0].signals);
  calls = [];
  const r2 = await engagementGet(makeContext(req(), env));
  const d2 = await r2.json();
  check("second read served from the D1 cache (no Fello calls)", d2.cached === true && felloCalls().length === 0, { cached: d2.cached, fello: felloCalls().length });
  const r3 = await engagementGet(makeContext(new Request("https://drozq.com/api/fello/engagement?days=30&limit=50&fresh=1", { headers: { authorization: "Bearer adm" } }), env));
  const d3 = await r3.json();
  check("fresh=1 bypasses the cache", d3.cached === false && felloCalls().length === 3, { cached: d3.cached, fello: felloCalls().length });
  check("pickFelloFubFields ignores non-custom keys", Object.keys(pickFelloFubFields({ id: 1, customFelloScore: 5, name: "x" })).join() === "customFelloScore", null);
  const s = summarizeFelloContact({ engagement: { lastEmailClickDate: new Date(now - 10 * 86400000).toISOString() }, leadScore: 10 }, now, 7);
  check("a click older than the window is not hot", s.hot === false && s.lastClickAt !== null, s);
}

console.log("\n== misc ==");
{
  check("extractContactRef reads contactInfo and validates the email", JSON.stringify(extractContactRef({ data: { contactInfo: { contactId: "x", emailId: "BAD" } } })) === JSON.stringify({ email: "", contactId: "x", propertyId: "", assignedUser: "" }), null);
}

done();
