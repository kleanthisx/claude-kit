---
name: plan-before-code
description: "When the user opens vaguely ('fix a few things') they already have the change list — ask for it before touching code; and the formal PLAN.md gate applies to one gated client app"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-01T05:59:22.194Z
---

**Universal guard.** When the user opens with something vague like *"get it up and running and fix a few things"*, **they** hold the list. Ask for it before writing or changing code.

On an RP project's session (2026-07-20) I verified the stack and then autonomously chose and implemented three spec-vs-code fixes. The user had their own list. Result: tokens spent, code rewritten, none of it what they wanted.

**Formal plan artifact — a related project note (a client app).** There the plan is written down and signed off: numbered plan → `PLAN.md` → wait for GO → add `APPROVED: GO`. It's a done-before, requirements-rich app, so there is a vast amount of readily-available requirement to plan against.

**Corrected 2026-08-11:** this file previously said other projects have "no plan". Wrong — see [[build-mode-concept-vs-plan]]. Every project has a plan (get acquainted → draft 1 complete in every aspect → work from there); what that client app additionally gets is the enforced artifact and the sign-off gate.

**2026-10-01, same failure from the other side:** user said "what i want from you is very specific and very simple. i asked it yesterday as well but somehow it got fucked up" — I went to search yesterday's transcripts. Stopped: *"no, the proper thing is asking. not going back and searching all the time. listen, plan, act."* When the user is about to tell me what they want, ASK — the transcript is for recovering exact past values, not for pre-empting the person in front of me.

**How to apply:** Get-it-running and verification work proceeds immediately. Before writing or changing code on a vague open, ask what changes they have in mind. Related: [[work-style-kiss-mvp-rtfm]], [[build-mode-concept-vs-plan]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
