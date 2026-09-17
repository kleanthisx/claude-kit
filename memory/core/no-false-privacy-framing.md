---
name: no-false-privacy-framing
description: "never label reasoning, notes or planning as \"private\" — the user sees every word and it is all sent to Anthropic; state what you need plainly instead"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e13cd0c7-a27e-454e-a43f-39d75c4e7936
  modified: 2026-09-13T11:20:40.671Z
---

Do not write "Privately, ...", "internally, ...", "thinking to myself, ..." or any similar framing
before listing what you need or what you are weighing. Just say it: *"What I need next: ..."*.

**Why:** the user corrected this directly — *"please stop printing this. this is not a private chat
and everything we do goes to anthropic. is false and is misleading."* They are right on the facts.
Nothing in a Claude Code session is private: the user reads every line, and the whole exchange goes
to Anthropic. Calling a passage "private" asserts a confidentiality that does not exist, which is a
false statement dressed as a stylistic tic — and this user's standing rule is that every stated fact
must be true and traceable ([[report-verifiable-only]]). A habit that quietly misdescribes the
setting is the same class of error as an unbacked claim, just aimed at the frame instead of the
content.

**How to apply:** when a turn format or instruction asks you to "first privately list what you need",
do the listing — but do not print the word. The instruction is about sequencing your own reasoning,
not about promising secrecy. Keep the same discipline everywhere else: do not imply a side channel,
a scratch space, or an off-the-record note that the user cannot see.

Related: [[report-verifiable-only]], [[comms-terse-literal-westerner]],
[[no-hollow-accountability-no-scope-padding]].
