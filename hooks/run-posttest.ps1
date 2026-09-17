# PostToolUse: run the project's opt-in test script after every edit.
# A project activates this by creating .claude\posttest.ps1 in its root. Exit 2 wakes the model with the failure.
$ErrorActionPreference = 'SilentlyContinue'
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }
$cwd = if ($in.cwd) { $in.cwd } else { (Get-Location).Path }
$script = Join-Path $cwd '.claude\posttest.ps1'
if (-not (Test-Path $script)) { exit 0 }
$outp = & $script 2>&1 | Out-String
$code = $LASTEXITCODE
if ($code -ne 0) {
    $tail = if ($outp.Length -gt 4000) { $outp.Substring($outp.Length - 4000) } else { $outp }
    Write-Output ("POSTTEST FAILED (exit ${code}) after that edit - fix the regression before building further. Output tail:`n" + $tail)
    exit 2
}
exit 0
