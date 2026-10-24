---
name: unattended
description: Operator-only switch for unattended mode. "/unattended on" arms the keep-going Stop hook for this session; "/unattended off" disarms it.
disable-model-invocation: true
---

# /unattended on | off

The argument is `$ARGUMENTS`.

- **on** — run exactly this, then continue the current job:
  `powershell -NoProfile -Command "Set-Content -Path $env:USERPROFILE\.claude\unattended.json -Value '{\"session\":\"\",\"blocks\":0}'"`
  From now on `~/.claude/hooks/keep-going.ps1` blocks every turn end in this session unless the final
  message has a line `STOP-CASE: <reason>` (complete with evidence / irreversible / outward-facing /
  spend bound / operator-only decision parked in PENDING_APPROVAL.md). Work the whole list.
- **off** — run exactly this, then answer normally:
  `powershell -NoProfile -Command "Remove-Item $env:USERPROFILE\.claude\unattended.json -ErrorAction SilentlyContinue"`
- anything else — reply with one line: `usage: /unattended on | off`.

Report in one line: `unattended: on` or `unattended: off`, with the command's exit code.
