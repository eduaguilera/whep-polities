#!/usr/bin/env python3
"""Does the assertion triage queue still describe its own rows?

`state/assertion_triage.csv` is the queue the verification workflow walks: 796 pending assertions,
each a (label, source, year-span) claim routed to a candidate polity, ordered by `verify_order` and
bucketed into a `tier` that decides how much scrutiny it gets. It is the table that decides WHAT GETS
LOOKED AT, so a silent corruption here does not produce a wrong number — it produces work never done.

Until 2026-08-19 no gate read it. It was the third of the three ungated tables issue 432 named, and
the one I called least consequential; that was a judgement about blast radius, not about whether the
table is checkable. It turned out to be the most re-derivable of the three.

Almost nothing here is a pinned count. Five of the six arms recompute the column from other columns:

    A  key            == norm(label)|source|years_observed   [+ |candidate when disambiguated]
    B  keys unique    -- a key maps to one ledger row and one evidence bundle (00_intake.py:354)
    C  verify_order   is a dense permutation of 1..N, so no assertion is unreachable or duplicated
    D  n_distinct_years in [1, span width] -- cannot observe more years than the span contains
    E  inclusion_impossible agrees with assertion_nesting_flags.csv   <-- CROSS-TABLE
    F  candidate resolves to a live polity_code

E is the arm worth having. `inclusion_impossible` is a copy of a verdict computed in a DIFFERENT
table, and a copied verdict is exactly the thing that goes stale when its source is regenerated and
its consumer is not. Verified 2026-08-19: the biconditional holds for all 796 rows (17 True), against
the impossible pairs in assertion_nesting_flags.csv keyed on either side.

Why no baseline row count: the queue drains on purpose. Pinning 796 would fail on the correct action
of verifying an assertion, which is the failure mode validate_magnitude_outliers.py exists to avoid.

WHAT THIS GATE DOES NOT CATCH — stated because the coverage is otherwise easy to over-read. Arm A is
INTERNAL consistency: it proves each key rebuilds from its own three columns, and all 796 do. A row
that is stale relative to `assertions.json` rebuilds perfectly and passes. Issue 434 is exactly that
defect and this gate is green on it: 71 queue rows name a span no current assertion has, and 198
pending/reopened assertions (8.9% of pending panel rows) never reach the queue at all.

The arm that would catch it is a seventh, checking the queue against `assertions.json`. It is absent
because it would fail on main today, and the resync it demands is a decision about curated state
(re-running the generator has previously re-banked verdicts over hand retractions). Order is: resync
under 434, then add the arm. Arm E is the same class of check against a table that IS in sync.

Usage:
  python3 scripts/validate_assertion_triage.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/assertion_triage.csv")
NESTING = os.path.join(REPO, "pipelines/polity-autoimprove/state/assertion_nesting_flags.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

TIERS = {"territory_basis_wrong", "nested_reporting", "boundary_year", "weak_route", "precedent",
         "thin", "bulk"}
STATUSES = {"pending", "reopened", "confirmed", "rejected", "withdrawn"}
TRUEISH = {"true", "yes", "1"}


def norm(s) -> str:
    """matchlib.norm, restated so the gate does not import the generator to know what a key means.

    Cross-checked against the real one below when it is importable; CI has no numpy guarantee, so
    this gate must not depend on that import to run its main arms.
    """
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def impossible_keys() -> set[str] | None:
    if not os.path.exists(NESTING):
        return None
    keys = set()
    with open(NESTING, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("inclusion") == "impossible_outer_excludes_inner":
                for k in ("outer_key", "inner_key"):
                    if r.get(k):
                        keys.add(r[k])
    return keys


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run 12_triage_assertions.py",
              file=sys.stderr)
        return 1
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} has no rows", file=sys.stderr)
        return 1

    live = None
    if os.path.exists(POLITIES):
        with open(POLITIES, encoding="utf-8") as fh:
            live = {r["polity_code"] for r in csv.DictReader(fh)}
    imposs = impossible_keys()

    problems, orphans, seen, orders = [], set(), {}, []
    rederived = flagged = 0

    for i, r in enumerate(rows, start=2):
        key = (r.get("key") or "").strip()
        label, src = r.get("label") or "", (r.get("source") or "").strip()
        span = (r.get("years_observed") or "").strip()
        where = f"line {i} {key or '<no key>'}"

        # --- A: the key must be rebuildable from the columns it claims to summarise ---
        base = f"{norm(label)}|{src}|{span}"
        cand = (r.get("candidate") or "").strip()
        if key not in (base, f"{base}|{cand}"):
            problems.append(
                f"A {where}: key does not rebuild from its own columns — expected {base!r} "
                f"(or that plus |{cand} when 00_intake disambiguates a shared key)")
        else:
            rederived += 1

        # --- B: one key, one ledger row ---
        if key in seen:
            problems.append(
                f"B {where}: key repeats line {seen[key]}. A key maps to one ledger row and one "
                f"evidence bundle, so banking a verdict on it would write to both (00_intake.py)")
        seen[key] = i

        # --- C: the queue must be walkable ---
        try:
            orders.append(int(r["verify_order"]))
        except (KeyError, TypeError, ValueError):
            problems.append(f"C {where}: verify_order {r.get('verify_order')!r} is not an integer")

        # --- D: you cannot observe more distinct years than the span holds ---
        m = re.fullmatch(r"(-?\d+)-(-?\d+)", span)
        n = r.get("n_distinct_years")
        if m and n not in (None, ""):
            try:
                n_i, width = int(n), int(m.group(2)) - int(m.group(1)) + 1
                if n_i < 1:
                    problems.append(f"D {where}: n_distinct_years {n_i} is not positive")
                elif n_i > width:
                    problems.append(
                        f"D {where}: n_distinct_years {n_i} exceeds the {width}-year span {span} — "
                        f"the row observes more years than it covers")
            except ValueError:
                problems.append(f"D {where}: n_distinct_years {n!r} is not an integer")

        # --- E: a verdict copied from another table must still match that table ---
        flag = (r.get("inclusion_impossible") or "").strip().lower() in TRUEISH
        flagged += flag
        if imposs is not None:
            want = key in imposs
            if flag != want:
                problems.append(
                    f"E {where}: inclusion_impossible={flag} but assertion_nesting_flags.csv "
                    f"{'does' if want else 'does not'} class this key impossible. This column is a "
                    f"COPY of that table's verdict — a disagreement means one of the two was "
                    f"regenerated without the other (issue 273's finding is in that table)")

        # --- F: the routing target must still exist ---
        if live is not None and cand and cand not in live:
            orphans.add(cand)

        tier, status = (r.get("tier") or "").strip(), (r.get("status") or "").strip()
        if tier and tier not in TIERS:
            problems.append(f"{where}: unknown tier {tier!r} — generator and gate disagree about "
                            f"the vocabulary that decides how much scrutiny a row gets")
        if status and status not in STATUSES:
            problems.append(f"{where}: unknown status {status!r}")

    if orders:
        want = list(range(1, len(rows) + 1))
        if sorted(orders) != want:
            got = sorted(orders)
            dup = {o for o in orders if orders.count(o) > 1}
            problems.append(
                f"C verify_order is not a dense 1..{len(rows)} ordering (min {got[0]}, max "
                f"{got[-1]}, {len(set(orders))} distinct of {len(rows)}"
                + (f", repeats {sorted(dup)[:5]}" if dup else "")
                + ") — a gap or a repeat means an assertion is skipped or handled twice")

    for code in sorted(orphans):
        problems.append(
            f"F {code} is not a polity in data/final/polities_database.csv — the assertion routes to "
            f"a code the database no longer has, so verifying it can reach no polity")

    # Drift check on the restated normaliser. Optional by design: it needs the generator's numpy.
    try:
        sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
        from matchlib import norm as real_norm  # noqa: PLC0415
    except Exception:
        pass
    else:
        drift = [r["label"] for r in rows if norm(r.get("label")) != real_norm(r.get("label"))]
        if drift:
            problems.append(
                f"this gate's restated norm() has drifted from matchlib.norm on {len(drift)} labels "
                f"(e.g. {drift[:3]}) — arm A is then checking a rule the generator does not use")

    print(f"assertion triage: {len(rows)} rows, {rederived} keys rebuilt from their own columns, "
          f"inclusion_impossible {flagged}"
          + (f" agreeing with {len(imposs)} nesting keys" if imposs is not None
             else " (nesting table absent, arm E skipped)")
          + f", orphaned candidates {len(orphans)}")

    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
