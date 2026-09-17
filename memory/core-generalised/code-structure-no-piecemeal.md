---
name: code-structure-no-piecemeal
description: "Break engines into modules/objects with clear ownership (no single-file monoliths), and always finish a feature completely before stopping — no piecemeal states"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9f2df323-62f1-4091-b1db-6fba74ee35df
  modified: 2026-07-24T16:12:05.977Z
---

On one project's build (2026-07-20) the user pushed back twice in one
message: play.ps1 had grown into a ~1000-line monolith ("you seem to go all ham in a
single file — break the engine into objects and classes and params, that way we know
what to touch"), and Phase 3b was left half-wired mid-implementation ("a job needs to
be finished at all times. we don't do piecemeal").

**Why:** They navigate the code by ownership — one module = one concern = obvious place
to touch. And a half-built feature is worse than an unbuilt one: it looks done on the
surface (data present, no errors) while silently doing nothing.

**How to apply:** Split code by responsibility into separate files/modules with clear
state ownership, even in PowerShell (dot-sourced engine/*.ps1 modules). When building a
feature, land the FULL vertical slice (engine + data + UI + tests green) before ending
the turn or moving to the next feature.

**What no-piecemeal actually means (not a contradiction):** don't build module-by-module
while the software is still incomplete — you can't test isolated, unwired modules. The
whole thing must always **RUN and be testable** at each step: vertical slices that run, not
horizontal modules that sit dead. This holds in BOTH build modes ([[build-mode-concept-vs-plan]]):
a concept build runs from its first basic MVP (mock or real, wrong output still counts) and
is refined; a planned build lands runnable slices against the requirements. It is NOT a
mandate to gold-plate every feature or expand scope beyond the ask ([[work-style-kiss-mvp-rtfm]]).
Related: [[work-style-kiss-mvp-rtfm]], [[plan-before-code]], [[build-mode-concept-vs-plan]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
