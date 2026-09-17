# claude-kit

**Start at [`BOOTSTRAP.md`](BOOTSTRAP.md)** — what this is, the measured problem each piece
addresses, how the pieces tie together, the full rule list, costs/limits, and how to adapt it at a
new site. This README is the shorter, install-focused version.

The whole Claude Code working setup — enforcement hooks, session skills, the working agreement, and
the memory that carries *why* each rule exists — packaged so it can be installed on another machine
without disturbing what is already there.

Two repos already held halves of this: [`claude-hooks`](https://github.com/kleanthisx/claude-hooks)
(the guards) and [`shadowguard`](https://github.com/kleanthisx/shadowguard) (Judge Dread). Neither
carried the doctrine, and the memory files existed on exactly one disk with no copy anywhere.

## Layout

```
install.ps1          the installer (see below)
BOOTSTRAP.md          read this first
doctrine/             the working agreement (CLAUDE.md, RULES.md, RATIONALE.md) -- installed
memory/               tiered method rules + evidence -- installed (tier depends on -Profile)
hooks/                the enforcement layer (PowerShell, PreToolUse/PostToolUse/Stop/SessionStart/...) -- installed
skills/               enter / judge / wrap SKILL.md -- installed
agents/               scribe.md -- installed, {{CLAUDE_HOME}} substituted
tools/                render_session.py, statusline-usage.ps1, tally-usage.py -- installed
settings/             hooks.json + permissions.json fragments merged into settings.json by install.ps1
tests/                test-hooks.ps1, test-entity-read.ps1, test-delete-coverage.py, test-judge-dread.ps1
templates/            REFERENCE ONLY -- never installed; see BOOTSTRAP.md "Adapting at a new site"
wiki-v1/, wiki-v2/    REFERENCE ONLY -- never installed; two wiki designs to build from, not copy
```

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
| `settings.json` | **Merged, never replaced.** Existing hooks, permissions, `statusLine` and preferences are kept; only missing entries are added (a `statusLine` is added only if the target has none at all). Verified by installing over a foreign config: their Stop hook survived alongside Judge Dread, `model`/`defaultMode`/`statusLine` were left exactly as found. |
| `permissions.defaultMode` | **Never written.** A `dontAsk` source machine pushing that onto a work laptop is the riskiest line in the package, so the installer refuses to touch it. |
| `~\CLAUDE.md` | If one exists it is **left alone** and you are told to merge by hand. An installer should not overwrite a working agreement. |
| Backups | Written **lazily** — only when a run actually changes something, so a no-op re-run cannot leave a backup of the already-merged state. |
| `-Uninstall` | Restores the **oldest** backup (the true pre-kit state) and removes the copied hooks/agents/tools. Memory and doctrine are left: they are content, not wiring. |

Idempotent: a second run reports every file as `same:`, `0 to add`, `+0 new` permissions,
`statusLine : already set`, and writes nothing.

## Memory tiers

Counts below are what is currently on disk in this repo — recompute after any edit, do not reuse
these numbers (`install.ps1`'s own messages compute them at run time rather than hardcode them, for
the same reason).

- **`core/`** (17 files) — method with no project in the evidence. Ships on every profile.
- **`core-generalised/`** (43 files) — the rules whose evidence named a project, rewritten so the
  project is *described* rather than named, **plus** the `gem-*.md` generic lessons that never had a
  project-named counterpart. Numbers, quotes and lessons unchanged from their originals; each
  generalised file carries a footer saying so. Ships on every profile.
- **`core-sensitive/`** (30 files) — the named originals of the generalised rules above. **Not in a
  fresh clone** — it is git-ignored and lives only on the machine it was written on.
- **`personal/`** (21 files) — project state and machine specifics, plus the home-only
  `inject-exclude.home.txt`. Also git-ignored, also absent from a fresh clone.

`-Profile work` installs `core + core-generalised` = **60 files, nothing withheld, no project named
anywhere**. `-Profile home` installs `core + core-sensitive + personal` = **68 files**, but only on
the machine that has those git-ignored tiers — a clone made elsewhere gets `core` only, and the
installer says so per tier rather than silently installing less than the profile implies.

Everything published here is portable method. Project state never leaves the machine it belongs to.

## The directives are injected in full, not summarised

`session-rules.ps1` (`SessionStart` + `PostCompact`) injects **every method file in the installed
memory tier, in full**, plus `doctrine/RULES.md` (3.9 KB): currently **~141 KB / ~35k tokens** for
the work profile (60 files), **~193 KB / ~48k tokens** for the home profile (68 files, home machine only).

It used to inject `RULES.md` alone, a 3.6 KB summary. That was the bug: with a summary in context and
`MEMORY.md`'s one-line index auto-loaded, a session has the *appearance* of the directives and none of
their evidence, and reciting from that appearance is indistinguishable from reciting from the files. A
summary cannot prove a read.

The injection opens with a short precedence header (829 chars, the only added text) stating that these
standing instructions outrank the harness's default tool-choice steering — scoped to method, and
explicitly NOT overriding safety rules or a live instruction in the user's current message. A blanket
override was rejected on the evidence in `memory/core/enforcement-approaches-evidence.md`: contradictory
rule sets produce fabrication rather than refusal.

**The dial is `memory/inject-exclude.txt`** (or `memory/personal/inject-exclude.home.txt` on the home
profile — the installer picks the right one automatically), one basename per line, `#` comments
allowed. Tune the cost there; do not tune it by going back to a summary.

`load-wiki.ps1` (also `SessionStart` + `PostCompact`, right after `session-rules.ps1`) additionally
injects a v2 project's generated wiki surfaces when one exists — measured ~74 KB / ~19k tokens on one
project (`hooks/README.md`); no-op everywhere else.

## Before you trust it on a new machine

1. **Is `claude` on `PATH`?** Judge Dread shells out to `claude -p` for every verdict. Without it he
   fails open — and a dark judge is indistinguishable from an approving one. The installer checks and
   warns.
2. **Judge Dread costs one `claude -p` per turn.** That is the deliberate trade: it catches unbacked
   claims and substituted methods. `/judge quiet` or `/judge off` if a given machine shouldn't pay it.
3. **Run the suites.** `tests\test-hooks.ps1` (86 PASS / 0 FAIL / 1 SKIP as of this writing — the
   SKIP is `verify-done.ps1`'s superseded cases, opt in with `-IncludeSuperseded`).
   `tests\test-entity-read.ps1` (9 PASS / 0 FAIL). `python tests\test-delete-coverage.py` (42 cases,
   `ALL GREEN`). `tests\test-judge-dread.ps1` needs the CLI and makes live model calls — not run as
   part of finishing this repo.
4. **`verify-done.ps1` is superseded** by Judge Dread and is shipped as a record only. Wiring both
   would audit the same Stop event twice and pay two model calls per turn.
5. **`settings/permissions.json` is a starting point, not a finished list.** Every entry naming a
   home path, a home project, a home-research web domain, a local model server, or GPU tooling was
   removed before this repo was finished — see `BOOTSTRAP.md` §e. What's left is generic developer
   commands; add what the new site's own tools actually need.

## Known gaps, carried over honestly

`guard-destructive.ps1` covers *recursive* deletion typed at the prompt. It does **not** catch a
forced delete of named files (`rm -f a.json b.log`), and it cannot see deletion inside a script file —
it only ever receives `tool_input.command`, so `python run_x.py` is invisible while an inline
`os.remove(p)` is caught. Both were measured, both hit live. `test-delete-coverage.py` (the matrix, beside the suite) was RUN: **ALL GREEN, 42 cases, exit 0**. It does
NOT omit these two shapes — it asserts them as allowed: the cases `plain-rm-file` and `py-script`
both carry `expected=PASS`. So neither finding above is an oversight; both are encoded current design, and
"fixing" them means flipping two green assertions. That is a call for the user, not a patch to slip in.

`guard-agent-fleet.ps1`'s spawn counter is per-session, so a spawn burst split across two sessions is
not aggregated. See `hooks/README.md` for the rest of the per-hook gaps.

Full detail on every problem this kit addresses, with sources, lives in [`BOOTSTRAP.md`](BOOTSTRAP.md).

## License

[CC0 1.0 Universal](LICENSE) — public domain dedication. Use, copy, modify and redistribute for any purpose, with no permission or attribution required.
