---
name: label-by-model-not-letter
description: "In image tests, name every arm and review folder by the MODEL that made it (a base checkpoint, Qwen Edit...), never A/B/C - letters mean nothing to the operator (2026-10-05)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-04T21:18:06.363Z
---

Operator, 2026-10-05: *"you know a b c mean nothing to me. what model did them?"*

**Why:** the operator judges models and methods; arm letters force them to decode my scheme before they can say what
works. They had said "c, d and e work" without knowing those were all the same base checkpoint.

**How to apply:** folder, sheet and report labels say the model and the method, e.g. `checkpoint_direct`,
`qwen_edit_from_canon`, `checkpoint_i2i_over_qwen_d40`. If letters exist in a script, translate them in every report.
Related: a related project note, [[comms-terse-literal-westerner]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
