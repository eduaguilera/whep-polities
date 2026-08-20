#!/usr/bin/env python3
"""Where the SOURCE revises its own stated area, does our periodisation have a boundary? (issue 503)

THE SIGNAL, AND WHY IT IS INDEPENDENT OF EVERYTHING ELSE HERE. `data/final/source_stated_areas.csv`
carries what each yearbook edition said its own reporting units measured. 210 of 1,008 labels revise
that figure at least once, and a LARGE revision marks a year the source itself treated as a
territorial change. Our span boundaries and those revisions should coincide -- and where they do, that
is corroboration of the periodisation from the data rather than from historical reading, which nothing
else in this repo supplies. Where they do not, one polity is asserting a constant territory that the
source contradicts in its own area column.

This depends on no polygon, no wiki page, no magnitude profile and no second source, which is what
makes it worth having: every other check on periodisation here shares inputs with the thing it checks.

WHAT AGREEMENT LOOKS LIKE. 87,776 -> 247,916 km2 for `ETAT SERBE-CROATE-SLOVENE` between the 1913 and
1921 statements, with `F248-1920-1947` beginning in 1920. 137,903 -> 294,695 for `ROUMANIE`, boundary
at 1920. `HONGRIE` 70% at Trianon, `GRÈCE` 127% across the Balkan Wars, `AUTRICHE` 74% at the
dissolution. The source watched the same events.

THE FILTER IS WHAT MAKES THIS A WORKLIST RATHER THAN A FIXED LIST, and it is the whole design. A large
revision has two possible causes and only one of them is ours:

    a real territorial or scope change  -> our span may be missing a boundary
    a defect in the source              -> nothing to do here

`validate_stated_areas.py` already curates the second class, in BASELINE (a divergence that suppresses
a failure) and SOURCE_NOTES (a one-source note that does not). MONACO's dropped decimal separator,
GREENLAND's three estimates, GIBRALTAR's 1000-hectare unit error are all recorded there. So this file
EXCLUDES any (polity, source) pair those dicts already explain, which means:

  * a diagnosed source error leaves the table by being diagnosed, not by being hard-coded here;
  * an UNEXPLAINED large revision stays, whichever cause it turns out to have, which is correct --
    `ESTHONIE` stating 6,775 km2 against Estonia's 45,339 is worth looking at either way.

Without the filter, 4 of the 9 spanning cases are known source defects and the table reads as a
false-positive generator.

WHAT THIS DOES NOT DO. It does not propose moving any polity. `ALGÉRIE` is the clearest case -- 575,289
km2 (the three civil departments) to 2,196,294 (the colony including the Southern Territories), with
`DZA-1919-1962` carrying one polygon across it -- and that is issue 400's case 2, whose remedy is a
polity-creation decision. `EQUATEUR`'s 306,644 -> 714,860 tracks Ecuador's CLAIMED Amazon before the
1942 Rio Protocol, so it is a claim rather than control and probably not ours at all. The table records
the disagreement and its size; whose it is, is a judgement.

Usage:
  python3 pipelines/polity-autoimprove/34_area_revision_boundaries.py            # report only
  python3 pipelines/polity-autoimprove/34_area_revision_boundaries.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/34_area_revision_boundaries.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "area_revision_boundaries.csv")
STATED = os.path.join(REPO, "data/final/source_stated_areas.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

# A revision below this is re-measurement, rounding or a boundary survey, not an event. 50% is not
# tuned: every agreement case below sits at 60% or more, and the largest sub-50% revisions are
# plainly surveys (`TRANSJORDANIE` 40,000 -> 89,975 as its desert frontier was fixed).
MIN_STEP = 0.50

FIELDS = ("label", "source", "step_pct", "year_before", "year_after", "area_before", "area_after",
          "polity_code", "polity_start", "polity_end", "verdict")


def _n(x, nd=4):
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def build() -> list[dict]:
    import pandas as pd
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    sys.path.insert(0, HERE)
    import io
    _o = sys.stdout
    sys.stdout = io.StringIO()
    try:
        import validate_stated_areas as V
        res = V.analyse()
        import matchlib
        matcher = matchlib.Matcher(
            V.CSV_PATH, os.path.join(HERE, "state/applied_aliases.csv"), verbose=False)
    finally:
        sys.stdout = _o
    lex, ours = res["lexicon"], res["ours"]
    # (polity, source) pairs whose divergence is already explained by curation
    explained = set(V.BASELINE) | set(V.SOURCE_NOTES)

    db = pd.read_csv(POLITIES).set_index("polity_code")
    st = pd.read_csv(STATED)
    st = st[st.stated_area_km2 > 0]

    rows = []
    for (source, label), g in st.groupby(["source", "label"], sort=True):
        if g.stated_area_km2.nunique() < 2:
            continue
        seq = [(int(r.data_year), float(r.stated_area_km2))
               for r in g.sort_values("data_year").itertuples()]
        steps = [(abs(seq[i + 1][1] / seq[i][1] - 1), i) for i in range(len(seq) - 1) if seq[i][1] > 0]
        if not steps:
            continue
        step, i = max(steps)
        if step < MIN_STEP:
            continue
        y0, a0 = seq[i]
        y1, a1 = seq[i + 1]
        code = None
        for cand in (label, lex.get(V.normalise_label(label))):
            if not cand:
                continue
            try:
                code = matcher.assign(cand, None, source, y1)[0]
            except Exception:
                code = None
            if code:
                break
        if not code or code not in ours or code not in db.index:
            continue
        if (code, source) in explained:
            continue                      # a diagnosed source defect leaves by being diagnosed
        a, b = int(db.at[code, "start_year"]), int(db.at[code, "end_year"])
        rows.append({
            "label": label, "source": source, "step_pct": _n(round(step * 100, 1)),
            "year_before": y0, "year_after": y1,
            "area_before": _n(a0), "area_after": _n(a1),
            "polity_code": code, "polity_start": a, "polity_end": b,
            "verdict": "one_polity_spans_the_revision" if (a <= y0 and y1 <= b)
                       else "our_boundary_falls_between",
        })
    rows.sort(key=lambda r: (-float(r["step_pct"]), r["label"]))
    return rows


def write(rows: list[dict], path: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    for p in (STATED, POLITIES):
        if not os.path.exists(p):
            print(f"input absent ({p}); nothing to do", file=sys.stderr)
            return 0
    rows = build()
    spans = [r for r in rows if r["verdict"] == "one_polity_spans_the_revision"]
    agree = [r for r in rows if r["verdict"] == "our_boundary_falls_between"]
    print(f"{len(rows)} stated-area revision(s) of at least {MIN_STEP:.0%} whose label resolves to a "
          f"polity, excluding those already explained in BASELINE/SOURCE_NOTES")
    print(f"  our boundary falls between the two figures: {len(agree)}   (corroboration)")
    print(f"  ONE POLITY SPANS THE REVISION:              {len(spans)}   (a constant territory the "
          f"source contradicts)")
    for r in rows:
        m = "SPANS" if r["verdict"] == "one_polity_spans_the_revision" else "boundary"
        print(f"  {r['label'][:28]:30}{float(r['step_pct']):>6.0f}%  {r['year_before']}->"
              f"{r['year_after']:<6}{float(r['area_before']):>11,.0f} -> "
              f"{float(r['area_after']):>11,.0f}  {r['polity_code']:20} {m}")

    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {OUT}; run with --write", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {OUT}: {len(have)} row(s) on disk, {len(want)} rebuilt", file=sys.stderr)
            for h, w in zip(have, want):
                if h != w:
                    print(f"  first difference:\n    disk {h}\n    built {w}", file=sys.stderr)
                    break
            return 1
        print(f"OK {os.path.basename(OUT)} matches a fresh rebuild ({len(have)} rows)")
    if a.write:
        write(rows, OUT)
        print(f"wrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
