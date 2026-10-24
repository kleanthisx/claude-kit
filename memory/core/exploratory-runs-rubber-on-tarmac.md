---
name: exploratory-runs-rubber-on-tarmac
description: "Exploratory work = get a real run going early and watch what happens; practice exposes what design cannot. \"Theory and practice are the same in theory and different in practice.\""
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-17T14:13:24.718Z
---

When the operator frames work as exploratory, **put rubber on the tarmac**: build the smallest thing
that runs, run it on real data, and let the results drive the next change. Do not front-load design,
research lanes and vocabulary before anything has been executed.

Operator, 2026-09-17: *"these are exploratory runs you know? put some rubber on the tarmac and see
what happens. theory and practice are the same in theory and different in practice. write that
down"*

**Why:** the same day showed it concretely. Hours of research and a vocabulary spec came first; the
real runs then produced every finding that mattered, and none of them were predicted by the design:
`commitment` extracts as pure noise (+/-30 of 100 with nothing changed); thinking makes the
abliterated MoE emit no JSON at all; a row-merge bug silently dropped every new field; four runner
copies ran concurrently because Git Bash `pkill` cannot see Windows processes; the 3090 hit 350 W, not
the ~303 W estimated. Each of those cost less to find by running than it would have to reason about.

**How to apply:** for exploratory tasks, get to a first real run within a few steps. Keep the design
pass to what the run needs. Treat estimates as hypotheses the run will overturn, and report what the
run showed, not what the design predicted. This refines [[build-mode-concept-vs-plan]] — draft 1 is a
RUNNING draft — and pairs with [[verify-moves-by-running]] and [[one-change-per-run-subtract-to-find-fault]].
Research still has its place when the operator asks for it ([[research-method-rules]]); the failure
is doing it instead of running, when running was the ask.
