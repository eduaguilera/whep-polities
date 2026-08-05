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

Nine cases: three geometry gates mutating the GeoPackage, four contract gates
mutating a CSV, one mutating a WIKI PAGE -- the source of truth every other artefact
derives from -- and one mutating a BUILDER SCRIPT's own literal. Nine of twenty-four, chosen by what it would cost if the gate were
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
    marker = '"RASI-1850-2021": {'
    assert marker in text, "no RASI aggregate to extend"
    i = text.index(marker)
    j = text.index('"components": [', i) + len('"components": [')
    text = text[:j] + '"FRO", ' + text[j:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return "claimed FRO for RASI-1850-2021 as well as Europe Other"



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


CASES = (
    (
        "validate_schema_contract.py",
        mutate_renamed_column,
        "observed_rows",
        "a renamed column, which every reader sees as None rather than as an error",
    ),
    # validate_polygon_binding_determinism.py is NOT here, and the reason is the whole
    # point of this file. Its mutation IS staged and does fire locally -- setting
    # VNM-1887-1954's polygon_feature_year back to 1893 makes the gate exit 1 and name
    # the row. But the gate needs data/geodata/**, which is GITIGNORED, so in CI it can
    # resolve no bindings at all, exits 0, and this harness correctly reported it as
    # "PASSED a mutation it claims to catch". Keeping the case would have meant a red CI
    # for a gate that is simply unverifiable there. The gate now prints an explicit SKIP
    # rather than a bare pass, and is marked local-only in the README, so an inert run is
    # visible instead of looking like a verification. Mutation-tested by hand on 2026-08-05
    # (three ways: reintroduce the defect, drop a live baseline entry, baseline a fixed
    # row) -- which is weaker than a standing claim, and is the honest state.
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
        "validate_code_year_agreement.py",
        mutate_code_year_disagreement,
        "FRA-1800-1871",
        "a code whose embedded years contradict its own columns",
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
    "validate_polygon_binding_determinism.py": ("sources.yaml",),"build_database.py": ("sources.yaml",)}

# Which data files each case needs to be a real, writable copy rather than a symlink.
WRITABLE = {
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
    "validate_polygon_binding_determinism.py": (
        "polities_database.csv",
        "data/geodata/cshapes-2.0/CShapes-2.0.shp",
        "data/geodata/cshapes-2.0/CShapes-2.0.dbf",
        "data/geodata/cshapes-2.0/CShapes-2.0.shx",
        "data/geodata/cshapes-2.0/CShapes-2.0.prj",
    ),
    "validate_code_year_agreement.py": ("polities_database.csv",),
    "validate_alias_chain_overlaps.py": ("label_alias_map.csv",),
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
    "validate_aliases.py": (
        "polities_database.csv",
        "pipelines/polity-autoimprove/state/applied_aliases.csv",
    ),
    "build_database.py": ("polities_database.csv", "wiki/polities"),
    "validate_reporting_areas.py": ("scripts/sources/reporting-areas/build.py",),
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
