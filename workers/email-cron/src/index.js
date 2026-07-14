// Cron shim: all real logic lives in the site repo at /functions/api/email/
// (deployed with the Pages site). This Worker only supplies the schedule.

export default {
  async scheduled(event, env, ctx) {
    try {
      const r = await fetch("https://drozq.com/api/email/tick", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + env.EMAIL_SECRET,
          // Workers send no default User-Agent; the zone's Browser Integrity
          // Check can 403 empty-UA requests, so identify explicitly.
          "User-Agent": "drozq-email-cron/1.0"
        }
      });
      const body = await r.text();
      console.log("EMAIL_CRON status=" + r.status + " " + body.slice(0, 300));
    } catch (e) {
      console.error("EMAIL_CRON_THREW " + ((e && e.message) || e));
    }
  },
  async fetch() {
    return new Response("drozq-email-cron: scheduled worker, nothing to see here.", { status: 200 });
  }
};
