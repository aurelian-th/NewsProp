param(
    [string]$VenvDir = ".venv"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot $VenvDir
$pythonExe = Join-Path $venvPath "Scripts\\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "[bootstrap] Creating virtual environment at $venvPath"
    python -m venv $venvPath
}

$pythonExe = Join-Path $venvPath "Scripts\\python.exe"

Write-Host "[bootstrap] Upgrading pip"
& $pythonExe -m pip install --upgrade pip

Write-Host "[bootstrap] Installing project requirements"
& $pythonExe -m pip install -r (Join-Path $repoRoot "requirements.txt")

Write-Host "[bootstrap] Environment ready"
Write-Host "[bootstrap] Python: $pythonExe"
