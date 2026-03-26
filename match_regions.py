#!/usr/bin/env python3
"""
Match cleaned region names from cleaning_geography.xlsx to polities in polities_database.csv.

Categories:
  - matched:    found a corresponding polity
  - subnational: subregion of a polity (e.g. "British India: princely states")
  - aggregate:  total/summary row (e.g. "total africa")
  - unmatched:  no corresponding polity found
"""

import csv
import os
import re
import unicodedata
from collections import defaultdict

import openpyxl


# ---------------------------------------------------------------------------
# 1. Read inputs
# ---------------------------------------------------------------------------

EXCEL_PATH = "cleaning_geography.xlsx"
DB_PATH = "data/final/polities_database.csv"
OUT_DIR = "data/analysis"
OUT_PATH = os.path.join(OUT_DIR, "region_matching.csv")

os.makedirs(OUT_DIR, exist_ok=True)

# Read unique cleaned names from Excel column B
wb = openpyxl.load_workbook(EXCEL_PATH)
ws = wb.active
cleaned_names = set()
for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
    val = row[1]
    if val and str(val).strip():
        cleaned_names.add(str(val).strip())
cleaned_names = sorted(cleaned_names)

# Read polities database
polities = []
with open(DB_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        polities.append(row)


# ---------------------------------------------------------------------------
# 2. Build lookup structures
# ---------------------------------------------------------------------------

def normalize(s):
    """Lowercase, strip accents, collapse whitespace."""
    s = s.lower().strip()
    # Replace special unicode hyphens with regular hyphens
    s = s.replace("\u2011", "-").replace("\u2010", "-")
    # Strip accents
    nfkd = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in nfkd if not unicodedata.category(c).startswith("M"))
    s = re.sub(r"\s+", " ", s)
    return s


# Map normalized polity name -> list of (polity_code, polity_name)
name_to_polity = defaultdict(list)
# Also map iso3 -> list of (polity_code, polity_name)
iso_to_polity = defaultdict(list)

for p in polities:
    code = p["polity_code"]
    name = p["polity_name"]
    iso3 = p.get("iso3_code", "")
    ptype = p.get("polity_type", "")

    nname = normalize(name)
    name_to_polity[nname].append((code, name, ptype))

    if iso3:
        iso_to_polity[iso3].append((code, name, ptype))

# Flat list of all (normalized_name, code, name, type) for substring search
all_polities_flat = []
for p in polities:
    all_polities_flat.append((
        normalize(p["polity_name"]),
        p["polity_code"],
        p["polity_name"],
        p.get("polity_type", "")
    ))


# ---------------------------------------------------------------------------
# 3. Qualifier / variant stripping
# ---------------------------------------------------------------------------

# Parenthetical qualifiers that represent measurement variants, not distinct geographies
VARIANT_QUALIFIERS_RE = re.compile(
    r"\s*\("
    r"(?:"
    r"by (?:land|sea)"
    r"|trade with .*"
    r"|production area"
    r"|total (?:area|and production area|area and area in production|cultivation)"
    r"|area in production"
    r"|non-production area"
    r"|reexportation"
    r"|european (?:cultivation|plantations?|vineyard)"
    r"|indigenous (?:cultivation|vineyard)"
    r"|native cultivations?"
    r"|muslim vineyard"
    r"|rural communities"
    r"|urban communities"
    r"|associated cultivation"
    r"|intercalary cultivation"
    r"|main (?:and secondary )?cultivation"
    r"|secondary cultivation"
    r"|simple (?:and associated )?cultivation"
    r"|simple cultivation"
    r"|total and production area"
    r"|mixed cultivation"
    r"|in production"
    r"|specialist cultivation"
    r"|regular plantations"
    r"|trellises"
    r"|fresh"
    r"|not wine grapes"
    r"|raisins"
    r"|table grapes"
    r"|vines for wine"
    r"|wine grapes"
    r"|for agriculture"
    r"|for export"
    r"|sea island"
    r"|autumn rearing"
    r"|spring rearing"
    r"|coree seule"
    r"|frijoles rojos"
    r")"
    r"\)\s*$",
    re.IGNORECASE,
)


def strip_variant_qualifier(name):
    """Remove parenthetical measurement qualifiers, returning base name."""
    return VARIANT_QUALIFIERS_RE.sub("", name).strip()


# ---------------------------------------------------------------------------
# 4. Colonial prefix handling
# ---------------------------------------------------------------------------

COLONIAL_PREFIXES = [
    "british", "french", "dutch", "japanese", "portuguese",
    "spanish", "italian", "us", "german", "belgian",
]


def strip_colonial_prefix(name):
    """Remove leading colonial-power prefix, return (prefix, remainder)."""
    lower = name.lower()
    for pref in COLONIAL_PREFIXES:
        if lower.startswith(pref + " "):
            return pref, name[len(pref)+1:]
    return None, name


def norm_key(s):
    """Normalize a string for dictionary lookup: lowercase, normalize hyphens."""
    s = s.lower().strip()
    # Replace non-breaking hyphen (U+2011) and other hyphen variants with ASCII hyphen
    s = s.replace("\u2011", "-").replace("\u2010", "-").replace("\u2012", "-")
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return s


# ---------------------------------------------------------------------------
# 5. Explicit manual mapping (colonial-era -> database code/name)
# ---------------------------------------------------------------------------

# This covers names that cannot be resolved by simple name/substring matching.
# Keys are normalized cleaned names (after variant stripping).
MANUAL_MAP = {
    # --- British colonial ---
    "british india": ("IND-1800-1947", "India (to 1947)"),
    "british burma": ("MMR-1800-2025", "Myanmar"),
    "british ceylon": ("LKA-1800-2025", "Sri Lanka"),
    "british malaya": ("BMA-1922-2025", "British Malaya"),
    "british federated malay states": ("FED-1909-1946", "Federated Malay States (1909-1946)"),
    "british hong kong": ("HKG-1841-2025", "Hong Kong"),
    "british cyprus": ("CYP-1879-2025", "Cyprus"),
    "british malta": ("MLT-1800-2025", "Malta"),
    "british palestine": ("PAL-1920-1948", "Palestine (1920-1948)"),
    "british iraq": ("IRQ-1921-2025", "Iraq"),
    "british transjordan": ("JOR-1920-1923", "Jordan (1920-1923)"),
    "british tanganyika": ("TAN-1922-1964", "Tanzania (1922-1964)"),
    "british kenya": ("KEN-1924-1926", "Kenya (1924-1926)"),
    "british uganda": ("UGA-1910-1926", "Uganda (1910-1926)"),
    "british nigeria": ("NIG-1914-1961", "Nigeria (1914-1961)"),
    "british gold coast": ("GOL-1843-2025", "Gold Coast"),
    "british sierra leone": ("SLE-1800-2025", "Sierra Leone"),
    "british gambia": ("GMB-1800-2025", "Gambia"),
    "british nyasaland": ("NYA-1891-2025", "Nyasaland Protectorate (Malawi)"),
    "british north rhodesia": ("ZMB-1964-2025", "Zambia"),
    "british south rhodesia": ("ZWE-1890-2025", "Zimbabwe"),
    "british somaliland": ("BSO-1884-2025", "British Protectorate (British Somaliland)"),
    "british swaziland": ("SWZ-1894-2025", "Eswatini"),
    "british basutoland": ("BAS-1884-2025", "Basutoland"),
    "british bechuanaland": ("BEC-1885-2025", "Bechuanaland Protectorate"),
    "british zanzibar": ("ZAN-1890-1964", "Zanzibar (1890-1964)"),
    "british mauritius": ("MUS-1800-2025", "Mauritius"),
    "british seychelles": ("SYC-1903-2025", "Seychelles"),
    "british fiji": ("FJI-1874-2025", "Fiji"),
    "british samoa": ("WSM-1900-2025", "Samoa"),
    "british tonga": ("TON-1800-2025", "Tonga"),
    "british solomon": ("SLB-1885-2025", "Solomon Islands"),
    "british nauru": ("NRU-1888-2025", "Nauru"),
    "british gilbert and ellice": ("GIL-1892-2025", "Gilbert and Ellice Island"),
    "british gibraltar": ("GIB-1800-2025", "Gibraltar"),
    "british bermuda": ("BMU-1800-2025", "Bermuda"),
    "british bahamas": ("BHS-1800-2025", "Bahamas"),
    "british jamaica": ("JAM-1800-2025", "Jamaica"),
    "british barbados": ("BRB-1800-2025", "Barbados"),
    "british trinidad and tobago": ("TTO-1800-2025", "Trinidad and Tobago"),
    "british guiana": ("GUY-1800-2025", "Guyana"),
    "british honduras": ("BLZ-1800-2025", "Belize"),
    "british falkland islands": ("FLK-1833-2025", "Falkland Islands"),
    "british antigua": ("ATG-1800-2025", "Antigua and Barbuda"),
    "british dominica": ("DMA-1800-2025", "Dominica"),
    "british grenada": ("GRD-1800-1833", "Grenada"),
    "british montserrat": ("MSR-1800-2025", "Montserrat"),
    "british saint christopher and nevis": ("KNA-1800-2025", "Saint Kitts and Nevis"),
    "british saint helena": ("SHN-1800-2025", "Saint Helena, Ascension and Tristan da Cunha"),
    "british saint lucia": ("LCA-1800-2025", "Saint Lucia"),
    "british saint vincent": ("VCT-1800-2025", "Saint Vincent and the Grenadines"),
    "british virgin islands": ("VGB-1800-2025", "British Virgin Islands"),
    "british leeward islands": ("LEE-1800-2025", "Leeward Islands (Antigua, Dominica, St.Christopher, Montserrat, Nevis, Virgin Island)"),
    "british windward islands": ("VCT-1800-2025", "Saint Vincent and the Grenadines"),
    "british guernsey": ("GGY-2005-2025", "Guernsey"),
    "british jersey": ("JEY-2005-2025", "Jersey"),
    "british newfoundland": ("NFL-1816-2025", "Newfoundland"),
    "british aden": ("ADE-1839-1967", "Aden"),
    "british caymans": ("CYM-1800-2025", "Cayman Islands"),
    "british turks and caicos islands": ("TCA-1800-2025", "Turks and Caicos Islands"),
    "british ascension": ("SHN-1800-2025", "Saint Helena, Ascension and Tristan da Cunha"),
    "british cameroon": ("BCA-1914-2025", "British Cameroon"),
    "british togoland": ("BRI-1922-1955", "British Togoland (1922-1955)"),
    "british north borneo": ("SAB-1888-2025", "Sabah (British Borneo)"),
    "british sarawak": ("SAR-1841-2025", "Sarawak"),
    "british brunei": ("BRN-1888-2025", "Brunei Darussalam"),
    "british south west africa": ("NAM-1884-2025", "Namibia"),
    "british christmas": ("CXR-1800-2025", "Christmas Island"),
    "british andaman and nicobar": ("IND-1800-1947", "India (to 1947)"),
    "british nauru and ocean island": ("NRU-1888-2025", "Nauru"),
    "british ocean island": ("KIR-1800-2025", "Kiribati"),
    "british west indies federation": ("LEE-1800-2025", "Leeward Islands (Antigua, Dominica, St.Christopher, Montserrat, Nevis, Virgin Island)"),

    # --- French colonial ---
    "french equatorial africa": ("FEA-1910-2025", "French Equatorial Africa"),
    "french west africa": ("FWA-1895-2025", "French West Africa"),
    "french indochine": ("FID-1887-2025", "French Indochina"),
    "french algeria": ("DZA-1831-2025", "Algeria"),
    "french tunisia": ("TUN-1881-2025", "Tunisia"),
    "french morocco": ("MOR-1904-1956", "Morocco (1904-1956)"),
    "french madagascar": ("MAD-1912-1946", "Madagascar (1912-1946)"),
    "french cameroon": ("CAM-1919-1961", "Cameroon (1919-1961)"),
    "french somali coast": ("FSO-1884-1977", "French Somalia"),
    "french india": ("FRI-1800-2025", "French India"),
    "french reunion": ("REU-1816-2025", "Reunion"),
    "french guiana": ("GUF-1800-2025", "French Guiana"),
    "french guadeloupe": ("GLP-1800-2025", "Guadeloupe"),
    "french martinique": ("MTQ-1800-2025", "Martinique"),
    "french new caledonia": ("NCL-1853-2025", "New Caledonia"),
    "french oceania": ("PYF-1800-2025", "French Polynesia"),
    "french saint pierre and miquelon": ("SPM-1800-2025", "Saint Pierre and Miquelon"),
    "french syria and lebanon": ("SYR-1918-2025", "Syria and Lebanon"),
    "french syria": ("SYR-1920-1967", "Syrian Arab Republic (1920-1967)"),
    "french lebanon": ("LBN-1944-2025", "Lebanon"),
    "french annam": ("VIE-1893-1954", "Vietnam (1893-1954)"),
    "french cochinchina": ("VIE-1893-1954", "Vietnam (1893-1954)"),
    "french tonkin": ("VIE-1893-1954", "Vietnam (1893-1954)"),
    "french cambodia": ("CAM-1904-1907", "Cambodia (1904-1907)"),
    "french laos": ("LAO-1954-2025", "Laos"),
    "french tangier": ("MOR-1904-1956", "Morocco (1904-1956)"),
    "french mayotte": ("MYT-1843-1914", "Mayotte and Noissi-be"),

    # --- Dutch colonial ---
    "dutch east indies": ("DEI-1800-2025", "Dutch East Indies (Indonesia)"),
    "dutch guiana": ("DGU-1800-2025", "Dutch Guayana"),
    "dutch curacao": ("CUW-2010-2025", "Curacao"),

    # --- Portuguese colonial ---
    "portuguese angola": ("AGO-1816-2025", "Angola"),
    "portuguese mozambique": ("MOZ-1816-2025", "Mozambique"),
    "portuguese guinea": ("GNB-1879-2025", "Guinea-Bissau"),
    "portuguese cape verde": ("CPV-1800-2025", "Cabo Verde"),
    "portuguese sao tome and principe": ("STP-1800-2025", "Sao Tome and Principe"),
    "portuguese india": ("POR-1800-2025", "Portuguese India"),
    "portuguese macau": ("MAC-1800-2025", "Macao"),
    "portuguese timor": ("TLS-1800-2025", "Timor-Leste"),
    "portuguese timor and kambing": ("TLS-1800-2025", "Timor-Leste"),

    # --- Italian colonial ---
    "italian somaliland": ("ITS-1908-2025", "Italian Somaliland"),
    "italian eritrea": ("ERI-1882-2025", "Eritrea"),
    "italian libya": ("ITL-1911-2025", "Italian Libia Cyrenaica (Lybia)"),
    "italian east africa": ("ETH-1907-1952", "Ethiopia (1907-1952)"),
    "italian dodecanese islands": ("DOD-1912-2025", "Dodecanese Is."),

    # --- Japanese colonial ---
    "japanese korea": ("KOR-1800-1945", "Korea (old) (to 1945)"),
    "japanese taiwan": ("TWN-1896-2025", "Taiwan"),
    "japanese manchukuo": ("MAN-1932-1945", "Manchukuo"),
    "japanese kwantung": ("KWA-1898-2025", "Kwantung (Port Arthur)"),
    "japanese south pacific": ("MNP-1991-2025", "Northern Mariana Islands"),

    # --- US territories ---
    "us philippines": ("PHL-1800-2025", "Philippines"),
    "us hawaii": ("HAW-1898-1959", "Hawaii (1898-1959)"),
    "us alaska": ("ALA-1800-1959", "Alaska (to 1959)"),
    "us puerto rico": ("PRI-1800-2025", "Puerto Rico"),
    "us virgin islands": ("VIR-1800-2025", "United States Virgin Islands"),
    "us guam": ("GUM-1800-2025", "Guam"),
    "us samoa": ("ASM-1900-2025", "American Samoa"),
    "us panama canal": ("PAN-1800-1979", "Panama (before Canal Zone)"),

    # --- Spanish colonial ---
    "spanish guinea": ("SPA-1858-2025", "Spanish Guinea"),
    "spanish fernando po": ("SPA-1858-2025", "Spanish Guinea"),
    "spanish guinea and fernando po": ("SPA-1858-2025", "Spanish Guinea"),
    "spanish morocco": ("SPA-1912-1956", "Spanish Morocco (1912-1956)"),

    # --- German colonial ---
    "german south west africa": ("GWA-1884-1914", "German West Africa"),
    "german new guinea": ("GER-1884-2025", "German colonies Oceania"),
    "german togoland": ("GER-1897-1919", "German Togoland (1897-1919)"),
    "german western samoa": ("WSM-1900-2025", "Samoa"),
    "german bohemia and moravia": ("CZE-1947-1992", "Czechoslovakia (1947-1992)"),

    # --- Belgian colonial ---
    "belgian congo": ("BEL-1885-2025", "Belgian Congo"),
    "belgian ruanda-urundi": ("RWB-1919-2025", "Rwanda and Burundi"),

    # --- Composite / special names ---
    "british-french togoland": ("TGO-1960-2025", "Togo"),
    "british-french cameroon": ("CMR-1884-2025", "Cameroon (Kamerun)"),
    "british-egyptian sudan": ("SUD-1882-2025", "Sudan (Anglo-Egyptian)"),
    "british-french new hebrides": ("NHB-1906-2025", "New Hebrides"),
    "french togoland": ("GER-1919-1922", "German Togoland (1919-1922)"),
    "aden and perim": ("ADE-1839-1967", "Aden"),
    "italian and british somaliland": ("SOM-1960-2025", "Somalia"),
    "aegean economic zone": ("GRC-1919-2025", "Greece"),
    "australia administered islands": ("AUS-1901-2025", "Australia"),
    "australian papua": ("PAP-1800-1949", "Papua (to 1949)"),
    "british kenya and uganda": ("BEA-1895-2025", "British East Africa"),
    "british straits settlements": ("STR-1826-1922", "Straits Settlement"),
    "belgium-luxembourg economic union": ("F15-1800-1999", "Belgium-Luxembourg"),
    "union of south africa": ("ZAF-1828-2025", "South Africa"),
    "kingdom of serbs, croats and slovenes": ("F248-1920-1991", "Yugoslavia (1920-1991)"),
    "free city of danzig": ("DAN-1919-1938", "Danzig (1919-1938)"),
    "territory of the saar basin": ("DEU-1920-1938", "Germany (1920-1938)"),
    "south west africa": ("NAM-1884-2025", "Namibia"),
    "austria-hungary": ("AUH-1908-1918", "Austria-Hungary (1908-1918)"),
    "siam": ("THA-1909-2025", "Thailand"),
    "czechoslovakia": ("F51-1918-1938", "Czechoslovakia (1918-1938)"),
    "ussr": ("F228-1921-1940", "USSR (1921-1940)"),
    "uk": ("GBR-1800-1921", "United Kingdom (to 1921)"),
    "usa": ("USA-1800-1959", "United States of America (to 1959)"),
    "usa and canada": ("USA-1800-1959", "United States of America (to 1959)"),
    "russia": ("RUS-1991-2014", "Russia (1991-2014)"),
    "yugoslavia": ("F248-1920-1991", "Yugoslavia (1920-1991)"),

    # Countries with direct matches that use slightly different naming
    "iran": ("IRN-1800-2025", "Iran"),
    "egypt": ("EGY-1899-1925", "Egypt (1899-1925)"),
    "ireland": ("IRL-1921-2025", "Ireland"),
    "china": ("CHN-1800-2025", "China, mainland"),
    "ethiopia": ("ETH-1800-2025", "Ethiopia (old)"),
    "liberia": ("LBR-1847-2025", "Liberia"),
    "nepal": ("NPL-1800-2025", "Nepal"),
    "japan": ("JPN-1800-2025", "Japan"),
    "turkey": ("TUR-1920-2025", "Turkiye"),
}

# ---------------------------------------------------------------------------
# 6. Subnational entries (sub-region of a parent polity)
# ---------------------------------------------------------------------------

# Pattern: "parent_name: sub-part" or specific known subnational names.
# Also covers Dutch sub-island entries, Straits Settlements sub-entries, etc.

SUBNATIONAL_MAP = {
    # British India sub-divisions
    "british india: crown provinces": ("IND-1800-1947", "India (to 1947)", "Crown provinces sub-division"),
    "british india: crown provinces, excluding burma": ("IND-1800-1947", "India (to 1947)", "Crown provinces excluding Burma"),
    "british india: excluding burma": ("IND-1800-1947", "India (to 1947)", "India excluding Burma"),
    "british india: princely states": ("IND-1800-1947", "India (to 1947)", "Princely states sub-division"),
    "british india: south provinces": ("IND-1800-1947", "India (to 1947)", "South provinces sub-division"),

    # British Nigeria sub-divisions
    "british nigeria: north provinces": ("NIG-1914-1961", "Nigeria (1914-1961)", "North provinces"),
    "british nigeria: south provinces": ("NIG-1914-1961", "Nigeria (1914-1961)", "South provinces"),
    "british nigeria and cameroon: north provinces, adamawa and bornu": ("NIG-1914-1961", "Nigeria (1914-1961)", "North provinces, Adamawa and Bornu (incl. Cameroon)"),
    "british nigeria and cameroon: south provinces": ("NIG-1914-1961", "Nigeria (1914-1961)", "South provinces (incl. Cameroon)"),
    "british mauritius, adamawa and bornu": ("MUS-1800-2025", "Mauritius", "Possibly mislabeled entry, includes Adamawa and Bornu"),

    # British Straits Settlements sub-divisions
    "british straits settlements: labuan": ("STR-1826-1922", "Straits Settlement", "Labuan"),
    "british straits settlements: malacca": ("STR-1826-1922", "Straits Settlement", "Malacca"),
    "british straits settlements: penang": ("STR-1826-1922", "Straits Settlement", "Penang"),
    "british straits settlements: singapore": ("STR-1826-1922", "Straits Settlement", "Singapore"),

    # British Unfederated Malay States
    "british unfederated malay states: johor": ("UNF-1909-1946", "Unfederated Malay States (1909-1946)", "Johor"),
    "british unfederated malay states: kedah": ("UNF-1909-1946", "Unfederated Malay States (1909-1946)", "Kedah"),
    "british unfederated malay states: kelantan": ("UNF-1909-1946", "Unfederated Malay States (1909-1946)", "Kelantan"),
    "british unfederated malay states: perlis": ("UNF-1909-1946", "Unfederated Malay States (1909-1946)", "Perlis"),
    "british unfederated malay states: terengganu": ("UNF-1909-1946", "Unfederated Malay States (1909-1946)", "Terengganu"),

    # Dutch East Indies sub-divisions
    "dutch java and madura": ("DEI-1800-2025", "Dutch East Indies (Indonesia)", "Java and Madura"),
    "dutch java and sumatra": ("DEI-1800-2025", "Dutch East Indies (Indonesia)", "Java and Sumatra"),
    "dutch java, madura and east outer provinces": ("DEI-1800-2025", "Dutch East Indies (Indonesia)", "Java, Madura and East Outer Provinces"),
    "dutch sumatra": ("DEI-1800-2025", "Dutch East Indies (Indonesia)", "Sumatra"),
    "dutch bali and lombok": ("DEI-1800-2025", "Dutch East Indies (Indonesia)", "Bali and Lombok"),
    "dutch east outer provinces": ("DEI-1800-2025", "Dutch East Indies (Indonesia)", "East Outer Provinces"),
    "dutch sint eustatius and sint maarten": ("DUT-1800-2025", "Dutch West Indies (Netherland Antilles)", "Sint Eustatius and Sint Maarten"),

    # French West Africa sub-divisions
    "french senegal": ("FWA-1895-2025", "French West Africa", "Senegal"),
    "french guinea": ("FWA-1895-2025", "French West Africa", "Guinea"),
    "french ivory coast": ("FWA-1895-2025", "French West Africa", "Ivory Coast"),
    "french dahomey": ("FWA-1895-2025", "French West Africa", "Dahomey"),
    "french sudan": ("FWA-1895-2025", "French West Africa", "Sudan (French)"),
    "french upper volta": ("FWA-1895-2025", "French West Africa", "Upper Volta"),
    "french niger": ("FWA-1895-2025", "French West Africa", "Niger"),
    "french mauritania": ("FWA-1895-2025", "French West Africa", "Mauritania"),
    "french dakar": ("FWA-1895-2025", "French West Africa", "Dakar"),
    "french senegal and sudan": ("FWA-1895-2025", "French West Africa", "Senegal and Sudan"),
    "french upper senegal and niger": ("FWA-1895-2025", "French West Africa", "Upper Senegal and Niger"),

    # French Equatorial Africa sub-divisions
    "french gabon": ("FEA-1910-2025", "French Equatorial Africa", "Gabon"),
    "french middle congo": ("FEA-1910-2025", "French Equatorial Africa", "Middle Congo"),
    "french oubangui-chari": ("FEA-1910-2025", "French Equatorial Africa", "Oubangui-Chari"),
    "french chad": ("FEA-1910-2025", "French Equatorial Africa", "Chad"),
    "french gabon and middle congo": ("FEA-1910-2025", "French Equatorial Africa", "Gabon and Middle Congo"),
    "french middle congo and oubangui-chari": ("FEA-1910-2025", "French Equatorial Africa", "Middle Congo and Oubangui-Chari"),
    "french chad and oubangui-chari": ("FEA-1910-2025", "French Equatorial Africa", "Chad and Oubangui-Chari"),
    "french chad, gabon, middle congo and oubangui-chari": ("FEA-1910-2025", "French Equatorial Africa", "Chad, Gabon, Middle Congo and Oubangui-Chari"),
    "french chad, middle congo and oubangui-chari": ("FEA-1910-2025", "French Equatorial Africa", "Chad, Middle Congo and Oubangui-Chari"),

    # French Indochina sub-divisions
    "french annam": ("FID-1887-2025", "French Indochina", "Annam"),
    "french cochinchina": ("FID-1887-2025", "French Indochina", "Cochinchina"),
    "french tonkin": ("FID-1887-2025", "French Indochina", "Tonkin"),
    "french cambodia": ("FID-1887-2025", "French Indochina", "Cambodia"),
    "french laos": ("FID-1887-2025", "French Indochina", "Laos"),

    # French Syria and Lebanon sub-divisions
    "french syria": ("SYR-1918-2025", "Syria and Lebanon", "Syria"),
    "french lebanon": ("SYR-1918-2025", "Syria and Lebanon", "Lebanon"),
    "french syria and lebanon: state of the alawites": ("SYR-1918-2025", "Syria and Lebanon", "State of the Alawites"),

    # French Morocco sub-divisions
    "french east morocco": ("MOR-1904-1956", "Morocco (1904-1956)", "East Morocco"),
    "french west morocco": ("MOR-1904-1956", "Morocco (1904-1956)", "West Morocco"),

    # French Guadeloupe sub-divisions
    "french guadeloupe: marie-galante": ("GLP-1800-2025", "Guadeloupe", "Marie-Galante"),

    # French Oceania sub-divisions
    "french oceania: makatea": ("PYF-1800-2025", "French Polynesia", "Makatea"),

    # French Madagascar sub-division
    "french madagascar: juan de nova": ("MAD-1912-1946", "Madagascar (1912-1946)", "Juan de Nova"),

    # Italian Libya sub-divisions
    "italian libya: cyrenaica": ("ITL-1911-2025", "Italian Libia Cyrenaica (Lybia)", "Cyrenaica"),
    "italian libya: tripolitania": ("ITL-1911-2025", "Italian Libia Cyrenaica (Lybia)", "Tripolitania"),

    # Portuguese Mozambique sub-divisions
    "portuguese mozambique: company": ("MOZ-1816-2025", "Mozambique", "Mozambique Company territory"),
    "portuguese mozambique: niassa": ("MOZ-1816-2025", "Mozambique", "Niassa"),
    "portuguese mozambique: province": ("MOZ-1816-2025", "Mozambique", "Province territory"),

    # Spanish Morocco sub-divisions
    "spanish morocco: ceuta": ("SPA-1912-1956", "Spanish Morocco (1912-1956)", "Ceuta"),
    "spanish morocco: melilla": ("SPA-1912-1956", "Spanish Morocco (1912-1956)", "Melilla"),

    # Japanese sub-divisions
    "japanese south pacific: angaur": ("MNP-1991-2025", "Northern Mariana Islands", "Angaur"),
    "japanese south pacific: palau": ("MNP-1991-2025", "Northern Mariana Islands", "Palau"),
    "japan: karafuto prefecture": ("JPN-1800-2025", "Japan", "Karafuto (South Sakhalin)"),

    # UK sub-divisions
    "uk: england and wales": ("GBR-1800-1921", "United Kingdom (to 1921)", "England and Wales"),
    "uk: great britain": ("GBR-1800-1921", "United Kingdom (to 1921)", "Great Britain"),
    "uk: north ireland": ("GBR-1800-1921", "United Kingdom (to 1921)", "North Ireland"),
    "uk: scotland": ("GBR-1800-1921", "United Kingdom (to 1921)", "Scotland"),

    # Australia sub-divisions
    "australia: queensland": ("AUS-1901-2025", "Australia", "Queensland"),
    "australia: tasmania": ("AUS-1901-2025", "Australia", "Tasmania"),
    "australia: victoria": ("AUS-1901-2025", "Australia", "Victoria"),

    # Argentina sub-division
    "argentina: mendoza": ("ARG-1902-2025", "Argentina", "Mendoza"),

    # Brazil sub-division
    "brazil: sao paulo": ("BRA-1909-2025", "Brazil", "Sao Paulo"),

    # Chile sub-division (reexportation is a variant qualifier)
    # handled below in variant logic

    # China sub-divisions
    "china: excluding manchuria": ("CHN-1800-2025", "China, mainland", "Excluding Manchuria"),
    "china: manchuria": ("CHN-1800-2025", "China, mainland", "Manchuria"),

    # Denmark sub-divisions
    "denmark: faroe islands": ("FRO-1800-2025", "Faroe Islands", "Faroe Islands"),
    "denmark: greenland": ("GRL-1800-2025", "Greenland", "Greenland"),

    # France sub-divisions
    "france: alsace": ("FRA-1919-2025", "France", "Alsace"),

    # New Zealand sub-divisions
    "new zealand: cook": ("COK-1893-2025", "Cook Islands", "Cook Islands"),

    # Portugal sub-divisions
    "portugal: madeira": ("PRT-1800-2025", "Portugal", "Madeira"),

    # Spain sub-divisions
    "spain: canary": ("CAN-1800-2025", "Canary Islands", "Canary Islands"),

    # USA sub-divisions
    "usa: california": ("USA-1800-1959", "United States of America (to 1959)", "California"),
    "usa: louisiana and florida": ("USA-1800-1959", "United States of America (to 1959)", "Louisiana and Florida"),
    "usa: other states different from alaska, california, louisiana and florida": ("USA-1800-1959", "United States of America (to 1959)", "Other states"),

    # USSR sub-divisions
    "ussr in asia": ("F228-1921-1940", "USSR (1921-1940)", "USSR in Asia"),
    "ussr in europe": ("F228-1921-1940", "USSR (1921-1940)", "USSR in Europe"),
    "ussr: khibiny": ("F228-1921-1940", "USSR (1921-1940)", "Khibiny"),
    "ussr: transcaucasian sfsr": ("F228-1921-1940", "USSR (1921-1940)", "Transcaucasian SFSR"),

    # Russia sub-divisions
    "russia in asia": ("RUS-1991-2014", "Russia (1991-2014)", "Russia in Asia"),
    "russia in europe": ("RUS-1991-2014", "Russia (1991-2014)", "Russia in Europe"),

    # Turkey sub-divisions
    "turkey in asia": ("TUR-1920-2025", "Turkiye", "Turkey in Asia"),
    "turkey in europe": ("TUR-1920-2025", "Turkiye", "Turkey in Europe"),

    # Denmark sub-division
    "denmark (rural communities)": ("DNK-1920-2025", "Denmark", "Rural communities"),

    # El Salvador sub-division
    "el salvador: san salvador department": ("SLV-1821-2025", "El Salvador", "San Salvador department"),

    # Union of South Africa sub-divisions
    "union of south africa: cape province": ("ZAF-1828-2025", "South Africa", "Cape Province"),

    # British Kenya sub-variant
    "british kenya (european cultivation)": ("KEN-1924-1926", "Kenya (1924-1926)", "European cultivation variant"),
    "british nyasaland (european cultivation)": ("NYA-1891-2025", "Nyasaland Protectorate (Malawi)", "European cultivation variant"),
    "british nyasaland (indigenous cultivation)": ("NYA-1891-2025", "Nyasaland Protectorate (Malawi)", "Indigenous cultivation variant"),
}


# ---------------------------------------------------------------------------
# 7. Aggregate detection
# ---------------------------------------------------------------------------

AGGREGATE_RE = re.compile(r"^total\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# 8. Direct-match countries (simple name matching)
# ---------------------------------------------------------------------------

DIRECT_COUNTRIES = {
    "albania": ("ALB-1913-2025", "Albania"),
    "argentina": ("ARG-1902-2025", "Argentina"),
    "australia": ("AUS-1901-2025", "Australia"),
    "austria": ("AUT-1918-2025", "Austria"),
    "belgium": ("BEL-1831-2025", "Belgium"),
    "bolivia": ("BOL-1938-2025", "Bolivia"),
    "brazil": ("BRA-1909-2025", "Brazil"),
    "bulgaria": ("BGR-1940-2025", "Bulgaria"),
    "canada": ("CAN-1948-2025", "Canada"),
    "chile": ("CHL-1902-2025", "Chile"),
    "colombia": ("COL-1922-2025", "Colombia"),
    "costa rica": ("CRI-1800-2025", "Costa Rica"),
    "cuba": ("CUB-1800-2025", "Cuba"),
    "denmark": ("DNK-1920-2025", "Denmark"),
    "dominican republic": ("DOM-1800-2025", "Dominican Republic"),
    "ecuador": ("ECU-1942-2025", "Ecuador"),
    "el salvador": ("SLV-1821-2025", "El Salvador"),
    "estonia": ("EST-1991-2025", "Estonia"),
    "finland": ("FIN-1940-2025", "Finland"),
    "france": ("FRA-1919-2025", "France"),
    "germany": ("DEU-1990-2025", "Germany"),
    "greece": ("GRC-1919-2025", "Greece"),
    "guatemala": ("GTM-1821-2025", "Guatemala"),
    "haiti": ("HTI-1800-2025", "Haiti"),
    "honduras": ("HND-1800-2025", "Honduras"),
    "hungary": ("HUN-1947-2025", "Hungary"),
    "iceland": ("ISL-1800-2025", "Iceland"),
    "italy": ("ITA-1919-2025", "Italy"),
    "latvia": ("LVA-1991-2025", "Latvia"),
    "lithuania": ("LTU-1991-2025", "Lithuania"),
    "luxembourg": ("LUX-2000-2025", "Luxembourg"),
    "mexico": ("MEX-1800-2025", "Mexico"),
    "netherlands": ("NLD-1800-2025", "Netherlands"),
    "new zealand": ("NZL-1907-2025", "New Zealand"),
    "nicaragua": ("NIC-1800-2025", "Nicaragua"),
    "norway": ("NOR-1800-2025", "Norway"),
    "panama": ("PAN-1903-2025", "Panama"),
    "paraguay": ("PRY-1938-2025", "Paraguay"),
    "peru": ("PER-1942-2025", "Peru"),
    "poland": ("POL-1945-2025", "Poland"),
    "portugal": ("PRT-1800-2025", "Portugal"),
    "romania": ("ROU-1940-2025", "Romania"),
    "serbia": ("SRB-2008-2025", "Serbia"),
    "spain": ("ESP-1800-2025", "Spain"),
    "sweden": ("SWE-1800-2025", "Sweden"),
    "switzerland": ("CHE-1800-2025", "Switzerland"),
    "uruguay": ("URY-1828-2025", "Uruguay"),
    "venezuela": ("VEN-1821-2025", "Venezuela"),
}


# ---------------------------------------------------------------------------
# 9. Main matching logic
# ---------------------------------------------------------------------------

results = []

for name in cleaned_names:
    status = "unmatched"
    matched_code = ""
    matched_name = ""
    parent_code = ""
    notes = ""

    # --- Step A: detect aggregates ---
    if AGGREGATE_RE.match(name):
        status = "aggregate"
        notes = "Total/summary row"
        results.append((name, status, matched_code, matched_name, parent_code, notes))
        continue

    # --- Step B: strip variant qualifiers to get base name ---
    base_name = strip_variant_qualifier(name)
    is_variant = base_name != name
    variant_note = ""
    if is_variant:
        qualifier = name[len(base_name):].strip()
        variant_note = f"Measurement variant: {qualifier}"

    # --- Step C: check subnational map (use original name first, then base) ---
    lookup_key = norm_key(name)
    if lookup_key in SUBNATIONAL_MAP:
        parent_code_val, parent_name, sub_note = SUBNATIONAL_MAP[lookup_key]
        status = "subnational"
        matched_code = parent_code_val
        matched_name = parent_name
        parent_code = parent_code_val
        notes = f"Subnational: {sub_note}"
        if variant_note:
            notes += f"; {variant_note}"
        results.append((name, status, matched_code, matched_name, parent_code, notes))
        continue

    lookup_base = norm_key(base_name)
    if lookup_base in SUBNATIONAL_MAP:
        parent_code_val, parent_name, sub_note = SUBNATIONAL_MAP[lookup_base]
        status = "subnational"
        matched_code = parent_code_val
        matched_name = parent_name
        parent_code = parent_code_val
        notes = f"Subnational: {sub_note}"
        if variant_note:
            notes += f"; {variant_note}"
        results.append((name, status, matched_code, matched_name, parent_code, notes))
        continue

    # --- Step D: check manual map ---
    if lookup_key in MANUAL_MAP:
        code, mname = MANUAL_MAP[lookup_key]
        status = "matched"
        matched_code = code
        matched_name = mname
        notes = variant_note if variant_note else ""
        results.append((name, status, matched_code, matched_name, parent_code, notes))
        continue

    if lookup_base in MANUAL_MAP:
        code, mname = MANUAL_MAP[lookup_base]
        status = "matched"
        matched_code = code
        matched_name = mname
        notes = variant_note if variant_note else ""
        results.append((name, status, matched_code, matched_name, parent_code, notes))
        continue

    # --- Step E: check direct countries map ---
    if lookup_base in DIRECT_COUNTRIES:
        code, mname = DIRECT_COUNTRIES[lookup_base]
        status = "matched"
        matched_code = code
        matched_name = mname
        notes = variant_note if variant_note else ""
        results.append((name, status, matched_code, matched_name, parent_code, notes))
        continue

    # --- Step F: exact name match in database ---
    norm_base = normalize(base_name)
    if norm_base in name_to_polity:
        candidates = name_to_polity[norm_base]
        # Prefer aggregate/colonial types for period data
        chosen = candidates[0]
        for c in candidates:
            if c[2] in ("aggregate", "colonial", "sovereign"):
                chosen = c
                break
        status = "matched"
        matched_code = chosen[0]
        matched_name = chosen[1]
        notes = f"Exact name match in DB" + (f"; {variant_note}" if variant_note else "")
        results.append((name, status, matched_code, matched_name, parent_code, notes))
        continue

    # --- Step G: detect colon-based subnational patterns not in the map ---
    if ":" in base_name:
        parent_part = base_name.split(":")[0].strip()
        sub_part = base_name.split(":", 1)[1].strip()
        # Try to match the parent part
        parent_lower = norm_key(parent_part)
        parent_match = None
        if parent_lower in MANUAL_MAP:
            parent_match = MANUAL_MAP[parent_lower]
        elif parent_lower in DIRECT_COUNTRIES:
            parent_match = DIRECT_COUNTRIES[parent_lower]
        else:
            norm_parent = normalize(parent_part)
            if norm_parent in name_to_polity:
                c = name_to_polity[norm_parent][0]
                parent_match = (c[0], c[1])

        if parent_match:
            status = "subnational"
            matched_code = parent_match[0]
            matched_name = parent_match[1]
            parent_code = parent_match[0]
            notes = f"Subnational: {sub_part}"
            if variant_note:
                notes += f"; {variant_note}"
            results.append((name, status, matched_code, matched_name, parent_code, notes))
            continue

    # If still unmatched
    notes = variant_note if variant_note else "No match found"
    results.append((name, status, matched_code, matched_name, parent_code, notes))


# ---------------------------------------------------------------------------
# 10. Write output CSV
# ---------------------------------------------------------------------------

with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "cleaned_name", "match_status", "matched_polity_code",
        "matched_polity_name", "parent_polity_code", "notes"
    ])
    for row in results:
        writer.writerow(row)


# ---------------------------------------------------------------------------
# 11. Summary
# ---------------------------------------------------------------------------

counts = defaultdict(int)
for row in results:
    counts[row[1]] += 1

print("=" * 65)
print("REGION MATCHING SUMMARY")
print("=" * 65)
print(f"  Total unique cleaned names:  {len(results)}")
print(f"  Matched:                     {counts['matched']}")
print(f"  Subnational:                 {counts['subnational']}")
print(f"  Aggregate:                   {counts['aggregate']}")
print(f"  Unmatched:                   {counts['unmatched']}")
print("=" * 65)

if counts["unmatched"] > 0:
    print("\nUNMATCHED entries:")
    for row in results:
        if row[1] == "unmatched":
            print(f"  - {row[0]}  ({row[5]})")

print(f"\nOutput written to: {OUT_PATH}")
