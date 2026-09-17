---
name: verify-moves-by-running
description: "A file copy/move is NOT verified until the relocated code actually RUNS from its new home; byte-diff + import-check are hints, not proof — keep the originals until a real run passes"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 788e6064-2a62-45bf-b73d-765501f4ab5c
  modified: 2026-08-24T16:04:39.954Z
---

When I copy/move code (or any artifact) to a new location, **byte-identity and an import check are not proof it works there — an actual execution from the new location is.** "A test is worth a 1000 expert opinions" (user, recurring — see [[work-style-kiss-mvp-rtfm]]).

**Why:** the user: "it is not the first time I trusted you to copy something and it was not copied correctly." Proven the same session — my `build_stages.py` reported "success" while Python's `pathlib` silently wrote to `C:\d\...` instead of `D:\` (Bash `/d/` ≠ Python drive). A tool's "OK" is a claim; only running the moved thing on the real path exercises cwd/relative-path/env assumptions a diff can't see.

**How to apply:**
- After a move, **run the relocated code end-to-end** (produce its real output), don't stop at diff/import. Offer to run it; provide the exact command if the user wants to run it themselves.
- **Keep the originals as the safety net until a real run passes** — the user's rule. Don't delete/overwrite the source copy on the strength of a byte-diff.
- Report it as evidence: "ran `<cmd>` from the new location → `<output/exit>`", per [[report-verifiable-only]]. Reuse the [[transcript-is-the-notes]] bit-diff, but treat it as necessary-not-sufficient.
