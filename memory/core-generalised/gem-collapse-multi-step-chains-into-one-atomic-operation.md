---
name: gem-collapse-multi-step-chains-into-one-atomic-operation
description: "An unreliable actor (a weaker model, a human under load, a flaky script) driving a multi-step sequence WILL skip steps under pressure — make correctness independent of it remembering the chain by collapsing the sequence into one atomic operation"
metadata:
  node_type: memory
  type: feedback
---

When a procedure requires an actor to remember and execute several steps in sequence (draw a
value, then update the record, then settle the account, all at the end of a shift), and that actor
is not perfectly reliable, do not fix reliability by adding more instructions telling it to
remember the chain. Collapse the chain into ONE atomic operation the actor invokes once, that
internally performs every step.

**Why:** A turn-based simulation harness gave a language model several separate tool calls to invoke
in sequence at the end of each turn (a random draw, then a state settlement). Under a five-run stress
test, a weaker model in the loop skipped the settlement step on roughly 40-45% of turns — even
with extended reasoning enabled, it still skipped it on about 38% — because remembering to invoke
every step of a multi-call chain is exactly the kind of thing an imperfect actor drops under load.
The fix was not a better prompt: it was removing the multi-step chain's individual pieces from what
the actor could call at all, and replacing them with one atomic operation that performed the whole
sequence internally. The skip-step failure mode became structurally impossible.

**How to apply:** Whenever a procedure's correctness depends on an actor (a junior operator, a
smaller model, a script called by hand at 3am) remembering to execute every step of a multi-step
sequence, look for a way to make the whole sequence a single callable unit instead. This is a much
stronger fix than better documentation or a checklist, because a checklist can still be
under-followed under load while an atomic operation cannot be partially invoked. Applies directly
to maintenance runbooks: a "shutdown, patch, verify, restart" sequence that is four separate manual
steps will eventually have a step skipped under time pressure; a single scripted action that does
all four removes the failure mode entirely.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
