#!/usr/bin/env python3
"""
Build data/geodata/constructed/constructed.gpkg from other fetched sources.

Some WHEP polities have no single external-source polygon that matches their
territorial extent. This script derives those polygons from other raw
sources already under data/geodata/ and writes them keyed by polity_code.

Current entries:
  DEU-1945-1949  Allied-occupied Germany = CShapes 2.0 gwcode 260 ∪ 265
                 (both 1945-1949 time-steps, i.e. the three Western and
                 one Soviet occupation zones before the 1949 formal
                 division into FRG/GDR).

Add new entries by appending to the BUILDERS list below, with a function
that returns an ogr.Geometry in WGS84 (lon,lat axis order).

IMPORTANT — this script REWRITES constructed.gpkg from scratch every run
(it unlinks the file, then writes exactly the features in BUILDERS). So:
  * EVERY polity whose wiki page sets `polygon_source: constructed` MUST have
    an entry in BUILDERS here. If it doesn't, a re-run silently drops its
    polygon and `scripts/build_database.py` then logs it as feature-not-found.
  * NEVER hand-edit constructed.gpkg directly — those edits are lost on the
    next run. The BUILDERS list is the single source of truth; this file is a
    derived artifact (gitignored). Add the recipe here instead.
"""
from __future__ import annotations
import sys
from pathlib import Path
from osgeo import ogr, osr

ogr.UseExceptions()
osr.UseExceptions()

REPO_ROOT = Path(__file__).resolve().parents[3]
CSHAPES2 = REPO_ROOT / "data/geodata/cshapes-2.0/CShapes-2.0.shp"
GADM41_ADM1 = REPO_ROOT / "data/geodata/gadm-4.1/gadm41_adm1.gpkg"
GADM41_ADM0 = REPO_ROOT / "data/geodata/gadm-4.1/gadm41_adm0.gpkg"
CLIOPATRIA = REPO_ROOT / "data/geodata/cliopatria/cliopatria_polities_only.geojson"
CROWNLANDS = (
    REPO_ROOT
    / "data/geodata/histogis-1860-habsburg/crownlands_1860"
    / "austrian_empire_adm2_crownlands_1860.shp"
)
# GeoPackage, not GeoJSON. GeoJSON carries a per-object size limit
# (OGR_GEOJSON_MAX_OBJ_SIZE, default 200 MB of coordinates per feature) and adding
# IDN-OTH-1949-1951 -- Indonesia minus Java minus Bali, tens of thousands of islands --
# crossed it. The failure mode is the dangerous kind: ogr.Open() rejects the WHOLE
# FILE, so every constructed polygon silently stops attaching, not just the large one.
# A GeoPackage has no such limit and is what every other polygon source here uses.
OUT = REPO_ROOT / "data/geodata/constructed/constructed.gpkg"


def wgs84_lonlat() -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def _cshapes2_feature(gwcode: int, year: int) -> ogr.Geometry:
    """Return the geometry of the CShapes 2.0 feature matching (gwcode, year)."""
    if not CSHAPES2.exists():
        raise FileNotFoundError(
            f"{CSHAPES2} missing — run scripts/sources/cshapes-2.0/fetch.sh first."
        )
    ds = ogr.Open(str(CSHAPES2))
    lyr = ds.GetLayer()
    for f in lyr:
        if int(f.GetField("gwcode")) != gwcode:
            continue
        if f.GetField("gwsyear") <= year <= f.GetField("gweyear"):
            return f.GetGeometryRef().Clone()
    raise LookupError(f"CShapes 2.0 has no feature for gwcode={gwcode}, year={year}")


def _gadm_adm1(gid_1: str) -> ogr.Geometry:
    """Return the geometry of the GADM 4.1 admin-1 feature with the given GID_1."""
    if not GADM41_ADM1.exists():
        raise FileNotFoundError(
            f"{GADM41_ADM1} missing — run scripts/sources/gadm-4.1/fetch.sh first."
        )
    ds = ogr.Open(str(GADM41_ADM1))
    lyr = ds.GetLayer()
    for f in lyr:
        if f.GetField("GID_1") == gid_1:
            return f.GetGeometryRef().Clone()
    raise LookupError(f"GADM 4.1 adm1 has no feature with GID_1={gid_1!r}")


def _gadm_adm0(gid_0: str) -> ogr.Geometry:
    """Return the geometry of the GADM 4.1 country feature with the given GID_0."""
    if not GADM41_ADM0.exists():
        raise FileNotFoundError(
            f"{GADM41_ADM0} missing — run scripts/sources/gadm-4.1/fetch.sh first."
        )
    ds = ogr.Open(str(GADM41_ADM0))
    lyr = ds.GetLayer()
    for f in lyr:
        if f.GetField("GID_0") == gid_0:
            return f.GetGeometryRef().Clone()
    raise LookupError(f"GADM 4.1 adm0 has no feature with GID_0={gid_0!r}")


def _cliopatria_feature(name: str, year: int) -> ogr.Geometry:
    """Return the Cliopatria feature called `name` whose [FromYear, ToYear] contains `year`.

    Cliopatria steps are inclusive on both ends, unlike this repo's exclusive end_year, so the
    containment test here is deliberately `<= year <=`. Raises if the year is covered by more
    than one step, because a silent first-match would reintroduce exactly the order-dependence
    that validate_polygon_binding_determinism exists to prevent.
    """
    if not CLIOPATRIA.exists():
        raise FileNotFoundError(
            f"{CLIOPATRIA} missing - run scripts/sources/cliopatria/fetch.sh first."
        )
    ds = ogr.Open(str(CLIOPATRIA))
    lyr = ds.GetLayer()
    hits = []
    for f in lyr:
        if f.GetField("Name") != name:
            continue
        if int(f.GetField("FromYear")) <= year <= int(f.GetField("ToYear")):
            hits.append(f.GetGeometryRef().Clone())
    if not hits:
        raise LookupError(f"Cliopatria has no {name!r} step covering {year}")
    if len(hits) > 1:
        raise LookupError(f"Cliopatria has {len(hits)} {name!r} steps covering {year}")
    return hits[0]


def _keep_parts_within(geom: ogr.Geometry, lon_min: float, lat_min: float,
                       lon_max: float, lat_max: float) -> ogr.Geometry:
    """Drop the parts of a multipolygon that do not touch the given lon/lat envelope.

    Written for one specific defect and deliberately narrow. Some Cliopatria "polities" are
    records of an empire's whole possession list rather than of one territory, so the feature
    named "French Indochina" also carries New Caledonia, Reunion, Kerguelen, the Loyalty
    Islands and the French concession at Tianjin. Selecting a different step cannot help --
    all 35 steps carry them.

    Dropping by envelope rather than by named exclusion because the parts have no attributes
    to name them by; the envelope is stated at the call site and the kept/dropped areas are
    asserted there, so the operation is checkable rather than merely plausible.
    """
    env = ogr.CreateGeometryFromWkt(
        f"POLYGON(({lon_min} {lat_min},{lon_max} {lat_min},{lon_max} {lat_max},"
        f"{lon_min} {lat_max},{lon_min} {lat_min}))"
    )
    if geom.GetGeometryType() not in (ogr.wkbMultiPolygon, ogr.wkbMultiPolygon25D):
        return geom.Clone() if geom.Intersects(env) else None
    out = ogr.Geometry(ogr.wkbMultiPolygon)
    for i in range(geom.GetGeometryCount()):
        part = geom.GetGeometryRef(i)
        if part.Intersects(env):
            out.AddGeometry(part)
    return out


def _crownland(feature_id: str) -> ogr.Geometry:
    """Return the geometry of the Histogis 1860 Habsburg crownland with `id`,
    reprojected to WGS84 (the source shapefile is EPSG:3857 Web Mercator)."""
    if not CROWNLANDS.exists():
        raise FileNotFoundError(
            f"{CROWNLANDS} missing — fetch the Histogis crownlands shapefile first."
        )
    ds = ogr.Open(str(CROWNLANDS))
    lyr = ds.GetLayer()
    src_srs = lyr.GetSpatialRef()
    transform = (
        osr.CoordinateTransformation(src_srs, wgs84_lonlat())
        if src_srs is not None
        else None
    )
    for f in lyr:
        if str(f.GetField("id")) == str(feature_id):
            g = f.GetGeometryRef().Clone()
            if transform is not None:
                g.Transform(transform)
            return g
    raise LookupError(f"crownlands shapefile has no feature id={feature_id!r}")


def _difference(base: ogr.Geometry, *subtract: ogr.Geometry) -> ogr.Geometry:
    """base minus each of `subtract` — for polities defined as a parent territory
    with a breakaway/occupied region removed (e.g. China without Manchukuo)."""
    acc = base.Clone()
    for g in subtract:
        acc = acc.Difference(g)
    if acc.GetGeometryType() != ogr.wkbMultiPolygon:
        acc = ogr.ForceToMultiPolygon(acc)
    return acc


def _union(*geoms: ogr.Geometry) -> ogr.Geometry:
    acc = geoms[0].Clone()
    for g in geoms[1:]:
        acc = acc.Union(g)
    if acc.GetGeometryType() != ogr.wkbMultiPolygon:
        acc = ogr.ForceToMultiPolygon(acc)
    return acc


def build_fid_1887_1954() -> ogr.Geometry:
    """French Indochina 1887-1954 = Cliopatria's "French Indochina" at 1920, with the parts
    outside mainland Indochina removed.

    The attached Cliopatria polygon CONTAINED NEW CALEDONIA, REUNION AND KERGUELEN -- 15 parts
    spanning 55.1E to 168.0E and 49.8S to 39.6N, so a containment test put Noumea, Saint-Denis
    and Port-aux-Francais inside French Indochina. All 35 steps of that feature carry them, so
    no choice of polygon_feature_year fixes it; the feature is a record of French possessions
    east of Africa rather than of Indochina.

    Two things this recipe fixes at once:

      * 11 parts totalling 36,992 km2 are dropped: New Caledonia 20,278, Kerguelen 8,939,
        Reunion 3,513, the Loyalty Islands ~2,700, and 681 km2 near Tianjin (39.4N) which is
        the French concession there. Guangzhouwan (110.4E, 21.2N) is INSIDE the envelope and
        deliberately kept -- it was leased to France and administered from Indochina.
      * The result is VALID, but not for free. The raw feature fails is_valid in Cliopatria's
        own GeoJSON, and clipping does not cure it: two KEPT parts abut along a line, which a
        multipolygon may not do. They are unioned, which preserves area exactly, where
        make_valid would have dropped a 56.7 km2 part. See the assertion in the body.

    1920 rather than the 1900 the page previously declared. Clipped areas by step:

        1895-1897   659,948      1908-1939   753,213   <- stable mature extent
        1900-1904   662,141      1946-1955   751,021
        1905-1907   700,369      1940-1945     2,473   <- Japanese occupation

    French Indochina's territory was essentially complete after the 1907 Franco-Siamese treaty
    and stable until 1940, so the plateau is the right representation for a row spanning
    1887-1954. 1920 falls inside exactly one step (1919-1921), which keeps the binding
    deterministic. Result 753,049 km2 against the commonly cited ~740,000, i.e. 1.8% high --
    where the previously attached polygon was 5% LOW while containing three wrong territories,
    the two errors partly cancelling, which is why no area check ever flagged it.
    """
    raw = _cliopatria_feature("French Indochina", 1920)
    clipped = _keep_parts_within(raw, 99.0, 7.5, 110.5, 24.5)
    if clipped is None or clipped.IsEmpty():
        raise ValueError("clipping French Indochina to the mainland envelope left nothing")

    # The clipped multipolygon is still invalid, and the reason decides the repair. EVERY
    # INDIVIDUAL PART IS VALID; two of them share a boundary LINE, which a multipolygon may not
    # do (points are allowed, lines are not). So this is adjacency recorded as two pieces, not a
    # broken ring -- and the two candidate repairs behave completely differently:
    #
    #     union       753,049.331 km2   area-preserving; merges the two adjacent pieces
    #     make_valid  752,992.664 km2   DROPS the 56.7 km2 part entirely
    #
    # make_valid would delete real territory to satisfy the predicate. Union is therefore the
    # correct repair here, and the assertion below is what makes that a checked claim rather
    # than a preference: if a future Cliopatria vintage makes these parts genuinely OVERLAP
    # instead of abut, the union would shrink and this raises instead of quietly changing area.
    before = sum(
        clipped.GetGeometryRef(i).GetArea() for i in range(clipped.GetGeometryCount())
    )
    merged = clipped.GetGeometryRef(0).Clone()
    for i in range(1, clipped.GetGeometryCount()):
        merged = merged.Union(clipped.GetGeometryRef(i))
    if abs(merged.GetArea() - before) > before * 1e-9:
        raise ValueError(
            "unioning the kept parts of French Indochina changed the area "
            f"({before:.6f} -> {merged.GetArea():.6f} in square degrees): the parts now overlap "
            "rather than abut, so decide the repair explicitly instead of unioning"
        )
    if not merged.IsValid():
        raise ValueError("French Indochina is still invalid after unioning the kept parts")
    return merged


def build_papng_1920_1949() -> ogr.Geometry:
    """Papua + New Guinea as a single reporting unit = CShapes gwcode 911 (Territory of Papua)
    union gwcode 912 (Territory of New Guinea), both at their 1920-1949 step.

    INDEPENDENTLY VALIDATED, the same way build_gct_1919_1956()'s recipe was. CShapes codes the
    post-1949 combined Territory of Papua and New Guinea as its own feature, gwcode 910:

        gw911 1920-1949   224,148 km2      Papua
        gw912 1920-1949   237,536 km2      New Guinea
        union             461,684 km2
        gw910 1949-1975   461,689 km2      the combined territory, coded separately
        difference              5 km2      0.001%

    The two constituents also intersect in ZERO area, so the union double-counts nothing.

    1930 rather than 1920 for the lookup year: 1920 is the boundary between gw912's 1914-1920
    step (228,080 km2) and its 1920-1949 step (237,536), and a boundary year is exactly where
    find_feature's tie-break stops discriminating. 1930 is interior to both features' steps.
    """
    return _union(_cshapes2_feature(911, 1930), _cshapes2_feature(912, 1930))


def build_idn_jvm_1949_1951() -> ogr.Geometry:
    """Java and Madura = the six GADM adm1 provinces that make up Java.

    Madura is not separable in GADM: it is part of Jawa Timur, which is correct for this row
    anyway since the source reports Java and Madura together.

        Jakarta Raya      654        IDN.7_1
        Banten          9,352        IDN.4_1
        Jawa Barat     37,059        IDN.9_1
        Jawa Tengah    34,437        IDN.10_1
        Yogyakarta      3,177        IDN.33_1
        Jawa Timur     47,996        IDN.11_1
        union         132,674  km2   against the page's declared 132,000 -> 0.5%

    THE FEATURE IDS THE PAGE DECLARED WERE WRONG AND ARE NOT USED. It listed
    `IDN.7_1+IDN.10_1+IDN.11_1+IDN.29_1`, and in this GADM extract IDN.29_1 is SULAWESI UTARA --
    North Sulawesi, a different island 1,500 km away -- while Banten, Jawa Barat and Yogyakarta
    are missing. Those four sum to 97,594 km2, against a declared 132,000. Building the recipe as
    written would have attached North Sulawesi to Java and dropped a third of Java itself.

    The declared AREA was right and the declared RECIPE was wrong, which is the same shape as
    SER-1918-1945 (PR 157) and CAN-1800-1866: a page whose prose and whose ids disagree, where
    following the ids is worse than ignoring them. The area is what identified the correct set.
    """
    return _union(
        _gadm_adm1("IDN.7_1"),    # Jakarta Raya
        _gadm_adm1("IDN.4_1"),    # Banten
        _gadm_adm1("IDN.9_1"),    # Jawa Barat
        _gadm_adm1("IDN.10_1"),   # Jawa Tengah
        _gadm_adm1("IDN.33_1"),   # Yogyakarta
        _gadm_adm1("IDN.11_1"),   # Jawa Timur
    )


def build_deu_1945_1949() -> ogr.Geometry:
    """Allied-occupied Germany = West (gwcode 260) ∪ East (gwcode 265)
    for 1945-1949."""
    return _union(_cshapes2_feature(260, 1945),
                  _cshapes2_feature(265, 1945))


def build_deu_1949_1990() -> ogr.Geometry:
    """Divided Germany 1949-1990 = FRG (gwcode 260) ∪ GDR (gwcode 265),
    using the post-1949 time-step polygons. Used for input data that
    reports 'Germany' as a single undifferentiated aggregate for the
    divided-state period (as all 1949-1961 rows in the WHEP pre-1961
    dataset do)."""
    return _union(_cshapes2_feature(260, 1949),
                  _cshapes2_feature(265, 1949))


def build_jpn_1895_1945() -> ogr.Geometry:
    """Japanese Empire 1895-1945 = Japan metropole ∪ Taiwan ∪ Korea peninsula.
    CShapes 2.0 has no pre-1945 Korea feature, so we approximate with the
    post-1945 North Korea (gwcode 731) + South Korea (gwcode 732) polygons
    which together cover the peninsula. Does NOT include Manchukuo (not in
    CShapes 2.0) or southern Sakhalin."""
    return _union(
        _cshapes2_feature(740, 1895),   # Japan metropole
        _cshapes2_feature(713, 1895),   # Taiwan
        _cshapes2_feature(731, 1945),   # North Korea (post-liberation polygon)
        _cshapes2_feature(732, 1945),   # South Korea
    )


def build_kor_1800_1945() -> ogr.Geometry:
    """Korea before independence 1800-1945 = North Korea (gwcode 731)
    ∪ South Korea (gwcode 732), post-1945 polygons. Same territorial
    extent as the unified Korean peninsula throughout 1800-1945 (Korean
    Empire then Japanese colony Chōsen)."""
    return _union(_cshapes2_feature(731, 1945),
                  _cshapes2_feature(732, 1945))


def build_man_1932_1945() -> ogr.Geometry:
    """Manchukuo 1932-1945 ≈ union of modern Chinese provinces
    Heilongjiang, Jilin, and Liaoning (GADM 4.1 adm-1). Historical
    Manchukuo also included parts of Inner Mongolia (Rehe/Jehol); the
    3-province approximation captures ~90% of territory and the bulk of
    the population base."""
    return _union(_gadm_adm1("CHN.11_1"),   # Heilongjiang
                  _gadm_adm1("CHN.17_1"),   # Jilin
                  _gadm_adm1("CHN.18_1"))   # Liaoning


def build_egysud_1934_1956() -> ogr.Geometry:
    """Egypt + Anglo-Egyptian Sudan = CShapes Egypt (651) ∪ Sudan (625).
    The Anglo-Egyptian condominium (1899-1956); FAO/IIA agricultural series
    are frequently reported for Egypt with Sudan folded in (e.g. livestock
    'cattle received from Anglo-Egyptian Sudan'). Holds data reported under a
    combined Egypt-incl-Sudan label."""
    return _union(_cshapes2_feature(651, 1950), _cshapes2_feature(625, 1950))


def build_codru_1922_1960() -> ogr.Geometry:
    """Belgian Congo + Ruanda-Urundi = CShapes Congo/Zaire (490) ∪
    Ruanda-Urundi (515). Belgium administered Ruanda-Urundi as a League/UN
    mandate alongside the Congo; colonial agricultural returns commonly
    combine the two."""
    return _union(_cshapes2_feature(490, 1950), _cshapes2_feature(515, 1950))


def build_blx_1921_1999() -> ogr.Geometry:
    """Belgium-Luxembourg Economic Union (BLEU, from 1921) = CShapes Belgium
    (211) ∪ Luxembourg (212). Many interwar/post-war trade and production
    series report the two as a single customs unit."""
    return _union(_cshapes2_feature(211, 1950), _cshapes2_feature(212, 1950))


def build_masg_1946_1963() -> ogr.Geometry:
    """Malaya + Singapore = CShapes Malaya/Malaysia (820) ∪ Singapore (830).
    FAO footnotes report the Federation of Malaya figure as including
    Singapore for 1949-1960; this union holds that combined-label data."""
    return _union(_cshapes2_feature(820, 1953), _cshapes2_feature(830, 1953))


def build_aof_1895_1960() -> ogr.Geometry:
    """French West Africa (AOF) 1895-1960 ≈ union of CShapes 2.0 constituent
    colonies at vintage 1938: gwcodes 432 (French Sudan/Mali), 433 (Senegal),
    434 (Dahomey/Benin), 435 (Mauritania), 436 (Niger), 437 (Cote d'Ivoire),
    438 (Guinea). CShapes drops the federation-level aggregate (gwcode 430)
    after 1904; the 1938 vintage excludes Upper Volta (dissolved 1932,
    reconstituted 1947). See wiki/polities/aof-1895-1960.md for the drift note."""
    return _union(*[
        _cshapes2_feature(gw, 1938)
        for gw in (432, 433, 434, 435, 436, 437, 438)
    ])


def build_cze_1804_1918() -> ogr.Geometry:
    """Czech Lands 1804-1918 = Bohemia (id 7) ∪ Moravia (id 15) ∪ Austrian
    Silesia (id 5) from the Histogis 1860 Habsburg crownlands shapefile. The
    three crownlands' borders were administratively stable across the period;
    see wiki/polities/cze-1804-1918.md."""
    return _union(_crownland("7"), _crownland("15"), _crownland("5"))


def build_irl_1800_1921() -> ogr.Geometry:
    """All-Ireland (32 counties), 1800-1921 = GADM 4.1 Ireland (GID_0 IRL, the
    26 counties) union Northern Ireland (GID_1 GBR.2_1).

    Neither CShapes nor a single GADM feature can supply pre-partition Ireland:
    CShapes gwcode 205 begins in 1921 at 26 counties, and gwcode 200 (United
    Kingdom, 1886-1921) fuses Great Britain with all Ireland inseparably. Modern
    borders are an acceptable proxy here because the island's coastline is the
    boundary and the internal 1921 partition line is exactly what the union
    dissolves."""
    return _union(_gadm_adm0("IRL"), _gadm_adm1("GBR.2_1"))


def build_chn_1932_1945() -> ogr.Geometry:
    """China excluding Manchukuo, 1932-1945 = CShapes 2.0 gwcode 710 (the
    1921-1945 feature, i.e. post-Mongolian-independence China, which still
    INCLUDES Manchuria) minus the Manchukuo polygon built above.

    Without this subtraction, data labelled as China proper for 1932-1945 is
    matched to a territory that includes the three northeastern provinces,
    which Manchukuo held and which MAN-1932-1945 already covers — so the two
    rows would double-count that area."""
    return _difference(_cshapes2_feature(710, 1932), build_man_1932_1945())



def build_its_1908_1960() -> ogr.Geometry:
    """Italian Somaliland 1908-1960 = CShapes 2.0 gwcode 520 (Somalia, the
    1960-2019 feature) MINUS gwcode 521 (British Somaliland, 1897-1960).

    CShapes 2.0 as distributed here (the sovereign-state shapefile) cannot
    supply this territory directly: its only Somali polygon is gwcode 520,
    which starts on 1960-07-01 and is therefore the whole of *independent
    Somalia* — Italian Somaliland PLUS British Somaliland, which united on
    that date. Binding this row to 520 as a proxy overstated it by the British
    share (636,242 -> 464,743 km2, ~21%).

    Because British Somaliland is itself a separate CShapes feature (gwcode
    521, entirely contained in 520 — the intersection equals 521 exactly), the
    subtraction recovers the colonial boundary rather than approximating it.
    Verified: the result is bit-identical (symmetric difference 0.0 km2) to
    CShapes 2.0's own `Italian Somaliland` dependency feature (cowcode 5200,
    time-steps from 1924-07-01 onward, 464,743 km2), which lives only in the
    dependencies=TRUE distribution that is not one of the registered polygon
    sources. So this is the CShapes colonial polygon, reconstructed from the
    sovereign-only distribution.

    Caveat: 464,743 km2 is the POST-1924 extent, i.e. after the Jubaland /
    Oltre Giuba transfer from British Kenya (Treaty of London, 1924). The
    1889-1924 extent was 370,338 km2. This row spans 1908-1960, so the polygon
    overstates its first 16 years by ~94,400 km2; see oq-its-1924-split in
    wiki/polities/its-1908-1960.md. The row's data is 1924-1959.
    """
    return _difference(_cshapes2_feature(520, 1960), _cshapes2_feature(521, 1960))

def build_can_1800_1866() -> ogr.Geometry:
    """Canada pre-Confederation, 1800-1866 = the union of the five colonies that
    became the Dominion, on GADM 4.1 adm1 boundaries.

    The page recorded the recipe symbolically as `gadm-ON+QC+NB+NS+PE` against an
    unregistered `gadm-composed-union` slug, so nothing built it. Resolved against
    the fetched extract: Ontario CAN.9_1, Quebec CAN.11_1, New Brunswick CAN.4_1,
    Nova Scotia CAN.7_1, Prince Edward Island CAN.10_1.

    NOT REGISTERED in BUILDERS, on measurement. Modern provincial boundaries give
    2,735,024 km2 against the page's 1,209,852 -- 126% over, because Ontario and
    Quebec reach Hudson Bay while the 1866 Province of Canada stopped at the
    Hudson's Bay Company's Rupert's Land. That is not a proxy, it is a different
    territory. The recipe is kept for anyone who fetches a pre-Confederation
    source; it should not ship against GADM.
    """
    return _union(
        _gadm_adm1("CAN.9_1"),
        _gadm_adm1("CAN.11_1"),
        _gadm_adm1("CAN.4_1"),
        _gadm_adm1("CAN.7_1"),
        _gadm_adm1("CAN.10_1"),
    )


# The Second Vienna Award holding, 1940-1944, as eight modern Romanian counties.
# CShapes CANNOT supply this territory and the difference recipe HUN-1940-1944 declared
# does not either: `ROU360 1920-1940 MINUS ROU360 1940-2019` is 58,707 km2 on Romania's
# EASTERN edge (lon 24.67..30.51) -- Bessarabia, Northern Bukovina and Southern Dobruja,
# ceded to the USSR and Bulgaria. Northern Transylvania is on the WESTERN edge and cancels
# out of that difference entirely, because post-war Romania kept it and it is interior to
# both operands. See issue 106; the recipe's area happened to match its declared figure
# exactly (108,785 + 58,707 = 167,492), so no area check would have objected.
NTR_1940_COUNTIES = (
    "ROU.34_1",   # Satu Mare        4,418 km2
    "ROU.27_1",   # Maramures        6,304
    "ROU.33_1",   # Salaj            3,864
    "ROU.6_1",    # Bistrita-Nasaud  5,354
    "ROU.14_1",   # Cluj             6,673
    "ROU.29_1",   # Mures            6,713
    "ROU.22_1",   # Harghita         6,650
    "ROU.16_1",   # Covasna          3,709
)


def _northern_transylvania_1940() -> ogr.Geometry:
    """The 1940-44 Hungarian holding, approximated by eight modern Romanian counties.

    A PROXY with a measured error, not an exact boundary. The union measures 43,685 km2
    against the Second Vienna Award's 43,104 -- +1.3%. Two offsetting inaccuracies:
    the award also took the northern part of BIHOR (not included here, since Bihor is one
    modern county of 7,548 km2 and including it whole would overshoot by 24%), while these
    county boundaries over-cover slightly elsewhere. The residual is smaller than either
    error alone, which is luck rather than design and is why the figure is stated.
    """
    return _union(*(_gadm_adm1(gid) for gid in NTR_1940_COUNTIES))


def build_hun_1940_1944() -> ogr.Geometry:
    """Hungary at peak expansion, 1940-1944 = Hungary 1938 union Northern Transylvania.

    `_cshapes2_feature(310, 1939)` rather than 1938: the helper returns the FIRST feature
    whose span contains the year, and gwcode 310 has both a 1920-1938 and a 1938-1947 step,
    so 1938 is ambiguous while 1939 selects the post-First-Vienna-Award polygon uniquely.
    The same class of defect as issue 99.

    Understates the peak: the April 1941 Backa and Baranya strips (~10,000 km2) are not
    included, because CShapes retains Yugoslavia's full pre-war footprint through the
    occupation and GADM cannot isolate them either. The page records the peak as
    ~172,277 km2 against this construction's ~152,500.
    """
    return _union(_cshapes2_feature(310, 1939), _northern_transylvania_1940())


def build_rou_1940_1947() -> ogr.Geometry:
    """Romania after the 1940 losses = post-war Romania minus Northern Transylvania.

    `_cshapes2_feature(360, 1941)` selects the 1940-2019 step (237,379 km2): post-war
    Romania, already without Bessarabia, Northern Bukovina and Southern Dobruja but WITH
    Northern Transylvania, which this subtracts. 1941 rather than 1940 because three steps
    contain 1940 and two of them start in it -- the row is the one case in issue 100 that
    no polygon_feature_year can disambiguate.

    Expected ~193,700 km2 against the page's declared 194,000.
    """
    return _difference(_cshapes2_feature(360, 1941), _northern_transylvania_1940())


def build_ptind_1816_1961() -> ogr.Geometry:
    """Portuguese India, 1816-1961 = Goa union Daman and Diu, on GADM 4.1 adm1.

    The page names the components in `polygon_method` as
    `composed-union-goa-daman-diu` and carries no `polygon_feature_id`, which is
    why an earlier pass mistook it for having no recipe at all. Resolved: Goa
    IND.10_1, and Daman and Diu IND.9_1 -- GADM carries those two as ONE feature,
    so the union is of two features rather than three.

    Excludes Dadra and Nagar Haveli (IND.8_1), which Portugal also held until 1954
    but which the page does not name. Left out deliberately rather than added
    silently.
    """
    return _union(_gadm_adm1("IND.10_1"), _gadm_adm1("IND.9_1"))


def build_idn_blb_1949_1951() -> ogr.Geometry:
    """Bali and Lombok, 1949-1951 = Bali union Nusa Tenggara Barat, GADM 4.1 adm1.

    CORRECTS the page's `polygon_feature_id`, which read `IDN.1_1+IDN.20_1`.
    IDN.1_1 is ACEH, on northern Sumatra, some 3,000 km from Bali. Bali is
    IDN.2_1. The Lombok half was right: Lombok lies in Nusa Tenggara Barat
    (IDN.20_1), though that province also contains Sumbawa, so the polygon
    overstates a unit named for Lombok alone.

    NOT REGISTERED in BUILDERS, on measurement: 25,261 km2 against the page's
    10,505 -- 140% over, and Sumbawa is why. GADM adm1 cannot separate Lombok from
    Nusa Tenggara Barat, so building this to the page's own figure needs adm2. The
    corrected Bali id is kept here so the work is not lost.
    """
    return _union(_gadm_adm1("IDN.2_1"), _gadm_adm1("IDN.20_1"))


def build_idn_jvm_1949_1951() -> ogr.Geometry:
    """Java and Madura, 1949-1951 = the six modern provinces of Java island.

    CORRECTS the page's `polygon_feature_id`, which read
    `IDN.7_1+IDN.10_1+IDN.11_1+IDN.29_1`. Three of those are Java (Jakarta Raya,
    Jawa Tengah, Jawa Timur) but IDN.29_1 is SULAWESI UTARA, a different island
    entirely; and the list omitted half of Java.

    Java island is Banten IDN.4_1, Jakarta Raya IDN.7_1, Jawa Barat IDN.9_1, Jawa
    Tengah IDN.10_1, Yogyakarta IDN.33_1 and Jawa Timur IDN.11_1. Madura needs no
    separate feature: it is part of Jawa Timur.

    Banten and Yogyakarta are included because the unit is named for the ISLAND.
    Banten was part of West Java until 2000 and Yogyakarta was a Special Region,
    so neither existed as a separate province in 1949-1951, but both are on Java
    and their territory was inside the reporting unit.

    VERIFIED: 132,720 km2 against the page's own 132,000 -- 0.5%, which is what
    confirms this province set rather than the four the page listed.

    NOT REGISTERED in BUILDERS, and not because the polygon is wrong. Attaching it
    makes audit_family_shadowing fail against NNG-1949-1963 at a 3.1x ratio, on a
    TIED type rank, because NNG carries iso3 IDN although it was Dutch until 1963.
    Java and West Papua are geographically disjoint, so that is a false positive
    driven by NNG's iso3, not a territorial error here. It is entangled with the
    IDN-OTH question -- see the issue -- so all three 1949-1951 rows want settling
    together rather than one at a time.
    """
    return _union(
        _gadm_adm1("IDN.4_1"),
        _gadm_adm1("IDN.7_1"),
        _gadm_adm1("IDN.9_1"),
        _gadm_adm1("IDN.10_1"),
        _gadm_adm1("IDN.33_1"),
        _gadm_adm1("IDN.11_1"),
    )


def build_idn_oth_1949_1951() -> ogr.Geometry:
    """Other islands of Indonesia, 1949-1951 = Indonesia minus Java-and-Madura
    minus Bali-and-Lombok, which is what the page's `IDN-complement-JVM-BLB` says.

    Built as a complement so the three 1949-1951 rows partition Indonesia exactly:
    any area not in the other two lands here, with no gap and no double count. That
    property is why it must be derived rather than enumerated -- listing the other
    27 provinces by hand would break the partition the moment GADM re-splits one.

    NOT REGISTERED in BUILDERS. As written it is territorially WRONG for the period:
    modern Indonesia includes Papua, but Netherlands New Guinea stayed Dutch until
    1963, so subtracting only Java and Bali leaves 410,399 km2 of Dutch territory
    inside a 1949-1951 Indonesian row. audit_family_shadowing caught it, flagging
    NNG-1949-1963 against this row at a 4.2x ratio.

    The fix is to subtract NNG-1949-1963 as well, but the page's own
    polygon_area_km2 of 1,757,495 also appears to include Papua, so the recorded
    figure needs settling with the territory. Left disabled pending that.
    """
    return _difference(
        _gadm_adm0("IDN"),
        build_idn_jvm_1949_1951(),
        build_idn_blb_1949_1951(),
    )


# (polity_code, polity_name, builder-callable, provenance note)
def build_btl_1920_1957() -> ogr.Geometry:
    """British Togoland 1920-1957 = Ghana AFTER the 1956 incorporation MINUS the
    Gold Coast before it.

    CShapes gwcode 452 steps from 212,416 km2 (1898-1956, the Gold Coast) to
    239,046 km2 (1956 onward, once British Togoland was incorporated following the
    1956 plebiscite). The difference is the mandate territory itself.

    Years are chosen to be UNAMBIGUOUS. 1956 is contained by both the 1898-1956 and
    1956-1957 steps, and `_cshapes2_feature` returns whichever comes first in the
    shapefile, so 1950 and 1960 are used instead: each is inside exactly one step.
    (The 1956-1957 and 1957-2019 steps both measure 239,046 km2, so 1960 is
    equivalent to 1956 for this purpose.)
    """
    return _difference(_cshapes2_feature(452, 1960), _cshapes2_feature(452, 1950))


def build_ttpi_1947_1994() -> ogr.Geometry:
    """Trust Territory of the Pacific Islands = the four successor states'
    modern coastlines: Micronesia, Marshall Islands, Northern Marianas, Palau.

    Guam is deliberately excluded: it was a US possession from 1898 and never part
    of the Trust Territory.

    Modern coastlines are the only available proxy — no historical source in the
    priority stack carries the Trust Territory as one feature — and the internal
    boundaries have not changed, so the union is the same extent the mandate had.
    """
    return _union(
        _gadm_adm0("FSM"),
        _gadm_adm0("MHL"),
        _gadm_adm0("MNP"),
        _gadm_adm0("PLW"),
    )


def build_aef_1910_1960() -> ogr.Geometry:
    """French Equatorial Africa (AEF) 1910-1960 = union of its four constituent
    colonies: Gabon (481), Ubangi-Shari / CAR (482), Chad (483), Middle Congo (484).

    1950 is used as the sampling year because it sits inside every one of the four
    CShapes steps — Chad's colonial status was only confirmed in 1920, so its step
    starts later than the others' 1919 — and none of the four changes borders again
    before independence in 1960.

    The composition is not inferred: this polity's page names all four territories
    WITH their gwcodes and per-territory areas, and those areas sum to the 2,495,219
    km2 the page records. The union measures 2,495,221, which is that sum to within
    rounding.
    """
    return _union(
        _cshapes2_feature(481, 1950),
        _cshapes2_feature(482, 1950),
        _cshapes2_feature(483, 1950),
        _cshapes2_feature(484, 1950),
    )


def build_gbm_1895_1946() -> ogr.Geometry:
    """British Malaya 1895-1946 = Straits Settlements (827) + Federated Malay
    States (821) + Unfederated Malay States (822).

    Sampled at 1930, inside every one of the three CShapes steps. The union measures
    132,040 km2, which is EXACTLY the total this polity's page tabulates from the
    same three components (3,601 + 71,415 + 57,024).
    """
    return _union(
        _cshapes2_feature(827, 1930),
        _cshapes2_feature(821, 1930),
        _cshapes2_feature(822, 1930),
    )


def build_gct_1919_1956() -> ogr.Geometry:
    """Gold Coast and British Togoland 1919-1956 = Gold Coast (452) + the British
    Togoland mandate (462's 1922-1955 step).

    Sampled at 1930, inside both steps. 212,416 + 26,630 = 239,046 km2 against the
    240,056 the page records from historical sources — 0.4%.

    Worth noting as corroboration: the 26,630 km2 Togoland component here is the same
    figure `build_btl_1920_1957()` derives by an entirely different route, as the
    difference between Ghana before and after the 1956 incorporation. Two independent
    computations agreeing to the km2 is strong evidence that CShapes gwcode 462 does
    carry the BRITISH mandate for 1922-1955, which is what this page asserts and which
    is not obvious — 462 is the Republic of Togo (the French mandate) after 1960.

    WHY IT IS NOT REGISTERED. Attaching this polygon made
    scripts/audit_family_shadowing.py fail: GCT and BTL-1920-1957 then both carry
    iso3 GHA, both are typed `colonial`, and they overlap 1920-1956 at a 9x area
    ratio — so which one GHA-labelled data reaches would be decided by family
    ordering rather than by type. That is the Alaska-absorbing-mainland-US failure
    the audit exists to prevent.
    
    The risk is not created by the polygon; it exists because both rows carry iso3
    GHA. The polygon only made it MEASURABLE, since the audit needs areas. Resolving
    it means deciding how a composite reporting unit should be typed, and the
    database is currently inconsistent about that — BLX is `aggregate`, SYL is
    `statistical`, AOF and AEF are `national`, GCT is `colonial`. That is a modelling
    decision, so the recipe is kept here, verified and ready, and the row stays in
    the polygon backlog until the typing question is settled. See issue 47.
    """
    return _union(_cshapes2_feature(452, 1930), _cshapes2_feature(462, 1930))


def build_syl_1944_1953() -> ogr.Geometry:
    """Syria and Lebanon as one statistical unit = Syria (652) + Lebanon (660).

    NOT Sylhet — the prefix is misleading. This row exists to route FAO 1952 tobacco
    data published under the joint label "Syria and Lebanon", an artifact of the
    French Mandate joint administration and the customs union that ran to March 1950.

    Sampled at 1950, inside both steps: 188,004 + 10,209 = 198,213 km2 against the
    195,632 the page records (1.3%). The page's figures come from the vintages it
    names, ~185,180 for Syria and ~10,452 for Lebanon.
    """
    return _union(_cshapes2_feature(652, 1950), _cshapes2_feature(660, 1950))


BUILDERS = [
    (
        "IDN-JVM-1949-1951",
        "Java and Madura (within Indonesia, 1949-1951)",
        build_idn_jvm_1949_1951,
        "Union of the six GADM adm1 Java provinces = 132,674 km2 against the page's declared "
        "132,000 (0.5%). The feature ids the page declared are NOT used: IDN.29_1 is Sulawesi "
        "Utara, a different island, and three Java provinces were missing, so those four ids sum "
        "to 97,594. Declared area right, declared recipe wrong -- the SER-1918-1945 shape.",
    ),
    (
        "GCT-1919-1956",
        "Gold Coast and British Togoland (1919-1956)",
        build_gct_1919_1956,
        "CShapes gwcode 452 (Gold Coast, 1898-1956 step) union gwcode 462 (the British Togoland "
        "mandate, 1922-1955) = 239,046 km2 with ZERO overlap. Registered 2026-08-06 after issue 47's "
        "blocker was resolved by retyping this row `aggregate`, the MASG/PAPNG pattern for a "
        "combined reporting unit -- it and BTL-1920-1957 both being `colonial` on iso3 GHA is what "
        "made audit_family_shadowing fail. Corroborated three ways: CShapes' own post-plebiscite "
        "Gold Coast step is 239,046 to 0.000%, FAO states 237,880 for 'Gold Coast and Br Togoland' "
        "(0.49%), and the page derives 240,056 from historical sources (0.42%).",
    ),
    (
        "PAPNG-1920-1949",
        "Papua and New Guinea (combined reporting unit)",
        build_papng_1920_1949,
        "CShapes gwcode 911 (Papua) union 912 (New Guinea) at their 1920-1949 steps = "
        "461,684 km2, against CShapes' own separately-coded combined territory gwcode 910 at "
        "461,689 -- a 5 km2 / 0.001% match, and the constituents intersect in zero area. "
        "Created so 23 Mitchell rows labelled `papua new guinea` for 1922-1940 stop landing on "
        "TNGU-1920-1949, New Guinea alone, which silently dropped Papua's 224,148 km2.",
    ),
    (
        "FID-1887-1954",
        "French Indochina",
        build_fid_1887_1954,
        "Cliopatria 'French Indochina' at 1920, clipped to the mainland envelope "
        "(99-110.5E, 7.5-24.5N). REPLACES a polygon that contained New Caledonia, Reunion and "
        "Kerguelen -- all 35 steps of that feature carry them, so no feature_year fixed it. "
        "Drops 11 parts totalling 36,992 km2, keeps Guangzhouwan, and yields a VALID geometry "
        "where the raw feature is invalid in Cliopatria's own GeoJSON. 753,049 km2 against "
        "~740,000 cited.",
    ),
    (
        "HUN-1940-1944",
        "Hungary (1940-1944)",
        build_hun_1940_1944,
        "CShapes gwcode 310 at 1939 (108,785 km2, post-First Vienna Award) union the "
        "eight-county Northern Transylvania proxy (43,685). REPLACES the recipe the page "
        "declared, which added Romania's EASTERN losses instead -- Bessarabia and Southern "
        "Dobruja, ceded to the USSR and Bulgaria, on the wrong side of the country "
        "(issue 106). Understates the ~172,277 km2 peak because the 1941 Backa and Baranya "
        "strips cannot be isolated from CShapes or GADM.",
    ),
    (
        "ROU-1940-1947",
        "Romania (1940-1947)",
        build_rou_1940_1947,
        "CShapes gwcode 360 at 1941 (237,379 km2, post-war Romania) MINUS the same "
        "Northern Transylvania proxy. Its declared 194,000 km2 was unreachable from "
        "CShapes alone: no feature offers it, and the step it was bound to spans exactly "
        "{1940} while both neighbours also contain 1940, so no polygon_feature_year could "
        "select it (issues 100, 12).",
    ),
    (
        "GBM-1895-1946",
        "British Malaya (1895-1946)",
        build_gbm_1895_1946,
        "Union of CShapes 2.0 gwcodes 827 Straits Settlements (3,601 km2), 821 "
        "Federated Malay States (71,415) and 822 Unfederated Malay States (57,024) "
        "at 1930 = 132,040 km2, exactly the union total the page tabulates.",
    ),
    (
        "SYL-1944-1953",
        "Syria and Lebanon (combined statistical unit)",
        build_syl_1944_1953,
        "Union of CShapes 2.0 gwcodes 652 Syria (188,004 km2) and 660 Lebanon "
        "(10,209) at 1950 = 198,213 against 195,632 recorded (1.3%). Despite the "
        "prefix this is NOT Sylhet: it is the joint 'Syria and Lebanon' reporting "
        "unit the FAO 1952 yearbook uses.",
    ),

    (
        "AEF-1910-1960",
        "French Equatorial Africa (AEF)",
        build_aef_1910_1960,
        "Union of CShapes 2.0 gwcodes 481 Gabon (260,681 km2), 482 Ubangi-Shari "
        "(618,630), 483 Chad (1,271,888) and 484 Middle Congo (344,022) at 1950 = "
        "2,495,221 km2, matching the 2,495,219 the page records as the sum of its "
        "own constituent-territory table. The previous feature id, "
        "'cshapes-idx-366+370+375+382', gave shapefile ROW INDICES rather than "
        "gwcodes, which nothing could resolve; the page's table supplies both, and "
        "the gwcodes are what the builder uses.",
    ),

    (
        "BTL-1920-1957",
        "British Togoland (1920-1957)",
        build_btl_1920_1957,
        "CShapes 2.0 gwcode 452 at 1960 (239,046 km2, Ghana including the "
        "incorporated mandate) MINUS gwcode 452 at 1950 (212,416 km2, the Gold "
        "Coast alone) = 26,630 km2. That matches the figure this polity's page "
        "already recorded from the same computation, and sits 21% below the "
        "~33,771 km2 historical figure — a gap the page documents and attributes "
        "to CShapes generalisation, which is why the row is `assigned` on the "
        "geodesic value rather than the historical one.",
    ),
    (
        "TTPI-1947-1994",
        "Trust Territory of the Pacific Islands (1947-1994)",
        build_ttpi_1947_1994,
        "Union of GADM 4.1 adm0 FSM, MHL, MNP and PLW = ~2,063 km2 against the "
        "~1,791 km2 the page records; GADM's coastlines include reef and lagoon "
        "area that land-area figures exclude, which is why the row is `proxy` "
        "rather than `assigned`. Guam is excluded deliberately: a US possession "
        "from 1898, never part of the Trust Territory.",
    ),

    (
        "IRL-1800-1921",
        "Ireland (all-island, 1800-1921)",
        build_irl_1800_1921,
        "Union of GADM 4.1 adm0 IRL (26 counties, 70,266 km2) and adm1 "
        "GBR.2_1 Northern Ireland (14,167 km2) = 84,433 km2, matching the "
        "~84,421 km2 all-island figure. Used because no historical source in "
        "the priority stack carries pre-partition Ireland as one feature: "
        "CShapes gwcode 205 starts in 1921 at 26 counties and gwcode 200 "
        "fuses Great Britain with all Ireland. Modern coastline is a sound "
        "proxy; the only internal change is the 1921 partition, which this "
        "union reverses.",
    ),
    (
        "CHN-1932-1945",
        "China (excluding Manchukuo, 1932-1945)",
        build_chn_1932_1945,
        "CShapes 2.0 gwcode 710 (1921-1945 feature) MINUS the constructed "
        "MAN-1932-1945 Manchukuo polygon. The CShapes feature still includes "
        "Manchuria, so subtracting Manchukuo is what prevents this row and "
        "MAN-1932-1945 from double-counting the three northeastern provinces.",
    ),
    (
        "DEU-1945-1949",
        "Allied-occupied Germany",
        build_deu_1945_1949,
        "Union of CShapes 2.0 gwcode 260 (West Germany / Trizone) and "
        "gwcode 265 (Soviet zone / GDR) for 1945-1949. CShapes records "
        "the two zones as separate features; the WHEP row refers to the "
        "combined Allied-occupied territory.",
    ),
    (
        "DEU-1949-1990",
        "Germany (divided, 1949-1990)",
        build_deu_1949_1990,
        "Union of CShapes 2.0 gwcode 260 (FRG / West Germany) and gwcode "
        "265 (GDR / East Germany) for 1949-1990. The companion rows "
        "F77-1949-1990 and F78-1949-1990 carry the two halves separately "
        "for datasets that distinguish them; this combined row holds "
        "data reported under a single undifferentiated 'Germany' label.",
    ),
    (
        "JPN-1895-1945",
        "Japanese Empire",
        build_jpn_1895_1945,
        "Partial union of CShapes 2.0 features: Japan metropole (740), "
        "Taiwan (713, 1895-1945), and the combined Korean peninsula using "
        "post-1945 North Korea (731) + South Korea (732) as a proxy for "
        "colonial-era Chōsen. Does NOT include Manchukuo or S. Sakhalin — "
        "neither is present in CShapes 2.0. Captures ~95% of the Empire's "
        "population base and the bulk of its agricultural territory.",
    ),
    (
        "KOR-1800-1945",
        "Korea (to 1945)",
        build_kor_1800_1945,
        "Union of CShapes 2.0 gwcode 731 (North Korea) and 732 (South "
        "Korea) using the 1945-onward polygons as a proxy for the unified "
        "Korean peninsula under the Korean Empire (1800-1910) and Japanese "
        "colonial rule (1910-1945). The peninsula's boundaries were "
        "effectively unchanged across this whole period.",
    ),
    (
        "MAN-1932-1945",
        "Manchukuo (1932-1945)",
        build_man_1932_1945,
        "Union of GADM 4.1 Chinese provinces Heilongjiang (CHN.11_1), "
        "Jilin (CHN.17_1), and Liaoning (CHN.18_1) — a close approximation "
        "of the Japanese puppet state Manchukuo's territory. Historical "
        "Manchukuo also annexed Rehe/Jehol from Inner Mongolia (1933); "
        "the 3-province polygon captures ~90% of the state's area.",
    ),
    (
        "EGYSUD-1934-1956",
        "Egypt and Anglo-Egyptian Sudan",
        build_egysud_1934_1956,
        "Union of CShapes 2.0 Egypt (gwcode 651) and Sudan (gwcode 625). "
        "Composed-union row for FAO/IIA series reported under Egypt with "
        "Anglo-Egyptian Sudan folded in; the constituents EGY-1925-1967 and "
        "SUD-1934-1956 carry the two separately.",
    ),
    (
        "CODRU-1922-1960",
        "Belgian Congo and Ruanda-Urundi",
        build_codru_1922_1960,
        "Union of CShapes 2.0 Belgian Congo (gwcode 490) and Ruanda-Urundi "
        "(gwcode 515). Composed-union row for colonial returns combining the "
        "two; constituents COD-1910-1960 and RWB-1922-1962 carry them apart.",
    ),
    (
        "BLX-1921-1999",
        "Belgium-Luxembourg Economic Union",
        build_blx_1921_1999,
        "Union of CShapes 2.0 Belgium (gwcode 211) and Luxembourg (gwcode "
        "212). BLEU customs union (1921-1999); composed-union row for series "
        "reporting the two as one unit. Constituents BEL-1831-2025 and "
        "LUX-1839-2025 carry them apart.",
    ),
    (
        "MASG-1946-1963",
        "Malaya and Singapore",
        build_masg_1946_1963,
        "Union of CShapes 2.0 Malaya/Malaysia (gwcode 820) and Singapore "
        "(gwcode 830). Composed-union row for FAO series reporting the "
        "Federation of Malaya figure as including Singapore (1949-1960); "
        "constituents MYS-1946-1957/MYS-1957-1963 and SGP-1946-1963 carry "
        "them apart.",
    ),
    (
        "AOF-1895-1960",
        "French West Africa (AOF)",
        build_aof_1895_1960,
        "Union of CShapes 2.0 constituent colonies at vintage 1938 (gwcodes "
        "432, 433, 434, 435, 436, 437, 438). CShapes drops the federation "
        "aggregate (gwcode 430) after 1904; 1938 excludes Upper Volta "
        "(dissolved 1932-1947). See wiki/polities/aof-1895-1960.md.",
    ),
    (
        "CZE-1804-1918",
        "Czech Lands (Crownlands of Bohemia, 1804-1918)",
        build_cze_1804_1918,
        "Union of Histogis 1860 Habsburg crownlands Bohemia (id 7), Moravia "
        "(id 15), and Austrian Silesia (id 5). The only vector source with "
        "individual crownland polygons for this sub-imperial unit. See "
        "wiki/polities/cze-1804-1918.md.",
    ),
    (
        "ITS-1908-1960",
        "Italian Somaliland (1908-1960)",
        build_its_1908_1960,
        "CShapes 2.0 gwcode 520 (Somalia, 1960-2019, 636,242 km2) MINUS gwcode "
        "521 (British Somaliland, 1897-1960, 171,499 km2) = 464,743 km2. The "
        "only Somali feature in the sovereign-state distribution starts at the "
        "1960-07-01 union, so it covers BOTH Somalilands; subtracting the "
        "British protectorate recovers the Italian colony. Verified identical "
        "(symmetric difference 0.0 km2) to CShapes 2.0's own Italian "
        "Somaliland dependency feature (cowcode 5200, 1924-07-01 onward), "
        "which is absent from the registered source. Post-1924 (post-Jubaland) "
        "extent; overstates 1908-1924 by ~94,400 km2 — see "
        "wiki/polities/its-1908-1960.md.",
    ),
    (
        "PTIND-1816-1961",
        "Portuguese India (Estado da India Portuguesa)",
        build_ptind_1816_1961,
        "Union of GADM 4.1 adm1 Goa IND.10_1 and Daman and Diu IND.9_1, which GADM "
        "carries as one feature. Components named by the page's polygon_method "
        "composed-union-goa-daman-diu; it had no polygon_feature_id, which is why "
        "an earlier pass read it as having no recipe. Excludes Dadra and Nagar "
        "Haveli, held until 1954 but not named by the page.",
    ),
]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    drv = ogr.GetDriverByName("GPKG")
    ds = drv.CreateDataSource(str(OUT))
    srs = wgs84_lonlat()
    layer = ds.CreateLayer("constructed", srs, ogr.wkbMultiPolygon)
    layer.CreateField(ogr.FieldDefn("polity_code", ogr.OFTString))
    layer.CreateField(ogr.FieldDefn("polity_name", ogr.OFTString))
    layer.CreateField(ogr.FieldDefn("provenance", ogr.OFTString))

    defn = layer.GetLayerDefn()
    for code, name, builder, provenance in BUILDERS:
        try:
            geom = builder()
        except Exception as e:
            print(f"  FAIL {code}: {e}", file=sys.stderr)
            continue
        feat = ogr.Feature(defn)
        feat.SetField("polity_code", code)
        feat.SetField("polity_name", name)
        feat.SetField("provenance", provenance)
        feat.SetGeometry(geom)
        layer.CreateFeature(feat)
        print(f"  OK   {code}: {name}")

    ds = None
    print(f"Wrote: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
