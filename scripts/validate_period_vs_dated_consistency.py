#!/usr/bin/env python3
"""Guard `period_vs_dated_consistency.csv`: the CONTROL must hold, or the tails mean nothing
(issues 424, 416).

WHAT THIS PROTECTS, AND WHY ARM B COMES FIRST. The table's claim is that a multi-year average equals
the mean of the years it covers, so a ratio near a power of ten is a defect. That inference is only
available because the median ratio is 1.000 in every volume over 1,655 pairs -- the source computes
its own averages correctly as a rule. If the median ever drifted, the same 20 cells at 100x could
just as well be a modelling artefact of how the table pairs rows, and every conclusion drawn from
this file would have to be withdrawn. So arm B pins the median PER VOLUME and in BOTH directions,
and it is the arm that matters most; the count arms below only say how many outliers there are.

THE VERDICT IS RE-DERIVED, NOT IMPORTED (arm C). An imported classifier moves with the tool that
wrote the table, which is exactly what a gate must not permit -- and this classifier is a band test,
the shape most likely to be quietly widened.

ARM F IS THE ONE CELL THAT IS IMPOSSIBLE ON THREE INDEPENDENT COMPARISONS. `israel / olives /
1934-1938` reads 3,075,400 t: about 100x its own dated mean (30,660), about 200x its own sibling
period rows (15,751 for 1925-1929 and 12,300 for 1928-1932), and more olives than the Mediterranean
produced. It is pinned by value because it is the strongest single finding in the table and the only
x100 outside every recorded item scope apart from `indonesia / cotton lint`.

Counts are pinned BIDIRECTIONALLY. A fall is as much a failure as a rise: if the 20 becomes 19 a
repair has landed somewhere and this gate must be re-recorded rather than pass quietly.
"""
import csv
import os
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines", "polity-autoimprove", "state",
                     "period_vs_dated_consistency.csv")

# Restated from 43_period_vs_dated_consistency.py, deliberately not imported.
TOL = 0.15
MIN_DATED = 3
VERDICTS = {"consistent", "disagree_x100_period_higher", "disagree_x10_period_higher",
            "disagree_x100_dated_higher", "disagree_x10_dated_higher",
            "unexplained_period_higher", "unexplained_dated_higher"}
ROWS = 1655
# (n, median) per volume. The median is the control; 1.000 is what licenses reading the tails.
CONTROL = {"iia_1925_26": (224, 1.000000), "iia_1938_39": (642, 1.004844),
           "iia_1939_45": (789, 1.000000)}
MEDIAN_BAND = 0.05
COUNTS = {"consistent": 1504, "unexplained_period_higher": 57, "unexplained_dated_higher": 56,
          "disagree_x100_period_higher": 20, "disagree_x10_dated_higher": 10,
          "disagree_x10_period_higher": 8}
# Of the 20 at 100x, 18 are tobacco or hops -- #416 arriving through the period rows. The other two
# are the finding this table adds, so both halves are pinned.
X100_TOBACCO_HOPS = 18
X100_OTHER = {("indonesia", "cotton lint"), ("israel", "olives")}
# israel/olives/1934-1938: production x100 with the PAIRED AREA ROW CLEAN, which is #416's exact
# signature on an item outside its scope. Both rows are pinned, because the area being consistent is
# what turns the tonnage into an impossible YIELD rather than merely a large number:
#   3,075,400 t / 52,000 ha = 59.1 t/ha      real olive yields are ~1-3 t/ha
#      30,660 t / 51,750 ha =  0.59 t/ha     plausible
# The same series is `consistent` at 1928-1932 (12,300 vs 14,486), so the defect is confined to the
# late volume -- a fourth independent comparison after the dated mean, the sibling period row and the
# Mediterranean total.
ISRAEL_OLIVES = {"tonnes": (3075400.0, 30660.0), "ha": (52000.0, 51750.0)}
OLIVE_YIELD_BAD = 59.1
OLIVE_YIELD_OK = 0.59
# `1925-1929` produces no comparable pair: no series has 3+ dated years in that window. Pinned as a
# recorded negative so that its appearing later is noticed rather than absorbed.
PERIODS = {"1900-1913", "1909-1913", "1928-1932", "1934-1938"}


def reclassify(ratio):
    for f in (100.0, 10.0):
        if f * (1 - TOL) <= ratio <= f * (1 + TOL):
            return f"disagree_x{int(f)}_period_higher"
    for f in (100.0, 10.0):
        if 1 / (f * (1 + TOL)) <= ratio <= 1 / (f * (1 - TOL)):
            return f"disagree_x{int(f)}_dated_higher"
    if 0.5 <= ratio <= 2.0:
        return "consistent"
    return "unexplained_period_higher" if ratio > 2.0 else "unexplained_dated_higher"


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — "
              f"run 43_period_vs_dated_consistency.py --write", file=sys.stderr)
        return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    problems = []

    # A. shape
    if len(rows) != ROWS:
        problems.append(f"A: {len(rows)} rows, recorded {ROWS}")
    bad = sorted({r["verdict"] for r in rows} - VERDICTS)
    if bad:
        problems.append(f"A: unknown verdict(s) {bad}")

    # B. THE CONTROL -- pinned per volume, both directions
    for vol, (want_n, want_med) in CONTROL.items():
        d = [float(r["ratio"]) for r in rows if r["volume"] == vol]
        if len(d) != want_n:
            problems.append(f"B: {vol} has {len(d)} pairs, recorded {want_n}")
        if not d:
            continue
        med = statistics.median(d)
        if abs(med - want_med) > MEDIAN_BAND:
            problems.append(
                f"B: {vol} median ratio is {med:.6f}, recorded {want_med:.6f}. THIS IS THE CONTROL: "
                f"the table's whole inference is that a period average normally equals the mean of "
                f"its own years, so if the median moves the outliers below are no longer evidence "
                f"of a defect and every conclusion drawn from this file must be withdrawn.")
    seen_vols = {r["volume"] for r in rows}
    if seen_vols != set(CONTROL):
        problems.append(f"B: volumes present are {sorted(seen_vols)}, recorded {sorted(CONTROL)}")

    # C. verdict re-derived from the ratio
    for r in rows:
        want = reclassify(float(r["ratio"]))
        if r["verdict"] != want:
            problems.append(f"C: {r['label']}/{r['item']}/{r['period']} ratio {r['ratio']} is "
                            f"classed {r['verdict']}, the restated bands say {want}")
            break

    # D. counts, bidirectional
    import collections
    got = collections.Counter(r["verdict"] for r in rows)
    for v, n in COUNTS.items():
        if got.get(v, 0) != n:
            problems.append(f"D: {v} is {got.get(v, 0)}, recorded {n}")

    # E. the x100 set splits 18 known / 2 new
    x100 = [r for r in rows if r["verdict"] == "disagree_x100_period_higher"]
    th = sum(1 for r in x100 if r["item"] in ("tobacco, unmanufactured", "hops"))
    if th != X100_TOBACCO_HOPS:
        problems.append(f"E: {th} of the x100 cases are tobacco/hops, recorded "
                        f"{X100_TOBACCO_HOPS} — this is the independent corroboration of issue 416 "
                        f"at series level, so a change means that link has moved")
    other = {(r["label"], r["item"]) for r in x100
             if r["item"] not in ("tobacco, unmanufactured", "hops")}
    if other != X100_OTHER:
        problems.append(f"E: x100 cases outside tobacco/hops are {sorted(other)}, recorded "
                        f"{sorted(X100_OTHER)} — these are what this table adds")

    # F. the strongest single cell, and the paired area row that makes it a yield
    io = {r["unit"]: r for r in rows if r["label"] == "israel" and r["item"] == "olives"
          and r["period"] == "1934-1938"}
    if set(io) != set(ISRAEL_OLIVES):
        problems.append(f"F: israel/olives/1934-1938 has units {sorted(io)}, recorded "
                        f"{sorted(ISRAEL_OLIVES)} — the AREA row is half the evidence")
    else:
        for unit, want in ISRAEL_OLIVES.items():
            got_pair = (float(io[unit]["period_value"]), float(io[unit]["dated_mean"]))
            if got_pair != want:
                problems.append(f"F: israel/olives/1934-1938 ({unit}) is {got_pair}, recorded "
                                f"{want}")
        if io["ha"]["verdict"] != "consistent":
            problems.append(f"F: the israel/olives AREA row is classed {io['ha']['verdict']}, not "
                            f"consistent. Its being consistent is what makes the tonnage an "
                            f"impossible YIELD rather than just a large number.")
        bad = float(io["tonnes"]["period_value"]) / float(io["ha"]["period_value"])
        ok = float(io["tonnes"]["dated_mean"]) / float(io["ha"]["dated_mean"])
        if abs(bad - OLIVE_YIELD_BAD) > 0.5 or abs(ok - OLIVE_YIELD_OK) > 0.05:
            problems.append(f"F: implied olive yields are {bad:.1f} and {ok:.2f} t/ha, recorded "
                            f"{OLIVE_YIELD_BAD} and {OLIVE_YIELD_OK}. Real olive yields are ~1-3 "
                            f"t/ha, so these two numbers are the physical argument.")

    # G/H. the exclusion premises the ratios rest on
    for r in rows:
        if float(r["period_value"]) <= 0 or float(r["dated_mean"]) <= 0:
            problems.append(f"G: {r['label']}/{r['item']} has a non-positive side, which no ratio "
                            f"can describe; zeros are issue 414 and must stay excluded")
            break
        if int(r["dated_n"]) < MIN_DATED:
            problems.append(f"H: {r['label']}/{r['item']} rests on {r['dated_n']} dated year(s); "
                            f"fewer than {MIN_DATED} is not a mean worth comparing")
            break

    # J. the derived column against its own inputs. Found by mutation testing this gate: changing
    # `period_value` alone left every other arm quiet, because each one reads either the value or the
    # ratio but nothing compared them. A derived column can be wrong while its neighbours are right.
    for r in rows:
        pv, dm, ra = float(r["period_value"]), float(r["dated_mean"]), float(r["ratio"])
        if dm > 0 and abs(pv / dm - ra) > max(1e-4, abs(ra) * 1e-4):
            problems.append(f"J: {r['label']}/{r['item']}/{r['unit']}/{r['period']} carries ratio "
                            f"{ra} but {pv} / {dm} = {pv / dm:.6f}. The ratio is the column every "
                            f"verdict here rests on, so it must agree with the two numbers it "
                            f"describes.")
            break

    # I. recorded negative
    if {r["period"] for r in rows} != PERIODS:
        problems.append(f"I: periods present are {sorted({r['period'] for r in rows})}, recorded "
                        f"{sorted(PERIODS)} — `1925-1929` yielding no pair is a recorded negative")

    if problems:
        print(f"FAIL {os.path.relpath(TABLE, REPO)}", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK period_vs_dated_consistency.csv: {len(rows)} pairs, median ratio 1.000 in every "
          f"volume (the control), {len(x100)} at 100x of which {th} are tobacco/hops")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
