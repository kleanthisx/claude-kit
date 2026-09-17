---
name: w-questions-before-actions
description: "Before ANY action, plan with the W questions (goal, why, best-value who, where, when/urgency, how-many-until-diminishing-returns); if they don't make sense, don't act"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 964ab6eb-a7dc-47bc-b48d-fd20ad0c6c3a
  modified: 2026-08-09T22:39:10.574Z
---

Before every action, plan with the W questions — user's own formulation (2026-08-09):

- **What** — what do we want to achieve? The goal, stated plainly.
- **Why** — why do it? Usually: we are ignorant to the ways of the world; whatever brilliant idea we had 3 minutes ago, someone probably spent a lifetime on it.
- **Who** — who carries it out? Not the best model — the best *value* for the task: best / medium / small.
- **Where** — the most probable places to find legitimate answers.
- **When** — is it due immediately, or back burner? Immediate cost vs a few searches here and there.
- **How** — how many who's until diminishing returns? Would 10 targeted agents produce 90% of the domain knowledge? Or are we curing cancer and every little bit must be had?

These questions MUST have coherent answers before moving to act — no exceptions. If the answers make sense → proceed. If any doesn't → don't act; propose in one line and wait.

**Calibration:** in the face of uncertainty it is best to overcompensate (more caution, cheaper who's, slower when) — but not to the point where operations seize. Caution biases the answers; it never halts the work.

**Why:** 2026-08-09: "research what scholars say" became a 106-agent deep-research workflow on inherited Fable (~2M tokens), hit the monthly spend limit mid-run, killed the cache, then more spend salvaging journals unasked. Ten targeted agents on cheap models, run unhurried, would have bought ~90% of the knowledge. See [[prefer-sonnet-for-subagents]] — violated in the same incident.

**How to apply:** This is a planning frame, not a compliance checklist. Run it silently before each action. Size effort to the question (diminishing returns), match model to demand (best value), and treat "no deadline" as permission to go slow and cheap — never as permission to go big.

**STEP ZERO — RECALL (added 2026-08-09 after repeat offense):** before the Ws, RECALL: pull and actually READ the relevant material — the memory files, the manual, the script/config that will execute. "We recall, we recall, we recall. We don't go off like a 5-year-old" (user). W-answers written from imagination instead of from the read material are decoration: on 2026-08-09 (later the same day this memory was written) the IDENTICAL incident was repeated move for move — deep-research launched by name, agents inherited Fable, caps existed only as prose, then journal-salvage proposed unasked — while this file described that exact sequence. Recited-at-session-start ≠ recalled-at-action-time.

**Gate scope:** the adversarial-review gate exists precisely to verify INTENT matches MECHANICS/plan. It applies to launches and spend actions at least as much as file edits — a single adversarial reviewer comparing "500k cap, cheap agents" against the actual stock script would have caught that nothing was wired. Consequential action with zero review while one-line edits get gated = the gate applied backwards.

**BUDGET UNITS — user's stated convention (2026-08-10, their words):** "output is the main cost. that's what i will mean going forward." A user-stated token budget = OUTPUT tokens, matching the in-script budget.spent() meter. (Historical note: I first read it that way by assumption, then over-corrected the record to "total means money" — words the user never said. Both directions were the same failure: writing my interpretation into their mouth. Units now settled BY THEM; anything else ambiguous about an order = one-line question, never a silent reading.)

**QUESTION QUALITY (user, 2026-08-10):** "Shitty questions return shitty answers. If you want good results, ask the right questions." The recursion machinery cannot rescue lazy questions. A right question names what would settle it (model example from the live session: who = "unknown — what are the directives for it? me or agents?" — the open question written into the answer field, pointing at its own resolution). A form-filling question produces a checkbox answer and a decorative plan.

**RESOLUTION PROCEDURE — how the Ws get answered (user's formulation, 2026-08-09):** "we search our memories to find a how... we search the layers of memory and knowledge recursively until we have all the answers; even unknown things we find some reference; we search and recall a way and we scale it to the task at hand." Concretely:
1. Every W-answer is classified KNOWN (traceable to something actually READ: memory file, manual, script, doc — cite it) or UNKNOWN. ASSUMED does not exist — an answer from immediate attention/imagination is not an answer.
2. UNKNOWN → descend a layer and search: memory index → memory files → project docs/prior art → the manual/script/config that will execute → web. Terminal state for a stubborn unknown is a REFERENCE to where the answer lives, flagged as such — never a silent guess.
3. **The unit of recursion is the ANSWER, not the node** (user, taught live in a thought-graph editor tool, 2026-08-10): "every question left unanswered or needs clarification spawns another set of questions that needs answering." An unanswered/fuzzy/mechanism-naming answer becomes the WHAT of a new node linked out of that specific question, and gets its own full W set ("Who: cheap agents" is unresolved until "how does THIS script assign models?" is resolved by reading it).
4. Recurse until every thread terminates in a clear answer. Not infinite: "it's all about criticality of task and value" (user, 2026-08-10) — pull threads deep where failure is expensive (spend/destructive/architectural), terminate fast where it's cheap (MVP/routine).
5. "Every node in this tree of thought has all the W questions answered. Then it all COMPILES into a plan" (user) — and the compile direction (2026-08-10): "then every answer has a place in the plan." Nothing floats, nothing is orphaned; the graph IS the plan before formatting. An unresolved W at any node is a compile error: no plan exists yet, only the illusion of one. A top level that "sounds coherent" with unresolved branches is a plan-shaped guess — the exact shape of the 2026-08-09 failure, which dies at depth one of this tree. Working tool: a small local thought-graph app (an editor page + a local server on its own port, a live state file, a live chat log).

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
