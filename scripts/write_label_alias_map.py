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
    "observed_rows",  # rows seen for this label: a count, 0 if measured and none,
    #                   EMPTY if this source's corpus is not in this repo (see below)
    "disposition",    # EMPTY means the source observed this territory in these years, which is
    #                   the ordinary case. `back_cast` means the source reports these years FOR
    #                   this territory while projecting a later boundary backwards, so the values
    #                   are a reconstruction: the data routes here, and the polity's own span
    #                   still begins when the territory did. Added 2026-09-22; the routing
    #                   verdict schema has always specified this behaviour and nothing could
    #                   express it, which left 377,822 panel rows resolving to no polity at all.
    #                   A consumer that wants observation only filters on this column.
    "indicator",      # EMPTY means the rule applies to every row of the label, the ordinary case.
    #                   A value limits it to rows whose panel `indicator` equals it exactly
    #                   (`area`, `production`, `yield`, `livestock_stock`, `landuse`). Added
    #                   2026-09-25 for a unit whose indicators are two territories: the panel's
    #                   CHL-LL reports crops for Los Lagos + Los Rios and landuse/livestock for
    #                   Los Lagos alone, under one id and one name. Same convention as the
    #                   `unit` / `indicator` scope of source_label_item_corrections.csv (#700):
    #                   blank = any. Appended LAST so a positional reader of the earlier shape
    #                   keeps its columns. A consumer that cannot supply a row's indicator must
    #                   not use a scoped rule, and must refuse (not guess) a label/year that
    #                   only scoped rules cover -- see the manifest's `label_alias_map`.
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
    target = (r.get("polity_code") or "").strip()
    if not target:
        # validate_aliases.py rejects these, so this should be unreachable; skip
        # rather than publish a row that resolves to nothing.
        continue
    rows.append(
        {
            "source_label": (r.get("source_label") or "").strip(),
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
            # and trade were routed to ROW-1850-2025 while each has its own live polity
            # that THIS map already targets for the same label. Two published contracts
            # disagreeing about where one territory's data belongs.
            #
            # With the count exposed, the consumer can fold only what genuinely has no
            # data, instead of guessing from a single domain's flag.
            # EMPTY IS PRESERVED, and is not the same fact as 0. This used to coerce
            # both to "0", which made the column say "no data row uses this alias"
            # about 393 aliases when only 29 had actually been measured at zero.
            #
            # The registry distinguishes three states and so must the contract:
            #   a number   measured, that many rows
            #   0          measured, genuinely none
            #   empty      NOT MEASURED here, because this source's corpus is not in
            #              this repository
            #
            # The third state is most of the non-FAOSTAT sources. All 138
            # lassaletta-grassland-share aliases, all 10 mueller-synthetic-n and all 4
            # crops-manure-n read empty, because those datasets live in the whep R
            # package and this repo never sees them. Measured over there, they are
            # anything but inert: 6,781 Lassaletta country-years resolve, 184
            # crops_manure_n codes, 156 Mueller codes. Publishing 0 for them invited
            # exactly the wrong conclusion, and an inert-alias check reading this
            # column would have flagged every one of them.
            "observed_rows": (r.get("observed_rows") or "").strip(),
            # Carried through verbatim. EMPTY means observed; `back_cast` means these years are
            # a reconstruction onto a boundary that did not exist yet. Publishing the registry's
            # value unchanged is the point: validate_aliases.py's before-target check reads it to
            # know that a range beginning before its target does so BY DESIGN, and a consumer
            # wanting observation only filters on it. Dropping it here would have left the
            # published map unable to distinguish the two, while the gate passed on the registry.
            "disposition": (r.get("disposition") or "").strip(),
            # Carried through verbatim, like `disposition`: a scope dropped here would publish
            # two rules for one label and years, and a consumer would pick one by file order.
            # A registry row written before the column existed has no field at all (None).
            "indicator": (r.get("indicator") or "").strip(),
        }
    )

# Sorted so the file is a stable diff and an entity's rules read in time order.
rows.sort(
    key=lambda r: (
        r["source_label"].lower(),
        r["source"],
        r["year_start"],
        r["indicator"],
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
# Atomic: a killed run must not leave a truncated contract behind for a consumer to embed.
tmp = f"{OUT}.{os.getpid()}.tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    fh.write(new)
os.replace(tmp, OUT)
print(
    f"wrote {os.path.relpath(OUT, REPO)}: {len(rows)} aliases over "
    f"{len(labels)} labels and {len(sources)} sources"
)
