#!/bin/bash
# Fetch CShapes 2.0. Source: ETH Zürich ICR.
# https://icr.ethz.ch/data/cshapes/
#
# ICR publishes CShapes in Shapefile, GeoJSON, CSV, SQL, and R-package
# formats (not GeoPackage). We grab the Shapefile.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/cshapes-2.0"
mkdir -p "$OUT_DIR"
ZIP="$OUT_DIR/CShapes-2.0.zip"
curl -fL -o "$ZIP" "https://icr.ethz.ch/data/cshapes/CShapes-2.0.zip"
(cd "$OUT_DIR" && unzip -o CShapes-2.0.zip)
echo "Fetched CShapes 2.0 shapefile into $OUT_DIR/"
