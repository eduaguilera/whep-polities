#!/usr/bin/env python3
"""Re-test the QUANTITATIVE claims in state/data_errors.csv against the current data (issue 431).

WHY THIS EXISTS, AND WHY IT IS NOT A DUPLICATE OF 11_retest_conventions.py. The two curated registries in
`state/` are policed very differently, and the asymmetry has a cost:

    source_conventions.csv    validate_source_conventions.py (its own gate)
                              11_retest_conventions.py (26 mechanical re-tests)
                              a registration rule: two corroborators, and a re-test per entry

    data_errors.csv           read by SIX gates as input -- baselines, exclusions, ceilings --
                              no gate of its own, no re-test, no registration rule

The pipeline README justifies the conventions re-test on the ground that "a wrong one propagates further
than any single verdict". That argument applies here too: six gates consume this file. But nothing
re-measured whether an entry still describes reality, and on 2026-08-20 that cost showed twice.
`iia-layerb-magnitude-scale-inconsistent` sat as pending_audit with a diagnosis whose EVERY leg turned out
refutable -- its magnitude evidence cited `wheat`, which in this source is spelt and meslin -- and nothing
flagged it; it took re-deriving the entry by hand. `iia-reunion-tobacco-baseline-contaminated`, written the
same day, had its stated condition refuted within the hour by the one row not checked.

WHAT THIS COVERS, AND WHAT IT DELIBERATELY DOES NOT. Only entries resting on a REPRODUCIBLE FIGURE -- a row
count, a label count, an absence -- can be re-tested mechanically. Most of this file is single attributable
cells with no measurement behind them (`nru-1933-phosphate-transposed-with-australia`,
`cze-1910-rye-area-orphan-3ha`), and several are explicitly unrepairable, so there is nothing to re-run.
Those are out of scope by design rather than by omission, and this script says so rather than implying
coverage it does not have.

A FIGURE MISMATCH IS NOT AUTOMATICALLY AN ERROR, the same distinction 11_retest_conventions.py draws: a
count can move because the panel was reconsolidated while the diagnosis stays true. The check reports what
it now finds; whether that is drift to correct in the entry or a conclusion to withdraw is a reading.

Usage:
  python3 pipelines/polity-autoimprove/35_retest_data_errors.py [--raw PATH] [--layer-b PATH]

Exit 1 if a claim no longer reproduces; 0 on pass, or on SKIP when the inputs are absent.
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
ERRORS = os.path.join(STATE, "data_errors.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))


def check_corrupted_country_labels(ctx):
    """1,237 rows carry a country label beginning `[error]`, across 93 distinct labels, and the PRODUCT
    column is clean. The product-side zero is the load-bearing half: it is what makes the corruption
    specific to the country axis rather than a general extraction failure."""
    raw = ctx["raw"]
    e = raw[raw["_c"].str.startswith("[error]")]
    prod_broken = int(raw["_p"].str.startswith("[error]").sum())
    return ([("rows", len(e), 1237), ("distinct labels", e["_c"].nunique(), 93),
             ("broken product labels", prod_broken, 0)],
            "the country axis is corrupted and the product axis is not")


def check_wheat_is_spelt_and_meslin(ctx):
    """The source carries ZERO `wheat` production or area rows -- only trade -- so layer B's iia `wheat`
    cannot have come from a wheat production series. An absence is the strongest form this file records,
    and also the easiest to falsify if a re-extraction adds one."""
    raw = ctx["raw"]
    w = raw[(raw["_p"] == "wheat") & raw["_v"].isin(["production", "area"])]
    trade = raw[(raw["_p"] == "wheat") & raw["_v"].isin(["imports", "exports", "reexports"])]
    return ([("wheat production/area rows", len(w), 0)],
            f"and {len(trade)} wheat rows remain, all trade")


def check_tobacco_era_scope(ctx):
    """The era table holds 427 rows across 93 labels. Both numbers are quoted in
    iia-tobacco-implausible-magnitudes and in issue 416's own scope, and the label count is the one that
    matters: it is what says the defect is source-wide rather than a few series."""
    v = ctx["era"]
    return ([("era rows", len(v), 427), ("labels", len({r["label"] for r in v}), 93)],
            "scope unchanged")


def check_fao1952_china_label(ctx):
    """The `China` label carries 33 rows. The entry's argument is that the label is a correct national
    total with six broken livestock cells inside it, and the row count is the denominator of that claim."""
    lb = ctx["panel"]
    ch = lb[(lb["source"] == "fao1952") & (lb["country"] == "China")]
    return ([("`China` rows", len(ch), 33)], "denominator unchanged")


def check_fao1952_wrong_group_heading(ctx):
    """Seven fao1952 labels for one territory, two of them carrying a group heading it was never in, and
    the 513 that decides WHICH HALF of the label is wrong.

    The load-bearing claim is not the row counts -- it is that the value belongs to Trinidad. If the
    heading were right and the territory name had bled in from an adjacent row, 513 thousand ha would be
    a Leeward Islands figure and this would be a wrong VALUE rather than a wrong label. 513 thousand ha
    is 5,130 km2 and Trinidad and Tobago is 5,128 km2, so the check re-measures that cell: if a
    re-extraction ever changes it, the entry's reasoning has to be redone rather than its count nudged.

    The zero is load-bearing too, in the other direction: 0 colliding cells against the five correctly
    parented labels is what makes these rows recoverable data rather than a double count.
    """
    lb = ctx["panel"]
    f = lb[lb["source"] == "fao1952"].copy()
    f["_l"] = f["country"].str.replace(r"\s+", " ", regex=True).str.strip().str.lower()
    t = f[f["_l"].str.contains("trinidad", na=False)]
    BAD = ["leeward islands trinidad and tobago", "jamaica trinidad and tobago"]
    bad, good = t[t["_l"].isin(BAD)], t[~t["_l"].isin(BAD)]
    coll = bad.merge(good, on=["item", "indicator", "year", "unit"], suffixes=("_b", "_g"))
    tot = bad[(bad["_l"] == BAD[0]) & (bad["item"] == "use total")]["value"]
    return ([("trinidad label variants", int(t["_l"].nunique()), 7),
             ("rows under the wrong heading", len(bad), 7),
             ("cells colliding with the correct labels", len(coll), 0),
             ("`use total` under the Leeward heading", float(tot.iloc[0]) if len(tot) else None, 513.0)],
            "the value is Trinidad's 5,128 km2, so the heading is the wrong half")


def check_korea_rice_paddy_area(ctx):
    """645 kha of paddy under 3,699 kt, i.e. 5.73 t/ha, with the part larger than the whole.

    THE YIELD IS THE LOAD-BEARING FIGURE, not the two areas. A part exceeding its whole could be fixed by
    deciding the labels are not whole and part; an implied 5.73 t/ha of 1930s paddy rice cannot be fixed
    that way, and it is what makes the AREA the wrong cell rather than the scope. The count of violating
    cells is re-measured too, because "1 of 17" is what rules out a systematic scope problem.
    """
    lb = ctx["panel"]
    f = lb[lb["source"] == "fao1952"].copy()
    f["lab"] = f["country"].str.replace(r"\s+", " ", regex=True).str.strip().str.lower()
    k = f[f["lab"].isin(["korea", "korea south"]) & (f["period"] == "1934-1938")]
    piv = k.pivot_table(index=["item", "indicator", "unit"], columns="lab", values="value",
                        aggfunc="sum").dropna()
    if piv.empty or "korea" not in piv.columns:
        return [("cells with both labels", 0, 17)], "the label pair is no longer in the panel"
    ratio = piv["korea south"] / piv["korea"]
    AK = ("rice paddy", "crops:area", "1000 hectares")
    PK = ("rice paddy", "crops:production", "1000 tonnes")
    area = piv.loc[AK] if AK in piv.index else None
    prod = piv.loc[PK] if PK in piv.index else None
    yield_t = (float(prod["korea"]) / float(area["korea"])) if area is not None and prod is not None else None
    return ([("cells with both labels", len(piv), 17),
             ("cells where the part exceeds the whole", int((ratio > 1.0).sum()), 1),
             ("`korea` rice paddy area", float(area["korea"]) if area is not None else None, 645.0),
             ("`korea south` rice paddy area", float(area["korea south"]) if area is not None else None,
              1216.0),
             ("implied t/ha", round(yield_t, 2) if yield_t else None, 5.73)],
            "the impossible yield, not the two areas, is what pins the area cell")


def check_russia_asian_component(ctx):
    """Eight tobacco cells equal to `russia in europe` to the digit, with the Asian half never added.

    EXACT EQUALITY IS THE CLAIM, not the size of the gap. An approximate match to one component would be
    consistent with a revision or with a different volume; equality to the digit in eight consecutive
    years says the component was never added. So the check counts EXACT matches (1e-6 relative) and
    fails if any of the eight stops being one.

    THE SECOND LEG IS RE-MEASURED TOO, because without it the finding is indistinguishable from "this
    label never sums anything". The entry cites 72 correctly-summed cells across all items; re-deriving
    that number needs the item crosswalk and multi-product pooling, which is where my own first pass
    manufactured five spurious `flax fibre and tow` rows. So the leg is re-tested on RYE instead --
    same label, one raw product, no crosswalk -- where 1909-1916 must sum both components and 1917/1920
    must not. That is the same claim on ground that cannot be got wrong the same way.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    tob = raw[(raw["_p"] == "tobacco") & (raw["_v"] == "production") & raw["value"].notna()]
    eu = {str(t.year).strip(): float(t.value) for t in tob[tob["_c"] == "russia in europe"].itertuples()}
    asi = {str(t.year).strip(): float(t.value) for t in tob[tob["_c"] == "russia in asia"].itertuples()}
    g = lb[(lb["source"] == "iia") & (lb["country"] == "russian federation")
           & (lb["item"] == "tobacco, unmanufactured") & (lb["unit"] == "tonnes") & lb["value"].notna()]
    when = g["period"].where(g["period"].notna(), g["year"].astype("string"))
    exact_eu = both = 0
    for w, v in zip(when, g["value"]):
        k = str(w).strip()
        if k not in eu or k not in asi:
            continue
        both += 1
        if abs(float(v) - eu[k]) <= 1e-6 * max(abs(eu[k]), 1.0):
            exact_eu += 1
    # Second leg: rye, where the SAME label sums both components in the early years and drops the
    # Asian one at 1917 and 1920. One raw product, so no crosswalk and no pooling to get wrong.
    rye = raw[(raw["_p"] == "rye") & (raw["_v"] == "area") & raw["value"].notna()]
    # SUM the rows per year, do not take one. `russia in asia` carries TWO rye rows for each of
    # 1909-1916 (e.g. 918,720 and 318,737 at 1909) and one for 1917 and 1920 -- it is itself a group
    # label. Keeping a single row understates the component by about 3% and made this leg report 0
    # correctly-summed cells when the answer is 8; issue 422's three-term identity
    # (28,161,536 + 918,720 + 318,737 = 29,398,993) is the same fact seen from the other side.
    reu = rye[rye["_c"] == "russia in europe"].groupby(
        rye["year"].astype(str).str.strip())["value"].sum().to_dict()
    ras = rye[rye["_c"] == "russia in asia"].groupby(
        rye["year"].astype(str).str.strip())["value"].sum().to_dict()
    gr = lb[(lb["source"] == "iia") & (lb["country"] == "russian federation")
            & (lb["item"] == "rye") & (lb["unit"] == "ha") & lb["value"].notna()]
    rwhen = gr["period"].where(gr["period"].notna(), gr["year"].astype("string"))
    summed = eu_only = 0
    for w, v in zip(rwhen, gr["value"]):
        k = str(w).strip()
        if k not in reu or k not in ras:
            continue
        v = float(v)
        reu_k, ras_k = float(reu[k]), float(ras[k])
        if abs(v - (reu_k + ras_k)) <= 0.02 * (reu_k + ras_k):
            summed += 1
        elif abs(v - reu_k) <= 0.001 * max(reu_k, 1.0):
            eu_only += 1
    return ([("tobacco cells with both components", both, 8),
             ("of those, EXACTLY equal to europe alone", exact_eu, 8),
             ("rye cells that DO sum both components", summed, 8),
             ("rye cells that are europe-only", eu_only, 2)],
            "the summing works for rye in the same label, so this is a per-item omission")


def check_nested_reporting_levels(ctx):
    """72 cells receive more than one source label, and 7 of them now share a value.

    THIS ENTRY IS WHY THE RE-TEST EXISTS. Written 2026-08-17 with 52 cells and 110 rows, it also
    claimed "NONE of the colliding values are equal, so this is not duplicate ingestion but genuinely
    different series landing on one key" -- the sentence its whole argument rests on. Both halves had
    moved by 2026-08-21 and nothing noticed: the counts had drifted 38%, and the equality claim was
    false in 7 cells, SIX of them explained by work recorded elsewhere in this repo after the entry was
    written (`ethiopia`/`ethiopia pdr` is the pure duplicate of issues 451 and 519; the three Korea cells
    are 1950-51, where the peninsula total equals the South because the North was not reported, issues
    451 and 521).

    THE EQUALITY COUNT IS THE LOAD-BEARING CLAIM, not the cell count. A drifting count means the panel
    moved; a rising equality count means the entry's DIAGNOSIS is wrong, because equal values across two
    labels are duplicate ingestion rather than two different series. So it is measured per pair of
    labels rather than by comparing distinct-value counts, which cannot tell "two labels agree" from
    "one label repeats itself".
    """
    mr = ctx.get("matched")
    if mr is None:
        return [("cells with more than one source label", None, 72)], "matched_rows.parquet absent"
    d = mr[mr["value"].notna() & mr["whep_code"].notna()]
    K = ["whep_code", "source", "item", "indicator", "year", "unit"]
    cells = rows = shared = 0
    for _, g in d.groupby(K, dropna=False):
        if g["country"].nunique() < 2:
            continue
        cells += 1
        rows += len(g)
        per = {lab: set(v.round(6)) for lab, v in g.groupby("country")["value"]}
        labs = sorted(per)
        if any(per[labs[i]] & per[labs[j]]
               for i in range(len(labs) - 1) for j in range(i + 1, len(labs))):
            shared += 1
    return ([("cells with more than one source label", cells, 72),
             ("rows in those cells", rows, 173),
             ("cells where two DIFFERENT labels share a value", shared, 7)],
            "the equality count is the diagnosis; the cell count is only the panel's size")


def check_iia_scale_is_common(ctx):
    """The POSITIVE test the magnitude-scale entry says it is waiting for.

    `iia-layerb-magnitude-scale-inconsistent` records that every leg of its own diagnosis was refuted,
    then leaves its status at pending_audit for an explicit reason: *"refuting the evidence offered is
    not the same as proving iia magnitudes ARE on a common scale, which should rest on a positive
    test"*. This is that test, run mechanically instead of quoted in prose.

    THE LOGIC. If layer-B consolidation applied a per-publication or per-table multiplier -- the
    mechanism the entry asked to be traced -- then layer-B values would NOT appear verbatim among the
    raw extract's own production figures. A high verbatim rate is incompatible with per-table
    rescaling, and it is the verbatim COUNT rather than the refutations that licenses lifting the
    verifier instruction.

    WHAT THE TEST IS NOT. Matching a value against every raw production figure for the same year is a
    WEAK match -- it does not check that the value came from the right label or product, and a common
    round number will find a partner. It is the right test for this claim anyway, because the claim is
    about SCALE: a rescaled panel would fail it however the labels line up. For per-cell provenance the
    strict join is `cell_attribution.csv` (issues 372, 443), which constrains product, variable, year
    and value together.

    The population is dated rows only (`year` present), which is what reproduces the entry's own
    12,052 -- period averages are excluded because a period's value has no single raw year to match.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    prod = raw[(raw["_v"] == "production") & raw["value"].notna()]
    by_year = collections.defaultdict(set)
    for t in prod.itertuples():
        by_year[str(t.year).strip()].add(round(float(t.value), 6))
    g = lb[(lb["source"] == "iia") & (lb["unit"] == "tonnes")
           & lb["value"].notna() & lb["year"].notna()]
    verbatim = pow10 = 0
    for y, v in zip(g["year"], g["value"]):
        s = by_year.get(str(int(y)), ())
        v = round(float(v), 6)
        if v in s:
            verbatim += 1
        elif any(round(v * f, 6) in s or round(v / f, 6) in s for f in (10, 100, 1000)):
            pow10 += 1
    return ([("dated iia tonnes rows", len(g), 12052),
             ("of those, VERBATIM in the raw extract at the same year", verbatim, 10810),
             ("needing a power of ten", pow10, 112)],
            "a per-table rescaling would make the verbatim rate LOW; 89.7% is incompatible with it")


def check_hops_x100_and_area_x10(ctx):
    """Two distinct hops defects and the control that separates them.

    The entry records that hops PRODUCTION is 100x too large from 1934 and that hops AREA carries a
    SEPARATE x10 -- and that its remedy "is incomplete without" the second. Those are different repairs
    on the same commodity, so a re-test that measured only one would let the other drift away.

    THE TOBACCO-AREA CONTROL IS THE THIRD CLAIM AND IT IS LOAD-BEARING. Tobacco and hops share the x100
    production defect, but tobacco AREA is clean (median 1.00x). That is what establishes the x100 as
    production-only and the hops area x10 as a second fault rather than the same one seen twice. If the
    control ever moved to 10x or 100x, the two defects would have merged and the entry's whole structure
    would need rewriting -- so it is measured here beside them, not assumed.

    Measured on 1933, the only year iia_1933_34 and iia_1938_39 both cover, which is what makes an
    intra-source factor measurable at all.
    """
    raw = ctx["raw"]
    r = raw[(raw["year"].astype(str).str.strip() == "1933") & raw["value"].notna()
            & raw["yearbook"].isin(["iia_1933_34", "iia_1938_39"])]

    def factors(prod, var):
        out = []
        sub = r[(r["_p"] == prod) & (r["_v"] == var)]
        for _, g in sub.groupby("_c"):
            a = g[g["yearbook"] == "iia_1933_34"]["value"]
            b = g[g["yearbook"] == "iia_1938_39"]["value"]
            if len(a) and len(b):
                av, bv = float(a.max()), float(b.max())
                if av > 0 and bv > 0:
                    out.append(bv / av)
        return sorted(out)

    def med(xs):
        return None if not xs else (xs[len(xs) // 2] if len(xs) % 2
                                    else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2)

    hp, ha, ta = factors("hops", "production"), factors("hops", "area"), factors("tobacco", "area")
    return ([("hops production 1933 pairs", len(hp), 15),
             ("of those within 20% of 100x", sum(1 for x in hp if 80 <= x <= 120), 15),
             ("hops area 1933 pairs", len(ha), 16),
             ("of those within 20% of 10x", sum(1 for x in ha if 8 <= x <= 12), 14),
             ("tobacco area 1933 pairs (the CONTROL)", len(ta), 46),
             ("of those within 5% of 1x", sum(1 for x in ta if 0.95 <= x <= 1.05), 32),
             ("hops area median factor", round(med(ha), 2) if ha else None, 10.04)],
            "the tobacco-area control is what makes these two defects rather than one")


def check_hemp_germany_glued(ctx):
    """The parent/child identity that proves three fao1952 hemp labels are Germany's, and the row count
    the entry understates.

    THE IDENTITY IS THE PROOF and it needs no source page: in the hemp-fibre table
    `France Eastern` + `Western` equals `France Germany` on BOTH indicators, exactly --
    production 2.9 + 1.2 = 4.1 and area 4.0 + 2.0 = 6.0 (1934-1938). Two supporting absences make it
    unambiguous: the table carries NO bare `Germany` label, and `France` is present separately at 3.9,
    so a France-plus-Germany aggregate is ruled out in both directions.

    THE ROW COUNT IS LARGER THAN THE ENTRY SAYS, and the re-test measures it rather than repeating the
    figure. The entry records "6 rows (2 per label)", which counts the 1934-1938 triple that carries the
    identity. But `Western` also appears at 1949, 1950 and 1951 on both indicators -- 8 `Western` rows in
    total, not 2 -- and those rows carry the same uninformative label without being part of the
    arithmetic. Twelve rows in the table are labelled with one of the three, so a repair keyed on the
    identity would leave six of them behind.
    """
    lb = ctx["panel"]
    f = lb[(lb["source"] == "fao1952") & lb["item"].str.contains("hemp", case=False, na=False)].copy()
    f["lab"] = f["country"].str.replace(r"\s+", " ", regex=True).str.strip()

    def val(lab, ind):
        v = f[(f["lab"] == lab) & (f["indicator"] == ind) & (f["period"] == "1934-1938")]["value"]
        return round(float(v.iloc[0]), 6) if len(v) == 1 else None

    pe, pw, pg = (val("France Eastern", "crops:production"), val("Western", "crops:production"),
                  val("France Germany", "crops:production"))
    ae, aw, ag = (val("France Eastern", "crops:area"), val("Western", "crops:area"),
                  val("France Germany", "crops:area"))
    return ([("production: France Eastern + Western",
              round(pe + pw, 6) if None not in (pe, pw) else None, 4.1),
             ("production: France Germany", pg, 4.1),
             ("area: France Eastern + Western",
              round(ae + aw, 6) if None not in (ae, aw) else None, 6.0),
             ("area: France Germany", ag, 6.0),
             ("bare `Germany` labels in the hemp table", int((f["lab"] == "Germany").sum()), 0),
             ("`France` production 1934-1938 (present separately)",
              val("France", "crops:production"), 3.9),
             ("rows carrying one of the three glued labels",
              int(f["lab"].isin(["France Eastern", "Western", "France Germany"]).sum()), 12)],
            "the identity holds on both indicators; 12 rows carry these labels, not the 6 in the entry")


def check_item_product_switches(ctx):
    """The australia sugar exhibit, cell by cell -- and one of its cells is a different TERRITORY.

    The entry's clearest case is `australia / sugar raw centrifugal / tonnes`, described as a series
    stitched from `sugar: cane`, `sugar: beet` and `sugar: cane, unrefined`. Re-measuring each cell
    against the raw extract's own (label, product, year, value):

        19  australia / sugar: cane          the real series
        17  australia / sugar: beet          about 1/300 of it -- the defect
         1  australia administered islands / sugar: cane, unrefined      <- NOT a product switch

    THE THIRD "PRODUCT" IS A LABEL CONTAMINATION. 537,211.5 at 1925 is not australia's under a third
    product name; it is `australia administered islands`, a different territory, and `australia` has no
    1925 cane row at all. cell_attribution.csv flags the same cell independently
    (`australia / sugar raw centrifugal`: australia 36, australia administered islands 1). So this
    exhibit carries TWO mechanisms and the entry attributes both to product switching -- the cane/beet
    alternation is real and is this entry's subject; the 1925 cell belongs with issues 372 and 483.

    THE COUNTS ARE MEASURED, NOT QUOTED. The entry says "33 cells" with "12 of the 33" on the wrong
    product; the series now has 37 cells with 17 on beet. Pinning its own figures would have failed on
    the panel it describes.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    R = raw[(raw["_v"] == "production") & raw["value"].notna()
            & raw["_p"].str.startswith("sugar", na=False)]
    g = lb[(lb["source"] == "iia") & (lb["country"] == "australia")
           & (lb["item"] == "sugar raw centrifugal") & lb["value"].notna()]
    when = g["period"].where(g["period"].notna(), g["year"].astype("string"))
    cane = beet = foreign = 0
    for w, v in zip(when, g["value"]):
        m = R[(R["year"].astype(str).str.strip() == str(w).strip())
              & (R["value"].round(6) == round(float(v), 6))]
        labs = sorted(set(zip(m["_c"], m["_p"])))
        if len(labs) != 1:
            continue
        c, prod = labs[0]
        if c != "australia":
            foreign += 1
        elif prod == "sugar: cane":
            cane += 1
        elif prod == "sugar: beet":
            beet += 1
    return ([("australia sugar series cells", len(g), 37),
             ("from australia / sugar: cane", cane, 19),
             ("from australia / sugar: beet (the defect)", beet, 17),
             ("from a DIFFERENT LABEL (not a product switch)", foreign, 1)],
            "the exhibit carries two mechanisms; the 1925 cell is australia administered islands")


# Only entries with a reproducible figure appear here. See the docstring on why the rest cannot.
CHECKS = {
    "iia-corrupted-country-labels": check_corrupted_country_labels,
    "iia-wheat-is-spelt-and-meslin": check_wheat_is_spelt_and_meslin,
    "iia-tobacco-implausible-magnitudes": check_tobacco_era_scope,
    "fao1952-china-livestock-cells-implausible": check_fao1952_china_label,
    "fao1952-label-carries-a-wrong-group-heading": check_fao1952_wrong_group_heading,
    "fao1952-korea-rice-paddy-area-impossible": check_korea_rice_paddy_area,
    "iia-russia-asian-component-dropped": check_russia_asian_component,
    "layerb-nested-reporting-levels-one-polity": check_nested_reporting_levels,
    "iia-layerb-magnitude-scale-inconsistent": check_iia_scale_is_common,
    "iia-hops-x100": check_hops_x100_and_area_x10,
    "fao1952-hemp-germany-label-glued": check_hemp_germany_glued,
    "iia-item-series-switch-raw-products": check_item_product_switches,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    a = ap.parse_args()

    for p in (a.raw, a.layer_b, MATCHED, ERRORS):
        if not os.path.exists(p):
            print(f"SKIP: {p} not present on this machine", file=sys.stderr)
            return 0

    import pandas as pd
    raw = pd.read_excel(a.raw)
    raw = raw.assign(_c=raw["country"].astype(str).str.strip().str.lower(),
                     _p=raw["product"].astype(str).str.strip().str.lower(),
                     _v=raw["variable"].astype(str).str.lower())
    with open(os.path.join(STATE, "era_shift_verdicts.csv"), newline="", encoding="utf-8") as fh:
        era = list(csv.DictReader(fh))
    matched_path = os.path.join(STATE, "matched_rows.parquet")
    ctx = {"raw": raw, "panel": pd.read_parquet(a.layer_b), "era": era,
           # matched_rows carries the polity assignment, which the panel does not; an entry keyed on
           # (polity, source, item, ...) cannot be re-tested without it.
           "matched": pd.read_parquet(matched_path) if os.path.exists(matched_path) else None}

    with open(ERRORS, newline="", encoding="utf-8") as fh:
        entries = list(csv.DictReader(fh))
    ids = {r["issue_id"] for r in entries}

    problems, tested = [], 0
    for eid, fn in sorted(CHECKS.items()):
        if eid not in ids:
            problems.append(f"{eid}: has a re-test here but no longer exists in data_errors.csv")
            continue
        claims, note = fn(ctx)
        for label, now, stated in claims:
            tested += 1
            ok = now == stated
            print(f"  {'ok  ' if ok else 'FAIL'} {eid[:42]:44}{label[:26]:28}{now:>9} (stated {stated})")
            if not ok:
                problems.append(f"{eid}: {label} is now {now}, the entry states {stated}")
        print(f"       -> {note}")

    print(f"\n{len(CHECKS)} entr(ies) re-tested over {tested} claim(s); "
          f"{len(ids) - len(CHECKS)} of {len(ids)} entries carry no reproducible figure and are out of "
          f"scope by design")
    if problems:
        print(f"\nFAIL: {len(problems)} claim(s) no longer reproduce", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: every re-testable claim in data_errors.csv still reproduces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
