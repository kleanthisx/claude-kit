# Ekbasis consequence-model paper - sources

Fetched 2026-10-10 for the question: should a pre-action judge gate Claude Code's state-changing calls?
Findings, with line locators into `agents.v2.tex`: [ROWS.md](ROWS.md).

| file               | what it is                | source                     | version                  | bytes   | hash                        |
| ------------------ | ------------------------- | -------------------------- | ------------------------ | ------- | --------------------------- |
| `agents.v2.tex`    | paper source, read whole  | `raw.githubusercontent.`   | commit `2b8ce2e`,        | 95,641  | sha256                      |
|                    | (1,048 lines)             | `com/OpenInterpretability` | 2026-10-10 (v2, erratum) |         | `c04b5f1d5d571b1b...`       |
|                    |                           | `/ekbasis/main/paper/`     |                          |         |                             |
|                    |                           | `agents/agents.tex`        |                          |         |                             |
| `agents.v1.pdf`    | paper as published on     | `zenodo.org/records/`      | v1, 2026-10-06           | 506,642 | md5                         |
|                    | Zenodo (NOT read: no PDF  | `23197341/files/agents.`   |                          |         | `38a1fb5a9f7a21c127f663341` |
|                    | renderer on this machine) | `pdf`                      |                          |         | `1e36ff5` (matches the      |
|                    |                           |                            |                          |         | record)                     |
| `zenodo_record.md` | the record page: title,   | `r.jina.ai/https://`       | -                        | 3,541   | -                           |
|                    | abstract, file list       | `zenodo.org/records/`      |                          |         |                             |
|                    |                           | `23197341`                 |                          |         |                             |
| `repo_tree.tsv`    | every file in the repo,   | `gh api repos/`            | HEAD on 2026-10-10       | 58,180  | -                           |
|                    | size and path (1,079      | `OpenInterpretability/`    |                          |         |                             |
|                    | files)                    | `ekbasis/git/trees/`       |                          |         |                             |
|                    |                           | `HEAD?recursive=1`         |                          |         |                             |

- Paper: C. Vicentino, *When Does a Consequence Model Make AI Agents Safer?*, DOI 10.5281/zenodo.23197341.
- Repo licence: Apache-2.0 (`gh api repos/OpenInterpretability/ekbasis`). The Zenodo record's licence was not checked.
- **This is third-party work.** The kit's GitHub copy is public and CC0. Do not ship this folder in a transfer without checking the licences.

## Their code, in `code/` (raw.githubusercontent.com, `main` on 2026-10-10; the hook's last commit `4b0f9b3`)

- `claude_code_hook.py` (29,737 B), **read whole**: a PreToolUse hook on `Bash` only. Git lines (and, opt-in,
  shell lines that change files) are checked for lost uncommitted work. Code settles read-only git, clean repos,
  and commits nothing else holds before any model call. `EKBASIS_GUARD_MODE=log` records what it would do and
  never blocks (added 2026-10-10). Needs the `ekbasis` package and a running Ekbasis server.
- `claude_plugin.py` (3,845 B), `marketplace.json` (445 B): the plugin wrapper, not read.
- What we built from it: `hooks/pre-action-log.py` + `hooks/pre-action-review.py` (shadow mode, Edit/Write and
  state-changing Bash/PowerShell, no model).

## Not read yet

- The model card: `huggingface.co/caiovicentino1/Ekbasis-27B`.
- The earlier paper, DOI 10.5281/zenodo.23146970: its title says consequence training makes the remaining errors confident.
- `paper/agents/benchmark/capability/real_terminal/`: the terminal study's harness.

## What ships in the public kit (2026-10-24)

Only our own notes: [SUMMARY.md](SUMMARY.md) (the detailed summary with the academic reference), [ROWS.md](ROWS.md)
and this file. The copied third-party files (`agents.v1.pdf`, `agents.v2.tex`, `zenodo_record.md`, `repo_tree.tsv`,
`code/`) stay in the local repository and out of every transfer; the references above are how to fetch them.
