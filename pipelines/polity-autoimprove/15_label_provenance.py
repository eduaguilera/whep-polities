#!/usr/bin/env python3
"""Which RAW source label is each layer-B label actually made of?

THE BLIND SPOT THIS EXISTS FOR. Layer B carries 164 IIA labels. The raw IIA extract carries 403.
Somewhere in harmonisation, 403 became 164, and nothing in this repository records which went
where. Most of that collapse is a benign modernisation of colonial names -- `french algeria` ->
`algeria`, `british cyprus` -> `cyprus`, `british burma` -> `myanmar`. Some of it silently merges
DIFFERENT TERRITORIES, and those are unfindable from inside the database:

  * `viet nam` is 94% `french tonkin` -- northern Vietnam, ~105,000 km2, routed to a 326,024 km2
    polity. IIA carries `french annam` and `french cochinchina` as separate labels.
  * `serbia` is 93% `yugoslavia` + `kingdom of serbs, croats and slovenes`, and 0% raw `serbia`
    (which has 28 rows, all trade, no production at all). Issue 315.
  * `indonesia` mixes `dutch east indies` (46%) with `dutch java and madura` (39%) -- the colony
    and a 7% subset of it, inside one label. Issue 312.
  * `mozambique` is 68% `portuguese mozambique: COMPANY CONCESSION`, a chartered concession.

Every one of these passes every other check the pipeline has. The polygon is stable, the wiki page
is coherent, the neighbours are continuous, the magnitudes are plausible -- a national-scale
agricultural series looks plausible at either scale. In #312 it took the decorrelated reviewer
opening the raw file to overturn a high-confidence `verified_equal`; the verifier was reasoning
correctly from everything it could see.

METHOD, AND THE TWO CORRECTIONS THAT CHANGED THE ANSWER. Each label is fingerprinted as its set of
(year, rounded value) pairs and matched against every raw label by set overlap. Item names differ
between the two, so matching on values rather than names is deliberate. But:

  1. PRODUCTION-SIDE ONLY. The raw `variable` column separates imports / exports / production /
     area, and trade rows outnumber production rows roughly 3:1. Matching without that filter lets
     an export tonnage match a production tonnage. It changed the Indonesia answer materially --
     from "is java and madura" to "mixes the colony with java and madura", which is a different
     and worse defect.
  2. THERE IS A NOISE FLOOR. Fingerprints collide by chance, and unrelated labels (`bulgaria`,
     `british cyprus`, `italy`) show up against everything at 7-25%. Anything at or below ~25% is
     not evidence. Only wide margins mean anything, which is why the report prints the runners-up
     rather than just the winner -- a 40/38/35 three-way split says something quite different from
     a single 94%.

The two already-registered conventions (`iia/russian federation` = whole USSR, `iia/south korea` =
whole peninsula) are rediscovered by this method unprompted, which is the available control on it.

NOT A GATE. The raw extract lives outside the repository and is not on every machine, so CI cannot
run this. It SKIPs cleanly when the file is absent, the same way 11_retest_conventions.py does when
the layer-B panel is missing.

Usage:
  python3 pipelines/polity-autoimprove/15_label_provenance.py
  python3 pipelines/polity-autoimprove/15_label_provenance.py --label serbia
  python3 pipelines/polity-autoimprove/15_label_provenance.py --raw PATH --min-rows 30
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

DEFAULT_RAW = os.path.expanduser(
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"
)
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")
)

# Raw `variable` values that are production-side rather than trade. Trade rows outnumber these
# ~3:1 and matching against them produces false positives.
PRODUCTION_VARIABLES = {
    "production", "area", "bearing area", "planted area", "dry production",
    "laying hens", "number", "production of cocoons", "eggs for incubation",
}

# Chance-collision level between unrelated labels, measured across this panel. A match at or under
# this is not evidence of anything.
NOISE_FLOOR = 0.25

# A label whose best raw match explains at least this much is accounted for by ONE raw label, and
# whatever it is called is then just a naming question. Below it, something else is contributing.
EXPLAINED = 0.85

# A runner-up only counts as a genuine second contributor if it is within this fraction of the top
# match. Without it, `french mauritania 100%` lists `total 31%` and `british cyprus 29%` as
# co-contributors, which is only the noise floor showing through on a small series.
RUNNER_UP_RATIO = 0.45


# Colonial qualifiers the harmonisation strips when modernising a name. `french algeria` ->
# `algeria` is a RENAME and benign; `dutch new guinea` -> `papua new guinea` is a REDIRECT to a
# different territory and is not. Separating the two mechanically is what makes the output
# readable -- most of the 403 -> 164 collapse is the benign kind.
COLONIAL = (
    "british", "french", "dutch", "portuguese", "italian", "spanish", "german",
    "japanese", "danish", "belgian", "american", "us", "soviet", "russian",
)


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def is_rename(raw_label: str, lb_label: str) -> bool:
    """Is the raw label just the layer-B label wearing a colonial qualifier?

    Deliberately conservative: it must reduce to the SAME name. `british southern rhodesia` does
    not reduce to `zimbabwe`, so that legitimate rename is reported as a redirect and read by a
    human. Over-reporting is the safe direction here -- a missed redirect is the failure that
    matters, and it is the one that produced issues 312 and 315.
    """
    a, b = norm(raw_label), norm(lb_label)
    if a == b:
        return True
    parts = a.split()
    while parts and parts[0] in COLONIAL:
        parts = parts[1:]
    return " ".join(parts) == b


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW, help="raw IIA harmonized extract (xlsx)")
    ap.add_argument("--layer-b", default=DEFAULT_PANEL, help="consolidated layer-B parquet")
    ap.add_argument("--source", default="iia", help="source tag to audit (default: %(default)s)")
    ap.add_argument("--label", help="report one layer-B label in full instead of the ranked table")
    ap.add_argument("--min-rows", type=int, default=30,
                    help="skip labels with fewer dated values (default: %(default)s)")
    args = ap.parse_args()

    for path, what in ((args.raw, "raw extract"), (args.layer_b, "layer-B panel")):
        if not os.path.exists(path):
            print(f"SKIP: {what} not present at {path}")
            return 0

    import pandas as pd

    x = pd.read_excel(args.raw)
    x["_c"] = x["country"].astype(str)
    x["_y"] = pd.to_numeric(x["year"], errors="coerce")
    x["_v"] = pd.to_numeric(x["value"], errors="coerce")
    prod = x[x["variable"].astype(str).str.lower().isin(PRODUCTION_VARIABLES)].dropna(
        subset=["_y", "_v"])

    raw_fp: dict[str, set] = defaultdict(set)
    for c, y, v in zip(prod["_c"], prod["_y"], prod["_v"]):
        raw_fp[c].add((int(y), round(float(v), 1)))

    d = pd.read_parquet(args.layer_b)
    lb = d[d["source"] == args.source].dropna(subset=["year", "value"])
    lb_fp: dict[str, set] = defaultdict(set)
    for c, y, v in zip(lb["country"], lb["year"], lb["value"]):
        lb_fp[str(c)].add((int(y), round(float(v), 1)))

    print(f"raw: {len(prod):,} production-side rows over {len(raw_fp)} labels")
    print(f"layer B ({args.source}): {len(lb):,} dated rows over {len(lb_fp)} labels")
    print(f"noise floor {NOISE_FLOOR:.0%} — matches at or below it are chance collisions\n")

    targets = {k: v for k, v in lb_fp.items() if norm(k) == norm(args.label)} if args.label else lb_fp

    rows = []
    for label, fp in targets.items():
        if not args.label and len(fp) < args.min_rows:
            continue
        scored = sorted(
            ((len(fp & r), rl) for rl, r in raw_fp.items() if fp & r),
            key=lambda t: (-t[0], t[1]),
        )
        if not scored:
            continue
        top = scored[0][0]
        above = [
            (c, rl) for c, rl in scored
            if c / len(fp) > NOISE_FLOOR and c >= top * RUNNER_UP_RATIO
        ]
        # UNION, not the sum: the same value can match several raw labels, so adding the
        # percentages double counts. `serbia` is yugoslavia 71% and kingdom-of-SCS 25%, which is
        # 93% of its values between them, not 96%.
        covered = set()
        for _c, rl in above:
            covered |= fp & raw_fp[rl]
        rows.append((label, len(fp), scored[:4], above, top / len(fp), len(covered) / len(fp)))

    if args.label:
        for label, n, scored, above, share, union in rows:
            print(f"{label}  ({n} dated production values)\n")
            for c, rl in scored:
                flag = "" if c / n > NOISE_FLOOR else "   (at/below noise floor)"
                print(f"   {100 * c / n:5.1f}%  {rl}{flag}")
            named = [rl for _c, rl in above]
            if len(named) > 1:
                print(f"\n   MIXED: draws on {len(named)} raw labels — {', '.join(named)}")
                print(f"   between them they account for {union:.0%} of the values "
                      f"(union, not sum — a value can match more than one label)")
            elif named and not is_rename(named[0], label):
                # Checked BEFORE coverage, so this agrees with the summary table's ordering: a
                # label pointing at a different territory is the finding, whether or not that
                # match also happens to be partial.
                print(f"\n   REDIRECTED: {named[0]} — one raw label, a different name"
                      + (f", and it covers only {share:.0%}" if share < EXPLAINED else ""))
            elif share < EXPLAINED:
                print(f"\n   UNDER-EXPLAINED: best match covers only {share:.0%}")
            elif named:
                print(f"\n   RENAMED: {named[0]}")
        return 0

    # A label built from ONE raw label is fine whatever it is called -- that is just the colonial
    # rename. The interesting cases are labels built from several, and labels where no single raw
    # label accounts for most of the values.
    multi = [r for r in rows if len(r[3]) > 1]
    single = [r for r in rows if len(r[3]) <= 1]
    redirect = [r for r in single if r[2] and not is_rename(r[2][0][1], r[0])]
    thin = [r for r in single
            if r[4] < EXPLAINED and r not in redirect]
    multi.sort(key=lambda r: -r[1])
    redirect.sort(key=lambda r: -r[1])
    thin.sort(key=lambda r: r[4])

    print("MIXED — drawing on more than one raw label. A label assembled from two territories\n"
          "cannot be corrected by one routing decision:\n")
    for label, n, _scored, above, _share, _u in multi:
        parts = " | ".join(f"{rl} {100 * c / n:.0f}%" for c, rl in above)
        print(f"  {label[:26]:28} n={n:>4}  {parts}")

    if redirect:
        print("\nREDIRECTED — one raw label, but NOT this label under a colonial qualifier.\n"
              "Some are legitimate historical renames (british southern rhodesia -> zimbabwe);\n"
              "the rest are a different territory and need a routing decision:\n")
        for label, n, scored, _above, share, _u in redirect:
            print(f"  {label[:26]:28} n={n:>4}  {scored[0][1]} {share:.0%}")

    if thin:
        print(f"\nUNDER-EXPLAINED — matches its own name, but only {EXPLAINED:.0%} of values are\n"
              "accounted for. Usually method loss (unit conversion, period rows), not mixing:\n")
        for label, n, scored, _above, share, _u in thin:
            print(f"  {label[:26]:28} n={n:>4}  {scored[0][1]} {share:.0%}")

    print(f"\n{len(multi)} mixed, {len(redirect)} redirected, {len(thin)} under-explained, "
          f"of {len(rows)} labels examined.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
