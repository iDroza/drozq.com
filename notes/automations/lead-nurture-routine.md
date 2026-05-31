# Lead-nurture routine (ready to run)

*Written 2026-05-30. Read `README.md` in this folder first for the concept, the cloud tiers, and the cadence-vs-cap rule.*

This is a complete, drafting-first lead-nurture machine that runs on Anthropic's cloud, so it works when your laptop is home and offline. It reads your new leads, decides who is due for a follow-up, writes each one in your voice, and leaves it as a Gmail draft for you to send from your phone. Hot sellers also get a calendar reminder to call.

---

## 1. The concept (why nurture is the right first automation)

Most leads never convert on the first touch. The money is in touches 5 through 12, which is exactly the work a solo agent drops when busy. A nurture automation is a tireless assistant that never forgets to follow up, never lets a lead go cold, and always follows up *on time*. It does not replace you; it teees up the human moment (the call, the personal note) and removes the "I forgot to email them back" failure mode.

**Drafting-first, on purpose.** The routine does all the thinking, writing, and scheduling. It does **not** auto-send outreach (at first). You review and send. Reasons: it protects your brand voice while you learn to trust it, and it keeps a human in the loop on anything a lead sees. Once you have watched a week of drafts and they are good, flip one line to auto-send (§7).

---

## 2. How a lead reaches the routine

Today a submit hits `/functions/api/lead.js`, which emails you a lead with subject:

```
🏠 New Lead (<intent>): <name> — <city>, <state>
```

and sets `reply_to` to the lead's own email. So **your inbox is already the lead feed.** The routine reads Gmail for those subjects. (If you also forward leads to a CRM via `ZAPIER_WEBHOOK_URL`, the inbox copy still arrives, so this works unchanged.)

## 3. State: Gmail labels as the state machine

A routine run is a fresh cloud VM with no memory of last run, so state must live outside it. The simplest, most visible store for a solo agent is **Gmail labels** (you have the Gmail connector with label tools). Each lead thread carries exactly one stage label:

| Label | Meaning | Next action |
|---|---|---|
| *(none)* | brand-new lead, not yet processed | draft first touch, label `Nurture/Stage-1` |
| `Nurture/Stage-1` | first touch drafted/sent | if no reply after 2 days, draft second touch -> `Nurture/Stage-2` |
| `Nurture/Stage-2` | second touch (value: market snapshot) | if no reply after 3 more days, draft third touch -> `Nurture/Stage-3` |
| `Nurture/Stage-3` | third touch (the "should I close your file?" nudge) | if no reply after 5 more days -> `Nurture/Dormant` |
| `Nurture/Engaged` | the lead replied | stop the drip; calendar a personal follow-up |
| `Nurture/Dormant` | exhausted the sequence | leave alone; quarterly check-in only |

The routine reads each lead thread, sees the lead replied or not, sees the current label and how long it has sat, and moves it one step. That is the entire state machine, and you can see it in Gmail at a glance.

> Optional reporting layer: also append a row to a "Drozq Lead Tracker" Google Sheet via the Drive connector for an at-a-glance pipeline view. Not required; labels are the source of truth.

---

## 4. The two routines

You will create **two**, because instant-response and slow-drip are different jobs (see the cadence-vs-cap rule in `README.md` §5):

- **Routine A: the drip** (scheduled, 3x/day) handles stages 1 to 3, dormancy, and engaged hand-off.
- **Routine B: the instant first-touch** (API-triggered by `/api/lead`) drafts the speed-to-lead reply within a minute of submission. Optional; add it after A works.

---

## 5. Routine A: the drip (build this first)

In a Claude Code session logged into your subscription (no `ANTHROPIC_API_KEY` in the shell), run `/schedule` and paste the prompt below, or create it at **claude.ai/code/routines** (New routine -> Remote). Set the schedule to **daily, then `/schedule update` to cron `0 8,13,18 * * *`** (8am, 1pm, 6pm PT). Attach the **Gmail** and **Google Calendar** connectors. Repo: `drozq.com` (so it can read `CLAUDE.md` for your voice rules).

> Paste this as the routine prompt:

```text
You are running my (Joshua Guerrero, solo real-estate agent, Drozq, Irvine CA, DRE 02267255) lead-nurture drip. Each run, process new and due leads from my Gmail and move each one step through the nurture sequence. DRAFT replies, do not send them.

VOICE: first-person, confident, direct, specific, sparse. Follow the copy rules in the repo's CLAUDE.md ("Conversion copy principles"): no platitudes, no SEO filler, no star ratings, NO em dashes, and NEVER use anti-promise phrasing ("no pressure / no spam / no obligation / no autodialer"). Frame value positively. Keep every email under 120 words. Sign as "Joshua" with my number (949) 438-5948.

STATE = Gmail labels. Ensure these labels exist (create if missing): Nurture/Stage-1, Nurture/Stage-2, Nurture/Stage-3, Nurture/Engaged, Nurture/Dormant.

STEP 1 - find leads. Search Gmail for threads whose subject contains "New Lead" from the last 21 days. For each thread, read the lead's name, email (the reply-to / the address in the body), intent, city, and timeline from the lead email body.

STEP 2 - per lead, decide the action by its current label and the lead's behavior:
- If the lead has REPLIED in the thread (a message from them after my lead-form email): apply Nurture/Engaged, remove any Nurture/Stage-* label, create a Google Calendar event for me tomorrow 9:00am PT titled "Call back: <name> (<intent>)" with their email + phone in the description, and do NOT draft a drip email. This is a hot human moment.
- Else if NO label yet: this is a brand-new lead. Draft a FIRST touch (warm, specific to their intent and city; one concrete next step: offer a quick call or the refined CMA). Apply Nurture/Stage-1. If intent is "Home Valuation", "Home Sale + Purchase", or timeline is urgent (0-3 months), ALSO create a Calendar event for me within 2 hours titled "Call now (hot): <name>".
- Else if Nurture/Stage-1 and >=2 days since the lead email and no reply: draft a SECOND touch that leads with value (a one-line Irvine/OC market snapshot: seller's market, recent median, days on market; pull a current figure if you can, otherwise keep it qualitative). Apply Nurture/Stage-2, remove Stage-1.
- Else if Nurture/Stage-2 and >=3 days and no reply: draft a THIRD touch (a low-pressure "want me to keep your file open or close it for now?" that invites a yes/no reply). Apply Nurture/Stage-3, remove Stage-2.
- Else if Nurture/Stage-3 and >=5 days and no reply: apply Nurture/Dormant, remove Stage-3. Do not draft.
- Else: not due yet, skip.

STEP 3 - every draft is created with Gmail create_draft on the SAME thread, addressed to the lead, ready for me to review and send. Never send.

STEP 4 - finish by emailing me (joshuag@chirogg.com) a single summary: how many new leads, how many drafts created at each stage, how many marked Engaged with calls scheduled, how many went Dormant, and any lead you could not parse. One short email. This is my daily pipeline pulse.

Be conservative: if you are unsure whether a thread is a real lead, skip it and note it in the summary rather than drafting to a stranger.
```

### Sizing it to your cap
Three runs/day = 3 against your daily routine cap, leaving plenty. If your plan's cap is tight (check claude.ai/code/routines), drop to 2x/day (8am, 5pm). Do not go hourly; the drip does not need it, and stage timing is measured in days.

---

## 6. Routine B: instant first-touch (add after A works)

Speed-to-lead is the 5-minute rule: the faster the first reply, the higher the contact rate. Polling cannot hit 5 minutes on a 1-hour minimum, so make it **event-driven** from your own site.

1. Create a second routine (a one-line prompt: *"A new lead just submitted on drozq.com. The lead details are in the trigger text. Draft a warm, specific first-touch reply in my voice (CLAUDE.md rules, no em dashes, under 120 words, sign as Joshua with (949) 438-5948) as a Gmail draft to the lead, and if the intent is a valuation or sale, add a Calendar event to call them within the hour."*). Give it the **Gmail + Calendar** connectors.
2. Add an **API trigger** (only editable on the web). Copy the per-routine `/fire` URL and the bearer token. **The token is shown once.** Store it as a Cloudflare Pages env var, e.g. `ROUTINE_FIRE_URL` and `ROUTINE_FIRE_TOKEN`.
3. In `functions/api/lead.js`, after the lead validates, add a non-blocking fire (mirror the existing `context.waitUntil(...)` Zapier pattern):

```js
// Fire the instant-nurture routine (non-blocking; never affects the lead response)
if (env.ROUTINE_FIRE_URL && env.ROUTINE_FIRE_TOKEN) {
  context.waitUntil(
    fetch(env.ROUTINE_FIRE_URL, {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + env.ROUTINE_FIRE_TOKEN,
        "anthropic-beta": "experimental-cc-routine-2026-04-01",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
      },
      body: JSON.stringify({
        text: `New ${intent} lead: ${name}, email ${email}, phone ${phone}, ` +
              `city ${city || "?"}, timeline ${timeline || "?"}. Draft the first touch now.`
      })
    }).catch(() => {})   // a fire failure must never break the lead save
  );
}
```

This is additive and conversion-safe: it runs in `waitUntil`, catches its own errors, and never changes what `/api/lead` returns. The lead email + Zapier path are untouched. At your volume each fire is one run; it counts against the daily cap and will `429` if you ever exceed it, which a solo pipeline will not.

> Beta caveat: the `experimental-cc-routine-2026-04-01` header is a research-preview version and may change. If fires start `400`-ing, check the current header on the routine's API-trigger page.

---

## 7. Going from drafting to auto-send

Once a week of drafts reads the way you would send them, change Routine A's prompt: replace "DRAFT replies, do not send them" and the `create_draft` instruction with "SEND the reply" (Gmail send). Keep the third-touch and dormant logic conservative. Even then, consider keeping the **first** touch on auto-send (consenting form leads expect a fast reply) but the later, judgement-heavier touches as drafts. You control the line.

---

## 8. Verify it is live (green != success)

1. `/schedule list` shows Routine A; claude.ai/code/routines shows it with a next-run time.
2. `/schedule run` (or "Run now") fires it once. Open the run in the Claude mobile app and **read the transcript**, a green status only means it started and exited, not that it did the right thing.
3. Confirm in Gmail: new leads got `Nurture/Stage-1` and a draft exists on the thread. Confirm the summary email arrived. Confirm a hot lead produced a Calendar event.
4. Close your laptop. The 1pm and 6pm runs should still happen. That is the proof.
5. First week: skim every draft before sending and read each daily summary. Tune the prompt (timing, tone, word count) by editing the routine.

---

## 9. Guardrails specific to this site

- **Do not touch the funnel, `/api/lead` core logic, tracking, or `funnels.json`.** Routine B's change is purely additive (a guarded `waitUntil` fire) and respects the form-integrity rules in CLAUDE.md.
- Leads carry `consent="yes"` (required server-side), so email follow-up to them is appropriate. Still default to drafting early.
- The routine acts **as you** from your Gmail. That is the point for nurture, and it means you own everything it sends. Keep the connector list minimal (Gmail + Calendar only).
- Re-read `notes/posthog/lessons.md` if you ever have the routine touch funnel copy; it should not.
