#!/usr/bin/env python3
"""
Add present-day subnational polity entries for the 6 largest countries by area.

Countries: Russia (83), Canada (13), USA (51), China (31), Brazil (27), Australia (11)
Total: 216 new subnational entries

Reads:
  - data/final/polities_database.csv
  - GADM 3.6 admin-1 polygons
  - data/geodata/polities_polygons.gpkg (existing polygon database)

Writes:
  - data/final/polities_database.csv (updated with subnational entries)
  - data/geodata/polities_polygons.gpkg (updated with subnational polygons)
  - data/analysis/subnational_additions_report.csv
"""

import os
import warnings

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

BASE = "/home/usuario/whep-polities"
GADM_PATH = "/home/usuario/LandInG/gadm/gadm36_levels.gpkg"

# ── Configuration ──────────────────────────────────────────────────────

# Start year = when the current administrative division was finalized
COUNTRY_CONFIG = {
    "USA": {
        "start_year": 1959,   # Hawaii statehood → 50 states + DC
        "continent": "North America",
        "iso3": "USA",
        "parent_polity": "USA-1959-2025",
    },
    "CAN": {
        "start_year": 1999,   # Nunavut creation → 13 provinces/territories
        "continent": "North America",
        "iso3": "CAN",
        "parent_polity": "CAN-1948-2025",
    },
    "BRA": {
        "start_year": 1988,   # Tocantins creation → 27 states
        "continent": "South America",
        "iso3": "BRA",
        "parent_polity": "BRA-1909-2025",
    },
    "AUS": {
        "start_year": 1901,   # Federation → 6 states + territories
        "continent": "Oceania",
        "iso3": "AUS",
        "parent_polity": "AUS-1901-2025",
    },
    "CHN": {
        "start_year": 1997,   # Chongqing municipality → current 31 divisions
        "continent": "Asia",
        "iso3": "CHN",
        "parent_polity": "F351-1950-2025",
    },
    "RUS": {
        "start_year": 1993,   # Post-Soviet constitution → current subjects
        "continent": "Europe",       # Russia classified as Europe by convention
        "iso3": "RUS",
        "parent_polity": "RUS-2014-2025",
    },
}

# Manual HASC fix for entries with missing HASC codes
HASC_FIXES = {
    ("RUS", "Moscow City"): "RU.MW",
}

# ── Load data ──────────────────────────────────────────────────────────

print("Loading data sources...")
polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
gadm = gpd.read_file(GADM_PATH, layer="level1")

print(f"  Existing polities: {len(polities)}")
print(f"  GADM admin-1 units: {len(gadm)}")

# Load existing polygons
polygons_path = f"{BASE}/data/geodata/polities_polygons.gpkg"
if os.path.exists(polygons_path):
    existing_polygons = gpd.read_file(polygons_path)
    print(f"  Existing polygons: {len(existing_polygons)}")
else:
    existing_polygons = None
    print("  No existing polygon file found — will create new one")

existing_codes = set(polities["polity_code"].values)

# ── Generate subnational entries ───────────────────────────────────────

print("\nGenerating subnational entries...")
new_entries = []
new_polygons = []

for country_iso, config in COUNTRY_CONFIG.items():
    country_gadm = gadm[gadm["GID_0"] == country_iso].sort_values("NAME_1")
    start = config["start_year"]
    end = 2025

    print(f"\n  {country_iso}: {len(country_gadm)} admin-1 units")

    for _, row in country_gadm.iterrows():
        name = row["NAME_1"]
        eng_type = row["ENGTYPE_1"]
        gid = row["GID_1"]
        hasc = row["HASC_1"]

        # Fix missing HASC codes
        if hasc is None or (isinstance(hasc, float) and pd.isna(hasc)):
            key = (country_iso, name)
            if key in HASC_FIXES:
                hasc = HASC_FIXES[key]
            else:
                # Generate from GID: RUS.43_1 -> RU.43
                gid_num = gid.split(".")[1].split("_")[0]
                hasc = f"{country_iso[:2]}.{gid_num}"
                print(f"    WARNING: No HASC for {name}, using {hasc}")

        # Generate polity code: HASC without dot + dates
        code_prefix = hasc.replace(".", "")
        polity_code = f"{code_prefix}-{start}-{end}"

        # Check for collision
        if polity_code in existing_codes:
            print(f"    COLLISION: {polity_code} ({name}) — skipping")
            continue

        # Build polity name with type context
        polity_name = f"{name} ({eng_type})"

        # Create entry
        entry = {
            "polity_code": polity_code,
            "polity_name": polity_name,
            "start_year": start,
            "end_year": end,
            "duration_years": end - start + 1,
            "polity_type": "subnational",
            "continent": config["continent"],
            "iso3_code": config["iso3"],
            "cow_code": "",
            "polygon_source": "GADM 3.6 (subnational)",
            "predecessor": "",
            "successor": "",
            "data_sources": "GADM",
            "verification_status": "VERIFIED",
            "notes": f"Parent: {config['parent_polity']}; GADM GID: {gid}",
        }
        new_entries.append(entry)
        existing_codes.add(polity_code)

        # Extract polygon
        geom = row["geometry"]
        if geom is not None and not geom.is_empty:
            new_polygons.append({
                "polity_code": polity_code,
                "polity_name": polity_name,
                "geometry": geom,
            })

        print(f"    {polity_code:20s} {polity_name}")

# ── Summary ────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"Total new entries: {len(new_entries)}")
print(f"Total new polygons: {len(new_polygons)}")

by_country = {}
for e in new_entries:
    iso = e["iso3_code"]
    by_country[iso] = by_country.get(iso, 0) + 1
for iso, count in sorted(by_country.items()):
    print(f"  {iso}: {count}")

# ── Save updated CSV ──────────────────────────────────────────────────

new_df = pd.DataFrame(new_entries)
updated = pd.concat([polities, new_df], ignore_index=True)
updated.to_csv(f"{BASE}/data/final/polities_database.csv", index=False)
print(f"\nUpdated polities_database.csv: {len(polities)} → {len(updated)} entries")

# ── Save updated polygons ─────────────────────────────────────────────

if new_polygons:
    new_poly_gdf = gpd.GeoDataFrame(new_polygons, crs="EPSG:4326")

    if existing_polygons is not None:
        # Keep only columns that match
        cols_to_keep = ["polity_code", "polity_name", "geometry"]
        existing_slim = existing_polygons[
            [c for c in cols_to_keep if c in existing_polygons.columns]
        ].copy()
        combined = pd.concat([existing_slim, new_poly_gdf], ignore_index=True)
    else:
        combined = new_poly_gdf

    combined_gdf = gpd.GeoDataFrame(combined, crs="EPSG:4326")
    # Remove existing file and rewrite with single layer to avoid layer duplication
    if os.path.exists(polygons_path):
        os.remove(polygons_path)
    combined_gdf.to_file(polygons_path, driver="GPKG", layer="polities")
    print(f"Updated polities_polygons.gpkg: {len(combined_gdf)} total polygons")

# ── Save report ────────────────────────────────────────────────────────

os.makedirs(f"{BASE}/data/analysis", exist_ok=True)
report_df = pd.DataFrame(new_entries)
report_df.to_csv(f"{BASE}/data/analysis/subnational_additions_report.csv", index=False)
print(f"Saved report: data/analysis/subnational_additions_report.csv")

print("\nDone!")
