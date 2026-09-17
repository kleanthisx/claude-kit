---
name: ops-ticket-protocol
description: "Standing ops protocol (user, 2026-08-10) — ticket system, all jobs via lower-tier agents, Fable only summarizes/judges/compiles/delegates, usage ledger, 80% pause rule"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4f3c9365-4917-40c1-834e-8ee9a0d8e6e0
  modified: 2026-08-10T00:31:48.186Z
---

Standing operating protocol, user's orders 2026-08-10 ("you eat tokens like a hog eats sugarcane"):

1. **Budgets = OUTPUT tokens** — "output is the main cost. that's what i will mean going forward."
2. **Ticket system for all jobs.** Every job becomes a ticket (board: the tree-level `OPS.md` at the root of the projects workspace) with tier, output budget, status, and actual usage logged after.
3. **All execution through LOWER-TIER agents.** The Fable main loop only: summarize, judge, compile, delegate. Why: "you cost 3 times the opus and 15 times sonnete" (user's ratio — Fable output is the most expensive unit in the house; every paragraph I write in-loop is premium-priced).
4. **Usage tracking is mandatory** — log every operation's tokens (from usage blocks / run stats) in the OPS.md ledger. Main-loop Fable usage isn't directly measurable by me; authoritative signals are the harness banners — record them when they appear.
5. **80% rule (user-corrected 2026-08-10): applies to the 5-HOUR SESSION limit**, not the weekly bars — "weekly are broken up into 5h sessions." At 80% of the session bar: pause; 45-min cache touches; when the session reset is within the hour, resume and burn to 95%; last 5% reserved for special care. Weekly bars are the longer-horizon budget consumed session by session.
5b. **Fable-exhausted fallback (user, 2026-08-10):** "if we run out of fable, opus is equally good at the work we do" — when the Fable weekly pool runs out, the main loop switches to Opus (draws the separate all-models pool). Not a downgrade for our purposes.
6. **Both meters run:** server ground truth via the statusline script (`~\.claude\statusline-usage.ps1` → live footer display + change-only appends to `projects\usage-ledger.log`); local convenience tally from transcripts (`~\.claude\tally-usage.py`, Task Scheduler daily → `projects\usage-tally.md`). Server ledger decides; the tally informs.

7b. **Size budgets from session capacity (user, 2026-08-10):** "if you know that 200k on sonnet is 5% of the session then plan accordingly." A run's cap is a runaway-stop, not a ration: set it at roughly 2× the expected need, and judge affordability against actual session capacity (a 200k-output sonnet run ≈ 5% of a session — not a reason for caution). Tight caps that cut a job short waste more than they save.
7. **Don't starve the agents (user, 2026-08-10):** "give them more. the idea is not to starve the agents. the idea is to manage session token usage overall." Per-agent tool caps stay generous (search ~20, fetch ~15 — enough to finish the job, not rationing); the real controls are SESSION-level: the run's output cap in code, the meters, and launch-time pool arithmetic — a ticket's expected search demand is checked against the session's remaining shared pool (200 searches/session, shared by ALL agents) before launch, and a dry pool is a reason to run the job in a fresh session, not to starve workers mid-task.

**How to apply:** at session start, recite alongside the other directives (see [[session-start-recite-directives]]); open OPS.md before starting work; new job = new ticket BEFORE launching; log actuals after every run; check the last-known usage state in the ledger. Related: [[prefer-sonnet-for-subagents]] (escalation ladder), [[w-questions-before-actions]] (budget units).
