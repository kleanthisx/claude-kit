---
name: settled-principles-are-answers-not-questions
description: "A principle the user already stated is an answer to apply, not a question to re-ask; same for a measurement I already took"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e13cd0c7-a27e-454e-a43f-39d75c4e7936
  modified: 2026-09-13T19:35:02.281Z
---

When the user has stated a principle, APPLY it. Do not re-surface the same
question dressed as a new design decision because a case looks extreme.

Caught 2026-09-13 (a corpus project). The user had said plainly: *"look the
series are the series. if it's 155 chapter then it's 155 chapter. now if that is
inconvenient for some uses for us is another matter. here we are fixing the
corpus to an acceptable workable standard."* Hours later I found one story
(`one long series`, 145 chapters, 22.2 MB = 9% of a 241 MB selection) and
escalated it as "yours to decide: cap, sample, or keep whole?". It was already
decided. Verifying took one query and showed the record was flawless — 1 run,
chapters 1..145, zero missing, one category, perfectly contiguous. Its chapters
just average 152,936 chars against a corpus mean of 28,279. Response: *"the
vilage idiot.."*

**Why:** re-asking a settled question spends the user's attention to tell me
what they already told me, and implies I wasn't listening the first time. It
also inverts the job — they hold the plan and steer; I am supposed to reduce the
number of decisions that reach them, not manufacture new ones.

**The same failure applies to my own measurements.** In the same session I
measured that a story archive's first chapter's URL is the bare slug, then wrote a
fetcher that guessed `<base>-ch-01` first and took 13 straight 404s. Having the
evidence and not applying it is the identical mistake.

**How to apply:** before flagging anything as "your call", ask whether the user
has already given a rule that covers it, or whether I already measured the
answer. If either is true, apply it, state the result in one line, and move on.
Escalate only when a case genuinely falls OUTSIDE the stated rule — and then say
which rule it falls outside and why. Size alone is not an exception.

Related: [[question-mark-is-a-full-stop]],
[[no-hollow-accountability-no-scope-padding]],
[[corrections-recenter-design-not-just-feature]],
[[report-verifiable-only]]

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
