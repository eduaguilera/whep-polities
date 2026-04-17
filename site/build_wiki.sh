#!/bin/bash
# Build site/polities.csv, site/polities.geojson, and a copy of the wiki
# for in-browser rendering. The master database (data/final/polities_database.gpkg)
# is authoritative; this script only trims and simplifies for web display.
#
# Run from the project root: bash site/build_wiki.sh
# Requires: ogr2ogr (GDAL), python3.

set -euo pipefail

PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="$PROJ_ROOT/site"
WIKI_DIR="$PROJ_ROOT/wiki/polities"
GPKG="$PROJ_ROOT/data/final/polities_database.gpkg"
DB_CSV="$PROJ_ROOT/data/final/polities_database.csv"

if [ ! -f "$GPKG" ]; then
  echo "ERROR: $GPKG missing. Run scripts/build_database.py first." >&2
  exit 1
fi

echo "Building site/ from wiki + master GeoPackage..."

# 1) Copy the master CSV directly — it's already the wiki-derived subset.
cp "$DB_CSV" "$SITE_DIR/polities.csv"
echo "  $(wc -l < "$SITE_DIR/polities.csv") rows → site/polities.csv"

# 2) Convert the master GeoPackage to simplified GeoJSON. Fix antimeridian
#    for polygons crossing ±180° (CShapes Russia / USA).
ogr2ogr -f GeoJSON /tmp/polities_raw.geojson "$GPKG" -simplify 0.01 -lco RFC7946=YES 2>/dev/null

python3 - "$SITE_DIR" << 'PYEOF'
import json, sys

site_dir = sys.argv[1]

def ring_area(ring):
    n = len(ring)
    if n < 3: return 0
    a = sum(ring[i][0]*ring[(i+1)%n][1] - ring[(i+1)%n][0]*ring[i][1] for i in range(n))
    return abs(a) / 2

def simplify_ring(ring, max_pts=80):
    if len(ring) <= max_pts: return ring
    step = max(1, len(ring) // max_pts)
    r = ring[::step]
    if r[-1] != ring[-1]: r.append(ring[-1])
    if r[0] != r[-1]: r.append(r[0])
    return r

with open('/tmp/polities_raw.geojson') as f:
    data = json.load(f)

kept = []
for feat in data['features']:
    g = feat.get('geometry')
    if not g or g.get('type') not in ('Polygon', 'MultiPolygon'):
        continue

    # Fix antimeridian-spanning single polygons (e.g. Russia, USA).
    if g['type'] == 'Polygon':
        lons = [p[0] for p in g['coordinates'][0]]
        if lons and max(lons) - min(lons) > 300:
            east = [[p[0], p[1]] for p in g['coordinates'][0] if p[0] >= 0]
            west = [[p[0], p[1]] for p in g['coordinates'][0] if p[0] < 0]
            parts = []
            for pts in (east, west):
                if len(pts) >= 4:
                    if pts[0] != pts[-1]:
                        pts.append(pts[0])
                    parts.append([pts])
            if parts:
                g['type'] = 'MultiPolygon'
                g['coordinates'] = parts

    # Drop tiny parts and simplify rings.
    if g['type'] == 'MultiPolygon':
        good = [
            [simplify_ring(ring) for ring in poly]
            for poly in g['coordinates']
            if ring_area(poly[0]) >= 0.1
               and max(p[0] for p in poly[0]) - min(p[0] for p in poly[0]) <= 180
        ]
        if not good:
            largest = max(g['coordinates'], key=lambda p: ring_area(p[0]))
            good = [[simplify_ring(r) for r in largest]]
        g['coordinates'] = good
    else:
        g['coordinates'] = [simplify_ring(r) for r in g['coordinates']]

    kept.append(feat)

data['features'] = kept
with open(f"{site_dir}/polities.geojson", 'w') as f:
    json.dump(data, f)
print(f"  {len(kept)} features → site/polities.geojson")
PYEOF

# 3) Copy pre-1961 crosslink outputs if present.
if [ -d "$PROJ_ROOT/data/compiled/pre1961" ]; then
  rm -rf "$SITE_DIR/pre1961"
  mkdir -p "$SITE_DIR/pre1961/by_item"
  cp "$PROJ_ROOT/data/compiled/pre1961/summary_by_polity.json" "$SITE_DIR/pre1961/" 2>/dev/null || true
  cp "$PROJ_ROOT/data/compiled/pre1961/by_item_index.json" "$SITE_DIR/pre1961/" 2>/dev/null || true
  cp "$PROJ_ROOT/data/compiled/pre1961/by_item/"*.json "$SITE_DIR/pre1961/by_item/" 2>/dev/null || true
  echo "  pre1961 crosslink data copied ($(ls $SITE_DIR/pre1961/by_item/ 2>/dev/null | wc -l) items)"
fi

# 4) Copy wiki markdown so the site can render pages in-browser.
rm -rf "$SITE_DIR/wiki"
mkdir -p "$SITE_DIR/wiki/polities" "$SITE_DIR/wiki/sources"
cp "$WIKI_DIR"/*.md "$SITE_DIR/wiki/polities/" 2>/dev/null || true
cp "$PROJ_ROOT/wiki/sources"/*.md "$SITE_DIR/wiki/sources/" 2>/dev/null || true
[ -f "$PROJ_ROOT/wiki/log.md" ]    && cp "$PROJ_ROOT/wiki/log.md"    "$SITE_DIR/wiki/"
[ -f "$PROJ_ROOT/wiki/README.md" ] && cp "$PROJ_ROOT/wiki/README.md" "$SITE_DIR/wiki/"
echo "  wiki markdown → site/wiki/"

echo "Done."
