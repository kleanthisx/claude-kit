# PreToolUse gate (Edit|Write|NotebookEdit): do not let a file be changed until the wiki entity
# that OWNS it has been read this session.
#
# Why this exists: the two benchmarks that test obedience rather than recall found the governing
# document was never opened in ~96-97% of violations, even one grep away. Size caps and good
# intentions do not fix that; removing the decision from the model's discretion does.
# (RAG/agent-memory-research/SYNTHESIS.md §1; PLAN-WIKI-V2.md §7.)
#
# It is deliberately PERMISSIVE at the edges - it only denies when all of these hold:
#   1. the project has docs/wiki/entities/
#   2. the target file is claimed by some entity's `owns:` line
#   3. that entity's file does not appear as a tool file_path anywhere in this session's transcript
# Anything else passes. A false deny costs real work; a false allow costs one unread page.
#
# Disarm for a session:  $env:WIKI_GATE = 'off'
$ErrorActionPreference = 'SilentlyContinue'

if ($env:WIKI_GATE -eq 'off') { exit 0 }
try { $in = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }

$target = $in.tool_input.file_path
if (-not $target) { exit 0 }

# --- find the project root: nearest ancestor with docs/wiki/entities ---------
$dir = if (Test-Path $target -PathType Leaf) { Split-Path $target -Parent } else { Split-Path $target -Parent }
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
$rel = $norm
if ($norm.StartsWith($rootNorm, [StringComparison]::OrdinalIgnoreCase)) {
    $rel = $norm.Substring($rootNorm.Length).TrimStart('/')
}
$leaf = Split-Path $target -Leaf

# --- which entity owns it? --------------------------------------------------
$owner = $null; $ownerName = $null
foreach ($f in Get-ChildItem $entDir -Filter *.md -File) {
    $lines = Get-Content $f.FullName -TotalCount 14
    $ownsLine = ($lines | Where-Object { $_ -match '^owns:' }) -join ' '
    if (-not $ownsLine) { continue }
    # tokens that look like a path or a filename, plus bare directories
    $tokens = [regex]::Matches($ownsLine, '[\w][\w./\\-]*(?:\.(?:py|js|md|ps1|css|html|json|tsv|txt|jsonl)|/)') |
              ForEach-Object { $_.Value.Trim().TrimEnd(')').Replace('\', '/') }
    foreach ($t in $tokens) {
        if (-not $t) { continue }
        if ($t.EndsWith('/')) {
            if ($rel -like ($t + '*')) { $owner = $f; break }
        } elseif ($rel -ieq $t -or $rel -like ('*/' + $t) -or $leaf -ieq (Split-Path $t -Leaf)) {
            # a bare filename only counts if the owning line also names this entity's area
            if ($rel -ieq $t -or $rel -like ('*/' + $t) -or $rel -like ('*' + $t)) { $owner = $f; break }
        }
    }
    if ($owner) { $ownerName = ($lines[0] -replace '^#\s*', '').Trim(); break }
}
if (-not $owner) { exit 0 }

# --- was the owning entity read this session? -------------------------------
$tp = $in.transcript_path
if (-not $tp -or -not (Test-Path $tp)) { exit 0 }   # cannot prove it was not read -> allow

$pattern = '"file_path"\s*:\s*"[^"]*' + [regex]::Escape($owner.Name)
$seen = Select-String -Path $tp -Pattern $pattern -SimpleMatch:$false -Quiet
if ($seen) { exit 0 }

$relOwner = "docs/wiki/entities/" + $owner.Name
$reason = @"
BLOCKED: $rel is owned by the wiki entity $ownerName, and that entity has not been read this session.

Read it first:  $relOwner

It carries the four things that decide whether this edit is the right move:
  - invariants:  what must not change here, and what breaks if it does
  - open:        what is already known to be broken
  - the body:    why it is this way, and what was already tried and discarded
  - dependents:  who else this change reaches

This gate exists because a governing document one grep away is not read in ~96-97% of violations
(SYNTHESIS.md section 1). If the entity is wrong, fix the entity in the same breath as the code.
To disarm for this session: set `$env:WIKI_GATE = 'off'`.
"@

$out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
Write-Output $out
exit 0
