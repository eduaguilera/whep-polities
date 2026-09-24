#!/usr/bin/env python3
"""An alias label that names a panel unit must not route it to another country.

The subnational panel names each reporting unit by an `admin_unit_id` ('ARG-FORMOSA') and an
`admin_name_clean` ('Formosa'), and routing resolves a unit by either form (see
validate_name_labels_single_country.py). The alias map does not know which rows a label will
meet. A rule with a BLANK source applies to every source, the panel included. So a rule written
for one territory, keyed on a name that is also a panel unit's name, sends that unit's rows to the
wrong country.

WHAT IT FOUND (2026-09-24). One rule did this:

    'Formosa' (any source) 1895-1945 -> TWN-1895-1945
        The rule was written for Federico-Tena, which lists Japanese Taiwan as 'Formosa
        (Taiwan)'. Formosa is also Argentina's national territory (later a province), and the
        panel reports it as 'Formosa' in the same years. A reader that did not pass
        source = juan-subnational routed 11,284 valued rows of ARG-FORMOSA (1900-1945) to
        Japanese Taiwan. The rule is now two rules, scoped to federico_tena and to iia. IIA's
        French 'FORMOSE' labels reach 'Formosa' through source_label_lexicon.csv, and the first
        re-run of write_stated_area_basis.py showed that without an iia rule they resolve by name
        to ARG-FORMOSA.

validate_name_labels_single_country.py could not see this case. The name is carried by only one
panel country, and the other territory is not a panel unit at all.

A SOURCE-SCOPED rule is different: it applies only to rows of its own source. 'Georgia |
faostat -> GEO-1991-2025' has the same name as the panel's USA-GEORGIA (12,458 valued rows in
the rule's years). FAOSTAT does not report US states, so that rule cannot reach those rows. The
gate lets such a rule stand when its source does not carry the unit. A source CARRIES a unit
when it has a rule on one of the unit's forms that routes into the unit's own country. For the
panel slugs that means every unit they report.

WHAT THIS CHECKS. For every row of data/final/label_alias_map.csv whose label, normalised as
matchlib.norm and the WHEP consumer's .norm_polity_label normalise it, equals a panel unit's id
or any of its names:
  * the target polity must belong to the unit's country, or
  * the rule's source must be one that does not carry the unit.
A target belongs to a country when that country's iso3 is its own, one of its containers'
(polity_containment.csv), or one of its successors' (a colony, dominion or territory counts for
the state it became part of). The unit's country is the iso3 prefix of its id.

NAMES. The ledger (pipelines/agent-harness/state/routing_verdicts.csv) keeps one name per unit,
but the panel gives some units several names. MEX-CMX is 'Ciudad de México' and also 'Distrito
Federal', and BOL-BEN is 'Beni' and also 'El Beni'. So this gate reads every (unit, name) pair
from pipelines/agent-harness/state/panel_unit_names.csv. That file is committed and regenerated
from the gitignored panel with --refresh. It fails if a ledger unit or ledger name is missing
from the file, because a names table that lags the ledger would hide exactly the units added
last.

Bidirectional baseline: a new collision fails, and a baselined one that no longer occurs must be
removed or this fails too.

Usage:
  python3 scripts/validate_alias_labels_cross_country.py
  python3 scripts/validate_alias_labels_cross_country.py --refresh [PANEL.parquet]
"""
import collections
import csv
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "pipelines/agent-harness/state/routing_verdicts.csv")
NAMES = os.path.join(REPO, "pipelines/agent-harness/state/panel_unit_names.csv")
ALIASES = os.path.join(REPO, "data/final/label_alias_map.csv")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
CONTAIN = os.path.join(REPO, "data/final/polity_containment.csv")
# Same default and override as pipelines/agent-harness/harness.py.
PANEL = os.environ.get(
    "WHEP_SUBNATIONAL",
    os.path.expanduser("~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_juan/"
                       "whep_production_subnational.parquet"))

NAME_FIELDS = ["unit_id", "country", "admin_name", "first_year", "last_year", "valued_rows"]

# (source_label, source, unit_id) -> reason it is knowingly left in place.
BASELINE = {}


def norm(s: str) -> str:
    """matchlib.norm, verbatim. It is the same key the WHEP consumer builds (.norm_polity_label),
    so 'México', 'Mexico' and 'MEXICO' are one label here, as they are at resolution time."""
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def refresh(panel: str) -> int:
    """Rewrite panel_unit_names.csv from the panel: one row per (unit, name) with valued data."""
    import pandas as pd

    if not os.path.exists(panel):
        print(f"FAIL: panel not found at {panel} (set WHEP_SUBNATIONAL or pass the path)")
        return 1
    d = pd.read_parquet(panel, columns=["country_clean", "admin_unit_id", "admin_name_clean",
                                        "year", "value_canonical"])
    d = d[d["value_canonical"].notna()]
    g = (d.groupby(["admin_unit_id", "admin_name_clean", "country_clean"])
           .agg(first_year=("year", "min"), last_year=("year", "max"),
                valued_rows=("year", "size"))
           .reset_index()
           .sort_values(["admin_unit_id", "admin_name_clean"]))
    rows = [{"unit_id": r.admin_unit_id, "country": r.country_clean,
             "admin_name": r.admin_name_clean, "first_year": int(r.first_year),
             "last_year": int(r.last_year), "valued_rows": int(r.valued_rows)}
            for r in g.itertuples(index=False)]
    tmp = NAMES + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=NAME_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, NAMES)
    print(f"wrote {os.path.relpath(NAMES, REPO)}: {len(rows)} (unit, name) pairs over "
          f"{g['admin_unit_id'].nunique()} units")
    return 0


def load_countries():
    """polity_code -> set of iso3 codes it belongs to (own, containers', successors')."""
    pol = {}
    with open(POLDB, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pol[r["polity_code"]] = r
    up = collections.defaultdict(set)
    for code, r in pol.items():
        for o in re.split(r"[;,]", r.get("successor") or ""):
            if o.strip():
                up[code].add(o.strip())
    with open(CONTAIN, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            up[r["member_code"]].add(r["container_code"])

    cache = {}

    def countries(code):
        if code not in cache:
            seen, stack, isos = {code}, [code], set()
            while stack:
                c = stack.pop()
                iso = (pol.get(c, {}).get("iso3_code") or "").strip().upper()
                if iso:
                    isos.add(iso)
                for n in up[c] - seen:
                    seen.add(n)
                    stack.append(n)
            cache[code] = isos
        return cache[code]

    return countries


def main() -> int:
    if "--refresh" in sys.argv:
        i = sys.argv.index("--refresh")
        return refresh(sys.argv[i + 1] if len(sys.argv) > i + 1 else PANEL)

    for path in (LEDGER, NAMES, ALIASES, POLDB, CONTAIN):
        if not os.path.exists(path):
            print(f"FAIL: {os.path.relpath(path, REPO)} is missing")
            return 1
    csv.field_size_limit(sys.maxsize)

    # unit_id -> (iso3, set of names); the id prefix is the country, as the panel writes it.
    units = collections.defaultdict(lambda: ["", set(), 0])
    with open(NAMES, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            u = units[r["unit_id"]]
            u[0] = r["unit_id"].split("-")[0].upper()
            u[1].add(r["admin_name"])
            u[2] += int(r["valued_rows"] or 0)

    lag = []
    with open(LEDGER, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            uid, name = r["unit_id"], (r.get("admin_name") or "").strip()
            if uid not in units or (name and name not in units[uid][1]):
                lag.append(f"{uid} ({name!r})")
    if lag:
        print(f"FAIL: {len(lag)} ledger unit/name pair(s) are not in "
              f"{os.path.relpath(NAMES, REPO)}: {', '.join(lag[:10])}")
        print("\nThe names table lags the ledger, so a collision on the newest units would go "
              "unseen. Regenerate it from the panel with --refresh.")
        return 1

    forms = collections.defaultdict(set)          # normalised label -> unit ids
    for uid, (iso, names, _) in units.items():
        forms[norm(uid)].add(uid)
        for n in names:
            forms[norm(n)].add(uid)

    countries = load_countries()
    with open(ALIASES, encoding="utf-8", newline="") as fh:
        rules = [r for r in csv.DictReader(fh) if norm(r["source_label"]) in forms]

    # A source carries a unit when it routes one of the unit's forms into the unit's country.
    carries = collections.defaultdict(set)
    for r in rules:
        src = r["source"].strip()
        for uid in forms[norm(r["source_label"])]:
            if units[uid][0] in countries(r["polity_code"]):
                carries[src].add(uid)

    hits, benign = {}, []
    for r in rules:
        src = r["source"].strip()
        for uid in sorted(forms[norm(r["source_label"])]):
            iso = units[uid][0]
            if iso in countries(r["polity_code"]):
                continue
            key = (r["source_label"], src, uid)
            if src and uid not in carries[src]:
                benign.append(key + (r["polity_code"],))
                continue
            hits[key] = (r["polity_code"], r["year_start"], r["year_end"],
                         "blank source" if not src else f"{src} also carries {uid}")

    stale = sorted(set(BASELINE) - set(hits))
    if stale:
        print(f"FAIL: {len(stale)} baseline entr(ies) no longer needed -- remove them:")
        for key in stale:
            print(f"  {key}: {BASELINE[key]}")
        return 1

    new = sorted(set(hits) - set(BASELINE))
    if new:
        print(f"FAIL: {len(new)} alias rule(s) route a panel unit's label to another country\n")
        for label, src, uid in new:
            code, y0, y1, why = hits[(label, src, uid)]
            iso, names, n = units[uid]
            print(f"  {label!r} [{src or 'any source'}] {y0}-{y1} -> {code}  ({why})")
            print(f"      is also {uid} ({iso}; {', '.join(sorted(names))}; {n:,} valued "
                  f"panel rows), which {code} does not belong to")
        print("\nA blank-source rule applies to every source, so it meets the panel's rows too. "
              "Scope the rule to the source(s) that actually use the label for that territory "
              "(check layer B and the source's own vocabulary) in "
              "pipelines/polity-autoimprove/state/applied_aliases.csv, or for faostat rows in "
              "pipelines/faostat-era-matching/match.R, then regenerate with "
              "scripts/write_label_alias_map.py. Baseline it here only with a reason.")
        return 1

    print(f"PASS: no alias rule routes a panel unit's label to another country "
          f"({len(units)} units, {sum(len(v[1]) for v in units.values())} names, "
          f"{len(rules)} rule(s) on a unit label; {len(benign)} source-scoped rule(s) name a "
          f"unit their source does not carry, e.g. "
          f"{', '.join(f'{b[0]!r} [{b[1]}] -> {b[3]}' for b in benign[:3]) or 'none'}; "
          f"{len(BASELINE)} baselined)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
