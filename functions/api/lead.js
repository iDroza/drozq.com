export async function onRequestPost(context) {
  const { request, env } = context;

  // Only accept form submits
  const contentType = request.headers.get("Content-Type") || "";
  if (!contentType.includes("application/x-www-form-urlencoded")
   && !contentType.includes("multipart/form-data")) {
    return new Response("Unsupported content type", { status: 415 });
  }

  const formData = await request.formData();

  // Honeypot check
  const honey = formData.get("company_website");
  if (honey && String(honey).trim() !== "") {
    return new Response("ok", { status: 200 });
  }

  // Extract fields
  const name = String(formData.get("name") || "").trim();
  const email = String(formData.get("email") || "").trim();
  const phone = String(formData.get("phone") || "").trim();
  const message = String(formData.get("message") || "").trim();

  // Basic validation
  if (!name || !email || !message) {
    return new Response("Missing required fields", { status: 400 });
  }

  // Choose your delivery method:
  // A) Send to an email API directly
  // B) Forward to Zapier webhook (then to CRM)
  //
  // This example uses MailChannels Email API.

  const TO_EMAIL = env.TO_EMAIL;
  const FROM_EMAIL = env.FROM_EMAIL;

  if (!TO_EMAIL || !FROM_EMAIL) {
    return new Response("Server not configured", { status: 500 });
  }

  const emailBody =
`New lead from drozq.com/contact

Name: ${name}
Email: ${email}
Phone: ${phone || "—"}

Message:
${message}
`;

  // MailChannels Email API
  // Note: the old free MailChannels Workers service ended Aug 31, 2024.
  // The Email API offers a free plan (up to 100 emails/day),
  // but requires a Domain Lockdown DNS record for your domain. :contentReference[oaicite:2]{index=2}
  const sendReq = new Request("https://api.mailchannels.net/tx/v1/send", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: TO_EMAIL }] }],
      from: { email: FROM_EMAIL, name: "drozq.com Lead Form" },
      reply_to: { email, name },
      subject: `New Lead: ${name}`,
      content: [{ type: "text/plain", value: emailBody }]
    })
  });

  const resp = await fetch(sendReq);

  if (!resp.ok) {
    return new Response("Email failed", { status: 502 });
  }

  // Optional: Forward to Zapier
  if (env.ZAPIER_WEBHOOK_URL) {
    // Fire and forget (don’t block the user)
    context.waitUntil(fetch(env.ZAPIER_WEBHOOK_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name, email, phone, message, source: "drozq.com/contact" })
    }));
  }

  return new Response("ok", { status: 200 });
}
