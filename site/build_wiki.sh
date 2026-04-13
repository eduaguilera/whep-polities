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

# Step 3: Filter, remap codes, and fix geometries
echo "  Remapping GeoPackage codes to wiki codes and fixing geometries..."
python3 - "$SITE_DIR" "$WIKI_DIR" << 'PYEOF'
import json, sys, os, re

site_dir = sys.argv[1]
wiki_dir = sys.argv[2]

# Parse wiki polity codes with date ranges
wiki_polities = {}
for fname in os.listdir(wiki_dir):
    if not fname.endswith('.md') or fname == '_template.md' or fname.startswith('_'):
        continue
    with open(os.path.join(wiki_dir, fname)) as f:
        lines = f.readlines()
    if not lines or lines[0].strip() != '---':
        continue
    fm = {}
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if ':' in line:
            k, v = line.split(':', 1)
            fm[k.strip()] = v.strip()
    code = fm.get('polity_code', '').strip()
    if code:
        try:
            wiki_polities[code] = {
                'start': int(fm.get('start_year', 0)),
                'end': int(fm.get('end_year', 9999))
            }
        except ValueError:
            pass

wiki_codes = set(wiki_polities.keys())
print(f"  {len(wiki_codes)} wiki polity codes found")

with open('/tmp/polities_raw.geojson') as f:
    data = json.load(f)

# Build a mapping from GeoPackage codes to wiki codes.
# The GeoPackage was built before CSV restructuring, so codes differ.
# Strategy: for each GeoPackage feature, if its code isn't in wiki,
# find a wiki code with the same prefix whose date range overlaps.
def parse_years(code):
    """Extract start/end years from a polity code like 'BRA-1800-1903'."""
    m = re.findall(r'(\d{4})', code)
    if len(m) >= 2:
        return int(m[-2]), int(m[-1])
    return None, None

def find_wiki_match(geo_code):
    """Find the best wiki code for a GeoPackage code."""
    if geo_code in wiki_codes:
        return geo_code

    prefix = geo_code.split('-')[0]
    gs, ge = parse_years(geo_code)
    if gs is None:
        return None

    # Find wiki codes with same prefix and overlapping date range
    best = None
    best_overlap = 0
    for wc, wr in wiki_polities.items():
        if not wc.startswith(prefix + '-'):
            continue
        # Compute overlap
        overlap_start = max(gs, wr['start'])
        overlap_end = min(ge, wr['end'])
        overlap = max(0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best = wc

    return best

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

# Index GeoPackage features by prefix and date range
import copy
geo_by_prefix = {}  # prefix -> [(start, end, area, feature)]
for feat in data['features']:
    g = feat.get('geometry')
    if not g or g.get('type') not in ('Polygon', 'MultiPolygon'):
        continue
    geo_code = feat['properties'].get('polity_code', '')
    prefix = geo_code.split('-')[0]
    gs, ge = parse_years(geo_code)
    if gs is None:
        continue
    if g['type'] == 'MultiPolygon':
        area = sum(ring_area(poly[0]) for poly in g['coordinates'])
    else:
        area = ring_area(g['coordinates'][0])
    if prefix not in geo_by_prefix:
        geo_by_prefix[prefix] = []
    geo_by_prefix[prefix].append((gs, ge, area, feat))

# For each wiki polity, find the best matching GeoPackage polygon.
# Allow the same geo polygon to be reused for multiple wiki codes
# (e.g. JPN-1800-2025 geo polygon used for JPN-1800-1895, JPN-1895-1945, etc.)
features = []
remapped = 0
matched_wiki = set()
skipped = 0
for wiki_code in sorted(wiki_polities.keys()):
    wr = wiki_polities[wiki_code]
    prefix = wiki_code.split('-')[0]

    # Direct match first
    direct = [e for e in geo_by_prefix.get(prefix, [])
              if f"{prefix}-{e[0]}-{e[1]}" == wiki_code]
    if direct:
        best = max(direct, key=lambda x: x[2])
        feat = copy.deepcopy(best[3])
        feat['properties']['polity_code'] = wiki_code
        matched_wiki.add(wiki_code)
    else:
        # Find geo polygon with best overlap to this wiki code's date range
        candidates = geo_by_prefix.get(prefix, [])
        if not candidates:
            continue
        best = None
        best_score = -1
        for gs, ge, area, gfeat in candidates:
            overlap = max(0, min(ge, wr['end']) - max(gs, wr['start']))
            if overlap > best_score:
                best_score = overlap
                best = (gs, ge, area, gfeat)
        if best and best_score > 0:
            feat = copy.deepcopy(best[3])
            feat['properties']['polity_code'] = wiki_code
            matched_wiki.add(wiki_code)
            remapped += 1
        else:
            continue

    g = feat['geometry']

    # Skip CHGIS (wrong CRS)
    if wiki_code.startswith('CN') and '1820' in wiki_code:
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
no_polygon = len(wiki_codes) - len(matched_wiki)
print(f"  {len(features)} wiki-verified features written ({remapped} remapped from old codes, {no_polygon} wiki polities with no polygon)")
PYEOF

echo "  Done. Site data in $SITE_DIR (wiki-sourced only)"
