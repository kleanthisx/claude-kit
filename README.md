# claude-kit

The whole Claude Code working setup — enforcement hooks, session skills, the working agreement, and
the memory that carries *why* each rule exists — packaged so it can be installed on another machine
without disturbing what is already there.

Two repos already held halves of this: [`claude-hooks`](https://github.com/kleanthisx/claude-hooks)
(the guards) and [`shadowguard`](https://github.com/kleanthisx/shadowguard) (Judge Dread). Neither
carried the doctrine, and the memory files existed on exactly one disk with no copy anywhere.

## Install

```powershell
# always first, on a machine you do not own:
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -WhatIf

powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 `
    -Profile work `
    -MemoryDir "$env:USERPROFILE\.claude\projects\<encoded-dir>\memory"

powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Uninstall
```

`-MemoryDir` has no safe default: memory is **project-scoped**, living under
`<ClaudeHome>\projects\<encoded-working-dir>\memory\`, and the encoding differs per machine. Given no
value, the installer skips memory and says so rather than guessing.

## What it will not do to an existing setup

| | |
|---|---|
| `settings.json` | **Merged, never replaced.** Existing hooks, permissions and preferences are kept; only missing entries are added. Verified by installing over a foreign config: their Stop hook survived alongside Judge Dread, `model` and `defaultMode` were left as found. |
| `permissions.defaultMode` | **Never written.** The source machine runs `dontAsk`; pushing that onto a work laptop is the riskiest line in the package, so the installer refuses to touch it. |
| `~\CLAUDE.md` | If one exists it is **left alone** and you are told to merge by hand. An installer should not overwrite a working agreement. |
| Backups | Written **lazily** — only when a run actually changes something, so a no-op re-run cannot leave a backup of the already-merged state. |
| `-Uninstall` | Restores the **oldest** backup (the true pre-kit state) and removes the copied hooks. Memory and doctrine are left: they are content, not wiring. |

Idempotent: the second run reports `14 of 14 same`, `0 to add`, `+0 new` permissions, and writes nothing.

## Memory tiers

45 method rules, split by what their evidence names — because the *why* is the value, and a rule
stripped of its incident is just an assertion.

- **`core/`** (32) — method with no project in the evidence.
- **`core-generalised/`** (13) — the same rules whose incident involved a private project, rewritten
  so the project is *described* rather than named. Numbers, quotes and lessons unchanged; each file
  carries a footer saying it was generalised. Verified: zero project identifiers remain.
- **`core-sensitive/`** (13) — the originals of those same 13, for the home machine.
- **`personal/`** (20) — project state and machine specifics. **Not in this repo.** It is
  git-ignored and lives only on the home machine; a clone will not contain it, and `-Profile home`
  will simply find no `memory/personal` directory and install the other tiers.

`-Profile work` installs `core` + `core-generalised` = **all 45 rules, nothing withheld, no project
named anywhere**. `-Profile home` installs `core` + `core-sensitive` (+ `personal` if present locally)
= the originals.

Everything published here is portable method. Project state never leaves the machine it belongs to.

## The directives are injected in full, not summarised

`session-rules.ps1` (SessionStart + PostCompact) injects **every method file in the memory
directory, in full** -- measured 2026-09-16: **45 files, ~106 KB, ~26.5k tokens per injection**.

It used to inject `RULES.md` alone, a 3.6 KB summary. That was the bug: with a summary in context and
`MEMORY.md`'s one-line index auto-loaded, a session has the *appearance* of the directives and none of
their evidence, and reciting from that appearance is indistinguishable from reciting from the files.
A summary cannot prove a read.

The injection opens with a short precedence header (829 chars, the only added text) stating that these
standing instructions outrank the harness's default tool-choice steering -- scoped to method, and
explicitly NOT overriding safety rules or a live instruction in the user's current message. A blanket
override was rejected on the evidence in `enforcement-approaches-evidence`: contradictory rule sets
produce fabrication rather than refusal.

**The dial is `memory/inject-exclude.txt`**, one basename per line, `#` comments allowed. It ships
listing project-state files -- inventory rather than method, and the bulk of the bytes. Tune the cost
there; do not tune it by going back to a summary.

## Before you trust it on a new machine

1. **Is `claude` on `PATH`?** Judge Dread shells out to `claude -p` for every verdict. Without it he
   fails open — and a dark judge is indistinguishable from an approving one. The installer checks and
   warns.
2. **Judge Dread costs one `claude -p` per turn.** That is the deliberate trade: it catches unbacked
   claims and substituted methods. `/judge quiet` or `/judge off` if a given machine shouldn't pay it.
3. **Run the suites.** `tests\test-hooks.ps1` → 80 PASS / 0 FAIL / 1 SKIP. `tests\test-judge-dread.ps1`
   needs the CLI.
4. **`verify-done.ps1` is superseded** by Judge Dread and is shipped as a record only. Wiring both
   would audit the same Stop event twice and pay two model calls per turn.

## Known gaps, carried over honestly

`guard-destructive.ps1` covers *recursive* deletion typed at the prompt. It does **not** catch a
forced delete of named files (`rm -f a.json b.log`), and it cannot see deletion inside a script file —
it only ever receives `tool_input.command`, so `python run_x.py` is invisible while an inline
`os.remove(p)` is caught. Both were measured, both hit live. `test-delete-coverage.py` asserts the
current behaviour as intended (cases `plain-rm-file`, `py-script`), so closing them means flipping
two green assertions — a decision, not a patch.
