# Conclave

Conclave is a local, shared-state MCP service for a two-model engineering council:

- **Operator:** owns intent, priorities, budget and final overrides.
- **Claude:** execution lead; decomposes approved work, spawns agents and delivers it.
- **Codex:** architecture governor; reviews intent and plans, audits evidence and may veto drift or corner-cutting.

It exchanges decisions and observable evidence. It neither requests nor stores hidden model reasoning.

## What makes it two-way

Codex and Claude each launch the same stdio MCP server with a different identity. Both processes use one SQLite
database. Messages, immutable plan revisions, signatures, execution events, vetoes and audits therefore appear to
both clients. The actor is fixed on the process command line; a tool call cannot claim to be the other model.

Communication is push plus pull:

1. `conclave_push` writes one durable delivery for every council participant except the pusher.
2. A detached transport immediately wakes each recipient. The wake-up contains delivery ids, never message content.
3. The recipient calls `conclave_pull` to retrieve authoritative content and atomically acknowledge only those rows.
4. A failed wake-up remains `push_failed` and retryable; it is never reported as pulled.

On this machine the Codex adapter uses the native session queue. The Claude adapter launches a constrained one-turn
worker that is instructed to pull and deliberate through Conclave only. That worker is a real model turn and can
consume model quota. `conclave_read_messages` remains available as a cursor-based compatibility/read tool, but it is
not the wake-up mechanism.

Claude wake-ups are single-flight per council/recipient: a filesystem lease prevents concurrent workers, the active
dispatcher drains deliveries that arrive while it is running, and ordinary Claude hook events never retry an old
delivery. Messages emitted by a headless worker carry `metadata.worker=true` and a correlation id in
`metadata.session`, so they cannot be mistaken for the interactive Claude session.

## State machine

```text
NEW -> INTENT REVIEW -> DELIBERATION -> CONSENSUS LOCKED
                                      -> EXECUTING -> AUDIT -> ACCEPTED
                                             |          |
                                             +-> PAUSED <-+
                                                   |
                                            correction/revision
```

Execution requires `approve` from both actors on the same immutable plan hash. Any changed plan is a new revision
with no inherited signatures. A new operator message pauses active work until Codex classifies its intent impact.
Codex vetoes pause execution until Claude answers with evidence and Codex releases them. Claude requests completion;
Codex alone records final acceptance.

## Files

- `core.py` — SQLite schema, permissions and state machine.
- `mcp_server.py` — dependency-free JSON-RPC/MCP stdio transport.
- `push.py` — durable-inbox wake-up dispatch for Codex and Claude.
- `claude_hook.py` — optional Claude Code intent recorder and deterministic execution gate.
- `test_conclave.py` — workflow, identity, MCP transport and hook regression tests.
- `README.md` — this file. (The source repository also keeps the operator's own handoff and backlog notes;
  they are project state and are not installed.)

Runtime state belongs outside the code. Default database (both clients must point at the same file):

```text
~\.conclave\conclave.db        (Path.home() / ".conclave" / "conclave.db"; override with --db)
```

## Install with the kit

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Profile work -MemoryDir <dir> `
    -WithConclave -Council <council-name> [-ConclaveProjectRoot <path> ...]
```

This copies the code to `<ClaudeHome>\conclave\`, registers `mcpServers.conclave` for Claude Code in
`~\.claude.json` (actor `claude`, your council name, default database), and wires the two optional hooks below in
`--mode observe` into `settings.json`. `-ConclaveProjectRoot` (repeatable) limits the hooks to sessions under those
paths. The installer prints the matching Codex registration line; run it yourself, Codex's config is not touched.
`-Uninstall` removes the code and the Claude registration and leaves the database.

## Verify

No packages are required beyond Python 3.11+.

```powershell
Set-Location <ClaudeHome>\conclave
python -m py_compile core.py mcp_server.py claude_hook.py push.py
python -m unittest -v test_conclave.py
```

## Register Codex

Invoking the `.cmd` shim avoids PowerShell's script-policy block on the npm-installed CLI:

```powershell
cmd /c codex.cmd mcp add conclave -- python -I <ClaudeHome>\conclave\mcp_server.py --actor codex --council <council-name>
```

Add `--db <path>` to both registrations if you do not use the default database.

Start a new Codex session after registration; an already-running session does not hot-load a newly configured MCP
server.

## Register Claude Code

Done by `install.ps1 -WithConclave`. By hand:

```powershell
claude mcp add --scope user conclave -- python -I <ClaudeHome>\conclave\mcp_server.py --actor claude --council <council-name>
```

Restart Claude Code and call `conclave_health`.

## Optional Claude Code hook

The MCP protocol governs calls made through it. It cannot stop Claude from using an unrelated tool outside the
protocol. The optional hook makes the veto and plan state enforceable for Claude Code's state-changing tools and
captures each operator prompt verbatim.

Merge entries into the existing `~/.claude/settings.json`; never replace the file or its existing hooks. First wire
both entries with `--mode observe`. After both clients pass `conclave_health`, change only the `PreToolUse` entry to
`--mode enforce`.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -I <ClaudeHome>/conclave/claude_hook.py --council <council-name> --mode observe --project-root <path>",
            "timeout": 10,
            "statusMessage": "Recording intent in Conclave"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Agent|Task|Workflow|Edit|Write|NotebookEdit|Bash|PowerShell",
        "hooks": [
          {
            "type": "command",
            "command": "python -I <ClaudeHome>/conclave/claude_hook.py --council <council-name> --mode enforce --project-root <path>",
            "timeout": 10,
            "statusMessage": "Conclave gate"
          }
        ]
      }
    ]
  }
}
```

`--project-root` is repeatable. Events outside the configured roots are ignored, which keeps unrelated projects'
sessions out of this council. The gate checks:

- no unreviewed operator message;
- no active Codex veto;
- an execution exists and is `running` or `rework`;
- edits stay under the plan's `allowed_paths`;
- shell commands begin with an `allowed_commands` prefix.

Conclave complements the kit's destructive-command and file-read guards. It does not replace them.

## Deliberation protocol

1. Record the operator's words verbatim. Codex classifies whether they clarify or change scope.
2. Discuss with `conclave_push`; react to wake-ups with `conclave_pull`.
3. Claude normally submits the structured plan as execution lead.
4. Both actors review the exact revision. Two approvals lock consensus.
5. Claude starts execution and reports delegation, progress, decisions, risks, tests and completion.
6. Codex audits at useful milestones. A veto must name the clause, evidence and required correction.
7. Claude answers a veto with evidence; only Codex can release it.
8. Claude requests completion; only Codex can accept it. The operator can override either model explicitly.

## Trust boundary and limits

- This is a local single-user design. Filesystem access to the SQLite file is the security boundary; there is no
  network listener or remote authentication.
- Communication outside the connected clients is not visible. The Claude hook captures only sessions in which it is
  installed.
- Wake-up depends on a registered local client endpoint. Durable inbox state survives a missing or failed endpoint,
  and `conclave_get_state` exposes unpulled deliveries for diagnosis.
- A successful push means the client accepted the wake-up. Only `pulled_at` proves that the participant retrieved it.
- Shell-prefix scope checks are deliberately conservative and not a shell parser. Keep the existing destructive
  command guard enabled.
- The append-only `ledger` table records every governance transition. Current-state rows are mutable projections;
  the ledger and immutable plan revisions retain the history.

