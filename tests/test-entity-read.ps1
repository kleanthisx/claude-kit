# Test suite for guard-entity-read.ps1 -- runs the real hook with real stdin, no mocking of the hook.
# Ported from the source machine's home test to a tiny in-repo fixture project so it needs no
# machine-specific path: fixtures\wiki-v2-project\ (two entities, three owned files, one un-owned).
$ErrorActionPreference = 'Stop'
$hook = Join-Path $PSScriptRoot '..\hooks\guard-entity-read.ps1'
$root = Join-Path $PSScriptRoot 'fixtures\wiki-v2-project'
$tmp  = Join-Path $env:TEMP ('entgate-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

# Fake transcripts cover a complete result, a request without a result, a short excerpt,
# and a failed result. Merely naming the path must not disarm the gate.
$tRead = Join-Path $tmp 'read.jsonl'
$tCold = Join-Path $tmp 'cold.jsonl'
$tRequest = Join-Path $tmp 'request-only.jsonl'
$tPartial = Join-Path $tmp 'partial.jsonl'
$tFailed = Join-Path $tmp 'failed.jsonl'
$tStale = Join-Path $tmp 'stale.jsonl'
$widgetEntity = Join-Path $root 'docs\wiki\entities\svc-widget.md'
$readmePath = Join-Path $root 'README.md'
$lineCount = [System.IO.File]::ReadAllLines($widgetEntity).Length
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Make-Transcript($path, $file, $limit, $result, $failed, $stale) {
    $inputArgs = @{ file_path = $file }
    if ($limit) { $inputArgs.limit = $limit }
    $request = @{ type='assistant'; message=@{ content=@(
        @{ type='tool_use'; name='Read'; id='toolu_test'; input=$inputArgs }
    ) } } | ConvertTo-Json -Depth 10 -Compress
    $records = @($request)
    if ($result) {
        $seenLines = if ($limit) { [Math]::Min($limit, $lineCount) } else { $lineCount }
        $body = ((1..$seenLines | ForEach-Object { "    $_`tcontent" }) -join "`n")
        $when = if ($stale) { (Get-Item $widgetEntity).LastWriteTimeUtc.AddMinutes(-1) }
                else { [DateTime]::UtcNow.AddMinutes(1) }
        $reply = @{ type='user'; timestamp=$when.ToString('o'); message=@{ content=@(
            @{ type='tool_result'; tool_use_id='toolu_test'; is_error=$failed; content=$body }
        ) } } | ConvertTo-Json -Depth 10 -Compress
        $records += $reply
    }
    [System.IO.File]::WriteAllLines($path, $records, $utf8)
}
Make-Transcript $tRead $widgetEntity 0 $true $false $false
Make-Transcript $tCold $readmePath 0 $true $false $false
Make-Transcript $tRequest $widgetEntity 0 $false $false $false
Make-Transcript $tPartial $widgetEntity 3 $true $false $false
Make-Transcript $tFailed $widgetEntity 0 $true $true $false
Make-Transcript $tStale $widgetEntity 0 $true $false $true

function Invoke-Gate($file, $transcript, $tool = 'Edit') {
    if (-not $tool) { $tool = 'Edit' }
    $payload = @{ cwd = $root; transcript_path = $transcript; tool_name = $tool; tool_input = @{ file_path = $file } } | ConvertTo-Json -Depth 4 -Compress
    $out = $payload | & powershell -NoProfile -ExecutionPolicy Bypass -File $hook 2>$null
    if ($out) { return 'DENY' } else { return 'ALLOW' }
}

$cases = @(
  @{ n='owned file, entity NOT read  -> DENY ';  f="$root\widget\serve.py";                        t=$tCold; want='DENY'  }
  @{ n='owned file, full Read result -> ALLOW'; f="$root\widget\serve.py";                        t=$tRead; want='ALLOW' }
  @{ n='Read request without result -> DENY';  f="$root\widget\serve.py";                        t=$tRequest; want='DENY' }
  @{ n='first three lines only      -> DENY';  f="$root\widget\serve.py";                        t=$tPartial; want='DENY' }
  @{ n='failed Read result          -> DENY';  f="$root\widget\serve.py";                        t=$tFailed; want='DENY' }
  @{ n='stale Read result           -> DENY';  f="$root\widget\serve.py";                        t=$tStale; want='DENY' }
  @{ n='unowned file                 -> ALLOW';  f="$root\README-nonexistent.md";                  t=$tCold; want='ALLOW' }
  @{ n='new unowned script on Write -> DENY';   f="$root\widget\suite_run.py";                    t=$tCold; tool='Write'; want='DENY' }
  @{ n='existing unowned file       -> ALLOW';  f="$root\README.md";                              t=$tCold; tool='Write'; want='ALLOW' }
  @{ n='the wiki itself              -> ALLOW';  f="$root\docs\wiki\entities\svc-widget.md";        t=$tCold; want='ALLOW' }
  @{ n='history                      -> ALLOW';  f="$root\docs\history\log.md";                     t=$tCold; want='ALLOW' }
  @{ n='project without entities/    -> ALLOW';  f=(Join-Path $tmp 'SOMETHING.md');                 t=$tCold; want='ALLOW' }
  @{ n='second entity, unread file   -> DENY ';  f="$root\tracker\state.py";                        t=$tCold; want='DENY'  }
  @{ n='same entity, other owned file-> DENY ';  f="$root\widget\config.py";                        t=$tCold; want='DENY'  }
)

$pass = 0; $fail = 0
foreach ($c in $cases) {
    $got = Invoke-Gate $c.f $c.t $c.tool
    if ($got -eq $c.want) { $pass++; Write-Host ("  PASS  " + $c.n) -ForegroundColor Green }
    else { $fail++; Write-Host ("  FAIL  " + $c.n + "  got=$got want=" + $c.want) -ForegroundColor Red }
}

# --- the read set and the owns: rule, on a project built here (2026-10-08) ---------------------
# app:web/site depends on component:web/grid, so a change to a grid file needs the site page too
# (dependents are derived from depends:), and a change to a site file needs the grid page (a part).
$rs = Join-Path $tmp 'readset'
$rsEnt = Join-Path $rs 'docs\wiki\entities'
$rsLed = Join-Path $rs 'docs\wiki\ledgers'
foreach ($d in @($rsEnt, $rsLed, "$rs\src\views", "$rs\shared", "$rs\scripts", "$rs\docs dir", "$rs\web", "$rs\data",
                 "$rs\lib", "$rs\nb", "$rs\pkg\deep", "$rs\sub", "$tmp\elsewhere")) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}
foreach ($f in @('src\app.py', 'src\views\grid.ts', 'src\views\observe.py', 'shared\util.py', 'scripts\bench.sh',
                 'docs dir\notes.txt', 'web\other.txt', 'data\a.csv', 'Makefile', 'README2.md', 'README.md',
                 'sub\README.md', 'lib\x.py', 'nb\n.ipynb', 'src\main.py', 'pkg\deep\y.py')) {
    [System.IO.File]::WriteAllText((Join-Path $rs $f), "x`n", $utf8)
}
[System.IO.File]::WriteAllText("$tmp\elsewhere\README.md", "x`n", $utf8)
function Write-Page($path, $name, $owns, $depends) {
    $text = @("# $name", 'aka:         -', 'state:       LIVE - test page', "owns:        $owns",
              "depends:     $depends", 'dependents:  -', 'invariants:  -', 'open:        -',
              'verified:    2026-10-08 - test', 'index:       -', '', '## What it is', '', 'A test page.')
    [System.IO.File]::WriteAllLines($path, $text, $utf8)
}
Write-Page "$rsEnt\app-web-site.md"    'app:web/site'      'src/app.py - Makefile, the main entry, e.g. startup' 'component:web/grid'
Write-Page "$rsEnt\component-web-grid.md" 'component:web/grid' 'src/views/grid.ts' '-'
Write-Page "$rsEnt\tool-web-a.md"      'tool:web/a'        'shared/util.py - `docs dir/notes.txt` - data/*.csv' '-'
Write-Page "$rsEnt\tool-web-b.md"      'tool:web/b'        'shared/util.py - used by layer:web/x' '-'
Write-Page "$rsLed\bench.md"           'ledger:web/bench'  'scripts/bench.sh' '-'
Write-Page "$rsEnt\tool-web-c.md"      'tool:web/c'        'lib\ - src/main.py:12 - nb/ - pkg/deep - README.md' '-'
$pSite = "$rsEnt\app-web-site.md"; $pGrid = "$rsEnt\component-web-grid.md"
$pA = "$rsEnt\tool-web-a.md"; $pB = "$rsEnt\tool-web-b.md"; $pBench = "$rsLed\bench.md"
# a long page, read in chunks: chunked reads must add up
$pLong = "$rsEnt\tool-web-long.md"
Write-Page $pLong 'tool:web/long' 'shared/long.txt' '-'
Add-Content -LiteralPath $pLong -Value (1..60 | ForEach-Object { "line $_" }) -Encoding UTF8
[System.IO.File]::WriteAllText("$rs\shared\long.txt", "x`n", $utf8)

$rsSeq = 0
function Read-Transcript($name, $paths) {
    $records = @()
    foreach ($p in $paths) {
        $script:rsSeq++; $id = "toolu_rs_$($script:rsSeq)"
        $lines = [System.IO.File]::ReadAllLines($p)
        $body = (1..$lines.Count | ForEach-Object { "{0,6}`t{1}" -f $_, $lines[$_ - 1] }) -join "`n"
        $records += (@{ type='assistant'; message=@{ content=@(@{ type='tool_use'; id=$id; name='Read'; input=@{ file_path=$p } }) } } | ConvertTo-Json -Depth 8 -Compress)
        $records += (@{ type='user'; timestamp=[DateTime]::UtcNow.AddMinutes(1).ToString('o'); message=@{ content=@(@{ type='tool_result'; tool_use_id=$id; content=$body }) } } | ConvertTo-Json -Depth 8 -Compress)
    }
    $path = Join-Path $tmp "$name.jsonl"
    [System.IO.File]::WriteAllLines($path, [string[]]$records, $utf8)
    return $path
}
function Read-Chunks($name, $path, $chunks) {
    # chunks: pairs of (offset, limit); offset is the first line number shown, as in the Read tool
    $lines = [System.IO.File]::ReadAllLines($path); $records = @()
    foreach ($c in $chunks) {
        $script:rsSeq++; $id = "toolu_rs_$($script:rsSeq)"
        $from = [int]$c[0]; $to = [Math]::Min($lines.Count, $from + [int]$c[1] - 1)
        $body = ($from..$to | ForEach-Object { "{0,6}`t{1}" -f $_, $lines[$_ - 1] }) -join "`n"
        $records += (@{ type='assistant'; message=@{ content=@(@{ type='tool_use'; id=$id; name='Read'; input=@{ file_path=$path; offset=$c[0]; limit=$c[1] } }) } } | ConvertTo-Json -Depth 8 -Compress)
        $records += (@{ type='user'; timestamp=[DateTime]::UtcNow.AddMinutes(1).ToString('o'); message=@{ content=@(@{ type='tool_result'; tool_use_id=$id; content=$body }) } } | ConvertTo-Json -Depth 8 -Compress)
    }
    $p = Join-Path $tmp "$name.jsonl"
    [System.IO.File]::WriteAllLines($p, [string[]]$records, $utf8)
    return $p
}
$longLines = [System.IO.File]::ReadAllLines($pLong).Length
$rChunks   = Read-Chunks 'rs-chunks' $pLong @(@(1, 30), @(31, 100))
# the leading comma keeps a single pair from being unrolled into two separate numbers
$rHalf     = Read-Chunks 'rs-half' $pLong @(,@(1, 30))
$rOffset1  = Read-Chunks 'rs-offset1' $pLong @(,@(1, 1000))
$rNone     = Read-Transcript 'rs-none' @()
$rGrid     = Read-Transcript 'rs-grid' @($pGrid)
$rGridSite = Read-Transcript 'rs-grid-site' @($pGrid, $pSite)
$rSite     = Read-Transcript 'rs-site' @($pSite)
$rA        = Read-Transcript 'rs-a' @($pA)
$rAB       = Read-Transcript 'rs-ab' @($pA, $pB)

function Invoke-GateAt($file, $transcript, $tool) {
    if (-not $tool) { $tool = 'Edit' }
    $ti = if ($tool -eq 'NotebookEdit') { @{ notebook_path = $file } } else { @{ file_path = $file } }
    $payload = @{ cwd = $rs; transcript_path = $transcript; tool_name = $tool; tool_input = $ti } | ConvertTo-Json -Depth 4 -Compress
    $out = $payload | & powershell -NoProfile -ExecutionPolicy Bypass -File $hook 2>$null
    if ($out) { return 'DENY' } else { return 'ALLOW' }
}
$rsCases = @(
  @{ n='.ts file, nothing read                 -> DENY ';  f="$rs\src\views\grid.ts";    t=$rNone;     want='DENY'  }
  @{ n='.ts file, owner read, user not         -> DENY ';  f="$rs\src\views\grid.ts";    t=$rGrid;     want='DENY'  }
  @{ n='.ts file, owner + user (site) read     -> ALLOW';  f="$rs\src\views\grid.ts";    t=$rGridSite; want='ALLOW' }
  @{ n='site file, owner read, part not        -> DENY ';  f="$rs\src\app.py";           t=$rSite;     want='DENY'  }
  @{ n='site file, owner + part read           -> ALLOW';  f="$rs\src\app.py";           t=$rGridSite; want='ALLOW' }
  @{ n='root file without extension (Makefile) -> DENY ';  f="$rs\Makefile";             t=$rNone;     want='DENY'  }
  @{ n='bare name matches at a segment only    -> ALLOW';  f="$rs\src\views\observe.py"; t=$rNone;     want='ALLOW' }
  @{ n='quoted owns path with a space          -> DENY ';  f="$rs\docs dir\notes.txt";   t=$rNone;     want='DENY'  }
  @{ n='glob owns (data/*.csv)                 -> DENY ';  f="$rs\data\a.csv";           t=$rNone;     want='DENY'  }
  @{ n='page name in owns claims no folder     -> ALLOW';  f="$rs\web\other.txt";        t=$rNone;     want='ALLOW' }
  @{ n='prose word "e.g." claims nothing       -> ALLOW';  f="$rs\README2.md";           t=$rNone;     want='ALLOW' }
  @{ n='two owners, one read                   -> DENY ';  f="$rs\shared\util.py";       t=$rA;        want='DENY'  }
  @{ n='two owners, both read                  -> ALLOW';  f="$rs\shared\util.py";       t=$rAB;       want='ALLOW' }
  @{ n='ledger page owns a script              -> DENY ';  f="$rs\scripts\bench.sh";     t=$rNone;     want='DENY'  }
  @{ n='backslash folder in owns (lib\)        -> DENY ';  f="$rs\lib\x.py";             t=$rNone;     want='DENY'  }
  @{ n='file:line in owns is a citation        -> ALLOW';  f="$rs\src\main.py";          t=$rNone;     want='ALLOW' }
  @{ n='folder without trailing slash          -> DENY ';  f="$rs\pkg\deep\y.py";        t=$rNone;     want='DENY'  }
  @{ n='root README.md owner, root file        -> DENY ';  f="$rs\README.md";            t=$rNone;     want='DENY'  }
  @{ n='root README.md owner, sub/README.md    -> ALLOW';  f="$rs\sub\README.md";        t=$rNone;     want='ALLOW' }
  @{ n='file outside the project (cwd = proj)  -> ALLOW';  f="$tmp\elsewhere\README.md"; t=$rNone;     want='ALLOW' }
  @{ n='NotebookEdit on an owned notebook      -> DENY ';  f="$rs\nb\n.ipynb";           t=$rNone;     want='DENY'; tool='NotebookEdit' }
  @{ n='no transcript available                -> ALLOW';  f="$rs\src\views\grid.ts";    t='';         want='ALLOW' }
  @{ n='long page read in two chunks           -> ALLOW';  f="$rs\shared\long.txt";      t=$rChunks;   want='ALLOW' }
  @{ n='long page, only the first chunk        -> DENY ';  f="$rs\shared\long.txt";      t=$rHalf;     want='DENY'  }
  @{ n='full read with offset 1                -> ALLOW';  f="$rs\shared\long.txt";      t=$rOffset1;  want='ALLOW' }
)
foreach ($c in $rsCases) {
    $got = Invoke-GateAt $c.f $c.t $c.tool
    if ($got -eq $c.want) { $pass++; Write-Host ("  PASS  " + $c.n) -ForegroundColor Green }
    else { $fail++; Write-Host ("  FAIL  " + $c.n + "  got=$got want=" + $c.want) -ForegroundColor Red }
}

# disarm switch
$env:WIKI_GATE = 'off'
$got = Invoke-Gate "$root\widget\serve.py" $tCold
$env:WIKI_GATE = $null
if ($got -eq 'ALLOW') { $pass++; Write-Host "  PASS  WIKI_GATE=off             -> ALLOW" -ForegroundColor Green }
else { $fail++; Write-Host "  FAIL  WIKI_GATE=off  got=$got" -ForegroundColor Red }

$safeTemp = [System.IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
$resolvedTemp = [System.IO.Path]::GetFullPath($tmp)
if ($resolvedTemp.StartsWith($safeTemp, [System.StringComparison]::OrdinalIgnoreCase) -and
    [System.IO.Path]::GetFileName($resolvedTemp).StartsWith('entgate-')) {
    Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
}
Write-Host ""
Write-Host ("$pass passed, $fail failed") -ForegroundColor $(if ($fail) { 'Red' } else { 'Green' })
exit $(if ($fail) { 1 } else { 0 })
