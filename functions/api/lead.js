const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8" }
  });

export async function onRequestPost(context) {
  try {
    const { request, env } = context;

    // 1) Only accept HTML form submits
    const contentType = request.headers.get("Content-Type") || "";
    const isForm =
      contentType.includes("application/x-www-form-urlencoded") ||
      contentType.includes("multipart/form-data");

    if (!isForm) {
      return json({ ok: false, error: "Unsupported content type" }, 415);
    }

    const formData = await request.formData();

    // 2) Honeypot check
    const honey = formData.get("company_website");
    if (honey && String(honey).trim() !== "") {
      return json({ ok: true }, 200);
    }

    // 3) Extract fields
    const firstName = String(formData.get("first_name") || "").trim();
    const lastName = String(formData.get("last_name") || "").trim();
    const name = (firstName + " " + lastName).trim() || String(formData.get("name") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const phone = String(formData.get("phone") || "").trim();

    const intent = String(formData.get("intent") || "").trim();
    const message = String(formData.get("message") || "").trim();

    // Address fields
    const streetAddress = String(formData.get("street_address") || "").trim();
    const addressLine2 = String(formData.get("address_line_2") || "").trim();
    const city = String(formData.get("city") || "").trim();
    const state = String(formData.get("state") || "").trim();
    const zip = String(formData.get("zip") || "").trim();
    const fullAddress = String(formData.get("full_address") || "").trim();
    const lat = String(formData.get("lat") || "").trim();
    const lng = String(formData.get("lng") || "").trim();

    const referralSource = String(formData.get("referral_source") || "").trim();
    const sourcePage = String(formData.get("source_page") || formData.get("source") || "").trim();
    const consent = String(formData.get("consent") || "").trim();
    const timeline = String(formData.get("timeline") || "").trim();
    const gclid = String(formData.get("gclid") || "").trim();

    // 4) Server-side validation
    if (!name || !email || !phone) {
      return json({ ok: false, error: "Missing required fields" }, 400);
    }
    if (!intent) {
      return json({ ok: false, error: "Missing inquiry type" }, 400);
    }
    if (consent !== "yes") {
      return json({ ok: false, error: "Consent required" }, 400);
    }

    // 5) Length guards
    if (
      name.length > 200 ||
      email.length > 200 ||
      phone.length > 50 ||
      intent.length > 80 ||
      sourcePage.length > 100 ||
      message.length > 5000 ||
      streetAddress.length > 300 ||
      fullAddress.length > 500
    ) {
      return json({ ok: false, error: "Payload too large" }, 413);
    }

    // 6) Env vars
    const TO_EMAIL = env.TO_EMAIL;
    const FROM_EMAIL = env.FROM_EMAIL;
    const MAILCHANNELS_API_KEY = env.MAILCHANNELS_API_KEY;

    if (!TO_EMAIL || !FROM_EMAIL) {
      return json(
        { ok: false, error: "Server not configured: TO_EMAIL/FROM_EMAIL missing" },
        500
      );
    }
    if (!MAILCHANNELS_API_KEY) {
      return json(
        { ok: false, error: "Server not configured: MAILCHANNELS_API_KEY missing" },
        500
      );
    }

    // 7) Metadata
    const ip =
      request.headers.get("cf-connecting-ip") ||
      request.headers.get("x-forwarded-for") ||
      "";
    const ua = request.headers.get("user-agent") || "";
    const url = new URL(request.url);

    // 8) Compose address block
    const addressBlock = [
      streetAddress,
      addressLine2,
      [city, state, zip].filter(Boolean).join(", ")
    ].filter(Boolean).join("\n");

    // 9) Compose email
    const emailBody =
`New lead from drozq.com

IDENTITY
Name: ${name}
Email: ${email}
Phone: ${phone}

ADDRESS
${addressBlock || fullAddress || "—"}
Full (Google): ${fullAddress || "—"}
Lat/Lng: ${lat || "—"}, ${lng || "—"}

INQUIRY
Type: ${intent}
Timeline: ${timeline || "—"}
Referral Source: ${referralSource || "—"}

NOTES
${message || "—"}

META
Source: ${sourcePage || "—"}
Page URL: ${String(formData.get("page_url") || "—")}
Submitted: ${String(formData.get("submitted_at") || "—")}
GCLID: ${gclid || "—"}
Endpoint: ${url.pathname}
IP: ${ip || "—"}
User-Agent: ${ua || "—"}
Consent: ${consent}
`;

    // 10) Send email via MailChannels (non-blocking)
    context.waitUntil(
      fetch("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "X-Api-Key": MAILCHANNELS_API_KEY,
          "Accept": "application/json"
        },
        body: JSON.stringify({
          personalizations: [{ to: [{ email: TO_EMAIL }] }],
          from: { email: FROM_EMAIL, name: "drozq.com Lead Form" },
          reply_to: { email, name },
          subject: `🏠 New Lead (${intent}): ${name} — ${city || "Unknown City"}, ${state || "CA"}`,
          content: [{ type: "text/plain", value: emailBody }]
        })
      })
    );

    // 11) Optional Zapier forward (non-blocking)
    if (env.ZAPIER_WEBHOOK_URL) {
      context.waitUntil(
        fetch(env.ZAPIER_WEBHOOK_URL, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            first_name: firstName,
            last_name: lastName,
            name,
            email,
            phone,
            intent,
            street_address: streetAddress,
            address_line_2: addressLine2,
            city,
            state,
            zip,
            full_address: fullAddress,
            lat,
            lng,
            referral_source: referralSource,
            timeline,
            gclid,
            message,
            source_page: sourcePage,
            consent,
            ip,
            user_agent: ua
          })
        })
      );
    }

    return json({ ok: true }, 200);
  } catch (err) {
    return json({ ok: false, error: "Server error" }, 500);
  }
}
