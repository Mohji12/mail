# Build and push to ECR in one step (linux/amd64, no attestations).
# After login: aws ecr get-login-password --region ap-south-1 | docker login ...
#
# Usage:
#   .\build-lambda-push.ps1 -EcrUri "474833638797.dkr.ecr.ap-south-1.amazonaws.com/mailing:latest"

param(
    [Parameter(Mandatory = $true)]
    [string]$EcrUri
)

$ErrorActionPreference = "Stop"
$env:DOCKER_BUILDKIT = "1"
$env:BUILDX_NO_DEFAULT_ATTESTATIONS = "1"

Write-Host "Building + pushing: $EcrUri" -ForegroundColor Cyan

docker buildx build `
    --platform linux/amd64 `
    --provenance=false `
    --sbom=false `
    -f Dockerfile `
    -t $EcrUri `
    --push `
    .

Write-Host "Done." -ForegroundColor Green
