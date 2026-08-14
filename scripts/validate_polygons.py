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
VOCABULARY = {"assigned", "proxy", "estimate", "polygon_vintage_drift", "unassigned"}

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
NO_CLAIM = {"unassigned", "excluded", "none", ""}
declared_none = have[
    have.get("polygon_status").fillna("").astype(str).isin(NO_CLAIM)
    & ~have.get("wiki_status").isin(DEAD_STATUS)
]
print(f"\nA0. DECLARES NO POLYGON YET HAS ONE — {len(declared_none)} live row(s)")
for r in declared_none.itertuples():
    print(f"   FAIL {r.polity_code:18s} polygon_status={r.polygon_status!r} but carries "
          f"{r.polygon_source}/{r.polygon_feature_id}")

# ---------- A: area agreement ----------
have["claimed"] = pd.to_numeric(have.get("polygon_area_km2"), errors="coerce")
# Skip only when BOTH the claimed and the measured area are small — a genuine
# microstate, where projection noise dominates. Filtering on the CLAIMED value
# alone made the check exempt exactly the errors it should catch loudest: a claim
# that is wrong by being far TOO SMALL falls below the threshold and is never
# compared. FRA-1871-1919 claimed 62.43 km2 against a geometry measuring 532,305
# — France without Alsace-Lorraine recorded as smaller than Manhattan, almost
# certainly a square-degrees value written into a km2 field — and this check
# reported zero disagreements for as long as the filter used `claimed`.
chk = have[
    have.claimed.notna()
    & ((have.claimed >= A.min_km2) | (have.measured_km2 >= A.min_km2))
].copy()
chk["divergence"] = (chk.measured_km2 - chk.claimed).abs() / chk.claimed
diverging = chk[chk.divergence > A.tolerance].sort_values("divergence", ascending=False)
# Only `assigned` CLAIMS the polygon is the territory, so only there is a
# divergence a contradiction. estimate/proxy/*_drift already say the polygon is
# inexact, and those pages document the direction and magnitude — report but
# don't fail, otherwise the gate punishes honest documentation.
EXACT_CLAIM = {"assigned"}
st = diverging.get("polygon_status").astype(str)
bad_area = diverging[st.isin(EXACT_CLAIM)]
documented = diverging[~st.isin(EXACT_CLAIM)]
print(f"\nA. AREA AGREEMENT — {len(chk)} polities state an area; {len(diverging)} diverge "
      f"from their geometry by >{A.tolerance:.0%} ({len(bad_area)} claim polygon_status=assigned)")
for r in bad_area.itertuples():
    print(f"   FAIL {r.divergence*100:6.0f}%  {r.polity_code:18s} claims {r.claimed:>12,.0f} km2, "
          f"geometry measures {r.measured_km2:>12,.0f} km2   ({r.polygon_source}/{r.polygon_feature_id})")
for r in documented.itertuples():
    print(f"   ok   {r.divergence*100:6.0f}%  {r.polity_code:18s} claims {r.claimed:>12,.0f} km2 vs "
          f"{r.measured_km2:>12,.0f} km2 — declared '{r.polygon_status}', divergence documented")

# ---------- A2: how many of check A's comparisons cannot fail ----------
#
# CHECK A COMPARES A DECLARED AREA AGAINST THE GEOMETRY IT WAS OFTEN COPIED FROM.
#
# `polygon_area_km2` has no recorded provenance. Some pages declare an official land area or a
# yearbook figure -- TKL-1800-2025 declares 12 km2 against a GADM 15.95, deliberately -- and some
# declare what their own polygon measures. For the second kind, check A is a no-op: a polygon
# cannot disagree with a number read off it, and the row reports PASS whatever is wrong with it.
#
# THAT TAUTOLOGY HID THREE REAL ERRORS, each of which agreed to under 1%:
#
#     IDN-OTH-1949-1951   declared 1,757,495 vs measured 1,747,408   0.6%    both included West Papua
#     IND-1800-1886       declared 4,209,917 vs measured 4,209,869   0.001%  both included Ceylon
#     CAN-1800-1866       declared 1,209,852, recipe 2,735,024       -       declared = recipe minus Quebec
#
# The right fix is provenance metadata -- a `polygon_area_source` field distinguishing
# measured-from-polygon / source-stated / official-gazetteer / derived-arithmetic -- which is
# issue 195 and a schema change. This is the cheap half: COUNT the comparisons that cannot fail,
# so the number is visible on every run and can only be argued down.
#
# NOT BIDIRECTIONAL, unlike every other baseline in this repo, and the reason is specific. A
# DECREASE here does not mean the provenance improved; it means the GEOMETRY MOVED -- PR 189
# changed 42 geometries and would have pushed rows out of the tight band without anyone sourcing
# a single figure. Failing on a decrease would print "lock in the improvement" when nothing
# improved. A row can only ENTER the band by someone re-deriving a declared figure from a
# polygon, which is a human act and worth failing on. So this is a ceiling.
SELF_REF_TOLERANCE = 0.001          # 0.1%: closer than any independent source would land
BASELINE_SELF_REFERENTIAL = 102     # 103 on 2026-08-10; 104 on 2026-08-12; 102 on 2026-08-13, see below

# THE CEILING IS NOT A PURE RATCHET, and one day of use falsified the reason given for making it
# one. The original note argued: "a row can only ENTER the band by someone re-deriving a declared
# figure from a polygon, which is a human act worth failing on." That is not the only way in.
#
# TUR-1913-1914 entered it on 2026-08-12 by having its GEOMETRY CORRECTED. The row declared
# 1,785,218 km2 and published 1,705,971 -- a 4.5% disagreement -- because polygon_feature_year 1914
# resolved to CShapes 640's `1914-1918` step, one that begins after the row ends. Rebinding it to
# the `1913-1914` step it had always declared brought the measurement to 1,784,775, which agrees
# with the declared figure to 0.02% and so counts as self-referential here.
#
# But that declared figure PREDATES the fix and was independently right -- it is what identified
# the correct step in the first place. Nothing was copied off a polygon; a polygon was corrected
# to match an independently-stated number. That is the best outcome available, and it raises this
# count.
#
# So the ceiling moves up for a geometry fix and down for a sourcing fix, and the two cannot be
# told apart without the provenance field issue 195 asks for. Until then, raising it requires the
# reason to be written here -- which is the actual guard, rather than the number.
#
# 104 -> 102 on 2026-08-13, AND THIS IS THE "GEOMETRY SIMPLY MOVED" CASE THE NOTE ABOVE WARNS
# ABOUT, not a sourcing improvement. Issue 84 rebuilt six British India periods as their CShapes
# step MINUS Portuguese India MINUS French India. Two of the six declare an area, and both were
# declaring the UNCUT step, so removing 4,246 km2 of enclave pushed each just outside the 0.1%
# band:
#
#     IND-1886-1893   declared 4,652,712   measured 4,647,939   0.1026%   was 0.000%
#     IND-1937-1947   declared 4,227,508   measured 4,223,063   0.1051%   was 0.000%
#
# Their declared figures were left alone deliberately. Rewriting them to the post-cut measurement
# would put both straight back into this band and re-create exactly the tautology A2 exists to
# count -- the declared number is now a source-stated CShapes figure disagreeing with a corrected
# polygon by 0.1%, which is check A doing its job. The pin is lowered because selftest_gates
# requires the ceiling to bite: at 104 the harness's own mutation (rewriting a declared area to
# what its polygon measures, +1) landed at 103 and the gate PASSED a defect it claims to catch.

# Live rows only, matching the population check A actually judges -- `have` includes the
# retired and superseded rows that still carry geometry, and check A exempts those.
with_both = have[
    have.claimed.notna() & (have.claimed > 0) & have.measured_km2.notna()
    & ~have.get("wiki_status").isin(DEAD_STATUS)
].copy()
with_both["dev"] = (with_both.measured_km2 / with_both.claimed - 1).abs()
selfref = with_both[with_both.dev <= SELF_REF_TOLERANCE]
exact = with_both[with_both.dev <= 0.000005]
print(f"\nA2. SELF-REFERENTIAL AREAS — {len(selfref)} of {len(with_both)} declared areas agree with "
      f"their own geometry within {SELF_REF_TOLERANCE:.1%}, so check A cannot fail for them "
      f"({len(exact)} agree to every digit)")
for r in exact.sort_values("polity_code").itertuples():
    print(f"   exact  {r.polity_code:18s} {r.claimed:>12,.0f} km2   ({r.polygon_source})")
selfref_over = len(selfref) - BASELINE_SELF_REFERENTIAL
if selfref_over > 0:
    print(f"   FAIL: {len(selfref)} is above the pinned ceiling of {BASELINE_SELF_REFERENTIAL}. "
          f"A declared area within {SELF_REF_TOLERANCE:.1%} of its own polygon is not evidence "
          f"about the territory -- source it from a yearbook or an official gazetteer, or say in "
          f"polygon_method that it was measured from the geometry.")
elif selfref_over < 0:
    print(f"   note: {len(selfref)} is BELOW the pinned {BASELINE_SELF_REFERENTIAL}. Lower the pin "
          f"to keep the ratchet tight -- but check first whether a figure was actually sourced, or "
          f"whether the geometry simply moved.")

# ---------- C: status claims a polygon that was never attached ----------
# `assigned`/`proxy`/`estimate` all assert a polygon exists. When the build
# cannot resolve polygon_feature_id it attaches nothing and says so only in a
# summary line, so a page can claim an exact polygon while carrying none —
# e.g. an id written as prose ("composed-union: cowcode=452 UNION cowcode=462")
# instead of a resolvable value. That is a direct contradiction, not a gap.
CLAIMS_POLYGON = {"assigned", "proxy", "estimate", "polygon_vintage_drift"}
missing = g[g.geometry.isna() | g.geometry.is_empty].copy()
missing["st"] = missing.get("polygon_status").astype(str)
claim_no_geom = missing[missing.st.isin(CLAIMS_POLYGON)]
# Baseline: polities already known to claim a polygon they don't have. They are a
# tracked backlog (each needs a real builder in scripts/sources/constructed/build.py
# or an honest downgrade to unassigned); baselining keeps the gate meaningful for
# NEW regressions instead of leaving it permanently red.
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
# priorities, and the distinction is computable from the published contracts. Measured
# today: NONE of the 13 baselined polities is FAOSTAT-mapped, and only four are reachable
# at all — via historical-source aliases, 655 observed rows between them. So the backlog
# is genuinely low-impact, which is worth knowing before anyone spends a week on it.
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

fail = (len(bad_area) > 0 or len(declared_none) > 0 or len(new_claim_no_geom) > 0
        or len(stale_baseline) > 0 or len(undoc) > 0 or len(off_vocab) > 0
        or selfref_over > 0
        or (A.strict and mismatch))
print(f"\n{'FAIL' if fail else 'PASS'}: {len(off_vocab)} off-vocabulary status(es), "
      f"{len(bad_area)} area disagreement(s), "
      f"{max(selfref_over, 0)} self-referential area(s) above the ceiling, "
      f"{len(declared_none)} declares-none-but-has-one, "
      f"{len(new_claim_no_geom)} NEW claimed-but-absent polygon(s), {len(undoc)} undocumented-but-reviewed"
      + (f", {len(mismatch)} identity mismatch(es)" if A.strict else ""))
sys.exit(1 if fail else 0)
