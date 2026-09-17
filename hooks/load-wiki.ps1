# SessionStart + PostCompact: load the wiki's always-loaded layer.
#
# The four generated surfaces plus doctrine ARE the always-loaded layer. Without this hook they are
# "always loaded" by intention only, which is the same as not loaded.
#
# PostCompact is the load-bearing half: compaction takes rule violation from 0% to 30-59%, and
# re-injection after compaction is the documented fix (SYNTHESIS.md section 1, lane a9). Hook output
# also arrives as a clean system-reminder with none of the "ignore if irrelevant" framing that makes
# the model skip injected files.
#
# Regenerates before reading, so what is loaded is never stale relative to the entity files.
# Disarm:  $env:WIKI_LOAD = 'off'
$ErrorActionPreference = 'SilentlyContinue'
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
if (-not $root) { exit 0 }
$wiki = Join-Path $root 'docs\wiki'

# --- regenerate so the loaded copy is current -------------------------------
$gen = Join-Path $wiki 'generate.py'
$genNote = ''
if (Test-Path $gen) {
    $o = & python $gen 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { $genNote = "  (generate.py exited $LASTEXITCODE - surfaces may be stale)" }
    $warn = ([regex]::Matches($o, 'WARN')).Count
    $err  = ([regex]::Matches($o, 'ERROR')).Count
    if ($err -gt 0) { $genNote = "  (LINT: $err error(s), $warn warning(s) - run: python docs/wiki/generate.py --lint)" }
    elseif ($warn -gt 0) { $genNote = "  (lint: $warn warning(s))" }
}

# --- collect ----------------------------------------------------------------
$parts = New-Object System.Collections.Generic.List[string]
$bytes = 0
function Add-Surface($path, $why) {
    if (-not (Test-Path $path)) { return }
    $t = Get-Content $path -Raw
    if (-not $t) { return }
    $script:bytes += $t.Length
    $parts.Add("`n<<<<<< $why`n$t`n>>>>>>`n")
}

Add-Surface (Join-Path $wiki 'OVERVIEW.md')   'OVERVIEW - what exists. Every entity in this project, no exceptions. If it is here, DO NOT REBUILD IT.'
Add-Surface (Join-Path $wiki 'DISCARDED.md')  'THE MAP - what is already a dead end. Read before proposing anything: you cannot search for a decision whose name you do not know.'
Add-Surface (Join-Path $wiki 'NAMES.md')      'NAMES - aliases to canonical. A row marked AMBIGUOUS means ASK, never guess.'
Add-Surface (Join-Path $wiki 'DECISIONS.md')  'DECISIONS - one line per durable decision. The full entry, with its evidence locator, is in the entity that owns it.'
foreach ($d in Get-ChildItem (Join-Path $wiki 'doctrine') -Filter *.md -File) {
    Add-Surface $d.FullName "DOCTRINE ($($d.Name)) - how work is done here. Read wholesale; it governs every entity, so it is never routed."
}
if ($parts.Count -eq 0) { exit 0 }

$proj = Split-Path $root -Leaf
$kb = [math]::Round($bytes / 1024)
$tok = [math]::Round($bytes / 4000, 1)

$header = @"
# WIKI v2 - the always-loaded layer for '$proj' ($evt)

These are GENERATED from docs/wiki/entities/*.md and docs/wiki/doctrine/. They are not prose to skim;
they are the index that makes the rest of the wiki cheap to reach.

  ${kb} KB / ~${tok}k tokens$genNote

How to use them, in order:
  1. NAMES      - resolve what the user said to ONE canonical entity. AMBIGUOUS means ask.
  2. OVERVIEW   - that entity's state, invariants, open defects, dependents, and how to run it.
  3. THE MAP    - has this already been tried and killed? Check before proposing.
  4. Then read  docs/wiki/entities/<the entity>.md  in full. An edit to a file is BLOCKED by
                guard-entity-read.ps1 until its owning entity has been read this session.

What is NOT here, by design: history (docs/history/, never loaded, cited by path), the v1 reference
pages still at wiki root, IDEAS.md and TASKS.md (routed by tag, on demand).
"@

$context = $header + "`n" + ($parts -join "`n")

$payload = [pscustomobject]@{
  hookSpecificOutput = [pscustomobject]@{
    hookEventName     = $evt
    additionalContext = $context
  }
  suppressOutput = $true
}
# PURE ASCII out - the wiki carries em-dashes, arrows and box characters well outside ASCII, and no
# console codepage between here and Claude Code can be trusted with them.
$json = $payload | ConvertTo-Json -Depth 6 -Compress
$out = New-Object System.Text.StringBuilder
foreach ($ch in $json.ToCharArray()) {
  if ([int]$ch -gt 126) { [void]$out.AppendFormat('\u{0:x4}', [int]$ch) } else { [void]$out.Append($ch) }
}
[Console]::Out.Write($out.ToString())
exit 0
