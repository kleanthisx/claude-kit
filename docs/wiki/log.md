# Log — claude-kit

Short, append-only, newest entry on top. One line-or-two per action. Full reasoning for any of
these is in [ACTION-LOG.md](ACTION-LOG.md).

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
