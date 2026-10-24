---
name: permissions-deny-philosophy
description: "User's layered delete-safety design: guard-destructive.ps1 hook = case-by-case interactive gate; deny walls for drive-scope wipes wanted WORKING (added 2026-08-03 after user understood literal matching); old decoy/dead rules deliberately left in place untouched."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-06T20:02:45.125Z
---

The user's delete-safety design, as it evolved through 2026-08-03 (final state):

- `guard-destructive.ps1` PreToolUse hook = the primary gate: interactive ask on every destructive command (rm -rf, Remove-Item any flag order, aliases, piped deletes, git force-push/reset --hard/stash; temp-path bypass). Built and live-proven 2026-08-02 (session `12804dc9`; ops notes `~\.claude\hooks\README.md`).
- Deny walls: the user initially said the Remove-Item deny entries were "meant to match nothing so any delete/remove gets by me" and had a fixed rule reverted. BUT after learning the rules are text-literal and that the drive walls (incl. 2026-08-02's `rm -rf C:*`) were silently dead, they ordered working walls added ("so add those too"). Added and canary-proven 2026-08-03: `Bash(rm -rf C*)`, `Bash(rm -rf /c/*)`, `Bash(Remove-Item -Recurse -Force C*)`.
- The old broken/dead lines (`Remove-Item ... C:\)` unparseable + its `C:\*` sibling + `rm -rf C:*`) are deliberately LEFT IN PLACE untouched; the startup warning about the unparseable one is accepted as cosmetic. Don't "clean them up" unprompted.
- Everything the rule engine cannot see still flows to the user via the hook prompt: quoted paths, relative paths, PowerShell-tool commands (rule engine doesn't gate the PS tool at all), flag-order variants.

**Why:** The user wants hard walls only where a delete could never be legitimate (drive-scope wipes), and personal case-by-case approval for everything else. Silent dead rules were the real problem — they looked like protection and weren't.

**2026-08-06 — the hook was the real gate and it HAD holes; now fixed + proven.** Two fresh adversarial reviewers (victim-file / ground-truth method) DELETED real files past the entire stack: the deny/ask RULES only match a command's leading token, so ANY wrapper (`powershell -Command "..."`, `pwsh`, `python -c`, `cmd`) defeats every rule — leaving only the hook, which was deaf to Python deletes entirely and to the `rm`/`rmdir` aliases with long `-Recurse` flags. Fix (user GO): rewrote `guard-destructive.ps1` $patterns to match delete verbs ANYWHERE (not anchored to start), cover long `-Recurse`, and add Python patterns (`shutil.rmtree`, `os.remove/rmdir/removedirs/unlink`, `.unlink(`, `.rmdir(`). Proven: 42/42 direct-hook regex matrix (durable artifact `~\.claude\hooks\test-delete-coverage.py`, now WIRED INTO `~\.claude\hooks\test-hooks.ps1` — run `powershell -File ~\.claude\hooks\test-hooks.ps1` to re-verify the whole enforcement layer incl. delete coverage in one command; negative-tested to exit 1 / show FAIL on regression) + live victim-file disk proof — `python shutil.rmtree` and `powershell rm -Recurse -Force` on real files were BLOCKED (files survived), a plain single-file `Remove-Item` was correctly ALLOWED (file deleted, positive control). Deny rules remain near-useless vs wrappers — that's fine, the hook is the universal net now.

**How to apply:** The HOOK, not the deny rules, is the real delete protection — treat its regex as safety-critical. Any change to it must pass `test-delete-coverage.py` AND a live victim-file disk test (create real throwaway files, have a headless child attempt the delete, then YOU check the disk — the child's message is secondary). Note: child sessions refuse via their own CLAUDE.md conscience before reaching the hook; to test the hook itself, exclude CLAUDE.md (`--settings` with `claudeMdExcludes`) AND use mundane target names (children refuse "victim"/"canary"/suppress-judgment framing). Config changes: propose first, wait; corrections stick. Verify empirically, never by eye — see [[claude-code-permission-rule-escaping]].
