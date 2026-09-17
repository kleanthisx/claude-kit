# PreToolUse gate: if PLAN.md exists in the project and is not approved, block edits (Protocol B).
# Arms itself when a PLAN.md is created; disarms when it contains "APPROVED: GO" or is deleted.
$ErrorActionPreference = 'SilentlyContinue'
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }
$cwd = if ($in.cwd) { $in.cwd } else { (Get-Location).Path }
$plan = Join-Path $cwd 'PLAN.md'
if (-not (Test-Path $plan)) { exit 0 }
$target = $in.tool_input.file_path
if ($target -and ((Split-Path $target -Leaf) -ieq 'PLAN.md')) { exit 0 }
$content = Get-Content $plan -Raw
if ($content -match 'APPROVED:\s*GO') { exit 0 }
$reason = 'PLAN.md exists but is not approved (no "APPROVED: GO" line). Protocol B: present the plan and wait for the user to say GO; then add the line "APPROVED: GO" to PLAN.md and proceed. The user can also delete PLAN.md to disarm this gate.'
$out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
Write-Output $out
exit 0
