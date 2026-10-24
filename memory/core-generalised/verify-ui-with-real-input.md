---
name: verify-ui-with-real-input
description: "A UI control is verified only by real mouse/keyboard input as a user would do it; scripted el.click() proves the handler, not the control"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-02T21:25:41.938Z
---

A control counts as working only after real input (computer-tool clicks/typing on screen coordinates), operated the way the operator would, and compared against the reference doing the same thing. Scripted `el.click()` / `dispatchEvent` skips pointerdown/pointerup, :active styling, hit-testing and stacking - so it passes controls a human cannot use.

**Why:** 2026-10-02, a site-clone parity pass. PARITY.md was marked 0 CHECK / 0 MISSING with most "SAME"/"FIXED" rows proven by scripted clicks. The operator's first real walk-through (Generate's character picker) found the Gender filter dropping real clicks: motion.css scaled the pill holding the open menu, the grid painted over the menu, and the release landed on an image. Scripted clicks never press, so every check had passed. Operator: "when i said i wanted it to work exactly like the other site, what did you do? cause it's not finished."

**Even a driver click is not a human click (2026-10-03):** the browser tool's `left_click` sends mousedown + mouseup together, before any press animation runs, so a control that MOVES while held (the same motion.css press, here replacing a carousel arrow's `translateY(-50%)`) passes every driver click and fails every human one. I declared the carousel arrows fixed twice; the operator: *"it's the arrows the user will click and they are still broken."* Test press-sensitive controls with a HELD press (`left_click_drag` with start = end), and prove a cause by re-injecting the old rule and reproducing the failure, not by the fix passing.

**How to apply:** a "verified" claim about a UI names the input method. For parity work, each row = real click on theirs + real click on ours + the visible result of both. Scripted clicks are for reading state afterwards, never as the proof. Related: [[verify-moves-by-running]], [[report-verifiable-only]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
