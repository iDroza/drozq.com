// Durable, opaque first-party visitor identity for the returning-visitor
// system and gclid ad-attribution.
//
// Why this exists: the funnel's original returning-visitor system lived
// entirely in localStorage (30-day TTL coded in JS), and gclid lived in a
// document.cookie-set cookie (90-day max-age coded in JS). Both are fiction
// on Safari: Intelligent Tracking Prevention caps ALL script-writable
// storage (document.cookie AND localStorage, not just third-party cookies)
// to 7 days unless the visitor returns via a direct, interacted top-level
// navigation inside that window. A paid-search real estate visitor who
// clicks an ad, doesn't convert same-session, and comes back two weeks
// later on mobile Safari (the majority of this site's traffic) gets wiped
// clean: no gclid for attribution, no prefill, no recognition. This is
// exactly why a server-rendered CRM site "remembers" a returning visitor
// better than a static site doing everything in client JS: its cookies are
// (re)issued via HTTP Set-Cookie response headers, which ITP does NOT cap.
//
// The fix: functions/_middleware.js calls refreshVisitorCookies() on every
// request to re-issue both cookies via Set-Cookie (sliding expiry), which
// keeps them alive past the 7-day cap regardless of how long the visitor
// stays away, as long as they load *any* page on the site.
//
// drozq_vid: an opaque UUID, HttpOnly (page JS never touches it directly;
// the browser still sends it automatically on same-origin fetches), keys
// the returning_visitors D1 row in functions/api/visitor.js. Carries no PII
// itself.
// gclid: unchanged in shape from the original client-set cookie (the funnel
// JS still reads it via document.cookie for the client-side fallback), just
// also re-issued here so its window survives ITP the same way.

const VID_COOKIE = "drozq_vid";
const VID_MAX_AGE = 60 * 60 * 24 * 400; // 400 days: the practical cookie-lifetime ceiling
const GCLID_COOKIE = "gclid";
const GCLID_MAX_AGE = 60 * 60 * 24 * 90;

function parseCookies(request) {
  const out = {};
  const header = request.headers.get("Cookie") || request.headers.get("cookie") || "";
  header.split(";").forEach((part) => {
    const i = part.indexOf("=");
    if (i === -1) return;
    const k = part.slice(0, i).trim();
    const v = part.slice(i + 1).trim();
    if (!k) return;
    try {
      out[k] = decodeURIComponent(v);
    } catch (e) {
      out[k] = v;
    }
  });
  return out;
}

function newVid() {
  try {
    return crypto.randomUUID();
  } catch (e) {
    return "v" + Date.now().toString(36) + Math.random().toString(36).slice(2);
  }
}

function cookieHeader(name, value, maxAge, httpOnly) {
  let s = name + "=" + encodeURIComponent(value) + "; Path=/; Max-Age=" + maxAge + "; SameSite=Lax; Secure";
  if (httpOnly) s += "; HttpOnly";
  return s;
}

export function getVid(request) {
  return parseCookies(request)[VID_COOKIE] || "";
}

export function getCookieGclid(request) {
  return parseCookies(request)[GCLID_COOKIE] || "";
}

// Re-issues (or creates) both cookies on the outgoing response via
// Set-Cookie, with a fresh sliding expiry every visit. A `?gclid=` query
// param on this request always wins over a stored value (a fresh ad click
// re-attributes). Call from _middleware.js on the response from
// context.next(); mutates `response` in place (its Headers must already be
// a fresh, mutable instance -- see the middleware for why).
export function refreshVisitorCookies(request, response, url) {
  const cookies = parseCookies(request);
  const u = url || new URL(request.url);

  const vid = cookies[VID_COOKIE] || newVid();
  response.headers.append("Set-Cookie", cookieHeader(VID_COOKIE, vid, VID_MAX_AGE, true));

  const fromUrl = (u.searchParams.get("gclid") || "").trim();
  const gclid = fromUrl || cookies[GCLID_COOKIE] || "";
  if (gclid) {
    response.headers.append("Set-Cookie", cookieHeader(GCLID_COOKIE, gclid, GCLID_MAX_AGE, false));
  }

  return { vid, gclid };
}

export { VID_COOKIE, GCLID_COOKIE };
