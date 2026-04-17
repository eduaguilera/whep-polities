#!/bin/bash
# Fetch CShapes-Europe (pre-1886 European boundaries extension).
# Source: ETH Zürich ICR.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/cshapes-europe"
mkdir -p "$OUT_DIR"
# Exact URL TBD — ICR publishes Europe variants under the CShapes project.
# Update when the correct URL is confirmed at:
# https://icr.ethz.ch/data/cshapes/
curl -fL -o "$OUT_DIR/CShapes-europe.gpkg" \
  "https://icr.ethz.ch/data/cshapes/CShapes-europe.gpkg" \
  || { echo "FAIL — update URL in this script" >&2; exit 1; }
echo "Fetched: $OUT_DIR/CShapes-europe.gpkg"
