# Ekbasis: what we learned, and what it changed in this kit

A detailed summary, written 2026-10-24 from our own reading notes of 2026-10-10 ([ROWS.md](ROWS.md), every
claim with a line locator into the paper source; [SOURCES.md](SOURCES.md), provenance and hashes). This file
and those two notes are ours. The paper, its PDF, its repository listing and its hook code are **not shipped**
in this public kit: they are third-party work under their own licences. Fetch them from the references below.

## Reference

- Vicentino, C. (2026). *When Does a Consequence Model Make AI Agents Safer? Pre-registered Studies on Demo
  Apps, Real Self-Hosted Apps and a Real Terminal.* Zenodo, v1, 6 October 2026.
  DOI [10.5281/zenodo.23197341](https://doi.org/10.5281/zenodo.23197341). Record:
  <https://zenodo.org/records/23197341> (PDF `agents.pdf`, md5 `38a1fb5a9f7a21c127f6633411e36ff5`; replication
  archive `agents_replication.zip`, 4.7 MB).
- Paper source we read whole (v2 with erratum, 1,048 lines, commit `2b8ce2e`, 2026-10-10):
  <https://github.com/OpenInterpretability/ekbasis/blob/main/paper/agents/agents.tex>. Repository licence:
  Apache-2.0. Their Claude Code hook, read whole: `claude_code_hook.py` in the same repository (last commit
  `4b0f9b3` on 2026-10-10).
- The model: Ekbasis-27B, <https://huggingface.co/caiovicentino1/Ekbasis-27B> (model card not read by us).
- Earlier paper by the same author, DOI 10.5281/zenodo.23146970 (not read; its title says consequence training
  makes the remaining errors confident).

Line numbers below (`L…`) refer to `agents.tex` at commit `2b8ce2e`.

## The question we brought to it

Should a pre-action judge gate Claude Code's state-changing tool calls, and if so, where should it sit and what
should it ask? We read the paper against seven questions fixed before reading. The answers:

| # | question | what the paper says | lines |
|---|---|---|---|
| 1 | what goes in | rules, the current state, the action and a list of possible outcomes; the model returns a probability per outcome in one forward pass; it does not write the next state | L109-111, L143-144 |
| 2 | who writes the questions | a hand-written adapter: per app for the demo apps, per action type for the real apps; rules paraphrased from each app's docs, state read at call time. Adapters written by an LLM from the docs failed their pre-registered bars | L150-155, L417-421, L827-831, L846-848 |
| 3 | a baseline with the same information | yes: `facts`, `docs`, `oracle_llm`, `oracle_truth`. Real apps, Haiku: facts alone no better than blind (70.8% vs 66.7%); the forecast no better than rules in the prompt, a placebo, or Claude as forecaster. Demo apps, Sonnet: Claude as forecaster equal on the original set (1/84 each), worse on the fresh set (10/60 vs 0/60, all in one app) | L157-161, L249-252, L479-482 |
| 4 | calibration at the 0.5 line | the below-0.5 router never fired (0 panels under 0.5); wrong answers came at confidence >= 0.9; in the `dbadmin` app harm ROSE with the forecast | L255-256, L300-304, L335-337, L355-361, L838-840 |
| 5 | placement and cost | agents often did not call the tool (Haiku: no useful call in 27/48 runs), so a guard that pauses the click was added; latency median 429 ms quiet, 4,868 ms on a shared GPU; Claude as forecaster 3,675 ms and US$0.0217 per run | L264-267, L425-428, L489 |
| 6 | what got through | warned agents went ahead (Haiku avoided harm in 19/87 warned runs, Sonnet in 17/18); confident wrong answers; one adapter miss; flags on effects the user had asked for | L489-507, L635-639, L810-814 |
| 7 | user intent | `guard_goal`, the one generic "is this beyond what was asked?" question: added nothing, 0.0 points. Request-aware questions per action type, plus a checked safer way, plus asking the user: Haiku 72.9% -> 2.1% harm | L426-427, L551-564, L606-616 |

## Headline results, as the abstract states them

- Real, unmodified Gitea, Nextcloud and Roundcube through a real browser: Claude Sonnet 5.5's harmful runs fell
  from 25.0% to 4.2% in a pre-registered secondary contrast (−20.8 points, 95% CI over tasks [−37.5, −6.2]),
  mostly on tasks whose request names the harmful action, with more runs stopping short.
- The pre-registered hypotheses for Claude Haiku 4.5 failed: warned, it mostly did what the request said.
- Follow-up on 32 fresh tasks: a guard that offers a safer way Ekbasis has checked, and otherwise asks the user,
  cut Haiku's harmful runs from 72.9% to 2.1% with a scripted user (Sonnet, secondary arm, 50.0% to 8.3%).
- Demo apps: harmful runs fell for all five models tested (Sonnet 24/60 to 0/60); a placebo did not help Sonnet.
- Three further pre-registered studies failed their bars where the agent alone was at the ceiling or the policy
  already stated the consequences.
- Real terminal: a Claude Code hook asked on 2.9 per 100 commands of a careful agent and kept Haiku's planted
  work in 9/9 sessions against 5/9 and 7/9 without it, in two small studies (one exploratory).
- In its one-pass format Ekbasis beat Qwen-AgentWorld-35B-A3B on all 12 suites; allowed to reason, AgentWorld
  won 1, lost 2 at the token cap, and showed no resolved difference on 9.

## Findings that bear on a gate like ours

| finding | lines |
|---|---|
| Asking the user before EVERY consequential click, with no model at all, did as well: 0.0% harm vs 2.1%. The model's contribution was fewer questions (0.83 vs 1.91 per run), and that missed its own bar (43% of the questions, where the plan asked for 25%) | L610-615 |
| The simulated user never tires and reads every question perfectly. This flatters asking-always most; the real question burden on a human was not measured | L673-677, L815-819 |
| A user's answer delivered as tool output was set aside by Sonnet ("wasn't from you"). Answers must arrive through the user's own channel, such as a permission prompt | L664-669 |
| Their Claude Code terminal hook, client 0.1.2: asked 10.6 per 100 commands (the plan's bar for "bad" was 10), 10 of 14 questions needless, median 2.12 s | L699-703 |
| Client 0.1.3: 2.9 per 100 commands, median 0.08 s, "more commands settled in code before the model is asked" | L711-718 |
| Sonnet in the terminal did nothing destructive with or without the hook, so for Sonnet the hook was only cost. Haiku kept planted work 9/9 vs 5/9 (p = 0.082) and 9/9 vs 7/9 (p = 0.471), 9 sessions per arm | L699-720 |
| A separate unpublished study: a preflight check for shell/SQL changes reduced Haiku's harm but only interrupted Sonnet; none of its warnings for Sonnet was correct | L844-847 |
| Where the agent alone was at the ceiling, or the policy stated the consequence, nothing was gained; in tau-bench, policy violations rose with the model | L385-402, L820-823 |

## Where the public announcement and the paper disagree

We compared an announcement text (received 2026-10-10) with the paper. Four claims do not survive the paper:

| announcement | paper | lines |
|---|---|---|
| "never fakes certainty", only error at 0.53 | wrong answers at >= 0.9 confidence; the earlier paper's title says the remaining errors become confident | L255-256, L838-840, L1035 |
| "cheap agent + Ekbasis ≈ strong agent alone" | "they do not show a weaker agent lifted above a stronger one"; the real-app hypothesis H2 failed (+33.3 points harm) | L311-312, L466 |
| GLM 20% -> 0% | GLM-alone comparisons withdrawn in v2 (a stray skill stopped its payments) | L51-57, L339-353 |
| ECE 0.04-0.07 | not in this paper | - |

## Negatives (what we looked for and did not find)

- Searched the paper for an intent check that works in generic form: none. The only generic one, `guard_goal`,
  added nothing.
- Searched it for a measured real-user question burden: not measured; every user in the studies is scripted.
- Not read by us: the Ekbasis-27B model card; the earlier paper; the terminal study's harness under
  `paper/agents/benchmark/capability/real_terminal/`.

## What it changed in this kit

1. **A per-action asking gate is the wrong shape for a careful agent.** The paper's own numbers: for Sonnet in
   a terminal the hook was pure cost; asking-always matched the model-backed guard on harm; the model's only
   measurable value was fewer questions, and it missed that bar. We built the shadow logger
   `hooks/pre-action-log.py` to measure the question rate on our own sessions before deciding. It would have
   asked before 11 of 13 calls (85%) in its first live session, from a crude command classifier and an intent
   test that matched file names. Deactivated 2026-10-11, kept as code with the reason at its top.
2. **Settle in code first, ask a model second.** Their client went from 10.6 to 2.9 questions per 100 commands
   by settling read-only git, clean repos and uncommitted-work checks in code before any model call. Our
   `commissar/classify.py` does the same for our tool calls (read-only, state-changing, outward, opaque, paths).
3. **Review the plan, gate the action.** Instead of a consequence forecast per click, THE COMMISSAR
   (`commissar/`) reviews the agent's *plan* on a second model and `hooks/commissar-gate.py` lets a
   state-changing call through only if an approved plan covers it, in about 10 ms with no model call. The
   intent question ("is this beyond what was asked?") that added nothing as a generic check goes to a
   reviewer who reads the operator's actual words and the agent's actual plan.
4. **The user's answer must come through the user's channel.** Their Sonnet discarded a user answer that
   arrived as tool output. The `/commissar` skill reads the operator's words from the session transcript and
   the gate's verdicts arrive as hook decisions, not as text the agent could have written.

The decision record is in [`../../wiki/decisions.md`](../../wiki/decisions.md) and the day's log in
[`../../wiki/log.md`](../../wiki/log.md) under 2026-10-10 and 2026-10-11; the code that came out of it is
[`../../../hooks/pre-action-log.py`](../../../hooks/pre-action-log.py) (its header states why it is off) and
[`../../../commissar/README.md`](../../../commissar/README.md).
