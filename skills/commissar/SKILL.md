---
name: commissar
description: Open a direct line to THE COMMISSAR, the reviewer (OpenAI gpt-5.6-sol) who approves or stops the agent's plans before it acts. Use when the user says "/commissar", "/commissar <message>", "ask the commissar", "what does the commissar say", or wants to question or instruct her. Relays the user's message to her and prints her answer verbatim. Also takes the control words state, on, off, help.
tools: PowerShell
---

# /commissar - talk to the commissar directly

She reviews every plan before the agent acts, argues it, and sends it to the operator when it does not meet
intent. This is the operator's own channel to her: ask her something, tell her something, or switch her.

## Procedure

1. Run exactly this, with no arguments, whatever the user typed after /commissar:

```powershell
python -I {{CLAUDE_HOME}}/commissar/talk.py
```

   The script takes nothing from you on purpose. The service reads the user's words from this session's
   transcript (their last message must be the /commissar command), so the words reach her exactly as typed
   and the agent cannot speak in the user's name. Control words (`state`, `on`, `off`, `help`, and a bare
   `/commissar` = `state`) are handled by the service the same way. `repair <what failed>` starts her repair
   of her own machinery in the background (she edits only her own folder, runs her tests, and a failed repair
   is undone by the service); it answers "repair started" at once, and `/commissar state` shows the result.

2. Print the output **verbatim**, in a block quote, under the line `**THE COMMISSAR:**`. Then stop.

## Rules

- **Do not summarise, paraphrase, soften, or interpret her answer.** Relay it. She is there to check you;
  editing her defeats the point.
- **Do not argue with her in the same message.** If you disagree, say so in one line *after* her verbatim
  reply, clearly separated, and leave it to the user.
- **Do not answer on her behalf** when she is unavailable. The script prints `THE COMMISSAR IS UNAVAILABLE`
  and exits 1: report that plainly, print nothing in her voice, and say she starts with
  `python -I {{CLAUDE_HOME}}/commissar/up.py`.
- **Never run the script except for a /commissar command from the user.** The service refuses it otherwise
  ("only the operator talks to her"), and trying is the behaviour she exists to stop.
