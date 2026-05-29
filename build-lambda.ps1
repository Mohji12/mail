# Build a Lambda-compatible image (linux/amd64, no OCI attestations — Lambda rejects them).
# If this STILL fails in Lambda, use .\build-lambda-legacy.ps1 (classic builder, no BuildKit).
#
# Usage: .\build-lambda.ps1 -Tag "474833638797.dkr.ecr.ap-south-1.amazonaws.com/critical:latest"
param(
    [Parameter(Mandatory = $false)]
    [string]$Tag = "cric:local"
)

$ErrorActionPreference = "Stop"
$env:DOCKER_BUILDKIT = "1"
$env:BUILDX_NO_DEFAULT_ATTESTATIONS = "1"

Write-Host "Buildx: linux/amd64, gzip layers, provenance/sbom off, attestations disabled..." -ForegroundColor Cyan
Write-Host "(Lambda can reject zstd/OCI attestation layers; we force gzip + no attestations.)" -ForegroundColor DarkGray

# -o type=docker,compression=gzip avoids zstd-compressed layers some Docker versions use (Lambda may reject zstd).
docker buildx build `
    --platform linux/amd64 `
    --provenance=false `
    --sbom=false `
    -o "type=docker,compression=gzip" `
    -f Dockerfile `
    -t $Tag `
    .

Write-Host "Done. Image: $Tag" -ForegroundColor Green
Write-Host "ECR: aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 474833638797.dkr.ecr.ap-south-1.amazonaws.com" -ForegroundColor DarkGray
Write-Host "     docker push $Tag" -ForegroundColor DarkGray
