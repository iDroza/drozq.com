const json = (data, status = 200, extraHeaders = {}) =>
  new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=UTF-8",
      "cache-control": "private, max-age=3600",
      ...extraHeaders
    }
  });

// Returns the visitor's geolocation as inferred by Cloudflare from the request IP.
// request.cf is populated by Cloudflare on every Pages Function invocation; no
// external service is called. Used by /index.html to swap the realtor.com clone's
// hardcoded "Columbus, OH" defaults with the visitor's real city.
export async function onRequest(context) {
  try {
    const cf = context.request.cf || {};
    return json({
      city: cf.city || "",
      region: cf.region || "",
      regionCode: cf.regionCode || "",
      country: cf.country || "",
      postalCode: cf.postalCode || "",
      timezone: cf.timezone || ""
    });
  } catch (err) {
    return json({ city: "", region: "", regionCode: "", country: "", postalCode: "", timezone: "" }, 200);
  }
}
