---
name: unattended-defer-gated-ops
description: "When the user is away, never seize on an approval gate — restructure to avoid it, or mark the destructive/gated op to PENDING_APPROVAL.md, keep progressing, present the batch on return (user, 2026-08-10)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4f3c9365-4917-40c1-834e-8ee9a0d8e6e0
  modified: 2026-08-10T07:34:21.538Z
---

User order, 2026-08-10 (after the overnight pilot-integration stall): an approval
gate hit while the user is away seizes ALL progress from that point — the run sits
waiting for an approval nobody is there to give, and 8 hours of unattended time
becomes 8 hours of zero progress.

**The rule is NOT "never delete."** I first over-read it that way; the user
corrected: "it's not never delete. it's that the gate will get you stuck and no
progress from then on. mark them and you tell me to approve when i get back." The
actual rule — during unattended operation, never let a destructive/gated op block:

1. **Restructure to avoid the gate** where possible — e.g. folder-per-run
   (`runs/<name>/<NNN>/`) instead of deleting/overwriting, so the run never needs a
   delete to proceed. See [[ops-ticket-protocol]].
2. **Where a destructive op is genuinely needed, defer it:** mark it to a
   `PENDING_APPROVAL.md` list, skip it, keep progressing on everything else, and tell
   the user the batch is waiting when they return.

**Why it matters (and the related design point):** the user also generalized — you
can't make a harness idiot-proof against the model under test: "make something
idiot-proof, nature builds a better idiot; tighten a harness and a model finds
another way to fuck it up." So build for robustness-to-misbehavior + grading, not
prevention. A cage that blocks on every gate is worst of all when nobody's watching.

**How to apply:** when the user says they're leaving, audit the unattended path for
any op that would surface an approval prompt (deletes, overwrites, process-stops) and
either design it out or wire it to defer-and-mark BEFORE they go. Relates to
[[report-verifiable-only]] (tell them plainly what's pending) and
[[session-start-recite-directives]].
