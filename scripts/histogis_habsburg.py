#!/usr/bin/env python3
"""
Integrate HistoGIS 1860 Habsburg crownlands into Cisleithania and Transleithania polygons.

Source: HistoGIS (ACDH-CH), Austrian Empire Crownlands 1860
URL: https://histogis.acdh.oeaw.ac.at/shp-samples
License: Open access (Austrian public institution, academic use)

Creates two dissolved polygons:
  - AUT-1800-1918 = Cisleithania (Austrian half of Austria-Hungary)
  - HUN-1800-1918 = Transleithania (Hungarian half of Austria-Hungary)

The 1860 shapefile represents boundaries just before the 1866 loss of Venetia
and the 1867 Ausgleich. Since the Ausgleich was constitutional (not territorial),
the crownland boundaries are valid for both the 1800-1867 Austrian Empire period
and the 1867-1918 Dual Monarchy period, with these exceptions:
  - Venetia (feature 12) excluded: lost to Italy 1866
  - Voivodeship of Serbia/Banat (feature 18): formally abolished 1860, merged
    into Hungary — assigned to Transleithania
  - Military Frontier (feature 19): dissolved 1881, incorporated into Croatia
    (Transleithania) — assigned to Transleithania
"""

import sys
from osgeo import ogr, osr

SHP = "data/geodata/histogis/crownlands_1860/austrian_empire_adm2_crownlands_1860.shp"
OUT_GPKG = "data/geodata/histogis/habsburg_cisleithania_transleithania.gpkg"

# Crownland index → half assignment
# 'C' = Cisleithania, 'T' = Transleithania, 'X' = exclude
ASSIGNMENTS = {
    0:  ('C', 'Erzherzogtum Österreich unter der Enns'),   # Lower Austria
    1:  ('C', 'Herzogtum Steiermark'),                      # Styria
    2:  ('C', 'Herzogtum Ober- und Niederschlesien'),       # Silesia
    3:  ('C', 'Königreich Dalmatien'),                      # Dalmatia
    4:  ('C', 'Herzogtum Salzburg'),                        # Salzburg
    5:  ('C', 'Königreich Böhmen'),                         # Bohemia
    6:  ('C', 'Markgrafschaft Mähren'),                     # Moravia
    7:  ('C', 'Herzogtum Kärnten'),                         # Carinthia
    8:  ('C', 'Herzogtum Krain'),                           # Carniola
    9:  ('C', 'Erzherzogtum Österreich ob der Enns'),       # Upper Austria
    10: ('T', 'Königreich Ungarn'),                          # Hungary
    11: ('T', 'Großfürstentum Siebenbürgen'),                # Transylvania (merged 1867)
    12: ('X', 'Königreich Venetien'),                        # Venetia — lost 1866, excluded
    13: ('T', 'Königreich Kroatien und Slawonien'),          # Croatia-Slavonia
    14: ('C', 'Küstenland'),                                 # Gorizia, Trieste, Istria
    15: ('C', 'Königreich Galizien und Lodomerien'),         # Galicia
    16: ('C', 'Herzogtum Bukowina'),                         # Bukovina
    17: ('C', 'Gefürstete Grafschaft Tirol mit dem Lande Vorarlberg'),  # Tyrol+Vorarlberg
    18: ('T', 'Woiwodschaft Serbien und Temeser Banat'),     # Banat — merged into Hungary 1860
    19: ('T', 'Militärgrenze'),                              # Military Frontier — Croatia 1881
}

def reproject_to_wgs84(geom, src_srs):
    # Force traditional GIS axis order (lon, lat) for both source and target.
    # Without this, EPSG:4326 uses authority-compliant (lat, lon) which
    # produces swapped coordinates when read by most GIS tools (including R sf).
    src_srs_trad = src_srs.Clone()
    src_srs_trad.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    tgt_srs = osr.SpatialReference()
    tgt_srs.ImportFromEPSG(4326)
    tgt_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transform = osr.CoordinateTransformation(src_srs_trad, tgt_srs)
    geom.Transform(transform)
    return geom

def main():
    drv = ogr.GetDriverByName("ESRI Shapefile")
    src_ds = drv.Open(SHP, 0)
    if not src_ds:
        print(f"ERROR: Cannot open {SHP}", file=sys.stderr)
        sys.exit(1)

    src_layer = src_ds.GetLayer()
    src_srs = src_layer.GetSpatialRef()

    cis_geoms = []
    trans_geoms = []

    for feat in src_layer:
        fid = feat.GetFID()
        half, label = ASSIGNMENTS[fid]
        geom = feat.GetGeometryRef().Clone()
        geom = reproject_to_wgs84(geom, src_srs)
        if half == 'C':
            cis_geoms.append(geom)
            print(f"  Cisleithania: {label}")
        elif half == 'T':
            trans_geoms.append(geom)
            print(f"  Transleithania: {label}")
        else:
            print(f"  EXCLUDED: {label}")

    def dissolve(geoms):
        union = geoms[0]
        for g in geoms[1:]:
            union = union.Union(g)
        return union

    print("\nDissolving Cisleithania...")
    cis_union = dissolve(cis_geoms)
    print("Dissolving Transleithania...")
    trans_union = dissolve(trans_geoms)

    # Write to GeoPackage
    gpkg_drv = ogr.GetDriverByName("GPKG")
    if gpkg_drv is None:
        print("ERROR: GeoPackage driver not available", file=sys.stderr)
        sys.exit(1)

    import os
    if os.path.exists(OUT_GPKG):
        gpkg_drv.DeleteDataSource(OUT_GPKG)

    out_ds = gpkg_drv.CreateDataSource(OUT_GPKG)
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    layer = out_ds.CreateLayer("habsburg_halves", wgs84, ogr.wkbMultiPolygon)
    layer.CreateField(ogr.FieldDefn("polity_code", ogr.OFTString))
    layer.CreateField(ogr.FieldDefn("polity_name", ogr.OFTString))
    layer.CreateField(ogr.FieldDefn("half", ogr.OFTString))
    layer.CreateField(ogr.FieldDefn("source", ogr.OFTString))
    layer.CreateField(ogr.FieldDefn("source_year", ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn("notes", ogr.OFTString))

    defn = layer.GetLayerDefn()

    def add_feature(polity_code, polity_name, half, geom, notes=""):
        feat = ogr.Feature(defn)
        feat.SetField("polity_code", polity_code)
        feat.SetField("polity_name", polity_name)
        feat.SetField("half", half)
        feat.SetField("source", "HistoGIS (ACDH-CH) Austrian Empire Crownlands 1860")
        feat.SetField("source_year", 1860)
        feat.SetField("notes", notes)
        if geom.GetGeometryType() != ogr.wkbMultiPolygon:
            geom = ogr.ForceToMultiPolygon(geom)
        feat.SetGeometry(geom)
        layer.CreateFeature(feat)

    add_feature(
        "AUT-1800-1918",
        "Austria (Cisleithania)",
        "Cisleithania",
        cis_union,
        "Dissolved from 14 crownlands. Venetia excluded (lost 1866). "
        "Valid for 1800-1918 Habsburg Austrian lands. Source year 1860 "
        "(pre-Ausgleich, but Ausgleich was constitutional not territorial)."
    )

    add_feature(
        "HUN-1800-1918",
        "Kingdom of Hungary (Transleithania)",
        "Transleithania",
        trans_union,
        "Dissolved from: Hungary, Transylvania, Croatia-Slavonia, "
        "Banat/Voivodeship (merged 1860), Military Frontier (merged 1881). "
        "Valid for 1800-1918 Habsburg Hungarian lands."
    )

    out_ds = None
    src_ds = None

    cis_area_km2 = cis_union.GetArea() / 1e6
    trans_area_km2 = trans_union.GetArea() / 1e6
    print(f"\nResults:")
    print(f"  Cisleithania  (AUT-1800-1918): {cis_area_km2:,.0f} km² (approx, WGS84 degrees²×111²)")
    print(f"  Transleithania (HUN-1800-1918): {trans_area_km2:,.0f} km² (approx)")
    print(f"\nOutput: {OUT_GPKG}")
    print("Done.")

if __name__ == "__main__":
    main()
