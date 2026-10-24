---
name: diagnose-layer-before-rebuilding
description: "When something \"is broken\", find WHICH layer broke before rebuilding — don't reimplement a working component"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-12T18:51:16.009Z
---

When told "X is broken, rebuild it", first identify **which layer** actually failed — do not reimplement a component that still works.

**Why:** a pipeline project, 2026-09-04 — the user said the pipeline was broken ("anything beyond commandline is not usable"). I rebuilt the whole **engine** from scratch. Wrong: only the **Streamlit GUI** was broken; the engine (`runner.py`) was fine (6 themed test-build runs logged that day proved it). My reimplemented engine diverged from the prior version's tuned prompts and produced worse SD4 (value-explosion, RNG errors). User: *"you probably build the wrong thing... other than the gui it was working fine."*

**How to apply:**
- Before rebuilding, run the diagnosis: import/parse each layer, run each in isolation, read the prior transcripts/logs. Name the broken layer with evidence.
- Root-cause it: here, `runner.run()` is a live Python generator holding state between yields; Streamlit reruns the whole script per interaction and can't persist a live generator → the fragile rebuild-on-click hack = "unusable". Framework mismatch, not a one-line bug.
- Fix = replace ONLY the broken layer, reusing the working one. New driver imports the working engine **read-only** (never modified); holds the generator on a persistent background thread (http.server + SSE), not Streamlit.
- **A local model's settings are such a layer.** Earlier instance, 2026-07-31 (merged 2026-10-08 from the
  retired memory folder of an RP project, original in a related project note as
  `diagnose-model-settings-before-replacing`): to "gemma is an idiot" I recommended replacement models
  (two models marketed for RP) and diagnosed only after the operator twice said "fix gemma". The cause was one flag:
  `-rea on` sent the whole token budget into the thought channel and returned empty content on open-ended
  prose; `-rea off` fixed it at once. On "model X is bad": load it, read the raw response (reasoning vs
  content, finish_reason, token usage), vary its per-model settings (reasoning mode, template, sampling, KV
  type, budget); a different model only after settings are ruled out. Pin flags per model AND use case.
- **Fix it in the layer that made it, not downstream of it.** 2026-10-12, image bench: our skin came out overexposed
  (skin highlights near white, shadows flat - measured inside the operator's own circles). I built three
  rounds of post-processing (soft/diffusion, a skin-mask colour transfer, a fill-light curve); the skin mask itself was
  dirty and the third round brightened what it should have darkened. Operator: *"no. you go about it wrong"*, then *"cant
  fix what's broken. it needs a promt adjustment. that's it. pixel peeping can only take you so far."* The exposure and
  lighting are made by the generator, so the knob is a prompt word (lighting, skin finish, highlights) on the generating
  model and on the edit model, not a pass over the finished pixels.
- Deliverable: the project's `pipeline/webgui/` (bridge.py imports the prior runner read-only; webui.py = SSE driver). Verified by a REAL build → base compiled clean, RTP 87.27% = the prior working number. See [[stage-per-script-never-mutate]], [[verify-moves-by-running]], [[transcript-is-the-notes]].

**2026-10-21, an inference engine on the 3090:** decode was 5-6 tok/s against 39 on the node. I followed the engine's own
warning (VRAM below 1 GiB, "driver pages GPU memory") through two restarts with a bigger reserve; nothing moved.
The operator asked "is the ngram on E? if so then maybe that's it". It was: the `--ple-gguf` shard is the n-gram
table, read with random 4 KiB reads per token, and it sat on a USB HDD. On an SSD decode went to 94-111 tok/s.
**The rule:** before accepting a program's self-diagnosis, list every per-token I/O path (which file, which disk,
which bus) and check each against the machine where it worked. A warning that also prints on the fast run is
not the cause. Record in the local-infra wiki page.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
