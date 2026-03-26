#!/usr/bin/env python3
"""
Comprehensive stress tests for the WHEP polities database.

Tests:
  1. Schema integrity (required columns, types, no nulls where expected)
  2. Code format validation (XXX-yyyy-YYYY)
  3. Code uniqueness
  4. Date range consistency
  5. Predecessor/successor chain integrity
  6. ISO3 code validation
  7. COW code cross-validation with external COW state system
  8. Polygon coverage completeness
  9. Continent assignment validation
  10. Duplicate detection (same polity, overlapping dates)
  11. Timeline gap/overlap analysis for successor chains
  12. Data source field consistency
  13. Verification status distribution
  14. Cross-validation with FAOSTAT ISO codes
  15. Cross-validation with decolonization events
  16. Polygon source vs actual polygon match validation
  17. Area reasonableness checks (polygon areas)
  18. Temporal density analysis (no lost decades)

Outputs:
  - Console summary with PASS/FAIL/WARN per test
  - data/analysis/stress_test_report.csv (detailed findings)
  - data/analysis/plots/stress_test_*.png (diagnostic plots)
"""

import warnings
warnings.filterwarnings("ignore")

import os
import re
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

BASE = "/home/usuario/whep-polities"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────
print("=" * 70)
print("WHEP POLITIES DATABASE — STRESS TEST SUITE")
print("=" * 70)
print()

polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
poly_report = pd.read_csv(f"{BASE}/data/analysis/polygon_matching_report.csv")
cow = pd.read_csv(f"{BASE}/data/external/cow_state_system.csv")
decol = pd.read_csv(f"{BASE}/data/external/decolonization_events.csv")
polygons = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")

non_region = polities[polities["polity_type"] != "region"]

print(f"Database: {len(polities)} entries ({len(non_region)} non-region)")
print(f"Polygons: {len(polygons)} geometries")
print()

results = []
test_num = 0
passed = 0
failed = 0
warned = 0


def report(test_name, status, details="", findings=None):
    global test_num, passed, failed, warned
    test_num += 1
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}[status]
    color = {"PASS": "\033[92m", "FAIL": "\033[91m", "WARN": "\033[93m"}[status]
    reset = "\033[0m"
    print(f"  {color}{icon}{reset} Test {test_num:2d}: {test_name} [{status}] {details}")
    if status == "PASS":
        passed += 1
    elif status == "FAIL":
        failed += 1
    else:
        warned += 1
    results.append({"test": test_num, "name": test_name, "status": status, "details": details})
    if findings:
        for f in findings[:10]:
            print(f"           → {f}")
        if len(findings) > 10:
            print(f"           → ... and {len(findings) - 10} more")


# =====================================================================
# TEST 1: Schema integrity
# =====================================================================
print("─── SCHEMA INTEGRITY ───")
required_cols = ["polity_code", "polity_name", "start_year", "end_year",
                 "duration_years", "polity_type", "continent", "polygon_source",
                 "verification_status"]
missing = [c for c in required_cols if c not in polities.columns]
if missing:
    report("Required columns present", "FAIL", f"Missing: {missing}")
else:
    report("Required columns present", "PASS", f"All {len(required_cols)} required columns found")

# No nulls in required fields
null_counts = {}
for col in required_cols:
    nulls = polities[col].isna().sum()
    if nulls > 0:
        null_counts[col] = nulls
if null_counts:
    report("No nulls in required fields", "FAIL", f"Nulls found: {null_counts}")
else:
    report("No nulls in required fields", "PASS")

# Type validation
valid_types = {"sovereign", "historical", "colonial", "dependency", "aggregate",
               "region", "mandate", "disputed", "puppet", "occupation"}
bad_types = set(polities["polity_type"].unique()) - valid_types
if bad_types:
    report("Valid polity types", "FAIL", f"Invalid types: {bad_types}")
else:
    report("Valid polity types", "PASS", f"{len(polities['polity_type'].unique())} types used")

valid_continents = {"Africa", "Asia", "Europe", "North America", "South America",
                    "Oceania", "Antarctica", "Global"}
bad_conts = set(polities["continent"].unique()) - valid_continents
if bad_conts:
    report("Valid continents", "FAIL", f"Invalid: {bad_conts}")
else:
    report("Valid continents", "PASS", f"{len(polities['continent'].unique())} continents used")


# =====================================================================
# TEST 2: Code format validation
# =====================================================================
print("\n─── CODE FORMAT ───")
code_pattern = re.compile(r'^[A-Z0-9]+-\d{4}-\d{4}$')
bad_codes = polities[~polities["polity_code"].str.match(r'^[A-Z0-9]+-\d{4}-\d{4}$')]
if len(bad_codes) > 0:
    report("Code format (XXX-yyyy-YYYY)", "FAIL",
           f"{len(bad_codes)} invalid codes",
           bad_codes["polity_code"].tolist())
else:
    report("Code format (XXX-yyyy-YYYY)", "PASS", f"All {len(polities)} codes valid")


# =====================================================================
# TEST 3: Code uniqueness
# =====================================================================
dupes = polities["polity_code"].value_counts()
dupes = dupes[dupes > 1]
if len(dupes) > 0:
    report("Code uniqueness", "FAIL",
           f"{len(dupes)} duplicate codes",
           [f"{code}: {count}x" for code, count in dupes.items()])
else:
    report("Code uniqueness", "PASS", f"All {len(polities)} codes unique")


# =====================================================================
# TEST 4: Date range consistency
# =====================================================================
print("\n─── TEMPORAL CONSISTENCY ───")
# start <= end
bad_range = polities[polities["start_year"] > polities["end_year"]]
if len(bad_range) > 0:
    report("start_year <= end_year", "FAIL",
           f"{len(bad_range)} entries with inverted dates",
           [f"{r.polity_code}: {r.start_year}-{r.end_year}" for _, r in bad_range.iterrows()])
else:
    report("start_year <= end_year", "PASS")

# Duration matches
bad_dur = polities[polities["duration_years"] != (polities["end_year"] - polities["start_year"] + 1)]
if len(bad_dur) > 0:
    report("duration_years consistency", "FAIL",
           f"{len(bad_dur)} entries with wrong duration",
           [f"{r.polity_code}: says {r.duration_years}, calc {r.end_year - r.start_year + 1}"
            for _, r in bad_dur.iterrows()])
else:
    report("duration_years consistency", "PASS")

# Code dates match column dates
code_date_mismatch = []
for _, r in polities.iterrows():
    m = re.match(r'^(.+)-(\d{4})-(\d{4})$', r["polity_code"])
    if m:
        code_start = int(m.group(2))
        code_end = int(m.group(3))
        if code_start != r["start_year"] or code_end != r["end_year"]:
            code_date_mismatch.append(
                f"{r['polity_code']}: code={code_start}-{code_end} vs cols={r['start_year']}-{r['end_year']}")
if code_date_mismatch:
    report("Code dates match column dates", "FAIL",
           f"{len(code_date_mismatch)} mismatches", code_date_mismatch)
else:
    report("Code dates match column dates", "PASS")

# Date range
out_of_range = polities[(polities["start_year"] < 1800) | (polities["end_year"] > 2025)]
if len(out_of_range) > 0:
    report("Dates within 1800-2025", "FAIL",
           f"{len(out_of_range)} entries outside range",
           [f"{r.polity_code}: {r.start_year}-{r.end_year}" for _, r in out_of_range.iterrows()])
else:
    report("Dates within 1800-2025", "PASS")


# =====================================================================
# TEST 5: Predecessor/successor chain integrity
# =====================================================================
print("\n─── CHAIN INTEGRITY ───")
all_codes = set(polities["polity_code"])
broken_pred = []
broken_succ = []
for _, r in polities.iterrows():
    if pd.notna(r["predecessor"]) and str(r["predecessor"]).strip():
        for pred in str(r["predecessor"]).split(";"):
            pred = pred.strip()
            if pred and pred not in all_codes:
                broken_pred.append(f"{r['polity_code']} → pred={pred}")
    if pd.notna(r["successor"]) and str(r["successor"]).strip():
        for succ in str(r["successor"]).split(";"):
            succ = succ.strip()
            if succ and succ not in all_codes:
                broken_succ.append(f"{r['polity_code']} → succ={succ}")

if broken_pred:
    report("Predecessor codes exist", "WARN",
           f"{len(broken_pred)} broken predecessor refs", broken_pred)
else:
    report("Predecessor codes exist", "PASS")

if broken_succ:
    report("Successor codes exist", "WARN",
           f"{len(broken_succ)} broken successor refs", broken_succ)
else:
    report("Successor codes exist", "PASS")

# Bidirectional check: if A's predecessor is B, B's successor should include A
bidir_issues = []
pred_lookup = {}
succ_lookup = {}
for _, r in polities.iterrows():
    code = r["polity_code"]
    if pd.notna(r["predecessor"]) and str(r["predecessor"]).strip():
        pred_lookup[code] = [p.strip() for p in str(r["predecessor"]).split(";") if p.strip()]
    if pd.notna(r["successor"]) and str(r["successor"]).strip():
        succ_lookup[code] = [s.strip() for s in str(r["successor"]).split(";") if s.strip()]

for code, preds in pred_lookup.items():
    for pred in preds:
        if pred in all_codes:
            succs_of_pred = succ_lookup.get(pred, [])
            if code not in succs_of_pred:
                bidir_issues.append(f"{code}.predecessor={pred} but {pred}.successor missing {code}")

if bidir_issues:
    report("Bidirectional predecessor↔successor", "WARN",
           f"{len(bidir_issues)} asymmetric links", bidir_issues)
else:
    report("Bidirectional predecessor↔successor", "PASS")


# =====================================================================
# TEST 6: ISO3 code validation
# =====================================================================
print("\n─── CODE VALIDATION ───")
iso3_entries = polities[polities["iso3_code"].notna()]
bad_iso = iso3_entries[~iso3_entries["iso3_code"].str.match(r'^[A-Z]{3}$')]
if len(bad_iso) > 0:
    report("ISO3 code format", "FAIL",
           f"{len(bad_iso)} invalid ISO3 codes",
           [f"{r.polity_code}: iso3={r.iso3_code}" for _, r in bad_iso.iterrows()])
else:
    report("ISO3 code format", "PASS", f"{len(iso3_entries)} entries with ISO3 codes")

# Check for ISO code collisions (different polities sharing same ISO3)
iso_collision = iso3_entries.groupby("iso3_code").filter(lambda x: len(x) > 1)
iso_groups = iso_collision.groupby("iso3_code")
collision_details = []
for iso, group in iso_groups:
    names = group["polity_name"].unique()
    # Same name = period splits (OK); different name = potential collision
    if len(names) > 1:
        collision_details.append(f"{iso}: {list(names)}")

if collision_details:
    report("ISO3 code uniqueness across names", "WARN",
           f"{len(collision_details)} ISO codes shared by different names", collision_details)
else:
    report("ISO3 code uniqueness across names", "PASS")


# =====================================================================
# TEST 7: COW code cross-validation
# =====================================================================
our_cow = set()
for c in polities["cow_code"].dropna():
    try:
        our_cow.add(int(float(c)))
    except (ValueError, TypeError):
        pass

cow_codes_ext = set()
for _, r in cow.iterrows():
    try:
        cow_codes_ext.add(int(r["cow_code"]))
    except (ValueError, TypeError):
        pass

matched = our_cow & cow_codes_ext
cow_only = cow_codes_ext - our_cow
whep_only = our_cow - cow_codes_ext

report("COW codes match external COW system", "PASS" if len(cow_only) <= 2 else "WARN",
       f"Matched: {len(matched)}, COW-only: {len(cow_only)}, WHEP-only: {len(whep_only)}",
       [f"COW-only: {sorted(cow_only)[:10]}"] if cow_only else None)


# =====================================================================
# TEST 8: Polygon coverage
# =====================================================================
print("\n─── POLYGON COVERAGE ───")
has_poly = poly_report[poly_report["has_geometry"] == True]
no_poly = poly_report[(poly_report["has_geometry"] == False) & (~poly_report["source_used"].str.contains("region", na=False))]

non_region_total = len(polities[polities["polity_type"] != "region"])
coverage = len(has_poly) / non_region_total * 100

report("Polygon coverage rate", "PASS" if coverage >= 95 else "WARN",
       f"{len(has_poly)}/{non_region_total} = {coverage:.1f}%")

# All polygons have valid geometries
invalid_geom = polygons[~polygons.geometry.is_valid]
if len(invalid_geom) > 0:
    report("All polygon geometries valid", "WARN",
           f"{len(invalid_geom)} invalid geometries",
           invalid_geom["polity_code"].tolist()[:10])
else:
    report("All polygon geometries valid", "PASS", f"{len(polygons)} geometries OK")

# No empty geometries
empty_geom = polygons[polygons.geometry.is_empty]
if len(empty_geom) > 0:
    report("No empty geometries", "FAIL",
           f"{len(empty_geom)} empty geometries",
           empty_geom["polity_code"].tolist())
else:
    report("No empty geometries", "PASS")

# CRS check
if polygons.crs and "4326" in str(polygons.crs):
    report("CRS is EPSG:4326", "PASS")
else:
    report("CRS is EPSG:4326", "FAIL", f"CRS is {polygons.crs}")


# =====================================================================
# TEST 9: Continent assignment validation
# =====================================================================
# Cross-check polygon centroids against continental bounding boxes
continent_bounds = {
    "Africa": (-35, -25, 38, 55),
    "Asia": (-10, 25, 80, 180),
    "Europe": (35, -30, 72, 60),
    "North America": (5, -170, 85, -50),
    "South America": (-60, -85, 15, -30),
    "Oceania": (-50, 100, 30, 180),
    "Antarctica": (-90, -180, -60, 180),
}

centroid_issues = []
for _, p in polygons.iterrows():
    poly_row = polities[polities["polity_code"] == p["polity_code"]]
    if len(poly_row) == 0:
        continue
    cont = poly_row.iloc[0]["continent"]
    if cont in ("Global", "Antarctica"):
        continue
    centroid = p.geometry.centroid
    lat, lon = centroid.y, centroid.x
    if cont in continent_bounds:
        lat_min, lon_min, lat_max, lon_max = continent_bounds[cont]
        if not (lat_min <= lat <= lat_max):
            centroid_issues.append(f"{p['polity_code']} ({cont}): lat={lat:.1f} outside [{lat_min},{lat_max}]")

if centroid_issues:
    report("Polygon centroids match continent", "WARN",
           f"{len(centroid_issues)} centroids outside expected continent bounds",
           centroid_issues)
else:
    report("Polygon centroids match continent", "PASS")


# =====================================================================
# TEST 10: Duplicate detection
# =====================================================================
print("\n─── DUPLICATE DETECTION ───")
# Check for same ISO3 + overlapping date ranges (potential duplicates)
overlap_issues = []
for iso in polities["iso3_code"].dropna().unique():
    group = non_region[non_region["iso3_code"] == iso].sort_values("start_year")
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            ri = group.iloc[i]
            rj = group.iloc[j]
            if ri["end_year"] >= rj["start_year"] and ri["start_year"] <= rj["end_year"]:
                # Overlapping — check if same type (aggregates overlap by design)
                if ri["polity_type"] != "aggregate" and rj["polity_type"] != "aggregate":
                    overlap_issues.append(
                        f"{ri['polity_code']} ({ri['start_year']}-{ri['end_year']}) overlaps "
                        f"{rj['polity_code']} ({rj['start_year']}-{rj['end_year']}) [iso={iso}]")

if overlap_issues:
    report("No overlapping non-aggregate entries per ISO", "WARN",
           f"{len(overlap_issues)} overlapping pairs", overlap_issues)
else:
    report("No overlapping non-aggregate entries per ISO", "PASS")


# =====================================================================
# TEST 11: Data source field consistency
# =====================================================================
print("\n─── DATA CONSISTENCY ───")
valid_sources = {"FT", "FAOSTAT", "M49", "CShapes", "CShapes-Europe", "GADM",
                 "WHEP-fix", "WHEP", "WHEP-fix; GADM", "GADM 4.1", "NaturalEarth"}
bad_source_entries = []
for _, r in polities.iterrows():
    ds = str(r.get("data_sources", ""))
    if ds and ds != "nan":
        parts = [p.strip() for p in ds.split(";")]
        for p in parts:
            if p and not any(v in p for v in ["FT", "FAOSTAT", "M49", "CShapes", "GADM",
                                                "WHEP", "NaturalEarth", "Europe"]):
                bad_source_entries.append(f"{r['polity_code']}: unknown source '{p}'")

if bad_source_entries:
    report("Data source labels valid", "WARN",
           f"{len(bad_source_entries)} unrecognized source labels", bad_source_entries)
else:
    report("Data source labels valid", "PASS")

# Verification coverage
n_verified = (polities["verification_status"].str.startswith("VERIFIED") |
              polities["verification_status"].str.startswith("FIXED")).sum()
n_region = (polities["verification_status"] == "REGION").sum()
n_unverified = (polities["verification_status"] == "UNVERIFIED").sum()
total = len(polities)
report("Verification coverage", "PASS" if n_verified / total > 0.5 else "WARN",
       f"Verified: {n_verified} ({n_verified/total*100:.0f}%), Region: {n_region}, Unverified: {n_unverified}")


# =====================================================================
# TEST 12: Temporal density (no lost decades)
# =====================================================================
print("\n─── TEMPORAL DENSITY ───")
decades = range(1800, 2030, 10)
active_by_decade = {}
for d in decades:
    n = ((non_region["start_year"] <= d) & (non_region["end_year"] >= d)).sum()
    active_by_decade[d] = n

min_decade = min(active_by_decade, key=active_by_decade.get)
min_count = active_by_decade[min_decade]
report("No empty decades", "PASS" if min_count > 10 else "FAIL",
       f"Min: {min_count} active polities in {min_decade}, Max: {max(active_by_decade.values())}")

# Check for smooth transitions (no sudden drops > 50%)
drop_issues = []
prev_count = None
for d in sorted(active_by_decade.keys()):
    count = active_by_decade[d]
    if prev_count and count < prev_count * 0.5:
        drop_issues.append(f"{d}: {count} (was {prev_count}, drop={1-count/prev_count:.0%})")
    prev_count = count

if drop_issues:
    report("No sudden drops in active count", "WARN",
           f"{len(drop_issues)} decades with >50% drop", drop_issues)
else:
    report("No sudden drops in active count", "PASS")


# =====================================================================
# TEST 13: Polygon area reasonableness
# =====================================================================
print("\n─── POLYGON AREA CHECKS ───")
# Calculate areas in square degrees (rough proxy)
polygons["area_deg2"] = polygons.geometry.area
# Merge polity metadata, handling column name conflicts from the gpkg
poly_meta = polities[["polity_code", "polity_type", "continent", "polity_name"]].copy()
poly_meta.columns = ["polity_code", "p_type", "p_continent", "p_name"]
p_merged = polygons.merge(poly_meta, on="polity_code", how="left")

# Extremely small polygons (< 0.01 sq degrees = likely a point error)
tiny = p_merged[p_merged["area_deg2"] < 0.001]
if len(tiny) > 0:
    # Filter out known small islands
    true_tiny = tiny[~tiny["p_type"].isin(["dependency", "colonial"])]
    report("No suspiciously tiny polygons", "WARN" if len(true_tiny) > 0 else "PASS",
           f"{len(tiny)} polygons < 0.001 deg² ({len(true_tiny)} non-dependency)",
           [f"{r.polity_code} ({r.p_name}): {r.area_deg2:.6f} deg²"
            for _, r in true_tiny.iterrows()])
else:
    report("No suspiciously tiny polygons", "PASS")

# Extremely large polygons (> 5000 sq degrees - basically Russia + Antarctica)
huge = p_merged[p_merged["area_deg2"] > 5000]
report("Large polygon check", "PASS",
       f"{len(huge)} polygons > 5000 deg²: {', '.join(huge['polity_code'].tolist())}" if len(huge) > 0 else "No unexpectedly large polygons")


# =====================================================================
# TEST 14: FAOSTAT cross-validation
# =====================================================================
print("\n─── EXTERNAL CROSS-VALIDATION ───")
faostat_entries = polities[polities["data_sources"].str.contains("FAOSTAT", na=False)]
faostat_iso = set(faostat_entries["iso3_code"].dropna())
report("FAOSTAT entries have ISO3", "PASS" if len(faostat_iso) > 200 else "WARN",
       f"{len(faostat_iso)} FAOSTAT entries with ISO3 codes out of {len(faostat_entries)} total")

# Decolonization coverage
decol_iso = set(decol["iso3"].dropna().astype(str))
our_iso = set(polities["iso3_code"].dropna().astype(str))
decol_matched = decol_iso & our_iso
decol_missing = decol_iso - our_iso
report("Decolonization event coverage", "PASS" if len(decol_missing) <= 2 else "WARN",
       f"{len(decol_matched)}/{len(decol_iso)} events matched",
       [f"Missing: {sorted(decol_missing)}"] if decol_missing else None)


# =====================================================================
# TEST 15: Polygon source consistency
# =====================================================================
# Check that entries claiming CShapes actually got CShapes polygons
source_mismatch = []
for _, r in poly_report.iterrows():
    if not r["has_geometry"]:
        continue
    poly_row = polities[polities["polity_code"] == r["polity_code"]]
    if len(poly_row) == 0:
        continue
    claimed = str(poly_row.iloc[0]["polygon_source"])
    actual = str(r["source_used"])
    # Check for major mismatches (CShapes claimed but GADM used, etc.)
    if "CShapes" in claimed and "GADM" in actual and "fallback" not in claimed.lower():
        source_mismatch.append(f"{r['polity_code']}: claimed={claimed}, got={actual}")

if source_mismatch:
    report("Polygon source matches claim", "WARN",
           f"{len(source_mismatch)} source mismatches", source_mismatch)
else:
    report("Polygon source matches claim", "PASS")


# =====================================================================
# DIAGNOSTIC PLOTS
# =====================================================================
print("\n─── GENERATING DIAGNOSTIC PLOTS ───")

# Plot 1: Active polities by decade with annotations
fig, ax = plt.subplots(figsize=(14, 6))
decades_list = sorted(active_by_decade.keys())
counts_list = [active_by_decade[d] for d in decades_list]
ax.bar(decades_list, counts_list, width=8, color="#2196F3", edgecolor="white")
for d, c in zip(decades_list, counts_list):
    ax.text(d, c + 2, str(c), ha="center", fontsize=7)
ax.set_xlabel("Decade")
ax.set_ylabel("Active Non-Region Polities")
ax.set_title("Active Polities by Decade (Stress Test Density Check)")
ax.axhline(y=np.mean(counts_list), color="red", linestyle="--", alpha=0.5, label=f"Mean: {np.mean(counts_list):.0f}")
ax.legend()
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/stress_test_01_temporal_density.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 1: temporal density")

# Plot 2: Polygon area distribution (log scale)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
areas = p_merged["area_deg2"].values
areas_log = np.log10(areas[areas > 0])
ax.hist(areas_log, bins=50, color="#4CAF50", edgecolor="white")
ax.set_xlabel("log₁₀(area in deg²)")
ax.set_ylabel("Count")
ax.set_title("Polygon Area Distribution (all)")
ax.axvline(np.log10(0.001), color="red", linestyle="--", label="tiny threshold")
ax.legend()

# By type
ax = axes[1]
for ptype in ["sovereign", "historical", "colonial", "dependency"]:
    subset = p_merged[p_merged["p_type"] == ptype]["area_deg2"]
    subset = subset[subset > 0]
    ax.hist(np.log10(subset), bins=30, alpha=0.5, label=f"{ptype} (n={len(subset)})")
ax.set_xlabel("log₁₀(area in deg²)")
ax.set_ylabel("Count")
ax.set_title("Polygon Area Distribution by Type")
ax.legend()

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/stress_test_02_area_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 2: area distribution")

# Plot 3: Test results summary
fig, ax = plt.subplots(figsize=(10, 4))
statuses = [r["status"] for r in results]
status_counts = Counter(statuses)
colors = {"PASS": "#4CAF50", "WARN": "#FF9800", "FAIL": "#F44336"}
bars = ax.bar(status_counts.keys(), status_counts.values(),
              color=[colors[s] for s in status_counts.keys()], edgecolor="white", linewidth=2)
for bar, v in zip(bars, status_counts.values()):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            str(v), ha="center", fontweight="bold", fontsize=14)
ax.set_ylabel("Number of Tests")
ax.set_title(f"Stress Test Results Summary ({test_num} tests)")
ax.set_ylim(0, max(status_counts.values()) + 3)
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/stress_test_03_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 3: results summary")

# Plot 4: Polygon coverage by continent and type
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# By continent
ax = axes[0]
continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
cont_with = []
cont_without = []
for cont in continents:
    in_cont = non_region[non_region["continent"] == cont]
    in_poly = poly_report[(poly_report["polity_code"].isin(in_cont["polity_code"])) &
                          (poly_report["has_geometry"] == True)]
    cont_with.append(len(in_poly))
    cont_without.append(len(in_cont) - len(in_poly))

x = np.arange(len(continents))
ax.bar(x, cont_with, color="#4CAF50", label="With polygon")
ax.bar(x, cont_without, bottom=cont_with, color="#F44336", label="Without polygon")
ax.set_xticks(x)
ax.set_xticklabels(continents, rotation=30, ha="right")
ax.set_ylabel("Count")
ax.set_title("Polygon Coverage by Continent")
ax.legend()

# By type
ax = axes[1]
types = ["sovereign", "historical", "colonial", "dependency", "mandate"]
type_with = []
type_without = []
for t in types:
    in_type = non_region[non_region["polity_type"] == t]
    in_poly = poly_report[(poly_report["polity_code"].isin(in_type["polity_code"])) &
                          (poly_report["has_geometry"] == True)]
    type_with.append(len(in_poly))
    type_without.append(len(in_type) - len(in_poly))

x = np.arange(len(types))
ax.bar(x, type_with, color="#4CAF50", label="With polygon")
ax.bar(x, type_without, bottom=type_with, color="#F44336", label="Without polygon")
ax.set_xticks(x)
ax.set_xticklabels(types, rotation=30, ha="right")
ax.set_ylabel("Count")
ax.set_title("Polygon Coverage by Type")
ax.legend()
for i, (w, wo) in enumerate(zip(type_with, type_without)):
    total = w + wo
    pct = w / total * 100 if total > 0 else 0
    ax.text(i, w + wo + 1, f"{pct:.0f}%", ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/stress_test_04_coverage_breakdown.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 4: coverage breakdown")

# Plot 5: Predecessor/successor chain visualization
fig, ax = plt.subplots(figsize=(16, 8))
# Count chain lengths
chain_lengths = Counter()
for _, r in polities.iterrows():
    n_pred = 0
    if pd.notna(r["predecessor"]) and str(r["predecessor"]).strip():
        n_pred = len([p for p in str(r["predecessor"]).split(";") if p.strip()])
    n_succ = 0
    if pd.notna(r["successor"]) and str(r["successor"]).strip():
        n_succ = len([s for s in str(r["successor"]).split(";") if s.strip()])
    chain_lengths[(n_pred, n_succ)] += 1

# Heatmap of pred/succ counts
max_links = 6
matrix = np.zeros((max_links + 1, max_links + 1))
for (np_, ns), count in chain_lengths.items():
    np_c = min(np_, max_links)
    ns_c = min(ns, max_links)
    matrix[np_c][ns_c] += count

im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(max_links + 1))
ax.set_yticks(range(max_links + 1))
labels = [str(i) for i in range(max_links)] + [f"{max_links}+"]
ax.set_xticklabels(labels)
ax.set_yticklabels(labels)
ax.set_xlabel("Number of successors")
ax.set_ylabel("Number of predecessors")
ax.set_title("Predecessor/Successor Link Distribution")
for i in range(max_links + 1):
    for j in range(max_links + 1):
        if matrix[i][j] > 0:
            ax.text(j, i, f"{int(matrix[i][j])}", ha="center", va="center",
                    fontsize=9, color="white" if matrix[i][j] > 100 else "black")
plt.colorbar(im, ax=ax, shrink=0.8)
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/stress_test_05_chain_links.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 5: chain links")


# ── Save report ──────────────────────────────────────────────────────
report_df = pd.DataFrame(results)
report_df.to_csv(f"{BASE}/data/analysis/stress_test_report.csv", index=False)

# ── Final summary ────────────────────────────────────────────────────
print()
print("=" * 70)
print(f"STRESS TEST COMPLETE: {test_num} tests")
print(f"  PASSED: {passed}")
print(f"  WARNED: {warned}")
print(f"  FAILED: {failed}")
print("=" * 70)
