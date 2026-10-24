---
name: finish-the-defect-class-not-the-instance
description: "Fix every place a defect appears before reporting; stopping at the first visible improvement is the repeat failure the operator calls \"half this half that\""
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-04T11:17:17.654Z
---

When a defect is found, the unit of work is **the defect CLASS across the whole surface**, not the
one instance that was pointed at. Enumerate every place it appears FIRST, fix the set, then report.
Never report "done" on the strength of the first visible improvement.

Operator, 2026-10-01, after a night of it: *"only half-fixed... half this half that..."* and, earlier
the same night, *"another half assed job left mid work and no reference to it to be found"* and
*"are you sure you finished generate?"* (I was not, and had implied I was).

**Why:** a half-fix is worse than none. It *looks* addressed, so it stops being on anyone's list,
and the operator has to re-find it — which is the expensive part, and it lands on them. Five
instances in one session, all the same shape:

| pointed at | fixed | left broken |
|---|---|---|
| option tiles showed arbitrary photos | the PICKER grid | the selected preset CARD, still `poolImg` |
| filter menus unreadable | the 3 clipped menus | never audited the page's other 20 controls |
| "finish the Generate page" | 3 defects | 🖼/🎬 Video toggle is a no-op |
| video playback test | mount + manifest | the test page itself; no record until told |
| media download | images | videos not started |

**How to apply:**
1. Before editing, grep the codebase for the defect's *shape*, not its symptom — `poolImg(` for
   "wrong art", `alignRight` for "clipped menu", `state0.X` read-nowhere for "dead control".
2. Write the full hit list as a checklist before the first edit. Coverage is the deliverable;
   depth is what gets cut when time is short.
3. A control is not verified by reading CSS — operate it. 21 of 23 controls had handlers, and one
   of them still did nothing.
4. If something must be parked, it is written into the task board / entity with its exact state in
   the same breath — an unrecorded parked job is a lost job.

**Second form, 2026-10-04 (an RP project playtest):** after 3 rounds of defect lists I proposed a
per-defect fix table; operator: *"Needs a model. Case by case is a dead end"*. A playtest report
lists SYMPTOMS. Before any fix table, classify every symptom by the mechanism that produces it
(which component owns which fact, who may change state) and fix the mechanism. A fix list with one
row per symptom is the instance-level work this file forbids, one level up.

Sits under [[work-style-kiss-mvp-rtfm]] (complete in every aspect) and
[[no-hollow-accountability-no-scope-padding]]. Distinct from both: those govern how much to build.
This one governs when I am allowed to say it is finished.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
