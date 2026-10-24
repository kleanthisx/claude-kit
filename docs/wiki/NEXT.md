# NEXT — start here

Last updated 2026-10-24.

**State:** local `main` (full history, not pushed, no upstream) carries the 2026-10-24 release prep: memory
tier level with live (86 files), live hooks/skills synced, commissar as an optional `-WithCommissar` layer.
`transfer` 53c8cd0 = `origin/main` on https://github.com/kleanthisx/claude-kit — PUBLIC, CC0-1.0 — is the
2026-10-08 state. To send changes: commit on main -> build the transfer tree WITHOUT `docs/research/`
(third-party corpus, licences unchecked) and without untracked `conclave/` -> `git commit-tree <tree> -p
transfer` -> `git branch -f transfer <sha>` -> denylist scan -> fresh adversarial review -> `git push origin
transfer:main` (outward-facing: operator's go).

## Open items from 2026-10-24, most actionable first

A. **Push the new transfer** once the operator says go (second candidate after the review fixes; re-review first); then have the friend run `install.ps1 -WhatIf`
   first, then the real install, then the four free suites. Nothing is verified off this machine yet.
B. **Conclave ships** (operator, 2026-10-24: "conclave stays in"). It gets the commissar treatment:
   tracked, council/db/project-root parameterised, an installer switch, a README section; then the
   candidate is rebuilt and re-reviewed.
C. **Ekbasis** ships as our `SUMMARY.md` + `ROWS.md` + `SOURCES.md` with the academic reference; the copied
   third-party files stay home (operator, 2026-10-24). The transfer filter drops exactly those files.
D. **Live commissar drift:** the kit's `service.py`, `talk.py`, `up.py`, `commissar-gate.py` now derive
   their paths from the install location; the live `~/.claude/commissar` copies still hardcode this
   machine. Copy the kit versions over (same behaviour here) or the next sync diffs them again.
E. **Live `hooks/test-hooks.ps1` vs kit `tests/test-hooks.ps1`:** same 50 cases, different `$H` root and
   one example path; keep syncing live -> kit with that one substitution.
F. **Stray untracked copies** in `hooks/` (`test-entity-read.ps1`, `guard-entity-read.ps1.from-live-2026-10-08`,
   both older than the tracked files): delete or move to an archive; they never ship (untracked) but confuse a diff.

## Open items carried from 2026-09-17

A. **Install at the work site and run the suites there** — nothing is verified off this machine:
   `install.ps1 -WhatIf`, real install, tests, then `test-judge-dread.ps1` once `claude` is on PATH
   (paid calls; never run this session).
B. **Stale "FOUND, NOT FIXED" heading** was corrected only in claude-kit `hooks/README.md`; the live
   `~/.claude/hooks/README.md` and the `claude-hooks` repo still carry it.
C. **Uninstall leaves `hooks/fixtures/` behind** (file-only removal loop) — noted in BOOTSTRAP, not fixed.
D. **Agent budgets:** set token/tool caps in every agent prompt and send one shared conventions bundle
   instead of letting each agent re-read it.

## Carried from 2026-09-16

1. **Verify the 45-directive injection and the wholesale/defaults-discarded precedence header in
   a real session — cheap, concrete test available.** Both changes (see ACTION-LOG units 2, 10,
   11) take effect starting at the *next* session start and have not yet fired in a live session.
   Verification that neither party can fake: at the start of the next session, ask the assistant
   to quote a sentence from a directive file that does **not** appear in `RULES.md`. If the
   injection worked, it can quote it (the full file is in context). If the injection silently
   failed, it cannot — it only has the summary. This is a pass/fail test, not a judgment call.

2. **Judge Dread's one-turn delivery lag is still open — the accuracy half was fixed today, the
   lag half was not.** A verdict written against turn N is delivered after turn N+1 and re-fires
   again at N+2 without ever re-evaluating, so evidence produced in direct response to a verdict
   can never reach that verdict. Measured 2026-09-16: 9 distinct verdicts produced 47 deliveries.
   A delivery-side dedupe (deliver each verdict hash once) was proposed mid-session and then
   **withdrawn by the assistant** on the grounds that it would be improper self-editing of the
   assistant's own accountability mechanism. This is recorded as the operator's call to open, not
   the assistant's, per `judge-dread-one-turn-lag-re-fires-stale-verdicts` in decisions.md.

3. **The `$snip` head-only exception awaits an operator yes/no.** Everywhere else in
   `judge-dread.ps1`, truncation was made two-ended today (see ACTION-LOG unit 14 /
   `evidence-truncation-is-two-ended`). One site was deliberately left head-only: the 90-char
   `$snip` that labels which turn a lagged verdict is ruling on, because it identifies a turn by
   its opening words. This was a judgment call flagged to the operator rather than decided
   unilaterally — needs a yes (leave as head-only) or no (find a different way to label the turn)
   before it's considered closed.

4. **personal-memory-off-github — CLOSED 2026-09-17** by deleting and recreating the GitHub repo (only the curated `transfer` history exists remotely). Original note: 20 project-state files were
   removed from `claude-kit`'s git history via amend + force-with-lease; GitHub may still hold
   orphaned objects until its own GC runs. The operator declined the delete-and-recreate
   alternative that would close this fully — no further action planned unless revisited.

5. **claude-hooks does not carry the two-ended judge-truncation fix — this is intentional, not
   drift.** `judge-dread.ps1` lives in `shadowguard` (canonical) and is mirrored into `claude-kit`
   only. It does not exist in `claude-hooks`, which holds the destructive-command guard family
   instead (named-file-deletion, script-content scanning). Noted here so a future session doesn't
   read the absence as an out-of-sync mirror and try to "fix" it.

## Quick pointers
- Precedence/override header history: commit `109b8fa` (wholesale override) then `31cbd42`
  (defaults discarded, not subordinate) in `claude-kit`.
- Destructive-command guard: `claude-hooks` commits `4d203fb` + `afbd05d` (named-file deletion),
  `303e374` + `e5cce04` (script-content scanning, SHA256-keyed PostToolUse approval).
- Judge Dread truncation fix: `shadowguard` commits `a878791` then `5d40b73`; mirrored into
  `claude-kit` as `5b51e58` then `1dab75e`.
- Test suite for hooks: `tests/test-hooks.ps1` — run with `-IncludeSuperseded` to also exercise
  the dead `verify-done.ps1` cases; without it, suite is 86 PASS / 0 FAIL / 1 SKIP as of the
  script-content-scanning addition (was 80 PASS / 0 FAIL / 1 SKIP earlier today).
- Injection exclude list for the memory injector: `memory/inject-exclude.txt`.
- Live settings.json backup taken before the PostToolUse gap-B change:
  `settings.json.pre-gapb-<timestamp>.bak`.
