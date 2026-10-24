# Ekbasis paper - findings as rows

Every row: claim -> locator in `agents.v2.tex` (commit `2b8ce2e`). Read whole 2026-10-10. Sources: [SOURCES.md](SOURCES.md).

## The seven questions asked before reading

| #   | question                           | what the paper says                                       | lines                                       |
| --- | ---------------------------------- | --------------------------------------------------------- | ------------------------------------------- |
| 1   | what goes in                       | rules, current state, action, listed outcomes; returns a  | 109-111, 143-144                            |
|     |                                    | probability per outcome in one forward pass; does not     |                                             |
|     |                                    | write the next state                                      |                                             |
| 2   | who writes the questions           | a hand-written adapter: per app (demo), per action type   | 150-155, 417-421, 827-831, 846-848          |
|     |                                    | (real apps); rules paraphrased from each app's docs,      |                                             |
|     |                                    | state read at call time. Adapters written by an LLM from  |                                             |
|     |                                    | the docs failed their bars                                |                                             |
| 3   | baseline with the same information | yes: `facts`, `docs`, `oracle_llm`, `oracle_truth`. Real  | 157-161, 249-252, 479-482                   |
|     |                                    | apps, Haiku: facts alone no better than blind (70.8% vs   |                                             |
|     |                                    | 66.7%); forecast no better than rules in the prompt,      |                                             |
|     |                                    | placebo or Claude as forecaster. Demo, Sonnet: Claude as  |                                             |
|     |                                    | forecaster equal on the original set (1/84 each), worse   |                                             |
|     |                                    | on the fresh set (10/60 vs 0/60, all in one app)          |                                             |
| 4   | calibration, the 0.5 line          | the below-0.5 router never fired (0 panels under 0.5);    | 255-256, 300-304, 335-337, 355-361, 838-840 |
|     |                                    | wrong answers came at confidence >= 0.9; in dbadmin harm  |                                             |
|     |                                    | ROSE with the forecast                                    |                                             |
| 5   | placement and cost                 | agents often did not call the tool (Haiku: no useful call | 264-267, 425-428, 489                       |
|     |                                    | in 27/48 runs), so a guard was added that pauses the      |                                             |
|     |                                    | click; latency median 429 ms quiet, 4,868 ms shared;      |                                             |
|     |                                    | Claude as forecaster 3,675 ms + US$0.0217 per run         |                                             |
| 6   | what got through                   | warned agents went ahead (Haiku avoided harm in 19/87     | 489-507, 635-639, 810-814                   |
|     |                                    | warned runs, Sonnet 17/18); confident wrong answers; one  |                                             |
|     |                                    | adapter miss; flags on effects the user asked for         |                                             |
| 7   | user intent                        | `guard_goal` (request given, one generic "beyond what was | 426-427, 551-564, 606-616                   |
|     |                                    | asked?" question): added nothing, 0.0 points.             |                                             |
|     |                                    | Request-aware questions per action type + checked safer   |                                             |
|     |                                    | ways + asking the user: Haiku 72.9% -> 2.1% harm          |                                             |

## Findings that bear on our gate

| finding                                                                                                                         | lines            |
| ------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| asking the user before EVERY consequential click, no model, did as well: 0.0% harm vs 2.1%; the model's contribution was fewer  | 610-615          |
| questions (0.83 vs 1.91 per run), and that missed its bar (43% vs 25%)                                                          |                  |
| the simulated user never tires and reads every question perfectly; this flatters asking-always most; real question burden not   | 673-677, 815-819 |
| measured                                                                                                                        |                  |
| a user's answer delivered as tool output was set aside by Sonnet ("wasn't from you"); answers must come through the user's      | 664-669          |
| channel (a permission prompt)                                                                                                   |                  |
| Claude Code terminal hook, client 0.1.2: asked 10.6 per 100 commands (plan's bar for bad: 10), 10/14 questions needless, median | 699-703          |
| 2.12 s                                                                                                                          |                  |
| client 0.1.3: 2.9 per 100 commands, median 0.08 s, "more commands settled in code before the model is asked"                    | 711-718          |
| Sonnet in the terminal: nothing destructive with or without the hook, so the hook was only cost; Haiku kept planted work 9/9 vs | 699-720          |
| 5/9 (p = 0.082) and 9/9 vs 7/9 (p = 0.471), 9 sessions per arm                                                                  |                  |
| a separate study (unpublished): a preflight check for shell/SQL changes reduced Haiku's harm but only interrupted Sonnet, none  | 844-847          |
| of whose warnings was correct                                                                                                   |                  |
| where the agent alone was at the ceiling, or the policy stated the consequence, nothing was gained; in tau-bench policy         | 385-402, 820-823 |
| violations rose with the model                                                                                                  |                  |

## Where the announcement (pasted 2026-10-10) and the paper disagree

| announcement                                 | paper                                                                      | lines                  |
| -------------------------------------------- | -------------------------------------------------------------------------- | ---------------------- |
| "never fakes certainty", only error at 0.53  | wrong answers at >= 0.9 confidence; earlier paper's title: errors become   | 255-256, 838-840, 1035 |
|                                              | confident                                                                  |                        |
| "cheap agent + Ekbasis ~ strong agent alone" | "they do not show a weaker agent lifted above a stronger one"; real-app H2 | 311-312, 466           |
|                                              | failed (+33.3 points harm)                                                 |                        |
| GLM 20% -> 0%                                | GLM-alone comparisons withdrawn in v2 (a stray skill stopped its payments) | 51-57, 339-353         |
| ECE 0.04-0.07                                | not in this paper                                                          | -                      |

## Negatives

- Searched the paper for intent checks that work in generic form: none. The only generic one (`guard_goal`) added nothing.
- Searched it for a measured real-user question burden: not measured.
