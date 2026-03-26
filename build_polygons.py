#!/usr/bin/env python3
"""
Build polygon database for WHEP polities.

Reads:
  - data/final/polities_database.csv (810 polity entries)
  - data/geodata/cshapes2_full.gpkg (CShapes 2.0, dependencies=TRUE)
  - data/geodata/cshapes2_sovereign.gpkg (CShapes 2.0, sovereign only)
  - WHEP reference project geodata (CShapes-Europe, GADM)

Writes:
  - data/geodata/polities_polygons.gpkg (unified polygon database)
  - data/analysis/polygon_matching_report.csv
"""

import csv
import os
import re
import warnings
from datetime import datetime

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

warnings.filterwarnings("ignore")

BASE = "/home/usuario/whep-polities"
REF = "/home/usuario/WHEP.worktrees/lbm364dl-refactor-polities/data-raw/polities_inputs"

# ── Load data ────────────────────────────────────────────────────────

print("Loading data sources...")
polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
cshapes = gpd.read_file(f"{BASE}/data/geodata/cshapes2_full.gpkg")
cshapes_sov = gpd.read_file(f"{BASE}/data/geodata/cshapes2_sovereign.gpkg")
cshapes_eu = gpd.read_file(f"{REF}/cshapes_europe_geometries.gpkg")
gadm = gpd.read_file(f"{REF}/gadm_geometries.gpkg")
gadm_full = gpd.read_file("/home/usuario/LandInG/gadm/gadm36_levels.gpkg", layer="level0")

print(f"  Polities: {len(polities)}")
print(f"  CShapes (full): {len(cshapes)}")
print(f"  CShapes (sovereign): {len(cshapes_sov)}")
print(f"  CShapes-Europe: {len(cshapes_eu)}")
print(f"  GADM (ref): {len(gadm)}")
print(f"  GADM (full): {len(gadm_full)}")

# Parse CShapes dates
cshapes["start_dt"] = pd.to_datetime(cshapes["start"])
cshapes["end_dt"] = pd.to_datetime(cshapes["end"])
cshapes["start_year"] = cshapes["start_dt"].dt.year
cshapes["end_year"] = cshapes["end_dt"].dt.year

cshapes_sov["start_dt"] = pd.to_datetime(cshapes_sov["start"])
cshapes_sov["end_dt"] = pd.to_datetime(cshapes_sov["end"])
cshapes_sov["start_year"] = cshapes_sov["start_dt"].dt.year
cshapes_sov["end_year"] = cshapes_sov["end_dt"].dt.year


# ── Name mapping: polity name → CShapes country_name ────────────────

# Direct name mappings (polity name -> CShapes name)
CSHAPES_NAME_MAP = {
    # Sovereign states
    "United States of America": "United States of America",
    "United Kingdom": "United Kingdom",
    "France": "France",
    "Germany": "German Federal Republic",
    "Russia": "Russia (Soviet Union)",
    "China": "China",
    "Japan": "Japan",
    "Italy": "Italy/Sardinia",
    "Spain": "Spain",
    "Portugal": "Portugal",
    "Netherlands": "Netherlands",
    "Belgium": "Belgium",
    "Switzerland": "Switzerland",
    "Sweden": "Sweden",
    "Norway": "Norway",
    "Denmark": "Denmark",
    "Finland": "Finland",
    "Austria": "Austria",
    "Hungary": "Hungary",
    "Poland": "Poland",
    "Romania": "Rumania",
    "Greece": "Greece",
    "Bulgaria": "Bulgaria",
    "Serbia": "Serbia",
    "Albania": "Albania",
    "Turkey (Ottoman Empire)": "Turkey (Ottoman Empire)",
    "Türkiye": "Turkey (Ottoman Empire)",
    "Ireland": "Ireland",
    "Iceland": "Iceland",
    "Luxembourg": "Luxembourg",
    "Liechtenstein": "Liechtenstein",
    "Monaco": "Monaco",
    "San Marino": "San Marino",
    "Holy See": "Italy/Sardinia",  # fallback
    "Andorra": "Andorra",
    "Canada": "Canada",
    "Mexico": "Mexico",
    "Brazil": "Brazil",
    "Argentina": "Argentina",
    "Chile": "Chile",
    "Colombia": "Colombia",
    "Venezuela": "Venezuela",
    "Peru": "Peru",
    "Bolivia": "Bolivia",
    "Ecuador": "Ecuador",
    "Uruguay": "Uruguay",
    "Paraguay": "Paraguay",
    "Panama": "Panama",
    "Costa Rica": "Costa Rica",
    "Nicaragua": "Nicaragua",
    "Honduras": "Honduras",
    "El Salvador": "El Salvador",
    "Guatemala": "Guatemala",
    "Cuba": "Cuba",
    "Dominican Republic": "Dominican Republic",
    "Haiti": "Haiti",
    "Jamaica": "Jamaica",
    "Trinidad and Tobago": "Trinidad and Tobago",
    "Barbados": "Barbados",
    "Bahamas": "Bahamas",
    "India": "India",
    "India (to 1947)": "India",
    "Pakistan": "Pakistan",
    "Bangladesh": "Bangladesh",
    "Myanmar": "Myanmar (Burma)",
    "Myanmar (Burma)": "Myanmar (Burma)",
    "Thailand": "Thailand",
    "Cambodia": "Cambodia (Kampuchea)",
    "Laos": "Laos",
    "Vietnam": "Vietnam (Annam/Cochin China/Tonkin)",
    "Indonesia": "Indonesia",
    "Philippines": "Philippines",
    "Malaysia": "Malaysia",
    "Singapore": "Singapore",
    "Brunei Darussalam": "Brunei",
    "Sri Lanka": "Sri Lanka (Ceylon)",
    "Nepal": "Nepal",
    "Bhutan": "Bhutan",
    "Afghanistan": "Afghanistan",
    "Iran": "Iran (Persia)",
    "Iraq": "Iraq",
    "Saudi Arabia": "Saudi Arabia",
    "Egypt": "Egypt",
    "Morocco": "Morocco",
    "Algeria": "Algeria",
    "Tunisia": "Tunisia",
    "Libya": "Libya",
    "Sudan": "Sudan",
    "South Sudan": "South Sudan",
    "Ethiopia": "Ethiopia",
    "Somalia": "Somalia",
    "Kenya": "Kenya",
    "Tanzania": "Tanzania (Tanganyika)",
    "Uganda": "Uganda",
    "Mozambique": "Mozambique",
    "Madagascar": "Madagascar (Malagasy)",
    "South Africa": "South Africa",
    "Nigeria": "Nigeria",
    "Ghana": "Ghana",
    "Cameroon": "Cameroon",
    "Senegal": "Senegal",
    "Côte d'Ivoire": "Cote D'Ivoire",
    "Mali": "Mali",
    "Niger": "Niger",
    "Chad": "Chad",
    "Burkina Faso": "Burkina Faso (Upper Volta)",
    "Guinea": "Guinea",
    "Benin": "Benin",
    "Togo": "Togo",
    "Sierra Leone": "Sierra Leone",
    "Liberia": "Liberia",
    "Mauritania": "Mauritania",
    "Gabon": "Gabon",
    "Congo": "Congo",
    "Democratic Republic of the Congo": "Congo, Democratic Republic of (Zaire)",
    "Central African Republic": "Central African Republic",
    "Angola": "Angola",
    "Zambia": "Zambia",
    "Zimbabwe": "Zimbabwe (Rhodesia)",
    "Malawi": "Malawi",
    "Botswana": "Botswana",
    "Namibia": "Namibia",
    "Eswatini": "Swaziland (Eswatini)",
    "Lesotho": "Lesotho",
    "Rwanda": "Rwanda",
    "Burundi": "Burundi",
    "Djibouti": "Djibouti",
    "Eritrea": "Eritrea",
    "Gambia": "Gambia",
    "Equatorial Guinea": "Equatorial Guinea",
    "Guinea-Bissau": "Guinea-Bissau",
    "Cabo Verde": "Cape Verde",
    "Comoros": "Comoros",
    "Mauritius": "Mauritius",
    "Seychelles": "Seychelles",
    "Sao Tome and Principe": "Sao Tome and Principe",
    "Australia": "Australia",
    "New Zealand": "New Zealand",
    "Fiji": "Fiji",
    "Papua New Guinea": "Papua New Guinea",
    "Samoa": "Samoa",
    "Tonga": "Tonga",
    "Kiribati": "Kiribati",
    "Nauru": "Nauru",
    "Tuvalu": "Tuvalu",
    "Vanuatu": "Vanuatu",
    "Solomon Islands": "Solomon Islands",
    "Marshall Islands": "Marshall Islands",
    "Micronesia": "Micronesia (Federated states of)",
    "Palau": "Palau",
    "Mongolia": "Mongolia",
    "North Korea": "Korea, People's Republic of",
    "South Korea": "Korea, Republic of",
    "Taiwan": "Taiwan",
    "Jordan": "Jordan",
    "Lebanon": "Lebanon",
    "Syria": "Syria",
    "Syrian Arab Republic": "Syria",
    "Israel": "Israel",
    "Kuwait": "Kuwait",
    "Bahrain": "Bahrain",
    "Qatar": "Qatar",
    "United Arab Emirates": "United Arab Emirates",
    "Oman": "Oman",
    "Yemen": "Yemen (Arab Republic of Yemen)",
    "North Yemen": "Yemen (Arab Republic of Yemen)",
    "South Yemen": "Yemen, People's Republic of",
    "Cyprus": "Cyprus",
    "Malta": "Malta",
    "Estonia": "Estonia",
    "Latvia": "Latvia",
    "Lithuania": "Lithuania",
    "Belarus": "Belarus (Byelorussia)",
    "Ukraine": "Ukraine",
    "Moldova": "Moldova",
    "Georgia": "Georgia",
    "Armenia": "Armenia",
    "Azerbaijan": "Azerbaijan",
    "Kazakhstan": "Kazakhstan",
    "Uzbekistan": "Uzbekistan",
    "Turkmenistan": "Turkmenistan",
    "Tajikistan": "Tajikistan",
    "Kyrgyzstan": "Kyrgyz Republic",
    "Czechia": "Czech Republic",
    "Slovakia": "Slovakia",
    "Croatia": "Croatia",
    "Slovenia": "Slovenia",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "North Macedonia": "Macedonia (FYROM/North Macedonia)",
    "Montenegro": "Montenegro",
    "Kosovo": "Kosovo",
    "Timor-Leste": "East Timor",
    "Western Sahara": "Spanish Sahara",

    # Period-specific entries (match via base CShapes name)
    "Alaska": "Alaska",
    "Alaska (to 1959)": "Alaska",
    "Hawaii": "Hawaii",
    "Hawaii (1898-1959)": "Hawaii",
    "Bosnia (to 1908)": "Bosnia",
    "Herzegovina (to 1908)": "Herzegovina",
    "Bukhara": "Bokhara",
    "Bukhara (to 1920)": "Bokhara",
    "Khiva": "Khiva",
    "Khiva (to 1920)": "Khiva",
    "Lagos (to 1906)": "Lagos",
    "New South Wales (to 1900)": "New South Wales",
    "Queensland (to 1900)": "Queensland",
    "South Australia (to 1900)": "South Australia",
    "Van Diemen's Land (Tasmania) (to 1900)": "Tasmania",
    "Victoria (to 1900)": "Victoria",
    "Western Australia (to 1900)": "Western Australia",
    "Tibet": "Tibet",
    "Tibet (1913-1914)": "Tibet",
    "Tibet (1914-1950)": "Tibet",
    "Natal (colony)": "Natal",
    "Natal (to 1895)": "Natal",
    "Natal (1895-1910)": "Natal",
    "Yugoslavia (1992-2006)": "Yugoslavia/Serbia",
    "Yugoslavia": "Yugoslavia/Serbia",
    "Oil Rivers Protectorate (to 1898)": "Oil Rivers Protectorate",
    "Papua": "Papua",
    "Papua (to 1949)": "Papua",
    "Pahang (1888-1896)": "Pahang",
    "Selangore (to 1896)": "Selangore",
    "Southern Sakhalin Island (1905-1945)": "Southern Sakhalin Island",
    "Inini (1930-1946)": "Inini",
    "Spanish West Africa (1912-1958)": "Spanish West Africa",
    "Spanish West Africa (to 1912)": "Spanish West Africa",
    "East Aden Protectorate (1937-1962)": "East Aden Protectorate",
    "Federation of Rhodesia and Nyasaland (1953-1964)": "Federation of Rhodesia and Nyasaland",
    "Federation of South Arabia (1962-1967)": "Federation of South Arabia",
    "North Vietnam": "Vietnam, Democratic Republic of",
    "South Vietnam": "Vietnam, Republic of",
    "Sabah (British Borneo) (1888-1963)": "Sabah (North Borneo)",
    "Kashmir (North Azad) (1947-1949)": "Kashmir (North, Azad)",
    "Straits Settlement (to 1946)": "Straits Settlements",
    "Dutch new Guinea (1949-1969)": "West Irian (Dutch New Guinea)",
    "Southern zone of Spanish Morocco (1956-1958)": "Southern zone of Spanish Morocco",
    "Belgium-Luxembourg": "Belgium",  # fallback to Belgium polygon
    "Ethiopia PDR": "Ethiopia",  # fallback
    "Pacific Islands Trust Territory": "Palau",  # partial fallback
    "British Bechuanaland (to 1895)": "British Bechuanaland",
    "British Protectorate (British Somaliland) (to 1960)": "British Somaliland (Somaliland Republic)",
    "British settlement Oceania": "Fiji",  # partial fallback
    "French India": "India",  # fallback
    "French Guiana (to 1930)": "French Guyana",
    "French Guiana (1930-1946)": "French Guyana",
    "Gaza Strip (1948-1967)": "Gaza",
    "Palmyra Island": "Hawaii",  # closest fallback
    "West Bank (1948-1967)": "West Bank",
    "Palestine": "Palestine",

    # Historical/colonial
    "Austria-Hungary": "Austria-Hungary",
    "Ottoman Empire": "Turkey (Ottoman Empire)",
    "German East Africa": "Tanzania (Tanganyika)",
    "German Togoland": "German Togoland",
    "Cameroon (Kamerun)": "Kamerun",
    "Belgian Congo": "Congo, Democratic Republic of (Zaire)",
    "British East Africa": "Kenya",
    "British Cameroon": "British Cameroons",
    "British Malaya": "Federated Malay States",
    "Bechuanaland Protectorate": "British Bechuanaland",
    "Basutoland": "Lesotho",
    "Gold Coast": "Ghana",
    "Nyasaland Protectorate (Malawi)": "Malawi",
    "Italian Libia Cyrenaica (Lybia)": "Libya",
    "Italian Somaliland": "Italian Somaliland",
    "French Equatorial Africa": "Gabon",  # FEA composite
    "French West Africa": "French West Africa",
    "French Indochina": "Vietnam (Annam/Cochin China/Tonkin)",
    "French Somaliland": "Djibouti",
    "Sudan (Anglo-Egyptian)": "Sudan",
    "Dutch East Indies (Indonesia)": "Indonesia",
    "Manchukuo": "China",
    "Danzig": "Danzig",
    "Newfoundland": "Newfoundland",
    "Czechoslovakia": "Czechoslovakia",
    "Rwanda and Burundi": "Rwanda-Urundi",
    "Sarawak": "Sarawak",
    "Spanish Guinea": "Equatorial Guinea",
    "Spanish Morocco": "Spanish Morocco",
    "New Hebrides": "Vanuatu",
    "Gilbert and Ellice Island": "Kiribati",
    "Cape Colony": "Cape Colony",
    "Natal (colony)": "Natal",
    "Transvaal": "Transvaal",
    "Orange Free State": "Orange Free State",
    "Dodecanese Is.": "Greece",
    "Korea (to 1910)": "Korea",
    "Korea (1910-1945)": "Korea",
    "Straits Settlements": "Straits Settlements",
    "Federated Malay States": "Federated Malay States",
    "Unfederated Malay States": "Unfederated Malay States",
    "French Settlements in Oceania": "French Polynesia",
    "New Guinea": "Papua New Guinea",
    "British New Guinea": "Papua",
    "Aden": "Aden",
    "Zanzibar": "Zanzibar",
    "Sabah (British Borneo)": "Sabah (North Borneo)",
    "Tibet (old)": "Tibet",
    "British Somaliland": "British Somaliland (Somaliland Republic)",
    "British Togoland": "British Togoland",
    "Northern Nigeria": "Northern Nigeria",
    "Southern Nigeria": "Southern Nigeria",

    # Caribbean islands (name map prevents COW code mismatch with CShapes)
    "Dominica": "Dominica",
    "Saint Lucia": "St. Lucia",
    "Saint Vincent and the Grenadines": "St. Vincent and the Grenadines",
    "Antigua and Barbuda": "Antigua & Barbuda",
    "Grenada": "Grenada",

    # Fix ISO code collision mismatches (these entity names must map correctly
    # because their ISO/COW codes collide with different countries)
    "Northeastern Rhodesia": "Northeastern Rhodesia",
    "Northeastern Rhodesia (1900-1911)": "Northeastern Rhodesia",
    "Northwestern Rhodesia": "Northwestern Rhodesia",
    "Northwestern Rhodesia (1900-1905)": "Northwestern Rhodesia",
    "Northwestern Rhodesia (1905-1911)": "Northwestern Rhodesia",
    "Perak": "Perak",
    "Perak (to 1896)": "Perak",
    "Sardinia": "Italy/Sardinia",
    "German Solomon Islands": "German Solomon Islands",
    "German colonies Oceania": "New Guinea (German New Guinea) (Kaiser Wilhelmsland)",
    "Jammu and Kashmir": "Jammu and Kashmir",
    "Jammu and Kashmir (1947-1949)": "Jammu and Kashmir",

    # CShapes-Europe names
    "Two Sicilies": "Two Sicilies",
    "Papal States": "Papal States",
    "Tuscany": "Tuscany",
    "Bavaria": "Bavaria",
    "Saxony": "Saxony",
    "Hanover": "Hanover",
}

# Polity codes where ISO/COW codes collide with a different country.
# COW matching AND GADM ISO fallback are skipped for these to prevent
# wrong-continent polygon assignment.
SKIP_COW_MATCHING = {
    "CHE-1816-1857",   # Chechnya ≠ Switzerland (both CHE/225)
    "SWE-1816-1870",   # Saxe-Weimar ≠ Sweden (both SWE/380)
    "JAM-1947-1949",   # Jammu & Kashmir ≠ Jamaica (both JAM/51)
    "CAN-1800-1982",   # Canton & Enderbury ≠ Canada (both CAN/20)
    "PAL-1889-1912",   # Palmyra Island ≠ Palau (PAL code)
    "SAR-1800-1860",   # Sardinia: COW 338 = Malta in CShapes (use name map)
    "MAN-1932-1945",   # Manchukuo ≠ China (already has name map)
    "GER-1800-1899",   # German Solomon Islands ≠ Germany (GER/255)
    "GER-1884-2025",   # German colonies Oceania ≠ Germany (GER/255)
}

# COW code mapping for secondary matching
COW_CODE_MAP = {}
for _, row in cshapes.iterrows():
    code = row["cowcode"]
    if code and str(code) != "0":
        COW_CODE_MAP.setdefault(str(int(code)) if isinstance(code, float) else str(code), []).append(row["country_name"])


def normalize(name):
    """Normalize a name for matching."""
    import unicodedata
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return name.lower().strip()


def find_cshapes_match(polity_name, polity_code, cow_code, start_year, end_year):
    """Find the best CShapes polygon match for a polity, targeting ~1920 era.
    polity_code is used to check SKIP_COW_MATCHING for ISO/COW collision avoidance."""
    # 1. Direct name mapping
    cs_name = CSHAPES_NAME_MAP.get(polity_name)
    if not cs_name:
        # Try base name without parenthetical
        base = re.sub(r'\s*\(.*?\)\s*$', '', polity_name).strip()
        cs_name = CSHAPES_NAME_MAP.get(base)

    if cs_name:
        matches = cshapes[cshapes["country_name"] == cs_name]
        if len(matches) > 0:
            return select_best_temporal(matches, start_year, end_year)

    # 2. Try COW code matching (skip for known ISO/COW code collisions)
    if cow_code and str(cow_code) not in ("", "nan") and polity_code not in SKIP_COW_MATCHING:
        cow_str = str(int(float(cow_code))) if "." in str(cow_code) else str(cow_code)
        matches = cshapes[cshapes["cowcode"].astype(str) == cow_str]
        if len(matches) > 0:
            return select_best_temporal(matches, start_year, end_year)

    # 3. Fuzzy name matching
    norm_name = normalize(polity_name)
    for _, cs_row in cshapes.drop_duplicates("country_name").iterrows():
        if normalize(cs_row["country_name"]) == norm_name:
            matches = cshapes[cshapes["country_name"] == cs_row["country_name"]]
            return select_best_temporal(matches, start_year, end_year)

    return None


def select_best_temporal(matches, start_year, end_year):
    """Select the CShapes entry with best temporal overlap, targeting ~1920 era."""
    if len(matches) == 1:
        return matches.iloc[0]

    # Target year: middle of our polity's range, clamped to CShapes range
    target = max(1886, min(2019, (start_year + min(end_year, 2019)) // 2))

    best = None
    best_score = -1
    for _, row in matches.iterrows():
        cs_start = row["start_year"]
        cs_end = row["end_year"]
        # Score: overlap with our polity range + bonus for containing target year
        overlap_start = max(start_year, cs_start)
        overlap_end = min(end_year, cs_end)
        overlap = max(0, overlap_end - overlap_start)
        contains_target = 1000 if cs_start <= target <= cs_end else 0
        score = overlap + contains_target
        if score > best_score:
            best_score = score
            best = row
    return best


def find_gadm_match(polity_name):
    """Find a GADM polygon match."""
    norm = normalize(polity_name)
    for _, row in gadm.iterrows():
        if normalize(row["polity_name"]) == norm:
            return row
    return None


def find_cshapes_eu_match(polity_name):
    """Find a CShapes-Europe polygon match."""
    norm = normalize(polity_name)
    for _, row in cshapes_eu.iterrows():
        if normalize(row["polity_name"]) == norm:
            return row
    # Try partial matching
    base = re.sub(r'\s*\(.*?\)\s*$', '', polity_name).strip()
    for _, row in cshapes_eu.iterrows():
        if normalize(row["polity_name"]) == normalize(base):
            return row
    return None


# ── Match all polities ──────────────────────────────────────────────

print("\nMatching polities to polygons...")

results = []
matched = 0
no_geom = 0

for _, p in polities.iterrows():
    pcode = p["polity_code"]
    pname = p["polity_name"]
    ptype = p["polity_type"]
    psource = p["polygon_source"]
    start = int(p["start_year"])
    end = int(p["end_year"])
    cow = p.get("cow_code", "")

    geom = None
    source_used = "none"
    match_name = ""

    # Skip regions (no geometry needed)
    if ptype == "region":
        results.append({
            "polity_code": pcode, "polity_name": pname,
            "source_used": "none (region)", "match_name": "",
            "has_geometry": False
        })
        no_geom += 1
        continue

    # 1. Try CShapes-Europe for pre-1886 European entities
    if "CShapes-Europe" in str(psource):
        eu_match = find_cshapes_eu_match(pname)
        if eu_match is not None:
            geom = eu_match.geometry
            source_used = "CShapes-Europe"
            match_name = eu_match["polity_name"]

    # 2. Try CShapes 2.0 (main source)
    if geom is None and "CShapes" in str(psource):
        cs_match = find_cshapes_match(pname, pcode, cow, start, end)
        if cs_match is not None:
            geom = cs_match.geometry
            source_used = f"CShapes 2.0 ({cs_match['start_year']}-{cs_match['end_year']})"
            match_name = cs_match["country_name"]

    # 3. Try GADM
    if geom is None and "GADM" in str(psource):
        gm_match = find_gadm_match(pname)
        if gm_match is not None:
            geom = gm_match.geometry
            source_used = "GADM 4.1"
            match_name = gm_match["polity_name"]

    # 4. Fallback: try all sources
    if geom is None:
        # Try CShapes anyway
        cs_match = find_cshapes_match(pname, pcode, cow, start, end)
        if cs_match is not None:
            geom = cs_match.geometry
            source_used = f"CShapes 2.0 fallback ({cs_match['start_year']}-{cs_match['end_year']})"
            match_name = cs_match["country_name"]
        else:
            # Try GADM
            gm_match = find_gadm_match(pname)
            if gm_match is not None:
                geom = gm_match.geometry
                source_used = "GADM 4.1 fallback"
                match_name = gm_match["polity_name"]
            else:
                # Try CShapes-Europe
                eu_match = find_cshapes_eu_match(pname)
                if eu_match is not None:
                    geom = eu_match.geometry
                    source_used = "CShapes-Europe fallback"
                    match_name = eu_match["polity_name"]

    # 5. Ultimate fallback: full GADM by ISO3 code
    # Skip for entities with colliding ISO codes (would get wrong country's polygon)
    if geom is None and pd.notna(p.get("iso3_code")) and pcode not in SKIP_COW_MATCHING:
        iso = p["iso3_code"]
        gf = gadm_full[gadm_full["GID_0"] == iso]
        if len(gf) > 0:
            geom = gf.iloc[0].geometry
            source_used = f"GADM 3.6 (full, {iso})"
            match_name = gf.iloc[0]["NAME_0"]

    if geom is not None:
        matched += 1
        results.append({
            "polity_code": pcode, "polity_name": pname,
            "source_used": source_used, "match_name": match_name,
            "has_geometry": True, "geometry": geom
        })
    else:
        no_geom += 1
        results.append({
            "polity_code": pcode, "polity_name": pname,
            "source_used": "UNMATCHED", "match_name": "",
            "has_geometry": False
        })

# ── Summary ─────────────────────────────────────────────────────────

non_region = [r for r in results if "region" not in r["source_used"]]
matched_non_region = [r for r in non_region if r["has_geometry"]]
unmatched = [r for r in non_region if not r["has_geometry"]]

print(f"\nTotal polities: {len(polities)}")
print(f"  Regions (no geometry): {len(results) - len(non_region)}")
print(f"  Non-region with geometry: {len(matched_non_region)}")
print(f"  Non-region WITHOUT geometry: {len(unmatched)}")
print(f"  Match rate (non-region): {len(matched_non_region)/len(non_region)*100:.1f}%")

# Show unmatched
if unmatched:
    print(f"\nUnmatched polities ({len(unmatched)}):")
    for r in sorted(unmatched, key=lambda x: x["polity_name"]):
        p = polities[polities["polity_code"] == r["polity_code"]].iloc[0]
        print(f"  {r['polity_code']:25s} {r['polity_name']:45s} type={p['polity_type']:12s} src={p['polygon_source']}")

# ── Build GeoPackage ────────────────────────────────────────────────

print("\nBuilding GeoPackage...")
geo_rows = [r for r in results if r["has_geometry"]]
if geo_rows:
    gdf = gpd.GeoDataFrame(
        [{k: v for k, v in r.items() if k != "geometry"} for r in geo_rows],
        geometry=[r["geometry"] for r in geo_rows],
        crs="EPSG:4326"
    )
    # Merge with polity metadata
    gdf = gdf.merge(
        polities[["polity_code", "start_year", "end_year", "polity_type",
                  "continent", "iso3_code"]],
        on="polity_code", how="left"
    )
    gdf.to_file(f"{BASE}/data/geodata/polities_polygons.gpkg",
                layer="polities", driver="GPKG")
    print(f"  Written {len(gdf)} polygons to polities_polygons.gpkg")

# ── Write matching report ───────────────────────────────────────────

os.makedirs(f"{BASE}/data/analysis", exist_ok=True)
report = pd.DataFrame([{k: v for k, v in r.items() if k not in ("geometry",)}
                        for r in results])
report.to_csv(f"{BASE}/data/analysis/polygon_matching_report.csv", index=False)
print(f"  Written matching report ({len(report)} rows)")

# Source distribution
print("\nPolygon sources used:")
for src, count in report["source_used"].value_counts().items():
    print(f"  {src}: {count}")
