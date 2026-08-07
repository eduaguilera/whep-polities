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
  # Added 2026-08-05 for issue 56: MDV-1800-2025's CShapes polygon measures 24 km2
  # against an official ~300, because CShapes captures only part of the atoll chain.
  MDV
  # Added 2026-08-05 for issues 155 and 156. LBY: occupied Libya 1943-1951 was THREE separately
  # administered territories and the database has a polygon for none of them -- TRP-1943-1951 and
  # CYR-1949-1951 carry polygon_source `none`, and Fezzan has no row at all. FAO 1952 states the
  # partition exactly (Cyrenaica 855,400 + Fezzan 551,100 + Tripolitania 353,000 = 1,759,500 =
  # Libya), so adm1 regions can be unioned to each territory and asserted against those figures.
  # DEU: the Saar. SAA-1947-1957 and SAC-1935-1947 receive 133 layer-B rows between them with no
  # geometry, and neither cshapes-europe nor cliopatria carries a Saar feature -- checked, both
  # return zero matches. GADM adm1 is the only remaining route.
  LBY DEU
  DMA ESH ESP FJI FLK FRO FSM GIB GLP GRD GRL GUF GUM HMD IOT KIR KNA LCA
  LIE LUX MAF MCO MHL MNP MSR MTQ MYT NCL NFK NIU NRU PCN PLW PRI PSE PYF
  REU SGS SHN SJM SLB SMR SPM SWE SYC SXM TCA TKL TON TUV UMI VAT VCT VGB
  VIR VUT WLF WSM
  # Added 2026-08-05: the 1940-44 Northern Transylvania holding is built from eight
  # Romanian adm1 counties (issues 12, 106). CShapes cannot supply it -- the territory
  # is interior to both of its Romanian steps, because post-war Romania kept it.
  ROU
)

ADM0="$OUT_DIR/gadm41_adm0.gpkg"
ADM1="$OUT_DIR/gadm41_adm1.gpkg"
ADM2="$OUT_DIR/gadm41_adm2.gpkg"
rm -f "$ADM0" "$ADM1" "$ADM2"

# Level 2 is built for a SHORT EXPLICIT LIST, not for every country, because a global adm2 extract
# is far larger than anything here needs and the per-country files already on disk can be re-read
# at any time. Extend this list, not the COUNTRIES loop.
#
# IDN added 2026-08-07: IDN-BLB-1949-1951 is Bali and LOMBOK, and adm1 cannot separate Lombok from
# Sumbawa -- Nusa Tenggara Barat contains both, so the adm1 union measured 25,261 km2 against the
# page's declared 10,505 (140% over) and the builder was left unregistered for it. At adm2 Lombok
# is five districts (Lombok Barat/Tengah/Timur/Utara plus Mataram) totalling 4,570 km2, and
# Bali + Lombok = 10,160, which is 3.3% of the declared figure. IDN-OTH-1949-1951 is the
# complement of Java and Bali/Lombok, so it was blocked behind the same thing.
ADM2_COUNTRIES=(IDN)

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
  # Level 2 (admin-2 / districts) -- only for the countries named in ADM2_COUNTRIES
  for want in "${ADM2_COUNTRIES[@]}"; do
    if [ "$iso" = "$want" ] && ogrinfo -q "$CFILE" 2>/dev/null | grep -q 'ADM_ADM_2'; then
      if [ ! -f "$ADM2" ]; then
        ogr2ogr -f GPKG -nln polygons "$ADM2" "$CFILE" ADM_ADM_2
      else
        ogr2ogr -f GPKG -update -append -nln polygons "$ADM2" "$CFILE" ADM_ADM_2
      fi
    fi
  done
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
[ -f "$ADM2" ] && echo "Wrote: $ADM2 (countries: ${ADM2_COUNTRIES[*]})"
