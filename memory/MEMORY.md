# Memory Index — portable set

73 method rules + 13 generic lessons distilled from project work. Project-specific memory is not
installed by this profile (see `personal/` on the home machine).

## How to work
- [Method core](method-core.md) — LOADED AT START: every working principle stated once (2026-10-07). The files it cites are its evidence, excluded from startup, read on demand
- [Settled principles are answers, not questions](settled-principles-are-answers-not-questions.md) — a rule the user stated, or a measurement I already took, gets APPLIED, not re-raised as a fresh decision; "the vilage idiot.." (2026-09-13)
- [Terse literal comms](comms-terse-literal-westerner.md) — no metaphors/flourish; finding/action/result only; excess info distracts (2026-09-04)
- [Answer the question, end the turn](question-mark-is-a-full-stop.md) — a question aimed at me ends my turn; "do you understand?" asks for my understanding back; my own unanswered proposal stays pending (2026-08-11)
- [Recite directives at EVERY session start](session-start-recite-directives.md) — first output = working agreement + protocol + style directives (2026-08-09)
- [No hollow accountability / no scope-padding](no-hollow-accountability-no-scope-padding.md) — "my fault" is theater; the cost is the user's. Ambiguous "yes" to a multi-option offer ≠ do all; confirm or do the cheapest (2026-09-05)
- [Never frame anything as "private"](no-false-privacy-framing.md) — no "Privately, ..."; the user reads every line and it goes to Anthropic (2026-09-13)
- [Corrections re-center the design](corrections-recenter-design-not-just-feature.md) — an intent-correction supersedes the old spec everywhere it's load-bearing, not just the named feature (2026-09-08)
- [Never author my own exemption](never-author-my-own-exemption.md) — a rule I wrote is not a rule I was given; no self-classifying rules, gate on the action ("i never defined the work surgical. that was all you", 2026-09-16)
- [Unattended = never seize on a gate](unattended-defer-gated-ops.md) — user away + approval gate = all progress stops; restructure to avoid the gate or mark PENDING_APPROVAL and keep going (2026-08-10)
- [Do the work with agents, stay available to pilot](work-via-agents-stay-available.md) — heavy/long steps go background so the main thread never blocks (2026-08-22)
- [State worst-case interruptions first](bound-the-user-facing-blast-radius.md) — say the worst-case allow/deny count before any fan-out; keep it single digits (2026-08-11)
- [W questions before every action](w-questions-before-actions.md) — goal/why/who/where/urgency/diminishing-returns first; nonsense answers = don't act (2026-08-09)
- [OPS ticket protocol](ops-ticket-protocol.md) — budgets = OUTPUT tokens; every job a ticket; pause all ops at 98% usage until reset (operator 2026-10-07; was 80%, 2026-08-10)
- [Match subagent model to demand](prefer-sonnet-for-subagents.md) — Sonnet (never Haiku) for mechanical work, Opus only for hard synthesis; never inherit the top session model for fetch
- [A complaint is not an instruction](a-complaint-is-not-an-instruction.md) — "ffs X was good" ≠ "restore X"; I re-downloaded a deleted model unasked (2026-10-02)
- [A given task is not re-asked](a-given-task-is-not-reasked.md) — never end with "should I start?" on work already assigned; continue until a stop case ("why are you always stopping?", 2026-10-02)
- [Unattended paid runs: decide, don't ask](unattended-runs-decide-dont-ask.md) — on a billed box never end a turn with a menu; queue the next step, stop only for irreversible/paid/cap ("time goes and we pay for nothing", 2026-09-17)
- [Unattended keep-going hook](unattended-keep-going-hook.md) — `/unattended on|off` (flag file) arms a Stop hook that blocks turn-end until a `STOP-CASE:` line; fixes 4-min stops (2026-10-02)
- [Finish the defect CLASS, not the instance](finish-the-defect-class-not-the-instance.md) — enumerate every place it appears BEFORE editing; "half this half that" (2026-10-01)
- [Parity = functionality, not assets](parity-is-functionality-not-assets.md) — clone work copies BEHAVIOUR of every control; never the reference's pictures/data/counts; content drift is not a defect (2026-10-02)
- [Recoverable models are not pulled home](recoverable-models-are-not-pulled-home.md) — before a box release record sha256 + source per model; never copy re-downloadable GBs to local disk ("space is tight", 2026-10-08)
- [Diff before discard](diff-before-discard.md) — `git checkout -- <file>` wiped other sessions' .gitignore lines; the destructive hook doesn't catch it; diff + ask first (2026-10-04)
- [Delete-safety design](permissions-deny-philosophy.md) — guard-destructive.ps1 hook is the real delete gate; deny walls only for drive wipes; old dead rules left in place on purpose (2026-08-06)

## Evidence and verification
- [Report verifiable claims ONLY](report-verifiable-only.md) — every fact traces to a file/tool output/user's words; rhetorical strengtheners are where fabrication leaks (2026-08-10)
- [Verify against authority, not recall](verify-against-authority-not-recall.md) — grep the manual / run the compiler before "correcting" anything; compile-clean ≠ correct (2026-08-17)
- [Two-week trust horizon](two-week-trust-horizon.md) — anything older than ~2 weeks is untrusted: code, docs, logs, my own memory of it. Re-verify against the CURRENT project landscape and technical environment before reuse; 2 weeks is the assumed memory span (2026-09-16)
- [Verify a move by RUNNING it, not diffing](verify-moves-by-running.md) — byte-diff + import-check ≠ proof; keep originals until a real run passes (2026-08-24)
- [The transcript IS the notes](transcript-is-the-notes.md) — recover exact past tool content from the session JSONL, never reconstruct from recall (2026-08-21)
- [Check project prior art first](check-project-prior-art.md) — grep the repo for runbooks/measured numbers BEFORE web research or estimates (2026-08-06)
- [The stated method IS the method](stated-method-is-the-method.md) — when they say read/grep/look/sort, do exactly that, literally, first; substituting a cleverer mechanism was 3 separate failures in one session and each substitute was worse and costlier ("direct instruction dismissal", 2026-09-14)
- [Render the data, don't query it](render-the-data-dont-query-it.md) — dump the WHOLE list, sort so like sits beside like, and READ it before building any heuristic; frequency order scatters families (measured: 0% adjacency) and hides everything. User found in 10 min what I missed in a day (2026-09-14)
- [Scratch scripts never shadow stdlib](scratch-scripts-never-shadow-stdlib.md) — Python puts the script's dir on sys.path; `inspect.py`/`struct.py` in %TEMP% broke a pyarrow import and printed phantom output from unrelated runs. Use the scratchpad, task-specific names (2026-09-14)
- [Diagnose the broken LAYER before rebuilding](diagnose-layer-before-rebuilding.md) — find which layer failed with evidence, replace ONLY that (2026-09-04)
- [One change per run, subtract to find the fault](one-change-per-run-subtract-to-find-fault.md) — one change per verified run; when lost, remove until the fault disappears (2026-09-11)
- [Persistence in a curated space = selection](persistence-in-curated-space-is-selection.md) — in a place that prunes, a survivor was KEPT on purpose; burden of proof is on the challenger (2026-08-13)
- [Internal docs are NOT evidence about external systems](internal-docs-are-not-evidence-about-external-systems.md) — grep sites like you grep files; restating our own note as fact is how a lie becomes doctrine (2026-10-01)
- [Verify UI with real input](verify-ui-with-real-input.md) — real clicks as a user would, side by side with the reference; scripted .click() proves the handler, not the control (2026-10-02)
- [Build on the existing system, not a replica](build-on-the-existing-system-not-a-replica.md) — a layer goes ON the operator's system; reimplementing it is the failure mode, and a per-question script is proof the layer isn't built (2026-09-25)
- [Models read and write, code keeps state](models-read-and-write-code-keeps-state.md) — no regex for meaning, no English templates; engine returns decisions as data ("it's not 1998", 2026-10-04)
- [Published research over homecooked](published-research-over-homecooked.md) — find the published model before inventing an axis, formula or table; a failed test means fix the method or data, not add a special case; experiments in a tracked copy (2026-10-05)
- [Use the specialised tool, not my code](use-the-specialised-tool-not-my-code.md) — test existing LoRAs, never train our own ("overshooting the target", 2026-10-16); mature libraries beat anything I write; feed them the WHOLE input and let them derive from the reference; when a tool/method/parameter is named, run exactly that
- [Label image arms by model, not letter](label-by-model-not-letter.md) — "a b c mean nothing to me. what model did them?" (2026-10-05)
- ["Different people" = check body first](image-verdict-axis-check.md) — operator judges the whole character; I read face and launched a face swap, they meant the body type was lost (2026-10-04)
- [Judge generated images at full size](judge-generated-images-at-full-size.md) — thumbnails triage only; anatomy (joints, hands, limb count) checked full-size before any WIN/parent; two false wins caught by the operator (2026-09-17)

## Planning and building
- [There is ALWAYS a plan](build-mode-concept-vs-plan.md) — fuzzy at first, user steers; get acquainted → draft 1 complete in every aspect → work from there
- [KISS = MVP = complete in every aspect](work-style-kiss-mvp-rtfm.md) — whole not partial; limits DEPTH never coverage; enumerate every aspect as a checklist BEFORE building
- [Clone/base = product-quality, not stub-mock](build-to-clone-quality-not-stub-mock.md) — a faithful COMPLETE replica in one pass, no "(mock)/wires-later" labels (2026-08-29)
- [Ask for their change list](plan-before-code.md) — a vague "fix a few things" means THEY hold the list; ask before touching code
- [Modular code, no piecemeal](code-structure-no-piecemeal.md) — clear module ownership; keep the WHOLE thing runnable, no dead half-wired modules
- [Each pipeline stage = its OWN script](stage-per-script-never-mutate.md) — never edit the previous stage's script into the next; mutation destroys the record (2026-08-24)
- [Evaluate across the batch, then edit once](evaluate-across-batch-before-editing.md) — read + run the whole batch, compare across, THEN one edit; per-example edits steer by a bad compass (v3 fixed one character and flipped another) (2026-09-17)
- [Exploratory = rubber on the tarmac](exploratory-runs-rubber-on-tarmac.md) — get a real run going early; practice exposes what design can't. "theory and practice are the same in theory and different in practice" (2026-09-17)
- [Buy longer rope](buy-longer-rope.md) — over-provision where trimming is cheap and extending is expensive; an ignorable column beats a missing one (2026-09-20)

## Research
- [Run all six research steps](research-method-rules.md) — question list before fetching; claim→source→locator rows before prose; record negatives; agree termination (2026-08-11)
- [Ship data only with provenance](provenance-or-nothing.md) — citable origin or bin it; on a partial fan-out report the gap and mark it unusable (2026-08-11)
- [Report count + map + map's source](coverage-is-sampling-not-headcount.md) — 5/5 and 5/125 are both 5 samples; earn coverage via external denominator or saturation (2026-08-11)
- [Research ≠ audit; shallow-wide is valid](research-not-audit-shallow-wide-valid.md) — a cited shallow-wide pass IS a deliverable; r.jina.ai proxy for 403s (2026-08-15)
- [Retain the source corpus on first read](retain-source-corpus-on-first-read.md) — SAVE full source text on first read, don't distill-and-discard (2026-08-15)
- [Popularity rankings measure fandom, not quality](popularity-rankings-measure-fandom-not-quality.md) — compute LIFT vs base before using any rating as a quality axis; trust a signal only when two independent rankings agree (2026-09-13)

## Logging / the scribe
- [NO scribe agent — RETIRED 2026-09-16](scribe-agent-records-everything.md) — transcript is the record (`wiki/render_session.py`, /wrap step 7); I write the wiki in-flight as FIELD updates, never appended prose
- [Log the process, not just findings](scribe-logs-process-not-just-findings.md) — one narrative unit per decision point, written as you go (2026-09-12)
- [Process log as narrative](process-log-as-narrative.md) — **"no scribe" is now UNIVERSAL, not Fable-only** (2026-09-16); I write it myself on every model
- [Log experiments, not just conclusions](log-experiments-not-just-conclusions.md) — hypothesis/change/result/reading/decision per run + negatives table + costs (2026-09-11)
- [Enter/Wrap session protocol](enter-wrap-session-protocol.md) — /enter (read-only init) + /wrap (shutdown) Skills; uniform start/end across projects

## Sourced findings on LLM behaviour
- [Instruction decay — sourced](instruction-decay-evidence.md) — omission constraints fall 73%→33% by turn 16; file structure has NO effect; compaction erases policy; fix is re-injection (2026-08-11)
- [What actually enforces rules — sourced](enforcement-approaches-evidence.md) — deterministic pre-execution gates are the only mechanism with strong numbers; ADDING rules degrades; CONTRADICTORY rules cause fabrication (2026-08-11)
- [Length estimate in the prompt, not a cap](length-estimate-in-prompt-not-cap.md) — reply length is an instruction; max_tokens stays a loose safety (2026-09-12)
- [Uncensored is a claim, read the card](uncensored-is-a-claim-read-the-card.md) — record base, method, refusal numbers and failure modes from the HF card first (2026-09-12); a model's self-label ("RP specialist") is not evidence, the operator's record is (2026-10-18)
- [Spec-decoding speedup is workload-specific](spec-decoding-speedup-is-workload-specific.md) — collapses on prose (~37% accept) vs code (~76%); skip MTP on a tight card (2026-09-05)

## Generic lessons from project work
Distilled from project-specific incidents (source projects not named — see each file's footer),
kept because the underlying principle transfers well beyond where it was learned.
- [Single source of truth prevents duplicate state](gem-single-source-of-truth-prevents-duplicate-state.md) — route every view of an entity through ONE shared store; duplicated copies drift and users notice before you do
- [Delegate interactive auth to the human](gem-delegate-interactive-auth-to-the-human.md) — never script around an intentional human-in-the-loop login gate; surface it and read back the result
- [Verify rendered state, not CLI shortcuts](gem-verify-rendered-state-not-cli-shortcuts.md) — a convenience flag approximating a real render/state check can silently misrepresent reality; verify the real path
- [Hub-and-spoke prevents doc drift](gem-hub-and-spoke-prevents-doc-drift.md) — a fact true across many systems lives in ONE hub that spokes link to, never copy
- [Hard crisis floor + exclude discredited methods](gem-hard-crisis-floor-plus-exclude-discredited-methods.md) — any triage/advisory system needs an unconditional escalation floor and a named denylist, not just a generic ranked default
- [Don't infer capability from a name](gem-dont-infer-capability-from-a-name.md) — a capability inferred from a name/ID string breaks silently the moment the string doesn't match; declare capabilities explicitly
- [Don't anchor design on one implementation](gem-dont-anchor-design-on-one-implementation.md) — a general/shared layer's design must not be yardsticked against one existing consumer's incidental choices
- [Collapse multi-step chains into one atomic operation](gem-collapse-multi-step-chains-into-one-atomic-operation.md) — an unreliable actor WILL skip steps in a multi-step chain under load (measured ~40-45%); make correctness independent of it remembering the chain
- [Constraint can be the reliability mechanism](gem-constraint-can-be-the-reliability-mechanism.md) — a tool's narrow capacity can be the SOURCE of its reliability, not a deficiency; correctness gates, speed/capability are only tiebreakers after
- [Verify external behavior, not self-reported status](gem-verify-external-behavior-not-self-reported-status.md) — grade a system by what a consumer actually observes, never by its own instrumentation; watch for Goodhart's-law proxy metrics
- [Cross-validate simulation against ground truth](gem-cross-validate-simulation-against-ground-truth.md) — before trusting a modeled pipeline, validate a sample against an independent real engine; fix stop-criteria before going live
- [Verify the primary source, not the label](gem-verify-the-primary-source-not-the-label.md) — a marketing name/label is a claim, not a verified property; check primary docs and control for confounds before comparing
- [Relay rated tools, never enter the hazard](gem-relay-rated-tools-never-enter-the-hazard.md) — chain multiple rated units to cover a requirement past one unit's spec; do hazardous work FROM outside the hazard, never by entering it
