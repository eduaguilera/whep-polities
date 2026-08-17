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
# Built for a short explicit country list only -- see ADM2_COUNTRIES in the fetch script.
GADM41_ADM2 = REPO_ROOT / "data/geodata/gadm-4.1/gadm41_adm2.gpkg"
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
# Natural Earth 10m rivers + lake centrelines, as distributed INSIDE the Paine et al. 2024
# replication package (data/geodata/paine-2024). It is not a separately registered WHEP source,
# and it is used here for exactly one feature: the two line parts named "Panama Canal", which are
# the only canal centreline in any fetched file. Named at the top rather than inside the builder
# so that a future fetch reorganising paine-2024 breaks in one place.
NE10M_RIVERS = (
    REPO_ROOT
    / "data/geodata/paine-2024/AfricanBordersReplication/Shapefiles/Rivers"
    / "ne_10m_rivers_lake_centerlines.shp"
)


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


def _cshapes2_step(gwcode: int, start_year: int, end_year: int) -> ogr.Geometry:
    """Return the CShapes 2.0 step matching (gwcode, gwsyear, gweyear) EXACTLY.

    `_cshapes2_feature(gwcode, year)` selects by containment, which cannot express a step whose
    years are shared with another step. CShapes 640 has BOTH `1913-1913` (1,912,569 km2) and
    `1913-1914` (1,784,488) because the Ottoman border moved during 1913, so:

        polygon_feature_year: 1913   ties -- both steps start in 1913, and find_feature's
                                     exact-start preference leaves the winner to shapefile row
                                     order, which validate_polygon_binding_determinism exists
                                     to forbid
        polygon_feature_year: 1914   resolves DETERMINISTICALLY to `1914-1918`, a step that
                                     begins after the row ends

    There is no year that names the intended step, so it has to be named by its bounds.
    """
    if not CSHAPES2.exists():
        raise FileNotFoundError(
            f"{CSHAPES2} missing - run scripts/sources/cshapes-2.0/fetch.sh first."
        )
    ds = ogr.Open(str(CSHAPES2))
    lyr = ds.GetLayer()
    hits = []
    for f in lyr:
        if int(f.GetField("gwcode")) != gwcode:
            continue
        if int(f.GetField("gwsyear")) == start_year and int(f.GetField("gweyear")) == end_year:
            hits.append(f.GetGeometryRef().Clone())
    if not hits:
        raise LookupError(
            f"CShapes 2.0 has no gwcode={gwcode} step exactly {start_year}-{end_year}"
        )
    if len(hits) > 1:
        raise LookupError(
            f"CShapes 2.0 has {len(hits)} gwcode={gwcode} steps at {start_year}-{end_year}; "
            f"naming a step by its bounds is supposed to be unique"
        )
    return hits[0]


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



def _gadm_adm2(gid_2: str) -> ogr.Geometry:
    """Return the GADM 4.1 admin-2 feature with the given GID_2.

    The adm2 extract covers only the countries in the fetch script's ADM2_COUNTRIES, because a
    global one is far larger than anything here needs. A missing country raises rather than
    returning nothing.
    """
    if not GADM41_ADM2.exists():
        raise FileNotFoundError(
            f"{GADM41_ADM2} missing - run scripts/sources/gadm-4.1/fetch.sh first."
        )
    ds = ogr.Open(str(GADM41_ADM2))
    lyr = ds.GetLayer()
    for f in lyr:
        if f.GetField("GID_2") == gid_2:
            return f.GetGeometryRef().Clone()
    raise LookupError(
        f"GADM 4.1 adm2 has no feature with GID_2={gid_2!r}. If its country is not in the fetch "
        f"script's ADM2_COUNTRIES list, add it there."
    )


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


def _ne10m_river(name: str) -> ogr.Geometry:
    """Union of the Natural Earth 10m river/lake-centreline parts whose `name` matches exactly.

    Returns a LINE geometry in WGS84, not a polygon: the only caller buffers it. NE splits the
    Panama Canal into two parts with different `featurecla` ("Lake Centerline" through Gatun Lake,
    "River" for the cut sections), so a single-feature lookup would silently return half a canal.
    """
    if not NE10M_RIVERS.exists():
        raise FileNotFoundError(
            f"{NE10M_RIVERS} missing - run scripts/sources/paine-2024/fetch.sh first."
        )
    ds = ogr.Open(str(NE10M_RIVERS))
    lyr = ds.GetLayer()
    acc = None
    n = 0
    for f in lyr:
        if f.GetField("name") != name:
            continue
        g = f.GetGeometryRef().Clone()
        acc = g if acc is None else acc.Union(g)
        n += 1
    if acc is None:
        raise LookupError(f"Natural Earth 10m rivers has no feature named {name!r}")
    print(f"    NE 10m {name!r}: {n} part(s)")
    return acc


def _buffer_metres(geom: ogr.Geometry, metres: float, epsg: int) -> ogr.Geometry:
    """Buffer a WGS84 geometry by a distance in METRES, via the projected CRS `epsg`.

    Buffering in degrees is not a distance at all, and buffering in a global equal-area CRS is a
    distance that varies with latitude, so the projection is named by the caller for the one place
    the polygon actually is. The round trip is WGS84 -> epsg -> buffer -> WGS84.
    """
    src = wgs84_lonlat()
    dst = osr.SpatialReference()
    dst.ImportFromEPSG(epsg)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    g = geom.Clone()
    g.Transform(osr.CoordinateTransformation(src, dst))
    b = g.Buffer(metres)
    b.Transform(osr.CoordinateTransformation(dst, src))
    if b.GetGeometryType() != ogr.wkbMultiPolygon:
        b = ogr.ForceToMultiPolygon(b)
    return b


def _envelope_of(g: ogr.Geometry) -> ogr.Geometry:
    """The axis-aligned bounding box of `g`, as a polygon.

    For clipping an ISLAND out of a coarser containing feature. Subtracting the island's own
    outline is not enough when the two sources disagree about where its coast is: Cliopatria's
    Ceylon is about 8,000 km2 larger than CShapes 780's, so `British Raj MINUS CShapes 780` left
    12 fragments totalling 7,995 km2, every one of them ON Sri Lanka (79.9-81.9E, 6.6-9.7N) and
    still attributed to British India.
    
    Subtracting the ENVELOPE removes the island and any coastal disagreement in one operation.
    It is only safe where the box holds nothing else, so the caller must have checked: Ceylon's
    box is lon 79.70-81.89, lat 5.92-9.82, India's nearest land is 0.443 degrees away, and no
    other live polity in the database has any land inside it.
    """
    x0, x1, y0, y1 = g.GetEnvelope()
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)):
        ring.AddPoint_2D(x, y)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly


MAX_REPAIR_COST = 0.001  # 0.1% of area; a repair costing more than this is a judgement, not a fix


def _valid(g: ogr.Geometry, label: str) -> ogr.Geometry:
    """Repair a source geometry enough for set operations, refusing an expensive repair.

    SOURCE FEATURES ARE NOT ALWAYS VALID, and GEOS set operations abort on them rather than
    returning something wrong -- which is the good failure mode, but it means a builder cannot
    just call Difference() on whatever the source hands back. Cliopatria's "British Raj" @1880
    self-intersects in Balochistan (63.83E, 29.47N), so subtracting Ceylon from it died with
    "side location conflict at 71.33 20.80".

    build_database repairs invalid geometry on write, under its own 0.5% budget, so this only
    matters for geometry consumed by a BUILDER before it ever reaches that step.

    The cost is checked rather than assumed: repairing British Raj moves 0.0009% of its area.
    A repair that moves more than 0.1% is refused, because at that point it is changing the
    territory rather than fixing the encoding, and the builder should say so instead of
    silently publishing the difference.
    """
    if g.IsValid():
        return g
    fixed = g.MakeValid()
    if fixed is None or not fixed.IsValid():
        raise ValueError(f"{label}: MakeValid produced nothing usable")
    before = g.GetArea()
    if before > 0:
        cost = abs(fixed.GetArea() - before) / before
        if cost > MAX_REPAIR_COST:
            raise ValueError(
                f"{label}: repairing the source moves {cost:.3%} of its area, above the "
                f"{MAX_REPAIR_COST:.1%} budget - decide it explicitly rather than here"
            )
    return fixed


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


def build_aoi_1936_1941() -> ogr.Geometry:
    """Italian East Africa 1936-1941 = Ethiopia union Eritrea union Italian Somaliland.

    The recipe is not invented here. wiki/polities/aoi-1936-1941.md has carried it as
    `oq-aoi-polygon-construction` since the row was created -- "union of CShapes 530
    (1907) + 531 (1900) + 5200 (1924)" -- and the row has declared
    `polygon_source: constructed` all along with nothing built, which is exactly the
    failure mode the constructed-source docstring warns about: a declaration with no
    BUILDERS entry ships no geometry.

    Two of the three ids resolve directly. The third does NOT, and that is why this is
    written against `build_its_1908_1960` rather than against 5200: cowcode 5200 is a
    DEPENDENCY feature, and the CShapes distribution registered here is the
    sovereign-state one, which has no Italian Somaliland at all -- its only Somali
    polygon is gwcode 520, independent Somalia from 1960, i.e. Italian PLUS British
    Somaliland. `build_its_1908_1960` already reconstructs the colonial boundary as
    520 MINUS 521 and is documented there as bit-identical (symmetric difference
    0.0 km2) to 5200 itself, so reusing it satisfies the page's recipe rather than
    substituting for it.

    The two CShapes members are named by their step bounds, not by a year, because
    both families have steps that share a start year with a neighbour and
    `_cshapes2_feature` would leave the winner to shapefile row order:
      530  1907-1952  Ethiopia after the 1907 Anglo-Italian-Ethiopian boundary
                      settlement, 1,127,556 km2. Note this is the pre-1952 extent,
                      i.e. WITHOUT Eritrea, which is supplied separately -- CShapes'
                      1952-1993 step (1,248,452) is federated Ethiopia-with-Eritrea
                      and using it would have double-counted Eritrea.
      531  1900-1941  Eritrea in its final colonial boundary, 120,897 km2. The step
                      ends in 1941, the year AOI did.

    MEASURED, all three members reprojected to ESRI:54034:
        Ethiopia            1,127,556 km2
        Eritrea               120,897
        Italian Somaliland    464,743
        union               1,713,196      = the arithmetic sum, because all three
                                             pairwise intersections are 0.000 km2

    1,713,196 against the page's declared 1,700,000 is +0.78%, and against the
    1,725,330 km2 usually quoted for AOI it is -0.70%. So the union is not a proxy
    for the territory; it is the territory, on the boundaries of its own three parts.

    CONSEQUENCE, stated rather than discovered later: this polygon necessarily
    contains ETH-1907-1936, ERI-1889-1952 and ITS-1908-1960, all three of which
    overlap 1936-1941, so it becomes a container under
    validate_spatial_containment and is listed there. That is the same relationship
    AOF/AEF/MASG already have with their members and is not a defect. What it does
    NOT settle is whether a consumer summing AOI together with its members
    double-counts the Horn -- see oq-aoi-member-double-count on the page. Nothing in
    this repo sums them, and the page's own verification concluded that the sources
    checked report the members separately, so the geometry is attached and the
    aggregation question is left named.
    """
    return _union(
        _cshapes2_step(530, 1907, 1952),
        _cshapes2_step(531, 1900, 1941),
        build_its_1908_1960(),
    )


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

    Understates the peak by 11.5% for TWO reasons, not one (re-measured for issue 106):
    the April 1941 Backa and Baranya strips (~10,000 km2) are not included, because CShapes
    retains Yugoslavia's full pre-war footprint through the occupation and GADM cannot
    isolate them either; and neither is Subcarpathian Ruthenia (annexed March 1939,
    ~12,000 km2), which the page long claimed was already inside this CShapes feature.
    It is not -- the feature has 0 km2 inside modern Ukraine, and decomposes as Trianon
    Hungary (92,991) plus 15,795 km2 inside modern Slovakia (the First Vienna Award slice),
    which is the whole 108,785. The page records the peak as ~172,277 km2 against this
    construction's 152,423; restoring both missing components gives ~174,500.
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
    """Bali and Lombok, 1949-1951 = Bali (adm1) union the five Lombok districts (adm2).

    TWO SEPARATE ERRORS IN THE PAGE'S DECLARED RECIPE, `IDN.1_1+IDN.20_1`:

      IDN.1_1 is ACEH, on northern Sumatra, some 3,000 km from Bali. Bali is IDN.2_1.
      IDN.20_1 is Nusa Tenggara Barat, which is Lombok PLUS SUMBAWA.

    The second is why this builder sat unregistered: at adm1 the union measured 25,261 km2 against
    the page's declared 10,505, 140% over, because Sumbawa is four times Lombok's size. Separating
    them needs adm2, which the fetch script now builds for IDN.

        Lombok Barat    IDN.20.4_1     924
        Lombok Tengah   IDN.20.5_1   1,167
        Lombok Timur    IDN.20.6_1   1,607
        Lombok Utara    IDN.20.7_1     812
        Mataram         IDN.20.8_1      60   the city, on Lombok
        Lombok total               4,570 km2   against a published ~4,725
        + Bali IDN.2_1             5,591
        union                     10,160 km2   against the declared 10,505 -> 3.3%

    Mataram is included because it is a kota carved out of Lombok Barat, not a separate island;
    omitting it would leave a hole in the middle of the polygon.
    """
    return _union(
        _gadm_adm1("IDN.2_1"),      # Bali
        _gadm_adm2("IDN.20.4_1"),   # Lombok Barat
        _gadm_adm2("IDN.20.5_1"),   # Lombok Tengah
        _gadm_adm2("IDN.20.6_1"),   # Lombok Timur
        _gadm_adm2("IDN.20.7_1"),   # Lombok Utara
        _gadm_adm2("IDN.20.8_1"),   # Mataram
    )


# OCCUPIED LIBYA 1943-1951 WAS THREE SEPARATELY ADMINISTERED TERRITORIES, and the database
# could represent the whole but none of the parts (issue 156). Tripolitania and Cyrenaica were
# under British military administration, Fezzan under French; 39 data rows route to them.
#
# NO SOURCE IN THIS REPO DRAWS THEM. Checked directly: CShapes has only gwcode 620 (Libya
# entire) for every step 1912-2019, and Cliopatria's nearest features are "Ottoman
# Tripolitania" (1840-1911) and an ANCIENT "Cyrenaica" (-331 to -92). So the three have to be
# composed from modern GADM 4.1 adm1 shabiyat, and the assignment of those shabiyat is the
# judgement this comment exists to justify.
#
# THE HISTORICAL BOUNDARIES DO NOT FOLLOW THE MODERN SHABIYAT, and the disagreement is
# concentrated in exactly two units: Surt (78,659 km2, the Sirte basin, historically the
# Tripolitania/Cyrenaica frontier) and Al Jufrah (111,245 km2, the Jufra oases, between
# Tripolitania's southern reach and Fezzan's northern one). The other 20 units are unambiguous
# by geography. All four possible placements were measured against FAO 1952's own areas for the
# three reporting units -- Tripolitania 353,000, Cyrenaica 855,400, Fezzan 551,100, summing to
# exactly its Libya of 1,759,500:
#
#     placement                        TRP        CYR        FEZ      worst
#     Surt->CYR, Jufrah->TRP      -10.9%      -2.0%     -15.9%     -15.9%   <- chosen
#     Surt->CYR, Jufrah->FEZ      -42.4%      -2.0%      +4.3%     -42.4%
#     Surt->TRP, Jufrah->FEZ      -20.1%     -11.2%      +4.3%     -20.1%
#     Surt->TRP, Jufrah->TRP      +11.4%     -11.2%     -15.9%     -15.9%
#
# The first was chosen for a reason stronger than "smallest worst error": GADM's Libya measures
# 1,616,058 km2 against the accepted 1,759,540, apparently 8.2% SHORT, so if the whole is under
# FAO then EVERY PART SHOULD BE UNDER TOO -- which only the first placement achieved.
#
# THAT ARGUMENT IS WITHDRAWN (issue 196). GADM is not short. Three independent products agree on
# Libya to 0.5%: GADM 1,616,058, CShapes 2.0 1,617,537, Natural Earth 10m 1,623,761. The outlier
# is 1,759,540, an Italian 1930s figure for a LARGER Libya: it first appears in IIA 1938, while
# the 1933 edition gives Tripolitania 900,000 + Cyrenaica 738,000 = 1,638,000 for the same country,
# matching modern GIS to +0.9%..+1.4% (1925 and 1929 give 1,500,000; 1932 has only Tripolitania). In between, the January 1935 Laval-Mussolini treaty put Libya's
# southern boundary on the Aouzou line -- 114,000 km2, 79% of the 143,482 km2 gap -- never
# ratified and awarded to Chad by the ICJ in 1994. All three products draw the 1899/1919 line
# instead, confirmed from Chad's own vertices at 15.985E/23.4447N (Tropic of Cancer at 16E) and
# 19.4961N at 23.9813E (19 deg 30' N at 24E). So the gap is territory OUTSIDE the polygon, not area
# missing from inside it, and FAO's three territorial figures -- which sum to exactly its
# 1,759,500 -- carry the same over-count. Against a strip-corrected 353,000 / 792,377 / 500,123
# (the strip split 55.3/44.7 CYR/FEZ by MEASURED length of Chad frontage: Al Kufrah and Murzuq are
# the only two shabiyat on that boundary, which measures 1,051.5 km -- 581.3 on Al Kufrah, 470.2 on
# Murzuq):
#
#     placement                        TRP        CYR        FEZ      worst
#     Surt->CYR, Jufrah->TRP      -10.9%      +5.7%      -7.3%     -10.9%   <- still chosen
#     Surt->CYR, Jufrah->FEZ      -42.4%      +5.7%     +14.9%     -42.4%
#     Surt->TRP, Jufrah->FEZ      -20.1%      -4.2%     +14.9%     -20.1%
#     Surt->TRP, Jufrah->TRP      +11.4%      -4.2%      -7.3%     +11.4%
#
# NO placement now puts every part under FAO, and the first leads the fourth 10.9% to 11.4%.
#
# WHAT IS STILL A GUESS, AND NOW MORE OPEN THAN BEFORE: whether the 1943-1951 administrators drew
# Sirte into Cyrenaica. The 1934 Italian provinces put Sirte in Misurata, i.e. Tripolitania, which
# argues for the third or fourth placement, and the consistency test that refused them is gone.
# The assignment is left UNCHANGED -- issue 196 answered the area question, not the placement one,
# and 55.3/44.7 is a frontage estimate, not a measured strip. Recorded as
# oq-fez-shabiya-placement-consistency-withdrawn on fez-1943-1951 for all three pages.
#
# THE PARTITION IS THE DELIVERABLE. The three unions are exhaustive over GADM's 22 Libyan
# shabiyat and pairwise disjoint by construction, so per-territory data sums to the national
# total -- which is what makes TRP + CYR + FEZ usable alongside LBY at all.
_TRP_ADM1 = (
    "LBY.20_1",  # Tripoli
    "LBY.4_1",   # Al Jifarah
    "LBY.11_1",  # Az Zawiyah
    "LBY.10_1",  # An Nuqat al Khams
    "LBY.8_1",   # Al Marqab
    "LBY.15_1",  # Misratah
    "LBY.3_1",   # Al Jabal al Gharbi
    "LBY.17_1",  # Nalut
    "LBY.5_1",   # Al Jufrah -- the judgement; see above
)
_CYR_ADM1 = (
    "LBY.1_1",   # Al Butnan
    "LBY.13_1",  # Darnah
    "LBY.2_1",   # Al Jabal al Akhdar
    "LBY.7_1",   # Al Marj
    "LBY.12_1",  # Benghazi
    "LBY.9_1",   # Al Wahat
    "LBY.6_1",   # Al Kufrah
    "LBY.19_1",  # Surt -- the judgement; see above
)
_FEZ_ADM1 = (
    "LBY.16_1",  # Murzuq
    "LBY.18_1",  # Sabha
    "LBY.21_1",  # Wadi al Hayat
    "LBY.22_1",  # Wadi ash Shati'
    "LBY.14_1",  # Ghat
)


def build_trp_1943_1951() -> ogr.Geometry:
    """Tripolitania under British military administration = 9 GADM adm1 shabiyat, 314,598 km2
    against FAO 1952's 353,000 (-10.9%). See the partition note above for why Al Jufrah is here
    and Surt is not."""
    return _union(*(_gadm_adm1(g) for g in _TRP_ADM1))


def build_cyr_1949_1951() -> ogr.Geometry:
    """Cyrenaica = 8 GADM adm1 shabiyat, 837,876 km2 against FAO 1952's 855,400 (-2.0%).

    TWO POLITY ROWS SHARE THIS ONE FEATURE, and that is the point: CYR-1949-1951 (the Emirate of
    Cyrenaica, proclaimed 1 June 1949) and CYR-1943-1949 (the British Military Administration
    before it, added for issue 198) both declare polygon_feature_id `CYR-1949-1951`. The TERRITORY
    is the same one Britain administered from 1943; only the polity changed in 1949, so the
    geometry carries no vintage question and no second builder was written for it. Successive
    periods of one territory sharing a feature is the normal case -- validate_shared_polygons
    reports sharing only for rows that COEXIST, and these two do not, because end_year is
    exclusive. MAN-1945-1950 reuses MAN-1932-1945's feature the same way.

    This docstring previously ended "leaves Cyrenaican data for 1943-1949 with no destination --
    not something this geometry can fix", which was right about the geometry and wrong about the
    remedy: the fix was a row, not a polygon.
    """
    return _union(*(_gadm_adm1(g) for g in _CYR_ADM1))


def build_fez_1943_1951() -> ogr.Geometry:
    """Fezzan under French military administration = 5 GADM adm1 shabiyat, 463,596 km2 against
    FAO 1952's 551,100 (-15.9%), the largest of the three deviations.

    Fezzan is where GADM's 8.2% Libya-wide shortfall concentrates: it is the emptiest quarter of
    the country, so a coarse desert boundary costs proportionally most here. The deviation is
    stated rather than corrected -- scaling a polygon to hit a stated area would make the check
    that compares them circular.
    """
    return _union(*(_gadm_adm1(g) for g in _FEZ_ADM1))


def build_mmr_lwr_1852_1885() -> ogr.Geometry:
    """British Lower Burma 1852-1885 = Cliopatria's Burma BEFORE the Second Anglo-Burmese War
    minus Burma AFTER it. The territory Britain took in 1852 is the difference between the two
    steps that bracket the war, so the source defines it without anyone having to enumerate
    provinces:

        Burma 1842-1852    552,405 km2    before
        Burma 1853-1858    437,084 km2    Upper Burma after annexation
        difference         115,321 km2    page declares 116,000 -> 0.6%

    Years 1850 and 1855 are each inside exactly ONE step, which _cliopatria_feature requires --
    the same care build_btl_1920_1957 documents, and that builder is the model here: British
    Togoland is likewise "Ghana after incorporation minus the Gold Coast before it".

    THE PAGE'S OWN RECIPE WAS WRONG IN TWO WAYS, and neither could have been caught by area alone
    because the row carried no geometry at all. It read `MMR.2_1+MMR.13_1+MMR.15_1`:

      * MMR.13_1 is SHAN -- 155,756 km2 of the northeastern plateau, annexed with UPPER Burma in
        1885-87, i.e. after this row ends. The page's own component table names Ayeyarwady in that
        slot, which is MMR.1_1: a GID transposition swapped the Irrawaddy delta for a highland
        state that was never in Lower Burma.
      * It listed three GIDs where the table lists FOUR components, omitting Tenasserim.

        as written (Bago+Shan+Yangon)         203,832 km2   +76%
        as apparently intended (Bago+Ayeyarwady+Yangon)  81,839 km2   -29%
        adding Tanintharyi                   123,140 km2    +6%
        adding Mon as well                   134,689 km2   +16%
        adding Rakhine as well               170,183 km2   +47%

    Every GADM reading needs a judgement about how much of Tenasserim and whether Arakan counts.
    The Cliopatria difference needs none: it is what the source says changed hands in 1852, and it
    lands within 0.6% of the page's independently-derived figure. So the GADM recipe is abandoned
    rather than repaired.
    """
    return _difference(
        _valid(_cliopatria_feature("Burma", 1850), "Cliopatria Burma @1850"),
        _valid(_cliopatria_feature("Burma", 1855), "Cliopatria Burma @1855"),
    )


def build_fcc_1862_1887() -> ogr.Geometry:
    """French Cochinchina = Cliopatria's Vietnam BEFORE the French conquest of the south minus
    Vietnam AFTER it. Exactly the MMR-LWR-1852-1885 pattern: the territory that changed hands is
    the difference between the two steps that bracket the war, so the source defines it without
    anyone enumerating provinces -- and here nobody could have, because GADM 4.1's fetched set has
    no VNM file at all (re-measured 2026-08-17: adm0 99 countries, adm1 80, adm2 Indonesia only).

        Vietnam 1834-1858    300,525 km2    before the Cochinchina campaign
        Vietnam 1859-1867    234,392 km2    after
        difference            66,277 km2    in 4 parts

    THE OBVIOUS CANDIDATE WAS THE WRONG SHAPE, which is why this row sat unbuilt: Cliopatria's
    "French Indochina" is the whole federation at 753,049 km2, 11x this row's territory, and its
    own successor FID-1887-1954 already uses it. The difference is a different question put to the
    same source.

    Three of the four parts are boundary jitter between the two steps, not territory: 49.6 km2 at
    107.5-107.6E/12.37-12.44N, 84.9 km2 at 109.4E/13.0N and 152.6 km2 at 109.3E/13.5-14.0N -- the
    last two on the central coast around Nha Trang and Qui Nhon, 150-300 km from Cochinchina and
    on the wrong side of the 1862 line. `_keep_parts_within` drops the two coastal ones by
    envelope (104-108.5E, 8-12.5N):

        kept       66,039 km2   the Mekong delta and Saigon, 104.4-108.0E, 8.5-12.4N
        dropped       238 km2   0.36%

    66,039 km2 against the ~65,000 km2 usually stated for Cochinchina, +1.6%. The page declares no
    area at all, so there is no in-repo figure to check against and the external one is what there
    is; `polygon_area_km2` is set to the measured 66,039 with that stated externally, NOT the other
    way round.

    VINTAGE CAVEAT, stated because it is real. France took the three eastern provinces in 1862 and
    the three western ones in 1867, but Cliopatria models the whole loss at its 1859 step break --
    the campaign began in 1858. So this polygon is the SIX-province Cochinchina for the row's whole
    1862-1887 span, and overstates 1862-1867, when France held only the east. The row spans 25
    years of which 20 are six-province, and no source here can split the two halves: the 1868-1869
    step is 234,478 km2, i.e. Cliopatria records no further reduction in 1867. `proxy`, for that
    reason, rather than `assigned`.
    """
    before = _valid(_cliopatria_feature("Vietnam", 1855), "Cliopatria Vietnam @1855")
    after = _valid(_cliopatria_feature("Vietnam", 1860), "Cliopatria Vietnam @1860")
    ceded = _difference(before, after)
    kept = _keep_parts_within(ceded, 104.0, 8.0, 108.5, 12.5)
    if kept is None or kept.IsEmpty():
        raise ValueError("build_fcc_1862_1887: the Cochinchina envelope kept nothing")
    return kept


def build_tur_1913_1914() -> ogr.Geometry:
    """The Ottoman Empire during 1913 = CShapes 640's `1913-1914` step, named by its bounds.

    THE ROW WAS PUBLISHING A STEP THAT BEGINS AFTER IT ENDS. It covered 1913 (end_year exclusive)
    with `polygon_feature_year: 1914`, and 1914 sits in two steps -- `1913-1914` and `1914-1918`.
    find_feature prefers the step whose start_year equals the queried year, so it took
    `1914-1918`: the row published 1,705,971 km2 while DECLARING 1,785,218, a 4.5% disagreement
    between a page and its own geometry that check A could not see, because 200 km2 of that gap
    is simplification and the rest is a different step entirely.

    It also made TUR-1913-1914 and TUR-1914-1918 publish IDENTICAL geometry, which is why the
    period-fit gate carried both an A entry and a B pair for this row.

    WHY THE `1913-1914` STEP AND NOT `1913-1913`. CShapes splits 1913 in two because the Ottoman
    border moved during it -- the Treaty of London in May, Bucharest in August, and the
    Ottoman-Bulgarian treaty in September that returned Edirne:

        1913-1913   1,912,569 km2   the earlier extent
        1913-1914   1,784,488 km2   the extent that carried into 1914

    The page declares 1,785,218, a 0.04% match to the second, so the second is what this row has
    always intended. For a row covering a full year the settled end-of-year extent is also the
    more useful one.

    Neither step can be selected by `polygon_feature_year` at all -- see _cshapes2_step.
    """
    return _cshapes2_step(640, 1913, 1914)


def build_pol_1919_1920() -> ogr.Geometry:
    """Poland after the Treaty of Saint-Germain = CShapes 290's `1919-1920` step, by its bounds.

    THE ROW WAS PUBLISHING THE POLYGON ITS OWN PAGE REJECTS BY NAME. CShapes gives gwcode 290
    three steps containing 1919:

        1918-11-11 / 1919-06-27   130,205 km2   post-independence, pre-Versailles
        1919-06-28 / 1919-09-09   177,762 km2   post-Versailles, EXCLUDES Galicia
        1919-09-10 / 1920-10-06   256,575 km2   post-Saint-Germain, Galicia incorporated

    Two of them start in 1919, so `polygon_feature_year: 1919` left find_feature's exact-start
    preference tied and the winner was decided by shapefile row order (issue 100's mechanism). Row
    order handed back the middle one -- 177,762 km2 -- while the page names the Saint-Germain step
    four times as "the polygon for this row" and rejects the middle one explicitly because it
    "excludes Galicia" and "would understate the actual territorial extent by ~44%".

    The error was invisible to validate_polygons check A because `polygon_area_km2: 177754` had
    been back-filled FROM the attached geometry (a 2026-07-24 caveat on the page records that
    edit), so the check compared the wrong polygon against its own area and passed.

    WHY A CONSTRUCTED FEATURE AND NOT A `polygon_feature_year` FIX. No year names the wanted step:
    1919 is shared by three candidates, and 1920 resolves deterministically to the NEXT step
    (1920-10-07 / 1921-03-17, 284,599 km2), which begins after this row's period and which the
    page assigns to the successor POL-1920-1921. The page also carried
    `polygon_feature_date: 1919-09-10`, an attempt to pin the step that nothing in the pipeline
    reads. Naming the step by its bounds is the same remedy TUR-1913-1914 got -- see
    _cshapes2_step -- and `1919-1920` is unique among gwcode 290's steps.

    This does not touch the row's residual `polygon_vintage_drift`: the Saint-Germain extent still
    understates October-December 1920 by ~11%, which is the page's own open question.
    """
    return _cshapes2_step(290, 1919, 1920)


def build_f206_2011_2025() -> ogr.Geometry:
    """Sudan and South Sudan as one reporting unit, 2011 onward = CShapes 625 union 626.

    Built from the SAME features the two members bind -- SDN-2011-2025 uses gwcode 625 and
    SSD-2011-2025 uses 626 -- so the aggregate cannot drift from its parts. Measured, the union is
    2,486,805 km2 against SUD-1956-2011's 2,486,812: a ratio of 1.0000, which is the check that
    matters, because this entity exists to describe exactly the territory unified Sudan had.

    The 8.9 km2 the two members intersect is sliver along their shared boundary from simplifying
    each independently, the same artefact documented for TRP/CYR in issue 156; the union absorbs it.
    """
    return _union(_cshapes2_feature(625, 2015), _cshapes2_feature(626, 2015))


def build_bwi_1833_1962() -> ogr.Geometry:
    """British West Indies colonial aggregate = the eleven territories the page enumerates.

    The recipe was written in `polygon_feature_id` as the string
    `gadm-union-JAM+TTO+BRB+BHS+ATG+GRD+VCT+DMA+LCA+KNA+MSR` with no builder, and the extract had
    no Jamaica or Trinidad and Tobago, so 24 rows of FAO "British West Indies" data landed on a
    polity with no territory. Both countries were fetched on 2026-08-10; the other nine were
    already present.

        JAM 11,000.0   BHS 13,388.1   TTO 5,159.1   DMA  754.2   LCA  614.4
        BRB    434.6   ATG    435.8   VCT   397.9   GRD  359.5   KNA  267.1   MSR 100.6
        union 32,912 km2    page declares 34,766 -> -5.3%

    FAO CANNOT SETTLE THE 5.3%, and it is worth saying why rather than implying the union is
    5% short of something known. FAO 1952's stated-area table has NO British West Indies
    aggregate -- only per-member rows (`British West Indies Jamaica`, `... Bahamas`, `...
    Cayman Islands`, `... Turks and Caicos`) plus separate `Leeward Islands` and `Windward
    Islands` groups. And two of those members are unusable:

        British West Indies Bahamas   1,400 km2   the Bahamas are 13,880
        British West Indies Jamaica   1,420 km2   Jamaica is 10,991

    roughly a factor of ten out, where the same table gives Cape Verde 4,030 against an actual
    4,033 and the Channel Islands 190 against 194. So those two rows are a units or OCR defect
    in the source extraction, not a disagreement about territory -- the class issue 111
    describes. Reported there.

    The page also excludes VGB, CYM and TCA "pending creation of those polity entries", and
    their combined ~1,300 km2 is most of the 1,854 km2 gap, which is the likeliest explanation
    for the declared figure being higher than the eleven-member union.
    """
    return _union(*(_gadm_adm0(c) for c in (
        "JAM", "TTO", "BRB", "BHS", "ATG", "GRD", "VCT", "DMA", "LCA", "KNA", "MSR")))


def build_bli_1833_1960() -> ogr.Geometry:
    """British Leeward Islands Colony 1833-1960 = the five modern territories it federated.

    The page carried the recipe in its `polygon_feature_id` as the string
    `gadm-union-ATG+KNA+MSR+DMA+VGB` and no builder, so the build logged
    "feature not found" and 24 rows of FAO Leeward Islands data landed on a polity with no
    territory (issues 3 and 155). The recipe is right; it just had nowhere to run.

        Antigua and Barbuda    435.8 km2
        Saint Kitts and Nevis  267.1
        Montserrat             100.6
        Dominica               754.2
        British Virgin Islands 169.4
        union                1,727.1 km2   page declares 1,716 -> 0.6%

    Dominica is included because it WAS a Leeward Island for most of this span: transferred
    from the Leeward Islands to the Windward Islands group in 1940, seventeen years before the
    colony was dissolved in 1956 and twenty before this row ends. So the union overstates the
    1940-1960 tail by Dominica's 754 km2 -- 44% of the total -- which is recorded on the page as
    an open question rather than smoothed away by dropping an island that belonged here for 107
    of the row's 127 years.
    """
    return _union(*(_gadm_adm0(c) for c in ("ATG", "KNA", "MSR", "DMA", "VGB")))


def build_win_1833_1960() -> ogr.Geometry:
    """British Windward Islands Colony 1833-1960 = the four islands it grouped in 1940-1960.

    The Leeward half of the British Caribbean got a polity (BLI-1833-1960, issues 3 and 155);
    the Windward half did not, so three FAO 1952 label variants carrying 13 rows had nowhere
    to route (issue 18). The only alternatives were BWI-1833-1962 at ~34,766 km2 -- 16x this
    colony -- or a single island, which understates it 3-6x.

        Grenada                359.5 km2
        Saint Lucia            614.4
        Saint Vincent          397.9
        Dominica               754.2
        union                2,126.1 km2

    THE COMPOSITION IS MEASURED, NOT ASSUMED, because the source prints the parent and the
    parts in the same column. FAO 1952's 1950 land-use table gives `Windward Islands` a total
    of 215.0 thousand ha = 2,150 km2, which the four-island union matches to 1.1%. The three
    island sub-entries in that same table -- Grenada 34.0, St Lucia 62.0, St Vincent 34.0
    thousand ha -- sum to only 1,300 km2, and Dominica's 754 is the difference. So Dominica is
    IN (transferred from the Leeward Islands in 1940) and Barbados is OUT (434.6 km2, left the
    Windward Islands government in 1885) -- both of which the administrative history says
    independently.

    This is therefore the POST-1940 composition, held for the whole 1833-1960 span, because it
    is the composition the data measures: the group population totals (247 thousand in 1937,
    279 in 1951) also fit the four-island unit throughout. Same choice and same reason as
    build_bli_1833_1960 above, and the two rows consequently BOTH claim Dominica for the years
    they share -- 754 km2 of deliberate, documented overlap, on both pages.
    """
    return _union(*(_gadm_adm0(c) for c in ("GRD", "LCA", "VCT", "DMA")))


def build_ind_1800_1886() -> ogr.Geometry:
    """British India 1800-1886 = Cliopatria's "British Raj" at 1880, MINUS Ceylon and the
    European enclaves that were never British.

    CEYLON IS THE WHOLE POINT, and it is 65,600 km2. Cliopatria's "British Raj" feature
    includes it, so this row -- the only IND period bound to Cliopatria rather than to CShapes
    750 -- geometrically contained LKA-1800-2025 at 99.5% of Ceylon. Ceylon was a separate
    Crown Colony from 1802, administered from Colombo and answering to the Colonial Office
    rather than to the India Office. It was never part of British India, and every CShapes-bound
    IND period correctly contains 0 km2 of it. Measured:

        IND-1800-1886 n LKA-1800-2025    65,600 km2
        every other IND period n LKA          0 km2

    THE DECLARED AREA AGREED WITH THE GEOMETRY BECAUSE BOTH INCLUDED CEYLON. The page declared
    4,209,917 and the polygon measured 4,209,869 -- a 0.001% match that looked like confirmation
    and was two errors cancelling, the same shape as IDN-OTH-1949-1951's West Papua (PR 182).

    The two European enclaves are subtracted as well, and for this span that is unambiguous:
    Portuguese India was Portuguese until December 1961 and French India French until October
    1954, so both were foreign for the whole of 1800-1886. They are small -- 1,299 and 311 km2
    inside this feature -- but they cost nothing to remove and leaving them would keep a known
    double claim in a row being rebuilt anyway.

    Each subtrahend is the SAME geometry the other row publishes, not a re-derivation, so the
    pairs cannot drift apart: CShapes 780 at 1948 is what LKA-1800-2025 binds, and the two
    enclave builders are the ones PTIND-1816-1961 and FRIN-1816-1954 use.

    WHAT THIS DOES NOT FIX -- REVISED 2026-08-13, and the earlier text overstated the blocker.
    It said the CShapes-bound periods "cannot be subtracted the same way, because IND-1949-2025
    spans both sides of 1954 and 1961". That is true of IND-1949-2025 ALONE. The five periods
    IND-1886-1893 .. IND-1947-1949 all end in or before 1949, five years before Pondicherry and
    twelve before Goa, so for them the subtraction is as unambiguous as it is here -- and they
    now do it, via _british_india_minus_enclaves(). Only IND-1949-2025 remains, and it does need
    a periodisation decision (issue 84).
    """
    return _difference(
        _valid(_cliopatria_feature("British Raj", 1880), "Cliopatria British Raj @1880"),
        _envelope_of(_cshapes2_feature(780, 1948)),
        build_ptind_1816_1961(),
        build_frin_1816_1954(),
    )


def _british_india_minus_enclaves(gwsyear: int, gweyear: int) -> ogr.Geometry:
    """A CShapes 750 step MINUS Portuguese India MINUS French India.

    THE ENCLAVES WERE NEVER BRITISH AND THE DOUBLE-COUNT WAS CONTINUOUS. Measured on the built
    GeoPackage before this change, every CShapes-bound British India period contained both:

        each IND period n PTIND-1816-1961    3,719 km2   98.4% of Portuguese India
        each IND period n FRIN-1816-1954       520 km2   95.2% of French India

    Portuguese India (Goa, Daman, Diu) was Portuguese until December 1961 and French India
    (Pondicherry, Karikal, Mahe, Yanam) French until October 1954, so for every period ending in
    or before 1949 both were foreign for the whole span and the subtraction needs no judgement.
    That is what makes this safe here and unsafe for IND-1949-2025, which straddles both
    annexation dates -- see the BUILDERS note and issue 84.

    THE SUBTRACTION ITSELF LEAVES NO RIM, AND THE PUBLISHED POLYGON STILL DOES. Both were
    measured, because they disagree and the difference is build_database.py rather than this
    recipe:

        this builder's own geometry n PTIND     0.00 km2      n FRIN     0.00 km2
        the published GeoPackage    n PTIND    13.60 km2      n FRIN    47.20 km2

    CShapes' India covers both GADM enclaves completely, so the raw difference removes them
    outright -- unlike Cliopatria's British Raj, whose coastline disagrees with GADM's and leaves
    build_ind_1800_1886() with 8.3 km2 of Goa and 40.2 km2 of Puducherry. What puts a rim back is
    write_gpkg()'s Douglas-Peucker simplification: it moves every boundary by up to the tolerance,
    including the freshly cut enclave holes, and the same step is why these rows publish ~0.011%
    less area than the builder computes. So the double-count falls 3,719 -> 13.6 km2 (99.6% gone)
    and 520 -> 47.2 (90.9% gone) rather than to zero, and the remainder is a property of the
    published simplification, not of the recipe. Recorded rather than rounded to "fixed".

    THE STEP IS NAMED BY ITS BOUNDS rather than by a year, because two of these rows would
    otherwise pick the wrong geometry: `polygon_feature_year: 1914` on IND-1914-1937 matches BOTH
    the 1899-1914 step (4,819,795 km2) and the 1914-1931 one (4,894,456), and only
    find_feature's exact-start preference separates them. Each wrapper below passes the bounds of
    the step its row was already bound to, so this change subtracts the enclaves and moves
    nothing else.

    Each subtrahend is the SAME geometry PTIND-1816-1961 and FRIN-1816-1954 publish, not a
    re-derivation, so the pairs cannot drift apart.
    """
    return _difference(
        _cshapes2_step(750, gwsyear, gweyear),
        build_ptind_1816_1961(),
        build_frin_1816_1954(),
    )


def build_ind_1886_1893() -> ogr.Geometry:
    """British India 1886-1893 = CShapes 750's `1886-1893` step minus the two enclaves.

    4,652,712 km2 measured on the step, 4,648,466 after the cut, 4,647,939 published -- the last
    gap being write_gpkg's simplification."""
    return _british_india_minus_enclaves(1886, 1893)


def build_ind_1893_1914() -> ogr.Geometry:
    """British India 1893-1914 = CShapes 750's `1899-1914` step minus the two enclaves.

    The row spans 1893-1913 and CShapes splits it in two -- `1893-1898` and `1899-1914` -- at
    identical area (4,819,795 km2 both). The row was bound to the later step via
    `polygon_feature_year: 1899`; that binding is preserved so this change is the subtraction
    only. 4,815,549 after the cut, 4,815,028 published."""
    return _british_india_minus_enclaves(1899, 1914)


def build_ind_1914_1937() -> ogr.Geometry:
    """British India 1914-1937 = CShapes 750's `1914-1931` step minus the two enclaves.

    CShapes also has a `1931-1937` step at bit-identical area (4,894,456 km2) whose only changed
    field is `capname`, Calcutta to New Delhi -- the row's page already establishes that this is
    not a territorial change. 4,890,210 after the cut, 4,889,739 published."""
    return _british_india_minus_enclaves(1914, 1931)


def build_ind_1937_1947() -> ogr.Geometry:
    """British India 1937-1947 = CShapes 750's `1937-1947` step minus the two enclaves.

    Burma is already out of this step. 4,227,508 km2 measured on it, 4,223,262 after the cut,
    4,223,063 published."""
    return _british_india_minus_enclaves(1937, 1947)


def build_ind_1947_1949() -> ogr.Geometry:
    """India 1947-1949 = CShapes 750's `1947-1949` step minus the two enclaves.

    Post-partition India, and the last period that can be cut without a periodisation decision:
    it ends on 1949-01-04, five years before France ceded Pondicherry and twelve before India
    annexed Goa. 3,046,196 km2 in CShapes, 3,041,950 after the cut, 3,041,829 published."""
    return _british_india_minus_enclaves(1947, 1949)


def build_frin_1816_1954() -> ogr.Geometry:
    """French India 1816-1954 = the modern Puducherry union territory, GADM adm1 IND.27_1.

    Puducherry UT is the four southern establishments -- Pondicherry, Karikal, Mahe and Yanam --
    as six disjoint parts, which is why one adm1 feature covers all four.

        IND.27_1 Puducherry     547 km2
        the page declares       510 km2   -> +7.3%

    CHANDERNAGORE IS NOT INCLUDED, and the direction of the error is worth reading carefully.
    Chandernagore (~19 km2) was ceded in 1952 and merged into West Bengal, so it is not separable
    above adm3. Omitting it should make this polygon SMALLER than the declared 510, and instead it
    is 7% LARGER -- so modern Puducherry UT is about 13% bigger than the four historical enclaves
    it descends from. Both effects are inside the 25% tolerance and the row is `estimate`, which is
    what that status is for.

    Compare build_ptind_1816_1961(), Portuguese India, which needed two adm1 features for Goa and
    Daman-and-Diu.
    """
    return _gadm_adm1("IND.27_1")

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

    WEST PAPUA IS SUBTRACTED TOO, and the source is what settles it. Modern
    Indonesia includes Papua, but Netherlands New Guinea stayed Dutch until 1962, so
    subtracting only Java and Bali left 405,513 km2 of Dutch territory inside a
    1949-1951 Indonesian row -- 98.8% of NNG-1949-1963, which is the overlap
    whep#514 reported.

    The page's own polygon_area_km2 of 1,757,495 included Papua, so the recorded
    figure had to be settled against the territory rather than assumed correct. FAO's
    1952 yearbook lists the two as SEPARATE REPORTING UNITS:

        Indonesia (ASIA)     1947    1,904,350 km2
        New Guinea (ASIA)    1951      412,780 km2

    NNG-1949-1963 declares 410,361, a 0.6% match to FAO's New Guinea. The 1,904,350
    figure is a PRE-INDEPENDENCE 1947 total for the whole Dutch East Indies, which is
    how the anachronism entered the page: 1,757,495 is that total less Java and Bali.
    The Netherlands held West Papua until 1962 -- which is the entire reason
    NNG-1949-1963 exists as a row at all.

    PAPUA IS SUBTRACTED AS GADM PROVINCES, NOT AS NNG'S OWN CShapes FEATURE, and the
    reason is measured. Subtracting `_cshapes2_feature(851, 1955)` -- the feature
    NNG-1949-1963 binds to -- is the obvious choice, since cutting both rows from one
    source ought to keep them from drifting. It does not survive publication:

        minus CShapes 851             1,341,857 km2   n published NNG   341 km2
        minus GADM Papua provinces    1,335,103 km2   n published NNG     0 km2

    GADM's Papua coastline does not follow CShapes', so `_gadm_adm0("IDN")` minus 851
    leaves a hairline coastal RIM of GADM Papua behind -- 1,031 fragments, 6,140 km2,
    largest 268 km2. Every fragment is outside 851 by construction, so the unsimplified
    intersection really is zero; then build_database simplifies the two rows
    INDEPENDENTLY at 0.01 degrees (~1.1 km), the rim's edges wobble back across the
    boundary, and 341 km2 of double claim reappears in the published GeoPackage. Cutting
    GADM with GADM leaves no rim to wobble.

    It also fits the source better. FAO 1952 gives New Guinea 412,780 km2:

        GADM Papua + Papua Barat   412,305 km2   0.1%
        CShapes 851                410,361 km2   0.6%

    THE RESIDUAL IS NOW A GAP, NOT AN OVERLAP, and that is the intended direction.
    GADM Papua is ~1,900 km2 larger than CShapes 851, so that much coastal fringe is
    subtracted here while NNG-1949-1963 (still CShapes-bound) does not cover it, and it
    belongs to no polity. A gap of 1,900 km2 is strictly preferable to a double count of
    405,513: unassigned territory is visible and honest, whereas doubly-claimed territory
    silently inflates any area-weighted aggregate over it.
    """
    return _difference(
        _gadm_adm0("IDN"),
        build_idn_jvm_1949_1951(),
        build_idn_blb_1949_1951(),
        _gadm_adm1("IDN.22_1"),   # Papua Barat
        _gadm_adm1("IDN.23_1"),   # Papua
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


def build_gto_1884_1920() -> ogr.Geometry:
    """German Togoland 1884-1920 = the two mandates it was partitioned into, re-joined.

    French Togoland (CShapes gwcode 461, the 1922-1960 mandate step, 57,094 km2)
    UNION British Togoland (build_btl_1920_1957, 26,630 km2) = the whole of the
    former German colony as the 1919-1922 partition divided it.

    This is a PROXY, and the direction of its error is known: the union measures
    ~83.7k km2 against the ~87.2k km2 usually published for Deutsch-Togoland, i.e.
    4% low. The gap is not a missing piece -- both mandates are present -- it is
    that CShapes' generalised mandate outlines are individually a little tight
    (BTL alone is 21% below the ~33,771 km2 historical figure for the British
    portion, which its own page documents). No source in the priority stack
    carries the German colony as a feature of its own: CShapes 2.0 begins its Togo
    coverage with the 1922 mandate step, and Cliopatria has no Togoland polity.
    """
    return _union(_cshapes2_feature(461, 1930), build_btl_1920_1957())


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

    WHY IT WAS NOT REGISTERED UNTIL 2026-08-06 (history; it IS registered now, see the
    BUILDERS entry). Attaching this polygon made
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
    decision, so the recipe was kept here, verified and ready, while the row stayed in
    the polygon backlog until the typing question was settled. Issue 47 settled it: the
    row is typed `aggregate` (the MASG/PAPNG pattern for a combined reporting unit), the
    shadowing audit passes, and this builder was registered on 2026-08-06.
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


STATUTE_MILE_M = 1609.344
CZN_HALF_WIDTH_M = 5 * STATUTE_MILE_M  # 8,046.72 m -- the treaty's five miles each side
CZN_UTM = 32617                        # UTM zone 17N; the canal sits at 79.6-79.9W, 8.96-9.30N


def build_czn_1903_1979() -> ogr.Geometry:
    """Panama Canal Zone = the canal centreline buffered by five statute miles each side.

    THE RECIPE IS THE TREATY, not an approximation of it. Article II of the Hay-Bunau-Varilla
    Treaty (1903-11-18) grants the United States "a zone of land and land under water ... of the
    width of ten miles extending to the distance of five miles on each side of the center line of
    the route of the Canal". So the Zone is DEFINED as a 5-mile buffer of the canal centreline,
    and the only thing this builder needs from a source is that centreline.

    The centreline was believed unavailable here. The page's oq-polygon-construction said a
    faithful polygon "could be constructed from the historical treaty description (16 km wide strip
    centred on the canal centreline)" but that no source in data/geodata carried it, and the four
    sources it had queried (CShapes, Cliopatria, Paine's PCS, GADM adm1) indeed do not. It is in a
    FIFTH file nobody queried: Natural Earth 10m rivers/lake centrelines, shipped inside the
    Paine 2024 replication package, carries the "Panama Canal" as two line parts.

    MEASURED, and the deviation is one-directional and explained:

        NE centreline length            60.65 km
        5-mile buffer                1,175.9 km2   ESRI:54034
        conventionally stated        1,432    km2   (553 sq mi)
        deviation                      -17.9%

    The shortfall is NOT buffer distance; it is the two things the Zone held BEYOND the strip:
      * Gatun Lake. The Zone included the whole lake (~425 km2), much of which lies more than
        five miles from the centreline. The commonly quoted 553 sq mi is land AND water; the
        Zone's LAND area is usually given near 553-185 = 368 sq mi (~953 km2), which this
        1,176 km2 land-plus-water strip sits above, as it should.
      * The sea approaches, three marine miles out from each coast. NE's line stops at the
        coast: it ends at 9.304N against Cristobal's ~9.35N and 8.960N against Balboa's ~8.93N,
        so about 9 km of centreline, ~145 km2 of buffer, is missing at the ends.
    Nothing here is scaled to hit 1,432. Extending the line to invented termini, or widening the
    buffer until the area matched, would make the area check circular -- the FEZ-1943-1951 rule.

    NOT SUBTRACTED, and this is the known overstatement in the other direction: the treaty
    excludes "the cities of Panama and Colon", which sit at the two ends inside the strip. No
    fetched source has either city's 1903 limits (GADM has no PAN file at all), so they stay in.
    Both cities were small in 1903 and the two errors partly cancel; the net is still -17.9%.

    Reveals a false claim on a NEIGHBOUR's page, which is why it is recorded here as well as
    there: pan-1903-1979.md says its CShapes feature 95 covers Panama "excluding the
    US-administered Canal Zone strip". Measured, 95.9% of this Zone polygon (1,127 of 1,176 km2)
    is INSIDE CShapes 95 -- the feature does not exclude the Zone, and the 4.1% outside is the
    sea approaches, not an excluded enclave. So PAN-1903-1979 and CZN-1903-1979 overlap almost
    completely, and any area-weighted consumer summing both double-counts the Zone.
    """
    return _buffer_metres(_ne10m_river("Panama Canal"), CZN_HALF_WIDTH_M, CZN_UTM)


BUILDERS = [
    (
        "CZN-1903-1979",
        "Panama Canal Zone (US-administered)",
        build_czn_1903_1979,
        "Natural Earth 10m's 'Panama Canal' centreline buffered by five statute miles each side, "
        "which is the Hay-Bunau-Varilla Treaty's own definition of the Zone rather than a proxy "
        "for it = 1,175.9 km2 against the conventionally stated 1,432 (-17.9%). The shortfall is "
        "Gatun Lake beyond the five-mile strip plus the three-marine-mile sea approaches, both of "
        "which the Zone held and a centreline buffer cannot reach; Panama City and Colon, which "
        "the treaty excludes, are not subtracted because no fetched source has their limits. "
        "Unblocks 5 layer-B rows that were matched but spatially unusable (issue 155).",
    ),
    (
        "FCC-1862-1887",
        "French Cochinchina",
        build_fcc_1862_1887,
        "Cliopatria's Vietnam at 1855 (300,525 km2) MINUS Vietnam at 1860 (234,392), clipped to the "
        "Mekong-delta envelope (104-108.5E, 8-12.5N) = 66,039 km2 against the ~65,000 usually "
        "stated for Cochinchina (+1.6%). The MMR-LWR-1852-1885 pattern: what changed hands is the "
        "difference between the two steps bracketing the conquest. GADM cannot do it -- there is no "
        "VNM file in the fetched set -- and Cliopatria's 'French Indochina' is the whole federation "
        "at 11x this territory. Drops 238 km2 (0.36%) of step-boundary jitter on the central coast. "
        "Overstates 1862-1867, when France held only the three eastern provinces; Cliopatria puts "
        "the whole loss at its 1859 break. Unblocks 20 layer-B rows (issue 155).",
    ),
    (
        "IDN-BLB-1949-1951",
        "Bali and Lombok (within Indonesia, 1949-1951)",
        build_idn_blb_1949_1951,
        "Bali (adm1) union the five Lombok districts (adm2) = 10,160 km2 against a declared 10,505 "
        "(3.3%). The page's ids were IDN.1_1 (ACEH, 3,000 km away) plus Nusa Tenggara Barat, which "
        "is Lombok PLUS SUMBAWA -- 25,261 km2, 140% over, which is why this sat unregistered until "
        "the fetch script gained a targeted adm2 extract.",
    ),
    (
        "IDN-OTH-1949-1951",
        "Other islands (within Indonesia, 1949-1951)",
        build_idn_oth_1949_1951,
        "Indonesia minus Java, Bali/Lombok AND West Papua. FAO 1952 lists Netherlands New Guinea "
        "as its own reporting unit at 412,780 km2, and NNG-1949-1963 declares 410,361 (0.6%), so "
        "the source did not count West Papua inside Indonesia for 1949-1951 -- the Netherlands held "
        "it until 1962. Including it (PR 178) overlapped NNG by 405,513 km2, 98.8% of NNG, claiming "
        "every West Papuan cell twice.",
    ),
    (
        "FRIN-1816-1954",
        "French India (Etablissements francais dans l'Inde)",
        build_frin_1816_1954,
        "GADM adm1 IND.27_1, the modern Puducherry union territory = 547 km2 against a declared "
        "510 (+7.3%). Covers Pondicherry, Karikal, Mahe and Yanam as six disjoint parts. "
        "Chandernagore (~19 km2, merged into West Bengal in 1952) is not separable above adm3 and "
        "is excluded -- yet the polygon is still 7% LARGER than declared, so modern Puducherry UT "
        "is ~13% bigger than the historical enclaves.",
    ),
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
        "GTO-1884-1920",
        "German Togoland (1884-1920)",
        build_gto_1884_1920,
        "Union of CShapes 2.0 gwcode 461 at 1930 (French Togoland mandate, 57,094 "
        "km2) and the BTL-1920-1957 difference above (British Togoland, 26,630) = "
        "83,724 km2, against the ~87,200 km2 usually published for the German "
        "colony (4% low). The two mandates ARE the partition of German Togoland, so "
        "re-joining them is the only composition available: CShapes' Togo coverage "
        "starts at the 1922 mandate step and no other source in the stack carries "
        "Deutsch-Togoland as a feature. Recorded `proxy`, not `assigned`, because "
        "the outline is the 1922 mandate boundary pair rather than the 1884-1914 "
        "colonial boundary.",
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
        "AOI-1936-1941",
        "Italian East Africa (1936-1941)",
        build_aoi_1936_1941,
        "CShapes step 530/1907-1952 (Ethiopia without Eritrea, 1,127,556 km2) union "
        "531/1900-1941 (Eritrea, 120,897) union ITS-1908-1960 (Italian Somaliland, "
        "464,743) = 1,713,196 km2, the exact arithmetic sum because all three pairwise "
        "intersections are 0.000 km2. Against the page's declared 1,700,000 that is "
        "+0.78%, and against the 1,725,330 usually quoted for AOI, -0.70%. The recipe is "
        "the page's own oq-aoi-polygon-construction, unbuilt since the row was created "
        "while the row declared `constructed` — so it shipped with no geometry and "
        "received 10 layer-B rows with no territory (issue 155). The page's third id, "
        "cowcode 5200, is a DEPENDENCY feature absent from the registered "
        "sovereign-state distribution, which is why the Somali member comes from "
        "ITS-1908-1960's 520-minus-521 reconstruction — documented there as "
        "bit-identical to 5200.",
    ),
    (
        "TUR-1913-1914",
        "Turkiye (1913-1914)",
        build_tur_1913_1914,
        "CShapes 640's 1913-1914 step (1,784,488 km2) named by its bounds. The row previously "
        "used polygon_feature_year 1914, which resolves to the 1914-1918 step -- one that begins "
        "after the row ends -- publishing 1,705,971 against a declared 1,785,218 and making this "
        "row identical to TUR-1914-1918. No feature_year can name either 1913 step: both start in "
        "1913, so 1913 is an order-dependent tie. Issue 123.",
    ),
    (
        "POL-1919-1920",
        "Poland (1919-1920)",
        build_pol_1919_1920,
        "CShapes 290's 1919-1920 step (256,575 km2, gwsdate 1919-09-10, Treaty of Saint-Germain) "
        "named by its bounds. The row previously used polygon_feature_year 1919, which ties three "
        "candidates -- two of them starting in 1919 -- so shapefile row order picked the "
        "177,762 km2 post-Versailles step that the page rejects BY NAME for excluding Galicia: a "
        "live 44% shortfall, hidden from check A because polygon_area_km2 had been back-filled "
        "from the wrong geometry. No feature_year can name the wanted step (1919 is shared, 1920 "
        "resolves to the 1920-10-07 step, which begins after the row ends). Issue 100.",
    ),
    (
        "F206-2011-2025",
        "Sudan and South Sudan (combined reporting)",
        build_f206_2011_2025,
        "Union of CShapes 625 (Sudan) and 626 (South Sudan), the features the two members "
        "themselves bind, so the aggregate cannot drift from its parts: 2,486,805 km2 against "
        "SUD-1956-2011's 2,486,812, ratio 1.0000. Issue 139.",
    ),
    (
        "BWI-1833-1962",
        "British West Indies (colonial aggregate)",
        build_bwi_1833_1962,
        "Union of 11 GADM 4.1 adm0 territories as the page enumerates them: 32,912 km2 against "
        "34,766 declared (-5.3%, most of it the VGB/CYM/TCA the page excludes). JAM and TTO were "
        "fetched for this. Issues 3 and 155.",
    ),
    (
        "MMR-LWR-1852-1885",
        "British Lower Burma (1852-1885)",
        build_mmr_lwr_1852_1885,
        "Cliopatria 'Burma' @1850 (552,405 km2, before the Second Anglo-Burmese War) MINUS "
        "'Burma' @1855 (437,084 km2, Upper Burma after it) = 115,321 km2, within 0.6% of the "
        "page's declared 116,000. Replaces a GADM recipe that named Shan -- upper Burma, "
        "annexed 1885-87 -- in the slot its own table gives to Ayeyarwady. Issues 3 and 155.",
    ),
    (
        "BLI-1833-1960",
        "British Leeward Islands Colony",
        build_bli_1833_1960,
        "Union of GADM 4.1 adm0 Antigua and Barbuda, Saint Kitts and Nevis, Montserrat, "
        "Dominica and the British Virgin Islands: 1,727 km2 against 1,716 declared (0.6%). "
        "The recipe was already written in the page's polygon_feature_id with no builder to "
        "run it. Issues 3 and 155.",
    ),
    (
        "WIN-1833-1960",
        "British Windward Islands Colony",
        build_win_1833_1960,
        "Union of GADM 4.1 adm0 Grenada, Saint Lucia, Saint Vincent and Dominica: 2,126 km2 "
        "against FAO 1952's own 1950 group land-use total of 215.0 thousand ha = 2,150 km2 "
        "(1.1%). The composition is fixed by that measurement, not assumed -- the same table "
        "prints the three island sub-entries, which sum to 1,300 km2, and Dominica's 754 is "
        "the difference. The Leeward sibling BLI-1833-1960 existed and this one did not, so "
        "13 FAO rows had nowhere to route. Issue 18.",
    ),
    (
        "TRP-1943-1951",
        "British Military Administration of Tripolitania",
        build_trp_1943_1951,
        "Union of 9 GADM 4.1 adm1 shabiyat: Tripoli, Al Jifarah, Az Zawiyah, An Nuqat al "
        "Khams, Al Marqab, Misratah, Al Jabal al Gharbi, Nalut and Al Jufrah. 314,598 km2 "
        "against FAO 1952's 353,000 (-10.9%). Issue 156.",
    ),
    (
        "CYR-1949-1951",
        "Emirate of Cyrenaica",
        build_cyr_1949_1951,
        "Union of 8 GADM 4.1 adm1 shabiyat: Al Butnan, Darnah, Al Jabal al Akhdar, Al Marj, "
        "Benghazi, Al Wahat, Al Kufrah and Surt. 837,876 km2 against FAO 1952's 855,400 "
        "(-2.0%). Issue 156.",
    ),
    (
        "FEZ-1943-1951",
        "French Military Administration of Fezzan",
        build_fez_1943_1951,
        "Union of 5 GADM 4.1 adm1 shabiyat: Murzuq, Sabha, Wadi al Hayat, Wadi ash Shati' "
        "and Ghat. 463,596 km2 against FAO 1952's 551,100 (-15.9%), the largest deviation of "
        "the three and where GADM's Libya-wide 8.2% shortfall concentrates. Issue 156.",
    ),
    (
        "IND-1800-1886",
        "British India (to 1886)",
        build_ind_1800_1886,
        "Cliopatria 'British Raj' @1880 MINUS Ceylon (CShapes 780 @1948), Portuguese "
        "India and French India. The Cliopatria feature includes Ceylon, which was a "
        "separate Crown Colony from 1802 and never part of British India: 65,600 km2 "
        "claimed by both this row and LKA-1800-2025. Every CShapes-bound IND period "
        "correctly contains 0 km2 of Ceylon. Issue 84.",
    ),
    # The five CShapes-bound British India periods that end before the enclaves became Indian,
    # registered 2026-08-13 (issue 84). Each is the SAME CShapes 750 step the row was already
    # bound to, MINUS Portuguese India and French India -- 3,719 + 520 km2 that every one of them
    # claimed alongside PTIND-1816-1961 and FRIN-1816-1954. The cut itself leaves 0.00 km2 of
    # either enclave -- CShapes' India covers both GADM outlines completely -- but the PUBLISHED
    # polygons keep 13.6 and 47.2 km2, because write_gpkg() simplifies every boundary including
    # the new holes. 3,719 -> 13.6 and 520 -> 47.2, not to zero; see the helper's docstring.
    #
    # IND-1949-2025 IS DELIBERATELY ABSENT and keeps both enclaves. It spans 1949-2025, which
    # contains October 1954 (Pondicherry) and December 1961 (Goa): for part of that row the
    # enclaves really were Indian territory, so subtracting them for the whole span would trade
    # a 1949-1961 double claim for a 1961-2025 hole. Fixing it needs the row split at those
    # dates, and THAT SPLIT WAS CONSIDERED AND DECLINED on 2026-08-13 (issue 84): it renames the
    # modern-India polity code, which is referenced outside this repository (whep's
    # tests/testthat/test_build_cbs.R) and by two aliases that span the cut, for a 0.13%
    # correction -- while Sikkim, 6,988 km2 and wrong for 27 years, sits in the same CShapes step
    # untouched because no WHEP polity claims it. CShapes 750 has ONE step for 1949-2019 and it
    # encodes neither the 1961 nor the 1975 acquisition, so both halves of a split would need
    # constructed polygons and the later one would be the unchanged step. The 3,719 + 520 km2
    # overstatement is recorded on wiki/polities/ind-1949-2025.md and on both enclave pages.
    (
        "IND-1886-1893",
        "British India (1886-1893)",
        build_ind_1886_1893,
        "CShapes 750's 1886-1893 step MINUS Portuguese India and French India = 4,648,466 km2 "
        "from 4,652,712. The step's own span matches this row's exactly, so the only change is "
        "the enclaves.",
    ),
    (
        "IND-1893-1914",
        "India (1893-1914)",
        build_ind_1893_1914,
        "CShapes 750's 1899-1914 step MINUS the two enclaves = 4,815,549 km2 from 4,819,795. "
        "CShapes splits 1893-1914 into two steps of identical area; the row's existing binding "
        "to the later one is preserved.",
    ),
    (
        "IND-1914-1937",
        "India (1914-1937)",
        build_ind_1914_1937,
        "CShapes 750's 1914-1931 step MINUS the two enclaves = 4,890,210 km2 from 4,894,456. "
        "Named by its bounds because `polygon_feature_year: 1914` matches the 1899-1914 step "
        "too, and only exact-start preference separated them.",
    ),
    (
        "IND-1937-1947",
        "India (1937-1947)",
        build_ind_1937_1947,
        "CShapes 750's 1937-1947 step MINUS the two enclaves = 4,223,262 km2 from 4,227,508. "
        "Burma is already out of this step -- the 1937 separation is in CShapes, not in this "
        "recipe.",
    ),
    (
        "IND-1947-1949",
        "India (1947-1949)",
        build_ind_1947_1949,
        "CShapes 750's 1947-1949 step MINUS the two enclaves = 3,041,950 km2 from 3,046,196. "
        "The last period that ends before either annexation: 1949-01-04, five years before "
        "Pondicherry and twelve before Goa.",
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
