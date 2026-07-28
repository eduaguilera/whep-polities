#!/usr/bin/env python3
"""Guard a STRUCTURAL change to the polity set: prove no data row was lost.

Creating, splitting, merging, retiring or re-dating a polity re-routes the data
that matches it. The matcher resolves a label by alias, then by iso3 family +
year containment, then by name; a structural edit can therefore move rows that
were never mentioned on the page being edited. Every failure below is real, from
one session, and every one was invisible in the wiki diff:

  * The Indonesia merge renamed a row to "Dutch East Indies" and silently
    ORPHANED 23 rows whose label had resolved by NAME. Nothing pointed at the
    old name any more, so those rows simply stopped matching.
  * The India split typed the new rows `colonial`, so HYD-1724-1948 (Hyderabad,
    a princely state) outranked them on the family preference and took 36 rows
    of plainly national "india" data.
  * The Newfoundland fix moved 54 rows of 1948 Canadian data to the wrong side
    of a boundary. The TOTAL matched count was unchanged — only a PER-POLITY
    diff exposed it.
  * ETH-1936-1941 shipped with `polygon_area_km2: 1000000`, a rounded
    placeholder that no equal-area measurement would ever produce.

So a total-count check is not enough, and a wiki review is not enough. This
script is the mechanical half of the structural-change checklist (the checklist
itself, including the human steps, is in
pipelines/polity-autoimprove/README.md, "Structural-change checklist").

Workflow — snapshot BEFORE the edit, compare AFTER:

    python3 scripts/structural_change_check.py --snapshot
    ... edit the wiki page(s), run scripts/build_database.py ...
    python3 scripts/structural_change_check.py --compare

`--snapshot` re-runs the matcher and records per-polity matched-row counts, the
total, and which labels currently match. `--compare` re-runs the matcher and
reports:

  1. TOTAL matched rows, before vs after — a DROP is a FAILURE (rows orphaned).
  2. PER-POLITY movement, biggest first — the Newfoundland case. Not auto-
     judgeable: a human confirms each movement was the intended one.
  3. Polities that received rows before and now receive ZERO — a row was
     superseded without its data being re-routed.
  4. Labels that became UNMATCHED — the rename-orphans-a-label case.

then runs the mechanical checks that must follow any structural change:
`scripts/audit_family_shadowing.py`, `scripts/validate_polygons.py`, and a scan
for placeholder-looking `polygon_area_km2` values (exact multiples of 100,000 —
a measured equal-area figure is never that round). The snapshot records areas
too, so a round value THIS change introduced or altered blocks, while one that
already sat in the database is reported as pre-existing cleanup.

NOT IN CI, deliberately. Getting matched-row counts requires the matcher, which
reads the consolidated layer-B dataset from personal Nextcloud
(`WHEP_LAYERB`, ~190k rows, not redistributable). CI has no access to it, so
this is a LOCAL pre/post-change tool and is intentionally absent from
.github/workflows/validate.yml. Issue #17 tracks that CI limitation.

Usage:
  python3 scripts/structural_change_check.py --snapshot [--no-rematch]
  python3 scripts/structural_change_check.py --compare  [--no-rematch] [--top N]
                                                        [--skip-checks]
Exit 1 if the comparison fails (or, with --snapshot, if the snapshot could not
be taken).
"""
import argparse, json, os, subprocess, sys, time
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
MATCHER = os.path.join(REPO, "pipelines/polity-autoimprove/01_match_and_findings.py")
MATCHED = os.path.join(STATE, "matched_rows.parquet")
SNAPSHOT = os.path.join(STATE, "structural_snapshot.json")   # gitignored per-run artefact
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
DEAD = ("retired", "superseded")

ap = argparse.ArgumentParser()
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--snapshot", action="store_true",
               help="record the pre-change per-polity matched-row counts")
g.add_argument("--compare", action="store_true",
               help="re-run the matcher and diff against the snapshot")
ap.add_argument("--no-rematch", action="store_true",
                help="reuse the existing state/matched_rows.parquet instead of re-running the matcher")
ap.add_argument("--top", type=int, default=40,
                help="how many per-polity movements to print (default 40)")
ap.add_argument("--skip-checks", action="store_true",
                help="skip the follow-up mechanical checks (shadowing, polygons, placeholder areas)")
A = ap.parse_args()


def section(title):
    print(f"\n=== {title} ===")


def run_matcher():
    """Re-run 01_match_and_findings.py so matched_rows.parquet reflects the tree."""
    if A.no_rematch:
        if not os.path.exists(MATCHED):
            sys.exit(f"FAIL: --no-rematch but {os.path.relpath(MATCHED, REPO)} does not exist")
        age = (time.time() - os.path.getmtime(MATCHED)) / 60
        print(f"reusing {os.path.relpath(MATCHED, REPO)} ({age:.0f} min old)")
        return
    print(f"running the matcher ({os.path.relpath(MATCHER, REPO)}) ...")
    r = subprocess.run([sys.executable, MATCHER], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:]); print(r.stderr[-3000:])
        sys.exit("FAIL: the matcher did not run. It needs the layer-B dataset "
                 "(WHEP_LAYERB); this script cannot work without it.")
    for line in r.stdout.splitlines():
        if line.startswith(("Stage 0:", "bare-iso", "excluded from matching")):
            print("  " + line)


def counts():
    """Per-polity matched-row counts, the total, matching labels, and areas."""
    df = pd.read_parquet(MATCHED)
    m = df[df.whep_code.notna()]
    per = m.groupby("whep_code").size().sort_values(ascending=False)
    # a label is the (entity, iso-in-data) pair the matcher routes; keep the
    # pairs that currently resolve, so a rename that orphans one is visible
    lab = m[["country", "iso3c"]].fillna("").astype(str).drop_duplicates()
    labels = sorted({f"{c}\t{i}" for c, i in lab.itertuples(index=False)})
    p = pd.read_csv(POLDB, keep_default_na=False, na_values=[""])
    area = pd.to_numeric(p.polygon_area_km2, errors="coerce")
    return {
        "total_rows": int(len(df)),
        "matched_rows": int(len(m)),
        "per_polity": {k: int(v) for k, v in per.items()},
        "labels": labels,
        "areas": {c: (None if pd.isna(v) else float(v))
                  for c, v in zip(p.polity_code, area)},
    }


def names():
    p = pd.read_csv(POLDB, keep_default_na=False, na_values=[""])
    return (dict(zip(p.polity_code, p.polity_name)),
            dict(zip(p.polity_code, p.wiki_status.astype(str))))


# ---------------------------------------------------------------- snapshot
if A.snapshot:
    run_matcher()
    snap = counts()
    snap["taken_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    snap["git_head"] = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                                      capture_output=True, text=True).stdout.strip()
    json.dump(snap, open(SNAPSHOT, "w"), indent=1)
    section("SNAPSHOT TAKEN")
    print(f"  {snap['matched_rows']:,} matched rows of {snap['total_rows']:,} "
          f"({100*snap['matched_rows']/snap['total_rows']:.2f}%)")
    print(f"  {len(snap['per_polity']):,} polities receive data; "
          f"{len(snap['labels']):,} labels resolve")
    print(f"  written to {os.path.relpath(SNAPSHOT, REPO)}  (HEAD {snap['git_head']})")
    print("\nPASS: snapshot recorded. Make the structural change, run "
          "scripts/build_database.py, then re-run with --compare.")
    sys.exit(0)

# ---------------------------------------------------------------- compare
if not os.path.exists(SNAPSHOT):
    sys.exit(f"FAIL: no snapshot at {os.path.relpath(SNAPSHOT, REPO)} — run "
             f"--snapshot BEFORE making the structural change.")
before = json.load(open(SNAPSHOT))
run_matcher()
after = counts()
name, status = names()
fails, reviews = [], []


def label(code):
    return f"{code:18s} {str(name.get(code, '?'))[:38]:38s}"


# 1. total ------------------------------------------------------------------
section("1. TOTAL MATCHED ROWS")
b, a = before["matched_rows"], after["matched_rows"]
print(f"  snapshot ({before.get('taken_at')}, HEAD {before.get('git_head')}): {b:,}")
print(f"  now:                                        {a:,}")
print(f"  delta: {a-b:+,}   (of {after['total_rows']:,} non-aggregate rows)")
if a < b:
    fails.append(f"total matched rows DROPPED by {b-a:,} — those rows were orphaned")
    print(f"  FAIL: {b-a:,} rows no longer match any polity")
elif a > b:
    print(f"  OK: {a-b:,} more rows match than before")
else:
    print("  OK: total unchanged — but see section 2, the total alone hides "
          "rows moving to the WRONG polity")

# 2. per-polity movement ----------------------------------------------------
section("2. PER-POLITY MOVEMENT (biggest first)")
bp, apc = before["per_polity"], after["per_polity"]
moved = []
for code in set(bp) | set(apc):
    d = apc.get(code, 0) - bp.get(code, 0)
    if d: moved.append((abs(d), d, code))
moved.sort(reverse=True)
print(f"  {len(moved)} polity/polities changed row count "
      f"(gained {sum(d for _, d, _ in moved if d > 0):+,} / "
      f"lost {sum(d for _, d, _ in moved if d < 0):+,})")
if moved:
    print()
    for _, d, code in moved[:A.top]:
        tag = "NEW " if code not in bp else ("GONE" if apc.get(code, 0) == 0 else "    ")
        print(f"   {tag} {d:+7,}  {label(code)} {bp.get(code,0):>7,} -> {apc.get(code,0):>7,}")
    if len(moved) > A.top:
        print(f"   ... {len(moved)-A.top} more (raise --top to see them)")
    reviews.append(f"{len(moved)} polity/polities changed row count — confirm EACH "
                   f"movement is the intended one (the Newfoundland case had an "
                   f"unchanged total and rows on the wrong side of a boundary)")

# 3. polities that went to zero --------------------------------------------
section("3. POLITIES THAT NOW RECEIVE ZERO ROWS (but did before)")
zeroed = sorted(((bp[c], c) for c in bp if apc.get(c, 0) == 0), reverse=True)
print(f"  {len(zeroed)} polity/polities")
for n, code in zeroed[:A.top]:
    print(f"   FAIL {n:>7,} rows lost  {label(code)} wiki_status={status.get(code,'?')}")
if zeroed:
    fails.append(f"{len(zeroed)} polity/polities lost ALL their data "
                 f"({sum(n for n, _ in zeroed):,} rows) — a row was superseded "
                 f"without its data being re-routed to the successor")

# 4. labels that became unmatched ------------------------------------------
section("4. LABELS THAT BECAME UNMATCHED")
lost = sorted(set(before["labels"]) - set(after["labels"]))
gained = len(set(after["labels"]) - set(before["labels"]))
print(f"  {len(lost)} label(s) stopped resolving; {gained} newly resolve")
if lost:
    # how many rows those labels carry now, so the cost is explicit
    df = pd.read_parquet(MATCHED)
    key = df.country.fillna("").astype(str) + "\t" + df.iso3c.fillna("").astype(str)
    n_rows = df.assign(_k=key).groupby("_k").size()
    for k in lost[:A.top]:
        c, i = k.split("\t")
        print(f"   FAIL {n_rows.get(k, 0):>7,} rows  label={c!r} iso={i or '-'}  "
              f"(resolved before, now unmatched — add an alias for the old name)")
    fails.append(f"{len(lost)} label(s) that resolved before are now UNMATCHED — "
                 f"a rename orphaned them (add an alias, do not leave the rows adrift)")

# ---------------------------------------------------------------- mechanical follow-ups
if not A.skip_checks:
    section("5. PLACEHOLDER polygon_area_km2")
    p = pd.read_csv(POLDB, keep_default_na=False, na_values=[""])
    live = p[~p.wiki_status.astype(str).isin(DEAD)].copy()
    live["area"] = pd.to_numeric(live.polygon_area_km2, errors="coerce")
    ar = live[live.area.notna() & (live.area > 0)]
    place = ar[ar.area % 100_000 == 0]
    suspect = ar[(ar.area % 10_000 == 0) & (ar.area % 100_000 != 0)]
    print(f"  {len(ar):,} live polities carry an area; a measured equal-area figure "
          f"(ESRI:54034) is never an exact multiple of 100,000")
    # only areas THIS change introduced or altered block: pre-existing round
    # figures are a separate cleanup, not this change's regression
    was = before.get("areas", {})
    new_place = [r for r in place.itertuples() if was.get(r.polity_code) != r.area]
    old_place = [r for r in place.itertuples() if was.get(r.polity_code) == r.area]
    for r in new_place:
        print(f"   FAIL {r.area:>12,.0f} km2  {label(r.polity_code)} <- placeholder "
              f"introduced/changed by this change; re-measure the attached geometry")
    for r in old_place:
        print(f"   WARN {r.area:>12,.0f} km2  {label(r.polity_code)} <- rounded, but "
              f"predates this change (pre-existing placeholder; fix separately)")
    for r in suspect.itertuples():
        tag = "FAIL" if was.get(r.polity_code) != r.area else "WARN"
        print(f"   {tag} {r.area:>12,.0f} km2  {label(r.polity_code)} <- suspiciously "
              f"round (multiple of 10,000); confirm it was measured")
    new_suspect = [r for r in suspect.itertuples() if was.get(r.polity_code) != r.area]
    if new_place:
        fails.append(f"{len(new_place)} polity/polities carry a rounded placeholder "
                     f"polygon_area_km2 introduced by this change "
                     f"(ETH-1936-1941's 1000000 case)")
    if new_suspect:
        fails.append(f"{len(new_suspect)} suspiciously round area(s) (multiple of "
                     f"10,000) introduced by this change")
    if old_place or (len(suspect) - len(new_suspect)):
        reviews.append(f"{len(old_place) + len(suspect) - len(new_suspect)} "
                       f"pre-existing round area(s) — cleanup, not this change")

    for script in ("audit_family_shadowing.py", "validate_polygons.py"):
        section(f"6. {script}")
        r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", script)],
                           cwd=REPO, capture_output=True, text=True)
        out = (r.stdout or "").rstrip().splitlines()
        for line in out[-30:]: print("  " + line)
        if r.returncode != 0:
            if r.stderr.strip(): print("  " + r.stderr.strip()[-1500:])
            fails.append(f"{script} exited {r.returncode} — a structural change "
                         f"broke it (new row ties on type rank / geometry claim)")
else:
    print("\n(mechanical follow-up checks skipped: --skip-checks)")

# ---------------------------------------------------------------- verdict
section("VERDICT")
for f in fails:    print(f"  FAIL    {f}")
for r in reviews:  print(f"  REVIEW  {r}")
if not fails and not reviews:
    print("  nothing moved, nothing flagged"
          + ("  (follow-up checks were skipped)" if A.skip_checks else ""))
print("\nStill HUMAN, not checkable here (see the checklist in "
      "pipelines/polity-autoimprove/README.md):")
print("  * the wiki page body and frontmatter agree, and say what changed and why")
print("  * a wiki/log.md entry of kind `decision` naming who signed off")
print(f"\n{'FAIL' if fails else 'PASS'}: {len(fails)} blocking problem(s), "
      f"{len(reviews)} item(s) needing human confirmation")
sys.exit(1 if fails else 0)
