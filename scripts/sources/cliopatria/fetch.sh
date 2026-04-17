#!/bin/bash
# Fetch Cliopatria (Seshat Global History Databank historical polygons).
# https://github.com/Seshat-Global-History-Databank/cliopatria
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/cliopatria"
mkdir -p "$OUT_DIR"
ZIP="$OUT_DIR/cliopatria.geojson.zip"
curl -fL -o "$ZIP" \
  "https://github.com/Seshat-Global-History-Databank/cliopatria/raw/main/cliopatria.geojson.zip"
(cd "$OUT_DIR" && unzip -o cliopatria.geojson.zip)
echo "Fetched: $OUT_DIR/cliopatria.geojson"
