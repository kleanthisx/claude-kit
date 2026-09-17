---
name: verify-against-authority-not-recall
description: "don't \"correct\" a model or state a fact from recall — check the manual/compiler; compile-clean != correct; a model's self-diagnosis is a claim, not a finding"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 555e6469-b088-499b-b0e7-6b7f197ad198
  modified: 2026-08-17T12:06:26.783Z
---

On a pipeline project's 5-model A/B (2026-08-17) I relayed each model's self-diagnosis of its own compile error as ✅/❌, and "corrected" model 2 with a recalled SD4 rule — "`@` binds only a payline, its `@ {coords}` was invented." The manual (`manual-core.md:200`, `substitute wild = all except scat @ {1:0,1:1,1:2};`) proves `@ {coords}` is VALID. My correction was false. I had also called builds "clean/coherent" having read only the ~10-line window around each error, never the full file.

The user caught it: *"is it correct though? have you read the code? or did the model say it was correct?"*

**Why:** trusting recall over the source is exactly where fabrication leaks (same failure class as [[report-verifiable-only]]). Asserting a made-up rule to overrule the model is worse than relaying the model's claim, because it wears the costume of a correction.

**How to apply:**
1. A compile-error COUNT is verified only if I actually ran the compiler (the project's math-build executable). Say "ran X -> Y".
2. An error's CAUSE, and any "correct form", must be checked against `manual-core.md` / the SD4 grammar before I assert it — never from memory. Grep the manual first ([[check-project-prior-art]]).
3. compile-clean != game-correct. To claim a build is correct I must read the full code against the state-graph, or run the reviewer stage — not infer it from line count + low error count.
4. A model's self-assessment is the MODEL'S claim; label it as such until verified against the authority. Do not upgrade "the model said X" into "X" by restating it.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
