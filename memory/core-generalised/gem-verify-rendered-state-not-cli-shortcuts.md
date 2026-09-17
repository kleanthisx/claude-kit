---
name: gem-verify-rendered-state-not-cli-shortcuts
description: "A convenience CLI flag for checking rendered/visual state (a --window-size screenshot flag, a headless capture shortcut) can silently misrepresent reality — verify through the real rendering path, not the shortcut"
metadata:
  node_type: memory
  type: feedback
---

When verifying how something actually renders or behaves at runtime, prefer the real mechanism
(true viewport/device emulation, an actual client) over a CLI convenience flag that approximates
it — the approximation can silently diverge from the real thing and produce a false reading.

**Why:** Verifying a responsive layout on two separate builds (2026-07), a `--window-size`
screenshot flag was used to check the mobile view. It quietly floors the emulated width in
headless mode, producing screenshots that showed false clipping that was never present for a real
device. Switching to true device-metric emulation (setting the actual viewport dimensions the
browser reports to the page, not just the screenshot size) produced the correct result. The same
gotcha showed up independently on a second, unrelated build using the same verification shortcut —
it is a property of the flag, not a one-off fluke.

**How to apply:** Before trusting an automated visual/state check — a health-check screenshot, a
"is the dashboard rendering" probe, a synthetic browser test — confirm the check exercises the
real code path (real viewport, real client, real request) rather than a flag or shortcut that
approximates it. If a check's result looks surprising (unexpected clipping, a metric that "looks
wrong"), suspect the verification method itself before the thing being verified — cheap flags
that mimic reality are a common source of false alarms and false passes alike in any automated
monitoring or QA pipeline.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
