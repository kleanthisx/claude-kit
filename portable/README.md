# portable/ - the kit without the installer

Use this where `install.ps1` cannot run or should not run: another operating system, a machine you do not
control (a work machine), or claude.ai. It carries the working agreement and the method as one file, plus the
wiki design and its tools. It installs nothing and runs no hooks.

## What to take

| file                                                                                         | what it is                                                                                                                                      |
| -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| [`CLAUDE.md`](CLAUDE.md)                                                                     | the working agreement and the method in one file: stop cases, turn-taking, verification, research, recording, communication                     |
| [`../wiki-v2/WIKI-PRIMER.md`](../wiki-v2/WIKI-PRIMER.md)                                     | how to build and keep a project wiki on existing work: page format, rules, the bootstrap process, the session routine                           |
| [`../wiki-v2/generate.py`](../wiki-v2/generate.py)                                           | builds `OVERVIEW.md`, `NAMES.md`, `DISCARDED.md`, `DECISIONS.md` from the pages and lints them                                                  |
| [`../wiki-v2/coverage.py`](../wiki-v2/coverage.py)                                           | lists project files no wiki page owns                                                                                                           |
| [`../wiki-v2/entity-template.md`](../wiki-v2/entity-template.md)                             | a blank wiki page                                                                                                                               |
| [`../wiki-v2/PROJECT-CLAUDE.md`](../wiki-v2/PROJECT-CLAUDE.md)                               | lines for a project's `CLAUDE.md` that load the wiki at session start                                                                           |
| [`../skills/enter/`](../skills/enter/SKILL.md), [`../skills/wrap/`](../skills/wrap/SKILL.md) | the session bookends; they work without the hooks. Their date command is PowerShell (`Get-Date -Format 'yyyy-MM-dd'`); elsewhere use `date +%F` |

The two Python scripts use only the standard library. They are written for Python 3.8 or later and were
tested on 3.10, 3.12 and 3.14 (3.8 and 3.9 not tested). The commands below say `python`; on macOS and Linux
that is usually `python3`.

About the skills: they handle two wiki generations. Use the v2 path (a `docs/wiki/entities/` folder), which is
what `WIKI-PRIMER.md` describes; the v1 path (append to `log.md`) is for older wikis. `/wrap` mentions the
`scribe` agent for turning a transcript into readable text; it is optional (`../agents/scribe.md`, copy it to
`~/.claude/agents/` if wanted). Its usage-ledger step applies only if the workspace keeps one.

## Install

**Claude Code (any OS).**
1. Put `CLAUDE.md` at `~/.claude/CLAUDE.md`. If one exists, append this file to it and read the result for
   contradictions. Instructions the employer manages still apply.
2. Copy `skills/enter` and `skills/wrap` to `~/.claude/skills/`.
3. For each project that gets a wiki: copy `generate.py`, `coverage.py`, `WIKI-PRIMER.md` and
   `entity-template.md` to `<project>/docs/wiki/` (the template stays there, NOT in `entities/`, where it
   would be linted as a page), create `docs/wiki/entities/`, paste the lines of `PROJECT-CLAUDE.md` into the
   project's `CLAUDE.md`, add the four generated files to `.gitignore`, then follow `WIKI-PRIMER.md` section 5.
   Run `generate.py` before each session starts: the `@` imports are read at launch.

**claude.ai (Projects).** Paste `CLAUDE.md` into the project's instructions and add `WIKI-PRIMER.md` as a
project file. The generator runs where the files are, on a machine with Python: generate there, then upload
`OVERVIEW.md`, `NAMES.md`, `DISCARDED.md` and the doctrine files, and re-upload after the pages change.

**Windows, Claude Code, and you may install software:** the full kit adds the hooks. See
[`../README.md`](../README.md); run `install.ps1 -WhatIf` first.

## Memory

`CLAUDE.md` section 10 asks for corrections to be written into memory. Claude Code keeps per-project memory
under `~/.claude/projects/<encoded-dir>/memory/` with a `MEMORY.md` index; that is where they go. On
claude.ai, use the project's instructions or memory.

## What is missing without the hooks

| the full kit does                                                                                                                                                                                          | without it                                                                                                                                                                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| re-injects the rules and the wiki surfaces at session start and after every compaction                                                                                                                     | compaction drops standing rules (measured: violations rose from 0% to 30%, and 59% on some models, after compaction; `../BOOTSTRAP.md` section b). Re-read `CLAUDE.md` and the wiki surfaces after a compaction; `CLAUDE.md` says so |
| blocks an edit to a file until every page that owns it, and the pages on their `depends:` and `dependents:` lines, have a complete Read of their current version this session (`WIKI-PRIMER.md` section 7) | ask for the read receipt: the pages read and the entries that govern the change, before the change                                                                                                                                   |
| asks before recursive deletes, force-pushes and hard resets                                                                                                                                                | stop case 1 in `CLAUDE.md`                                                                                                                                                                                                           |
| audits each turn's claims on Stop                                                                                                                                                                          | none                                                                                                                                                                                                                                 |

## Provenance

Built 2026-10-08 from the kit's working agreement and the 2026-10-07 consolidation of the method rules
(each principle stated once). The kit's `memory/` tier predates that consolidation and still holds the
per-principle files.
