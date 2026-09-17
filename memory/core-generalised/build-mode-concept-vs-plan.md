---
name: build-mode-concept-vs-plan
description: "There is ALWAYS a plan — fuzzy at the start, held and steered by the user. Three stages: get acquainted → draft 1 complete in every aspect → work from there. What varies by project is whether a PLAN.md artifact is enforced, not whether a plan exists."
metadata:
  node_type: memory
  type: feedback
  originSessionId: 649df042-b2c0-49fe-8801-3d981f00dc59
  modified: 2026-08-11T15:37:11.700Z
---

**CORRECTED 2026-08-11.** This file previously said concept work has "NO plan" and "there is nothing to plan". That was wrong. Absence of a PLAN.md ceremony is not absence of a plan. User: *"there is always a plan but at the beginning is fuzzy… just because you are blind to it doesn't mean it doesn't exist."*

**The plan always exists. It starts fuzzy and sharpens as it goes.** Its shape, in the user's words:

1. **Get acquainted.** A first impression of what has to be done and what is already out there. General orientation, before committing to anything.
2. **Draft 1 — complete in every aspect.** Rough everywhere rather than polished in one corner. Applies equally to research and to software.
3. **Work from there.** Refine the whole thing, repeatedly. Wrong output is still output — it's a drawing you refine.

**What varies by project is enforcement, not existence.** On a related note (a client app) the plan is a formal artifact: numbered plan → `PLAN.md` → wait for GO → add `APPROVED: GO`. Everywhere else the user holds the plan and steers in real time, because the territory is uncertain and steering beats sign-off. That is a choice about ceremony — not evidence that planning is absent.

**Invariant across every project — it must always run and be testable.** That is what "no piecemeal" ([[code-structure-no-piecemeal]]) means: vertical slices that run, not horizontal modules sitting dead.

**Why:** 2026-08-11 — I trimmed CLAUDE.md to say plan-first applies to a client app only, citing this file, and was corrected on the spot. Earlier the same day I skipped stage 1 outright on a brand-new project: proposed research lanes and launched 12 agents without ever getting acquainted with the domain first. To plan is to know; skipping it means not discovering my own ignorance until it has already cost something.

**How to apply:** State which stage I think we're in and check it, rather than assuming there is no plan. Do stage 1 before proposing work. Make drafts complete-in-every-aspect rather than deep in one corner. Related: [[plan-before-code]], [[work-style-kiss-mvp-rtfm]], [[research-method-rules]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
