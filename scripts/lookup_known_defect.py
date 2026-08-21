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



# Directories whose SOURCE documents established mechanisms. A convention, a swap, a scope rule or an
# exclusion is written where it is RE-TESTED, in a docstring or a constant block, and no state table
# indexes that.
MECHANISM_DIRS = ("pipelines/polity-autoimprove", "scripts")

# Labels this common match everything and their hits carry no information.
TOO_COMMON = frozenset({"total", "world", "other", "all", "none"})


def mechanism_hits(needles: list) -> list:
    """Where in the TOOL SOURCE is this label or item already discussed?

    WHY THIS ARM EXISTS. On 2026-08-21 the same mistake was made three times in one day: a mechanism was
    published as a finding when it was already written down -- and each time the record was in a place
    this tool did not read. The worst was `austria`'s meslin false zero, documented in
    `11_retest_conventions.py`'s RATIO_ONLY_SWAP_LABELS comment with the same cell, the same 0.15% match
    and an explicit attribution to issue 414, while data_errors.csv and the provenance tables (which this
    tool did read) said nothing. A grep would have found it in one second.

    So this reports FILE AND LINE for every mention of the queried label or item in the pipeline and gate
    source. It is deliberately dumb -- a substring match on comments, docstrings and constants alike --
    because the exclusion lists that matter (RATIO_ONLY_SWAP_LABELS, SWAPPED_PAIRS, BASELINE,
    SOURCE_NOTES) are literals, and a smarter parser would miss the prose around them.

    Hits are NOT evidence that a finding is already recorded; they are places to read before claiming it
    is not. The distinction matters because a common label appears in dozens of unrelated files.
    """
    out = []
    for d in MECHANISM_DIRS:
        base = os.path.join(REPO, d)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(base, name)
            try:
                lines = open(path, encoding="utf-8").read().splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                low = line.lower()
                hit = [n for n in needles if n in low]
                if hit:
                    out.append((os.path.join(d, name), i, hit, line.strip()[:130]))
    return out


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
            print(f"  matched on {field}: raw_label={r.get('raw_label')!r} -> "
                  f"layer_b={r.get('layer_b_label')!r} (assigned {r.get('assigned_modern')!r})")
            print(f"    kind={r.get('kind')!r} territory_signal={r.get('territory_signal')!r} "
                  f"mixing_observed={r.get('mixing_observed')!r}")
            print(f"    fingerprint: {r.get('fingerprint_note')!r} "
                  f"dominant={r.get('dominant_raw_label')!r} @ {r.get('dominant_share')!r}")
        print("  A classification here means the ROUTING is known. It does NOT quantify how many cells")
        print("  are affected, so a measured count can still be new -- but say what was already recorded.")
        print("  NOTE `raw_label` is a CANONICAL territory name, not the raw extract's label (it matches")
        print("  the extract in only 32% of rows). `dominant` IS the extract's label -- 100% of rows --")
        print("  so join on that: e.g. canonical `cyprus` is `british cyprus` in the extract.")

    # --- mechanisms documented in tool source, which no state table indexes ---
    needles = [n for n in (str(a.label or "").strip().lower(), str(a.item or "").strip().lower())
               if n and n not in TOO_COMMON and len(n) >= 4]
    if needles:
        hits = mechanism_hits(needles)
        if hits:
            byfile = {}
            for f, ln, needle, text in hits:
                byfile.setdefault(f, []).append((ln, needle, text))
            print(f"\nMECHANISMS IN TOOL SOURCE -- {len(hits)} mention(s) across {len(byfile)} file(s). "
                  f"These are NOT")
            print("  proof the finding is recorded, but they are where a convention, swap, scope rule or")
            print("  exclusion list would be written, and no state table indexes them. READ THEM FIRST:")
            for f in sorted(byfile, key=lambda k: -len(byfile[k]))[:8]:
                # A LINE MENTIONING EVERY NEEDLE COMES FIRST. That ranking is the whole point: the line
                # this tool was written for -- 11_retest_conventions.py's
                # "austria  iia_1938_39 prints meslin = 0.0 for 1933, a false zero of issue 414's class"
                # -- names BOTH the label and the item, while the 19 other `austria` mentions in that file
                # name only one. Showing hits in line order buried it under a docstring.
                rows = sorted(byfile[f], key=lambda r: (-len(r[1]), r[0]))
                print(f"  {f}  ({len(rows)} mention(s))")
                for ln, hit, text in rows[:3]:
                    print(f"    :{ln}  [{'+'.join(hit)}]  {text}")
                if len(rows) > 3:
                    print(f"    ... and {len(rows) - 3} more in this file")
        else:
            print(f"\nMECHANISMS IN TOOL SOURCE -- no mention of {needles} in the pipeline or gate "
                  f"source.")

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
