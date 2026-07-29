#!/usr/bin/env python3
"""Publish the source-label -> polity alias map as a consumer contract.

Why: a consumer that holds data labelled "Cape Verde", "Swaziland" or "ZAR" needs
to know which polity that label means, and in which years. This repository already
resolves that — it is the whole point of the alias registry — but the registry
lives in `pipelines/polity-autoimprove/state/`, which is working state: its columns
serve the matcher, it carries multi-line `basis` prose, and nothing promises its
shape from one run to the next.

The alternative is each consumer building its own label lookup, which is how the
FAOSTAT area mapping ended up with two authorities and 118 area-years attributed
to polities that did not exist (eduaguilera/whep#387). So the resolved mapping is
republished here with a stable, documented column set.

`basis` is deliberately excluded. It is the matcher's audit trail — often several
sentences, with commas and quotes — and a consumer needs the answer, not the
argument. It stays in the registry for review.

Every published row is checked by scripts/validate_aliases.py first, so a
consumer can rely on `polity_code` naming a live polity.

Usage:
  python3 scripts/write_label_alias_map.py [--check]

`--check` verifies the committed map matches the registry without writing,
exiting 1 on drift, for CI.
"""
import argparse
import csv
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(
    REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv"
)
OUT = os.path.join(REPO, "data/final/label_alias_map.csv")

COLUMNS = (
    "source_label",   # the label as the source writes it, verbatim
    "source",         # which source it came from; empty means any source
    "year_start",     # first year the alias applies (inclusive); empty means any
    "year_end",       # last year (inclusive); empty means any
    "polity_code",    # the polity the label resolves to
    "common_name",    # a human-readable name for that polity
    "confidence",     # matcher confidence in the assignment
    "observed_rows",  # source rows seen for this label, 0 when only mappable
)

ap = argparse.ArgumentParser()
ap.add_argument(
    "--check",
    action="store_true",
    help="verify the committed map matches the registry; exit 1 on drift",
)
A = ap.parse_args()

if not os.path.exists(REGISTRY):
    print(f"alias registry not found: {REGISTRY}", file=sys.stderr)
    sys.exit(2)

rows = []
for r in csv.DictReader(open(REGISTRY, encoding="utf-8")):
    target = (r.get("target_polity_code") or "").strip()
    if not target:
        # validate_aliases.py rejects these, so this should be unreachable; skip
        # rather than publish a row that resolves to nothing.
        continue
    rows.append(
        {
            "source_label": (r.get("original_name") or "").strip(),
            "source": (r.get("source") or "").strip(),
            "year_start": (r.get("year_start") or "").strip(),
            "year_end": (r.get("year_end") or "").strip(),
            "polity_code": target,
            "common_name": (r.get("common_name") or "").strip(),
            "confidence": (r.get("confidence") or "").strip(),
            # How many source rows were actually OBSERVED for this label. Published
            # because a consumer cannot otherwise tell "this label carries data" from
            # "this label is merely mappable", and those need different treatment.
            #
            # Concretely: eduaguilera/whep folds FABIO rest-of-world areas into a ROW
            # polity, excluding only areas flagged with their own commodity balances.
            # That excluded too little. Eleven folded areas carry substantial data in
            # OTHER domains — Bermuda 67,310 rows, Faroe Islands 45,036, Cook Islands
            # 42,137, Palestine 32,534, Equatorial Guinea 23,719 — so their production
            # and trade were routed to ROW-1850-2023 while each has its own live polity
            # that THIS map already targets for the same label. Two published contracts
            # disagreeing about where one territory's data belongs.
            #
            # With the count exposed, the consumer can fold only what genuinely has no
            # data, instead of guessing from a single domain's flag.
            "observed_rows": (r.get("rows") or "0").strip() or "0",
        }
    )

# Sorted so the file is a stable diff and an entity's rules read in time order.
rows.sort(
    key=lambda r: (
        r["source_label"].lower(),
        r["source"],
        r["year_start"],
        r["polity_code"],
    )
)

sio = io.StringIO()
w = csv.DictWriter(sio, fieldnames=list(COLUMNS), lineterminator="\n")
w.writeheader()
for r in rows:
    w.writerow(r)
new = sio.getvalue()

labels = {r["source_label"] for r in rows}
sources = {r["source"] for r in rows if r["source"]}

if A.check:
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if old == new:
        print(
            f"--check: PASS — label_alias_map.csv matches the registry "
            f"({len(rows)} aliases, {len(labels)} labels, {len(sources)} sources)"
        )
        sys.exit(0)
    print("--check: FAIL — data/final/label_alias_map.csv is stale")
    old_lines, new_lines = old.splitlines(), new.splitlines()
    if len(old_lines) != len(new_lines):
        print(
            f"  committed map has {max(len(old_lines) - 1, 0)} aliases; "
            f"the registry yields {len(rows)}"
        )
    else:
        print(f"  same number of aliases ({len(rows)}), but the content differs")
        for k, (o, n) in enumerate(zip(old_lines, new_lines)):
            if o != n:
                print(f"  first difference on line {k + 1}:")
                print(f"    committed: {o}")
                print(f"    expected:  {n}")
                break
    print("\n  Fix: run scripts/write_label_alias_map.py and commit data/final/.")
    sys.exit(1)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(new)
print(
    f"wrote {os.path.relpath(OUT, REPO)}: {len(rows)} aliases over "
    f"{len(labels)} labels and {len(sources)} sources"
)
