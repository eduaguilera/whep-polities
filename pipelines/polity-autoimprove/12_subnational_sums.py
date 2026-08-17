#!/usr/bin/env python3
"""Sub-national sums: where a source reports a whole and its parts, test parts == whole.

Issue #29 listed five candidate identities. Three are done (06 land use, 07 area x yield,
10 livestock), one is retracted (heads x carcass weight is a stock times a rate against a
flow, and 10's docstring records the case that breaks it), and this is the last one: "where
a source reports both a country and its provinces (`Indonesia Java and Madura` etc.), the
parts should sum to the whole -- which also detects double-counting."

FIRST QUESTION: DOES THE IDENTITY EXIST? It does, and it holds TO THE PRINTED DIGIT rather
than approximately, which is the whole reason it is usable. Of the 128 (table, item,
indicator, unit, period) keys where a whole and at least two of its parts are all present,
93 have the parts summing to the stated whole with a residual of EXACTLY zero -- Germany
1949 rye 5,338 = 2,025 East + 3,310 West + 3 Berlin, Indonesia 1951 soybean area 396 = Java
and Madura + Bali and Lombok + Other islands, British Borneo 1951 population 953 = Brunei +
North Borneo + Sarawak -- and not one key lands between zero and one. Nothing distributional
is assumed anywhere below.

WHICH SOURCES HAVE IT AT ALL. Only fao1952. The other four layer-B sources carry no
sub-national label structure: `iia` and `mitchell` each produce exactly one prefix pair
("ethiopia"/"ethiopia pdr", "rwanda"/"rwanda and burundi") and both are composite or
successor labels rather than a part of a whole, and `juan` and `sa_colonial` produce none.
So this script reads fao1952 and says so, rather than looping over sources that cannot
contribute and reporting a clean zero.

WHAT IS AND IS NOT A DEFECT. The three-way split matters more here than in 06, because two
of the three directions are not errors:

  parts > whole   IMPOSSIBLE. A part cannot exceed its whole under any reading of the
                  labels, whichever cell is wrong. Reported.
  parts == whole  The identity holding. Not a value error -- but it PROVES the whole row is
                  an aggregate of the part rows inside one table, and layer B marks
                  `is_aggregate` False for every one of them (that column carries only the
                  yearbook's continental and world totals: 2,141 rows under seven labels,
                  `Total`, `Total north america`, `Total central america`,
                  `Total excluding the USSR`, `GENERAL TOTAL`,
                  `GENERAL TOTAL EXCLUDING THE USSR` and one bare `ASIA`, and no country
                  label at all). So each of these keys is a live double count for any
                  consumer that sums the source. Reported, as `mark_aggregate`.
  parts < whole   NOT DECIDABLE and deliberately NOT reported. The extraction holds only
                  some parts of most families, so a deficit is the expected state: the
                  Windward Islands' 1950 land-use block is short by 85 (1000 ha) because
                  three of the colony's islands are in the parquet and the rest are not,
                  and Germany's 1937 population is short by 14,782 because the Eastern zone
                  row is absent for that item. Flagging these would bury the 4 real defects
                  under 31 non-events.

WHY `mark_aggregate` IS NOT A PEDANTIC FINDING. The double count issue #29 predicted is
already live in this repository's own matches, because a whole and one of its parts can land
on the SAME polity code for the same year. Measured in matched_rows.parquet: `Indochina` and
`Indochina Viet Nam` both match FID-1887-1954; `Korea` and `Korea South` both match
KOR-1948-2025; `China`, `China 22 provinces` and `China Manchuria` all match CHN-1949-1950
and CHN-1950-2025; `Germany` and `Germany Western` both match DEU-1920-1938. So summing
layer B's fao1952 rows by polity code adds the aggregate to its own components -- the same
error 10_livestock_consistency.py measured at +21.6% for Argentine meat, arriving by a
different route. This script names the 93 keys where that is provably happening; it does not
change the alias map, because which of the two rows a given polity should keep is a matching
decision, not an arithmetic one.

A RULE TRIED AND REJECTED, because it is the obvious one. "A deficit where EVERY part of the
family is present is a defect" sounds sound and is not, because the parts this script can
discover are the ones the extraction happens to carry under the parent's own name -- not the
units the colony had. It fires on 5 keys and all 5 are non-defects: four are the Windward
Islands' 1950 land-use block, whose fourth island is in the parquet as
`British West Indies Dominica`, under a different prefix and so invisible to the family; the
fifth is Jamaica's 1951 irrigated area against `Jamaica St Lucia`, `Jamaica St Vincent` and
`Jamaica Trinidad and Tobago`, which are not parts of Jamaica at all but the same spillover
fault as defect 1 below, arriving as a deficit where the arithmetic cannot settle it. So the
rule is not applied, and the count it would have flagged is printed instead.

THE FOUR DEFECTS, in two families, and what the identity recovers.

1. LABEL SPILLOVER, RECOVERABLE (fao1952 hemp fibre, r_fao_crops_1952_101_101). France's
   own area for 1934-38 is 3 (1000 ha) and the two rows labelled `France Germany` and
   `France Eastern` sum to 10. The parquet's row order says what happened: after France's
   four rows come `France Germany` 6, `France Eastern` 4, then FOUR rows labelled bare
   `Western` 2/1/1/1 -- and the table is alphabetical, so what stood there was Germany with
   its Eastern and Western zones under a stacked label cell. The extraction glued the
   previous country's name onto two of the three lines and left the third bare. The
   identity settles it rather than merely suggesting it: 6 = 4 + 2 and 4.1 = 2.9 + 1.2, both
   exactly, so `France Germany` -> `Germany`, `France Eastern` -> `Germany Eastern`,
   `Western` -> `Germany Western`. This is the only relabel the hypothesis accepts, and it
   is required to hold on every key where the trio is complete, not just one.

2. THE PARENT CELL IS NOT THE TABLE'S TOTAL, NOT RECOVERABLE HERE (fao1952 pigs and
   buffaloes, China). `China` 1949 pigs is 95 (1000 heads) against `China 22 provinces`
   59,510 plus `China Taiwan` 167, and `China` buffaloes 658/656/568 for 1949-51 against
   `China 22 provinces` 9,460. No relabel of the parts fixes this because the offending
   cell is the parent's, and the arithmetic gives no candidate for it: unlike 06, there is
   no stated total to subtract from.

   The neighbourhood in table order suggests the cause is an off-by-one LABEL SHIFT across
   a run of rows rather than a corrupted number, and that is worth writing down even though
   this script cannot act on it. In the buffalo table the run reads Burma 1950 only (725),
   Ceylon 1949 only (748), China 1949-51 (658/656/568): 748 fits Burma's own 725 and
   658/656/568 fit a country of Ceylon's size, while China's real buffalo herd is the 9,460
   sitting one row below under `China 22 provinces`. Same shape in the pig table, where
   `China` 1949 = 95 continues Ceylon's 104/1950 and 75/1951. That is an extraction fault
   in a block of labels, upstream of anything a correction table can express as a cell
   edit, so both keys are reported as `review` with the parts named and no value proposed.

WHAT THIS DOES NOT COVER. Keys where the whole or any part has MORE THAN ONE row are
skipped (329 keys), because in those tables the parquet's rows are the table's COLUMNS laid
end to end and one label carries four parallel series -- the meat and poultry tables are the
whole of that set. That column dimension is recovered, and its identity exploited, by
10_livestock_consistency.py; guessing at it a second time here would only add a second way
to be wrong. Trade mirrors, the fourth item on issue #29's list, need bilateral data layer B
does not carry and are untouched.

Like 06, 07 and 10 this does NOT modify the source parquet (it lives outside the repo, in
the maintainer's own store): it writes a correction table so the fix lands upstream in the
consolidation step. `action` says what the upstream applier should do:

  relabel_rows    the parts belong to another whole; `proposed` gives `old -> new` per row
  review          the parent cell is wrong and the arithmetic proposes no value
  mark_aggregate  the whole IS the sum of its parts in this table, so `is_aggregate` should
                  be True on it -- or the consumer must exclude the parts

Usage:
  python3 pipelines/polity-autoimprove/12_subnational_sums.py
Writes state/subnational_sums.csv
"""
from __future__ import annotations

import os
import sys
import warnings

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extdata  # noqa: E402

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
OUT = os.path.join(H, "subnational_sums.csv")

# Suffixes that mean "this label is a COMPOSITE of two units", not "this is a part of the
# label before it": `Gold Coast and British Togoland`, `China 22 provinces & Taiwan`,
# `Aden Colony Inc Perim and Kuria`. Summing those against their prefix compares a union
# with one of its members and would report every one of them as a surplus.
COMPOSITE_PREFIXES = ("and ", "& ", "inc ", "inc", "including ")

# A family needs at least two parts present in a key before the sum means anything: one
# part against its whole is just the deficit case with n=1.
MIN_PARTS = 2


def tolerance(whole: float) -> float:
    """Window on "the parts sum to the whole": half a printed unit, NOT a percentage.

    The yearbook prints each cell to at most one decimal, so if the whole really is the sum
    of the parts the residual is a rounding artefact of a tenth or two. A percentage window
    would be the wrong instrument, and measurably so: at 0.5% of the whole, four keys pass
    as "the identity holds" whose parts are 6, 12, 18 and 31 units short of it (Germany's
    1937 population sub-items, where the Berlin row is absent for that item, and Indochina's
    1937 population), so the table would assert an exact aggregate relation about blocks
    that do not have one. Measured on the current parquet: 93 keys have residual EXACTLY 0,
    nothing at all lands between 0 and 1, and the rest are 1 or more.
    """
    return 0.5


def normalise(label: str) -> str:
    """Fold the punctuation variants the yearbook labels arrive in.

    `Libya: Cyrenaica` and `Libya Cyrenaica` are the same unit reported in two editions,
    and `Germany  Western` (two spaces) is the same as `Germany Western`.
    """
    return " ".join(str(label).replace(":", " ").split())


def discover_families(labels):
    """Map each whole to its parts, by LONGEST matching prefix.

    Longest wins so that `Aden Colony Inc Perim and Kuria` is read as a composite of
    `Aden Colony` -- and therefore dropped -- rather than as a part of `Aden`, where its
    suffix starts with `Colony` and nothing would filter it.
    """
    lower = {label: label.casefold() for label in labels}
    families: dict[str, list[str]] = {}
    for child in labels:
        parent = None
        for candidate in labels:
            if candidate == child:
                continue
            if lower[child].startswith(lower[candidate] + " ") and (
                parent is None or len(candidate) > len(parent)
            ):
                parent = candidate
        if parent is None:
            continue
        suffix = child[len(parent) + 1:]
        if suffix.casefold().startswith(COMPOSITE_PREFIXES):
            continue
        # `Indonesia 4`, `Kenya *`, `South West Africa :` -- a footnote marker the
        # extraction kept, not a unit.
        if len(suffix.strip("*: ")) < 2 or suffix.strip("*: ").isdigit():
            continue
        families.setdefault(parent, []).append(child)
    return {p: sorted(k) for p, k in families.items() if len(k) >= MIN_PARTS}


def spillover_relabel(frame, parent, kids, families):
    """Test the one hypothesis that RECOVERS a surplus, and return its relabelling or None.

    HYPOTHESIS. The parts are not parts of `parent` at all: the extraction glued `parent`'s
    name onto a following country's stacked label cell. Then stripping `parent` off the kid
    labels yields a real whole and one of its parts, and the remaining line of that cell is
    sitting in the same table under a BARE suffix label (`Western`) because it had no name
    to be glued to.

    ACCEPTED ONLY IF THE ARITHMETIC CONFIRMS IT: the stripped head must equal the sum of
    the other stripped labels plus the bare ones, within tolerance, on EVERY key where all
    of them are present, and on at least two keys. One key agreeing is a coincidence at
    these magnitudes; two independent indicators agreeing is not.
    """
    stripped = {kid: kid[len(parent) + 1:] for kid in kids}
    # The head is the stripped label that is a whole in its own right elsewhere in this
    # source, e.g. `Germany`. The others (`Eastern`) exist only as somebody's suffix.
    heads = [k for k, s in stripped.items() if s in families]
    if len(heads) != 1:
        return None
    head = heads[0]
    head_name = stripped[head]
    # (label to read the value under IN THIS TABLE, label it should have carried).
    members = [(kid, f"{head_name} {stripped[kid]}") for kid in kids if kid != head]
    # The bare lines of the same stacked label cell: labels in THIS table that are a suffix
    # of the head's own family, so `Western` where the head is `Germany`.
    members += [
        (label, f"{head_name} {label}")
        for label in frame.label.unique()
        if label != head_name and f"{head_name} {label}" in families[head_name]
    ]
    if not members:
        return None

    keys = ["item", "indicator", "unit", "year_key", "period_key"]
    reads = [head] + [m[0] for m in members]
    ok = seen = 0
    for _, block in frame[frame.label.isin(reads)].groupby(keys, dropna=False):
        values = dict(zip(block.label, block.value))
        total = values.get(head)          # the head arrives under its glued name
        if total is None or any(m not in values for m, _ in members):
            continue
        seen += 1
        ok += abs(sum(values[m] for m, _ in members) - total) <= tolerance(total)
    if seen < 2 or ok != seen:
        return None
    mapping = [(head, head_name)] + members
    return seen, "; ".join(f"{old} -> {new}" for old, new in mapping if old != new)


def main() -> int:
    frame = extdata.load_layer_b()
    frame = frame[(frame.source == "fao1952") & (~frame.is_aggregate)].copy()
    frame["label"] = frame.country.map(normalise)
    frame["year_key"] = frame.year.astype("string").fillna("")
    frame["period_key"] = frame.period.astype("string").fillna("")

    families = discover_families(sorted(frame.label.unique()))
    keys = ["source_detail", "item", "indicator", "unit", "year_key", "period_key"]

    rows = []
    n_keys = n_skipped = n_deficit = n_deficit_complete = n_exact = 0
    for parent, kids in sorted(families.items()):
        whole = frame[frame.label == parent]
        parts = frame[frame.label.isin(kids)]
        if whole.empty or parts.empty:
            continue
        w = whole.groupby(keys, dropna=False).value.agg(["sum", "count"])
        p = (
            parts.groupby(keys + ["label"], dropna=False)
            .value.agg(["sum", "count"])
            .reset_index()
        )
        n_skipped += int((w["count"] > 1).sum()) + int((p["count"] > 1).sum())
        w, p = w[w["count"] == 1], p[p["count"] == 1]
        agg = p.groupby(keys, dropna=False).agg(
            parts=("sum", "sum"),
            n_parts=("label", "nunique"),
            labels=("label", lambda s: "; ".join(sorted(s))),
        )
        joined = w[["sum"]].rename(columns={"sum": "whole"}).join(agg, how="inner")
        joined = joined[joined.n_parts >= MIN_PARTS]
        if joined.empty:
            continue
        n_keys += len(joined)

        relabel = None
        surplus = joined[joined.parts - joined.whole > joined.whole.map(tolerance)]
        if len(surplus):
            # The hypothesis is about ONE table's label cell, so it is tested on the table
            # the surplus is in and on the parts that table actually carries -- `France` has
            # a `France Saar` elsewhere in the source, and demanding a value for it here
            # would make every key incomplete and the test silently vacuous.
            here = frame[frame.source_detail.isin(
                surplus.reset_index().source_detail.unique())]
            relabel = spillover_relabel(
                here, parent, sorted(set(here.label) & set(kids)), families,
            )

        for key, r in joined.iterrows():
            residual = r.parts - r.whole
            tol = tolerance(r.whole)
            base = dict(
                zip(
                    ["source_detail", "item", "indicator", "unit", "year", "period"],
                    [str(k) for k in key],
                )
            )
            base.update(
                source="fao1952", whole_label=parent, part_labels=r.labels,
                n_parts=int(r.n_parts), whole=r.whole, parts_sum=round(r.parts, 6),
                residual=round(residual, 6),
            )
            if abs(residual) <= tol:
                n_exact += abs(residual) < 1e-9
                rows.append({
                    **base, "action": "mark_aggregate", "proposed": "",
                    "diagnosis": f"parts sum to the stated whole ({r.whole:,.1f}), so this "
                                 f"whole row is an aggregate of its {int(r.n_parts)} part "
                                 f"row(s) and is_aggregate is False on it",
                })
            elif residual > tol:
                if relabel:
                    seen, mapping = relabel
                    rows.append({
                        **base, "action": "relabel_rows", "proposed": mapping,
                        "diagnosis": f"label spillover: the parts are not parts of "
                                     f"{parent!r}; relabelled they satisfy the identity on "
                                     f"all {seen} complete key(s)",
                    })
                else:
                    rows.append({
                        **base, "action": "review", "proposed": "",
                        "diagnosis": f"parts sum to {r.parts:,.1f} against a whole of "
                                     f"{r.whole:,.1f}: a part cannot exceed its whole, and "
                                     f"no stated total localises the bad cell",
                    })
            else:
                # NOT REPORTED, and not because it is harmless: it is not decidable from
                # the parquet. See the docstring, including the rule tried and rejected.
                n_deficit += 1
                n_deficit_complete += int(r.n_parts) == len(kids)

    columns = [
        "source", "source_detail", "whole_label", "part_labels", "n_parts", "item",
        "indicator", "unit", "year", "period", "whole", "parts_sum", "residual",
        "action", "proposed", "diagnosis",
    ]
    out = pd.DataFrame(rows, columns=columns)
    if len(out):
        out = out.sort_values(["action", "residual"], ascending=[True, False])
        out.to_csv(OUT, index=False)

    print(f"fao1952 whole/part families discovered: {len(families)}")
    print(f"(table, item, indicator, unit, period) keys with a whole and >= {MIN_PARTS} "
          f"parts: {n_keys}")
    print(f"  skipped, whole or part has several rows under one label "
          f"(multi-column tables, see 10): {n_skipped}")
    holds = int((out.action == "mark_aggregate").sum()) if len(out) else 0
    print(f"  identity HOLDS: {holds} ({n_exact} of them EXACTLY)")
    print(f"  deficit, parts incomplete, NOT reported: {n_deficit} "
          f"({n_deficit_complete} with every discovered part present)")
    for action in ("relabel_rows", "review"):
        n = int((out.action == action).sum()) if len(out) else 0
        print(f"  {action}: {n}")
    if len(out):
        print()
        for r in out.itertuples():
            where = f"{r.whole_label} {r.item[:28]} {r.year or r.period}"
            print(f"  {r.action:14s} {where:52s} whole {r.whole:>10,.1f}  parts "
                  f"{r.parts_sum:>10,.1f}  [{r.part_labels[:60]}]")
        print(f"\nwrote {os.path.relpath(OUT, REPO)} ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
