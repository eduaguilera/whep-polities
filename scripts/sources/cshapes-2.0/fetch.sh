#!/bin/bash
# Fetch CShapes 2.0 GeoPackage. Source: ETH Zürich ICR.
# https://icr.ethz.ch/data/cshapes/
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/cshapes-2.0"
mkdir -p "$OUT_DIR"
curl -fL -o "$OUT_DIR/CShapes-2.0.gpkg" \
  "https://icr.ethz.ch/data/cshapes/CShapes-2.0.gpkg"
echo "Fetched: $OUT_DIR/CShapes-2.0.gpkg"
