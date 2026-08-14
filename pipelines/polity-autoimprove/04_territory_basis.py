#!/usr/bin/env python3
"""Stage 4 (deterministic): classify each polity's TERRITORY_BASIS — does its
polygon faithfully represent the territory of the period it serves, or is it an
ASSUMPTION (a later/modern border projected back, a single vintage held constant
across a long span, or no polygon at all)?

This operationalises the concern: "WHEP may carry 1860-1961 country data on
expected-same-territory borders that were not the real territory." For each
polity we compare the polygon's vintage (polygon_feature_year) to the polity's
own period [start_year, end_year] and emit a graded basis:

  measured            polygon vintage falls inside the period AND the span is
                      short enough that one vintage is defensible (faithful).
  assumed_constant    vintage inside the period but the span is long (>= SPAN_LONG):
                      one polygon is held constant across years whose borders
                      may have changed (e.g. a 1886 polygon for an 1850-1910 span).
  back_projected      vintage is OUTSIDE the period — a later (usually modern)
                      or earlier border applied to this period. The clearest
                      "not the real territory" case.
  unassigned          no polygon (polygon_status=unassigned / no geometry):
                      an HONEST gap, never a false territory.

A polity is "territory_assumed" (needs review) when basis != measured.
The report focuses on polities overlapping the WINDOW (default 1860-1961).
Data magnitude per polity is attached from the layer-B matched_rows when present.
"""
import pandas as pd, numpy as np, json, os, sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
CONSTRUCTED = os.path.join(REPO, "data/geodata/constructed/constructed.geojson")

WIN_LO, WIN_HI = 1860, 1961   # the concern window
SPAN_LONG = 25                # a span this long can't be one fixed border
DRIFT_TOL = 15                # vintage this far from period edge = real drift

pol = pd.read_csv(POLDB)

# has_geometry from the master gpkg (authoritative on what actually carries a polygon)
import geopandas as gpd, warnings
warnings.filterwarnings("ignore")
g = gpd.read_file(GPKG)
has_geom = {r.polity_code: (r.geometry is not None and not r.geometry.is_empty)
            for _, r in g.iterrows()}

# polygon_method (faithfulness label) for constructed/composed polygons
method = {}
if os.path.exists(CONSTRUCTED):
    cg = gpd.read_file(CONSTRUCTED)
    if "polygon_method" in cg.columns:
        method = {r.polity_code: str(r.polygon_method) for _, r in cg.iterrows()}

# priority signal: polities the territorial-evidence step (02) independently
# flagged (data magnitude step-change vs sibling period, README-known mismatch,
# polygon-vintage drift, or aggregate-contains-concurrent-data). An assumed_constant
# polity that ALSO trips 02 is a HIGH-PRIORITY review (real evidence its single
# polygon misrepresents the territory), vs a long-span border that was actually stable.
flagged_02 = set()
tf = os.path.join(H, "territorial_flagged.json")
if os.path.exists(tf):
    flagged_02 = {f["polity_code"] for f in json.load(open(tf))}

# footnote-derived territorial coverage flags (committed; persists across runs,
# unlike the per-run stage-02 flags). Polities whose published figures carry a
# documented coverage caveat from FAO/IIA yearbook footnotes (inclusion/exclusion/
# boundary-vintage) — direct evidence the nominal territory differs from the
# reported one, so always a priority review regardless of polygon vintage.
footnote_flagged = set()
ff = os.path.join(H, "footnote_flags.csv")
if os.path.exists(ff):
    footnote_flagged = set(pd.read_csv(ff)["polity_code"].dropna())

# layer-B data magnitude per polity (optional hint)
#
# ORPHAN-CODE GUARD (issue 243). matched_rows.parquet is gitignored per-run state written
# by stage 01; `layerb_data_rows` below is the only column of the TRACKED territory_basis.csv
# derived from it. When a polity is re-spanned, the stale parquet keeps the OLD code, so its
# rows are attributed to a code the database no longer contains -- and this script, which
# only looks codes UP, silently commits 0 rows for the renamed polity. That is not a
# hypothetical: measured on main 2026-08-14, five codes carrying 799 rows were orphaned
# (SEN-1886-1959 471, CHL-1810-1883 168, LAO-1893-1953 89, TCD-1920-1960 46, LBY-1950-1951
# 25) and CHL-1810-1884 had to be dropped from validate_data_without_geometry's baseline
# because committed state said it received nothing.
#
# So refuse to write (or to validate) an accounting whose input describes a different polity
# set. The check costs one set difference and is the invariant that actually broke; it can
# only fire where the parquet exists at all, which is where the damage is authored.
rows_by_code = {}
mp = os.path.join(H, "matched_rows.parquet")
if os.path.exists(mp):
    m = pd.read_parquet(mp)
    rows_by_code = m[m.whep_code.notna()].groupby("whep_code").size().to_dict()
    _orphans = {c: n for c, n in rows_by_code.items() if c not in set(pol["polity_code"])}
    if _orphans:
        print(f"FAIL: matched_rows.parquet attributes {sum(_orphans.values()):,} rows to "
              f"{len(_orphans)} code(s) the database does not contain, so layerb_data_rows "
              f"would undercount their successors:")
        for c, n in sorted(_orphans.items(), key=lambda t: -t[1]):
            print(f"  {c}  {n:,} rows")
        print("  the parquet predates a re-span; regenerate it and rerun:\n"
              "    python3 pipelines/polity-autoimprove/01_match_and_findings.py\n"
              "    python3 pipelines/polity-autoimprove/02_territorial_evidence.py")
        sys.exit(1)

def classify(r):
    code = r.polity_code
    s, e = int(r.start_year), int(r.end_year)
    status = str(r.get("polygon_status") or "").strip().lower()
    src = str(r.get("polygon_source") or "").strip().lower()
    fy = r.get("polygon_feature_year")
    geo = has_geom.get(code, False)
    if status == "unassigned" or not geo or src in ("none", "", "nan"):
        return "unassigned", "no polygon (honest gap; never a false territory)"
    if pd.isna(fy):
        return "assumed_constant", "polygon present but no recorded vintage year"
    fy = int(fy)
    span = e - s
    meth = method.get(code, "")
    if meth in ("modern_proxy", "constructed_estimate"):
        return "back_projected", f"polygon_method={meth} (not a faithful-vintage border)"
    if fy > e:
        return "back_projected", f"polygon vintage {fy} is AFTER the period ends ({e}) — later/modern border applied back"
    if fy < s:
        return "back_projected", f"polygon vintage {fy} is BEFORE the period starts ({s})"
    # vintage inside [s, e]
    drift = max(fy - s, e - fy)
    if span >= SPAN_LONG and drift >= DRIFT_TOL:
        return "assumed_constant", f"single {fy} polygon held across a {span}y span ({s}-{e}); borders may have changed"
    return "measured", f"vintage {fy} faithful to period {s}-{e}"

recs = []
for _, r in pol.iterrows():
    s, e = int(r.start_year), int(r.end_year)
    overlaps = (s <= WIN_HI) and (e >= WIN_LO)
    basis, reason = classify(r)
    fn = r.polity_code in footnote_flagged
    is_prio = ((basis in ("assumed_constant", "back_projected")) and (r.polity_code in flagged_02)) or fn
    if fn:
        reason = reason + "; footnote coverage caveat (FAO/IIA yearbook)"
    recs.append({
        "polity_code": r.polity_code, "polity_name": r.polity_name,
        "start_year": s, "end_year": e,
        "polygon_source": r.get("polygon_source"),
        "polygon_feature_year": (int(r.polygon_feature_year) if pd.notna(r.get("polygon_feature_year")) else None),
        "polygon_status": r.get("polygon_status"),
        "overlaps_1860_1961": overlaps,
        "territory_basis": basis, "territory_assumed": basis != "measured",
        "priority_review": is_prio,
        "basis_reason": reason, "layerb_data_rows": int(rows_by_code.get(r.polity_code, 0)),
    })

out = pd.DataFrame(recs)
_DEST = os.path.join(H, "territory_basis.csv")

# --check mirrors the write_*.py convention in scripts/: regenerate in memory and compare,
# exiting 1 on drift, so staleness is a CI failure rather than something a reader has to
# notice. Added 2026-08-05 after this file was found 122 commits behind the database it
# describes -- 721 rows against 749, with 28 polities simply absent. A derived file with no
# freshness check is a file that silently stops describing its input, and this one feeds the
# territory-basis assessment that answers "is WHEP carrying 1860-1961 data on borders that
# were not the real territory" -- so 28 missing rows read as 28 polities with nothing to
# worry about.
if "--check" in sys.argv:
    import io
    import csv as _csv

    # TWO OF THIS SCRIPT'S INPUTS ARE UNTRACKED, so CI can never reproduce every column.
    #   state/matched_rows.parquet    -> layerb_data_rows   (layer B lives outside the repo)
    #   state/territorial_flagged.json -> priority_review   (written per-run by stage 02)
    # state/footnote_flags.csv IS committed, so basis_reason is reproducible everywhere.
    #
    # The first version of this check compared the whole frame and turned main red within
    # minutes of merging: CI reported "749 committed rows vs 749 regenerated", identical
    # counts with differing content, because both columns collapse to 0/False without their
    # inputs. Comparing everything looked stricter and was simply broken in the only
    # environment that runs it automatically.
    #
    # So: compare every column when both inputs are present, and otherwise compare the
    # columns that ARE reproducible -- which still catches the failure this check exists for
    # (a polity missing from the file, or a basis reclassified), and says which comparison it
    # performed rather than implying full coverage.
    _VOLATILE = {
        "layerb_data_rows": os.path.join(H, "matched_rows.parquet"),
        "priority_review": os.path.join(H, "territorial_flagged.json"),
    }
    _missing = sorted(c for c, src in _VOLATILE.items() if not os.path.exists(src))

    if not os.path.exists(_DEST):
        print(f"FAIL: {_DEST} missing; run this script without --check")
        raise SystemExit(1)

    committed = pd.read_csv(_DEST, keep_default_na=False, dtype=str)
    fresh = pd.read_csv(io.StringIO(out.to_csv(index=False)), keep_default_na=False, dtype=str)

    cf = set(fresh["polity_code"])
    cc = set(committed["polity_code"])
    problems = []
    if cf - cc:
        problems.append(f"in the database but MISSING from the committed file: {sorted(cf - cc)}")
    if cc - cf:
        problems.append(f"in the committed file but no longer in the database: {sorted(cc - cf)}")

    compared = [c for c in fresh.columns if c not in _missing]
    if not problems:
        a = committed.set_index("polity_code")[compared[1:]].sort_index()
        b = fresh.set_index("polity_code")[compared[1:]].sort_index()
        for code in a.index:
            for col in compared[1:]:
                if a.at[code, col] != b.at[code, col]:
                    problems.append(
                        f"{code} {col}: committed {a.at[code, col]!r} != regenerated "
                        f"{b.at[code, col]!r}"
                    )
                    if len(problems) > 12:
                        break
            if len(problems) > 12:
                problems.append("... further differences suppressed")
                break

    if problems:
        print(f"FAIL: territory_basis.csv is stale ({len(cc)} committed rows vs {len(cf)} "
              f"regenerated)")
        for line in problems:
            print(f"  {line}")
        print("  rerun: python3 pipelines/polity-autoimprove/04_territory_basis.py")
        raise SystemExit(1)

    if _missing:
        print(f"OK: territory_basis.csv matches the database ({len(fresh)} polities); "
              f"{len(compared)} of {len(fresh.columns)} columns compared -- "
              f"{_missing} need untracked inputs and were skipped")
    else:
        print(f"OK: territory_basis.csv matches the database ({len(fresh)} polities, "
              f"all {len(fresh.columns)} columns)")
    raise SystemExit(0)

out.to_csv(_DEST, index=False)

ORDER = ["measured", "assumed_constant", "back_projected", "unassigned"]
print(f"classified {len(out)} polities -> state/territory_basis.csv\n")
print("ALL polities by territory_basis:")
for b in ORDER:
    sub = out[out.territory_basis == b]
    print(f"  {b:18s} {len(sub):>4} polities")

win = out[out.overlaps_1860_1961]
print(f"\n=== WINDOW {WIN_LO}-{WIN_HI}: {len(win)} polities overlap ===")
for b in ORDER:
    sub = win[win.territory_basis == b]
    print(f"  {b:18s} {len(sub):>4} polities  {int(sub.layerb_data_rows.sum()):>8,} layer-B rows")

prio = win[win.priority_review].sort_values("layerb_data_rows", ascending=False)
print(f"\n=== {len(prio)} window polities are PRIORITY_REVIEW "
      f"(assumed/back-projected AND flagged by stage 02, OR footnote coverage caveat) ===")
print(f"    ({len(footnote_flagged)} polities carry FAO/IIA footnote coverage flags)")
for _, r in prio.head(30).iterrows():
    print(f"  {r.polity_code:18s} {r.territory_basis:16s} {r.basis_reason[:60]:60s} [{r.layerb_data_rows}r]")
