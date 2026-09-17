# Test suite for guard-entity-read.ps1 -- runs the real hook with real stdin, no mocking of the hook.
# Ported from the source machine's home test to a tiny in-repo fixture project so it needs no
# machine-specific path: fixtures\wiki-v2-project\ (two entities, three owned files, one un-owned).
$ErrorActionPreference = 'Stop'
$hook = Join-Path $PSScriptRoot '..\hooks\guard-entity-read.ps1'
$root = Join-Path $PSScriptRoot 'fixtures\wiki-v2-project'
$tmp  = Join-Path $env:TEMP ('entgate-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

# two fake transcripts: one that read the widget entity, one that read nothing relevant
$tRead = Join-Path $tmp 'read.jsonl'
$tCold = Join-Path $tmp 'cold.jsonl'
$widgetEntity = (Join-Path $root 'docs\wiki\entities\svc-widget.md') -replace '\\', '\\'
$readmePath   = (Join-Path $root 'README.md') -replace '\\', '\\'
"{`"type`":`"assistant`",`"message`":{`"content`":[{`"type`":`"tool_use`",`"name`":`"Read`",`"input`":{`"file_path`":`"$widgetEntity`"}}]}}" | Set-Content $tRead -Encoding utf8
"{`"type`":`"assistant`",`"message`":{`"content`":[{`"type`":`"tool_use`",`"name`":`"Read`",`"input`":{`"file_path`":`"$readmePath`"}}]}}" | Set-Content $tCold -Encoding utf8

function Invoke-Gate($file, $transcript) {
    $payload = @{ cwd = $root; transcript_path = $transcript; tool_input = @{ file_path = $file } } | ConvertTo-Json -Depth 4 -Compress
    $out = $payload | & powershell -NoProfile -ExecutionPolicy Bypass -File $hook 2>$null
    if ($out) { return 'DENY' } else { return 'ALLOW' }
}

$cases = @(
  @{ n='owned file, entity NOT read  -> DENY ';  f="$root\widget\serve.py";                        t=$tCold; want='DENY'  }
  @{ n='owned file, entity WAS read  -> ALLOW';  f="$root\widget\serve.py";                        t=$tRead; want='ALLOW' }
  @{ n='unowned file                 -> ALLOW';  f="$root\README-nonexistent.md";                  t=$tCold; want='ALLOW' }
  @{ n='the wiki itself              -> ALLOW';  f="$root\docs\wiki\entities\svc-widget.md";        t=$tCold; want='ALLOW' }
  @{ n='history                      -> ALLOW';  f="$root\docs\history\log.md";                     t=$tCold; want='ALLOW' }
  @{ n='project without entities/    -> ALLOW';  f=(Join-Path $tmp 'SOMETHING.md');                 t=$tCold; want='ALLOW' }
  @{ n='second entity, unread file   -> DENY ';  f="$root\tracker\state.py";                        t=$tCold; want='DENY'  }
  @{ n='same entity, other owned file-> DENY ';  f="$root\widget\config.py";                        t=$tCold; want='DENY'  }
)

$pass = 0; $fail = 0
foreach ($c in $cases) {
    $got = Invoke-Gate $c.f $c.t
    if ($got -eq $c.want) { $pass++; Write-Host ("  PASS  " + $c.n) -ForegroundColor Green }
    else { $fail++; Write-Host ("  FAIL  " + $c.n + "  got=$got want=" + $c.want) -ForegroundColor Red }
}

# disarm switch
$env:WIKI_GATE = 'off'
$got = Invoke-Gate "$root\widget\serve.py" $tCold
$env:WIKI_GATE = $null
if ($got -eq 'ALLOW') { $pass++; Write-Host "  PASS  WIKI_GATE=off             -> ALLOW" -ForegroundColor Green }
else { $fail++; Write-Host "  FAIL  WIKI_GATE=off  got=$got" -ForegroundColor Red }

Remove-Item $tmp -Recurse -Force
Write-Host ""
Write-Host ("$pass passed, $fail failed") -ForegroundColor $(if ($fail) { 'Red' } else { 'Green' })
exit $(if ($fail) { 1 } else { 0 })
