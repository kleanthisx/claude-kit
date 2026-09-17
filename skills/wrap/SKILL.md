---
name: wrap
description: The standard way to SHUT DOWN / end a working session in a project. Use when the user says "/wrap", "wrap up", "shutdown", "let's stop here", "close out", "checkpoint and quit", "end of session", or is otherwise ending work in a project. Records what happened into the project's ledger, writes a next-session pointer, proposes a commit (never commits without a yes), and updates the usage ledger. The counterpart of /enter.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# /wrap — unified project shutdown (Full)

Close a session the same way in every project so the next `/enter` can pick up cleanly. Writes to the project's `docs/wiki/` ledger (per the hub's `WIKI-STANDARD.md`, if this workspace has one), leaves a next-session pointer, then **proposes** a commit and usage update.

**Guardrails (from `~/CLAUDE.md`):**
- **Never commit, push, or run any irreversible/outward git op without an explicit "yes".** Propose it, then wait.
- **Stamp dates from the real clock**, never from memory: `Get-Date -Format 'yyyy-MM-dd'`.
- Report as evidence: "ran `<cmd>` → `<output>`". Do not claim a write you did not make.
- Ledger writes are additive — safe without a gate. The **commit** is the only gated step.
- **In a v2 wiki, never hand-edit a generated surface** (`OVERVIEW.md`, `DECISIONS.md`,
  `DISCARDED.md`, `NAMES.md`) and never append to the frozen `docs/history/log.md`.

## Procedure

### 1. Find the project root
Same as `/enter`: nearest dir with `docs/wiki/`, `CLAUDE.md`, `AGENTS.md`, `PLAN.md`, or `.git`.

### 2. Summarize what changed this session
```bash
git status -s
git diff --stat
git log --oneline -5
```
From that + the session's actions, write a short **what-happened** list (include dead-ends — a rejected approach is worth recording). Get the date: `Get-Date -Format 'yyyy-MM-dd'`.

### 3. Which wiki is this? Branch here

```bash
ls docs/wiki/entities 2>/dev/null && echo V2 || echo V1
```

- **`docs/wiki/entities/` exists → wiki v2.** Do steps 4v2-6v2 and SKIP 4-6.
- **Otherwise → v1.** Do steps 4-6 as written.

If unsure which projects on this workspace use v1 vs v2, check the hub's project-map (if kept) —
don't assume from another project's status.

---

## v1 path

### 3a. Ensure the ledger exists (on-demand conformance)
If `docs/wiki/` is missing the standard files, create minimal ones (do not overwrite existing):
- `index.md` — front door: one line + a list of pages.
- `decisions.md` — header + `> tried/proven/discarded ledger. PROVEN ✓ · DISCARDED ✗ · STANDING ⚖ · OPEN ?`
- `log.md` — header: `# Log — newest on top`.

### 4. Append to `log.md` (newest on top)
```
## [YYYY-MM-DD] <category> | <headline>
- <what happened, incl. dead-ends>
```
`<category>` ∈ infra · knowledge · pipeline · tooling · design (or whatever category set the hub's `WIKI-STANDARD.md` defines).

### 5. Update `decisions.md` IF a durable decision was made
One line only: `**<name>** — <STATUS> — <what/why>. [<src>]`. Skip if nothing durable was decided.

### 6. Write the next-session pointer
Create/overwrite `docs/wiki/NEXT.md` with the open threads so the next `/enter` surfaces them:
```
# Start here next — <YYYY-MM-DD>
- <open thread 1 — the immediate next action>
- <open thread 2>
Uncommitted: <yes/no + rough diffstat>
```

---

## v2 path

**The premise is different, and it changes what wrap is for.** In v2 the wiki is written **in
flight** — at the moment of the work, into the entity that owns the thing — not summarised at the
end. `log.md` and `ACTION-LOG.md` are **frozen in `docs/history/`** and are never appended to again;
`decisions.md`, `OVERVIEW.md`, `DISCARDED.md` and `NAMES.md` are **generated** and must never be
hand-edited. So wrap does not write the knowledge. **It checks that the knowledge got written, and
regenerates.**

### 4v2. Verify the in-flight writing actually happened
```bash
git diff --stat HEAD~<n> -- docs/wiki/entities docs/wiki/ledgers docs/wiki/doctrine
```
Every finding, decision, dead end and measurement from this session should already be in an entity
body. **If something is only in the transcript, write it now** — into the entity that owns it, as a
named `PROVEN ✓ / DISCARDED ✗ / STANDING ⚖ / OPEN ?` entry with its evidence path. That is the one
writing step wrap still owns, and it is a backstop, not the normal path.

Do **not** append to `docs/history/log.md`. It is frozen by design: a hand-written narrative is a
lossy second copy of a record (the session transcript) that already exists exactly.

### 5v2. Regenerate and lint
```bash
python docs/wiki/generate.py
```
Report the four surface sizes, the entity count, and **any errors or warnings**. Specifically:
- **errors ≠ 0** → fix before finishing. Dangling entity references and missing mandatory fields are errors.
- **a surface OVER CAP** → say so plainly and put it in `TASKS.md`. **Do not raise the cap to silence
  it** — the caps are the only thing between this and the bloated entry set v2 replaced.
- **`verified:` past the two-week horizon** → a warning worth surfacing to the operator.

### 6v2. Update `TASKS.md` — it is the pointer now
`NEXT.md` is a redirect stub; `TASKS.md` carries the next actions. Refresh its header block with:
- date and time from the real clock
- one paragraph on what this session did
- what is uncommitted **and whose it is** (another window's work is not yours to commit)
- anything primed to run and what it is blocked on

Close any task finished this session (`- [x]` with the evidence), and add tasks for anything the
session surfaced. An entity's `open:` line carries *conditions*; `TASKS.md` carries *intended
actions*; `IDEAS.md` carries the unevaluated. Keep them distinct.

---

### 7. Transcript — do NOT render it here

The raw transcript is already on disk as JSON and **is** the record. Rendering it to readable text is
a separate, on-demand job — **call the `scribe` agent when you actually want readable text**, not at
every wrap. Rendering every session by default writes a second copy of information that already
exists exactly.

**The standing rule this preserves:** the wiki is written by the assistant, in flight, at the moment
of the work — **never by a subagent writing prose from memory**, which is a lossy second copy of a
record that already exists exactly. Steps 4 and 5 above are that in-flight writing, done by you.

If the user asks for the transcript now: `Agent(subagent_type="scribe")`, telling it which session
and where. It renders verbatim — operator turns, assistant replies, every tool call with command and
result, and every Stop-hook verdict **including the ones against you** — to
`docs/history/sessions/<YYYY-MM-DD>-<project>.md`.

### 8. Git — PROPOSE, then wait
Show `git status -s`. If there is work to save, propose a commit: if on the default branch, propose a branch first; draft a message ending with the standard co-author/session trailers. **Print the exact command and WAIT for the user's "yes".** Never `push` unless explicitly asked.

### 9. Usage / OPS update (Full)
- **If this workspace keeps a usage ledger** (see `templates/ops/OPS.template.md` for the format), append a session-close line to it noting the date + a one-line summary. If a usage footer/tally figure is visible, record it beside the note. Best-effort — never block on it.
- **If this workspace runs a ticket board** and a ticket was worked this session, update its Status/Actual cell.
- Neither exists on a single-project install → skip this step.

### 10. Final report
List what was written (files + lines), and state clearly what is **awaiting your approval** (the commit command). Then stop.
