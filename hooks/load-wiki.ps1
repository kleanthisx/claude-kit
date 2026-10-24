# SessionStart: emit one numbered part of the wiki's always-loaded layer.
#
# SYSTEM, DISCARDED plus doctrine ARE the always-loaded layer. Without this hook they are
# "always loaded" by intention only, which is the same as not loaded. OVERVIEW.md and NAMES.md
# (2026-10-11) and DECISIONS.md (operator, 2026-10-07) are generated too but loaded on demand.
#
# SessionStart fires again with source=compact, so these parts are re-injected then.
#
# Regenerates before reading, so what is loaded is never stale relative to the entity files.
# Disarm:  $env:WIKI_LOAD = 'off'
param([Parameter(Mandatory=$true)][ValidateRange(0,39)][int]$Part)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'context-part.ps1')
if ($env:WIKI_LOAD -eq 'off') { exit 0 }

try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { $in = $null }
$evt = if ($in.hook_event_name) { $in.hook_event_name } else { 'SessionStart' }
$cwd = if ($in.cwd) { $in.cwd } else { (Get-Location).Path }

# --- nearest ancestor holding a v2 wiki -------------------------------------
$root = $null; $probe = $cwd
for ($i = 0; $i -lt 8 -and $probe; $i++) {
    if (Test-Path (Join-Path $probe 'docs\wiki\entities')) { $root = $probe; break }
    $probe = Split-Path $probe -Parent
}
if (-not $root) {
    # The operator often starts at the parent `projects` folder. Do not guess a project and
    # silently claim its wiki was loaded; flag the required /enter step instead.
    # 2026-10-11: they start there "to get an overview of other related projects", so the project map
    # (wiki/project-map.md: what each project is and how they relate) loads here too. Every part builds
    # the same text and Write-KitContextPart prints its own slice, so the map arrives whole at any size.
    $ctx = ''
    if (Test-Path $cwd) {
        $available = @(Get-ChildItem $cwd -Directory -ErrorAction SilentlyContinue | Where-Object {
            Test-Path (Join-Path $_.FullName 'docs\wiki\entities')
        } | Select-Object -ExpandProperty Name)
        if ($available.Count) {
            $ctx = 'NO WIKI v2 LOADED: this session started above the project wiki. ' +
                'Before project work, enter the intended project and load its wiki; do not infer which one. ' +
                'Immediate child projects with v2 wikis: ' + ($available -join ', ')
        }
        $map = Join-Path $cwd 'wiki\project-map.md'
        if (Test-Path $map) {
            $ctx += "`n`n<<<<<< PROJECT MAP - what each project is and how they relate (wiki/project-map.md)`n" +
                [System.IO.File]::ReadAllText($map, [System.Text.Encoding]::UTF8) + "`n>>>>>>`n"
        }
    }
    if ($ctx) { Write-KitContextPart -Context $ctx -Kind 'WIKI' -EventName $evt -Part $Part -PartCount 40 }
    exit 0
}
$wiki = Join-Path $root 'docs\wiki'

# --- regenerate once across parallel parts if the generated surfaces are stale ---
$gen = Join-Path $wiki 'generate.py'
function Test-WikiSurfacesFresh {
    $outputs = @('OVERVIEW.md','DISCARDED.md','NAMES.md','DECISIONS.md') |
        ForEach-Object { Join-Path $wiki $_ }
    foreach ($p in $outputs) { if (-not (Test-Path $p)) { return $false } }
    $inputs = @()
    if (Test-Path $gen) { $inputs += @(Get-Item $gen) }
    foreach ($d in @('entities','ledgers')) {
        $dir = Join-Path $wiki $d
        if (Test-Path $dir) { $inputs += @(Get-ChildItem $dir -Filter *.md -File) }
    }
    if ($inputs.Count -eq 0) { return $true }
    $newestInput = ($inputs | Measure-Object LastWriteTimeUtc -Maximum).Maximum
    $oldestOutput = ($outputs | Get-Item | Measure-Object LastWriteTimeUtc -Minimum).Minimum
    return ($oldestOutput -ge $newestInput)
}

if (Test-Path $gen) {
    $nameHash = [BitConverter]::ToString(
        [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($wiki))
    ).Replace('-', '').Substring(0, 24)
    $mutex = New-Object System.Threading.Mutex($false, "Local\claude-kit-wiki-$nameHash")
    $acquired = $false
    try {
        try { $acquired = $mutex.WaitOne(12000) }
        catch [System.Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) { throw 'Timed out waiting for wiki generator lock' }
        if (-not (Test-WikiSurfacesFresh)) {
            $o = & python $gen 2>&1 | Out-String
            if ($LASTEXITCODE -ne 0) { throw "generate.py exited ${LASTEXITCODE}: $o" }
            if (-not (Test-WikiSurfacesFresh)) { throw 'generate.py did not produce all current wiki surfaces' }
        }
    } catch {
        if ($Part -eq 0) {
            $msg = "WIKI v2 DELIVERY FAILED: $($_.Exception.Message). Generated surfaces were NOT loaded. " +
                'Stop project work and report this to the operator.'
            Write-KitContextPart -Context $msg -Kind 'WIKI' -EventName $evt -Part 0 -PartCount 40
        }
        exit 0
    } finally {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}
elseif (-not (Test-WikiSurfacesFresh)) {
    if ($Part -eq 0) {
        $msg = 'WIKI v2 DELIVERY FAILED: generated surfaces are missing or stale, and generate.py is absent. ' +
            'The wiki was NOT loaded. Stop project work and report this to the operator.'
        Write-KitContextPart -Context $msg -Kind 'WIKI' -EventName $evt -Part 0 -PartCount 40
    }
    exit 0
}

# Lint is read-only. Run it for every part so the warning count and the decision to load are
# identical across parallel processes, including when another process did the regeneration.
$genNote = ''
if (Test-Path $gen) {
    try {
        $lint = & python $gen --lint 2>&1 | Out-String
        $warn = ([regex]::Matches($lint, '(?m)^WARN\s')).Count
        $err = ([regex]::Matches($lint, '(?m)^ERROR\s')).Count
        if ($LASTEXITCODE -ne 0 -or $err -gt 0) {
            throw "wiki lint found $err error(s); run python docs/wiki/generate.py --lint"
        }
        if ($warn -gt 0) { $genNote = "  (lint: $warn warning(s))" }
    } catch {
        if ($Part -eq 0) {
            $msg = "WIKI v2 DELIVERY FAILED: $($_.Exception.Message). The wiki was NOT loaded. " +
                'Stop project work and report this to the operator.'
            Write-KitContextPart -Context $msg -Kind 'WIKI' -EventName $evt -Part 0 -PartCount 40
        }
        exit 0
    }
}

# --- collect ----------------------------------------------------------------
$parts = New-Object System.Collections.Generic.List[string]
$bytes = 0
function Add-Surface($path, $why) {
    if (-not (Test-Path $path)) { return }
    $t = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
    if (-not $t) { return }
    $script:bytes += $t.Length
    $parts.Add("`n<<<<<< $why`n$t`n>>>>>>`n")
}

# 2026-10-11 (operator: the overview is "prose and entity names as entry points"; the code is the ground truth):
# SYSTEM.md, the system in prose, is what loads. OVERVIEW.md (the entity list) and NAMES.md (aliases) are still
# generated and are read on demand, when work starts on a part. projects/wiki/WIKI-STANDARD.md, "The layers".
# A wiki with no SYSTEM.md yet keeps the behaviour from before: OVERVIEW.md and NAMES.md load at start.
$hasSystem = Test-Path (Join-Path $wiki 'SYSTEM.md')
if ($hasSystem) {
    Add-Surface (Join-Path $wiki 'SYSTEM.md')   'SYSTEM - the overview: how this project works, in prose. Names in backticks are the entry points to the next level.'
} else {
    Add-Surface (Join-Path $wiki 'OVERVIEW.md') 'OVERVIEW - what exists. Every entity in this project, no exceptions. If it is here, DO NOT REBUILD IT.'
    Add-Surface (Join-Path $wiki 'NAMES.md')    'NAMES - aliases to canonical. A row marked AMBIGUOUS means ASK, never guess.'
}
Add-Surface (Join-Path $wiki 'DISCARDED.md')  'THE MAP - what is already a dead end. Read before proposing anything: you cannot search for a decision whose name you do not know.'
# DECISIONS.md is ON DEMAND since 2026-10-07 (operator): it repeats the entity bodies and cost
# ~53 KB at every start. It is still generated; grep it for a decision by name when one is needed.
if (Test-Path (Join-Path $wiki 'doctrine')) {
    foreach ($d in Get-ChildItem (Join-Path $wiki 'doctrine') -Filter *.md -File | Sort-Object Name) {
        Add-Surface $d.FullName "DOCTRINE ($($d.Name)) - how work is done here. Read wholesale; it governs every entity, so it is never routed."
    }
}
if ($parts.Count -eq 0) { exit 0 }

$proj = Split-Path $root -Leaf
$kb = [math]::Round($bytes / 1024)
$tok = [math]::Round($bytes / 4000, 1)

$header = @"
# WIKI v2 - the always-loaded layer for '$proj' ($evt)

SYSTEM.md is the overview, written in prose; THE MAP (generated) and doctrine/ load beside it.
The code is the ground truth of the code; the wiki holds design, decisions and what each thing affects.

  ${kb} KB / ~${tok}k tokens$genNote

How to use them, in order:
  1. SYSTEM     - how the project works. Find the part you are working on and its entity name.
  2. THE MAP    - has this already been tried and killed? Check before proposing.
  3. When work starts on a part: docs/wiki/OVERVIEW.md lists every entity (name, aliases, state);
                grep docs/wiki/NAMES.md to resolve what the user said to ONE entity (AMBIGUOUS means ask).
  4. Then read  docs/wiki/entities/<the entity>.md  in full. An edit to a file is BLOCKED by
                guard-entity-read.ps1 until every entity that owns it, and every entity named in
                their depends: and dependents: lines, has been read in full this session.

What is NOT here, by design: history (docs/history/, never loaded, cited by path), the v1 reference
pages still at wiki root, IDEAS.md and TASKS.md (routed by tag, on demand), OVERVIEW.md and NAMES.md
(on demand, step 3), and DECISIONS.md (on demand: grep it for a decision by name).
"@

if (-not $hasSystem) {
    $header += "`n(No SYSTEM.md in this wiki yet: OVERVIEW.md and NAMES.md are loaded in its place, as before 2026-10-11.)`n"
}
$context = $header + "`n" + ($parts -join "`n")

Write-KitContextPart -Context $context -Kind 'WIKI' -EventName $evt -Part $Part -PartCount 40
exit 0
