#!/usr/bin/env python3
"""Ratchet the set of DATA-RECEIVING polity pages that are still CSV-derived stubs.

WHY THIS REPOSITORY OWES THE PROPERTY. The wiki is the database's source of truth AND the
evidence the verification pipeline reads when it judges whether a source's reporting
territory equals a candidate polity's territory. So a page that receives data but says
nothing about its territory is not merely undocumented: it is a place where verification
has nothing to lean on, and where an agent citing the page is citing an earlier agent's
hypothesis. Issue 19 is the standing statement of that problem -- 672 of 775 pages
(86.7% on 2026-08-17) are `status: draft`, most generated programmatically from CSV
metadata by `autonomous-38-bulk-remaining`.

Issue 19 cannot be closed in one pass, and it should not be gated as a whole either:
`draft` is a status about HUMAN review, and no check can promote a page. What CAN be
ratcheted is the much smaller set that actually carries risk -- pages that receive layer-B
data and are still stubs. Measured on main 2026-08-17: 45 of the 460 data-receiving pages,
holding 5,580 of 189,839 layer-B rows (2.94%). Fourteen were documented in the commit that
added this gate, leaving 31 pages / 1,005 rows (0.53%) baselined; the gate fails on a 32nd.

THE DEPTH SCREEN IS DELIBERATELY CRUDE, AND KNOWS IT. A page counts as a stub when it is
under 2,600 bytes AND carries zero `](../sources/...)` citations -- the same two numbers
`00_intake.py`'s `page_stats()` puts in every evidence bundle, and the threshold issue 19
itself used. Crude has a cost that must be stated rather than hidden: PYF-1800-2025 and
NCL-1800-2025 are in the baseline below yet are NOT empty stubs -- verification wrote real
territorial findings into them (Makatea's phosphate monopoly, New Caledonia's 1853
boundaries), citing external works such as the US Bureau of Mines *Minerals Yearbook*,
which are not registered under `wiki/sources/` and so count as zero citations. The baseline
comments mark which entries are true stubs and which are this false positive. Loosening the
screen to exempt them would also exempt every future page that gestures at a source without
registering it, which is the thing `validate_citations.py` exists to make impossible.

WHY THE ROW COUNT IS THE PRIORITISER. Issue 19 says to prioritise pages that actually
receive data, and `layerb_data_rows` in `pipelines/polity-autoimprove/state/territory_basis.csv`
is where that lives. That column is derived from the gitignored `state/matched_rows.parquet`,
which is STALE (issue 243: it undercounts SEN/LAO/TCD/CHL/LBY). Staleness here is permissive,
never strict -- an undercounted polity reads as 0 rows and is skipped -- so it can hide a
stub, but it can never invent one. A fresh parquet may therefore surface new unbaselined
stubs; that is the ratchet working, not a false alarm.

FAILS ON:
  - a data-receiving polity whose page is a stub and is not in the baseline
  - a baselined polity whose page is no longer a stub (delete the line -- the whole point
    is that this list shrinks, and a documented page left in it hides the next stub)
  - a baselined polity that no longer receives data, or whose page no longer exists

Usage:
  python3 scripts/validate_page_depth.py [--list]
Exit 1 on any of the above.
"""

import argparse
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIS = os.path.join(REPO, "pipelines/polity-autoimprove/state/territory_basis.csv")
PAGES = os.path.join(REPO, "wiki/polities")
BASELINE_PATH = os.path.join(REPO, "scripts/validate_page_depth_baseline.txt")

# From issue 19's own screen: "100 assertions rest on pages under 2.6 KB with zero
# citations". Kept identical so the gate measures the thing the issue named.
BYTE_FLOOR = 2600
CITE = re.compile(r"\]\(\.\./sources/")


def load_baseline() -> set:
    """Codes accepted as stubs today. Inline comments carry WHY, which is the useful
    part of the file, so they are stripped rather than treated as codes."""
    if not os.path.exists(BASELINE_PATH):
        return set()
    codes = set()
    with open(BASELINE_PATH, encoding="utf-8") as fh:
        for line in fh:
            text = line.split("#", 1)[0].strip()
            if text:
                codes.add(text)
    return codes


def page_depth(code: str):
    """(bytes, citations) for a polity's page, or None if it has no page.

    Mirrors `page_stats()` in pipelines/polity-autoimprove/00_intake.py on purpose: the
    gate must screen on the same numbers the verification agents are shown.
    """
    fp = os.path.join(PAGES, f"{code.lower()}.md")
    if not os.path.exists(fp):
        return None
    txt = open(fp, encoding="utf-8").read()
    return len(txt), len(CITE.findall(txt))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true",
                    help="print every stub with its row count, worst first")
    args = ap.parse_args()

    if not os.path.exists(BASIS):
        print(f"FAIL: {BASIS} not found (run pipelines/polity-autoimprove/04_territory_basis.py)")
        return 1

    with open(BASIS, encoding="utf-8") as fh:
        basis = list(csv.DictReader(fh))
    if not basis:
        print("FAIL: territory_basis.csv is empty")
        return 1

    baseline = load_baseline()
    receiving, stubs, missing_page = {}, {}, []
    for row in basis:
        code = (row.get("polity_code") or "").strip()
        try:
            rows_n = int((row.get("layerb_data_rows") or "0").strip() or 0)
        except ValueError:
            rows_n = 0
        if not code or rows_n <= 0:
            continue
        receiving[code] = rows_n
        depth = page_depth(code)
        if depth is None:
            # A data-receiving polity with no page at all. validate_references owns that
            # defect; reported here only so this gate is not silently skipping rows.
            missing_page.append(code)
            continue
        nbytes, ncites = depth
        if nbytes < BYTE_FLOOR and ncites == 0:
            stubs[code] = (rows_n, nbytes)

    total_rows = sum(receiving.values())
    stub_rows = sum(v[0] for v in stubs.values())
    print(f"{len(receiving)} data-receiving polities, {total_rows:,} layer-B rows")
    print(f"stubs (<{BYTE_FLOOR} bytes AND zero ../sources/ citations): "
          f"{len(stubs)} pages, {stub_rows:,} rows "
          f"({100.0 * stub_rows / total_rows:.2f}% of rows)")
    print(f"baseline: {len(baseline)} accepted")

    if args.list:
        for code, (rows_n, nbytes) in sorted(stubs.items(), key=lambda kv: -kv[1][0]):
            mark = " " if code in baseline else "N"
            print(f"  {mark} {code:16s} rows={rows_n:6d} {nbytes:5d}B")

    new = sorted(set(stubs) - baseline)
    print(f"\nUNBASELINED STUB PAGES: {len(new)}")
    for code in new:
        rows_n, nbytes = stubs[code]
        print(f"   FAIL {code:16s} {nbytes:5d} bytes, 0 citations, receives "
              f"{rows_n:,} layer-B rows -- document the page (see issue 19) or, if the "
              f"thinness is accepted for now, add it to "
              f"scripts/validate_page_depth_baseline.txt with a reason")

    graduated = sorted(c for c in baseline if c in receiving and c not in stubs)
    print(f"\nBASELINED PAGES THAT ARE NO LONGER STUBS: {len(graduated)}")
    for code in graduated:
        depth = page_depth(code)
        nbytes, ncites = depth if depth else (0, 0)
        print(f"   FAIL {code:16s} now {nbytes:5d} bytes, {ncites} citation(s) -- delete "
              f"its line from scripts/validate_page_depth_baseline.txt and say in the "
              f"commit what was documented")

    stale = sorted(c for c in baseline if c not in receiving)
    print(f"\nBASELINED PAGES THAT NO LONGER RECEIVE DATA: {len(stale)}")
    for code in stale:
        why = "page missing" if page_depth(code) is None else "0 layer-B rows"
        print(f"   FAIL {code:16s} {why} -- this gate no longer covers it; delete its "
              f"baseline line")

    if missing_page:
        print(f"\nnote: {len(missing_page)} data-receiving polity(ies) have no wiki page "
              f"at all: {', '.join(missing_page[:8])}")

    fail = bool(new or graduated or stale)
    print(f"\n{'FAIL' if fail else 'PASS'}: {len(new)} unbaselined stub(s), "
          f"{len(graduated)} graduated, {len(stale)} stale baseline entry(ies)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
