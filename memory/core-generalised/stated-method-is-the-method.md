---
name: stated-method-is-the-method
description: "When the user specifies HOW, execute that exact method; substituting my own is the most repeated failure"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-08T03:24:31.186Z
---

When the user states a method, **execute that method**. Not a variant, not
something that achieves a similar goal more cleverly. `~/CLAUDE.md` already says
this ("Follow the stated method exactly. An explicit method is an instruction");
the point of this memory is that I break it repeatedly and do not notice.

Three violations in one session, 2026-09-14 (an RP / story-archive project):

| they said | I did |
|---|---|
| "read everything and categorise it. it's not hard" | built an embedding classifier (it failed), then hand-wrote aliases |
| "go in and read the words. it's apparent what is mispelled" | fanned out 12 agents to read for me |
| "we grep a couple of lines before and after and evaluate" | counted word frequencies across whole chapters |

The third one needed the user to explain with an example — "'mom made cookies'
is a different signal than 'i banged mom on the couch'" — before I saw that
document-level counting cannot distinguish them. The stated method (a window
around the hit) handles it natively. Their verdict: **"direct instruction
dismissal."**

**Why it keeps happening:** a stated method looks like a suggestion when I can
see a more general mechanism. But the user has usually already reasoned about
the data; the method IS the conclusion of that reasoning. Every time I
substituted, the substitute was worse AND cost more.

**How to apply:** when the message contains a verb describing procedure — read,
grep, look, open, sort, split, list — that is the instruction. Do it literally,
first, at small scale, and show the result. If I genuinely think something else
is better, say so in ONE line and then do it their way anyway unless told
otherwise. Building the alternative first and presenting it as progress is the
failure.

**Earlier instance, 2026-07-26** (an RP engine, polishing seed characters; merged 2026-10-08 from the retired memory folder of an RP project, original in a related project note as `follow-stated-method-no-silent-deviation`):
the stated method was "polish each seed until correct, then move on". I batched instead of looping per seed
and folded 9 of 20 seeds into a batch, flagged only in passing. The operator asked how to stop having to
babysit; the answer was an operating agreement, not a different tool: never change the deliverable, coverage
or scope without an explicit OK, and flag any shortcut prominently at the moment it is taken.

**The adversarial-review gate (operator-mandated 2026-07-26)** - the procedure `method-core` section 3 refers
to. Before proceeding with a planned approach on a task that has an instructed directive:
1. Re-read the operator's literal words, not my paraphrase.
2. Spawn an adversarial Opus subagent whose only job is to compare the directive with my plan and hunt for any
   deviation, mismatch, silent scope-narrowing, or added or dropped step. It must check explicitly: does the
   plan do EXACTLY the cadence and scope the directive states, item by item, with nothing collapsed into a batch?
3. No problem found -> proceed.
4. Problem found -> fix the plan, then spawn a NEW, fresh adversarial agent to re-review. Never reuse a
   reviewer: it anchors on the errors it already spotted.
5. Loop until a fresh agent clears the plan; only then execute.
(The gate was run this way on 2026-08-02: cleared on round 3 by fresh reviewers, a related project note.)

Related: [[render-the-data-dont-query-it]],
[[settled-principles-are-answers-not-questions]],
[[no-hollow-accountability-no-scope-padding]]

**2026-10-18, same class.** Operator: "rp fast moe's ... since the flash model, we can only scale up." I answered the adjacent question (make Flash-Next faster: 3090s, risers, Q2_0) for three turns. Correction: "you missed the point entirely. i want to try and run laguna on the node faster than the stock llama cpp. or chat oss." In this project **scale up = a bigger model on the same box**, served faster with the new expert-cache paths; the hardware thread is separate. When the operator names a model (Laguna, gpt-oss), the run is on that model.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
