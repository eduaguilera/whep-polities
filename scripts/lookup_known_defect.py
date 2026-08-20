#!/usr/bin/env python3
"""Before reporting a finding about a cell, ask whether it is already recorded.

WHY THIS EXISTS. `state/data_errors.csv` and `state/source_conventions.csv` hold established facts
about source defects and label semantics, and the way to consult them has been `grep`. That fails
often enough to be a pattern rather than an accident: on 2026-08-19 alone, twelve measurements were
re-derived from tracked state, and three of those became published claims that had to be retracted --
including a comment asserting that five specific cells were "outside every recorded scope" when they
were listed individually, with both sides' values, in a `confirmed` entry.

Grep fails here for a structural reason. The scope columns are often PLACEHOLDERS:

    label      "(16 labels; see summary)"      "(4 measured: czech republic, serbia, ...)"
    commodity  "(all)"                         "(multiple: sugar, p, n, groundnuts...)"

so the specific label, item and year live in the free-text `summary`. Grepping for `x10` finds the
entry named after a ten-fold error and misses the entry that merely CONTAINS a ten-fold cell.

THE DESIGN RULE THAT MATTERS: this tool must never answer "not recorded" when it cannot tell.
A lookup that reports a confident absence is worse than no lookup, because absence is what licenses
publishing. So every entry lands in exactly one of three buckets, and the middle one is the point:

    MATCH          the entry's SCOPE covers every dimension the caller gave
    INDETERMINATE  a scope field is a placeholder, so coverage cannot be decided from the
                   table -- READ THE SUMMARY
    no match       a dimension is present, parseable, and definitely excludes the query

An INDETERMINATE result is not a pass. It means a human reads that entry before publishing.

AND NEITHER IS A MATCH, WHICH IS THE MIRROR MISTAKE. A MATCH says the entry's declared scope
COVERS the query -- not that the query's specific cell is enumerated inside it. Those come apart
routinely, because an entry's scope is a year RANGE and a label LIST while its findings are
individual cells: `iia-attributable-single-cell-errors` declares `serbia / rye / 1920-1945` and
enumerates serbia rye divergences at 1931, 1932 and 1945 ONLY. Querying `serbia / rye / 1942`
returns MATCH, and the 1941-1944 block turned out to be an unrecorded defect (a cross-label
duplication with `czech republic`, whep-polities#433) sitting inside a covering entry.

So the two failure modes are opposite and both are real: treating absence as proof nothing is
recorded, and treating a scope match as proof the cell already is. This tool removes the first
and cannot remove the second -- only reading the summary does.

Usage:
  python3 scripts/lookup_known_defect.py --source iia --label serbia --item rye --year 1931
  python3 scripts/lookup_known_defect.py --label "czech republic" --year 1939
  python3 scripts/lookup_known_defect.py --item tobacco            # every entry touching tobacco
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
ERRORS = os.path.join(STATE, "data_errors.csv")
CONVENTIONS = os.path.join(STATE, "source_conventions.csv")
# The label-provenance table is the SECOND place a claim about a label is likely already recorded, and
# covering only data_errors is why this tool did not prevent its own author from filing whep-polities#483
# as new: `kwantung` was already there as `shares_target / redirected`, assigned to China, mainland, with
# china at 62% dominance. I had read that file earlier the same session. A lookup that covers one
# registry teaches you to trust it for all of them, which is worse than no lookup for the ones it omits.
PROVENANCE = os.path.join(STATE, "iia_label_provenance.csv")

# A scope cell that names a count or defers to prose instead of listing members. Coverage cannot be
# decided from these, which is exactly why they must not read as "no match".
PLACEHOLDER = re.compile(r"^\s*\(|see summary|\ball\b|\bmultiple\b|;\s*\.\.\.|\betc\b", re.I)


def norm(s) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", str(s or "").lower()).strip()


# THREE OUTCOMES, NOT TWO, and keeping them apart is what makes the tool usable. The first version
# returned None both for "the caller did not constrain this dimension" and for "the scope field is a
# placeholder", which are opposites: the first should be IGNORED, the second DEMANDS a human read.
# Conflating them made every entry indeterminate as soon as a flag was omitted -- a query for
# `--source iia --item tobacco --year 1934` reported no match while two confirmed tobacco entries
# covered it exactly.
NEUTRAL = "neutral"          # caller gave nothing for this dimension: no opinion, do not penalise
UNRESOLVED = "unresolved"    # scope is a placeholder: coverage cannot be decided from the table


def covers_text(field: str, needle: str):
    """True / False / NEUTRAL / UNRESOLVED for 'does this scope field cover `needle`?'"""
    if not needle:
        return NEUTRAL
    f = str(field or "")
    if not f.strip():
        return UNRESOLVED                # an empty scope says nothing about coverage
    n, fn = norm(needle), norm(f)
    if n and n in fn:
        return True
    # a placeholder may still cover it; the summary is where the members are
    if PLACEHOLDER.search(f):
        return UNRESOLVED
    # semicolon/comma lists are enumerations we CAN decide against
    return False


def covers_year(lo, hi, year):
    if year is None:
        return NEUTRAL
    try:
        lo_i, hi_i = int(str(lo).strip()), int(str(hi).strip())
    except (TypeError, ValueError):
        return UNRESOLVED
    return lo_i <= year <= hi_i


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source")
    ap.add_argument("--label")
    ap.add_argument("--item")
    ap.add_argument("--year", type=int)
    a = ap.parse_args()
    if not any((a.source, a.label, a.item, a.year)):
        ap.error("give at least one of --source/--label/--item/--year")

    if not os.path.exists(ERRORS):
        print(f"MISSING {os.path.relpath(ERRORS, REPO)}", file=sys.stderr)
        return 1
    rows = list(csv.DictReader(open(ERRORS, newline="")))

    matches, indet = [], []
    for r in rows:
        verdicts = {
            "source": covers_text(r.get("source"), a.source),
            "label": covers_text(r.get("label"), a.label),
            "item": covers_text(r.get("commodity"), a.item),
            "year": covers_year(r.get("year_min"), r.get("year_max"), a.year),
        }
        # THE SUMMARY IS PART OF THE SCOPE, not commentary. Specific cells live there when the
        # columns are placeholders -- the serbia rye cells that caused this tool to exist are named
        # only in prose. A hit there upgrades an indeterminate dimension, never a definite exclusion.
        summ = str(r.get("summary") or "")
        for dim, needle in (("label", a.label), ("item", a.item)):
            if verdicts[dim] == UNRESOLVED and needle and norm(needle) in norm(summ):
                verdicts[dim] = True
        if any(v is False for v in verdicts.values()):
            continue                     # a parseable scope definitely excludes the query
        vals = list(verdicts.values())
        if any(v == UNRESOLVED for v in vals):
            indet.append((r, verdicts))  # a human must read this one
        elif any(v is True for v in vals):
            matches.append((r, verdicts))  # every constrained dimension is covered

    # --- label provenance: does a raw or layer-B label already have a recorded classification? ---
    # TOKEN matching, not substring. A substring test made `--label china` return `cochinchina` and
    # `indochina` -- both contain "china" and neither has anything to do with the query. Same
    # naming-heuristic trap as assuming a delimiter or reading "share" inside "shared".
    prov = []
    if a.label and os.path.exists(PROVENANCE):
        want = set(norm(a.label).split())
        for r in csv.DictReader(open(PROVENANCE, newline="")):
            for field in ("raw_label", "layer_b_label", "assigned_modern"):
                have = set(norm(r.get(field)).split())
                if have and (want <= have or have <= want):
                    prov.append((field, r))
                    break

    given = {k: v for k, v in (("source", a.source), ("label", a.label),
                               ("item", a.item), ("year", a.year)) if v}
    print(f"query: {given}")
    print(f"scanned {len(rows)} data_errors entries\n")

    if matches:
        print(f"MATCH -- the entry's SCOPE covers your query ({len(matches)}). This does NOT mean your")
        print("cell is enumerated inside it: scope is a year range and a label list, findings are cells.")
        for r, _ in matches:
            print(f"  {r['issue_id']}  [{r['status']}]  {r['year_min']}-{r['year_max']}")
            print(f"      source={r['source']!r} label={r['label']!r} commodity={r['commodity']!r}")
    if indet:
        print(f"\nINDETERMINATE -- scope cannot be decided from the table; READ THESE ({len(indet)}):")
        for r, v in indet:
            why = ", ".join(f"{k} unresolved" for k, x in v.items() if x == UNRESOLVED) or "partial"
            print(f"  {r['issue_id']}  [{r['status']}]  {r['year_min']}-{r['year_max']}  ({why})")
    if a.label and not prov and os.path.exists(PROVENANCE):
        print(f"\nLABEL PROVENANCE -- no row matches {a.label!r} BY NAME, which is NOT proof the "
              f"territory is unrecorded.")
        print("  The table keys on the raw label's own spelling, and a territory is often filed under a")
        print("  different one: KARAFUTO is recorded as `japan: sakhalin`, so `--label karafuto` finds")
        print("  nothing while the routing is documented. Grep the table for the territory's other")
        print("  names before concluding it is absent:")
        print(f"    {os.path.relpath(PROVENANCE, REPO)}")
    if prov:
        print(f"\nLABEL PROVENANCE -- this label already carries a recorded classification ({len(prov)}):")
        for field, r in prov[:6]:
            print(f"  matched on {field}: raw={r.get('raw_label')!r} -> layer_b={r.get('layer_b_label')!r}"
                  f" (assigned {r.get('assigned_modern')!r})")
            print(f"    kind={r.get('kind')!r} territory_signal={r.get('territory_signal')!r} "
                  f"mixing_observed={r.get('mixing_observed')!r}")
            print(f"    fingerprint: {r.get('fingerprint_note')!r} "
                  f"dominant={r.get('dominant_raw_label')!r} @ {r.get('dominant_share')!r}")
        print("  A classification here means the ROUTING is known. It does NOT quantify how many cells")
        print("  are affected, so a measured count can still be new -- but say what was already recorded.")

    if not matches and not indet:
        print("no entry can cover this query on the dimensions given.")
        print("That is a definite NO only for the dimensions you constrained -- narrow queries")
        print("exclude more entries, so re-run with fewer flags before concluding it is unrecorded.")
    else:
        print("\nRead the summaries before publishing -- an INDETERMINATE is not a pass, and a MATCH is")
        print("not proof the cell is already recorded:")
        print(f"  {os.path.relpath(ERRORS, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
