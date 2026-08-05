#!/usr/bin/env python3
"""Write data/final/polygon_feature_index.csv: the candidates each binding could match.

WHY. `validate_polygon_binding_determinism.py` asks whether a declared
`polygon_feature_id` + `polygon_feature_year` could have matched more than one source
feature, with the winner then decided by shapefile ROW ORDER. Answering that needs every
CANDIDATE feature -- but `data/geodata/**` is gitignored, and the committed
`polities_database.gpkg` holds only the feature that WAS chosen, which is exactly the
information the check cannot use.

So the gate could not run in CI at all. Its selftest case had to be removed, because the
harness correctly reported it as "PASSED a mutation it claims to catch" (issue 103).

This writes the small slice the check needs: for every (source, id) the wiki actually
references, every feature carrying that id, IN FILE ORDER, with its temporal span and
area. Roughly a thousand rows against the 13 MB GeoPackage already committed.

WHAT `row_order` IS FOR. It is not decoration. The defect being detected is that
`find_feature` returns `exact[0]` -- the FIRST match -- so reproducing its choice requires
knowing which feature the source lists first. Sorting this file would destroy the only
column that matters.

WHY `area_km2` IS HERE. The useful output is not "this binding is order-dependent" but
"and its candidates differ by 1.99x". Of 25 order-dependent bindings, 9 have candidates
identical in area and are harmless today, while 16 differ and can silently change on a
re-fetch (issue 100). Without areas the gate would report 25 undifferentiated items.

Usage:
  python3 scripts/write_feature_index.py [--check]

`--check` exits 1 if the committed index is stale, without writing, for CI.
"""
import argparse
import csv
import os
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(REPO, "scripts/sources.yaml")
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
OUT = os.path.join(REPO, "data/final/polygon_feature_index.csv")
COLUMNS = ["source", "feature_id", "row_order", "start_year", "end_year", "area_km2"]
EQUAL_AREA = "+proj=cea +lat_ts=0 +lon_0=0 +units=m"


def build():
    from osgeo import ogr, osr
    ogr.UseExceptions()
    osr.UseExceptions()

    with open(SOURCES, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh).get("sources", {})
    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # Which (source, id) pairs does the wiki actually reference? Indexing every feature of
    # every source would be large and pointless -- a binding can only be ambiguous among
    # features sharing the id it declares.
    wanted = {}
    for r in rows:
        slug = (r.get("polygon_source") or "").strip()
        fid = (r.get("polygon_feature_id") or "").strip()
        if slug and slug != "none" and fid:
            wanted.setdefault(slug, set()).add(fid)

    out = []
    unknown = []      # a polygon_source that names no source at all -- a DATA defect,
                      # permanent, and not a reason to distrust the index
    unfetched = []    # a real source whose file is absent -- ENVIRONMENTAL, and the only
                      # thing that makes the index unverifiable
    for slug in sorted(wanted):
        entry = cfg.get(slug)
        if entry is None:
            unknown.append(slug)
            continue
        path = os.path.join(REPO, entry["file"])
        if not os.path.exists(path):
            unfetched.append(slug)
            continue
        ds = ogr.Open(path)
        lyr = ds.GetLayer()
        src_ref = lyr.GetSpatialRef()
        tgt = osr.SpatialReference()
        tgt.ImportFromProj4(EQUAL_AREA)
        tr = osr.CoordinateTransformation(src_ref, tgt) if src_ref else None
        temporal = entry.get("temporal") or {}
        ids = wanted[slug]
        int_ids = entry.get("id_type") == "int"
        order = 0
        lyr.ResetReading()
        for feat in lyr:
            v = feat.GetField(entry["id_column"])
            if v is None:
                order += 1
                continue
            key = str(int(v)) if int_ids and str(v).lstrip("-").isdigit() else str(v)
            match = key in ids or str(v) in ids
            if not match:
                order += 1
                continue
            s = e = ""
            if temporal:
                sv = feat.GetField(temporal["start_column"])
                ev = feat.GetField(temporal["end_column"])
                if sv is not None:
                    s = int(str(sv)[:4])
                if ev is not None:
                    e = int(str(ev)[:4])
            area = ""
            g = feat.GetGeometryRef()
            if g is not None and tr is not None:
                gg = g.Clone()
                try:
                    gg.Transform(tr)
                    area = round(gg.GetArea() / 1e6, 1)
                except Exception:
                    area = ""
            out.append({
                "source": slug, "feature_id": key, "row_order": order,
                "start_year": s, "end_year": e, "area_km2": area,
            })
            order += 1
    return out, unknown, unfetched


def render(recs):
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(recs)
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify without writing; exit 1 if stale")
    A = ap.parse_args()

    try:
        from osgeo import ogr  # noqa: F401
    except ImportError as exc:
        print(f"SKIP: GDAL unavailable ({exc})")
        return 0

    recs, unknown, unfetched = build()
    text = render(recs)

    if A.check:
        if not os.path.exists(OUT):
            print(f"--check: FAIL — {OUT} missing; run scripts/write_feature_index.py")
            return 1
        with open(OUT, encoding="utf-8") as fh:
            have = fh.read()
        if unfetched:
            # Rebuilding from a partial set of sources would DELETE the rows of every
            # source that is not fetched, and --check would then call the committed file
            # stale. In CI nothing is fetched, so this is the normal case, not an error.
            #
            # `unknown` deliberately does NOT trigger this. Four polygon_source values in
            # the wiki name no source in sources.yaml at all, so they are skipped on every
            # run including a fully-fetched one -- treating them as "unavailable" would
            # make --check skip permanently and verify nothing, which is how a check
            # becomes decoration.
            print(f"--check: SKIP — cannot verify, {len(unfetched)} source(s) not "
                  f"fetched: {unfetched}")
            return 0
        if have == text:
            print(f"--check: PASS — feature index is current ({len(recs)} rows)")
            return 0
        print("--check: FAIL — data/final/polygon_feature_index.csv is stale; run "
              "python3 scripts/write_feature_index.py")
        return 1

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote data/final/polygon_feature_index.csv: {len(recs)} rows")
    if unfetched:
        print(f"  not fetched, so absent from the index: {unfetched}")
    if unknown:
        print(f"  polygon_source values naming no source in sources.yaml: {unknown}")
        print("    (a data defect, not a fetch problem -- build_database reports these too)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
