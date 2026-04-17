#!/bin/bash
# Constructed polygons (hand-authored: Antarctic sector claims, Uqair Protocol,
# point buffers). Stored in-repo under data/geodata/constructed/constructed.geojson.
#
# This fetch script is a stub — there's no external source to download.
# To populate, hand-edit data/geodata/constructed/constructed.geojson directly.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/constructed"
mkdir -p "$OUT_DIR"
if [ ! -f "$OUT_DIR/constructed.geojson" ]; then
  cat > "$OUT_DIR/constructed.geojson" <<'EOF'
{"type": "FeatureCollection", "features": []}
EOF
  echo "Seeded empty: $OUT_DIR/constructed.geojson"
else
  echo "Already exists: $OUT_DIR/constructed.geojson"
fi
