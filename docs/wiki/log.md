# Log — claude-kit

Short, append-only, newest entry on top. One line-or-two per action. Full reasoning for any of
these is in [ACTION-LOG.md](ACTION-LOG.md).

## [2026-10-24] release-prep | Kit brought level with the live setup for a hand-off to a friend
- Operator: "i will give the claude kit to friends. is it up to date? is the commisar in?" then "i want my friend
  to have my setup at the end." Found: GitHub at the 2026-10-08 transfer; local main 2 commits ahead plus 848
  uncommitted lines; memory tier frozen at 2026-09-17 (25 method files missing, `method-core.md` among them);
  5 live hooks and 2 skills not in the kit; commissar committed but not wired; conclave untracked.
- Committed the pending work (4c25546: numbered context parts, installer migration, generated index).
- Memory: 1 Sonnet agent (207k tokens, 63 calls) added 25 method files and refreshed 12 against the live
  folder; 2 core files moved to generalised; denylist grep over memory/ returns nothing. Tier is now 19 core +
  67 generalised = 86 files (242 KB). Portability blockquote normalised to end-of-file (33 moved).
- Hooks: `guard-destructive.ps1` (git checkout/restore/switch discard forms, `-C` prefix), `keep-going.ps1`,
  `usage-gate.ps1` from live; wired in `settings/hooks.json`. Skills `fleet`, `unattended` added.
  `tests/test-hooks.ps1` synced (50 cases). `test-context-delivery.ps1`: wiki parts 16 -> 40, DECISIONS.md
  asserted on demand (was asserting delivery; stale since 2026-10-07).
- Commissar: live code synced (gate fixes of 2026-10-11 21:37); every absolute path derived from the install
  location; `install.ps1 -WithCommissar` copies her code, the gate, the skill (CLAUDE_HOME substituted), merges
  `settings/commissar.json`, registers `mcpServers.commissar` in `~/.claude.json` (new `-ClaudeJsonPath`),
  reports python/node/codex/login; uninstall removes code + registration, keeps her state. 17 new installer
  assertions. `commissar/README.md` written.
- Suites at close: install-profile 41, context-delivery 80, entity-read 40/0, hooks ALL GREEN, classify 28/28.
- Fresh Opus review of the first candidate: NOT CLEAR, 2 blockers. (1) 86 memory files = 240k chars overflowed the 24
  wired parts (216k): a fresh install would have delivered only a failure notice. Fixed: 32 parts; the delivery test now
  pushes the REAL tier through the hook (241,553 of 288,000 chars). (2) Explicit image-bench wording in 6 generalised
  files under the public handle: scrubbed to anatomy/body wording; `scrape-gently-*`, `md-files-table-script-then-notepadpp`,
  `claude-launch-workflow` dropped from the kit (one project's capture practice; operator preferences, one of them
  `--dangerously-skip-permissions`); `originSessionId` stripped from 69 files; machine profile removed from spec-decoding.
  Should-fix: settings.json read as UTF-8 and written BOM-less; hooks without `command` no longer crash the merge;
  unparseable `~/.claude.json` skips MCP registration instead of dying; uninstall removes kit skills + fixtures; RULES.md
  backed up; warning on a ClaudeHome with a space; permissions allow list minus research domains and venv entries;
  doc counts corrected; commissar gate/service derive paths from their install location, case-insensitive match.
- Conclave ships (operator: "conclave stays in"): `-WithConclave -Council <name> [-ConclaveProjectRoot]`, hooks in
  observe mode, Claude-side MCP registered, Codex line printed; 11 installer assertions; README machine-neutral.
- Earlier line, superseded the same day: `conclave/` (Codex-written, bound to one project's council, absolute paths; operator decision
  pending) and `docs/research/ekbasis-2026-10-10/` (third-party, "not for a transfer until the licences are
  checked", commit f43c336). Push is outward-facing: stopped before it.

## [2026-10-11] hooks | THE COMMISSAR: a second model reviews the agent's plans; the shadow logger deactivated
- `commissar/`: reviewer on OpenAI through `codex app-server`; `service.py` on 127.0.0.1:8791, one session per
  Claude session; `mcp_server.py` the agent's side; `hooks/commissar-gate.py` lets a state-changing action through
  only if her approved plan covers it (code only, ~10 ms; fails closed in enforce mode). She keeps her own copy of
  the method (`doctrine.md`, every version kept) and repairs her own machinery on `/commissar repair` with a snapshot
  and her tests as the safety net. `skills/commissar/`: the operator's direct line; the words are read from the
  transcript. Acceptance on the 2026-10-10/11 transcript: the four failures of that session stopped on substance.
- `hooks/pre-action-log.py` deactivated (would have asked on 85% of calls: crude classifier + file-name intent
  test); kept as code with the reason at its top. (Written 2026-10-24 from the commit record.)

## [2026-10-10] research | Ekbasis paper read whole; pre-action check in shadow mode
- `docs/research/ekbasis-2026-10-10/`: Vicentino, *When Does a Consequence Model Make AI Agents Safer?* (Zenodo
  10.5281/zenodo.23197341), v2 source read whole, their Claude Code hook read whole; `ROWS.md` (findings with line
  locators), `SOURCES.md` (provenance). Question: should a pre-action judge gate state-changing calls? Their own
  numbers: asking-always matched the model-backed guard on harm; for Sonnet in a terminal the hook was only cost;
  settling in code cut their questions 10.6 -> 2.9 per 100 commands.
- `hooks/pre-action-log.py` + `pre-action-review.py`: shadow mode on Edit/Write and state-changing Bash/PowerShell,
  records what an asking check would do, never blocks. (Written 2026-10-24 from the commit record.)

## [2026-09-17] tooling | Kit generalised for a work (ops) site; GitHub became a CC0 public transfer layer
- All governing files brought to latest; project specifics shipped as generalised docs and templates
  (skills, workspace doctrine, OPS board, launch notes), wiki-v1 standard + wiki-v2 design/synthesis/process
  as principles only. Operator cut the wiki scope mid-run: "i dont need the actual wiki but the design
  and implementation principles" — no skeletons or example wikis ship.
- 4 Sonnet agents (A memory 355.7k, B wiki 174.6k, C skills/ops 229.6k, D installer/BOOTSTRAP 230.4k).
  No caps were set on A-C; D exceeded its 90-call cap (96). Operator: "they all read the same things".
- 13 generic lessons mined from project notes -> memory/core-generalised/gem-*.md.
- Main-loop full-repo scan caught what per-agent scans could not: tracked core-sensitive tier, an
  exclude list naming 15 project files, a roleplay test fixture, home paths in tests. All fixed;
  core-sensitive and the home exclude list are now git-ignored.
- BOOTSTRAP.md: stale "gaps not fixed" claim and a mis-cited figure corrected against the code.
  Operator style rule for it: state the rules, do not defend them.
- Dead end: rewrote local main to one commit to "repush"; operator stopped it — local keeps history,
  GitHub is a transfer layer. Implemented as orphan `transfer` branch -> origin/main.
- Operator deleted the GitHub repo; recreated, pushed transfer (866e660), made PUBLIC, licensed CC0-1.0
  (66ba5c0). Tests at close: test-hooks 86/0/1, entity-read 9/0, delete-coverage 42 green.

## [2026-09-16] process | Precedence header rewritten to cover operator directives wholesale
User: internal-prompt defaults are overridden by the user's rules wholesale, not just for method
and tool choice as the assistant had scoped it; uncovered cases get asked about, not silently
defaulted. Landed in commit `109b8fa`. See decisions.md: operator-directives-override-harness-defaults.

## [2026-09-16] process | Orphaned-scribe self-correction
Assistant cited a system-prompt/scribe conflict as the reason no scribe was running; user pointed
out the scribe request was already standing (2026-09-12) and never expired. Both exemption clauses
were satisfied all along — no real conflict existed. See decisions.md:
a-standing-request-does-not-expire-per-session.

## [2026-09-16] measurement | Judge Dread verdict delivery measured: 47 deliveries for 9 verdicts
9 distinct verdicts, 47 deliveries total (Stop-block + UserPromptSubmit + system record per
re-fire), 8/9 re-fired 3+ times, 5/9 verdicts correct. One-turn lag means evidence produced in
response to a verdict can't reach that verdict. Left OPEN, no fix applied (see decisions.md).

## [2026-09-16] github | Personal memory files removed from claude-kit repo history
20 project-state files present in the first commit; removed via amend + force-with-lease
(single-commit repo). Verified 404 on the path, blob count 119 -> 99. GC-pending caveat recorded.

## [2026-09-16] test | Two installer bugs found by running the installer against a foreign config
(a) backup was written eagerly, so a no-op re-run snapshotted the already-merged state; (b)
uninstall restored the newest backup instead of the oldest. Fixed both: lazy backup, uninstall
restores oldest. Re-verified against the same scratch ClaudeHome: foreign Stop hook preserved
alongside Dread, model/defaultMode untouched, idempotent 2nd run, clean uninstall revert.

## [2026-09-16] decision | Memory split generalised instead of withholding 13 rules
User corrected the plan: reword evidence to drop project names rather than exclude the rules from
the work profile. Result: all 45 rules ship, 0 identifiers. Fixed 5 grammar breaks + 1 corrupted
wikilink caused by generalising before de-linking.

## [2026-09-16] cleanup | verify-done.ps1 confirmed dead code, gated out of the live suite
Stop hook is judge-dread.ps1; verify-done.ps1 referenced nowhere in settings.json. Its 5 test
cases cost 3 live `claude -p` calls per run for a hook that never fires; gated behind
`-IncludeSuperseded`. Suite now 80 PASS / 0 FAIL / 1 SKIP in 44s.

## [2026-09-16] repo | Three private repos in play: claude-hooks, shadowguard, claude-kit
claude-hooks (guards) and claude-kit (this project's full setup) created today; shadowguard
(Judge Dread) pre-existing.

## [2026-09-16] fix | Root cause of the session-start recitation failure found and fixed
`session-rules.ps1` injected only the RULES.md summary at SessionStart/PostCompact. Rewritten to
inject all 45 method files in full: 106,014 chars, ~26.5k tokens, ASCII-clean JSON, 0 leaked
project-state files. Control file: `memory/inject-exclude.txt`.

## [2026-09-16] dead-end | Session-start recitation done from index + summary, not from files
User caught it: "recite IS USED AS MEANS OF PROVING YOU READ THE FILE, NOT CAT FILE." All 66
memory files (194,429 bytes) then read in full and the recitation redone. This is the reason the
injector fix above exists.

## [2026-09-16] retraction | "4 of 9 verdicts wrong" figure withdrawn, not re-derived
The correct/incorrect split of Judge Dread's 9 verdicts was never tool-measured — it was the
assistant's own unqueried opinion. J5 (unit 14) showed the "wrong" ones were largely input
starvation. Figure withdrawn; decisions.md judge-dread entry updated in place with the old text
struck through, not deleted.

## [2026-09-16] fix | Judge Dread's evidence truncation made two-ended (J5 diagnostic first)
Two caps in judge-dread.ps1 both kept the wrong end: whole-turn cap kept the tail (1/47 turns
over, lost 9/24 tool calls), per-tool-result cap kept the head (43/162 over, 8 hid a decisive
token, 2 were the exact pushes a verdict said had no evidence). Fixed all 4 sites to two-ended
with elided-count markers; hidden tokens 8 -> 3 in simulation. $snip label deliberately left
head-only, flagged to operator. shadowguard a878791/5d40b73, claude-kit 5b51e58/1dab75e.

## [2026-09-16] fix | Gap B closed: deletion inside a launched script no longer invisible
Guard only saw tool_input.command, so python run_x.py hid an inline os.remove() that a literal
command would have caught. Now resolves and scans the launched script's contents; approval keyed
on file SHA256 so edits re-prompt. One file does PreToolUse (decide) + PostToolUse (record)
because PreToolUse never learns of approval. 6 new gapb- cases green, suite 86/0/1.
claude-kit e5cce04, claude-hooks 303e374.

## [2026-09-16] fix | Gap A closed: named-file deletion now asks
Live incident (build_catalog.py deleted, untracked, no prompt) showed rm/del/Remove-Item on a
named file all ALLOWed regardless of -f. Measured noise cost first: 2 non-recursive deletes in
12 transcripts. Anchored patterns added (anywhere-match first attempt false-positived on grep -rn
rm file.txt). 19/19 matrix, 42/42 green, suite 80/0/1. claude-hooks 4d203fb, claude-kit afbd05d.

## [2026-09-16] correction | Precedence header reworded again: defaults discarded, not subordinate
User: defaults aren't a lower tier that still votes on silence, they're orphaned entirely; silence
means ask, not fall back to a default. Header reworded; fabrication/safety exclusions kept but
reframed. Commit 31cbd42. Dead end: first commit attempt broke because a PowerShell here-string
terminator wasn't at column 0, git read the message as pathspecs; fixed with a message file.

## [2026-10-06] fix | SessionStart memory delivery failed: 21 parts needed, 20 wired
Hook reported "CONTEXT DELIVERY FAILED (MEMORY): 21 parts required; only 20 configured" (memory
corpus 100 files / 182,255 chars > 20 x 9,000). Raised memory parts 20 -> 24 in settings/hooks.json,
session-rules.ps1 (ValidateRange + PartCount) and tests/test-context-delivery.ps1; same edit mirrored
to the live ~/.claude copies (settings.json backed up as settings.json.bak-2026-10-06-parts). Verified by
running all 24 live parts: 21/21 delivered, parts 22-24 empty by design. Pre-existing, untouched:
test "settings wires all wiki parts" expects 16, settings/hooks.json wires 20 (another session's
uncommitted load-wiki work). Not committed.
