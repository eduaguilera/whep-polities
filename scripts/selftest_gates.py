#!/usr/bin/env python3
"""Prove the gates can fail.

Twenty-one validators guard this database and every one of them passes. That is
the intended state and it is also indistinguishable, from the outside, from
twenty-one validators that cannot fail. A gate whose criteria no real row can
satisfy prints PASS forever and protects nothing.

The distinction is not decidable by reading the code -- I tried, and reasoned
myself into two wrong conclusions in a row. It is decidable by mutation: inject a
defect of exactly the shape a gate claims to catch, and require that gate to
FAIL. That is what this script does.

It matters because the sibling repository has already paid for an assertion that
never executed. A bidirectional baseline there sat twelve fixes out of date while
its test skipped on every run, local and CI, because the file it reads lives on
an unmerged branch. The test was correct and simply not running. Nothing in a
green summary line distinguishes "passed" from "did not execute", so the only
defence is to demand a failure on demand.

Each case below stages a scratch repo whose scripts/ is a copy and whose
data/final/ holds a MUTATED GeoPackage, then runs one gate against it and
requires a non-zero exit. The real data is never written to.

WHAT MUTATION TESTING ESTABLISHED, beyond that the gates fire:

  The containment check normalises overlap by the SMALLER polygon, so a successor
  bound to a wrong feature strictly inside the right territory scores ~1.0 and
  passes. That looks like a hole, and symmetrising it -- also normalising by the
  larger -- was the obvious fix. Measuring first showed the fix would be a
  mistake: 26 consecutive pairs pass the smaller-normalised metric and fail a
  larger-normalised one, and they are overwhelmingly REAL HISTORY. USA-1848-1867
  -> USA-1867-1959 is the Alaska purchase (3.5M -> 8.9M km2); ISR-1948-1967 ->
  ISR-1967-1979 is the Six-Day War; HUN-1918-1919 -> HUN-1920-1938 is the Treaty
  of Trianon; the remainder is colonial expansion into the hinterland. The
  smaller-normalised metric is invariant to legitimate expansion and contraction,
  which is precisely why it is the right one, and 26 historical facts would have
  been baselined as defects to "close" a hole.

  The hole is closed by a different instrument. validate_family_areas measures
  the same shrink at 222x its family median and names polygon_feature_id as the
  thing to check. Position and magnitude are covered by two gates, each blind to
  what the other sees. Case 3 pins that, so a future change to either cannot
  quietly leave the shrink case uncovered.

Usage:
  python3 scripts/selftest_gates.py            # all cases
  python3 scripts/selftest_gates.py --case 2   # one case, by number
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
CSV = os.path.join(REPO, "data/final/polities_database.csv")


def stage(gate: str, extra: tuple = ()) -> str:
    """A scratch repo holding one gate, its baseline, and a writable data/final."""
    root = tempfile.mkdtemp(prefix="selftest-gates-")
    os.makedirs(os.path.join(root, "scripts"))
    os.makedirs(os.path.join(root, "data/final"))
    for name in (gate, *extra):
        src = os.path.join(REPO, "scripts", name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(root, "scripts", name))
    baseline = gate.replace(".py", "_baseline.txt")
    src = os.path.join(REPO, "scripts", baseline)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(root, "scripts", baseline))
    # The CSV is only read for wiki_status, so a symlink to the real one is safe;
    # the GeoPackage is the thing being mutated, so it is always a real copy.
    os.symlink(CSV, os.path.join(root, "data/final/polities_database.csv"))
    return root


def run(root: str, gate: str) -> tuple:
    p = subprocess.run(
        [sys.executable, os.path.join(root, "scripts", gate)],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# --- the mutations ------------------------------------------------------------
# Each returns a one-line description of what it did, having written the mutated
# GeoPackage into `root`.


def mutate_shadowing_twin(root, gpd, make_valid, affinity):
    """A same-iso3, time-overlapping, same-type twin far smaller than its family
    peer: the exact conjunction audit_family_shadowing says it looks for."""
    import pandas as pd

    g = gpd.read_file(GPKG)
    base = g[g.polity_code == "FRA-1800-1871"].iloc[0].copy()
    twin = base.copy()
    twin["polity_code"] = "FRA-1820-1860"
    twin["start_year"], twin["end_year"] = 1820, 1860
    twin["geometry"] = base.geometry.centroid.buffer(0.5)
    out = gpd.GeoDataFrame(
        pd.concat([g, gpd.GeoDataFrame([twin], crs=g.crs)], ignore_index=True),
        crs=g.crs,
    )
    out.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "added FRA-1820-1860, a small same-type twin overlapping FRA-1800-1871"


def mutate_disjoint_successor(root, gpd, make_valid, affinity):
    """A period moved off its own territory -- the mis-binding of PLAUSIBLE SIZE
    that no area-based check can see, which is the stated reason the containment
    gate exists."""
    g = gpd.read_file(GPKG)
    i = g.index[g.polity_code == "FRA-1871-1919"][0]
    g.loc[i, "geometry"] = affinity.translate(
        g.loc[i, "geometry"], xoff=-150.0, yoff=-20.0
    )
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "translated FRA-1871-1919 into the Pacific, disjoint from its neighbours"


def mutate_shrunk_successor(root, gpd, make_valid, affinity):
    """A period bound to a much smaller feature INSIDE the right territory. The
    containment gate cannot see this by construction; the area gate must."""
    g = gpd.read_file(GPKG)
    src = g.loc[g.polity_code == "FRA-1800-1871", "geometry"].iloc[0]
    i = g.index[g.polity_code == "FRA-1871-1919"][0]
    g.loc[i, "geometry"] = src.centroid.buffer(0.3)
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "shrank FRA-1871-1919 to a disc inside FRA-1800-1871"


CASES = (
    (
        "audit_family_shadowing.py",
        mutate_shadowing_twin,
        "FRA-1820-1860",
        "family ordering, not polity_type, would decide which polity a label matches",
    ),
    (
        "validate_spatial_containment.py",
        mutate_disjoint_successor,
        "FRA-1871-1919",
        "a polygon bound to the wrong feature, detectable only by position",
    ),
    (
        "validate_family_areas.py",
        mutate_shrunk_successor,
        "FRA-1871-1919",
        "a polygon bound to a smaller feature inside the right territory",
    ),
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=int, help="run one case by 1-based number")
    args = ap.parse_args()

    try:
        import geopandas as gpd
        from shapely import affinity
        from shapely.validation import make_valid
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely unavailable ({exc})")
        return 2
    if not os.path.exists(GPKG):
        print(f"FAIL: {GPKG} missing; run scripts/build_database.py first")
        return 2

    cases = list(enumerate(CASES, start=1))
    if args.case:
        cases = [c for c in cases if c[0] == args.case]
        if not cases:
            print(f"FAIL: no case {args.case}")
            return 2

    problems = []
    for n, (gate, mutate, expect, why) in cases:
        root = stage(gate)
        try:
            did = mutate(root, gpd, make_valid, affinity)
            code, out = run(root, gate)
            fired = code != 0
            names = expect in out
            print(f"case {n}: {gate}")
            print(f"   mutation: {did}")
            print(f"   detects:  {why}")
            print(f"   result:   exit={code} names {expect}: {names}")
            if not fired:
                problems.append(
                    f"{gate} PASSED a mutation it claims to catch ({did}) — the gate "
                    f"cannot fail, so its green verdict on real data means nothing"
                )
            elif not names:
                problems.append(
                    f"{gate} failed as required but its output does not name {expect}, "
                    f"so a real failure would not tell a maintainer where to look"
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    if problems:
        print(f"\nFAIL: {len(problems)} gate(s) could not be shown to fail\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"\nPASS: {len(cases)} gate(s) fail on an injected defect and name it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
