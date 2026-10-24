---
name: diff-before-discard
description: "`git checkout -- <file>` / `git restore` discard uncommitted work irreversibly and guard-destructive.ps1 does NOT catch them; run `git diff <file>` and ask before any discard (2026-10-04)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-04T21:01:01.074Z
---

To drop one line I had added to an RP project's `.gitignore`, I ran `git checkout -- .gitignore`. That also wiped other sessions' uncommitted lines, including the ignore rules for `webapp/data/.secret_key` and `webapp/data/app.db`. For a while both were un-ignored and open to a `git add -A`. I restored them from the transcripts (session 3cbbdebe 2026-09-29, 6ae7be97 2026-09-17).

Operator: *"how can you wipe out when there is a hook there?"* `guard-destructive.ps1` matches `reset --hard`, `clean -f`, `push --force` and `stash`. It did not match `checkout -- <path>` or `restore`. Fixed 2026-10-05 at the operator's word: patterns for `checkout --` / `checkout .` / `checkout -f` / `restore` (not `--staged` alone) / `switch --discard-changes`, and every git pattern now also matches `git -C <dir> ...`; 14 new cases in `test-hooks.ps1`, all green. The rule below still applies to forms the hook misses.

**Why:** a discard on a shared working tree destroys work that is not mine, and there is no undo.

**How to apply:**
- To remove my own change, edit the line out.
- Never discard a whole file.
- Before any `checkout --` / `restore` / `checkout .`, run `git diff <path>`, then ask.

Related: [[unattended-defer-gated-ops]], [[transcript-is-the-notes]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
