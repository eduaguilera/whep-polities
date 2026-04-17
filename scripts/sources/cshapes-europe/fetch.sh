#!/bin/bash
# Fetch CShapes-Europe (pre-1886 European boundaries extension).
# Source: ETH Zürich ICR.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/cshapes-europe"
mkdir -p "$OUT_DIR"
curl -fL -o "$OUT_DIR/CShapes-Europe.geojson" \
  "https://icr.ethz.ch/data/cshapes/CShapes-Europe.geojson"
echo "Fetched: $OUT_DIR/CShapes-Europe.geojson"
