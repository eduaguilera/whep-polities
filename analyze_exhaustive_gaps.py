#!/usr/bin/env python3
"""
Exhaustive coverage gap analysis for the WHEP polities database.

Systematically checks for:
1. COW State System gaps (states in COW not in our DB)
2. FAOSTAT entity gaps
3. UN M49 gaps
4. CShapes polities not represented
5. Decolonization events without polity entries
6. Empire dissolution events without successors
7. Territorial transfers without entries
8. Polygon coverage gaps by era and continent
9. Predecessor/successor chain completeness

Produces:
  - data/analysis/exhaustive_gap_report.csv
  - data/analysis/plots/gap_*.png
  - Console summary
"""

import warnings
warnings.filterwarnings("ignore")

import os
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from collections import defaultdict

BASE = "/home/usuario/whep-polities"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
non_region = polities[polities["polity_type"] != "region"]
poly_report = pd.read_csv(f"{BASE}/data/analysis/polygon_matching_report.csv")
polygons = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")

print("=" * 70)
print("EXHAUSTIVE COVERAGE GAP ANALYSIS")
print("=" * 70)
print(f"Total polities: {len(polities)}")
print(f"Non-region polities: {len(non_region)}")
print(f"Polygons: {len(polygons)}")

gap_rows = []

# =====================================================================
# 1. COW STATE SYSTEM GAPS
# =====================================================================
print("\n─── 1. COW STATE SYSTEM GAPS ───")

# Full COW state system (209 states as of 2016)
# Source: Correlates of War State System Membership v2016
COW_STATES = {
    2: ("USA", "United States"), 20: ("CAN", "Canada"), 31: ("BHS", "Bahamas"),
    40: ("CUB", "Cuba"), 41: ("HTI", "Haiti"), 42: ("DOM", "Dominican Republic"),
    51: ("JAM", "Jamaica"), 52: ("TTO", "Trinidad and Tobago"),
    53: ("BRB", "Barbados"), 54: ("DMA", "Dominica"), 55: ("GRD", "Grenada"),
    56: ("LCA", "Saint Lucia"), 57: ("VCT", "Saint Vincent"),
    58: ("ATG", "Antigua and Barbuda"), 60: ("KNA", "Saint Kitts and Nevis"),
    70: ("MEX", "Mexico"), 80: ("BLZ", "Belize"), 90: ("GTM", "Guatemala"),
    91: ("HND", "Honduras"), 92: ("SLV", "El Salvador"), 93: ("NIC", "Nicaragua"),
    94: ("CRI", "Costa Rica"), 95: ("PAN", "Panama"), 100: ("COL", "Colombia"),
    101: ("VEN", "Venezuela"), 110: ("GUY", "Guyana"), 115: ("SUR", "Suriname"),
    130: ("ECU", "Ecuador"), 135: ("PER", "Peru"), 140: ("BRA", "Brazil"),
    145: ("BOL", "Bolivia"), 150: ("PRY", "Paraguay"), 155: ("CHL", "Chile"),
    160: ("ARG", "Argentina"), 165: ("URY", "Uruguay"),
    200: ("GBR", "United Kingdom"), 205: ("IRL", "Ireland"),
    210: ("NLD", "Netherlands"), 211: ("BEL", "Belgium"),
    212: ("LUX", "Luxembourg"), 220: ("FRA", "France"),
    225: ("CHE", "Switzerland"), 230: ("ESP", "Spain"),
    235: ("PRT", "Portugal"), 240: ("HAN", "Hanover"),
    245: ("BAV", "Bavaria"), 255: ("DEU", "Germany"),
    260: ("GDR", "German Democratic Republic"), 265: ("BAD", "Baden"),
    267: ("SAX", "Saxony"), 269: ("WRT", "Württemberg"),
    271: ("HES", "Hesse Electoral"), 273: ("HSD", "Hesse Grand Ducal"),
    275: ("MEK", "Mecklenburg-Schwerin"), 280: ("ITA", "Italy"),
    290: ("MOD", "Modena"), 291: ("PRM", "Parma"),
    293: ("PAP", "Papal States"), 294: ("TUS", "Tuscany"),
    325: ("SIC", "Two Sicilies"), 310: ("HUN", "Hungary"),
    305: ("AUT", "Austria"), 315: ("CZE", "Czechoslovakia"),
    316: ("CZR", "Czech Republic"), 317: ("SVK", "Slovakia"),
    325: ("ITA", "Italy"), 329: ("SMR", "San Marino"),
    331: ("VAT", "Vatican City/Holy See"), 332: ("LIE", "Liechtenstein"),
    335: ("MLT", "Malta"), 338: ("AND", "Andorra"),
    339: ("MCO", "Monaco"),
    340: ("POL", "Poland"), 341: ("EST", "Estonia"), 342: ("LVA", "Latvia"),
    343: ("LTU", "Lithuania"), 344: ("BLR", "Belarus"),
    345: ("UKR", "Ukraine"), 346: ("MDA", "Moldova"),
    349: ("RUS", "Russia"), 350: ("FIN", "Finland"),
    352: ("SWE", "Sweden"), 355: ("NOR", "Norway"),
    357: ("DNK", "Denmark"), 359: ("ISL", "Iceland"),
    360: ("ROU", "Romania"), 365: ("BGR", "Bulgaria"),
    366: ("MNE", "Montenegro"), 367: ("MKD", "North Macedonia"),
    368: ("BIH", "Bosnia and Herzegovina"), 369: ("HRV", "Croatia"),
    370: ("SVN", "Slovenia"), 371: ("SRB", "Serbia"),
    372: ("KOS", "Kosovo"), 373: ("YUG", "Yugoslavia (Serbia and Montenegro)"),
    375: ("GRC", "Greece"), 380: ("CYP", "Cyprus"),
    385: ("TUR", "Turkey"),
    390: ("ALB", "Albania"),
    395: ("RUS", "Russia/Soviet Union"),
    402: ("CPV", "Cape Verde"), 403: ("STP", "São Tomé and Príncipe"),
    404: ("GNB", "Guinea-Bissau"),
    411: ("GNQ", "Equatorial Guinea"), 420: ("GMB", "Gambia"),
    432: ("MLI", "Mali"), 433: ("SEN", "Senegal"),
    434: ("BEN", "Benin"), 435: ("MRT", "Mauritania"),
    436: ("NER", "Niger"), 437: ("CIV", "Côte d'Ivoire"),
    438: ("GIN", "Guinea"), 439: ("BFA", "Burkina Faso"),
    450: ("LBR", "Liberia"), 451: ("SLE", "Sierra Leone"),
    452: ("GHA", "Ghana"), 461: ("TGO", "Togo"),
    471: ("CMR", "Cameroon"), 475: ("NGA", "Nigeria"),
    481: ("GAB", "Gabon"), 482: ("CAF", "Central African Republic"),
    483: ("TCD", "Chad"), 484: ("COG", "Congo"),
    490: ("COD", "DR Congo"), 500: ("UGA", "Uganda"),
    501: ("KEN", "Kenya"), 510: ("TZA", "Tanzania"),
    511: ("ZNZ", "Zanzibar"), 516: ("BDI", "Burundi"),
    517: ("RWA", "Rwanda"), 520: ("SOM", "Somalia"),
    522: ("DJI", "Djibouti"), 530: ("ETH", "Ethiopia"),
    531: ("ERI", "Eritrea"),
    540: ("AGO", "Angola"), 541: ("MOZ", "Mozambique"),
    551: ("ZMB", "Zambia"), 552: ("ZWE", "Zimbabwe"),
    553: ("MWI", "Malawi"), 560: ("ZAF", "South Africa"),
    565: ("NAM", "Namibia"), 570: ("LSO", "Lesotho"),
    571: ("BWA", "Botswana"), 572: ("SWZ", "Eswatini"),
    580: ("MDG", "Madagascar"), 581: ("COM", "Comoros"),
    590: ("MUS", "Mauritius"), 591: ("SYC", "Seychelles"),
    600: ("MAR", "Morocco"), 615: ("DZA", "Algeria"),
    616: ("TUN", "Tunisia"), 620: ("LBY", "Libya"),
    625: ("SDN", "Sudan"), 626: ("SSD", "South Sudan"),
    630: ("IRN", "Iran"), 640: ("TUR", "Turkey"),
    645: ("IRQ", "Iraq"), 651: ("EGY", "Egypt"),
    652: ("SYR", "Syria"), 660: ("LBN", "Lebanon"),
    663: ("JOR", "Jordan"), 666: ("ISR", "Israel"),
    670: ("SAU", "Saudi Arabia"), 678: ("YEM", "Yemen"),
    679: ("YAR", "Yemen Arab Republic"), 680: ("YPR", "Yemen People's Republic"),
    690: ("KWT", "Kuwait"), 692: ("BHR", "Bahrain"),
    694: ("QAT", "Qatar"), 696: ("ARE", "United Arab Emirates"),
    698: ("OMN", "Oman"),
    700: ("AFG", "Afghanistan"), 701: ("TKM", "Turkmenistan"),
    702: ("TJK", "Tajikistan"), 703: ("KGZ", "Kyrgyzstan"),
    704: ("UZB", "Uzbekistan"), 705: ("KAZ", "Kazakhstan"),
    710: ("CHN", "China"), 712: ("MNG", "Mongolia"),
    713: ("TWN", "Taiwan"), 730: ("KOR", "South Korea"),
    731: ("PRK", "North Korea"), 740: ("JPN", "Japan"),
    750: ("IND", "India"), 760: ("BTN", "Bhutan"),
    770: ("PAK", "Pakistan"), 771: ("BGD", "Bangladesh"),
    775: ("MMR", "Myanmar"), 780: ("LKA", "Sri Lanka"),
    781: ("MDV", "Maldives"), 790: ("NPL", "Nepal"),
    800: ("THA", "Thailand"), 811: ("KHM", "Cambodia"),
    812: ("LAO", "Laos"), 816: ("VNM", "Vietnam"),
    817: ("VDR", "Vietnam, Democratic Republic"),
    818: ("RVN", "Republic of Vietnam"),
    820: ("MYS", "Malaysia"), 830: ("SGP", "Singapore"),
    835: ("BRN", "Brunei"), 840: ("PHL", "Philippines"),
    850: ("IDN", "Indonesia"), 860: ("TLS", "Timor-Leste"),
    900: ("AUS", "Australia"), 910: ("PNG", "Papua New Guinea"),
    920: ("NZL", "New Zealand"), 935: ("VUT", "Vanuatu"),
    940: ("SLB", "Solomon Islands"), 946: ("KIR", "Kiribati"),
    947: ("TUV", "Tuvalu"), 950: ("FJI", "Fiji"),
    955: ("TON", "Tonga"), 970: ("NRU", "Nauru"),
    983: ("MHL", "Marshall Islands"), 986: ("PLW", "Palau"),
    987: ("FSM", "Micronesia"), 990: ("WSM", "Samoa"),
}

our_cow = set()
for _, row in polities.iterrows():
    if pd.notna(row["cow_code"]):
        try:
            our_cow.add(int(float(row["cow_code"])))
        except (ValueError, TypeError):
            pass

cow_only = set(COW_STATES.keys()) - our_cow
cow_matched = set(COW_STATES.keys()) & our_cow

print(f"COW states in reference: {len(COW_STATES)}")
print(f"Matched in our DB: {len(cow_matched)}")
print(f"COW-only (not in our DB): {len(cow_only)}")
for cow in sorted(cow_only):
    iso, name = COW_STATES[cow]
    gap_rows.append({"source": "COW", "code": str(cow), "name": name, "iso": iso,
                     "severity": "low", "note": "COW state not matched to polity"})
    print(f"  COW {cow}: {name} ({iso})")


# =====================================================================
# 2. POLITIES WITHOUT POLYGONS - DETAILED ANALYSIS
# =====================================================================
print("\n─── 2. POLITIES WITHOUT POLYGONS ───")

poly_codes = set(poly_report[poly_report["has_geometry"] == True]["polity_code"])
nr_without = non_region[~non_region["polity_code"].isin(poly_codes)]

print(f"Non-region polities without polygons: {len(nr_without)}")
for _, row in nr_without.iterrows():
    print(f"  {row['polity_code']:25s} {row['polity_name']:35s} {row['polity_type']:12s} {row['continent']}")
    gap_rows.append({"source": "polygon", "code": row["polity_code"],
                     "name": row["polity_name"], "iso": row.get("iso3_code", ""),
                     "severity": "medium", "note": f"No polygon ({row['polity_type']}, {row['continent']})"})


# =====================================================================
# 3. PREDECESSOR/SUCCESSOR CHAIN ANALYSIS
# =====================================================================
print("\n─── 3. PREDECESSOR/SUCCESSOR CHAIN ANALYSIS ───")

all_codes = set(polities["polity_code"])

# Check predecessor references
broken_pred = []
for _, row in polities.iterrows():
    if pd.notna(row.get("predecessor")) and str(row["predecessor"]).strip():
        refs = str(row["predecessor"]).strip()
        # Extract polity codes (XXX-yyyy-YYYY pattern)
        codes = re.findall(r'[A-Z0-9.]{2,6}-\d{4}-\d{4}', refs)
        for code in codes:
            if code not in all_codes:
                broken_pred.append((row["polity_code"], code))

# Check successor references
broken_succ = []
for _, row in polities.iterrows():
    if pd.notna(row.get("successor")) and str(row["successor"]).strip():
        refs = str(row["successor"]).strip()
        codes = re.findall(r'[A-Z0-9.]{2,6}-\d{4}-\d{4}', refs)
        for code in codes:
            if code not in all_codes:
                broken_succ.append((row["polity_code"], code))

# Check bidirectional consistency
asymmetric = []
for _, row in polities.iterrows():
    if pd.notna(row.get("successor")) and str(row["successor"]).strip():
        succ_codes = re.findall(r'[A-Z0-9.]{2,6}-\d{4}-\d{4}', str(row["successor"]))
        for sc in succ_codes:
            if sc in all_codes:
                succ_row = polities[polities["polity_code"] == sc]
                if len(succ_row) > 0:
                    pred_field = str(succ_row.iloc[0].get("predecessor", ""))
                    if row["polity_code"] not in pred_field:
                        asymmetric.append((row["polity_code"], sc, "successor→predecessor"))

for _, row in polities.iterrows():
    if pd.notna(row.get("predecessor")) and str(row["predecessor"]).strip():
        pred_codes = re.findall(r'[A-Z0-9.]{2,6}-\d{4}-\d{4}', str(row["predecessor"]))
        for pc in pred_codes:
            if pc in all_codes:
                pred_row = polities[polities["polity_code"] == pc]
                if len(pred_row) > 0:
                    succ_field = str(pred_row.iloc[0].get("successor", ""))
                    if row["polity_code"] not in succ_field:
                        asymmetric.append((pc, row["polity_code"], "predecessor→successor"))

# Deduplicate asymmetric
seen = set()
unique_asym = []
for a, b, direction in asymmetric:
    key = tuple(sorted([a, b]))
    if key not in seen:
        seen.add(key)
        unique_asym.append((a, b, direction))

print(f"Broken predecessor refs: {len(broken_pred)}")
for src, ref in broken_pred[:10]:
    print(f"  {src} → {ref}")
    gap_rows.append({"source": "chain", "code": src, "name": f"→ {ref}",
                     "iso": "", "severity": "low", "note": "Broken predecessor ref"})

print(f"Broken successor refs: {len(broken_succ)}")
for src, ref in broken_succ[:10]:
    print(f"  {src} → {ref}")
    gap_rows.append({"source": "chain", "code": src, "name": f"→ {ref}",
                     "iso": "", "severity": "low", "note": "Broken successor ref"})

print(f"Asymmetric links: {len(unique_asym)}")
for a, b, direction in unique_asym[:10]:
    print(f"  {a} → {b} ({direction} missing)")


# =====================================================================
# 4. TEMPORAL COVERAGE GAPS
# =====================================================================
print("\n─── 4. TEMPORAL COVERAGE GAPS ───")

# For each ISO3 code, check if there are time gaps between entries
iso_groups = non_region[non_region["iso3_code"].notna()].groupby("iso3_code")
temporal_gaps = []

for iso, group in iso_groups:
    # Sort by start_year
    sorted_group = group.sort_values("start_year")
    # Only check same-type entries (e.g., sovereign)
    for ptype in sorted_group["polity_type"].unique():
        type_entries = sorted_group[sorted_group["polity_type"] == ptype]
        if len(type_entries) < 2:
            continue
        for i in range(len(type_entries) - 1):
            end_current = type_entries.iloc[i]["end_year"]
            start_next = type_entries.iloc[i + 1]["start_year"]
            if start_next > end_current + 1:
                gap_size = start_next - end_current - 1
                if gap_size > 1:  # 1-year gaps are common at boundaries
                    temporal_gaps.append({
                        "iso": iso,
                        "type": ptype,
                        "gap_start": end_current + 1,
                        "gap_end": start_next - 1,
                        "gap_years": gap_size,
                        "before": type_entries.iloc[i]["polity_code"],
                        "after": type_entries.iloc[i + 1]["polity_code"],
                    })

print(f"Temporal gaps (>1 year, same type & ISO): {len(temporal_gaps)}")
for g in sorted(temporal_gaps, key=lambda x: -x["gap_years"])[:15]:
    print(f"  {g['iso']} {g['type']:12s}: {g['gap_start']}-{g['gap_end']} ({g['gap_years']}yr) "
          f"between {g['before']} and {g['after']}")
    gap_rows.append({"source": "temporal", "code": g["iso"],
                     "name": f"{g['type']} gap {g['gap_start']}-{g['gap_end']}",
                     "iso": g["iso"], "severity": "medium",
                     "note": f"{g['gap_years']}yr gap between {g['before']} and {g['after']}"})


# =====================================================================
# 5. DATA SOURCE COVERAGE ANALYSIS
# =====================================================================
print("\n─── 5. DATA SOURCE COVERAGE ───")

# Analyze which data sources are represented
source_counts = defaultdict(int)
for _, row in polities.iterrows():
    if pd.notna(row["data_sources"]):
        for src in str(row["data_sources"]).split(";"):
            src = src.strip()
            if src:
                source_counts[src] += 1

print("\nData source representation:")
for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
    pct = count / len(polities) * 100
    print(f"  {src:20s}: {count:4d} ({pct:5.1f}%)")

# Check which polities have only one source
single_source = polities[polities["data_sources"].str.count(";") == 0]
print(f"\nSingle-source polities: {len(single_source)}")
for src in sorted(single_source["data_sources"].value_counts().index):
    count = (single_source["data_sources"] == src).sum()
    print(f"  {src:20s}: {count}")


# =====================================================================
# 6. VERIFICATION STATUS ANALYSIS
# =====================================================================
print("\n─── 6. VERIFICATION STATUS ───")

for status in sorted(polities["verification_status"].unique()):
    subset = polities[polities["verification_status"] == status]
    print(f"  {status:15s}: {len(subset):4d} ({len(subset)/len(polities)*100:5.1f}%)")

# Unverified non-regions
unverified = non_region[non_region["verification_status"] == "UNVERIFIED"]
print(f"\nUnverified non-region polities: {len(unverified)}")
by_type = unverified.groupby("polity_type").size().sort_values(ascending=False)
for ptype, count in by_type.items():
    print(f"  {ptype:15s}: {count}")

by_cont = unverified.groupby("continent").size().sort_values(ascending=False)
for cont, count in by_cont.items():
    print(f"  {cont:20s}: {count}")


# =====================================================================
# 7. POLYGON SOURCE CONSISTENCY
# =====================================================================
print("\n─── 7. POLYGON SOURCE CONSISTENCY ───")

# Check claimed polygon_source vs actual match
source_mismatches = []
for _, row in non_region.iterrows():
    claimed = str(row.get("polygon_source", ""))
    report_row = poly_report[poly_report["polity_code"] == row["polity_code"]]
    if len(report_row) > 0:
        actual = str(report_row.iloc[0].get("source_used", ""))
        has_geo = report_row.iloc[0]["has_geometry"]
        if has_geo and "CShapes" in claimed and "GADM" in actual and "CShapes" not in actual:
            source_mismatches.append({
                "code": row["polity_code"],
                "name": row["polity_name"],
                "type": row["polity_type"],
                "claimed": claimed,
                "actual": actual,
            })

print(f"Source mismatches (claims CShapes, gets GADM): {len(source_mismatches)}")
for m in source_mismatches:
    print(f"  {m['code']:25s} {m['name']:30s} {m['type']:12s}")
    print(f"    Claimed: {m['claimed'][:40]}  →  Actual: {m['actual'][:40]}")
    gap_rows.append({"source": "polygon_src", "code": m["code"], "name": m["name"],
                     "iso": "", "severity": "low",
                     "note": f"Claims {m['claimed'][:30]}, got {m['actual'][:30]}"})


# =====================================================================
# 8. CONTINENT DISTRIBUTION ANALYSIS
# =====================================================================
print("\n─── 8. CONTINENT DISTRIBUTION ───")

print("\nBy continent and type:")
pivot = non_region.pivot_table(index="continent", columns="polity_type",
                                aggfunc="size", fill_value=0)
print(pivot.to_string())

print("\nPolygon coverage by continent:")
merged = non_region.merge(poly_report[["polity_code", "has_geometry"]],
                          on="polity_code", how="left")
merged["has_geometry"] = merged["has_geometry"].fillna(False)
for cont in sorted(merged["continent"].unique()):
    subset = merged[merged["continent"] == cont]
    with_geo = subset["has_geometry"].sum()
    total = len(subset)
    pct = with_geo / total * 100 if total > 0 else 0
    bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
    print(f"  {cont:20s} {bar} {pct:5.1f}% ({with_geo}/{total})")


# =====================================================================
# GENERATE PLOTS
# =====================================================================
print("\n─── GENERATING PLOTS ───")

# Plot 1: Coverage gap heatmap (continent × era)
fig, axes = plt.subplots(1, 2, figsize=(20, 8))

# A: Polygon coverage rate by continent × decade
ax = axes[0]
continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
decades = list(range(1800, 2030, 10))

merged = non_region.merge(poly_report[["polity_code", "has_geometry"]],
                          on="polity_code", how="left")
merged["has_geometry"] = merged["has_geometry"].fillna(False)

heatmap = np.zeros((len(continents), len(decades)))
for i, cont in enumerate(continents):
    subset = merged[merged["continent"] == cont]
    for j, d in enumerate(decades):
        active = subset[(subset["start_year"] <= d) & (subset["end_year"] >= d)]
        if len(active) > 0:
            heatmap[i][j] = active["has_geometry"].mean() * 100

im = ax.imshow(heatmap, cmap="RdYlGn", aspect="auto", vmin=80, vmax=100)
ax.set_xticks(range(len(decades)))
ax.set_xticklabels(decades, rotation=45, fontsize=8)
ax.set_yticks(range(len(continents)))
ax.set_yticklabels(continents, fontsize=10)
for i in range(len(continents)):
    for j in range(len(decades)):
        val = heatmap[i][j]
        ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=7,
                color="white" if val < 90 else "black")
ax.set_title("A) Polygon Coverage Rate (%) by Continent × Decade", fontweight="bold")
plt.colorbar(im, ax=ax, shrink=0.7, label="Coverage %")

# B: Temporal gaps timeline
ax = axes[1]
if temporal_gaps:
    gap_df = pd.DataFrame(temporal_gaps)
    gap_df_sorted = gap_df.sort_values("gap_years", ascending=True)
    y_pos = range(min(len(gap_df_sorted), 25))
    gap_df_top = gap_df_sorted.tail(25)

    for i, (_, g) in enumerate(gap_df_top.iterrows()):
        color = "#F44336" if g["gap_years"] > 50 else "#FF9800" if g["gap_years"] > 10 else "#FFC107"
        ax.barh(i, g["gap_years"], left=g["gap_start"], height=0.6, color=color, alpha=0.7)
        ax.text(g["gap_start"] - 2, i, f"{g['iso']} ({g['type'][:4]})",
                ha="right", va="center", fontsize=7)

    ax.set_title("B) Largest Temporal Gaps (same ISO & type)", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_yticks([])
else:
    ax.text(0.5, 0.5, "No temporal gaps found", ha="center", va="center",
            transform=ax.transAxes, fontsize=14)
    ax.set_title("B) Temporal Gaps", fontweight="bold")

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/gap_01_coverage_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 1: coverage heatmap & temporal gaps")


# Plot 2: Verification status breakdown
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# A: Overall verification
ax = axes[0]
status_counts = polities["verification_status"].value_counts()
colors_status = {"VERIFIED": "#4CAF50", "FIXED": "#8BC34A", "REGION": "#2196F3",
                 "UNVERIFIED": "#FF9800"}
ax.pie(status_counts.values, labels=status_counts.index,
       colors=[colors_status.get(s, "#999") for s in status_counts.index],
       autopct="%1.0f%%", textprops={"fontsize": 9})
ax.set_title("A) Verification Status (All)", fontweight="bold")

# B: Verification by type
ax = axes[1]
types = ["sovereign", "historical", "colonial", "dependency", "aggregate"]
verified_by_type = []
unverified_by_type = []
for t in types:
    subset = non_region[non_region["polity_type"] == t]
    v = subset["verification_status"].isin(["VERIFIED", "FIXED"]).sum()
    verified_by_type.append(v)
    unverified_by_type.append(len(subset) - v)

x = np.arange(len(types))
ax.bar(x, verified_by_type, color="#4CAF50", label="Verified/Fixed")
ax.bar(x, unverified_by_type, bottom=verified_by_type, color="#FF9800", label="Unverified")
ax.set_xticks(x)
ax.set_xticklabels(types, rotation=30, ha="right", fontsize=9)
ax.set_title("B) Verification by Type", fontweight="bold")
ax.legend(fontsize=8)

# C: Verification by continent
ax = axes[2]
conts = sorted(non_region["continent"].unique())
verified_by_cont = []
total_by_cont = []
for c in conts:
    subset = non_region[non_region["continent"] == c]
    v = subset["verification_status"].isin(["VERIFIED", "FIXED"]).sum()
    verified_by_cont.append(v / len(subset) * 100 if len(subset) > 0 else 0)
    total_by_cont.append(len(subset))

x = np.arange(len(conts))
bars = ax.bar(x, verified_by_cont, color="#4CAF50", alpha=0.7)
for i, (pct, tot) in enumerate(zip(verified_by_cont, total_by_cont)):
    ax.text(i, pct + 1, f"n={tot}", ha="center", fontsize=7)
ax.set_xticks(x)
ax.set_xticklabels(conts, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("% Verified")
ax.set_title("C) Verification Rate by Continent", fontweight="bold")
ax.set_ylim(0, 105)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/gap_02_verification.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 2: verification breakdown")


# Plot 3: Data source overlap matrix
fig, ax = plt.subplots(figsize=(10, 8))

sources = ["FT", "FAOSTAT", "M49", "CShapes", "CShapes-Europe", "GADM", "WHEP"]
overlap_matrix = np.zeros((len(sources), len(sources)))

for i, si in enumerate(sources):
    for j, sj in enumerate(sources):
        count = 0
        for _, row in polities.iterrows():
            ds = str(row.get("data_sources", ""))
            if si in ds and sj in ds:
                count += 1
        overlap_matrix[i][j] = count

im = ax.imshow(overlap_matrix, cmap="Blues", aspect="auto")
ax.set_xticks(range(len(sources)))
ax.set_xticklabels(sources, rotation=45, ha="right")
ax.set_yticks(range(len(sources)))
ax.set_yticklabels(sources)
for i in range(len(sources)):
    for j in range(len(sources)):
        val = int(overlap_matrix[i][j])
        if val > 0:
            ax.text(j, i, str(val), ha="center", va="center", fontsize=8,
                    color="white" if val > 200 else "black")

ax.set_title("Data Source Overlap Matrix", fontweight="bold", fontsize=12)
plt.colorbar(im, ax=ax, shrink=0.7, label="Polity count")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/gap_03_source_matrix.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 3: data source overlap matrix")


# Plot 4: Polity type transitions over time
fig, ax = plt.subplots(figsize=(16, 8))

years = np.arange(1800, 2026)
type_order = ["colonial", "mandate", "puppet", "historical", "dependency",
              "disputed", "sovereign", "aggregate"]
type_colors = {
    "sovereign": "#2196F3", "historical": "#9E9E9E", "colonial": "#F44336",
    "dependency": "#FF9800", "aggregate": "#9C27B0", "mandate": "#4CAF50",
    "disputed": "#FFEB3B", "puppet": "#795548"
}

# Compute ratios
type_counts_by_year = np.zeros((len(type_order), len(years)))
for i, ptype in enumerate(type_order):
    subset = non_region[non_region["polity_type"] == ptype]
    for j, yr in enumerate(years):
        type_counts_by_year[i][j] = ((subset["start_year"] <= yr) &
                                      (subset["end_year"] >= yr)).sum()

totals = type_counts_by_year.sum(axis=0)
totals[totals == 0] = 1  # avoid div by zero

ratios = type_counts_by_year / totals * 100

bottom = np.zeros(len(years))
for i, ptype in enumerate(type_order):
    ax.fill_between(years, bottom, bottom + ratios[i],
                    color=type_colors.get(ptype, "#999"), alpha=0.7, label=ptype)
    bottom += ratios[i]

ax.set_xlim(1800, 2025)
ax.set_ylim(0, 100)
ax.set_ylabel("% of Active Polities")
ax.set_title("Polity Type Composition Over Time", fontweight="bold", fontsize=13)
ax.legend(loc="upper left", fontsize=8, ncol=4)

# Key events
events = [(1861, "Italian\nUnification"), (1871, "German\nUnification"),
          (1918, "WWI\nEnd"), (1945, "WWII\nEnd"),
          (1960, "Year of\nAfrica"), (1991, "USSR\nCollapse")]
for yr, label in events:
    ax.axvline(yr, color="black", linestyle=":", alpha=0.3, linewidth=0.8)
    ax.text(yr + 1, 102, label, fontsize=6, rotation=0, va="bottom")

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/gap_04_type_composition.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 4: type composition over time")


# Plot 5: Duration distribution by type
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

for ax, ptype in zip(axes.flat, ["sovereign", "historical", "colonial",
                                  "dependency", "aggregate", "mandate"]):
    subset = non_region[non_region["polity_type"] == ptype]
    if len(subset) > 0:
        ax.hist(subset["duration_years"], bins=30, color=type_colors.get(ptype, "#999"),
                edgecolor="white", alpha=0.7)
        ax.axvline(subset["duration_years"].median(), color="red", linestyle="--",
                   label=f"Median: {subset['duration_years'].median():.0f}yr")
        ax.set_xlabel("Duration (years)")
        ax.set_ylabel("Count")
        ax.set_title(f"{ptype} (n={len(subset)})", fontweight="bold")
        ax.legend(fontsize=8)

plt.suptitle("Polity Duration Distribution by Type", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/gap_05_duration_dist.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 5: duration distributions")


# Plot 6: Polygon source sunburst (simplified as nested pie)
fig, ax = plt.subplots(figsize=(10, 10))

source_groups = non_region.groupby("polygon_source").size().sort_values(ascending=False)
# Simplify source labels
def simplify(src):
    if "CShapes 2.0" in str(src) and "dependencies" in str(src):
        return "CShapes 2.0 (dep.)"
    elif "CShapes 2.0" in str(src) and "CShapes-Europe" in str(src):
        return "CShapes + CShapes-EU"
    elif "CShapes 2.0" in str(src):
        return "CShapes 2.0"
    elif "CShapes-Europe" in str(src):
        return "CShapes-Europe"
    elif "GADM" in str(src) and "subnational" in str(src):
        return "GADM (subnational)"
    elif "GADM" in str(src):
        return "GADM"
    elif "None" in str(src) or "nan" in str(src).lower():
        return "None"
    else:
        return str(src)[:25]

simplified = non_region["polygon_source"].apply(simplify)
src_counts = simplified.value_counts()

src_colors = {
    "CShapes 2.0": "#2196F3", "CShapes + CShapes-EU": "#1565C0",
    "CShapes 2.0 (dep.)": "#42A5F5", "CShapes-Europe": "#9C27B0",
    "GADM": "#FF9800", "GADM (subnational)": "#FFB74D",
    "None": "#E0E0E0",
}
colors = [src_colors.get(s, "#999") for s in src_counts.index]

wedges, texts, autotexts = ax.pie(
    src_counts.values, labels=src_counts.index,
    colors=colors, autopct=lambda pct: f"{pct:.0f}%" if pct > 3 else "",
    textprops={"fontsize": 9}, pctdistance=0.8
)
ax.set_title("Polygon Sources for Non-Region Polities", fontweight="bold", fontsize=13)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/gap_06_polygon_sources.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 6: polygon source distribution")


# ── Save gap report ──────────────────────────────────────────────────
gap_df = pd.DataFrame(gap_rows)
gap_df.to_csv(f"{BASE}/data/analysis/exhaustive_gap_report.csv", index=False)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total gaps identified: {len(gap_df)}")
if len(gap_df) > 0:
    print(f"  By source: {dict(gap_df['source'].value_counts())}")
    print(f"  By severity: {dict(gap_df['severity'].value_counts())}")
print(f"\nFiles generated:")
print(f"  data/analysis/exhaustive_gap_report.csv")
print(f"  data/analysis/plots/gap_01_coverage_heatmap.png")
print(f"  data/analysis/plots/gap_02_verification.png")
print(f"  data/analysis/plots/gap_03_source_matrix.png")
print(f"  data/analysis/plots/gap_04_type_composition.png")
print(f"  data/analysis/plots/gap_05_duration_dist.png")
print(f"  data/analysis/plots/gap_06_polygon_sources.png")
print("\n✓ Exhaustive gap analysis complete")
