---
name: diagnose-layer-before-rebuilding
description: "When something \"is broken\", find WHICH layer broke before rebuilding — don't reimplement a working component"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7bdfbc80-44f2-4500-ba78-7bd75a444a02
  modified: 2026-09-05T18:50:48.042Z
---

When told "X is broken, rebuild it", first identify **which layer** actually failed — do not reimplement a component that still works.

**Why:** a pipeline project, 2026-09-04 — the user said the pipeline was broken ("anything beyond commandline is not usable"). I rebuilt the whole **engine** from scratch. Wrong: only the **Streamlit GUI** was broken; the engine (`runner.py`) was fine (6 themed test-build runs logged that day proved it). My reimplemented engine diverged from the prior version's tuned prompts and produced worse SD4 (value-explosion, RNG errors). User: *"you probably build the wrong thing... other than the gui it was working fine."*

**How to apply:**
- Before rebuilding, run the diagnosis: import/parse each layer, run each in isolation, read the prior transcripts/logs. Name the broken layer with evidence.
- Root-cause it: here, `runner.run()` is a live Python generator holding state between yields; Streamlit reruns the whole script per interaction and can't persist a live generator → the fragile rebuild-on-click hack = "unusable". Framework mismatch, not a one-line bug.
- Fix = replace ONLY the broken layer, reusing the working one. New driver imports the working engine **read-only** (never modified); holds the generator on a persistent background thread (http.server + SSE), not Streamlit.
- Deliverable: the project's `pipeline/webgui/` (bridge.py imports the prior runner read-only; webui.py = SSE driver). Verified by a REAL build → base compiled clean, RTP 87.27% = the prior working number. See [[stage-per-script-never-mutate]], [[verify-moves-by-running]], [[transcript-is-the-notes]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
