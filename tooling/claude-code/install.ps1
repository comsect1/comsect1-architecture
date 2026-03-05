# comsect1 Architecture - Claude Code AIAD Setup
# Installs rules, sub-agent, and skill to ~/.claude/
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File tooling\claude-code\install.ps1
#
# Existing files are backed up as .bak before overwriting.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$ClaudeHome = Join-Path $env:USERPROFILE ".claude"
$Placeholder = "{{COMSECT1_ROOT}}"

# Files to install: source (relative to ScriptDir) -> target (relative to ClaudeHome)
$Files = @{
    "agents\comsect1-reviewer\AGENT.md"    = "agents\comsect1-reviewer\AGENT.md"
    "skills\comsect1-analyze\SKILL.md"     = "skills\comsect1-analyze\SKILL.md"
    "rules\comsect1.md"                    = "rules\comsect1.md"
}

Write-Host "comsect1 Architecture - Claude Code AIAD Setup"
Write-Host "================================================"
Write-Host ""
Write-Host "  Repo root:    $RepoRoot"
Write-Host "  Claude home:  $ClaudeHome"
Write-Host ""

$installed = 0
$backedUp = 0

foreach ($srcRel in $Files.Keys) {
    $tgtRel = $Files[$srcRel]
    $src = Join-Path $ScriptDir $srcRel
    $tgt = Join-Path $ClaudeHome $tgtRel
    $tgtDir = Split-Path -Parent $tgt

    # Create target directory if needed
    if (-not (Test-Path $tgtDir)) {
        New-Item -ItemType Directory -Path $tgtDir -Force | Out-Null
    }

    # Backup existing file
    if (Test-Path $tgt) {
        Copy-Item $tgt "$tgt.bak" -Force
        Write-Host "  [backup]  $tgt -> $tgt.bak"
        $backedUp++
    }

    # Substitute placeholder and write
    $content = Get-Content $src -Raw -Encoding UTF8
    $content = $content -replace [regex]::Escape($Placeholder), $RepoRoot
    Set-Content -Path $tgt -Value $content -Encoding UTF8 -NoNewline
    Write-Host "  [install] $tgt"
    $installed++
}

Write-Host ""
Write-Host "Done."
Write-Host "  Installed: $installed file(s)"
Write-Host "  Backed up: $backedUp file(s)"
Write-Host ""
Write-Host "The installed files reference: $RepoRoot\specs\"
Write-Host "Run 'git pull' in the spec repo to get updates - no reinstall needed."
