#!/bin/bash
# Fetch HistoGIS 1860 Austrian Empire crownlands, then run the ad-hoc
# dissolve script to build Cisleithania/Transleithania polygons.
#
# Source: ACDH-CH (Austrian Academy of Sciences).
set -euo pipefail
PROJ_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT_DIR="$PROJ_ROOT/data/geodata/histogis-1860-habsburg"
mkdir -p "$OUT_DIR"

# 1. Download raw crownlands shapefile.
ZIP="$OUT_DIR/austrian_empire_adm2_crownlands_1860.zip"
curl -fL -o "$ZIP" \
  "https://shared.acdh.oeaw.ac.at/histogis/austrian_empire_adm2_crownlands_1860.zip"
(cd "$OUT_DIR" && unzip -o austrian_empire_adm2_crownlands_1860.zip -d crownlands_1860)

# 2. Run the dissolve script (build.py in this directory) to produce the
#    Cisleithania/Transleithania GPKG from the raw crownlands shapefile.
cd "$PROJ_ROOT"
python3 scripts/sources/histogis-1860-habsburg/build.py
echo "Fetched and processed: $OUT_DIR/habsburg_cisleithania_transleithania.gpkg"
