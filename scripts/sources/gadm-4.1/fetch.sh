#!/bin/bash
# Fetch GADM 4.1 multi-level GeoPackage. Source: https://gadm.org/
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/gadm-4.1"
mkdir -p "$OUT_DIR"
curl -fL -o "$OUT_DIR/gadm_410-levels.gpkg" \
  "https://geodata.ucdavis.edu/gadm/gadm4.1/gadm_410-levels.gpkg"
echo "Fetched: $OUT_DIR/gadm_410-levels.gpkg"
