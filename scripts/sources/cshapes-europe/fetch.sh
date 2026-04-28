#!/bin/bash
# Fetch CShapes-Europe (pre-1886 European boundaries extension).
# Source: ETH Zürich ICR.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/cshapes-europe"
mkdir -p "$OUT_DIR"
FILE="$OUT_DIR/CShapes-Europe.geojson"
if [ ! -f "$FILE" ]; then
  curl -fL -A "Mozilla/5.0" -o "$FILE" \
    "https://icr.ethz.ch/data/cshapes/CShapes-Europe.geojson" || {
    echo ""
    echo "ERROR: automatic download failed (server may be rate-limiting this IP)."
    echo "Please download the file manually from a browser:"
    echo "  https://icr.ethz.ch/data/cshapes/CShapes-Europe.geojson"
    echo "and place it at: $FILE"
    echo "Then re-run this script."
    exit 1
  }
fi
echo "Fetched: $FILE"
