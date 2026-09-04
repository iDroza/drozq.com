// Tests for the durable returning-visitor system: functions/_lib/visitorid.js,
// functions/_middleware.js, and functions/api/visitor.js.
//
// Run:  node scripts/test_visitor.mjs
import { getVid, getCookieGclid, refreshVisitorCookies } from "../functions/_lib/visitorid.js";
import { onRequest as middleware } from "../functions/_middleware.js";
import { onRequestGet as visitorGet, onRequestPost as visitorPost } from "../functions/api/visitor.js";
import { memoryD1, makeContext, checker } from "./_test_d1.mjs";

const { check, done } = checker();

function reqWithCookies(url, cookies, init) {
  const headers = Object.assign({}, (init && init.headers) || {});
  if (cookies) headers["Cookie"] = cookies;
  return new Request(url, Object.assign({}, init, { headers }));
}

function setCookies(response) {
  // Response.headers doesn't expose getAll() in the fetch spec; getSetCookie()
  // is available on modern Node/Workers Headers.
  return typeof response.headers.getSetCookie === "function"
    ? response.headers.getSetCookie()
    : [response.headers.get("set-cookie")].filter(Boolean);
}

console.log("\n== visitorid.js: cookie parsing + refresh ==");
{
  const req = reqWithCookies("https://drozq.com/", "drozq_vid=abc-123; gclid=OLDCLID; other=x");
  check("getVid reads drozq_vid", getVid(req) === "abc-123");
  check("getCookieGclid reads gclid", getCookieGclid(req) === "OLDCLID");

  const res = new Response("ok");
  const { vid, gclid } = refreshVisitorCookies(req, res, new URL(req.url));
  check("reuses the existing vid", vid === "abc-123");
  check("reuses the existing gclid absent a query param", gclid === "OLDCLID");
  const cookies = setCookies(res);
  check("Set-Cookie issued for both", cookies.length === 2, cookies);
  check("vid cookie is HttpOnly", cookies.some((c) => c.startsWith("drozq_vid=abc-123") && c.includes("HttpOnly")), cookies);
  check("gclid cookie is NOT HttpOnly (client JS still reads it)", cookies.some((c) => c.startsWith("gclid=OLDCLID") && !c.includes("HttpOnly")), cookies);
  check("vid cookie carries a long Max-Age", cookies.some((c) => c.includes("drozq_vid") && /Max-Age=34560000/.test(c)), cookies);
  check("gclid cookie carries the 90-day Max-Age", cookies.some((c) => c.includes("gclid=OLDCLID") && /Max-Age=7776000/.test(c)), cookies);
}

console.log("\n== visitorid.js: no cookies yet -> issues a fresh vid, no gclid without one ==");
{
  const req = new Request("https://drozq.com/about/");
  const res = new Response("ok");
  const { vid, gclid } = refreshVisitorCookies(req, res, new URL(req.url));
  check("a fresh vid is generated", typeof vid === "string" && vid.length > 10, vid);
  check("no gclid value -> no gclid Set-Cookie", gclid === "");
  const cookies = setCookies(res);
  check("only the vid cookie is set", cookies.length === 1, cookies);
}

console.log("\n== visitorid.js: fresh ?gclid= query wins over the stored cookie ==");
{
  const req = reqWithCookies("https://drozq.com/?gclid=NEWCLICK", "gclid=STALECLICK");
  const res = new Response("ok");
  const { gclid } = refreshVisitorCookies(req, res, new URL(req.url));
  check("URL gclid wins", gclid === "NEWCLICK");
}

console.log("\n== _middleware.js: refreshes cookies on a page request, skips static assets ==");
{
  const okNext = () => new Response("<html></html>", { headers: { "content-type": "text/html" } });
  const ctx1 = { request: new Request("https://drozq.com/sellers/"), next: async () => okNext() };
  const res1 = await middleware(ctx1);
  check("HTML route gets a Set-Cookie", setCookies(res1).length > 0, setCookies(res1));

  const ctx2 = { request: new Request("https://drozq.com/media/css/panda.css"), next: async () => new Response("body{}", { headers: { "content-type": "text/css" } }) };
  const res2 = await middleware(ctx2);
  check("static asset is skipped (no cookie work)", setCookies(res2).length === 0, setCookies(res2));

  // Anything that goes wrong while rebuilding/decorating the response (a
  // Cloudflare edge case like an immutable Headers on a cached asset) must
  // fall back to the original response untouched, never reject the request.
  const badRes = { status: 200, statusText: "OK", headers: new Headers(), get body() { throw new Error("boom"); } };
  const ctx3 = { request: new Request("https://drozq.com/"), next: async () => badRes };
  const res3 = await middleware(ctx3);
  check("a construction failure falls back to the original response, doesn't reject", res3 === badRes);
}

console.log("\n== /api/visitor GET: no vid cookie -> found:false, no throw ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const res = await visitorGet(makeContext(new Request("https://drozq.com/api/visitor"), env));
  const body = await res.json();
  check("found:false with no cookie", body.ok === true && body.found === false, body);
}

console.log("\n== /api/visitor POST: no vid cookie -> soft no_visitor_id, no throw ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const req = new Request("https://drozq.com/api/visitor", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: "a@b.com" }) });
  const res = await visitorPost(makeContext(req, env));
  const body = await res.json();
  check("soft-fails without a vid, still 200", res.status === 200 && body.ok === false && body.error === "no_visitor_id", body);
}

console.log("\n== /api/visitor POST -> GET round trip ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const vid = "test-vid-1";
  const cookie = "drozq_vid=" + vid;
  const address = { street: "123 Main St", city: "Irvine", state: "CA", zip: "92614", lat: 33.6, lng: -117.8, formatted: "123 Main St, Irvine, CA 92614" };

  const postReq = reqWithCookies("https://drozq.com/api/visitor", cookie, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ fullName: "Jane Doe", email: "jane@example.com", phone: "9494385948", gclid: "CLID123", address })
  });
  const postRes = await visitorPost(makeContext(postReq, env));
  const postBody = await postRes.json();
  check("POST accepted", postRes.status === 200 && postBody.ok === true, postBody);

  const table = await env.EMAIL_DB.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='returning_visitors'").first();
  check("returning_visitors table created lazily", !!table);

  const getReq = reqWithCookies("https://drozq.com/api/visitor", cookie);
  const getRes = await visitorGet(makeContext(getReq, env));
  const getBody = await getRes.json();
  check("GET finds the row", getBody.ok === true && getBody.found === true, getBody);
  check("fields round-trip", getBody.data.fullName === "Jane Doe" && getBody.data.email === "jane@example.com" && getBody.data.phone === "9494385948" && getBody.data.gclid === "CLID123", getBody.data);
  check("address round-trips as an object", getBody.data.address && getBody.data.address.formatted === address.formatted, getBody.data.address);

  // A different vid must never see this row.
  const otherReq = reqWithCookies("https://drozq.com/api/visitor", "drozq_vid=someone-else");
  const otherRes = await visitorGet(makeContext(otherReq, env));
  const otherBody = await otherRes.json();
  check("a different vid gets found:false", otherBody.found === false, otherBody);
}

console.log("\n== /api/visitor POST: partial update never blanks existing fields ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const vid = "test-vid-2";
  const cookie = "drozq_vid=" + vid;

  await visitorPost(makeContext(reqWithCookies("https://drozq.com/api/visitor", cookie, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ fullName: "Sam Seller", email: "sam@example.com" })
  }), env));

  // A later step only supplies phone (as the funnel does step by step).
  await visitorPost(makeContext(reqWithCookies("https://drozq.com/api/visitor", cookie, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ phone: "9495551212" })
  }), env));

  const res = await visitorGet(makeContext(reqWithCookies("https://drozq.com/api/visitor", cookie), env));
  const body = await res.json();
  check("name + email survive a phone-only follow-up POST", body.data.fullName === "Sam Seller" && body.data.email === "sam@example.com" && body.data.phone === "9495551212", body.data);
}

console.log("\n== /api/visitor GET: a row older than the 30-day TTL reads as not found ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const vid = "test-vid-3";
  const cookie = "drozq_vid=" + vid;
  await visitorPost(makeContext(reqWithCookies("https://drozq.com/api/visitor", cookie, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: "old@example.com" })
  }), env));

  const staleAt = Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 31;
  await env.EMAIL_DB.prepare("UPDATE returning_visitors SET updated_at = ?1 WHERE vid = ?2").bind(staleAt, vid).run();

  const res = await visitorGet(makeContext(reqWithCookies("https://drozq.com/api/visitor", cookie), env));
  const body = await res.json();
  check("31-day-old row reads as found:false", body.found === false, body);
}

console.log("\n== /api/visitor POST: rate limited after 30 requests in 10 minutes ==");
{
  const env = { EMAIL_DB: memoryD1() };
  const cookie = "drozq_vid=rl-vid";
  const ip = "203.0.113.55";
  let last = null;
  for (let i = 0; i < 31; i++) {
    const req = reqWithCookies("https://drozq.com/api/visitor", cookie, {
      method: "POST", headers: { "content-type": "application/json", "CF-Connecting-IP": ip },
      body: JSON.stringify({ email: "spam" + i + "@example.com" })
    });
    last = await visitorPost(makeContext(req, env));
  }
  check("31st POST in 10 minutes is rate limited", last.status === 429, last.status);
}

console.log("\n== /api/visitor: EMAIL_DB unbound degrades gracefully ==");
{
  const getRes = await visitorGet(makeContext(reqWithCookies("https://drozq.com/api/visitor", "drozq_vid=x"), {}));
  const getBody = await getRes.json();
  check("GET without EMAIL_DB -> found:false, no throw", getBody.ok === true && getBody.found === false, getBody);

  const postRes = await visitorPost(makeContext(reqWithCookies("https://drozq.com/api/visitor", "drozq_vid=x", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: "a@b.com" })
  }), {}));
  check("POST without EMAIL_DB -> 503 unconfigured", postRes.status === 503, postRes.status);
}

done();
