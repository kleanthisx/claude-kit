# THE COMMISSAR — a second model reviews the agent's plans before it acts

Optional component. Installed only with `install.ps1 -WithCommissar`; nothing here runs otherwise.

## What it does

A reviewer running on a *different* model (OpenAI, through the Codex CLI's `codex app-server`) reads the
agent's plan for each piece of work and approves it, objects, or asks. A deterministic hook,
`hooks/commissar-gate.py`, then lets a state-changing tool call through only if an approved plan covers
it. The gate is code only (about 10 ms, no model call); the review is the model call.

| Piece | Where | Role |
|---|---|---|
| `service.py` | `<ClaudeHome>/commissar/` | keeps her sessions up on `127.0.0.1:8791`, one per Claude session; holds plan state (`state.json`), her copy of the method (`doctrine.md`, every earlier version in `doctrine.history/`), the log (`commissar.log.jsonl`) |
| `appserver.py` | same | the JSON-RPC client for `codex app-server` over stdio |
| `classify.py` | same | classifies a tool call (read-only / state-changing / outward / opaque, and the paths it names); `test_classify.py` is its offline test |
| `mcp_server.py` | same, registered in `~/.claude.json` as `mcpServers.commissar` | the agent's side: submit a plan, reply to an objection |
| `up.py` | same, `SessionStart` hook | starts the service if `/health` does not answer; prints nothing when she is already up |
| `talk.py` | same, run by the `/commissar` skill | the operator's direct line; reads the operator's words from the session transcript, so the agent cannot speak in their name |
| `hooks/commissar-gate.py` | `<ClaudeHome>/hooks/` | `PreToolUse` on `Edit\|Write\|NotebookEdit\|Bash\|PowerShell\|mcp__commissar__.*` |
| `config.json` | `<ClaudeHome>/commissar/` | `mode`: `log` (record only, never block) or `enforce` (block what no approved plan covers; fails closed when she is down); `effort`: her reasoning effort. Installed once, never overwritten |

Her doctrine is seeded the first time from `~/CLAUDE.md` and sections 1, 3 and 5 of `method-core.md`
(found under `~/.claude/projects/*/memory/`, newest wins). She may change her own copy; every version is
kept.

## Prerequisites (checked by the installer, not fixed by it)

- Python 3 on `PATH` as `python`.
- Node.js on `PATH` as `node`, and the Codex CLI installed globally with npm
  (`npm install -g @openai/codex`): `appserver.py` launches
  `%APPDATA%\npm\node_modules\@openai\codex\bin\codex.js app-server`.
- A Codex login (`codex login`). Her calls bill the Codex account, not the Claude one.
- Windows. The service detaches itself with Windows process-creation flags.

## Operator commands

```
/commissar <message>     talk to her (the words are read from the transcript)
/commissar state         what she holds: sessions, plans, mode
/commissar on | off      enforce | log
/commissar repair        she repairs her own machinery, with a snapshot and her tests as the safety net
python -I <ClaudeHome>/commissar/up.py        start her by hand
python -I <ClaudeHome>/commissar/test_classify.py   offline test, no model call
```

`test_acceptance.py` and `test_debate.py` replay recorded sessions against the live reviewer: they
cost model calls, run them deliberately.

## Record

Built 2026-10-10/11 on the source machine after a session in which four failures of the method went
unnoticed by the agent itself; acceptance on that transcript: all four stopped on substance. The
earlier shadow logger (`hooks/pre-action-log.py`, kept as code with its reason at the top) measured
that an asking pre-action check would have asked on 85% of actions, which is why the review is a
plan-level conversation and the per-action gate is code.
