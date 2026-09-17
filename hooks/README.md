# Claude Code Enforcement Layer — How It Works & How To Change It
*Built from a full-transcript communication analysis of this operator's own sessions. All four
original hooks live-verified, including the Stop hook blocking the assistant's own unbacked recap.*

## The one-paragraph mental model
Prose rules (CLAUDE.md) are advice the model can ignore — transcript analysis proved it ignores them. This layer moves the critical rules into mechanisms that run **outside the model's discretion**: hooks fire on every matching tool call no matter what the model "decides." CLAUDE.md still carries the Q:/GO protocol (advice), and the hooks are the enforcement floor under it.

## The six hooks (wired in `~\.claude\settings.json` → `"hooks"`)

### 1. `guard-destructive.ps1` — PreToolUse on `Bash|PowerShell`
Regex-scans every shell command. Destructive patterns (rm -rf variants any flag order, `Remove-Item/-ri/-rd/-erase/-del` with Recurse+Force, piped `| Remove-Item`, `[System.IO.Directory]::Delete`, `rmdir /s`, `del /s|/q`, `git push --force` (but **not** `--force-with-lease`), `git reset --hard`, `git clean -f`, bare `git stash` (but not pop/apply/list/show), mkfs/Format-Volume/Clear-Disk) → **interactive ask prompt** (confirmed working even under `defaultMode: dontAsk`).
- Commands touching only `AppData\Local\Temp` / `$env:TEMP` / `/tmp/` pass silently — **voided** if the command contains any chaining char (`; | & backtick` or newline).
- **To add a pattern:** append to the `$patterns` array. **To relax:** delete the pattern line.
- **Known gap (accepted):** exotic rephrasings that evade the regex run silently under `dontAsk`. Hard closure = change `permissions.defaultMode` from `"dontAsk"` to `"default"` (more prompts on everything).

### 2. `guard-plan-gate.ps1` — PreToolUse on `Edit|Write|NotebookEdit`
If **`PLAN.md` exists in the project cwd** and lacks the line `APPROVED: GO` → all edits are **denied** (editing PLAN.md itself stays allowed).
- Lifecycle: model writes PLAN.md (arms the gate) → user says GO → model adds `APPROVED: GO` line → edits flow. Deleting PLAN.md also disarms.
- No PLAN.md = no gate — concept-mode/build-and-refine is untouched.
- **To disable entirely:** remove its entry from settings hooks.

### 3. `run-posttest.ps1` — PostToolUse on `Edit|Write` (asyncRewake)
After every edit, if the project has **`.claude\posttest.ps1`**, it runs; non-zero exit **wakes the model with the failure output** (exit 2), catching A-breaks-B before more is built on top.
- **Per-project opt-in.** Inert by default in every project until you copy `posttest.template.ps1` to `<project>\.claude\posttest.ps1` and put the right test command in it (e.g. `npm test` for a JS project). Keep it FAST (seconds) — it runs on every edit.

### 4. `verify-done.ps1` — Stop hook (every turn end)
Reads the final turn from the transcript. If the last assistant message contains completion-claim language (done/complete/verified/fixed/working/finished/ready/passes/…) → sends the whole turn (incl. real tool outputs) to a **Haiku judge** (`claude -p --model claude-haiku-4-5 --settings judge-settings.json`). Judge says UNBACKED → turn end is **blocked** with the reason; the model must produce evidence. One block max per turn (`stop_hook_active` guard).
- Recap leniency: status summaries explicitly attributed to earlier-verified work count as BACKED; only NEW this-turn claims need in-turn evidence.
- Discussion leniency (added after a live false positive): text that merely discusses/quotes done-words without claiming new this-turn work counts as BACKED; a claim that the assistant itself fixed/verified something with zero tool activity in the turn stays UNBACKED (the original bluff case still blocks).
- Recursion-proofed twice: `CLAUDE_HOOK_JUDGE` env breaker + `disableAllHooks` in `judge-settings.json` for the nested call.
- **Fail-open (two paths):** claude CLI errors → warning, turn allowed. Judge replies with neither `BACKED` nor `UNBACKED` (confused/meta reply — observed live) → "malformed verdict" warning, turn allowed. Only a real `UNBACKED: …` blocks.
- **To tune strictness:** edit `$judgePrompt` or the `$claimRx` lexicon in the script. **To disable:** remove the Stop entry from settings hooks.
- Cost: one Haiku call only on claim-bearing turns (~fractions of a cent).
- **Superseded:** this hook now ships with a header noting `judge-dread.ps1` (a fuller adversarial auditor, see the shadowguard-style repo this kit's Judge Dread hooks come from) replaced it as the wired Stop hook. Kept as the record of the original design — do not wire both back in alongside each other, or you pay two model calls per turn auditing the same Stop event.

### 5. `guard-launch-gate.ps1` — PreToolUse on `Workflow`
Multi-agent fleet launches are gated on a **machine-computed audit**, never the model's description of the script. Added after a launch-by-name burned a very large token count on an inherited model tier while a stated cap/cheap-agents plan existed only as prose in the brief.
- `name`-only launch → **deny always** (stock scripts inherit the session model, carry no budget gates, and can't be audited before they run).
- Inline `script` → **deny always** (no stable on-disk artifact to hash and approve).
- `scriptPath` → the hook itself greps the file: `agent()` call sites, per-stage `model:` declarations, `budget.spent()/remaining()` gates, SHA256. Allowed ONLY if `<cwd>\LAUNCH.md` contains `APPROVED: GO` **and** `SCRIPT-SHA256: <hash of that exact file>`. The deny message prints the audit + hash for the user to approve against. Template: `templates/ops/LAUNCH.template.md`.
- Approval is **per-script-version**: any edit changes the hash and re-arms the gate. Resume of an unchanged approved script stays approved. Deleting LAUNCH.md re-arms.
- Fires only on Workflow calls (rare) — zero friction on all routine work, so the prompt keeps its signal.
- **Known gap, closed by hook 6:** single `Agent` calls used to be ungated. The gap fired exactly as written once: a dozen individual `Agent` calls walked past this gate because none of them was a `Workflow`.
- **To disable:** remove the Workflow entry from settings hooks.

### 6. `guard-agent-fleet.ps1` — PreToolUse on `Agent`
Bounds the **user-facing blast radius** of subagent spawning. Added after a dozen parallel `Agent` calls — each instructed to read several web sources — produced roughly a hundred allow/deny prompts on the user's screen, several killed by hand, and returned nothing useful. Bounds had been set on word count, source count and model tier; never on interruptions.
- **Gates accumulation, not individual subagents** — precisely to avoid the alarm-fatigue anti-pattern hook 5 warns about. Spawns 1–3 inside a rolling **15-minute window** pass silently; the **4th+ asks**.
- Counter is **per-session**, an append-only timestamp log at `~\.claude\hooks\.agent-fleet\<session_id>.log`, so multiple spawns issued in a single message still count individually (read-modify-write would race). Session logs older than 1 day are pruned on entry.
- **Blast-radius estimate is machine-read from the agent's own prompt**, never from the model's description of it: `"at most 8-10 sources"` → `~N×10 allow/deny prompts` printed in the ask reason.
- The ask text also requires stating the **coverage mechanism** (externally-sourced denominator, or planned saturation) — N agents on N disjoint lanes yield N samples of an unknown with no way to detect coverage.
- **Escape hatch (same idiom as LAUNCH.md):** a line `APPROVED: GO` in `<cwd>\FLEET.md` pre-approves a batch and the gate goes silent. Removing the line or the file re-arms it. (This is a per-batch approval record, not a template — there is no generic content to fill in beyond "state what you're approving and why.")
- **To tune:** `$THRESHOLD` / `$WINDOW_MIN` at the top of the script. **To disable:** remove the Agent entry from settings hooks.
- **Known gap (accepted):** the counter is per-session, so a spawn burst split across two sessions is not aggregated.

## Measured coverage gaps in `guard-destructive.ps1` — FOUND, NOT FIXED

Two holes, found after the guard stayed silent through four real deletions in a live project session and
the user asked why. Verdicts below are from piping hook JSON into the script itself, not from reading the regex.

**1. A forced delete of NAMED FILES is not covered — only recursive deletion is.**
Every deletion pattern requires a recursive flag (`-rf`/`-fr`, `-r`, `-rec*`, `-Recurse`, `/s`). These two
real commands (paths generalised; the shape is what matters) returned no output at all (= allow):

    rm -f state/run-prod-*.json state/run-prod-*.db
    rm -f results/run_engine_only.json results/run_A.log

while `rm -rf build/`, `Remove-Item -Recurse -Force C:\x` and `git reset --hard` all correctly returned
`permissionDecision: ask`. The section header says "file-tree deletion", so this is by design — but deleting
several named files is exactly as irreversible as deleting a directory, and that is how the artifacts of a
completed experiment run were destroyed unprompted.

*Would close it:* one pattern for a delete verb carrying `-f` / `-Force` without a recurse flag. The existing
Temp/scratchpad allowance already keeps routine scratch churn quiet.

**2. The structural one: deletion inside a SCRIPT FILE is invisible to the guard.**
The hook only ever sees `tool_input.command`. Compare:

    python run_something.py --port 8012 --conv x    ->  silence (allow)
    os.remove(p)                                     ->  ask

Identical deletion, opposite verdicts, decided purely by whether the call was typed inline. The pattern list
already contains `os.remove`, `shutil.rmtree`, `.unlink(` — so covering them was the intent — but those
patterns only ever fire for the one case that almost never happens when every pipeline stage is its own
script (a stated house convention in the source project). The guard is blind to the normal way work gets
done there. The contaminated run that triggered this investigation called `os.remove()` on state and
memory files on every invocation; no hook could have seen it.

*Would close it:* when the command is `python <file>` / `powershell -File <file>`, read that file and run the
same pattern set over its contents. That is the only way an inline-string matcher can see into a script.

Neither is fixed. Do not assume this guard covers deletion in general — it covers recursive deletion typed at
the prompt. `test-delete-coverage.py` (the matrix, beside the suite) was RUN: **ALL GREEN, 42 cases, exit 0**. It does
NOT omit these two shapes — it asserts them as allowed: the cases `plain-rm-file` and `py-script` both
carry `expected=PASS`. So neither finding above is an oversight; both are encoded current design, and
"fixing" them means flipping two green assertions. That is a call for the user, not a patch to slip in.


## Permission rules (settings.json → `"permissions"`)
- **ask** (10 rules): command-initial destructive prefixes (`Remove-Item`, `rm -rf/-r/-fr`, `rmdir`, `git push --force/-f`, `git reset --hard`, `git stash`, `git clean`) prompt even in dontAsk. Note: `Remove-Item` was MOVED here from the allow list — do not re-add it to allow.
- **deny** (7 rules): literal catastrophic forms (`rm -rf /`, `rm -rf ~`, `rm -rf C:*`, `Remove-Item -Recurse -Force C:\`). Tripwire only — prefix-match, not a wall. Deny is NOT interactively approvable; keep this list to never-even-with-approval cases.
- Rule syntax is prefix matching: `"Bash(cmd:*)"`. Embedded/mid-pipeline commands are the hook's job, not rules.

## CLAUDE.md pieces (`$env:USERPROFILE\CLAUDE.md`)
- **Interaction Protocol** section: Q:/GO markers, plan-first, checklists, done-banned/evidence-only, destructive propose-and-wait, corrections-stick-or-restart, model tiering. Advisory layer; hooks enforce the load-bearing parts.
- **Anti-deviation gate ceiling:** max 2 review rounds after the first; still failing → surface findings and ask, never loop on.

## Testing after any change
- `powershell -File ~\.claude\hooks\test-hooks.ps1` — pipe-tests for the four guards (incl. launch-gate cases, and fleet-gate cases: threshold 1-3 silent / 4th-5th ask, prompt-read blast estimate, FLEET.md armed+disarmed, fresh-session reset) + posttest + the delete-coverage matrix + Stop-hook cases (synthetic fixtures, no side effects outside temp). The Stop-hook cases: no-claim prefilter skip, bluff-with-no-tools → block, evidence-backed → pass, chat-only mention of done-words → pass, PATH-stubbed malformed judge → fail-open warning. Some of them use one real Haiku call each.
- Live: create a dummy dir and `Remove-Item -Recurse -Force` it — expect the prompt. Create an unapproved `PLAN.md` and try an edit — expect a deny.

## Kill switches
- Everything at once: `"disableAllHooks": true` in settings.json (or `/hooks` menu).
- Any single hook: delete its entry from settings hooks and save (hot-reloads).
- The `/hooks` UI in Claude Code shows and edits all of this interactively.


## guard-entity-read.ps1 — the wiki entity gate

`PreToolUse` on `Edit|Write|NotebookEdit`, alongside `guard-plan-gate.ps1`.

**Denies an edit to a file whose owning wiki entity has not been read this session.** Ownership comes
from the `owns:` line of each `docs/wiki/entities/*.md` header — no separate registry to drift. Proof
of reading comes from the session transcript (`transcript_path`): a `"file_path"` mentioning the
entity file anywhere in it counts.

**Deliberately permissive at the edges.** It denies only when the project has `docs/wiki/entities/`,
**and** the target is claimed by an `owns:` line, **and** the entity is absent from the transcript.
Files under `docs/wiki/` and `docs/history/` are never gated — you must always be able to fix the
map. A false deny costs real work; a false allow costs one unread page.

**Why it exists:** benchmarks that test *obedience* rather than recall have found the governing
document goes unopened in the large majority of violations, even when it is one grep away. Caps and
good intentions do not fix that; removing the decision from the model's discretion does.

- Disarm for a session: `$env:WIKI_GATE = 'off'`
- Tests: `powershell -NoProfile -ExecutionPolicy Bypass -File test-entity-read.ps1` — 9 cases
  (owned/unowned, read/unread, wiki, history, no-entities project, disarm).
- Design: see this workspace's own wiki-v2 design notes, if kept, for the fuller rationale and the
  measured obedience-benchmark figures.


## load-wiki.ps1 — the always-loaded layer

`SessionStart` **and** `PostCompact`, after `session-rules.ps1`.

Injects a project's generated wiki surfaces — `OVERVIEW.md` (what exists), `DISCARDED.md` (what is
already a dead end), `NAMES.md` (aliases to canonical; AMBIGUOUS means ask), `DECISIONS.md` (one line
per decision) and everything in `doctrine/` — as `additionalContext`, with a header saying how to use
them in order. **Regenerates first** (`python docs/wiki/generate.py`), so what is injected is never
stale relative to the entity files, and reports the lint count inline.

**`PostCompact` is the load-bearing half.** Compaction has been measured to take rule violation from
near-zero to 30-59%, and re-injection after compaction is the documented fix. Hook output also
arrives as a clean system-reminder without the "ignore if irrelevant" framing that licenses
skipping an injected file.

Fires only in a project that has `docs/wiki/entities/`; silent everywhere else. Emits pure ASCII
(unicode-escaped) for the same reason `session-rules.ps1` does.

- Disarm: `$env:WIKI_LOAD = 'off'`
- Cost, one v2 project, measured: **74 KB / ~19k tokens** per injection. It pairs with
  `guard-entity-read.ps1`: this one makes the index present, that one makes the detail non-optional.
