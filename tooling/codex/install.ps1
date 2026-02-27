$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$ScriptPath = Join-Path $RepoRoot "scripts\comsect1_ai_tooling.py"

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $ScriptPath install --tool codex @args
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $ScriptPath install --tool codex @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $ScriptPath install --tool codex @args
} else {
    throw "Python 3 is required to run comsect1 AI tooling."
}

exit $LASTEXITCODE
