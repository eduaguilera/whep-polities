#!/bin/bash
# Fetch GADM 4.1 per-country GeoPackages, then build two combined files:
#   gadm41_adm0.gpkg  — country-level features keyed by GID_0
#   gadm41_adm1.gpkg  — admin-1 features keyed by GID_1
# These correspond to the two source slugs `gadm-4.1-adm0` and `gadm-4.1-adm1`
# in scripts/sources.yaml.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/gadm-4.1"
mkdir -p "$OUT_DIR"

# Countries currently cited by the wiki. Extend as more polities use GADM.
COUNTRIES=(ATG BHS BRB CHN ESP FJI GRD GRL NCL PRI PYF SLB LCA SWE VCT)

ADM0="$OUT_DIR/gadm41_adm0.gpkg"
ADM1="$OUT_DIR/gadm41_adm1.gpkg"
rm -f "$ADM0" "$ADM1"

for iso in "${COUNTRIES[@]}"; do
  CFILE="$OUT_DIR/gadm41_${iso}.gpkg"
  if [ ! -f "$CFILE" ]; then
    curl -fL -o "$CFILE" "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_${iso}.gpkg"
    echo "Fetched: $CFILE"
  fi
  # Level 0 (country outline)
  if ogrinfo -q "$CFILE" 2>/dev/null | grep -q 'ADM_ADM_0'; then
    if [ ! -f "$ADM0" ]; then
      ogr2ogr -f GPKG -nln polygons "$ADM0" "$CFILE" ADM_ADM_0
    else
      ogr2ogr -f GPKG -update -append -nln polygons "$ADM0" "$CFILE" ADM_ADM_0
    fi
  fi
  # Level 1 (admin-1 / provinces)
  if ogrinfo -q "$CFILE" 2>/dev/null | grep -q 'ADM_ADM_1'; then
    if [ ! -f "$ADM1" ]; then
      ogr2ogr -f GPKG -nln polygons "$ADM1" "$CFILE" ADM_ADM_1
    else
      ogr2ogr -f GPKG -update -append -nln polygons "$ADM1" "$CFILE" ADM_ADM_1
    fi
  fi
done
echo "Wrote: $ADM0"
echo "Wrote: $ADM1"
