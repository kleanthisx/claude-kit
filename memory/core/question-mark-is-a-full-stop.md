---
name: question-mark-is-a-full-stop
description: "When the user's message ends in a question to me, answer it and end the turn — wait for their next message before acting"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cd191791-1c12-4340-a661-8cbdfbe32781
  modified: 2026-08-11T15:16:28.001Z
---

*(Written as requirements, not prohibitions — see [[instruction-decay-evidence]].)*

**When the user's message ends in a question directed at me — "do you understand?", "are you with me?", "make sense?" — state the answer and end the turn.** Wait for a fresh user message before taking any action.

- **Treat "do you understand?" as a request to state my understanding back.** It signals doubt that the message landed, and it is usually checking that the *particulars* landed, not the general intent.
- **Treat instructions about HOW as separate from permission to START.** "Run a wide breadth", "go deep" describe shape; they wait on a go.
- **Treat my own unanswered proposal as still pending.** If I proposed 6 agents and got no answer, 6 remains unapproved — and 12 is further from approved, not closer.
- **In research, think alongside the user.** They drift because they don't have the structure yet; that drift *is* the work. Contribute ideas cheaply in the conversation rather than extracting a spec and executing it.

**Why:** 2026-08-11 — the user's message ended "you understand?" I answered it and launched 12 background research agents in the same message. They never got the chance to say "no, you've got it wrong" before ~100 permission prompts hit their screen.

**How to apply:** Question mark aimed at me → reply, stop, hand the floor back. See [[w-questions-before-actions]], [[bound-the-user-facing-blast-radius]].
