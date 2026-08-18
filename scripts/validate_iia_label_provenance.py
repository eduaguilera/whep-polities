#!/usr/bin/env python3
"""Can a verdict claim the source territory EQUALS the polity's, when the label mixes territories?

WHAT THIS RECORDS. `state/iia_label_provenance.csv` is derived from an IIA harmonisation mapping
(`harmonization_geography.xlsx`, sheet `iia harmonization`): 335 labels collapsed onto 173 modern
countries.

READ THE PROVENANCE OF THE PROVENANCE FILE BEFORE TRUSTING IT. That mapping is a DIFFERENT VINTAGE
from the raw extract the pipeline actually carries: only **109 of its 334 labels** appear verbatim in
`harmonized_data.xlsx`. It says `algeria` and `angola` where the data says `french algeria` and
`portuguese angola`, and `dutch east indies: java and madura` where the data says
`dutch java and madura`. Five of its eight declared multi-country labels — `anglo-egyptian sudan`
among them — do not occur in the data at all, which is why that entry has zero rows behind it.

So this file is a statement of HARMONISATION INTENT, not a transcript of what happened to these
rows. It is a risk flag: a target the spec assembles from a whole plus its parts is one where a
territorial merge is likely, and worth refusing an equality claim on. It is NOT proof that any
particular row was merged. The direct evidence for that is value-fingerprint matching against the
raw extract — `15_label_provenance.py` — and the two are complementary: `czech republic` is flagged
here, yet fingerprints show 92.5% from `czechoslovakia` alone with no sub-label above the noise
floor, so the risk did not materialise there.

The three declared multi-country labels that DO occur in the data are all confirmed by direct
measurement, which is what makes the flag worth keeping:

    layer B `serbia`    24% of its values match raw `kingdom of serbs, croats and slovenes`
    layer B `niger`     31% match raw `french west africa` (a federation of eight territories)
    layer B `austria`   12% match raw `austria-hungary`

The findings that motivated this gate — `serbia` being Yugoslavia, `viet nam` being Tonkin,
`indonesia` mixing a colony with a 7% subset — were all measured directly against the raw extract and
do not depend on this mapping being the right vintage.

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

# Measured 2026-08-18, after excluding the two retracted this same day. These verdicts were made
# before the mapping was tracked, from evidence that was self-consistent at the time.
#
# It was 14 counting only the applied record's own `quarantined` flag, which was WRONG: retracting a
# verdict sets the ledger row to `issue`, and the appended jsonl line is history that is never
# rewritten. Reading the ledger too drops `united states of america|iia|1909-1945` and
# `viet nam|iia|1930-1944`, both retracted in this session on raw-source measurements.
#
# Then 12 -> 13 when the join moved from `assigned_modern` to the resolved layer-B label, which
# added `czech republic|iia|1919-1937`. Both corrections moved the number, in opposite directions,
# and neither was visible in the output: an unjoined label and a stale flag both read as clean.
BASELINE_VERIFIED_EQUAL_ON_MIXED = 13

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
    mixed_targets = {r["layer_b_label"] for r in prov
                     if r["kind"] in MIXING and r.get("layer_b_label")}
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
