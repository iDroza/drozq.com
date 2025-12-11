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

    // 2) Honeypot check (matches your HTML)
    const honey = formData.get("company_website");
    if (honey && String(honey).trim() !== "") {
      // Act like success; don't tip off bots.
      return json({ ok: true }, 200);
    }

    // 3) Extract fields from your exact form
    const name = String(formData.get("name") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const phone = String(formData.get("phone") || "").trim();

    const intent = String(formData.get("intent") || "").trim(); // sell/buy/investor/other
    const budgetRange = String(formData.get("budget_range") || "").trim();
    const timeline = String(formData.get("timeline") || "").trim();

    const message = String(formData.get("message") || "").trim();
    const sourcePage = String(formData.get("source_page") || "").trim();

    const consent = String(formData.get("consent") || "").trim(); // "yes" when checked

    // 4) Server-side validation (mirrors your required UI)
    if (!name || !email || !message) {
      return json({ ok: false, error: "Missing required fields" }, 400);
    }

    if (!intent) {
      return json({ ok: false, error: "Missing intent" }, 400);
    }

    if (consent !== "yes") {
      return json({ ok: false, error: "Consent required" }, 400);
    }

    // 5) Length guards (anti-abuse)
    if (
      name.length > 200 ||
      email.length > 200 ||
      phone.length > 50 ||
      intent.length > 50 ||
      budgetRange.length > 200 ||
      timeline.length > 200 ||
      sourcePage.length > 100 ||
      message.length > 5000
    ) {
      return json({ ok: false, error: "Payload too large" }, 413);
    }

    // 6) Environment variables
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

    // 7) Optional metadata (useful for triage)
    const ip =
      request.headers.get("cf-connecting-ip") ||
      request.headers.get("x-forwarded-for") ||
      "";
    const ua = request.headers.get("user-agent") || "";
    const url = new URL(request.url);

    // 8) Compose email body with all fields
    const emailBody =
`New lead from drozq.com/contact

IDENTITY
Name: ${name}
Email: ${email}
Phone: ${phone || "—"}

DEAL SIGNAL
Intent: ${intent}
Price range: ${budgetRange || "—"}
Timeline: ${timeline || "—"}

MESSAGE
${message}

META
Source page: ${sourcePage || "contact"}
Endpoint: ${url.pathname}
IP: ${ip || "—"}
User-Agent: ${ua || "—"}
Consent: ${consent}
`;

    // 9) MailChannels Email API (authenticated)
    const sendReq = new Request("https://api.mailchannels.net/tx/v1/send", {
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
        subject: `New Lead (${intent}): ${name}`,
        content: [{ type: "text/plain", value: emailBody }]
      })
    });

    const resp = await fetch(sendReq);
    const respText = await resp.text().catch(() => "");

    if (!resp.ok) {
      // Critical: return the actual provider response so you can debug instantly
      return json(
        { ok: false, error: "Email failed", provider_status: resp.status, provider_body: respText },
        502
      );
    }

    // 10) Optional: forward to Zapier (CRM flow)
    if (env.ZAPIER_WEBHOOK_URL) {
      context.waitUntil(
        fetch(env.ZAPIER_WEBHOOK_URL, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            name,
            email,
            phone,
            intent,
            budget_range: budgetRange,
            timeline,
            message,
            source_page: sourcePage || "contact",
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
