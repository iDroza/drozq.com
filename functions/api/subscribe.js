// Public newsletter subscribe endpoint. Accepts a form or JSON POST with
// { email, name?, first_name?, source? }. Same honeypot convention as
// /api/lead. Enrolls the address (newsletter welcome sequence by default) and
// sends the welcome email instantly via waitUntil, so the visitor's response
// never waits on MailChannels. Existing and unsubscribed addresses are left
// untouched; the response is identical either way.

import { validEmail } from "../_lib/email.js";
import { enrollSubscriber } from "../_lib/enroll.js";

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8" }
  });

export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    if (!env.EMAIL_DB || !env.EMAIL_SECRET) {
      return json({ ok: false, error: "unconfigured" }, 503);
    }

    const contentType = request.headers.get("Content-Type") || "";
    let fields = {};
    if (contentType.includes("application/json")) {
      fields = await request.json();
    } else {
      const formData = await request.formData();
      for (const [k, v] of formData.entries()) fields[k] = String(v);
    }

    // Honeypot: bots that fill company_website get a silent 200.
    if (fields.company_website && String(fields.company_website).trim() !== "") {
      return json({ ok: true }, 200);
    }

    const email = String(fields.email || "").trim().toLowerCase();
    if (!validEmail(email)) return json({ ok: false, error: "invalid_email" }, 400);

    const name = String(fields.name || "").trim().slice(0, 200);
    const firstName = String(fields.first_name || "").trim().slice(0, 100) || (name ? name.split(/\s+/)[0] : "");

    context.waitUntil(
      enrollSubscriber(env, {
        email,
        name: name || null,
        first_name: firstName || null,
        // Public endpoint: the caller must NOT be able to self-select the
        // 4-email lead-response drip (or the leads broadcast segment) for an
        // arbitrary address. Everything through here is newsletter-only;
        // leads enter exclusively via /api/lead.
        source: "newsletter",
        intent: String(fields.intent || "").trim().slice(0, 80) || null,
        city: String(fields.city || "").trim().slice(0, 100) || null,
        street: String(fields.street || "").trim().slice(0, 120) || null,
        timeline: String(fields.timeline || "").trim().slice(0, 80) || null,
        gclid: String(fields.gclid || "").trim().slice(0, 200) || null,
        page_url: String(fields.page_url || request.headers.get("referer") || "").slice(0, 300) || null
      }).catch((e) => console.error("SUBSCRIBE_ENROLL_THREW " + ((e && e.message) || e)))
    );

    return json({ ok: true }, 200);
  } catch (e) {
    console.error("SUBSCRIBE_HANDLER_ERROR " + ((e && e.stack) || e));
    return json({ ok: false, error: "Server error" }, 500);
  }
}
