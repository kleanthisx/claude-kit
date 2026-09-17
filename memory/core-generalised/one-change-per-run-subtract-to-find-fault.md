---
name: one-change-per-run-subtract-to-find-fault
description: "User's debugging principles — start basic, change ONE thing per run and verify; when lost, take things away until the fault disappears, fix at that level, build back up (2026-09-11, state tracker)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c70b1007-9573-41fe-8972-5240b6dc2ff7
  modified: 2026-09-11T19:19:46.692Z
---

Two stated principles (user, 2026-09-11, while tuning the an RP project state tracker):
1. "Always start basic and add/remove/change a single thing at a time."
2. "When things get complicated and can't find the fault you take away until the fault disappears. Then you know what caused it. You debug on that level and then build it up again."

**Why:** with two changes in one run (model swap + tracker fix) a quality change can't be attributed; the user was reluctant to swap models for exactly this reason. Subtraction isolates the layer (an RP project 2026-09-11: removing the character card from the tracker prompt exposed the card-copy bug; run 2's added context changed nothing and was proven irrelevant).

**How to apply:** make the change list explicit, run one change per verification run with its own output file/flag so every run is reproducible, report the delta per run in a table, and let the user pick the next change. Keep the previous run's config as the baseline for the next. When a run confounds two things, split it. Related: [[verify-moves-by-running]], [[stage-per-script-never-mutate]], [[diagnose-layer-before-rebuilding]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
