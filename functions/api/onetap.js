// Google One Tap / "Sign in with Google" lead capture.
//
// The homepage shows the Google One Tap prompt (see the ONE_TAP block in
// /index.html). When a visitor taps it, Google returns a signed ID token (a
// JWT). The browser POSTs that token here. This endpoint VERIFIES the token
// server-side (so a forged email can't be injected), pulls the visitor's real
// Google-verified email + name, and forwards it into the existing lead pipeline
// (/api/lead -> MailChannels email + optional Zapier) so One Tap leads land in
// the same inbox as form leads.
//
// One Tap returns email + name + a stable Google user id (sub). It NEVER
// returns a phone number, so these are email-only leads (placeholder phone).
//
// Optional env var: GOOGLE_ONETAP_CLIENT_ID. When set, the token's audience
// must match it (rejects tokens minted for other apps). Recommended: set it to
// the same client ID used in /index.html.

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8" }
  });

export async function onRequestPost(context) {
  try {
    const { request, env } = context;

    // 1) Read the credential from JSON or form body
    let body;
    const contentType = request.headers.get("Content-Type") || "";
    if (contentType.includes("application/json")) {
      body = await request.json();
    } else {
      const fd = await request.formData();
      body = Object.fromEntries(fd.entries());
    }

    const credential = String((body && body.credential) || "").trim();
    if (!credential) {
      return json({ ok: false, error: "missing_credential" }, 400);
    }

    // 2) Verify the Google ID token. Google's tokeninfo endpoint validates the
    //    signature + expiry and returns the decoded claims, erroring on anything
    //    invalid. We additionally pin issuer + audience below.
    const verifyResp = await fetch(
      "https://oauth2.googleapis.com/tokeninfo?id_token=" + encodeURIComponent(credential)
    );
    if (!verifyResp.ok) {
      return json({ ok: false, error: "invalid_token" }, 401);
    }
    const claims = await verifyResp.json();

    // 3) Issuer check
    const iss = String(claims.iss || "");
    if (iss !== "accounts.google.com" && iss !== "https://accounts.google.com") {
      return json({ ok: false, error: "bad_issuer" }, 401);
    }

    // 4) Audience check (only enforced when the env var is configured)
    const expectedAud = env.GOOGLE_ONETAP_CLIENT_ID;
    if (expectedAud && String(claims.aud || "") !== String(expectedAud)) {
      return json({ ok: false, error: "bad_audience" }, 401);
    }

    // 5) Expiry check (belt-and-suspenders; tokeninfo already enforces it)
    const now = Math.floor(Date.now() / 1000);
    if (claims.exp && Number(claims.exp) < now) {
      return json({ ok: false, error: "expired_token" }, 401);
    }

    // 6) Email must be present and verified. tokeninfo returns strings.
    const email = String(claims.email || "").trim();
    const emailVerified = String(claims.email_verified) === "true";
    if (!email || !emailVerified) {
      return json({ ok: false, error: "unverified_email" }, 401);
    }

    const name =
      String(claims.name || "").trim() ||
      (String(claims.given_name || "").trim() + " " + String(claims.family_name || "").trim()).trim() ||
      "Google user";

    // 7) Attribution context passed from the client (all optional)
    const sourcePage = String((body && body.source_page) || "").slice(0, 100);
    const pageUrl = String((body && body.page_url) || "").slice(0, 500);
    const gclid = String((body && body.gclid) || "").slice(0, 500);

    // 8) Forward into the existing lead pipeline. Server-built body: the client
    //    never controls the email/name that get saved.
    const lead = new URLSearchParams();
    lead.set("name", name);
    lead.set("email", email);
    lead.set("phone", "0000000000"); // One Tap returns no phone; placeholder keeps /api/lead validation happy
    lead.set("intent", "Google One Tap Lead");
    lead.set("consent", "yes");
    lead.set("referral_source", "Google One Tap");
    lead.set("source_page", sourcePage || "one-tap");
    lead.set("page_url", pageUrl);
    lead.set("gclid", gclid);
    lead.set("submitted_at", new Date().toISOString());
    lead.set(
      "message",
      "Captured via Google One Tap (real Google-verified email + name; no phone collected). Google sub: " +
        String(claims.sub || "n/a")
    );

    const url = new URL(request.url);
    const leadResp = await fetch(url.origin + "/api/lead", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: lead.toString()
    });

    let leadJson = null;
    try {
      leadJson = await leadResp.json();
    } catch (e) {}
    const leadSaved = leadResp.ok && leadJson && leadJson.ok !== false;

    return json(
      { ok: leadSaved, email, name, lead_saved: leadSaved },
      leadSaved ? 200 : 502
    );
  } catch (err) {
    return json({ ok: false, error: "server_error" }, 500);
  }
}
