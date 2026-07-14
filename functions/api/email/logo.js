// The brand logo, served through a Function route for use inside emails.
// Cloudflare Hotlink Protection is ON for drozq.com: any image path with an
// image extension 403s when the Referer is a foreign site, which includes
// webmail clients rendering an email. This route has no image extension, so
// hotlink protection never matches it; the bytes come from the project's own
// static assets via the ASSETS binding. Never reference /media/*.png directly
// inside an email template.

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const v = url.searchParams.get("v");
  const file = v === "dark"
    ? "brand-logo-red-white.png"  // dark-mode email variant: red house, white text
    : v === "white"
      ? "brand-logo-white.png"    // all-white variant
      : "brand-header-logo.png";
  const asset = await context.env.ASSETS.fetch("https://drozq.com/media/images/" + file);
  if (!asset.ok) return new Response("logo unavailable", { status: 502 });
  return new Response(asset.body, {
    status: 200,
    headers: {
      "content-type": "image/png",
      "cache-control": "public, max-age=604800",
      "access-control-allow-origin": "*"
    }
  });
}
