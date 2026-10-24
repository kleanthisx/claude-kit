# PreToolUse hook (all tools, main session + subagents): usage pause gate (2026-10-02).
# Reads ~/.claude/usage-state.json (written by statusline-usage.ps1 from the server's rate_limits).
# If the 5h or 7d limit is at/above the threshold and its reset is still ahead, the tool call
# SLEEPS until reset + 60 s, then proceeds -- every agent pauses in place, no tokens spent.
# Threshold: env CLAUDE_USAGE_PAUSE_PCT, default 98. A stale reading whose reset already passed is ignored.
$state = if ($env:CLAUDE_USAGE_STATE) { $env:CLAUDE_USAGE_STATE } else { Join-Path $env:USERPROFILE '.claude\usage-state.json' }
if (-not (Test-Path $state)) { exit 0 }
try { $u = Get-Content $state -Raw | ConvertFrom-Json } catch { exit 0 }
$limit = if ($env:CLAUDE_USAGE_PAUSE_PCT) { [double]$env:CLAUDE_USAGE_PAUSE_PCT } else { 98 }
$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$wake = 0; $which = ''
foreach ($k in @('five_hour', 'seven_day')) {
    $pct = $u.$k; $rs = $u."${k}_resets_at"
    if ($null -ne $pct -and $rs -and [double]$pct -ge $limit -and [long]$rs -gt $now) {
        if ([long]$rs -gt $wake) { $wake = [long]$rs; $which = "$k at $pct%" }
    }
}
if ($wake -eq 0) { exit 0 }
$secs = $wake - $now + 60
Add-Content (Join-Path $env:USERPROFILE '.claude\hooks\usage-gate.log') ("$(Get-Date -Format s) pause $which, sleeping ${secs}s")
Start-Sleep -Seconds $secs
Add-Content (Join-Path $env:USERPROFILE '.claude\hooks\usage-gate.log') ("$(Get-Date -Format s) resume")
Write-Output ('{"systemMessage":"usage-gate: paused ' + $secs + 's for ' + $which + ', resumed after reset."}')
exit 0
