# Local image build with workarounds for Docker Desktop "rpc error ... EOF" during pip RUN.
# Usage: .\docker-build-local.ps1 -Tag "critical:latest"
param(
    [string]$Tag = "critical:latest",
    [switch]$LegacyBuilder
)

$ErrorActionPreference = "Stop"
Write-Host "Tag: $Tag" -ForegroundColor Cyan

if ($LegacyBuilder) {
    Write-Host "Using legacy builder (DOCKER_BUILDKIT=0) — slower but more stable on some Windows setups." -ForegroundColor Yellow
    $env:DOCKER_BUILDKIT = "0"
    docker build -f Dockerfile.legacy -t $Tag .
} else {
    $env:DOCKER_BUILDKIT = "1"
    # Plain progress helps spot which step failed; single merged RUN in Dockerfile reduces EOF risk
    docker build --progress=plain -t $Tag .
}

Write-Host "Done." -ForegroundColor Green
