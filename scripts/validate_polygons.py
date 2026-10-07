#!/usr/bin/env python3
"""Validate that every polity's ATTACHED geometry is the territory it claims.

Why this exists: eight polities were found carrying a completely different
country's polygon — San Marino (61 km2) had Albania's (28,624 km2), Indonesia
had India's, French Cameroun had Bulgaria's — because `polygon_feature_id` was
recorded as a row index or a guessed number rather than the Gleditsch-Ward code
that scripts/sources.yaml actually resolves. Nothing checked the result, so the
errors sat in the database silently. This script is that check.

Three independent tests:

  A. AREA AGREEMENT — measure the attached geometry in an equal-area projection
     and compare against the page's own polygon_area_km2. A large divergence
     means one of them is wrong.

     WHICH GEOMETRY THIS IS, since issue 71 found that the answer mattered. It is
     the SHIPPED geometry, after build_database.py's simplify/densify/repair
     passes -- not the source polygon the page names. Those were once different
     things: simplification at 0.01 degrees deleted 42% of MDV-1800-2025's 791
     atolls, so the Maldives could declare 299.68 and fail this check on a
     CORRECT polygon, or declare 172.62 and understate the country by 42%.
     `polygon_area_km2` means the territory's area (wiki/README.md), so the
     second reading was never available and the check was measuring the wrong
     object.

     It is now safe, and the safety is asserted rather than assumed:
     build_database.py's simplification carries an area budget and
     validate_simplification_loss.py fails if any shipped polygon moves more
     than 5% from the source area recorded in polygon_feature_index.csv. The
     largest movement across all 735 is 2.1% (2026-08-13), well inside this
     check's 25%, so a divergence here is the declared figure or the binding --
     never the rendering.

  C. CLAIMED BUT ABSENT — a polygon_status of assigned/proxy/estimate asserts a
     polygon exists; fail if the build attached none (e.g. polygon_feature_id
     written as prose, "composed-union: cowcode=452 UNION cowcode=462", which
     nothing can resolve). Known cases are baselined in
     scripts/validate_polygons_baseline.txt so the gate catches NEW ones.

  D. REVIEWED MEANS DOCUMENTED — a page flagged wiki_status=reviewed must carry
     at least one source citation and no unfilled sections, since the
     verification pipeline treats `reviewed` as settled.

  B. IDENTITY — for cshapes-bound polities, look up the feature the id resolves
     to and compare its country name against the polity. An unrelated country
     is a mis-binding. Historical/modern synonyms (Bechuanaland/Botswana,
     Rumania/Romania) are expected, so this test reports for review rather than
     failing; use --strict in CI once the known-synonym list is settled.

Exit code 1 if any test-A failure exceeds the tolerance, so it can gate CI.

Usage:
  python3 scripts/validate_polygons.py [--tolerance 0.25] [--strict]
"""
import geopandas as gpd, pandas as pd, argparse, os, sys, re, warnings
warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
CSV = os.path.join(REPO, "data/final/polities_database.csv")
CSHAPES = os.path.join(REPO, "data/geodata/cshapes-2.0/CShapes-2.0.shp")
EQUAL_AREA = "ESRI:54034"

ap = argparse.ArgumentParser()
ap.add_argument("--tolerance", type=float, default=0.25,
                help="fractional area divergence tolerated between geometry and frontmatter")
ap.add_argument("--min-km2", type=float, default=200.0,
                help="skip the area check only when BOTH claimed and measured are "
                     "below this size (projection artifacts dominate microstates)")
ap.add_argument("--strict", action="store_true", help="also fail on identity mismatches")
A = ap.parse_args()

DEAD_STATUS = ("retired", "superseded")

# The five documented values (wiki/README.md). Ported from PR #38, whose data half --
# consolidating nine values down to these five -- already landed on main while the GUARD
# did not. Without it the field can grow back: `derived`, `missing`, `approximate` and
# `excluded` were all near-synonyms of these, none was in CLAIMS_POLYGON, and so 21 pages
# were silently exempt from check C. Any value outside this set is invisible to C, which
# means a page could declare a polygon and carry none while failing nothing. That blind
# spot, not the tidying, was PR #38's point.
#
# Retired and superseded rows are exempt, for the same reason check A0 exempts them: they
# receive no data and one of them (DJI-1886-2025) carries no polygon_status at all.
VOCABULARY = frozenset({"assigned", "proxy", "estimate", "polygon_vintage_drift", "unassigned"})

g = gpd.read_file(GPKG)
have = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
have["measured_km2"] = have.to_crs(EQUAL_AREA).geometry.area / 1e6
print(f"{len(have)} polities with geometry (of {len(g)} rows)")

# ---------- V: polygon_status must be a documented value ----------
_st = g.get("polygon_status")
_st = pd.Series([None] * len(g)) if _st is None else _st.reset_index(drop=True)
_live = ~g.reset_index(drop=True).get("wiki_status").isin(DEAD_STATUS)
off_vocab = g.reset_index(drop=True)[~_st.fillna("").isin(VOCABULARY) & _live]
print(
    f"\nV. VOCABULARY - {len(off_vocab)} live polit(ies) carry a polygon_status outside "
    f"the documented set ({', '.join(sorted(VOCABULARY))})"
)
for r in off_vocab.itertuples():
    print(
        f"   FAIL {r.polity_code:18s} polygon_status="
        f"{getattr(r, 'polygon_status', None)!r} - not a documented value, so this row "
        f"is invisible to check C"
    )

# ---------- A0: a row that declares no polygon must not carry one ----------
# The mirror of check C. C catches a row claiming a polygon it does not have; this
# catches one that HAS a polygon while declaring it does not, which is just as
# contradictory and was not checked at all.
#
# It found ADE-1839-1963 (Aden Protectorate) declaring `unassigned` — the status
# meaning "no polygon is claimed" — while carrying CShapes 680 and describing it, on
# the same page, as a "period proxy" with documented vintage drift. A consumer
# trusting `polygon_status`, which is exactly what the manifest's
# `claims_polygon_status` set is for, would have concluded Aden has no polygon.
# Corrected to `proxy`.
#
# DEAD rows are exempt. Five superseded/retired rows still carry geometry from
# before they were withdrawn, because build_database.py declines to rewrite the
# GeoPackage when a run attaches fewer geometries — so the residue cannot be removed
# without a full rebuild with the sources fetched. They receive no data either way.
NO_CLAIM = frozenset({"unassigned", "excluded", "none", ""})
declared_none = have[
    have.get("polygon_status").fillna("").astype(str).isin(NO_CLAIM)
    & ~have.get("wiki_status").isin(DEAD_STATUS)
]
print(f"\nA0. DECLARES NO POLYGON YET HAS ONE — {len(declared_none)} live row(s)")
for r in declared_none.itertuples():
    print(f"   FAIL {r.polity_code:18s} polygon_status={r.polygon_status!r} but carries "
          f"{r.polygon_source}/{r.polygon_feature_id}")

# Arm A3. An `assigned` row under check A's size floor whose polygon disagrees with the declared
# territory by more than check A's own tolerance. Zero today, and zero is reachable -- the rows that
# diverge that far (TUV 60%, TKL 31%, BMU 26%) all declare `estimate` or `proxy`, which is the honest
# label for a polygon that is not exactly the territory. So this fires only on a row claiming
# certainty it does not have, in the band where nothing else looks.
BASELINE_SUBFLOOR_ASSIGNED = 0

# ---------- A: area agreement ----------
have["claimed"] = pd.to_numeric(have.get("polygon_area_km2"), errors="coerce")
# A figure labelled measured-from-polygon IS the geometry's own measurement, so comparing it with
# that geometry cannot fail. Check A skips those rows -- A2 counts them and A6 tests the one thing
# that can be false about them (that they are still the measurement).
have["asrc"] = have.get("polygon_area_source", pd.Series("", index=have.index)).fillna("").astype(str).str.strip()
# Skip only when BOTH the claimed and the measured area are small — a genuine
# microstate, where projection noise dominates. Filtering on the CLAIMED value
# alone made the check exempt exactly the errors it should catch loudest: a claim
# that is wrong by being far TOO SMALL falls below the threshold and is never
# compared. FRA-1871-1919 claimed 62.43 km2 against a geometry measuring 532,305
# — France without Alsace-Lorraine recorded as smaller than Manhattan, almost
# certainly a square-degrees value written into a km2 field — and this check
# reported zero disagreements for as long as the filter used `claimed`.
chk = have[
    have.claimed.notna() & (have.asrc != "measured-from-polygon")
    & ((have.claimed >= A.min_km2) | (have.measured_km2 >= A.min_km2))
].copy()
chk["divergence"] = (chk.measured_km2 - chk.claimed).abs() / chk.claimed
diverging = chk[chk.divergence > A.tolerance].sort_values("divergence", ascending=False)
# Only `assigned` CLAIMS the polygon is the territory, so only there is a
# divergence a contradiction. estimate/proxy/*_drift already say the polygon is
# inexact, and those pages document the direction and magnitude — report but
# don't fail, otherwise the gate punishes honest documentation.
EXACT_CLAIM = frozenset({"assigned"})
st = diverging.get("polygon_status").astype(str)
bad_area = diverging[st.isin(EXACT_CLAIM)]
documented = diverging[~st.isin(EXACT_CLAIM)]

# A3. THE POPULATION CHECK A SKIPS. The 200 km2 floor above exists for projection noise, which is
# worth about half a percent (see issue 569's measurement of the two area conventions: -0.43% to
# +0.60%). It is currently excluding errors two orders of magnitude larger than that. Issue 570
# measured the 100-1,000 km2 band running ~4% large with 22 of 28 comparisons on the same side, and
# every polity it named except one sits under this floor -- so the check is blindest exactly where
# the bias is strongest.
#
# This does not lower the floor, which would be a policy change: a small polygon really is noisier,
# and `estimate`/`proxy` rows are documenting their own inexactness honestly. It applies check A's
# OWN rule -- an `assigned` row claims the polygon IS the territory, so a divergence there is a
# contradiction -- to the rows the floor exempts, and pins the count.
_sub = have[
    have.claimed.notna() & (have.claimed > 0) & have.measured_km2.notna()
    & (have.claimed < A.min_km2) & (have.measured_km2 < A.min_km2)
    & ~have.get("wiki_status").isin(DEAD_STATUS)
].copy()
_sub["dev"] = (_sub.measured_km2 - _sub.claimed).abs() / _sub.claimed
_sub_bad = _sub[(_sub.dev > A.tolerance) & _sub.get("polygon_status").astype(str).isin(EXACT_CLAIM)]
_sub_soft = _sub[_sub.dev > 0.10]
print(f"\nA3. BELOW CHECK A'S {A.min_km2:.0f} km2 FLOOR — {len(_sub)} live row(s) declare an area that "
      f"check A never compares; {len(_sub_soft)} diverge >10%, {len(_sub_bad)} of those claim "
      f"polygon_status=assigned (ceiling {BASELINE_SUBFLOOR_ASSIGNED})")
for r in _sub_soft.sort_values("dev", ascending=False).itertuples():
    print(f"   {r.dev*100:6.1f}%  {r.polity_code:18s} declared {r.claimed:>8,.1f} km2  "
          f"polygon {r.measured_km2:>8,.1f}  status={r.polygon_status}")
print(f"\nA. AREA AGREEMENT — {len(chk)} polities state an area independent of their polygon; {len(diverging)} diverge "
      f"from their geometry by >{A.tolerance:.0%} ({len(bad_area)} claim polygon_status=assigned)")
for r in bad_area.itertuples():
    print(f"   FAIL {r.divergence*100:6.0f}%  {r.polity_code:18s} claims {r.claimed:>12,.0f} km2, "
          f"geometry measures {r.measured_km2:>12,.0f} km2   ({r.polygon_source}/{r.polygon_feature_id})")
for r in documented.itertuples():
    print(f"   ok   {r.divergence*100:6.0f}%  {r.polity_code:18s} claims {r.claimed:>12,.0f} km2 vs "
          f"{r.measured_km2:>12,.0f} km2 — declared '{r.polygon_status}', divergence documented")

# ---------- A2: provenance of the declared area (issue 600; was issue 195's tautology count) ----------
#
# CHECK A COMPARES A DECLARED AREA AGAINST THE GEOMETRY IT WAS OFTEN COPIED FROM, and until issue
# 600 nothing recorded which rows those were: `polygon_area_km2` meant "what a source states" on
# some pages and "what our polygon measures" on others. The tautology hid three real errors, each
# of which agreed with its polygon to under 1% while both were wrong the same way
# (IDN-OTH-1949-1951 and IND-1800-1886 both included territory they should not -- West Papua,
# Ceylon -- and CAN-1800-1866 was the recipe minus Quebec).
#
# Every declared area now carries `polygon_area_source` (wiki/README.md), and this block makes the
# comparison NON-TAUTOLOGICAL by testing what each kind of figure can actually be tested against:
#
#   measured-from-polygon   cannot be compared with the polygon -- it IS the polygon -- so check A
#                           skips it (counted below). What CAN fail is the claim: the figure must
#                           still equal what the shipped geometry measures. If it does not, the
#                           geometry moved and the "measurement" is stale (A6).
#   source-stated           must be corroborated by a figure in source_stated_area_basis.csv for
#                           that polity (A7). Uncorroborated ones are pinned, not forbidden: some are
#                           dataset attributes (CShapes `area`) that no yearbook table carries.
#   official-gazetteer / derived-arithmetic / unrecorded
#                           compared against the geometry by check A like any independent figure.
#
# And the loophole this closes: a figure copied from the polygon but filed under an independent
# label. Any row NOT labelled measured-from-polygon whose figure sits within 0.1% of its own
# polygon, with no basis-table corroboration, is exactly that (A2c).
AREA_SOURCES = frozenset({
    "measured-from-polygon", "source-stated", "official-gazetteer",
    "derived-arithmetic", "unrecorded",
})
# `unrecorded` is a legacy bucket (figures whose origin the page does not state). A CEILING that may
# only fall: new pages name one of the other four. 49 live rows on 2026-10-07, the migration of
# issue 600 (51 pages in all; two are superseded rows).
BASELINE_UNRECORDED_AREA_SOURCE = 49
# source-stated figures no row of source_stated_area_basis.csv corroborates within 2%. 14 on 2026-10-07.
BASELINE_SOURCE_STATED_UNCORROBORATED = 14
# Rows labelled independent whose figure sits within 0.1% of their own polygon with no corroboration,
# i.e. indistinguishable from a copy. 0 on 2026-10-07: the migration of issue 600 labelled every such
# row measured-from-polygon, including CShapes `area` attributes, which describe the very feature
# the row ships and so are not independent of it.
BASELINE_INDEPENDENT_IN_BAND = 0
# measured-from-polygon rows for which a yearbook figure is already published: option B of issue 195,
# declaring the source's number, is available for them. Pinned so the set cannot grow while it is decided.
BASELINE_AVOIDABLE_SELF_REF = 33  # 43 by the old 0.1%-band heuristic (issue 195); 33 by label, 2026-10-07
SELF_REF_TOLERANCE = 0.001          # 0.1%: closer than any independent source would land
STALE_MEASUREMENT_TOLERANCE = 0.02  # a measured-from-polygon figure may drift this far (rebuilds,
                                    # the two area conventions' 0.8%) before it is called stale

_basis_path = os.path.join(REPO, "data/final/source_stated_area_basis.csv")
_basis = pd.DataFrame(columns=["polity_code", "stated_area_km2"])
if os.path.exists(_basis_path):
    _basis = pd.read_csv(_basis_path)
    _basis = _basis[pd.to_numeric(_basis.stated_area_km2, errors="coerce").notna()]

live_decl = have[
    have.claimed.notna() & (have.claimed > 0) & have.measured_km2.notna()
    & ~have.get("wiki_status").isin(DEAD_STATUS)
].copy()
live_decl["dev"] = (live_decl.measured_km2 / live_decl.claimed - 1).abs()
live_decl["asrc"] = live_decl.get("polygon_area_source").fillna("").astype(str).str.strip()

# A2a. Provenance present and in vocabulary. Read from the GeoPackage like `claimed` is.
_any_decl = g[
    pd.to_numeric(g.get("polygon_area_km2"), errors="coerce").notna()
    & ~g.get("wiki_status").isin(DEAD_STATUS)
].copy()
_any_decl["asrc"] = _any_decl.get("polygon_area_source").fillna("").astype(str).str.strip()
no_src = _any_decl[~_any_decl.asrc.isin(AREA_SOURCES)]
print(f"\nA2a. PROVENANCE — {len(_any_decl)} live rows declare an area; {len(no_src)} name no "
      f"valid polygon_area_source")
for r in no_src.itertuples():
    print(f"   FAIL {r.polity_code:18s} declares {r.polygon_area_km2} km2 with "
          f"polygon_area_source={r.asrc!r} (allowed: {', '.join(sorted(AREA_SOURCES))})")
n_unrec = int((_any_decl.asrc == "unrecorded").sum())
print(f"   {n_unrec} are `unrecorded` legacy figures (ceiling {BASELINE_UNRECORDED_AREA_SOURCE})")
if n_unrec > BASELINE_UNRECORDED_AREA_SOURCE:
    print(f"   FAIL: {n_unrec} is above the pinned ceiling of {BASELINE_UNRECORDED_AREA_SOURCE}. "
          f"Name where the figure came from -- source-stated, official-gazetteer, "
          f"derived-arithmetic or measured-from-polygon -- instead of `unrecorded`.")
elif n_unrec < BASELINE_UNRECORDED_AREA_SOURCE:
    print(f"   note: {n_unrec} is BELOW the pinned {BASELINE_UNRECORDED_AREA_SOURCE}. Lower the "
          f"pin; provenance improved.")

# A2b. What cannot fail, now counted EXACTLY from the label rather than guessed from a 0.1% band.
selfref = live_decl[live_decl.asrc == "measured-from-polygon"]
print(f"\nA2. SELF-REFERENTIAL AREAS — {len(selfref)} of {len(live_decl)} declared areas are labelled "
      f"measured-from-polygon, so check A skips them (a polygon cannot disagree with a number "
      f"read off it)")
_have_stated = set(_basis.polity_code)
avoidable = sorted(selfref[selfref.polity_code.isin(_have_stated)].polity_code)
print(f"   of which AVOIDABLE — an independent stated figure exists for them: {len(avoidable)} "
      f"(ceiling {BASELINE_AVOIDABLE_SELF_REF})")
if len(avoidable) > BASELINE_AVOIDABLE_SELF_REF:
    print(f"   FAIL: {len(avoidable)} is above the pinned ceiling of {BASELINE_AVOIDABLE_SELF_REF}. "
          f"These rows declare their own polygon's area while a yearbook figure for them is "
          f"already published in source_stated_area_basis.csv; declare that figure instead, as "
          f"source-stated (issue 195 option B)")
    for _c in avoidable:
        print(f"     {_c}")

# A6. The claim a self-measured figure makes is that it still IS the polygon's measurement.
stale = selfref[selfref.dev > STALE_MEASUREMENT_TOLERANCE]
print(f"\nA6. STALE MEASUREMENT — {len(stale)} measured-from-polygon figure(s) no longer match their "
      f"geometry within {STALE_MEASUREMENT_TOLERANCE:.0%}")
for r in stale.sort_values("dev", ascending=False).itertuples():
    print(f"   FAIL {r.dev*100:6.1f}%  {r.polity_code:18s} declares {r.claimed:>12,.1f} km2, "
          f"geometry now measures {r.measured_km2:>12,.1f} -- re-measure it or source a figure")

# A7. A `source-stated` figure should be one a source states.
ss = live_decl[live_decl.asrc == "source-stated"]
def _corroborated(r):
    b = _basis[_basis.polity_code == r.polity_code]
    return bool(((b.stated_area_km2.astype(float) / r.claimed - 1).abs() <= 0.02).any())
unc = sorted(r.polity_code for r in ss.itertuples() if not _corroborated(r))
print(f"\nA7. SOURCE-STATED CORROBORATION — {len(ss) - len(unc)} of {len(ss)} source-stated figures "
      f"match a row of source_stated_area_basis.csv within 2%; {len(unc)} do not "
      f"(ceiling {BASELINE_SOURCE_STATED_UNCORROBORATED})")
if len(unc) > BASELINE_SOURCE_STATED_UNCORROBORATED:
    print(f"   FAIL: {len(unc)} is above the pinned ceiling of {BASELINE_SOURCE_STATED_UNCORROBORATED}. "
          f"Either the figure is not a source's (label it measured-from-polygon, "
          f"official-gazetteer or derived-arithmetic) or the source's label is not yet routed to "
          f"this polity in source_label_lexicon.csv.")
    for _c in unc:
        print(f"     {_c}")

# A2c. Independent label, polygon-sized figure, no corroboration: indistinguishable from a copy.
_ind = live_decl[live_decl.asrc.isin(AREA_SOURCES - {"measured-from-polygon", "source-stated"})
                 | live_decl.polity_code.isin(unc)]
in_band = sorted(r.polity_code for r in _ind.itertuples() if r.dev <= SELF_REF_TOLERANCE)
print(f"\nA2c. INDEPENDENT LABEL, POLYGON-SIZED FIGURE — {len(in_band)} row(s) not labelled "
      f"measured-from-polygon sit within {SELF_REF_TOLERANCE:.1%} of their own geometry with no "
      f"corroborating source figure (ceiling {BASELINE_INDEPENDENT_IN_BAND})")
for _c in in_band:
    print(f"     {_c}")
if len(in_band) > BASELINE_INDEPENDENT_IN_BAND:
    print(f"   FAIL: {len(in_band)} is above the pinned ceiling of {BASELINE_INDEPENDENT_IN_BAND}. "
          f"A figure within {SELF_REF_TOLERANCE:.1%} of its own polygon is not evidence about the "
          f"territory. If it was read off the geometry, label it measured-from-polygon; if a source "
          f"states it, show that source in source_stated_area_basis.csv.")
elif len(in_band) < BASELINE_INDEPENDENT_IN_BAND:
    print(f"   note: {len(in_band)} is BELOW the pinned {BASELINE_INDEPENDENT_IN_BAND}. Lower the pin.")

# A8. The published MEASURED area (GeoPackage field written by build_database.py) must be what the
# geometry measures, so a consumer reading the two fields side by side compares real things.
if "computed_polygon_area_km2" in g.columns:
    _pub = have.assign(pub=pd.to_numeric(have["computed_polygon_area_km2"], errors="coerce"))
    _bad = _pub[
        _pub.pub.isna() | ((_pub.pub - _pub.measured_km2).abs() > 0.02 + 0.001 * _pub.measured_km2)
    ]
else:
    _bad = have
print(f"\nA8. PUBLISHED MEASURED AREA — {len(_bad)} of {len(have)} geometries carry a "
      f"computed_polygon_area_km2 that is missing or disagrees with the geometry")
for r in _bad.head(10).itertuples():
    print(f"   FAIL {r.polity_code:18s} measured {r.measured_km2:>12,.2f} km2, field says "
          f"{getattr(r, 'computed_polygon_area_km2', None)!r} -- run scripts/build_database.py")

a2_fail = (
    len(no_src) > 0 or n_unrec > BASELINE_UNRECORDED_AREA_SOURCE
    or len(avoidable) > BASELINE_AVOIDABLE_SELF_REF or len(stale) > 0
    or len(unc) > BASELINE_SOURCE_STATED_UNCORROBORATED
    or len(in_band) > BASELINE_INDEPENDENT_IN_BAND or len(_bad) > 0
)

# ---------- C: status claims a polygon that was never attached ----------
# `assigned`/`proxy`/`estimate` all assert a polygon exists. When the build
# cannot resolve polygon_feature_id it attaches nothing and says so only in a
# summary line, so a page can claim an exact polygon while carrying none —
# e.g. an id written as prose ("composed-union: cowcode=452 UNION cowcode=462")
# instead of a resolvable value. That is a direct contradiction, not a gap.
CLAIMS_POLYGON = frozenset({"assigned", "proxy", "estimate", "polygon_vintage_drift"})
missing = g[g.geometry.isna() | g.geometry.is_empty].copy()
missing["st"] = missing.get("polygon_status").astype(str)
claim_no_geom = missing[missing.st.isin(CLAIMS_POLYGON)]
# Baseline: polities already known to claim a polygon they don't have. It is EMPTY as of
# 2026-08-13 — the issue #3 backlog is cleared — so every occurrence is now a failure.
# The file is kept as the ratchet: if a page ever has to claim a polygon it cannot carry,
# it needs a line there with the blocker named (each such row needs a real builder in
# scripts/sources/constructed/build.py or an honest downgrade to unassigned).
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validate_polygons_baseline.txt")
baseline = set()
if os.path.exists(BASELINE):
    baseline = {l.split("#")[0].strip() for l in open(BASELINE) if l.split("#")[0].strip()}
new_claim_no_geom = claim_no_geom[~claim_no_geom.polity_code.isin(baseline)]
# Bidirectional, like every other baseline in this repo. Without the second
# direction a baselined row that has since been FIXED keeps its licence forever, so
# the gate would stay silent if the same code regressed later — and the list quietly
# grows into a record of history rather than of open work. It is accurate today (0
# stale), which is the moment to make it stay that way.
stale_baseline = sorted(baseline - set(claim_no_geom.polity_code))
print(f"\nC. CLAIMED BUT ABSENT — {len(missing)} polities have no geometry; "
      f"{len(claim_no_geom)} declare a polygon_status that asserts one "
      f"({len(baseline)} baselined, {len(new_claim_no_geom)} new, "
      f"{len(stale_baseline)} stale)")
for code in stale_baseline:
    print(f"   STALE {code:18s} baselined but no longer claims a polygon it lacks — "
          f"remove it from scripts/validate_polygons_baseline.txt")

# How much the backlog actually costs, printed rather than left to be re-derived.
#
# A gap on a polity no consumer can reach costs nothing in any output; a gap on a
# FAOSTAT-mapped polity costs every row that routes there. The two need different
# priorities, and the distinction is computable from the published contracts.
#
# The baseline is EMPTY as of 2026-08-13 (issue #3 closed: 17 of the 20 tracked rows got
# real geometry, 3 were withdrawn to `unassigned`), so this block prints nothing and the
# `if baseline` guard below short-circuits. It is kept because the reachability question is
# the first thing anyone will ask the next time a row has to be baselined. When the list was
# 13 rows long, none was FAOSTAT-mapped and only four were reachable at all — via
# historical-source aliases, 655 observed rows between them — which is why the backlog was
# correctly treated as low-impact rather than urgent.
#
# Two findings on this branch were written up as live and downgraded after checking
# reachability, which is why every baseline here now reports it.
_area_map = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data/final/faostat_area_polity_map.csv")
_alias_map = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data/final/label_alias_map.csv")
if baseline and os.path.exists(_area_map):
    import csv as _csv
    with open(_area_map, encoding="utf-8") as fh:
        _mapped = {(r.get("polity_code") or "").strip() for r in _csv.DictReader(fh)}
    _obs = {}
    if os.path.exists(_alias_map):
        with open(_alias_map, encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                c = (r.get("polity_code") or "").strip()
                try:
                    _obs[c] = _obs.get(c, 0) + int(r.get("observed_rows") or 0)
                except ValueError:
                    pass
    _live = sorted(c for c in baseline if c in _mapped)
    _aliased = sorted(c for c in baseline if c not in _mapped and _obs.get(c, 0) > 0)
    print(f"   reachability of the {len(baseline)} baselined gaps: "
          f"{len(_live)} FAOSTAT-mapped, {len(_aliased)} alias-only, "
          f"{len(baseline) - len(_live) - len(_aliased)} unreachable")
    for c in _live:
        print(f"     LIVE      {c:18s} reachable by FAOSTAT area — a gap here affects output")
    for c in _aliased:
        print(f"     alias-only {c:17s} {_obs[c]} observed rows via historical sources")
for r in new_claim_no_geom.itertuples():
    fid = str(r.polygon_feature_id)
    print(f"   FAIL {r.polity_code:18s} status='{r.st}' but no geometry attached  "
          f"({r.polygon_source}/{fid[:52]}{'...' if len(fid) > 52 else ''})")

# ---------- D: `reviewed` must mean documented ----------
# `reviewed` asserts a human checked the page's claims against sources, and the
# verification pipeline leans on that. A reviewed page with no source citations
# invites unsourced assertions to be treated as settled — 10 of 72 were in that
# state (the whole IND and IDN chains). Fail so the label stays meaningful.
import glob
undoc = []
for _, r in pd.read_csv(CSV).iterrows():
    if str(r.get("wiki_status")) != "reviewed": continue
    fp = os.path.join(REPO, "wiki/polities", f"{str(r.polity_code).lower()}.md")
    if not os.path.exists(fp): continue
    txt = open(fp).read()
    cites = len(re.findall(r"\]\(\.\./sources/", txt))
    if cites == 0 or "(to be documented)" in txt:
        undoc.append((r.polity_code, len(txt), cites, "(to be documented)" in txt))
print(f"\nD. REVIEWED MEANS DOCUMENTED — {len(undoc)} page(s) flagged wiki_status=reviewed "
      f"with no source citations or unfilled sections")
for c, n, ci, td in undoc:
    print(f"   FAIL {c:18s} {n:6d} bytes, {ci} source citations"
          + (", has '(to be documented)'" if td else ""))

# ---------- B: identity of cshapes bindings ----------
mismatch = []
if os.path.exists(CSHAPES):
    cs = gpd.read_file(CSHAPES)
    name_by_gw = {int(c): grp.cntry_name.iloc[0] for c, grp in cs.groupby("gwcode")}
    pol = pd.read_csv(CSV)
    # EXACTLY cshapes-2.0, not any source containing "cshapes". The looser filter also
    # caught the 21 rows bound to `cshapes-europe`, then looked their ids up in the
    # cshapes-2.0 shapefile — a different file with a different schema (`Id`, `Holder`,
    # `Name`, no `gwcode`). That produced three false "id absent from CShapes" reports
    # for AND-1800-2025, LIE-1800-2025 and MCO-1800-2025, whose ids are perfectly valid
    # in the file they are actually bound to, and made the name comparison meaningless
    # for all 21. The 514 genuinely cshapes-2.0-bound rows have no absent ids at all.
    #
    # cshapes-europe bindings are therefore NOT identity-checked. Doing so needs a
    # second lookup against that file's own id column, which is a separate change.
    sub = pol[pol.polygon_source.astype(str).str.strip() == "cshapes-2.0"]
    def toks(s): return set(re.findall(r"[a-z]{4,}", str(s).lower()))
    for _, r in sub.iterrows():
        fid = str(r.polygon_feature_id).strip().replace(".0", "")
        if not fid.isdigit(): continue
        cn = name_by_gw.get(int(fid))
        if cn is None:
            mismatch.append((r.polity_code, r.polity_name, fid, "(id absent from CShapes)"))
            continue
        if not (toks(r.polity_name) & toks(cn)):
            mismatch.append((r.polity_code, r.polity_name, fid, cn))
    print(f"\nB. IDENTITY — {len(sub)} cshapes-bound polities; {len(mismatch)} whose feature name "
          f"shares no word with the polity name (review; historical synonyms are expected)")
    for pc, pn, fid, cn in mismatch:
        print(f"   {pc:18s} {str(pn)[:34]:34s} id {fid:>5s} -> {cn}")
else:
    print("\nB. IDENTITY — skipped, CShapes source not fetched")

_subfloor_over = len(_sub_bad) - BASELINE_SUBFLOOR_ASSIGNED
for _r in _sub_bad.itertuples():                                                    # A3
    print(f"   FAIL {_r.dev*100:6.1f}%  {_r.polity_code:18s} declares polygon_status=assigned with "
          f"{_r.claimed:,.1f} km2 against a polygon of {_r.measured_km2:,.1f}. `assigned` says the "
          f"polygon IS this territory; below check A's {A.min_km2:.0f} km2 floor nothing else "
          f"compares them, so the claim is untested rather than true")

fail = (len(bad_area) > 0 or len(declared_none) > 0 or len(new_claim_no_geom) > 0
        or len(stale_baseline) > 0 or len(undoc) > 0 or len(off_vocab) > 0
        or a2_fail or _subfloor_over > 0
        or (A.strict and mismatch))
print(f"\n{'FAIL' if fail else 'PASS'}: {len(off_vocab)} off-vocabulary status(es), "
      f"{len(bad_area)} area disagreement(s), "
      f"{int(a2_fail)} area-provenance failure(s) (A2a/A2/A2c/A6/A7/A8), "
      f"{len(declared_none)} declares-none-but-has-one, "
      f"{len(new_claim_no_geom)} NEW claimed-but-absent polygon(s), {len(undoc)} undocumented-but-reviewed"
      + f", {max(_subfloor_over, 0)} sub-floor assigned area(s) above the ceiling"
      + (f", {len(mismatch)} identity mismatch(es)" if A.strict else ""))
sys.exit(1 if fail else 0)
