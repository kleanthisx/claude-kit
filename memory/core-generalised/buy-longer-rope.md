---
name: buy-longer-rope
description: "Over-provision where trimming is cheap and extending is expensive — keep the extra column, the extra field, the extra capture. \"The longer rope can be cut shorter. The short one can't be stretched to length.\""
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-20T10:28:44.668Z
---

Operator, 2026-09-20: *"when buying rope always get longer. the longer rope can be cut shorter. the
short one can't be stretched to length."*

Said after I removed 13 extracted character fields (outfit, appearance, speech_style, big_five,
occupation, age_desc, lie, desires, limits, …) from a LanceDB indexer because they looked unused.
Their verdict: *"again you don't know that. you took away something that could be simply ignored but
can't be available in case we need it."*

**Why:** the two errors are not symmetrical. An unused column costs a little disk and is ignorable.
A missing column costs a **full re-index** the day someone wants it — and in that case the data was
already extracted and sitting on disk, so carrying it was nearly free. I traded a free option away
for nothing.

**The tell I missed:** I proposed the 13 columns, the operator made one remark about the model being
able to invent a description from context, and I dropped all 13. That is swinging to whatever was
said last instead of weighing the cost of being wrong in each direction. The remark was true *and*
did not imply removal.

**How to apply:** before removing or declining to capture something, ask what reversal costs. Cheap
to trim later + expensive to add later = take the longer rope. Concretely: extra columns that are
stored but not embedded change no retrieval behaviour; a wider scrape you can filter; a fuller
capture you can distill. Narrow only where the excess actually hurts — context you must read every
turn, prompts that degrade with length, spend.

Related: [[retain-source-corpus-on-first-read]] (the same asymmetry, applied to fetched sources),
[[work-style-kiss-mvp-rtfm]] (MVP limits DEPTH, never coverage — "shallow everywhere yes, missing
somewhere no"), [[stage-per-script-never-mutate]].

**Instance 2026-10-17 (a chat prototype):** I capped memories at 12 recalled, 3 per turn, mood at 40 chars, situation at
160, none of it in any spec. Operator: "what's with you and numbers? memories stay whole. they can be core memories
that stay, or weak memories that go away after X amount of time/turns. it's in the specs" (the project's memory module:
tiers by importance, timestamps, Ebbinghaus). A limit I did not read in the spec or measure is not mine to add; find
the project's model first ([[build-on-the-existing-system-not-a-replica]]), and when a count is needed take the one
the existing pipeline uses and say where it comes from.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
