---
name: transcript-is-the-notes
description: "The session transcript IS the authoritative log — recover exact past tool-call content from it, never reconstruct from memory; and never overwrite an artifact that produced a kept output."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 197c5409-8bd1-42d1-b07f-e1f310de7987
  modified: 2026-09-11T17:01:53.664Z
---

When an exact past value is needed (a prompt, a script, a command that produced a kept result), the session transcript is the ground truth — do NOT reconstruct it from recall and present the reconstruction as the original.

**Why:** On a pipeline project (2026-08) I overwrote `generate_bg.py` (which had produced the loved `bg_painterly` background), then "recovered" its prompt from memory and logged it. My reconstruction silently dropped the final clause `, no photographic realism`, so re-running it gave a near-twin, not the original — and I wrongly blamed "GPU nondeterminism." The user (rightly, twice, with frustration: "how could you not take notes?") sent me to the transcript. The exact prompt was there verbatim; extracting it and re-running reproduced the image **bit-for-bit (mean-abs-diff 0.0000)**.

**How to apply:**
- Transcripts live at `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl` (Windows: `C:\Users\<you>\.claude\projects\<encoded-cwd>\*.jsonl`). Each line is a JSON message; tool calls are `type:"tool_use"` blocks with full `input` (e.g. a Write's `file_path`+`content`). Grep for a distinctive token, `json.loads` the line, walk for the `tool_use`. Reusable extractor: the project's local `extract_prompt.py`.
- **Never overwrite** a script/config that produced a kept artifact — version it (`foo2.py`) and log the exact prompt+seed+params the moment the output is a keeper (see [[provenance-or-nothing]]).
- **Search the transcripts before declaring something absent.** Transcripts are the ultimate truth, above the wiki and the disk. On 2026-09-11 I reported "no HF token" after checking env, cache files, credential manager and wikis, but never grepped the JSONLs, and the user had one. For credentials, mask the output (print only a prefix and length).
- When exactness matters, **verify** by re-running and diffing (bit-identical, not "looks the same"). Deterministic pipelines (e.g. a fixed-seed image model) make this a hard check, not a vibe.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
