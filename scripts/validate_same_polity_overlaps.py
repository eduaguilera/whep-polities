#!/usr/bin/env python3
"""Do two labels of ONE source land on ONE polity and disagree about the same cell?

`validate_composition_sums.py` check C forbids an undeclared double count between a registered
whole and part. It needs TWO polity codes to do that, and `polity_composition.csv` is keyed on
`(whole_code, part_code)`, so the case where **both labels route to the same code** has no pair to
register and no check to catch it. Issue 355 raised it and proposed a second registry.

`pipelines/polity-autoimprove/25_same_polity_overlaps.py` derives them from the matcher's actual
routings and writes `state/same_polity_overlaps.csv`. The panel is gitignored and absent in CI, so
this gate reads the committed table -- the same arrangement as `validate_isolated_spikes.py`,
`validate_constant_runs.py` and `validate_source_splices.py`.

WHY THE DERIVED VERSION REPLACED THE STRING TEST. Issue 355 found its four by asking whether one
label was a prefix-extension of another. That matched 39 polities of which 4 were real: `'Lao'`
extends to `"Lao People's Democratic Republic"`, and eight spellings of `'Trieste UK-US'` extend to
each other. Label shape cannot distinguish a parent from a longer synonym; a shared (item, unit,
year) cell can, because a parent and its part disagree there and two synonyms do not.

WHAT THE FIRST RUN MEASURED: 37 pairs share at least one cell, 13 of them with enough cells to
support any verdict at all.

    containment           4    `Germany` over `Germany Western` (25 cells) and over `Germany Berlin`
                               (8); `Germany Berlin` over `Germany Western` (9); mitchell
                               `china, mainland` over `china, manchuria province of` (8)
    identical             1    mitchell `cape natal` equals `south africa` in all 12 shared cattle
                               cells, 1946-1957, over 12 distinct values -- a province carrying the
                               national series
    disagreement          2    fao1952 `New Guinea` / `Papua`, 9 cells running both directions; and
                               `Korea` / `Korea South`, 5 cells, see the KOR note below
    identical_indistinct  3    equal, but on one cell, which proves nothing
    undetermined         14    too few shared cells to say anything

    (Counts as of the fao1952 `indicator` key, issue 451. Before it: 37 pairs, with 5 containment,
    3 orthographic_variant and 24 undetermined. `orthographic_variant` is now empty and
    `United Kingdom`/`United Kingdom Great Britain` fell from containment to undetermined at 4 cells,
    below the floor -- both because their extra "shared" cells were population-indicator artefacts.)

ONE OF ISSUE 355'S FOUR NOW SURVIVES AS A SUPPORTED FINDING, and three still do not.
`indochina viet nam` no longer routes to FID-1887-1954 at all; RWB's `rwanda`/`rwanda and burundi`
share no cells; GBM's two labels are disjoint in year. KOR's `Korea`/`Korea South` DOES survive since
the fao1952 `indicator` key (issue 451): it has 5 shared cells rather than 4, exactly at the floor
where direction means anything, and classifies as `disagreement`. Before the key it sat one cell below
that floor -- so the string test issue 355 used happened to name a real pair, but only the cell
evidence can say which, and it could only say so once the indicator stopped merging cells.
The other real overlaps are different pairs, which a string test could not have found.

Two signals:
  A. COUNT CEILING   pairs sharing cells may not grow. Bidirectional: reroute some and the ceiling
                     must come down with a note, so the table cannot quietly refill.
  B. EVERY SUPPORTED PAIR is pinned by identity, including its relation, so a pair cannot silently
     change verdict -- a `containment` becoming a `disagreement` means a routing moved.

Usage:
  python3 scripts/validate_same_polity_overlaps.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/same_polity_overlaps.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

# Measured 2026-08-19. BIDIRECTIONAL: rerouting a label must lower this, with a note saying which
# pair was resolved, so a later regression cannot hide inside the old headroom.
#
# LOWERED 37 -> 24 when the generator began keying fao1952 on `indicator` (issue 451). The 13 pairs
# that went were not resolved by a reroute -- they were never real: their ONLY shared cell was an
# `r_fao_population_1952_10_18` cell, and that item code carries five distinct indicators (issue 13),
# so two labels reporting DIFFERENT measures read as sharing one. Three of the 13 carried
# `orthographic_variant`; that loses a row, not a finding, because the generator's own docstring
# already records all 30 such fao1952 groups in prose and explains why shared-cell pairs are the
# only ones tabled.
BASELINE_PAIRS = 24

# The floor 25_same_polity_overlaps.py needs before it will call a direction; restated here so the
# gate does not depend on the generator's constant to know what `undetermined` means.
MIN_DIRECTIONAL = 5

RELATIONS = {"containment", "identical", "identical_indistinct", "disagreement",
             "orthographic_variant", "undetermined"}

# Every pair with a supported verdict on the first run. GENERATED FROM THE TABLE, never hand-typed --
# transcribing a baseline from a truncated printout once missed 18 of 30 entries.
# KOR-1948-2025 enters this set as a `disagreement` only once fao1952 is keyed on `indicator`: with
# the key, `Korea` and `Korea South` share 5 cells instead of 4, and the added one is decisive --
# 1951 population, both rows `indicator = population:population total`, 29,300 thousand against
# 20,500. The first is the whole peninsula and the second is South Korea, so the polity carries a
# figure for a territory 43% larger than itself alongside the correct one. RECORDED, NOT RESOLVED:
# `data_errors.csv`'s `layerb-nested-reporting-levels-one-polity` already lists this pair among 52
# such cells with status `pending_audit`, and the audit is where the reroute decision belongs.
BASELINE_SUPPORTED = frozenset({
    ('CHN-1950-2025', 'mitchell', 'china, mainland', 'china, manchuria province of', 'containment'),
    ('DEU-1920-1938', 'fao1952', 'Germany', 'Germany Berlin', 'containment'),
    ('DEU-1920-1938', 'fao1952', 'Germany', 'Germany Western', 'containment'),
    ('DEU-1920-1938', 'fao1952', 'Germany Berlin', 'Germany Western', 'containment'),
    ('ETH-1907-1936', 'iia', 'ethiopia', 'ethiopia pdr', 'identical_indistinct'),
    ('ETH-1936-1941', 'iia', 'ethiopia', 'ethiopia pdr', 'identical_indistinct'),
    ('ETH-1941-1952', 'iia', 'ethiopia', 'ethiopia pdr', 'identical_indistinct'),
    ('KOR-1948-2025', 'fao1952', 'Korea', 'Korea South', 'disagreement'),
    ('PNG-1949-1975', 'fao1952', 'New Guinea', 'Papua', 'disagreement'),
    ('ZAF-1910-2025', 'mitchell', 'cape natal', 'south africa', 'identical'),
})


def key(r):
    return (r["whep_code"], r["source"], r["label_a"], r["label_b"], r["relation"])


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run 25_same_polity_overlaps.py --write",
              file=sys.stderr)
        return 1
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    supported = [r for r in rows if r["relation"] != "undetermined"]
    print(f"same-polity label overlaps: {len(rows)} sharing cells "
          f"(ceiling {BASELINE_PAIRS}), {len(supported)} supported (pinned {len(BASELINE_SUPPORTED)})")

    problems = []
    if len(rows) > BASELINE_PAIRS:
        problems.append(
            f"{len(rows)} label pairs share a cell on one polity, above the ceiling of "
            f"{BASELINE_PAIRS}. Two labels of one source describing one polity-item-year hold two "
            f"numbers for it, and nothing downstream can choose between them")
    elif len(rows) < BASELINE_PAIRS:
        problems.append(
            f"only {len(rows)} pairs remain, below the pinned ceiling of {BASELINE_PAIRS} — lower the "
            f"baseline and say which routing was fixed")

    seen = {key(r) for r in supported}
    for k in sorted(seen - BASELINE_SUPPORTED):
        problems.append(
            f"NEW {k[4]}: {k[0]} receives {k[2]!r} and {k[3]!r} from {k[1]}, and they collide on "
            f"cells this database cannot reconcile — reroute one label or record why both belong")
    for k in sorted(BASELINE_SUPPORTED - seen):
        problems.append(
            f"{k[0]} {k[2]!r}/{k[3]!r} is pinned as {k[4]} but the table no longer says so — remove "
            f"its entry, saying what changed, or restore the routing")

    # A relation the generator cannot emit means the table and this gate disagree about the
    # vocabulary, and every pinned key above would be comparing against nothing.
    for r in rows:
        if r["relation"] not in RELATIONS:
            problems.append(f"unknown relation {r['relation']!r} for {r['whep_code']} — "
                            f"generator and gate disagree about the vocabulary")
        n = int(r["shared_cells"])
        if n != int(r["n_equal"]) + int(r["n_a_gt_b"]) + int(r["n_b_gt_a"]):
            problems.append(
                f"{r['whep_code']} {r['label_a']!r}/{r['label_b']!r}: equal+greater+lesser does not "
                f"add to {n} shared cells — the table is internally inconsistent")
        if r["relation"] in ("containment", "disagreement") and n < MIN_DIRECTIONAL:
            problems.append(
                f"{r['whep_code']} {r['label_a']!r}/{r['label_b']!r} claims {r['relation']} on {n} "
                f"cells, under the floor of {MIN_DIRECTIONAL} where direction is a coin flip")

    # Every code must be a real polity, or the pins above refer to nothing. NOT conditional on the
    # file existing: this check shipped pointing at `data/final/polities.csv`, which is not the name
    # of anything in this repo, so `os.path.exists` was False and the whole arm silently no-opped --
    # the exact failure this gate's own docstring cites from issue 387. An absent input is a FAILURE.
    if not os.path.exists(POLITIES):
        problems.append(f"{os.path.relpath(POLITIES, REPO)} is missing, so no code here can be "
                        f"checked against a real polity")
    else:
        with open(POLITIES, encoding="utf-8") as fh:
            live = {r["polity_code"] for r in csv.DictReader(fh)}
        for code in sorted({r["whep_code"] for r in rows} - live):
            problems.append(
                f"{code} is not a polity in {os.path.relpath(POLITIES, REPO)} — every pinned pair "
                f"above refers to it, so the pin is checking against nothing")

    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
