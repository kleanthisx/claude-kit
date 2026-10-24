---
name: recoverable-models-are-not-pulled-home
description: "Before releasing a rented box, record each model's sha256 + public source; do NOT copy re-downloadable model files home - local disk is tight (2026-10-08)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-08T22:31:03.249Z
---

Closing a rented box (2026-10-08), the operator said *"take the new models and the settings we used and lets
close it"*. I started a 48 GB scp of every model not held locally. Operator stopped it: *"as long as we can recover
them it's ok. no need for 48 gb of models right now. space is tight."*

**Why:** local disk is the scarce resource, not bandwidth or the files. A model with a recorded sha256 and a public
source (HF path, a model-hub version id) is recovered the moment a fresh box runs the setup script (5.5 min measured).
Copying it home costs tens of GB for nothing. "Take the models" meant "make sure we can get them back", not "download them".

**How to apply:** before any box release, write a `box_final/RECOVER.md`: every model file with bytes, sha256 computed
on the box, and its source; plus the inventory (ComfyUI/custom-node commits, launch line, pip freeze), the run dir and
the inputs as tarballs. Pull home only what has NO public source (our own LoRAs, outputs, logs). Ask before any
multi-GB copy to local disk. Precedent: the `box_final/RECOVER.md` written for an earlier image-model bench run.
Related: a related project note, [[provenance-or-nothing]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
