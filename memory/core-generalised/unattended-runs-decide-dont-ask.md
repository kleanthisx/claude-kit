---
name: unattended-runs-decide-dont-ask
description: "On a paid, unattended compute run (rented GPU), never end a turn with a menu or question — pick the next step, queue it so the box stays busy, and report; stop only for the brief's hard limits"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-05T10:54:39.178Z
---

When a rented box is running and the operator has handed over a goal, **decide the next step yourself and
launch it in the same turn.** Report what was chosen and why in one line; do not offer options and wait.

**Why:** 2026-09-17, an RP project's image bench on a $0.721/hr rented 5090. After finishing the untested-model
round I listed three next options, asked "want any of these?" and set an idle-pause timer. Operator: *"yes. look
you run this unattended. if you keep asking me things time goes and we pay for nothing"*. Every question on a
billed box converts the operator's attention into idle GPU time.

**Repeated 2026-10-05** (a second rented box, $0.825/hr): I finished the IP-Adapter test, offered "a next run, not
started", and left the box idle. Operator: *"You will either use the box for research or turn it off. Waiting on
me when i am not there while paying on idle.. is not a great way to be productive. ... Your call."* So the turn
must END with exactly one of: a queued run working toward the open questions, or the box paused (and its outputs
already pulled home). "Idle, waiting for a verdict" is never a valid end state.

**How to apply:**
- Keep a queue: when one batch is launched, the next is already decided; chain them in one box-side script.
- Still stop for the hard limits the brief names — irreversible actions, paid/outward actions (e.g. buying
  a model-hub Early Access with site credits), spend past the cap — and say which limit it hit.
- Questions only when a choice would change spend or be irreversible; otherwise choose the cheapest
  informative step and log the reasoning.
Related: [[unattended-defer-gated-ops]], [[bound-the-user-facing-blast-radius]], [[question-mark-is-a-full-stop]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
