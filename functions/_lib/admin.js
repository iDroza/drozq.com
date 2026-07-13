// Shared gate for the admin email endpoints (/api/email/*): Bearer EMAIL_SECRET
// plus the D1 binding. Returns a Response to short-circuit with, or null when
// the request is authorized and the platform is configured.

export const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8" }
  });

export function adminGate(context) {
  const { request, env } = context;
  if (!env.EMAIL_SECRET) return json({ ok: false, error: "email_secret_missing" }, 503);
  const auth = request.headers.get("authorization") || "";
  if (auth !== "Bearer " + env.EMAIL_SECRET) return json({ ok: false, error: "unauthorized" }, 401);
  if (!env.EMAIL_DB) return json({ ok: false, error: "email_db_not_bound" }, 503);
  return null;
}
