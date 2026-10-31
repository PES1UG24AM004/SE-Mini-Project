<#
.SYNOPSIS
    Starts the local SQLite-backed MLflow tracking server for CodeCraft.
.DESCRIPTION
    Launches an MLflow tracking server bound strictly to localhost (127.0.0.1) on port 5000
    using a local SQLite backend database and local artifacts directory.
.NOTES
    Author: Aarav Yuval B G (PES1UG24AM004)
#>

[CmdletBinding()]
param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 5000,
    [string]$DbPath = "sqlite:///mlflow.db",
    [string]$ArtifactsPath = "./mlartifacts"
)

# 1. Resolve project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location -Path $ProjectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CodeCraft MLflow Experiment Tracking Server (Localhost)   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Working Directory : $ProjectRoot"
Write-Host "Backend Store     : $DbPath"
Write-Host "Artifact Root     : $ArtifactsPath"
Write-Host "Binding Host      : $HostAddress (Localhost only)"
Write-Host "Binding Port      : $Port"
Write-Host ""

# 2. Check for Python / Virtual Environment / MLflow
$PythonCmd = "python"
if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    $PythonCmd = "$ProjectRoot\.venv\Scripts\python.exe"
    Write-Host "[+] Using virtual environment: $ProjectRoot\.venv" -ForegroundColor Green
}

$mlflowCheck = & $PythonCmd -c "import mlflow; print(mlflow.__version__)" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($mlflowCheck)) {
    Write-Error "[!] MLflow is not installed in the active environment. Run: pip install -r requirements.txt"
    exit 1
}

Write-Host "[+] Detected MLflow version: $mlflowCheck" -ForegroundColor Green

# 3. Ensure artifacts directory exists
$ArtifactsDir = Join-Path $ProjectRoot "mlartifacts"
if (-not (Test-Path $ArtifactsDir)) {
    New-Item -ItemType Directory -Path $ArtifactsDir -Force | Out-Null
    Write-Host "[+] Created local artifacts directory: $ArtifactsDir" -ForegroundColor Gray
}

# 4. Silence telemetry and hints if desired
$env:MLFLOW_DISABLE_AGENT_HINT = "1"
$env:MLFLOW_TRACKING_URI = "http://${HostAddress}:${Port}"

Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "MLflow Tracking Server is starting..." -ForegroundColor Yellow
Write-Host "Access the Experiment Tracking UI at:" -ForegroundColor Yellow
Write-Host "   >> http://${HostAddress}:${Port} <<" -ForegroundColor White -BackgroundColor DarkGreen
Write-Host "Press Ctrl+C to terminate server." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""

# 5. Execute MLflow server
& $PythonCmd -m mlflow server `
    --backend-store-uri $DbPath `
    --default-artifact-root $ArtifactsPath `
    --host $HostAddress `
    --port $Port
