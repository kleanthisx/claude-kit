# Install the Claude Code working setup (hooks, skills, doctrine, memory) onto a machine.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -WhatIf     # show, change nothing
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Profile work
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Uninstall
#
# Design rules, in order of importance:
#   1. MERGE, never replace user entries. Old claude-kit context handlers are migrated in place;
#      unrelated settings and hooks are kept. A timestamped backup precedes any change.
#   2. Reversible. -Uninstall restores the newest backup and removes the files we copied.
#   3. The settings merge is idempotent. Kit-owned content files may be refreshed on a re-run;
#      local MEMORY.md, inject-exclude.txt, and runtime logs are preserved.
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
    [string]$UserDoctrinePath = (Join-Path $env:USERPROFILE 'CLAUDE.md'),
    [ValidateSet('work','home')] [string]$Profile = 'work',
    [string]$MemoryDir = '',
    [switch]$WithCommissar,
    [switch]$WithConclave,
    [string]$Council = 'main',
    [string[]]$ConclaveProjectRoot = @(),
    [string]$ClaudeJsonPath = (Join-Path $env:USERPROFILE '.claude.json'),
    [switch]$WhatIf,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$src       = $PSScriptRoot
$hooksDst  = Join-Path $ClaudeHome 'hooks'
$skillDst  = Join-Path $ClaudeHome 'skills'
$agentsDst = Join-Path $ClaudeHome 'agents'
$toolsDst  = Join-Path $ClaudeHome 'tools'
$commissarDst = Join-Path $ClaudeHome 'commissar'
$conclaveDst  = Join-Path $ClaudeHome 'conclave'
if ($WithConclave -and ($Council -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*$')) { throw "-Council must be a plain key (letters, digits, _ . -), got '$Council'" }
$settings  = Join-Path $ClaudeHome 'settings.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'   # one stamp per run, for every backup this run writes

function Say  { param($m) Write-Host $m }
function Act  { param($what, $action)
    if ($WhatIf) { Say "  WOULD: $what" } else { & $action; Say "  did:   $what" }
}
function Get-KitHookFiles {
    # Runtime logs and arbitrary files in hooks/ are not installable hook code. In particular,
    # launch-gate.log is gitignored but may exist in the source checkout; copying it clobbered
    # the live audit log on 2026-09-20.
    @(Get-ChildItem (Join-Path $src 'hooks') -File | Where-Object {
        $_.Extension -eq '.ps1' -or $_.Name -in @('judge-settings.json','README.md') -or
        ($WithCommissar -and $_.Name -eq 'commissar-gate.py')
    })
}
function Get-KitCommissarFiles {
    # Her code and schemas. Never state.json, config.json, doctrine.md, logs: those are hers once installed.
    @(Get-ChildItem (Join-Path $src 'commissar') -File | Where-Object {
        $_.Extension -eq '.py' -or $_.Name -like '*.schema.json' -or $_.Name -eq 'README.md'
    })
}
function Get-KitConclaveFiles {
    # The council code and its README. The operator's handoff and backlog notes are project state, not installed.
    @(Get-ChildItem (Join-Path $src 'conclave') -File | Where-Object { $_.Extension -eq '.py' -or $_.Name -eq 'README.md' })
}
function Expand-ConclaveFragment([string]$rawJson) {
    $roots = ''
    foreach ($r in $ConclaveProjectRoot) { if ($r) { $roots += " --project-root " + ($r -replace '\\','/') } }
    return $rawJson -replace '\{\{CLAUDE_HOME\}\}', ($ClaudeHome -replace '\\','/') -replace '\{\{COUNCIL\}\}', $Council -replace '\{\{PROJECT_ROOTS\}\}', $roots
}
function Remove-McpEntry([string]$name) {
    $cj = Try-ReadClaudeJson
    if ($null -eq $cj) { return }
    if ($cj.PSObject.Properties['mcpServers'] -and $cj.mcpServers.PSObject.Properties[$name] -and
        (($cj.mcpServers.$name.args -join ' ') -like "*$($ClaudeHome -replace '\\','/')/$name/*")) {
        Act "remove mcpServers.$name from $(Split-Path $ClaudeJsonPath -Leaf)" {
            Copy-Item $ClaudeJsonPath "$ClaudeJsonPath.claude-kit-$(Get-Date -Format yyyyMMdd-HHmmss).bak" -Force
            $cj.mcpServers.PSObject.Properties.Remove($name)
            Write-JsonFile $ClaudeJsonPath $cj
        }.GetNewClosure()
    }
}
function Read-JsonFile([string]$path) {
    if (Test-Path $path) { (Get-Content $path -Raw -Encoding UTF8) | ConvertFrom-Json } else { [pscustomobject]@{} }
}
function Write-JsonFile([string]$path, $obj) {
    # Set-Content -Encoding utf8 writes a BOM in PowerShell 5.1; Claude Code's own files have none.
    [System.IO.File]::WriteAllText($path, (($obj | ConvertTo-Json -Depth 20) + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}
function Try-ReadClaudeJson {
    # ~/.claude.json is Claude Code's own file. PowerShell 5.1's ConvertFrom-Json rejects keys differing only by
    # case and empty keys; if it cannot parse the file we leave it alone and say what to run by hand.
    try { return (Read-JsonFile $ClaudeJsonPath) }
    catch {
        Say "  WARNING: cannot parse $ClaudeJsonPath with this PowerShell ($($_.Exception.Message.Split([char]10)[0]))."
        Say "           MCP registration skipped. Register by hand: claude mcp add --scope user <name> -- <command>"
        return $null
    }
}
function New-InstalledMemoryIndex {
    param([string]$Dir, [string]$Tier)
    $present = @(Get-ChildItem $Dir -Filter *.md -File | Where-Object {
        $_.Name -notin @('MEMORY.md','MEMORY.personal.md')
    } | Sort-Object Name)
    $names = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($f in $present) { [void]$names.Add($f.Name) }
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $lines = New-Object 'System.Collections.Generic.List[string]'
    $lines.Add("# Memory Index - installed $Tier profile")
    $lines.Add('')
    $lines.Add('Generated from files present at installation. Existing indexes are never overwritten.')
    $lines.Add('')
    $sources = @(Join-Path $src 'memory\MEMORY.md')
    if ($Tier -eq 'home') { $sources += Join-Path $src 'memory\personal\MEMORY.personal.md' }
    foreach ($indexSource in $sources) {
        if (-not (Test-Path $indexSource)) { continue }
        foreach ($line in [System.IO.File]::ReadAllLines($indexSource, [System.Text.Encoding]::UTF8)) {
            $m = [regex]::Match($line, '^\s*-\s*\[[^]]+\]\(([^)]+\.md)\)')
            if (-not $m.Success) { continue }
            $name = [System.IO.Path]::GetFileName($m.Groups[1].Value)
            if ($names.Contains($name) -and $seen.Add($name)) { $lines.Add($line) }
        }
    }
    foreach ($f in $present) {
        if ($seen.Add($f.Name)) { $lines.Add("- [$($f.BaseName)]($($f.Name))") }
    }
    return (($lines -join "`n") + "`n")
}
function Show-MemoryIndexCoverage {
    param([string]$Dir)
    $index = Join-Path $Dir 'MEMORY.md'
    if (-not (Test-Path $index)) { return }
    $present = @(Get-ChildItem $Dir -Filter *.md -File | Where-Object {
        $_.Name -notin @('MEMORY.md','MEMORY.personal.md')
    } | ForEach-Object { $_.Name })
    $links = @([regex]::Matches([System.IO.File]::ReadAllText($index, [System.Text.Encoding]::UTF8),
        '\]\(([^)]+\.md)\)') | ForEach-Object { [System.IO.Path]::GetFileName($_.Groups[1].Value) })
    $dead = @($links | Where-Object { $present -notcontains $_ })
    $unindexed = @($present | Where-Object { $links -notcontains $_ })
    Say "  MEMORY.md coverage: $($unindexed.Count) unindexed, $($dead.Count) dead links"
    if ($unindexed.Count) { Say "    unindexed: $($unindexed -join ', ')" }
    if ($dead.Count) { Say "    dead links: $($dead -join ', ')" }
    if (Test-Path (Join-Path $Dir 'MEMORY.personal.md')) {
        Say '  WARNING: legacy MEMORY.personal.md remains; it is not copied by this installer and may duplicate the index in session context.'
    }
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
    foreach ($f in (Get-KitHookFiles)) {
        $t = Join-Path $hooksDst $f.Name
        if (Test-Path $t) { Act "remove hooks\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
    }
    foreach ($f in (Get-ChildItem (Join-Path $src 'agents') -Filter *.md -File)) {
        $t = Join-Path $agentsDst $f.Name
        if (Test-Path $t) { Act "remove agents\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
    }
    foreach ($sk in (Get-ChildItem (Join-Path $src 'skills') -Directory)) {
        $t = Join-Path $skillDst $sk.Name
        $f = Join-Path $t 'SKILL.md'
        if (Test-Path $f) { Act "remove skills\$($sk.Name)\SKILL.md" { Remove-Item $f -Force }.GetNewClosure() }
        if ((Test-Path $t) -and -not (Get-ChildItem $t -Force | Select-Object -First 1)) { Act "remove empty skills\$($sk.Name)" { Remove-Item $t -Force }.GetNewClosure() }
    }
    $fixDst = Join-Path $hooksDst 'fixtures'
    if (Test-Path $fixDst) { Act "remove hooks\fixtures" { Remove-Item $fixDst -Recurse -Force } }
    foreach ($f in (Get-ChildItem (Join-Path $src 'tools') -File)) {
        $t = Join-Path $toolsDst $f.Name
        if (Test-Path $t) { Act "remove tools\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
    }
    if (Test-Path $commissarDst) {
        foreach ($f in (Get-KitCommissarFiles)) {
            $t = Join-Path $commissarDst $f.Name
            if (Test-Path $t) { Act "remove commissar\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
        }
        $gate = Join-Path $hooksDst 'commissar-gate.py'
        if (Test-Path $gate) { Act "remove hooks\commissar-gate.py" { Remove-Item $gate -Force } }
        Say "  commissar: state.json, config.json, doctrine.md and the log are left in $commissarDst"
    }
    Remove-McpEntry 'commissar'
    if (Test-Path $conclaveDst) {
        foreach ($f in (Get-KitConclaveFiles)) {
            $t = Join-Path $conclaveDst $f.Name
            if (Test-Path $t) { Act "remove conclave\$($f.Name)" { Remove-Item $t -Force }.GetNewClosure() }
        }
        Say "  conclave: the database (default ~\.conclave\conclave.db) is left in place"
    }
    Remove-McpEntry 'conclave'
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
if ($ClaudeHome -match '\s') {
    Say "             WARNING: '$ClaudeHome' contains a space. The hook command lines in settings.json are"
    Say "             unquoted (settings/hooks.json), so every hook would fail silently. Use a ClaudeHome without"
    Say "             spaces, or quote the -File paths in the fragments before installing."
}
if ($psv -lt 5) { Say "             WARNING: these hooks are written for 5.1+." }
if ($WithConclave -and -not $WithCommissar) {
    $py = Get-Command python -ErrorAction SilentlyContinue
    Say "python     : $(if ($py) { "found ($($py.Source))" } else { 'NOT ON PATH - conclave is Python 3.11+' })"
}
if ($WithCommissar) {
    # Reported, never fixed here: the layer is installed either way and fails open in 'log' mode.
    $py = Get-Command python -ErrorAction SilentlyContinue
    Say "python     : $(if ($py) { "found ($($py.Source))" } else { 'NOT ON PATH - the commissar and her gate are Python' })"
    $node = Get-Command node -ErrorAction SilentlyContinue
    Say "node       : $(if ($node) { "found ($($node.Source))" } else { 'NOT ON PATH - codex app-server runs on node' })"
    $codexJs = Join-Path $env:APPDATA 'npm\node_modules\@openai\codex\bin\codex.js'
    Say "codex CLI  : $(if (Test-Path $codexJs) { "found ($codexJs)" } else { 'NOT INSTALLED - npm install -g @openai/codex, then: codex login' })"
    if (Test-Path $codexJs) {
        # codex prints its status on stderr; under $ErrorActionPreference='Stop' a redirected stderr line
        # becomes a terminating NativeCommandError, so read it with 'Continue' and stringify the records.
        $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $login = ((& node $codexJs login status 2>&1 | ForEach-Object { "$_" }) -join ' ').Trim()
        $ErrorActionPreference = $eap
        Say "codex login: $(if ($login) { $login } else { 'unknown (codex login status printed nothing)' })"
    }
}
Say ""

# ---------------------------------------------------------------- files
Say "files:"
foreach ($d in @($hooksDst, $skillDst)) {
    if (-not (Test-Path $d)) { Act "create $d" { New-Item -ItemType Directory -Force -Path $d | Out-Null }.GetNewClosure() }
}
foreach ($f in (Get-KitHookFiles)) {
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
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
foreach ($sk in (Get-ChildItem (Join-Path $src 'skills') -Directory)) {
    if ($sk.Name -eq 'commissar' -and -not $WithCommissar) { Say "  skip:  skills\commissar (install with -WithCommissar)"; continue }
    $t = Join-Path $skillDst $sk.Name
    if (-not (Test-Path $t)) { Act "create skills\$($sk.Name)" { New-Item -ItemType Directory -Force -Path $t | Out-Null }.GetNewClosure() }
    $skSrc = Join-Path $sk.FullName 'SKILL.md'
    $skDst = Join-Path $t 'SKILL.md'
    $body = [System.IO.File]::ReadAllText($skSrc, [System.Text.Encoding]::UTF8) -replace '\{\{CLAUDE_HOME\}\}', ($ClaudeHome -replace '\\','/')
    $same = (Test-Path $skDst) -and ([System.IO.File]::ReadAllText($skDst, [System.Text.Encoding]::UTF8) -eq $body)
    if ($same) { Say "  same:  skills\$($sk.Name)\SKILL.md" }
    else       { Act "copy skills\$($sk.Name)\SKILL.md (CLAUDE_HOME substituted)" { [System.IO.File]::WriteAllText($skDst, $body, $utf8NoBom) }.GetNewClosure() }
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
if ($WithCommissar) {
    Say ""
    Say "commissar (optional layer, -WithCommissar):"
    if (-not (Test-Path $commissarDst)) { Act "create $commissarDst" { New-Item -ItemType Directory -Force -Path $commissarDst | Out-Null }.GetNewClosure() }
    foreach ($f in (Get-KitCommissarFiles)) {
        $t = Join-Path $commissarDst $f.Name
        $same = (Test-Path $t) -and ((Get-FileHash $f.FullName).Hash -eq (Get-FileHash $t).Hash)
        if ($same) { Say "  same:  commissar\$($f.Name)" }
        else       { Act "copy commissar\$($f.Name)" { Copy-Item $f.FullName $t -Force }.GetNewClosure() }
    }
    $cfgDst = Join-Path $commissarDst 'config.json'
    if (Test-Path $cfgDst) { Say "  PRESERVED: commissar\config.json (mode/effort are hers once set)" }
    else { Act "copy commissar\config.json (mode: log)" { Copy-Item (Join-Path $src 'commissar\config.json') $cfgDst }.GetNewClosure() }
}
if ($WithConclave) {
    Say ""
    Say "conclave (optional layer, -WithConclave, council '$Council'):"
    if (-not (Test-Path $conclaveDst)) { Act "create $conclaveDst" { New-Item -ItemType Directory -Force -Path $conclaveDst | Out-Null }.GetNewClosure() }
    foreach ($f in (Get-KitConclaveFiles)) {
        $t = Join-Path $conclaveDst $f.Name
        $same = (Test-Path $t) -and ((Get-FileHash $f.FullName).Hash -eq (Get-FileHash $t).Hash)
        if ($same) { Say "  same:  conclave\$($f.Name)" }
        else       { Act "copy conclave\$($f.Name)" { Copy-Item $f.FullName $t -Force }.GetNewClosure() }
    }
}

# ---------------------------------------------------------------- doctrine
Say ""
Say "doctrine:"
$home_md = $UserDoctrinePath
if (Test-Path $home_md) {
    Say "  EXISTS: $home_md - left alone. Merge by hand; overwriting a working agreement is not"
    Say "          something an installer should decide."
} else {
    Act "install CLAUDE.md -> $home_md" { Copy-Item (Join-Path $src 'doctrine\CLAUDE.md') $home_md -Force }.GetNewClosure()
}
$rulesDst = Join-Path $ClaudeHome 'RULES.md'
if ((Test-Path $rulesDst) -and ((Get-FileHash $rulesDst).Hash -ne (Get-FileHash (Join-Path $src 'doctrine\RULES.md')).Hash)) {
    Act "backup RULES.md -> RULES.md.claude-kit-$stamp.bak" { Copy-Item $rulesDst "$rulesDst.claude-kit-$stamp.bak" -Force }.GetNewClosure()
}
Act "install RULES.md -> $ClaudeHome\RULES.md" { Copy-Item (Join-Path $src 'doctrine\RULES.md') $rulesDst -Force }.GetNewClosure()

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
        $tierFiles = @(Get-ChildItem $td -Filter *.md -File | Where-Object {
            $_.Name -ne 'MEMORY.personal.md'
        })
        $n = $tierFiles.Count
        $installedCount += $n
        Act "copy memory\$tier ($n files)" { foreach ($f in $tierFiles) { Copy-Item $f.FullName (Join-Path $MemoryDir $f.Name) -Force } }.GetNewClosure()
    }
    $indexPath = Join-Path $MemoryDir 'MEMORY.md'
    if (Test-Path $indexPath) {
        Say '  PRESERVED: existing MEMORY.md (local index; never overwrite it with a portable snapshot)'
    } else {
        Act 'create MEMORY.md from the files actually installed' {
            $body = New-InstalledMemoryIndex -Dir $MemoryDir -Tier $Profile
            [System.IO.File]::WriteAllText($indexPath, $body, (New-Object System.Text.UTF8Encoding($false)))
        }.GetNewClosure()
    }
    if (-not $WhatIf) { Show-MemoryIndexCoverage $MemoryDir }
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
    $excludeDst = Join-Path $MemoryDir 'inject-exclude.txt'
    if (Test-Path $ex) {
        if (Test-Path $excludeDst) {
            if ((Get-FileHash $ex).Hash -eq (Get-FileHash $excludeDst).Hash) {
                Say '  same:  inject-exclude.txt'
            } else {
                Say "  PRESERVED: local inject-exclude.txt differs from $(Split-Path $ex -Leaf); review and merge by hand"
            }
        } else {
            Act "copy inject-exclude.txt (source: $(Split-Path $ex -Leaf))" { Copy-Item $ex $excludeDst }.GetNewClosure()
        }
    }
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
    Act "create empty settings.json" { [System.IO.File]::WriteAllText($settings, "{}`n", (New-Object System.Text.UTF8Encoding($false))) }.GetNewClosure()
}
# -WhatIf performs no action above, so a truly fresh machine still has no file here -- read the
# virtual empty document instead of failing rule 4 ("-WhatIf shows every action and performs none").
$raw = if (Test-Path $settings) { Get-Content $settings -Raw -Encoding UTF8 } else { '{}' }
$cur = $raw | ConvertFrom-Json
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

# The old single-string SessionStart handlers were silently capped to a 2 KB preview. Replace only
# our own handlers with the numbered parts, and remove our PostCompact handlers: SessionStart runs
# again with source=compact; PostCompact cannot deliver context to the model. Preserve any other
# handlers even when they share the same event entry.
function Is-KitContextCommand($command) {
    return ([string]$command -match '(?i)[\\/](session-rules|load-wiki)\.ps1(?:\s|$)')
}
function Remove-KitContextHandlers($event) {
    if (-not $cur.hooks.PSObject.Properties[$event]) { return }
    $entries = New-Object System.Collections.ArrayList
    $removed = 0
    foreach ($entry in @($cur.hooks.$event)) {
        $all = @($entry.hooks)
        $other = @($all | Where-Object { -not ($_.command -and (Is-KitContextCommand $_.command)) })
        $removed += $all.Count - $other.Count
        if ($other.Count -eq 0) { continue }
        if ($other.Count -ne $all.Count) { $entry.hooks = $other }
        [void]$entries.Add($entry)
    }
    if ($removed -gt 0) {
        Ensure-Backup
        $cur.hooks.$event = @($entries.ToArray())
        Say "  migrated: removed $removed old $event context handler(s); user handlers preserved"
    }
}
$expectedContext = @($frag.hooks.SessionStart[0].hooks | ForEach-Object { $_.command })
$installedContext = @()
if ($cur.hooks.PSObject.Properties['SessionStart']) {
    $installedContext = @($cur.hooks.SessionStart | ForEach-Object { $_.hooks } |
        Where-Object { $_.command -and (Is-KitContextCommand $_.command) } | ForEach-Object { $_.command })
}
$contextReady = $installedContext.Count -eq $expectedContext.Count
if ($contextReady) {
    foreach ($cmd in $expectedContext) {
        if ($installedContext -notcontains $cmd) { $contextReady = $false; break }
    }
}
if (-not $contextReady) { Remove-KitContextHandlers 'SessionStart' }
Remove-KitContextHandlers 'PostCompact'

$fragments = @($frag)
$mcpToRegister = @()
if ($WithCommissar) {
    $cFragRaw = (Get-Content (Join-Path $src 'settings\commissar.json') -Raw) -replace '\{\{CLAUDE_HOME\}\}', ($ClaudeHome -replace '\\','/')
    $cFrag = $cFragRaw | ConvertFrom-Json
    $fragments += $cFrag
    $mcpToRegister += @{ name = 'commissar'; entry = $cFrag.mcpServers.commissar }
}
if ($WithConclave) {
    $vFrag = (Expand-ConclaveFragment (Get-Content (Join-Path $src 'settings\conclave.json') -Raw)) | ConvertFrom-Json
    $fragments += $vFrag
    $mcpToRegister += @{ name = 'conclave'; entry = $vFrag.mcpServers.conclave }
}
foreach ($fragment in $fragments) {
foreach ($ev in $fragment.hooks.PSObject.Properties.Name) {
    if ($ev -eq 'SessionStart' -and $contextReady -and $fragment -eq $frag) { $kept++; continue }
    if (-not $cur.hooks.PSObject.Properties[$ev]) {
        $cur.hooks | Add-Member -NotePropertyName $ev -NotePropertyValue @()
    }
    foreach ($entry in $fragment.hooks.$ev) {
        $ourCmds = @($entry.hooks | ForEach-Object { Split-Path $_.command -Leaf })
        $already = $false
        foreach ($existing in $cur.hooks.$ev) {
            foreach ($h in @($existing.hooks)) {
                if ($h.command -and ($ourCmds -contains (Split-Path $h.command -Leaf))) { $already = $true }
            }
        }
        if ($already) { $kept++ }
        else { Ensure-Backup; $cur.hooks.$ev = @($cur.hooks.$ev) + $entry; $added++ }
    }
}
}
Say "  hooks: $added to add, $kept already present"

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
    Write-JsonFile $settings $cur
    Say "  did:   write settings.json"
}

if ($mcpToRegister.Count) {
    # The MCP server list lives in ~/.claude.json, not settings.json. Add our entries, keep the rest.
    $cj = Try-ReadClaudeJson
    if ($null -eq $cj) { $cj = [pscustomobject]@{}; $mcpToRegister = @() }   # unparseable file: register nothing, write nothing
    if (-not $cj.PSObject.Properties['mcpServers']) { $cj | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }
    $cjChanged = $false
    foreach ($m in $mcpToRegister) {
        if ($cj.mcpServers.PSObject.Properties[$m.name]) {
            Say "  mcpServers.$($m.name) : already present in $(Split-Path $ClaudeJsonPath -Leaf) - left untouched"
        } else {
            $cj.mcpServers | Add-Member -NotePropertyName $m.name -NotePropertyValue $m.entry
            $cjChanged = $true
            Say "  $(if ($WhatIf) { 'WOULD: ' } else { 'did:   ' })register mcpServers.$($m.name) in $(Split-Path $ClaudeJsonPath -Leaf)"
        }
    }
    if ($cjChanged) {
        Act "write $(Split-Path $ClaudeJsonPath -Leaf) (backup first)" {
            if (Test-Path $ClaudeJsonPath) { Copy-Item $ClaudeJsonPath "$ClaudeJsonPath.claude-kit-$(Get-Date -Format yyyyMMdd-HHmmss).bak" -Force }
            Write-JsonFile $ClaudeJsonPath $cj
        }.GetNewClosure()
    }
}

Say ""
Say "Next:"
Say "  1. powershell -File tests\test-install-profile.ps1 (isolated install, no model calls)"
Say "  2. powershell -File tests\test-context-delivery.ps1 (all numbered parts under 10,000 chars)"
Say "  3. powershell -File tests\test-entity-read.ps1     (40 cases, 0 FAIL)"
Say "  4. powershell -File tests\test-hooks.ps1           (0 FAIL is the bar)"
Say "  5. powershell -File tests\test-judge-dread.ps1     (14 paid calls; run deliberately)"
Say "  6. Start a session and confirm all numbered MEMORY/WIKI parts arrive at SessionStart."
Say "  7. Judge Dread costs one 'claude -p' per turn. '/judge quiet' or '/judge off' if that"
Say "     is not the trade you want on this machine."
if ($WithCommissar) {
Say "  8. The commissar starts at the next SessionStart (python -I $commissarDst\up.py by hand). She is in"
Say "     'log' mode until '/commissar on'; her calls bill the Codex account. commissar\README.md has the rest."
}
if ($WithConclave) {
Say "  9. Conclave: register the Codex side yourself (the installer does not touch Codex's config):"
Say "       cmd /c codex.cmd mcp add conclave -- python -I $conclaveDst\mcp_server.py --actor codex --council $Council"
Say "     Restart both clients, call conclave_health in each. Hooks are wired in --mode observe; switch the"
Say "     PreToolUse entry to --mode enforce only after both pass. conclave\README.md has the protocol."
}
