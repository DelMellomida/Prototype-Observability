<#
Runs the OpenTelemetry Collector Docker container using a local env file for secrets.

Usage:
  - Place your real ingestion key in `config/collector.env` (copy from collector.env.example)
  - Run from repo root in PowerShell:
      .\config\run-collector.ps1

This script is intended for non-Kubernetes environments and is repeatable across services/hosts.
Do NOT commit `config/collector.env` to source control.
#>

param(
    [string]$EnvFile = "config\collector.env",
    [string]$ConfigFile = "config\otel-collector-config.yaml",
    [string]$Image = "otel/opentelemetry-collector-contrib:latest"
)

# Resolve paths relative to script location when relative paths are provided
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Helper: resolve relative paths by checking CWD first, then script dir, then fallback to scriptDir\leaf
function Resolve-RelativePath($path) {
    if ([System.IO.Path]::IsPathRooted($path)) { return $path }

    $cwdCandidate = Join-Path (Get-Location) $path
    if (Test-Path $cwdCandidate) { return (Resolve-Path $cwdCandidate).Path }

    $scriptCandidate = Join-Path $scriptDir $path
    if (Test-Path $scriptCandidate) { return (Resolve-Path $scriptCandidate).Path }

    # Fallback: use script dir + leaf name (handles cases like 'config\collector.env' when script is in 'config')
    $leaf = Split-Path $path -Leaf
    $fallback = Join-Path $scriptDir $leaf
    return $fallback
}

if (-not [System.IO.Path]::IsPathRooted($EnvFile)) { $EnvFile = Resolve-RelativePath $EnvFile }
if (-not [System.IO.Path]::IsPathRooted($ConfigFile)) { $ConfigFile = Resolve-RelativePath $ConfigFile }

if (-not (Test-Path $EnvFile)) {
    Write-Host "Env file '$EnvFile' not found. Copy 'config/collector.env.example' -> 'config/collector.env' and fill in your key." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $ConfigFile)) {
    Write-Host "Collector config '$ConfigFile' not found." -ForegroundColor Red
    exit 1
}

# Resolve absolute paths for mounting
$absConfig = (Resolve-Path $ConfigFile).Path
$absEnv = (Resolve-Path $EnvFile).Path

Write-Host "Starting OpenTelemetry Collector using config: $absConfig" -ForegroundColor Green
Write-Host "Using env file: $absEnv" -ForegroundColor Green

# Run Docker container with the env-file injected (PowerShell-safe invocation)
$dockerArgs = @(
        'run', '--rm',
        '-p', '4317:4317',
        '-p', '4318:4318',
        '-p', '13133:13133',
        '--env-file', $absEnv,
        '-v', "${absConfig}:/etc/otel-collector-config.yaml:ro",
        $Image,
        '--config', '/etc/otel-collector-config.yaml'
)

Write-Host "Running: docker $($dockerArgs -join ' ')" -ForegroundColor Cyan
& docker @dockerArgs
