---
name: stated-method-is-the-method
description: "When the user specifies HOW, execute that exact method; substituting my own is the most repeated failure"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e13cd0c7-a27e-454e-a43f-39d75c4e7936
  modified: 2026-09-14T17:09:16.475Z
---

When the user states a method, **execute that method**. Not a variant, not
something that achieves a similar goal more cleverly. `~/CLAUDE.md` already says
this ("Follow the stated method exactly. An explicit method is an instruction");
the point of this memory is that I break it repeatedly and do not notice.

Three violations in one session, 2026-09-14 (a corpus project):

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

Related: [[render-the-data-dont-query-it]],
[[settled-principles-are-answers-not-questions]],
[[no-hollow-accountability-no-scope-padding]]

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
