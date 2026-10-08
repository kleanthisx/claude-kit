# PreToolUse gate (Edit|Write|NotebookEdit): do not let a file be changed until every wiki page
# directly related to it has been read this session.
#
# Why this exists: the two benchmarks that test obedience rather than recall found the governing
# document was never opened in ~96-97% of violations, even one grep away. Size caps and good
# intentions do not fix that; removing the decision from the model's discretion does.
# (claude-kit wiki-v2/SYNTHESIS.md section 1; wiki-v2/DESIGN.md section 13.)
#
# The read set (wiki-v2/WIKI-PRIMER.md, ruling 6): every page in docs/wiki/entities/ or
# docs/wiki/ledgers/ whose owns: line covers the file, every page named on their depends: and
# dependents: lines, and every page whose depends: line names one of them (dependents are generated
# from depends:, so an authored dependents: line is not trusted alone).
#
# owns: entries (the same rule as wiki-v2/coverage.py): paths relative to the project root. An entry
# owns that exact file, or everything under it when it is a folder (trailing / optional), or what it
# matches when it is a glob (* or ?). Backtick-quote a path with spaces; backslashes count as /. A bare
# word counts as a path when it contains / \ . or *, or names a FILE at the project root (Makefile); a
# folder needs its / (a prose word that happens to name a folder claims nothing). A path with a :line
# locator is a citation, not a claim. Page names (kind:namespace/name) on the line are ignored. A bare
# name does NOT match at other depths: README.md owns ./README.md, not docs/README.md.
#
# It denies when the target is inside a project that has docs/wiki/entities/, some page owns it, and
# the transcript does not show, for every page in the read set, successful Read results of its current
# version that together contain every numbered line (chunked reads add up). A request, a grep hit, a
# failed read or an older read is not proof. A NEW unowned script written with Write is also denied,
# to catch ad hoc replacement runners. Everything else passes, including when no transcript is
# available. Shell edits are outside this Edit|Write|NotebookEdit hook.
#
# This file must stay pure ASCII: Windows PowerShell 5.1 reads a BOM-less file as cp1252.
# Disarm for a session:  $env:WIKI_GATE = 'off'
$ErrorActionPreference = 'SilentlyContinue'

if ($env:WIKI_GATE -eq 'off') { exit 0 }
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }

$target = $in.tool_input.file_path
if (-not $target) { $target = $in.tool_input.notebook_path }   # NotebookEdit
if (-not $target) { exit 0 }

# --- find the project root: nearest ancestor with docs/wiki/entities ---------
$dir = Split-Path $target -Parent
if (-not $dir) { $dir = $in.cwd }
$root = $null
$probe = $dir
for ($i = 0; $i -lt 8 -and $probe; $i++) {
    if (Test-Path (Join-Path $probe 'docs\wiki\entities')) { $root = $probe; break }
    $probe = Split-Path $probe -Parent
}
if (-not $root -and $in.cwd -and (Test-Path (Join-Path $in.cwd 'docs\wiki\entities'))) { $root = $in.cwd }
if (-not $root) { exit 0 }

$entDir = Join-Path $root 'docs\wiki\entities'

# never gate the wiki itself - you must always be able to fix the map
$norm = ($target -replace '\\', '/')
if ($norm -match '/docs/(wiki|history)/') { exit 0 }

# --- relative path of the target, for matching against owns: ----------------
$rootNorm = ($root -replace '\\', '/').TrimEnd('/')
# a file outside the project is not this wiki's business (the root can come from the cwd)
if (-not $norm.StartsWith($rootNorm + '/', [StringComparison]::OrdinalIgnoreCase)) { exit 0 }
$rel = $norm.Substring($rootNorm.Length).TrimStart('/')

function Get-OwnsTokens([string]$ownsLine, $rootNames) {
    # field names and page names are case-sensitive (lowercase), as in generate.py and coverage.py
    $value = $ownsLine -creplace '^owns:\s*', ''
    $tokens = New-Object System.Collections.Generic.List[string]
    foreach ($m in [regex]::Matches($value, '`([^`]+)`')) { $tokens.Add($m.Groups[1].Value.Trim()) }
    $bare = ($value -replace '`[^`]*`', ' ') -creplace '\b[a-z]+:[a-z0-9-]+/[a-z0-9-]+', ' '
    foreach ($w in ($bare -split '\s+-\s+|[\s,;]+')) {
        $t = $w.Trim().Trim('(', ')').TrimEnd('.', ':').Replace('\', '/')
        if (-not $t -or $t -eq '-') { continue }
        if ($t -match '[/.*]' -or $rootNames -contains $t) { $tokens.Add($t) }
    }
    $clean = foreach ($t in $tokens) {
        $t = $t.Replace('\', '/')
        if ($t -match ':\d+(-\d+)?$') { continue }   # file:line is a citation, not a claim
        if ($t.StartsWith('./')) { $t = $t.Substring(2) }
        if ($t) { $t }
    }
    return @($clean)
}

function Test-Owns([string]$relPath, [string]$t) {
    # only * and ? are wildcards: the -like escape character (backtick) and [ ] are escaped, so they are literal
    if ($t.Contains('*') -or $t.Contains('?')) {
        return ($relPath -like $t.Replace('`', '``').Replace('[', '`[').Replace(']', '`]'))
    }
    $t = $t.TrimEnd('/')
    if ($relPath -ieq $t) { return $true }
    return $relPath.StartsWith($t + '/', [StringComparison]::OrdinalIgnoreCase)
}

# --- which pages own it? ALL of them: one file can hold several components --------------------
$ledDir = Join-Path $root 'docs\wiki\ledgers'
$allPages = @(Get-ChildItem $entDir -Filter *.md -File) + @(Get-ChildItem $ledDir -Filter *.md -File)
$rootNames = @(Get-ChildItem $root -Force -File | ForEach-Object { $_.Name })   # root FILES only
$owners = New-Object System.Collections.Generic.List[object]
foreach ($f in $allPages) {
    $lines = Get-Content $f.FullName -TotalCount 14 -Encoding UTF8
    $ownsLine = ($lines | Where-Object { $_ -cmatch '^owns:' }) -join ' '
    if (-not $ownsLine) { continue }
    $hit = $false
    foreach ($t in (Get-OwnsTokens $ownsLine $rootNames)) {
        if (Test-Owns $rel $t) { $hit = $true; break }
    }
    if ($hit) { $owners.Add(@{ File = $f; Name = (($lines[0] -replace '^#\s*', '').Trim()); Lines = $lines }) }
}
if ($owners.Count -eq 0) {
    # A new script with no wiki owner is the exact shape of an ad hoc replacement runner.
    # This gate does not cover shell-based file creation; it only sees Write/Edit calls.
    $inProject = $norm.StartsWith($rootNorm + '/', [StringComparison]::OrdinalIgnoreCase)
    if ($in.tool_name -eq 'Write' -and $inProject -and -not (Test-Path $target) -and
        $rel -match '(?i)\.(py|ps1|sh|js|ts|mjs|cjs|bat|cmd)$') {
        $reason = "BLOCKED: new script $rel has no owning wiki entity. Before creating a replacement runner, " +
            'read the existing run path in the wiki. If a new script is genuinely required, add its ' +
            'path to the appropriate entity owns: line and explain why the existing path cannot be used.'
        $out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
        Write-Output $out
    }
    exit 0
}
$ownerName = ($owners | ForEach-Object { $_.Name }) -join ', '

# --- the read set: every owning page, plus every page named in their depends: (the parts it is
# --- made of) and dependents: (who uses it) lines, plus every page whose depends: names an owner
$required = @{}
$refs = New-Object System.Collections.Generic.List[string]
foreach ($o in $owners) {
    $full = [System.IO.Path]::GetFullPath($o.File.FullName)
    $required[$full.ToLowerInvariant()] = @{ Path = $full; Name = $o.Name }
    $rel2 = ($o.Lines | Where-Object { $_ -cmatch '^(depends|dependents):' }) -join ' '
    foreach ($m in [regex]::Matches($rel2, '\b[a-z]+:[a-z0-9-]+/[a-z0-9-]+')) { $refs.Add($m.Value) }
}
$ownerNames = @($owners | ForEach-Object { $_.Name })
foreach ($f in $allPages) {
    $head = Get-Content $f.FullName -TotalCount 14 -Encoding UTF8
    $first = (($head[0]) -replace '^#\s*', '').Trim()
    $itsDeps = ($head | Where-Object { $_ -cmatch '^depends:' }) -join ' '
    $usesOwner = $false
    foreach ($on in $ownerNames) { if ($itsDeps -cmatch ('(^|[^a-z0-9/-])' + [regex]::Escape($on) + '($|[^a-z0-9-])')) { $usesOwner = $true; break } }
    if ($refs -ccontains $first -or $usesOwner) {
        $full = [System.IO.Path]::GetFullPath($f.FullName)
        if (-not $required.ContainsKey($full.ToLowerInvariant())) {
            $required[$full.ToLowerInvariant()] = @{ Path = $full; Name = $first }
        }
    }
}
foreach ($k in @($required.Keys)) {
    $required[$k].Lines = [System.IO.File]::ReadAllLines($required[$k].Path).Length
    $required[$k].Modified = (Get-Item $required[$k].Path).LastWriteTimeUtc
}

# --- which of them have a complete, successful Read of their current version this session? ----
# A Read result numbers each line: "   12<TAB>text" or "   12<RIGHTWARDS ARROW>text" (U+2192, built
# here from its code point so this file stays ASCII).
$lineNumberRx = '(?m)^\s*(\d+)\s*[\t' + [char]0x2192 + ']'
$tp = $in.transcript_path
# no transcript = nothing can be proven either way: permissive at the edge, as everywhere else
if (-not $tp -or -not (Test-Path $tp)) { exit 0 }
$seenSet = New-Object 'System.Collections.Generic.HashSet[string]'
$linesSeen = @{}   # page key -> line numbers seen so far; chunked reads (offset/limit) add up
$idToKey = @{}
foreach ($line in [System.IO.File]::ReadLines($tp)) {
    if ($line -notmatch '"name"\s*:\s*"Read"|"type"\s*:\s*"tool_result"') { continue }
    try { $record = $line | ConvertFrom-Json } catch { continue }
    if ($record.type -eq 'assistant') {
        foreach ($block in @($record.message.content)) {
            if ($block.type -ne 'tool_use' -or $block.name -ne 'Read' -or -not $block.id) { continue }
            try { $key = [System.IO.Path]::GetFullPath([string]$block.input.file_path).ToLowerInvariant() }
            catch { continue }
            if (-not $required.ContainsKey($key)) { continue }
            $idToKey[[string]$block.id] = $key
        }
    } elseif ($record.type -eq 'user') {
        foreach ($block in @($record.message.content)) {
            if ($block.type -ne 'tool_result') { continue }
            $key = $idToKey[[string]$block.tool_use_id]
            if (-not $key -or $seenSet.Contains($key)) { continue }
            if ($block.is_error) { continue }
            try { $readTime = [DateTimeOffset]::Parse([string]$record.timestamp).UtcDateTime }
            catch { continue }
            if ($readTime -lt $required[$key].Modified) { continue }
            $body = if ($block.content -is [string]) { [string]$block.content }
                    else { (@($block.content) | Where-Object { $_.type -eq 'text' } |
                            ForEach-Object { [string]$_.text }) -join "`n" }
            if (-not $body -or $body -match '<persisted-output>|Output truncated') { continue }
            if (-not $linesSeen.ContainsKey($key)) { $linesSeen[$key] = New-Object 'System.Collections.Generic.HashSet[int]' }
            foreach ($m in [regex]::Matches($body, $lineNumberRx)) {
                [void]$linesSeen[$key].Add([int]$m.Groups[1].Value)
            }
            $need = $required[$key].Lines
            if ($linesSeen[$key].Count -lt $need) { continue }
            $complete = $true
            for ($i = 1; $i -le $need; $i++) { if (-not $linesSeen[$key].Contains($i)) { $complete = $false; break } }
            if ($complete) { [void]$seenSet.Add($key) }
        }
    }
    if ($seenSet.Count -eq $required.Count) { break }
}
$missing = @($required.Keys | Where-Object { -not $seenSet.Contains($_) })
if ($missing.Count -eq 0) { exit 0 }

$rootFull = [System.IO.Path]::GetFullPath($root).TrimEnd('\')
$list = ($missing | ForEach-Object {
    $r = $required[$_]
    '  ' + $r.Name.PadRight(36) + ' ' + ($r.Path.Substring($rootFull.Length + 1) -replace '\\', '/')
}) -join "`n"
$reason = @"
BLOCKED: $rel is owned by $ownerName. A thing is not changed without knowing every part directly related to it: every owning page, every page in their depends: (its parts) and dependents: (what uses it) lines needs a complete, successful Read of its current version this session.

Not yet read:
$list

The owning page carries invariants (what must not change), open (what is already broken), the body (why it is this way, what was tried and discarded). Its depends: pages are its parts; its dependents: pages are what a change here can break.

This gate exists because a governing document one grep away is not read in ~96-97% of violations
(SYNTHESIS.md section 1). If a page is wrong, fix it in the same breath as the code.
To disarm for this session: set `$env:WIKI_GATE = 'off'`.
"@

$out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
Write-Output $out
exit 0
