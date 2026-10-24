---
name: evaluate-across-batch-before-editing
description: "When tuning a prompt or schema, read the whole batch and run it, evaluate ACROSS all results, THEN make one edit — editing after each example steers by a bad compass"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-12T18:54:11.533Z
---

Operator, 2026-09-17: *"read all 3/6 and do a run. evaluate across. then edit. that way you are not
steered by a bad compass potentially"*

**Rule:** read the full batch, run it, compare the results side by side, and only then change the prompt,
once. Do not revise after every chapter or pair of chapters.

**Why:** a single example is a compass that may point the wrong way. The same day proved it: the story
extractor was revised after every 2-4 chapters, and prompt v3's sharper "dom only for a real power
exchange" rule — written to fix ONE chapter's Mystery Man — flipped a different character (Quinn) from
`none` to `sub`. A fix that looked right against one failure was wrong across the set. Per-example
edits also fit the prompt to whichever chapter happened to come last.

**Second instance, an image-generation bench, 2026-10-03:** I tuned an image-generation site's face look on one character alone through seven runs and ended on a
one-character-only patch (`(blunt bangs:1.2)`). Operator: *"focusing on a single point loses it's value. we should look at a
few characters together. [that character] is out first and favourite but not the only control point. we are not matching
exceptions or statistical deviation, we are looking into the rule"*. For images: a fixed control set of several
characters, every arm run on all of them, judged side by side; a change that helps one character and not the others is
an exception, not the rule. No per-character hand edits in a recipe test.

**Third instance, image bench 2026-10-12 (a checkpoint version test, 7 checkpoints):** I sent sheets per version as each landed
and called verdicts on each ("V3 is not their model", "v6.0 is closest") with four of seven versions missing. Operator:
*"we cant decide on partial data"*. A verdict is a comparison, and a comparison needs the whole set. "Bring it down as they
finish" (their earlier ask) means pull and build as it lands; it does not mean judge as it lands. The rule covers
verdicts, not only edits: report progress as counts while a set runs; send the full sheet and the comparison once, when
the set is complete.

**Qualifier, 2026-10-12 (calibrating a new knob):** I designed a look-knob test as 3 characters x 6 arms x 5 seeds. Operator:
*"well, if it doesnt work for one, what makes you think it will work for the others? you know the baseline. generate on that
on variations of the knobs."* A new control is first SCREENED on one known baseline (fixed prompt + seed, an image already
judged) with the knob at several strengths and in combination; only a knob that works there goes to the batch. The batch
rule is for deciding a change is general, not for finding out whether it does anything at all.

**How to apply:** batch first (the operator suggested 3-6 items), read everything in the batch before
judging, tabulate the same fields across all items so a pattern separates from a one-off, then make a
single consolidated edit and re-run the SAME batch to measure it. A defect seen once is a note; a defect
seen across the batch is a fix. Pairs with [[one-change-per-run-subtract-to-find-fault]] and
[[exploratory-runs-rubber-on-tarmac]], and with the sourced finding in [[enforcement-approaches-evidence]]
that piling on rules degrades adherence.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
