#!/usr/bin/env python3
"""
Extract subnational polygons for historical regions from the Excel cleaning_geography.

Strategy (in order of preference):
  Tier 1 — CShapes 2.0: actual historical boundaries for colonial-era entities
  Tier 2 — GADM admin-1: good proxy where colonial→modern boundary continuity holds
  Tier 3 — Flag: no good modern proxy available; requires historical GIS

Each polygon is annotated with a quality tier and limitations.

Sources:
  - CShapes 2.0 (Schvitz et al. 2022) — dependencies=TRUE for colonial entities
  - GADM 3.6 (admin levels 0-1) — modern administrative boundaries
  - Uti possidetis juris principle — colonial boundaries → modern national borders in Africa
"""

import warnings

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

warnings.filterwarnings("ignore")

BASE = "/home/usuario/whep-polities"
GADM_PATH = "/home/usuario/LandInG/gadm/gadm36_levels.gpkg"
CSHAPES_PATH = f"{BASE}/data/geodata/cshapes2_full.gpkg"

# ── Load sources ─────────────────────────────────────────────────────

print("Loading data sources...")
cshapes = gpd.read_file(CSHAPES_PATH)
cshapes["start_year"] = pd.to_datetime(cshapes["start"]).dt.year
cshapes["end_year"] = pd.to_datetime(cshapes["end"]).dt.year
print(f"  CShapes: {len(cshapes)} features, {cshapes['country_name'].nunique()} unique names")

gadm0 = gpd.read_file(GADM_PATH, layer="level0")
gadm1 = gpd.read_file(GADM_PATH, layer="level1")
gadm2 = gpd.read_file(GADM_PATH, layer="level2")
print(f"  GADM level-0: {len(gadm0)} countries")
print(f"  GADM level-1: {len(gadm1)} admin units")
print(f"  GADM level-2: {len(gadm2)} admin units")

matching = pd.read_csv(f"{BASE}/data/analysis/region_matching.csv")
subnational = matching[matching["match_status"] == "subnational"].copy()
print(f"  Subnational regions to resolve: {len(subnational)}")


# ── Helper: find CShapes polygon by name for a target era ────────────

def find_cshapes(name, target_year=1920):
    """Find best CShapes polygon matching name, preferring target_year."""
    matches = cshapes[cshapes["country_name"].str.lower() == name.lower()]
    if len(matches) == 0:
        # Try contains
        matches = cshapes[cshapes["country_name"].str.lower().str.contains(
            name.lower(), regex=False)]
    if len(matches) == 0:
        return None
    # Pick the entry containing target_year, or closest
    for _, row in matches.iterrows():
        if row["start_year"] <= target_year <= row["end_year"]:
            return row
    return matches.iloc[len(matches) // 2]  # middle entry as fallback


def find_gadm1(country_iso, state_names):
    """Get GADM admin-1 polygon(s) for a country by state name(s)."""
    country = gadm1[gadm1["GID_0"] == country_iso]
    if len(country) == 0:
        return None, []
    matched_names = []
    geoms = []
    for sname in state_names:
        for _, row in country.iterrows():
            if (sname.lower() in row["NAME_1"].lower() or
                    (pd.notna(row.get("VARNAME_1")) and
                     sname.lower() in str(row["VARNAME_1"]).lower())):
                geoms.append(row.geometry)
                matched_names.append(row["NAME_1"])
                break
    if geoms:
        return unary_union(geoms), matched_names
    return None, []


def find_gadm0(country_iso):
    """Get GADM admin-0 polygon for a country."""
    matches = gadm0[gadm0["GID_0"] == country_iso]
    if len(matches) > 0:
        return matches.iloc[0].geometry
    return None


def find_gadm2(country_iso, dept_names):
    """Get GADM admin-2 polygon(s) for a country by department name(s)."""
    country = gadm2[gadm2["GID_0"] == country_iso]
    if len(country) == 0:
        return None, []
    matched_names = []
    geoms = []
    for dname in dept_names:
        for _, row in country.iterrows():
            if (dname.lower() in row["NAME_2"].lower() or
                    (pd.notna(row.get("VARNAME_2")) and
                     dname.lower() in str(row["VARNAME_2"]).lower())):
                geoms.append(row.geometry)
                matched_names.append(row["NAME_2"])
                break
    if geoms:
        return unary_union(geoms), matched_names
    return None, []


# ── Define subnational extraction rules ──────────────────────────────
# Each entry: (excel_name, method, params, quality_tier, limitations)
# method: "cshapes", "gadm0", "gadm1", "gadm1_merge", "cshapes_merge", "none"
# quality_tier: 1=historical boundary, 2=good proxy, 3=acceptable proxy, 4=no proxy

SUBNATIONAL_RULES = {
    # ─── FRENCH WEST AFRICA sub-colonies (Tier 1: CShapes has individual colonies) ───
    "french senegal": ("cshapes", "Senegal", 1,
        "CShapes colonial-era Senegal; borders unchanged at independence (uti possidetis juris)"),
    "french guinea": ("cshapes", "Guinea", 1,
        "CShapes colonial-era Guinea; borders unchanged at independence"),
    "french dahomey": ("cshapes", "Benin", 1,
        "CShapes Dahomey/Benin; colonial borders became modern borders"),
    "french ivory coast": ("cshapes", "Cote D'Ivoire", 1,
        "CShapes Côte d'Ivoire; colonial borders became modern borders"),
    "french niger": ("cshapes", "Niger", 1,
        "CShapes colonial Niger; borders unchanged at independence"),
    "french mauritania": ("cshapes", "Mauritania", 1,
        "CShapes colonial Mauritania; borders unchanged at independence"),
    "french sudan": ("cshapes", "Mali", 1,
        "CShapes Mali/French Sudan; borders changed when Upper Volta carved out (1919) and reattached (1932-1947)"),
    "french upper volta": ("cshapes", "Burkina Faso (Upper Volta)", 1,
        "CShapes Upper Volta/Burkina Faso; dissolved 1932-1947, reconstituted boundaries"),
    "french dakar": ("gadm1", {"iso": "SEN", "states": ["Dakar"]}, 3,
        "Dakar was a city/commune, not a territory. GADM admin-1 Dakar region is a rough proxy"),
    "french upper senegal and niger": ("cshapes_merge", ["Mali", "Niger", "Burkina Faso (Upper Volta)"], 3,
        "Upper Senegal and Niger (1904-1920) encompassed Mali+Niger+Burkina Faso. Merged CShapes polygons are approximate; internal boundaries shifted multiple times"),
    "french senegal and sudan": ("cshapes_merge", ["Senegal", "Mali"], 2,
        "Combined Senegal + French Sudan (Mali) polygons"),

    # ─── FRENCH EQUATORIAL AFRICA sub-colonies (Tier 1-2: CShapes + GADM) ───
    "french gabon": ("cshapes", "Gabon", 1,
        "CShapes colonial Gabon; borders unchanged at independence"),
    "french middle congo": ("cshapes", "Congo", 1,
        "CShapes Congo-Brazzaville = Middle Congo; borders unchanged at independence"),
    "french oubangui\u2011chari": ("cshapes", "Central African Republic", 1,
        "CShapes CAR = Oubangui-Chari; colonial borders became modern borders"),
    "french chad": ("cshapes", "Chad", 1,
        "CShapes colonial Chad; borders unchanged at independence"),
    "french gabon and middle congo": ("cshapes_merge", ["Gabon", "Congo"], 2,
        "Merged Gabon + Congo-Brazzaville CShapes polygons"),
    "french middle congo and oubangui\u2011chari": ("cshapes_merge", ["Congo", "Central African Republic"], 2,
        "Merged Congo + CAR CShapes polygons"),
    "french chad and oubangui\u2011chari": ("cshapes_merge", ["Chad", "Central African Republic"], 2,
        "Merged Chad + CAR CShapes polygons"),
    "french chad, middle congo and oubangui\u2011chari": ("cshapes_merge", ["Chad", "Congo", "Central African Republic"], 2,
        "Merged Chad + Congo + CAR CShapes polygons"),
    "french chad, gabon, middle congo and oubangui\u2011chari": ("cshapes_merge", ["Chad", "Gabon", "Congo", "Central African Republic"], 2,
        "All four FEA territories merged; equals the FEA aggregate polygon"),

    # ─── FRENCH INDOCHINA (Tier 1 for Cambodia/Laos; Tier 4 for Vietnam divisions) ───
    "french cambodia": ("cshapes", "Cambodia (Kampuchea)", 1,
        "CShapes colonial Cambodia; borders largely stable since French protectorate"),
    "french laos": ("cshapes", "Laos", 1,
        "CShapes colonial Laos; borders largely stable since French protectorate"),
    "french tonkin": ("none", None, 4,
        "Tonkin = northern Vietnam (north of ~18th parallel, around Hanoi). No modern admin equivalent; the 1954 N/S Vietnam partition roughly follows the old Tonkin/Annam boundary. Would require historical GIS data"),
    "french annam": ("none", None, 4,
        "Annam = central Vietnam (Hue region, between ~11th-18th parallels). No modern admin equivalent; cuts across Vietnamese provinces. Would require historical GIS data"),
    "french cochinchina": ("none", None, 4,
        "Cochinchina = southern Vietnam (Saigon, Mekong Delta, south of ~11th parallel). No modern admin equivalent; would require historical GIS data"),

    # ─── BRITISH INDIA (Tier 4: no good modern proxy) ───
    "british india: crown provinces": ("none", None, 4,
        "Crown provinces (~60% of subcontinent) were directly-ruled territories forming a patchwork. No modern admin equivalent due to 1947 Partition and 1956 linguistic state reorganisation"),
    "british india: princely states": ("none", None, 4,
        "Princely states (~584 semi-autonomous entities, ~40% of subcontinent) formed a scattered patchwork. No modern admin equivalent; would require specialised historical GIS (e.g. Imperial Gazetteer maps)"),
    "british india: south provinces": ("none", None, 4,
        "Likely Madras Presidency and southern territories. Roughly modern Tamil Nadu + Kerala + Andhra Pradesh + parts of Karnataka, but boundaries differ substantially from modern states"),
    "british india: crown provinces, excluding burma": ("none", None, 4,
        "Crown provinces minus Burma. Same limitations as 'Crown provinces'; Burma subtraction is feasible with CShapes Myanmar polygon, but Crown/Princely distinction has no spatial equivalent"),
    "british india: excluding burma": ("cshapes_subtract", {"base": "India", "subtract": ["Myanmar (Burma)"]}, 3,
        "CShapes British India polygon minus CShapes Myanmar polygon. Gives correct outer boundary, but cannot represent internal Crown provinces vs Princely states distinction"),

    # ─── UNFEDERATED MALAY STATES (Tier 2: GADM admin-1 = good proxy) ───
    "british unfederated malay states: johor": ("gadm1", {"iso": "MYS", "states": ["Johor"]}, 2,
        "Colonial Johor = modern Johor state (Malaysia). Boundaries stable since colonial era"),
    "british unfederated malay states: kedah": ("gadm1", {"iso": "MYS", "states": ["Kedah"]}, 2,
        "Colonial Kedah = modern Kedah state (Malaysia). Boundaries stable since colonial era"),
    "british unfederated malay states: kelantan": ("gadm1", {"iso": "MYS", "states": ["Kelantan"]}, 2,
        "Colonial Kelantan = modern Kelantan state (Malaysia). Boundaries stable since colonial era"),
    "british unfederated malay states: perlis": ("gadm1", {"iso": "MYS", "states": ["Perlis"]}, 2,
        "Colonial Perlis = modern Perlis state (Malaysia). Boundaries stable since colonial era"),
    "british unfederated malay states: terengganu": ("gadm1", {"iso": "MYS", "states": ["Terengganu"]}, 2,
        "Colonial Terengganu = modern Terengganu state (Malaysia). Boundaries stable since colonial era"),

    # ─── STRAITS SETTLEMENTS (Tier 2: GADM admin-0/1) ───
    "british straits settlements: singapore": ("gadm0", "SGP", 2,
        "Modern Singapore = colonial Singapore settlement. Boundaries stable"),
    "british straits settlements: penang": ("gadm1", {"iso": "MYS", "states": ["Pulau Pinang"]}, 2,
        "Colonial Penang = modern Pulau Pinang state. Note: colonial Penang included the Dindings (transferred to Perak, 1935)"),
    "british straits settlements: malacca": ("gadm1", {"iso": "MYS", "states": ["Melaka"]}, 2,
        "Colonial Malacca = modern Melaka state. Boundaries stable since colonial era"),
    "british straits settlements: labuan": ("gadm1", {"iso": "MYS", "states": ["Labuan"]}, 2,
        "Colonial Labuan = modern Labuan Federal Territory. Boundaries stable (island)"),

    # ─── UK SUB-REGIONS (Tier 2: stable since centuries) ───
    "uk: england and wales": ("gadm1_merge", {"iso": "GBR", "states": ["England", "Wales"]}, 2,
        "Merged England + Wales from GADM. Boundary stable since Laws in Wales Acts (1535-1542)"),
    "uk: great britain": ("gadm1_merge", {"iso": "GBR", "states": ["England", "Wales", "Scotland"]}, 2,
        "Merged England + Wales + Scotland from GADM"),
    "uk: scotland": ("gadm1", {"iso": "GBR", "states": ["Scotland"]}, 2,
        "Scotland boundary with England fixed since Treaty of York (1237)"),
    "uk: north ireland": ("gadm1", {"iso": "GBR", "states": ["Northern Ireland"]}, 2,
        "Northern Ireland created 1921 (6 counties of Ulster); boundary stable since"),

    # ─── BRITISH NIGERIA (Tier 1: CShapes has pre-1914 protectorates) ───
    "british nigeria: north provinces": ("cshapes", "Northern Nigeria", 1,
        "CShapes Northern Nigeria protectorate (1899-1913). Post-1914 provincial boundary followed same line (roughly along Niger/Benue rivers). CShapes polygon ends at 1913; used as proxy for post-1914 administrative division"),
    "british nigeria: south provinces": ("cshapes", "Southern Nigeria", 1,
        "CShapes Southern Nigeria protectorate (1899-1913). Same caveat as north provinces"),
    "british nigeria and cameroon: north provinces, adamawa and bornu": ("cshapes_merge", ["Northern Nigeria", "British Cameroons"], 2,
        "Merged Northern Nigeria + British Cameroons CShapes polygons. Northern Cameroons was administered as part of northern Nigerian provinces"),
    "british nigeria and cameroon: south provinces": ("cshapes_merge", ["Southern Nigeria", "British Cameroons"], 2,
        "Merged Southern Nigeria + British Cameroons CShapes polygons"),

    # ─── FRENCH SYRIA AND LEBANON ───
    "french syria": ("cshapes", "Syria", 1,
        "CShapes Syria from French Mandate period; boundaries established under mandate"),
    "french lebanon": ("cshapes", "Lebanon", 1,
        "CShapes Lebanon from French Mandate period; boundaries established under mandate"),
    "french syria and lebanon: state of the alawites": ("gadm1_merge", {"iso": "SYR", "states": ["Lattakia", "Tartous"]}, 3,
        "Alawite State (1920-1937): autonomous territory in NW Syria. Approximated by Latakia + Tartus governorates from GADM. Historical boundaries extended slightly beyond these into parts of Hama and Idlib"),

    # ─── DUTCH EAST INDIES (Tier 2-3: GADM province groupings) ───
    "dutch java and madura": ("gadm1_merge", {"iso": "IDN", "states": ["Jawa Barat", "Jawa Tengah", "Jawa Timur", "Banten", "Jakarta Raya", "Yogyakarta"]}, 2,
        "Java provinces from GADM. Madura is part of Jawa Timur. Island-based division; geographic boundaries are precise"),
    "dutch java and madura (european cultivation)": ("gadm1_merge", {"iso": "IDN", "states": ["Jawa Barat", "Jawa Tengah", "Jawa Timur", "Banten", "Jakarta Raya", "Yogyakarta"]}, 2,
        "Same geography as Java and Madura; European cultivation is a data variant, not geographic"),
    "dutch java and madura (indigenous cultivation)": ("gadm1_merge", {"iso": "IDN", "states": ["Jawa Barat", "Jawa Tengah", "Jawa Timur", "Banten", "Jakarta Raya", "Yogyakarta"]}, 2,
        "Same geography as Java and Madura; indigenous cultivation is a data variant"),
    "dutch java and madura (native cultivations)": ("gadm1_merge", {"iso": "IDN", "states": ["Jawa Barat", "Jawa Tengah", "Jawa Timur", "Banten", "Jakarta Raya", "Yogyakarta"]}, 2,
        "Same geography as Java and Madura"),
    "dutch sumatra": ("gadm1_merge", {"iso": "IDN", "states": ["Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi", "Sumatera Selatan", "Bengkulu", "Lampung", "Kepulauan Bangka Belitung", "Kepulauan Riau"]}, 2,
        "All Sumatran provinces from GADM. Island-based; geographic boundary is precise"),
    "dutch sumatra (european cultivation)": ("gadm1_merge", {"iso": "IDN", "states": ["Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi", "Sumatera Selatan", "Bengkulu", "Lampung", "Kepulauan Bangka Belitung", "Kepulauan Riau"]}, 2,
        "Same geography as Sumatra"),
    "dutch java and sumatra": ("gadm1_merge", {"iso": "IDN", "states": ["Jawa Barat", "Jawa Tengah", "Jawa Timur", "Banten", "Jakarta Raya", "Yogyakarta", "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi", "Sumatera Selatan", "Bengkulu", "Lampung", "Kepulauan Bangka Belitung", "Kepulauan Riau"]}, 2,
        "Java + Sumatra provinces merged"),
    "dutch bali and lombok": ("gadm1_merge", {"iso": "IDN", "states": ["Bali", "Nusa Tenggara Barat"]}, 3,
        "Bali province + Nusa Tenggara Barat (which includes Sumbawa, not part of historical 'Bali and Lombok'). Acceptable proxy; Lombok is ~80% of NTB area"),
    "dutch bali and lombok (indigenous cultivation)": ("gadm1_merge", {"iso": "IDN", "states": ["Bali", "Nusa Tenggara Barat"]}, 3,
        "Same geography as Bali and Lombok"),
    "dutch east outer provinces": ("gadm1_merge", {"iso": "IDN", "states": ["Nusa Tenggara Timur", "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan", "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku", "Maluku Utara", "Papua", "Papua Barat"]}, 3,
        "Groote Oost (East Outer Provinces): all islands east of Java/Borneo. GADM provinces of NTT + Sulawesi + Maluku + Papua. Excludes Bali/NTB. Note: historical division included West New Guinea (now Indonesian Papua)"),
    "dutch east outer provinces (european plantations)": ("gadm1_merge", {"iso": "IDN", "states": ["Nusa Tenggara Timur", "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan", "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku", "Maluku Utara", "Papua", "Papua Barat"]}, 3,
        "Same geography as East Outer Provinces"),
    "dutch east outer provinces (indigenous cultivation)": ("gadm1_merge", {"iso": "IDN", "states": ["Nusa Tenggara Timur", "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan", "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku", "Maluku Utara", "Papua", "Papua Barat"]}, 3,
        "Same geography as East Outer Provinces"),
    "dutch java, madura and east outer provinces": ("gadm1_merge", {"iso": "IDN", "states": ["Jawa Barat", "Jawa Tengah", "Jawa Timur", "Banten", "Jakarta Raya", "Yogyakarta", "Nusa Tenggara Timur", "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan", "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku", "Maluku Utara", "Papua", "Papua Barat"]}, 3,
        "Java + Madura + East Outer Provinces (everything except Sumatra, Borneo, Bali/Lombok)"),

    # ─── USSR (Tier 2-3) ───
    "ussr in europe": ("none", None, 4,
        "European USSR ≈ west of Ural Mountains. Would require classifying Russian federal subjects into European/Asian; some straddle the boundary (Chelyabinsk, Sverdlovsk, Orenburg, Bashkortostan). Plus non-Russian SSRs"),
    "ussr in asia": ("none", None, 4,
        "Asian USSR ≈ east of Urals + Central Asian SSRs. Same boundary ambiguity as above"),
    "ussr: transcaucasian sfsr": ("cshapes_merge", ["Georgia", "Armenia", "Azerbaijan"], 2,
        "Transcaucasian SFSR (1922-1936) = Georgia + Armenia + Azerbaijan. CShapes has individual country polygons"),
    "ussr: khibiny": ("none", None, 4,
        "Khibiny is a mining locality in the Kola Peninsula (Murmansk Oblast), not an administrative unit. Would require a point or very small area polygon"),

    # ─── PORTUGUESE MOZAMBIQUE (Tier 3: GADM province groupings) ───
    "portuguese mozambique: company": ("gadm1_merge", {"iso": "MOZ", "states": ["Manica", "Sofala"]}, 3,
        "Mozambique Company territory (1891-1942) ≈ modern Manica + Sofala provinces. Historical boundary followed the Save River (south) and Zambezi (north), which don't precisely align with modern provincial lines"),
    "portuguese mozambique: niassa": ("gadm1_merge", {"iso": "MOZ", "states": ["Cabo Delgado", "Niassa"]}, 3,
        "Niassa Company territory (1893-1929) ≈ modern Cabo Delgado + Niassa provinces. Southern boundary was the Lurio River, not precisely matching modern provincial boundary"),
    "portuguese mozambique: province": ("gadm1_merge", {"iso": "MOZ", "states": ["Maputo", "Gaza", "Inhambane", "Zambezia", "Tete", "Nampula"]}, 3,
        "Directly-administered territory = remainder after subtracting Company and Niassa zones. Approximate; boundaries were river-based, not aligned with modern provinces"),

    # ─── ITALIAN LIBYA (Tier 3: GADM admin-1 groupings) ───
    "italian libya: tripolitania": ("gadm1_merge", {"iso": "LBY", "states": ["Tripoli", "Al Murgub", "Misratah", "Al Jufrah", "Nalut", "Az Zawiyah", "An Nuqat al Khams", "Jabal al Gharbi"]}, 3,
        "Tripolitania = NW Libya. Approximated by western Libyan districts. Historical boundary roughly followed the Gulf of Sidra coastline. Modern districts are much finer than the three historical regions"),
    "italian libya: cyrenaica": ("gadm1_merge", {"iso": "LBY", "states": ["Benghazi", "Al Marj", "Darnah", "Al Jabal al Akhdar", "Al Butnan", "Al Kufrah", "Al Wahat"]}, 3,
        "Cyrenaica = eastern Libya. Approximated by eastern Libyan districts. Libya used this tripartite division (Tripolitania/Cyrenaica/Fezzan) officially until 1963"),

    # ─── CHINA: MANCHURIA (Tier 3) ───
    "china: manchuria": ("gadm1_merge", {"iso": "CHN", "states": ["Heilongjiang", "Jilin", "Liaoning"]}, 3,
        "Manchuria ≈ modern Heilongjiang + Jilin + Liaoning ('Three Northeastern Provinces'). Note: Manchukuo (1932-1945) also included parts of Inner Mongolia (Hulunbuir, Hinggan) and Hebei (Chengde); this approximation covers the core territory only"),
    "china: excluding manchuria": ("subtract_gadm1", {"iso": "CHN", "subtract": ["Heilongjiang", "Jilin", "Liaoning"]}, 3,
        "CShapes China polygon minus Manchuria (Heilongjiang+Jilin+Liaoning GADM provinces). Approximate: Manchukuo also included parts of Inner Mongolia"),

    # ─── TURKEY ASIA/EUROPE (Tier 2-3) ───
    "turkey in europe": ("gadm1_merge", {"iso": "TUR", "states": ["Edirne", "Kirklareli", "Tekirdag"]}, 3,
        "East Thrace ≈ Edirne + Kirklareli + Tekirdag provinces. Note: Istanbul and Canakkale provinces straddle the continental divide; this approximation excludes their European parts"),
    "turkey in asia": ("subtract_gadm1", {"iso": "TUR", "subtract": ["Edirne", "Kirklareli", "Tekirdag"]}, 3,
        "Turkey GADM polygon minus East Thrace (Edirne+Kirklareli+Tekirdag). Note: Istanbul and Canakkale provinces straddle the divide; this keeps their entire area in the 'Asia' result"),

    # ─── MOROCCO (Tier 3-4) ───
    "french east morocco": ("none", None, 4,
        "Eastern zone of the French protectorate (towards Algeria, including Taza corridor). Not a standard modern division; would require historical maps of the French protectorate administrative zones"),
    "french west morocco": ("none", None, 4,
        "Western/Atlantic zone of the French protectorate (Casablanca, Rabat). Not a standard modern division"),

    # ─── AUSTRALIA (Tier 2: stable boundaries) ───
    "australia: queensland": ("gadm1", {"iso": "AUS", "states": ["Queensland"]}, 2,
        "Boundaries stable since colonial era; Queensland established 1859"),
    "australia: tasmania": ("gadm1", {"iso": "AUS", "states": ["Tasmania"]}, 2,
        "Island; boundaries inherently stable"),
    "australia: victoria": ("gadm1", {"iso": "AUS", "states": ["Victoria"]}, 2,
        "Boundaries stable since separation from New South Wales (1851)"),

    # ─── USA (Tier 2: stable state boundaries) ───
    "usa: california": ("gadm1", {"iso": "USA", "states": ["California"]}, 2,
        "State boundaries stable since 1850 admission"),
    "usa: louisiana and florida": ("gadm1_merge", {"iso": "USA", "states": ["Louisiana", "Florida"]}, 2,
        "State boundaries stable"),
    "usa: other states different from alaska, california, louisiana and florida": ("subtract_gadm1", {"iso": "USA", "subtract": ["Alaska", "California", "Louisiana", "Florida"]}, 3,
        "USA GADM polygon minus Alaska, California, Louisiana, Florida. Contiguous US residual + Hawaii"),

    # ─── SPANISH MOROCCO: CEUTA AND MELILLA (Tier 2) ───
    "spanish morocco: ceuta": ("gadm1", {"iso": "ESP", "states": ["Ceuta"]}, 2,
        "Modern Spanish autonomous city; boundaries stable"),
    "spanish morocco: melilla": ("gadm1", {"iso": "ESP", "states": ["Melilla"]}, 2,
        "Modern Spanish autonomous city; boundaries stable"),

    # ─── SINGLE ENTRIES ───
    "france: alsace": ("gadm2_merge", {"iso": "FRA", "depts": ["Bas-Rhin", "Haut-Rhin"]}, 2,
        "Alsace = Bas-Rhin + Haut-Rhin départements (GADM level-2). Note: historical Alsace included parts of Belfort (now Territoire de Belfort)"),
    "denmark: faroe islands": ("gadm0", "FRO", 2,
        "GADM Faroe Islands; boundaries stable (island group)"),
    "denmark: greenland": ("gadm0", "GRL", 2,
        "GADM Greenland; boundaries stable (island)"),
    "denmark (rural communities)": ("gadm0", "DNK", 2,
        "Not a geographic subdivision; rural communities across all Denmark. Using full Denmark polygon"),
    "argentina: mendoza": ("gadm1", {"iso": "ARG", "states": ["Mendoza"]}, 2,
        "Modern Mendoza province; boundaries stable since colonial era"),
    "brazil: sao paulo": ("gadm1", {"iso": "BRA", "states": ["São Paulo"]}, 2,
        "Modern São Paulo state; boundaries mostly stable"),
    "el salvador: san salvador department": ("gadm1", {"iso": "SLV", "states": ["San Salvador"]}, 2,
        "Modern San Salvador department"),
    "new zealand: cook": ("gadm0", "COK", 2,
        "Cook Islands; boundaries stable (island group)"),
    "portugal: madeira": ("gadm1", {"iso": "PRT", "states": ["Madeira"]}, 2,
        "Madeira autonomous region; island, boundaries inherently stable"),
    "spain: canary": ("gadm1", {"iso": "ESP", "states": ["Islas Canarias"]}, 2,
        "Canary Islands; island group, boundaries inherently stable"),
    "union of south africa: cape province": ("gadm1_merge", {"iso": "ZAF", "states": ["Western Cape", "Eastern Cape", "Northern Cape"]}, 3,
        "Historical Cape Province (1910-1994) was divided into 3 modern provinces in 1994. Merged Western + Eastern + Northern Cape is a good approximation but modern boundaries may differ at margins"),
    "british kenya (european cultivation)": ("cshapes", "Kenya", 2,
        "Not a geographic subdivision; 'European cultivation' is a data variant. Using full Kenya CShapes polygon"),
    "british nyasaland (european cultivation)": ("cshapes", "Malawi", 2,
        "Not a geographic subdivision; data variant. Using full Nyasaland/Malawi CShapes polygon"),
    "british nyasaland (indigenous cultivation)": ("cshapes", "Malawi", 2,
        "Not a geographic subdivision; data variant. Using full Nyasaland/Malawi CShapes polygon"),
    "british mauritius, adamawa and bornu": ("none", None, 4,
        "Possibly mislabelled OCR entry. Mauritius is an island; Adamawa and Bornu are Nigerian provinces. Cannot resolve geographically"),
    "dutch sint eustatius and sint maarten": ("gadm0_merge", ["BES", "SXM"], 3,
        "Colonial Dutch Caribbean islands. Merged GADM: Bonaire/Sint Eustatius/Saba (BES) + Sint Maarten (SXM). Includes Bonaire and Saba which weren't part of the historical grouping"),
    "french guadeloupe: marie\u2011galante": ("none", None, 4,
        "Marie-Galante is a small island in the Guadeloupe archipelago. Would require sub-admin polygon extraction"),
    "french madagascar: juan de nova": ("none", None, 4,
        "Juan de Nova is a tiny island (4.4 km²) in the Mozambique Channel. Would require Natural Earth minor islands data"),
    "french oceania: makatea": ("none", None, 4,
        "Makatea is a single atoll in French Polynesia (29 km²). Known for phosphate mining. Would require point/small-area data"),
    "japan: karafuto prefecture": ("cshapes", "Southern Sakhalin Island", 1,
        "CShapes has Southern Sakhalin Island (1905-1945) polygon; this IS Karafuto Prefecture"),
    "japanese south pacific: angaur": ("none", None, 4,
        "Angaur is a single island in Palau (8 km²). Would require specific island polygon"),
    "japanese south pacific: palau": ("gadm0", "PLW", 2,
        "GADM Palau country polygon"),
    "russia in asia": ("none", None, 4,
        "Asian Russia ≈ east of Urals. Would require classifying Russian federal subjects"),
    "russia in europe": ("none", None, 4,
        "European Russia ≈ west of Urals. Same caveat"),
}


# ── Execute extraction ──────────────────────────────────────────────

print("\nExtracting subnational polygons...")

results = []
stats = {"tier1": 0, "tier2": 0, "tier3": 0, "tier4": 0, "missing_rule": 0}

for _, row in subnational.iterrows():
    name = row["cleaned_name"].strip()
    # Normalize unicode hyphens
    name_norm = name.replace("\u2011", "\u2011")  # keep non-breaking hyphens

    rule = SUBNATIONAL_RULES.get(name) or SUBNATIONAL_RULES.get(name_norm)
    if rule is None:
        # Try without measurement variants
        base = name.split("(")[0].strip() if "(" in name else name
        rule = SUBNATIONAL_RULES.get(base)

    if rule is None:
        stats["missing_rule"] += 1
        results.append({
            "excel_region": name,
            "parent_code": row.get("parent_polity_code", ""),
            "geometry": None,
            "quality_tier": 0,
            "source": "NO RULE DEFINED",
            "limitations": f"No extraction rule defined for '{name}'",
        })
        continue

    method, params, tier, limitations = rule
    geom = None
    source = ""

    if method == "cshapes":
        cs = find_cshapes(params)
        if cs is not None:
            geom = cs.geometry
            source = f"CShapes 2.0 ({cs['country_name']}, {cs['start_year']}-{cs['end_year']})"
        else:
            source = f"CShapes MISS: {params}"

    elif method == "cshapes_merge":
        geoms = []
        names_found = []
        for cs_name in params:
            cs = find_cshapes(cs_name)
            if cs is not None:
                geoms.append(cs.geometry)
                names_found.append(cs["country_name"])
        if geoms:
            geom = unary_union(geoms)
            source = f"CShapes 2.0 merged: {', '.join(names_found)}"
        else:
            source = f"CShapes MISS: {params}"

    elif method == "gadm0":
        geom = find_gadm0(params)
        source = f"GADM admin-0: {params}"

    elif method == "gadm0_merge":
        geoms = []
        names_found = []
        for iso in params:
            g = find_gadm0(iso)
            if g is not None:
                geoms.append(g)
                names_found.append(iso)
        if geoms:
            geom = unary_union(geoms)
            source = f"GADM admin-0 merged: {', '.join(names_found)}"
        else:
            source = f"GADM admin-0 MISS: {params}"

    elif method == "gadm1":
        g, matched = find_gadm1(params["iso"], params["states"])
        geom = g
        source = f"GADM admin-1: {params['iso']} [{', '.join(matched)}]"

    elif method == "gadm1_merge":
        g, matched = find_gadm1(params["iso"], params["states"])
        geom = g
        source = f"GADM admin-1 merged: {params['iso']} [{', '.join(matched)}]"

    elif method == "gadm2_merge":
        g, matched = find_gadm2(params["iso"], params["depts"])
        geom = g
        source = f"GADM admin-2 merged: {params['iso']} [{', '.join(matched)}]"

    elif method == "subtract_gadm1":
        # Full country polygon minus specific admin-1 regions
        base_geom = find_gadm0(params["iso"])
        sub_geom, sub_matched = find_gadm1(params["iso"], params["subtract"])
        if base_geom is not None and sub_geom is not None:
            geom = base_geom.difference(sub_geom)
            source = f"GADM admin-0 minus admin-1: {params['iso']} - [{', '.join(sub_matched)}]"
        else:
            source = f"GADM subtraction MISS: {params['iso']}"

    elif method == "cshapes_subtract":
        # CShapes base polygon minus CShapes other polygons
        base_cs = find_cshapes(params["base"])
        sub_geoms = []
        sub_names = []
        for cs_name in params["subtract"]:
            cs = find_cshapes(cs_name)
            if cs is not None:
                sub_geoms.append(cs.geometry)
                sub_names.append(cs["country_name"])
        if base_cs is not None and sub_geoms:
            geom = base_cs.geometry.difference(unary_union(sub_geoms))
            source = f"CShapes 2.0 subtracted: {base_cs['country_name']} - [{', '.join(sub_names)}]"
        else:
            source = f"CShapes subtraction MISS: {params}"

    elif method == "none":
        source = "No proxy available"

    tier_key = f"tier{tier}"
    stats[tier_key] = stats.get(tier_key, 0) + 1

    results.append({
        "excel_region": name,
        "parent_code": row.get("parent_polity_code", ""),
        "geometry": geom,
        "quality_tier": tier,
        "source": source,
        "limitations": limitations,
    })


# ── Summary ─────────────────────────────────────────────────────────

print(f"\nResults ({len(results)} subnational regions):")
print(f"  Tier 1 (historical boundary):     {stats['tier1']}")
print(f"  Tier 2 (good modern proxy):       {stats['tier2']}")
print(f"  Tier 3 (acceptable with caveats): {stats['tier3']}")
print(f"  Tier 4 (no good proxy):           {stats['tier4']}")
print(f"  No rule defined:                  {stats['missing_rule']}")

with_geom = sum(1 for r in results if r["geometry"] is not None)
print(f"\n  With geometry: {with_geom}/{len(results)}")

# ── Write outputs ───────────────────────────────────────────────────

# GeoPackage with subnational polygons
geo_results = [r for r in results if r["geometry"] is not None]
if geo_results:
    gdf = gpd.GeoDataFrame(
        [{k: v for k, v in r.items() if k != "geometry"} for r in geo_results],
        geometry=[r["geometry"] for r in geo_results],
        crs="EPSG:4326"
    )
    out_path = f"{BASE}/data/geodata/subnational_polygons.gpkg"
    gdf.to_file(out_path, layer="subnational", driver="GPKG")
    print(f"\n  Written {len(gdf)} polygons to subnational_polygons.gpkg")

# CSV report with all entries including tier and limitations
report = pd.DataFrame([{k: v for k, v in r.items() if k != "geometry"}
                        for r in results])
report["has_geometry"] = [r["geometry"] is not None for r in results]
report_path = f"{BASE}/data/analysis/subnational_report.csv"
report.to_csv(report_path, index=False)
print(f"  Written report to subnational_report.csv")

# Tier 4 entries (needing historical GIS)
tier4 = [r for r in results if r["quality_tier"] == 4]
if tier4:
    print(f"\n  Tier 4 entries needing historical GIS ({len(tier4)}):")
    for r in sorted(tier4, key=lambda x: x["excel_region"]):
        print(f"    {r['excel_region']:55s} {r['limitations'][:70]}")
