---
name: judge
description: Open a direct line to JUDGE DREAD, the adversarial auditor that rules on every turn. Use when the user says "/judge", "/judge <question>", "ask dread", "ask the judge", "what does dread say", or wants to question a verdict he gave. Relays the user's message to him and prints his answer verbatim.
tools: PowerShell
---

# /judge — talk to Judge Dread directly

The Stop hook allows Dread one sentence per turn and only three things to say.
This is the other channel: the user asks him something, he answers in his own
words.

## Procedure

0. **Check for a control word first.** Strip a leading `:` and whitespace. If
   what remains is exactly one of `help`, `state`, `off`, `on`, `quiet`,
   `verbose` (case-insensitive), it is a switch, not a question — run:

```powershell
& powershell -NoProfile -ExecutionPolicy Bypass -File $env:USERPROFILE\.claude\hooks\judge-dread-ctl.ps1 -Action <word>
```

   Print that output verbatim in a fenced block and stop. Do **not** send control
   words to him as questions, and do not paraphrase the result — `state` in
   particular is the answer to "is anything actually guarding me", so it is
   relayed exactly, including the OFF warning.

   Bare `/judge` with no argument runs `-Action state`.

1. Otherwise it is a message for him. If it is empty, ask what they want to ask —
   do not invent a question.

2. Run, with the message passed as a single argument:

```powershell
& powershell -NoProfile -ExecutionPolicy Bypass -File $env:USERPROFILE\.claude\hooks\judge-dread-ask.ps1 -Message '<the user message>' -SessionId '<this session id, if known>'
```

   Single-quote the message and double any internal single quotes. Do not
   reformat, correct, translate or "clean up" what the user wrote — including
   typos and gibberish. He gets it exactly as typed.

3. Print his reply **verbatim**, in a block quote, under the line
   `**JUDGE DREAD:**`. Then stop.

## Rules

- **Do not summarise, paraphrase, soften, or interpret his answer.** Relay it.
  He is adversarial to you specifically; editing him defeats the point.
- **Do not argue with him in the same message.** If you disagree, say so in one
  line *after* his verbatim reply, clearly separated, and leave it to the user.
- **Do not answer on his behalf** when he is unavailable. The script prints
  `JUDGE DREAD IS UNAVAILABLE` and exits 1 — report that plainly and print
  nothing in his voice.
- He has Read, Grep and Glob and will open his own charter files before
  answering questions about his rules. Expect him to contradict how you have
  described them. That is the feature.
