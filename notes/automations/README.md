# Automations: n8n-style workflows, entirely in Claude Code

*Written 2026-05-30. Facts verified against the live Anthropic docs (code.claude.com/docs: routines, scheduled-tasks, claude-code-on-the-web, headless, authentication) on that date. The cloud feature is in research preview, so re-check limits before relying on a number.*

This is the playbook for running automations (lead nurture, daily reports, ad checks) that fire on a schedule and run on a computer that is not your laptop, so they keep working the 14 hours a day your laptop is home and offline.

---

## 1. The mental model (n8n vs Claude Code)

n8n is a **node graph**. You draw boxes (trigger, IF, HTTP request, send email) and wire them by hand. Every branch is something you decided in advance. It executes a flowchart.

Claude Code is the opposite. You write the **goal** in plain English ("read the new leads, work out who's a hot seller, draft the right follow-up in my voice, remind me to call the urgent ones") and the agent decides the steps on each run, using tools (Gmail, Calendar, the repo, PostHog, the web). It executes **judgment**.

For most real-estate work that is an upgrade, because "what do I say to this specific lead" is a reasoning problem, not a switch statement. The tradeoff: a flowchart is 100% predictable; an agent is ~95% predictable and needs a review step on anything customer-facing. That is why the lead-nurture build defaults to **drafting**, not auto-sending (see `lead-nurture-routine.md`).

---

## 2. The three layers of any automation

Every automation, whether in n8n or here, is three separate questions. Keep them separate in your head.

| Layer | The question | In Claude Code |
|---|---|---|
| **The work** | What gets done? | A prompt (optionally a skill / committed instructions). Plain English. |
| **The schedule** | When does it fire? | A trigger: a cron schedule, an HTTP call, or a GitHub event. |
| **The cloud** | *Where* does it run so it does not need my laptop? | A persistent cloud instance. This is the layer that solves your 10-hours-online problem. |

Most people only think about layer 1. Your actual constraint is layer 3.

---

## 3. What is a "persistent cloud instance"?

A persistent cloud instance is **a computer that someone else keeps powered on 24/7 in a data center, that you reach over the internet.** "Persistent" = it stays on and remembers its setup when you disconnect. "Instance" = your own slice of a bigger machine.

Your laptop is the opposite: it is *ephemeral from the internet's view*. When you bring it home and close it, anything running on it stops. An automation that lives on your laptop is asleep 14 hours a day. An automation that lives on a persistent cloud instance runs at 3am while you sleep and at 2pm while you show a house.

There are two flavors, and you do not have to pick philosophically, you pick per task:

- **Managed / serverless** (someone runs the box, you never see it). You hand over a prompt and a schedule; the provider spins up a fresh machine each run, does the work, tears it down. **Anthropic's "Routines" are exactly this.** Zero servers for you to babysit. This is the recommended starting point.
- **A VM you rent** (a literal always-on Linux box you control). You SSH in, install things, and a cron job runs your command. More power and no per-day limits, more upkeep. Covered in §6 as the graduation path.

---

## 4. The recommended path: Claude Code "Routines" (the cloud tier)

Claude Code has **three** scheduling tiers. Only one runs when your laptop is off:

| | **Cloud (Routines)** | Desktop scheduled task | `/loop` (in-session) |
|---|---|---|---|
| Runs on | **Anthropic's cloud** | Your machine | Your machine |
| Works with laptop **off** | **Yes** | No | No |
| Needs an open terminal | No | No | Yes |
| Min interval | **1 hour** | 1 minute | 1 minute |

> Verbatim from the docs: *"Routines execute on Anthropic-managed cloud infrastructure, so they keep working when your laptop is closed."*

**This is the answer to your core problem.** A Routine is essentially an auto-triggered "Claude Code on the web" session: each run is a fresh, isolated Anthropic-managed VM (~4 vCPU / 16 GB RAM / 30 GB disk) that clones your GitHub repo, does the work autonomously (no permission prompts mid-run), and you can watch every run from the **Claude mobile app** on your phone.

### What you need
- A paid **claude.ai plan: Pro, Max, Team, or Enterprise**, with Claude Code on the web enabled. (The `schedule` skill is already present in your CLI, so you are on a supporting version, ≥ v2.1.81.)
- **It does not work if you are logged in with an API key.** If `ANTHROPIC_API_KEY` is set in your shell, `/schedule` hides itself. You must be logged into your subscription.

### What a Routine bundles
A prompt + a model + one or more **GitHub repos** + a **cloud environment** (network access level, env vars, a setup script) + **triggers** + **connectors** (MCP / your Gmail, Calendar, Drive, PostHog).

### Triggers (you can combine them)
- **Schedule:** hourly / daily / weekdays / weekly, or a one-off future time, or a custom cron via `/schedule update` (minimum interval 1 hour).
- **API:** an HTTPS `POST` to a private per-routine URL with a bearer token. This is how `drozq.com` itself can trigger a run the instant a lead submits (see `lead-nurture-routine.md` §6).
- **GitHub:** on pull request or release events.

### Cost
- **No separate compute charge for the cloud VM.** Verbatim: *"There is no separate compute charge for the cloud VM."*
- Runs **draw down your normal subscription usage** like any interactive session.
- There is a **per-account daily cap on how many runs can start.** The docs do **not** publish the number; they tell you to read your live counter at **claude.ai/code/routines** or **claude.ai/settings/usage**. (Community write-ups report ~5/day on Pro, ~15/day on Max, ~25/day Team. Treat that as rumor, not gospel, and check your own number.)

**The daily cap is the one design constraint that matters for you.** See §5.

### Honest caveats
- **Research preview.** Limits and the API can change.
- A **green run status only means the run started and exited without an infra error, not that the task succeeded.** Open the run and read the transcript, especially while you are still trusting it.
- **No dedicated secrets store yet.** Env vars and setup scripts are visible to anyone who can edit that environment. Fine for a solo account; relevant if you ever add teammates.
- Anything the routine does through your Gmail/connectors **appears as you** (your account sends it). Good for nurture; means you own the blast radius.
- A routine has **no access to your local files**, only a fresh clone of the repo. State must live somewhere external (Gmail labels, a Google Sheet, or a file in the repo). The nurture build uses Gmail labels.

---

## 5. The cadence-vs-cap rule (read this before you build)

A daily run cap collides with the instinct to "run every hour." 24 hourly runs/day would blow past a 5 or 15/day cap on the first morning.

You are a **solo agent**, not an enterprise. You do not have n8n-scale volume, so this is manageable if you size cadence to your cap:

- **Scheduled drip** (day-1, day-3, day-7 follow-ups): a routine **2 to 4 times a day** (e.g. 8am, 1pm, 6pm) batch-processes every lead that is due. Three runs/day fits any plan's cap with room to spare.
- **Instant first-touch** (the speed-to-lead 5-minute rule): do **not** poll for this. Make it **event-driven**: `drozq.com`'s existing `/api/lead` function calls the routine's API trigger the moment a lead submits. One run per lead. At solo-agent volume (a handful of leads/day) this stays comfortably inside the cap. (Note: API-triggered runs still count against the run allowance and will `429` if you exceed it, so this is "fine at your volume," not "unlimited.")
- **If you ever outgrow the cap** (sub-hourly polling, or dozens of leads/day each needing an instant agent run): graduate to the self-hosted path in §6, where runs are unlimited and you pay per token instead.

---

## 6. The graduation path: a VM you own (Oracle free, or a cheap VPS)

When you want **unlimited runs, sub-hourly cadence, or full control**, rent (or get free) an always-on Linux box and run Claude Code **headless** on a normal cron.

### Headless Claude Code
`claude -p "<prompt>"` runs once, non-interactively, prints the result, and exits. It is the CLI form of the Agent SDK. Useful flags: `--output-format json` (machine-readable result + token cost), `--allowedTools "Bash,Read,Edit,mcp__posthog"` (pre-approve tools so it never blocks waiting for a click), `--permission-mode acceptEdits`, `--mcp-config .mcp.json` + `--strict-mcp-config` (load exactly your PostHog server and nothing else).

Cron entry (runs 8am/1pm/6pm, machine never sleeps):
```cron
0 8,13,18 * * *  cd ~/drozq.com && claude -p "$(cat ~/prompts/lead-nurture.md)" --allowedTools "mcp__posthog,Read,Bash(python scripts/ads.py*)" --mcp-config .mcp.json --strict-mcp-config >> ~/logs/nurture.log 2>&1
```

### Auth for an unattended box (two options)
1. **API key (pay per token):** `export ANTHROPIC_API_KEY=sk-ant-...`. Billed on the Console, separate from your subscription. Best for high volume.
2. **Your subscription token:** run `claude setup-token` once (interactive, ~1-year token), store it as `CLAUDE_CODE_OAUTH_TOKEN`. Lets the box run on your Max/Pro plan. Note: if `ANTHROPIC_API_KEY` is also set, the API key wins in `-p` mode, so `unset` it to use the subscription. (From 2026-06-15, subscription `-p`/SDK usage draws from a separate monthly "Agent SDK credit," so confirm your allotment if you go high-volume.)

### Where to host (verified pricing, 2026)

| Option | Monthly | Truly free? | Main gotcha |
|---|---|---|---|
| **Oracle Cloud "Always Free"** | **$0 forever** | **Yes** | Arm Ampere A1: up to 4 cores / 24 GB RAM, no 12-month cliff. "Out of host capacity" errors when creating the free Arm VM in busy regions (retry or pick a quieter home region). Idle reclaim is a non-issue: a box running cron jobs stays above the 20% threshold. **Best free option.** |
| **GitHub Actions (cron)** | **$0** (public repo) / 2,000 free min/mo (private) | Mostly | Not always-on, only fires on the cron. Cron is best-effort and can be delayed at peak. **Scheduled workflows auto-disable after 60 days with no commits** (have a job push a keepalive). Runs `claude -p` fine on `ubuntu-latest`. Use the official `anthropics/claude-code-action@v1`. |
| **GCP free e2-micro** | $0 forever | Yes | 1 micro VM, only in us-west1/central1/east1. Small (1 GB) but enough. |
| **Hetzner CAX11** | ~EUR 3.79 + ~EUR 0.50 IPv4 | No | Cheapest solid paid VPS (2 Arm cores / 4 GB). Best price/performance if you want a no-drama box. |
| **DigitalOcean / AWS Lightsail** | $4 to $6 | No | Fine. Use a >=1 GB tier; 512 MB is tight for Node + the CLI (add swap). |
| **Cloudflare Workers** | $0 | n/a | **Cannot run the CLI** (V8 isolate, no shell). It can only `fetch()` the Anthropic API directly. Keep Pages as-is; use a Worker only to *trigger* a routine or call the API, not to run Claude Code. |

> AWS and Azure free VMs are **12-month-only**, then they bill. AWS further gutted its free tier in July 2025 (now a ~$100 credit good ~6 months). For "free forever," use **Oracle** (or GCP).

---

## 7. Decision guide

- **Start here:** a Routine, scheduled a few times a day. Zero servers, runs on your phone's radar, "free" on your plan. Covers 90% of what you want.
- **Add instant lead response:** wire `/api/lead` to the routine's API trigger.
- **Outgrow the daily cap or need every-few-minutes:** stand up the **Oracle Always Free** VM and move the same prompt to a cron + `claude -p`.
- **Never** try to run the Claude Code CLI inside a Cloudflare Worker.

---

## 8. Your first 30 minutes (prove the cloud works before building the machine)

Do the "hello world" before the nurture engine:

1. In a Claude Code session (logged into your subscription, no `ANTHROPIC_API_KEY` set), run:
   `/schedule every morning at 8am, email me a one-line summary of yesterday's drozq leads and the funnel_submit_success count from PostHog`
2. Open **claude.ai/code/routines**, confirm it is listed, check your remaining daily-run counter.
3. Hit **Run now** (`/schedule run`) to fire it once. Watch it in the Claude mobile app.
4. Read the run transcript. Confirm the email actually arrived (green != success).
5. Close your laptop. Tomorrow at 8am, the email should still arrive. That is the whole point.

Once that works, build the real thing: `lead-nurture-routine.md`.
