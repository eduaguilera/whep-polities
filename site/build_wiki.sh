#!/bin/bash
# Build the web site data files from WIKI content (source of truth).
# Only polities with wiki pages appear on the map.
# Run from the project root: bash site/build_wiki.sh
#
# Requires: ogr2ogr (GDAL), python3

set -e

PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="$PROJ_ROOT/site"
WIKI_DIR="$PROJ_ROOT/wiki/polities"
GPKG="$PROJ_ROOT/data/final/polities_database.gpkg"

echo "Building web site from wiki content..."

# Step 1: Extract frontmatter from wiki pages into CSV
echo "  Extracting wiki frontmatter..."
python3 - "$WIKI_DIR" "$SITE_DIR" "$PROJ_ROOT/data/final/polities_database.csv" << 'PYEOF'
import os, sys, csv

wiki_dir = sys.argv[1]
site_dir = sys.argv[2]
db_csv   = sys.argv[3]

# Parse YAML-like frontmatter from wiki pages
wiki_rows = {}
for fname in sorted(os.listdir(wiki_dir)):
    if not fname.endswith('.md') or fname == '_template.md' or fname.startswith('_'):
        continue
    path = os.path.join(wiki_dir, fname)
    with open(path) as f:
        lines = f.readlines()
    if not lines or lines[0].strip() != '---':
        continue
    fm = {}
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip()
    code = fm.get('polity_code', '').strip()
    if code:
        wiki_rows[code] = fm

print(f"  Found {len(wiki_rows)} wiki pages with frontmatter")

# Read the database CSV to get columns the wiki doesn't store
# (continent, polygon_source, predecessor, successor, etc.)
db_data = {}
with open(db_csv) as f:
    reader = csv.DictReader(f)
    db_headers = reader.fieldnames
    for row in reader:
        db_data[row['polity_code']] = row

# Build wiki-filtered CSV: only rows that have wiki pages
out_path = os.path.join(site_dir, 'polities.csv')
fieldnames = db_headers if db_headers else [
    'polity_code','polity_name','start_year','end_year','duration_years',
    'polity_type','continent','iso3_code','cow_code','polygon_source',
    'predecessor','successor','data_sources','verification_status','notes'
]

written = 0
missing_from_db = 0
with open(out_path, 'w', newline='') as f:
    # Add wiki_status column
    out_fields = list(fieldnames) + ['wiki_status']
    writer = csv.DictWriter(f, fieldnames=out_fields)
    writer.writeheader()
    for code, fm in sorted(wiki_rows.items()):
        if code in db_data:
            row = dict(db_data[code])
            # Override with wiki frontmatter values (wiki is source of truth)
            row['polity_code'] = code
            row['polity_name'] = fm.get('polity_name', row.get('polity_name', ''))
            row['start_year'] = fm.get('start_year', row.get('start_year', ''))
            row['end_year'] = fm.get('end_year', row.get('end_year', ''))
            row['polity_type'] = fm.get('type', row.get('polity_type', ''))
            row['wiki_status'] = fm.get('status', 'draft')
            writer.writerow(row)
            written += 1
        else:
            # Wiki page exists but no CSV row — still include with wiki data
            row = {h: 'NA' for h in fieldnames}
            row['polity_code'] = code
            row['polity_name'] = fm.get('polity_name', code)
            row['start_year'] = fm.get('start_year', '')
            row['end_year'] = fm.get('end_year', '')
            row['polity_type'] = fm.get('type', 'national')
            row['continent'] = 'NA'
            row['wiki_status'] = fm.get('status', 'draft')
            writer.writerow(row)
            written += 1
            missing_from_db += 1

print(f"  Wrote {written} rows to {out_path} ({missing_from_db} wiki-only, no DB row)")
PYEOF

# Step 2: Convert GeoPackage to GeoJSON, filtered to wiki polity codes
echo "  Converting GeoPackage to GeoJSON (wiki-filtered)..."
ogr2ogr -f GeoJSON /tmp/polities_raw.geojson "$GPKG" -simplify 0.01 -lco RFC7946=YES 2>/dev/null

# Step 3: Filter and fix geometries
echo "  Filtering to wiki polities and fixing geometries..."
python3 - "$SITE_DIR" "$WIKI_DIR" << 'PYEOF'
import json, sys, os

site_dir = sys.argv[1]
wiki_dir = sys.argv[2]

# Get wiki polity codes
wiki_codes = set()
for fname in os.listdir(wiki_dir):
    if not fname.endswith('.md') or fname == '_template.md' or fname.startswith('_'):
        continue
    with open(os.path.join(wiki_dir, fname)) as f:
        for line in f:
            if line.strip() == '---':
                break
            if line.startswith('polity_code:'):
                wiki_codes.add(line.split(':', 1)[1].strip())

# Need to read past first --- to get to frontmatter
wiki_codes = set()
for fname in os.listdir(wiki_dir):
    if not fname.endswith('.md') or fname == '_template.md' or fname.startswith('_'):
        continue
    with open(os.path.join(wiki_dir, fname)) as f:
        lines = f.readlines()
    if not lines or lines[0].strip() != '---':
        continue
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if line.startswith('polity_code:'):
            wiki_codes.add(line.split(':', 1)[1].strip())

print(f"  {len(wiki_codes)} wiki polity codes found")

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
skipped = 0
for feat in data['features']:
    g = feat.get('geometry')
    if not g or g.get('type') not in ('Polygon', 'MultiPolygon'):
        continue
    pc = feat['properties'].get('polity_code', '')

    # Only include wiki-verified polities
    if pc not in wiki_codes:
        skipped += 1
        continue

    # Skip CHGIS (wrong CRS)
    if pc.startswith('CN') and '1820' in pc:
        continue

    # Fix antimeridian-spanning polygons
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
out_path = f"{site_dir}/polities.geojson"
with open(out_path, 'w') as f:
    json.dump(data, f)
print(f"  {len(features)} wiki-verified features written ({skipped} non-wiki skipped)")
PYEOF

echo "  Done. Site data in $SITE_DIR (wiki-sourced only)"
