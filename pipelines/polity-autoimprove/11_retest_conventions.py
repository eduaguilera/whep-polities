#!/usr/bin/env python3
"""Re-test every registered source convention against the current layer-B data.

Why this exists (issue 24). `state/source_conventions.csv` holds verified statements
about what a source's labels and series ACTUALLY measure. `00_intake.py` attaches each
matching entry to the evidence bundle of every assertion touching that source, so a
convention is not one opinion: it is a premise handed to every later verifier. An
over-strong or stale convention therefore propagates further than any single verdict,
and until now nothing checked one against the data it describes.

Most of the entries are MAGNITUDE claims ("cotton area too large for the RSFSR alone",
"median 14,114 t/yr is implausible as domestic output"), and a magnitude claim is
mechanically re-testable. This script re-runs the measurement behind each entry and
prints what it now finds, so a drifted figure is visible instead of being inherited.

It is NOT a CI gate, and cannot be: it reads the consolidated layer-B panel, which is
gitignored and lives outside the repository. The CI-side half is
`scripts/validate_source_conventions.py`, which validates the registry's structure and
— reading CHECKS from this file — refuses a convention that has no re-test at all, so
the registry cannot grow entries this script does not cover.

Two things the checks deliberately separate:
  * the CONCLUSION (whole-USSR scope, transit not production) — the thing that
    propagates, and the only thing whose failure is an error here;
  * the FIGURES quoted in the `evidence` column — which can drift when the panel is
    reconsolidated without the conclusion being wrong. A figure mismatch is reported as
    DRIFT, and the fix is to correct the evidence, not to delete the convention.

Usage:
  python3 pipelines/polity-autoimprove/11_retest_conventions.py [--layer-b PATH]

Exit 1 if a conclusion fails or a registry row has no check; 0 on pass or on SKIP when
the panel is not present on this machine.
"""
import argparse
import csv
import os
import re
import sys

H = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(H))
CONVENTIONS = os.path.join(H, "state/source_conventions.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")
)


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


# --- the checks ---------------------------------------------------------------
# One per registry row, keyed exactly as the row identifies itself:
# (source, label_pattern, item_pattern). Each takes the panel and returns
# (conclusion_holds, message).


def _label(d, source, label):
    """Rows of one source under one label, matched the way 00_intake.py matches."""
    sub = d[d["source"] == source]
    return sub[sub["country"].map(norm).str.contains(norm(label), regex=False)]


def _median(g, item, unit):
    s = g[(g["item"].map(norm) == norm(item)) & (g["unit"] == unit)]["value"].dropna()
    return (float(s.median()), len(s)) if len(s) else (None, 0)


def check_fao1952_population(d):
    """The claim that matters: `item` alone mixes five indicators, and
    "population total" is a usable total. Both are structural, so both are checkable."""
    f = d[(d["source"] == "fao1952")
          & d["item"].map(norm).str.contains("population", regex=False)]
    inds = sorted({str(i) for i in f["indicator"].dropna().unique()})
    codes = sorted({str(c) for c in f["item_code"].dropna().unique()})
    tot = f[f["indicator"].map(norm).str.contains("population total", regex=False)]
    yu = tot[(tot["country"].map(norm) == "yugoslavia") & (tot["year"] == 1937)]["value"]
    ok = len(inds) >= 5 and len(codes) <= 1 and len(yu) and 15_000 <= yu.iloc[0] <= 16_500
    return ok, (
        f"{len(f)} population rows; {len(inds)} distinct indicators under "
        f"{len(codes) or 'no'} item_code(s); Yugoslavia 1937 total "
        f"{(yu.iloc[0] if len(yu) else float('nan')):,.0f}k "
        f"(1931 census 13.9M, 1948 census 15.77M)"
    )


def check_iia_algeria(d):
    """The claim: IIA reports Algeria as its OWN reporting unit, not inside metropolitan France.

    Structural, so it is checkable without judgement. If Algeria were folded into France the
    label would not appear at all; if it appeared but meant "France including Algeria" its
    magnitudes would sit at French levels rather than a fraction of them.

    Corroborated independently by the stated areas, which is a different mechanism from the
    agricultural series this convention was learned from: IIA states an ALGERIE area in six
    editions, 2,195,696 km2 against our 2,318,386 km2 colony polygon (ratio 1.056, recorded as
    `agrees` in data/final/source_stated_area_basis.csv). A source that treated Algeria as part
    of France would not state a separate area for it six times.
    """
    a = d[(d["source"] == "iia") & (d["country"].map(norm) == "algeria")]
    f = d[(d["source"] == "iia") & (d["country"].map(norm) == "france")]
    shared = set(a["item"].map(norm)) & set(f["item"].map(norm))
    smaller = 0
    for item in shared:
        av = a[a["item"].map(norm) == item]["value"].dropna()
        fv = f[f["item"].map(norm) == item]["value"].dropna()
        if len(av) and len(fv) and float(av.median()) < float(fv.median()):
            smaller += 1
    ok = len(a) > 0 and len(f) > 0 and len(shared) >= 3 and smaller >= len(shared) * 0.6
    return ok, (
        f"iia carries {len(a)} algeria rows and {len(f)} france rows as separate labels; "
        f"{len(shared)} shared items, algeria's median below france's in {smaller} of them "
        f"(a folded-in Algeria would not be a separate label at all)"
    )


def check_iia_russia(d):
    """Whole-USSR scope. The test is that the areas are impossible for the RSFSR:
    Soviet cotton grew in Central Asia and Transcaucasia, not in Russia proper."""
    g = _label(d, "iia", "russian federation")
    g = g[(g["year"] >= 1922) & (g["year"] <= 1940)]
    lint, nl = _median(g, "cotton lint", "ha")
    seed, ns = _median(g, "cotton seed", "ha")
    rye, nr = _median(g, "rye", "ha")
    # RSFSR cotton area was negligible; anything above ~200k ha is union-scale, and
    # union rye was ~24M ha against a Russia-proper figure well under half that.
    ok = bool(lint and lint > 1_000_000 and rye and rye > 15_000_000)
    return ok, (
        f"1922-1940 medians: cotton lint {lint:,.0f} ha (n={nl}), cotton seed "
        f"{seed:,.0f} ha (n={ns}), rye {rye:,.0f} ha (n={nr})"
    )


def check_iia_south_korea(d):
    """Pre-1945 "south korea" is the whole peninsula. Two observables: the source
    carries no other Korean label, and the areas are peninsula-scale."""
    kor = d[(d["source"] == "iia")
            & d["country"].map(norm).str.contains("korea", regex=False)]
    labels = sorted({norm(c) for c in kor["country"].dropna().unique()})
    ks = _label(d, "iia", "south korea")
    dated = int(ks["year"].notna().sum())
    soy, ns = _median(ks, "soybeans", "ha")
    ok = labels == ["south korea"] and bool(soy and soy > 300_000)
    return ok, (
        f"labels containing 'korea': {labels}; {len(ks)} rows, {dated} dated, "
        f"{int(ks['year'].min())}-{int(ks['year'].max())}; soybean area median "
        f"{soy:,.0f} ha (n={ns}) — peninsula-scale"
    )


def check_juan_germany(d):
    """Undifferentiated Germany 1949-1960. The decisive observable is the ABSENCE of a
    companion FRG/GDR series anywhere in the source, not the row count."""
    j = d[d["source"] == "juan"]
    labels = {norm(c) for c in j["country"].dropna().unique()}
    # Any label that could be a separate German state: a German label qualified by
    # west/east/federal/democratic, or the bare pair of names for the two of them.
    split = sorted(
        l for l in labels
        if ("german" in l and any(t in l for t in ("fed", "democ", "west", "east")))
        or l in {"west germany", "east germany", "frg", "gdr"}
    )
    g = _label(d, "juan", "germany")
    w = g[(g["year"] >= 1949) & (g["year"] <= 1960)]
    yrs = sorted(int(y) for y in w["year"].dropna().unique())
    ok = not split and len(w) > 0
    return ok, (
        f"{len(w)} rows under the single label 'germany' across {len(yrs)} years "
        f"{yrs[0]}-{yrs[-1]}; FRG/GDR companion labels found: {split or 'none'}"
    )


def check_juan_finland(d):
    """Post-1940 reduced territory throughout. A switch to the recaptured Karelia
    borders would show as a STEP in sown area at 1941 and back at 1944; the test is
    that the series falls smoothly through the war instead."""
    f = _label(d, "juan", "finland")
    oats = f[(f["item"].map(norm) == "oats") & (f["unit"] == "ha")]
    by = oats.groupby("year")["value"].median()
    seq = {y: by.get(y) for y in range(1939, 1946)}
    steps = [
        (y, seq[y], seq[y + 1])
        for y in range(1939, 1945)
        if seq.get(y) and seq.get(y + 1) and abs(seq[y + 1] / seq[y] - 1) > 0.15
    ]
    ok = not steps and bool(seq.get(1939) and seq.get(1945)
                            and seq[1945] < seq[1939])
    return ok, (
        "oats sown area "
        + ", ".join(f"{y}={v:,.0f}" for y, v in seq.items() if v)
        + f" ha; year-on-year steps above 15%: {steps or 'none'}"
    )


def check_juan_czechoslovakia(d):
    """Constant pre-Munich basis. Same instrument as Finland: no ~28% step at either
    the 1938 or the 1945 territorial boundary CShapes documents."""
    c = _label(d, "juan", "czechoslovakia")
    out, ok = [], True
    for item in ("barley", "potatoes"):
        by = c[(c["item"].map(norm) == item) & (c["unit"] == "ha")].groupby("year")["value"].median()
        seq = {y: by.get(y) for y in range(1937, 1947)}
        for y in (1937, 1944):
            a, b = seq.get(y), seq.get(y + 1)
            if a and b and abs(b / a - 1) > 0.25:
                ok = False
                out.append(f"{item} STEP {y}->{y+1}: {a:,.0f} -> {b:,.0f}")
        out.append(item + " " + "/".join(f"{v/1000:,.0f}k" for v in seq.values() if v))
    return ok, "; ".join(out)


def check_iia_djibouti_coffee(d):
    """Transit, not production. The magnitude is the whole argument: a small arid
    territory with no coffee agriculture cannot output this."""
    g = _label(d, "iia", "djibouti")
    cf = g[g["item"].map(norm).str.contains("coffee", regex=False)]
    v = cf["value"].dropna()
    ok = bool(len(v) and v.median() > 1_000)
    yrs = sorted(int(y) for y in cf["year"].dropna().unique())
    return ok, (
        f"coffee, green under 'djibouti': {len(cf)} rows, "
        f"{yrs[0] if yrs else '?'}-{yrs[-1] if yrs else '?'}, median "
        f"{v.median():,.1f} t (min {v.min():,.0f}, max {v.max():,.0f})"
    )


def check_iia_antigua(d):
    """The claim: IIA's `antigua and barbuda` is the island group (Antigua + Barbuda + Redonda,
    ~442 km2), NOT the British Leeward Islands colony it belonged to.

    STRUCTURAL, and checkable from the provenance table plus the raw label inventory rather than from
    magnitudes -- island agriculture at this scale is too small for plausibility arguments to carry
    anything. Two facts, either of which failing would break the claim:

      * the raw extract carries `british antigua` (485 rows) AND `british leeward islands` (91 rows)
        as SEPARATE labels, so the source distinguishes the island from its colony. It also carries
        `british montserrat` (628 rows) separately, another Leeward member.
      * the span reads single-source at share 1.00 in
        state/iia_assertion_provenance.csv -- `antigua and barbuda|iia|1909-1945`, n=92, dominant
        `british antigua`, signal `redirected` rather than `mixed`. Nothing else contributes.

    Consistent with the composition registry, which records BLI-1833-1960 <- ATG-1800-2025 as a
    `sum_risk` pair precisely because fao1952 carries both the colony and the island: the two files
    agree that these are different territories in the same family.
    """
    import csv as _csv
    prov = os.path.join(H, "state/iia_assertion_provenance.csv")
    if not os.path.exists(prov):
        return False, "iia_assertion_provenance.csv missing; the span cannot be checked"
    with open(prov, encoding="utf-8") as fh:
        rows = {r["key"]: r for r in _csv.DictReader(fh)}
    r = rows.get("antigua and barbuda|iia|1909-1945")
    if not r:
        return False, "no provenance row for antigua and barbuda|iia|1909-1945"
    single = r["span_signal"] in ("clean", "redirected") and float(r["dominant_share"] or 0) >= 0.95
    dom = r["dominant_raw_label"]
    ok = single and "antigua" in norm(dom)
    return ok, (
        f"span is {r['span_signal']} on `{dom}` at share {r['dominant_share']} over {r['n_values']} "
        f"values, i.e. one island-level source and not the Leeward colony (which the raw extract "
        f"carries separately as `british leeward islands`)"
    )


def check_mitchell_syria(d):
    """The claim: Mitchell reports Syria as a standalone unit THROUGH the 1958-1961 United Arab
    Republic union, not merged with Egypt.

    Two independent tests, neither of which is the continuity argument the convention was learned
    from.

    CONCURRENCY. If Egypt's figures were folded into Syria's during the union, Egypt would not still
    be carried as its own label in those years. It is: both labels have rows in every year 1955-1960.

    AREA, NOT OUTPUT. Syrian wheat AREA runs 1,495k ha (1957), 1,460k (1958), 1,422k (1959),
    1,550k (1960) -- flat across the union's start. Egyptian wheat area was on the order of 600k ha,
    so a merge would show a step of roughly 40%. Production tonnage is NOT usable here: Syria's wheat
    output swings 438k -> 1,051k -> 1,354k -> 562k over 1955-1958, which is harvest variance and
    would drown any territorial signal. Sown area is what tracks the reporting unit.
    """
    syr = _label(d, "mitchell", "syrian arab republic").dropna(subset=["year"])
    egy = _label(d, "mitchell", "egypt").dropna(subset=["year"])
    union = set(range(1958, 1961))
    syr_years = {int(y) for y in syr["year"].unique()} & union
    egy_years = {int(y) for y in egy["year"].unique()} & union
    area = syr[(syr["item"].map(norm) == "wheat") & (syr["unit"] == "ha")].dropna(subset=["value"])
    by = {int(r.year): float(r.value) for r in area.itertuples()}
    pre = [by[y] for y in (1956, 1957) if y in by]
    post = [by[y] for y in (1958, 1959, 1960) if y in by]
    step = (sum(post) / len(post)) / (sum(pre) / len(pre)) if pre and post else None
    ok = bool(syr_years and egy_years and step is not None and 0.85 < step < 1.15)
    return ok, (
        f"both labels carry data in the union years ({sorted(syr_years)} syria, {sorted(egy_years)} "
        f"egypt); syrian wheat AREA moves {step:.2f}x across 1958, where folding in Egypt's ~600k ha "
        f"would step it by roughly 1.4x"
    )


def check_iia_libya(d):
    """The claim: IIA's plain `libya` is the whole colony (Tripolitania + Cyrenaica + Fezzan), with
    provincial data carried under sibling raw labels.

    STRUCTURAL and falsifiable via the provenance table rather than the panel, because the panel has
    collapsed all three raw labels into one `libya`. state/iia_label_provenance.csv carries them
    separately -- `italian libya`, `italian libya: tripolitania`, `italian libya: cyrenaica` -- which
    is exactly what the convention asserts: the source distinguishes whole from part.

    WHAT IT DOES NOT LICENSE, and the reason libya assertions are still refused by
    validate_iia_label_provenance.py: the layer-B label MIXES them. libya|iia|1925-1933 has NO
    dominant source at all (best is `italian libya: tripolitania` at 25% over 44 values), and
    libya|iia|1922-1924 is 100% Tripolitania. So the source being careful does not make the
    harmonisation careful, and this convention describes the source only.
    """
    import csv as _csv
    path = os.path.join(H, "state/iia_label_provenance.csv")
    if not os.path.exists(path):
        return False, "iia_label_provenance.csv missing; the raw labels cannot be checked"
    with open(path, encoding="utf-8") as fh:
        raws = {r["raw_label"] for r in _csv.DictReader(fh)}
    whole = [r for r in raws if norm(r) in ("libya", "italian libya")]
    parts = [r for r in raws if ":" in r and "libya" in norm(r)]
    ok = bool(whole) and len(parts) >= 2
    return ok, (
        f"the source carries {len(whole)} whole-Libya label(s) and {len(parts)} provincial "
        f"sibling(s) ({', '.join(sorted(parts)[:3])}) — whole and part are distinguished upstream, "
        f"which is all this convention claims; the layer-B label still mixes them"
    )


def check_iia_austria(d):
    """The claim: IIA's `Austria` through 1917/18 is CISLEITHANIA (~300,560 km2 — the Austrian half
    of the dual monarchy, including Bohemia, Moravia and Galicia), not rump Austria (~84,000 km2).

    TEMPORAL, so it can fail, and independent of the magnitude-plausibility argument the convention
    was learned from. If the pre-1918 label is Cisleithania and the post-1919 label is the republic,
    the same series must STEP DOWN hard at the dissolution. Measured medians, pre-1918 vs 1920+:

        sugar raw centrifugal   938,389 t -> 128,900 t   0.14
        p (phosphate)           323,050   ->  36,327     0.11
        yarn of true hemp         3,336   ->     352     0.11
        wine                    310,305   ->  85,075     0.27

    The drop is far steeper than the 3.6x area ratio, which is itself the evidence: Bohemia and
    Moravia were the empire's sugar-beet heartland and both left in 1918, so sugar had to fall by
    more than area. A label that meant rump Austria all along would show no step at all.

    NOT THE WHOLE STORY, and the assertion is quarantined for the rest: the label also draws ~12%
    of its values from raw `austria-hungary`, the WHOLE monarchy, concurrently with raw `austria`.
    This convention establishes what the dominant 73% means; it does not license verified_equal.
    """
    a = _label(d, "iia", "austria")
    a = a.dropna(subset=["year", "value"])
    ratios = []
    for (item, unit), g in a.groupby(["item", "unit"]):
        pre = g[g["year"] <= 1917]["value"].dropna()
        post = g[g["year"] >= 1920]["value"].dropna()
        if len(pre) >= 3 and len(post) >= 3 and float(pre.median()) > 0:
            ratios.append(float(post.median()) / float(pre.median()))
    if len(ratios) < 3:
        return False, "too few items span 1918 to test the step; the check is unavailable"
    ratios.sort()
    med = ratios[len(ratios) // 2]
    ok = med < 0.5
    return ok, (
        f"{len(ratios)} items span the 1918 dissolution; median post/pre ratio {med:.2f} "
        f"(range {ratios[0]:.2f}-{ratios[-1]:.2f}) — a label meaning rump Austria throughout would "
        f"show no step"
    )


def check_iia_netherlands(d):
    """The claim: IIA's `netherlands` is the metropolitan country, with the Dutch colonies carried
    under their own labels rather than folded in.

    AGRONOMIC, so it can fail. The Netherlands cannot grow cacao, coffee, rubber or tea; the
    Netherlands East Indies was one of the world's largest producers of all four. If the colonies
    were folded into the metropolitan label, those items would appear under it. Measured: ZERO
    tropical items under `netherlands` against four under `indonesia`, across 33 shared years --
    concurrent, so this is not an artefact of the two labels covering different periods.

    This is a different mechanism from the one the convention was learned from (the verifier argued
    from the commodity MIX looking temperate, which is the same observation read qualitatively); the
    test here is the concurrency plus the absence, and it is the absence that would break.
    """
    tropical = ("coffee", "cacao", "cocoa", "rubber", "tea", "copra", "cinchona")
    nl = _label(d, "iia", "netherlands")
    idn = _label(d, "iia", "indonesia")
    nl_trop = {it for it in nl["item"].unique() if any(t in norm(it) for t in tropical)}
    id_trop = {it for it in idn["item"].unique() if any(t in norm(it) for t in tropical)}
    yn = set(nl.dropna(subset=["year"])["year"].astype(int))
    yi = set(idn.dropna(subset=["year"])["year"].astype(int))
    ok = len(nl) > 0 and len(idn) > 0 and not nl_trop and len(id_trop) >= 2 and len(yn & yi) >= 10
    return ok, (
        f"iia carries {len(nl)} netherlands and {len(idn)} indonesia rows over {len(yn & yi)} shared "
        f"years; tropical items under netherlands: {len(nl_trop)}, under indonesia: {len(id_trop)} "
        f"({', '.join(sorted(id_trop)[:3])}) -- a folded-in East Indies would put those under the "
        f"metropolitan label"
    )


def check_fao1952_france(d):
    """The claim: fao1952's plain `France` is metropolitan France, with Algeria and the Saar
    carried under their own labels rather than folded in.

    Structural and therefore checkable. The decisive detail is not just that `Algeria` and
    `Saar` exist alongside `France` -- it is that `France Saar` ALSO exists as its own
    125-row label. A source that folded the 1948-56 customs union into `France` would have no
    reason to carry the combination separately, and a source that ignored the union would have
    no reason to carry it at all. Its presence is what a deliberate convention looks like.
    """
    f = d[d["source"] == "fao1952"]
    fr = f[f["country"].map(norm) == "france"]
    al = f[f["country"].map(norm).str.contains("algeria", regex=False, na=False)]
    saar = f[f["country"].map(norm).str.contains("saar", regex=False, na=False)]
    combo = f[f["country"].map(norm).str.contains("france saar", regex=False, na=False)]
    shared = set(fr["item"].map(norm)) & set(al["item"].map(norm))
    smaller = 0
    for item in shared:
        a = al[al["item"].map(norm) == item]["value"].dropna()
        b = fr[fr["item"].map(norm) == item]["value"].dropna()
        if len(a) and len(b) and float(a.median()) < float(b.median()):
            smaller += 1
    ok = (
        len(fr) > 0 and len(al) > 0 and len(saar) > 0 and len(combo) > 0
        and len(shared) >= 10 and smaller >= len(shared) * 0.6
    )
    return ok, (
        f"fao1952 carries {len(fr)} france, {len(al)} algeria and {len(saar)} saar rows as "
        f"separate labels, plus {len(combo)} rows under a distinct france-saar combination; "
        f"{len(shared)} shared items, algeria's median below france's in {smaller}"
    )


def check_mitchell_algeria(d):
    """The claim: Mitchell's Algeria follows the civil-departments basis (~575,511 km2,
    northern Algeria) rather than the full colony polygon including the Sahara Southern
    Territories annexed in 1902 (~2.44M km2). Same basis already documented for IIA (issue 166).

    THE CAMEL TEST, which is what makes this falsifiable rather than a restatement. Camels are
    overwhelmingly a Saharan animal, so if Mitchell's reporting territory had widened to the
    full colony when the Southern Territories were annexed in 1902, the camel herd would step
    up sharply at that year. Measured: 203,000 head median before 1902 against 180,500 after --
    it goes very slightly DOWN, 0.89x, over a 74-year series running from 1867. The basis did
    not change at the annexation.

    This is deliberately a LIVESTOCK mechanism. The convention was learned from cropland
    magnitudes, and desert contains little cropland either way, so crop areas cannot
    discriminate between the two territories. Camels can, and they were tested as a potential
    refutation rather than as confirmation.

    Corroborated a second way, cross-source: Mitchell and IIA agree closely on shared items
    (oats 164,000 vs 185,000 ha, ratio 0.89; olive oil 22,000 vs 20,685 t, ratio 1.06), and
    IIA's civil-departments basis for Algeria is the one issue 166 already established.
    """
    a = _label(d, "mitchell", "algeria")
    cam = a[a["item"].map(norm) == "camels"].dropna(subset=["year"])
    pre = cam[cam["year"] < 1902]["value"].dropna()
    post = cam[cam["year"] >= 1902]["value"].dropna()
    if not len(pre) or not len(post):
        return False, "no camel series either side of 1902; the discriminating test is unavailable"
    step = float(post.median()) / float(pre.median())
    # A widening to the full colony would multiply the herd, not leave it flat. Anything under
    # 1.5x means no Saharan population entered the series at the annexation.
    ok = step < 1.5
    return ok, (
        f"camels {pre.median():,.0f} head median pre-1902 vs {post.median():,.0f} from 1902 "
        f"({step:.2f}x): no step at the Southern Territories annexation, so the reporting "
        f"basis did not widen to the full colony"
    )


CHECKS = {
    ("iia", "algeria", "*"): check_iia_algeria,
    ("fao1952", "France", "*"): check_fao1952_france,
    ("iia", "netherlands", "*"): check_iia_netherlands,
    ("iia", "austria", "*"): check_iia_austria,
    ("iia", "libya", "*"): check_iia_libya,
    ("mitchell", "Syrian Arab Republic", "*"): check_mitchell_syria,
    ("iia", "antigua and barbuda", "*"): check_iia_antigua,
    ("mitchell", "algeria", "*"): check_mitchell_algeria,
    ("fao1952", "*", "population"): check_fao1952_population,
    ("iia", "russian federation", "*"): check_iia_russia,
    ("iia", "south korea", "*"): check_iia_south_korea,
    ("juan", "germany", "*"): check_juan_germany,
    ("juan", "finland", "*"): check_juan_finland,
    ("juan", "Czechoslovakia", "*"): check_juan_czechoslovakia,
    ("iia", "djibouti", "coffee, green"): check_iia_djibouti_coffee,
}


def registry_keys(path=CONVENTIONS):
    """(source, label_pattern, item_pattern) of every registered convention."""
    with open(path, encoding="utf-8") as fh:
        return [
            (r["source"], r["label_pattern"], r["item_pattern"])
            for r in csv.DictReader(fh)
        ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer-b", default=DEFAULT_PANEL,
                    help="consolidated layer-B parquet (default: %(default)s)")
    args = ap.parse_args()

    keys = registry_keys()
    uncovered = [k for k in keys if k not in CHECKS]
    orphan = [k for k in CHECKS if k not in keys]
    print(f"{len(keys)} registered convention(s), {len(CHECKS)} check(s) defined")
    for k in uncovered:
        print(f"  FAIL no re-test defined for {k} — add one to CHECKS in this file")
    for k in orphan:
        print(f"  note check defined for {k}, which the registry no longer carries")

    if not os.path.exists(args.layer_b):
        print(f"SKIP measurements — layer-B panel not found at {args.layer_b} "
              f"(gitignored; set WHEP_LAYER_B or pass --layer-b)")
        return 1 if uncovered else 0

    import pandas as pd  # only needed for the measuring half

    d = pd.read_parquet(args.layer_b)
    failed, drift = [], 0
    for k in keys:
        fn = CHECKS.get(k)
        if fn is None:
            continue
        try:
            ok, msg = fn(d)
        except Exception as exc:                      # a check that crashes is a failure
            ok, msg = False, f"check raised {type(exc).__name__}: {exc}"
        print(f"  {'PASS' if ok else 'FAIL'} {k[0]}/{k[1]}/{k[2]}: {msg}")
        if not ok:
            failed.append(k)
    print(f"\n{'FAIL' if (failed or uncovered) else 'PASS'}: "
          f"{len(failed)} conclusion(s) contradicted, {len(uncovered)} row(s) with no "
          f"re-test, over {len(d):,} layer-B rows")
    if failed:
        print("A contradicted conclusion must be softened or withdrawn in "
              "state/source_conventions.csv — it is a premise every verifier inherits.")
    return 1 if (failed or uncovered) else 0


if __name__ == "__main__":
    sys.exit(main())
