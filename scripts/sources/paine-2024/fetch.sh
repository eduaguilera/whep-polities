#!/bin/bash
# Fetch Paine, Qiu & Ricart-Huguet (2024) pre-colonial African states.
# Harvard Dataverse: doi:10.7910/DVN/9QJVJ1
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/paine-2024"
mkdir -p "$OUT_DIR"
# Dataverse serves the full replication archive as a ZIP via the dataset's
# access endpoint. The PCS shapefile is under Shapefiles/Precolonial states/.
ZIP="$OUT_DIR/dataverse_files.zip"
curl -fL -o "$ZIP" \
  "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/9QJVJ1"
(cd "$OUT_DIR" && unzip -o dataverse_files.zip)
# Normalize: move PCS.* up to data/geodata/paine-2024/ so the config's
# `file: data/geodata/paine-2024/PCS.shp` holds.
find "$OUT_DIR" -name 'PCS.*' -exec cp -n {} "$OUT_DIR/" \;
echo "Fetched. PCS shapefile at: $OUT_DIR/PCS.shp"
