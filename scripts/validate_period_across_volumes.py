#!/usr/bin/env python3
"""Guard `period_across_volumes.csv`: a series' 1934-1938 average against its own 1928-1932 average
(issue 640).

WHAT THIS PROTECTS. 47_period_across_volumes.py pairs every iia (label, item, unit) that has BOTH
period averages -- `1928-1932` from iia_1938_39 and `1934-1938` from iia_1939_45 -- and reports the
ratio. Six years apart that ratio is about 1 (median 1.09 over 1,324 pairs), so a ratio beyond 30x is
not drift. 17 pairs break, 12 high and 5 low, and the gate holds them as a BASELINE OF EXPLAINED
BREAKS: every one is tied below to a `data_errors.csv` entry that names its label and item, or to a
documented reason. A NEW break fails, and so does a baselined one that stopped breaking -- a repair
has landed and the baseline must be re-recorded rather than quietly carry a stale claim.

THE CONTROL COMES FIRST (arm B). The tails mean something only because the median is ~1.09. If it
moved, "30x" would no longer separate a defect from the way the pairs were built. It is pinned in
both directions together with the share of pairs inside the 1/30-30 band.

THE EXPLANATION IS CHECKED, NOT TRUSTED (arm D). An entry id that merely exists proves nothing: the
catch-all `layerb-nested-reporting-levels-one-polity` has `commodity = (all)` and matches every
cell (#635). So each baselined break names the entry AND the label and item words that entry's own
text must contain, and the entry must be `confirmed`.

THE VALUE-SCALE DIVISORS (#416/#717) divide DATED rows only, so this screen compares printed period
values. Arm E pins what that means: the 100 pairs a rule covers have a median ratio near 1, because
both period rows of a tobacco/hops series sit in the same x100 late volumes. Dividing one side only
would break them; the two tobacco breaks (czech republic, dominican republic) are therefore breaks
ON TOP of the shared unit change, as their entry records.

Restated from the stage, not imported: the break threshold, the verdict bands and the rule test.
"""
import csv
import os
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines", "polity-autoimprove", "state")
TABLE = os.path.join(STATE, "period_across_volumes.csv")
ERRORS = os.path.join(STATE, "data_errors.csv")
RULES = os.path.join(REPO, "data", "final", "source_value_scale_corrections.csv")

BREAK = 30.0
ROWS = 1324
MEDIAN, MEDIAN_BAND = 1.0932, 0.05
MIN_WITHIN = 0.98            # share of pairs inside the 1/30..30 band (1307 of 1324 today)
BREAKS_HIGH, BREAKS_LOW = 12, 5
RULE_COVERED, RULE_MEDIAN, RULE_BAND = 100, 1.0301, 0.1
# (label, item, unit) -> ("entry", issue_id, label needle, item needle) | ("reason", text)
BASELINE = {
    ("bulgaria", "beans, dry", "tonnes"):
        ("entry", "bgr-beans-1934-1938-production-x1000", "bulgaria", "bean"),
    ("israel", "olives", "tonnes"):
        ("entry", "iia-olives-1934-1938-scale-scrambled", "israel", "olive"),
    ("italy", "olives", "tonnes"):
        ("entry", "iia-olives-1934-1938-scale-scrambled", "italy", "olive"),
    ("united states of america", "olives", "tonnes"):
        ("entry", "iia-olives-1934-1938-scale-scrambled", "united states", "olive"),
    ("libya", "olives", "tonnes"):
        ("entry", "iia-libya-olives-1934-1938-inflated", "libya", "olive"),
    ("argentina", "sugar raw centrifugal", "tonnes"):
        ("entry", "iia-sugar-1934-1938-deflated", "argentina", "sugar"),
    ("australia", "sugar raw centrifugal", "tonnes"):
        ("entry", "iia-sugar-1934-1938-deflated", "australia", "sugar"),
    ("united states of america", "rye", "ha"):
        ("entry", "iia-1934-1938-single-axis-deflated", "united states", "rye"),
    ("israel", "oranges", "tonnes"):
        ("entry", "iia-1934-1938-single-axis-deflated", "israel", "orange"),
    ("japan", "tea", "tonnes"):
        ("entry", "iia-period-cells-1934-1938-impossible-yield", "japan tea", "tea"),
    ("czech republic", "flax fibre and tow", "tonnes"):
        ("entry", "iia-period-cells-1934-1938-impossible-yield", "czech republic flax", "flax"),
    ("belgium", "grapes", "tonnes"):
        ("entry", "iia-period-cells-1934-1938-impossible-yield", "belgium grapes", "grapes"),
    ("mexico", "grapes", "tonnes"):
        ("entry", "iia-period-cells-1934-1938-impossible-yield", "mexico grapes", "grapes"),
    ("czech republic", "tobacco, unmanufactured", "tonnes"):
        ("entry", "iia-period-cells-1934-1938-impossible-yield", "czech republic tobacco",
         "tobacco"),
    ("dominican republic", "tobacco, unmanufactured", "tonnes"):
        ("entry", "iia-period-cells-1934-1938-impossible-yield", "dominican republic tobacco",
         "tobacco"),
    # china groundnuts: the LOW side is the earlier one. iia's dated 1930-1933 rows (34,000-36,500
    # ha) and the 1928-1932 average (65,200 t on 34,000 ha) sit ~40x below the 1934+ level
    # (1,490,000 ha; 2.3-2.7 Mt), and mitchell reads 2.2-3.0 Mt for 1931-1934, i.e. the late
    # volume agrees with the second source and the early one does not. The yield is plausible on
    # both sides (1.9 and 1.8 t/ha), so area and output move together: a SCOPE shift (the early
    # volumes print a sub-area -- cf. iia-china-mainland-kwantung-summed-cells and the
    # `china: excluding manchuria` label), not a unit factor (it is 39.8x and 42.6x, not a power
    # of ten). Not registered as a correction because the territory it covers is not identified.
    ("china, mainland", "groundnuts, with shell", "tonnes"):
        ("reason", "scope shift at 1934: the early volumes print a sub-area; late volume agrees "
                   "with mitchell 2.2-3.0 Mt; yield plausible on both sides, ratio not a power of ten"),
    ("china, mainland", "groundnuts, with shell", "ha"):
        ("reason", "scope shift at 1934: the early volumes print a sub-area; area moves with "
                   "output (34,000 ha -> 1,448,000 ha), yield plausible on both sides"),
}


def verdict(ratio):
    if ratio >= BREAK:
        return "break_higher"
    if ratio <= 1.0 / BREAK:
        return "break_lower"
    return "within_band"


def main() -> int:
    for p in (TABLE, ERRORS, RULES):
        if not os.path.exists(p):
            print(f"FAIL: {os.path.relpath(p, REPO)} missing", file=sys.stderr)
            return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(ERRORS, newline="", encoding="utf-8") as fh:
        errors = {r["issue_id"]: r for r in csv.DictReader(fh)}
    with open(RULES, newline="", encoding="utf-8") as fh:
        rules = list(csv.DictReader(fh))
    problems = []

    # A. shape, and every derived column against its own inputs
    if len(rows) != ROWS:
        problems.append(f"A: {len(rows)} rows, recorded {ROWS}")
    keys = [(r["label"], r["item"], r["unit"]) for r in rows]
    if len(set(keys)) != len(keys):
        problems.append("A: a (label, item, unit) appears twice")
    for r in rows:
        e, l, ra = float(r["value_1928_1932"]), float(r["value_1934_1938"]), float(r["ratio"])
        if e <= 0 or l <= 0:
            problems.append(f"A: {r['label']}/{r['item']} has a non-positive side; zeros are #414")
            break
        if abs(l / e - ra) > max(1e-4, ra * 1e-4):
            problems.append(f"A: {r['label']}/{r['item']}/{r['unit']} carries ratio {ra} but "
                            f"{l} / {e} = {l / e:.6f}")
            break
        if r["verdict"] != verdict(ra):
            problems.append(f"A: {r['label']}/{r['item']}/{r['unit']} ratio {ra} is classed "
                            f"{r['verdict']}, the restated bands say {verdict(ra)}")
            break

    # B. THE CONTROL
    ratios = [float(r["ratio"]) for r in rows]
    if ratios:
        med = statistics.median(ratios)
        if abs(med - MEDIAN) > MEDIAN_BAND:
            problems.append(f"B: median ratio is {med:.4f}, recorded {MEDIAN}. THIS IS THE CONTROL: "
                            f"a 30x break is a defect only because ordinary pairs sit near 1.")
        within = sum(1 for x in ratios if 1 / BREAK < x < BREAK) / len(ratios)
        if within < MIN_WITHIN:
            problems.append(f"B: only {within:.3f} of pairs are inside the 1/30..30 band, "
                            f"recorded at least {MIN_WITHIN}")

    # C. the breaks ARE the baseline, in both directions
    broke = {(r["label"], r["item"], r["unit"]): r["verdict"] for r in rows
             if r["verdict"] != "within_band"}
    new = sorted(set(broke) - set(BASELINE))
    gone = sorted(set(BASELINE) - set(broke))
    if new:
        problems.append(f"C: NEW unexplained break(s) {new}. Investigate (unit header change, "
                        f"x10/x100, territory change), record via data_errors.csv or a documented "
                        f"reason, and add to BASELINE.")
    if gone:
        problems.append(f"C: baselined break(s) no longer breaking {gone} -- a repair landed; "
                        f"re-record the baseline rather than carry a stale claim.")
    hi = sum(1 for v in broke.values() if v == "break_higher")
    lo = sum(1 for v in broke.values() if v == "break_lower")
    if (hi, lo) != (BREAKS_HIGH, BREAKS_LOW):
        problems.append(f"C: breaks are {hi} higher / {lo} lower, recorded "
                        f"{BREAKS_HIGH} / {BREAKS_LOW}")

    # D. the explanation is real
    for key, ex in sorted(BASELINE.items()):
        if ex[0] == "entry":
            _, eid, lab, item = ex
            ent = errors.get(eid)
            if ent is None:
                problems.append(f"D: {key} is explained by `{eid}`, which is not in data_errors.csv")
                continue
            if ent["status"] != "confirmed":
                problems.append(f"D: {key} is explained by `{eid}` whose status is "
                                f"{ent['status']!r}, not confirmed")
            text = (ent["summary"] + " " + ent["label"] + " " + ent["commodity"]).lower()
            if lab.lower() not in text and not all(w in text for w in lab.lower().split()):
                problems.append(f"D: `{eid}` never names {lab!r}; an entry that does not mention "
                                f"the cell does not explain it (#635)")
            if item.lower() not in text:
                problems.append(f"D: `{eid}` never names {item!r}")
        elif len(ex) != 2 or len(ex[1]) < 40:
            problems.append(f"D: {key} has no documented reason")

    # E. the value-scale divisors do not change what this screen compares
    def covered(r):
        for ru in rules:
            if (ru["source"] == "iia" and ru["item"] == r["item"] and ru["unit"] == r["unit"]
                    and int(ru["year_start"]) <= 1934 and int(ru["year_end"]) >= 1938
                    and r["label"] not in [x.strip() for x in ru["exempt_labels"].split(";")]):
                return True
        return False
    cov = [r for r in rows if covered(r)]
    flagged = [r for r in rows if r["rule_covered"] == "True"]
    if sorted((r["label"], r["item"], r["unit"]) for r in cov) != \
            sorted((r["label"], r["item"], r["unit"]) for r in flagged):
        problems.append(f"E: rule_covered marks {len(flagged)} pairs, the rule table says {len(cov)}")
    if len(cov) != RULE_COVERED:
        problems.append(f"E: {len(cov)} pairs sit under a value-scale rule, recorded {RULE_COVERED}")
    if cov:
        m = statistics.median(float(r["ratio"]) for r in cov)
        if abs(m - RULE_MEDIAN) > RULE_BAND:
            problems.append(f"E: rule-covered pairs have median ratio {m:.4f}, recorded "
                            f"{RULE_MEDIAN}: both period rows of such a series must share the "
                            f"x100 unit, or dividing one side would be the right comparison")

    if problems:
        print(f"FAIL {os.path.relpath(TABLE, REPO)}", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK period_across_volumes.csv: {len(rows)} pairs, median ratio {MEDIAN} (the control), "
          f"{hi + lo} breaks ({hi} high, {lo} low) all explained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
