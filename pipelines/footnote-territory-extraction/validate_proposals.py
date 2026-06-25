#!/usr/bin/env python3
"""Validate, clean, and categorize footnote->polity proposals (step 5).

Takes the step-4 ``footnote_polity_proposals.csv`` and:
  - drops low-confidence (< MIN_CONF) and self-referential (host == territory)
    proposals;
  - validates host_polity_code / territory_polity_code against the polity DB and
    checks the host is active in the claim year (polity DB read from the
    polity-autoimprove ``territory_basis.csv``, which carries polity_code,
    polity_name, start_year, end_year for the full set);
  - emits a creation/handling backlog of territories not in the DB;
  - cross-checks boundary-vintage claims against the classifier's
    ``territory_basis`` so disagreements (e.g. data flagged "Bizone only" while
    the classifier guessed assumed_constant) surface for review.

Outputs (in OUT_DIR):
  - footnote_proposals_validated.csv
  - footnote_territory_gaps.csv
  - footnote_territory_basis_crosscheck.csv

Usage:
    python3 validate_proposals.py [PROPOSALS_CSV] [TERRITORY_BASIS_CSV] [OUT_DIR]
"""

import os
import sys
import csv
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.expanduser("~/Nextcloud/whep/footnote_territory")
DEFAULT_PROPS = os.path.join(DEFAULT_OUT, "footnote_polity_proposals.csv")
DEFAULT_TB = os.path.join(
    HERE, "..", "polity-autoimprove", "state", "territory_basis.csv")
MIN_CONF = 0.85


def _active(ref, code, year):
    p = ref.get(code)
    if not p:
        return None
    try:
        y = int(year)
        return int(float(p["start_year"])) <= y <= int(float(p["end_year"]))
    except (ValueError, KeyError):
        return None


def main():
    props_path = os.path.expanduser(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PROPS
    tb_path = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TB
    out_dir = os.path.expanduser(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OUT

    props = list(csv.DictReader(open(props_path)))
    tb_rows = list(csv.DictReader(open(tb_path)))
    ref = {r["polity_code"]: r for r in tb_rows}

    kept = []
    for p in props:
        try:
            conf = float(p["confidence"])
        except ValueError:
            conf = 0.0
        self_ref = bool(
            p["host_country"].strip().lower() == p["territory"].strip().lower()
            or (p["host_polity_code"] != ""
                and p["host_polity_code"] == p["territory_polity_code"]))
        terr = p["territory_polity_code"]
        row = dict(p)
        row["host_valid"] = p["host_polity_code"] in ref
        row["host_active_in_year"] = _active(ref, p["host_polity_code"], p["year"])
        row["territory_in_db"] = ("NOT_IN_DB" if terr in ("NOT_IN_DB", "")
                                  else terr in ref)
        row["self_referential"] = self_ref
        if conf >= MIN_CONF and not self_ref:
            kept.append(row)

    os.makedirs(out_dir, exist_ok=True)
    cols = list(kept[0].keys())
    kept.sort(key=lambda x: (x["action"], -float(x["confidence"])))
    with open(os.path.join(out_dir, "footnote_proposals_validated.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(kept)

    # territory gaps backlog
    gaps = {}
    for p in kept:
        if (p["territory_in_db"] == "NOT_IN_DB"
                and p["action"] in ("composed_union", "separate_entity", "new_polity")):
            g = gaps.setdefault(p["territory"], {"hosts": set(), "years": set(),
                                                 "actions": set()})
            g["hosts"].add(p["host_country"])
            g["years"].add(p["year"])
            g["actions"].add(p["action"])
    with open(os.path.join(out_dir, "footnote_territory_gaps.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["territory", "hosts", "years", "actions"])
        for t, v in sorted(gaps.items()):
            w.writerow([t, "; ".join(sorted(h for h in v["hosts"] if h)),
                        ",".join(sorted(y for y in v["years"] if y)),
                        ",".join(sorted(v["actions"]))])

    # territory_basis cross-check
    cc = []
    for p in kept:
        if p["action"] == "territory_basis" or p.get("relation") == "boundary":
            r = ref.get(p["host_polity_code"])
            cc.append({
                "host_polity_code": p["host_polity_code"], "year": p["year"],
                "footnote": p["text_en"][:80],
                "classifier_basis": r["territory_basis"] if r else "(host not in DB)",
                "classifier_priority_review": r["priority_review"] if r else "",
            })
    if cc:
        with open(os.path.join(out_dir, "footnote_territory_basis_crosscheck.csv"),
                  "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(cc[0].keys()))
            w.writeheader()
            w.writerows(cc)

    print(f"proposals={len(props)} kept(conf>={MIN_CONF},non-selfref)={len(kept)}")
    print("kept by action:", dict(Counter(p["action"] for p in kept)))
    print(f"territory gaps (not in DB): {len(gaps)}")
    print(f"territory_basis cross-check rows: {len(cc)}")


if __name__ == "__main__":
    main()
