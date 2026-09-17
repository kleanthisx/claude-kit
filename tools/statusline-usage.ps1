# Statusline: display SERVER ground-truth usage limits + append changes to the ledger.
# Data source: Claude Code pipes statusline JSON incl. rate_limits (5h/7d used %, resets_at)
# during active sessions — the only officially supported path to subscription limit status.
# Zero model involvement per reading.
#
# Ledger path resolution (most specific wins): -LedgerPath param > $env:CLAUDE_USAGE_LEDGER >
# <CLAUDE_HOME>/usage-ledger.log, where CLAUDE_HOME is $env:CLAUDE_HOME or "$env:USERPROFILE\.claude".
# Claude Code invokes a statusLine command with no arguments, so the env-var override is the
# practical way to point this at a different file without editing the script.
param(
    [string]$LedgerPath = ''
)
$ErrorActionPreference = 'SilentlyContinue'

if (-not $LedgerPath) {
    if ($env:CLAUDE_USAGE_LEDGER) {
        $LedgerPath = $env:CLAUDE_USAGE_LEDGER
    } else {
        $claudeHome = if ($env:CLAUDE_HOME) { $env:CLAUDE_HOME } else { Join-Path $env:USERPROFILE '.claude' }
        $LedgerPath = Join-Path $claudeHome 'usage-ledger.log'
    }
}

try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }

$model = $in.model.display_name
$rl = $in.rate_limits
$fiveH = $rl.five_hour.used_percentage
$sevenD = $rl.seven_day.used_percentage

if ($null -eq $fiveH -and $null -eq $sevenD) {
    Write-Output "$model | limits: n/a yet"
    exit 0
}

$parts = @()
if ($null -ne $fiveH) {
    $r5 = if ($rl.five_hour.resets_at) { ([DateTimeOffset]::FromUnixTimeSeconds([long]$rl.five_hour.resets_at)).ToLocalTime().ToString('HH:mm') } else { '?' }
    $parts += "5h: $([math]::Round($fiveH))% (reset $r5)"
}
if ($null -ne $sevenD) {
    $r7 = if ($rl.seven_day.resets_at) { ([DateTimeOffset]::FromUnixTimeSeconds([long]$rl.seven_day.resets_at)).ToLocalTime().ToString('ddd HH:mm') } else { '?' }
    $parts += "7d: $([math]::Round($sevenD))% (reset $r7)"
}
$line = "$model | " + ($parts -join ' | ')
Write-Output $line

# Ledger: append only on CHANGE (dedupe via state file) — server truth, no spam.
$ledgerDir = Split-Path $LedgerPath -Parent
if ($ledgerDir -and -not (Test-Path $ledgerDir)) { New-Item -ItemType Directory -Force -Path $ledgerDir | Out-Null }
$state = Join-Path $env:TEMP 'claude-usage-last.txt'
$snapshot = "$([math]::Round($fiveH))|$([math]::Round($sevenD))"
$last = if (Test-Path $state) { Get-Content $state -Raw } else { '' }
if ($snapshot -ne $last.Trim()) {
    Add-Content $LedgerPath ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | 5h: ' + [math]::Round($fiveH) + '% | 7d: ' + [math]::Round($sevenD) + '%')
    Set-Content $state $snapshot -NoNewline
}
exit 0
