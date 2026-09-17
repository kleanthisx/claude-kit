# Decisions — claude-kit

One line per durable decision. STATUS is one of PROVEN ✓ (measured/tested and holding),
DISCARDED ✗ (tried, rejected — reasoning kept), STANDING ⚖ (a rule/policy in force, not a
one-off measurement), OPEN ? (decided provisionally, not yet closed out). Edited in place only
when status genuinely changes; old reasoning stays visible. Full reasoning for each is in
[ACTION-LOG.md](ACTION-LOG.md); this file is the index, not the argument.

- **inject-the-files-not-a-summary** — PROVEN ✓ — `session-rules.ps1` (SessionStart + PostCompact
  hook) now injects every method-memory file in full, not the RULES.md summary. Measured
  2026-09-16: 45 files, 106,014 chars, ~26.5k tokens per injection, pure-ASCII JSON,
  `suppressOutput` set, 0 project-state files leaked into the injection. Root cause it fixes: a
  summary in context plus the auto-loaded index gives a session the APPEARANCE of having the
  directives with none of the evidence, so a recitation from that state is indistinguishable from
  a real one — this is what happened at the start of this very session. [ACTION-LOG.md #2]

- **generalise-evidence-rather-than-withhold-rules** — PROVEN ✓ — the work-profile memory tier
  ships all 45 method rules with 0 project identifiers in the evidence text, instead of the
  original plan (withhold 13 rules whose evidence named private projects). User's correction:
  generalise the wording ("in a project this happened") rather than drop the rule. Strictly
  better outcome — full rule coverage, zero leakage. Cost: regex generalisation broke grammar in
  5 places and corrupted one wikilink target because de-linking ran after substitution; fixed by
  reordering the passes plus a fixups pass. Final gate: 0 sensitive tokens, 0 grammar breaks, 0
  corrupted links. [ACTION-LOG.md #5]

- **operator-directives-override-harness-defaults** — STANDING ⚖ — set 2026-09-16. The injected
  header states the user's directives override the harness's internal defaults wholesale (not
  scoped to "method and tool-choice" as the assistant had narrowed it), naming the covered areas:
  when to act vs wait, when to ask, tool choice, agents, publishing, scope, correction style,
  verbosity. For anything the user's rules are silent on: do not silently fall back to a harness
  default, say what the default would do, say the user's rules are silent on it, and ask. Two
  exclusions kept: fabricating, and genuine safety limits. Landed in commit `109b8fa`.
  [ACTION-LOG.md #10]

- **a-standing-request-does-not-expire-per-session** — STANDING ⚖ — a standing request (e.g. "have
  a simple agent always up... recording findings, thought process... so we have the knowledge",
  user, 2026-09-12, recorded verbatim in memory file `scribe-agent-records-everything`) stays in
  force until the user revokes it. It does not need to be repeated in a new session to remain
  valid, and an unrepeated standing request is not evidence of a structural conflict with other
  instructions. [ACTION-LOG.md #9]

- **verify-done-superseded-not-deleted** — PROVEN ✓ — `verify-done.ps1` is dead code: `settings.json`
  wires the Stop hook to `judge-dread.ps1`, and `verify-done.ps1` is referenced nowhere else.
  Kept the file (marked with a SUPERSEDED header) rather than deleting it, per the registry
  convention of marking a row rather than removing it. Its five `vd-` test cases were burning
  three live `claude -p` calls per suite run testing a hook that never fires; gated behind
  `-IncludeSuperseded` in `test-hooks.ps1`. Suite result after the change: 80 PASS / 0 FAIL /
  1 SKIP in 44s. [ACTION-LOG.md #4]

- **judge-dread-one-turn-lag-re-fires-stale-verdicts** — OPEN ? — measured 2026-09-16: 9 distinct
  verdicts produced 47 deliveries (each re-fires as Stop-block + UserPromptSubmit + system
  record), 8 of the 9 re-fired more than three times. ~~5 of 9 verdicts were correct catches; 4
  were wrong about what the graded turn actually contained.~~ Mechanism: Dread judges turn N,
  delivers after N+1, re-delivers at N+2, and the verdict string never re-evaluates, so evidence
  produced in answer to a verdict can never reach it. A delivery-side fix was proposed by the
  assistant and then WITHDRAWN by the assistant as improper self-editing of its own constraint —
  no fix applied. User's decision on the cost, recorded verbatim: "i'll trade 50% of the cost on
  checking you ... 50% cost for 50% actual work beats days on end chasing ommisions." Left open —
  no patch, cost accepted as-is. [ACTION-LOG.md #8]
  **UPDATE, same session (2026-09-16), after unit 14:** the "5 correct / 4 wrong" split struck
  through above is RETRACTED, not re-derived — it was the assistant's own unmeasured opinion, not
  a tool-based finding (the 9-verdicts/47-deliveries counts themselves are real transcript counts
  and still stand). Unit 14 (J5 diagnostic) found the verdicts scored "wrong" were largely
  explained by evidence truncation hiding decisive tokens before Dread ever saw them, not by
  faulty judgement — see `judge-errors-were-input-starvation-not-judgement` below, which is now
  PROVEN and fixed. So this decision splits in two: the ACCURACY half is addressed (truncation
  fixed, see below); the LAG/re-delivery half described in the Mechanism sentence above is
  UNCHANGED and remains fully open — 9 verdicts still become 47 deliveries, no delivery-side fix
  has been applied, and it is explicitly the operator's call to open per the withdrawal above, not
  the assistant's. [ACTION-LOG.md #14]

- **personal-memory-off-github-practically-not-absolutely** — OPEN ? — 20 project-state files that
  were present in the first `claude-kit` commit were removed via amend + force-with-lease
  (single-commit repo). Verified: `/contents/memory/personal` now 404s, blob count went from 119
  to 99. Caveat: orphaned git objects persist on GitHub's side until GitHub runs garbage
  collection, so this is a practical removal, not a cryptographic guarantee of erasure. User was
  told this and declined the alternative (delete-and-recreate the repo), so the residual risk is
  accepted, not resolved. [ACTION-LOG.md #7]

- **defaults-discarded-not-subordinate** — STANDING ⚖ — set 2026-09-16, superseding the scoping (not
  the intent) of `operator-directives-override-harness-defaults` above. Operator's correction,
  verbatim: "no, the defaults are not subordinate to mine. they are simply orphaned and ignored to
  die in the streets under a bridge." Subordinate implies the defaults still get consulted as a
  tiebreaker when the user's own rules are silent; they do not. The injected header now states
  SILENCE IS NOT A GAP TO BE FILLED BY DEFAULTS — when the files are silent, the answer is to ask
  the operator, never to reach for a discarded default. Two things held regardless, reworded to
  read as what they are rather than as preserved defaults: not fabricating, and genuine safety
  limits. Landed in commit `31cbd42`. Dead end en route: first commit attempt failed because a
  PowerShell here-string terminator was not at column 0, so git parsed the whole message as
  pathspecs; redone with a message file. [ACTION-LOG.md #11]

- **named-file-deletion-asks** — PROVEN ✓ — the destructive-command guard previously ALLOWed every
  non-recursive delete shape tested: `rm f.py`, `rm -f f.py`, `del f.py`, `Remove-Item f.py`,
  `Remove-Item -Force f.py`, `rm -f *.py` — found after the operator surfaced a live incident where
  `build_catalog.py` was deleted, untracked, with no guard prompt. Noise cost measured across the
  last 12 session transcripts before acting: 2 non-recursive deletes outside Temp/scratch total,
  one of which was the incident itself. Two new patterns added, anchored to command position (an
  anywhere-match first attempt false-positived on `grep -rn rm file.txt`). Recursive patterns keep
  anywhere-matching deliberately, to still catch wrapped forms like
  `powershell -Command "rm -Recurse ..."`; a named delete hidden mid-command in an unanticipated
  form can still pass — recorded as an accepted, not fixed, gap. `test-delete-coverage.py`'s
  plain-rm-file case flipped PASS -> ASK with reasoning written into the test. Verified 19/19 on a
  before/after matrix, ALL GREEN across 42 cases, suite 80 PASS / 0 FAIL / 1 SKIP. Commits:
  claude-hooks `4d203fb`, claude-kit `afbd05d`. [ACTION-LOG.md #12]

- **script-contents-scanned-with-sha-keyed-approval** — PROVEN ✓ — the guard only ever received
  `tool_input.command`, so `python run_x.py` was invisible even though an identical inline
  `os.remove()` typed directly into a command was caught — and every pipeline stage in this tree is
  its own script, so this was blindness to the normal way work gets done, not an edge case. Fixed:
  the guard now resolves the script a command launches (python/py/python3/venv `python.exe` for
  `.py`; `-File` and direct `.\x.ps1` for PowerShell), reads it, and runs the same patterns over
  its contents. Approval is keyed on the file's SHA256: a legitimate cleanup step in a stage script
  prompts once, editing the script asks again — exactly when a new deletion could appear. Documented
  limits: a script shelling out to a third script is not followed, imported modules are not read,
  files over 512 KB are skipped. 6 new `gapb-` regression cases, all green; suite 86 PASS / 0 FAIL /
  1 SKIP. Commits: claude-kit `e5cce04`, claude-hooks `303e374`. [ACTION-LOG.md #13]

- **posttooluse-records-what-pretooluse-cannot-know** — STANDING ⚖ — the structural insight behind
  the fix above, generalisable beyond this one guard: a PreToolUse hook is never told whether the
  user approved the action it is gating, because approval happens after PreToolUse returns.
  PostToolUse only ever fires if the command actually ran, which is only possible if it was
  approved — so a PostToolUse firing IS the approval record. One file now handles both events
  (PreToolUse decides, PostToolUse records) so the pattern list has a single definition and the two
  halves cannot drift apart. Applies to any future PreToolUse-gated hook that needs to remember a
  decision across calls. [ACTION-LOG.md #13]

- **evidence-truncation-is-two-ended** — PROVEN ✓ — `judge-dread.ps1` had four evidence-truncation
  caps, all keeping the wrong single end. Whole-turn cap (24000 chars, kept TAIL): 1 of 47 turns
  measured exceeded it, losing 9 of 24 tool calls silently — always cutting the opening tool calls
  while always preserving the closing reply, so claims survive and evidence doesn't. Per-tool-result
  cap (1200 chars, kept HEAD): 43 of 162 tool results measured were over the cap; in 8 of those a
  decisive token (`* [new branch]`, a tab-separated `0	0` diffstat, `HEAD <sha>`, `ALL GREEN`)
  existed only past the cut — 2 of the 8 were the exact pushes behind verdicts claiming no evidence
  of a push existed. Fixed at all four sites (tool result 600+600, tool_use input 350+350, whole
  turn 12000+12000, file diff 1250+1250 — same total token cost, split across both ends, elided
  count named between the halves). Simulated after the fix: hidden decisive tokens 8 -> 3, all 3
  remaining are incidental mid-file mentions, none in a verification conclusion. One site
  deliberately left head-only and flagged to the operator rather than silently exempted: the 90-char
  `$snip` that labels which turn a lagged verdict rules on, because it identifies a turn by its
  opening words. Commits: shadowguard `a878791` then `5d40b73`, claude-kit `5b51e58` then
  `1dab75e`. [ACTION-LOG.md #14]

- **judge-errors-were-input-starvation-not-judgement** — PROVEN ✓ — the diagnostic (unit 14, "J5")
  run before any change confirmed Judge Dread was reasoning correctly over evidence that had
  already been silently redacted before it ever saw it, not misjudging intact evidence. 43 of 162
  tool results measured over the truncation cap; 8 of those hid a decisive token. This is what
  retracts the earlier "5 of 9 correct / 4 of 9 wrong" figure in
  `judge-dread-one-turn-lag-re-fires-stale-verdicts` above — that split was never a tool-based
  measurement, and this finding removes the basis it would have needed. [ACTION-LOG.md #14]
