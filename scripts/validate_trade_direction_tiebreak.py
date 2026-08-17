#!/usr/bin/env python3
"""Validate the availability tables: the entrepot classes and the mirror direction claims.

`pipelines/polity-autoimprove/state/trade_entrepot_flags.csv` and
`state/trade_mirror_direction.csv` (issue #112's remainder, and issue #14's untested half)
are written by `pipelines/polity-autoimprove/13_trade_entrepot_direction.py` from two pins
that live outside the repository — 46.8M bilateral trade rows and 4.2M production rows — so
nothing in CI can re-derive the flows. What CI CAN re-derive is every claim the two tables
make about the rows they carry, and here that matters more than it does for the pair table
next door, because THESE TABLES NAME A GUILTY SIDE.

WHY EACH CHECK EXISTS

  the direction     `validate_trade_mirror_gaps.py` forbids `trade_mirror_gaps.csv` from
                    growing an `implied_correct`-shaped column, and that stands: two numbers
                    about one shipment cannot arbitrate themselves. What licenses a direction
                    HERE is a third quantity the pair does not have — the exporter's own
                    production plus its own imports in that item and year, which a shipment
                    cannot exceed. So `impossible_side`, `plausible_side` and
                    `whep_keeps_plausible` are re-derived from `exp_t`, `imp_t` and `avail_t`
                    at the documented 2.0x threshold on every row. A stale one is the whole
                    risk of the table: it says whep's documented preference (R/bilateral_trade.R
                    keeps the exporter's figure) retains a tonnage the exporter's own supply
                    refutes, on 18 flows of 3,913, and a consumer would act on that.

  undetermined      `both` and `none` are opposite states that mean the same thing — one side
                    refuted, and only one, is what decides — so both must map to
                    `plausible_side = undetermined` and `whep_keeps_plausible = unknown`. A
                    "both impossible" row silently reading as a decision would invert half of
                    the very cases where the production figure is itself the suspect one.

  availability      `avail_t` must equal `prod_t + reporter_imports_t`, and every direction
                    row must carry a production figure at all. The tie-breaker's coverage is
                    the fact most easily lost in a refactor: only 3,913 of the 12,775 flagged
                    flows (30.6%) have a production row, the rest being processed or composite
                    trade items, and a left join in place of an inner one would fill the table
                    with rows whose availability is 0 and whose every claim is therefore
                    "impossible".

  the mirror screen Every direction row must exist in `trade_mirror_gaps.csv` with the same
                    two tonnages. Otherwise a flow that never passed the mirror screen — the
                    tonne floor and the 1000x ratio — could acquire a direction verdict here,
                    which is a claim about a disagreement that was never established.

  entrepot classes  `reexport` is NOT a defect and the gate is what keeps the two apart.
                    Exporting more than you produce is what an entrepot does: the class is
                    led by the Netherlands, Belgium, Hong Kong and Singapore, which is issue
                    14's own candidate list. Exporting more than production PLUS imports is
                    unsourceable. So `flow_class` is re-derived from the row's own three
                    tonnages at the documented 1.1x / 10x thresholds, and the two classes are
                    required to be disjoint and exhaustive — a `reexport` row drifting into
                    the other class would present Rotterdam's transit trade as an error, and
                    an `exceeds_availability` row drifting into `reexport` would file a
                    scale error (Mozambique reports 84,235,262 t of raw sugar exported in
                    2016 against 2,081,964 t available) as ordinary transit.

  no repair         Neither table may grow a corrected tonnage. A refuted side is not a
                    measured one: knowing Mexico cannot have exported 195,282 t of green
                    onions does not make the importer's 2 t the truth, and #14 asks for
                    entrepot rows to be MARKED, not rewritten.

  the summary       `trade_availability_summary.csv` carries the pin-side census (the two
                    pins' year ranges, the layer-B overlap that is zero, the 1.32M cells)
                    which CI cannot check, and the table-side counts that it can. Every
                    table-side count is re-derived, which is what catches the real failure of
                    a three-file artifact: one regenerated and the others not.

Usage:
  python3 scripts/validate_trade_direction_tiebreak.py
Exit 1 if any row breaches its screen, any derived column disagrees with the tonnages it is
a function of, a direction row is absent from the mirror table, or the summary disagrees.
"""
import csv
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
ENTREPOT = os.path.join(STATE, "trade_entrepot_flags.csv")
DIRECTION = os.path.join(STATE, "trade_mirror_direction.csv")
SUMMARY = os.path.join(STATE, "trade_availability_summary.csv")
GAPS = os.path.join(STATE, "trade_mirror_gaps.csv")

ENTREPOT_COLUMNS = ["reporter_code", "reporter", "item_code", "item", "year", "prod_t",
                    "imports_t", "exports_t", "avail_t", "exp_over_prod", "exp_over_avail",
                    "flow_class"]
DIRECTION_COLUMNS = ["reporter_code", "reporter", "partner_code", "partner", "item_code",
                     "item", "year", "exp_t", "imp_t", "ratio", "prod_t",
                     "reporter_imports_t", "avail_t", "exp_over_avail", "imp_over_avail",
                     "impossible_side", "plausible_side", "whep_keeps_plausible"]

# The generator's constants, repeated rather than imported because the summary states them
# too and the point is that all three agree.
MIN_EXPORT_T = 1000.0
AVAIL_TOL = 1.1
REEXPORT_FACTOR = 10.0
DIRECTION_TOL = 2.0
WHEP_KEEPS = "exporter"

# Ratios are stored rounded to 3 decimals; sums of three published tonnages carry their own
# float noise. Both tolerances are far tighter than any real drift and far looser than the
# rounding.
RATIO_TOL = 1e-3
SUM_TOL = 1e-6

FORBIDDEN = frozenset({
    "implied_correct", "corrected_t", "repair", "action", "correct_side", "wrong_side",
    "implied_factor", "true_t",
})
FLOW_CLASSES = frozenset({"exceeds_availability", "reexport"})
SIDES = frozenset({"exporter", "importer", "both", "none"})

TABLE_DERIVED_ENTREPOT = {
    "entrepot_rows", "entrepot_exceeds_availability", "entrepot_reexport",
    "entrepot_reporters", "entrepot_items", "entrepot_year_min", "entrepot_year_max",
}
TABLE_DERIVED_DIRECTION = {
    "direction_rows", "direction_resolved", "direction_exporter_impossible",
    "direction_importer_impossible", "direction_both_impossible",
    "direction_undetermined", "direction_whep_keeps_refuted_side",
}


def num(s):
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None


def read(path, columns, label, problems):
    if not os.path.exists(path):
        problems.append(f"{label}: {os.path.relpath(path, REPO)} is missing; run "
                        f"pipelines/polity-autoimprove/13_trade_entrepot_direction.py")
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        problems.append(f"{label}: {os.path.relpath(path, REPO)} has no rows")
        return []
    got = list(rows[0].keys())
    if got != columns:
        problems.append(f"{label}: columns are {got}, expected {columns}")
    bad = sorted(FORBIDDEN.intersection(got))
    if bad:
        problems.append(
            f"{label}: carries {bad}, a repaired or attributed value. A refuted side is not "
            f"a measured one, and issue 14 asks for entrepot rows to be marked, not rewritten")
    return rows


def ratio_field(raw, numerator, denominator, where, field, problems):
    """Re-derive a stored ratio, whose blank means 'the denominator was zero'."""
    text = (raw or "").strip()
    if denominator <= 0:
        if text != "":
            problems.append(f"{where}: {field} is {text!r} but the denominator is "
                            f"{denominator:g}; blank is what a zero denominator writes")
        return
    if text == "":
        problems.append(f"{where}: {field} is blank but the denominator is {denominator:g}")
        return
    got, want = num(text), numerator / denominator
    if got is None or want == 0 or abs(got - want) > max(RATIO_TOL, RATIO_TOL * abs(want)):
        problems.append(f"{where}: {field} says {text} but {numerator:g}/{denominator:g} "
                        f"is {want:.3f}")


def check_entrepot(problems):
    rows = read(ENTREPOT, ENTREPOT_COLUMNS, "entrepot table", problems)
    seen, counts = set(), {}
    for r in rows:
        where = (f"entrepot {r.get('reporter')} {r.get('item')} {r.get('year')}")
        key = (r.get("reporter_code"), r.get("item_code"), r.get("year"))
        if key in seen:
            problems.append(f"{where}: duplicate (reporter, item, year) row")
        seen.add(key)
        prod, imp, exp = num(r["prod_t"]), num(r["imports_t"]), num(r["exports_t"])
        avail = num(r["avail_t"])
        if None in (prod, imp, exp, avail):
            problems.append(f"{where}: a tonnage is not a number")
            continue
        if exp < MIN_EXPORT_T:
            problems.append(f"{where}: exports {exp:g} t are below the {MIN_EXPORT_T:g} t "
                            f"floor, so 'exports exceed production' is as likely rounding "
                            f"as routing")
        if abs(avail - (prod + imp)) > max(SUM_TOL, SUM_TOL * abs(avail)):
            problems.append(f"{where}: avail_t {avail:g} != prod_t {prod:g} + imports_t "
                            f"{imp:g} = {prod + imp:g}")
        ratio_field(r["exp_over_prod"], exp, prod, where, "exp_over_prod", problems)
        ratio_field(r["exp_over_avail"], exp, avail, where, "exp_over_avail", problems)
        klass = (r["flow_class"] or "").strip()
        if klass not in FLOW_CLASSES:
            problems.append(f"{where}: flow_class {klass!r} is not one of "
                            f"{sorted(FLOW_CLASSES)}")
            continue
        counts[klass] = counts.get(klass, 0) + 1
        unsourced = exp > AVAIL_TOL * avail
        if unsourced and klass != "exceeds_availability":
            problems.append(
                f"{where}: exports {exp:g} t exceed {AVAIL_TOL:g}x availability "
                f"{avail:g} t, so this is unsourceable, not {klass!r} — filing a scale "
                f"error as ordinary transit is how it stops being looked at")
        if not unsourced:
            if klass != "reexport":
                problems.append(f"{where}: exports {exp:g} t are covered by availability "
                                f"{avail:g} t, so the class cannot be {klass!r}")
            elif not exp > REEXPORT_FACTOR * max(prod, 0.0):
                problems.append(
                    f"{where}: exports {exp:g} t are only {exp / prod:.2f}x production "
                    f"{prod:g} t, below the {REEXPORT_FACTOR:g}x re-export screen — "
                    f"ordinary stock drawdown would label half the world an entrepot")
    return rows, counts


def check_direction(problems):
    rows = read(DIRECTION, DIRECTION_COLUMNS, "direction table", problems)
    mirrored = {}
    if os.path.exists(GAPS):
        with open(GAPS, newline="", encoding="utf-8") as fh:
            for g in csv.DictReader(fh):
                mirrored[(g["reporter_code"], g["partner_code"], g["item_code"],
                          g["year"])] = g
    else:
        problems.append("direction table: trade_mirror_gaps.csv is missing, so the mirror "
                        "screen behind every row here cannot be checked")
    counts, resolved, refuted = {}, 0, 0
    seen = set()
    for r in rows:
        where = (f"direction {r.get('reporter')}->{r.get('partner')} {r.get('item')} "
                 f"{r.get('year')}")
        key = (r.get("reporter_code"), r.get("partner_code"), r.get("item_code"),
               r.get("year"))
        if key in seen:
            problems.append(f"{where}: duplicate flow row")
        seen.add(key)
        exp, imp = num(r["exp_t"]), num(r["imp_t"])
        prod, rimp, avail = num(r["prod_t"]), num(r["reporter_imports_t"]), num(r["avail_t"])
        if None in (exp, imp, prod, rimp, avail):
            problems.append(f"{where}: a tonnage is not a number")
            continue
        if mirrored and key not in mirrored:
            problems.append(
                f"{where}: this flow is not in trade_mirror_gaps.csv, so it never passed the "
                f"mirror screen (both sides >= 1 t, ratio > 1000x) that a direction verdict "
                f"here presumes")
        elif key in mirrored:
            g = mirrored[key]
            for field, got in (("exp_t", exp), ("imp_t", imp)):
                want = num(g[field])
                if want is None or abs(got - want) > max(SUM_TOL, SUM_TOL * abs(want)):
                    problems.append(f"{where}: {field} {got:g} disagrees with the mirror "
                                    f"table's {g[field]}")
        if abs(avail - (prod + rimp)) > max(SUM_TOL, SUM_TOL * abs(avail)):
            problems.append(f"{where}: avail_t {avail:g} != prod_t {prod:g} + "
                            f"reporter_imports_t {rimp:g} = {prod + rimp:g}")
        hi, lo = max(exp, imp), min(exp, imp)
        stored = num(r["ratio"])
        if lo <= 0:
            problems.append(f"{where}: a side is {lo:g} t, which the mirror screen excludes")
        elif stored is None or abs(stored - hi / lo) > max(RATIO_TOL,
                                                          RATIO_TOL * hi / lo):
            problems.append(f"{where}: ratio says {r['ratio']} but {hi:g}/{lo:g} is "
                            f"{hi / lo:.3f}")
        ratio_field(r["exp_over_avail"], exp, avail, where, "exp_over_avail", problems)
        ratio_field(r["imp_over_avail"], imp, avail, where, "imp_over_avail", problems)

        exp_bad, imp_bad = exp > DIRECTION_TOL * avail, imp > DIRECTION_TOL * avail
        want_side = ("both" if exp_bad and imp_bad else
                     "exporter" if exp_bad else "importer" if imp_bad else "none")
        side = (r["impossible_side"] or "").strip()
        if side not in SIDES:
            problems.append(f"{where}: impossible_side {side!r} is not one of {sorted(SIDES)}")
            continue
        counts[side] = counts.get(side, 0) + 1
        if side != want_side:
            problems.append(
                f"{where}: impossible_side says {side!r}, but at {DIRECTION_TOL:g}x "
                f"availability {avail:g} t the exporter's {exp:g} t is "
                f"{'refuted' if exp_bad else 'possible'} and the importer's {imp:g} t is "
                f"{'refuted' if imp_bad else 'possible'} — {want_side!r}")
        want_plausible = {"exporter": "importer", "importer": "exporter"}.get(
            want_side, "undetermined")
        plausible = (r["plausible_side"] or "").strip()
        if plausible != want_plausible:
            problems.append(
                f"{where}: plausible_side says {plausible!r}, expected {want_plausible!r}. "
                f"'both' and 'none' are opposite states that decide nothing alike: one "
                f"refutes no side, the other refutes every side")
        want_keeps = ("unknown" if want_plausible == "undetermined"
                      else "true" if want_plausible == WHEP_KEEPS else "false")
        keeps = (r["whep_keeps_plausible"] or "").strip()
        if keeps != want_keeps:
            problems.append(f"{where}: whep_keeps_plausible says {keeps!r}, but whep keeps "
                            f"the {WHEP_KEEPS}'s figure and the surviving side here is "
                            f"{want_plausible!r} — {want_keeps!r}")
        if want_plausible != "undetermined":
            resolved += 1
            if want_keeps == "false":
                refuted += 1
    return rows, counts, resolved, refuted


def check_summary(ent, ent_counts, dirn, dir_counts, resolved, refuted, problems):
    if not os.path.exists(SUMMARY):
        problems.append(f"summary: {os.path.relpath(SUMMARY, REPO)} is missing")
        return
    with open(SUMMARY, newline="", encoding="utf-8") as fh:
        summary = {r["metric"]: r["value"] for r in csv.DictReader(fh)}
    derived = {
        "entrepot_rows": len(ent),
        "entrepot_exceeds_availability": ent_counts.get("exceeds_availability", 0),
        "entrepot_reexport": ent_counts.get("reexport", 0),
        "entrepot_reporters": len({r["reporter_code"] for r in ent}),
        "entrepot_items": len({r["item_code"] for r in ent}),
        "entrepot_year_min": min((int(r["year"]) for r in ent), default=0),
        "entrepot_year_max": max((int(r["year"]) for r in ent), default=0),
        "direction_rows": len(dirn),
        "direction_resolved": resolved,
        "direction_exporter_impossible": dir_counts.get("exporter", 0),
        "direction_importer_impossible": dir_counts.get("importer", 0),
        "direction_both_impossible": dir_counts.get("both", 0),
        "direction_undetermined": dir_counts.get("none", 0),
        "direction_whep_keeps_refuted_side": refuted,
    }
    for metric in sorted(TABLE_DERIVED_ENTREPOT | TABLE_DERIVED_DIRECTION):
        if metric not in summary:
            problems.append(f"summary: {metric} is missing, so a reader cannot tell whether "
                            f"the tables and the summary describe the same run")
            continue
        got, want = num(summary[metric]), derived[metric]
        if got is None or int(got) != int(want):
            problems.append(f"summary: {metric} says {summary[metric]} but the table gives "
                            f"{want} — one file was regenerated and the other was not")
    # The constants have to agree three ways: generator, gate, summary.
    for metric, want in (("min_export_t", MIN_EXPORT_T), ("avail_tol", AVAIL_TOL),
                         ("reexport_factor", REEXPORT_FACTOR),
                         ("direction_tol", DIRECTION_TOL)):
        got = num(summary.get(metric))
        if got is None or abs(got - want) > 1e-9:
            problems.append(f"summary: {metric} says {summary.get(metric)!r}, but this gate "
                            f"and the generator screen at {want:g}")
    if (summary.get("whep_keeps") or "").strip() != WHEP_KEEPS:
        problems.append(f"summary: whep_keeps says {summary.get('whep_keeps')!r}; "
                        f"whep_keeps_plausible is meaningless unless it is {WHEP_KEEPS!r}")
    # The layer-B correction is the reason this table uses the production pin at all, so it
    # has to survive a regeneration: issue 112's follow-up says "checkable against layer-B
    # production", and layer B (1850-1960) shares no year with the bilateral pin (1986-2021).
    overlap = num(summary.get("layer_b_bilateral_overlap_years"))
    if overlap is None:
        problems.append("summary: layer_b_bilateral_overlap_years is missing; it records why "
                        "the third quantity comes from the production pin and not layer B")
    elif overlap > 0:
        problems.append(
            f"summary: layer_b_bilateral_overlap_years is {overlap:g}. If the two datasets "
            f"now share years, the entrepot check CAN be run against layer B as issue 112 "
            f"asked, and this table's choice of source needs revisiting")


def main() -> int:
    problems = []
    ent, ent_counts = check_entrepot(problems)
    dirn, dir_counts, resolved, refuted = check_direction(problems)
    check_summary(ent, ent_counts, dirn, dir_counts, resolved, refuted, problems)
    if problems:
        print(f"FAIL: {len(problems)} problem(s) in the trade availability tables\n")
        for p in problems[:40]:
            print(f"  - {p}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1
    print(f"PASS: {len(ent):,} entrepot rows "
          f"({ent_counts.get('exceeds_availability', 0):,} unsourceable, "
          f"{ent_counts.get('reexport', 0):,} re-export) and {len(dirn):,} mirror flows with "
          f"a third quantity ({resolved} resolved, {refuted} where whep keeps the refuted "
          f"side) all agree with their own tonnages and with the summary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
