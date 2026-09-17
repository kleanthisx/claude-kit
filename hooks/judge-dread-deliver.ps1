# JUDGE DREAD -- early delivery, wired to UserPromptSubmit.
#
# THE PROBLEM THIS FIXES. Judging happens in a detached worker, so a verdict on
# turn N lands a few seconds after turn N ends -- while the user is still reading
# it. But hooks only speak on events, and the delivery half lives in the Stop
# hook, so the verdict was not shown until the END OF TURN N+1. The user waited
# through an entire extra turn to hear about the one before it.
#
# UserPromptSubmit is the first event after that Stop. Delivering here shows the
# verdict the instant the user sends their next message, and puts it in the
# assistant's context BEFORE it answers, rather than after.
#
# WHAT IT DOES NOT DO: push anything while the user simply sits and reads. There
# is no mechanism for that -- a hook cannot speak without an event, and the
# earliest event available is this one.
#
# ENFORCEMENT IS NOT WEAKENED. A FAITHFUL or a could-not-rule notice is consumed
# here, because there is nothing to enforce. A BLOCK is shown but deliberately
# LEFT ON DISK, so the Stop hook still blocks at the end of the turn. Early
# sight, same teeth.
$ErrorActionPreference = 'SilentlyContinue'
if ($env:CLAUDE_HOOK_JUDGE) { exit 0 }
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }

$ESC = [char]27
function Paint { param($code, $text) return "$ESC[38;5;${code}m$text$ESC[0m" }
function Emit { param($o)
    $j = $o | ConvertTo-Json -Compress
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $j.ToCharArray()) {
        if ([int]$ch -gt 126) { [void]$sb.AppendFormat('\u{0:x4}', [int]$ch) } else { [void]$sb.Append($ch) }
    }
    [Console]::Out.Write($sb.ToString())
}

$mode = 'verbose'
try {
    $st = Get-Content (Join-Path $PSScriptRoot 'judge-state.json') -Raw | ConvertFrom-Json
    if ($st.mode) { $mode = $st.mode }
} catch { }
if ($mode -eq 'off') { exit 0 }

$sid = if ($in.session_id) { $in.session_id } else { 'default' }
$dir = Join-Path $env:TEMP "shadowguard\$sid"
$outFile = Join-Path $dir 'verdict.txt'
$lockFile = Join-Path $dir 'inflight.lock'

if (-not (Test-Path $outFile)) {
    # Nothing ready. Say so ONLY if he is still working, so the user knows a
    # verdict is coming rather than wondering whether he ran at all.
    if (Test-Path $lockFile) {
        $age = [int]((Get-Date) - (Get-Item $lockFile).LastWriteTime).TotalSeconds
        Emit @{ systemMessage = (Paint 137 "JUDGE DREAD: still reading your previous turn (${age}s).") }
    }
    exit 0
}

$line = ([IO.File]::ReadAllText($outFile)).Trim()
$prev = ''
$askFile = Join-Path $dir 'lastask.txt'
if (Test-Path $askFile) { $prev = ([IO.File]::ReadAllText($askFile)).Trim() }
$ctx = if ($prev) { " (`"$prev`")" } else { '' }

if ($line -match '(?i)^\s*(UNBACKED|SUBSTITUTED|OMITTED)') {
    # Shown now, NOT consumed -- the Stop hook still blocks on it.
    $msg = 'JUDGE DREAD has ruled on your previous message' + $ctx + ' and it FAILS: ' +
           ($line -replace '"', "'") + ' -- this will block at the end of this turn; address it first.'
    Emit @{ systemMessage = (Paint 131 $msg)
            hookSpecificOutput = @{ hookEventName = 'UserPromptSubmit'; additionalContext = $msg } }
    exit 0
}

Remove-Item -LiteralPath $outFile -Force -ErrorAction SilentlyContinue
if ($line -match '(?i)^\s*FAITHFUL') {
    if ($mode -ne 'quiet') {
        Emit @{ systemMessage = (Paint 108 ('This is Judge Dread and I approve the previous message' + $ctx + '.')) }
    }
} elseif ($line -eq 'UNAVAILABLE') {
    Emit @{ systemMessage = (Paint 137 'JUDGE DREAD: judge unavailable (out of tokens, or the CLI failed) - previous turn NOT audited.') }
} else {
    Emit @{ systemMessage = (Paint 137 'JUDGE DREAD: malformed verdict - previous turn NOT audited.') }
}
exit 0
