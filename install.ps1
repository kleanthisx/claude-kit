# Install the Claude Code working setup (hooks, skills, doctrine, memory) onto a machine.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -WhatIf     # show, change nothing
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Profile work
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Uninstall
#
# Design rules, in order of importance:
#   1. MERGE, never replace. settings.json is read, added to, written back. Anything already
#      there is kept. A timestamped backup is written before any change.
#   2. Reversible. -Uninstall restores the newest backup and removes the files we copied.
#   3. Idempotent. Run it twice; the second run reports "already present" and changes nothing.
#   4. -WhatIf shows every action and performs none. Run it first on a machine you do not own.
#   5. defaultMode is NEVER exported or set. The home box runs "dontAsk"; imposing that on a
#      work machine is the single riskiest line in this package, so the installer refuses to
#      touch it and leaves whatever the target already has.
#
# Profiles decide which memory tiers land:
#   work  -> core + core-generalised   (all 45 method rules; no project named anywhere)
#   home  -> core + core-sensitive + personal   (originals, plus the 20 project files)
# 13 rules had the project baked into their evidence. Rather than withhold them, core-generalised
# carries the same rule with the incident described instead of named -- the lesson, the numbers and
# the user's own words survive, the project does not. Nothing is lost at work except identifiers.

param(
    [string]$ClaudeHome = (Join-Path $env:USERPROFILE '.claude'),
    [ValidateSet('work','home')] [string]$Profile = 'work',
    [string]$MemoryDir = '',
    [switch]$WhatIf,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$src      = $PSScriptRoot
$hooksDst = Join-Path $ClaudeHome 'hooks'
$skillDst = Join-Path $ClaudeHome 'skills'
$settings = Join-Path $ClaudeHome 'settings.json'

function Say  { param($m) Write-Host $m }
function Act  { param($what, $action)
    if ($WhatIf) { Say "  WOULD: $what" } else { & $action; Say "  did:   $what" }
}

# ---------------------------------------------------------------- uninstall
if ($Uninstall) {
    Say "Uninstall from $ClaudeHome"
    $backups = Get-ChildItem (Join-Path $ClaudeHome 'settings.json.claude-kit-*.bak') -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime      # OLDEST = the state before claude-kit ever ran.
                                              # The newest may be a post-install snapshot from a
                                              # later re-run, which would "restore" the merge.
    if ($backups) {
        Act "restore settings.json from $($backups[0].Name)" { Copy-Item $backups[0].FullName $settings -Force }
    } else {
        Say "  no claude-kit backup found - settings.json left untouched (nothing safe to restore)"
    }
    foreach ($f in (Get-ChildItem (Join-Path $src 'hooks') -File)) {
        $t = Join-Path $hooksDst $f.Name
        if (Test-Path $t) { Act "remove hooks\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
    }
    Say ""
    Say "Memory and doctrine files are NOT removed - they are content, not wiring."
    Say "Delete them by hand if you want them gone."
    exit 0
}

Say "claude-kit -> $ClaudeHome   (profile: $Profile)"
Say ""

# ---------------------------------------------------------------- prerequisites
$claude = Get-Command claude -ErrorAction SilentlyContinue
if ($claude) { Say "claude CLI : found ($($claude.Source))" }
else {
    Say "claude CLI : NOT ON PATH"
    Say "             Judge Dread shells out to 'claude -p' for every verdict. Without it he"
    Say "             FAILS OPEN - no error, no verdict, and a dark judge looks exactly like"
    Say "             an approving one. Fix the PATH before trusting the enforcement layer."
}
$psv = $PSVersionTable.PSVersion.Major
Say "PowerShell : $($PSVersionTable.PSVersion)"
if ($psv -lt 5) { Say "             WARNING: these hooks are written for 5.1+." }
Say ""

# ---------------------------------------------------------------- files
Say "files:"
foreach ($d in @($hooksDst, $skillDst)) {
    if (-not (Test-Path $d)) { Act "create $d" { New-Item -ItemType Directory -Force -Path $d | Out-Null }.GetNewClosure() }
}
foreach ($f in (Get-ChildItem (Join-Path $src 'hooks') -File)) {
    $t = Join-Path $hooksDst $f.Name
    $same = (Test-Path $t) -and ((Get-FileHash $f.FullName).Hash -eq (Get-FileHash $t).Hash)
    if ($same) { Say "  same:  hooks\$($f.Name)" }
    else       { Act "copy hooks\$($f.Name)" { Copy-Item $f.FullName $t -Force }.GetNewClosure() }
}
$fixSrc = Join-Path $src 'tests\fixtures'
if (Test-Path $fixSrc) {
    $fixDst = Join-Path $hooksDst 'fixtures'
    Act "copy tests\fixtures -> hooks\fixtures" { Copy-Item $fixSrc $fixDst -Recurse -Force }.GetNewClosure()
}
foreach ($sk in (Get-ChildItem (Join-Path $src 'skills') -Directory)) {
    $t = Join-Path $skillDst $sk.Name
    if (-not (Test-Path $t)) { Act "create skills\$($sk.Name)" { New-Item -ItemType Directory -Force -Path $t | Out-Null }.GetNewClosure() }
    Act "copy skills\$($sk.Name)\SKILL.md" { Copy-Item (Join-Path $sk.FullName 'SKILL.md') (Join-Path $t 'SKILL.md') -Force }.GetNewClosure()
}

# ---------------------------------------------------------------- doctrine
Say ""
Say "doctrine:"
$home_md = Join-Path $env:USERPROFILE 'CLAUDE.md'
if (Test-Path $home_md) {
    Say "  EXISTS: $home_md - left alone. Merge by hand; overwriting a working agreement is not"
    Say "          something an installer should decide."
} else {
    Act "install CLAUDE.md -> $home_md" { Copy-Item (Join-Path $src 'doctrine\CLAUDE.md') $home_md -Force }.GetNewClosure()
}
Act "install RULES.md -> $ClaudeHome\RULES.md" { Copy-Item (Join-Path $src 'doctrine\RULES.md') (Join-Path $ClaudeHome 'RULES.md') -Force }.GetNewClosure()

# ---------------------------------------------------------------- memory
Say ""
Say "memory (profile: $Profile):"
if (-not $MemoryDir) {
    Say "  -MemoryDir not given. Memory is PROJECT-SCOPED: it lives at"
    Say "    <ClaudeHome>\projects\<encoded-working-dir>\memory\"
    Say "  and the encoding differs per machine, so this cannot be guessed safely."
    Say "  Re-run with e.g. -MemoryDir `"$ClaudeHome\projects\C--Users-you-projects\memory`""
    Say "  SKIPPED - no memory installed."
} else {
    # work -> generalised evidence (no project named anywhere); home -> the originals + projects.
    # core-sensitive and core-generalised hold the SAME 13 filenames: one is the original incident,
    # the other the same rule with the project generalised out. Only one tier is ever installed.
    if ($Profile -eq 'home') { $tiers = @('core','core-sensitive','personal') }
    else                     { $tiers = @('core','core-generalised') }
    if (-not (Test-Path $MemoryDir)) { Act "create $MemoryDir" { New-Item -ItemType Directory -Force -Path $MemoryDir | Out-Null }.GetNewClosure() }
    foreach ($tier in $tiers) {
        $td = Join-Path $src "memory\$tier"
        if (-not (Test-Path $td)) { continue }
        $n = (Get-ChildItem $td -Filter *.md).Count
        Act "copy memory\$tier ($n files)" { Get-ChildItem $td -Filter *.md | ForEach-Object { Copy-Item $_.FullName (Join-Path $MemoryDir $_.Name) -Force } }.GetNewClosure()
    }
    Act "copy MEMORY.md (index)" { Copy-Item (Join-Path $src 'memory\MEMORY.md') (Join-Path $MemoryDir 'MEMORY.md') -Force }.GetNewClosure()
    # inject-exclude.txt controls what session-rules.ps1 puts in EVERY session's context.
    # Without it the hook injects every .md in the directory -- project state included.
    $ex = Join-Path $src 'memory\inject-exclude.txt'
    if (Test-Path $ex) { Act "copy inject-exclude.txt" { Copy-Item $ex (Join-Path $MemoryDir 'inject-exclude.txt') -Force }.GetNewClosure() }
    if ($Profile -ne 'home') {
        $gen = Get-ChildItem (Join-Path $src 'memory\core-generalised') -Filter *.md -ErrorAction SilentlyContinue
        Say ""
        Say "  NOTHING WITHHELD. All 45 method rules are installed. $($gen.Count) of them ship in a"
        Say "  generalised form -- same rule, same numbers, same quoted words, with the project it"
        Say "  happened on described rather than named. Each carries a footer saying so."
    }
}

# ---------------------------------------------------------------- settings merge
Say ""
Say "settings.json:"
if (-not (Test-Path $settings)) {
    Act "create empty settings.json" { '{}' | Set-Content $settings -Encoding utf8 }.GetNewClosure()
}
$raw = Get-Content $settings -Raw
$cur = $raw | ConvertFrom-Json
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$bak = Join-Path $ClaudeHome "settings.json.claude-kit-$stamp.bak"
# The backup is written LAZILY, only if this run actually changes something. A no-op re-run that
# still wrote one would leave a "backup" of the already-merged state, and -Uninstall would then
# restore the merge instead of undoing it. Found by running install twice then uninstalling.
$backedUp = $false
function Ensure-Backup {
    if ($script:backedUp) { return }
    Act "backup -> $(Split-Path $bak -Leaf)" { Copy-Item $settings $bak -Force }.GetNewClosure()
    $script:backedUp = $true
}

$fragRaw = (Get-Content (Join-Path $src 'settings\hooks.json') -Raw) -replace '\{\{CLAUDE_HOME\}\}', ($ClaudeHome -replace '\\','/')
$frag = $fragRaw | ConvertFrom-Json

$added = 0; $kept = 0
if (-not $cur.PSObject.Properties['hooks']) { $cur | Add-Member -NotePropertyName hooks -NotePropertyValue ([pscustomobject]@{}) }
foreach ($ev in $frag.hooks.PSObject.Properties.Name) {
    if (-not $cur.hooks.PSObject.Properties[$ev]) {
        $cur.hooks | Add-Member -NotePropertyName $ev -NotePropertyValue @()
    }
    foreach ($entry in $frag.hooks.$ev) {
        $ourCmds = @($entry.hooks | ForEach-Object { Split-Path $_.command -Leaf })
        $already = $false
        foreach ($existing in $cur.hooks.$ev) {
            foreach ($h in $existing.hooks) {
                if ($ourCmds -contains (Split-Path $h.command -Leaf)) { $already = $true }
            }
        }
        if ($already) { $kept++ }
        else { Ensure-Backup; $cur.hooks.$ev = @($cur.hooks.$ev) + $entry; $added++ }
    }
}
Say "  hooks: $added to add, $kept already present (existing entries untouched)"

$permFrag = (Get-Content (Join-Path $src 'settings\permissions.json') -Raw) | ConvertFrom-Json
if (-not $cur.PSObject.Properties['permissions']) { $cur | Add-Member -NotePropertyName permissions -NotePropertyValue ([pscustomobject]@{}) }
foreach ($bucket in @('allow','deny','ask')) {
    if (-not $permFrag.permissions.PSObject.Properties[$bucket]) { continue }
    if (-not $cur.permissions.PSObject.Properties[$bucket]) {
        $cur.permissions | Add-Member -NotePropertyName $bucket -NotePropertyValue @()
    }
    $have = @($cur.permissions.$bucket)
    $new  = @($permFrag.permissions.$bucket | Where-Object { $have -notcontains $_ })
    if ($new.Count) { Ensure-Backup; $cur.permissions.$bucket = $have + $new }
    Say "  permissions.$bucket : +$($new.Count) new, $($have.Count) already there"
}
Say "  permissions.defaultMode : NOT touched (deliberate - see header)"

if (-not $backedUp) { Say "  no changes - settings.json not rewritten, no backup created" }
elseif ($WhatIf)    { Say "  WOULD: write settings.json" }
else {
    ($cur | ConvertTo-Json -Depth 20) | Set-Content $settings -Encoding utf8
    Say "  did:   write settings.json"
}

Say ""
Say "Next:"
Say "  1. powershell -File tests\test-hooks.ps1          (expect 80 PASS / 0 FAIL / 1 SKIP)"
Say "  2. powershell -File tests\test-judge-dread.ps1    (needs the claude CLI on PATH)"
Say "  3. Start a session and confirm RULES.md arrives at SessionStart."
Say "  4. Judge Dread costs one 'claude -p' per turn. '/judge quiet' or '/judge off' if that"
Say "     is not the trade you want on this machine."
