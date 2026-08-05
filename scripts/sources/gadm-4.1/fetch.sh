#!/bin/bash
# Fetch GADM 4.1 per-country GeoPackages, then build two combined files:
#   gadm41_adm0.gpkg  — country-level features keyed by GID_0
#   gadm41_adm1.gpkg  — admin-1 features keyed by GID_1
# These correspond to the two source slugs `gadm-4.1-adm0` and `gadm-4.1-adm1`
# in scripts/sources.yaml.
set -euo pipefail
OUT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/data/geodata/gadm-4.1"
mkdir -p "$OUT_DIR"

# Countries and territories currently cited by the wiki or by derived
# reporting-area polygons. Extend as more polities use GADM.
COUNTRIES=(
  ABW AIA AND ASM ATF ATG BEL BES BHS BMU BRB BVT CCK CHN COK CUW CYM CXR
  GBR IRL STP
  # Added 2026-08-04: ALK-1867-1959 needs USA.2_1 (Alaska) and both RYU rows need
  # JPN.38_1 (Okinawa). Their polygon_source and polygon_feature_id were already
  # correct; the features were simply absent from this extract, so the build logged
  # 'feature not found' and attached nothing. See issue 59.
  USA JPN
  # Added 2026-08-05: the remaining polygon gaps in issue 59 are GADM unions or a
  # complement over these three. CAN-1800-1866 needs Ontario/Quebec/New Brunswick/
  # Nova Scotia/PEI; PTIND-1816-1961 needs Goa/Daman/Diu and FRIN-1816-1954 needs
  # Puducherry/Karikal/Mahe/Yanam; the three IDN-* rows need Java, Madura, Bali and
  # Lombok. None of them can be built while the extract lacks the country.
  CAN IND IDN
  DMA ESH ESP FJI FLK FRO FSM GIB GLP GRD GRL GUF GUM HMD IOT KIR KNA LCA
  LIE LUX MAF MCO MHL MNP MSR MTQ MYT NCL NFK NIU NRU PCN PLW PRI PSE PYF
  REU SGS SHN SJM SLB SMR SPM SWE SYC SXM TCA TKL TON TUV UMI VAT VCT VGB
  VIR VUT WLF WSM
)

ADM0="$OUT_DIR/gadm41_adm0.gpkg"
ADM1="$OUT_DIR/gadm41_adm1.gpkg"
rm -f "$ADM0" "$ADM1"

for iso in "${COUNTRIES[@]}"; do
  CFILE="$OUT_DIR/gadm41_${iso}.gpkg"
  if [ ! -f "$CFILE" ]; then
    if curl -fL -o "$CFILE" "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_${iso}.gpkg"; then
      echo "Fetched: $CFILE"
    else
      rm -f "$CFILE"
      echo "WARN: GADM 4.1 has no fetchable file for ${iso}; skipping." >&2
      continue
    fi
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
