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
# Profiles decide which memory tiers land (counts are computed at install time, never hardcoded):
#   work  -> core + core-generalised   (every method rule; no project named anywhere)
#   home  -> core + core-sensitive + personal   (originals, plus project-state files)
# Some rules have the project baked into their evidence. Rather than withhold them, core-generalised
# carries the same rule with the incident described instead of named -- the lesson, the numbers and
# the user's own words survive, the project does not. Nothing is lost at work except identifiers.
# core-sensitive/ and personal/ are git-ignored: a clone made away from the source machine will not
# contain them, and -Profile home says so plainly when a tier is missing.

param(
    [string]$ClaudeHome = (Join-Path $env:USERPROFILE '.claude'),
    [ValidateSet('work','home')] [string]$Profile = 'work',
    [string]$MemoryDir = '',
    [switch]$WhatIf,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$src       = $PSScriptRoot
$hooksDst  = Join-Path $ClaudeHome 'hooks'
$skillDst  = Join-Path $ClaudeHome 'skills'
$agentsDst = Join-Path $ClaudeHome 'agents'
$toolsDst  = Join-Path $ClaudeHome 'tools'
$settings  = Join-Path $ClaudeHome 'settings.json'

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
    foreach ($f in (Get-ChildItem (Join-Path $src 'agents') -Filter *.md -File)) {
        $t = Join-Path $agentsDst $f.Name
        if (Test-Path $t) { Act "remove agents\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
    }
    foreach ($f in (Get-ChildItem (Join-Path $src 'tools') -File)) {
        $t = Join-Path $toolsDst $f.Name
        if (Test-Path $t) { Act "remove tools\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
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
foreach ($d in @($agentsDst, $toolsDst)) {
    if (-not (Test-Path $d)) { Act "create $d" { New-Item -ItemType Directory -Force -Path $d | Out-Null }.GetNewClosure() }
}
foreach ($f in (Get-ChildItem (Join-Path $src 'agents') -Filter *.md -File)) {
    $t = Join-Path $agentsDst $f.Name
    # Read/write via .NET UTF8 explicitly -- PowerShell 5.1's Get-Content/Set-Content -Encoding utf8
    # guesses ANSI on a BOM-less file (these are BOM-less) and mojibake's every em-dash. WriteAllText
    # with UTF8Encoding($false) keeps the output BOM-less too, matching the source convention.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $body = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8) -replace '\{\{CLAUDE_HOME\}\}', ($ClaudeHome -replace '\\','/')
    $same = (Test-Path $t) -and ([System.IO.File]::ReadAllText($t, [System.Text.Encoding]::UTF8) -eq $body)
    if ($same) { Say "  same:  agents\$($f.Name)" }
    else       { Act "copy agents\$($f.Name) (CLAUDE_HOME substituted)" { [System.IO.File]::WriteAllText($t, $body, $utf8NoBom) }.GetNewClosure() }
}
foreach ($f in (Get-ChildItem (Join-Path $src 'tools') -File)) {
    $t = Join-Path $toolsDst $f.Name
    $same = (Test-Path $t) -and ((Get-FileHash $f.FullName).Hash -eq (Get-FileHash $t).Hash)
    if ($same) { Say "  same:  tools\$($f.Name)" }
    else       { Act "copy tools\$($f.Name)" { Copy-Item $f.FullName $t -Force }.GetNewClosure() }
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

Say ""
Say "reference only, never installed: templates/, wiki-v1/, wiki-v2/ -- see BOOTSTRAP.md for how to use them."

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
    # work -> generalised evidence (no project named anywhere); home -> the originals + personal.
    # core-sensitive and core-generalised hold the SAME filenames for rules that had a project baked
    # into their evidence: one is the original incident, the other the same rule generalised out.
    # Only one tier is ever installed. core-sensitive/ and personal/ are git-ignored, so a clone made
    # away from the source machine will not have them -- reported below, not silently skipped.
    if ($Profile -eq 'home') { $tiers = @('core','core-sensitive','personal') }
    else                     { $tiers = @('core','core-generalised') }
    if (-not (Test-Path $MemoryDir)) { Act "create $MemoryDir" { New-Item -ItemType Directory -Force -Path $MemoryDir | Out-Null }.GetNewClosure() }
    $installedCount = 0
    foreach ($tier in $tiers) {
        $td = Join-Path $src "memory\$tier"
        if (-not (Test-Path $td)) {
            if ($Profile -eq 'home') { Say "  memory\$tier : NOT PRESENT in this clone (git-ignored -- lives only on the source machine)" }
            continue
        }
        $n = (Get-ChildItem $td -Filter *.md).Count
        $installedCount += $n
        Act "copy memory\$tier ($n files)" { Get-ChildItem $td -Filter *.md | ForEach-Object { Copy-Item $_.FullName (Join-Path $MemoryDir $_.Name) -Force } }.GetNewClosure()
    }
    Act "copy MEMORY.md (index)" { Copy-Item (Join-Path $src 'memory\MEMORY.md') (Join-Path $MemoryDir 'MEMORY.md') -Force }.GetNewClosure()
    # inject-exclude.txt controls what session-rules.ps1 puts in EVERY session's context.
    # Without it the hook injects every .md in the directory -- project state included.
    # Home has its own list (git-ignored, personal inventory files it alone knows to exclude);
    # falls back to the generic list if that clone doesn't have it.
    if ($Profile -eq 'home') {
        $ex = Join-Path $src 'memory\personal\inject-exclude.home.txt'
        if (-not (Test-Path $ex)) { $ex = Join-Path $src 'memory\inject-exclude.txt' }
    } else {
        $ex = Join-Path $src 'memory\inject-exclude.txt'
    }
    if (Test-Path $ex) { Act "copy inject-exclude.txt (source: $(Split-Path $ex -Leaf))" { Copy-Item $ex (Join-Path $MemoryDir 'inject-exclude.txt') -Force }.GetNewClosure() }
    elseif ($Profile -eq 'home') { Say "  inject-exclude.home.txt : NOT PRESENT in this clone (git-ignored) -- no inject-exclude.txt installed" }
    if ($Profile -ne 'home') {
        $gen = Get-ChildItem (Join-Path $src 'memory\core-generalised') -Filter *.md -ErrorAction SilentlyContinue
        Say ""
        Say "  NOTHING WITHHELD. All $installedCount method rules are installed. $($gen.Count) of them ship in a"
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
# -WhatIf performs no action above, so a truly fresh machine still has no file here -- read the
# virtual empty document instead of failing rule 4 ("-WhatIf shows every action and performs none").
$raw = if (Test-Path $settings) { Get-Content $settings -Raw } else { '{}' }
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

if ($frag.PSObject.Properties['statusLine']) {
    if ($cur.PSObject.Properties['statusLine'] -and $cur.statusLine) {
        Say "  statusLine : already set - left untouched"
    } else {
        Ensure-Backup
        if ($cur.PSObject.Properties['statusLine']) { $cur.statusLine = $frag.statusLine }
        else { $cur | Add-Member -NotePropertyName statusLine -NotePropertyValue $frag.statusLine -Force }
        Say "  statusLine : added (tools/statusline-usage.ps1)"
    }
}

if (-not $backedUp) { Say "  no changes - settings.json not rewritten, no backup created" }
elseif ($WhatIf)    { Say "  WOULD: write settings.json" }
else {
    ($cur | ConvertTo-Json -Depth 20) | Set-Content $settings -Encoding utf8
    Say "  did:   write settings.json"
}

Say ""
Say "Next:"
Say "  1. powershell -File tests\test-hooks.ps1          (counts drift as cases are added -- 0 FAIL is the bar)"
Say "  2. powershell -File tests\test-entity-read.ps1    (9 PASS / 0 FAIL)"
Say "  3. powershell -File tests\test-judge-dread.ps1    (needs the claude CLI on PATH)"
Say "  4. Start a session and confirm RULES.md arrives at SessionStart."
Say "  5. Judge Dread costs one 'claude -p' per turn. '/judge quiet' or '/judge off' if that"
Say "     is not the trade you want on this machine."
