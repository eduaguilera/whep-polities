#!/usr/bin/env python3
"""Publish a manifest of the polities database for downstream consumers.

Why: the WHEP R package embeds a copy of this database (`data/polities.rda`,
built by its `data-raw/table_mappings.R`). That copy silently drifted to **603
rows against 740 here** — 144 polities missing, 7 that no longer existed, and
**24 that were retired or superseded**, so real FAOSTAT area codes were being
routed to withdrawn rows. Nothing detected it because checking meant comparing
whole tables across two repositories.

A manifest makes the check cheap and unambiguous: a consumer compares one small
JSON file — row count, a content hash, and the set of live polity codes — and
knows immediately whether its copy is current. It also states which rows are
**not for routing**, so a consumer cannot repeat the dead-polity mistake by
omission.

The hash covers only the fields a consumer resolves against (code, name, span,
type, iso3, cow, status), NOT polygon geometry or areas: a re-measured polygon
should not invalidate every downstream copy, whereas a changed date or status
must.

Usage:
  python3 scripts/write_manifest.py [--check]

`--check` verifies the committed manifest matches the database without writing,
exiting 1 on drift, for CI.
"""
import argparse, csv, hashlib, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
MANIFEST = os.path.join(REPO, "data/final/polities_manifest.json")

# Statuses that ASSERT a polygon exists. A row carrying one of these while the
# build attached no geometry is a known gap, published so consumers can assert
# that no NEW gap appears rather than against an invariant we do not yet meet.
CLAIMS_POLYGON = ("assigned", "proxy", "estimate", "polygon_vintage_drift")

# Statuses whose rows must NEVER receive data. Kept in the database for
# provenance; consumers must exclude them from resolution. Mirrors
# pipelines/polity-autoimprove/matchlib.py, Matcher.DEAD_STATUS.
DEAD_STATUS = ("retired", "superseded")

# Fields a consumer resolves against. Deliberately excludes polygon_* — a
# re-measured area must not invalidate every downstream copy.
# Duplicated from pipelines/faostat-era-matching/match.R, which acts on them. Kept in step by
# scripts/validate_constants.py — the same treatment DEAD_STATUS gets, and for the same reason: a
# constant that lives in two places will drift unless something compares them.
FAOSTAT_GROUP_CODE_MIN = 5000
FAOSTAT_AGGREGATE_CODES = (351,)

# FAOSTAT AGGREGATES that sit BELOW group_code_min. The >= 5000 rule covers the main
# regional groups (World 5000, the continents, the income bands) but is not exhaustive:
# several domains carry aggregates in the country range.
#
#   261  European Union (12) (excluding intra-trade)
#   265  China (excluding intra-trade)
#   266  European Union (15) (excluding intra-trade)
#   268  European Union (25) (excluding intra-trade)
#   269  European Union (27) (excluding Croatia) (excluding intra-trade)
#   420  Sub-Saharan Africa
#
# Two kinds, deliberately in one list because a consumer treats them identically: 420 is
# a regional group, and the five "(excluding intra-trade)" codes are multi-territory
# trade totals. Neither is a territory.
#
# Found by running real consumer builds, one code at a time -- 420 in a production build
# from faostat-emissions-livestock, 265 in a CBS build from faostat-trade-totals -- and
# then enumerated properly by sweeping every readable pin for unmapped codes below the
# threshold, which found exactly these six across nine pins. Discovering them one per
# smoke run would have taken as many runs as there are codes.
#
# Published separately from deliberate_area_codes because the two are different facts.
# 351 China is a deliberate NON-MAPPING: it is reported alongside its own components and
# routing it anywhere would double-count. 420 is simply a regional group whose code
# happens to be low. A consumer should report the first as a decision and the second as
# a group, and it cannot tell them apart from the numbers alone.
FAOSTAT_SUBTHRESHOLD_GROUP_CODES = (261, 265, 266, 268, 269, 420)

# The local (non-ISO) iso3_code values, read from the gate's baseline rather than restated.
# scripts/validate_local_iso_codes.py already owns and CI-gates that list; a second copy here
# would be a second thing to drift. Missing baseline -> empty field rather than a wrong one.
def _local_iso3_codes():
    path = os.path.join(REPO, "scripts/validate_local_iso_codes_baseline.txt")
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            code, _, comment = line.partition("#")
            code = code.strip()
            if code and "local" in comment:
                out.append(code)
    return sorted(out)


LOCAL_ISO3_CODES = _local_iso3_codes()

IDENTITY_FIELDS = ("polity_code", "polity_name", "start_year", "end_year",
                   "polity_type", "iso3_code", "cow_code", "wiki_status")

ap = argparse.ArgumentParser()
ap.add_argument("--check", action="store_true",
                help="verify the committed manifest matches the database; exit 1 on drift")
A = ap.parse_args()

rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))
live = [r for r in rows if r.get("wiki_status") not in DEAD_STATUS]
dead = [r for r in rows if r.get("wiki_status") in DEAD_STATUS]

# Polities whose status asserts a polygon the GeoPackage does not carry. Read
# from the baseline the polygon validator maintains, which is the authoritative
# record of the tracked backlog (see scripts/validate_polygons_baseline.txt and
# issue #3), so the manifest cannot disagree with the gate.
BASELINE = os.path.join(REPO, "scripts/validate_polygons_baseline.txt")
polygon_gaps = []
if os.path.exists(BASELINE):
    polygon_gaps = sorted(
        l.split("#")[0].strip() for l in open(BASELINE, encoding="utf-8")
        if l.split("#")[0].strip()
    )

payload = [[r.get(f, "") for f in IDENTITY_FIELDS]
           for r in sorted(rows, key=lambda r: r["polity_code"])]
identity_hash = hashlib.sha256(
    json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

# The FAOSTAT area -> polity map published alongside this manifest, fingerprinted
# so a consumer can pin both with one comparison. Only the digest and shape are
# recorded, not the mapping itself: the map is 281 rows and belongs in its own
# file, while what a consumer needs from the manifest is whether the copy it
# holds is the current one.
AREA_MAP = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
area_map_info = None
if os.path.exists(AREA_MAP):
    raw = open(AREA_MAP, "rb").read()
    map_rows = list(csv.DictReader(open(AREA_MAP, encoding="utf-8")))
    area_map_info = {
        "path": "data/final/faostat_area_polity_map.csv",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mappings": len(map_rows),
        "areas": len({r["area_code"] for r in map_rows}),
    }

# The source-label -> polity alias map, fingerprinted the same way. A consumer
# holding data labelled "Cape Verde" or "ZAR" resolves it through this rather than
# building its own lookup — which is how the FAOSTAT mapping acquired a second
# authority and misattributed 118 area-years.
ALIAS_MAP = os.path.join(REPO, "data/final/label_alias_map.csv")
alias_map_info = None
if os.path.exists(ALIAS_MAP):
    raw = open(ALIAS_MAP, "rb").read()
    alias_rows = list(csv.DictReader(open(ALIAS_MAP, encoding="utf-8")))
    alias_map_info = {
        "path": "data/final/label_alias_map.csv",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "aliases": len(alias_rows),
        "labels": len({r["source_label"] for r in alias_rows}),
        "sources": sorted({r["source"] for r in alias_rows if r["source"]}),
    }

manifest = {
    "_comment": (
        "Contract for consumers of the WHEP polities database. Compare "
        "`identity_sha256` against your embedded copy to detect drift; exclude "
        "`dead_status` rows from any resolution of data to polities; and treat "
        "`polygon_gap_polity_codes` as the known set of rows whose status "
        "asserts a polygon the GeoPackage does not carry, so you can assert no "
        "NEW gap appears without asserting an invariant we do not yet meet. "
        "`faostat_area_map` fingerprints the FAOSTAT area -> polity mapping "
        "published beside this file, which is the authority for which polity a "
        "reporting area's data belongs to in a given year, and "
        "`label_alias_map` the mapping from a source's own country LABEL to a "
        "polity — prefer both over rebuilding those mappings yourself. "
        "Regenerate with scripts/write_manifest.py."
    ),
    "source": "data/final/polities_database.csv",
    "identity_fields": list(IDENTITY_FIELDS),
    "identity_sha256": identity_hash,
    "counts": {
        "total": len(rows),
        "live": len(live),
        "dead": len(dead),
    },
    "dead_status": list(DEAD_STATUS),
    "dead_polity_codes": sorted(r["polity_code"] for r in dead),
    "claims_polygon_status": list(CLAIMS_POLYGON),
    "polygon_gap_polity_codes": polygon_gaps,
    # What the consumer otherwise has to infer or re-derive.
    #
    # pipelines/faostat-era-matching/match.R states both of these in a comment and acts on them, but
    # neither was published, so eduaguilera/whep re-derived them independently: it inferred
    # "deliberately unmapped" from crosswalk membership, and it measured the 5000 threshold against
    # real FAOSTAT production (34 of 34 unmapped codes are >= 5000). Two repositories holding the
    # same fact with no link between them is what this file exists to prevent.
    #
    # Inference is also weaker than the fact. An area can be absent from the crosswalk for reasons
    # other than a deliberate decision, and a consumer inferring intent from absence cannot tell the
    # difference — which is exactly the mistake that made a downstream warning call FAOSTAT 351
    # "China" an unknown area code.
    # WHICH iso3_code values a consumer cannot join against ISO-keyed data.
    #
    # iso3_code is not ISO-conformant and cannot be: there is no ISO 3166 code for
    # Austria-Hungary, so this database invents AUH. Sound, but it makes the column two things
    # at once, and a consumer joining against an ISO-keyed dataset silently matches nothing for
    # the local ones. That is what stops four dissolved federations reaching WHEP's LUH2 land
    # series, and they carry 11.88% of production value at 1961.
    #
    # Published as a FACT rather than left to inference, for the same reason
    # faostat_unmapped_areas is: a consumer cannot tell a local code from an ISO one by looking,
    # and discovering it by getting no match is how that gap went unexplained.
    #
    # Descriptive only. It does NOT decide how dissolved states should be coded -- three
    # approaches coexist in the data today, which is issue 55.
    "local_iso3_codes": LOCAL_ISO3_CODES,
    "local_iso3_why": (
        "iso3_code holds real ISO 3166-1 codes for entities that have them and LOCAL "
        "identifiers for entities that do not (historical states, this project's own "
        "aggregates). A consumer joining iso3_code against an ISO-keyed dataset will not match "
        "any code listed here. The convention is the polity family's prefix, e.g. "
        "AUH-1800-1859 carries AUH. See issue 55 for how dissolved states SHOULD be coded; "
        "this field only reports which codes are local today."
    ),
    "faostat_unmapped_areas": {
        "group_code_min": FAOSTAT_GROUP_CODE_MIN,
        "deliberate_area_codes": sorted(FAOSTAT_AGGREGATE_CODES),
        "subthreshold_group_codes": sorted(FAOSTAT_SUBTHRESHOLD_GROUP_CODES),
        "why": (
            "Area codes at or above group_code_min are FAOSTAT's own regional groups "
            "(World, continents, income groups), never territories. The codes in "
            "deliberate_area_codes are statistical aggregates reported ALONGSIDE their own "
            "components, so routing them to a polity would double-count: 351 'China' is "
            "mainland + Hong Kong + Macao + Taiwan. subthreshold_group_codes are regional "
            "groups whose code falls BELOW group_code_min, so the threshold alone misses them: "
            "420 'Sub-Saharan Africa' appears in the emissions domains, and the "
            "'(excluding intra-trade)' codes are multi-territory trade totals. None of the three kinds "
            "is a gap in this database."
        ),
    },
    "faostat_area_map": area_map_info,
    "label_alias_map": alias_map_info,
    "live_polity_codes": sorted(r["polity_code"] for r in live),
}

new = json.dumps(manifest, indent=1, ensure_ascii=False) + "\n"

if A.check:
    old = open(MANIFEST, encoding="utf-8").read() if os.path.exists(MANIFEST) else ""
    if old == new:
        print(f"--check: PASS — manifest matches the database "
              f"({len(rows)} polities, {len(live)} live, {len(dead)} dead)")
        sys.exit(0)
    print("--check: FAIL — data/final/polities_manifest.json is stale")
    if old:
        try:
            o = json.loads(old)
            # Report only what actually differs. Printing the counts
            # unconditionally read as "the counts are wrong" even when they
            # matched and the drift was elsewhere — which sent the reader looking
            # in the wrong place, and was how a changed area-map digest got
            # reported as a polity-count problem.
            if (o["counts"]["total"], o["counts"]["live"]) != (len(rows), len(live)):
                print(f"  manifest says {o['counts']['total']} polities "
                      f"({o['counts']['live']} live); database has {len(rows)} ({len(live)} live)")
            if o.get("identity_sha256") != identity_hash:
                print(f"  identity hash {o.get('identity_sha256','')[:16]}… -> {identity_hash[:16]}…")
            if o.get("faostat_area_map") != area_map_info:
                print(f"  faostat_area_map changed: {o.get('faostat_area_map')} "
                      f"-> {area_map_info}")
            if o.get("label_alias_map") != alias_map_info:
                # Name the subfield that actually differs, for the same reason the
                # counts above are conditional. Reporting the alias count alone said
                # "869 -> 869 aliases" when four rows were rescoped from one source to
                # blanket: the count was identical and the digest was not, so the one
                # number printed was the one number that had not changed.
                was, now = o.get("label_alias_map") or {}, alias_map_info or {}
                for key in sorted(set(was) | set(now)):
                    if was.get(key) != now.get(key):
                        a, b = was.get(key), now.get(key)
                        if key.endswith("sha256"):
                            a = f"{str(a)[:16]}…"
                            b = f"{str(b)[:16]}…"
                        print(f"  label_alias_map.{key}: {a} -> {b}")
            for key in ("dead_polity_codes", "live_polity_codes",
                        "polygon_gap_polity_codes"):
                was, now = set(o.get(key) or []), set(manifest[key])
                if was != now:
                    added, removed = sorted(now - was), sorted(was - now)
                    print(f"  {key}: +{len(added)} -{len(removed)}"
                          + (f" added {added[:5]}" if added else "")
                          + (f" removed {removed[:5]}" if removed else ""))
        except Exception as exc:
            print(f"  (existing manifest is unparseable: {exc})")
    print("\n  Fix: run scripts/write_manifest.py and commit data/final/.")
    sys.exit(1)

open(MANIFEST, "w", encoding="utf-8").write(new)
print(f"wrote {os.path.relpath(MANIFEST, REPO)}: {len(rows)} polities "
      f"({len(live)} live, {len(dead)} dead), identity {identity_hash[:16]}…")
