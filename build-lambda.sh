#!/usr/bin/env bash
# Build a Lambda-compatible image (linux/amd64, no OCI attestations).
set -euo pipefail
TAG="${1:-cric:local}"
export DOCKER_BUILDKIT=1
export BUILDX_NO_DEFAULT_ATTESTATIONS=1

echo "Building for linux/amd64 with attestations disabled (Lambda requirement)..."
docker buildx build \
  --platform linux/amd64 \
  --provenance false \
  --sbom false \
  --load \
  -f Dockerfile \
  -t "$TAG" \
  .

echo "Done. Image: $TAG"
