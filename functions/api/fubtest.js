// TEMPORARY diagnostic endpoint to debug the FollowUpBoss lead push.
// Token-gated and read-first. REMOVE once the integration is confirmed.
// - GET /api/fubtest?token=...        -> is FOLLOWUPBOSS_API_KEY visible to the
//   runtime, and does it authenticate against the FUB identity endpoint?
// - GET /api/fubtest?token=...&send=1 -> additionally POST one representative
//   event so the exact status/body FUB returns is observable.
const json = (d, s = 200) =>
  new Response(JSON.stringify(d, null, 2), {
    status: s,
    headers: { "content-type": "application/json; charset=UTF-8" }
  });

const TOKEN = "drozq-fubdiag-9x7k2m4q8w1p5v3n";

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  if (url.searchParams.get("token") !== TOKEN) return json({ ok: false, error: "forbidden" }, 403);

  const key = env.FOLLOWUPBOSS_API_KEY || "";
  const out = {
    keyPresent: !!key,
    keyLength: key.length,
    keyTrimmedLength: key.trim().length,
    hasSurroundingWhitespace: key !== key.trim()
  };
  if (!key) return json(out);

  const auth = "Basic " + btoa(key.trim() + ":");

  try {
    const r = await fetch("https://api.followupboss.com/v1/identity", {
      headers: { "Authorization": auth, "Accept": "application/json" }
    });
    out.identityStatus = r.status;
    let b = "";
    try { b = await r.text(); } catch (e) {}
    out.identityBody = b.slice(0, 500);
  } catch (e) {
    out.identityError = (e && e.message) || String(e);
  }

  if (url.searchParams.get("send") === "1") {
    const event = {
      source: "Drozq.com",
      system: "Drozq.com",
      type: "Seller Inquiry",
      message: "Diagnostic test event from /api/fubtest. Safe to delete.",
      person: {
        firstName: "Drozq",
        lastName: "Diagnostic Test",
        emails: [{ value: "fub-diag-" + Date.now() + "@example.com" }],
        phones: [{ value: "+1 (949) 555-0148" }],
        tags: ["Drozq Website", "Diagnostic"],
        source: "Drozq.com"
      }
    };
    try {
      const r2 = await fetch("https://api.followupboss.com/v1/events", {
        method: "POST",
        headers: {
          "Authorization": auth,
          "Content-Type": "application/json",
          "Accept": "application/json",
          "X-System": "Drozq.com"
        },
        body: JSON.stringify(event)
      });
      out.eventStatus = r2.status;
      let b2 = "";
      try { b2 = await r2.text(); } catch (e) {}
      out.eventBody = b2.slice(0, 800);
    } catch (e) {
      out.eventError = (e && e.message) || String(e);
    }
  }

  return json(out);
}
