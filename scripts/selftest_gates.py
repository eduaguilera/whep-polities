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
for the reporting-area aggregates. Fifteen of twenty-eight, chosen by what it would cost if the gate were
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

  crosscheck_matchers.py is DELIBERATELY NOT COVERED HERE, and the reason is worth
  recording because it looked like an easy tenth case. It compares two independent
  matchers against each other, so producing a disagreement means changing what ONE of
  them computes -- and both read the same applied_aliases.csv, so mutating the registry
  moves both identically and they still agree. My attempt repointed a faostat Kenya
  alias and the gate passed, which reads as "the gate cannot fail" and is not: staged on
  its own it reports 281 mappings, 276 agreements and the 3 baselined differences, so it
  works. The mutation was the wrong shape, like the REMOVED_ prefix that could not hide
  a substring.
  Covering it properly needs a surgical edit to matchlib.py's or match.R's resolution
  logic, which is brittle to write and would fail for reasons unrelated to the gate. An
  uncovered gate that is honestly labelled uncovered beats a case that passes for the
  wrong reason.

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
    rows[0]["target_polity_code"] = target
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
        "area_code": "270", "area_name": "Mayotte", "iso3": "MYT",
        "note": "registry area with no polity family (non-country/aggregate)",
    })
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return "listed area 270 Mayotte as having no polity, while MYT-1800-2025 exists"


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
    Other -- and it was HIDDEN because the rest-of-world union deduplicates, so the
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


CASES = (
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
        "validate_local_iso_codes.py",
        mutate_new_iso_code,
        "ZZQ",
        "an unreviewed iso3_code value, which changes what an ISO-keyed join matches",
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
        "validate_shared_polygons.py",
        mutate_shared_polygon,
        "STP-1800-2025",
        "two coexisting live polities on one polygon, which claims the ground twice",
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
ARGS = {"write_manifest.py": ("--check",), "build_database.py": ("--check",)}

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
    "validate_alias_chain_overlaps.py": ("label_alias_map.csv",),
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
    "validate_reporting_areas.py": ("scripts/sources/reporting-areas/build.py",),
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
