---
name: stage-per-script-never-mutate
description: "In an iterative gen/build pipeline, each stage = its OWN new script; never edit the previous stage's script in place — mutation destroys the reproducible record of what worked"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 788e6064-2a62-45bf-b73d-765501f4ab5c
  modified: 2026-08-24T15:00:33.491Z
---

When iterating a generation/build pipeline (image, sound, or any multi-stage script chain), **save every stage as its own new file** (`gen_x.py` → `gen_x_op2.py` → …, or `..._v2`). **Never edit the previous stage's script in place to become the next stage.**

**Why:** editing in place overwrites the exact version that produced a kept output — the stage becomes unreproducible. On a pipeline project's asset pipelines (Aug 2026) I repeatedly mutated one script into the next stage; the finals survived but ~9 intermediate working versions existed only in the transcript. The user called it out: "you constantly changed the script for the next stage without keeping each stage separate. now we have no scripts per stage." This is the script-level twin of the existing image rule ("always write to a NEW filename — never overwrite").

**How to apply:**
- New stage → new filename. The previous stage's file stays frozen as the record of what worked at that stage.
- This is the *complete-in-every-aspect* / no-piecemeal discipline applied to time, not just modules — see [[code-structure-no-piecemeal]] and [[work-style-kiss-mvp-rtfm]].
- If it already happened, recovery is possible: replay the `Write`/`Edit` tool calls from the session JSONL in timestamp order — the bytes are exact, don't retype from recall. See [[transcript-is-the-notes]]. (Did this 2026-08-24: rebuilt the project's asset-stages archive — 49 stages + 22 recovered intermediates, byte-verified vs disk.)
- Windows path trap hit during that recovery: Python's `pathlib` does NOT understand Bash's `/d/` drive syntax — it silently writes to `C:\d\...` on the current drive. Use `D:\...` (or a raw Windows path) when a Python script must write to another drive.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
