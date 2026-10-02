#!/usr/bin/env python3
"""Keep subnational polity codes short and standard, and keep every rename one-way.

A subnational code is `ISO3-SUB-start-end`. Until 2026-10-02 the SUB part had three
shapes: short codes (AUS-QLD, FRA-84), spelled-out names copied from a source panel's
unit id (ARG-MENDOZA, BRA-RIOGRANDEDOSUL, 28 Japanese prefectures), and NUTS-like ids
(ITA-ITH1). The standard is now:

  - SUB is the ISO 3166-2 subdivision code where the unit is one (ARG-M, BRA-RS,
    JPN-13, FRA-56, ITA-21). The ISO code is the rule; this gate checks its SHAPE,
    because a vendored ISO list is not kept here.
  - Spain uses INE province numbers instead (ESP-17 Girona). The ISO letters would have
    given four retired codes to a different province (ESP-GI-1833-2025 was Gipuzkoa),
    which a rename table cannot undo, because the same string sits on both sides.
  - A unit with no ISO code (a composite, a colonial unit, a statistical area) keeps a
    documented abbreviation of at most four characters (CHL-BINB, USA-FLLA, IDN-JVM).

The old codes are published in data/final/polity_code_renames.csv, so data keyed on them
can be translated. That only works while the table stays a FUNCTION: one new code per old
code, no chains, and no old code ever reused for another polity.

FAILS ON:
  - a 4-part code whose SUB is not 1-4 characters of [A-Z0-9]. This is what stops a
    generator writing `<prefix>-<panel unit id>` again: see
    pipelines/subnational-vocabulary/10_generate_pages.py
  - a Spanish province bound to a mapspain-ign feature whose SUB is not that feature's
    INE number, and a Brazilian state bound to geobr-ibge whose SUB is not its UF code
    (the two sources where the feature id IS the standard code)
  - in polity_code_renames.csv: a duplicate old_code, an old_code that is still (or
    again) a polity code, a new_code that is not a polity code, a chain (a new_code that
    is also an old_code), or an identity row
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(REPO, "data/final/polities_database.csv")
RENAMES = os.path.join(REPO, "data/final/polity_code_renames.csv")
RENAME_FIELDS = ["old_code", "new_code", "renamed_on", "change_ref", "rule_applied",
                 "iso3166_2", "reason"]
SUBUNIT = re.compile(r"^([A-Z0-9]{3,4})-([A-Z0-9]+)-(\d{4})-(\d{4})$")
SUB_OK = re.compile(r"^[A-Z0-9]{1,4}$")
# Sources whose feature id IS the standard SUB for that country.
FEATURE_IS_SUB = {("ESP", "mapspain-ign"): "INE province number",
                  ("BRA", "geobr-ibge"): "IBGE UF code"}


def main() -> int:
    if not os.path.exists(DB) or not os.path.exists(RENAMES):
        print(f"FAIL: missing {DB if not os.path.exists(DB) else RENAMES}")
        return 2
    rows = list(csv.DictReader(open(DB, encoding="utf-8")))
    codes = {r["polity_code"] for r in rows}
    fails = []
    n_sub = 0
    for r in rows:
        code = r["polity_code"]
        if code.count("-") != 3:
            continue
        n_sub += 1
        m = SUBUNIT.match(code)
        if not m or not SUB_OK.match(m.group(2)):
            sub = m.group(2) if m else code
            fails.append(f"{code}: subunit part {sub!r} is not 1-4 characters of [A-Z0-9]; "
                         "use the ISO 3166-2 code (INE number in Spain), or a documented "
                         "abbreviation of at most 4 characters")
            continue
        iso3, sub = m.group(1), m.group(2)
        what = FEATURE_IS_SUB.get((iso3, r["polygon_source"]))
        fid = (r["polygon_feature_id"] or "").strip()
        if what and fid and sub != fid:
            fails.append(f"{code}: bound to {r['polygon_source']} feature {fid!r}, so its "
                         f"subunit part must be that {what}, not {sub!r}")

    with open(RENAMES, encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames != RENAME_FIELDS:
            fails.append(f"polity_code_renames.csv header is {rd.fieldnames}, expected {RENAME_FIELDS}")
        ren = list(rd)
    olds = [r["old_code"] for r in ren]
    old_set = set(olds)
    seen = set()
    for r in ren:
        o, n = r["old_code"], r["new_code"]
        if o in seen:
            fails.append(f"renames: {o} is renamed twice")
        seen.add(o)
        if o == n:
            fails.append(f"renames: {o} is renamed to itself")
        if o in codes:
            fails.append(f"renames: retired code {o} is a polity code again -- an old code "
                         "must never be reused, or data keyed on it changes meaning")
        if n not in codes:
            fails.append(f"renames: {o} -> {n}, but {n} is not a polity code")
        if n in old_set:
            fails.append(f"renames: {o} -> {n} chains, because {n} is itself renamed; "
                         "point the row at the final code")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["renamed_on"] or ""):
            fails.append(f"renames: {o} has renamed_on {r['renamed_on']!r}, expected YYYY-MM-DD (UTC)")

    if fails:
        print(f"FAIL: {len(fails)} subunit-code problem(s) over {n_sub} subunit rows "
              f"and {len(ren)} renames")
        for f in fails[:60]:
            print(f"  {f}")
        return 1
    print(f"PASS: {n_sub} subunit codes are standard (SUB of 1-4 [A-Z0-9]); "
          f"{len(ren)} renames are one-to-one, unchained and never reused")
    return 0


if __name__ == "__main__":
    sys.exit(main())
