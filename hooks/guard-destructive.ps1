# PreToolUse guard: destructive shell commands -> interactive ask (Protocol E: propose-and-wait)
# Matches Bash|PowerShell tool calls. Reads hook JSON on stdin.
#
# TWO EVENTS, ONE FILE (2026-09-16). Wired on PreToolUse AND PostToolUse for Bash|PowerShell:
#   PreToolUse  -> decide (ask / allow), including scanning the CONTENTS of any script the
#                  command launches (gap B: the hook only ever sees tool_input.command, so
#                  `python run_x.py` was invisible while an inline os.remove() was caught).
#   PostToolUse -> record approval. A PreToolUse hook is never told whether the user approved,
#                  but PostToolUse only fires if the command actually RAN -- which means it was
#                  approved. So that is where a script's hash gets remembered.
# Both events in one file so the pattern list has exactly one definition and cannot drift.
$ErrorActionPreference = 'SilentlyContinue'
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }
$cmd = $in.tool_input.command
if (-not $cmd) { exit 0 }
$evt = if ($in.hook_event_name) { [string]$in.hook_event_name } else { 'PreToolUse' }
$cwd = if ($in.cwd) { [string]$in.cwd } else { (Get-Location).Path }
$approvalsFile = Join-Path $PSScriptRoot '.script-approvals.json'

# Scratchpad/Temp allowance: only when the command touches Temp paths AND has no chaining
$hasChain = $cmd -match '[;|&`]' -or $cmd -match "`r" -or $cmd -match "`n"
$tempOnly = (-not $hasChain) -and ($cmd -match 'AppData\\+Local\\+Temp|\$env:TEMP|/tmp/|AppData/Local/Temp')

# NOTE: verbs are matched ANYWHERE in the command (not anchored to the start) so that
# wrapper spellings -- powershell -Command "rm -Recurse -Force ...", pwsh -c "...", etc. --
# are caught: the deny/ask permission RULES only match a command's leading token, so a
# wrapper defeats every rule and this hook is the only remaining gate. Confirmed by
# ground-truth victim-file tests 2026-08-06 (both adversarial reviewers deleted real files
# via powershell/python before this patch). This is an ASK gate, so it fails toward asking.
$patterns = @(
    # --- recursive / forced file-tree deletion, delete-verb anywhere (defeats ps/pwsh wrappers) ---
    # POSIX rm with combined recursive+force short flags (-rf / -fr, any letters)
    '\brm\b[^;|&\n]*\s-[a-zA-Z]*r[a-zA-Z]*f',
    '\brm\b[^;|&\n]*\s-[a-zA-Z]*f[a-zA-Z]*r',
    # any delete verb followed by a -r / -rec / -recurse flag (covers the long PowerShell flag)
    '\b(rm|rmdir|Remove-Item|ri|rd|erase|del)\b[^;|&\n]*\s-r(ec[a-zA-Z]*)?\b',
    '\b(rm|rmdir|Remove-Item|ri|rd|erase|del)\b[^;|&\n]*\s-r(ec[a-zA-Z]*)?:\$true',
    # explicit -Recurse + -Force in either order, for the whole verb set
    '\b(rm|rmdir|Remove-Item|ri|rd|erase|del)\b[^;|&\n]*(-Recurse\b|-Recurse:\$true)[^;|&\n]*(-Force\b|-fo\b)',
    '\b(rm|rmdir|Remove-Item|ri|rd|erase|del)\b[^;|&\n]*(-Force\b|-fo\b)[^;|&\n]*(-Recurse\b|-Recurse:\$true)',
    # --- named-file deletion, no recurse flag (added 2026-09-16) ---------------------------
    # Every pattern above requires a RECURSE flag, so deleting NAMED files was silent. Measured
    # against this script before the change: `rm f.py`, `rm -f f.py`, `del f.py`,
    # `Remove-Item f.py`, `Remove-Item -Force f.py` and even `rm -f *.py` all returned ALLOW,
    # while `rm -rf build/` correctly asked. An untracked file deleted that way is unrecoverable
    # -- exactly as irreversible as a directory, which is the case this guard exists for. It hit
    # live twice: four experiment-run artifacts, and an untracked build_catalog.py.
    # Noise measured BEFORE adding, across the last 12 session transcripts: non-recursive deletes
    # outside Temp/scratch numbered TWO, one of them the incident above. The $tempOnly allowance
    # below still exempts routine scratchpad churn, so the cost is ~2 prompts per 12 sessions.
    # Anchored to COMMAND POSITION (start of line, after a chain operator, or inside an explicit
    # -c/-Command wrapper) -- unlike the recursive patterns above, which match the verb anywhere.
    # Reason: matching anywhere made `grep -rn rm file.txt` ask, because the search term is the
    # verb. The recursive patterns can afford the anywhere-match because "-rf" next to a delete
    # verb is not something you type by accident; a bare "rm" is.
    '(?:^|[;&|(]|-c\s*"|-Command\s*")\s*(rm|del|erase)\b[^;|&\n]*\s+\S',
    '(?:^|[;&|(]|-c\s*"|-Command\s*")\s*(Remove-Item|ri)\b[^;|&\n]*\s+\S',
    # piped delete
    '\|\s*(Remove-Item|ri|rm|rd|del)\b',
    # .NET delete
    '\[System\.IO\.(Directory|File)\]::Delete',
    # cmd-style recursive dir / file delete
    '\b(rmdir|rd)\b[^;|&\n]*\s/s\b',
    '\bdel\b[^;|&\n]*\s/[sq]\b',
    # --- Python deletion APIs (python is allow-listed; this hook is the only gate) ---
    '\bshutil\.rmtree\b',
    '\brmtree\s*\(',
    '\bos\.(remove|rmdir|removedirs|unlink)\b',
    '\.unlink\s*\(',
    '\.rmdir\s*\(',
    # --- git / disk (unchanged) ---
    'git\s+push\s+[^;|&]*--force(?!-with-lease)',
    'git\s+push\s+[^;|&]*\s-f\b',
    'git\s+reset\s+--hard',
    'git\s+clean\s+-[a-zA-Z]*f',
    'git\s+stash\b(?!\s+(pop|apply|list|show|branch))',
    '\bmkfs\b',
    '\bFormat-Volume\b',
    '\bClear-Disk\b'
)

# --- gap B: scripts the command launches ------------------------------------------------
# Find script files a command runs, so their CONTENTS can be scanned with the same patterns.
# Scoped to python and PowerShell because that is what this tree runs; a script that shells
# out to a THIRD script is not followed, and neither are imported modules. Documented limit,
# not an oversight.
function Get-LaunchedScripts([string]$c, [string]$base) {
    $hits = @()
    $rx = @(
        '(?i)(?:^|[;&|(]|\s)(?:"[^"]*python[^"]*"|[^\s";|&]*python(?:3|\.exe)?|\bpy)\s+(?:-[^\s]+\s+)*"?([^\s";|&]+\.py)"?',
        '(?i)-File\s+"?([^\s";|&]+\.ps1)"?',
        '(?i)(?:^|[;&|(]\s*|\s&\s+)"?((?:\.[\\/])?[^\s";|&]+\.ps1)"?'
    )
    foreach ($r in $rx) {
        foreach ($m in [regex]::Matches($c, $r)) {
            $p = $m.Groups[1].Value.Trim('"')
            if (-not [System.IO.Path]::IsPathRooted($p)) { $p = Join-Path $base $p }
            if (Test-Path $p -PathType Leaf) { $hits += (Resolve-Path $p).Path }
        }
    }
    $hits | Select-Object -Unique
}
function Get-Sha([string]$path) {
    try { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash } catch { $null }
}
function Read-Approvals([string]$f) {
    if (-not (Test-Path $f)) { return @{} }
    $h = @{}
    try { (Get-Content $f -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $h[$_.Name] = $_.Value } } catch {}
    $h
}

# PostToolUse: the command RAN, so anything it launched was approved. Remember the hashes.
# Keyed on CONTENT, so editing the script invalidates the approval and it asks again -- which
# is exactly when a new deletion could have appeared.
if ($evt -eq 'PostToolUse') {
    $scripts = Get-LaunchedScripts $cmd $cwd
    if (-not $scripts) { exit 0 }
    $appr = Read-Approvals $approvalsFile
    $changed = $false
    foreach ($s in $scripts) {
        $sha = Get-Sha $s
        if (-not $sha -or $appr.ContainsKey($sha)) { continue }
        $appr[$sha] = @{ path = $s; approved = (Get-Date -Format 'o') }
        $changed = $true
    }
    if ($changed) { ($appr | ConvertTo-Json -Depth 5) | Set-Content $approvalsFile -Encoding utf8 }
    exit 0
}

foreach ($p in $patterns) {
    if ($cmd -match $p) {
        if ($tempOnly) { exit 0 }
        $reason = 'Protocol E (propose-and-wait): destructive command detected. The user must approve this prompt, or the command must be re-proposed in one line and wait for GO. Venting or ambiguous complaints are never authorization.'
        $out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'ask'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
        Write-Output $out
        exit 0
    }
}

# Nothing in the command text itself. Now look INSIDE any script it launches.
$approvals = $null
foreach ($s in (Get-LaunchedScripts $cmd $cwd)) {
    $fi = Get-Item -LiteralPath $s
    if ($fi.Length -gt 524288) { continue }   # 512 KB cap: a source file this large is not ours
    $body = [System.IO.File]::ReadAllText($s)
    if (-not $body) { continue }
    foreach ($p in $patterns) {
        if ($body -notmatch $p) { continue }
        $sha = Get-Sha $s
        if ($null -eq $approvals) { $approvals = Read-Approvals $approvalsFile }
        if ($sha -and $approvals.ContainsKey($sha)) { break }   # approved at this exact content
        $reason = "Protocol E (propose-and-wait): $([System.IO.Path]::GetFileName($s)) contains a destructive operation matching /$p/, and this command runs it. The hook only sees the command line, so this is the only point at which a deletion inside a script is visible. Approving runs it and remembers THIS VERSION of the file; editing the script asks again."
        $out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'ask'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
        Write-Output $out
        exit 0
    }
}
exit 0
