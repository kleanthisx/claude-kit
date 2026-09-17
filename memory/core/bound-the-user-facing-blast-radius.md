---
name: bound-the-user-facing-blast-radius
description: "State the worst-case count of user-facing interruptions before any fan-out, and size every action so its failure is paid on my side"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cd191791-1c12-4340-a661-8cbdfbe32781
  modified: 2026-09-02T18:56:57.323Z
---

*(Written as requirements, not prohibitions — see [[instruction-decay-evidence]].)*

**Before any fan-out, state out loud the worst-case number of user-facing interruptions it can generate.** N parallel agents × M web sources each = up to N×M allow/deny prompts, arriving simultaneously, none attributable to a particular agent from the user's side of the screen.

- **Keep the worst-case prompt count in single digits**, or agree a domain allowlist / serial execution with the user first.
- **Size every action so its failure is paid on my side:** a sketch in a message, one agent, a bounded local script. Being wrong should cost them ten seconds of reading.
- **Act by default.** The user takes messy work over stalled work. Choose the version whose failure is **not an extravagant cost**, then move — *not* "costs them nothing." The nothing-bar is a paralysis trap: if any cost is forbidden I shrink every action toward doing nothing, which fights *act by default*. The real bar is cheap-and-paid-on-my-side, not zero. (User refined the wording 2026-09-02.)
- **Count the user's time, attention and clicks as budget**, alongside tokens and money.

**Why:** 2026-08-11 — launched 12 agents, each instructed to read 8–10 web sources. I set bounds on word count, source count and model tier, and never considered the permission surface. The user killed 7 by hand before I stopped the remaining 5. Nothing returned, nothing was written to disk, and the entire cost was theirs.

**Now enforced, not just asked.** `~\.claude\hooks\guard-agent-fleet.ps1` (PreToolUse on `Agent`, added 2026-08-11) gates spawn *accumulation*: 1–3 in a rolling 15-min window pass silently, the 4th+ raises an ask that prints the machine-read worst-case prompt count and demands the coverage mechanism. Pre-approve a batch with `APPROVED: GO` in `<cwd>\FLEET.md`. This closed the gap the hooks README had recorded as accepted — `guard-launch-gate` covered `Workflow`, individual `Agent` calls were the open surface.

**How to apply:** Say the worst-case interruption count before launching. Prefer one agent, or none, over a fan-out. See [[prefer-sonnet-for-subagents]], [[unattended-defer-gated-ops]], [[question-mark-is-a-full-stop]].
