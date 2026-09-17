#!/usr/bin/env python3
"""A reporting unit can be fully routed, have a page, and still route no data.

THE TWO HALVES OF ROUTING ARE WRITTEN BY DIFFERENT TOOLS AND NOTHING KEPT THEM IN SYNC.
`pipelines/agent-harness/harness.py` decides which polity a reporting unit belongs to and
writes the wiki page; the alias that actually sends the source's rows to that polity is
appended by `pipelines/polity-autoimprove/apply_verdicts.py`, from the assertion workflow.
Neither checks the other, so a unit can carry `verdict: create_new`, a written page and a
live polity while its label resolves to nothing.

WHAT IT FOUND (2026-09-17, measured against the 8.9M-row subnational panel):

    USA-CALIFORNIA    34,452 valued rows   CAL-1850-2025 existed, page written, no alias
    USA-NORTHDAKOTA   21,560              USA-ND-1889-2025      "        "        "
    USA-NEWMEXICO     15,473              USA-NM-1912-2025      "        "        "
    ARG-CHACO         21,347              ARG-CHACO-1951-2025 created for these very years
    ARG-FORMOSA       19,020              ARG-FORMOSA-1955-2025          "
    PRT-PTBG          109 data years      alias started 1989, polity starts 1835

The three US states were the sharpest case: each WAS aliased, under `usda-nass-fips`, whose
labels are FIPS codes ('06', '35', '38'). The juan-subnational component reports states by
name, and no rule existed for that label in any slug. Routing is not per-source -- a polity
aliased under one vocabulary is still unrouted under another, and a coverage report keyed on
the polity looks complete either way.

Braganca is the one this gate is really for: it was MY residue. Seven Portuguese districts
were renamed to start in 1835 and had their aliases widened to match; Braganca already
started in 1835, so it was not in the rename batch and its alias was never widened with the
others. Nothing failed. 109 years quietly resolved to nothing.

WHAT THIS CHECKS. For every unit in the harness ledger whose coverage declares a `matched` or
`proposed` segment -- the two dispositions that assert "this data belongs to this polity" --
every year of that segment which falls inside the target polity's own span must be resolvable
from `data/final/label_alias_map.csv` under the unit's own label. Years OUTSIDE the target's
span are a different defect and are not this gate's business (see issues 655, 657, 658).

`back_cast` and `unroutable` segments are excluded by design: a back-cast is a reconstruction
onto a boundary that did not exist, and an unroutable span asserts there is no territory. In
neither case does an absent alias indicate a mistake.

Reads only committed files -- the ledger, the alias map and the polity table -- so it runs
anywhere. The panel itself is gitignored and is NOT needed: the ledger already records which
years each unit reports.

Usage:
  python3 scripts/validate_routed_units_are_aliased.py
"""
import collections
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "pipelines/agent-harness/state/routing_verdicts.csv")
ALIASES = os.path.join(REPO, "data/final/label_alias_map.csv")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")

# Dispositions that assert "these years belong to this polity". The other two do not:
# back_cast says the values are a reconstruction, unroutable says no territory existed.
ROUTED = ("matched", "proposed")

# Units knowingly left without an alias for part of a routed span, each with the reason.
# Bidirectional: a new one fails, and a resolved one must be removed or this fails too.
BASELINE = {}


def main() -> int:
    if not os.path.exists(LEDGER):
        print(f"SKIP: {os.path.relpath(LEDGER, REPO)} absent")
        return 0

    csv.field_size_limit(sys.maxsize)

    spans = {}
    with open(POLDB, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                spans[r["polity_code"]] = (int(r["start_year"]), int(r["end_year"]))
            except (TypeError, ValueError):
                continue

    rules = collections.defaultdict(list)
    with open(ALIASES, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                rules[r["source_label"]].append((int(r["year_start"]), int(r["year_end"])))
            except (TypeError, ValueError):
                continue

    problems = []
    checked = 0
    with open(LEDGER, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw = (r.get("coverage_json") or "").strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                continue
            segs = parsed.get("segments", []) if isinstance(parsed, dict) else parsed
            need = [s for s in segs if s.get("disposition") in ROUTED]
            if not need:
                continue

            codes = [(r.get("page_polity_code") or r.get("matched_polity_code") or "").strip()]
            codes += [c.strip() for c in
                      (r.get("extra_pages") or "").replace(";", ",").split(",") if c.strip()]
            codes = [c for c in codes if c in spans]
            if not codes:
                continue
            checked += 1

            # every year any target polity is alive for
            alive = set()
            for c in codes:
                start, end = spans[c]
                alive |= set(range(start, end))

            # THE UNIT'S LABEL TAKES MORE THAN ONE FORM and the slugs disagree about which
            # they use: `admin_unit_id` ('PRT-PTBG', 'ARG-CHACO') or `admin_name_clean`
            # ('PT_BG', 'Chaco'). Checking one form alone reports false gaps -- measuring only
            # the juan slug once called Queensland unrouted when whep-lab-australia had it.
            mine = rules.get(r["unit_id"], []) + rules.get(r.get("admin_name") or "", [])

            missing = []
            for s in need:
                try:
                    lo, hi = int(s["start_year"]), int(s["end_year"])
                except (KeyError, TypeError, ValueError):
                    continue
                for year in range(lo, hi + 1):
                    if year not in alive:
                        continue        # outside every target's span: not this gate's defect
                    if not any(a <= year <= b for a, b in mine):
                        missing.append(year)
            if missing:
                problems.append((r["country"], r["unit_id"], r.get("admin_name") or "",
                                 min(missing), max(missing), len(missing), codes[0]))

    live = {p[1] for p in problems}
    stale = sorted(set(BASELINE) - live)
    if stale:
        print(f"FAIL: {len(stale)} baseline entr(ies) no longer needed -- remove them:")
        for unit in stale:
            print(f"  {unit}: {BASELINE[unit]}")
        return 1

    unbaselined = [p for p in problems if p[1] not in BASELINE]
    if unbaselined:
        print(f"FAIL: {len(unbaselined)} routed unit(s) whose data cannot reach the polity "
              f"they were routed to\n")
        for country, unit, name, lo, hi, n, code in sorted(unbaselined, key=lambda p: -p[5]):
            print(f"  {unit:24} ({country}) {lo}-{hi}, {n} year(s) with no alias")
            print(f"      routed to {code}, which is alive for those years; the label "
                  f"{unit!r} / {name!r} resolves to nothing there")
        print("\nAn alias is what sends a source's rows to a polity. Without one the routing "
              "decision, the page and the polity all exist and no data arrives -- and every "
              "report keyed on the polity still looks complete. Add the rule to "
              "pipelines/polity-autoimprove/state/applied_aliases.csv and regenerate with "
              "scripts/write_label_alias_map.py, or baseline it here with the reason.")
        return 1

    print(f"PASS: every routed year of {checked} unit(s) with a matched/proposed coverage "
          f"segment resolves to the polity it was routed to "
          f"({len(BASELINE)} baselined)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
