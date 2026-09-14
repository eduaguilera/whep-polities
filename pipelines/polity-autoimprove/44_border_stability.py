#!/usr/bin/env python3
"""Did a polity's border actually MOVE during its span? Ask a year-stamped source instead of
guessing from the length of the span.

WHY THIS EXISTS. `04_territory_basis.py` labels a row `assumed_constant` on this rule:

    if span >= 25 and drift >= 15:  -> "assumed_constant"   # "borders may have changed"

That looks only at how LONG the span is. It never compares a border to anything, so it cannot
distinguish a long span whose border genuinely moved from a long span whose border was stable --
and 933 of 1,216 rows (77%) carry the label, which makes it a statement about our span lengths
rather than about our territories.

CShapes 2.0 can answer the question it is guessing at, because every feature is stamped with the
dates it is valid for. Worked through on the row with the most layer-B data behind it,
`USA-1867-1959` (8,231 rows):

    CShapes gwcode 2, the borders it records
      1886-01-01 .. 1959-01-02    7,939,971 km2   Alaska no   Hawaii no
      1959-01-03 .. 1959-08-20    9,446,212 km2   Alaska yes  Hawaii no
      1959-08-21 .. 2019-12-31    9,462,898 km2   Alaska yes  Hawaii yes

ONE border from 1886 to 1959. So the reference says the US border did not move in those 73 years
and the `assumed_constant` warning on that row is a false alarm -- holding one border across the
span is what the reference does too.

AND THE SAME LOOKUP FINDS A REAL PROBLEM THE SPAN RULE CANNOT SEE. Our row carries cliopatria's
1880 polygon at 8,906,417 km2, which is 966,446 km2 (+12.2%) larger than CShapes for the same
years -- not because a border moved, but because the two sources disagree about whether Alaska
was American before statehood. Cliopatria counts territory from the 1867 purchase; CShapes admits
it at statehood in 1959. Our own 1959 split follows the statehood convention while the polygon
either side of it follows the territorial one, so the pair publishes a 6.2% area step at 1959
where no border moved at all.

So this stage emits two measurements per row, and they are independent:

  border_verdict    what the year-stamped reference says happened INSIDE our span
                    stable_confirmed  one reference border covers the whole span -> a single
                                      polygon is faithful, and `assumed_constant` is unfounded
                    changed           2+ reference borders -> the border really did move, and
                                      `max_step_ratio` says by how much at the largest step
                    partial_span      the reference covers only part of the span
                    no_reference      the reference has no border for this code in these years
                                      (it tracks the state system, so this is normal for
                                      colonies, subnational rows and pre-state polities)

  source_gap_pct    our polygon's area against the reference border for the SAME years. A large
                    gap with `stable_confirmed` is a convention disagreement, not history --
                    exactly the Alaska case, and invisible to every span-based rule.

Neither measurement overrules a polygon choice on its own: a big `source_gap_pct` can mean the
reference is the wrong authority for that row (CShapes excludes colonial holdings that Cliopatria
and Paine include by design). It says which rows deserve a look, and what to look at.

Writes state/border_stability.csv. Needs data/geodata/cshapes-2.0, which is gitignored, so
`--check` SKIPS where that source is absent -- the same rule as scripts/write_feature_index.py.

Usage:
  python3 pipelines/polity-autoimprove/44_border_stability.py [--check]
"""
import os
import sys
import warnings

import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
CSHAPES = os.path.join(REPO, "data/geodata/cshapes-2.0/CShapes-2.0.shp")
DEST = os.path.join(H, "border_stability.csv")

# Equal-area, and the SAME projection the rest of this repo measures in -- see
# scripts/validate_area_convention.py. Mixing conventions here would show up as a
# source gap that is really a projection difference.
EQ_AREA = "ESRI:54034"
FIELDS = ["polity_code", "start_year", "end_year", "cow_code", "polity_type",
          "our_source", "our_km2", "border_verdict", "n_reference_borders",
          "reference_covers", "reference_bookkeeping_steps", "reference_km2_at_start",
          "reference_km2_at_end", "max_step_ratio", "change_years", "reference_iou",
          "source_gap_pct"]

# A CShapES feature can clip our span by a matter of DAYS and still share a calendar year with
# it: gwcode 2's pre-statehood border ends 1959-01-02, so on a year-granular test it "overlaps"
# USA-1959-2025 and was picked as that row's reference -- comparing a 1959+ polygon against the
# 1886 border and reporting a 19% gap that is pure date arithmetic. A border the polity actually
# had is one it had for at least a year.
MIN_OVERLAP_DAYS = 365

# CShapES OPENS A NEW FEATURE FOR NON-TERRITORIAL CHANGES TOO -- a moved capital starts a fresh
# row with the SAME geometry. gwcode 750 (India) has eight features between 1886 and 2019 and the
# symmetric difference across the 1899 and 1931 boundaries is exactly 0.0: nothing moved. Counting
# features instead of distinct borders reported a border move for IND-1914-1937, IND-1893-1914,
# PAK-1949-1971, ROU-1913-1918 and six others, every one of them at a step ratio of 1.000x.
# So consecutive features are ONE border when their shapes differ by less than this share.
SAME_BORDER_TOL = 0.001

# `cow_code` IS NOT A TERRITORY KEY, and joining on it alone compares the wrong ground. Colonial
# and subnational rows carry their METROPOLE's code -- French India 220 (France), Portuguese India
# 235 (Portugal), Hyderabad State 750 (India) -- and two rows carry a code for the wrong country
# outright: IDN-1800-1889 and IDN-1889-1945 are 750 (India, not Indonesia's 850) and NNI-1904-1913
# is 385 (Norway, not Nigeria's 475). Others are a legitimate SUBSET of the reference state, like
# Tripolitania and Fezzan against Libya, or the Ottoman span against modern Turkey.
#
# Every one of those pairs still yields an area and a ratio, which is the danger: the number looks
# like a measurement of our polygon and is a measurement of somebody else's. So the join must prove
# itself geometrically -- intersection over union against the reference border -- and say
# `reference_mismatch` instead of publishing a gap it cannot mean. 12 of 426 referenced rows fail
# it. The threshold is deliberately loose: Sweden 1814-1905 sits at 0.574 against CShapes' Sweden-
# Norway union and MUST stay visible, because that gap is the finding.
MIN_REFERENCE_IOU = 0.5


# BUILD_DATABASE IS NOT REPRODUCIBLE, so an exact comparison of areas fails for reasons that have
# nothing to do with borders. Rebuilding the GPKG from unchanged inputs moves 54 of 1,186 geometries
# (4.6%), worst case MEX-TAMAULIPAS-1824-2025 by 4.386 km2 and FJI-1800-2025 by 0.0121% of its area.
# The first version of this check compared rounded integers and duly failed with "20 rows differ by
# 1 km2" after an edge edit that touched no geometry at all. Filed separately -- the instability is
# in the build, not here.
#
# So numeric columns compare within a tolerance, absolute OR relative, whichever is looser, with
# roughly 2x headroom over the drift measured above. Everything else compares exactly, so the check
# still fails on what it is for: a row appearing or vanishing, a verdict flipping, a change year
# moving, a reference becoming incomparable.
NUMERIC_TOL = {                       # column -> (absolute, relative fraction)
    "our_km2": (10.0, 0.0003),
    "reference_km2_at_start": (10.0, 0.0003),
    "reference_km2_at_end": (10.0, 0.0003),
    "source_gap_pct": (0.05, 0.0),    # percentage points; drift propagates at ~0.012pp
    "reference_iou": (0.002, 0.0),
    "max_step_ratio": (0.002, 0.0),
}


def _close(a, b, tol):
    """Equal within tolerance, treating blanks as values in their own right.

    A blank becoming a number (or the reverse) is a real change -- the reference appeared, or
    stopped being comparable -- so it must NOT pass as "close".
    """
    a, b = (a or "").strip(), (b or "").strip()
    if a == b:
        return True
    if not a or not b:
        return False
    try:
        x, y = float(a), float(b)
    except ValueError:
        return False
    absolute, relative = tol
    return abs(x - y) <= max(absolute, relative * max(abs(x), abs(y)))


def _iou(a, b):
    """Intersection over union, tolerant of the invalid geometries both sides contain.

    Returns None when the operation cannot be done at all -- a mismatch must not be ASSUMED
    from a topology error, since that would silently downgrade a row for a reason that has
    nothing to do with its territory.
    """
    try:
        if not a.is_valid:
            a = make_valid(a)
        if not b.is_valid:
            b = make_valid(b)
        u = a.union(b).area
        return (a.intersection(b).area / u) if u else None
    except Exception:
        return None


def _int(v):
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return None


def build() -> pd.DataFrame:
    if not os.path.exists(CSHAPES):
        return pd.DataFrame(columns=FIELDS)

    cs = gpd.read_file(CSHAPES)
    cs["gwcode"] = cs["gwcode"].astype(int)
    cs = cs.to_crs(EQ_AREA)
    cs["km2"] = cs.geometry.area / 1e6
    by_code = {code: g.sort_values("gwsdate") for code, g in cs.groupby("gwcode")}

    pol = pd.read_csv(POLDB, keep_default_na=False, dtype=str)
    ours, ours_geom = {}, {}
    if os.path.exists(GPKG):
        g = gpd.read_file(GPKG).to_crs(EQ_AREA)
        for _, r in g.iterrows():
            if r.geometry is not None and not r.geometry.is_empty:
                ours[r["polity_code"]] = r.geometry.area / 1e6
                ours_geom[r["polity_code"]] = r.geometry

    rows = []
    for _, p in pol.iterrows():
        s, e = _int(p["start_year"]), _int(p["end_year"])
        if s is None or e is None:
            continue
        last = e - 1                      # end_year is EXCLUSIVE in this repo
        cow = _int(p["cow_code"])
        our_km2 = ours.get(p["polity_code"])
        rec = {"polity_code": p["polity_code"], "start_year": s, "end_year": e,
               "cow_code": "" if cow is None else cow, "polity_type": p["polity_type"],
               "our_source": p["polygon_source"],
               "our_km2": "" if our_km2 is None else round(our_km2),
               "border_verdict": "no_reference", "n_reference_borders": 0,
               "reference_covers": "", "reference_bookkeeping_steps": 0,
               "reference_km2_at_start": "", "reference_km2_at_end": "",
               "max_step_ratio": "", "change_years": "", "reference_iou": "",
               "source_gap_pct": ""}

        feats = by_code.get(cow) if cow is not None else None
        borders = []
        if feats is not None:
            lo = pd.Timestamp(year=s, month=1, day=1)
            hi = pd.Timestamp(year=last, month=12, day=31)
            ov = feats.copy()
            ov["overlap_days"] = (ov[["gwedate"]].clip(upper=hi)["gwedate"]
                                  - ov[["gwsdate"]].clip(lower=lo)["gwsdate"]).dt.days
            ov = ov[ov["overlap_days"] >= MIN_OVERLAP_DAYS].sort_values("gwsdate")
            # collapse consecutive features that describe the SAME shape
            borders = []
            for _, f in ov.iterrows():
                if borders:
                    prev = borders[-1]["geom"]
                    denom = max(prev.area, f.geometry.area)
                    share = (prev.symmetric_difference(f.geometry).area / denom
                             if denom else 0.0)
                    if share < SAME_BORDER_TOL:
                        borders[-1]["gweyear"] = f["gweyear"]
                        borders[-1]["steps"] += 1
                        continue
                borders.append({"geom": f.geometry, "km2": f["km2"],
                                "gwsyear": f["gwsyear"], "gweyear": f["gweyear"], "steps": 1})
            rec["n_reference_borders"] = len(borders)
            rec["reference_bookkeeping_steps"] = len(ov) - len(borders)
            if borders:
                c0 = max(borders[0]["gwsyear"], s)
                c1 = min(borders[-1]["gweyear"], last)
                rec["reference_covers"] = f"{int(c0)}-{int(c1)}"
                rec["reference_km2_at_start"] = round(borders[0]["km2"])
                rec["reference_km2_at_end"] = round(borders[-1]["km2"])
            if len(borders) == 1:
                b = borders[0]
                whole = (b["gwsyear"] <= s) and (b["gweyear"] >= last)
                rec["border_verdict"] = "stable_confirmed" if whole else "stable_where_covered"
            elif len(borders) > 1:
                rec["border_verdict"] = "changed"
                areas = [b["km2"] for b in borders]
                steps = [max(x, y) / min(x, y) for x, y in zip(areas, areas[1:])
                         if min(x, y) > 0]
                rec["max_step_ratio"] = round(max(steps), 3) if steps else ""
                rec["change_years"] = ";".join(
                    str(int(b["gwsyear"])) for b in borders[1:]
                    if s <= int(b["gwsyear"]) <= last)

        ref = rec["reference_km2_at_start"]
        if our_km2 and isinstance(ref, (int, float)) and ref:
            rec["source_gap_pct"] = round((our_km2 - ref) / ref * 100, 2)

        # does the reference describe THIS ground? Cheap rejects first: no geometry either side,
        # or no reference at all.
        og = ours_geom.get(p["polity_code"])
        if og is not None and borders:
            iou = _iou(og, borders[0]["geom"])
            if iou is not None:
                rec["reference_iou"] = round(iou, 3)
                if iou < MIN_REFERENCE_IOU:
                    rec["border_verdict"] = "reference_mismatch"
        rows.append(rec)

    return pd.DataFrame(rows, columns=FIELDS)


def main() -> int:
    check = "--check" in sys.argv
    if not os.path.exists(CSHAPES):
        # A CHECK MAY DEGRADE ON A MISSING INPUT (04_territory_basis.py's rule): CShapes is
        # gitignored, so CI cannot reproduce a single column here. Skipping is honest;
        # rebuilding from nothing and writing it would delete every row.
        print(f"SKIP: {os.path.relpath(CSHAPES, REPO)} absent (gitignored); "
              f"this measurement verifies where the source is fetched")
        return 0

    out = build()
    if check:
        if not os.path.exists(DEST):
            print(f"FAIL: {DEST} missing; run this script without --check")
            return 1
        committed = pd.read_csv(DEST, keep_default_na=False, dtype=str)
        fresh = pd.read_csv(pd.io.common.StringIO(out.to_csv(index=False)),
                            keep_default_na=False, dtype=str)
        if list(committed.columns) != list(fresh.columns):
            print(f"FAIL: columns differ\n  committed {list(committed.columns)}\n"
                  f"  regenerated {list(fresh.columns)}")
            return 1
        c = committed.set_index("polity_code")
        f = fresh.set_index("polity_code")
        missing = sorted(set(f.index) - set(c.index))
        extra = sorted(set(c.index) - set(f.index))
        problems = []
        if missing:
            problems.append(f"{len(missing)} polity(ies) absent from the committed file: "
                            f"{missing[:6]}")
        if extra:
            problems.append(f"{len(extra)} committed row(s) no longer in the database: "
                            f"{extra[:6]}")
        both = [i for i in f.index if i in c.index]
        for col in f.columns:
            tol = NUMERIC_TOL.get(col)
            if tol is None:
                diff = [i for i in both if c.loc[i, col] != f.loc[i, col]]
            else:
                diff = [i for i in both if not _close(c.loc[i, col], f.loc[i, col], tol)]
            if diff:
                i = diff[0]
                problems.append(f"{col}: {len(diff)} row(s) differ, e.g. {i} committed "
                                f"{c.loc[i, col]!r} != regenerated {f.loc[i, col]!r}"
                                + (f" (tolerance abs {tol[0]} / rel {tol[1]:.2%})"
                                   if tol is not None else ""))
        if problems:
            print("FAIL: border_stability.csv no longer describes the current database")
            for p in problems:
                print(f"  {p}")
            print(f"rerun: python3 {os.path.relpath(__file__, REPO)}")
            return 1
        print(f"OK: border_stability.csv matches a fresh measurement ({len(f)} rows)")
        return 0

    tmp = DEST + ".tmp"
    out.to_csv(tmp, index=False)
    os.replace(tmp, DEST)
    print(f"measured {len(out)} polities -> state/border_stability.csv\n")
    v = out["border_verdict"].value_counts()
    for k in ("stable_confirmed", "stable_where_covered", "changed",
              "reference_mismatch", "no_reference"):
        if k in v:
            print(f"   {k:18} {v[k]:5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
