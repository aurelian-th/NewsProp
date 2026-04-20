param(
    [string]$Source = "paper/tex/NewsProp.tex",
    [string]$OutputDir = "paper/build"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $repoRoot $Source
$outDir = Join-Path $repoRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$tectonicPath = $null
$cmd = Get-Command tectonic -ErrorAction SilentlyContinue
if ($cmd) {
    $tectonicPath = $cmd.Source
}

$tectonicCandidates = @(
    $tectonicPath,
    (Join-Path $repoRoot "tools\\tectonic\\tectonic.exe")
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $tectonicCandidates -or $tectonicCandidates.Count -eq 0) {
    throw "Tectonic was not found on PATH or at tools\\tectonic\\tectonic.exe. Install Tectonic before building the paper."
}

$tectonic = $tectonicCandidates | Select-Object -First 1
Write-Host "[paper] Using Tectonic: $tectonic"
Write-Host "[paper] Building: $sourcePath"

& $tectonic "--outdir" $outDir $sourcePath

Write-Host "[paper] Output written to $outDir"
