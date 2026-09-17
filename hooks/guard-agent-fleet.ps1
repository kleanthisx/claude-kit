# PreToolUse gate: fleet-scale Agent spawning -> interactive ask (blast-radius bound).
#
# Closes the gap documented in README.md ("single Agent calls are ungated ... if a new
# orchestration surface appears, gate it the same day"). guard-launch-gate.ps1 covers the
# Workflow tool; N individual Agent calls walked straight past it. 2026-08-11: 12 parallel
# Agent calls, each told to read 8-10 web sources, produced ~100 allow/deny prompts on the
# user's screen and returned zero results. Bounds were set on words, sources and model tier
# -- never on the user-facing interruption count.
#
# Design: does NOT gate individual subagents (that is the alarm-fatigue anti-pattern the
# README warns about). It gates ACCUMULATION -- 1-3 agents in a window pass silently, the
# 4th+ asks. Append-only per-session log so concurrent spawns in one message still count.
$ErrorActionPreference = 'SilentlyContinue'
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }

$THRESHOLD  = 3    # spawns allowed silently inside the window
$WINDOW_MIN = 15

$cwd = if ($in.cwd) { $in.cwd } else { (Get-Location).Path }

# Escape hatch, same idiom as guard-launch-gate's LAUNCH.md: pre-approve a batch.
$fleet = Join-Path $cwd 'FLEET.md'
if (Test-Path $fleet) {
    if ((Get-Content $fleet -Raw) -match 'APPROVED:\s*GO') { exit 0 }
}

$sid = if ($in.session_id) { $in.session_id } else { 'nosession' }
$sid = ($sid -replace '[^A-Za-z0-9\-_]', '_')
$dir = Join-Path $env:USERPROFILE '.claude\hooks\.agent-fleet'
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
$log = Join-Path $dir "$sid.log"

$now = Get-Date

# Prune stale session logs (>1 day). Scoped to *.log inside this dedicated directory.
Get-ChildItem $dir -Filter '*.log' | Where-Object { $_.LastWriteTime -lt $now.AddDays(-1) } | Remove-Item -Force

# Count prior spawns still inside the window. Append-only log tolerates concurrent writers.
$prior = 0
if (Test-Path $log) {
    foreach ($line in (Get-Content $log)) {
        $t = [DateTime]::MinValue
        if ([DateTime]::TryParse($line, [ref]$t)) {
            if ($t -gt $now.AddMinutes(-$WINDOW_MIN)) { $prior++ }
        }
    }
}

# Record this attempt (retry briefly on write contention from parallel spawns).
for ($i = 0; $i -lt 5; $i++) {
    try { Add-Content -Path $log -Value $now.ToString('o') -ErrorAction Stop; break }
    catch { Start-Sleep -Milliseconds 40 }
}

$n = $prior + 1
if ($n -le $THRESHOLD) { exit 0 }

# Blast-radius estimate read from the agent's own prompt, not from the model's description.
$p = [string]$in.tool_input.prompt
$perAgent = 0
if ($p -match '(?i)(\d+)\s*(?:-|to|–)\s*(\d+)\s*sources') { $perAgent = [int]$Matches[2] }
elseif ($p -match '(?i)(?:at most|up to|read)\s*(\d+)\s*sources') { $perAgent = [int]$Matches[1] }
elseif ($p -match '(?i)websearch|webfetch|search the web|\bsources\b|\bfetch\b') { $perAgent = 10 }

$est = ''
if ($perAgent -gt 0) {
    $est = " Worst case ~$($n * $perAgent) allow/deny prompts if each agent hits new domains."
}

$reason = "FLEET GATE: Agent spawn #$n in the last $WINDOW_MIN min (silent threshold $THRESHOLD).$est " +
          "On 2026-08-11 twelve parallel Agent calls produced ~100 permission prompts, were killed by hand, and returned nothing. " +
          "Before continuing, state out loud: (1) the worst-case user-facing interruption count, " +
          "(2) the coverage mechanism -- an externally-sourced denominator or planned saturation -- since N agents on N disjoint lanes yield N samples of an unknown and no way to detect coverage. " +
          "To pre-approve a batch, add a line 'APPROVED: GO' to $cwd\FLEET.md."

$out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'ask'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
Write-Output $out
exit 0
