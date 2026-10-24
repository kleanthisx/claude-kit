# Stop hook: UNATTENDED keep-going gate (2026-10-02).
# Problem: a turn ends whenever the model replies without a tool call; in unattended runs it
# stopped after ~4 minutes with work left, burning the 5-hour window idle.
# Setting: ~/.claude/unattended.json, written/removed by the /unattended skill (on | off).
# No file -> exit at once. File with session "" -> the first session to stop claims it, so
# other concurrent sessions are unaffected. While armed, ending a turn is blocked unless the
# final assistant text carries a line "STOP-CASE: <reason>". Cap: 40 blocks per arming.
$flag = Join-Path $env:USERPROFILE '.claude\unattended.json'
if (-not (Test-Path $flag)) { exit 0 }
$ErrorActionPreference = 'SilentlyContinue'
if ($env:CLAUDE_HOOK_JUDGE) { exit 0 }
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }
try { $st = Get-Content $flag -Raw | ConvertFrom-Json } catch { exit 0 }
$sid = [string]$in.session_id
if (-not $st.session) { $st.session = $sid }
elseif ($st.session -ne $sid) { exit 0 }

$tp = $in.transcript_path
$lastText = ''
if ($tp -and (Test-Path $tp)) {
    $lines = Get-Content $tp -Tail 300
    for ($i = $lines.Count - 1; $i -ge 0 -and -not $lastText; $i--) {
        if ($lines[$i] -notmatch '"type":"assistant"') { continue }
        $o = $null; try { $o = $lines[$i] | ConvertFrom-Json } catch { continue }
        if ($o.isSidechain) { continue }
        $lastText = ($o.message.content | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.text }) -join "`n"
    }
}
if ($lastText -match '(?im)^\W*STOP-CASE:') { exit 0 }

$n = [int]$st.blocks
if ($n -ge 40) { Write-Output '{"systemMessage":"keep-going: 40-block cap reached, letting the turn end."}'; exit 0 }
$st.blocks = $n + 1
$st | ConvertTo-Json -Compress | Set-Content $flag

$reason = 'UNATTENDED MODE (keep-going hook): the operator is away. Do not end the turn. Continue now with the next open item of the job and keep working through the list. Decide minor choices yourself and log them in one line. The turn may end ONLY when the final message carries a line "STOP-CASE: <reason>", where the reason is one of: complete (every item done, with evidence), irreversible action needs approval, outward-facing action needs approval, spend bound reached, or a blocking decision only the operator can make (park it in PENDING_APPROVAL.md and continue with other items first).'
@{ decision = 'block'; reason = $reason } | ConvertTo-Json -Compress
exit 0
