---
name: corrections-recenter-design-not-just-feature
description: "When the user corrects INTENT (what the tool is for), re-derive defaults/emphasis/center from it — don't just implement the named feature"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b81e3c6-99b7-4543-b977-7baffd490dcd
  modified: 2026-09-08T20:25:16.438Z
---

A pipeline project's webgui, 2026-09-08: the user's first spec said "at the end of each stage I get to
drive" → stage mode became the default. They later corrected the intent: "the attempt
pauses, I ask and give feedback, I click proceed to compile... step by fucking step."
I built step mode but left stage as the default — the correction was applied to the code
path it named, not to the design's center. The user then repeatedly landed in stage mode
(default + a reload bug resetting the dropdown) and watched the tool auto-run past the
gates that were its entire point. User: "are my words without weight?"

**Why:** a correction of intent supersedes the earlier spec everywhere it's load-bearing,
not just where it points. Defaults ARE the statement of what a tool is for; leaving the
old default keeps the old purpose in charge. Signals I ignored: my own verification runs
all used step mode while the default sat at stage.

**How to apply:** when a correction changes what the user wants the tool to BE (not just
do), sweep the design for everything derived from the old statement — defaults, labels,
prominent path, docs line — and update them in the same pass. Related: [[question-mark-is-a-full-stop]],
[[work-style-kiss-mvp-rtfm]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
