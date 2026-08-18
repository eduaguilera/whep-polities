#!/usr/bin/env python3
"""Does a series that switches SOURCE mid-stream stay on the same scale?

Layer B assigns every (country, year, item, unit) cell to exactly ONE source — zero of its 179,097
cells carry two. Sources are partitioned, never overlaid, so a series drawing on more than one is
SPLICED, and every splice is a seam where a scale mismatch can enter unnoticed.

`pipelines/polity-autoimprove/16_source_splices.py` measures the seams from the panel and writes
`state/source_splices.csv`. The panel is gitignored and absent in CI, so this gate reads the committed
table instead — the same arrangement as `validate_iia_label_provenance.py` and its provenance tables.

WHAT THE FIRST RUN FOUND (issue 360):

    adjacent-year seams where the value moves >30%     373
      by more than 3x                                  123
      by more than 10x                                  66
      by more than 100x                                 30

And it is not one bad source: >3x seams are near-symmetric across every pairing (`iia->mitchell` 26,
`mitchell->iia` 25, `juan->iia` 20, `iia->juan` 19, `juan->mitchell` 19, `mitchell->juan` 14).

THE CLUSTER THAT MAKES IT DIAGNOSABLE. Nine countries show `tobacco, unmanufactured` jumping a median
of **x101** at exactly 1939->1940 on a `mitchell->iia` seam, and back DOWN by the same factor at
1940->1941 on the return seam. Japan reads 86,000 t (1939, mitchell), 8,705,400 t (1940, iia), 84,000 t
(1941, mitchell) — a one-year x101 spike. World tobacco production in 1940 was on the order of 2-3
Mt, so 8.7 Mt for Japan alone is impossible. 40 IIA tobacco cells are implausibly large on that
evidence, logged as `iia-tobacco-implausible-magnitudes`. The x101 factor holds only where the
comparison value is ADJACENT-year, so the implausibility is established and the per-row multiplier is
NOT: those cells should be dropped, not rescaled. Same shape, smaller factor, in livestock: `swine, pigs` seams at 1950->1951 and 1955->1956
(`mitchell->juan`) sit at exactly 0.5, and `cattle` 1954->1955 at 2.1.

This is the already-recorded `iia-layerb-magnitude-scale-inconsistent` error (`state/data_errors.csv`,
`pending_audit`) pinned to a specific item and factor, and shown not to be confined to IIA.

Two signals:
  A. COUNT CEILING   the number of >30% seams may not grow. Bidirectional: fix some and the ceiling
                     must come down with a note, so the file cannot quietly refill.
  B. EXTREME SEAMS   every seam above 100x is pinned by identity, because those are the mechanical
                     ones and each is a single lookup in two sources. A new one is a regression.

Usage:
  python3 scripts/validate_source_splices.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/source_splices.csv")

# Measured 2026-08-18 on the first run. BIDIRECTIONAL: repairing seams must lower this, with a note
# saying which were repaired, so a later regression cannot hide inside the old headroom.
BASELINE_SEAMS = 373

# Seams above this factor are mechanical rather than arguable and are pinned individually.
EXTREME = 100.0


def key(r):
    return (r["country"], r["item"], r["unit"], r["year_before"],
            r["source_before"], r["source_after"])


# Every seam above EXTREME on the first run. EVERY BASELINE MUST BE A frozenset({...}).
BASELINE_EXTREME = frozenset({
    ("argentina", "rapeseed", "ha", "1939", "iia", "juan"),
    ("canada", "flax fibre and tow", "ha", "1920", "mitchell", "juan"),
    ("canada", "flax fibre and tow", "ha", "1924", "juan", "mitchell"),
    ("canada", "flax fibre and tow", "ha", "1925", "mitchell", "juan"),
    ("canada", "flax fibre and tow", "ha", "1951", "juan", "mitchell"),
    ("canada", "flax fibre and tow", "ha", "1952", "mitchell", "juan"),
    ("canada", "flax fibre and tow", "ha", "1956", "juan", "mitchell"),
    ("china mainland", "tobacco unmanufactured", "tonnes", "1939", "mitchell", "iia"),
    ("china mainland", "tobacco unmanufactured", "tonnes", "1940", "iia", "mitchell"),
    ("greece", "grapes", "tonnes", "1932", "juan", "iia"),
    ("india", "groundnuts with shell", "tonnes", "1944", "mitchell", "iia"),
    ("india", "groundnuts with shell", "tonnes", "1945", "iia", "mitchell"),
    ("iran", "tobacco unmanufactured", "tonnes", "1940", "iia", "mitchell"),
    ("iraq", "tobacco unmanufactured", "tonnes", "1939", "mitchell", "iia"),
    ("iraq", "tobacco unmanufactured", "tonnes", "1940", "iia", "mitchell"),
    ("japan", "tobacco unmanufactured", "tonnes", "1939", "mitchell", "iia"),
    ("japan", "tobacco unmanufactured", "tonnes", "1940", "iia", "mitchell"),
    ("madagascar", "tobacco unmanufactured", "tonnes", "1945", "iia", "mitchell"),
    ("myanmar", "tobacco unmanufactured", "tonnes", "1939", "mitchell", "iia"),
    ("myanmar", "tobacco unmanufactured", "tonnes", "1940", "iia", "mitchell"),
    ("philippines", "tobacco unmanufactured", "tonnes", "1939", "mitchell", "iia"),
    ("syrian arab republic", "tobacco unmanufactured", "tonnes", "1944", "iia", "mitchell"),
    ("turkey", "tobacco unmanufactured", "tonnes", "1939", "mitchell", "iia"),
    ("turkey", "tobacco unmanufactured", "tonnes", "1940", "iia", "mitchell"),
    ("united kingdom", "sheep", "heads", "1866", "mitchell", "juan"),
    ("united states of america", "flax fibre and tow", "ha", "1938", "mitchell", "juan"),
    ("united states of america", "flax fibre and tow", "ha", "1949", "juan", "mitchell"),
    ("united states of america", "flax fibre and tow", "ha", "1950", "mitchell", "juan"),
    ("united states of america", "flax fibre and tow", "ha", "1951", "juan", "mitchell"),
    ("united states of america", "flax fibre and tow", "tonnes", "1938", "iia", "juan"),
})


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 16_source_splices.py --write")
        return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    extreme = {key(r) for r in rows
               if float(r["ratio"]) > EXTREME or float(r["ratio"]) < 1 / EXTREME}
    print(f"recorded seams: {len(rows)} (ceiling {BASELINE_SEAMS})")
    print(f"  above {EXTREME:.0f}x: {len(extreme)} (pinned {len(BASELINE_EXTREME)})")

    problems = []
    if len(rows) > BASELINE_SEAMS:
        problems.append(
            f"{len(rows)} source seams move the value by more than 30%, above the ceiling of "
            f"{BASELINE_SEAMS}. A jump at exactly the year the source changes is not a harvest or a "
            f"border — something new is being spliced onto a different scale")
    elif len(rows) < BASELINE_SEAMS:
        problems.append(
            f"only {len(rows)} seams remain, below the pinned ceiling of {BASELINE_SEAMS} — lower the "
            f"baseline and say which were repaired and how")

    for k in sorted(extreme - BASELINE_EXTREME):
        problems.append(
            f"NEW seam above {EXTREME:.0f}x: {k[0]} / {k[1]} ({k[2]}) at {k[3]}, "
            f"{k[4]} -> {k[5]}. Factors this size are mechanical — a unit or thousands multiplier — "
            f"and are one lookup in each source to settle")
    for k in sorted(BASELINE_EXTREME - extreme):
        problems.append(
            f"{k[0]} / {k[1]} at {k[3]} is pinned as an extreme seam but is not one any more — remove "
            f"its entry, saying what was repaired")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: no new source seam, and every extreme one is accounted for")
    return 0


if __name__ == "__main__":
    sys.exit(main())
