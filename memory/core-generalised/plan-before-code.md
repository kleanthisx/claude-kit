---
name: plan-before-code
description: "When the user opens vaguely ('fix a few things') they already have the change list — ask for it before touching code; and the formal PLAN.md gate applies to a client app/a client app"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d259a209-8a66-4334-b4e9-6debde5d9442
  modified: 2026-08-11T15:37:18.209Z
---

**Universal guard.** When the user opens with something vague like *"get it up and running and fix a few things"*, **they** hold the list. Ask for it before writing or changing code.

On one project's session (2026-07-20) I verified the stack and then autonomously chose and implemented three spec-vs-code fixes. The user had their own list. Result: tokens spent, code rewritten, none of it what they wanted.

**Formal plan artifact — a related note (a client app).** There the plan is written down and signed off: numbered plan → `PLAN.md` → wait for GO → add `APPROVED: GO`. It's a done-before, requirements-rich app, so there is a vast amount of readily-available requirement to plan against.

**Corrected 2026-08-11:** this file previously said other projects have "no plan". Wrong — see [[build-mode-concept-vs-plan]]. Every project has a plan (get acquainted → draft 1 complete in every aspect → work from there); what a client app additionally gets is the enforced artifact and the sign-off gate.

**How to apply:** Get-it-running and verification work proceeds immediately. Before writing or changing code on a vague open, ask what changes they have in mind. Related: [[work-style-kiss-mvp-rtfm]], [[build-mode-concept-vs-plan]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
