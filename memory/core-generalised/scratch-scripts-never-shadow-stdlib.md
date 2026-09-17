---
name: scratch-scripts-never-shadow-stdlib
description: "Write throwaway Python into the session scratchpad, never %TEMP%, and never name one after a stdlib module"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e13cd0c7-a27e-454e-a43f-39d75c4e7936
  modified: 2026-09-14T11:54:30.956Z
---

Python puts the **script's own directory** on `sys.path`. Writing throwaway
scripts into `%TEMP%` therefore makes every file there importable, and any file
named after a stdlib module shadows the real one for every later script run from
that directory.

Caught 2026-09-13/14 (a corpus project). Scratch files named `inspect.py` and
`struct.py` sat in `%TEMP%`. Symptoms, neither of which pointed at the cause:

- `import pyarrow` died deep inside numpy with
  `AttributeError: module 'inspect' has no attribute 'cleandoc'`
- unrelated commands printed a stale `saved pages: 10911` block **before** their
  own output — `struct.py` was executing whenever anything imported `struct`,
  and its printed row count tracked a directory that was still growing, which
  made it look like a live background job

**Why it matters:** the failure surfaces far from the cause, in third-party code,
and looks like a broken package or a phantom background process. I lost time
suspecting both.

**How to apply:** put scratch scripts in the session scratchpad directory named
in the system prompt, not `%TEMP%`. Give them task-specific names
(`tagaudit.py`, `locate_test.py`), never a bare stdlib name — `inspect`,
`struct`, `types`, `json`, `csv`, `glob`, `random`, `time`, `copy`, `string`,
`select`, `signal`, `socket`, `queue`, `statistics`, `calendar`, `array`,
`platform`, `operator`, `secrets`, `token`, `code`. If an import fails absurdly
inside a library, check for a shadowing file before debugging the library.

Related: [[verify-against-authority-not-recall]],
[[one-change-per-run-subtract-to-find-fault]]

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
