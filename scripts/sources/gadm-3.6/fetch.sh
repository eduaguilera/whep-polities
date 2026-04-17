#!/bin/bash
# Fetch GADM 3.6 (discontinued version).
# Source: UC Davis mirror. Follow-up: decide whether to remap the ~216
# subnational entries onto GADM 4.1.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/gadm-3.6"
mkdir -p "$OUT_DIR"
ZIP="$OUT_DIR/gadm36_levels_gpkg.zip"
curl -fL -o "$ZIP" \
  "https://biogeo.ucdavis.edu/data/gadm3.6/gadm36_levels_gpkg.zip"
(cd "$OUT_DIR" && unzip -o gadm36_levels_gpkg.zip)
echo "Fetched: $OUT_DIR/gadm36_levels.gpkg"
