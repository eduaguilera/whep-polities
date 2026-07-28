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

# Statuses whose rows must NEVER receive data. Kept in the database for
# provenance; consumers must exclude them from resolution. Mirrors
# pipelines/polity-autoimprove/matchlib.py, Matcher.DEAD_STATUS.
DEAD_STATUS = ("retired", "superseded")

# Fields a consumer resolves against. Deliberately excludes polygon_* — a
# re-measured area must not invalidate every downstream copy.
IDENTITY_FIELDS = ("polity_code", "polity_name", "start_year", "end_year",
                   "polity_type", "iso3_code", "cow_code", "wiki_status")

ap = argparse.ArgumentParser()
ap.add_argument("--check", action="store_true",
                help="verify the committed manifest matches the database; exit 1 on drift")
A = ap.parse_args()

rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))
live = [r for r in rows if r.get("wiki_status") not in DEAD_STATUS]
dead = [r for r in rows if r.get("wiki_status") in DEAD_STATUS]

payload = [[r.get(f, "") for f in IDENTITY_FIELDS]
           for r in sorted(rows, key=lambda r: r["polity_code"])]
identity_hash = hashlib.sha256(
    json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

manifest = {
    "_comment": (
        "Contract for consumers of the WHEP polities database. Compare "
        "`identity_sha256` against your embedded copy to detect drift; exclude "
        "`dead_status` rows from any resolution of data to polities. Regenerate "
        "with scripts/write_manifest.py."
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
            print(f"  manifest says {o['counts']['total']} polities "
                  f"({o['counts']['live']} live); database has {len(rows)} ({len(live)} live)")
            if o.get("identity_sha256") != identity_hash:
                print(f"  identity hash {o.get('identity_sha256','')[:16]}… -> {identity_hash[:16]}…")
        except Exception:
            print("  (existing manifest is unparseable)")
    print("\n  Fix: run scripts/write_manifest.py and commit data/final/.")
    sys.exit(1)

open(MANIFEST, "w", encoding="utf-8").write(new)
print(f"wrote {os.path.relpath(MANIFEST, REPO)}: {len(rows)} polities "
      f"({len(live)} live, {len(dead)} dead), identity {identity_hash[:16]}…")
