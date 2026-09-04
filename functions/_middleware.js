// Runs ahead of every Pages request. Re-issues the drozq_vid + gclid cookies
// via a Set-Cookie response header on every visit (see
// _lib/visitorid.js for why this, not document.cookie/localStorage, is what
// survives Safari ITP's 7-day cap on script-writable storage). Cheap by
// design: no D1, no upstream calls, just header work, so it's safe to run
// on every request; static asset requests are skipped outright since
// attribution/identity only matter for page + API navigations.

import { refreshVisitorCookies } from "./_lib/visitorid.js";

const SKIP_EXT = /\.(css|js|mjs|png|jpe?g|webp|gif|svg|ico|woff2?|ttf|eot|map|xml|txt|json|pdf|mp4|webm)$/i;

export async function onRequest(context) {
  const { request } = context;
  const response = await context.next();

  try {
    const url = new URL(request.url);
    if (SKIP_EXT.test(url.pathname)) return response;

    // Rebuild the Response so its Headers are a fresh, mutable instance --
    // the one context.next() hands back (e.g. for a static asset) can be a
    // read-only Headers object that throws on .append().
    const out = new Response(response.body, response);
    refreshVisitorCookies(request, out, url);
    return out;
  } catch (e) {
    console.error("VISITOR_COOKIE_MIDDLEWARE_FAILED " + ((e && e.message) || e));
    return response;
  }
}
