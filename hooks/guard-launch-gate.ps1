# PreToolUse gate: Workflow (multi-agent fleet) launches must be approved against a
# MACHINE-COMPUTED audit of the actual script — never against the model's description.
# Born 2026-08-09: a "bounded, cheap-agents" launch by name ran ~1.5M tokens on inherited
# Fable because caps/models existed only as prose. This gate makes the intent-vs-mechanics
# comparison a physical precondition of the tool firing (same pattern as guard-plan-gate).
#
# Policy:
#   - name-only launch  -> DENY always (unauditable; stock scripts inherit the session model)
#   - inline `script`   -> DENY always (approved artifact must be a hashable file on disk)
#   - `scriptPath`      -> audit the file; allow ONLY if <cwd>\LAUNCH.md contains
#                          "APPROVED: GO" AND "SCRIPT-SHA256: <hash of that exact file>"
# Approval is per-script-version: any edit changes the hash and re-arms the gate.
# Resume of an approved script (same file, same hash) stays approved.
$ErrorActionPreference = 'SilentlyContinue'
$raw = [Console]::In.ReadToEnd()
# Tracer (2026-08-10): two live launches bypassed this gate on stale hashes. Log every
# invocation so the next event shows exactly what the harness sends (or proves the hook
# never ran). Trim keeps the log bounded.
$logFile = Join-Path $PSScriptRoot 'launch-gate.log'
try { Add-Content $logFile ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + $raw.Substring(0, [Math]::Min(500, $raw.Length))) } catch {}
$in = $null
try { $in = $raw | ConvertFrom-Json } catch {}
if (-not $in) {
    # Fail CLOSED: this hook only matches Workflow calls, so an unparseable event on a
    # spend surface must deny, not wave through (parse-fail was the last fail-open path).
    $out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = 'LAUNCH GATE: could not parse the hook event JSON — failing closed on a spend surface. Retry the launch.' } } | ConvertTo-Json -Depth 4 -Compress
    Write-Output $out
    exit 0
}

$name = $in.tool_input.name
$inline = $in.tool_input.script
$scriptPath = $in.tool_input.scriptPath
# Not a launch shape this gate understands (harness change / malformed) -> fail open,
# consistent with the other guards; the matcher already restricts us to Workflow calls.
if (-not ($name -or $inline -or $scriptPath)) { exit 0 }

function Deny($reason) {
    $out = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = $reason } } | ConvertTo-Json -Depth 4 -Compress
    Write-Output $out
    exit 0
}

if (-not $scriptPath) {
    if ($inline) {
        Deny ('LAUNCH GATE: inline scripts cannot be audited-and-approved (no stable artifact to hash). Write the script to a file, then relaunch via scriptPath. The gate will print a machine audit of that file for the user to approve in LAUNCH.md.')
    }
    Deny ('LAUNCH GATE: launch-by-name is blocked. Stock workflow scripts inherit the SESSION model for every agent and carry no budget gates (proven 2026-08-09, ~1.5M tokens). Author the script to a file (per-stage model: overrides, budget.spent() gates), read it end-to-end, then relaunch via scriptPath.')
}

if (-not (Test-Path $scriptPath)) {
    Deny ('LAUNCH GATE: scriptPath not found on disk (' + $scriptPath + '). Cannot audit what cannot be read.')
}

# ---- Machine audit: facts come from the file, not from the model's prose ----
$text = Get-Content $scriptPath -Raw
if (-not $text) { Deny ('LAUNCH GATE: script file is empty or unreadable (' + $scriptPath + ').') }
$hash = (Get-FileHash -Algorithm SHA256 $scriptPath).Hash
# Empty hash MUST deny: with $hash = '' the approval regex ('SCRIPT-SHA256:\s*' + '')
# matches ANY hash line and the gate falls open. Observed live 2026-08-10: a launch
# fired milliseconds after script edits slipped through on exactly this race.
if (-not $hash) { Deny ('LAUNCH GATE: could not hash the script (file locked or mid-write). Retry the launch.') }
$hash = $hash.ToLower()

$agentCalls  = ([regex]::Matches($text, '\bagent\s*\(')).Count
$modelDecls  = ([regex]::Matches($text, '\bmodel\s*:')).Count
$budgetGates = ([regex]::Matches($text, '\bbudget\.(spent|remaining)\s*\(')).Count
$metaName = if ($text -match "name\s*:\s*['`"]([^'`"]+)['`"]") { $Matches[1] } else { '(no meta name)' }

$audit = 'AUDIT of ' + $scriptPath + ' [' + $metaName + ']: ' +
    'agent() call sites=' + $agentCalls + '; ' +
    'model: declarations=' + $modelDecls + ($(if ($modelDecls -eq 0) { ' (EVERY agent inherits the session model!)' } else { '' })) + '; ' +
    'budget.spent()/remaining() gates=' + $budgetGates + ($(if ($budgetGates -eq 0) { ' (NO spend bound in code!)' } else { '' })) + '; ' +
    'SCRIPT-SHA256: ' + $hash

# ---- Approval check: LAUNCH.md in the session cwd, per-hash ----
$cwd = if ($in.cwd) { $in.cwd } else { (Get-Location).Path }
$launch = Join-Path $cwd 'LAUNCH.md'
if (Test-Path $launch) {
    $content = Get-Content $launch -Raw
    if (($content -match 'APPROVED:\s*GO') -and ($content -match ('SCRIPT-SHA256:\s*' + $hash))) { exit 0 }
    if ($content -match 'APPROVED:\s*GO') {
        Deny ('LAUNCH GATE: LAUNCH.md is approved for a DIFFERENT script version (hash mismatch — the file changed after approval). Re-present the current audit and wait for a fresh GO. ' + $audit)
    }
}
Deny ('LAUNCH GATE: no approved LAUNCH.md for this script. Write ' + $launch + ' containing the audit line below, present it to the user, and WAIT for them to add "APPROVED: GO". Facts below are machine-computed from the file; do not paraphrase them. ' + $audit)
