#!/bin/bash
# Fetch Cliopatria polities (Seshat-linked historical polygons).
# Exact release URL varies; confirm at: https://github.com/majkshkurti/cliopatria/releases
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/cliopatria"
mkdir -p "$OUT_DIR"
curl -fL -o "$OUT_DIR/cliopatria.geojson" \
  "https://github.com/majkshkurti/cliopatria/releases/download/v0.1.3/cliopatria.geojson" \
  || { echo "FAIL — confirm URL at https://github.com/majkshkurti/cliopatria/releases" >&2; exit 1; }
echo "Fetched: $OUT_DIR/cliopatria.geojson"
