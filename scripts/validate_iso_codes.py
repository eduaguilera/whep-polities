#!/usr/bin/env python3
"""Check that a live polity's `iso3` field really is an ISO 3166-1 alpha-3 code.

`iso3` is the field consumers join on when they have a country code rather than a WHEP
polity code, so a value that is not an ISO code makes the polity unreachable by that
route — silently, because there is nothing to fail.

That is not hypothetical. FRS-1977-2025 is modern Djibouti and carried `iso3: FRS`.
Djibouti's ISO 3166-1 alpha-3 is DJI, and FRS is not an ISO code at all, so matchlib
could not reach the polity by ISO family and fell back to matching on name. Corrected to
DJI (the FRS *prefix* is deliberate and unchanged — it continues the chain from the
colonial row — but the prefix and the ISO field are different things).

Historical entities that never had an ISO code are NOT the target here: Austria-Hungary,
the Ottoman Empire, Bechuanaland, French West Africa, New South Wales and dozens more
legitimately carry a WHEP-internal key, and so do the aggregate reporting buckets. The
check is therefore scoped to LIVE polities, where a real country should have a real code.

Two live rows are exempt because no ISO 3166-1 alpha-3 exists for them:

  ICN-1800-2025  Canary Islands. Part of Spain; ISO 3166-2:ES-CN, no alpha-3 of its own.
  KOS-2008-2025  Kosovo. No official assignment; XKX is user-assigned, not ISO.

The valid-code list is embedded below rather than read from R's `countrycode`. It was
generated FROM that package (249 alpha-3 codes) and then inlined, because this repo's
renv library does not carry countrycode — so a runtime lookup silently reported "skipped"
inside an overall pass, which is precisely how a check stops being a check. ISO 3166-1
alpha-3 assignments change very rarely; if one is added, a live polity using it fails here
and the fix is to add the code to the list.

Usage:
  python3 scripts/validate_iso_codes.py
"""
import csv
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")

# Live polities with no ISO 3166-1 alpha-3 in existence. See the docstring.
EXEMPT = {"ICN-1800-2025", "KOS-2008-2025"}

# Aggregate reporting buckets are not countries and are keyed by WHEP-internal codes.
AGGREGATE_PREFIXES = ("ROW", "RAFR", "RASI", "REUR", "RLAM", "RNAM", "ROCE", "BLX", "ANT")


# ISO 3166-1 alpha-3, generated from R's countrycode package. See the docstring.
ISO3 = set("""
    ABW AFG AGO AIA ALA ALB AND ARE ARG ARM ASM ATA ATF ATG AUS AUT AZE BDI
    BEL BEN BES BFA BGD BGR BHR BHS BIH BLM BLR BLZ BMU BOL BRA BRB BRN BTN
    BVT BWA CAF CAN CCK CHE CHL CHN CIV CMR COD COG COK COL COM CPV CRI CUB
    CUW CXR CYM CYP CZE DEU DJI DMA DNK DOM DZA ECU EGY ERI ESH ESP EST ETH
    FIN FJI FLK FRA FRO FSM GAB GBR GEO GGY GHA GIB GIN GLP GMB GNB GNQ GRC
    GRD GRL GTM GUF GUM GUY HKG HMD HND HRV HTI HUN IDN IMN IND IOT IRL IRN
    IRQ ISL ISR ITA JAM JEY JOR JPN KAZ KEN KGZ KHM KIR KNA KOR KWT LAO LBN
    LBR LBY LCA LIE LKA LSO LTU LUX LVA MAC MAF MAR MCO MDA MDG MDV MEX MHL
    MKD MLI MLT MMR MNE MNG MNP MOZ MRT MSR MTQ MUS MWI MYS MYT NAM NCL NER
    NFK NGA NIC NIU NLD NOR NPL NRU NZL OMN PAK PAN PCN PER PHL PLW PNG POL
    PRI PRK PRT PRY PSE PYF QAT REU ROU RUS RWA SAU SDN SEN SGP SGS SHN SJM
    SLB SLE SLV SMR SOM SPM SRB SSD STP SUR SVK SVN SWE SWZ SXM SYC SYR TCA
    TCD TGO THA TJK TKL TKM TLS TON TTO TUN TUR TUV TWN TZA UGA UKR UMI URY
    USA UZB VAT VCT VEN VGB VIR VNM VUT WLF WSM YEM ZAF ZMB ZWE
""".split())


def main() -> int:
    valid = ISO3
    live = []
    for r in csv.DictReader(open(POLITIES, encoding="utf-8")):
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            continue
        code = r["polity_code"]
        end = re.search(r"-(\d{4})$", code)
        if not end or int(end.group(1)) < 2025:
            continue
        iso = (r.get("iso3_code") or "").strip()
        if iso in ("", "NA"):
            continue
        if code in EXEMPT or code.split("-")[0] in AGGREGATE_PREFIXES:
            continue
        live.append((code, r.get("polity_name", ""), iso))

    print(f"live polities carrying an iso3 value: {len(live)}")
    print(f"exempt (no ISO code exists): {len(EXEMPT)}")

    bad = [(c, n, i) for c, n, i in live if i not in valid]
    print(f"whose iso3 is NOT ISO 3166-1 alpha-3: {len(bad)}")
    for code, name, iso in sorted(bad):
        print(f"   {code:<18} {name[:38]:<40} iso3={iso!r}")

    if bad:
        print(
            f"\nFAIL: {len(bad)} live polity(ies) advertise a non-ISO code in `iso3`, so "
            f"a consumer holding a real country code cannot reach them\n"
        )
        print(
            "  Fix the wiki page's `iso3` field, or add the polity to EXEMPT here if no "
            "ISO 3166-1 alpha-3 exists for it. Note the polity-code PREFIX is a separate "
            "thing and does not need to change."
        )
        return 1

    print("\nPASS: every live polity's iso3 is a real ISO 3166-1 alpha-3 code")
    return 0


if __name__ == "__main__":
    sys.exit(main())
