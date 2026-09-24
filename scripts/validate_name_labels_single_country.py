#!/usr/bin/env python3
"""A name label must not belong to reporting units in two different countries.

The subnational panel identifies each reporting unit two ways: an `admin_unit_id` that carries
its country ('ARG-SANTACRUZ', 'BOL-SANTACRUZ') and an `admin_name_clean` that does not
('Santa Cruz', 'Santa Cruz'). The alias map resolves a label whatever form it takes -- routing
reads the unit id OR the name, because the slugs disagree about which one they use (see
validate_routed_units_are_aliased.py). So a rule keyed on a bare NAME applies to every unit in
the panel that carries that name, in every country.

WHAT IT FOUND (2026-09-24). Two name-keyed juan-subnational rules routed another country's data:

    'Santa Cruz'        -> ARG-SANTACRUZ-*    also Bolivia's BOL-SANTACRUZ: 7,164 valued rows
    'Distrito Federal'  -> BRA-DF / BRA-DFRJ  also Mexico's MEX-CMX, which the panel names
                                              'Distrito Federal' in part of its span: 861 rows

Both units already had an id-keyed rule for their own polity, so the name rule added nothing for
the unit it was written for and a second, contradictory candidate for the other one. Nothing was
malformed: each rule named a live polity inside its span, and every per-label check passed.

WHAT THIS CHECKS. Every label in data/final/label_alias_map.csv, of any source, that is the
`admin_name` of harness-ledger units in two or more countries fails. The ledger is the committed
record of the panel's units, so the gate runs anywhere; the panel itself is gitignored.

WHAT IT CANNOT SEE. The ledger keeps one name per unit. MEX-CMX is recorded as 'Ciudad de
Mexico', so the 'Distrito Federal' collision above is invisible here -- it was found by reading
the panel. A unit's other names reach this gate only if they reach the ledger.

Bidirectional baseline: a new collision fails, and a baselined one that no longer occurs must be
removed or this fails too.

Usage:
  python3 scripts/validate_name_labels_single_country.py
"""
import collections
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "pipelines/agent-harness/state/routing_verdicts.csv")
ALIASES = os.path.join(REPO, "data/final/label_alias_map.csv")

# label -> reason it is knowingly left in place.
BASELINE = {}


def main() -> int:
    if not os.path.exists(LEDGER):
        print(f"FAIL: {os.path.relpath(LEDGER, REPO)} is missing")
        return 1
    csv.field_size_limit(sys.maxsize)

    by_name = collections.defaultdict(set)
    with open(LEDGER, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            name = (r.get("admin_name") or "").strip()
            if name:
                by_name[name].add(((r.get("country") or "").strip(), r["unit_id"]))
    shared = {n: u for n, u in by_name.items() if len({c for c, _ in u}) > 1}

    hits = collections.defaultdict(set)
    with open(ALIASES, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            label = r["source_label"].strip()
            if label in shared:
                hits[label].add((r["source"], r["polity_code"]))

    stale = sorted(set(BASELINE) - set(hits))
    if stale:
        print(f"FAIL: {len(stale)} baseline entr(ies) no longer needed -- remove them:")
        for label in stale:
            print(f"  {label!r}: {BASELINE[label]}")
        return 1

    new = sorted(set(hits) - set(BASELINE))
    if new:
        print(f"FAIL: {len(new)} alias label(s) name reporting units in more than one country\n")
        for label in new:
            units = ", ".join(f"{u} ({c})" for c, u in sorted(shared[label]))
            rules = ", ".join(f"{s or '(any)'} -> {p}" for s, p in sorted(hits[label]))
            print(f"  {label!r}  is the name of {units}")
            print(f"      aliased as {rules}")
        print("\nRouting resolves a unit by its id OR its name, so a rule keyed on a shared name "
              "sends every country's unit of that name to one polity. Key the rule on the "
              "unit id (e.g. 'ARG-SANTACRUZ' under whep-lab-latam) and remove the name rule from "
              "pipelines/polity-autoimprove/state/applied_aliases.csv, then regenerate with "
              "scripts/write_label_alias_map.py.")
        return 1

    print(f"PASS: no alias label names reporting units in two countries "
          f"({len(shared)} shared ledger name(s) checked, {len(BASELINE)} baselined)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
