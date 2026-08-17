#!/usr/bin/env python3
"""Validate the trade-mirror gap table against its own screen and its own summary.

`pipelines/polity-autoimprove/state/trade_mirror_gaps.csv` (issue #112) lists the
doubly-reported FAOSTAT trade flows whose two sides disagree absurdly: an exporter and an
importer cannot differ by a factor of a thousand about a tonnage. It is written by
`pipelines/polity-autoimprove/12_trade_mirror_gap.py` from a 46.8M-row pin that lives
outside the repository, so nothing in CI can re-derive the flows themselves. What CI CAN
re-derive is every claim the table makes about the rows it carries — and those claims are
the whole reason the table is reviewable without the pin.

WHY EACH CHECK EXISTS

  the screen        Issue #112 proposed "ratio >= 1000x" and that screen is wrong: 67.8% of
                    the 39,690 flows above 1000x have their smaller side under one tonne,
                    median 0.1 t against a median 532 t on the other side. That is a
                    reporting threshold, not a disagreement, and ratio is meaningless there
                    because it is unbounded as the denominator goes to zero. The table's
                    screen is therefore a PAIR — both sides >= 1 t AND ratio > 1000x — and
                    a single trace row leaking back in restores the statistic that made
                    39,804 look like 39,804 candidate errors when 12,775 are investigable.
                    So every row is re-tested against both halves.

  ratio, sides      `ratio`, `larger_side`, `nearest_pow10` and `ratio_is_pow10` are all
                    FUNCTIONS of `exp_t` and `imp_t`, so all four are recomputed. A stale
                    `larger_side` is the one that would do damage: `keeps_larger_side`
                    records whether whep's documented preference (R/bilateral_trade.R keeps
                    the exporter's figure) lands on the larger side, which is the whole
                    reason to look at a flow, and it is measured at 50.8% — near enough to a
                    coin flip that a systematic error in the column would be invisible.

  ratio_is_pow10    On the RATIO's own scale, not in log space. The two windows differ by
                    more than a factor of two here (926 of 39,690 vs 1,970), and #112's
                    follow-up reported the log figure — 5.0% — under the words "within 2% of
                    an exact power of ten", where the literal reading gives 2.3%. Both
                    support the same conclusion, that this is NOT #111's constant-power-of-ten
                    class, but the gate holds the tighter definition so the number cannot
                    drift into the looser one while keeping the words.

  the summary       `trade_mirror_summary.csv` carries the pin-side census (6.13M mirrored
                    flows, the >=2x/10x/100x steps) that CI cannot check, and the table-side
                    counts that it can. Every table-side count is re-derived. This is what
                    catches the real failure mode of a two-file artifact: the table
                    regenerated and the summary not, or the reverse, leaving a reader to
                    quote 12,775 against a table of a different size.

  no direction      A mirror gap localises the error to a PAIR and cannot say which side
                    moved: unlike 06's land-use identity and 07's area x yield there is no
                    third quantity to solve for. So the table must not grow an
                    `implied_correct`/`action`-shaped column. 07 writes `undetermined` where
                    it cannot decide; here the honest form is no such column at all, and a
                    consumer that found one would apply a repair nothing supports.

Usage:
  python3 scripts/validate_trade_mirror_gaps.py
Exit 1 if any row breaches the screen, any derived column disagrees with the two tonnages,
or the summary disagrees with the table.
"""
import csv
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAPS = os.path.join(REPO, "pipelines/polity-autoimprove/state/trade_mirror_gaps.csv")
SUMMARY = os.path.join(REPO, "pipelines/polity-autoimprove/state/trade_mirror_summary.csv")

COLUMNS = ["reporter_code", "reporter", "partner_code", "partner", "item_code", "item",
           "year", "exp_t", "imp_t", "ratio", "larger_side", "keeps_larger_side",
           "nearest_pow10", "ratio_is_pow10"]

# The screen, and whep's preference rule. These are the generator's constants; they are
# repeated here rather than imported because the summary states them too, and the point is
# that all three agree.
MIN_SIDE_T = 1.0
RATIO_THRESHOLD = 1000.0
POW10_WINDOW = 0.02
WHEP_KEEPS = "exporter"

# `ratio` is stored rounded to 3 decimals, so the recomputation is compared with a relative
# tolerance rather than for equality. 1e-3 is far tighter than any real drift and far looser
# than the rounding.
RATIO_TOL = 1e-3

# If the power-of-ten share ever rose above this, the "not #111's class" reading in
# 12_trade_mirror_gap.py's docstring and in README would no longer be what the table says.
# Measured 2.9% (372 of 12,775), so this is an order of magnitude of headroom, not a fitted
# threshold — it fails only on a change of KIND, not on ordinary movement.
POW10_SHARE_CEILING = 0.25

# Columns that would assert a direction or a repair the mirror cannot establish.
DIRECTION_CLAIMS = frozenset({
    "implied_correct", "action", "correct_side", "wrong_side", "repair", "corrected_t",
    "implied_factor", "diagnosis",
})

# Summary metrics that are functions of the table, and how to derive each from it.
TABLE_DERIVED = (
    "investigable_flows", "investigable_reporters", "investigable_items",
    "investigable_year_min", "investigable_year_max", "investigable_ratio_is_pow10",
    "investigable_keeps_larger_side",
)


def num(s):
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None


def boolean(s):
    return {"true": True, "false": False}.get(str(s).strip().lower())


def nearest_power_of_ten(ratio: float) -> int:
    if not ratio or ratio <= 0 or not math.isfinite(ratio):
        return 0
    return int(round(math.log10(ratio)))


def is_clean_power_of_ten(ratio: float) -> bool:
    if ratio is None or not math.isfinite(ratio) or ratio <= 0:
        return False
    p = nearest_power_of_ten(ratio)
    return p != 0 and abs(ratio / (10.0 ** p) - 1.0) < POW10_WINDOW


def main() -> int:
    problems = []
    for path in (GAPS, SUMMARY):
        if not os.path.exists(path):
            print(f"FAIL: {os.path.relpath(path, REPO)} is missing. Regenerate with "
                  f"python3 pipelines/polity-autoimprove/12_trade_mirror_gap.py")
            return 1

    with open(GAPS, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    with open(SUMMARY, newline="", encoding="utf-8") as fh:
        summary = {r["metric"]: r["value"] for r in csv.DictReader(fh)}

    missing = [c for c in COLUMNS if c not in header]
    if missing:
        print(f"FAIL: trade_mirror_gaps.csv is missing column(s) {missing}\n"
              f"  present: {header}")
        return 1
    claims = sorted(DIRECTION_CLAIMS & set(header))
    if claims:
        problems.append(
            f"the table carries {claims}, which asserts which SIDE of the flow is wrong. A "
            f"mirror gap localises the error to the (exporter, importer) pair and has no "
            f"third quantity to solve for, so no such column can be derived from it")
    if not rows:
        print("FAIL: trade_mirror_gaps.csv has no rows")
        return 1

    # The summary must state the same screen the generator applied and this gate re-tests.
    for metric, expect in (("min_side_t", MIN_SIDE_T),
                           ("ratio_threshold_strict", RATIO_THRESHOLD),
                           ("pow10_window", POW10_WINDOW)):
        got = num(summary.get(metric))
        if got is None or abs(got - expect) > 1e-12:
            problems.append(
                f"summary {metric} is {summary.get(metric)!r}, not {expect} -- the table was "
                f"screened on a different rule from the one this gate re-tests")
    if summary.get("whep_keeps") != WHEP_KEEPS:
        problems.append(
            f"summary whep_keeps is {summary.get('whep_keeps')!r}, not {WHEP_KEEPS!r}; "
            f"keeps_larger_side means nothing without the rule it refers to")

    seen = {}
    pow10_rows = keeps_rows = 0
    reporters, items, years = set(), set(), []
    for i, r in enumerate(rows, start=2):
        where = (f"{r.get('reporter')} ({r.get('reporter_code')}) -> "
                 f"{r.get('partner')} ({r.get('partner_code')}), "
                 f"{r.get('item')} {r.get('year')}")
        exp_t, imp_t, stored = num(r.get("exp_t")), num(r.get("imp_t")), num(r.get("ratio"))
        if exp_t is None or imp_t is None or stored is None:
            problems.append(f"line {i}: {where}: exp_t/imp_t/ratio not all numeric "
                            f"({r.get('exp_t')!r}, {r.get('imp_t')!r}, {r.get('ratio')!r})")
            continue
        if exp_t <= 0 or imp_t <= 0:
            problems.append(f"line {i}: {where}: a side is not positive "
                            f"(exp {exp_t}, imp {imp_t}); the screen is over reported flows")
            continue
        hi, lo = max(exp_t, imp_t), min(exp_t, imp_t)
        if lo < MIN_SIDE_T:
            problems.append(
                f"line {i}: {where}: smaller side {lo:g} t is below the {MIN_SIDE_T:g} t "
                f"floor, so this is trace reporting against a real flow ({hi:g} t) and not a "
                f"disagreement -- 67.8% of the >1000x flows are this, and admitting them "
                f"inflates the investigable set from 12,775 to 39,690")
        recomputed = hi / lo
        if recomputed <= RATIO_THRESHOLD:
            problems.append(
                f"line {i}: {where}: ratio {recomputed:.4g} does not exceed "
                f"{RATIO_THRESHOLD:g}x, the table's relative condition")
        if abs(recomputed - stored) > RATIO_TOL * recomputed:
            problems.append(f"line {i}: {where}: ratio column says {stored:g}, "
                            f"max/min of the two sides is {recomputed:g}")
        larger = "exporter" if exp_t > imp_t else "importer"
        if r.get("larger_side") != larger:
            problems.append(
                f"line {i}: {where}: larger_side says {r.get('larger_side')!r} but exp_t "
                f"{exp_t:g} vs imp_t {imp_t:g} makes it the {larger}")
        keeps = boolean(r.get("keeps_larger_side"))
        if keeps is None:
            problems.append(f"line {i}: {where}: keeps_larger_side is "
                            f"{r.get('keeps_larger_side')!r}, not a boolean")
        elif keeps != (larger == WHEP_KEEPS):
            problems.append(
                f"line {i}: {where}: keeps_larger_side says {keeps} while whep keeps the "
                f"{WHEP_KEEPS}'s figure and the larger side is the {larger}")
        elif keeps:
            keeps_rows += 1
        p = nearest_power_of_ten(stored)
        if num(r.get("nearest_pow10")) is None or int(num(r.get("nearest_pow10"))) != p:
            problems.append(f"line {i}: {where}: nearest_pow10 says "
                            f"{r.get('nearest_pow10')!r}, log10({stored:g}) rounds to {p}")
        flag = boolean(r.get("ratio_is_pow10"))
        expect_flag = is_clean_power_of_ten(stored)
        if flag is None:
            problems.append(f"line {i}: {where}: ratio_is_pow10 is "
                            f"{r.get('ratio_is_pow10')!r}, not a boolean")
        elif flag != expect_flag:
            problems.append(
                f"line {i}: {where}: ratio_is_pow10 says {flag} but {stored:g} is "
                f"{'' if expect_flag else 'not '}within {POW10_WINDOW:.0%} of 10^{p} -- the "
                f"window is on the RATIO, not on log10(ratio), which is the looser test that "
                f"turned 2.3% into 5.0% in issue 112")
        elif flag:
            pow10_rows += 1
        key = (r.get("reporter_code"), r.get("partner_code"), r.get("item_code"),
               r.get("year"))
        if key in seen:
            problems.append(f"line {i}: {where}: duplicates line {seen[key]}; the table is "
                            f"keyed one row per (reporter, partner, item, year)")
        else:
            seen[key] = i
        reporters.add(r.get("reporter_code"))
        items.add(r.get("item_code"))
        if num(r.get("year")) is not None:
            years.append(int(num(r.get("year"))))

    derived = {
        "investigable_flows": len(rows),
        "investigable_reporters": len(reporters),
        "investigable_items": len(items),
        "investigable_year_min": min(years) if years else None,
        "investigable_year_max": max(years) if years else None,
        "investigable_ratio_is_pow10": pow10_rows,
        "investigable_keeps_larger_side": keeps_rows,
    }
    for metric in TABLE_DERIVED:
        stated = num(summary.get(metric))
        if stated is None:
            problems.append(f"summary is missing {metric}, which a reader quotes instead of "
                            f"counting the table")
        elif derived[metric] is not None and int(stated) != derived[metric]:
            problems.append(
                f"summary {metric} is {int(stated)}, the table says {derived[metric]} -- one "
                f"of the two files was regenerated without the other")

    # The pin-side census cannot be re-derived, but its arithmetic can: the flows above the
    # threshold are exactly the trace ones plus the investigable ones, and the >=Nx steps
    # are nested.
    census = [num(summary.get(m)) for m in
              ("differ_ge_2x", "differ_ge_10x", "differ_ge_100x", "differ_gt_threshold")]
    if all(c is not None for c in census):
        for a, b, la, lb in zip(census, census[1:], ("2x", "10x", "100x"),
                                ("10x", "100x", "1000x")):
            if a < b:
                problems.append(f"summary says {int(a)} flows differ by >={la} but "
                                f"{int(b)} by >={lb}; the steps are nested")
    trace = num(summary.get("trace_excluded_smaller_side_below_min"))
    if trace is not None and census[3] is not None:
        if int(trace) + len(rows) != int(census[3]):
            problems.append(
                f"summary: {int(trace)} trace-excluded + {len(rows)} in the table is "
                f"{int(trace) + len(rows)}, not the {int(census[3])} flows above the "
                f"threshold. Every flow above it is one or the other, so a mismatch means "
                f"the exclusion is not what the summary says it is")
    if len(rows) and pow10_rows / len(rows) > POW10_SHARE_CEILING:
        problems.append(
            f"{pow10_rows} of {len(rows)} ratios ({100 * pow10_rows / len(rows):.1f}%) are "
            f"within {POW10_WINDOW:.0%} of a power of ten, above the "
            f"{POW10_SHARE_CEILING:.0%} ceiling. The table and README read this as NOT issue "
            f"111's constant-power-of-ten class, on a measured 2.9%; at this share that "
            f"reading no longer follows and both need revisiting")

    if problems:
        print(f"FAIL: {len(problems)} problem(s) in the trade-mirror gap table\n")
        for p in problems[:40]:
            print(f"  - {p}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1
    print(f"PASS: {len(rows):,} mirror gaps, every one with both sides >= {MIN_SIDE_T:g} t "
          f"and a ratio above {RATIO_THRESHOLD:g}x")
    print(f"  ratio, larger_side, nearest_pow10, ratio_is_pow10 re-derived from the two "
          f"tonnages on every row")
    print(f"  {pow10_rows} ({100 * pow10_rows / len(rows):.1f}%) within {POW10_WINDOW:.0%} of "
          f"a power of ten -- not issue 111's class")
    print(f"  whep's preference for the {WHEP_KEEPS} keeps the larger side in "
          f"{100 * keeps_rows / len(rows):.1f}% of them")
    print(f"  summary agrees with the table on {len(TABLE_DERIVED)} counts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
