#!/usr/bin/env python3
"""Do the five adjudication queues still say something true about the database?

WHY THIS EXISTS (issue 633). `validate_atomic_state_writes.py` names ten state files as holding
UNREGENERABLE adjudications -- what the repo itself says it cannot afford to lose -- but it checks
how they are WRITTEN, not what they CONTAIN. Five of the ten had no gate reading their content:

    quarantine.csv           verdicts two agents disagreed on, kept actionable
    quarantine_resolved.csv  append-only audit trail of cleared quarantine rows
    suspect_wiki_pages.csv   pages verification judged wrong or too thin
    wiki_notes_queue.csv     notes a verifier wants added to a page (legitimately empty when drained)
    wiki_findings_resolved.csv  archive of cleared wiki-queue rows

Measured clean when this was written, so this pins an invariant rather than reporting a defect. The
class is one the repo has paid for before: state keyed by polity code, written before a rename,
never re-derived (#17, #244, matched_rows.parquet, the review ledger). A code in a queue that the
database no longer holds is a statement about nothing.

Five arms, all reading only tracked files, so they run in CI:
  A. SCHEMA     the header is exactly the writer's field list (a dropped or renamed column makes
                every reader silently see an empty string), every row has that many cells.
  B. KEYS       quarantine keys are `label|source|first-last`, unique within a file.
  C. CODES      every polity code a queue names is in polities_database.csv -- quarantine
                `candidate`, `polity_code`, `review_polity_code`, resolved `current_candidate`.
                The wiki queues must name a LIVE polity with a page on disk: reconcile_wiki_queues.py
                drops dead/retired/superseded codes, so one surviving here is a finding about a page
                that can no longer be acted on. The resolved archive may name retired codes (that is
                what `not_live` rows are) but never a code absent from the database.
  D. VOCABULARY verdict / confidence / resolution / finding / queue values are in the closed sets
                the writers emit; a typo drops the row out of whichever filter reads it.
  E. DATES      every date is ISO and not in the future (UTC -- a local date after 22:00 UTC+2 has
                read as "in the future" to CI before); resolved_date is not before date.
  F. RESOLUTION a resolved `route_changed` row names a current_candidate DIFFERENT from the
                candidate it says no longer applies.

Usage:
  python3 scripts/validate_adjudication_queues.py
"""
from __future__ import annotations

import csv
import datetime
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
DB = os.path.join(REPO, "data/final/polities_database.csv")
PAGES = os.path.join(REPO, "wiki/polities")
DEAD = ("retired", "superseded")

# Restated, not imported: a gate that imports the names it checks agrees by construction.
QUAR = ["key", "candidate", "verdict", "polity_code", "confidence", "basis",
        "review_verdict", "review_polity_code", "review_basis", "review_proposal",
        "review_reason", "date"]
QUAR_RES = QUAR + ["resolution", "resolution_reason", "current_candidate", "resolved_by",
                   "resolved_date"]
SUSPECT = ["polity_code", "wiki_status", "finding", "assertion_key", "what_looks_wrong",
           "evidence_used", "date"]
NOTES = ["polity_code", "assertion_key", "note", "date"]
FINDINGS = ["queue", "polity_code", "reason", "resolved_on", "detail"]

VERDICTS = frozenset({"confirm", "reroute", "split_reroute", "uncertain", "new_polity",
                      "not_a_polity"})
CONFIDENCE = frozenset({"high", "medium", "low"})
RESOLUTIONS = frozenset({"route_changed", "banked"})
FINDING = frozenset({"inadequate", "wrong"})
# Both spellings are in the committed archive (with and without the extension).
QUEUES = frozenset({"suspect_wiki_pages", "suspect_wiki_pages.csv",
                    "wiki_notes_queue", "wiki_notes_queue.csv"})
KEY_RE = re.compile(r".+\|[a-z0-9_]+\|\d{4}-\d{4}")


def read(name, fields, problems):
    path = os.path.join(STATE, name)
    if not os.path.exists(path):
        problems.append(f"{name}: file missing (tracked state, so this is a deletion)")
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.reader(fh)
        rows = list(rd)
    if not rows or rows[0] != fields:
        problems.append(f"{name}: header {rows[0] if rows else None} is not the writer's field "
                        f"list {fields}")
        return []
    out = []
    for i, r in enumerate(rows[1:], start=2):
        if not r:
            continue
        if len(r) != len(fields):
            problems.append(f"{name}:{i}: {len(r)} cells, header has {len(fields)}")
            continue
        out.append(dict(zip(fields, r)))
    return out


def check():
    problems = []
    if not os.path.exists(DB):
        print(f"SKIP: {os.path.relpath(DB, REPO)} missing")
        return problems
    with open(DB, encoding="utf-8", newline="") as fh:
        db = {r["polity_code"]: (r.get("wiki_status") or "").strip() for r in csv.DictReader(fh)}
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    def date_ok(name, i, col, v, required=True):
        if not v:
            if required:
                problems.append(f"{name} row {i}: empty {col}")
            return
        try:
            datetime.date.fromisoformat(v)
        except ValueError:
            problems.append(f"{name} row {i}: {col} {v!r} is not an ISO date")
            return
        if v > today:
            problems.append(f"{name} row {i}: {col} {v} is in the future (UTC today is {today})")

    def known(name, i, col, v, required=False):
        if not v:
            if required:
                problems.append(f"{name} row {i}: empty {col}")
        elif v not in db:
            problems.append(f"{name} row {i}: {col} {v!r} is not in polities_database.csv")

    def live_with_page(name, i, v):
        if v not in db:
            problems.append(f"{name} row {i}: polity_code {v!r} is not in polities_database.csv")
            return
        if db[v] in DEAD:
            problems.append(f"{name} row {i}: polity_code {v} is {db[v]}; "
                            f"reconcile_wiki_queues.py drops such rows, so this finding is about a "
                            f"page that can no longer be acted on")
        if not os.path.exists(os.path.join(PAGES, f"{v.lower()}.md")):
            problems.append(f"{name} row {i}: polity_code {v} has no wiki page on disk")

    # --- quarantine.csv and its archive
    for name, fields in (("quarantine.csv", QUAR), ("quarantine_resolved.csv", QUAR_RES)):
        rows = read(name, fields, problems)
        seen = set()
        for i, r in enumerate(rows, start=2):
            if not KEY_RE.fullmatch(r["key"]):
                problems.append(f"{name} row {i}: key {r['key']!r} is not label|source|first-last")
            ident = (r["key"], r.get("resolved_date", ""), r["candidate"])
            if name == "quarantine.csv" and r["key"] in seen:
                problems.append(f"{name} row {i}: duplicate key {r['key']!r}")
            elif name != "quarantine.csv" and ident in seen:
                problems.append(f"{name} row {i}: duplicate archived row {r['key']!r}")
            seen.add(r["key"] if name == "quarantine.csv" else ident)
            known(name, i, "candidate", r["candidate"], required=True)
            known(name, i, "polity_code", r["polity_code"])
            known(name, i, "review_polity_code", r["review_polity_code"])
            if r["verdict"] not in VERDICTS:
                problems.append(f"{name} row {i}: verdict {r['verdict']!r} is not one of "
                                f"{sorted(VERDICTS)}")
            if r["review_verdict"] and r["review_verdict"] not in VERDICTS:
                problems.append(f"{name} row {i}: review_verdict {r['review_verdict']!r} is not "
                                f"one of {sorted(VERDICTS)}")
            if r["confidence"] not in CONFIDENCE:
                problems.append(f"{name} row {i}: confidence {r['confidence']!r} is not one of "
                                f"{sorted(CONFIDENCE)}")
            date_ok(name, i, "date", r["date"], required=False)
            if name == "quarantine_resolved.csv":
                known(name, i, "current_candidate", r["current_candidate"], required=True)
                if r["resolution"] not in RESOLUTIONS:
                    problems.append(f"{name} row {i}: resolution {r['resolution']!r} is not one "
                                    f"of {sorted(RESOLUTIONS)}")
                if r["resolution"] == "route_changed" and r["current_candidate"] == r["candidate"]:
                    problems.append(f"{name} row {i}: route_changed but current_candidate equals "
                                    f"the candidate {r['candidate']} it says no longer applies")
                if not r["resolution_reason"].strip() or not r["resolved_by"].strip():
                    problems.append(f"{name} row {i}: blank resolution_reason/resolved_by -- an "
                                    f"archived row must say why and who")
                date_ok(name, i, "resolved_date", r["resolved_date"])
                if r["date"] and r["resolved_date"] and r["resolved_date"] < r["date"]:
                    problems.append(f"{name} row {i}: resolved_date {r['resolved_date']} is "
                                    f"before date {r['date']}")

    # --- the two wiki queues
    for name, fields in (("suspect_wiki_pages.csv", SUSPECT), ("wiki_notes_queue.csv", NOTES)):
        for i, r in enumerate(read(name, fields, problems), start=2):
            live_with_page(name, i, r["polity_code"])
            date_ok(name, i, "date", r["date"])
            if name == "suspect_wiki_pages.csv":
                if r["finding"] not in FINDING:
                    problems.append(f"{name} row {i}: finding {r['finding']!r} is not one of "
                                    f"{sorted(FINDING)}")
                if not r["what_looks_wrong"].strip():
                    problems.append(f"{name} row {i}: empty what_looks_wrong")
            elif not r["note"].strip():
                problems.append(f"{name} row {i}: empty note")

    # --- the resolved archive for the wiki queues
    name = "wiki_findings_resolved.csv"
    for i, r in enumerate(read(name, FINDINGS, problems), start=2):
        if r["queue"] not in QUEUES:
            problems.append(f"{name} row {i}: queue {r['queue']!r} is not one of {sorted(QUEUES)}")
        if r["polity_code"] not in db:
            problems.append(f"{name} row {i}: polity_code {r['polity_code']!r} is not in "
                            f"polities_database.csv")
        elif not os.path.exists(os.path.join(PAGES, f"{r['polity_code'].lower()}.md")):
            problems.append(f"{name} row {i}: polity_code {r['polity_code']} has no wiki page")
        if not r["reason"].strip():
            problems.append(f"{name} row {i}: empty reason -- an archived row must say why")
        date_ok(name, i, "resolved_on", r["resolved_on"])
    return problems


def main():
    problems = check()
    if problems:
        print(f"FAIL: {len(problems)} problem(s) in the adjudication queues\n")
        for p in problems[:60]:
            print(f"  {p}")
        return 1
    print("PASS: quarantine, quarantine_resolved, suspect_wiki_pages, wiki_notes_queue and "
          "wiki_findings_resolved agree with the database and the writers' schemas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
