---
name: verify-moves-by-running
description: "A file copy/move is NOT verified until the relocated code actually RUNS from its new home; byte-diff + import-check are hints, not proof — keep the originals until a real run passes"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-08T03:24:37.932Z
---

When I copy/move code (or any artifact) to a new location, **byte-identity and an import check are not proof it works there — an actual execution from the new location is.** "A test is worth a 1000 expert opinions" (user, recurring — see [[work-style-kiss-mvp-rtfm]]).

**Why:** the user: "it is not the first time I trusted you to copy something and it was not copied correctly." Proven the same session — my `build_stages.py` reported "success" while Python's `pathlib` silently wrote to a stray `<drive>:\d\...` path instead of the intended drive (Bash `/d/` ≠ Python drive). A tool's "OK" is a claim; only running the moved thing on the real path exercises cwd/relative-path/env assumptions a diff can't see.

**How to apply:**
- After a move, **run the relocated code end-to-end** (produce its real output), don't stop at diff/import. Offer to run it; provide the exact command if the user wants to run it themselves.
- **Keep the originals as the safety net until a real run passes** — the user's rule. Don't delete/overwrite the source copy on the strength of a byte-diff.
- **Same principle, earlier instance, 2026-07-31** (merged 2026-10-08 from the retired memory folder of an RP project,
  original in a related project note as `done-means-verified-end-to-end`): I reported the turbo2
  launcher "ready" after a parse check and a flag check, without loading a model through it. A per-model flag
  bug (gemma `-rea on` -> empty content) sat there until the operator found it by testing: "you report done,
  i test, it's not". "Parses / flags present / file exists" is CONFIGURED; only "I ran it and saw the real
  output" is DONE. Say which of the two a claim is; if it cannot be run end to end, say "configured, not
  verified".
- Report it as evidence: "ran `<cmd>` from the new location → `<output/exit>`", per [[report-verifiable-only]]. Reuse the [[transcript-is-the-notes]] bit-diff, but treat it as necessary-not-sufficient.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
