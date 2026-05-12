# PostHog notes

This directory is the running log for what PostHog tells us about the homepage funnel. It is meant to be consulted at the start of any session that touches funnel UX, hero copy, tab switching, step ordering, or anything else that could move drop-off.

## Convention

There are two files in this directory:

- `funnel-log.md`: chronological. Each entry is dated `## YYYY-MM-DD, short title`. Drop in whatever the most recent PostHog query showed (drop-off between steps, mode mix, device breakdown, weird sessions, ad-side correlations). Keep entries tight, the goal is to scan back through a year of changes later and reconstruct what we tried.
- `lessons.md`: durable. Each entry is dated and short. Use this for things that survive a single observation: "Step 3 always loses the most users on mobile," "Buy mode converts at half the rate of Sell," "users who hit `funnel_back` once submit at 1.5× the rate of those who don't." Add to this only when a pattern has held up across multiple observations.

Both files are append-only in practice. Don't rewrite history, even when something turns out to be wrong, add a new dated entry that corrects it. Past wrongness is itself useful data.

## How sessions should use these files

When working on the funnel:

1. Read `lessons.md` first. It's the cumulative truth.
2. Read the last few entries of `funnel-log.md` to see what was recently observed.
3. If PostHog MCP is connected, query for whatever the task needs and write a fresh dated entry in `funnel-log.md` before making any code changes.
4. If a stable pattern emerges, promote it from the log into `lessons.md`.

## PostHog MCP connection

This repo's `.mcp.json` wires up PostHog's remote MCP server. To activate it locally:

1. Generate a personal API key at https://app.posthog.com/settings/user-api-keys?preset=mcp_server (preset auto-scopes it correctly).
2. Set `POSTHOG_API_KEY` as a user-level environment variable on your machine. On Windows PowerShell, run once:
   ```powershell
   [Environment]::SetEnvironmentVariable('POSTHOG_API_KEY', 'phx_your_key_here', 'User')
   ```
3. Quit and restart Claude Code so it picks up the new env var.
4. Run `/mcp` inside Claude Code to confirm PostHog is listed and connected.

The key itself never lives in the repo. `.mcp.json` only references the variable.

## What events exist

The homepage funnel dual-fires every transition to PostHog and the GTM dataLayer. The PostHog event names (per `CLAUDE.md`) are:

- `funnel_open`: overlay opens. Props: `mode`, `prefill_provided`, `gclid`.
- `funnel_step_advance`: forward step. Props: `mode`, `from_step`, `to_step`, `total_steps`.
- `funnel_back`: back step. Props: `mode`, `from_step`, `to_step`.
- `funnel_option_selected`: auto-advance option click. Props: `mode`, `step`, `value`.
- `funnel_submit_attempt`: validation passed, fetch starts. Props: `mode`.
- `funnel_submit_success`: `/api/lead` returned ok. Props: `mode`.
- `funnel_submit_error`: API non-ok or fetch rejected. Props: `mode`, `error_kind`.

`mode` is one of `sell`, `buy`, `sellandbuy`. Total steps per mode: Sell 5, Buy 5, Sell&Buy 6.

The canonical funnel viz in PostHog is:
`funnel_open` → `funnel_step_advance(to_step=2)` → `… =3` → `… =4` → `… =5` → `funnel_submit_success`, breakdown by `mode`.
