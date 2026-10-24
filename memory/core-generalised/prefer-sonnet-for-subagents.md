---
name: prefer-sonnet-for-subagents
description: "Match subagent model to task demand — never let cheap fetch/summarize work inherit the top session model (Fable/Opus)"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-01T09:00:00.000Z
---

For delegated subagent / parallel-agent / workflow work, **always set the model explicitly by task demand** — never let agents silently inherit the top session model. The rule is *match the tier to the job*, not a fixed model roster:

- **cheap tier** (web-search / fetch / extract / summarize / mechanical edits) → Sonnet. **No Haiku, ever** (user, 2026-10-01: "only Sonnet, no haiku").
- **mid tier** (review / research / fact-check) → mid model (currently Sonnet).
- **top tier** (genuinely hard synthesis, judging, complex spine work) → top model (currently Opus) — only when the task truly needs it.
- The top/main-loop model (whatever it is this session, e.g. Fable/Opus) should not be inherited by cheap delegated work.

(Model names above are examples as of writing; if the roster changes, keep the tiering, swap the names.)

**Why:** user said "it doesn't need to be opus if sonnet can deliver" (14-agent book-critique fan-out), and on 2026-07-13 reiterated: "having a Fable agent read websites and summarise back is like starting an F1 to go to the kitchen for a glass of water." Cost-conscious; wants the tier matched to the job.

**How to apply:** on every `Agent` call and `Workflow` `agent()` call, pass `model` explicitly — `sonnet` for mechanical fetch/extract/summarize, `sonnet` for research/review, `opus` only when the task genuinely needs it. When running prebuilt workflows (e.g. deep-research) whose agents inherit the session model, edit the script to add per-stage model overrides before launching. Aligns with [[work-style-kiss-mvp-rtfm]].

**ESCALATION LADDER (user doctrine, 2026-08-10; Haiku rung removed 2026-10-01):** Sonnet gathers broadly → Sonnet produces and verifies NORMAL entries → Opus ONLY resolves exceptions / reviews risky claims. "Use the cheapest model that can reliably do that particular piece of work. Don't use Opus to verify every obvious definition, and don't force Haiku to make judgments it cannot support." Verification is stratified by RISK, not applied uniformly: the worker tier flags its own low-confidence/contested items, and only the flagged queue reaches the expensive tier. Cost scales with the exception rate, not the corpus size.

**VIOLATED 2026-08-09 (a glossary-building run) — hardened rule:** launched stock deep-research by name without reading the script; ~40 agents inherited Fable, burned the user's Fable limit to 80%, and the "500k cap" existed only as prose in the args. The paragraph above already named deep-research explicitly — having the memory and not applying it = not knowing it. HARD RULE now: **never launch a prebuilt workflow by `name`**. Read the persisted script FIRST and verify in code, not prose: (a) `model:` set per stage (cheap groundwork, opus only for judgment/synthesis), (b) spend bounds enforced via `budget.spent()` gates in-script (args-text "caps" bind nothing), (c) say both checks passed in the launch message. Adversarial/judge agents: opus for the verdict, but any web/groundwork they need is done by a cheap gatherer stage feeding them a dossier — judges run tool-less. Related: [[w-questions-before-actions]].

**2026-10-01 — Sonnet is the floor.** User: "only Sonnet, no haiku". The reason was already on record — `~/.claude/hooks/judge-dread.ps1:491-508` (measured 2026-09-14): Haiku and Sonnet graded the same 300 text windows; where either saw anything (149 windows) they agreed on only 27, and Haiku missed 47 and invented 17. "Haiku cannot hold a sentence, let alone read a script and judge whether it computes what it prints." Haiku also enters silently as Claude Code's background small-fast model; `ANTHROPIC_SMALL_FAST_MODEL=claude-sonnet-5` removes it. I first wrote "no reason stated" here after my own grep had shown me that comment. Applies to Agent `model`, Workflow `agent()` `model`, and any `claude -p --model` in scripts/hooks.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
