# Use the CLASSIC Docker builder (BuildKit OFF). It never adds OCI provenance/SBOM layers
# that trigger: ImageLayerFailure / UnsupportedImageLayerDetected on Lambda.
#
# Best on: Windows or Linux PC with x86_64 (image matches Lambda "x86_64" directly).
# On Apple Silicon: use .\build-lambda.ps1 instead (buildx + --platform linux/amd64).
#
# Usage:
#   .\build-lambda-legacy.ps1 -Tag "474833638797.dkr.ecr.ap-south-1.amazonaws.com/critical:latest"
#   docker push (same tag)

param(
    [Parameter(Mandatory = $false)]
    [string]$Tag = "cric:local"
)

$ErrorActionPreference = "Stop"
$env:DOCKER_BUILDKIT = "0"
$env:COMPOSE_DOCKER_CLI_BUILD = "0"

Write-Host "Building with legacy Docker engine (DOCKER_BUILDKIT=0) — no attestation layers..." -ForegroundColor Cyan

docker build -f Dockerfile.legacy -t $Tag .

Write-Host "Done. Image: $Tag" -ForegroundColor Green
Write-Host "Push: docker push $Tag" -ForegroundColor DarkGray
