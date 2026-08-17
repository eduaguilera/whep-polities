#!/usr/bin/env python3
"""Triage the assertion-verification backlog (issue #7).

`state/assertions.json` is a queue of `(label, source, year_segment) -> polity`
claims awaiting the historian pass (`verify_assertions.workflow.js`). Verifying
one costs ~35k Sonnet tokens including its blind review, so the queue's SIZE is
the whole problem: at the measured backlog that is tens of millions of tokens.

This script does NOT verify anything and never writes the review ledger. It
answers the two cheap questions that decide how to spend that budget:

  1. WHICH assertions carry deterministically visible trouble, so they should be
     verified FIRST (and read with a specific suspicion in mind), and
  2. which carry no deterministic signal at all, so a historian is genuinely the
     only way to settle them.

Why deterministic evidence cannot simply CLEAR the queue
--------------------------------------------------------
An assertion exists precisely because the deterministic pass already finished:
`matchlib` decided the ROUTE (alias -> iso -> name + year containment) and
recorded it. What is pending is the question routing cannot answer -- whether the
SOURCE's reporting territory under that label equals the polity's territory over
that segment (union/empire scope, boundary vintage, combined reporting, split
basis). No check over the repo's own tables can settle that: the tables are one
side of the comparison. So a triage can order, flag and bound the work; it
cannot bank it. Nothing here writes a verdict.

The one screen that finds real defects: SOURCE-INTERNAL NESTING
---------------------------------------------------------------
Empirically (`state/verdicts_applied.jsonl`, 159 applied verdicts) the pass
changed the routing in 3 cases. Two were the same shape -- FAO-1952 and IIA
"Ethiopia" routed to `AOI-1936-1941` (Italian East Africa: Ethiopia + Eritrea +
Somaliland) while the SAME source reported Eritrea and Somaliland as separate
labels straight through the occupation, so the umbrella polity was the wrong
reporting unit. The third (Argentina) pointed at a retired collapsed row, a
class `matchlib` now excludes outright.

That shape is computable. For every pair of assertions of the SAME source whose
observed year spans overlap, this script intersects their candidates' polygons;
when one candidate covers more than `--nest-frac` of the other's area, the source
reports an OUTER and an INNER territory at the same time. Exactly one of two
things is then true, and both are worth a historian's attention before the rest
of the queue:

  * the outer figures EXCLUDE the inner (the outer polity's polygon overstates
    the reporting territory -- a territory-basis defect), or
  * they INCLUDE it (the panel double-counts the inner territory).

On the current backlog this flags 137 pending assertions -- 17% of the queue --
including the Ethiopia/`AOI` case the pass previously found by reading.

And for a fifth of those pairs the choice between the two IS deterministic
--------------------------------------------------------------------------
Every unit in layer B is EXTENSIVE (tonnes, ha, heads, and their thousands --
`--additive-units`), so if the outer label's figures included the inner
territory, `outer >= inner` would have to hold for every shared (item, unit,
year) cell. Where it fails repeatedly, inclusion is arithmetically impossible and
the source is reporting the outer EXCLUSIVE of the inner -- which makes the
polity's territory the thing to fix, not the routing. `--min-violations` /
`--min-violation-frac` keep an isolated bad cell (or a one-off item-definition
mismatch) from carrying that conclusion; the counts are written out so the reader
can judge the margin. Measured on the current backlog: of 234 pairs, 20 show
impossible inclusion (Japan/Korea and Japan/Taiwan in both IIA and Mitchell, the
UK/Ireland split in Juan, Germany 1938 vs its post-war zones in FAO-1952, French
Indochina's members, India/Burma, Mali/Upper Volta), 55 are consistent with
inclusion (consistency is NOT proof -- a genuine double count looks exactly like
this), and 118 share no comparable cell at all.

The test needs the layer-B panel, which lives outside the repo; without
`--layer-b` the nesting flags are still written, with the magnitude columns empty.

Tiers (first match wins, most actionable first)
----------------------------------------------
  nested_reporting  in a source-internal nesting pair (above).
  boundary_year     observed span ends exactly at the candidate's EXCLUSIVE
                    `end_year`, i.e. the data names a dissolved entity's final
                    reporting year. NOT a defect -- it is the convention decided
                    in `scripts/validate_alias_year_coverage.py` and implemented
                    in `matchlib.pick_by_year` (issue #131): that year's data
                    belongs to the OUTGOING entity. Tiered so a verifier does not
                    "fix" it, and so the few non-alias cases get looked at.
  weak_route        matched by name/tokenset/spelling-alias only -- no iso column
                    agreement and no human-written applied alias behind it.
  precedent         a ranged applied alias names this candidate and covers the
                    whole segment, or (label, candidate) is already banked from
                    another source/segment. The ROUTING rests on a recorded
                    decision, so only territory equality is open.
  thin              <=5 rows or a single distinct year: the evidence bundle's
                    magnitudes cannot support much, and the data at stake is
                    negligible. Cheapest to defer.
  bulk              everything else; order by rows descending.

Outputs (committed snapshots, since `assertions.json` itself is gitignored):
  state/assertion_triage.csv        one row per pending/reopened assertion
  state/assertion_nesting_flags.csv one row per nesting pair, with the areas

NOT a CI gate: its input is derived from a parquet outside the repo, so CI cannot
recompute it. Re-run it after `00_intake.py` whenever the backlog moves.
"""
import argparse
import csv
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")

ap = argparse.ArgumentParser()
ap.add_argument("--assertions", default=os.path.join(STATE, "assertions.json"))
ap.add_argument("--db", default=os.path.join(ROOT, "data/final/polities_database.csv"))
ap.add_argument("--gpkg", default=os.path.join(ROOT, "data/final/polities_database.gpkg"))
ap.add_argument("--aliases", default=os.path.join(STATE, "applied_aliases.csv"))
ap.add_argument("--applied", default=os.path.join(STATE, "verdicts_applied.jsonl"))
ap.add_argument("--out-triage", default=os.path.join(STATE, "assertion_triage.csv"))
ap.add_argument("--out-nesting", default=os.path.join(STATE, "assertion_nesting_flags.csv"))
ap.add_argument("--nest-frac", type=float, default=0.5,
                help="a pair nests when the intersection exceeds this share of the SMALLER polygon")
ap.add_argument("--no-geometry", action="store_true",
                help="skip the nesting screen (no geopandas / no gpkg available)")
ap.add_argument("--layer-b", default=os.path.expanduser(
    "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"),
    help="the panel the assertions were derived from; needed for the inclusion test")
ap.add_argument("--additive-units", default="tonnes,ha,heads,1000 tonnes,1000 hectares,"
                "1000 heads,Bushels,1000 people,Gallons,tons,Tons,hectoliters,1000000 hectares",
                help="units where outer>=inner must hold under inclusion; ratio units "
                     "(kilograms per head, yields) are NOT additive and are excluded")
ap.add_argument("--min-violations", type=int, default=3)
ap.add_argument("--min-violation-frac", type=float, default=0.1)
A = ap.parse_args()

if not os.path.exists(A.assertions):
    sys.exit(f"missing {A.assertions} — run 00_intake.py first (it is gitignored on purpose)")

import pandas as pd  # noqa: E402  (after the arg check, so --help works without it)

bundle = json.load(open(A.assertions))
asserts = bundle["assertions"]
PENDING = ("pending", "reopened")
pend = [x for x in asserts if x["status"] in PENDING]
banked = [x for x in asserts if x["status"] in ("banked", "banked_legacy")]
db = pd.read_csv(A.db).set_index("polity_code")


def span(x):
    y0, y1 = x["years_observed"].split("-")
    return int(y0), int(y1)


# ---- source-internal nesting screen -------------------------------------------
nesting_rows, nested_keys = [], set()
if not A.no_geometry:
    import geopandas as gpd
    from shapely import make_valid

    codes = sorted({x["candidate"] for x in asserts})
    g = gpd.read_file(A.gpkg)
    g = g[g.polity_code.isin(codes) & g.geometry.notna()].set_index("polity_code")
    # make_valid first: several source polygons have self-touching rings and a raw
    # .intersects() raises TopologyException on them.
    g["geometry"] = g.geometry.apply(make_valid)
    ea = g.to_crs("ESRI:54034")            # equal-area, so the share is meaningful
    km2 = ea.area / 1e6

    flat = ea[["geometry"]].reset_index()
    sj = gpd.sjoin(flat, flat, predicate="intersects")
    pairs = {tuple(sorted((a, b)))
             for a, b in zip(sj.polity_code_left, sj.polity_code_right) if a != b}
    nest_frac = {}
    for a, b in pairs:
        try:
            inter = ea.geometry[a].intersection(ea.geometry[b]).area / 1e6
        except Exception:
            continue                        # unrepairable geometry: no claim made
        smaller = min(km2[a], km2[b])
        if smaller and inter / smaller > A.nest_frac:
            nest_frac[(a, b)] = inter / smaller

    by_source = {}
    for x in asserts:
        y0, y1 = span(x)
        by_source.setdefault(x["source"], []).append((x["key"], x["candidate"], y0, y1,
                                                      x["rows"], x["status"]))
    for src, lst in by_source.items():
        for p, q in itertools.combinations(lst, 2):
            if p[1] == q[1] or not (p[2] <= q[3] and q[2] <= p[3]):
                continue                    # same polity, or no year overlap
            f = nest_frac.get(tuple(sorted((p[1], q[1]))))
            if f is None:
                continue
            outer, inner = (p, q) if km2[p[1]] >= km2[q[1]] else (q, p)
            nesting_rows.append(dict(
                source=src, outer_key=outer[0], outer_code=outer[1],
                inner_key=inner[0], inner_code=inner[1],
                overlap_years=f"{max(p[2], q[2])}-{min(p[3], q[3])}",
                inner_share_covered=round(f, 3),
                outer_km2=round(km2[outer[1]]), inner_km2=round(km2[inner[1]]),
                outer_rows=outer[4], inner_rows=inner[4],
                outer_status=outer[5], inner_status=inner[5]))
            for k in (outer[0], inner[0]):
                nested_keys.add(k)

# ---- inclusion test over the panel's own numbers ------------------------------
# An assertion key is "<normalized label>|<source>|<y0>-<y1>", so the label the
# panel carries is recoverable from the key without re-normalizing anything.
exclusion_keys = set()
if nesting_rows and os.path.exists(A.layer_b):
    sys.path.insert(0, HERE)
    from matchlib import eff_year, norm            # same normalization as 00_intake

    panel = pd.read_parquet(A.layer_b, columns=["country", "year", "value", "item",
                                                "unit", "period", "is_aggregate", "source"])
    panel = panel[~panel.is_aggregate.fillna(False)]
    panel = panel[panel.unit.isin({u.strip() for u in A.additive_units.split(",")})]
    panel["lab"] = panel.country.map(norm)
    panel["y"] = [eff_year(a, b) for a, b in zip(panel.year, panel.period)]
    idx = {k: v for k, v in panel.groupby(["lab", "source"])}

    for row in nesting_rows:
        lo, li = row["outer_key"].rsplit("|", 2)[0], row["inner_key"].rsplit("|", 2)[0]
        go, gi = idx.get((lo, row["source"])), idx.get((li, row["source"]))
        row.update(shared_cells=0, cells_outer_lt_inner=0, median_outer_over_inner="",
                   inclusion="no_shared_cells")
        if go is None or gi is None:
            row["inclusion"] = "label_not_in_panel"
            continue
        y0, y1 = (int(v) for v in row["overlap_years"].split("-"))
        m = (go[(go.y >= y0) & (go.y <= y1)]
             .merge(gi[(gi.y >= y0) & (gi.y <= y1)], on=["item", "unit", "y"],
                    suffixes=("_o", "_i")))
        m = m[m.value_o.notna() & m.value_i.notna() & (m.value_i > 0)]
        if m.empty:
            continue
        viol = m.value_o < m.value_i
        row.update(shared_cells=len(m), cells_outer_lt_inner=int(viol.sum()),
                   median_outer_over_inner=round(float((m.value_o / m.value_i).median()), 3))
        if viol.sum() >= A.min_violations and viol.mean() > A.min_violation_frac:
            row["inclusion"] = "impossible_outer_excludes_inner"
            exclusion_keys.update((row["outer_key"], row["inner_key"]))
        elif viol.sum() == 0:
            row["inclusion"] = "consistent_with_inclusion"
        else:
            row["inclusion"] = "few_violations"

# ---- precedent: applied aliases and already-banked (label, candidate) ---------
alias_rules = []
if os.path.exists(A.aliases):
    for r in csv.DictReader(open(A.aliases)):
        alias_rules.append(r)


def alias_precedent(x):
    """A ranged alias row naming this candidate and covering the whole segment."""
    y0, y1 = span(x)
    lab = (x["label_raw"] or "").strip().lower()
    for r in alias_rules:
        if (r.get("source_label") or "").strip().lower() != lab:
            continue
        if (r.get("polity_code") or "").strip() != x["candidate"]:
            continue
        src = (r.get("source") or "").strip().lower()
        if src and src != x["source"]:
            continue
        ys, ye = (r.get("year_start") or "").strip(), (r.get("year_end") or "").strip()
        if not ys or not ye:
            continue                        # blanket rule: no year claim to lean on
        if float(ys) <= y0 and y1 <= float(ye):
            return r.get("confidence") or ""
    return None


banked_lab_cand = {(x["label_raw"], x["candidate"]) for x in banked}

out = []
for x in pend:
    c = x["candidate"]
    d = db.loc[c] if c in db.index else None
    y0, y1 = span(x)
    ap_conf = alias_precedent(x)
    row = dict(
        key=x["key"], label=x["label_raw"], source=x["source"], candidate=c,
        status=x["status"], route="+".join(x["route"]), rows=x["rows"],
        years_observed=x["years_observed"], n_distinct_years=x["n_distinct_years"],
        candidate_period=(None if d is None else f"{int(d.start_year)}-{int(d.end_year)}"),
        polity_type=(None if d is None else d.polity_type),
        wiki_status=(None if d is None else d.wiki_status),
        polygon_status=(None if d is None else d.polygon_status),
        # apply_verdicts downgrades verified_equal to best_available when the only
        # evidence is a draft page; a reviewed page is what makes the stronger
        # confirm reachable without external corroboration.
        verified_equal_reachable=(d is not None and d.wiki_status == "reviewed"),
        nested_reporting=x["key"] in nested_keys,
        inclusion_impossible=x["key"] in exclusion_keys,
        boundary_year=(d is not None and y1 == int(d.end_year)),
        alias_precedent_confidence=(ap_conf or ""),
        banked_precedent=(x["label_raw"], c) in banked_lab_cand,
    )
    if row["inclusion_impossible"]:
        tier = "territory_basis_wrong"
    elif row["nested_reporting"]:
        tier = "nested_reporting"
    elif row["boundary_year"]:
        tier = "boundary_year"
    elif not ({"iso", "applied_alias"} & set(x["route"])):
        tier = "weak_route"
    elif ap_conf or row["banked_precedent"]:
        tier = "precedent"
    elif x["rows"] <= 5 or x["n_distinct_years"] <= 1:
        tier = "thin"
    else:
        tier = "bulk"
    row["tier"] = tier
    out.append(row)

t = pd.DataFrame(out)
TIER_ORDER = ["territory_basis_wrong", "nested_reporting", "boundary_year", "weak_route", "precedent", "thin", "bulk"]
t["tier"] = pd.Categorical(t["tier"], TIER_ORDER, ordered=True)
t = t.sort_values(["tier", "rows"], ascending=[True, False]).reset_index(drop=True)
t.insert(0, "verify_order", t.index + 1)
t.to_csv(A.out_triage, index=False)

if nesting_rows:
    n = pd.DataFrame(nesting_rows).sort_values(["source", "outer_km2", "inner_km2"],
                                               ascending=[True, False, False])
    n.to_csv(A.out_nesting, index=False)

# ---- report -------------------------------------------------------------------
print(f"assertions: {len(asserts)}  pending/reopened: {len(pend)}  banked: {len(banked)}")
print(f"rows behind the backlog: {int(t['rows'].sum()):,} of {bundle['summary']['rows_routed']:,} routed")
print("\ntier                 assertions      rows   reviewed page")
for tier in TIER_ORDER:
    s = t[t.tier == tier]
    if len(s):
        print(f"  {tier:<18} {len(s):>7} {int(s['rows'].sum()):>9} {int(s.verified_equal_reachable.sum()):>7}")
print("\nflags (independent of the tier a row landed in — tiers are first-match):")
for f in ("inclusion_impossible", "nested_reporting", "boundary_year", "banked_precedent"):
    print(f"  {f:<18} {int(t[f].sum()):>7} {int(t.loc[t[f], 'rows'].sum()):>9}")
print(f"  {'alias_precedent':<18} {int((t.alias_precedent_confidence != '').sum()):>7} "
      f"{int(t.loc[t.alias_precedent_confidence != '', 'rows'].sum()):>9}")
print(f"\nverified_equal reachable today (candidate page reviewed): "
      f"{int(t.verified_equal_reachable.sum())} of {len(t)} "
      f"({100 * t.verified_equal_reachable.mean():.1f}%) — for the rest a confirm resting only "
      f"on the draft page is recorded as best_available")
if nesting_rows:
    n = pd.DataFrame(nesting_rows)
    print(f"\nnesting pairs: {len(n)} over {n.outer_code.nunique()} outer / "
          f"{n.inner_code.nunique()} inner polities; "
          f"{len(nested_keys)} assertions implicated, "
          f"{int(t.nested_reporting.sum())} of them pending")
    print(n.source.value_counts().to_string())
    if "inclusion" in n:
        print("\ninclusion test over the panel's own extensive cells:")
        print(n.inclusion.value_counts().to_string())
        bad = n[n.inclusion == "impossible_outer_excludes_inner"]
        if len(bad):
            print("\nSETTLED DETERMINISTICALLY — the source cannot be reporting the outer "
                  "territory inclusive of the inner one, so the OUTER polity's territory "
                  "basis is what needs fixing:")
            already = bad[(bad.outer_status.isin(("banked", "banked_legacy")))
                          | (bad.inner_status.isin(("banked", "banked_legacy")))]
            print(f"  ({len(already)} of these {len(bad)} pairs involve an ALREADY-BANKED "
                  f"assertion — arithmetic contradicts a recorded verdict, so they need "
                  f"re-verification, not first verification)")
            for _, r in bad.sort_values("cells_outer_lt_inner", ascending=False).iterrows():
                print(f"  {r.source:<9} {r.outer_code} ({r.outer_km2:,} km2) vs {r.inner_code} "
                      f"({r.inner_km2:,} km2) {r.overlap_years}: outer < inner in "
                      f"{r.cells_outer_lt_inner}/{r.shared_cells} shared cells")
if os.path.exists(A.applied):
    mix = {}
    for line in open(A.applied):
        v = json.loads(line).get("verdict", {})
        mix[v.get("verdict")] = mix.get(v.get("verdict"), 0) + 1
    tot = sum(mix.values())
    changed = tot - mix.get("confirm", 0)
    print(f"\nprior yield: {tot} applied verdicts, {changed} changed the routing "
          f"({100 * changed / tot:.1f}%) — {mix}")
print(f"\nwrote {A.out_triage}" + (f" and {A.out_nesting}" if nesting_rows else ""))
