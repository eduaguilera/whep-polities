#!/usr/bin/env python3
"""Prove the gates can fail.

Twenty-four validators guard this database and every one of them passes. That is
the intended state and it is also indistinguishable, from the outside, from
twenty-four validators that cannot fail. A gate whose criteria no real row can
satisfy prints PASS forever and protects nothing.

The distinction is not decidable by reading the code -- I tried, and reasoned
myself into two wrong conclusions in a row. It is decidable by mutation: inject a
defect of exactly the shape a gate claims to catch, and require that gate to
FAIL. That is what this script does.

It matters because the sibling repository has already paid for an assertion that
never executed. A bidirectional baseline there sat twelve fixes out of date while
its test skipped on every run, local and CI, because the file it reads lives on
an unmerged branch. The test was correct and simply not running. Nothing in a
green summary line distinguishes "passed" from "did not execute", so the only
defence is to demand a failure on demand.

Each case below stages a scratch repo whose scripts/ is a copy and whose
data/final/ holds a MUTATED input, then runs one gate against it and requires a
non-zero exit AND that the output names the injected defect. The real data is
never written to.

Fifteen cases, each mutating one input: the GeoPackage for the geometry gates, a CSV
or the alias registry for the contract gates, a WIKI PAGE -- the source of truth every
other artefact derives from -- for build_database, and a BUILDER SCRIPT's own literal
for the reporting-area aggregates. The counts in this paragraph are prose and have gone
stale before — as of 2026-08-13 there are 26 cases against 37 gate scripts, and `main()`
prints both, which is the checkable version. Chosen by what it would cost if the gate were
inert rather than by what is easy to mutate -- case 6 guards the invariant that a
retired polity never receives data, which is not otherwise detectable, because a
retired duplicate carries the same name, iso3 and often a valid geometry as its live
successor. The last two were added after their own gates were, which is the
wrong order -- both were mutation-tested by hand when written, and a hand test
proves the gate worked once on one machine. This file is what makes it a standing
claim.

WHAT MUTATION TESTING ESTABLISHED, beyond that the gates fire:

  The containment check normalises overlap by the SMALLER polygon, so a successor
  bound to a wrong feature strictly inside the right territory scores ~1.0 and
  passes. That looks like a hole, and symmetrising it -- also normalising by the
  larger -- was the obvious fix. Measuring first showed the fix would be a
  mistake: 26 consecutive pairs pass the smaller-normalised metric and fail a
  larger-normalised one, and they are overwhelmingly REAL HISTORY. USA-1848-1867
  -> USA-1867-1959 is the Alaska purchase (3.5M -> 8.9M km2); ISR-1948-1967 ->
  ISR-1967-1979 is the Six-Day War; HUN-1918-1919 -> HUN-1920-1938 is the Treaty
  of Trianon; the remainder is colonial expansion into the hinterland. The
  smaller-normalised metric is invariant to legitimate expansion and contraction,
  which is precisely why it is the right one, and 26 historical facts would have
  been baselined as defects to "close" a hole.

  The hole is closed by a different instrument. validate_family_areas measures
  the same shrink at 222x its family median and names polygon_feature_id as the
  thing to check. Position and magnitude are covered by two gates, each blind to
  what the other sees. Case 3 pins that, so a future change to either cannot
  quietly leave the shrink case uncovered.

  Case 8 nearly passed for the wrong reason twice, which is the argument for this
  script requiring that a gate NAME the defect and not merely exit non-zero. Staged
  without sources.yaml it died with a FileNotFoundError; staged without the wiki it
  would have found nothing to compare. Both exit 1. Only the name check separated
  "detected the mutation" from "crashed before reaching it".

  crosscheck_matchers.py WAS DELIBERATELY NOT COVERED HERE, and the history is worth
  keeping because the stated reason was right and the conclusion was wrong. It compares
  two independent matchers against each other, so producing a disagreement means changing
  what ONE of them computes -- and both read the same applied_aliases.csv, so mutating the
  registry moves both identically and they still agree. An attempt that repointed a
  faostat Kenya alias made the gate pass, which reads as "the gate cannot fail" and was
  not: staged on its own it reported 281 mappings, 276 agreements and the 3 baselined
  differences, so it worked. The mutation was the wrong shape, like the REMOVED_ prefix
  that could not hide a substring. The note then concluded that covering it needed a
  surgical edit to matchlib's resolution logic, "brittle to write".
  Issue 16 made it easy instead of brittle, by changing what the gate asserts rather than
  how it is mutated: the gate now also pins a golden FIXTURE of routing decisions to
  expected polity codes, and a fixture has no second party to move in step with it. The
  last case in this file empties matchlib's DEAD_STATUS -- one token -- and the fixture
  reports ARG-1800-2025 by name. The lesson is that "this gate cannot be mutated" was
  really "this gate compares two things that move together"; giving it one absolute
  assertion was the fix.

  Case 5 exists because its gate shipped with a blind spot. The alias-chain check
  skipped rows with empty year bounds, so it missed "turkey", where an UNRANGED
  alias sits alongside a ranged one and therefore overlaps it at every year. That
  was found by reconciling the gate's count against the consumer's -- 24 against
  25 -- not by mutation, which is a reminder that a self-test proves a gate fires
  on the defect you thought of.

Usage:
  python3 scripts/selftest_gates.py            # all cases
  python3 scripts/selftest_gates.py --case 2   # one case, by number
"""
import argparse
import csv
import math
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
CSV = os.path.join(REPO, "data/final/polities_database.csv")


def fingerprint_real_data() -> str:
    """Snapshot the repository's working-tree state, so a leaking mutation is visible.

    A case that writes a file it did not declare in WRITABLE writes through `stage()`'s
    symlink and straight into the repository. That has happened TWICE here -- once
    renaming a polity, once rewriting an iso3_code -- and both times the only thing that
    caught it was a human reading `git status` afterwards. A comment at the WRITABLE entry
    did not prevent the second, so the harness checks instead of asking.

    Uses `git status --porcelain` rather than hashing a hand-listed set of files, because
    the first version of this did hash a list -- and that list missed `wiki/polities`,
    which the `build_database.py` case declares writable. A guard that covers only the
    files I thought of is the same class of mistake it exists to catch.
    """
    proc = subprocess.run(
        ["git", "-C", REPO, "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""  # not a git checkout; the guard simply does not apply
    return proc.stdout


def stage(gate: str, extra: tuple = (), writable: tuple = ()) -> str:
    """A scratch repo holding one gate, its baseline, and a writable data/final."""
    root = tempfile.mkdtemp(prefix="selftest-gates-")
    os.makedirs(os.path.join(root, "scripts"))
    os.makedirs(os.path.join(root, "data/final"))
    for name in (gate, *extra):
        src = os.path.join(REPO, "scripts", name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(root, "scripts", name))
    baseline = gate.replace(".py", "_baseline.txt")
    src = os.path.join(REPO, "scripts", baseline)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(root, "scripts", baseline))
    # The CSV is only read for wiki_status by the geometry gates, so a symlink is safe
    # there; the GeoPackage is what those mutate, so it is always a real copy. The
    # CSV-level gates below mutate the CSV or the alias map instead, so those cases ask
    # for a real copy via `writable`.
    if "polities_database.csv" in writable:
        shutil.copy(CSV, os.path.join(root, "data/final/polities_database.csv"))
    else:
        os.symlink(CSV, os.path.join(root, "data/final/polities_database.csv"))
    for name in writable:
        if name == "polities_database.csv":
            continue
        # A name containing a slash is repo-relative, for inputs that do not live under
        # data/final -- the alias registry is under pipelines/.
        if "/" in name:
            dest = os.path.join(root, name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            src = os.path.join(REPO, name)
        else:
            dest = os.path.join(root, "data/final", name)
            src = os.path.join(REPO, "data/final", name)
        if os.path.isdir(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
        elif os.path.exists(src):
            shutil.copy(src, dest)
    return root


def run(root: str, gate: str) -> tuple:
    p = subprocess.run(
        [sys.executable, os.path.join(root, "scripts", gate), *ARGS.get(gate, ())],
        capture_output=True,
        text=True,
        timeout=600,
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# --- the mutations ------------------------------------------------------------
# Each returns a one-line description of what it did, having written the mutated
# GeoPackage into `root`.


def mutate_pinned_disjoint_overlap(root, gpd, make_valid, affinity):
    """Put West Papua back inside IDN-OTH-1949-1951, which is the defect
    audit_family_shadowing's PINNED_DISJOINT exists to catch.

    THE PROSE BASELINE ALREADY "COVERED" THIS PAIR AND THE GATE STILL PASSED. For a
    day, BASELINE carried the entry `NNG-1949-1963 / IDN-OTH-1949-1951` with the string
    "REAL OVERLAP: 405,513 km2" in it, and every run reported PASS -- because a pair
    named in the baseline is an accepted pair, whatever the prose beside it says. That is
    what this case really tests: not that a number can be recomputed, but that describing
    a defect in a baseline no longer counts as handling it.
    """
    g = gpd.read_file(GPKG)
    i = g.index[g.polity_code == "IDN-OTH-1949-1951"][0]
    nng = g[g.polity_code == "NNG-1949-1963"].iloc[0].geometry
    g.loc[i, "geometry"] = make_valid(g.loc[i, "geometry"].union(nng))
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "unioned NNG-1949-1963 back into IDN-OTH-1949-1951, restoring the double claim"


def mutate_shadowing_twin(root, gpd, make_valid, affinity):
    """A same-iso3, time-overlapping, same-type twin far smaller than its family
    peer: the exact conjunction audit_family_shadowing says it looks for."""
    import pandas as pd

    g = gpd.read_file(GPKG)
    base = g[g.polity_code == "FRA-1800-1871"].iloc[0].copy()
    twin = base.copy()
    twin["polity_code"] = "FRA-1820-1860"
    twin["start_year"], twin["end_year"] = 1820, 1860
    twin["geometry"] = base.geometry.centroid.buffer(0.5)
    out = gpd.GeoDataFrame(
        pd.concat([g, gpd.GeoDataFrame([twin], crs=g.crs)], ignore_index=True),
        crs=g.crs,
    )
    out.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "added FRA-1820-1860, a small same-type twin overlapping FRA-1800-1871"


def mutate_disjoint_successor(root, gpd, make_valid, affinity):
    """A period moved off its own territory -- the mis-binding of PLAUSIBLE SIZE
    that no area-based check can see, which is the stated reason the containment
    gate exists."""
    g = gpd.read_file(GPKG)
    i = g.index[g.polity_code == "FRA-1871-1919"][0]
    g.loc[i, "geometry"] = affinity.translate(
        g.loc[i, "geometry"], xoff=-150.0, yoff=-20.0
    )
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "translated FRA-1871-1919 into the Pacific, disjoint from its neighbours"


def mutate_shrunk_successor(root, gpd, make_valid, affinity):
    """A period bound to a much smaller feature INSIDE the right territory. The
    containment gate cannot see this by construction; the area gate must."""
    g = gpd.read_file(GPKG)
    src = g.loc[g.polity_code == "FRA-1800-1871", "geometry"].iloc[0]
    i = g.index[g.polity_code == "FRA-1871-1919"][0]
    g.loc[i, "geometry"] = src.centroid.buffer(0.3)
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "shrank FRA-1871-1919 to a disc inside FRA-1800-1871"



def mutate_collapsed_planar_border(root, gpd, make_valid, affinity):
    """Re-simplify the USA polygon at 0.01 degrees, which is how the defect was MADE.

    Not a synthetic mutation: this is the exact operation `build_database.py` used to
    perform last, and it is what turned CShapes' 124-vertex 49th-parallel border into a
    single 27.6-degree chord. Douglas-Peucker measures deviation from the chord in PLANAR
    degrees, so every vertex sitting on the parallel is the first thing it deletes -- and
    under s2 the surviving chord renders as a great circle reaching latitude 49.83, 92 km
    into Canada, booking 12.33 Mha of Canadian prairie to the United States.

    This case is the reason the gate exists rather than a nice-to-have, because the defect
    is invisible to every other gate here BY CONSTRUCTION. Planar area is unchanged to the
    bit, so the area gates cannot move; USA + CAN still sums to exactly 1.0000 in every
    cell, so nothing conservation-based can object. A gate that only fires on
    non-conservation would pass this mutation, which is precisely what the real database
    did for as long as it shipped."""
    from shapely import simplify

    g = gpd.read_file(GPKG)
    i = g.index[g.polity_code == "USA-1959-2025"][0]
    g.loc[i, "geometry"] = simplify(g.loc[i, "geometry"], 0.01, preserve_topology=True)
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return (
        "re-ran SimplifyPreserveTopology(0.01) on USA-1959-2025, collapsing its "
        "49th-parallel border back to a single chord"
    )


def mutate_code_year_disagreement(root, gpd, make_valid, affinity):
    """Make one polity's start_year disagree with the years in its own code. A consumer
    reading the span off the identifier then gets a different answer from one reading the
    columns, which is how two aliases came to resolve 1962-1964 to a polity its columns
    say had ended."""
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    hit = 0
    for r in rows:
        if r["polity_code"] == "FRA-1800-1871":
            r["start_year"] = "1799"
            hit += 1
    assert hit == 1, f"expected one FRA-1800-1871 row, found {hit}"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    return "set FRA-1800-1871's start_year to 1799, contradicting its own code"


def mutate_cross_family_overlap(root, gpd, make_valid, affinity):
    """Re-create issue 82's Morocco defect: two LIVE polities in DIFFERENT families
    claiming Moroccan territory for the same years.

    The original was MOR-1956-1958 against MAR-1911-1958, retired by PR 83. This injects
    the same shape from the other end -- MAR-1911-1958 backdated to 1900, so it collides
    with MOR-1800-1904, whose family the successor map names as the previous holder of
    MAR's territory. Backdating rather than adding a row keeps the mutation inside the one
    file the case rewrites.

    The point of the case is that the SAME-family half of this gate provably cannot fire
    instead: MAR-* and MOR-* are different prefixes, which is exactly why the issue said
    no gate catches it.
    """
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    hit = 0
    for r in rows:
        if r["polity_code"] == "MAR-1911-1958":
            r["start_year"] = "1900"
            hit += 1
    assert hit == 1, f"expected one MAR-1911-1958 row, found {hit}"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    return (
        "backdated MAR-1911-1958 to 1900 so it claims Moroccan territory that "
        "MOR-1800-1904, a different family, already claims"
    )


def mutate_new_iso_code(root, gpd, make_valid, affinity):
    """Give a polity an iso3_code the baseline has never seen. A consumer joins on that
    vocabulary, so a new value silently changes which rows an ISO-keyed join matches --
    and if the value is a local invention rather than a real ISO code, it matches nothing
    at all, which is how four dissolved federations came to be unable to reach WHEP's
    LUH2 land series. Injected as a plausible-looking three-letter code rather than
    obvious junk, since the gate must catch the plausible case."""
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    victim = next((r for r in rows if (r.get("iso3_code") or "").strip()), None)
    assert victim is not None, "no row carrying an iso3_code"
    victim["iso3_code"] = "ZZQ"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    return "ZZQ"


def mutate_dissolved_iso_blanked(root, gpd, make_valid, affinity):
    """Blank the iso3_code of a dissolved state that carries its own ISO 3166-3 code.

    This is the exact defect issue 55 was filed for: the USSR's three rows carried nothing,
    so they belonged to no ISO family and a consumer holding `SUN` -- which WHEP's own
    `regions_full` and `polity_area_crosswalk` both reference -- resolved to nothing while
    the polity plainly existed. Blanking is chosen over corrupting the value because a blank
    is the version that hides: it looks like "this entity has no code" rather than an error,
    which is precisely how it survived long enough to reach a consumer.

    Yugoslavia is the victim rather than the USSR so the case does not merely re-test the row
    that motivated the gate.
    """
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    victim = next((r for r in rows if r["polity_code"] == "F248-1947-1991"), None)
    assert victim is not None, "F248-1947-1991 (Yugoslavia) not in the database"
    assert (victim.get("iso3_code") or "").strip() == "YUG", "victim no longer carries YUG"
    victim["iso3_code"] = ""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    return "F248-1947-1991"


def mutate_name_collision(root, gpd, make_valid, affinity):
    """Rename a live polity to a name a DIFFERENT live polity already holds over the same
    years. WHEP's resolve_polity_label() then cannot pick between them and returns NA for
    that label — indistinguishable, on the consumer's side, from a label nobody has
    mapped. Denmark is renamed to Norway here because both are live across the same span,
    which is exactly the condition the gate looks for."""
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    victim = next(
        (r for r in rows if r["polity_code"].startswith("DNK-")
         and (r.get("wiki_status") or "") != "retired"),
        None,
    )
    assert victim is not None, "no live DNK row to rename"
    target = next(
        (r for r in rows if r["polity_code"].startswith("NOR-")
         and (r.get("wiki_status") or "") != "retired"
         and int(r["start_year"]) < int(victim["end_year"])
         and int(victim["start_year"]) < int(r["end_year"])),
        None,
    )
    assert target is not None, "no live NOR row overlapping the DNK row"
    victim["polity_name"] = target["polity_name"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    return (
        f"renamed {victim['polity_code']} to {target['polity_name']!r}, which "
        f"{target['polity_code']} already holds over the same years"
    )


def mutate_touching_alias_chain(root, gpd, make_valid, affinity):
    """Extend one alias's year_end so it collides with the next row in its chain. The
    boundary year then resolves by whichever row the matcher reaches first."""
    path = os.path.join(root, "data/final/label_alias_map.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    # A chain the baseline does not already contain, so the mutation is what fails.
    target = None
    for r in rows:
        if r.get("source_label") == "Kenya" and r.get("year_end"):
            target = r
            break
    assert target is not None, "no Kenya alias to mutate"
    target["year_end"] = str(int(target["year_end"]) + 40)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    return "extended a Kenya alias's year_end by 40 years into the next row's range"


def mutate_alias_past_the_ceiling(root, gpd, make_valid, affinity):
    """Push the "Andorra" alias's year_end one year past the 2025 ceiling.

    This exists because of what issue 79 changed. validate_alias_year_coverage now SKIPS an
    alias whose target's exclusive end_year is 2025, since a live polity has no real last
    year for the alias to overclaim -- 67 of the 201 rows it was flagging were that and
    nothing else. The risk of an exclusion is that it swallows the real thing too, so the
    skip is conditioned on `year_end <= CEILING` and this case is the proof: AND-1800-2025
    is exactly such a ceiling polity, and an alias reaching 2026 against it claims a year
    that is past coverage on any reading. If the guard were dropped the gate would go quiet
    on it, and no other gate compares an alias's year_end against its target's span."""
    path = os.path.join(root, "data/final/label_alias_map.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    target = None
    for r in rows:
        if r.get("source_label") == "Andorra" and r.get("polity_code") == "AND-1800-2025":
            target = r
            break
    assert target is not None, "no Andorra alias on AND-1800-2025 to mutate"
    target["year_end"] = "2026"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    return "set the Andorra alias's year_end to 2026, one year past the ceiling"



def mutate_alias_to_dead_polity(root, gpd, make_valid, affinity):
    """Point one alias at a RETIRED polity. This is the invariant the whole dead_status
    mechanism exists for: a retired row must never receive data, and it is not otherwise
    distinguishable -- retired duplicates carry the same name, iso3 and often a valid
    geometry as their live successor. If this gate were inert, data would route to a
    withdrawn row and nothing downstream would object."""
    polities = os.path.join(root, "data/final/polities_database.csv")
    with open(polities, encoding="utf-8") as fh:
        dead = [
            r["polity_code"]
            for r in csv.DictReader(fh)
            if (r.get("wiki_status") or "") in ("retired", "superseded")
        ]
    assert dead, "no dead polity to aim an alias at"
    target = sorted(dead)[0]

    path = os.path.join(root, "pipelines/polity-autoimprove/state/applied_aliases.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    rows[0]["polity_code"] = target
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return f"aimed the first alias at {target}, which is retired or superseded"



def mutate_polity_without_regenerating_manifest(root, gpd, make_valid, affinity):
    """Change a polity's identity in the CSV and leave the manifest as it was. The
    manifest's `identity_sha256` is what a consumer compares against its embedded copy to
    detect drift in one step -- so if `--check` were inert, a stale contract would ship
    while claiming to be current, and every consumer's drift detection would be reading a
    hash of the wrong thing."""
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    hit = 0
    for r in rows:
        if r["polity_code"] == "FRA-1919-2025":
            r["polity_name"] = "France (mutated)"
            hit += 1
    assert hit == 1, f"expected one FRA-1919-2025 row, found {hit}"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return "renamed FRA-1919-2025 in the CSV without regenerating the manifest"



def mutate_wiki_without_rebuilding(root, gpd, make_valid, affinity):
    """Edit a wiki page's frontmatter and leave the derived CSV alone. The wiki is the
    SOURCE OF TRUTH here and every other artefact is derived from it, so this gate is the
    only thing standing between an edit and a database that silently disagrees with it.
    Its documented first catch was exactly this: a wiki edit that never propagated."""
    page = os.path.join(root, "wiki/polities/fra-1919-2025.md")
    assert os.path.exists(page), f"missing wiki page: {page}"
    with open(page, encoding="utf-8") as fh:
        text = fh.read()
    marker = "\ncow: "
    assert marker in text, "no cow field to edit in the France page"
    head, rest = text.split(marker, 1)
    _old, tail = rest.split("\n", 1)
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(head + marker + "999" + "\n" + tail)
    return "set the France page's cow code to 999 without rebuilding the CSV"



def write_gpkg(gdf, root):
    """Write a mutated GeoDataFrame over the staged GeoPackage, replacing it.

    USE THIS RATHER THAN gdf.to_file(...) WHENEVER THE GEOPACKAGE IS IN THIS GATE'S `WRITABLE`.
    `to_file` on a path that ALREADY EXISTS appends a new layer named after the file stem instead
    of overwriting the existing one, and `read_file` returns the FIRST layer -- so the mutation is
    written, reported, and completely invisible to the gate:

        layers after to_file over existing:  ['polities', 'polities_database']
        value re-read from dest:             the ORIGINAL, unmutated

    Measured on 2026-08-10 while adding the check-A2 case. The existing gpkg-mutating cases escape
    this only because their gates do not list the GeoPackage in WRITABLE, so stage() never creates
    it and their write lands on a fresh path. Any future case that stages it would silently pass --
    which is the one failure mode this harness exists to prevent, occurring inside the harness.
    """
    dest = os.path.join(root, "data/final/polities_database.gpkg")
    if os.path.exists(dest):
        os.unlink(dest)
    gdf.to_file(dest, driver="GPKG", layer="polities")


def mutate_unmapped_area_that_has_a_polity(root, gpd, make_valid, affinity):
    """List an area as having no polity family when its polity exists.

    THIS IS THE DEFECT THAT ACTUALLY HAPPENED, reproduced. Sixteen territories got
    polities in PRs 190, 201 and 210 and every one stayed on this list, so the FAOSTAT
    map -- generated from a registry that reads it -- never gained a row and all sixteen
    still resolved to ROW-1850-2025. A consuming session found it, not this repo.

    Mayotte is used because its polity is unambiguous and its area code appears in the
    published map, so both of the gate's signals fire on one edit.
    """
    import csv

    path = os.path.join(root, "pipelines/faostat-era-matching/state/registry_unmapped.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    rows.append({
        "area_code": "270", "source_label": "Mayotte", "iso3": "MYT",
        "note": "registry area with no polity family (non-country/aggregate)",
    })
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return "listed area 270 Mayotte as having no polity, while MYT-1800-2025 exists"


def mutate_data_receiving_polity_without_geometry(root, gpd, make_valid, affinity):
    """Strip the geometry from a polity that receives data, leaving the row in place.

    This is issue 155's defect exactly, and it is invisible to every other gate here by
    construction. `validate_polygons` check C fails a row that DECLARES a polygon and has
    none; this mutation leaves `polygon_status`/`polygon_source` untouched in the CSV, so C
    sees a declaration and — reading only the GeoPackage rows that HAVE geometry — simply
    stops considering it. The completeness harness meanwhile still counts its 195 layer-B
    rows as matched, because they are.

    TAS-1825-1900 is used deliberately: it is the largest of the bindings the PR that added
    this gate attached, so the mutation restores the precise state the gate was written to
    forbid rather than inventing a synthetic one.
    """
    g = gpd.read_file(GPKG)
    i = g.index[g.polity_code == "TAS-1825-1900"][0]
    g.loc[i, "geometry"] = None
    write_gpkg(g, root)
    return "dropped TAS-1825-1900's geometry while it still receives 195 layer-B rows"


def mutate_map_year_end_past_coverage(root, gpd, make_valid, affinity):
    """Raise a FAOSTAT map row's inclusive year_end past its polity's exclusive coverage.

    This is the convention collision of issue 131 as it appears IN DATA: end_year is
    exclusive here, the map's year_end is inclusive, so a consistent row has
    `end_year == year_end + 1`. A row at 0 claims a reporting year the polity does not
    cover, and a consumer joining on year containment either drops it or resolves it to
    an entity that had already dissolved.

    The row is chosen for having a CLOSED period -- an open-ended polity sits at the 2025
    ceiling, where year_end == end_year is the ceiling showing through rather than an
    overshoot, and 13 registry rows sat there harmlessly before match.R was fixed.
    """
    import csv

    db = os.path.join(root, "data/final/polities_database.csv")
    with open(db, encoding="utf-8") as fh:
        spans = {r["polity_code"]: r for r in csv.DictReader(fh)}
    path = os.path.join(root, "data/final/faostat_area_polity_map.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    hit = None
    for r in rows:
        p = spans.get(r.get("polity_code", ""))
        if not p:
            continue
        try:
            end_year, year_end = int(p["end_year"]), int(r["year_end"])
        except (TypeError, ValueError, KeyError):
            continue
        if end_year < 2025 and end_year - year_end == 1:      # currently consistent
            r["year_end"] = str(end_year)                      # now one past coverage
            hit = (r["area_code"], r["polity_code"])
            break
    assert hit, "no consistent closed-period row to push over"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return f"pushed area {hit[0]} -> {hit[1]}'s year_end one past the polity's coverage"


def mutate_map_handover_year_claimed_by_nobody(root, gpd, make_valid, affinity):
    """Clip an outgoing map row a year short, so the handover year has NO answer.

    The convention decided for issue 74 is that a transfer year belongs to the INCOMING
    polity, which makes an outgoing row consistent exactly when its inclusive `year_end`
    is its polity's exclusive `end_year - 1` and its successor starts the year after.

    Pulling year_end DOWN by one breaks that in the direction the other two arms are blind
    to. It is not an ambiguity -- one fewer polity claims the year, not one more -- and it
    is not `year_end past coverage`, which only looks at year_end too HIGH. The year simply
    stops resolving: FAOSTAT data for it lands on no polity at all.
    """
    import csv
    from collections import defaultdict

    path = os.path.join(root, "data/final/faostat_area_polity_map.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    by_area = defaultdict(list)
    for r in rows:
        by_area[r["area_code"]].append(r)
    hit = None
    for area, group in sorted(by_area.items()):
        if len(group) < 2:
            continue
        group.sort(key=lambda r: int(r["year_start"]))
        outgoing = group[0]
        year = int(outgoing["year_end"])
        outgoing["year_end"] = str(year - 1)
        hit = (area, outgoing["polity_code"], year)
        break
    assert hit, "no multi-row area to clip a handover in"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return (
        f"clipped area {hit[0]} -> {hit[1]} to end {hit[2] - 1}, leaving {hit[2]} claimed "
        f"by neither it nor its successor"
    )


def mutate_observed_area_backdated_before_the_reporting_era(root, gpd, make_valid, affinity):
    """Widen an OBSERVED FAOSTAT area's span back past 1961, which is issue 200's option (a).

    The map states the reporting era only, and FAOSTAT reports from 1961. Backdating a row that
    carries observed data makes the file assert which polity an area was in years the source never
    reported — the assertion the consumer was making for itself with 262 ISO3-prefix rows, arriving
    upstream instead and therefore no longer visible as a guess.

    The row is chosen for having a polity that ALREADY covered the earlier year, so the mutation
    trips arm A alone: a backdate past the polity's own `start_year` would also trip arm C, and a
    case that fires two arms cannot show which one is alive. `max(start_year, 1850)` is the same
    floor the legitimate `registry`/no-data rows use, so the mutated row is exactly what a widened
    observed span would look like.
    """
    import csv

    db = os.path.join(root, "data/final/polities_database.csv")
    with open(db, encoding="utf-8") as fh:
        spans = {r["polity_code"]: r for r in csv.DictReader(fh)}
    path = os.path.join(root, "data/final/faostat_area_polity_map.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    hit = None
    for r in rows:
        p = spans.get(r.get("polity_code", ""))
        if not p:
            continue
        try:
            obs = int(float(r["rows_observed"] or 0))
            start = int(float(p["start_year"]))
            year_start = int(float(r["year_start"]))
        except (TypeError, ValueError, KeyError):
            continue
        if obs > 0 and year_start == 1961 and start < 1961:
            r["year_start"] = str(max(start, 1850))
            hit = (r["area_code"], r["polity_code"], r["year_start"], obs)
            break
    assert hit, "no observed row starting at 1961 whose polity predates it"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return (
        f"backdated area {hit[0]} -> {hit[1]} to {hit[2]}, so {hit[3]} observed rows now claim a "
        f"territorial identity for years FAOSTAT does not report"
    )


def mutate_area_read_off_its_own_polygon(root, gpd, make_valid, affinity):
    """Rewrite a declared area to exactly what its own polygon measures, which is the
    tautology check A2 counts.

    THIS MUTATION MAKES CHECK A PASS, and that is the point. The row it targets is
    chosen for having a genuine divergence: overwriting the declared figure with the
    measured one silences check A's disagreement and raises A2's count in the same
    edit. A gate that only reported disagreements would score this as an improvement.

    THE DECLARED AREA IS READ FROM THE GEOPACKAGE, not the CSV -- validate_polygons
    takes `claimed` from `have`, which comes from the .gpkg attribute table. The first
    version of this case rewrote the CSV and the gate did not notice, which is worth
    knowing before writing another case against this gate.
    """
    g = gpd.read_file(GPKG)
    live = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
    live["km2"] = live.to_crs("ESRI:54034").geometry.area / 1e6
    hit = None
    for r in live.itertuples():
        dec = r.polygon_area_km2
        try:
            dec = float(dec)
        except (TypeError, ValueError):
            continue
        # km2 >= 1000 MATTERS. The rewrite rounds to a whole km2, and at small areas that
        # rounding alone exceeds A2's 0.1% band -- AIA-1800-2025 at 79.9 km2 rounds to 80, a
        # 0.125% gap, so the row never entered the band and this case silently PASSED when
        # nine new small territories shifted which row it picked first. At >=1000 km2 the
        # rounding error is at most 0.05%, half the band.
        if dec > 0 and r.km2 >= 1000 and abs(r.km2 / dec - 1) > 0.05:
            hit, newval = r.polity_code, round(r.km2)
            break
    assert hit, "no row over 1000 km2 with a >5% divergence to overwrite"
    # STRING, not int. The column's dtype is str, and newer pandas raises
    # "Invalid value '795' for dtype 'str'" on an int assignment while older pandas
    # silently accepts it -- so this passed locally and failed in CI.
    g.loc[g.polity_code == hit, "polygon_area_km2"] = str(newval)
    write_gpkg(g, root)
    return f"rewrote {hit}'s declared area to {newval:,}, exactly what its polygon measures"


def mutate_oversimplified_archipelago(root, gpd, make_valid, affinity):
    """Thin an archipelago's polygon at the build's own default tolerance, which is the
    defect issue 71 describes, reproduced exactly rather than modelled.

    `SimplifyPreserveTopology(0.01)` -- 0.01 degrees, about 1.1 km at the equator -- is
    what `build_database.py` applied unconditionally until the area budget landed on
    2026-08-10. On the Maldives, 791 atolls almost all smaller than that, it deleted 42% of
    the country: 299.68 km2 at source, 172.62 km2 shipped. The page could then declare the
    truth and fail check A on a correct polygon, or declare the rendering and understate
    the country by 42%.

    NO OTHER GATE HERE CAN SEE IT, and that is why the case exists. The loss is planar and
    internally consistent: the polygon stays valid, stays inside its neighbours, stays
    s2-loadable, keeps its binding and its feature year, and overlaps nothing new. Check A
    is the one gate that compares an area to anything, and it cannot fail here for two
    independent reasons -- MDV declares `estimate`, and check A fails only on `assigned`;
    and for the smaller members of the same class (VAT 0.53 km2, TKL 15.7, NRU 22, TUV 42)
    the --min-km2 200 filter exempts the row outright, which is every polity small enough
    for 1.1 km of thinning to matter, by construction. NOT ASSUMED: run against a freshly
    mutated copy, `validate_polygons.py` prints PASS and exits 0 on exactly this mutation.

    The mutation is milder than the original defect (shapely/GEOS `simplify` leaves 245
    km2 where GDAL's left 172) and is left that way deliberately: a case that only fires on
    the worst instance of a class proves less than one that fires on a mild one.
    """
    g = gpd.read_file(GPKG)
    target = "MDV-1800-2025"
    hit = g.polity_code == target
    assert hit.any(), f"{target} absent from the GeoPackage"
    g.loc[hit, "geometry"] = g.loc[hit, "geometry"].simplify(0.01, preserve_topology=True)
    write_gpkg(g, root)
    return (f"thinned {target}'s 791 atolls at the build's default 0.01 degrees, deleting "
            f"a fifth of the country while its source area stays on record")


def mutate_site_shows_withdrawn(root, gpd, make_valid, affinity):
    """Put a retired polity back into site/polities.geojson, which is how the site
    drew Argentina twice.

    THE DATABASE IS UNTOUCHED HERE, and that is the point. Both the CSV and the
    GeoPackage were correct the whole time this defect shipped -- the master carries
    geometry for dead rows on purpose -- and the defect was in what the site converter
    chose to keep. A reader checking either authoritative file would find nothing
    wrong, and `site/` was covered by exactly one workflow: the one that deploys it.
    """
    import json

    path = os.path.join(root, "site/polities.geojson")
    with open(path, encoding="utf-8") as fh:
        geo = json.load(fh)
    ghost = json.loads(json.dumps(geo["features"][0]))
    ghost["properties"]["polity_code"] = "ARG-1800-2025"
    ghost["properties"]["wiki_status"] = "superseded"
    geo["features"].append(ghost)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(geo, fh)
    return "added superseded ARG-1800-2025 back into site/polities.geojson"


def mutate_self_replacing_page(root, gpd, make_valid, affinity):
    """A page whose prose says it replaced ITS OWN code, so the retired predecessor
    it superseded is named nowhere.

    All seven reporting-bucket pages carried this at once. It is invisible to every
    other gate BY CONSTRUCTION: the chain gate's broken-link signal only asks whether
    a linked page exists, and a self-link always exists; the frontmatter is correct
    throughout. The claim lives in prose, which is where the REASON for a rename lives
    and which nothing else in this repo reads for meaning.
    """
    page = os.path.join(root, "wiki/polities/rafr-1850-2025.md")
    with open(page, encoding="utf-8") as fh:
        text = fh.read()
    assert "replacing `RAFR-1850-2021`" in text, "fixture page no longer names its predecessor"
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(text.replace("replacing `RAFR-1850-2021`", "replacing `RAFR-1850-2025`", 1))
    return "made rafr-1850-2025.md claim it replaced its own code"


def mutate_title_period_contradiction(root, gpd, make_valid, affinity):
    """Retitle a page so its heading claims a period its row does not cover.

    This is the defect issue #25 reports, in the one shape check 4 cannot see: a title
    can contradict the database while naming NO code at all, so the "asserted code does
    not exist" signal has nothing to catch. `blz-1800-2025` — a superseded 1800-2025
    umbrella — was headed "Belize (to 1886)", the name of the separate BLZ-1800-1886 row,
    and every code on the page resolved.

    France is used rather than one of the fixed pages so the case cannot pass by
    re-detecting a defect a later cleanup removes.
    """
    page = os.path.join(root, "wiki/polities/fra-1919-2025.md")
    with open(page, encoding="utf-8") as fh:
        text = fh.read()
    heading = next((ln for ln in text.split("\n") if ln.startswith("# ")), None)
    assert heading, "no h1 in the France page"
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(text.replace(heading, "# France (to 1940)", 1))
    return "headed fra-1919-2025.md 'France (to 1940)' on a 1919-2025 row"


def mutate_page_back_to_a_stub(root, gpd, make_valid, affinity):
    """Gut a documented, data-receiving page back to the CSV-derived stub it started as.

    This is the regression issue 19 describes rather than a hypothetical: 987 pages were
    generated programmatically from CSV metadata by one autonomous pass, and a page in that
    state is not neutral -- the verification pipeline reads pages as evidence, so an empty
    one makes an agent cite an earlier agent's hypothesis. The gate's whole job is that the
    accepted set of such pages can only shrink, and a gate that only reads a baseline file
    would pass this mutation without noticing.

    France is gutted rather than one of the pages already in the baseline, for the same
    reason the title case uses it: a case that re-detects a baselined defect would still
    pass once that page is documented, and would then be proving nothing. FRA-1919-2025
    receives 4,101 layer-B rows, so it is unambiguously in the gate's population.

    The frontmatter is KEPT. Truncating it too would break every other gate staged beside
    this one and, worse, would make this case pass for the wrong reason -- a page the CSV
    cannot be rebuilt from is a different defect, owned by build_database. What is removed
    is only the documentation: the prose and the `../sources/` citations.
    """
    page = os.path.join(root, "wiki/polities/fra-1919-2025.md")
    with open(page, encoding="utf-8") as fh:
        text = fh.read()
    end = text.find("---", 3)
    assert end > 0, "no closing frontmatter fence in the France page"
    front = text[: end + 3]
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(front + "\n\n# France (1919-2025)\n\n"
                 "Draft WHEP row for France, added to cover FAOSTAT reporting code FRA.\n")
    return "gutted fra-1919-2025.md back to a CSV-derived stub"


def mutate_succession_cycle(root, gpd, make_valid, affinity):
    """Make two rows whose spans OVERLAP name each other as successors, closing a cycle in
    the chronology.

    The overlap is the whole design of this case, not incidental. A cycle among
    NON-overlapping spans is necessarily caught by the same gate's impossible-order signal
    instead -- going round a loop has to run backwards in time somewhere -- so a cycle case
    built from consecutive periods would prove the wrong signal and read as success. Two rows
    that overlap can point at each other with neither edge running backwards, which is the
    only shape where cycle detection is the sole thing standing between the defect and a
    green run.

    That is not hypothetical: it is precisely what GRL-1800-2025 and ISL-1800-2025 did before
    2026-08-05, each naming the other as successor across identical 1800-2025 spans, to
    express a sovereignty relation the schema has no field for.
    """
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    live = [
        r for r in rows
        if (r.get("wiki_status") or "").strip() not in ("retired", "superseded")
    ]
    pair = None
    for a in live:
        for b in live:
            if a is b:
                continue
            # overlapping spans, so neither successor edge can trip the order signal
            if int(a["start_year"]) < int(b["end_year"]) and int(b["start_year"]) < int(a["end_year"]):
                pair = (a, b)
                break
        if pair:
            break
    assert pair is not None, "no overlapping live pair to build a cycle from"
    a, b = pair
    a["successor"] = b["polity_code"]
    b["successor"] = a["polity_code"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)
    return a["polity_code"]


def mutate_untyped_national(root, gpd, make_valid, affinity):
    """Retype the single `national` member of an overlapping ISO family, so the tie-break that
    was deciding the route stops discriminating and family ORDER decides instead.

    This is the exact shape of issue 44 in reverse. That issue was closed by typing
    MYS-1957-1963 `national`, which made 1961 determinate -- and a retype is therefore all it
    takes to undo it silently, with no error anywhere, because falling back to list position is
    a documented branch of pick_by_year rather than a failure. The route simply becomes whatever
    the CSV's row order happens to say.
    """
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = rows[0].keys()
    live = [r for r in rows
            if (r.get("wiki_status") or "").strip() not in ("retired", "superseded")]
    victim = None
    for a in live:
        if (a.get("polity_type") or "") != "national" or not a.get("iso3_code"):
            continue
        # needs a same-iso overlapping partner, or removing the type changes nothing observable
        for b in live:
            if b is a or b.get("iso3_code") != a["iso3_code"]:
                continue
            if int(a["start_year"]) < int(b["end_year"]) and int(b["start_year"]) < int(a["end_year"]):
                victim = a
                break
        if victim:
            break
    assert victim is not None, "no national row with an overlapping same-iso partner"
    victim["polity_type"] = "colonial"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)
    return victim["polity_code"]


def mutate_double_claimed_component(root, gpd, make_valid, affinity):
    """Add a GADM component to a second aggregate, so two aggregates claim the same
    territory. Its documented first catch was exactly this -- six territories claimed
    twice, with Palau and the Northern Marianas sitting in both Asia Other and Oceania
    Other (those two were removed from Asia Other on 2026-08-17, issue 48; four claims
    remain baselined) -- and it was HIDDEN because the rest-of-world union deduplicates, so the
    double claim never showed up as a duplicated row anywhere downstream. If this gate
    were inert those claims would return silently and double-count the territory."""
    path = os.path.join(root, "scripts/sources/reporting-areas/build.py")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    # The components live in a nested dict under a "components" key, not in a bare list
    # -- checked rather than guessed on the second attempt. Claim FRO, which belongs to
    # Europe Other, for Asia Other as well.
    marker = '"RASI-1850-2025": {'
    assert marker in text, "no RASI aggregate to extend"
    i = text.index(marker)
    j = text.index('"components": [', i) + len('"components": [')
    text = text[:j] + '"FRO", ' + text[j:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return "claimed FRO for RASI-1850-2025 as well as Europe Other"



def mutate_renamed_column(root, gpd, make_valid, affinity):
    """Rename `observed_rows` to `rows_observed` in the published alias map.

    Not an invented name: `rows_observed` is the REAL name of the same field in
    faostat_area_polity_map.csv, so this is exactly the transposition those two files
    invite. It is the right mutation for this gate because a renamed column is not an
    error at any read site -- csv.DictReader hands back None for a name that is not
    there, and None propagates into an empty result that reads as "nothing found".
    Four analyses in one session were wrong this way."""
    path = os.path.join(root, "data/final/label_alias_map.csv")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace("observed_rows", "rows_observed", 1))
    return "observed_rows"


def mutate_unrenamed_layer_b_column(root, gpd, make_valid, affinity):
    """Drop the layer-B rename from the R reader, leaving `polity_code` as the parquet spells it.

    Not an invented defect: this is exactly the state build.R was in until issue 95's option 4
    was finished. Layer B's column NAMED `polity_code` holds LOWERCASE ISO CODES -- 166 distinct
    values, 0 of them a real polity code -- so a frame that keeps the name invites
    `merge(..., on="polity_code")`, which returns an EMPTY frame and raises nothing. The
    mutation is a DELETION rather than a wrong value because that is how this defect appears:
    nobody writes the bad join, they simply omit the rename that makes it unwritable."""
    path = os.path.join(root, "pipelines/historical-production-harmonized/build.R")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    needle = 'layer_b <- dplyr::rename(layer_b, iso3_lower = "polity_code")'
    assert needle in text, "build.R no longer renames layer B's polity_code at the read"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace(needle, "layer_b <- layer_b", 1))
    return "build.R"


def mutate_retargeted_map_to_dead_polity(root, gpd, make_valid, affinity):
    """Retarget one published FAOSTAT mapping row to a RETIRED polity, as a re-span leaves it.

    Not an invented defect and not an invented code: `CAN-1886-1948` is a real row of this
    database, superseded by `CAN-1886-1949`, and it is one of the five codes that carried 799
    orphaned rows in issue 243 -- the matchers' outputs pointed at the old span for as long as
    they were not re-run. That is precisely how this defect arrives: nobody writes a wrong
    code, the code simply STOPS BEING THE RIGHT ONE when the database moves underneath a
    crosswalk that is not regenerated.

    A DEAD code rather than an absent one, deliberately, because dead is the harder half. An
    absent code at least fails a `code in database` test; a retired one exists, resolves, has
    a name and a polygon, and is only forbidden by policy -- and measured 2026-08-17, a row
    retargeted this way passes nine of the ten gates that read this file, because the one that
    joins on the code (`validate_map_area_year`) drops rows whose code is not live rather than
    complaining about them. The tenth, `crosscheck_matchers.py`, does catch it.
    """
    import csv as _csv

    path = os.path.join(root, "data/final/faostat_area_polity_map.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
        fields = list(rows[0].keys())
    hit = 0
    for r in rows:
        if r.get("polity_code", "").startswith("CAN-"):
            r["polity_code"] = "CAN-1886-1948"
            hit += 1
    assert hit, "no Canadian row in the published FAOSTAT map to retarget"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return (f"retargeted {hit} published FAOSTAT mapping row(s) from the live Canadian polity "
            f"to CAN-1886-1948, the span issue 243 retired, as an un-regenerated crosswalk does")


def mutate_order_dependent_binding(root, gpd, make_valid, affinity):
    """Set VNM-1887-1954's polygon_feature_year back to 1893, the value it shipped with.

    CShapes gwcode 815 has three steps containing 1893 and TWO of them start in 1893, so
    find_feature's tie-break cannot single one out and returns whichever the shapefile
    lists first -- a 379,848 km2 pre-Laos-transfer step, against the 326,024 recorded on
    the row. Not an invented mutation: it is the exact state of the repository before
    issue 99, and the third instance of this bug class after issues 45 and 92."""
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    head = rows[0]
    ci, cy = head.index("polity_code"), head.index("polygon_feature_year")
    for r in rows:
        if len(r) > cy and r[ci] == "VNM-1887-1954":
            r[cy] = "1893"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    return "set VNM-1887-1954's polygon_feature_year to 1893, which matches three steps"


def mutate_period_mismatched_binding(root, gpd, make_valid, affinity):
    """Put COG-1906-1912 back on its predecessor's CShapes step.

    The exact state of the repository before issue 124: polygon_feature_year 1900 on a row
    covering 1906-1911, selecting French Equatorial Africa's 2,234,540 km2 for a territory
    that should be 344,022 -- a 6.5x overstatement. Chosen over a synthetic mutation because
    it is what the data actually looked like, and because the row declares no
    polygon_area_km2, so no area check would object to it."""
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    head = rows[0]
    ci, cy = head.index("polity_code"), head.index("polygon_feature_year")
    for r in rows:
        if len(r) > cy and r[ci] == "COG-1906-1912":
            r[cy] = "1900"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    return "set COG-1906-1912's polygon_feature_year to its predecessor's, 1900"


def mutate_spherically_degenerate_ring(root, gpd, make_valid, affinity):
    """Give one polity a ring that is VALID in the plane and self-crossing on the sphere.

    The four vertices are the REAL ones from DEU-1871-1919's ring 3, the defect issue 515
    was filed for: a quad on CShapes Europe's 0.02-degree grid whose edges 0 and 2 pass
    3.576e-15 degrees -- 4e-10 m, about one ULP -- apart. GEOS reads that as no
    intersection and calls the ring valid; s2 rounds each lon/lat onto a unit vector
    first, and after the rounding the edges cross.

    Synthetic alternatives were tried first and DO NOT WORK, which is why the real
    coordinates are used: a deliberately thin high-latitude sliver spanning 40 degrees of
    longitude is accepted by s2 at every latitude from 0 to 80. The failure is not about
    geodesic sag, so a mutation built on that theory would have passed the gate and read
    as "this gate cannot fail".

    It is also the one mutation in this file that NO OTHER GATE HERE COULD CATCH, since
    every other geometry check reasons in the plane and this geometry is planar-valid.
    """
    from shapely.geometry import MultiPolygon, Polygon

    g = gpd.read_file(GPKG)
    victim = "SWE-1800-1809"
    idx = g.index[g.polity_code == victim]
    assert len(idx) == 1, f"expected one {victim} row, found {len(idx)}"
    ring = Polygon([(10.9, 53.96), (10.86, 53.92), (10.82, 53.9), (10.9, 53.94)])
    assert ring.is_valid, "the injected ring must be GEOS-valid or it proves nothing"
    g.loc[idx[0], "geometry"] = MultiPolygon([ring])
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return (
        f"replaced {victim}'s geometry with a GEOS-valid ring whose edges 0 and 2 are "
        f"4e-10 m apart, which s2 reads as a self-crossing"
    )
def mutate_shared_polygon(root, gpd, make_valid, affinity):
    """Bind STP-1800-2025 back to CShapes 2.0 feature 411, which is Equatorial Guinea.

    Not a synthetic mutation: it is the exact state the row shipped in, and still the
    state of WHEP's embedded copy at 603 rows. Sao Tome and Principe is two islands
    250 km offshore; feature 411 is mainland Rio Muni plus Bioko. Both rows were
    therefore handed one polygon, and cell (10.25, 1.75) claimed 2.0000x its own area
    (whep#514).

    `polygon_area_km2` is blanked as well, and that is the load-bearing part. With an
    area recorded, validate_polygons check A compares 1,002 km2 against ~28,000 and
    catches it; without one it cannot compare at all, which is the 76% blind spot that
    gate's own docstring names. The defect shipped in the blind spot, so the mutation
    has to as well.

    The GeoPackage is written FRESH into `root` rather than into a staged copy. A copy
    would already contain a layer named `polities`, and `to_file` without an explicit
    layer writes one named after the FILE -- so the gate would read layer 0, see
    unmutated data, pass, and this harness would report a working gate as one that
    cannot fail. Cost half an hour to find; recorded so the next geometry case does not
    repeat it.
    """
    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    head = rows[0]
    idx = {name: head.index(name) for name in (
        "polity_code", "polygon_source", "polygon_feature_id",
        "polygon_feature_year", "polygon_status", "polygon_area_km2")}
    hit = 0
    for r in rows:
        if len(r) > max(idx.values()) and r[idx["polity_code"]] == "STP-1800-2025":
            r[idx["polygon_source"]] = "cshapes-2.0"
            r[idx["polygon_feature_id"]] = "411"
            r[idx["polygon_feature_year"]] = "1900"
            r[idx["polygon_status"]] = "assigned"
            r[idx["polygon_area_km2"]] = ""
            hit += 1
    assert hit == 1, f"expected one STP-1800-2025 row, found {hit}"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)

    g = gpd.read_file(GPKG)
    src = g.loc[g.polity_code == "GNQ-1968-2025", "geometry"].iloc[0]
    i = g.index[g.polity_code == "STP-1800-2025"][0]
    g.loc[i, "geometry"] = src
    g.to_file(os.path.join(root, "data/final/polities_database.gpkg"), driver="GPKG")
    return "gave STP-1800-2025 Equatorial Guinea's CShapes feature 411 and blanked its area"


def mutate_undocumented_source_change(root, gpd, make_valid, affinity):
    """Rebind one period of a family to a different polygon source across a large area step.

    The gate's claim is that a source change AND a big ratio together must be accounted for,
    so the injected defect is exactly that: `ISR-1948-1967` -> `ISR-1967-1979` already steps
    4.27x (20,786 -> 88,667 km2) with BOTH rows on cshapes-2.0, which the gate ignores because
    no source changes. Declaring the later row as GADM-sourced makes the same step qualify,
    with nothing in the baseline saying why.

    ONLY THE DECLARED SOURCE IS CHANGED, not the geometry -- which is the point rather than a
    shortcut. This gate reads `polygon_source` from the CSV and the areas from the GeoPackage,
    so a label-only edit is precisely the operation that turns an unexamined step into a
    published convention difference, and it is how the TUN defect was written in the first
    place: the frontmatter named one source while the page's prose described another.

    The Six-Day War is real history, so a maintainer facing this failure would answer it with
    an `EVENT:` baseline entry rather than a repair. That is the correct behaviour and does not
    weaken the case: what is being tested is that the step cannot pass UNANSWERED.
    """
    import csv

    path = os.path.join(root, "data/final/polities_database.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    hit = 0
    for r in rows:
        if r["polity_code"] == "ISR-1967-1979":
            assert r["polygon_source"] == "cshapes-2.0", (
                f"ISR-1967-1979 no longer reads cshapes-2.0 but {r['polygon_source']!r}; "
                f"pick another same-source pair with a >=1.3x step"
            )
            r["polygon_source"] = "gadm-4.1-adm0"
            hit += 1
    assert hit == 1, f"expected one ISR-1967-1979 row, found {hit}"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return "declared ISR-1967-1979 as GADM-sourced, so the 4.27x step at 1967 now crosses a source change"
def mutate_inclusive_end_year(root, gpd, make_valid, affinity):
    """Put matchlib back to reading `end_year` INCLUSIVELY, which is issue #131.

    Not a synthetic mutation either: it is the state the matcher shipped in until
    that issue. `pick_by_year` tested `start <= year <= end`, so at a transition
    year the ENDED period was a candidate and, in any family with a third
    overlapping row, it won on list position. The empty `expired` list restores
    exactly that — the candidate gather is already inclusive, and the narrowing
    step is what makes the declared convention real.

    What makes this case worth having is that NOTHING ELSE CATCHES IT. The
    mutation raises no exception, changes no schema, moves no polygon and leaves
    every count identical; both readings return a real, live, plausibly-dated
    polity, so the only observable difference is WHICH one.

    "NOTHING ELSE CATCHES IT" was measured when crosscheck_matchers compared the
    two matchers at each area's MIDPOINT year alone and therefore never asked
    about a boundary. Since issue 16 that gate probes each mapping's FIRST and
    LAST year too, and it does now catch this mutation: 52 disagreements against
    the 9 baselined, plus 5 fixture failures. This case is kept anyway, aimed at
    validate_year_semantics, because that gate names the convention itself while
    crosscheck reports the symptom -- and the second reading of a defect is worth
    having when the first is a baselined comparison that a future entry could
    absorb.
    """
    path = os.path.join(root, "pipelines/polity-autoimprove/matchlib.py")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    target = "expired = [r for r in cands if not covers(r[3], r[4], year) and r[3] != year]"
    assert target in text, "matchlib.pick_by_year no longer narrows by expiry"
    text = text.replace(target, "expired = []")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return (
        "made matchlib.pick_by_year read end_year inclusively again, so a period "
        "that has ended still competes for its own boundary year"
    )


def mutate_inclusive_alias_end_year(root, gpd, make_valid, affinity):
    """Put matchlib's ALIAS path back to reading the target's `end_year` inclusively.

    The other half of issue #131, and the half that survived the first fix.
    `assign()` tested `rec[3] <= year <= rec[4]` — the INCLUSIVE reading of the
    exclusive field — for EVERY alias, including blanket ones that carry no year
    bound at all. Where an alias writes `year_end` down, honouring it is a
    deliberate deference to a human decision; where it does not, there is no
    decision and the exclusive convention simply leaks in through the alias path.

    Measured on the registry: 219 of 903 rules can reach their target's
    `end_year`; 200 declare it and 19 do not. This mutation restores the state in
    which all 219 were honoured alike.

    Like the polity-side case, nothing else catches it: the mutation raises no
    exception, moves no polygon, changes no count, and returns a real live polity
    — just the one that ended that year instead of the one that started it.
    """
    path = os.path.join(root, "pipelines/polity-autoimprove/matchlib.py")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    target = (
        "                    and (covers(rec[3], rec[4], year)\n"
        "                         or (ALIAS_YEAR_END_INCLUSIVE\n"
        "                             and year == rec[4] and alias_rule[\"y1\"] == year)):"
    )
    assert target in text, "matchlib.assign no longer guards the alias boundary year"
    text = text.replace(target, "                    and rec[3] <= year <= rec[4]:")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return (
        "made matchlib.assign honour every alias at its target's end_year, "
        "including blanket aliases that never claimed that year"
    )


def mutate_mislabelled_landuse_shift(root, gpd, make_valid, affinity):
    """Relabel Brazil 1947's land-use repair as a x100 decimal shift.

    THIS IS THE STATE THE TABLE SHIPPED IN until 2026-08-14, not an invented edit.
    `06_landuse_consistency.py` tested `recorded / implied` against 100 with a 2%
    window, and 1,918,835 / 18,835 = 101.9 fell inside it — so the row asserted a
    decimal shift while 18,835 x 100 is 1,883,500, a different number from the one
    recorded. The actual fault was two prepended digits.

    It is the right mutation for this gate because nothing else in the repository
    reads this file: the numbers stay exactly as they are, only the stated reason
    changes, so no count moves, no schema breaks, and a consumer that trusts the
    label divides by 100 and lands on 19,188.35 hectares of Brazilian arable land.
    """
    path = os.path.join(root, "pipelines/polity-autoimprove/state/landuse_corrections.csv")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    target = "1918835.0,18835.0,replace_value,digits prepended"
    assert target in text, "the Brazil 1947 arable repair row is no longer in the table"
    text = text.replace(target, "1918835.0,18835.0,replace_value,decimal point dropped (x100)")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return ("relabelled BRA-1909-2025 1947 arable as a x100 decimal shift, the label the "
            "generator's 2% ratio window really did emit")


def mutate_yield_run_as_clean_power_of_ten(root, gpd, make_valid, affinity):
    """Assert that iia congo green coffee 1922-1934 is off by a clean power of ten.

    THIS IS THE STATE THE TABLE SHIPPED IN until 2026-08-17, not an invented edit.
    `07_yield_consistency.py` wrote `implied_factor_pow10` — the NEAREST power of ten —
    and nothing that said whether the factor is actually one, so this run read as x10
    while the factor that restores the item's reference yield is x26.1. Repairing the
    run by 10 leaves its production 2.6x low, and this is precisely the kind of run
    (114 t recorded against a 1,800 t clean-year level) that gets batch-fixed by
    powers of ten. Issue #111's own headline, "off by a constant power of ten", holds
    for only 14 of the 28 runs naming a column.

    It is the right mutation for this gate because nothing else in the repository reads
    this file: every number stays exactly as it is and only the claim about them changes,
    so no count moves and no schema breaks — the sole thing that can catch it is a gate
    that re-derives the claim from the factor in the same row.
    """
    path = os.path.join(
        root, "pipelines/polity-autoimprove/state/yield_series_corrections.csv"
    )
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    target = "26.1,1,False"
    assert target in text, "the iia congo green-coffee run no longer carries factor 26.1"
    text = text.replace(target, "26.1,1,True")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return ("claimed the iia congo coffee, green 1922-1934 run is off by a clean x10 when "
            "its own factor is x26.1, the unconditional pow10 claim the table really made")

def mutate_subnational_aggregate_with_residual(root, gpd, make_valid, affinity):
    """Append the Germany 1937 agricultural-population block as an exact aggregate claim.

    THIS IS THE STATE THE TABLE HAD while 12_subnational_sums.py was being written, not an
    invented edit. The generator's first tolerance was `max(0.5, 0.005 * whole)` — a
    PERCENTAGE window, copied from 10_livestock_consistency.py, where the tables run to five
    figures and it is the right instrument. Here it is not: four keys passed as "the parts sum
    to the stated whole" whose parts are 6, 12, 18 and 31 units short of it, because the
    Berlin row is absent for those population sub-items and Indochina's 1937 parts genuinely
    do not add up. This case restores the largest of the four.

    It is the right mutation for this gate because nothing else in the repository reads this
    file, so no count moves and no schema breaks: the row is arithmetically self-consistent
    (7,098 - 7,116 = -18, exactly what `residual` says) and only its CLAIM is false. A
    consumer acting on `mark_aggregate` drops the whole row as a duplicate of its parts and
    silently loses Berlin's 18,000 agricultural inhabitants — and the only thing that can
    catch it is a gate that asks whether a row calling itself an aggregate has a residual.
    """
    path = os.path.join(root, "pipelines/polity-autoimprove/state/subnational_sums.csv")
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(
            "fao1952,r_fao_population_1952_10_18.xlsx,Germany,"
            "Germany Eastern; Germany Western,2,r_fao_population_1952_10_18,"
            "population:population agricultural ocupati,1000 people,1937,,"
            "7116.0,7098.0,-18.0,mark_aggregate,,"
            "\"parts sum to the stated whole (7,116.0), so this whole row is an aggregate "
            "of its 2 part row(s) and is_aggregate is False on it\"\n"
        )
    return ("asserted Germany's 1937 agricultural population is the exact sum of its "
            "Eastern and Western zones while the two are 18 (1000 people) short of it, the "
            "claim a 0.5% tolerance really made")


def mutate_short_convention_row(root, gpd, make_valid, affinity):
    """Append a convention row carrying only the FIRST SEVEN columns.

    NOT INVENTED: this is exactly what `apply_verdicts.py` did until issue 24. Its
    `append_dedup` call listed seven fields while the registry has twelve, so every
    convention a verdict taught the pipeline landed as a short row. Read back,
    `flow_type` is empty — and `write_source_flow_flags.py` reads an empty flow_type as
    `production`, so a verdict recording a TRANSIT flow would have published no flag at
    all: the double count that gate exists to expose, arriving through the writer that
    feeds it.

    The mutation is deliberately a plausible NEW entry rather than a corruption of an
    existing one, because that is the shape the defect really has — nothing looks wrong
    until a consumer asks the row a question about a column it never wrote.
    """
    path = os.path.join(
        root, "pipelines/polity-autoimprove/state/source_conventions.csv"
    )
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(
            "iia,brazil,\"coffee, green\",\"IIA figures under 'brazil' for coffee green "
            "are Santos port shipments, not national output\",\"Placeholder evidence long "
            "enough to pass the minimum-length arm of the gate, so the case can only fire "
            "on the missing columns and not on a short evidence string.\","
            "2026-08-17,assertion-verification (synthetic)\n"
        )
    return (
        "appended a convention row with 7 of the registry's 12 columns, the shape "
        "apply_verdicts.py wrote before issue 24 — its flow_type reads back empty, so a "
        "transit flow would publish as production"
    )


def mutate_dead_convention_pattern(root, gpd, make_valid, affinity):
    """Re-point a live convention's `label_pattern` at a label the source never carries.

    This is the silent failure the registry is most exposed to, and it needs no bad faith
    to happen: labels get renamed, re-spanned and re-normalised, and `00_intake.py`
    attaches a convention by NORMALISED SUBSTRING of the label. Miss, and the entry still
    sits in the file, still reads as verified, and reaches no bundle — every verifier
    touching that source goes back to re-deriving what was already settled, or worse,
    routes whole-USSR figures to Russia proper because the note that says not to never
    arrived.

    Nothing else can see it. The file parses, the flow flags regenerate byte-identically
    (the mutated row is a `production` row, so it is not published at all), and the
    pipeline that would notice cannot run in CI.
    """
    import csv as _csv

    path = os.path.join(
        root, "pipelines/polity-autoimprove/state/source_conventions.csv"
    )
    with open(path, encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
        fields = list(rows[0].keys())
    hit = 0
    for r in rows:
        if r["source"] == "iia" and r["label_pattern"] == "russian federation":
            r["label_pattern"] = "soviet union"      # a label the IIA does not use
            hit += 1
    assert hit == 1, f"expected one iia/russian federation convention, found {hit}"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return (
        "re-pointed the whole-USSR convention from `russian federation` to `soviet "
        "union`, a label iia never writes, so it attaches to no bundle while still "
        "reading as verified"
    )


def mutate_trace_flow_into_mirror_gaps(root, gpd, make_valid, affinity):
    """Put one trace-quantity flow back into the trade-mirror gap table.

    THIS IS THE SCREEN ISSUE #112 PROPOSED, not an invented edit: "filtered to >=1000x
    (40k)". Measured on the pin, 26,915 of the 39,690 flows above 1000x — 67.8% — have
    their smaller side under one tonne, median 0.1 t against a median 532 t on the other
    side, so the ratio screen alone selects mostly reporting-threshold artefacts in which
    neither figure need be wrong. This mutation shrinks one side of a real disagreement to
    0.02 t, the 25th percentile of that trace population, and leaves everything else
    consistent: the ratio column, `larger_side`, `nearest_pow10` and the row count all
    still agree with each other, so the row reads as an ordinary member of the table.

    Nothing else in the repository reads this file, and the mutated row is still a 1000x+
    ratio between two positive tonnages — which is precisely why only a gate that re-tests
    the ABSOLUTE half of the screen can see it. Admitting the class it belongs to takes the
    investigable set from 12,775 to 39,690 and turns a 0.2% tail into a 0.65% one.
    """
    path = os.path.join(root, "pipelines/polity-autoimprove/state/trade_mirror_gaps.csv")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines(keepends=True)
    target = None
    for i, line in enumerate(lines):
        if ",Ice and snow,1993,1.0," in line:
            target = i
            break
    assert target is not None, (
        "the Switzerland/France 1993 'Ice and snow' flow is no longer the table's exp_t=1.0 "
        "row; pick another row whose smaller side is the exporter's"
    )
    old = lines[target]
    new = old.replace(",Ice and snow,1993,1.0,", ",Ice and snow,1993,0.02,")
    assert new != old, "the exp_t field was not rewritten"
    # The ratio has to move with it, or the gate catches the arithmetic instead of the screen
    # and the case proves the wrong thing.
    fields = new.rstrip("\r\n").split(",")
    hi, lo = max(float(fields[7]), float(fields[8])), min(float(fields[7]), float(fields[8]))
    fields[9] = f"{round(hi / lo, 3)}"
    fields[12] = str(int(round(math.log10(hi / lo))))
    lines[target] = ",".join(fields) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    return ("shrank the exporter's side of the Switzerland->France 1993 'Ice and snow' flow "
            "to 0.02 t, so the row is trace reporting rather than a disagreement — the "
            "class that is 67.8% of what issue 112's ratio-only screen selected")


def mutate_entrepot_flag_dropped(root, gpd, make_valid, affinity):
    """Demote the one recorded entrepôt flow back to `production` in state, and leave the
    published file as it was.

    This is the pre-issue-14 world exactly: the IIA's green coffee under `djibouti` sits in
    the data as if French Somaliland grew 14,114 t/yr of it, and every production aggregate
    sums it beside Ethiopia's own crop. Nothing else in this repository can see it — the
    alias is right, the polity is right, the polygon is right, the row counts are unchanged.
    The ONLY thing that distinguishes a transit volume from an output is this flag, so the
    mutation removes it in the direction that matters: a flag DISAPPEARING is a double count
    coming back, which is why the check reports removals by name rather than just "stale".

    Direction matters for a second reason: the writer regenerates on demand, so if the case
    mutated the published file instead, a reader could dismiss it as "just rerun the
    writer". Mutating STATE makes the published file the thing that is wrong.
    """
    import csv as _csv

    path = os.path.join(
        root, "pipelines/polity-autoimprove/state/source_conventions.csv"
    )
    with open(path, encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
        fields = list(rows[0].keys())
    hit = 0
    for r in rows:
        if r.get("flow_type") and r["flow_type"] != "production":
            r["flow_type"] = "production"
            r["origin_iso3"] = ""
            hit += 1
    assert hit, "no non-production flow left in source_conventions.csv to demote"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return (
        f"demoted {hit} recorded non-production flow(s) to `production` in state without "
        f"republishing, so the published flags claim an exclusion state no longer recorded"
    )


def mutate_member_bound_to_a_siblings_polygon(root, gpd, make_valid, affinity):
    """Give one AEF constituent a SIBLING constituent's polygon, so the four parts no
    longer sum to the federation they compose.

    This is the defect class `composed_union` recipes keep producing here, reproduced in the
    one place a sum can see it. IDN-JVM-1949-1951 declared four GADM ids of which one was
    North Sulawesi, 1,500 km away, while three Java provinces were missing; SER-1918-1945 and
    CAN-1800-1866 had the same shape. Every per-row gate passed on all three: the geometry is
    valid, s2-loadable, inside its continent, the right SIZE ORDER for its family, and its
    row declares a polygon and has one. What contradicted them was the OTHER number the page
    carried -- the total -- which only a sum against the enumerated members can use.

    Chad is swapped in for Middle Congo rather than something absurd because it must stay
    inside AEF: that keeps containment (check B) quiet and leaves the sum as the only signal,
    which is the point of the case. 343,962 km2 becomes 1,271,822, so the four parts reach
    1.372x the federation polygon.
    """
    g = gpd.read_file(GPKG)
    i = g.index[g.polity_code == "COG-1919-1960"][0]
    tcd = g[g.polity_code == "TCD-1919-1960"].iloc[0].geometry
    g.loc[i, "geometry"] = make_valid(tcd)
    write_gpkg(g, root)
    return (
        "bound COG-1919-1960 to TCD-1919-1960's polygon, so AEF's four constituents sum to "
        "1.372x the federation while every one of them stays inside it"
    )


def mutate_dead_status_exclusion_dropped(root, gpd, make_valid, affinity):
    """Empty matchlib's DEAD_STATUS, so retired and superseded polities compete for data.

    THIS CASE EXISTS BECAUSE THE FILE ABOVE SAID IT COULD NOT. The prose recorded
    crosscheck_matchers as honestly uncovered, on the reasoning that both matchers read
    the same alias registry so mutating the registry moves both identically. That
    reasoning is sound and still is; what it missed is that the gate does not only
    compare the two matchers against each other. Since issue 16 it also pins a golden
    FIXTURE of routing decisions to expected polity codes, and a fixture has no second
    party to move in step with it.

    The mutation is one token — `DEAD_STATUS = ()` — and it is the state matchlib shipped
    in before the exclusion was added. Its effect is not subtle and is not local:
    ARG-1800-2025 (retired) and BRA-1800-2025 (superseded) each span 1800-2025 as
    `national`, so restored to their families they outrank every live successor at every
    year. Measured on the 874-probe FAOSTAT set the mutation raises disagreements from
    the 9 baselined to 49 -- 40 new, across 10 areas (7, 9, 21, 23, 33, 72, 84, 101, 103,
    248) -- and breaks 2 of the 19 fixture cases: 'Argentina' 1900 answers ARG-1800-2025,
    the retired row, and 'Hungary' 1938 answers HUN-1920-1938 because a dead row rejoining
    the HUN family changes which candidate the tie-break reaches.

    The R side is why this invariant needs a guard at all. faostat-era-matching/match.R
    and matchlib both filtered dead rows; pre1961-matching/match.R did not, and routed
    15,526 of 124,508 rows onto 24 dead polities before issue 16.
    """
    path = os.path.join(root, "pipelines/polity-autoimprove/matchlib.py")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    target = '    DEAD_STATUS = ("retired", "superseded")'
    assert target in text, "matchlib no longer declares DEAD_STATUS"
    text = text.replace(target, "    DEAD_STATUS = ()")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return (
        "emptied matchlib.Matcher.DEAD_STATUS, so retired and superseded polities are "
        "matchable again and their all-years `national` rows outrank live successors"
    )


CASES = (
    (
        "validate_composition_sums.py",
        mutate_member_bound_to_a_siblings_polygon,
        "AEF-1910-1960",
        "a member bound to a sibling's polygon, which no per-row check can see because "
        "every property of the geometry is fine — only the parts-sum-to-the-whole identity "
        "contradicts it",
    ),
    (
        "validate_source_change_steps.py",
        mutate_undocumented_source_change,
        "ISR-1948-1967 -> ISR-1967-1979",
        "an area step at a boundary where the polygon SOURCE also changes and nothing says "
        "which of the two produced it — the shape of the 3.55x Tunisia artefact",
    ),
    (
        "validate_polygon_period_fit.py",
        mutate_period_mismatched_binding,
        "COG-1906-1912",
        "a polygon bound to a step from outside the period its row covers",
    ),
    (
        "validate_schema_contract.py",
        mutate_renamed_column,
        "observed_rows",
        "a renamed column, which every reader sees as None rather than as an error",
    ),
    (
        "validate_layer_b_column_guard.py",
        mutate_unrenamed_layer_b_column,
        "build.R",
        "a layer-B read that keeps the column named `polity_code`, which holds lowercase ISO "
        "codes, so the obvious join returns zero rows and no error",
    ),
    (
        "validate_matcher_orphan_guard.py",
        mutate_retargeted_map_to_dead_polity,
        "CAN-1886-1948",
        "a matcher crosswalk still pointing at the polity code a re-span retired, which every "
        "consumer resolves by lookup and therefore routes NOWHERE without raising",
    ),
    (
        "validate_polygon_binding_determinism.py",
        mutate_order_dependent_binding,
        "VNM-1887-1954",
        "a polygon binding whose feature is chosen by shapefile row order",
    ),
    (
        "audit_family_shadowing.py",
        mutate_pinned_disjoint_overlap,
        "IDN-OTH-1949-1951",
        "two live rows claiming the same ground, the defect eduaguilera/whep#514 reports",
    ),
    (
        "audit_family_shadowing.py",
        mutate_shadowing_twin,
        "FRA-1820-1860",
        "family ordering, not polity_type, would decide which polity a label matches",
    ),
    (
        "validate_spatial_containment.py",
        mutate_disjoint_successor,
        "FRA-1871-1919",
        "a polygon bound to the wrong feature, detectable only by position",
    ),
    (
        "validate_family_areas.py",
        mutate_shrunk_successor,
        "FRA-1871-1919",
        "a polygon bound to a smaller feature inside the right territory",
    ),
    (
        "validate_spherical_edges.py",
        mutate_collapsed_planar_border,
        "USA-1959-2025",
        "a straight treaty border stored sparsely, which a spherical consumer "
        "renders 92 km off line while every conservation check still passes",
    ),
    (
        "validate_references.py",
        mutate_title_period_contradiction,
        "fra-1919-2025",
        "a page heading claiming a period its row does not cover, which contradicts "
        "the database while naming no code at all",
    ),
    (
        "validate_code_year_agreement.py",
        mutate_code_year_disagreement,
        "FRA-1800-1871",
        "a code whose embedded years contradict its own columns",
    ),
    (
        "validate_alias_year_coverage.py",
        mutate_alias_past_the_ceiling,
        "Andorra",
        "an alias claiming a year past its target's span, in the one place the gate's "
        "open-ended exclusion could have hidden it",
    ),
    (
        "validate_alias_chain_overlaps.py",
        mutate_touching_alias_chain,
        "kenya",
        "consecutive aliases for one label both covering a year",
    ),
    (
        "validate_live_name_ambiguity.py",
        mutate_name_collision,
        "norway",
        "two live polities sharing a name and a year, so the name resolves to neither",
    ),
    (
        "validate_dissolved_iso_codes.py",
        mutate_dissolved_iso_blanked,
        "F248-1947-1991",
        "a dissolved state left with no iso3_code, so it belongs to no ISO family and a "
        "consumer holding its 3166-3 code reaches nothing",
    ),
    (
        "validate_local_iso_codes.py",
        mutate_new_iso_code,
        "ZZQ",
        "an unreviewed iso3_code value, which changes what an ISO-keyed join matches",
    ),
    (
        "validate_page_depth.py",
        mutate_page_back_to_a_stub,
        "FRA-1919-2025",
        "a data-receiving polity documented only by a CSV-derived stub, which the "
        "verification pipeline would then read as evidence",
    ),
    (
        "validate_aliases.py",
        mutate_alias_to_dead_polity,
        "AGO-1816-2025",
        "an alias routing data to a polity that must never receive it",
    ),
    (
        "write_manifest.py",
        mutate_polity_without_regenerating_manifest,
        "stale",
        "a published contract that no longer matches the database it describes",
    ),
    (
        "write_source_flow_flags.py",
        mutate_entrepot_flag_dropped,
        "iia|djibouti|coffee, green",
        "an entrepôt series silently readmitted as production, which double-counts "
        "Ethiopia's coffee and is invisible to every other check",
    ),
    (
        "build_database.py",
        mutate_wiki_without_rebuilding,
        "FRA-1919-2025",
        "a wiki edit that never reached the database derived from it",
    ),
    (
        "validate_reporting_areas.py",
        mutate_double_claimed_component,
        "FRO",
        "one territory claimed by two aggregates, which double-counts it",
    ),
    (
        "validate_order_decided_families.py",
        mutate_untyped_national,
        "ORDER DECIDES",
        "an overlapping ISO family losing its only `national` member, so list position "
        "silently becomes the route",
    ),
    (
        "validate_registry_unmapped.py",
        mutate_unmapped_area_that_has_a_polity,
        "area 270",
        "an area listed as having no polity while its polity exists, so its data keeps resolving to ROW",
    ),
    (
        "validate_map_area_year.py",
        mutate_map_year_end_past_coverage,
        "year_end past coverage",
        "a map row claiming a reporting year its polity does not cover, which the exclusive/inclusive collision makes easy to write",
    ),
    (
        "validate_map_area_year.py",
        mutate_map_handover_year_claimed_by_nobody,
        "handover",
        "a handover year claimed by NEITHER polity, the direction the ambiguity and "
        "past-coverage arms are both blind to — one answer too few looks like nothing at all",
    ),
    (
        "validate_map_era_scope.py",
        mutate_observed_area_backdated_before_the_reporting_era,
        "before the reporting era",
        "an observed area backdated past 1961, so the map asserts a polity for years FAOSTAT "
        "never reported — the guess the consumer was making with ISO3 prefixes, moved upstream "
        "where it stops looking like a guess",
    ),
    (
        "validate_polygons.py",
        mutate_area_read_off_its_own_polygon,
        "self-referential",
        "a declared area overwritten with its own polygon's measurement, which silences check A",
    ),
    (
        "validate_simplification_loss.py",
        mutate_oversimplified_archipelago,
        "MDV-1800-2025",
        "an archipelago thinned by the build's own simplification pass, which makes "
        "`polygon_area_km2` unfillable and which check A skips by construction",
    ),
    (
        "validate_site_outputs.py",
        mutate_site_shows_withdrawn,
        "ARG-1800-2025",
        "a withdrawn polity drawn on the published map, over the rows that replaced it",
    ),
    (
        "validate_chain_integrity.py",
        mutate_self_replacing_page,
        "rafr-1850-2025.md",
        "a page documenting a rename by naming itself, leaving the retired code documented nowhere",
    ),
    (
        "validate_chain_integrity.py",
        mutate_succession_cycle,
        "CYCLE",
        "a chronology that loops, between two rows whose spans overlap so that the "
        "impossible-order signal provably cannot fire instead",
    ),
    (
        "validate_s2_polygons.py",
        mutate_spherically_degenerate_ring,
        "SWE-1800-1809",
        "a polygon GEOS calls valid that s2 cannot load, so every geodesic area and "
        "every grid intersection over it aborts",
    ),
    (
        "validate_period_overlaps.py",
        mutate_cross_family_overlap,
        "MAR-1911-1958",
        "two families the database says hold one territory both claiming the same "
        "years, which no same-prefix comparison can see",
    ),
    (
        "validate_shared_polygons.py",
        mutate_shared_polygon,
        "STP-1800-2025",
        "two coexisting live polities on one polygon, which claims the ground twice",
    ),
    (
        "validate_year_semantics.py",
        mutate_inclusive_end_year,
        "USA-1848-1867",
        "a matcher reading end_year the opposite way from the database, which returns "
        "an ended polity for its own boundary year and errors on nothing",
    ),
    (
        "validate_year_semantics.py",
        mutate_inclusive_alias_end_year,
        "COD-1910-1960",
        "the SAME misreading arriving through the alias path, where a blanket alias "
        "that claims no year at all is still honoured at its target's end_year",
    ),
    # APPENDED, not inserted: the prose above refers to cases by NUMBER ("case 6 guards the
    # invariant that a retired polity never receives data"), so putting a new case anywhere
    # but the end silently renumbers those references.
    (
        "validate_data_without_geometry.py",
        mutate_data_receiving_polity_without_geometry,
        "TAS-1825-1900",
        "a polity that receives data and carries no territory, so every area-weighted "
        "consumer drops its rows silently",
    ),
    (
        "validate_landuse_corrections.py",
        mutate_mislabelled_landuse_shift,
        "BRA-1909-2025",
        "a repair row whose stated reason contradicts its own numbers, so a consumer "
        "applying the label lands on a different value from the one in the table",
    ),
    (
        "validate_yield_corrections.py",
        mutate_yield_run_as_clean_power_of_ten,
        "iia congo coffee, green 1922-1934",
        "a defective series claiming a clean power-of-ten offset its own repair factor "
        "contradicts, so a batch decimal fix leaves the run 2.6x out",
    ),
    (
        "validate_source_conventions.py",
        mutate_short_convention_row,
        "fewer field(s) than the header",
        "a convention appended with fewer columns than the registry has — the shape "
        "apply_verdicts.py really wrote — whose empty flow_type publishes a transit flow "
        "as production",
    ),
    (
        "validate_source_conventions.py",
        mutate_dead_convention_pattern,
        "soviet union",
        "a convention whose label_pattern matches nothing the source carries, so the "
        "premise every verifier is supposed to inherit reaches no evidence bundle",
    ),
    (
        "validate_subnational_sums.py",
        mutate_subnational_aggregate_with_residual,
        "Germany r_fao_population_1952_10_18 1937",
        "a whole/part block calling itself an exact aggregate while its parts are 18 units "
        "short, so a consumer dropping the duplicate loses the difference silently",
    ),
    (
        "crosscheck_matchers.py",
        mutate_dead_status_exclusion_dropped,
        "ARG-1800-2025",
        "a matcher that can route data to a withdrawn polity, whose collapsed all-years "
        "row then outranks the live successors it was split into",
    ),
    (
        "validate_trade_mirror_gaps.py",
        mutate_trace_flow_into_mirror_gaps,
        "Ice and snow",
        "a trace-quantity flow readmitted to the mirror-gap table -- 0.02 t against a real "
        "flow is a 1000x 'disagreement' in which neither side need be wrong, and it is "
        "67.8% of what issue 112's ratio-only screen selected",
    ),
)

# Gates that need an argument to run in check mode rather than write mode. Verified, not
# assumed: against a freshly mutated copy, write_manifest.py with no arguments regenerates
# the manifest from the mutated CSV and exits 0, absorbing the defect, while --check exits
# 1 and says to rerun and commit. Without this mapping the case would pass while proving
# nothing.
#
# Verifying it took two attempts. The first harness ran write mode and then --check against
# the SAME directory, so write mode regenerated the manifest and --check compared two
# consistent files and passed -- which read as "the gate cannot detect this" when in fact
# the harness had repaired the defect before measuring it. Each mode needs its own fresh
# copy.
ARGS = {
    "write_manifest.py": ("--check",),
    "build_database.py": ("--check",),
    # Same trap as write_manifest: run with no arguments this script REGENERATES the
    # published flags from the mutated state and exits 0, absorbing the defect.
    "write_source_flow_flags.py": ("--check",),
}

# Non-script files under scripts/ that a gate reads before doing anything. build_database
# loads sources.yaml before parsing a single page, so without it the gate dies with a
# FileNotFoundError -- exit 1 for entirely the wrong reason. The "must name the defect"
# half of this script is what caught that; exit-code alone would have passed it.
EXTRA_SCRIPTS = {
    "validate_polygon_binding_determinism.py": ("sources.yaml",),
    # The s2 gate imports s2_failure()/geodesic_area_km2() from the repair script, so the two
    # cannot disagree about what "s2 can measure this" means. Staged without it the gate dies on
    # the import -- exit 2, no defect named, and the "must name the defect" arm of this harness is
    # what would report that as the wrong kind of failure.
    "validate_s2_polygons.py": ("repair_s2_polygons.py",),
    # spherical_edges.py is a LIBRARY, not a gate: it holds the great-circle maths that
    # build_database.py and validate_spherical_edges.py share, so neither can be staged without
    # it. It deliberately does not start with validate_/audit_/crosscheck_, so
    # check_every_gate_runs_in_ci does not demand a workflow step for it.
    #
    # Adding it to build_database.py's list was not optional and was not foreseen: the import sits
    # at module level, so a scratch repo without it made the build_database case die with an
    # ImportError -- exit 1 for entirely the wrong reason. The case still "fired", and only the
    # requirement that a gate NAME the defect separated a detected mutation from a crash before
    # reaching it. That is the third time that requirement has earned its keep in this file.
    "build_database.py": ("sources.yaml", "spherical_edges.py"),
    "validate_spherical_edges.py": ("spherical_edges.py",),
    # This gate derives the legal frontmatter key set by READING build_database.py's source,
    # so a scratch repo without it exits 2 before any check runs.
    "validate_references.py": ("build_database.py",),
}

# Which data files each case needs to be a real, writable copy rather than a symlink.
WRITABLE = {
    # crosscheck_matchers imports matchlib from `pipelines/polity-autoimprove` relative to
    # its OWN path, so in a scratch root that directory has to exist or the gate dies on
    # the import -- exit 1 with no defect named, which the "must name the defect" arm of
    # this harness would report as the wrong kind of failure. matchlib.py is the file the
    # case rewrites, so it must be a real copy and not a symlink; the registry and the
    # published FAOSTAT map are read-only but must be present, since a gate that finds no
    # mappings compares nothing and exits 0.
    # The two match.R files are staged because the gate also checks, by source text, that
    # all THREE matchers name both dead statuses. Absent, they would be reported as missing
    # -- true in the scratch root, misleading as a finding -- and the case's own defect would
    # arrive buried under two spurious ones.
    "crosscheck_matchers.py": (
        "pipelines/polity-autoimprove/matchlib.py",
        "pipelines/polity-autoimprove/state/applied_aliases.csv",
        "pipelines/pre1961-matching/match.R",
        "pipelines/faostat-era-matching/match.R",
        "faostat_area_polity_map.csv",
    ),
    # The GeoPackage is what this case mutates, so it must be a real copy — and it MUST be
    # written with write_gpkg(), not to_file(), for the reason that helper documents.
    # territory_basis.csv is staged not because the case writes it but because the gate
    # READS it for the row counts: without it the gate exits 1 saying the file is missing,
    # which is a failure for entirely the wrong reason and would have looked like a pass.
    "validate_data_without_geometry.py": (
        "polities_database.gpkg",
        "pipelines/polity-autoimprove/state/territory_basis.csv",
    ),
    # The correction table is the ONLY file this gate reads, and the case rewrites a
    # diagnosis string in it, so it must be a real copy or the mutation writes the wrong
    # label into the committed table through stage()'s symlink.
    "validate_landuse_corrections.py": (
        "pipelines/polity-autoimprove/state/landuse_corrections.csv",
    ),
    # Same reasoning: the case rewrites one field of the series table, and the gate also
    # reads the per-cell table for the cross-table coverage check, so both must be staged.
    # The series table must be a real copy or the mutation writes through the symlink into
    # the committed table; the per-cell one only has to be present, but naming it here is
    # cheaper than a second mechanism.
    "validate_yield_corrections.py": (
        "pipelines/polity-autoimprove/state/yield_series_corrections.csv",
        "pipelines/polity-autoimprove/state/yield_corrections.csv",
    ),
    # Same reasoning again: the sub-national table is the only file this gate reads, and the
    # case APPENDS a row to it, so it must be a real copy or the append lands in the
    # committed table through stage()'s symlink.
    "validate_subnational_sums.py": (
        "pipelines/polity-autoimprove/state/subnational_sums.csv",
    ),
    # The gap table is what the case rewrites, so it must be a real copy or the mutation
    # writes a trace flow through stage()'s symlink into the committed table. The summary is
    # staged because the gate holds the two to each other -- without it the gate exits 1
    # saying a file is missing, which is a failure for the wrong reason and would have read
    # as a pass.
    "validate_trade_mirror_gaps.py": (
        "pipelines/polity-autoimprove/state/trade_mirror_gaps.csv",
        "pipelines/polity-autoimprove/state/trade_mirror_summary.csv",
    ),
    # Signal A reads the CSV and the feature index; signal B also needs the GeoPackage for
    # geometry equality. All three must be REAL COPIES: the case rewrites the CSV, and with
    # only stage()'s default symlink in place the mutation wrote straight through into the
    # committed database -- which this harness detected and named, for the third time.
    "validate_polygon_period_fit.py": (
        "polities_database.csv",
        "polygon_feature_index.csv",
        "polities_database.gpkg",
    ),
    # This gate reads SEVEN tables, so all of them must be staged or it fails for the
    # wrong reason -- "file missing" rather than "column renamed". Listing them here is
    # itself the point of the gate: these are every table a consumer reads by name.
    "validate_schema_contract.py": (
        "label_alias_map.csv",
        "faostat_area_polity_map.csv",
        "polities_manifest.json",
        "pipelines/polity-autoimprove/state/applied_aliases.csv",
        "pipelines/faostat-era-matching/state/faostat_aliases.csv",
        # Pinned by issue 95 along with the rename that unified their column names.
        "pipelines/faostat-era-matching/state/ambiguous.csv",
        "pipelines/faostat-era-matching/state/unmatched.csv",
        "pipelines/faostat-era-matching/state/aggregates.csv",
        "pipelines/faostat-era-matching/state/registry_unmapped.csv",
    ),
    # A SOURCE-scanning gate, so what it needs staged is source files, not data. All three
    # layer-B readers are staged, not just the one the case mutates: the gate fails when it
    # can find NO reader at all -- a scan that has stopped matching anything must not read as
    # a pass -- so staging only build.R would have made this case fire for the wrong reason.
    # extdata.py is staged because the gate also checks that the rename and its reverse guard
    # are still declared there.
    "validate_layer_b_column_guard.py": (
        "pipelines/historical-production-harmonized/build.R",
        "pipelines/polity-autoimprove/extdata.py",
        "pipelines/polity-autoimprove/01_match_and_findings.py",
    ),
    # Half data, half source, because the gate is half of each. The published map is the file
    # the case mutates, so it must be a real copy; the other two crosswalks are staged because
    # the gate reports "missing -- this gate has stopped checking it" for an absent one, which
    # would make the case fire for the wrong reason. The four guarded WRITERS and the two guard
    # declarations are source files, and stage() copies only the gate itself from scripts/ --
    # without them check B reports four vanished writers and two missing declarations, and a
    # failure naming six things that are all fine is not a self-test of anything.
    "validate_matcher_orphan_guard.py": (
        "faostat_area_polity_map.csv",
        "pipelines/faostat-era-matching/state/faostat_aliases.csv",
        "pipelines/polity-autoimprove/state/applied_aliases.csv",
        "pipelines/polity-autoimprove/01_match_and_findings.py",
        "pipelines/polity-autoimprove/04_territory_basis.py",
        "pipelines/faostat-era-matching/match.R",
        "pipelines/pre1961-matching/match.R",
        "pipelines/polity-autoimprove/extdata.py",
        "pipelines/lib/orphan_guard.R",
    ),
    # Needs the SOURCE shapefile, not just the CSV: the gate compares each declared
    # binding against the features it could have matched. Without it the gate sees no
    # bindings at all and fails for the wrong reason, which is how this list was found.
    # The .zip in that directory is deliberately not staged (12 MB, unread).
    # Reads the COMMITTED feature index, not the 19 MB shapefile it was first staged with
    # (issue 103). That is what made this case possible at all: the shapefile is gitignored,
    # so in CI the gate resolved nothing, exited 0, and this harness correctly reported it
    # as a gate that cannot fail. The index carries the same candidates with their file
    # order, so the case now runs everywhere.
    "validate_polygon_binding_determinism.py": (
        "polities_database.csv",
        "polygon_feature_index.csv",
    ),
    "validate_code_year_agreement.py": ("polities_database.csv",),
    # Rewrites a PAGE, so wiki/polities must be a real copy; the CSV is only read, but the
    # gate needs `wiki/polities` staged at all or it sees zero pages and cannot fire.
    "validate_references.py": ("wiki/polities",),
    # Rewrites one row's polygon_source, so the CSV must be a real copy -- the fifth time
    # this list has been the difference between a self-test and a write into the committed
    # database.
    #
    # The GeoPackage is listed even though the case never writes it, and that is not
    # decorative: stage() creates NOTHING it was not asked for, and the CSV is the only file
    # it symlinks by default. Without this entry the gate exited **2** with "GeoPackage
    # missing" and named no defect -- the "must name the defect" arm of this harness caught
    # it, for the fourth time in this file. The gate measures its areas from the GeoPackage
    # and reads polygon_source from the CSV, so it needs both to see anything at all.
    #
    # The FAOSTAT map is listed so the gate reports reachability rather than calling every
    # step unmapped.
    "validate_source_change_steps.py": (
        "polities_database.csv",
        "polities_database.gpkg",
        "faostat_area_polity_map.csv",
    ),
    # Rewrites MAR-1911-1958's start_year, so the CSV must be a real copy. The successor
    # MAP must be staged too, and finding that out is the point: `stage()` provides only
    # the CSV by default, so without this line the cross-family signal had no territory
    # link, reported that it had checked nothing, and exited 1 for the wrong reason --
    # which the harness's "must NAME the defect" arm is what reported. The gate only
    # READS this file, but WRITABLE is the only mechanism that puts a second data file in
    # the scratch repo at all.
    "validate_period_overlaps.py": (
        "polities_database.csv",
        "iso3_successor_map.csv",
    ),
    # The GeoPackage is what this case rewrites, so it must be a real copy and must be
    # written with write_gpkg(). The other two are READ-ONLY for this gate but stage()
    # creates nothing it was not asked for: without the registry the gate exits 2 with
    # "missing" and names no defect, and without the alias map its double-count arm exits 2
    # the same way — both of which the "must NAME the defect" arm of this harness reports as
    # a failure for the wrong reason.
    "validate_composition_sums.py": (
        "polities_database.gpkg",
        "label_alias_map.csv",
        "pipelines/polity-autoimprove/state/polity_composition.csv",
    ),
    "validate_alias_chain_overlaps.py": ("label_alias_map.csv",),
    # The case REWRITES a page, so wiki/polities must be a real copy or the mutation would
    # gut the committed France page. territory_basis.csv is the gate's population -- without
    # it the gate finds no data-receiving polities at all, reports that, and exits 1 for the
    # wrong reason, which is the trap validate_chain_integrity's note above describes.
    "validate_page_depth.py": (
        "wiki/polities",
        "pipelines/polity-autoimprove/state/territory_basis.csv",
    ),
    # Rewrites the published alias map, so it needs a real copy rather than stage()'s
    # symlink; the baseline txt is copied automatically.
    "validate_alias_year_coverage.py": ("label_alias_map.csv",),
    # This case RENAMES a polity, so it needs a real copy of the CSV. Declaring the
    # baseline here instead let the default symlink stand, and the mutation wrote
    # straight through it into the repository — which two gates then correctly reported
    # as a defect in the real data. The baseline is copied by stage() automatically.
    "validate_live_name_ambiguity.py": ("polities_database.csv",),
    # Same lesson, learned twice. This case rewrites iso3_code, so it needs a real copy;
    # I added the case without touching this map and the mutation wrote ZZQ straight into
    # the committed database again. The default is a symlink precisely because most gates
    # only read the CSV, so a case that writes it MUST appear here.
    "validate_local_iso_codes.py": ("polities_database.csv",),
    # Same again: this case blanks an iso3_code, so a real copy is required or the mutation
    # writes through the default symlink into the committed database.
    "validate_dissolved_iso_codes.py": ("polities_database.csv",),
    # Rewrites two successor fields, so a real copy is required. The default symlink would
    # have written the cycle into the committed database -- the failure mode this harness has
    # now caught four times.
    # `wiki/polities` is staged because signals E and G read PAGES, not the CSV. Without it
    # `WIKI_DIR.glob("*.md")` yields nothing and both signals silently cannot fire -- so the
    # cycle case ran against a gate that was two-sevenths blind, and passed anyway because the
    # signal it targets reads the CSV. A gate staged without its inputs is a gate whose other
    # checks are being self-tested vacuously.
    "validate_chain_integrity.py": ("polities_database.csv", "wiki/polities"),
    # Only the GeoPackage: validate_polygons reads BOTH the declared area and the geometry from
    # it, so that is the file the case mutates. CShapes is not staged, so check B prints "skipped"
    # -- fine, since the case targets A2.
    #
    # NOTE FOR THE NEXT AUTHOR: this is the ONLY gate that both stages the GeoPackage and mutates
    # it, and that combination is a trap -- see write_gpkg(). Use that helper, not to_file().
    "validate_polygons.py": ("polities_database.gpkg",),
    # The GeoPackage is mutated, so it must be a real copy, and write_gpkg() must be used to
    # replace it -- see that helper: `to_file` over an existing .gpkg APPENDS a layer and the
    # gate reads the unmutated first one. The feature index is the gate's REFERENCE and is
    # deliberately left untouched by the mutation: the defect is that the shipped geometry
    # stopped matching a source area that is still correctly on record.
    "validate_simplification_loss.py": (
        "polities_database.gpkg",
        "polygon_feature_index.csv",
    ),
    # Both files as real copies: the case rewrites the map, and the gate reads polity spans from
    # the CSV to know what "past coverage" means. With the CSV symlinked the read still works, but
    # copying keeps the case honest about what it touches.
    # The case appends to registry_unmapped.csv, so that must be a real copy; the gate also reads
    # the published map and the database to decide whether the claim is false.
    "validate_registry_unmapped.py": (
        "pipelines/faostat-era-matching/state/registry_unmapped.csv",
        "faostat_area_polity_map.csv",
        "polities_database.csv",
    ),
    "validate_map_area_year.py": (
        "faostat_area_polity_map.csv",
        "polities_database.csv",
    ),
    # The case rewrites the map, so it must be a real copy. The manifest is listed although the
    # case never writes it: arm D reads the published scope declaration out of it, and with the
    # manifest absent that arm prints SKIP -- a gate self-tested with one arm silently switched
    # off, which is the trap several entries above document.
    "validate_map_era_scope.py": (
        "faostat_area_polity_map.csv",
        "polities_database.csv",
        "polities_manifest.json",
    ),
    # Needs the GeoPackage (to know which rows are live AND polygonal) and both site files,
    # writable because the case mutates the geojson. The master CSV must be a real copy too,
    # not stage()'s symlink: signal A compares it against site/polities.csv byte for byte, and
    # a mutation writing through the symlink would rewrite the committed database.
    "validate_site_outputs.py": (
        "polities_database.csv",
        "polities_database.gpkg",
        "site/polities.csv",
        "site/polities.geojson",
    ),
    "validate_order_decided_families.py": (
        "polities_database.csv",
        "pipelines/polity-autoimprove/state/applied_aliases.csv",
    ),
    "validate_aliases.py": (
        "polities_database.csv",
        "pipelines/polity-autoimprove/state/applied_aliases.csv",
    ),
    "build_database.py": ("polities_database.csv", "wiki/polities"),
    # The case rewrites the STATE file, so that must be a real copy or the mutation writes
    # through stage()'s symlink into the committed conventions registry. The published flags
    # are listed because they are what the check compares against: absent, the check reports
    # a missing file rather than the demoted flow, and would not name it.
    "write_source_flow_flags.py": (
        "pipelines/polity-autoimprove/state/source_conventions.csv",
        "source_flow_flags.csv",
        "label_alias_map.csv",
        # The writer resolves `polity_code` from the alias map and `wiki_page` from the
        # pages, so both must be PRESENT or the regenerated text differs from the committed
        # file for reasons that have nothing to do with the mutation — the check would then
        # fail on an unmutated repo, which is a case that proves nothing.
        "wiki/polities",
    ),
    "validate_reporting_areas.py": ("scripts/sources/reporting-areas/build.py",),
    # Both cases rewrite the registry, so it must be a real copy or the mutation writes
    # through stage()'s symlink into the committed file — the leak this harness has caught
    # four times. The review ledger is listed because the reachability arm reads the
    # (source, label) pairs out of it: absent, that arm cannot fire at all and the
    # dead-pattern case would pass for the wrong reason. 11_retest_conventions.py is
    # listed because the gate IMPORTS it for CHECKS; without it the gate reports "no
    # CHECKS" for every row, which is exit 1 without naming the injected defect — and the
    # "must NAME the defect" arm is what would report that.
    "validate_source_conventions.py": (
        "pipelines/polity-autoimprove/state/source_conventions.csv",
        "pipelines/polity-autoimprove/state/review_ledger.csv",
        "pipelines/polity-autoimprove/11_retest_conventions.py",
    ),
    # Rewrites the CSV, so that must be a real copy. The GeoPackage is deliberately
    # NOT listed: the mutation writes a fresh one into `root`, and staging a copy
    # first would give the file two layers and let the gate read the unmutated one.
    # The FAOSTAT map is listed only so it is PRESENT — the gate reads it to say
    # whether a consumer can reach the polities involved, and reports "not
    # FAOSTAT-mapped" for everything if it is absent.
    "validate_shared_polygons.py": (
        "polities_database.csv",
        "faostat_area_polity_map.csv",
    ),
    # sources.yaml is read before any page is parsed, so without it the gate dies with a
    # FileNotFoundError -- exit 1 for the wrong reason, which the "must name the defect"
    # requirement is what caught.
    "write_manifest.py": (
        "polities_database.csv",
        "polities_manifest.json",
        "faostat_area_polity_map.csv",
        "label_alias_map.csv",
    ),
    # matchlib.py must be a real COPY, not stage()'s symlink: the case rewrites it,
    # and a symlink would edit the matcher the whole pipeline uses. The other four
    # are read-only for this gate but must be PRESENT — it imports matchlib, and it
    # compares the constant across all three declaring components plus the sentence
    # in wiki/README.md, so a scratch repo missing any of them fails for the wrong
    # reason (one of them reported as "does not declare END_YEAR_EXCLUSIVE" rather
    # than the injected defect, which the "must name the defect" arm would catch).
    "validate_year_semantics.py": (
        "polities_database.csv",
        "pipelines/polity-autoimprove/matchlib.py",
        "pipelines/polity-autoimprove/state/applied_aliases.csv",
        "pipelines/pre1961-matching/match.R",
        "pipelines/faostat-era-matching/match.R",
        "wiki/README.md",
    ),
}



def check_every_gate_runs_in_ci() -> list:
    """Every gate script must appear in the workflow that claims to run them all.

    A gate absent from `.github/workflows/validate.yml` is not a gate — it passes on the
    author's machine and never runs again. This happened immediately: the
    validate_live_name_ambiguity gate was written, counted in the README, given a
    self-test case, and left out of the workflow, so CI would have run 23 of 24 while
    the README said otherwise.

    Checked here rather than as its own gate, because a gate that verifies gates are
    registered would itself need registering — the same problem one level up. This file
    already runs in CI, so the check runs whether or not anyone remembers it.
    """
    workflow = os.path.join(REPO, ".github/workflows/validate.yml")
    if not os.path.exists(workflow):
        return ["`.github/workflows/validate.yml` is missing"]
    with open(workflow, encoding="utf-8") as fh:
        text = fh.read()
    scripts = sorted(
        f
        for f in os.listdir(os.path.join(REPO, "scripts"))
        if f.startswith(("validate_", "crosscheck_", "audit_")) and f.endswith(".py")
    )
    missing = [f for f in scripts if f not in text]
    problems = []
    if missing:
        problems.append(
            f"{len(missing)} gate script(s) never run in CI, because "
            f"validate.yml does not mention them: {missing}"
        )

    # And a gate nobody documented is a gate nobody can find. Checked by SCRIPT NAME
    # rather than by counting: the README states its gate count in words, and a numeric
    # claim in prose is exactly what goes stale. This caught the live-name-ambiguity gate,
    # which had a table row describing it but no mention of the script that runs it — so
    # it read as documented while being invisible to any structural check.
    # EVERY BASELINE MUST BE A frozenset({...}), NOT A BARE {...}.
    #
    # A bare set literal is fine until it is EMPTIED, at which point `{}` is a DICT, and
    # `set(observed) - BASELINE` raises TypeError. The gate then breaks precisely when the
    # data becomes correct — the one moment nobody is expecting a failure, and the failure
    # looks like a bug in the check rather than a success in the data.
    #
    # This is not hypothetical and it is not new. validate_spatial_containment has carried a
    # comment explaining the trap since its KNOWN_DISCONTINUOUS was first emptied. On
    # 2026-08-05 it bit validate_period_overlaps anyway, when retiring BLX-1921-1999 removed
    # its last entry — the warning existed and had not been applied to the sibling. Checked
    # structurally here so the next baseline cannot repeat it.
    #
    # Detected by AST rather than by regex: a first pass with a pattern misread
    # `BASELINE_DIFFERENT = {237}` as empty, because the heuristic looked for quotes.
    import ast
    import glob as _glob
    bare = []
    for path in sorted(_glob.glob(os.path.join(REPO, "scripts", "*.py"))):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Set):
                continue
            names = [getattr(t, "id", "") for t in node.targets]
            if names and any(
                names[0].startswith(p)
                for p in ("BASELINE", "KNOWN", "TRACKED", "LEGITIMATE")
            ):
                bare.append(f"{os.path.basename(path)}:{names[0]}")
    if bare:
        problems.append(
            f"{len(bare)} baseline constant(s) declared as a bare set literal, which "
            f"becomes a DICT when emptied and raises TypeError on set arithmetic — use "
            f"frozenset({{...}}): {bare}"
        )

    readme = os.path.join(REPO, "README.md")
    if os.path.exists(readme):
        with open(readme, encoding="utf-8") as fh:
            rd = fh.read()
        undocumented = [f for f in scripts if f[: -len(".py")] not in rd]
        if undocumented:
            problems.append(
                f"{len(undocumented)} gate script(s) run in CI but are not named in "
                f"README.md: {undocumented}"
            )

    if not problems:
        print(
            f"every gate runs in CI and is named in the README "
            f"({len(scripts)} scripts)"
        )
    return problems

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=int, help="run one case by 1-based number")
    args = ap.parse_args()

    try:
        import geopandas as gpd
        from shapely import affinity
        from shapely.validation import make_valid
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely unavailable ({exc})")
        return 2
    if not os.path.exists(GPKG):
        print(f"FAIL: {GPKG} missing; run scripts/build_database.py first")
        return 2

    cases = list(enumerate(CASES, start=1))
    if args.case:
        cases = [c for c in cases if c[0] == args.case]
        if not cases:
            print(f"FAIL: no case {args.case}")
            return 2

    problems = []
    # A leaking mutation is worse than a missed defect: it edits the committed database
    # while reporting success. Fingerprinted per case so the culprit is named.
    before_all = fingerprint_real_data()
    for n, (gate, mutate, expect, why) in cases:
        root = stage(
            gate,
            extra=EXTRA_SCRIPTS.get(gate, ()),
            writable=WRITABLE.get(gate, ()),
        )
        try:
            did = mutate(root, gpd, make_valid, affinity)
            code, out = run(root, gate)
            fired = code != 0
            names = expect in out
            print(f"case {n}: {gate}")
            print(f"   mutation: {did}")
            print(f"   detects:  {why}")
            print(f"   result:   exit={code} names {expect}: {names}")
            if not fired:
                problems.append(
                    f"{gate} PASSED a mutation it claims to catch ({did}) — the gate "
                    f"cannot fail, so its green verdict on real data means nothing"
                )
            elif not names:
                problems.append(
                    f"{gate} failed as required but its output does not name {expect}, "
                    f"so a real failure would not tell a maintainer where to look"
                )
            after_all = fingerprint_real_data()
            leaked = sorted(
                set(after_all.splitlines()) - set(before_all.splitlines())
            )
            if leaked:
                problems.append(
                    f"{gate} MUTATED THE REAL REPOSITORY: "
                    f"{', '.join(x.strip() for x in leaked)}. The case "
                    f"writes a file it did not declare in WRITABLE, so stage()'s symlink "
                    f"stood and the mutation went through it. Restore with git checkout "
                    f"and add the file to WRITABLE for this gate."
                )
                # Re-fingerprint so one leak is not re-reported for every later case.
                before_all = fingerprint_real_data()
        finally:
            shutil.rmtree(root, ignore_errors=True)

    # Mutation proves a gate CAN fail; this proves it ever gets the chance.
    problems.extend(check_every_gate_runs_in_ci())

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"\nPASS: {len(cases)} gate(s) fail on an injected defect and name it, "
          f"and every gate runs in CI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
