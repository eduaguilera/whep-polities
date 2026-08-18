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
import csv
import os
import re
import sys
from collections import defaultdict

DEFAULT_RAW = os.path.expanduser(
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"
)
DEFAULT_PROV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "state/iia_label_provenance.csv")
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

# BUT the noise floor and the ratio were both calibrated on UNRELATED labels, and chance collisions
# do not respect naming. A runner-up from the same family as the top match -- `british gold coast`
# beside `german togoland`, `portuguese mozambique: province` beside the same colony's company
# concession -- is evidence at a level where an unrelated label would be noise. Judging those by the
# unrelated-label thresholds classified `ghana` (togoland 63% + gold coast 27%, union 90%) and
# `mozambique` (concession 68% + province 19%, union 84%) as single-source redirects when both are
# assembled from two territories.
FAMILY_FLOOR = 0.10

# How much NEW coverage an unrelated runner-up must add before it counts as a second contributor.
# Replaces a share-ratio test, which let `ghana` through as single-source: `british gold coast` sits
# at 27% against `german togoland` 63%, just under a 0.45 ratio, yet it explains 27 points of values
# togoland does not explain at all. Two different colonies in one label.
UNION_GAIN = 0.15


def same_family(a: str, b: str) -> bool:
    """Do two raw labels name parts of one colonial family?

    True when either is a `parent: child` refinement of the other, or when they share their first
    two words (`british gold coast` / `british togoland`). Deliberately loose: this only LOWERS the
    threshold at which a second contributor is believed, and the union share is reported alongside
    so the reader sees what was combined.
    """
    a, b = norm(a), norm(b)
    if a.startswith(b + " ") or b.startswith(a + " "):
        return True
    aw, bw = a.split(), b.split()
    return len(aw) >= 2 and len(bw) >= 2 and aw[:2] == bw[:2]


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


def era_runs(fp: set, raw_fp: dict, contributors: list) -> list:
    """Per-YEAR dominant contributor, collapsed into contiguous runs.

    WHY THIS EXISTS. Everything else here is computed per LABEL across all its years, which cannot
    be right for a label whose source changes mid-span. `serbia` is the clearest case: its values
    are 76%/92% `kingdom of serbs, croats and slovenes` up to 1929 and 94% `yugoslavia` after,
    because the STATE was renamed in 1929. Averaged over the whole label that reads as two
    territories mixed together, which overstates it — the label is one entity across a rename, and
    each era is internally consistent.

    So a label with two contributors is only genuinely MIXED if they co-occur in the SAME years.
    If they occupy different years it is SEQUENTIAL, and the switch year is the useful output: it
    tells a reader which assertions on that label are affected, instead of condemning all of them.

    Returns [(first_year, last_year, raw_label), ...] using only the contributors already found
    above the noise floor, so a chance collision cannot invent an era.
    """
    if len(contributors) < 2:
        return []

    # CO-OCCURRENCE FIRST. Per-year dominance alone is not enough: `indonesia` has sugar coming
    # from `dutch java and madura` in every year while cotton comes from `dutch east indies` in
    # every year, so whichever supplies more values that year "wins" and the label looks like a
    # clean succession when it is nothing of the kind. If both contributors supply values in the
    # SAME year, they are genuinely concurrent and there is no era structure to report.
    shared = 0
    years = sorted({y for y, _v in fp})
    for year in years:
        vals = {(y, v) for y, v in fp if y == year}
        supplying = sum(1 for rl in contributors if vals & raw_fp[rl])
        if supplying >= 2:
            shared += 1
    if years and shared / len(years) > 0.25:
        return []

    by_year = {}
    for year in sorted({y for y, _v in fp}):
        vals = {(y, v) for y, v in fp if y == year}
        best, best_n = None, 0
        for rl in contributors:
            n = len(vals & raw_fp[rl])
            if n > best_n:
                best, best_n = rl, n
        if best:
            by_year[year] = best
    runs = []
    for year in sorted(by_year):
        lab = by_year[year]
        if runs and runs[-1][2] == lab and year - runs[-1][1] <= 2:
            runs[-1][1] = year
        else:
            runs.append([year, year, lab])
    # Drop runs too short to be an era rather than a stray year.
    return [tuple(r) for r in runs if r[1] - r[0] >= 2]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW, help="raw IIA harmonized extract (xlsx)")
    ap.add_argument("--layer-b", default=DEFAULT_PANEL, help="consolidated layer-B parquet")
    ap.add_argument("--source", default="iia", help="source tag to audit (default: %(default)s)")
    ap.add_argument("--label", help="report one layer-B label in full instead of the ranked table")
    ap.add_argument("--min-rows", type=int, default=30,
                    help="skip labels with fewer dated values (default: %(default)s)")
    ap.add_argument("--write", metavar="CSV", nargs="?", const=DEFAULT_PROV,
                    help="re-derive the TRACKED provenance table (default: %(const)s). The "
                         "classification the gate enforces is computed HERE, so writing it from "
                         "this script is the only way tool and table cannot drift apart — they "
                         "already did once, when a hand-rolled derivation used a share-ratio test "
                         "this script had replaced with a union-gain test")
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
    # KEY BY THE NORMALISED LABEL. The tracked table stores `layer_b_label` normalised, so keying
    # these fingerprints by the raw string silently dropped every label containing punctuation --
    # `china, mainland`, `china, taiwan province of`, `china, hong kong sar` -- straight into
    # `unknown` on --write. Thirteen labels, and the only visible symptom was an `unknown` count
    # rising, which reads as "not enough data" rather than "join failed".
    lb_fp: dict[str, set] = defaultdict(set)
    for c, y, v in zip(lb["country"], lb["year"], lb["value"]):
        lb_fp[norm(c)].add((int(y), round(float(v), 1)))

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
        # A runner-up earns its place by what it ADDS to the union, not by its own share. Share is
        # the wrong measure because one value can match several raw labels: `french mauritania` is
        # 100% explained by its own label and STILL shows `total` at 31%, which contributes nothing
        # new. Ghana's second label lifts coverage from 63% to 90% -- 27 points of values the first
        # label does not explain at all -- which is what "assembled from two territories" means.
        top, top_label = scored[0]
        above = [(top, top_label)]
        covered = set(fp & raw_fp[top_label])
        for c, rl in scored[1:]:
            if rl == top_label:
                continue
            gain = len((fp & raw_fp[rl]) - covered) / len(fp)
            related = same_family(rl, top_label)
            if gain >= (FAMILY_FLOOR if related else UNION_GAIN):
                above.append((c, rl))
                covered |= fp & raw_fp[rl]
        # UNION, not the sum: the same value can match several raw labels, so adding the
        # percentages double counts. `serbia` is yugoslavia 71% and kingdom-of-SCS 25%, which is
        # 93% of its values between them, not 96%.
        covered = set()
        for _c, rl in above:
            covered |= fp & raw_fp[rl]
        runs = era_runs(fp, raw_fp, [rl for _c, rl in above])
        rows.append((label, len(fp), scored[:4], above, top / len(fp), len(covered) / len(fp), runs))

    if args.write:
        # Re-derive the tracked table: keep every column the mapping supplies, and overwrite the
        # measured ones from the fingerprints computed above.
        signal_by_label = {}
        for label, _n, scored, above, _share, union, runs in rows:
            named = [rl for _c, rl in above]
            if len(named) > 1 and len(runs) > 1 and len({r[2] for r in runs}) > 1:
                # SEQUENTIAL: one source at a time. But that is only benign when the sources are
                # the SAME territory under different names. `french polynesia` runs
                # `french oceania: makatea island` 1909-1920 then `french oceania` 1930-1937 -- a
                # phosphate island alone, then the whole territory. Sequential, and still a scope
                # error for the early years. Whereas `serbia` runs
                # `kingdom of serbs, croats and slovenes` then `yugoslavia`: one state renamed.
                # The discriminator is whether one contributor is a `parent: child` refinement of
                # the other, which same_family already answers.
                eras = [r[2] for r in runs]
                nested = any(same_family(a, b) and norm(a) != norm(b)
                             for a in eras for b in eras)
                sig = "sequential_scope" if nested else "sequential_rename"
                note = " -> ".join(f"{lo}-{hi} {rl}" for lo, hi, rl in runs)
            elif len(named) > 1:
                sig, note = "mixed", " + ".join(named[:3]) + f" (union {union:.0%})"
            elif named and not is_rename(named[0], label):
                sig, note = "redirected", f"{named[0]} {union:.0%}"
            elif named:
                sig, note = "clean", f"{named[0]} {union:.0%}"
            else:
                sig, note = "unknown", "no raw label matches"
            signal_by_label[label] = (sig, note, scored[0][1] if scored else "",
                                      f"{scored[0][0] / _n:.2f}" if scored else "")
        with open(args.write, newline="", encoding="utf-8") as fh:
            table = list(csv.DictReader(fh))
            fields = list(table[0])
        for col in ("territory_signal", "fingerprint_note", "dominant_raw_label", "dominant_share"):
            if col not in fields:
                fields.append(col)
        changed = 0
        for r in table:
            lab = r.get("layer_b_label") or ""
            got = signal_by_label.get(lab)
            if not got:
                if r.get("territory_signal") != "unknown":
                    changed += 1
                r["territory_signal"] = "unknown"
                r["fingerprint_note"] = "label not measured (absent, or under --min-rows)"
                continue
            sig, note, dom, share = got
            if r.get("territory_signal") != sig:
                changed += 1
            r["territory_signal"], r["fingerprint_note"] = sig, note
            r["dominant_raw_label"], r["dominant_share"] = dom, share
        with open(args.write, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(table)
        print(f"wrote {len(table)} rows to {args.write}; {changed} signals changed")
        return 0

    if args.label:
        for label, n, scored, above, share, union, runs in rows:
            print(f"{label}  ({n} dated production values)\n")
            for c, rl in scored:
                flag = "" if c / n > NOISE_FLOOR else "   (at/below noise floor)"
                print(f"   {100 * c / n:5.1f}%  {rl}{flag}")
            named = [rl for _c, rl in above]
            if len(named) > 1 and len(runs) > 1 and len({r[2] for r in runs}) > 1:
                print(f"\n   SEQUENTIAL: one source at a time, switching between them —")
                for lo, hi, rl in runs:
                    print(f"     {lo}-{hi}  {rl}")
                print(f"   {union:.0%} of values accounted for. The contributors occupy DIFFERENT "
                      f"years, so this is a renaming or a succession, not two territories mixed. "
                      f"Only assertions overlapping a switch are affected.")
            elif len(named) > 1:
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
    for label, n, _scored, above, _share, _u, _r in multi:
        parts = " | ".join(f"{rl} {100 * c / n:.0f}%" for c, rl in above)
        print(f"  {label[:26]:28} n={n:>4}  {parts}")

    if redirect:
        print("\nREDIRECTED — one raw label, but NOT this label under a colonial qualifier.\n"
              "Some are legitimate historical renames (british southern rhodesia -> zimbabwe);\n"
              "the rest are a different territory and need a routing decision:\n")
        for label, n, scored, _above, share, _u, _r in redirect:
            print(f"  {label[:26]:28} n={n:>4}  {scored[0][1]} {share:.0%}")

    if thin:
        print(f"\nUNDER-EXPLAINED — matches its own name, but only {EXPLAINED:.0%} of values are\n"
              "accounted for. Usually method loss (unit conversion, period rows), not mixing:\n")
        for label, n, scored, _above, share, _u, _r in thin:
            print(f"  {label[:26]:28} n={n:>4}  {scored[0][1]} {share:.0%}")

    print(f"\n{len(multi)} mixed, {len(redirect)} redirected, {len(thin)} under-explained, "
          f"of {len(rows)} labels examined.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
