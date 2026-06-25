#!/usr/bin/env python3
"""
Build data/geodata/constructed/constructed.geojson from other fetched sources.

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
OUT = REPO_ROOT / "data/geodata/constructed/constructed.geojson"


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


def _union(*geoms: ogr.Geometry) -> ogr.Geometry:
    acc = geoms[0].Clone()
    for g in geoms[1:]:
        acc = acc.Union(g)
    if acc.GetGeometryType() != ogr.wkbMultiPolygon:
        acc = ogr.ForceToMultiPolygon(acc)
    return acc


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


# (polity_code, polity_name, builder-callable, provenance note)
BUILDERS = [
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
]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    drv = ogr.GetDriverByName("GeoJSON")
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
