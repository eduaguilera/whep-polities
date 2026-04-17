#!/bin/bash
# Fetch CHGIS v6 (China Historical GIS). Harvard Dataverse.
# https://dataverse.harvard.edu/dataverse/chgis
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/chgis-v6"
mkdir -p "$OUT_DIR"
ZIP="$OUT_DIR/chgis_v6.zip"
# Confirm DOI at https://dataverse.harvard.edu/dataverse/chgis
curl -fL -o "$ZIP" \
  "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/FYWHEE" \
  || { echo "FAIL — confirm DOI at https://dataverse.harvard.edu/dataverse/chgis" >&2; exit 1; }
(cd "$OUT_DIR" && unzip -o chgis_v6.zip)
echo "Fetched CHGIS v6 into $OUT_DIR/"
