param(
    [switch]$DisableTranslation,
    [switch]$DisableEmbeddings,
    [int]$Phase3Nodes = 1000,
    [int]$Runs = 10,
    [int]$Ticks = 80,
    [string]$Phase2OutputDir = "phase2/outputs/autonomous",
    [string]$Phase3OutputDir = "outputs/phase3_network",
    [string]$Phase45OutputDir = "outputs/phase45",
    [int]$Seed = 42
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$bootstrapScript = Join-Path $PSScriptRoot "bootstrap_env.ps1"

Write-Host "[pipeline] Bootstrapping environment"
powershell -ExecutionPolicy Bypass -File $bootstrapScript

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"

$phase2Args = @(
    "phase2/pipeline.py",
    "--output-dir", $Phase2OutputDir
)

if ($DisableTranslation) {
    $phase2Args += "--disable-translation"
}

if ($DisableEmbeddings) {
    $phase2Args += "--disable-embeddings"
}

Write-Host "[pipeline] Running Phase 2"
& $pythonExe @phase2Args

$phase2Normalized = Join-Path $repoRoot ($Phase2OutputDir -replace "/", "\")
$phase2Normalized = Join-Path $phase2Normalized "normalized_with_phase2.json"

Write-Host "[pipeline] Running Phase 3"
& $pythonExe "run_phase3_network.py" "--nodes" $Phase3Nodes "--output-dir" $Phase3OutputDir

$phase3Payload = Join-Path $repoRoot ($Phase3OutputDir -replace "/", "\")
$phase3Payload = Join-Path $phase3Payload "mesa_payload_phase3.json"

Write-Host "[pipeline] Running Phase 4/5"
& $pythonExe "run_phase45.py" `
    "--phase2-normalized" $phase2Normalized `
    "--phase3-payload" $phase3Payload `
    "--runs" $Runs `
    "--ticks" $Ticks `
    "--num-agents" $Phase3Nodes `
    "--seed" $Seed `
    "--output-dir" $Phase45OutputDir

Write-Host "[pipeline] Completed successfully"
