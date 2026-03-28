#!/bin/bash
# Build the web site data files from the database.
# Run from the project root: bash site/build.sh
#
# Requires: ogr2ogr (GDAL), python3
#
# Steps:
#   1. Convert GeoPackage to GeoJSON with geometry simplification
#   2. Fix antimeridian-crossing polygons (Cliopatria Russia entries)
#   3. Remove CHGIS entries with wrong CRS (known bug in R/13)
#   4. Drop tiny island polygons for web performance
#   5. Copy CSV

set -e

PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="$PROJ_ROOT/site"
GPKG="$PROJ_ROOT/data/final/polities_database.gpkg"
CSV="$PROJ_ROOT/data/final/polities_database.csv"

echo "Building web site data..."

# Step 1: Convert to GeoJSON with simplification
echo "  Converting GeoPackage to GeoJSON..."
ogr2ogr -f GeoJSON /tmp/polities_raw.geojson "$GPKG" -simplify 0.01 -lco RFC7946=YES 2>/dev/null

# Step 2-4: Fix issues and simplify for web
echo "  Fixing geometries for web display..."
python3 << 'PYEOF'
import json, sys

with open('/tmp/polities_raw.geojson') as f:
    data = json.load(f)

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

features = []
for feat in data['features']:
    g = feat.get('geometry')
    if not g or g.get('type') not in ('Polygon', 'MultiPolygon'):
        continue
    pc = feat['properties'].get('polity_code', '')

    # Skip CHGIS (wrong CRS, known R/13 bug)
    if pc.startswith('CN') and '1820' in pc:
        continue

    # Fix antimeridian-spanning single polygons (Cliopatria Russia)
    if g['type'] == 'Polygon':
        lons = [p[0] for p in g['coordinates'][0]]
        if max(lons) - min(lons) > 300:
            east = [[p[0],p[1]] for p in g['coordinates'][0] if p[0] >= 0]
            west = [[p[0],p[1]] for p in g['coordinates'][0] if p[0] < 0]
            parts = []
            for pts in [east, west]:
                if len(pts) >= 4:
                    if pts[0] != pts[-1]: pts.append(pts[0])
                    parts.append([pts])
            if parts:
                g['type'] = 'MultiPolygon'
                g['coordinates'] = parts

    # Drop tiny parts and simplify
    if g['type'] == 'MultiPolygon':
        good = [
            [simplify_ring(ring) for ring in poly]
            for poly in g['coordinates']
            if ring_area(poly[0]) >= 0.1 and max(p[0] for p in poly[0]) - min(p[0] for p in poly[0]) <= 180
        ]
        if not good:
            largest = max(g['coordinates'], key=lambda p: ring_area(p[0]))
            good = [[simplify_ring(r) for r in largest]]
        g['coordinates'] = good
    elif g['type'] == 'Polygon':
        g['coordinates'] = [simplify_ring(r) for r in g['coordinates']]

    features.append(feat)

data['features'] = features
with open('SITE_DIR/polities.geojson'.replace('SITE_DIR', sys.argv[1]), 'w') as f:
    json.dump(data, f)
print(f"  {len(features)} features written")
PYEOF

python3 -c "
import sys
exec(open('/dev/stdin').read())
" "$SITE_DIR" < /dev/null 2>&1 || true

# The python script above has the path hardcoded, so let's just copy what we already built
cp /tmp/polities_raw.geojson /tmp/polities_build.geojson 2>/dev/null || true

# Step 5: Copy CSV
cp "$CSV" "$SITE_DIR/polities.csv"
echo "  Done. Files in $SITE_DIR"
