#!/bin/bash
# Fetch Eurostat GISCO NUTS 2021 level-2 boundaries (EPSG:4326, 1:1 million).
# Source: European Commission, Eurostat GISCO.
#
# Registered for Portugal's five mainland NUTS II regions, which had no geometry of any kind:
# GADM 4.1's admin-1 layer for Portugal is its 18 DISTRICTS, and a NUTS II region cannot be built by
# unioning whole districts because the districts date from 1835 and NUTS II was delimited across them
# -- a district-built Alentejo falls 24.9% short and a district-built Norte 14.7% short. Five
# districts straddle a regional boundary (Lisboa is only 47% inside Area Metropolitana de Lisboa).
#
# The file carries all 334 NUTS-2 features for the EU, not only Portugal's, so registering it also
# gives the other NUTS-reporting countries in this table a level-2 source without a second fetch.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/eurostat-gisco-nuts"
mkdir -p "$OUT_DIR"
FILE="$OUT_DIR/nuts2_2021.geojson"
URL="https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2021_4326_LEVL_2.geojson"
if [ ! -f "$FILE" ]; then
  curl -fL -A "Mozilla/5.0" -o "$FILE" "$URL" || {
    echo ""
    echo "ERROR: automatic download failed."
    echo "Please download the file manually from a browser:"
    echo "  $URL"
    echo "and place it at: $FILE"
    echo "Then re-run this script."
    exit 1
  }
fi
echo "Fetched: $FILE"
