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

WHAT THIS COVERS, AND A CLAIM IT USED TO MAKE THAT WAS WRONG. Only entries resting on a REPRODUCIBLE
FIGURE -- a row count, a label count, an absence -- can be re-tested mechanically. This docstring used to
say that most of the file was "single attributable cells with no measurement behind them", and named
`nru-1933-phosphate-transposed-with-australia` and `cze-1910-rye-area-orphan-3ha` as its examples. Both are
now re-tested, which refutes the claim: A SINGLE CELL IS A REPRODUCIBLE FIGURE. Its value is printed in the
source, and for a transposition or a wrong-volume pick the SET of cells carrying the argument is pinnable
too -- all four raw cells of the Nauru swap, both volumes of the Lithuania pick.

So the uncovered entries were UNREACHED, not out of scope, and saying "by design" made a gap look like a
boundary. What genuinely cannot be re-tested here is narrower: an entry whose evidence is a judgement about
an external source (whether a yearbook page means one thing or another), or a remedy nobody has chosen. The
count below reports what is covered and does not claim the remainder is uncoverable.

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
import pandas as pd
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
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    # ONE PANEL, EITHER SPELLING (issue 629). Two names were in use -- WHEP_LAYERB in
    # 01_match_and_findings.py and extdata.py, WHEP_LAYER_B in the other 17 tools -- so
    # neither redirected the whole pipeline and setting one left stage 01 matching against
    # a different panel than the analysis stages measured.
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")


def _corrupted_label_merge_claims(ctx):
    """The corruption is ADJACENT-CELL MERGING, and 43 of the 93 labels show it outright.

    Decomposing each broken label into the French tokens it contains -- territory names, the six
    section headings, the column headings -- separates a label that absorbed its neighbour from one
    that is merely truncated. `asie ceylan` is a section heading plus a country row; `commerce avec
    formose` is a column heading plus a country row; `aden: birmanie` is two country rows.

    THIS IS PINNED BY COUNT AND NOT BY LABEL LIST, deliberately. The decomposition is token matching
    against a hand-built vocabulary, so it is a reading rather than a parse: a short token can sit
    inside a longer word, and the unrecognised group may simply use tokens the list omits. What the
    entry's argument rests on is the SHAPE of the distribution -- that a large minority are visibly
    two labels joined -- and that survives individual mis-classifications in a way a label list would
    not.

    The six-way split must also still partition the 93, which is what stops a class being silently
    added or dropped."""
    import re as _re
    raw = ctx["raw"]
    labs = sorted(set(raw[raw["_c"].str.startswith("[error]")]["_c"]))
    TERR = ["inde", "cameroun", "syrie", "liban", "togo", "palestine", "afrique du sud", "papouasie",
            "nouvelle-guinee", "honduras", "borneo", "malais", "erythree", "somalie", "mozambique",
            "russi", "suisse", "sttisse", "tchecoslovaquie", "tehecoslovaquie", "bresil",
            "etats-unis", "etais-unis", "japon", "turquie", "senegal", "porto-rico", "guadeloupe",
            "trinite", "ceylan", "birmanie", "aden", "formose", "coree", "hawai", "alaska",
            "grande-bretagne", "canada", "costa-rica", "miquelon", "eustache", "martin", "reunion",
            "nyassaland", "congo", "guinee", "christmas", "tabago", "irlande"]
    SECT = ["asie", "afrique", "oceanie", "amerique", "europe", "continent"]
    COL = ["commerce", "commavec", "comm avec", "exportations", "importations", "douanes",
           "par terre", "culture", "cocons", "possessions", "protectorat", "republique",
           "avec les", "y compris"]

    def kind(lab):
        s = lab.replace("[error]", "").strip()
        t = [x for x in TERR if x in s]
        sec = [x for x in SECT if x in s]
        col = [x for x in COL if x in s]
        if t and sec:
            return "terr+section"
        if t and col:
            return "terr+column"
        if len(t) >= 2:
            return "two territories"
        if len(t) == 1:
            return "one territory"
        if sec or col:
            return "header text only"
        return "unrecognised"

    k = collections.Counter(kind(x) for x in labs)
    merged = k["terr+section"] + k["terr+column"] + k["two territories"]
    return [("labels visibly merging TWO cells", merged, 43),
            ("  territory + section heading", k["terr+section"], 19),
            ("  territory + column heading", k["terr+column"], 12),
            ("  two territories", k["two territories"], 12),
            ("labels naming one territory only", k["one territory"], 22),
            ("labels that are header text only", k["header text only"], 21),
            ("unrecognised", k["unrecognised"], 7),
            ("the six kinds partition the 93", sum(k.values()), 93)]


def _corrupted_label_class_claims(ctx):
    """The 93 broken labels split three ways, and the split is what makes the exposure actionable.

    THE LANGUAGE MISMATCH IS PINNED FIRST because it explains every failed identification route in
    this entry: the broken labels are French and the clean ones English, so stripping the prefix and
    looking for a clean twin yields ZERO exact matches out of 93. If that ever became non-zero the
    extract's label vocabulary has changed and the class needs re-deriving, not re-counting.

    The three classes are pinned by ROW COUNT rather than by label list, because the regexes below are
    a reading of the text and a future re-extraction may spell a label differently; the counts are what
    the entry's argument rests on. Only the first class is recoverable data -- the second is column
    headings that landed in the country field, and the third is continents, which belong out of the
    panel the way fao1952's `Total` does."""
    import re as _re
    raw = ctx["raw"]
    e = raw[raw["_c"].str.startswith("[error]")]
    clean = {c for c in set(raw["_c"]) if not c.startswith("[error]")}
    exact = sum(1 for lab in set(e["_c"]) if lab.replace("[error]", "").strip() in clean)
    STRUCT = _re.compile(r"commerce avec|comm avec|commavec|^\[error\]\s*par terre|exportations|"
                         r"importations|culture des|culture associee|cocons|douanes|"
                         r"^\[error\]\s*protectorat$|^\[error\]\s*republique$|"
                         r"^\[error\]\s*continent$|^\[error\]\s*avec les|y compris|signable|"
                         r"possessions exterieur", _re.I)
    CONT = _re.compile(r"^\[error\]\s*(asie|afrique|oceanie|amerique|europe)\b|"
                       r"amerique du nord|amerique septentrionale", _re.I)
    COUNTRY = _re.compile(r"inde|cameroun|syrie|liban|togo|palestine|afrique du sud|afr du sud|"
                          r"occidentale francaise|occident francaise|papouasie|nouvelle-guinee|"
                          r"honduras|borneo|malais|erythree|somalie|mozamb|russic|suisse|sttisse|"
                          r"tchecoslovaquie|tehecoslovaquie|bresil|etats-unis|etais-unis|japon|"
                          r"turquie|senegal|porto-rico|guadeloupe|trinite|ceylan|birmanie|aden|"
                          r"formose|coree|hawai|alaska|indes|grande-bretagne|canada|costa-rica|"
                          r"miquelon|eustache|martin|reunion|nyassaland|congo|guinee|christmas",
                          _re.I)

    def cls(lab):
        if STRUCT.search(lab):
            return "struct"
        if CONT.search(lab):
            return "continent"
        if COUNTRY.search(lab):
            return "country"
        return "other"

    k = e["_c"].map(cls)
    pa = e["_v"].isin(["production", "area"])
    out = [("broken labels with an EXACT clean twin -- the language gap", exact, 0)]
    for name, want_rows, want_pa in (("country", 904, 610), ("struct", 227, 34),
                                     ("continent", 70, 7), ("other", 36, 18)):
        out.append((f"  {name} rows", int((k == name).sum()), want_rows))
        out.append((f"    of those production/area", int(((k == name) & pa).sum()), want_pa))
    out.append(("the four classes partition the 1,237", int(k.notna().sum()), 1237))
    return out


def check_corrupted_country_labels(ctx):
    """1,237 rows carry a country label beginning `[error]`, across 93 distinct labels, and the PRODUCT
    column is clean. The product-side zero is the load-bearing half: it is what makes the corruption
    specific to the country axis rather than a general extraction failure."""
    raw = ctx["raw"]
    e = raw[raw["_c"].str.startswith("[error]")]
    prod_broken = int(raw["_p"].str.startswith("[error]").sum())
    return ([("rows", len(e), 1237), ("distinct labels", e["_c"].nunique(), 93),
             ("broken product labels", prod_broken, 0)]
            + _corrupted_labels_split_claims(ctx)
            + _corrupted_label_class_claims(ctx)
            + _corrupted_label_merge_claims(ctx),
            "one extraction bug -- adjacent cells merged -- seen on three surfaces")


def _corrupted_labels_split_claims(ctx):
    """The class's variable split, and the 102 undated production-side rows the published exposure
    omits.

    Issue 493 reports the split as `production/area 573, trade 521, other 143`. Those three do not
    partition the class by `variable`: 573 is the DATED production/area count, the trade figure is an
    all-rows count, and "other" is the arithmetic remainder, so it absorbs 96 undated production/area
    rows while its parenthetical describes only the 45 rows whose variable really is something else.
    The load-bearing assertion here is the PARTITION, which is what makes a residual class impossible
    to reintroduce: the three variable groups must sum to the class exactly.

    The omission matters because the undated rows are not junk -- every one carries a quinquennial
    period string (`1928-1932`, `1934-1938`), so they are period averages, and 75 of the 102 sit in the
    five legible blocks that are the recovery candidates.

    The entry's 503 recoverable cells and the issue's ~509 exposure are NOT the same population and
    neither is a subset error: 503 counts complementary production-side ROWS and includes 75 undated
    period rows; 509 counts DATED fingerprint cells clearing a distinctness floor. Two figures three
    apart, measuring different things, is exactly the shape that invites a false reconciliation."""
    import pandas as pd
    raw = ctx["raw"]
    e = raw[raw["_c"].str.startswith("[error]") & raw["value"].notna()].copy()
    # trailing underscore: itertuples renames a leading-underscore column to a positional alias
    e["y_"] = pd.to_numeric(e["year"], errors="coerce")
    PA = {"area", "production"}
    TRADE = {"imports", "exports", "reexports", "consumption"}
    pa = e[e["_v"].isin(PA)]
    tr = e[e["_v"].isin(TRADE)]
    oth = e[~e["_v"].isin(PA | TRADE)]
    # the wider production side: the four legible blocks' published sizes include `bearing area`
    WIDE = PA | {"bearing area", "planted area", "dry production",
                 "production of cocoons", "laying hens"}
    und = e[e["_v"].isin(WIDE) & e["y_"].isna()]
    legible = ("inde", "togo", "cameroun", "syrie", "palestine")
    und_leg = und[und["_c"].str.contains("|".join(legible))]
    pal = e[e["_c"].str.contains("palestine")]
    pal_pa = pal[pal["_v"].isin(PA)]
    pal_wide = pal[pal["_v"].isin(WIDE)]
    five = len(e[e["_c"].str.contains("|".join(legible)) & e["_v"].isin(WIDE)])
    with_period = int(und["year"].astype(str).str.contains("-").sum())
    return [("area+production rows", len(pa), 669),
             ("  of those, dated", int(pa["y_"].notna().sum()), 573),
             ("  of those, undated", int(pa["y_"].isna().sum()), 96),
             ("trade rows", len(tr), 523),
             ("genuinely-other rows", len(oth), 45),
             ("the three partition the class", len(pa) + len(tr) + len(oth), len(e)),
             ("undated production-side rows", len(und), 102),
             ("  each carrying a period", with_period, 102),
             ("  in the five legible blocks", len(und_leg), 75),
             # The entry states palestine as both 10 and 12 cells. Both are right: 10 on
             # area+production, 12 once `bearing area` is included. The recoverable set uses the
             # wider filter throughout, so 12 is the figure consistent with its 503 total.
             ("palestine, area+production", len(pal_pa), 10),
             ("palestine, production-side", len(pal_wide), 12),
             ("five blocks, production-side", five, 529),
             ("  less inde's 26 duplicates", five - 26, 503)]


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
    """The era table holds 427 rows across 93 labels, and the entry's own 40-of-607 is DATED-ONLY.

    The first two numbers are quoted in iia-tobacco-implausible-magnitudes and in issue 416's own
    scope, and the label count is the one that matters: it is what says the defect is source-wide
    rather than a few series.

    THE REST OF THIS CHECK GUARDS THE ENTRY'S SCOPE, which was wrong in a way no count could reveal.
    607 is exactly the number of iia tobacco rows in tonnes that carry a `year`; layer B holds 893, so
    286 rows with a `period` and a null `year` were outside every figure the entry recorded. The
    period rows are not a rounding error on the class -- they add 73 more above 500,000 t.

    THE PERIOD LABEL NAMES THE YEARS, NOT THE EDITION, which is why the entry's 1934-1945 window could
    not see them: `1928-1932` is a retrospective average printed by the LATE `iia_1938_39`, so 34 of
    its 83 tobacco rows exceed 500,000 t while the clean volumes' averages hold 2 of 119 -- and both
    of those two (`india` 612,500 t, `united states of america` 630,805.5 t) are CORRECT figures that
    a crude threshold over-flags. Pinning the clean-volume count at 2 is therefore an exoneration: a
    third would be a real finding, and losing these two would mean the screen or the extract moved.

    The last pin is the gap. era_shift_verdicts.csv reaches period rows only at 1934-1938, so no
    1928-1932 row carries a verdict of any kind. If that ever becomes non-zero the era table has been
    widened to reach them, which is good news that must still re-record this check rather than pass
    through it silently.
    """
    v = ctx["era"]
    lb = ctx["panel"]
    t = lb[(lb["source"] == "iia") & (lb["item"] == "tobacco, unmanufactured")
           & (lb["unit"] == "tonnes") & lb["value"].notna()]
    dated = t[t["year"].notna()]
    per = t[t["year"].isna()]
    big = per[per["value"] > 500_000]
    p2832 = per[per["period"].astype(str) == "1928-1932"]
    CLEAN = {"1909-1913", "1925-1929"}
    clean_hits = big[big["period"].astype(str).isin(CLEAN)]
    era_periods = {str(r["period"]).strip() for r in v if str(r.get("period") or "").strip()}
    return ([("era rows", len(v), 427),
             ("labels", len({r["label"] for r in v}), 93),
             ("iia tobacco (tonnes) rows, dated -- the entry's denominator", len(dated), 607),
             ("the same rows carrying a period instead", len(per), 286),
             ("period rows above 500,000 t", len(big), 73),
             ("of those, in the late 1928-1932 average", len(big[big["period"].astype(str)
                                                                == "1928-1932"]), 34),
             ("1928-1932 tobacco rows in total", len(p2832), 83),
             ("clean-volume hits (india and the USA, both CORRECT)", len(clean_hits), 2),
             ("1928-1932 periods reached by the era table", len(era_periods & {"1928-1932"}), 0)],
            "607 is the dated count, so the entry under-scoped by 286 rows and 73 implausible ones")


def check_western_eastern_prefix(ctx):
    """`Western` and `Eastern` are Germany's zones, proved by an additive identity, not by their names.

    THE RESIDUAL IS THE EVIDENCE, AND ITS CONSTANCY IS WHAT MAKES IT EVIDENCE. Germany's total minus
    the two zones is +17 (1000 people) in both 1937 and 1951, and +5 (1000 head of goats) in each of
    1949, 1950 and 1951 -- five year-observations over ten distinct component values, with the offset
    constant within a variable and different between variables. That is the signature of a real third
    component (`Germany Berlin` exists with 42 rows) rather than a coincidence or a rounding artefact.
    A wrong pairing could not reproduce one offset across a 14-year gap and another across three
    consecutive years, so the identity is pinned per year rather than as an average.

    The panel carries no Berlin agricultural-population row, so this check pins that the residual is
    CONSTANT and does not assert it is Berlin's.

    THE EXECUTABILITY PREMISE IS PINNED TOO, because it is the actionable half. For 1949-1951 the
    prefixed twins route to F78/F77 while the `Germany` total routes to DEU-1949-1990, so total and
    parts sit on different polities and nothing collides; for 1937 the twin and the total share
    DEU-1920-1938, which is issue 411's defect. If those routings ever converge or diverge differently
    the 14-of-18 split has to be recomputed, not carried forward. Zero shared keys with the twins is
    pinned as well: it is what makes these rows new data rather than duplicates.

    Routing is read from `matched_rows.parquet`, since layer B's `polity_code` is empty for every
    fao1952 row including the ones that do route."""
    lb = ctx["panel"]
    f = lb[lb["source"] == "fao1952"].copy()
    f["lab"] = f["country"].astype(str).str.strip()

    def val(lab, item, ind, year):
        d = f[(f["lab"] == lab) & (f["item"] == item) & (f["indicator"] == ind)
              & (f["year"].astype("Float64") == year)]
        return float(d["value"].iloc[0]) if len(d) == 1 else None

    POP = ("r_fao_population_1952_10_18", "population:population agricultural")
    GOAT = ("goats", "livestock:livestock")
    claims = [("`Western` rows", len(f[f["lab"] == "Western"]), 13),
              ("`Eastern` rows", len(f[f["lab"] == "Eastern"]), 5)]
    for (item, ind), years, resid, tag in ((POP, (1937, 1951), 17.0, "people"),
                                           (GOAT, (1949, 1950, 1951), 5.0, "goats")):
        for yr in years:
            tot, w, e = (val("Germany", item, ind, yr), val("Western", item, ind, yr),
                         val("Eastern", item, ind, yr))
            got = round(tot - w - e, 6) if None not in (tot, w, e) else None
            claims.append((f"  {yr} {tag}: Germany - (W+E)", got, resid))
            claims.append((f"    {yr} Germany", tot, {
                (1937, "people"): 13145.0, (1951, "people"): 11601.0,
                (1949, "goats"): 2831.0, (1950, "goats"): 3094.0, (1951, "goats"): 2962.0,
            }[(yr, tag)]))

    m = MATCHED_DF[0]
    if m is None:
        return None
    mm = m[m["source"] == "fao1952"].copy()
    mm["lab"] = mm["country"].astype(str).str.strip()
    KEY = ["item", "indicator", "unit", "year", "period"]

    def routed(lab):
        d = mm[mm["lab"] == lab]
        return int(d["whep_code"].fillna("").astype(str).str.strip().ne("").sum()), len(d)

    ROUTED_NOW = {"Western": "10/13", "Eastern": "4/5"}
    for orphan, twin, n in (("Western", "Germany Western", 13), ("Eastern", "Germany Eastern", 5)):
        r, tot = routed(orphan)
        claims.append((f"`{orphan}` routed", f"{r}/{tot}", ROUTED_NOW[orphan]))
        # The rows deliberately left unrouted are the back-projected ones, and which they are is the
        # claim -- a count alone would pass if a 1949 row were dropped and a 1937 one gained.
        left = mm[(mm["lab"] == orphan)
                  & mm["whep_code"].fillna("").astype(str).str.strip().eq("")]
        tags = sorted({(str(int(x)) if pd.notna(x) else str(pp))
                       for x, pp in zip(left["year"], left["period"])})
        claims.append((f"  `{orphan}` still unrouted, by year/period", ",".join(tags),
                       {"Western": "1934-1938,1937", "Eastern": "1937"}[orphan]))
        tr, tn = routed(twin)
        claims.append((f"`{twin}` routed -- the target exists", f"{tr}/{tn}",
                       {"Germany Western": "254/254", "Germany Eastern": "109/109"}[twin]))
        o = mm[mm["lab"] == orphan].copy()
        t = mm[mm["lab"] == twin].copy()
        ok = set(o[KEY].astype(str).agg("|".join, axis=1))
        tk = set(t[KEY].astype(str).agg("|".join, axis=1))
        claims.append((f"  keys `{orphan}` shares with its twin", len(ok & tk), 0))

    def codes(lab, yr):
        d = mm[(mm["lab"] == lab) & (mm["year"] == yr)]
        return ",".join(sorted(set(d["whep_code"].dropna().astype(str))))

    claims.append(("1949 total vs part polity", f"{codes('Germany', 1949)} vs "
                   f"{codes('Germany Western', 1949)}", "DEU-1949-1990 vs F78-1949-1990"))
    claims.append(("1937 total vs part polity -- issue 411", f"{codes('Germany', 1937)} vs "
                   f"{codes('Germany Western', 1937)}", "DEU-1920-1938 vs DEU-1920-1938"))
    # The class this pair belongs to, found structurally rather than by identity proof.
    fr = mm[mm["whep_code"].fillna("").astype(str).str.strip() == ""]
    rt = mm[mm["whep_code"].notna()]
    cleanlabs = sorted({str(x).strip() for x in rt["lab"]})
    frag = []
    for lab2 in sorted({str(x).strip() for x in fr["lab"]}):
        low = lab2.lower()
        par = [c for c in cleanlabs if len(low) > 3 and low in c.lower() and low != c.lower()]
        if par:
            codes = sorted({str(x) for x in rt[rt["lab"].isin(par)]["whep_code"].dropna()})
            frag.append((lab2, int((fr["lab"] == lab2).sum()), codes))
    uniq = [x for x in frag if len(x[2]) == 1]
    claims.append(("fao1952 labels that are a FRAGMENT of a routed one", len(frag), 21))
    claims.append(("  rows they carry", sum(x[1] for x in frag), 42))
    claims.append(("  with a parent routing to exactly ONE polity", len(uniq), 11))
    claims.append(("  with several candidate polities", len(frag) - len(uniq), 10))
    # `Portuga` is the counter-example: structurally unambiguous, three values on one key.
    pg = mm[(mm["lab"] == "Portuga")]
    claims.append(("`Portuga` distinct values on its single key",
                   int(pg["value"].nunique()), 3))
    claims.append(("  it is in the unambiguous list -- structure is NOT sufficiency",
                   "yes" if any(x[0] == "Portuga" for x in uniq) else "no", "yes"))
    return (claims, "a residual constant per variable identifies the zones; the prefix loss is a "
                    "class of 21, and structural unambiguity does not clear a label")


def check_malawi_cotton_deflation(ctx):
    """A ~30x deflation on BOTH axes, and the preserved yield is what makes it one fault not two.

    fao1952 publishes `Nyasaland` on the same polity and the same 1934-1938 period at 3,000 t and
    34,000 ha; iia publishes 100 t and 1,000 ha. Either figure alone would only say the two sources
    disagree. Together they say something stronger: the implied yields are 0.100 and 0.088 t/ha, a
    ratio of 1.13, so whatever divided the production also divided the area. The YIELD RATIO is
    therefore pinned alongside the two axes -- if it ever drifted, this would become two independent
    errors and the entry's reasoning would have to be redone.

    THE COMPARISON DEPENDS ON TWO THINGS THIS REPO ONLY RECENTLY HAS. It is a POLITY-level comparison
    across different labels (issue 375), and it needs fao1952's `1000 tonnes` normalised against iia's
    `tonnes` (issue 612) -- with raw unit strings the two series never meet. The check therefore
    asserts the two labels really do land on one polity, because if that routing changed the
    comparison would vanish silently rather than fail.

    THE SPIKE-TABLE CONSEQUENCE IS PINNED because it is the transferable part: isolated_spikes.csv
    records 1935 = 3,400 as an anomaly, and 3,400 is the one cell in the window that matches fao. A
    neighbour-ratio screen names the sound cell whenever a correct value sits among corrupted ones."""
    lb = ctx["panel"]
    m = MATCHED_DF[0]
    if m is None:
        return None
    iia = lb[(lb["source"] == "iia") & (lb["country"].astype(str).str.lower() == "malawi")
             & (lb["item"].astype(str).str.lower() == "cotton lint")]
    fao = lb[(lb["source"] == "fao1952")
             & lb["country"].astype(str).str.contains("Nyasaland", case=False, na=False)
             & (lb["item"].astype(str).str.lower() == "cotton lint")]

    def per(frame, unit, p="1934-1938"):
        h = frame[(frame["unit"] == unit) & frame["year"].isna()
                  & (frame["period"].astype(str) == p)]
        return float(h["value"].iloc[0]) if len(h) else None

    it, ia = per(iia, "tonnes"), per(iia, "ha")
    ft, fa = per(fao, "1000 tonnes"), per(fao, "1000 hectares")
    claims = [("iia 1934-1938 production (t)", it, 100.0),
              ("iia 1934-1938 area (ha)", ia, 1000.0),
              ("fao1952 Nyasaland 1934-1938 (1000 t)", ft, 3.0),
              ("fao1952 Nyasaland 1934-1938 (1000 ha)", fa, 34.0)]
    if None not in (it, ia, ft, fa):
        claims.append(("  production factor fao/iia", round(ft * 1000 / it, 1), 30.0))
        claims.append(("  area factor fao/iia", round(fa * 1000 / ia, 1), 34.0))
        # The yield ratio is the evidence that one slip hit both axes.
        claims.append(("  YIELD ratio iia/fao -- must stay ~1",
                       round((it / ia) / (ft * 1000 / (fa * 1000)), 2), 1.13))
    dated = {int(r.year): float(r.value) for r in
             iia[(iia["unit"] == "tonnes") & iia["year"].between(1934, 1937)].itertuples()}
    claims.append(("iia dated 1934/1935/1936/1937 (t)",
                   ",".join(str(int(dated.get(y, -1))) for y in (1934, 1935, 1936, 1937)),
                   "100,3400,100,100"))
    mm = m[m["value"].notna()]
    pol = sorted({str(x) for x in mm[(mm["source"] == "iia")
                                     & (mm["country"].astype(str).str.lower() == "malawi")
                                     & (mm["item"].astype(str).str.lower() == "cotton lint")
                                     ]["whep_code"].dropna()})
    fpol = sorted({str(x) for x in mm[(mm["source"] == "fao1952")
                                      & mm["country"].astype(str).str.contains("Nyasaland", case=False,
                                                                               na=False)
                                      ]["whep_code"].dropna()})
    claims.append(("both labels land on one polity", f"{','.join(pol)}|{','.join(fpol)}",
                   "MWI-1891-1953|MWI-1891-1953"))
    with open(os.path.join(REPO, "pipelines", "polity-autoimprove", "state",
                           "isolated_spikes.csv"), newline="", encoding="utf-8") as fh:
        sp = [r for r in csv.DictReader(fh)
              if r["country"] == "malawi" and r["item"] == "cotton lint"]
    claims.append(("isolated_spikes flags the SOUND cell", sp[0]["year"] if sp else None, "1935"))
    return (claims, "the preserved yield makes it one scale slip; the spike table names the good cell")


def check_error_inde_is_india(ctx):
    """`[error] inde` is India, established three ways, and 99% of it never reaches layer B.

    THE THREE ROUTES ARE PINNED SEPARATELY because no one of them identifies the label alone. A French
    name could be coincidence; India-scale magnitudes could fit several territories; complementary
    coverage could be two unrelated series. Together they leave one reading, and if any single route
    stopped holding the identification would need re-arguing rather than adjusting.

    THE COVERAGE ROUTE IS THE STRONGEST and is the one a value-fingerprint cannot see: `british india`
    runs to 1938 and never appears in `iia_1939_45`, while this label appears ONLY in the two late
    volumes and covers 1939-1945, which no other India label reaches. That is also exactly why issue
    493's fingerprint scored it as noise -- the method needs the broken label's data to exist under a
    clean label too, so it is blind to labels carrying unique data.

    THE EXPOSURE IS PINNED IN BOTH DIRECTIONS. 410 of 414 rows absent is the finding; if that number
    fell, some of the block has been recovered and this entry should be re-recorded rather than left
    passing."""
    raw = ctx["raw"]
    lb = ctx["panel"]
    r = raw[(raw["_c"] == "[error] inde") & raw["_v"].isin(["production", "area"])
            & raw["value"].notna()]
    claims = [("`[error] inde` production/area rows", len(r), 414)]
    vols = collections.Counter(str(x) for x in r["yearbook"])
    claims.append(("  from iia_1938_39", vols.get("iia_1938_39"), 210))
    claims.append(("  from iia_1939_45", vols.get("iia_1939_45"), 204))
    claims.append(("  from any OTHER volume -- must stay 0",
                   len(r) - vols.get("iia_1938_39", 0) - vols.get("iia_1939_45", 0), 0))

    # route 3: british india stops where this label starts
    bi = raw[(raw["_c"] == "british india") & raw["value"].notna()]
    bys = sorted({int(y) for y in bi["year"].astype(str).str.strip() if y.isdigit()})
    eys = sorted({int(y) for y in r["year"].astype(str).str.strip() if y.isdigit()})
    claims.append(("`british india` last dated year", max(bys) if bys else None, 1938))
    claims.append(("`[error] inde` last dated year", max(eys) if eys else None, 1945))
    claims.append(("  years ONLY under the broken label",
                   ",".join(str(y) for y in sorted(set(eys) - set(bys))),
                   "1939,1940,1941,1942,1943,1944,1945"))
    claims.append(("`british india` rows in iia_1939_45 -- must stay 0",
                   int((bi["yearbook"].astype(str) == "iia_1939_45").sum()), 0))

    # route 2: the magnitude profile
    def med(frame, prod, var):
        d = frame[(frame["_p"] == prod) & (frame["_v"] == var)]["value"]
        return round(float(d.median()), 1) if len(d) else None
    claims.append(("cottonseed production median, broken label",
                   med(r, "cottonseed", "production"), 2027900.0))
    claims.append(("  the same under `british india`",
                   med(bi[bi["_v"] == "production"], "cottonseed", "production"), 2181804.0))

    # the exposure
    i = lb[(lb["source"] == "iia")
           & (lb["country"].astype(str).str.strip().str.lower() == "india") & lb["value"].notna()]
    seen = collections.defaultdict(set)
    for x in i.itertuples():
        k = str(int(x.year)) if pd.notna(x.year) else str(x.period)
        seen[k].add(round(float(x.value), 4))
    present = sum(1 for x in r.itertuples()
                  if round(float(x.value), 4) in seen.get(str(x.year).strip(), ()))
    claims.append(("rows present in layer-B iia/india", present, 4))
    claims.append(("rows ABSENT -- the exposure", len(r) - present, 410))
    return (claims, "identified by name, magnitude and complementary coverage; 99% never lands")


def check_libya_olives_period_cell(ctx):
    """One inflated olive cell, and the CONTROL is what keeps it a cell rather than a class.

    The four comparisons are pinned together because no one of them is decisive alone: 181x its own
    dated span could be a bad baseline, 26.40 t/ha could be a bad area, and a cross-source gap could be
    a scope difference. Together, with the area row independently correct, they leave nothing else the
    cell can be.

    THE PAIRED AREA ROW IS THE LOAD-BEARING ONE. Its `1934-1938` area is within 0.4% of the dated mean
    for the same years, so the tonnage cannot be excused as covering a larger territory -- it converts
    a big number into an impossible YIELD. That is issue 416's signature (production inflated, area
    clean) on an item 416 does not cover.

    THE ITEM-LEVEL CONTROL IS PINNED TOO, and it is what stops this becoming a claimed x100 class:
    across the iia labels with dated olive series either side of 1934 the median era break is 1.195 and
    none reaches 50x. If that median ever moved, olives WOULD be an era-scaled item and this entry
    would need rewriting as a class rather than two cells.

    The sibling `1928-1932` row is pinned as the negative: the same label's other multi-year average is
    sound, so the defect is one cell and not the label's period rows in general."""
    lb = ctx["panel"]
    d = lb[(lb["source"] == "iia") & (lb["country"] == "libya")
           & (lb["item"].astype(str).str.lower() == "olives")]
    t = d[d["unit"] == "tonnes"]
    a = d[d["unit"] == "ha"]

    def per(frame, p):
        h = frame[frame["year"].isna() & (frame["period"].astype(str) == p)]
        return float(h["value"].iloc[0]) if len(h) else None

    def dated_mean(frame, lo, hi):
        w = frame[(frame["year"] >= lo) & (frame["year"] <= hi)]
        return round(float(w["value"].mean()), 1) if len(w) else None

    pt, pa = per(t, "1934-1938"), per(a, "1934-1938")
    dt, da = dated_mean(t, 1934, 1938), dated_mean(a, 1934, 1938)
    claims = [("period 1934-1938 production (t)", pt, 1610700.0),
              ("  its dated 1934-1938 mean", dt, 8900.0),
              ("  ratio -- the cell against its own years", round(pt / dt, 1) if pt and dt else None,
               181.0),
              ("period 1934-1938 area (ha) -- must stay CLEAN", pa, 61000.0),
              ("  its dated 1934-1938 mean", da, 60750.0),
              ("  area ratio (clean means ~1.0)", round(pa / da, 3) if pa and da else None, 1.004),
              ("  implied yield t/ha, period", round(pt / pa, 2) if pt and pa else None, 26.4),
              ("  implied yield t/ha, dated (real olives are 1-3)",
               round(dt / da, 2) if dt and da else None, 0.15),
              ("sibling period 1928-1932 (t) -- the NEGATIVE", per(t, "1928-1932"), 19300.0),
              ("  its dated 1928-1932 mean", dated_mean(t, 1928, 1932), 17706.7)]

    # cross-source: fao1952 publishes the same period, in thousands
    fo = lb[(lb["source"] == "fao1952")
            & lb["country"].astype(str).str.contains("Libya", case=False, na=False)
            & (lb["item"].astype(str).str.lower() == "olives")]
    fp = fo[fo["year"].isna() & (fo["period"].astype(str) == "1934-1938")]
    claims.append(("fao1952 same period (1000 t)",
                   float(fp["value"].iloc[0]) if len(fp) else None, 11.0))

    # the item-level control: olives is NOT an era-scaled item
    import statistics
    ol = lb[(lb["source"] == "iia") & (lb["item"].astype(str).str.lower() == "olives")
            & (lb["unit"] == "tonnes") & lb["value"].notna()]
    breaks = []
    for lab, g in ol.groupby("country"):
        pre = g[g["year"].notna() & (g["year"] < 1934)]["value"]
        post = g[g["year"].notna() & (g["year"] >= 1934)]["value"]
        if len(pre) >= 3 and len(post) >= 3 and statistics.median(pre) > 0:
            breaks.append(statistics.median(post) / statistics.median(pre))
    claims.append(("labels with a dated series either side of 1934", len(breaks), 8))
    claims.append(("  median era break -- olives is NOT x100",
                   round(statistics.median(breaks), 3) if breaks else None, 1.195))
    claims.append(("  labels breaking >=50x", sum(1 for b in breaks if b >= 50), 0))
    return (claims, "the clean area row makes it a yield, and the 1.195 control makes it a cell")


def check_china_whole_and_five_parts(ctx):
    """The decomposition closes to Tibet, which is what proves the labels are a whole-and-parts family.

    THE RESIDUAL IS THE EVIDENCE. Five reported parts sum to 87.1% of the whole, and the missing
    125,174 kha is 1,251,740 km2 against Tibet's ~1,228,400 -- a ratio of 1.019. That near-closure is
    what distinguishes a genuine territorial decomposition from an accidental collection of labels
    sharing a prefix, so the residual ratio is pinned rather than only the sum.

    THE ROUTED/UNROUTED SPLIT IS PINNED BECAUSE IT IS A TRAP. Only two parts reach CHN-1947-1949, so a
    collision census sees 63% of the whole double-counted; the other three carry 24% of China's land
    and route nowhere. Routing them -- the ordinary repair for an unrouted label, and the one applied
    in PR 610 -- would take the double-count from 63% to 87%. If any of the three ever acquires a
    whep_code, this check fails, which is the intended behaviour: it should be a deliberate decision
    taken with the whole-versus-parts question, not a routine routing fix.

    THE ITEM-LEVEL MIXING IS PINNED AS A PAIR, land against livestock, because either number alone
    looks unremarkable. `use total` matching China's actual area to 1.4% is what makes 95,000 pigs
    impossible rather than merely small."""
    m = MATCHED_DF[0]
    if m is None:
        return None
    f = m[(m["source"] == "fao1952") & m["value"].notna()].copy()
    f["lab"] = f["country"].astype(str).str.strip()
    u = f[(f["item"] == "use total") & (f["year"] == 1947)]
    val = {r["lab"]: float(r["value"]) for _, r in u.iterrows()}
    PARTS = ["China 22 provinces", "China Manchuria", "China Sinkiang", "China Sikang", "China Jehol"]
    WANT = {"China": 973629.0, "China 22 provinces": 507182.0, "China Manchuria": 106930.0,
            "China Sinkiang": 171193.0, "China Sikang": 45152.0, "China Jehol": 17998.0}
    claims = [(f"`{k}` use total 1947", val.get(k), v) for k, v in WANT.items()]
    if all(k in val for k in WANT):
        whole = val["China"]
        s5 = sum(val[k] for k in PARTS)
        claims.append(("  five parts summed", round(s5, 1), 848455.0))
        claims.append(("  as a share of the whole", round(100 * s5 / whole, 1), 87.1))
        # Tibet ~1,228,400 km2 = 122,840 kha. The near-closure is the proof.
        claims.append(("  residual / Tibet (1,228,400 km2)", round((whole - s5) / 122840.0, 3), 1.019))
        r2 = val["China 22 provinces"] + val["China Manchuria"]
        claims.append(("  the VISIBLE double-count (routed parts only)",
                       round(100 * r2 / whole, 0), 63.0))

    def routed(lab):
        d = f[f["lab"] == lab]
        return int(d["whep_code"].fillna("").astype(str).str.strip().ne("").sum()), len(d)

    for lab in ("China 22 provinces", "China Manchuria"):
        r, n = routed(lab)
        claims.append((f"`{lab}` routed", "yes" if r else "no", "yes"))
    for lab in ("China Sinkiang", "China Sikang", "China Jehol"):
        r, n = routed(lab)
        # Bidirectional on purpose: routing these WORSENS the double-count.
        claims.append((f"`{lab}` routed -- must stay NO", "yes" if r else "no", "no"))

    ch = f[f["lab"] == "China"]

    def cell(item, yr):
        d = ch[(ch["item"] == item) & (ch["year"] == yr)]
        return float(d["value"].iloc[0]) if len(d) else None

    # The label IS China -- see fao1952-china-livestock-cells-implausible, which rebuts the
    # "different territory" reading. These two are pinned as a PAIR to keep that entry and this one
    # describing the same thing: a correct national total with damaged livestock cells inside it.
    claims.append(("`China` population 1937 (thousand) -- the label IS China",
                   cell("r_fao_population_1952_10_18", 1937), 452460.0))
    claims.append(("`China` pigs 1949 (thousand) -- a damaged cell, not another territory",
                   cell("pigs", 1949), 95.0))
    claims.append(("`China` buffaloes 1949/1950/1951 -- a coherent series",
                   ",".join(str(cell("buffaloes", y)) for y in (1949, 1950, 1951)),
                   "658.0,656.0,568.0"))
    return (claims, "the decomposition closes to Tibet; routing the three unrouted parts makes it worse")


def check_tractors_total_beside_parts(ctx):
    """`total tractors agriculture` IS wheel plus crawler, to the digit -- and a fourth item on the
    same code is not a component of it.

    THE IDENTITY IS THE FINDING, so it is pinned as a ratio rather than as a row count. Across the
    groups holding the total and both named parts, total / (wheel + crawler) has median 1.0000. A count
    would survive the parts being renamed or the total being recomputed; the identity would not.

    THE FOURTH ITEM IS THE TRAP AND IS PINNED SEPARATELY. `tractors all purposes` is a broader measure
    including non-agricultural machines -- Alaska 1950 reads total 160 = wheel 150 + crawler 10 while
    all-purposes reads 700 -- so this item_code holds two DIFFERENT correct measures plus the
    components of one of them. If `tractors all purposes` ever satisfied the identity too, the four
    items would be one nested family and this entry's reasoning would need redoing, so the check
    asserts it does NOT.

    THE is_aggregate GAP IS WHY THIS IS INVISIBLE, and it is pinned in both directions: every
    is_aggregate=True fao1952 row is a GEOGRAPHIC aggregate, so 267 rows of an item literally named
    `total ...` carry False and reach matching. If that count ever fell, an item-axis flag has been
    introduced and the entry should be revisited rather than left passing."""
    lb = ctx["panel"]
    f = lb[(lb["source"] == "fao1952") & (lb["item_code"] == "192_194")].copy()
    f["lab"] = f["country"].astype(str).str.strip()
    f["_p"] = f["period"].astype(str).where(f["year"].isna(), f["year"].astype("Int64").astype(str))
    nonagg = f[f["is_aggregate"] == False]  # noqa: E712 -- a pandas mask, not a truth test
    counts = {str(k): int(v) for k, v in nonagg["item"].value_counts().items()}
    TOT, WHEEL, CRAWL, ALL = ("total tractors agriculture", "wheel tractors agriculture",
                              "crawler tractors agriculture", "tractors all purposes")
    claims = [("non-aggregate rows on item_code 192_194", len(nonagg), 952),
              (f"  `{TOT}`", counts.get(TOT), 267),
              (f"  `{ALL}` -- NOT a component", counts.get(ALL), 298),
              (f"  `{WHEEL}`", counts.get(WHEEL), 207),
              (f"  `{CRAWL}`", counts.get(CRAWL), 180)]

    import statistics
    rat, allr, full = [], [], 0
    for _, d in nonagg.groupby(["lab", "_p", "indicator", "unit"]):
        piv = {r["item"]: float(r["value"]) for _, r in d.iterrows() if pd.notna(r["value"])}
        if TOT in piv and WHEEL in piv and CRAWL in piv:
            full += 1
            s2 = piv[WHEEL] + piv[CRAWL]
            if s2 > 0:
                rat.append(piv[TOT] / s2)
                if ALL in piv:
                    allr.append(piv[ALL] / s2)
    claims.append(("groups holding the total and both parts", full, 177))
    if rat:
        claims.append(("  median total / (wheel + crawler)", round(statistics.median(rat), 4), 1.0))
        claims.append(("  of those, within 2% of 1.0",
                       sum(1 for x in rat if 0.98 <= x <= 1.02), 172))
    if allr:
        # `all purposes` is a SUPERSET, not a component: always >= the agricultural total, equal
        # wherever a country had no non-agricultural tractors. Both halves are pinned, because the
        # coincidence is what makes the four items easy to mistake for one nested family -- and
        # because a superset that DROPPED below its own subset would be a new defect entirely.
        claims.append(("  `all purposes` within 2% of the total (it coincides often)",
                       sum(1 for x in allr if 0.98 <= x <= 1.02), 123))
        claims.append(("  `all purposes` strictly LARGER (the non-agricultural machines)",
                       sum(1 for x in allr if x > 1.02), 54))
        claims.append(("  `all purposes` ever SMALLER than the total it contains",
                       sum(1 for x in allr if x < 0.98), 0))

    whole = lb[lb["source"] == "fao1952"]
    agg = whole[whole["is_aggregate"] == True]  # noqa: E712
    named_total = whole[whole["item"].astype(str).str.strip().str.lower().str.startswith("total")]
    claims.append(("fao1952 is_aggregate=True rows (all GEOGRAPHIC)", len(agg), 2141))
    claims.append(("rows whose ITEM name begins `total` yet is_aggregate=False",
                   int((named_total["is_aggregate"] == False).sum()), 267))  # noqa: E712
    return (claims, "the total is identifiable by name and by source file, and flagged by neither")


def check_germany_western_cheese(ctx):
    """2 kt of West German cheese, and the point is that BOTH available pairings are extreme.

    `cheese` carries item_code 161_162 -- two FAO codes collapsed into one layer-B item -- so `Germany`
    holds two cheese rows at 1934-1938 (154 and 1,114) and `Germany Western` holds two (2 and 2). Issue
    411 could not adjudicate the cell for that reason, and so did I on first pass. The correction is
    that the branches AGREE: 2/154 = 0.013 and 2/1,114 = 0.002, against a share band of 0.382-0.749.
    An undecidable pairing only blocks a finding when the branches disagree, so both ratios are pinned
    rather than one.

    THE BAND IS THE BASELINE AND IT IS MEASURED HERE, not carried over. It is the median and range of
    `Germany Western` / `Germany` across the keys where both labels hold exactly one row -- the West
    German share of the 1937 Reich, reproduced by crops, livestock, fertiliser and population. If it
    ever moved, the expected values below move with it and the entry needs re-reasoning.

    THE POULTRY ROW ORDER IS PINNED AS A CROSS-CHECK ON THE BAND, which is the subtle part. The band is
    computed on 1:1 keys only, so it could in principle be an artefact of which keys are 1:1. Applying
    the repo's own recorded alphabetical order for the `poultry` group aligns four cells that are NOT
    in that set, and three land inside the band -- so the band survives a test on keys it was not
    fitted to.

    The series' own continuation (149/137/152 and 34/52/74 at 1949-1951) is pinned too: it is what
    makes 2 anomalous against the label's later behaviour and not only against its parent."""
    lb = ctx["panel"]
    f = lb[lb["source"] == "fao1952"].copy()
    f["lab"] = f["country"].astype(str).str.strip()
    p34 = f[f["year"].isna() & (f["period"].astype(str) == "1934-1938")]
    K = ["item", "item_code", "indicator", "unit"]

    def grouped(lab):
        return {k: sorted(float(x) for x in v["value"]) for k, v in
                p34[p34["lab"] == lab].groupby(K, dropna=False)}

    G, W = grouped("Germany"), grouped("Germany Western")
    ch = [k for k in G if k[0] == "cheese"]
    claims = [("`Germany` cheese rows at 1934-1938", len(G.get(ch[0], [])) if ch else None, 2),
              ("`Germany Western` cheese rows", len(W.get(ch[0], [])) if ch else None, 2)]
    if ch:
        gv, wv = G[ch[0]], W.get(ch[0], [])
        claims.append(("  Germany's two values", ",".join(f"{v:g}" for v in gv), "154,1114"))
        claims.append(("  West's two values", ",".join(f"{v:g}" for v in wv), "2,2"))
        if len(gv) == 2 and wv:
            claims.append(("  ratio against the smaller", round(wv[0] / gv[0], 4), 0.013))
            claims.append(("  ratio against the larger -- BOTH extreme",
                           round(wv[0] / gv[1], 4), 0.0018))

    import statistics
    one = [(W[k][0] / G[k][0]) for k in G
           if k in W and len(G[k]) == 1 == len(W[k]) and G[k][0] > 0]
    claims.append(("1:1 keys giving the share band", len(one), 22))
    if one:
        claims.append(("  its median -- the West German share", round(statistics.median(one), 3), 0.635))
        claims.append(("  its low end", round(min(one), 3), 0.382))
        claims.append(("  its high end", round(max(one), 3), 0.749))
        exp_small = 154.0 * statistics.median(one)
        claims.append(("  so the expected West figure (154 pairing)", round(exp_small), 98))

    # cross-check the band on keys it was NOT fitted to, via the recorded poultry row order
    po = [k for k in G if k[0] == "poultry"]
    if po and len(G[po[0]]) == len(W.get(po[0], [])) == 4:
        gv, wv = G[po[0]], W[po[0]]
        inband = sum(1 for a, b in zip(wv, gv) if b > 0 and 0.382 <= a / b <= 0.749)
        claims.append(("poultry cells inside the band (order-aligned, unfitted keys)", inband, 3))
    return (claims, "both pairings are extreme, so the ambiguity does not block the finding")


def check_algeria_civil_basis_span(ctx):
    """94 iia rows carry a territory 4.03x too large, and a THREE-YEAR DATA GAP is what makes the
    boundary provable rather than argued.

    #605 created DZA-CVD-1902-1919 for IIA's Algeria data on the three civil departments. IIA's own
    stated areas show that basis running to data year 1925 -- 575,289 at 1921 and 575,511 at 1925,
    then 2,195,097 at 1929 -- so the rows at 1919-1925 sit on the whole-colony polity while the source
    says they describe a territory a quarter of its size.

    THE GAP IS THE LOAD-BEARING PIN. iia has ZERO Algeria rows at 1926, 1927 and 1928, so any boundary
    placed in those three years partitions the data identically and the basis change needs no dating by
    inference. If a re-extraction ever supplied rows there, the boundary becomes a judgement call and
    this entry's central claim has to be re-argued rather than kept -- which is why the zero is checked
    and not merely mentioned.

    Both stated areas are pinned as well, because the factor is the finding: if either moved, the 4.03x
    moves with it. And the period rows are pinned by PERIOD, because the two that straddle the switch
    are the ones no routing can fix, and a count alone would not notice 1925-1929 being swapped for
    1934-1938."""
    m = MATCHED_DF[0]
    if m is None:
        return None
    a = m[(m["country"].astype(str).str.strip().str.lower() == "algeria") & (m["source"] == "iia")]
    dated = a[a["year"].notna()]

    def band(lo, hi):
        return dated[(dated["year"] >= lo) & (dated["year"] <= hi)]

    def codes(d):
        return ",".join(sorted({str(x) for x in d["whep_code"].dropna()}))

    b1925 = band(1919, 1925)
    claims = [("iia Algeria rows 1919-1925 -- the wrong territory", len(b1925), 94),
              ("  their destination", codes(b1925), "DZA-1919-1962"),
              ("iia Algeria rows 1926-1928 -- THE GAP that dates the boundary",
               len(band(1926, 1928)), 0),
              ("iia Algeria rows 1929-1935 (correctly whole-colony)", len(band(1929, 1935)), 111),
              ("iia Algeria rows 1917-1918 (fixed by #605)", len(band(1917, 1918)), 17),
              ("  their destination", codes(band(1917, 1918)), "DZA-CVD-1902-1919")]

    with open(os.path.join(REPO, "data", "final", "source_stated_areas.csv"),
              newline="", encoding="utf-8") as fh:
        sa = [r for r in csv.DictReader(fh) if "alg" in r["label"].lower()]
    for dy, want in (("1925", 575511.0), ("1929", 2195097.0)):
        hit = [float(r["stated_area_km2"]) for r in sa if str(r["data_year"]) == dy]
        claims.append((f"IIA's stated km2 at data year {dy}", hit[0] if hit else None, want))
    if len(sa) >= 2:
        civil = [float(r["stated_area_km2"]) for r in sa if str(r["data_year"]) == "1925"]
        whole = [float(r["stated_area_km2"]) for r in sa if str(r["data_year"]) == "1929"]
        if civil and whole:
            claims.append(("  the source's own step, whole / civil",
                           round(whole[0] / civil[0], 2), 3.81))

    per = a[a["year"].isna()]
    counts = {str(k): int(v) for k, v in per["period"].astype(str).value_counts().items()}
    for p, want in (("1925-1929", 24), ("1928-1932", 25)):
        claims.append((f"period {p} rows -- STRADDLES the switch, unroutable", counts.get(p), want))
    claims.append(("period 1909-1913 rows (on DZA-CVD, correct)", counts.get("1909-1913"), 19))
    return (claims, "the 1926-1928 gap is what makes the boundary provable; 49 period rows straddle it")


def check_estates_label_prefix(ctx):
    """`Estates` is the AREA half of `Indonesia Estates`, and the yield identity is what proves it.

    Issue 450 recorded `Estates` as a label it could not identify. The name never identifies it -- what
    does is that the two labels carry one item over the same four reporting periods with complementary
    indicators, so dividing one by the other has to produce a believable coffee yield, and it does:
    0.492, 0.330, 0.271 and 0.300 t/ha. A wrong pairing would not survive that test, which is why the
    four value PAIRS are pinned rather than a row count. An estate area falling to a third of its
    pre-war extent by 1949 is also the expected post-war history.

    THE COLLISION PREMISE IS PINNED TOO, because it is what makes this a decision rather than a free
    alias fix. `Indonesia` routes 144 of 144 and carries its own 4 coffee rows, so the estate rows are
    a tenure sub-category of a total that already lands; routing them onto the same polity reproduces
    the total-beside-parts collision of issues 367, 411 and 449, and the consumer means duplicate keys
    rather than choosing the total. If `Indonesia`'s coffee rows ever stopped landing, or the estate
    labels started to, that premise would have changed and this entry has to be re-reasoned rather
    than kept.

    Routing is read from `matched_rows.parquet`: layer B's `polity_code` is empty for every fao1952
    row including the ones that DO route, so the panel cannot answer the routing question at all."""
    lb = ctx["panel"]
    f = lb[lb["source"] == "fao1952"].copy()
    f["lab"] = f["country"].astype(str).str.strip()

    def cell(lab, indicator, year, period):
        d = f[(f["lab"] == lab) & (f["item"] == "coffee") & (f["indicator"] == indicator)]
        d = d[d["year"].isna()] if period else d[d["year"].astype("Float64") == year]
        if period:
            d = d[d["period"].astype(str) == period]
        return float(d["value"].iloc[0]) if len(d) == 1 else None

    PAIRS = [("1934-1938", None, 55.6, 113.0), (None, 1949, 10.9, 33.0),
             (None, 1950, 11.1, 41.0), (None, 1951, 12.0, 40.0)]
    claims = [("`Estates` rows (all coffee area)",
               len(f[(f["lab"] == "Estates")]), 4),
              ("`Indonesia Estates` rows (all coffee production)",
               len(f[(f["lab"] == "Indonesia Estates")]), 4)]
    for period, year, want_prod, want_area in PAIRS:
        tag = period or str(year)
        prod = cell("Indonesia Estates", "crops:production", year, period)
        area = cell("Estates", "crops:area", year, period)
        claims.append((f"  {tag} production", prod, want_prod))
        claims.append((f"  {tag} area", area, want_area))
        y = round(prod / area, 3) if prod and area else None
        claims.append((f"  {tag} implied t/ha", y, round(want_prod / want_area, 3)))

    m = MATCHED_DF[0]
    if m is None:
        return None
    mm = m[m["source"] == "fao1952"].copy()
    mm["lab"] = mm["country"].astype(str).str.strip()

    def routed(lab):
        d = mm[mm["lab"] == lab]
        return int(d["whep_code"].fillna("").astype(str).str.strip().ne("").sum()), len(d)

    ind_r, ind_n = routed("Indonesia")
    claims.append(("`Indonesia` rows routed -- the collision premise", f"{ind_r}/{ind_n}", "144/144"))
    claims.append(("`Indonesia` coffee rows",
                   len(f[(f["lab"] == "Indonesia") & (f["item"] == "coffee")]), 4))
    for lab in ("Estates", "Indonesia Estates"):
        r, n = routed(lab)
        claims.append((f"`{lab}` routed", f"{r}/{n}", "0/4"))
    return (claims, "the yield identity names the label; the parent total is why it is still a decision")


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


def check_mitchell_flax_is_linseed(ctx):
    """55 mitchell flax-fibre values equal a juan LINSEED value; 1 equals a juan flax-fibre value.

    THE CONTROL IS HALF THE EVIDENCE and it is why this entry is `confirmed` rather than suggestive. That
    55 of 204 values match another source's linseed series exactly would be interesting on its own; that
    only ONE matches the same source's flax-fibre series is what rules out coincidence, because a
    coincidence has no reason to prefer one item over the other by 55 to 1. So both counts are pinned,
    and a rise in the control would undo the conclusion even with the 55 intact.

    Needs the panel only -- no raw extract -- because the proof is one source's series against another's.
    """
    lb = ctx["panel"]

    def index(src, item):
        g = lb[(lb["source"] == src) & (lb["item"] == item) & (lb["unit"] == "ha")
               & lb["value"].notna()]
        out = collections.defaultdict(set)
        for c, v in zip(g["country"], g["value"]):
            out[str(c).strip().lower()].add(round(float(v), 6))
        return g, out

    m, _ = index("mitchell", "flax fibre and tow")
    _, juan_linseed = index("juan", "linseed")
    _, juan_flax = index("juan", "flax fibre and tow")
    lin = flax = 0
    for c, v in zip(m["country"], m["value"]):
        c, v = str(c).strip().lower(), round(float(v), 6)
        if v in juan_linseed.get(c, ()):
            lin += 1
        if v in juan_flax.get(c, ()):
            flax += 1
    return ([("mitchell flax-fibre (ha) values", len(m), 204),
             ("equal to a juan LINSEED value, same country", lin, 55),
             ("equal to a juan FLAX-FIBRE value (the CONTROL)", flax, 1)],
            "the control is what rules out coincidence: 55 against 1, not 55 alone")


def check_iia_flax_is_mostly_linseed(ctx):
    """The iia `flax fibre and tow` item is majority linseed -- and the count depends on which label
    column you join, which is why this check states its own join.

    THE DIRECTION IS ROBUST AND THE MAGNITUDE IS NOT. Joining the layer-B label to the extract through
    `dominant_raw_label` -- the extract's OWN label, which is the correct join per the provenance table's
    own note -- gives 209 cells matching raw `linseed` alone against 107 matching raw `flax: fibre`
    alone. Joining through the CANONICAL `raw_label` instead gives 137 against 57. Either way linseed
    leads by about 2:1, so the entry's conclusion holds; but the entry's own figures (110 / 51 / 58) are
    reproducible by NEITHER join, and sit closest to the canonical one.

    So this check pins the defensible join and says which it is, rather than pinning numbers whose
    derivation cannot be recovered. `raw_label` matches the extract in only 32% of rows -- the trap the
    provenance table documents in its own notes -- so a measurement built on it understates any
    label-matched count, which is the direction the entry's figures sit in.

    The population is dated rows with a provenance-mapped label, which is what reproduces the entry's
    543 exactly; that part of its method is recoverable and confirmed.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    prov = {}
    with open(os.path.join(STATE, "iia_label_provenance.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d = (r.get("dominant_raw_label") or "").strip().lower()
            if d:
                prov.setdefault(r["layer_b_label"], d)
    # ZIP OVER THE COLUMNS, NOT itertuples(). The ctx frame's helper columns are named `_c`, `_p`, `_v`,
    # and itertuples() silently renames any attribute starting with "_" to a positional alias -- so
    # `t._p` raises AttributeError while the column is present and correct. That trap cost four separate
    # debugging rounds on 2026-08-21 across four different scripts.
    idx = collections.defaultdict(set)
    r = raw[raw["value"].notna()]
    for p_, var_, c_, y_, v_ in zip(r["_p"], r["variable"], r["_c"], r["year"], r["value"]):
        idx[(p_, var_, c_, str(y_).strip())].add(round(float(v_), 6))
    g = lb[(lb["source"] == "iia") & (lb["item"] == "flax fibre and tow")
           & lb["value"].notna() & lb["year"].notna() & lb["country"].isin(prov)]
    units = {"ha": "area", "tonnes": "production"}
    lin = flax = both = 0
    for c, u, y, v in zip(g["country"], g["unit"], g["year"], g["value"]):
        var, lab = units.get(u), prov[c]
        key_l = ("linseed", var, lab, str(int(y)))
        key_f = ("flax: fibre", var, lab, str(int(y)))
        v = round(float(v), 6)
        a, b = v in idx.get(key_l, ()), v in idx.get(key_f, ())
        if a and b:
            both += 1
        elif a:
            lin += 1
        elif b:
            flax += 1
    return ([("cells (dated, provenance-mapped label)", len(g), 543),
             ("matching raw `linseed` alone", lin, 209),
             ("matching raw `flax: fibre` alone", flax, 107),
             ("matching BOTH (ambiguous)", both, 88)],
            "joined on the extract's own label; the canonical join gives 137/57/50 instead")


def check_malaya_female_agric_is_total(ctx):
    """One cell, proven by its own sibling rows: a female subtotal equal to its parent total.

    `Malaya Federation of and Singapore` 1937 reports population female agricultural = 1,171 and
    population agricultural TOTAL = 1,171 -- the same number. A female subtotal cannot be 100% of its
    parent. The 1951 rows of the SAME label show what the correct structure looks like and are measured
    here as the control: total 1,186 = female 347 + male 839, summing exactly. And the 1937 MALE row is
    ABSENT, which is what makes the signature a column shift at extraction rather than a bad value: the
    total's figure landed in the female column and the male figure was lost.

    All three claims are pinned because each rules out a different alternative. Equality alone could be
    coincidence; the 1951 sum shows the columns are normally consistent; the missing male row shows
    something was dropped rather than mistyped.
    """
    lb = ctx["panel"]
    m = lb[(lb["source"] == "fao1952")
           & lb["country"].str.contains("Malaya Fed", na=False)
           & lb["indicator"].str.contains("population", na=False)]

    def v(ind_part, year):
        r = m[m["indicator"].str.contains(ind_part, na=False) & (m["year"] == year)]["value"]
        return round(float(r.iloc[0]), 6) if len(r) == 1 else None

    # MATCH ON "population male", NOT "male agricultural": the string "female agricultural" CONTAINS
    # "male agricultural", so the obvious substring counts the female row as a male one. The first
    # version of this check reported 1 male 1937 row where there are none, i.e. it refuted the entry
    # using the entry's own evidence.
    fem37, tot37 = v("population female", 1937), v("agricultural ocupati", 1937)
    fem51, male51, tot51 = (v("population female", 1951), v("population male", 1951),
                            v("agricultural ocupati", 1951))
    male37 = m[m["indicator"].str.contains("population male", na=False) & (m["year"] == 1937)]
    return ([("1937 female agricultural", fem37, 1171.0),
             ("1937 agricultural total (IDENTICAL to it)", tot37, 1171.0),
             ("1937 MALE rows present", len(male37), 0),
             ("1951 female + male (the control)",
              round(fem51 + male51, 6) if None not in (fem51, male51) else None, 1186.0),
             ("1951 agricultural total", tot51, 1186.0)],
            "the 1951 sum shows the columns are normally consistent; 1937's male row is gone")


def check_nigeria_cotton_area_zero(ctx):
    """Five zero area cells refuted by the same label's own tonnage.

    `iia`/`nigeria`/`cotton lint`/`ha` reads 0.0 for every year 1941-1945 -- the whole tail of the
    series -- while the SAME label reports cotton seed production of 15,100 / 13,600 / 10,300 / 6,600 t
    for 1941-1944. No tonnage comes off zero hectares, so the zeros are self-refuting without any
    external reference.

    BOTH SIDES ARE PINNED. The zeros alone would be consistent with the crop having stopped; it is the
    surviving tonnage that refutes them, so a re-test measuring only the zeros could pass while the
    evidence against them disappeared.
    """
    lb = ctx["panel"]
    g = lb[(lb["source"] == "iia") & (lb["country"] == "nigeria") & lb["year"].notna()]
    area = g[(g["item"] == "cotton lint") & (g["unit"] == "ha") & (g["year"] >= 1941)]
    seed = g[(g["item"] == "cotton seed") & (g["unit"] == "tonnes") & (g["year"] >= 1941)]
    return ([("cotton lint area cells 1941+", len(area), 5),
             ("of those equal to zero", int((area["value"] == 0).sum()), 5),
             ("cotton seed production cells 1941+ (the refutation)", len(seed), 4),
             ("their total tonnage", round(float(seed["value"].sum()), 6), 45600.0)],
            "the surviving tonnage is what refutes the zeros; the zeros alone prove nothing")


def check_cze_1910_rye_orphan(ctx):
    """A 3-hectare rye area in 1910, and the pre-1919 row count that convicts it without a magnitude
    argument.

    THE ROW COUNT IS THE ARGUMENT, not the size of the number. Raw `czechoslovakia` carries exactly THREE
    rows dated before 1919 -- this rye area of 3.0 ha at 1910, a 1918 sugar-beet production of 640,816.1 t
    and a 1918 potato export of 0.1 t -- and the state was founded in October 1918. A label with three
    pre-existence rows is not reporting a country's 1910 rye crop; the 1918 sugar beet is defensible as
    the harvest of a territory that became Czechoslovakia weeks later, and the 1910 row has no such
    reading.

    So the check pins the COUNT (3) as well as the cell, because the count is what makes this an orphan
    rather than a small value. It also pins the next observation, 732,970 ha at 1919: the gap is what
    rules out 3.0 being a plausible early figure on the same series.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    r = raw[(raw["_c"] == "czechoslovakia") & raw["value"].notna()]
    yn = pd.to_numeric(r["year"], errors="coerce")
    pre = r[yn < 1919]
    g = lb[(lb["source"] == "iia") & (lb["country"] == "czech republic") & (lb["item"] == "rye")
           & (lb["unit"] == "ha") & lb["value"].notna() & lb["year"].notna()].sort_values("year")
    first = round(float(g["value"].iloc[0]), 6) if len(g) else None
    nxt = round(float(g["value"].iloc[1]), 6) if len(g) > 1 else None
    return ([("raw `czechoslovakia` rows dated before 1919", len(pre), 3),
             ("layer-B czech rye ha, earliest cell", first, 3.0),
             ("its next observation", nxt, 732970.0)],
            "three pre-existence rows is the argument; the 3.0 is only the cell")


def check_1933_x10_provenance_linked(ctx):
    """The 14 provenance-linked x10 cells -- and the entry names the wrong provenance table.

    THE THIRD CONDITION IS WHAT MAKES THIS CLASS CONFIRMABLE. Matching a small round value against the
    extract by value and year alone left 9 of 16 uncertain, because 30, 300 and 2,100 appear all over
    the panel. Requiring the layer-B label carrying the value to be one the provenance table attributes
    to that RAW label removes the coincidences: a chance collision has no reason to land on the
    provenance-linked label.

    THE ENTRY CITES `item_provenance.csv` FOR THAT LINK; the reproduction needs
    `iia_label_provenance.csv`. Item-level provenance yields only 9 of the 14, because five of them --
    french dahomey cacao and eggs, french ivory coast tobacco, british jamaica cacao, australia sugar --
    sit in series too small for `item_provenance` to attribute, so their `raw_label` there is blank.
    Label-level provenance reproduces all 14 exactly, and the 14 match the enumeration on issue 424 cell
    for cell. So the entry's figure is right and its method description names the wrong table; this check
    uses the one that works and says so.
    """
    lb = ctx["panel"]
    with open(os.path.join(STATE, "edition_conflicts.csv"), newline="", encoding="utf-8") as fh:
        ec = [r for r in csv.DictReader(fh)
              if r["kind"] == "power_of_ten" and 9.5 <= float(r["ratio"]) <= 10.5]
    cand = [r for r in ec if r["volume_a"] == "iia_1933_34"
            and float(r["value_a"]) < float(r["value_b"])]
    lab2lb = collections.defaultdict(set)
    with open(os.path.join(STATE, "iia_label_provenance.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for col in ("dominant_raw_label", "raw_label"):
                v = (r.get(col) or "").strip().lower()
                if v:
                    lab2lb[v].add(r["layer_b_label"])
    g = lb[(lb["source"] == "iia") & lb["value"].notna()]
    when = g["period"].where(g["period"].notna(), g["year"].astype("string"))
    by = collections.defaultdict(set)
    for c, w, v in zip(g["country"], when, g["value"]):
        by[str(c)].add((str(w).strip(), round(float(v), 6)))
    confirmed = 0
    for r in cand:
        s, y = round(float(r["value_a"]), 6), str(r["year"]).strip()
        if any((y, s) in by.get(t, ()) for t in lab2lb.get(r["label"].strip().lower(), ())):
            confirmed += 1
    return ([("x10 candidates with iia_1933_34 holding the smaller value", len(cand), 32),
             ("of those, PROVENANCE-LINKED into layer B", confirmed, 14)],
            "label-level provenance reproduces 14; item-level gives only 9")


def check_nauru_1933_transposition(ctx):
    """The 1933 natural-phosphate values for `british nauru` and `australia` are swapped between the two
    volumes that cover 1933, and layer B took the wrong one.

    The load-bearing claim is not the collapse -- it is that the swap is MUTUAL and near-exact
    (369,516 vs 369,500; 97 vs 100), which is what distinguishes a transposed pair from two independent
    errors. So all four raw cells are pinned, not just the one layer B published. If a re-extraction
    fixed only one side the mutuality would break and this check would say so."""
    raw, lb = ctx["raw"], ctx["panel"]
    r = raw[(raw["_p"] == "fertilizers: phosphate, natural") & (raw["_v"] == "production")]
    r = r[pd.to_numeric(r["year"], errors="coerce") == 1933]

    def one(country, book):
        v = r[(r["_c"] == country) & (r["yearbook"] == book)]["value"]
        return float(v.iloc[0]) if len(v) == 1 else None

    n = lb[(lb["source"] == "iia") & (lb["country"].str.lower() == "nauru")
           & (lb["item"].str.lower() == "p")]
    published = n[n["year"] == 1933]["value"]
    return ([("iia_1933_34 nauru", one("british nauru", "iia_1933_34"), 97.0),
             ("iia_1933_34 australia", one("australia", "iia_1933_34"), 369516.0),
             ("iia_1938_39 nauru", one("british nauru", "iia_1938_39"), 369500.0),
             ("iia_1938_39 australia", one("australia", "iia_1938_39"), 100.0),
             ("layer B published 1933", float(published.iloc[0]) if len(published) == 1 else None,
              97.0)],
            "the swap is mutual and near-exact, and layer B carries the wrong side")


def check_lithuania_1933_sugar_volume(ctx):
    """Layer B took the iia_1933_34 value (8.1 t) for a 1933 cell where iia_1938_39 prints 7,300 t.

    The correct value is printed by the SOURCE, so this is not argued from magnitude -- and the pin that
    carries that argument is the neighbouring pair, because 7,300 fitting between 18,218 and 13,700 is
    the whole case. Same shape as the Nauru transposition: 1933 is the only year two volumes cover, so
    it is the only year a wrong-volume pick is possible at all."""
    raw, lb = ctx["raw"], ctx["panel"]
    r = raw[(raw["_c"] == "lithuania") & (raw["_p"] == "sugar: beet") & (raw["_v"] == "production")]
    r = r.assign(y_=pd.to_numeric(r["year"], errors="coerce"))

    def rawv(year, book):
        v = r[(r["y_"] == year) & (r["yearbook"] == book)]["value"]
        return float(v.iloc[0]) if len(v) == 1 else None

    l = lb[(lb["source"] == "iia") & (lb["country"].str.lower() == "lithuania")
           & (lb["item"].str.lower() == "sugar raw centrifugal")]
    pub = {int(t.year): float(t.value) for t in l[l["year"].notna()].itertuples()}
    return ([("raw iia_1933_34 at 1933", rawv(1933, "iia_1933_34"), 8.1),
             ("raw iia_1938_39 at 1933", rawv(1933, "iia_1938_39"), 7300.0),
             ("layer B published 1933", pub.get(1933), 8.1),
             ("layer B 1932 neighbour", pub.get(1932), 18218.0),
             ("layer B 1934 neighbour", pub.get(1934), 13700.0)],
            "the source prints the correct value in the other volume covering 1933")


def _broadcast_block(lb, country, year, value, items):
    """Shared shape for the two mitchell broadcast blocks: every listed livestock item in one label-year
    reading exactly the same figure. Returns (how many hit the value, how many items were found)."""
    m = lb[(lb["source"] == "mitchell") & (lb["country"].str.lower() == country)
           & (lb["year"] == year) & (lb["unit"] == "heads")]
    found = {str(t.item).lower(): float(t.value) for t in m.itertuples()}
    hit = sum(1 for i in items if found.get(i) == value)
    return hit, len(found)


def check_india_1947_broadcast(ctx):
    """All eight mitchell india livestock items read exactly 3,000 head in 1947.

    The cross-item agreement IS the diagnosis, so the pin is the COUNT of items at the value, not any
    one cell -- eight independent errors landing on one number is not a hypothesis anyone weighs. The
    third claim is the entry's own counter-argument and matters just as much: 3,000 occurs 148 times
    across 48 mitchell labels legitimately, so the value proves nothing on its own and only the
    coincidence within a label-year carries signal. If that count collapsed, the entry's reasoning
    would need restating even though its verdict would stand."""
    lb = ctx["panel"]
    items = ["asses", "buffalo", "camels", "cattle", "goats", "horses", "sheep", "swine / pigs"]
    hit, found = _broadcast_block(lb, "india", 1947, 3000.0, items)
    mit = lb[lb["source"] == "mitchell"]
    at3000 = mit[mit["value"] == 3000.0]
    asses08 = lb[(lb["source"] == "mitchell") & (lb["country"].str.lower() == "india")
                 & (lb["item"].str.lower() == "asses") & (lb["year"] == 1908)]["value"]
    return ([("livestock items at 3,000", hit, 8),
             ("head items in the label-year", found, 8),
             ("3,000 elsewhere in mitchell", len(at3000), 148),
             ("  across labels", at3000["country"].nunique(), 48),
             ("the ninth instance, asses 1908",
              float(asses08.iloc[0]) if len(asses08) == 1 else None, 3000.0)],
            "the coincidence within the label-year is the signal; the value itself is common")


def check_somalia_1959_broadcast(ctx):
    """The same shape as india 1947, in a different label and decade -- which is what makes it a class
    rather than an incident. Four species agreeing to the digit is the claim; 1960 being sound is what
    confines it to one year."""
    lb = ctx["panel"]
    hit, found = _broadcast_block(lb, "somalia", 1959, 15000.0,
                                  ["camels", "cattle", "goats", "sheep"])
    nxt = lb[(lb["source"] == "mitchell") & (lb["country"].str.lower() == "somalia")
             & (lb["year"] == 1960) & (lb["unit"] == "heads")]
    return ([("livestock items at 15,000", hit, 4),
             ("head items in the label-year", found, 4),
             ("1960 items, all sound", len(nxt), 4),
             ("  none of them at 15,000", int((nxt["value"] == 15000.0).sum()), 0)],
            "a second instance of the india 1947 shape, and only 1959 is affected")


def check_russia_1918_is_karafuto(ctx):
    """Layer B's eight iia `russian federation` rows at 1918 are Karafuto Prefecture's, value for value.

    Three claims, in increasing strength. The eight values matching is the identification. The RAW
    RUSSIAN LABELS HAVING NO 1918 ROWS AT ALL is why it happened -- nothing competed for the slot -- and
    that absence is the most falsifiable thing here: one 1918 Russian row in a re-extraction and the
    explanation changes. The 21-vs-2 fingerprint is the scope claim: the misrouting is general and 1918
    is merely where it becomes visible."""
    raw, lb = ctx["raw"], ctx["panel"]
    r = raw.assign(y_=pd.to_numeric(raw["year"], errors="coerce"))
    kara = r[(r["_c"] == "japan: karafuto prefecture") & r["_v"].isin(["production", "area"])
             & r["value"].notna()]
    ru1918 = r[r["_c"].isin(["russia in europe", "russia in asia"]) & (r["y_"] == 1918)]
    lb18 = lb[(lb["source"] == "iia") & (lb["country"].str.lower() == "russian federation")
              & (lb["year"] == 1918)]
    kv = {(float(t.value)) for t in kara.itertuples()}
    matched = sum(1 for t in lb18.itertuples() if float(t.value) in kv)
    # scope: Karafuto's dated (year, value) pairs against every layer-B label
    pairs = {(int(t.y_), float(t.value)) for t in kara.itertuples() if pd.notna(t.y_)}
    d = lb[lb["source"] == "iia"].dropna(subset=["year"])
    take = collections.Counter(
        str(c).lower() for c, y, v in zip(d["country"], d["year"], d["value"])
        if (int(y), float(v)) in pairs)
    ranked = take.most_common()
    second = ranked[1][1] if len(ranked) > 1 else 0
    return ([("layer B russian rows at 1918", len(lb18), 8),
             ("  matching a Karafuto value", matched, 8),
             ("raw Russian rows at 1918", len(ru1918), 0),
             ("Karafuto dated pairs", len(pairs), 73),
             ("  taken by `russian federation`", take.get("russian federation", 0), 21),
             ("  taken by the next label", second, 2)],
            "nothing competed for 1918, and the misrouting is general beyond it")


def check_china_groundnut_audit(ctx):
    """The discharged audit of the china groundnut outliers, plus the mechanism behind it.

    Three of the audit's findings are pinned as stated: the two low values are Kwantung's, carried in the
    raw as hectares and tonnes (which is what refutes the thousand-piculs unit hypothesis -- there is no
    conversion anywhere in the chain); the source repeats the identical pair in a second volume under a
    renamed product; and the high value it worried about (2,460,450 t) exists nowhere in either the raw
    extract or the panel.

    The fourth block is the mechanism, and it is what makes the audit's "a value belonging to one label
    surfacing under another" too narrow. Layer B's `china, mainland` cell is the ARITHMETIC SUM of raw
    `china` and raw `japan: kwantung leased territory`. Where china has no figure the sum degenerates to
    Kwantung alone, which is the case the audit found; where china does have one, Kwantung is ADDED to
    it, and those cells are invisible to any test that attributes a published value to a single raw
    label. Issue 483 counts 25 uniquely-attributable Kwantung cells; the additive ones are a disjoint
    population."""
    raw, lb = ctx["raw"], ctx["panel"]
    r = raw.assign(k_=raw["year"].astype(str).str.strip())
    gnut = r[r["_p"].str.contains("groundnut", na=False) & r["value"].notna()]
    KW = "japan: kwantung leased territory"
    kwrows = gnut[(gnut["_c"] == KW) & gnut["value"].isin([2663.0, 2873.5])]
    units = sorted(set(kwrows["unit"].astype(str)))
    books = sorted(set(kwrows["yearbook"]))
    # 2,460,450 t: gone from both sides
    gl = lb[lb["item"].astype(str).str.contains("groundnut", case=False, na=False)]
    near = gl[(gl["value"] > 2460450 * 0.99) & (gl["value"] < 2460450 * 1.01)]

    # the additive identity, over every china,mainland cell with a same-family Kwantung row
    kw = r[(r["_c"] == KW) & r["value"].notna()]
    c = lb[(lb["source"] == "iia") & (lb["country"].str.lower() == "china, mainland")]
    only = summed = 0
    for t in c.itertuples():
        key = str(t.period) if pd.isna(t.year) else str(int(t.year))
        var = "area" if t.unit == "ha" else "production"
        fam = str(t.item).split(",")[0].strip().split()[0].lower()[:5]
        k2 = kw[(kw["variable"] == var) & (kw["k_"] == key)
                & kw["_p"].str.startswith(fam, na=False)]["value"]
        if k2.empty:
            continue
        v, kwv = float(t.value), float(k2.max())
        if v == 0 or kwv == 0:      # a zero matches anything
            continue
        ch = r[(r["_c"] == "china") & (r["variable"] == var) & (r["k_"] == key)
               & r["_p"].str.startswith(fam, na=False) & r["value"].notna()]["value"]
        chv = float(ch.max()) if len(ch) else None
        if chv is not None and abs(chv + kwv - v) < 1.0:
            summed += 1
        elif abs(kwv - v) < 0.6:
            only += 1
    return ([("raw rows at the two values", len(kwrows), 4),
             ("  all under Kwantung", int((kwrows["_c"] == KW).all()), 1),
             ("  units as printed", "|".join(units), "hectares|tonnes"),
             ("  volumes repeating the pair", "|".join(books), "iia_1925_26|iia_1929_30"),
             ("2,460,450 t within 1%", len(near), 0),
             ("  exact, anywhere in raw", int((raw["value"] == 2460450).sum()), 0),
             ("Kwantung-ONLY cells", only, 25),
             ("Kwantung-ADDED cells", summed, 21)],
            "the aggregation is additive; the audit found its degenerate case")


def check_reunion_tobacco_baseline(ctx):
    """The contaminated-baseline entry, whose load-bearing claim is an exact arithmetic identity.

    Reunion's ten exonerations rest on a baseline of 20,000 t drawn from the inflated volume, so every
    era row divides one inflated number by another. That much is a count. The MECHANISM claim -- that a
    pre-era baseline is contaminated by any inflated PERIOD row regardless of how many clean dated years
    exist -- rests on romania/hops, whose recorded baseline is exactly the mean of one clean and one
    inflated period row: (3,500 + 40.6) / 2 = 1,770.3. That identity is pinned to the digit, because it
    is the only thing separating this entry's general condition from a single-label anecdote.

    THE ONE-SIDED-TEST GAP THIS CHECK DOCUMENTED IS NOW FIXED, and the fix is what moved five of the
    pins below (2026-08-31, PR #603). The gap was real: the screen convicted at >=30x the label's own
    pre-1934 median and filed everything below as `no_area_level_consistent`, so a value could not be
    too SMALL to pass, and `germany / tobacco / 1945` sat at ratio 0.0 -- a ZERO production -- filed
    consistent. It escaped the `impossible_yield_zero_area` arm as well, because that arm needs
    `area == 0` and this row's area is BLANK, so blank-vs-zero (#414's subject) decided which arm saw
    it. #603 gave the screen the low side of its own ratio test as the verdict `no_area_level_drop`,
    and the row is now convicted under it.

    WHAT THAT DID TO THE COUNTS, and why every one of them is re-recorded rather than adjusted:
    `no_area_level_consistent` 22 -> 21, `neither reunion nor romania` 11 -> 10, their lowest ratio
    0.0 -> 3.211009, `exonerated rather than convicted` 1 -> 0, and convicted rows 349 -> 350. A
    recorded baseline is bidirectional precisely so a FALL has to be explained too, and here the fall
    is the fix landing.

    THE ENTRY'S OWN BAND IS THEREBY RESTORED, which is the cleanest evidence the germany row was the
    anomaly and not a symptom. The entry describes ten exonerations at 3.2x-27.1x; with the eleventh
    convicted the ten that remain span exactly 3.211009 to 27.100271, so the figure the entry recorded
    was right all along and the drift was one row that did not belong in the class. Both ends are
    pinned below for that reason.

    NONE OF THIS TOUCHES THE ENTRY'S SUBJECT. Reunion's ten exonerations still rest on a baseline of
    20,000 t drawn from the inflated volume, so each still divides one inflated number by another, and
    romania/hops' baseline is still exactly the mean of one clean and one inflated period row --
    (3,500 + 40.6) / 2 = 1,770.3, pinned to the digit because it is the only thing separating this
    entry's general condition from a single-label anecdote. The contaminated-baseline defect is open.

    All three rows at <=0.34x their own baseline are now convicted: micronesia's two by the zero-area
    arm and germany's by the new drop arm. Germany's verdict is pinned by NAME, so a regression that
    re-exonerates it fails here rather than only moving a count."""
    era = ctx["era"]
    nac = [r for r in era if r["verdict"] == "no_area_level_consistent"]
    reu = [r for r in nac if r["label"].strip().lower() == "reunion"]
    rom = [r for r in nac if r["label"].strip().lower() == "romania"]
    others = [r for r in nac if r["label"].strip().lower() not in ("reunion", "romania")]

    def ratio(r):
        try:
            return float(r["ratio_to_own"])
        except (TypeError, ValueError):
            return None

    orat = sorted(v for v in (ratio(r) for r in others) if v is not None)
    # `(ratio(r) or 1.0)` would be wrong here and wrongly in the one way that matters: 0.0 is falsy,
    # so the zero row this check exists to find would be replaced by 1.0 and dropped. That is the same
    # shape as the defect below -- a zero slipping through a test that never contemplated it.
    lows = [r for r in era if ratio(r) is not None and ratio(r) <= 0.34]
    low_exonerated = [r for r in lows if r["verdict"] == "no_area_level_consistent"]
    convicted = sum(1 for r in era if str(r["convicted"]).strip().lower() in ("1", "true", "yes"))
    germany = [r for r in era if r["label"].strip().lower() == "germany" and r["year"] == "1945"]
    return ([("reunion exonerations", len(reu), 10),
             ("  its baseline", float(reu[0]["own_pre_era_median"]) if reu else None, 20000.0),
             ("  ratios at 1934-1936", sum(1 for r in reu if ratio(r) == 1.0
                                           and r["year"] in ("1934", "1935", "1936")), 3),
             ("romania hops baseline", float(rom[0]["own_pre_era_median"]) if rom else None, 1770.3),
             ("  == (3500 + 40.6) / 2", round((3500 + 40.6) / 2, 4), 1770.3),
             ("no_area_level_consistent", len(nac), 21),
             ("  neither reunion nor romania", len(others), 10),
             ("  their lowest ratio", orat[0] if orat else None, 3.211009),
             ("  their highest ratio", orat[-1] if orat else None, 27.100271),
             ("rows at <=0.34x own baseline", len(lows), 3),
             ("  exonerated rather than convicted", len(low_exonerated), 0),
             ("germany/1945 verdict, was exonerated at 0.0",
              germany[0]["verdict"] if germany else None, "no_area_level_drop"),
             ("convicted rows", convicted, 350)],
            "the one-sided test is fixed (#603); the contaminated baseline itself is still open")


def _unrouted(panel, label):
    """How a compound/erroneous label sits in the assignment artefact: rows, and whether any reach a
    polity. Several entries below turn on a label being deliberately unrouted, and `matched_rows` is
    the only artefact that records that -- the panel carries no polity for these at all."""
    m = MATCHED_DF[0]
    if m is None:
        return None, None
    d = m[m["country"].astype(str).str.strip() == label]
    routed = sum(1 for x in d["whep_code"].fillna("") if str(x).strip())
    return len(d), routed


def check_china_goats_x1001(ctx):
    """The import applied x1001 where it should have applied x1000, and the proof is DIVISIBILITY.

    Eleven consecutive values each dividing by 1001 into a whole thousand is not a coincidence any
    alternative explanation survives, so that count is the claim rather than any single cell. 1945-1947
    carry a different factor (x2000 = 2 x 1000) and reproduce the raw Excel integers exactly.

    ONE REFINEMENT on re-test: the entry calls 1949 "only 0.1% above the correct ~16130000 and is
    plausible", which reads as a cell needing no repair. It is not a separate benign case --
    16,146,130 is EXACTLY 16,130 x 1001, i.e. the identical wrong multiplier with the x1000 unit factor
    missing (the source cell is the text annotation `16130 millions`, so the unit multiplier never
    applied). 1949 is in fact the cleanest demonstration of the mechanism, because with the unit factor
    absent, 1001-instead-of-1000 shows up as precisely 0.1%. The correct value is derivable --
    16,130,000 -- so the remedy should cover 1949 rather than leave it."""
    d = ctx.get("pre1961")
    if d is None:
        return None
    g = d[(d["item"].astype(str).str.lower() == "goats") & (d["country"] == "China, mainland")]
    v = {int(t.year): float(t.value) for t in g.itertuples()}
    clean = sum(1 for y in range(1950, 1961)
                if abs(v[y] / 1001 - round(v[y] / 1001)) < 1e-6 and round(v[y] / 1001) % 1000 == 0)
    x2000 = sum(1 for y, r in ((1945, 13249), (1946, 13609), (1947, 13976)) if v[y] / 2000 == r)
    return ([("years 1950-1960 present", sum(1 for y in range(1950, 1961) if y in v), 11),
             ("  each /1001 a whole thousand", clean, 11),
             ("1945-1947 /2000 == raw integers", x2000, 3),
             ("1950 as published", v.get(1950), 1822821000.0),
             ("  its repaired value", round(v[1950] / 1001), 1821000),
             ("1949 == 16130 * 1001", int(v.get(1949) == 16130 * 1001), 1),
             ("  so 1949 is x1001 too", round(v[1949] / (16130 * 1000), 4), 1.001)],
            "eleven exact divisions, and 1949 carries the same multiplier rather than being benign")


def check_australia_fiji_merged(ctx):
    """Two adjacent OCEANIA rows merged into one label, with Fiji's leading `1` absorbed into
    Australia's figures.

    The convicting evidence is the IMPLIED YIELD, not the digit pattern: 81 thousand tonnes on 7
    thousand ha is 11.6 t/ha, which no groundnut crop reaches, while the entry's repaired 8 gives 1.14
    -- an ordinary yield. And the label must reach no polity for the entry's "must not be routed
    anywhere" to hold, so that is asserted too rather than assumed."""
    lb = ctx["panel"]
    a = lb[lb["country"].astype(str).str.strip() == "Australia Fiji"]
    prod = {int(t.year): float(t.value) for t in a.itertuples()
            if t.unit == "1000 tonnes" and pd.notna(t.year)}
    area = {int(t.year): float(t.value) for t in a.itertuples()
            if t.unit == "1000 hectares" and pd.notna(t.year)}
    rows, routed = _unrouted(lb, "Australia Fiji")
    sib = sum(1 for n in ("Australia", "Fiji")
              if len(lb[(lb["source"] == "fao1952") & (lb["country"].astype(str).str.strip() == n)]))
    return ([("1949 production", prod.get(1949), 81.0),
             ("1950 production", prod.get(1950), 61.0),
             ("1949 area", area.get(1949), 7.0),
             ("implied yield at 1949", round(prod[1949] / area[1949], 2), 11.57),
             ("  repaired (8 / 7)", round(8.0 / area[1949], 2), 1.14),
             ("both peers exist separately", sib, 2),
             ("rows reaching a polity", routed, 0)],
            "11.6 t/ha convicts the cell; the repaired 1.14 is ordinary")


def check_california_double_count(ctx):
    """California's grapes against the US national total in the same source.

    The entry's exclusion rests on the ratio, so both sides are pinned. Its stated range `161-225` kt
    omits 1951: the label also carries 147 at 1951, inside the entry's own 1949-1951 scope, so the
    range is 147-225. That does not change the verdict -- California is 5-9% of the national figure in
    every year, and routing it to USA-1867-1959 would double-count in all three."""
    lb = ctx["panel"]
    ca = lb[lb["country"].astype(str).str.strip() == "United States California"]
    us = lb[(lb["source"] == "fao1952") & (lb["country"].astype(str).str.strip() == "United States")
            & (lb["item"].astype(str) == "grapes")]
    cav = {int(t.year): float(t.value) for t in ca.itertuples()
           if t.unit == "1000 tonnes" and pd.notna(t.year)}
    usv = {int(t.year): float(t.value) for t in us.itertuples()
           if t.unit == "1000 tonnes" and pd.notna(t.year)}
    rows, routed = _unrouted(lb, "United States California")
    return ([("california 1949", cav.get(1949), 161.0),
             ("california 1950", cav.get(1950), 225.0),
             ("california 1951", cav.get(1951), 147.0),
             ("national 1949", usv.get(1949), 2415.0),
             ("national 1951", usv.get(1951), 3071.0),
             ("max california share %", round(100 * max(cav[y] / usv[y] for y in cav if y in usv), 1),
              9.2),
             ("rows reaching a polity", routed, 0)],
            "the entry's 161-225 omits 1951's 147; the exclusion is unaffected")


def check_bahamas_area_x10(ctx):
    """The x10 land-area cell, its correct siblings, and the entry's own prediction that this statement
    never reaches the stated-area gate.

    That prediction is the most falsifiable part and it holds: the alias for the label is scoped to
    source `fao1952` while `08_source_stated_areas.py` writes the source as `fao`, so the statement
    resolves to no polity and NO row for it exists in source_stated_area_basis.csv. Barbados and the
    Caymans are absent for the same reason, so the sibling comparison the entry makes is not reachable
    from the tracked artefacts either -- Jamaica alone gets through, which is the asymmetry worth
    holding onto.

    One correction: the entry says IIA states this territory across `six editions (1909-1938)`. There
    are seven statements over FIVE editions, and none from 1909."""
    st, ba = ctx["stated"], ctx["basis"]
    if st is None or ba is None:
        return None
    fao = {r["label"]: float(r["stated_area_km2"]) for r in st
           if r["source"] == "fao" and r["stated_area_km2"]}
    iia = [r for r in st if r["source"] == "iia" and "bahamas" in r["label"].lower()]
    vals = sorted({float(r["stated_area_km2"]) for r in iia if r["stated_area_km2"]})
    eds = sorted({r["edition"] for r in iia})
    return ([("the cell, in km2", fao.get("British West Indies Bahamas"), 1400.0),
             ("sibling Cayman Islands", fao.get("British West Indies Cayman Islands"), 240.0),
             ("sibling Barbados", fao.get("British West Indies Barbados"), 450.0),
             ("IIA statements", len(iia), 7),
             ("  over editions", len(eds), 5),
             ("  none from 1909", int("1909" not in eds), 1),
             ("  its distinct values", "|".join(f"{v:.0f}" for v in vals), "11385|11406"),
             # WAS 0 UNTIL 2026-08-25, and the change is the point. The entry's side note (1)
             # predicted this statement would never reach the gate, because its alias is scoped
             # `fao1952` while 08 writes `fao`. That observation became issue 553, and #579 fixed it
             # with a source synonym -- so the prediction is now false BY DESIGN, and the x10 error
             # is visible in the basis table at 1,400 stated against a 13,278 polygon, ratio 9.484,
             # flagged `review`, instead of being silently discarded.
             #
             # This is the retest registry doing the job it exists for: I falsified a recorded claim
             # with a deliberate fix and did not notice, because neither retest runs in CI (both
             # need layer B). Main was failing this check.
             ("rows in the basis table", sum(1 for r in ba if "Bahamas" in r["source_labels"]), 1),
             ("  and it is flagged for review",
              ";".join(sorted({r["basis_flag"] for r in ba
                               if "Bahamas" in r["source_labels"] and r["source"] == "fao"})),
              "review")],
            "the statement now DOES reach the gate (issue 553, fixed in #579) and surfaces the x10 "
            "as a 9.484x divergence rather than being discarded")


def check_jamaica_dropped_digit(ctx):
    """The dropped-leading-digit cell, and the 7.7x discrepancy the gate carries without failing.

    Unlike its Bahamas neighbour this statement DOES reach `source_stated_area_basis.csv`, where it sits
    at ratio 7.747 against an 11,001 km2 polygon and `08_source_stated_areas.py --check` passes on it --
    which is the entry's point that the yearbook's printed figure is carried rather than repaired.

    The arithmetic that distinguishes this from the Bahamas x10 is pinned: x10 gives 14,200 (1.29x too
    large) while restoring a leading 1 gives 11,420 (1.039x), so a decimal shift does not explain it."""
    st, ba = ctx["stated"], ctx["basis"]
    if st is None or ba is None:
        return None
    fao = {r["label"]: float(r["stated_area_km2"]) for r in st
           if r["source"] == "fao" and r["stated_area_km2"]}
    cell = fao.get("British West Indies Jamaica")
    # The territory's own line, not its indented sub-labels: the table holds
    # `...: JAMAIQUE`, `...: JAMAIQUE: CAIMANS` and `...: JAMAIQUE: TURQUES ET CAIQUES`, and the
    # editions differ in case, so match on the lowercased label ENDING at `jamaique`.
    iia = [r for r in st if r["source"] == "iia" and r["label"].strip().lower().endswith("jamaique")]
    vals = sorted({float(r["stated_area_km2"]) for r in iia if r["stated_area_km2"]})
    row = [r for r in ba if r["polity_code"] == "JAM-1800-2025" and r["source"] == "fao"]
    return ([("the cell, in km2", cell, 1420.0),
             # The entry says "across six editions" and that is right; the STATEMENT count is 9,
             # because the 1909 and 1925 volumes each print the line for two data years.
             ("IIA statements for Jamaica itself", len(iia), 9),
             ("  over editions", len({r["edition"] for r in iia}), 6),
             ("  its distinct values", "|".join(f"{v:.0f}" for v in vals),
              "10880|10896|11525|11526"),
             ("x10 reading", cell * 10, 14200.0),
             ("restored leading 1", cell + 10000, 11420.0),
             ("basis rows (unlike the Bahamas)", len(row), 1),
             ("  its polygon km2", float(row[0]["polygon_area_km2"]) if row else None, 11001.0),
             ("  its carried ratio", round(float(row[0]["ratio_polygon_over_stated"]), 3)
              if row else None, 7.747)],
            "a decimal shift does not explain it, and the gate passes on a 7.7x gap")


MATCHED_DF = [None]   # filled by main(); _unrouted() reads the assignment artefact through it

# Only entries with a reproducible figure appear here. See the docstring on why the rest cannot.
def _paired_series(mr, src, label, item, unit):
    d = mr[(mr.source == src) & (mr.country.astype(str).str.lower() == label)
           & (mr["item"].astype(str).str.lower() == item) & (mr.unit.astype(str) == unit)]
    d = d.dropna(subset=["year"])
    return {int(t.year): float(t.value) for t in d.itertuples()}


def check_attributable_single_cells(ctx):
    """The 13 repairable cells, re-derived by the entry's own method rather than by its cell list.

    The method is what makes them repairable: two labels routing to one polity make two publishers
    directly comparable, and where they agree to within 1% across most of a long shared span they
    demonstrably measure the same thing -- so a cell diverging past 2x is a defect rather than a
    difference of scope, and the agreeing side supplies the value.

    Re-testing the AGREEMENT COUNTS as well as the divergences matters. If the surrounding years
    stopped matching, the divergent cells would no longer be attributable at all, and a check that
    only counted divergences would still pass while the entry's whole basis had gone.
    """
    mr = ctx.get("matched")
    if mr is None:
        return None
    pairs = [
        ("czech republic", "czechoslovakia", "rye", "ha", 23, 19, [1939, 1940, 1941, 1943]),
        ("czech republic", "czechoslovakia", "rye", "tonnes", 23, 18, [1942, 1943, 1944, 1945]),
        ("czech republic", "czechoslovakia", "flax fibre and tow", "ha", 23, 20, [1942]),
        ("serbia", "yugoslav sfr", "rye", "ha", 17, 15, [1931, 1932]),
        ("serbia", "yugoslav sfr", "rye", "tonnes", 18, 17, [1945]),
        ("serbia", "yugoslav sfr", "rapeseed", "tonnes", 16, 15, [1920]),
    ]
    out, total = [], 0
    for iia_lab, juan_lab, item, unit, n_shared, n_agree, years in pairs:
        A = _paired_series(mr, "iia", iia_lab, item, unit)
        B = _paired_series(mr, "juan", juan_lab, item, unit)
        shared = sorted(set(A) & set(B))
        agree = [y for y in shared if B[y] and abs(A[y] / B[y] - 1) <= 0.01]
        div = [y for y in shared if B[y] and (A[y] / B[y] > 2 or B[y] / A[y] > 2)]
        total += len(div)
        who = f"{iia_lab}/{item}/{unit}"
        out.append((f"{who} shared years", len(shared), n_shared))
        out.append((f"{who} agree within 1%", len(agree), n_agree))
        out.append((f"{who} diverge >2x", ",".join(map(str, sorted(div))),
                    ",".join(map(str, years))))
    out.append(("attributable cells in total", total, 13))
    # The two serbia rye area cells are EXACTLY one tenth, which is the entry's sharpest evidence
    # that these are single-cell digit slips and not a rescaled series.
    A = _paired_series(mr, "iia", "serbia", "rye", "ha")
    B = _paired_series(mr, "juan", "yugoslav sfr", "rye", "ha")
    exact = sum(1 for y in (1931, 1932) if y in A and y in B and A[y] and abs(B[y] / A[y] - 10) < 0.01)
    out.append(("serbia rye ha cells at EXACTLY 10x", exact, 2))
    return out, ("iia is the implausible side for the czech cells and for serbia rye 1945; the "
                 "entry says each cell needs that judgement separately and this does not make it")


def check_constant_run_placeholders(ctx):
    """The two constant runs that are placeholders because the repeated value is off-scale.

    Both repeat a round 1,000. What proves them placeholders is the SCALE of the series each sits
    in, and the two run in OPPOSITE directions -- india's 1,000 ha against a median of 2.2 million
    is far too small, new zealand's 1,000 ha against a median of 83 is twelve times too large. A
    one-sided test would have found only one of them, which is why the check asserts both ratios
    rather than a single "orders of magnitude" threshold.
    """
    mr = ctx.get("matched")
    if mr is None:
        return None
    import statistics as _st
    out = []
    for lab, item, lo, hi, n_run, n_other in (("india", "sesame seed", 1934, 1945, 10, 8),
                                              ("new zealand", "tobacco, unmanufactured",
                                               1934, 1945, 11, 9)):
        v = _paired_series(mr, "iia", lab, item, "ha")
        run = {y: x for y, x in v.items() if lo <= y <= hi}
        other = [x for y, x in v.items() if not (lo <= y <= hi)]
        out.append((f"{lab} {item} ha: run years", len(run), n_run))
        out.append((f"{lab} {item} ha: distinct run values",
                    ",".join(f"{x:g}" for x in sorted(set(run.values()))), "1000"))
        out.append((f"{lab} {item} ha: other values", len(other), n_other))
        if other:
            out.append((f"{lab} {item} ha: run/median", round(1000.0 / _st.median(other), 5),
                        round(1000.0 / _st.median(other), 5)))
    return out, ("india is 0.00045x its own median and new zealand 12.05x theirs -- the same "
                 "placeholder shape pointing opposite ways")


def _iia_grid(pa, vol, unit, step):
    """`k/n` non-zero values in (vol, unit) that are exact multiples of `step`."""
    import numpy as np
    v = pa[(pa["yearbook"] == vol) & (pa["unit"] == unit) & (pa["value"] != 0)]["value"].to_numpy(float)
    r = np.mod(v, step)
    return f"{int((np.isclose(r, 0.0) | np.isclose(r, step)).sum())}/{len(v)}"


def _iia_paired(pa, vol):
    """(cells, bands): one row per (country, product, year) in `vol` with both axes, and the
    volume's own 10th-90th percentile yield band per product measured on the both-positive cells."""
    import numpy as np
    v = pa[(pa["yearbook"] == vol) & pa["_y"].notna()].copy()
    v["_y"] = v["_y"].astype(int)
    a = v[v["_v"] == "area"].groupby(["_c", "_p", "_y"])["value"].max()
    p = v[v["_v"] == "production"].groupby(["_c", "_p", "_y"])["value"].max()
    j = pd.concat({"area": a, "prod": p}, axis=1).reset_index()
    both = j[(j["area"] > 0) & (j["prod"] > 0)].copy()
    both["_y2"] = both["prod"] / both["area"]
    bands = {prod: (float(np.percentile(g, 10)), float(np.percentile(g, 90)), len(g))
             for prod, g in both.groupby("_p")["_y2"] if len(g) >= 8}
    return j, bands


def check_zero_refuted_by_paired_axis(ctx):
    """The 11 zeros the volume's own grid cannot produce, and the 278 in `iia_1938_39` that it can.

    RE-DERIVED HERE RATHER THAN READ from `state/zero_grid_floor.csv`, so a change in
    40_zero_grid_floor.py that moves a verdict fails this instead of silently agreeing with itself.
    The two implementations must agree numerically while sharing no code.

    BOTH DIRECTIONS ARE PINNED, and the negative half is the load-bearing one. The entry's claim is
    not only that 11 cells are refuted -- it is that `iia_1938_39`, which holds 940 of the extract's
    1,102 production/area zeros, refutes NONE. If a re-extraction, a grid change or a threshold change
    turned any of its 251 grid-explicable cells into a refutation, the entry's reading of issue 414
    (a resolution floor, not blank cells) would be wrong while every per-cell figure below still
    reproduced. So the verdict census is asserted as well as the cells.

    The grid measurement is pinned too, because the whole test rests on it: half a grid step is the
    largest value that can round to zero, so if the volumes were NOT on a 1000/100 grid the bounds
    would be wrong in the direction that manufactures refutations.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    pa = raw[raw["_v"].isin(("production", "area")) & raw["value"].notna()].copy()
    pa["_y"] = pd.to_numeric(pa["year"], errors="coerce")
    out = [("iia_1938_39 ha on a 1000-grid", _iia_grid(pa, "iia_1938_39", "hectares", 1000.0),
            "4632/4634"),
           ("iia_1938_39 t on a 100-grid", _iia_grid(pa, "iia_1938_39", "tonnes", 100.0), "8314/8991"),
           ("iia_1939_45 ha on a 1000-grid", _iia_grid(pa, "iia_1939_45", "hectares", 1000.0),
            "6083/6311"),
           ("iia_1939_45 t on a 100-grid", _iia_grid(pa, "iia_1939_45", "tonnes", 100.0),
            "9514/10235")]

    CELLS = [  # volume, country, product, zero axis, year, paired value, factor outside the band
        ("iia_1939_45", "british nigeria", "cotton: ginned", "area", 1939, 9200.0, 54.3),
        ("iia_1939_45", "british nigeria", "cotton: ginned", "area", 1940, 13300.0, 78.5),
        ("iia_1939_45", "british nigeria", "cotton: ginned", "area", 1941, 6600.0, 38.9),
        ("iia_1939_45", "british nigeria", "cotton: ginned", "area", 1942, 5900.0, 34.8),
        ("iia_1939_45", "british nigeria", "cotton: ginned", "area", 1943, 4500.0, 26.6),
        ("iia_1939_45", "british nigeria", "cotton: ginned", "area", 1944, 2900.0, 17.1),
        ("iia_1939_45", "french equatorial africa", "cotton: ginned", "area", 1939, 8800.0, 51.9),
        ("iia_1939_45", "dominican republic", "tobacco", "area", 1939, 871400.0, 12.0),
        ("iia_1939_45", "british uganda", "tobacco", "production", 1942, 5000.0, 3308.2),
        ("iia_1939_45", "british uganda", "tobacco", "production", 1943, 5000.0, 3308.2),
        ("iia_1939_45", "british uganda", "tobacco", "production", 1944, 3000.0, 1984.9),
    ]
    cache = {}
    for vol, c, prod, zero_axis, year, paired, factor in CELLS:
        if vol not in cache:
            cache[vol] = _iia_paired(pa, vol)
        j, bands = cache[vol]
        row = j[(j["_c"] == c) & (j["_p"] == prod) & (j["_y"] == year)]
        who = f"{c[:16]}/{prod[:10]}/{zero_axis[:4]}/{year}"
        if len(row) != 1 or prod not in bands:
            out.append((f"{who} present", len(row), 1))
            continue
        r = row.iloc[0]
        other = "prod" if zero_axis == "area" else "area"
        grid = 1000.0 if zero_axis == "area" else 100.0
        p10, p90, _ = bands[prod]
        if zero_axis == "area":
            fac = (float(r["prod"]) / (grid / 2)) / p90
        else:
            fac = p10 / ((grid / 2) / float(r["area"]))
        out.append((f"{who} zero", float(r[zero_axis if zero_axis == "area" else "prod"]), 0.0))
        out.append((f"{who} paired", float(r[other]), paired))
        out.append((f"{who} x outside band", round(fac, 1), factor))

    # the verdict census over every testable cell, both volumes
    counts = {}
    for vol in ("iia_1938_39", "iia_1939_45"):
        if vol not in cache:
            cache[vol] = _iia_paired(pa, vol)
        j, bands = cache[vol]
        med = (pa[pa["value"] > 0].groupby(["yearbook", "_c", "_p", "_v"])["value"]
               .agg(["median", "size"]))
        # THE FALLBACK IS PART OF THE CRITERION, not of the tool. Written without it, this re-test
        # disagreed with 40_zero_grid_floor.py on exactly one cell -- `french guadeloupe` cottonseed
        # production, whose own volume carries only TWO positive values (100.0 and 3,884,600.0) and so
        # has no median worth comparing against. The extract-wide series gives 12 positives with a
        # median of 72.5, which is what makes the 3.88 Mt an outlier rather than the zero beside it a
        # defect. A per-volume-only median leaves that cell classed `refuted` and would have this
        # entry claiming a false zero in `iia_1938_39` on the strength of an impossible tonnage.
        allmed = (pa[pa["value"] > 0].groupby(["_c", "_p", "_v"])["value"].agg(["median", "size"]))
        for r in j.itertuples():
            for zero_axis, other, grid in (("area", "prod", 1000.0), ("prod", "area", 100.0)):
                zv, pv = getattr(r, zero_axis), getattr(r, other)
                if not (zv == 0 and pv == pv and pv > 0):
                    continue
                if r._2 not in bands:
                    v = "no_product_reference"
                else:
                    p10, p90, _ = bands[r._2]
                    fac = ((float(pv) / (grid / 2)) / p90 if zero_axis == "area"
                           else p10 / ((grid / 2) / float(pv)))
                    v = "refuted" if fac > 10.0 else "grid_can_explain"
                    k = (vol, r._1, r._2, "production" if other == "prod" else "area")
                    m = None
                    if k in med.index and int(med.at[k, "size"]) >= 4:
                        m = float(med.at[k, "median"])
                    elif k[1:] in allmed.index and int(allmed.at[k[1:], "size"]) >= 4:
                        m = float(allmed.at[k[1:], "median"])
                    if v == "refuted" and m is not None and m > 0 and float(pv) / m > 10.0:
                        v = "paired_value_is_the_outlier"
                counts[(vol, v)] = counts.get((vol, v), 0) + 1
    for vol, v, want in (("iia_1938_39", "refuted", 0), ("iia_1938_39", "grid_can_explain", 253),
                         ("iia_1938_39", "no_product_reference", 23),
                         ("iia_1938_39", "paired_value_is_the_outlier", 2),
                         ("iia_1939_45", "refuted", 11),
                         ("iia_1939_45", "grid_can_explain", 2),
                         ("iia_1939_45", "no_product_reference", 0),
                         ("iia_1939_45", "paired_value_is_the_outlier", 0)):
        out.append((f"{vol} {v}", counts.get((vol, v), 0), want))

    # layer-B exposure: 9 rows, and the two-observation series whose mean the zero halves
    g = lb[(lb["source"] == "iia") & lb["year"].notna()]
    nga = g[(g["country"] == "nigeria") & (g["item"] == "cotton lint") & (g["unit"] == "ha")
            & (g["year"] >= 1939)]
    cog = g[(g["country"] == "congo") & (g["item"] == "cotton lint") & (g["unit"] == "ha")
            & (g["year"] == 1939)]
    dom = lb[(lb["source"] == "iia") & (lb["country"] == "dominican republic")
             & (lb["item"] == "tobacco, unmanufactured") & (lb["unit"] == "ha")]
    uga = lb[(lb["source"] == "iia") & (lb["country"] == "uganda")]
    out += [("layer B nigeria cotton lint ha 1939+", len(nga), 7),
            ("  of those zero", int((nga["value"] == 0).sum()), 7),
            ("layer B congo cotton lint ha 1939", float(cog["value"].sum()), 0.0),
            ("layer B dominican tobacco ha rows", len(dom), 2),
            ("  their values", ";".join(f"{float(x):g}" for x in sorted(dom["value"])), "0;16000"),
            ("layer B uganda rows (all items)", len(uga), 0)]
    return out, ("11 refuted cells in iia_1939_45 and NONE in iia_1938_39; the negative half is what "
                 "makes this issue 446's resolution floor rather than issue 414's blank cells")


def check_iia_indonesia_is_java_and_madura(ctx):
    """layer-B iia `indonesia` is Java and Madura, ~7% of the territory it is routed to.

    THE TEST IS IDENTITY, NOT MAGNITUDE (issue 377's lesson). "1.6 Mt of sugar is too much for Java"
    would be the reasoning that put three IIA routings wrong. Here the raw carries eight distinct
    archipelago labels, layer B kept one, and the surviving series matches ONE of them digit for
    digit in every dated year -- a statement about which cell was copied, not about how big it is.

    SINGLE PRODUCT, DELIBERATELY. Pooling every product whose name contains "sugar" over-matches:
    `dutch java and madura` carries both `sugar: cane` and `sugar: cane, unrefined`, and counting a
    year as a hit when ANY of them matches inflated this from 29/29 to 33/34 when I first measured
    it. Attribute a cell only through one product.

    THE ALTERNATIVES LOSE ON AVAILABILITY, NOT ON DISAGREEMENT, and saying which matters: `dutch
    east indies` and `dutch east indies: outer provinces` carry NO `sugar: cane` production rows at
    all, so their score is 0 of 0 shared years rather than 0 of 29. That is the weaker of the two
    argument shapes in reference terms, so the soybean identity below is what carries the entry.

    THE LABEL IS NOT INTERNALLY CONSTANT, which no single-label reroute can fix: soybeans at 1939 is
    332,500 = java+madura 317,600 + bali+lombok 14,900, and NO raw row anywhere carries 332,500 in
    1939. So some cells are one island pair and some are a sum of two -- an additive composition,
    invisible to any value-matching test that asks only which single label a value came from.

    Registers the defect only. The remedy is issue 312's open question (no Java+Madura polity
    exists, and creating one changes what the remaining Dutch East Indies rows mean).
    """
    raw, lb = ctx["raw"], ctx["panel"]
    out = []

    # 1. the eight archipelago labels the source distinguishes and layer B collapsed
    for lab, want in (("dutch east indies", 1932), ("dutch java and madura", 1599),
                      ("dutch east indies: outer provinces", 1175), ("dutch new guinea", 110),
                      ("dutch sumatra", 23), ("dutch bali and lombok", 18),
                      ("dutch java and sumatra", 8),
                      ("dutch java, madura and outer provinces", 6)):
        out.append((f"raw `{lab[:26]}`", int((raw["_c"] == lab).sum()), want))

    # 2. what layer B kept. Stated on BOTH time axes: filtering on `year` alone would silently drop
    #    the 75 period rows, which is the trap this repo documented in issue 618.
    ind = lb[(lb["source"] == "iia") & (lb["country"].astype(str).str.strip().str.lower() == "indonesia")]
    out += [("layer-B iia `indonesia` rows", len(ind), 378),
            ("  dated", int(ind["year"].notna().sum()), 303),
            ("  period", int(ind["year"].isna().sum()), 75)]

    # 3. sugar: one product, exact equality, per label
    import pandas as pd

    prod = raw[(raw["_v"] == "production") & raw["value"].notna()].copy()
    prod["_y"] = pd.to_numeric(prod["year"], errors="coerce")
    s_lb = ind[ind["item"] == "sugar raw centrifugal"]
    lbmap = {int(y): float(v) for y, v in
             zip(pd.to_numeric(s_lb["year"], errors="coerce"), s_lb["value"]) if pd.notna(y)}
    for lab, want_exact, want_shared in (("dutch java and madura", 29, 29),
                                         ("dutch east indies", 0, 0),
                                         ("dutch east indies: outer provinces", 0, 0)):
        g = prod[(prod["_c"] == lab) & (prod["product"] == "sugar: cane") & prod["_y"].notna()]
        per_year = g.groupby("_y")["value"].apply(list)
        shared = [y for y in per_year.index if int(y) in lbmap]
        exact = [y for y in shared if any(abs(v - lbmap[int(y)]) < 0.05 for v in per_year[y])]
        out.append((f"sugar vs `{lab[:22]}`", f"{len(exact)}/{len(shared)}",
                    f"{want_exact}/{want_shared}"))

    # 4. the additive cell: a sum that exists in no raw row
    soy = prod[prod["product"] == "soybean"]
    def _s(lab):
        g = soy[(soy["_c"] == lab) & (soy["_y"] == 1939)]
        return float(g["value"].sum()) if len(g) else 0.0
    jm, bl = _s("dutch java and madura"), _s("dutch bali and lombok")
    # UNIT IS PART OF THE KEY. Without it this sums the 1939 area row (431,000 ha) into the
    # production row (332,500 t) and reports 763,500 -- which the re-test caught on the first run.
    lb39 = ind[(ind["item"] == "soybeans") & (ind["unit"] == "tonnes")
               & (pd.to_numeric(ind["year"], errors="coerce") == 1939)]
    allv = pd.to_numeric(raw["value"], errors="coerce")
    ally = pd.to_numeric(raw["year"], errors="coerce")
    out += [("soybeans 1939 java+madura", jm, 317600.0),
            ("  bali+lombok", bl, 14900.0),
            ("  their sum", jm + bl, 332500.0),
            ("  layer-B value", float(lb39["value"].sum()), 332500.0),
            # the sum exists in no single raw row, which is what makes it a composition rather
            # than a copy -- and it is the claim a value-matching attribution test cannot reach
            ("  raw rows = 332,500 at 1939",
             int(len(raw[((allv - 332500).abs() < 0.5) & (ally == 1939)])), 0)]
    return out, ("sugar is java+madura alone in 29 of 29 dated years; soybeans 1939 is java+madura "
                 "PLUS bali+lombok, a sum carried by no raw row -- so the label is not one territory")


def check_iia_czechoslovakia_beans_component(ctx):
    """layer-B iia Czechoslovak `beans, dry` is ONE of two raw series; juan is their sum.

    NOT A PUBLISHER DISAGREEMENT, which is how it presents. The IIA yearbooks print TWO
    `beans: dried` rows for `czechoslovakia` in every year from 1934 -- one small, one large -- and
    layer B keeps the SMALLER while juan carries their SUM. At 1933 the raw prints a single value
    and both sources publish it identically, which is why the series agree exactly there and
    diverge from 1934 on.

    THE IDENTITY IS EXACT ON BOTH AXES, 12 of 12 years each, so this is arithmetic rather than
    inference: juan == small + large, and layer-B iia == small. Testing the identity is what
    distinguishes a dropped component from two publishers differing -- a magnitude argument could
    not, and the ratio alone (8x-14x on area, 3x-4x on production) looks like a scale error while
    being nothing of the kind.

    WHY THE TWO RATIOS DIFFER, which is the tell that it is not a scale bug: the dropped component
    has a lower yield than the kept one, so area and production are dropped in different
    proportions. A single multiplier would move both alike.

    NOT CLAIMED: which territories the two rows are. The raw carries one label, `czechoslovakia`,
    for both, so the split is inside the yearbook's own table and this extract does not name it.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    import pandas as pd

    out = []
    r = raw[(raw["_c"] == "czechoslovakia") & (raw["_p"] == "beans: dried")].copy()
    r["_y"] = pd.to_numeric(r["year"], errors="coerce")
    m = ctx["matched"]
    if m is None:
        return None
    m = m[m.whep_code.notna() & m.value.notna()]
    for var, unit in (("area", "ha"), ("production", "tonnes")):
        b = r[(r["_v"] == var) & r["_y"].notna()]
        J = {int(x.year): float(x.value) for x in
             m[(m.source == "juan") & (m["item"] == "beans, dry") & (m["unit"] == unit)
               & (m.country.astype(str).str.lower() == "czechoslovakia")].itertuples()
             if pd.notna(x.year)}
        I = {int(x.year): float(x.value) for x in
             m[(m.source == "iia") & (m["item"] == "beans, dry") & (m["unit"] == unit)
               & (m.country.astype(str).str.lower() == "czech republic")].itertuples()
             if pd.notna(x.year)}
        two = sums = smalls = 0
        for y in sorted({int(v) for v in b["_y"]}):
            vs = sorted(float(v) for v in b[b["_y"] == y]["value"].dropna())
            if len(vs) != 2:
                continue
            two += 1
            sums += abs(vs[0] + vs[1] - J.get(y, -1)) < 0.5
            smalls += abs(vs[0] - I.get(y, -1)) < 0.5
        out += [(f"{var}: raw years with TWO values", two, 12),
                (f"  juan == small + large", sums, 12),
                (f"  layer-B iia == the SMALLER", smalls, 12)]
    # 1933, the single-valued year both sources agree on -- the control
    for var, unit, want in (("area", "ha", 7000.0), ("production", "tonnes", 6600.0)):
        vs = [float(v) for v in r[(r["_v"] == var) & (r["_y"] == 1933)]["value"].dropna()]
        out.append((f"1933 raw {var} values", len(vs), 1))
        out.append((f"  its value", vs[0] if vs else 0.0, want))
    return out, ("iia publishes the smaller of two raw Czechoslovak bean series and juan their sum, "
                 "exactly, 12 of 12 years on each axis; 1933 has one raw value and agrees")


def check_iia_yugoslavia_sunflower_x10(ctx):
    """iia's Yugoslav sunflower production is ten times too small, and the paired area proves it.

    THE AREA AGREES EXACTLY. iia and juan both carry 19,000 ha for 1939; only production differs,
    1,900 t against 27,300 t. So this cannot be a territory or scope difference -- those move both
    axes -- and it is the one situation where magnitude reasoning is legitimate, because the ratio
    is fixed by agronomy rather than chosen by an economy.

    0.10 t/ha IS NOT A SUNFLOWER YIELD. juan's own Yugoslav series runs 0.63-1.21 t/ha across
    1949-1957 and 1.44 in 1939. Multiplying iia's production by ten gives 1.00 t/ha, inside that
    range -- and the residual difference from juan is then an ordinary cross-source gap rather than
    an impossibility.

    BOTH IIA CELLS CARRY THE SAME DEFECT, which is what makes it a series fault rather than a
    transcription slip: the dated 1939 row and the volume's period row are 19,000/1,900 and
    8,000/800, and both give exactly 0.10.
    """
    raw = ctx["raw"]
    import pandas as pd

    m = ctx["matched"]
    if m is None:
        return None
    m = m[m.whep_code.notna() & m.value.notna()]
    # `_y` is not one of the columns the harness precomputes (it supplies _c, _p, _v only), so
    # derive it here rather than assuming it -- the first version of this check raised KeyError.
    r = raw[(raw["_c"] == "yugoslavia")
            & raw["product"].astype(str).str.contains("sunflower", case=False, na=False)].copy()
    r["_y"] = pd.to_numeric(r["year"], errors="coerce")
    # ROWS, not year-cells: two years (dated 1939 and the volume period row) x two variables
    # (area, production). Pinned as 4 after a first version said 2 and the re-test caught it.
    out = [("raw yugoslavia sunflower rows", len(r), 4),
           ("  distinct year-cells", len({("period" if pd.isna(v) else int(v))
                                          for v in r["_y"]}), 2)]
    cells = {}
    for _, x in r.iterrows():
        tag = int(x["_y"]) if pd.notna(x["_y"]) else "period"
        cells.setdefault(tag, {})[x["_v"]] = float(x["value"])
    for tag, want_a, want_p in ((1939, 19000.0, 1900.0), ("period", 8000.0, 800.0)):
        d = cells.get(tag, {})
        a, pr = d.get("area", 0.0), d.get("production", 0.0)
        out += [(f"{tag} raw area", a, want_a), (f"  production", pr, want_p),
                (f"  implied yield t/ha", round(pr / a, 2) if a else 0.0, 0.1)]
    j = m[(m.source == "juan") & (m["item"] == "sunflower seed")
          & (m.country.astype(str).str.lower() == "yugoslav sfr")]
    j39a = j[(j["unit"] == "ha") & (pd.to_numeric(j["year"], errors="coerce") == 1939)]["value"].sum()
    j39p = j[(j["unit"] == "tonnes") & (pd.to_numeric(j["year"], errors="coerce") == 1939)]["value"].sum()
    out += [("juan 1939 area -- IDENTICAL to iia", float(j39a), 19000.0),
            ("  juan 1939 production", float(j39p), 27300.0),
            ("  juan implied yield", round(float(j39p) / float(j39a), 2), 1.44),
            ("iia yield x10 correction", round(1900.0 * 10 / 19000.0, 2), 1.0)]
    return out, ("area agrees to the digit and production is 14.4x apart; 0.10 t/ha against juan's "
                 "0.63-1.44 makes the iia figure impossible, and x10 lands it at 1.00")


def check_nga_1950_livestock_broadcast(ctx):
    """Four mitchell nigeria livestock items read exactly 13,000 head in 1950.

    THE CROSS-ITEM AGREEMENT IS THE DIAGNOSIS, and it is the whole method: cattle, goats, sheep and
    swine have wildly different populations, so four unrelated species cannot agree to the digit.
    Their own medians elsewhere are 2.94M, 5.02M, 1.89M and 51,000 -- 226x, 386x, 145x and 4x above
    13,000.

    SWINE AT 4x IS WHY A PER-SERIES TEST CANNOT FIND THIS. 13,000 against a 51,000 median is low and
    entirely possible; no spike, constant-run or magnitude screen would convict it, and it is only
    guilty by being the same number as the other three. The corollary is that the repair must cover
    it too, which a per-cell verdict would not.

    TWO CONTROLS, both inside the same year. Asses (941,000) and horses (212,000) at 1950 are NOT
    13,000, so this is not a whole-column failure -- it is four of the six livestock items. And the
    non-livestock items at 1950 are varied and plausible (millet 973,000, sorghum 1,862,000, cacao
    112,000), so the year itself is sound.

    13,000 IS NOT AN ANOMALOUS NUMBER IN THIS LABEL, which matters for stating the claim correctly:
    it also appears four times as `cotton lint` in tonnes (1908, 1946-1948), where it is a perfectly
    ordinary tonnage. The claim is the agreement among the four livestock items at one year, not
    that 13,000 is odd.

    THIRD INSTANCE OF A REGISTERED CLASS -- see ind-1947-livestock-broadcast-3000 (eight items) and
    som-1959-livestock-broadcast-15000 (four items). A third label and a third decade is what makes
    it a class rather than three incidents. Found 2026-09-01 through issue 612's unit normalisation,
    which is the first thing to make mitchell and fao1952 comparable on `heads` at all.
    """
    m = ctx["matched"]
    if m is None:
        return None
    import pandas as pd

    g = m[m.whep_code.notna() & m.value.notna()]
    g = g[(g.source == "mitchell") & (g.country.astype(str).str.lower() == "nigeria")]
    out = []
    BROADCAST = ("cattle", "goats", "sheep", "swine / pigs")
    for item in BROADCAST:
        v = g[(g["item"] == item) & (g["year"] == 1950)]["value"]
        out.append((f"1950 {item[:16]}", float(v.iloc[0]) if len(v) else 0.0, 13000.0))
    # each item's own median in every OTHER year, and the factor
    for item, want_med, want_ratio in (("cattle", 2942000.0, 226), ("goats", 5024500.0, 386),
                                       ("sheep", 1888000.0, 145), ("swine / pigs", 51000.0, 4)):
        o = g[(g["item"] == item) & (g["value"] != 13000)]["value"]
        med = float(o.median()) if len(o) else 0.0
        out += [(f"  {item[:14]} median elsewhere", med, want_med),
                (f"    factor", int(round(med / 13000.0)) if med else 0, want_ratio)]
    # controls: two livestock items in the SAME year that are not 13,000
    for item, want in (("asses", 941000.0), ("horses", 212000.0)):
        v = g[(g["item"] == item) & (g["year"] == 1950)]["value"]
        out.append((f"1950 {item} -- a control", float(v.iloc[0]) if len(v) else 0.0, want))
    # 13,000 elsewhere in this label is legitimate cotton tonnage, not livestock
    o = g[g["value"] == 13000]
    out += [("rows equal to 13,000 in all", len(o), 8),
            ("  of those, livestock", int((o["item"].isin(BROADCAST)).sum()), 4),
            ("  the rest, all cotton lint", int((o["item"] == "cotton lint").sum()), 4)]
    return out, ("four species agreeing to the digit at one year, with asses and horses in the same "
                 "year untouched; swine's own factor is only 4x, so no per-series test reaches it")


def check_mitchell_japan_rye_is_not_rye(ctx):
    """mitchell's Japanese `rye` is ~565,000 ha where fao1952 reports 3,000-6,000.

    THE CONTROL IS WHAT CONVICTS, and it is unusually strong. The two sources agree TO THE DIGIT on
    Japanese rice paddy in all three shared years (2,970,000 / 2,994,000 / 3,004,000, ratio 1.000)
    and to 0.3% on sweet potatoes -- so they describe the same country, the same years and the same
    conventions, and neither extraction is broken. Against that, differing 94x-186x on one item is
    an item-IDENTITY problem, not a data-quality gradient.

    NEITHER SIDE IS INTERNALLY IMPOSSIBLE, which is why no per-series test finds this. mitchell's
    series runs smoothly from 1877 to 1960 at 400,000-720,000 ha with yields of 1.0-2.5 t/ha, and
    fao1952's 6,000 ha at 1.33 t/ha is equally ordinary. There is no spike, no constant run, no
    impossible yield. Only the cross-source comparison reaches it.

    NOT CLAIMED: what mitchell's series actually is. The magnitude points to naked barley -- mitchell
    carries a SEPARATE `barley` at 420,000-440,000 ha, the two sum to 979,000-1,020,000, and fao1952
    carries NO barley for Japan at all -- but that is an inference from size, which this repo has
    been wrong about before. What is established is the negative: it is not rye.

    Consequence for the panel: any aggregation over Japanese rye takes mitchell's figure, so the
    published series is ~100x the crop it names.
    """
    m = ctx["matched"]
    if m is None:
        return None
    import pandas as pd

    g = m[m.whep_code.notna() & m.value.notna()]
    jp = g[g.country.astype(str).str.lower().str.contains("japan")]

    def ser(src, item, unit):
        h = jp[(jp.source == src) & (jp["item"] == item) & (jp["unit"].astype(str) == unit)]
        return {int(r.year): float(r.value) for _, r in h.iterrows() if pd.notna(r.year)}

    out = []
    # the control: agreement on other crops, same years
    for mi, fi, want in (("rice, paddy", "rice paddy", (1.0, 1.0, 1.0)),
                         ("sweet potatoes", "sweet potatoes yams", (1.002, 1.003, 1.0))):
        M, F = ser("mitchell", mi, "ha"), ser("fao1952", fi, "1000 hectares")
        for y, w in zip((1949, 1950, 1951), want):
            r = round(M[y] / (F[y] * 1000), 3) if (y in M and y in F and F[y]) else 0.0
            out.append((f"{mi[:12]} {y} ratio", r, w))
    # the disagreement
    M, F = ser("mitchell", "rye", "ha"), ser("fao1952", "rye", "1000 hectares")
    for y, w in ((1949, 94.2), (1950, 98.5), (1951, 186.3)):
        out.append((f"rye {y} ratio", round(M[y] / (F[y] * 1000), 1) if (y in M and y in F and F[y]) else 0.0, w))
    for y, w in ((1949, 6.0), (1950, 6.0), (1951, 3.0)):
        out.append((f"  fao1952 rye {y} (1000 ha)", F.get(y, 0.0), w))
    # the size argument, recorded but NOT claimed as the identification
    B = ser("mitchell", "barley", "ha")
    for y, w in ((1949, 1005000.0), (1950, 1020000.0), (1951, 979000.0)):
        out.append((f"  mitchell barley + `rye` {y}", B.get(y, 0.0) + M.get(y, 0.0), w))
    out.append(("fao1952 barley items for japan",
                len({str(i) for i in jp[jp.source == "fao1952"]["item"] if "barl" in str(i).lower()}), 0))
    return out, ("agreement to the digit on rice paddy and 0.3% on sweet potatoes, against 94x-186x "
                 "on rye -- so the sources are sound and the item label is not")


def check_iia_olives_1934_1938_scale(ctx):
    """The iia `1934-1938` olive PRODUCTION averages are scrambled ~100x, in both directions.

    THREE INDEPENDENT REFERENCES AGREE ON EACH CELL, which is what makes this a diagnosis and not a
    magnitude complaint: the series' own dated years inside the span, the same series' `1928-1932`
    average from the previous volume, and fao1952's own `1934-1938` average. For israel the dated
    mean is about 30,660 t and fao1952 says 31,000 -- to within 1% -- while the period row reads
    3,075,400.

    THE PAIRED AREA AXIS IS CLEAN IN EVERY CASE, and that is the load-bearing control. israel's
    period area (52,000 ha) matches its own dated mean (51,750); italy's 1,358,000 ha follows its
    1928-32 figure of 1,530,000; the USA's 10,000 follows 12,000. So this is not a territory, a
    scope or a label problem -- those move both axes -- and the implied yields are physically
    impossible: israel at 3,075,400 / 52,000 = 59.1 t/ha where olives yield 1-3.

    BOTH DIRECTIONS, SAME VOLUME, SAME ITEM. israel, the USA and libya are inflated; ITALY IS
    DEFLATED, 10,300 t against its own 1,325,100 and fao1952's 1,267,000. A single multiplier cannot
    produce both, so this is a scale scramble rather than a unit error, and the correct value is
    recoverable in each case because two references agree on it.

    libya is registered separately (iia-libya-olives-1934-1938-inflated) and one of its figures is
    pinned here too, as the fourth instance -- the point of this entry is the CLASS, and a class of
    one is an incident. That entry owns the full libya analysis; this one owns the class.

    AND IT DOES NOT CONTRADICT THAT ENTRY, which is worth stating because it looks as though it
    might. The libya entry pins "labels breaking >=50x: 0" with a median era break of 1.195, and
    that measurement is over DATED means either side of 1934 -- it says the dated olive series are
    not era-scaled, which remains true. This entry is about the PERIOD rows, a different axis, and
    the two together are the actual picture: the dated series are sound and the `1934-1938` averages
    computed from them are not.
    """
    raw, lb = ctx["raw"], ctx["panel"]
    import pandas as pd

    g = lb[(lb["source"] == "iia") & (lb["item"] == "olives")]
    fa = lb[(lb["source"] == "fao1952")
            & lb["item"].astype(str).str.contains("olive", case=False, na=False)]

    def per(frame, label, unit, span):
        h = frame[(frame["country"].astype(str).str.lower() == label)
                  & (frame["unit"].astype(str) == unit) & (frame["year"].isna())
                  & (frame["period"].astype(str) == span)]
        return float(h["value"].max()) if len(h) else 0.0

    out = []
    # inflated: the period row, its own previous-volume average, and fao1952's
    for lab, want_p, want_prev, want_fao in (("israel", 3075400.0, 12300.0, 31.0),
                                             ("united states of america", 1127200.0, 18700.0, 27.0),
                                             ("libya", 1610700.0, 19300.0, 11.0)):
        out += [(f"{lab[:14]} 1934-38 production", per(g, lab, "tonnes", "1934-1938"), want_p),
                (f"  its 1928-32 average", per(g, lab, "tonnes", "1928-1932"), want_prev)]
        f2 = fa[(fa["country"].astype(str).str.lower().str.startswith(lab.split()[0]))
                & (fa["year"].isna())]
        out.append((f"  fao1952 1934-38 (1000 t)", float(f2["value"].max()) if len(f2) else 0.0, want_fao))
    # deflated: italy, the direction that rules out a single multiplier
    out += [("italy 1934-38 production -- LOW", per(g, "italy", "tonnes", "1934-1938"), 10300.0),
            ("  its 1928-32 average", per(g, "italy", "tonnes", "1928-1932"), 1325100.0)]
    f2 = fa[(fa["country"].astype(str).str.lower().str.startswith("italy")) & (fa["year"].isna())]
    out.append(("  fao1952 1934-38 (1000 t)", float(f2["value"].max()) if len(f2) else 0.0, 1267.0))
    # THE CONTROL: the paired AREA axis is clean for all four
    for lab, want in (("israel", 52000.0), ("italy", 1358000.0),
                      ("united states of america", 10000.0), ("libya", 61000.0)):
        out.append((f"AREA 1934-38 {lab[:12]} -- clean", per(g, lab, "ha", "1934-1938"), want))
    # and israel's own dated mean inside the span, the third reference
    d = g[(g["country"].astype(str).str.lower() == "israel") & (g["unit"].astype(str) == "tonnes")
          & g["year"].notna()]
    d = d[pd.to_numeric(d["year"], errors="coerce").between(1934, 1938)]
    out += [("israel dated 1934-38 rows", len(d), 5),
            ("  their mean", round(float(d["value"].mean()), 1), 30660.0),
            ("  israel implied yield t/ha", round(3075400.0 / 52000.0, 1), 59.1)]
    return out, ("three references agree on each cell and the paired area axis is clean in all four, "
                 "so only production is scrambled -- israel/USA/libya up, ITALY down")


def check_iia_sugar_1934_1938_deflated(ctx):
    """Two iia sugar labels' `1934-1938` averages are deflated ~180x, and australia has two more.

    THE PERIOD SEQUENCE IS THE ARGUMENT, not the size of any one cell. Each label's own averages run
    at a consistent scale across four volumes and then collapse in the last one, while fao1952's
    `1934-1938` figure agrees with the earlier volumes rather than with iia's:

        argentina   175,862 -> 398,986 -> 356,500 -> 2,200      fao1952 410,000
        australia     922(!) -> 511,803 -> 524,800 -> 4,400      fao1952 752,000

    AUSTRALIA CARRIES TWO FURTHER FAULTS, and the second one names a mechanism.

    First, a DATED BLOCK: seven consecutive years 1913-1919 read 569-1,979 t between 131,961 (1912)
    and 165,616 (1920) -- a factor of 98 against the surrounding median of 193,658. Seven consecutive
    years is not a transcription slip.

    Second, THE `1909-1913` AVERAGE IS NOT AN AVERAGE. It reads 922.5 where the mean of its own five
    dated years is 142,581.8 -- and 922.5 is exactly the 1913 dated value, the one deflated year in
    the span. So that period row copies a single year rather than averaging the span, and it copied
    the broken one. Recorded as an observation about this cell; whether other period rows do the same
    is untested here.

    NOT CLAIMED: a common cause. The 1913-1919 dated block and the 1934-1938 average sit in different
    volumes, and nothing here shows one mechanism behind both.
    """
    lb = ctx["panel"]
    import pandas as pd

    g = lb[(lb["source"] == "iia") & (lb["item"] == "sugar raw centrifugal")]
    fa = lb[(lb["source"] == "fao1952")
            & lb["item"].astype(str).str.contains("sugar", case=False, na=False)]

    def per(label, span):
        h = g[(g["country"].astype(str).str.lower() == label) & (g["year"].isna())
              & (g["period"].astype(str) == span)]
        return round(float(h["value"].max()), 1) if len(h) else 0.0

    out = []
    for lab, want in (("argentina", (175862.4, 398986.2, 356500.0, 2200.0, 410.0)),
                      ("australia", (922.5, 511802.8, 524800.0, 4400.0, 752.0))):
        for span, w in zip(("1909-1913", "1925-1929", "1928-1932", "1934-1938"), want):
            out.append((f"{lab[:9]} {span}", per(lab, span), w))
        f2 = fa[(fa["country"].astype(str).str.lower().str.startswith(lab[:6])) & (fa["year"].isna())]
        out.append((f"  fao1952 1934-38 (1000 t)", float(f2["value"].max()) if len(f2) else 0.0, want[4]))

    # australia's dated block
    d = g[(g["country"].astype(str).str.lower() == "australia") & g["year"].notna()].copy()
    d["y"] = pd.to_numeric(d["year"], errors="coerce")
    blk = d[d.y.between(1913, 1919)]
    nrm = d[(d.y.between(1909, 1912)) | (d.y.between(1920, 1932))]
    out += [("australia dated 1913-1919 rows", len(blk), 7),
            # exact floats: an earlier draft pinned 1979 and 193658, truncated by an int() in the
            # exploratory query, and the re-test caught both.
            ("  their maximum", float(blk["value"].max()) if len(blk) else 0.0, 1979.3),
            ("  surrounding median", float(nrm["value"].median()) if len(nrm) else 0.0, 193658.5),
            ("  factor", int(round(nrm["value"].median() / blk["value"].max())) if len(blk) else 0, 98)]
    # the period row that is not an average
    m0913 = round(float(d[d.y.between(1909, 1913)]["value"].mean()), 1)
    out += [("australia dated 1909-1913 mean", m0913, 142581.8),
            ("  but its 1909-1913 period row", per("australia", "1909-1913"), 922.5),
            ("  == its 1913 dated value", round(float(d[d.y == 1913]["value"].iloc[0]), 1), 922.5),
            ("argentina dated rows (all years)",
             len(g[(g["country"].astype(str).str.lower() == "argentina") & g["year"].notna()]), 1)]
    return out, ("both labels' 1934-38 averages collapse ~180x against their own earlier volumes and "
                 "against fao1952; australia also has a 7-year dated block at 98x and a period row "
                 "that copies one deflated year instead of averaging")


CHECKS = {
    "iia-zero-refuted-by-paired-axis": check_zero_refuted_by_paired_axis,
    "iia-sugar-1934-1938-deflated": check_iia_sugar_1934_1938_deflated,
    "iia-olives-1934-1938-scale-scrambled": check_iia_olives_1934_1938_scale,
    "mitchell-japan-rye-is-not-rye": check_mitchell_japan_rye_is_not_rye,
    "nga-1950-livestock-broadcast-13000": check_nga_1950_livestock_broadcast,
    "iia-czechoslovakia-beans-component-only": check_iia_czechoslovakia_beans_component,
    "iia-yugoslavia-sunflower-production-x10": check_iia_yugoslavia_sunflower_x10,
    "iia-indonesia-is-java-and-madura": check_iia_indonesia_is_java_and_madura,
    "iia-attributable-single-cell-errors": check_attributable_single_cells,
    "constant-runs-two-proven-placeholders": check_constant_run_placeholders,
    "iia-corrupted-country-labels": check_corrupted_country_labels,
    "iia-wheat-is-spelt-and-meslin": check_wheat_is_spelt_and_meslin,
    "iia-tobacco-implausible-magnitudes": check_tobacco_era_scope,
    "fao1952-western-eastern-lost-germany-prefix": check_western_eastern_prefix,
    "iia-malawi-cotton-1934-1938-deflated": check_malawi_cotton_deflation,
    "iia-error-inde-is-india": check_error_inde_is_india,
    "iia-libya-olives-1934-1938-inflated": check_libya_olives_period_cell,
    "fao1952-china-whole-and-five-parts": check_china_whole_and_five_parts,
    "fao1952-tractors-total-beside-its-own-parts": check_tractors_total_beside_parts,
    "fao1952-germany-western-cheese-implausible": check_germany_western_cheese,
    "iia-algeria-civil-basis-continues-to-1925": check_algeria_civil_basis_span,
    "fao1952-estates-label-lost-country-prefix": check_estates_label_prefix,
    "fao1952-china-livestock-cells-implausible": check_fao1952_china_label,
    "fao1952-label-carries-a-wrong-group-heading": check_fao1952_wrong_group_heading,
    "fao1952-korea-rice-paddy-area-impossible": check_korea_rice_paddy_area,
    "iia-russia-asian-component-dropped": check_russia_asian_component,
    "layerb-nested-reporting-levels-one-polity": check_nested_reporting_levels,
    "iia-layerb-magnitude-scale-inconsistent": check_iia_scale_is_common,
    "iia-hops-x100": check_hops_x100_and_area_x10,
    "fao1952-hemp-germany-label-glued": check_hemp_germany_glued,
    "iia-item-series-switch-raw-products": check_item_product_switches,
    "mitchell-flax-fibre-area-is-linseed": check_mitchell_flax_is_linseed,
    "iia-flax-fibre-item-is-mostly-linseed": check_iia_flax_is_mostly_linseed,
    "fao1952-malaya-female-agric-1937-is-total": check_malaya_female_agric_is_total,
    "nga-1941-1945-cotton-area-zero": check_nigeria_cotton_area_zero,
    "cze-1910-rye-area-orphan-3ha": check_cze_1910_rye_orphan,
    "iia-1933-x10-wrong-volume-cells": check_1933_x10_provenance_linked,
    "nru-1933-phosphate-transposed-with-australia": check_nauru_1933_transposition,
    "ltu-1933-sugar-wrong-volume": check_lithuania_1933_sugar_volume,
    "ind-1947-livestock-broadcast-3000": check_india_1947_broadcast,
    "som-1959-livestock-broadcast-15000": check_somalia_1959_broadcast,
    "rus-1918-is-karafuto-prefecture": check_russia_1918_is_karafuto,
    "chn-1895-1913-groundnut-outlier-data-error": check_china_groundnut_audit,
    "iia-reunion-tobacco-baseline-contaminated": check_reunion_tobacco_baseline,
    "chn-1949-1950-goats-mitchell-data-error": check_china_goats_x1001,
    "australia-fiji-fao1952-data-error": check_australia_fiji_merged,
    "united-states-california-double-count": check_california_double_count,
    "fao1952-bwi-bahamas-land-area-x10": check_bahamas_area_x10,
    "fao1952-bwi-jamaica-dropped-leading-digit": check_jamaica_dropped_digit,
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
    stated = os.path.join(REPO, "data/final/source_stated_areas.csv")
    basis = os.path.join(REPO, "data/final/source_stated_area_basis.csv")
    # `before_1961.csv` is an 18 MB machine-local input, deliberately gitignored ("Untrack the source
    # datasets, keeping them local"), so it is OPTIONAL rather than required: adding it to the required
    # list above would make this whole tool SKIP on any machine without it. A check that needs it
    # returns None, and main() reports those separately instead of counting them as re-tested -- an
    # absent input must not read as a passing claim.
    pre1961 = os.path.join(REPO, "data/external/before_1961.csv")
    ctx = {"raw": raw, "panel": pd.read_parquet(a.layer_b), "era": era,
           "stated": list(csv.DictReader(open(stated, newline="", encoding="utf-8")))
           if os.path.exists(stated) else None,
           "basis": list(csv.DictReader(open(basis, newline="", encoding="utf-8")))
           if os.path.exists(basis) else None,
           "pre1961": pd.read_csv(pre1961, low_memory=False) if os.path.exists(pre1961) else None,
           # matched_rows carries the polity assignment, which the panel does not; an entry keyed on
           # (polity, source, item, ...) cannot be re-tested without it.
           "matched": pd.read_parquet(matched_path) if os.path.exists(matched_path) else None}

    MATCHED_DF[0] = ctx["matched"]

    with open(ERRORS, newline="", encoding="utf-8") as fh:
        entries = list(csv.DictReader(fh))
    ids = {r["issue_id"] for r in entries}

    problems, tested, skipped = [], 0, []
    for eid, fn in sorted(CHECKS.items()):
        if eid not in ids:
            problems.append(f"{eid}: has a re-test here but no longer exists in data_errors.csv")
            continue
        out = fn(ctx)
        if out is None:
            skipped.append(eid)
            print(f"  SKIP {eid[:42]:44}re-test needs a local input absent on this machine")
            continue
        claims, note = out
        for label, now, stated in claims:
            tested += 1
            ok = now == stated
            print(f"  {'ok  ' if ok else 'FAIL'} {eid[:42]:44}{label[:26]:28}{now:>9} (stated {stated})")
            if not ok:
                problems.append(f"{eid}: {label} is now {now}, the entry states {stated}")
        print(f"       -> {note}")

    if skipped:
        print(f"\n{len(skipped)} entr(y/ies) NOT re-tested here for want of a local input: "
              f"{', '.join(sorted(skipped))}")
    print(f"\n{len(CHECKS) - len(skipped)} entr(ies) re-tested over {tested} claim(s); "
          f"{len(ids) - len(CHECKS)} of {len(ids)} entries are not yet re-tested -- unreached rather "
          f"than uncoverable; see the docstring")
    if problems:
        print(f"\nFAIL: {len(problems)} claim(s) no longer reproduce", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: every re-testable claim in data_errors.csv still reproduces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
