#!/usr/bin/env python3
"""Can a verdict claim the source territory EQUALS the polity's, when the label mixes territories?

WHAT THIS RECORDS. `state/iia_label_provenance.csv` is derived from the IIA harmonisation mapping
(`harmonization_geography.xlsx`, sheet `iia harmonization`): 335 raw yearbook labels collapsed onto
173 modern countries. Until it was tracked, that mapping was the only record of where each IIA row's
territory came from and it lived in one person's Downloads folder — so nothing in this repository
could tell that `serbia` means Yugoslavia or that `viet nam` means Tonkin.

    one_to_one                104   one raw label, one target — clean
    shares_target              97   several labels on one target, none nested in another
    sub_of_sibling             86   A SUB-LABEL merged onto the same target as its parent
    whole_with_sub_siblings    40   the parent side of those 86
    multi_country               8   the mapping's own `notes` name several modern countries

THE DEFECT THE LAST TWO ROWS DESCRIBE. `Indonesia` receives `dutch east indies` AND
`dutch east indies: java and madura` — a colony and a ~7% subset of it. `Viet Nam` receives
`indochina` and `indochina: tonkin` and `indochina: annam`. `Congo` receives
`french equatorial africa` and two of its constituent territories. And the eight `multi_country`
rows are declared in the mapping's own notes: `austria-hungary` -> Austria (13 successor countries),
`french west africa` -> Niger (8 territories), `anglo-egyptian sudan` -> EGYPT (a territory that is
Sudan).

IT IS NOT DOUBLE COUNTING, WHICH IS WHY NOTHING ELSE CATCHES IT. Layer B deduplicates: there are
zero duplicate (label, year, item, unit) keys across its 20,012 dated IIA rows. So when a whole and
a part both report a cell, ONE SILENTLY WINS and the surviving row carries no trace of which.
Measured on Indonesia the winner varies by commodity — sugar is Java+Madura 33 of 33, soybeans 19 of
19, while cotton lint is the colony 37 vs 9 and `cacao, beans` is mixed within the single item.
There is no duplicate to find, no gap, no discontinuity: just one plausible number per cell.

WHAT THIS CHECKS. `verified_equal` is a specific claim — that the source's reporting territory IS
the candidate polity's territory, not merely the best row available. That claim cannot be true for a
label assembled from a whole plus its parts, or from several countries. Such verdicts should be
`best_available` at most.

The count is BASELINED rather than failed outright: these verdicts were made before the mapping was
tracked and were reasoning correctly from everything then visible. The ceiling stops the class
growing. BIDIRECTIONAL — downgrade one and this gate fails until the baseline is lowered.

Usage:
  python3 scripts/validate_iia_label_provenance.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROV = os.path.join(REPO, "pipelines/polity-autoimprove/state/iia_label_provenance.csv")
APPLIED = os.path.join(REPO, "pipelines/polity-autoimprove/state/verdicts_applied.jsonl")
LEDGER = os.path.join(REPO, "pipelines/polity-autoimprove/state/review_ledger.csv")

# Kinds where the layer-B label cannot be one territory.
MIXING = ("multi_country", "whole_with_sub_siblings")

# Measured 2026-08-18. ONE verdict: `french polynesia|iia|1909-1938` -> PYF-1800-2025, whose label
# reports `french oceania: makatea island` alone in 1909-1920 and the whole `french oceania` in
# 1930-1937 -- a phosphate island's output attributed to the territory for the early years.
#
# This count has moved SIX times and every wrong value printed as a clean pass or a plausible list:
#   14  trusting the applied record's own `quarantined` flag; a retraction sets the LEDGER to `issue`
#   12  joining on country NAME, missing 16 of 164 labels where the spec writes "Korea, Republic of"
#   13  counting the SPEC's merges, which flagged `jamaica` (86% `british jamaica` alone) for an
#       intent that never materialised in this data
#    1  counting observed merges, but judging a runner-up by its SHARE rather than by what it ADDS
#    3  judging by union gain, which correctly added `ghana`, `mozambique`, `serbia` and `austria`
#    2  `niger` retracted on the measurement rather than left grandfathered (the federation total
#       sat on Niger while all seven siblings resolved cleanly to their own labels)
#    1  distinguishing CONCURRENT sources from SEQUENTIAL ones. `serbia` is the Kingdom of Serbs,
#       Croats and Slovenes until 1929 and Yugoslavia after -- one state renamed, each era with one
#       territory -- so it is `sequential_rename` and this gate is not the right instrument for it.
#       Its actual problem is which polity it routes to (issues 315, 317). `french polynesia` stays,
#       because sequential there means a PART in some eras and the WHOLE in others.
BASELINE_VERIFIED_EQUAL_ON_MIXED = 1

# The eight the mapping itself declares as spanning several modern countries. Pinned by name so a
# change to the mapping surfaces here rather than silently shifting the count.
BASELINE_MULTI_COUNTRY = frozenset({
    "anglo-egyptian sudan",
    "austria-hungary",
    "british and french cameroon",
    "british west indies: leeward islands",
    "british west indies: windward islands",
    "french west africa",
    "japanese former oceania islands",
    "kingdom of serbs, croats and slovenes",
})


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def main() -> int:
    for path in (PROV, APPLIED):
        if not os.path.exists(path):
            print(f"SKIP: {os.path.relpath(path, REPO)} missing")
            return 0

    with open(PROV, encoding="utf-8") as fh:
        prov = list(csv.DictReader(fh))

    # THE LEDGER IS THE AUTHORITY ON WHAT IS STILL BANKED, not the applied record's own flag.
    # Retracting a verdict sets the ledger row to `issue` and writes the measurement into
    # quarantine.csv; the line already appended to verdicts_applied.jsonl is history and is never
    # rewritten. Reading only that flag counted two verdicts this session had already retracted
    # (united states of america|iia and viet nam|iia).
    retracted = set()
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (r.get("status") or "") == "issue":
                    retracted.add((r.get("key") or "").strip())

    # Join on the RESOLVED layer-B label, not on `assigned_modern`. The mapping uses long
    # official names and layer B uses short ones -- `south korea` vs "Korea, Republic of",
    # `turkey` vs "Türkiye", `dr congo`, `united kingdom` -- so a name join silently missed 16
    # of 164 labels, about 10%, and the miss looks exactly like a clean result. The derivation
    # resolves each row to its layer-B label once, via ISO3 where the names differ.
    # OBSERVED mixing, not merely specified. `territory_signal` is measured by value fingerprint
    # against the raw extract when it is available, and stored here so CI can use it without the
    # extract. Three values:
    #   mixed       two raw labels above the noise floor -> the label HAS no single territory
    #   redirected  one dominant raw label under a different name. Needs a human: `british ceylon`
    #               -> `sri lanka` is a legitimate rename, `yugoslavia` -> `serbia` is not
    #   clean       one dominant label, this label under a colonial qualifier
    #
    # Only `mixed` fails. Gating on the spec's `kind` instead was wrong in both directions: it
    # flagged `jamaica` (86% `british jamaica` alone) and `austria` and `niger`, and it flagged
    # them because the SPEC merges labels there, not because this data does.
    # `mixed` = two sources in the SAME years, so the label has no single territory at any moment.
    # `sequential_scope` = one source at a time, but a whole in some eras and a PART of it in
    # others -- `french polynesia` is one phosphate island 1909-1920 then the whole territory
    # 1930-1937 -- so the early years attribute a component's output to the parent. Both defeat an
    # equality claim.
    # `sequential_rename` does NOT: `serbia` is the Kingdom of Serbs, Croats and Slovenes and then
    # Yugoslavia, one state across a 1929 renaming, and each era genuinely has one territory. That
    # label's problem is which POLITY it routes to (issues 315, 317), which this gate is not about.
    FAILING = ("mixed", "sequential_scope")
    mixed_targets = {r["layer_b_label"] for r in prov
                     if r.get("territory_signal") in FAILING and r.get("layer_b_label")}
    declared_multi = {r["raw_label"] for r in prov if r["kind"] == "multi_country"}

    offenders = []
    with open(APPLIED, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            v = rec.get("verdict")
            if not isinstance(v, dict):
                continue
            key = v.get("key") or ""
            if "|iia|" not in key or rec.get("quarantined") or key in retracted:
                continue
            if v.get("confirm_kind") != "verified_equal":
                continue
            if norm(key.split("|")[0]) in mixed_targets:
                offenders.append((key, v.get("polity_code")))

    print(f"provenance rows: {len(prov)}")
    print(f"  targets assembled from a whole plus parts, or several countries: {len(mixed_targets)}")
    print(f"  labels the mapping's own notes call multi-country: {len(declared_multi)}")
    print(f"`verified_equal` verdicts on such a label: {len(offenders)} "
          f"(ceiling {BASELINE_VERIFIED_EQUAL_ON_MIXED})")

    problems = []
    if len(offenders) > BASELINE_VERIFIED_EQUAL_ON_MIXED:
        for key, code in sorted(offenders):
            print(f"   {key:40} -> {code}")
        problems.append(
            f"{len(offenders)} verdicts claim `verified_equal` on an IIA label that the "
            f"harmonisation mapping shows is assembled from a whole territory plus its parts (or "
            f"from several countries), above the ceiling of "
            f"{BASELINE_VERIFIED_EQUAL_ON_MIXED}. `verified_equal` asserts the source's territory "
            f"IS the polity's; such a label has no single territory, so the strongest honest "
            f"verdict is `best_available`"
        )
    elif len(offenders) < BASELINE_VERIFIED_EQUAL_ON_MIXED:
        problems.append(
            f"only {len(offenders)} `verified_equal` verdicts sit on a mixed label, below the "
            f"pinned ceiling of {BASELINE_VERIFIED_EQUAL_ON_MIXED} — lower the baseline and say "
            f"which verdicts were downgraded and on what evidence"
        )

    drift = declared_multi ^ BASELINE_MULTI_COUNTRY
    if drift:
        for label in sorted(drift):
            side = "no longer" if label in BASELINE_MULTI_COUNTRY else "newly"
            problems.append(
                f"`{label}` is {side} declared multi-country by the harmonisation mapping — the "
                f"mapping changed, so re-derive iia_label_provenance.csv and update the baseline"
            )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: no new equality claim rests on a label that mixes territories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
