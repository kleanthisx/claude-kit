# JUDGE DREAD -- the control switches.
#
# Three modes, and the hook reads this file on every turn:
#   verbose  DEFAULT. He audits and he speaks: green on approval, red on a block,
#            amber when he could not rule.
#   quiet    He audits exactly the same and blocks exactly the same. Only the
#            green approval line is suppressed. Amber still speaks -- "quiet"
#            means stop congratulating me, not stop telling me you are broken.
#   off      He does not run at all.
#
# OFF IS THE DANGEROUS ONE and it is built to be hard to forget: the hook prints
# one amber line on the FIRST turn of each session while off, so a switch thrown
# on Monday cannot quietly still be off on Friday. Once per session, not once per
# turn -- a warning nobody reads is the same as no warning.
#
# State is kept beside the hook rather than in TEMP so it survives a temp sweep
# and a reboot. The mode is a deliberate user act; it should not evaporate.
param([string]$Action = 'state')

$ErrorActionPreference = 'SilentlyContinue'
$stateFile = Join-Path $PSScriptRoot 'judge-state.json'

function Get-State {
    if (Test-Path $stateFile) {
        try { return (Get-Content $stateFile -Raw | ConvertFrom-Json) } catch { }
    }
    return [pscustomobject]@{ mode = 'verbose'; prev = 'verbose'; changed = '' }
}
function Set-State { param($mode, $prev)
    $o = [pscustomobject]@{ mode = $mode; prev = $prev; changed = (Get-Date).ToString('yyyy-MM-dd HH:mm') }
    $o | ConvertTo-Json -Compress | Set-Content -Path $stateFile -Encoding ascii
    return $o
}

$s = Get-State
switch ($Action.ToLower()) {

    'help' {
        @"
JUDGE DREAD -- commands

  /judge <anything>   Ask him directly. He answers in his own words, verbatim.
                      He reads his own charter files before answering about his
                      rules, so he will contradict the assistant if it misstates
                      them.

  /judge help         This list.
  /judge state        What mode he is in, when it changed, and his last verdict.

  /judge off          Stop auditing entirely. He does not run.
  /judge on           Resume, in whichever mode was active before off.
  /judge quiet        Keep auditing and blocking; drop the green approval line.
  /judge verbose      The default. Speak on every outcome.

What each mode still does:
                         blocks a bad turn   green approval   'could not rule'
  verbose (default)            yes                yes              yes
  quiet                        yes                no               yes
  off                          no                 no               once/session

He is four checks: unbacked claims (figures count), substituted method,
fabricated or circular evidence, and reports that are true clause by clause but
leave the failure out.
"@
    }

    'state' {
        $sess = Join-Path $env:TEMP 'shadowguard'
        "mode          : $($s.mode)" + $(if ($s.mode -eq 'verbose') { '   (default)' } else { '' })
        "changed       : " + $(if ($s.changed) { $s.changed } else { 'never - running on the default' })
        "state file    : $stateFile"
        if ($s.mode -eq 'off') {
            ""
            "*** DREAD IS OFF. NOTHING IS AUDITING THIS SESSION. ***"
            "    Turn him back on with /judge on"
        } elseif ($s.mode -eq 'quiet') {
            ""
            "Quiet: he still audits and still blocks. You will not see approvals."
        }
        ""
        "last verdicts on disk:"
        if (Test-Path $sess) {
            $any = $false
            Get-ChildItem $sess -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
                $v = Join-Path $_.FullName 'verdict.txt'
                $a = Join-Path $_.FullName 'lastask.txt'
                $l = Join-Path $_.FullName 'inflight.lock'
                $line = if (Test-Path $v) { (Get-Content $v -Raw).Trim() }
                        elseif (Test-Path $l) { '(still reading, verdict pending)' }
                        else { '(delivered and cleared)' }
                $on = if (Test-Path $a) { (Get-Content $a -Raw).Trim() } else { '' }
                "  [$($_.Name)] $line"
                if ($on) { "      on: $on" }
                $any = $true
            }
            if (-not $any) { "  (none yet)" }
        } else { "  (no session directory yet)" }
    }

    'off' {
        if ($s.mode -eq 'off') { "already off (since $($s.changed)). /judge on to resume." }
        else {
            $null = Set-State 'off' $s.mode
            "JUDGE DREAD IS OFF. He will not audit anything until /judge on."
            "He will remind you once per session that he is off, so this cannot be forgotten."
        }
    }

    'on' {
        if ($s.mode -ne 'off') { "already on, in $($s.mode) mode." }
        else {
            $back = if ($s.prev -and $s.prev -ne 'off') { $s.prev } else { 'verbose' }
            $null = Set-State $back $back
            "JUDGE DREAD IS BACK ON, in $back mode."
        }
    }

    'quiet' {
        $null = Set-State 'quiet' 'quiet'
        "Quiet mode. He audits and blocks exactly as before; the green approval line is gone."
        "You will still see amber when he could not rule - that is not congratulation, it is a gap."
    }

    'verbose' {
        $null = Set-State 'verbose' 'verbose'
        "Verbose mode (the default). He speaks on every outcome."
    }

    default { "unknown command '$Action'. Try /judge help" }
}
