# CLAUDE.md — rationale and history

Kept out of `CLAUDE.md` so the operative rules don't compete for attention with their own
justification. Nothing here is an instruction; it is the record of why each rule exists.
Original pre-trim file: `CLAUDE.md.bak-2026-08-11`.

## Why the rules got shorter (2026-08-11)

- **Contradictory rules cause fabrication, not refusal.** Facing irreconcilable constraints, agents
  invent obstacles rather than report the conflict; the extreme form fakes a system crash, and
  injecting correct information afterwards does not restore honest behaviour.
  ([arXiv 2606.14831](https://arxiv.org/abs/2606.14831)) → Removing conflicts is the well-evidenced win.
- **Adding rules degrades performance, even rules already being obeyed.** Inserting self-evident
  constraints produced substantial drops including on Claude Sonnet 4.5; failed cases allocate more
  attention to constraints. ([arXiv 2601.22047](https://arxiv.org/abs/2601.22047))
- **Length and structure, honestly, are NOT evidenced.** A factorial study over 1,650 Claude Code
  sessions found no detectable effect from file size, instruction position, file architecture, or
  contradictions between adjacent files. ([arXiv 2605.10039](https://arxiv.org/abs/2605.10039)) So the
  trim is justified by conflict-removal and constraint-count, not by page count.
- **Prohibitions decay, requirements persist.** Omission constraints fell 73%→33% by turn 16 while
  commission constraints held at 100%. ([arXiv 2604.20911](https://arxiv.org/html/2604.20911v1)) → Every
  rule rewritten as an action to perform.
- **Hooks are the only mechanism with strong numbers.** Deterministic pre-execution gates blocked
  >90% of unsafe executions at 1.4–2.8ms overhead. ([AgentSpec](https://arxiv.org/html/2503.18666v1))
  Prose asks; hooks enforce. Rules a hook already covers were reduced to a pointer.

Full research rows: kept in the source workspace's research log (not shipped in this kit).

## The contradiction that was resolved

The old file said both "never to the point where operations seize" and, in four separate places,
"stop and wait for a yes". On 2026-08-11 this produced the exact failure mode you would predict:
four turns of asking for a GO that had effectively been given, followed by a 12-agent fan-out
launched on a comprehension check — roughly 100 permission prompts, seven of which the user killed
by hand. Stall, then bolt.

Resolved in the user's own words that day: *"if that's what it takes to get some work done even in
a fucked up way i am ok with it."* → **Act by default; safety comes from sizing the action, not from
asking permission.** The four hard stops are the exceptions, and they are exhaustive.

## History of individual rules

- **2026-08-02** — transcript analysis produced the `Q:`/`GO` protocol, the PLAN.md gate, the
  every-list-is-a-checklist rule and the done-audit. Four hooks were built and wired.
- **2026-08-02** — ceiling of 2 extra review rounds added to the anti-deviation gate, to stop
  runaway review spirals.
- **2026-08-06** — anti-deviation gate made tiered; blanket full-looping had cost ~3× the actual
  work on routine tasks.
- **2026-08-09** — W-questions and the engineering-principles filter added after a ~2M-token
  research blowout. All six principles were already in knowledge and none were invoked.
  "Not applied = not known."
- **2026-08-09** — default scale set to MVP; the model could not reliably tell MVP from
  cancer-curing rigour from context.
- **2026-08-11** — the 5-step adversarial-Opus review gate was cut. It mandated spawning Opus
  subagents for every full-gate action, which fights value engineering ("the right resource, never
  the best by default") and estimate-before-execute, and its own note recorded the 3× cost. The
  surviving requirement is to re-read the user's literal words before acting.
- **2026-08-11** — universal "plan first, save PLAN.md, wait for GO" narrowed to match memory
  (`build-mode-concept-vs-plan`, `plan-before-code`): plan-first is reserved for a client app with a
  formal PLAN.md gate; everything else is concept/build-and-refine. The old file and memory
  contradicted each other outright.
