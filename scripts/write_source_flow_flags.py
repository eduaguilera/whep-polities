#!/usr/bin/env python3
"""Publish the NON-PRODUCTION source flows as a consumer contract.

Why this file exists (issue 14). A source can record, under a territory's own label,
a quantity the territory did not produce. The case that forced it: the IIA reports
green coffee under `djibouti` (French Somaliland) at a median of 14,114 t/yr. French
Somaliland grows essentially no coffee — the beans are Ethiopian, moving through the
port on the Djibouti–Addis Ababa railway. The ROUTING is correct: the source did write
that label, and FRS-1884-1977 is the right polity for it. The defect is downstream —
summing the series beside Ethiopia's own production counts the same coffee twice.

The judgement was already made and written down, in prose, in
`pipelines/polity-autoimprove/state/source_conventions.csv` and on the polity's wiki
page. Prose is unreachable to an aggregation. This script republishes the machine-
readable part of it under `data/final/` so a consumer can EXCLUDE or REATTRIBUTE the
rows without reading a pipeline's working state or parsing a paragraph.

What is deliberately NOT here:
  * No year range. The convention is about a label/item pair, not a window: every year
    the IIA reports coffee under `djibouti` is transit, and a year bound would silently
    let new years in. Consumers filter on (source, label, item).
  * No re-attribution of the values. `origin_iso3` names the territory whose production
    these figures duplicate (ETH here), so a consumer can drop the rows or fold them
    into that territory's series — but this repository does not decide which, because
    the transit volume is not the origin's output (it is exports, one of several
    outlets) and choosing would invent a number.
  * Only non-production rows are emitted. `flow_type == production` is the default for
    every other convention in the state file — those rows are territorial-SCOPE notes
    (whose land a label covers), a different question — and publishing them would make
    the file read as a census of what IS production, which it is not.

WHY THE FILE IS SHORT, AND WHY IT CANNOT BE AUTO-POPULATED (measured 2026-08-17).
It carries one row. That is a census problem, not a mechanism problem, and the obvious
mechanical route to filling it is REFUTED: ranking coffee tonnage by the receiving
polity's own area does not separate an entrepôt from a small intensive producer.
`05_magnitude_screen.py` puts Djibouti's `iia` green coffee at 47.1x the cross-polity
median intensity — genuinely extreme — and yet only **16th of the 52** coffee
(item, polity, source) combinations above the 8x threshold, behind Cape Verde (291x),
El Salvador (188x), Puerto Rico, Haiti and Guadeloupe, all of which really do grow
coffee on very little land. Intensity is necessary, not sufficient; each case needs the
domain judgement (a port, little arable land, and a producing neighbour whose series the
figures duplicate).

Two candidates issue 14 raised were screened on that judgement and CLEARED — recorded
here because a rejected candidate is as useful as an accepted one:
  * MKY-1918-1962 (Mocha is a port as well as a producing region): 2.6x intensity, and
    FAO 1952 independently estimates 6.0-6.6 kt of Yemeni production for 1949-1951,
    continuing the IIA level. Ethiopia's own output is 2-3x larger and separately
    recorded, so there is no origin series being duplicated.
  * PAN-1903-1979 (Canal Zone transit): 0.97x intensity — the coffee norm — and both
    `iia` and `juan` report a coffee PLANTED AREA of 1,000-3,000 ha beside the 1,000 t
    median, which transit tonnage cannot have.
Reasoning and figures on wiki/polities/mky-1918-1962.md and pan-1903-1979.md.

WHO CONSUMES THIS FILE. `pipelines/polity-autoimprove/05_magnitude_screen.py` joins it
onto its outlier table on (source, polity, item), so an already-adjudicated flow is
marked SETTLED instead of being re-investigated, and a flagged flow the screen does NOT
rank is printed as such. No aggregation in this repository excludes flagged rows, and the
downstream R package does not read the file yet: whether WHEP should subtract entrepôt
flows or carry them as a separate flow class is an accounting decision this repository
cannot make for it (issue 14 remains open on that half).

Usage:
  python3 scripts/write_source_flow_flags.py [--check]

`--check` verifies the committed file matches the pipeline state without writing,
exiting 1 on drift, for CI.
"""
import argparse
import csv
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(
    REPO, "pipelines/polity-autoimprove/state/source_conventions.csv"
)
ALIAS = os.path.join(REPO, "data/final/label_alias_map.csv")
WIKI = os.path.join(REPO, "wiki/polities")
OUT = os.path.join(REPO, "data/final/source_flow_flags.csv")

# The value that means "this is the territory's own output". Anything else is a flow the
# territory handled but did not grow or mine, and lands in the published file.
PRODUCTION = "production"

COLUMNS = (
    "source",           # data source whose rows this applies to (iia, fao1952, ...)
    "label_pattern",    # the source's own country label, or * for every label
    "item_pattern",     # the source's own item label, or * for every item
    "flow_type",        # what the figures actually measure (e.g. entrepot_transit)
    "polity_code",      # polity the label resolves to, from label_alias_map; ; -separated
    "origin_iso3",      # territory whose production these figures duplicate, if known
    "wiki_page",        # the page carrying the full reasoning
    "verified",         # date the convention was verified
)


def resolve_polities(source: str, label: str) -> str:
    """Which polity the flagged label resolves to, read from the PUBLISHED alias map.

    Resolved here rather than recorded by hand in the state file so the two cannot drift:
    a re-span or a re-route of the label moves this column with it. A `*` label pattern
    resolves to nothing on purpose — it means "every label from this source", which is not
    one polity and must not be made to look like one.
    """
    if label == "*" or not os.path.exists(ALIAS):
        return ""
    # A BLANK `source` IS A WILDCARD, NOT AN ABSENCE — such an alias routes its label from ANY
    # source, which is how the matchers apply it. `validate_composition_sums.py` already carries
    # this comment because skipping those rows made that check wrong; this function had the same
    # bug. 188 of the 995 published alias rows (19%), covering 79 distinct labels, have a blank
    # source, and every one of them resolved to nothing here.
    #
    # The consequence was a published flag with an EMPTY polity_code, which
    # 05_magnitude_screen.py joins on and so could never match — an inert row in a published file.
    # Found while trying to publish the iia/australia Christmas Island phosphate flag (issue 372),
    # which I wrongly diagnosed in issue 412 as "australia has no alias row": it has two, both
    # source-agnostic.
    hits = set()
    with open(ALIAS, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            row_src = (row.get("source") or "").strip()
            if row_src and row_src != source:
                continue
            if (row.get("source_label") or "").lower() != label.lower():
                continue
            if row.get("polity_code"):
                hits.add(row["polity_code"])
    return ";".join(sorted(hits))


def wiki_page_for(codes: str) -> str:
    """The page a maintainer should read, but only when it exists and is unambiguous."""
    parts = [c for c in codes.split(";") if c]
    if len(parts) != 1:
        return ""
    rel = f"wiki/polities/{parts[0].lower()}.md"
    return rel if os.path.exists(os.path.join(REPO, rel)) else ""


def build() -> str:
    with open(STATE, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        rows = list(reader)
    # Asserted, not assumed. Reading flow_type with a default would turn a RENAMED or
    # dropped column into "everything is production", which publishes an EMPTY file and
    # exits 0 — the failure this whole file exists to prevent, arriving silently.
    missing = [c for c in ("flow_type", "origin_iso3") if c not in fields]
    if missing:
        raise SystemExit(
            f"FAIL — {os.path.relpath(STATE, REPO)} has no {missing} column(s), so no "
            f"flow can be recorded as non-production. Restore the column(s); do not let "
            f"this script default them, or a known double count publishes as an empty file."
        )
    out = []
    for r in rows:
        flow = (r.get("flow_type") or PRODUCTION).strip()
        if flow == PRODUCTION:
            continue
        codes = resolve_polities(r["source"], r["label_pattern"])
        out.append(
            {
                "source": r["source"],
                "label_pattern": r["label_pattern"],
                "item_pattern": r["item_pattern"],
                "flow_type": flow,
                "polity_code": codes,
                "origin_iso3": (r.get("origin_iso3") or "").strip(),
                "wiki_page": wiki_page_for(codes),
                "verified": r.get("verified", ""),
            }
        )
    out.sort(key=lambda r: (r["source"], r["label_pattern"], r["item_pattern"]))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(COLUMNS), lineterminator="\n")
    w.writeheader()
    w.writerows(out)
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed file is stale, do not write")
    args = ap.parse_args()

    text = build()
    n = text.count("\n") - 1
    if args.check:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            # Name the rows, not just the file. "stale" alone sends a maintainer to diff two
            # CSVs by hand; the useful fact is WHICH (source, label, item) gained or lost its
            # flag, because a flag that disappeared is a double count that came back.
            def keyed(blob):
                return {
                    "|".join((r["source"], r["label_pattern"], r["item_pattern"])): r
                    for r in csv.DictReader(io.StringIO(blob))
                } if blob else {}

            have, want = keyed(current), keyed(text)
            gone = sorted(set(have) - set(want))
            new_rows = sorted(set(want) - set(have))
            changed = sorted(
                k for k in set(have) & set(want) if have[k] != want[k]
            )
            print(
                "FAIL — data/final/source_flow_flags.csv is stale: it does not match "
                "pipelines/polity-autoimprove/state/source_conventions.csv. A "
                "non-production flow recorded in state but not published is a flow no "
                "aggregation can exclude."
            )
            for label, keys in (
                ("only in the published file", gone),
                ("only in state", new_rows),
                ("differing", changed),
            ):
                for k in keys:
                    print(f"  {label}: {k}")
            print(
                "Rerun `python3 scripts/write_source_flow_flags.py` and commit data/final/."
            )
            return 1
        print(f"OK — source_flow_flags.csv matches state ({n} non-production flow(s))")
        return 0
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print(f"wrote {OUT} ({n} non-production flow(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
