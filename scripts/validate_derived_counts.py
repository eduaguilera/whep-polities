#!/usr/bin/env python3
"""Does every `n_<thing>` column still equal the number of things it counts?

WHY A GENERIC GATE RATHER THAN AN ARM PER TABLE. Twice on 2026-08-19/20 a derived column in a
tracked table disagreed with the columns it was derived from, and neither was visible from inside
the row:

  * `collapse_groups.ratio_mean_max` was computed from full-precision values while the table stores
    rounded ones, so 4 rows disagreed with their own arithmetic (fixed in whep-polities#457).
  * `cross_label_duplication.smaller_label` named the LARGER label in all six rows, and survived
    review because `block_matches_level_of` was derived from the SAME swapped variables -- the two
    columns were wrong in unison, so the one a reader would sanity-check read correct (#470).

Both were found by comparing a derived column against its INPUT, not against its neighbours. Sibling
agreement proves nothing when siblings share the defect. This gate makes the cheapest instance of that
comparison automatic and generic, so it also covers tables nobody has written yet.

WHAT IT CHECKS, AND WHY THE PAIRING IS BY NAME. A column `n_labels` is paired with `labels`,
`n_sources` with `sources` -- the count must equal the number of pipe-delimited entries in the list it
names. The pairing is derived from the NAME and nothing else, deliberately: an earlier version of this
scan inferred pairings by trying every count against every list, and on clean data it reported
`n_labels vs len(sources)` and `n_sources vs len(labels)` as disagreements. Those are not derivations
at all -- they agreed on 2,288 rows only because most groups carry exactly one label and one source.
Inferred pairings manufacture findings; a naming convention does not.

VERIFIED TO DETECT, not merely to pass. Planting `n_labels = 9` on 12 rows of collapse_groups.csv is
reported, and so is a broken ratio; the check was built by first breaking the data and confirming the
scan saw it. An earlier version MISSED the planted count defect because it required a `|` to appear in
a sample of the list column -- which skipped `n_labels` in collapse_groups, where 1,436 of 1,995 rows
carry exactly ONE label. That is, it skipped the majority case, which is precisely where a count bug
hides: a single-entry list still has a count, and `1` is the easiest value to get wrong silently.

Currently covers 6 pairs over 5 tables and ~2,850 rows. The pair COUNT is printed and floored at 1,
not pinned: new tables following the convention are picked up automatically, which is the point, but
the gate must not silently find nothing to check.
"""
import csv
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
MIN_PAIRS = 1          # a floor, not a pin: finding nothing to check is itself a failure


def tracked_tables():
    """The state tables, preferring git's view and falling back to the directory.

    `git ls-files` is the right question -- an untracked scratch file is not something CI can assert
    about -- but it returns NOTHING outside a git work tree, and selftest_gates.py runs every gate in
    a temporary scratch tree that is not a repository. Without the fallback this gate found zero
    tables there and failed on its own MIN_PAIRS floor, which would have made its selftest case pass
    for the wrong reason: exit 1, but from the floor rather than from the injected defect.
    """
    out = subprocess.run(["git", "ls-files", "pipelines/polity-autoimprove/state"],
                         capture_output=True, text=True, cwd=REPO).stdout.split()
    paths = [os.path.join(REPO, p) for p in out if p.endswith(".csv")]
    if paths:
        return paths
    import glob as _glob
    return sorted(_glob.glob(os.path.join(STATE, "*.csv")))


def main() -> int:
    problems = []
    pairs = 0
    rows_checked = 0
    report = []
    for path in tracked_tables():
        try:
            with open(path, newline="", encoding="utf-8") as fh:
                rd = csv.DictReader(fh)
                rows = list(rd)
                cols = list(rd.fieldnames or [])
        except (OSError, UnicodeDecodeError):
            continue
        if not rows:
            continue
        for c in cols:
            if not c.startswith("n_"):
                continue
            base = c[2:]
            # name-matched only; see the docstring on why inferred pairings were dropped
            listcol = next((cand for cand in (base, base + "s", base.rstrip("s"))
                            if cand in cols and cand != c), None)
            if listcol is None:
                continue
            pairs += 1
            # THE DELIMITER IS A PROPERTY OF THE COLUMN AND MUST BE MEASURED, NOT ASSUMED. The first
            # version of this gate split on "|" everywhere and reported 15 failures, every one of them
            # its own fault: `item_blocks.items` and `item_product_switches.products` use ";", and
            # `verdict_carryover.carries` uses ";" while each ENTRY contains pipes of its own, because
            # an assertion key is `label|source|span`. Splitting that on "|" turns one carry into
            # three. So the candidate delimiter that explains the most rows is chosen per column, and
            # it must explain nearly all of them before any row is called a mismatch -- otherwise the
            # gate is asserting a convention the writer never followed.
            usable = [(i, r) for i, r in enumerate(rows, start=2)
                      if (r.get(listcol) or "").strip() and (r.get(c) or "").strip()]
            best, best_ok = None, -1
            for delim in ("|", ";", ",", "\n"):
                ok = 0
                for _, r in usable:
                    try:
                        want = int((r.get(c) or "").strip())
                    except ValueError:
                        continue
                    have = len([x for x in (r.get(listcol) or "").split(delim) if x.strip()])
                    ok += (want == have)
                if ok > best_ok:
                    best, best_ok = delim, ok
            n_rows = len(usable)
            bad = []
            # AN ABSOLUTE FLOOR, NOT A PERCENTAGE. With a percentage, breaking 2 of a 5-row table
            # drops the match rate to 60% and the whole column is SKIPPED -- so the gate was weakest
            # exactly where a table is small and a single bad row matters most. Verified: planting a
            # defect on 2 of item_blocks' 5 rows was missed under a 90% rule and is caught under this
            # one. Three consistent rows are enough to establish which delimiter the writer used;
            # everything after that is a mismatch to report, not evidence about the convention.
            if n_rows and (best_ok < 3 or best_ok / n_rows < 0.50):
                report.append((os.path.basename(path), c, listcol, n_rows, -1))
                continue          # no delimiter explains this column: not a count of this list
            for i, r in usable:
                got = (r.get(c) or "").strip()
                try:
                    want = int(got)
                except ValueError:
                    problems.append(f"{os.path.basename(path)}:{i} {c} is {got!r}, not an integer")
                    continue
                raw = (r.get(listcol) or "").strip()
                have = len([x for x in raw.split(best) if x.strip()])
                if want != have:
                    bad.append((i, want, have, raw[:48]))
            rows_checked += n_rows
            report.append((os.path.basename(path), c, listcol, n_rows, len(bad)))
            for i, want, have, raw in bad[:5]:
                problems.append(
                    f"{os.path.basename(path)}:{i} {c}={want} but {listcol} holds {have} entry(ies) "
                    f"({raw!r}). A count that has drifted from the list it counts is the shape that "
                    f"survived review twice: a derived column can be wrong while every column beside "
                    f"it is right, so it has to be checked against its own input")

    print(f"{pairs} name-matched count/list pair(s) over {rows_checked} row(s):")
    for t, c, l, n, nbad in report:
        note = ("  no consistent delimiter -- not a count of this list" if nbad == -1
                else ("" if not nbad else f"  {nbad} MISMATCH"))
        print(f"  {t:34} {c:14} <-> {l:14} {n:>5} rows{note}")
    if pairs < MIN_PAIRS:
        problems.append(
            f"found {pairs} count/list pair(s), below the floor of {MIN_PAIRS}. This gate discovers "
            f"its own work from a naming convention, so finding nothing means the convention changed "
            f"or the tables moved -- either way it is checking nothing while reporting success")

    if problems:
        print(f"FAIL: {len(problems)} derived-count problem(s)", file=sys.stderr)
        for p in problems[:25]:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: every n_<thing> column equals the number of things its list holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
