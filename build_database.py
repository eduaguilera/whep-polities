#!/usr/bin/env python3
"""
Build the final WHEP polities database from all source files.

Reads:
  - data/whep-source/polity_codes.csv (810 entries)
  - data/whep-source/polities_database_verified.csv (602 entries with verification)
  - data/external/cow_state_system.csv (209 COW states)
  - data/external/decolonization_events.csv (96 events)
  - data/external/empire_dissolutions.csv (17 empires)
  - data/external/disputed_states.csv (10 disputed)
  - data/external/microstates.csv (10 microstates)

Writes:
  - data/final/polities_database.csv
"""

import csv
import os
import re
from collections import defaultdict

BASE = "/home/usuario/whep-polities"

def read_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def parse_code(code):
    """Parse XXX-yyyy-YYYY into (prefix, start, end)."""
    m = re.match(r'^(.+)-(\d{4})-(\d{4})$', code)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    return code, None, None

# ── Load all source data ──────────────────────────────────────────────

polity_codes = read_csv(f"{BASE}/data/whep-source/polity_codes.csv")
verified = read_csv(f"{BASE}/data/whep-source/polities_database_verified.csv")
cow_states = read_csv(f"{BASE}/data/external/cow_state_system.csv")
decolonization = read_csv(f"{BASE}/data/external/decolonization_events.csv")
empire_diss = read_csv(f"{BASE}/data/external/empire_dissolutions.csv")
disputed = read_csv(f"{BASE}/data/external/disputed_states.csv")
microstates_data = read_csv(f"{BASE}/data/external/microstates.csv")

# ── Build verification lookup ─────────────────────────────────────────

verified_lookup = {}
for v in verified:
    verified_lookup[v["polity_code"]] = {
        "status": v["verification_status"],
        "notes": v.get("notes", "")
    }

# ── Build COW lookup by ISO3 ─────────────────────────────────────────

cow_by_iso3 = {}
for c in cow_states:
    iso3 = c.get("iso3", "")
    if iso3 and iso3 != "NA":
        cow_by_iso3[iso3] = c["cow_code"]

# ── Build decolonization lookup by ISO3 ───────────────────────────────

decolonization_by_iso3 = {}
for d in decolonization:
    iso3 = d.get("iso3", "")
    if iso3:
        decolonization_by_iso3[iso3] = d

# ── Classification functions ──────────────────────────────────────────

REGION_PREFIXES = {"X", "F"}
REGION_CODES = set()

# Specific region identifiers (codes starting with F or X, or containing specific patterns)
REGION_KEYWORDS = [
    "Africa", "Americas", "Asia", "Europe", "Oceania", "World",
    "Caribbean", "Central America", "Central Asia", "Eastern Africa",
    "Eastern Asia", "Eastern Europe", "Middle Africa", "Northern Africa",
    "Northern America", "Northern Europe", "Polynesia", "Melanesia",
    "Micronesia (Oceania region)", "South America", "South-Central Asia",
    "South-eastern Asia", "Southern Africa", "Southern Asia", "Southern Europe",
    "Western Africa", "Western Asia", "Western Europe",
    "Developed regions", "Developing regions", "Annex I countries",
    "Non-Annex I countries", "High-income economies", "Low-income economies",
    "Lower-middle-income economies", "Upper-middle-income economies",
    "Land Locked Developing Countries", "Least Developed Countries",
    "Low Income Food Deficit Countries", "Net Food Importing Developing Countries",
    "Small Island Developing States", "OECD", "European Union",
    "Australia and New Zealand", "Latin America", "Latin America and the Caribbean",
    "North and Central America", "Sub-Saharan Africa", "Antarctic Region",
    "Caucasus and Central Asia", "International Centres", "Regional Centres",
    "Annex I", "Non-Annex I",
    "FAO Fishing", "Pacific Islands Trust",
    "Belgium-Luxembourg",
    "Eastern Asia and South-eastern Asia",
    "Western Asia and Northern Africa",
    "Northern America and Europe",
    "Europe, Northern America, Australia and New Zealand",
    "Eastern Asia (excluding Japan and China)",
    "Western Asia (exc.",
    "Southern Asia (excl. India)",
    "Oceania excl. Australia",
    "Northern Africa (excl. Sudan)",
    "Sub-Saharan Africa (incl. Sudan)",
    "Eastern Asia and South-eastern Asia",
]

COLONIAL_KEYWORDS = [
    "British East Africa", "British Malaya", "British New Guinea",
    "British Cameroon", "British Togoland", "British Protectorate",
    "British Bechuanaland", "British Indian Ocean", "British settlement",
    "British Columbia", "British Virgin",
    "French Equatorial Africa", "French West Africa", "French India",
    "French Indochina", "French Guiana", "French Somaliland", "French Somalia",
    "French Settlements", "French Southern", "French Polynesia",
    "Belgian Congo",
    "Dutch East Indies", "Dutch Guayana", "Dutch West Indies", "Dutch new Guinea",
    "German East Africa", "German West Africa", "German Togoland",
    "German Solomon", "German colonies",
    "Italian Libia", "Italian Somaliland",
    "Spanish Guinea", "Spanish Morocco", "Spanish North Africa", "Spanish West Africa",
    "Portuguese India",
    "Basutoland", "Bechuanaland Protectorate",
    "Gold Coast", "Nyasaland",
    "Anglo-Egyptian", "Sudan (Anglo",
    "Federation of Rhodesia",
    "Federated Malay", "Unfederated Malay",
    "Straits Settlement",
    "Cameroon (Kamerun)",
    "Oil Rivers Protectorate",
    "Cape Colony", "Natal (", "Transvaal",
    "Rwanda and Burundi",
    "Aden", "Aden (",
    "Kwang-Chou", "Kwantung", "Kiautchou",
    "Sabah (British",
    "Sarawak",
    "Gilbert and Ellice",
    "New Hebrides",
    "Leeward Islands",
    "Inini",
    # Caroline Island, Mariana Island -> AGGREGATE_OVERRIDES; Marshall Islands -> SOVEREIGN_OVERRIDES
    "Dodecanese",
]

MANDATE_KEYWORDS = [
    "Palestine (1920-1948)", "Palestine/Jordan",
    "Cameroon (1919-1961)", "British Cameroon (1919-1961)",
    "New Guinea (1920-1949)",
    "Danzig",
    "Tanganyika", "Tanzania (",
    "Rwanda and Burundi (1920-1962)",
    "Pacific Islands Trust Territory",
]

PUPPET_KEYWORDS = [
    "Manchukuo",
]

DISPUTED_KEYWORDS = [
    "Kosovo", "Western Sahara", "Palestine",
    "Taiwan",
]

AGGREGATE_KEYWORDS = [
    "Germany/Zollverein", "China, mainland", "Ethiopia (old)",
    "Korea (old)", "Sudan (old)", "Yugoslavia (old)",
    "Netherlands (old)", "Luxembourg (old)",
    "Ethiopia PDR", "Belgium-Luxembourg",
]

HISTORICAL_KEYWORDS = [
    "Ottoman Empire", "Austria-Hungary",
    "Two Sicilies", "Papal States", "Tuscany", "Sardinia",
    "Duchy Modena", "Duchy Parma", "Piedmont", "Lucca", "Massa",
    "Kingdom of Naples",
    "Bavaria", "Saxony", "Hanover", "Wurttemberg", "Baden", "Hesse",
    "Mecklenburg", "Thuringia", "Schleswig-Holstein", "Bremen", "Oldenburg",
    "Nassau", "Frankfurt (Free", "Cracow (Free",
    "Anhalt", "Lippe", "Reuss", "Waldeck", "Schaumburg",
    "Saxe-", "Hohenzollern", "Hohengeroldseck", "Wolfenbuttel",
    "Badakhshan", "Bukhara", "Khiva", "Kokand",
    "Circassia", "Chechnya", "Herat",
    "Ionian islands",
    "Crete",
    "Orange Free State",
    "Bonin island",
    "Yunnan",
    "Gambier Island", "Marquesas Island", "Society Islands",
    "St Martin and St Barthelemy",
]

DEPENDENCY_KEYWORDS = [
    "Hong Kong", "Macao", "Bermuda", "Cayman Islands",
    "Gibraltar", "Greenland", "Faroe Islands",
    "American Samoa", "Guam", "Puerto Rico",
    "United States Virgin Islands", "British Virgin Islands",
    "Montserrat", "Anguilla", "Turks and Caicos",
    "Cook Islands", "Niue", "Tokelau",
    "Pitcairn", "Norfolk Island",
    "Christmas Island", "Cocos",
    "Heard Island", "Bouvet Island",
    "Svalbard", "Isle of Man", "Channel Islands",
    "Guernsey", "Jersey", "Sark",
    "Curacao", "Sint Maarten", "Bonaire",
    "Saint Barthelemy", "Saint Martin (French",
    "Aland Islands",
    "Aruba", "Netherlands Antilles",
    "New Caledonia", "Wallis and Futuna",
    "Guadeloupe", "Martinique", "Reunion",
    "French Southern", "French Guiana", "French Polynesia",
    "British Indian Ocean",
    "Saint Pierre and Miquelon",
    "Falkland Islands",
    "South Georgia",
    "Saint Helena",
    "Mayotte",
    "Dronning Maud",
    "Wake Island", "Midway Islands", "Johnston Island",
    "United States Minor Outlying",
    "US settlement Oceania", "United States misc",
    "Northern Mariana",
    "East Berlin", "West Berlin",
    "Gaza Strip", "West Bank",
    "Neutral Zone",
    "Ryukyu Islands",
    "Canary Islands",
    "Ceuta Y Melilla",
    "St. Helena",
    "Antarctica",
]

OCCUPATION_KEYWORDS = [
    "Southern Sakhalin",
    "East Germany", "West Germany",
    "North Vietnam", "South Vietnam",
    "North Korea", "South Korea",
    "North Yemen", "South Yemen",
]

def classify_polity_type(name, code):
    """Classify a polity into its type."""
    prefix, start, end = parse_code(code)

    # ── Hard-coded overrides for known misclassifications ──
    SOVEREIGN_OVERRIDES = {
        "France", "France (to 1919)",
        "South Africa", "South Korea", "North Korea",
        "North Yemen", "South Yemen",
        "East Germany", "West Germany",
        "Marshall Islands",
    }
    # FT trade aggregates that span colonial-to-modern periods or past sovereignty loss
    AGGREGATE_OVERRIDES = {
        "Caroline Island", "Mariana Island",
        "New Guinea",           # FT aggregate; now Papua New Guinea
        "Newfoundland",         # FT aggregate; joined Canada 1949
        "Danish Virgin Islands",# FT aggregate; sold to US 1917
        "Sikkim",               # FT aggregate; merged into India 1975
        "Fujairah",             # FT aggregate; UAE emirate since 1971
        "Ras al Khaimah",       # FT aggregate; UAE emirate since 1972
        "Sharjah",              # FT aggregate; UAE emirate since 1971
        "Umm al Qawain",       # FT aggregate; UAE emirate since 1971
        "France, Metropolitan", # FT aggregate; metropolitan France trade reporting
        "Syria and Lebanon",    # FT aggregate; Syria+Lebanon trade reporting
        "China",                # FT aggregate; PRC FAOSTAT entity (F351)
    }
    # Dependency overrides
    DEPENDENCY_OVERRIDES = {
        "Réunion",              # French overseas department
        "Åland Islands",        # Autonomous region of Finland
    }
    # strip temporal qualifiers for matching
    base_name = re.sub(r'\s*\(.*?\)\s*$', '', name).strip()

    if name in SOVEREIGN_OVERRIDES or base_name in SOVEREIGN_OVERRIDES:
        if end and end < 2020 and name not in ("France, Metropolitan",):
            return "historical"
        return "sovereign"

    # Only exact name match for aggregate overrides (not base_name),
    # so period-specific entries like "New Guinea (to 1920)" aren't caught
    if name in AGGREGATE_OVERRIDES:
        return "aggregate"

    if name in DEPENDENCY_OVERRIDES or base_name in DEPENDENCY_OVERRIDES:
        return "dependency"

    # ── Names ending with "(old)" are FT trade aggregates ──
    if name.endswith("(old)") or name.endswith("(old) "):
        return "aggregate"

    # ── Check aggregates EARLY (before region check to avoid false matches) ──
    for kw in AGGREGATE_KEYWORDS:
        if kw.lower() in name.lower():
            return "aggregate"

    # ── Check mandates EARLY ──
    for kw in MANDATE_KEYWORDS:
        if kw.lower() in name.lower():
            return "mandate"

    # ── Check regions: Only X-prefix or F-prefix with 4+ digit numeric part ──
    # Real FAOSTAT regions have codes like F5300, F5401, F5848, F9010, F5801, etc.
    # Non-region F codes: F15 (Belgium-Lux), F51 (Czechoslovakia), F62 (Ethiopia PDR),
    # F77/F78 (Germany), F164 (Pacific Trust), F206 (Sudan old), F228 (USSR),
    # F246/F247 (Yemen), F248 (Yugoslavia), F285 (Sark), F336, F348, F351, F420, F429
    REGION_F_PREFIXES = set()
    NON_REGION_F_PREFIXES = {
        "FRA", "FRO", "FRE", "FRI", "FID", "FEA", "FWA", "FSO", "FSM",
        "FUJ", "FED", "FLK", "FJI", "FIN",
        "F15", "F51", "F62", "F77", "F78", "F164",
        "F206", "F228", "F246", "F247", "F248", "F285", "F336", "F348",
        "F351", "F420", "F429",
    }
    if prefix and prefix[0] == "X":
        return "region"
    if prefix and prefix[0] == "F" and len(prefix) > 2:
        if prefix not in NON_REGION_F_PREFIXES:
            # Check if it looks like a region code (F followed by 4+ digits)
            suffix = prefix[1:]
            if suffix.isdigit() and len(suffix) >= 4:
                return "region"
            # Otherwise don't auto-classify as region
    # Exact match against region keywords (not substring)
    for kw in REGION_KEYWORDS:
        # Use exact match or exact match ignoring case
        if kw.lower() == name.lower() or kw.lower() == base_name.lower():
            return "region"
        # Allow substring match ONLY for very specific multi-word region terms
        if len(kw) > 15 and kw.lower() in name.lower():
            return "region"
    # Income/development groups
    if any(x in name for x in ["economies", "Developing regions", "Developed regions",
                                "OECD", "European Union (", "Annex I countries",
                                "Non-Annex I countries", "Food Deficit",
                                "Food Importing", "Land Locked Developing"]):
        return "region"
    # FAO fishing areas
    if "FAO Fishing" in name or "Fishing Area" in name:
        return "region"

    # Check aggregates
    for kw in AGGREGATE_KEYWORDS:
        if kw.lower() in name.lower():
            return "aggregate"

    # Check puppet states
    for kw in PUPPET_KEYWORDS:
        if kw.lower() in name.lower():
            return "puppet"

    # Check mandates
    for kw in MANDATE_KEYWORDS:
        if kw.lower() in name.lower():
            return "mandate"

    # Check disputed
    for kw in DISPUTED_KEYWORDS:
        if kw.lower() == name.lower() or (kw.lower() in name.lower() and end and end == 2025):
            if name in ["Kosovo", "Taiwan", "Western Sahara", "Palestine"]:
                return "disputed"

    # Check dependencies (current)
    for kw in DEPENDENCY_KEYWORDS:
        if kw.lower() in name.lower():
            return "dependency"

    # Check colonial — if end_year=2025, the colony has dissolved and this is an FT
    # trade aggregate (no colonial entities exist in 2025)
    for kw in COLONIAL_KEYWORDS:
        if kw.lower() in name.lower():
            if end and end == 2025:
                return "aggregate"
            return "colonial"

    # Check historical (ended before present)
    for kw in HISTORICAL_KEYWORDS:
        if kw.lower() in name.lower():
            return "historical"

    # Historical: ended before 2020 and is a state
    if end and end < 2020:
        return "historical"

    # Default: sovereign
    return "sovereign"


CONTINENT_MAP = {
    # Africa
    "DZA": "Africa", "AGO": "Africa", "BEN": "Africa", "BWA": "Africa",
    "BFA": "Africa", "BDI": "Africa", "CPV": "Africa", "CMR": "Africa",
    "CAF": "Africa", "TCD": "Africa", "COM": "Africa", "COG": "Africa",
    "COD": "Africa", "CIV": "Africa", "DJI": "Africa", "EGY": "Africa",
    "GNQ": "Africa", "ERI": "Africa", "SWZ": "Africa", "ETH": "Africa",
    "GAB": "Africa", "GMB": "Africa", "GHA": "Africa", "GIN": "Africa",
    "GNB": "Africa", "KEN": "Africa", "LSO": "Africa", "LBR": "Africa",
    "LBY": "Africa", "MDG": "Africa", "MWI": "Africa", "MLI": "Africa",
    "MRT": "Africa", "MUS": "Africa", "MAR": "Africa", "MOZ": "Africa",
    "NAM": "Africa", "NER": "Africa", "NGA": "Africa", "RWA": "Africa",
    "STP": "Africa", "SEN": "Africa", "SYC": "Africa", "SLE": "Africa",
    "SOM": "Africa", "ZAF": "Africa", "SSD": "Africa", "SDN": "Africa",
    "TZA": "Africa", "TGO": "Africa", "TUN": "Africa", "UGA": "Africa",
    "ZMB": "Africa", "ZWE": "Africa", "ESH": "Africa", "MYT": "Africa",
    "REU": "Africa", "SHN": "Africa",
    # Asia
    "AFG": "Asia", "ARM": "Asia", "AZE": "Asia", "BHR": "Asia",
    "BGD": "Asia", "BTN": "Asia", "BRN": "Asia", "KHM": "Asia",
    "CHN": "Asia", "CYP": "Asia", "GEO": "Asia", "IND": "Asia",
    "IDN": "Asia", "IRN": "Asia", "IRQ": "Asia", "ISR": "Asia",
    "JPN": "Asia", "JOR": "Asia", "KAZ": "Asia", "KWT": "Asia",
    "KGZ": "Asia", "LAO": "Asia", "LBN": "Asia", "MYS": "Asia",
    "MDV": "Asia", "MNG": "Asia", "MMR": "Asia", "NPL": "Asia",
    "OMN": "Asia", "PAK": "Asia", "PSE": "Asia", "PHL": "Asia",
    "QAT": "Asia", "SAU": "Asia", "SGP": "Asia", "LKA": "Asia",
    "SYR": "Asia", "TWN": "Asia", "TJK": "Asia", "THA": "Asia",
    "TLS": "Asia", "TKM": "Asia", "ARE": "Asia", "UZB": "Asia",
    "VNM": "Asia", "YEM": "Asia", "PRK": "Asia", "KOR": "Asia",
    "HKG": "Asia", "MAC": "Asia", "IOT": "Asia",
    # Europe
    "ALB": "Europe", "AND": "Europe", "AUT": "Europe", "BLR": "Europe",
    "BEL": "Europe", "BIH": "Europe", "BGR": "Europe", "HRV": "Europe",
    "CZE": "Europe", "DNK": "Europe", "EST": "Europe", "FIN": "Europe",
    "FRA": "Europe", "DEU": "Europe", "GRC": "Europe", "HUN": "Europe",
    "ISL": "Europe", "IRL": "Europe", "ITA": "Europe", "KOS": "Europe",
    "LVA": "Europe", "LIE": "Europe", "LTU": "Europe", "LUX": "Europe",
    "MLT": "Europe", "MDA": "Europe", "MCO": "Europe", "MNE": "Europe",
    "NLD": "Europe", "MKD": "Europe", "NOR": "Europe", "POL": "Europe",
    "PRT": "Europe", "ROU": "Europe", "RUS": "Europe", "SMR": "Europe",
    "SRB": "Europe", "SVK": "Europe", "SVN": "Europe", "ESP": "Europe",
    "SWE": "Europe", "CHE": "Europe", "TUR": "Europe", "UKR": "Europe",
    "GBR": "Europe", "VAT": "Europe", "GIB": "Europe", "GGY": "Europe",
    "JEY": "Europe", "IMN": "Europe", "FRO": "Europe", "SJM": "Europe",
    "GRL": "Europe", "ALA": "Europe",
    # North America
    "USA": "North America", "CAN": "North America", "MEX": "North America",
    "GTM": "North America", "BLZ": "North America", "HND": "North America",
    "SLV": "North America", "NIC": "North America", "CRI": "North America",
    "PAN": "North America", "CUB": "North America", "HTI": "North America",
    "DOM": "North America", "JAM": "North America", "TTO": "North America",
    "BRB": "North America", "GRD": "North America", "DMA": "North America",
    "LCA": "North America", "VCT": "North America", "KNA": "North America",
    "ATG": "North America", "BHS": "North America", "BMU": "North America",
    "CYM": "North America", "VGB": "North America", "VIR": "North America",
    "PRI": "North America", "AIA": "North America", "MSR": "North America",
    "TCA": "North America", "ABW": "North America", "CUW": "North America",
    "SXM": "North America", "BES": "North America", "BLM": "North America",
    "MAF": "North America", "SPM": "North America", "GLP": "North America",
    "MTQ": "North America",
    # South America
    "ARG": "South America", "BOL": "South America", "BRA": "South America",
    "CHL": "South America", "COL": "South America", "ECU": "South America",
    "GUY": "South America", "PRY": "South America", "PER": "South America",
    "SUR": "South America", "URY": "South America", "VEN": "South America",
    "GUF": "South America", "FLK": "South America", "SGS": "South America",
    # Oceania
    "AUS": "Oceania", "NZL": "Oceania", "FJI": "Oceania", "PNG": "Oceania",
    "SLB": "Oceania", "VUT": "Oceania", "WSM": "Oceania", "TON": "Oceania",
    "KIR": "Oceania", "MHL": "Oceania", "FSM": "Oceania", "PLW": "Oceania",
    "NRU": "Oceania", "TUV": "Oceania", "COK": "Oceania", "NIU": "Oceania",
    "TKL": "Oceania", "PYF": "Oceania", "NCL": "Oceania", "WLF": "Oceania",
    "ASM": "Oceania", "GUM": "Oceania", "MNP": "Oceania", "PCN": "Oceania",
    "NFK": "Oceania", "CXR": "Oceania", "CCK": "Oceania", "HMD": "Oceania",
    # Antarctica
    "ATA": "Antarctica", "BVT": "Antarctica",
}

# Additional prefix-based continent assignments for historical/special entities
SPECIAL_CONTINENT = {
    "Ottoman Empire": "Asia",
    "Austria-Hungary": "Europe",
    "Manchukuo": "Asia",
    "Germany/Zollverein": "Europe",
    "Ionian islands": "Europe",
    "Crete": "Europe",
    "Two Sicilies": "Europe",
    "Papal States": "Europe",
    "Tuscany": "Europe",
    "Sardinia": "Europe",
    "Duchy Modena": "Europe",
    "Duchy Parma": "Europe",
    "Piedmont": "Europe",
    "Lucca": "Europe",
    "Massa": "Europe",
    "Kingdom of Naples": "Europe",
    "Bavaria": "Europe",
    "Saxony": "Europe",
    "Hanover": "Europe",
    "Wurttemberg": "Europe",
    "Baden": "Europe",
    "Hesse": "Europe",
    "Mecklenburg": "Europe",
    "Thuringia": "Europe",
    "Bremen (city-state)": "Europe",
    "Oldenburg": "Europe",
    "Nassau": "Europe",
    "Badakhshan": "Asia",
    "Bukhara": "Asia",
    "Khiva": "Asia",
    "Kokand": "Asia",
    "Herat": "Asia",
    "Circassia": "Asia",
    "Chechnya": "Asia",
    "Cracow (Free City)": "Europe",
    "Frankfurt (Free City)": "Europe",
    "Yunnan": "Asia",
    "Tibet": "Asia",
    "Sikkim": "Asia",
    "Bonin island": "Oceania",
    "Gold Coast": "Africa",
    "Belgian Congo": "Africa",
    "British East Africa": "Africa",
    "British Cameroon": "Africa",
    "British Bechuanaland": "Africa",
    "British Protectorate (British Somaliland)": "Africa",
    "British Togoland": "Africa",
    "French Equatorial Africa": "Africa",
    "French West Africa": "Africa",
    "French Somalia": "Africa",
    "French Somaliland": "Africa",
    "German East Africa (Tanganyika)": "Africa",
    "German West Africa": "Africa",
    "German Togoland": "Africa",
    "Italian Somaliland": "Africa",
    "Nyasaland Protectorate (Malawi)": "Africa",
    "Basutoland": "Africa",
    "Bechuanaland Protectorate": "Africa",
    "Zanzibar": "Africa",
    "Oil Rivers Protectorate": "Africa",
    "Cape Colony": "Africa",
    "Natal": "Africa",
    "Transvaal": "Africa",
    "Orange Free State": "Africa",
    "French Indochina": "Asia",
    "British Malaya": "Asia",
    "Dutch East Indies (Indonesia)": "Asia",
    "Straits Settlement": "Asia",
    "British New Guinea": "Oceania",
    "New Guinea": "Oceania",
    "New Hebrides": "Oceania",
    "Gilbert and Ellice Island": "Oceania",
    "Solomon Islands": "Oceania",
    "Caroline Island": "Oceania",
    "Mariana Island": "Oceania",
    "Marshall Islands": "Oceania",
    "Gambier Island": "Oceania",
    "Marquesas Island": "Oceania",
    "Society Islands (Tahiti)": "Oceania",
    "French Settlements in Oceania": "Oceania",
    "British settlement Oceania": "Oceania",
    "German colonies Oceania": "Oceania",
    "US settlement Oceania": "Oceania",
    "East Germany": "Europe",
    "West Germany": "Europe",
    "East Berlin": "Europe",
    "West Berlin": "Europe",
    "North Vietnam": "Asia",
    "South Vietnam": "Asia",
    "North Korea": "Asia",
    "South Korea": "Asia",
    "North Yemen": "Asia",
    "South Yemen": "Asia",
    "Alaska": "North America",
    "Hawaii": "Oceania",
    "Newfoundland": "North America",
    "Lower Quebec": "North America",
    "Ontario": "North America",
    "New Brunswick": "North America",
    "Nova Scotia Cape Breton Isl.": "North America",
    "Prince Edward Island": "North America",
    "British Columbia": "North America",
    "Queensland": "Oceania",
    "New South Wales": "Oceania",
    "Victoria": "Oceania",
    "South Australia": "Oceania",
    "Western Australia": "Oceania",
    "Tasmania": "Oceania",
    "Abu Dhabi": "Asia",
    "Ajman": "Asia",
    "Fujairah": "Asia",
    "Sharjah": "Asia",
    "Ras al Khaimah": "Asia",
    "Umm al Qawain": "Asia",
    "Aden": "Asia",
    "Federation of South Arabia": "Asia",
    "East Aden Protectorate": "Asia",
    "Rwanda and Burundi": "Africa",
    "Portuguese India": "Asia",
    "French India": "Asia",
    "Danish India": "Asia",
    "Danish Virgin Islands": "North America",
    "Danzig": "Europe",
    "Spanish Guinea": "Africa",
    "Spanish Morocco": "Africa",
    "Spanish North Africa": "Africa",
    "Spanish West Africa": "Africa",
    "Western Sahara": "Africa",
    "Italian Libia Cyrenaica (Lybia)": "Africa",
    "Kwang-Chou-Wan": "Asia",
    "Kwantung (Port Arthur)": "Asia",
    "Kiautchou": "Asia",
    "Sabah (British Borneo)": "Asia",
    "Sarawak": "Asia",
    "Federated Malay States": "Asia",
    "Unfederated Malay States": "Asia",
    "Leeward Islands": "North America",
    "Inini": "South America",
    "Dutch Guayana": "South America",
    "Canary Islands": "Africa",
    "Ceuta Y Melilla": "Africa",
    "Dodecanese Is.": "Europe",
    "Dronning Maud Land": "Antarctica",
    "Johnston Island": "Oceania",
    "Midway Islands": "Oceania",
    "Wake Island": "Oceania",
    "Palmyra Island": "Oceania",
    "St. Helena": "Africa",
    "Southern Sakhalin Island": "Asia",
    "Neutral Zone": "Asia",
    "Ryukyu Islands": "Asia",
    "Pahang": "Asia",
    "Selangore": "Asia",
    "Perak": "Asia",
    "Lagos": "Africa",
    "Southern Nigeria": "Africa",
    "Northern Nigeria": "Africa",
    "Northeastern Rhodesia": "Africa",
    "Northwestern Rhodesia": "Africa",
    "Federation of Rhodesia and Nyasaland": "Africa",
    "Eritrea": "Africa",
    "Bolivia": "South America",
    "Herzegovina": "Europe",
    "Bosnia": "Europe",
    "Serbia": "Europe",
    "Montenegro": "Europe",
    "Bulgaria": "Europe",
    "Romania": "Europe",
    "Greece": "Europe",
    "Hungary": "Europe",
    "Poland": "Europe",
    "Lithuania": "Europe",
    "Latvia": "Europe",
    "Estonia": "Europe",
    "Finland": "Europe",
    "Czechoslovakia": "Europe",
    "Yugoslavia": "Europe",
    "Serbia and Montenegro": "Europe",
    "Sudan": "Africa",
    "China": "Asia",
    "USSR": "Europe",
    "France, Metropolitan": "Europe",
    "Belgium-Luxembourg": "Europe",
    "Netherlands (old)": "Europe",
    "Luxembourg (old)": "Europe",
    "Korea (old)": "Asia",
    "Ethiopia (old)": "Africa",
    "Ethiopia PDR": "Africa",
    "Sudan (old)": "Africa",
    "Sudan (Anglo-Egyptian)": "Africa",
    "Nigeria (old)": "Africa",
    "Pacific Islands Trust Territory": "Oceania",
    "Dutch West Indies (Netherland Antilles)": "North America",
    "Netherlands Antilles": "North America",
    "Netherlands Antilles (original)": "North America",
    "Saint Kitts-Nevis-Anguilla": "North America",
    "St. Lucia": "North America",
    "St. Vincent": "North America",
    "Grenada": "North America",
    "Brunei (greater)": "Asia",
    "Gaza Strip": "Asia",
    "West Bank": "Asia",
    "Palestine": "Asia",
    "Jammu and Kashmir": "Asia",
    "Kashmir (North Azad)": "Asia",
    "Madagascar": "Africa",
    "Cameroon": "Africa",
    "Gabon": "Africa",
    "Kenya": "Africa",
    "Uganda": "Africa",
    "Tanzania": "Africa",
    "Mali": "Africa",
    "Niger": "Africa",
    "Chad": "Africa",
    "Central African Republic": "Africa",
    "Congo": "Africa",
    "Democratic Republic of the Congo": "Africa",
    "Morocco": "Africa",
    "Mauritania": "Africa",
    "Botswana": "Africa",
    "Zimbabwe": "Africa",
    "Algeria": "Africa",
    "Benin": "Africa",
    "Cote d'Ivoire": "Africa",
    "Burkina Faso": "Africa",
    "Senegal": "Africa",
    "Guinea": "Africa",
    "Guinea-Bissau": "Africa",
    "Angola": "Africa",
    "Ghana": "Africa",
    "Sierra Leone": "Africa",
    "Libya": "Africa",
    "Gambia": "Africa",
    "Mozambique": "Africa",
    "Cabo Verde": "Africa",
    "Sao Tome and Principe": "Africa",
    "Comoros": "Africa",
    "Equatorial Guinea": "Africa",
    "Burundi": "Africa",
    "South Africa": "Africa",
    "Namibia": "Africa",
    "Dutch new Guinea": "Oceania",
    "Samoa": "Oceania",
    "Tonga": "Oceania",
    "Fiji": "Oceania",
    "Papua New Guinea": "Oceania",
    "Nauru": "Oceania",
    "Tuvalu": "Oceania",
    "Kiribati": "Oceania",
    "Vanuatu": "Oceania",
    "Niue": "Oceania",
    "Tokelau": "Oceania",
    "Palau": "Oceania",
    "Micronesia": "Oceania",
    "Malaysia": "Asia",
    "Cambodia": "Asia",
    "Thailand": "Asia",
    "India": "Asia",
    "Indonesia": "Asia",
    "Pakistan": "Asia",
    "Afghanistan": "Asia",
    "Iran": "Asia",
    "Iraq": "Asia",
    "Syria and Lebanon": "Asia",
    "Syrian Arab Republic": "Asia",
    "Lebanon": "Asia",
    "Jordan": "Asia",
    "Israel": "Asia",
    "Egypt": "Africa",
    "Argentina": "South America",
    "Brazil": "South America",
    "Chile": "South America",
    "Colombia": "South America",
    "Ecuador": "South America",
    "Peru": "South America",
    "Venezuela": "South America",
    "Paraguay": "South America",
    "Uruguay": "South America",
    "Suriname": "South America",
    "Guyana": "South America",
    "French Guiana": "South America",
    "Southern zone of Spanish Morocco": "Africa",
    "Anhalt": "Europe",
    "Anhalt-Bernburg": "Europe",
    "Anhalt-Dessau": "Europe",
    "Lippe-Detmold": "Europe",
    "Reuss": "Europe",
    "Saxe-Altenburg": "Europe",
    "Saxe-Coburg-Gotha": "Europe",
    "Saxe-Coburg-Saalfeld": "Europe",
    "Saxe-Gotha-Altenberg": "Europe",
    "Saxe-Hildburgchausen": "Europe",
    "Saxe-Meiningen": "Europe",
    "Saxe-Weimar": "Europe",
    "Schaumburg-Lippe": "Europe",
    "Schleswig-Holstein": "Europe",
    "Waldeck": "Europe",
    "Wolfenbuttel": "Europe",
    "Hohenzollern-Hechingen": "Europe",
    "Hohenzollern-Sigmaringen": "Europe",
    "Hohengeroldseck": "Europe",
    "Vancouver's Island": "North America",
    "St Martin and St Barthelemy": "North America",
    "Korea (old)": "Asia",
    "Korea (to 1910)": "Asia",
    "Van Diemen's Land (Tasmania)": "Oceania",
    "Papua": "Oceania",
    "Hesse-Homburg": "Europe",
    "Wolfenbuttel": "Europe",
    "Society Islands (Tahiti)": "Oceania",
    "Vietnam": "Asia",
    "Nigeria": "Africa",
    "Kashmir (North Azad)": "Asia",
    "Channel Islands": "Europe",
    "French Southern Territories": "Antarctica",
    "United States Minor Outlying Islands": "Oceania",
    "United States misc. Pacific Islands": "Oceania",
    "Palestine/Jordan": "Asia",
    "German Solomon Islands": "Oceania",
    "Nova Scotia Cape Breton Isl.": "North America",
    "St. Lucia": "North America",
    "Sabah (British Borneo)": "Asia",
    "Württemberg": "Europe",
    "Côte d'Ivoire": "Africa",
    "British Protectorate (British Somaliland)": "Africa",
}


def normalize_name(name):
    """Strip accents and normalize for matching."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', name)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def get_continent(name, code):
    """Determine continent for a polity."""
    prefix, start, end = parse_code(code)

    # Check special name-based assignments first
    # Try exact name match
    if name in SPECIAL_CONTINENT:
        return SPECIAL_CONTINENT[name]
    # Try name without temporal qualifier
    base_name = re.sub(r'\s*\(.*?\)\s*$', '', name).strip()
    if base_name in SPECIAL_CONTINENT:
        return SPECIAL_CONTINENT[base_name]
    # Try normalized (accent-stripped) match
    norm_name = normalize_name(name)
    norm_base = normalize_name(base_name)
    for key, val in SPECIAL_CONTINENT.items():
        if normalize_name(key) == norm_name or normalize_name(key) == norm_base:
            return val
    # Try partial match on base name (strip extra whitespace too)
    clean_base = ' '.join(base_name.split())
    for key, val in SPECIAL_CONTINENT.items():
        clean_key = ' '.join(key.split())
        if clean_key == clean_base or normalize_name(clean_key) == normalize_name(clean_base):
            return val

    # Prefix-based special cases
    prefix_continent = {
        "TAS": "Oceania", "SOC": "Oceania", "KAS": "Asia",
        "BRI": "Africa", "SAB": "Asia", "UNI": "Oceania",
        "OKO": "Asia", "NOV": "North America", "ST.": "North America",
        "STM": "North America", "WOL": "Europe", "COT": "Africa",
        "VIE": "Asia", "NIG": "Africa", "GEB": "Europe",
        "GWB": "Europe", "NVI": "Asia", "SVI": "Asia",
        "BOK": "Asia", "SIE": "Africa", "LAG": "Africa",
        "OIL": "Africa", "ORA": "Africa", "SOU": "Oceania",
        "QUE": "Oceania", "VIC": "Oceania", "WES": "Oceania",
        "NBW": "North America", "ONT": "North America",
        "LOW": "North America", "BCO": "North America",
        "NFL": "North America", "HAW": "Oceania",
        "ALA": "North America",
    }
    if prefix and prefix in prefix_continent:
        return prefix_continent[prefix]

    # F285 = Sark (Channel Islands, Europe)
    if prefix == "F285":
        return "Europe"

    # Check ISO3-based continent
    if prefix and prefix in CONTINENT_MAP:
        return CONTINENT_MAP[prefix]

    # Check for region/aggregate -> Global
    ptype = classify_polity_type(name, code)
    if ptype == "region":
        return "Global"

    return "Unknown"


def get_polygon_source(name, code, ptype):
    """Determine the primary polygon source for a polity."""
    prefix, start, end = parse_code(code)

    if ptype == "region":
        return "none (statistical aggregate)"

    # CShapes-Europe for pre-1886 European entities
    cshapes_europe = [
        "Two Sicilies", "Papal States", "Tuscany", "Sardinia",
        "Duchy Modena", "Duchy Parma", "Piedmont", "Lucca", "Massa",
        "Kingdom of Naples", "Bavaria", "Saxony", "Hanover",
        "Frankfurt (Free City)", "Cracow (Free City)",
        "Anhalt", "Nassau", "Waldeck", "Reuss",
    ]
    for kw in cshapes_europe:
        if kw.lower() in name.lower():
            return "CShapes-Europe"

    # Check if entity is a colonial-era entity (needs dependencies=TRUE for CShapes)
    is_colonial_entity = ptype == "colonial" or any(
        kw.lower() in name.lower() for kw in COLONIAL_KEYWORDS)

    # CShapes 2.0 for most sovereign + colonial entities 1886-2019
    if ptype in ("sovereign", "historical", "colonial", "mandate",
                 "occupation", "puppet", "disputed", "aggregate"):
        # If entity existed within CShapes range
        if start and end:
            if (start <= 2019 and end >= 1886) or end == 2025:
                # Colonial-era entities need dependencies=TRUE
                if is_colonial_entity:
                    return "CShapes 2.0 (dependencies=TRUE)"
                # Current sovereign/aggregate entities
                if ptype in ("sovereign", "aggregate") and end == 2025:
                    return "CShapes 2.0"
                if ptype in ("historical", "mandate", "occupation", "puppet"):
                    if start >= 1886:
                        return "CShapes 2.0"
                    elif start < 1886 and end >= 1886:
                        return "CShapes 2.0 + CShapes-Europe"
                return "CShapes 2.0"

    # GADM for dependencies and modern territories
    if ptype == "dependency":
        return "GADM 4.1"

    # GADM subnational for sub-state entities
    subnational = ["Abu Dhabi", "Ajman", "Fujairah", "Sharjah",
                   "Ras al Khaimah", "Umm al Qawain",
                   "Queensland", "Victoria", "South Australia",
                   "Western Australia", "New South Wales", "Tasmania",
                   "Ontario", "Quebec", "Nova Scotia", "New Brunswick",
                   "Prince Edward Island", "British Columbia",
                   "Ryukyu", "Tibet", "Yunnan", "Sikkim"]
    for kw in subnational:
        if kw.lower() in name.lower():
            return "GADM 4.1 (subnational)"

    # Default: check if it might be in CShapes
    if start and end and start <= 2019 and end >= 1886:
        return "CShapes 2.0"

    return "GADM 4.1 or Natural Earth"


def get_data_sources(name, code):
    """List which source databases include this polity."""
    sources = []
    prefix, start, end = parse_code(code)

    # Federico-Tena: 1800-1938 trade entities
    if start and start <= 1938:
        sources.append("FT")

    # FAOSTAT: 1961-present
    if end and end >= 1961:
        sources.append("FAOSTAT")

    # M49: modern standard codes
    if end and end >= 1970:
        sources.append("M49")

    # CShapes: 1886-2019
    if start and end and start <= 2019 and end >= 1886:
        sources.append("CShapes")

    # WHEP fixes
    whep_fix_names = [
        "Manchukuo", "Ionian islands", "Kokand", "Two Sicilies",
        "Orange Free State", "Bavaria", "Saxony", "Hanover",
        "Wurttemberg", "Baden", "Hesse", "Mecklenburg", "Thuringia",
        "Schleswig-Holstein", "Bremen", "Oldenburg", "Ottoman Empire",
        "Cracow", "Frankfurt", "French Somalia", "Afghanistan (to 1888)",
        "Serbia (1816", "Zanzibar", "Korea (to 1910)",
    ]
    for kw in whep_fix_names:
        if kw.lower() in name.lower():
            sources.append("WHEP-fix")
            break

    return "; ".join(sources) if sources else "manual"


def get_predecessor_successor(name, code):
    """Get predecessor and successor codes for major transitions."""
    predecessors = {
        # Italian unification successors
        "ITA-1861-1919": "SAR-1800-1860; TWO-1800-1860; PAP-1800-1870; TUS-1800-1860; DMO-1800-1860; DPA-1800-1860",
        "ITA-1919-2025": "ITA-1861-1919",
        # Austria-Hungary dissolution
        "AUT-1918-2025": "AUH-1908-1918",
        "AUT-1918-1919": "AUH-1908-1918",
        "HUN-1918-1919": "AUH-1908-1918",
        # USSR dissolution
        "RUS-1991-2014": "F228-1940-1991",
        "UKR-1991-2014": "F228-1940-1991",
        "BLR-1991-2025": "F228-1940-1991",
        "KAZ-1991-2025": "F228-1940-1991",
        "GEO-1991-2025": "F228-1940-1991",
        "ARM-1991-2025": "F228-1940-1991",
        "AZE-1991-2025": "F228-1940-1991",
        "MDA-1991-2025": "F228-1940-1991",
        "TKM-1991-2025": "F228-1940-1991",
        "TJK-1991-2025": "F228-1940-1991",
        "KGZ-1991-2025": "F228-1940-1991",
        "UZB-1991-2025": "F228-1940-1991",
        "EST-1991-2025": "F228-1940-1991",
        "LVA-1991-2025": "F228-1940-1991",
        "LTU-1991-2025": "F228-1940-1991",
        # Yugoslavia dissolution
        "SVN-1992-2025": "F248-1991-1992",
        "HRV-1992-2025": "F248-1991-1992",
        "BIH-1992-2025": "F248-1991-1992",
        "MKD-1991-2025": "F248-1920-1991",
        "SCG-1992-2006": "F248-1991-1992",
        # Czechoslovakia dissolution
        "CZE-1993-2025": "F51-1947-1993",
        "SVK-1993-2025": "F51-1947-1993",
        # South Sudan
        "SSD-2011-2025": "SUD-1956-2011",
        "SDN-2011-2025": "SUD-1956-2011",
        # Germany reunification
        "DEU-1990-2025": "F78-1949-1990; F77-1949-1990",
        # Bangladesh
        "BGD-1971-2025": "PAK-1949-1971",
        # Crimea
        "RUS-2014-2025": "RUS-1991-2014",
        "UKR-2014-2025": "UKR-1991-2014",
        # Serbia/Montenegro/Kosovo
        "SER-2006-2008": "SCG-1992-2006",
        "MNE-2006-2025": "SCG-1992-2006",
        "SRB-2008-2025": "SER-2006-2008",
        "KOS-2008-2025": "SER-2006-2008",
    }

    successors = {
        "AUH-1908-1918": "AUT-1918-2025; HUN-1918-1919",
        "F228-1940-1991": "RUS-1991-2014; UKR-1991-2014; BLR-1991-2025 + 12 more",
        "F248-1991-1992": "SVN-1992-2025; HRV-1992-2025; BIH-1992-2025; SCG-1992-2006; MKD-1991-2025",
        "F51-1947-1993": "CZE-1993-2025; SVK-1993-2025",
        "SUD-1956-2011": "SDN-2011-2025; SSD-2011-2025",
        "F78-1949-1990": "DEU-1990-2025",
        "F77-1949-1990": "DEU-1990-2025",
        "SCG-1992-2006": "SER-2006-2008; MNE-2006-2025",
        "SER-2006-2008": "SRB-2008-2025; KOS-2008-2025",
        "OTT-1800-1912": "TUR-1920-2025 + successor states",
        "SAR-1800-1860": "ITA-1861-1919",
        "TWO-1800-1860": "ITA-1861-1919",
        "PAP-1800-1870": "ITA-1861-1919",
        "TUS-1800-1860": "ITA-1861-1919",
        "DMO-1800-1860": "ITA-1861-1919",
        "DPA-1800-1860": "ITA-1861-1919",
        "PAK-1949-1971": "PAK-1971-2025; BGD-1971-2025",
    }

    pred = predecessors.get(code, "")
    succ = successors.get(code, "")
    return pred, succ


def get_cow_code(name, code):
    """Look up COW code for a polity."""
    prefix, start, end = parse_code(code)

    # Direct ISO3 lookup
    if prefix in cow_by_iso3:
        return cow_by_iso3[prefix]

    # Special cases
    cow_special = {
        "AUH": "300",  # Austria-Hungary
        "OTT": "640",  # Ottoman Empire
        "GER": "255",  # Germany
        "TWO": "329",  # Two Sicilies
        "PAP": "327",  # Papal States
        "SAR": "325",  # Sardinia (also Sarawak)
        "TUS": "337",  # Tuscany
        "DMO": "332",  # Modena
        "DPA": "335",  # Parma
        "BAV": "245",  # Bavaria
        "SAX": "269",  # Saxony
        "HAN": "240",  # Hanover
        "WUR": "271",  # Wurttemberg
        "BAD": "267",  # Baden
        "HES": "275",  # Hesse (Grand Ducal/Electoral)
        "MEK": "280",  # Mecklenburg-Schwerin
        "NAP": "329",  # Kingdom of Naples = Two Sicilies
        "PIE": "325",  # Piedmont = Sardinia
        "F228": "365", # USSR
        "F248": "345", # Yugoslavia
        "F51": "315",  # Czechoslovakia
        "F78": "260",  # West Germany
        "F77": "265",  # East Germany
    }
    if prefix in cow_special:
        return cow_special[prefix]

    return ""


# ── Build the database ────────────────────────────────────────────────

rows = []
seen_codes = set()

for entry in polity_codes:
    name = entry["polity_name"]
    code = entry["polity_code"]

    if code in seen_codes:
        continue
    seen_codes.add(code)

    prefix, start, end = parse_code(code)
    duration = (end - start + 1) if start and end else None

    ptype = classify_polity_type(name, code)
    continent = get_continent(name, code)
    polygon_src = get_polygon_source(name, code, ptype)
    data_src = get_data_sources(name, code)
    cow = get_cow_code(name, code)
    pred, succ = get_predecessor_successor(name, code)

    # Get verification info
    vinfo = verified_lookup.get(code, {"status": "UNVERIFIED", "notes": ""})

    # Get ISO3 code (from prefix if it's a standard 3-letter code)
    iso3 = ""
    if prefix and len(prefix) == 3 and prefix.isalpha() and prefix.isupper():
        iso3 = prefix

    rows.append({
        "polity_code": code,
        "polity_name": name,
        "start_year": str(start) if start else "",
        "end_year": str(end) if end else "",
        "duration_years": str(duration) if duration else "",
        "polity_type": ptype,
        "continent": continent,
        "iso3_code": iso3,
        "cow_code": cow,
        "polygon_source": polygon_src,
        "predecessor": pred,
        "successor": succ,
        "data_sources": data_src,
        "verification_status": vinfo["status"],
        "notes": vinfo["notes"],
    })

# ── Sort by continent, type, start_year ───────────────────────────────

type_order = {"sovereign": 0, "historical": 1, "colonial": 2, "dependency": 3,
              "mandate": 4, "occupation": 5, "puppet": 6, "disputed": 7,
              "aggregate": 8, "region": 9}

rows.sort(key=lambda r: (
    r["continent"],
    type_order.get(r["polity_type"], 99),
    int(r["start_year"]) if r["start_year"] else 9999,
    r["polity_name"]
))

# ── Write output ──────────────────────────────────────────────────────

output_path = f"{BASE}/data/final/polities_database.csv"
fieldnames = [
    "polity_code", "polity_name", "start_year", "end_year", "duration_years",
    "polity_type", "continent", "iso3_code", "cow_code", "polygon_source",
    "predecessor", "successor", "data_sources", "verification_status", "notes"
]

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# ── Print summary statistics ──────────────────────────────────────────

print(f"Total polities written: {len(rows)}")
print()

# By type
type_counts = defaultdict(int)
for r in rows:
    type_counts[r["polity_type"]] += 1
print("By type:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")
print()

# By continent
continent_counts = defaultdict(int)
for r in rows:
    continent_counts[r["continent"]] += 1
print("By continent:")
for c, n in sorted(continent_counts.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n}")
print()

# By verification status
status_counts = defaultdict(int)
for r in rows:
    status_counts[r["verification_status"]] += 1
print("By verification status:")
for s, c in sorted(status_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print()

# By polygon source
poly_counts = defaultdict(int)
for r in rows:
    poly_counts[r["polygon_source"]] += 1
print("By polygon source:")
for p, c in sorted(poly_counts.items(), key=lambda x: -x[1]):
    print(f"  {p}: {c}")
print()

# Temporal coverage
starts = [int(r["start_year"]) for r in rows if r["start_year"]]
ends = [int(r["end_year"]) for r in rows if r["end_year"]]
active_2025 = sum(1 for r in rows if r["end_year"] == "2025" and r["polity_type"] != "region")
print(f"Earliest start year: {min(starts)}")
print(f"Latest end year: {max(ends)}")
print(f"Active in 2025 (non-region): {active_2025}")
print(f"Historical (ended before 2025): {sum(1 for r in rows if r['end_year'] and r['end_year'] != '2025' and r['polity_type'] != 'region')}")

print(f"\nOutput written to: {output_path}")
