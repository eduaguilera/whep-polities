#!/usr/bin/env python3
"""Validate that every polity's ATTACHED geometry is the territory it claims.

Why this exists: eight polities were found carrying a completely different
country's polygon — San Marino (61 km2) had Albania's (28,624 km2), Indonesia
had India's, French Cameroun had Bulgaria's — because `polygon_feature_id` was
recorded as a row index or a guessed number rather than the Gleditsch-Ward code
that scripts/sources.yaml actually resolves. Nothing checked the result, so the
errors sat in the database silently. This script is that check.

Tests:

  V. VOCABULARY — polygon_status must be one of the five documented values
     (wiki/README.md). This exists because the field had grown to nine values
     plus one page with none — `derived`, `missing`, `approximate` and
     `excluded` were near-synonyms of the documented five — and any value
     outside the set below is silently invisible to test
     C: a page could declare `derived` and carry no polygon at all without
     failing anything. Consolidated 2026-07-28 (GitHub issue #31).

  A. AREA AGREEMENT — measure the attached geometry in an equal-area projection
     and compare against the page's own polygon_area_km2. A large divergence
     means one of them is wrong.

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
                help="skip area check below this size (projection artifacts dominate microstates)")
ap.add_argument("--strict", action="store_true", help="also fail on identity mismatches")
A = ap.parse_args()

# The complete polygon_status vocabulary, as documented in wiki/README.md.
# Every value carries a validator commitment, so an unrecognised one is not a
# harmless synonym — it drops the page out of test C. Adding a value here
# without deciding whether it claims a polygon (VOCAB - {"unassigned"}, below)
# re-creates the bug issue #31 fixed.
VOCABULARY = {"assigned", "proxy", "estimate", "polygon_vintage_drift", "unassigned"}

g = gpd.read_file(GPKG)
have = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
have["measured_km2"] = have.to_crs(EQUAL_AREA).geometry.area / 1e6
print(f"{len(have)} polities with geometry (of {len(g)} rows)")

# ---------- V: polygon_status is in the documented vocabulary ----------
status_all = g.get("polygon_status")
status_all = pd.Series([None] * len(g)) if status_all is None else status_all.reset_index(drop=True)
off_vocab = g.reset_index(drop=True)[~status_all.fillna("").isin(VOCABULARY)]
print(f"\nV. VOCABULARY — {len(off_vocab)} polit(ies) carry a polygon_status outside "
      f"the documented set ({', '.join(sorted(VOCABULARY))})")
for r in off_vocab.itertuples():
    val = getattr(r, "polygon_status", None)
    print(f"   FAIL {r.polity_code:18s} polygon_status={val!r} — not a documented value, "
          f"so this row is invisible to test C")

# ---------- A: area agreement ----------
have["claimed"] = pd.to_numeric(have.get("polygon_area_km2"), errors="coerce")
chk = have[have.claimed.notna() & (have.claimed >= A.min_km2)].copy()
chk["divergence"] = (chk.measured_km2 - chk.claimed).abs() / chk.claimed
diverging = chk[chk.divergence > A.tolerance].sort_values("divergence", ascending=False)
# Only `assigned` CLAIMS the polygon is the territory, so only there is a
# divergence a contradiction. estimate/proxy/*_drift already say the polygon is
# inexact, and those pages document the direction and magnitude — report but
# don't fail, otherwise the gate punishes honest documentation. The complement
# (VOCABULARY - EXACT_CLAIM) is exactly the inexact-or-absent values, and test V
# guarantees no page sits outside VOCABULARY.
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

# ---------- C: status claims a polygon that was never attached ----------
# `assigned`/`proxy`/`estimate` all assert a polygon exists. When the build
# cannot resolve polygon_feature_id it attaches nothing and says so only in a
# summary line, so a page can claim an exact polygon while carrying none —
# e.g. an id written as prose ("composed-union: cowcode=452 UNION cowcode=462")
# instead of a resolvable value. That is a direct contradiction, not a gap.
#
# Derived from the vocabulary rather than listed by hand: every documented value
# except `unassigned` asserts a polygon. Before 2026-07-28 this was a hand-kept
# list and the four legacy values (`derived`, `missing`, `approximate`,
# `excluded`) were absent from it, so 21 pages — plus one carrying no value at
# all — were exempt from this test without saying so; test V stops that
# recurring.
CLAIMS_POLYGON = VOCABULARY - {"unassigned"}
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
print(f"\nC. CLAIMED BUT ABSENT — {len(missing)} polities have no geometry; "
      f"{len(claim_no_geom)} declare a polygon_status that asserts one "
      f"({len(baseline)} baselined, {len(new_claim_no_geom)} new)")
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
    sub = pol[pol.polygon_source.astype(str).str.contains("cshapes", na=False)]
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

fail = (len(off_vocab) > 0 or len(bad_area) > 0 or len(new_claim_no_geom) > 0
        or len(undoc) > 0 or (A.strict and mismatch))
print(f"\n{'FAIL' if fail else 'PASS'}: {len(off_vocab)} off-vocabulary status(es), "
      f"{len(bad_area)} area disagreement(s), "
      f"{len(new_claim_no_geom)} NEW claimed-but-absent polygon(s), {len(undoc)} undocumented-but-reviewed"
      + (f", {len(mismatch)} identity mismatch(es)" if A.strict else ""))
sys.exit(1 if fail else 0)
