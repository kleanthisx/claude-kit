---
name: gem-delegate-interactive-auth-to-the-human
description: "An interactive login/auth flow (device code, browser OAuth, MFA prompt) is not something an agent should drive itself — hand it to the human via a backgrounded prompt and read back only the resulting output"
metadata:
  node_type: memory
  type: feedback
---

When a CLI tool's authentication step is interactive by design (opens a browser, prints a
one-time device code, waits for a human to approve), do not try to script around it or fake
the interaction. Start it in a way the human can see and complete themselves, then read back
only the result.

**Why:** Setting up a CLI tool's auth (2026-08-01), the login command was interactive by design.
The working pattern was to run it as a backgrounded, human-visible prompt (so the terminal
output — including a device code — was captured to a file) and hand the user the code from that
file, rather than attempting to complete the OAuth dance programmatically. The same session also
hit a plainer trap: the tool had been installed via a package manager but was not on the default
shell's PATH, so an early attempt to run it looked like "not installed" when it was actually just
not visible from that shell.

**How to apply:** For any credential or access step that is intentionally gated behind human
interaction (SSO, device-code flows, hardware-key MFA, an approval click), start the process,
surface its output to the human, and let them complete the interactive part — never attempt to
automate past an intentional human-in-the-loop gate. Separately: when a tool "isn't found," check
whether it was installed for a different shell/PATH before concluding it is missing — a package
manager can install a tool without adding it to every shell's PATH, and that misdiagnosis wastes
time chasing a reinstall that was never needed. Both are common failure points in any
sysadmin/investigation workflow that scripts around real tools rather than owning them outright.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
