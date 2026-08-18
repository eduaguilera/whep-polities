#!/usr/bin/env python3
"""Reconcile the wiki findings queues against current state — keep them actionable queues.

`apply_verdicts.py` APPENDS to `state/suspect_wiki_pages.csv` (a verifier judged a page wrong or
too thin) and `state/wiki_notes_queue.csv` (a verifier has something to add to a page). Nothing
ever clears them, so an entry survives the fixing of the very page it describes. This is the
clearing pass, and it is the same shape as `reconcile_quarantine.py`.

MEASURED WHEN THIS WAS WRITTEN (2026-08-18), and this is why it exists:

  * `BRA-1800-2025` was flagged `wrong` on 2026-07-27 for naming a successor `BRA-1903-1909` that
    did not exist. It exists now — the split was made afterwards — and the row itself is
    `superseded`. The finding describes a state of the world that is three weeks gone.
  * `JAM-1800-2025` was flagged `wrong` the same day for claiming it covered only "to 1886" and
    naming a nonexistent `JAM-1886-1962`. The page now says "Single row … 1800 to 2025", "No
    successor row", and explicitly records that "a split at 1886 was once planned and never
    applied". Also already fixed.
  * `PYF-1800-2025` and `FRS-1884-1977` each appear TWICE with the same finding, because two
    assertions on the same page each queued it.

Anyone working this queue top-down would have re-fixed two already-correct pages before reaching
anything real. That is the fourth instance in this pipeline of one pattern — state keyed by polity
code, written before a change, never re-derived — after `matched_rows.parquet` (issue 243), the
deployed pre-1961 site (#300) and `review_ledger.csv` (#304).

WHAT IS DROPPED, and it is deliberately only the mechanical part:

  dead_code   the polity no longer exists. A finding about a page for a code that is gone cannot
              be acted on.
  not_live    the polity is `retired` or `superseded`. Its page documents a row that can never
              receive data again, so a thinness or accuracy complaint about it is not work.
  duplicate   an identical (polity_code, finding, what_looks_wrong) already kept. Several
              assertions routing to one page each queue the same complaint.

WHAT IS NOT DROPPED. Whether a `wrong` finding still holds, or whether an `inadequate` page has
since become adequate, is a JUDGEMENT about prose and this script does not make it. Instead every
kept row is reported with its page's current measurable state — bytes, source citations, whether it
carries a dated correction note — so triage is possible without opening 30 files. A 716-byte page
with no citations is still thin; a 13,000-byte page with eight citations flagged `inadequate` three
weeks ago probably is not.

Every dropped row is appended to `state/wiki_findings_resolved.csv` with its reason and the date,
and printed — never silently discarded.

Usage:
  python3 pipelines/polity-autoimprove/reconcile_wiki_queues.py --dry-run
  python3 pipelines/polity-autoimprove/reconcile_wiki_queues.py
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
DB = os.path.join(REPO, "data/final/polities_database.csv")
PAGES = os.path.join(REPO, "wiki/polities")
RESOLVED = os.path.join(STATE, "wiki_findings_resolved.csv")
NOT_LIVE = ("retired", "superseded")

# Dedup keys. For suspect pages this is (page, finding) and NOT the finding text: four separate
# assertions each flagged DZA-1919-1962 `inadequate` in four different wordings, which is four rows
# and one unit of work. Collapsing on the text left all four in place. The row with the LONGEST text
# is kept as the most informative, and the others go to the resolved log rather than being discarded,
# so the alternative wordings survive.
QUEUES = (
    ("suspect_wiki_pages.csv", ("polity_code", "finding"), "what_looks_wrong"),
    ("wiki_notes_queue.csv", ("polity_code",), "note"),
)


def page_stats(code: str) -> tuple[int, int, bool]:
    """Bytes, source-citation count, and whether the page carries a dated note."""
    path = os.path.join(PAGES, f"{code.lower()}.md")
    if not os.path.exists(path):
        return (0, 0, False)
    txt = open(path, encoding="utf-8").read()
    cites = len(re.findall(r"\.\./sources/", txt))
    dated = bool(re.search(r"\b20\d\d-\d\d-\d\d\b", txt))
    return (len(txt), cites, dated)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report without rewriting anything")
    ap.add_argument("--date", default="", help="date to stamp on resolved rows (default: today UTC)")
    args = ap.parse_args()

    if not os.path.exists(DB):
        print(f"SKIP: {os.path.relpath(DB, REPO)} missing")
        return 0
    with open(DB, encoding="utf-8") as fh:
        db = {r["polity_code"]: (r.get("wiki_status") or "").strip()
              for r in csv.DictReader(fh)}

    stamp = args.date
    if not stamp:
        import datetime
        # UTC, not local: a Madrid-local date has been rejected by a CI gate before.
        stamp = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    dropped_all = []
    for name, dedup_on, text_col in QUEUES:
        path = os.path.join(STATE, name)
        if not os.path.exists(path):
            print(f"SKIP: {name} missing")
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
            fields = list(rows[0]) if rows else []
        if not rows:
            print(f"{name}: empty")
            continue

        # Longest text first, so the row kept for each (page, finding) is the most informative one.
        ordered = sorted(rows, key=lambda r: -len(r.get(text_col) or ""))
        keep, seen = [], set()
        for r in ordered:
            code = (r.get("polity_code") or "").strip()
            sig = tuple((r.get(k) or "") for k in dedup_on)
            if code and code not in db:
                r["_why"] = "dead_code"
            elif code and db.get(code) in NOT_LIVE:
                r["_why"] = f"not_live ({db[code]})"
            elif sig in seen:
                r["_why"] = "duplicate_finding"
            else:
                seen.add(sig)
                keep.append(r)
                continue
            dropped_all.append((name, r))
        # Restore the file's original order among the rows that survive.
        order = {id(r): i for i, r in enumerate(rows)}
        keep.sort(key=lambda r: order.get(id(r), 0))

        print(f"\n{name}: {len(rows)} rows -> {len(keep)} kept, {len(rows) - len(keep)} resolved")
        for r in [x for n, x in dropped_all if n == name]:
            print(f"   DROP {r.get('polity_code',''):16} {r['_why']}")

        if keep and name == "suspect_wiki_pages.csv":
            print("   kept, with each page's current measurable state:")
            for r in sorted(keep, key=lambda x: (x.get("finding", ""), x.get("polity_code", ""))):
                b, c, dated = page_stats(r.get("polity_code", ""))
                print(f"     {r.get('finding',''):10} {r.get('polity_code',''):16} "
                      f"{b:>6}B  {c} citation(s)  dated_note={dated}")

        if not args.dry_run:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                w.writerows([{k: v for k, v in r.items() if k in fields} for r in keep])

    if dropped_all and not args.dry_run:
        exists = os.path.exists(RESOLVED)
        cols = ["queue", "polity_code", "reason", "resolved_on", "detail"]
        with open(RESOLVED, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            if not exists:
                w.writeheader()
            for name, r in dropped_all:
                w.writerow({"queue": name, "polity_code": r.get("polity_code", ""),
                            "reason": r["_why"], "resolved_on": stamp,
                            "detail": (r.get("what_looks_wrong") or r.get("note") or "")[:300]})
        print(f"\nappended {len(dropped_all)} resolved row(s) to "
              f"{os.path.relpath(RESOLVED, REPO)}")
    elif dropped_all:
        print(f"\n--dry-run: {len(dropped_all)} row(s) would be resolved")
    else:
        print("\nnothing to resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
