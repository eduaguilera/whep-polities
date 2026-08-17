---
source_slug: gadm-4.1
title: "GADM: Database of Global Administrative Areas, version 4.1"
author: GADM project (Robert J. Hijmans and collaborators)
year: 2022
version: "4.1"
url: https://gadm.org/
license: "Free for academic and other non-commercial use; redistribution and commercial use require permission (see https://gadm.org/license.html)"
access_date: 2026-08-17
type: dataset
coverage: Present-day administrative boundaries worldwide, national (adm0) and first sub-national level (adm1)
---

# GADM 4.1

This page exists because **46 polity pages already declared `gadm-4.1` in their
`sources:` frontmatter and it resolved to nothing** — the slug named
`scripts/sources.yaml`'s machine registry and `data/geodata/gadm-4.1/`, not a
readable source record here. A declared source that resolves to no file looks like
evidence and is not, which is the failure `validate_citations.py` exists to prevent
for inline links; `scripts/validate_declared_sources.py` now extends that to this
frontmatter channel, and this page is what the 46 pages resolve to (issue 19).

## Why it was ingested

GADM is this database's **modern-boundary proxy of last resort**. Where no
historical GIS vector exists for a polity — CShapes 2.0 begins in 1886 and covers
sovereign states and dependencies only, Cliopatria has no series for many small
colonies, and Paine et al. cover precolonial Africa — a present-day administrative
outline is often the only geometry available. Two uses dominate:

1. **Small islands and dependencies whose borders are the coastline**, so vintage
   barely matters: `wiki/polities/` rows for Aruba, the Bahamas, Bermuda, the
   Cayman Islands, the Falklands, the Faroes, Gibraltar, Guam, Niue, Norfolk
   Island, the Cook Islands, Saint Pierre and Miquelon, the Turks and Caicos, the
   US Virgin Islands and others bind GADM features directly.
2. **Composed unions built from adm1 units** for territories that were
   administered separately but have no feature of their own — French Cochinchina
   (six southern Vietnamese provinces), Portuguese India (Goa ∪ Daman ∪ Diu),
   French India (Puducherry ∪ Karikal ∪ Mahé ∪ Yanam), occupied Libya's
   Tripolitania / Cyrenaica / Fezzan, the Saar, and the 1949–1951 Indonesian
   federal units. Those are assembled by `scripts/sources/constructed/build.py`
   and carry `polygon_source: constructed`, but GADM is their underlying evidence.

## What it adds

- **Two extracts, registered separately in the machine registry**
  (`scripts/sources.yaml`): `gadm-4.1-adm0`, keyed by `GID_0` (ISO3, e.g. `AUT`),
  and `gadm-4.1-adm1`, keyed by `GID_1` (e.g. `ESP.6_1` for Canarias). Both are
  built by `scripts/sources/gadm-4.1/fetch.sh`, which downloads **per-country**
  GeoPackages for the countries the wiki actually cites and combines them, rather
  than the 1.4 GB world file.
- Because the extract is a country allow-list, **a polity can name a correct
  feature and still get no geometry** if its country was never fetched. That has
  happened and been fixed at least three times (issue 59: `USA`/`JPN` added
  2026-08-04 for Alaska and Okinawa; `CAN`/`IND`/`IDN` added 2026-08-05 for the
  Canadian, Portuguese-Indian, French-Indian and Indonesian unions; `LBY`/`DEU`
  added for issues 155 and 156). The symptom is a build log line reading
  `feature not found`, not an error.

## Known limitations

- **Vintage is 2022, and every historical use is an anachronism by
  construction.** GADM 4.1 records boundaries as they were when compiled, so a row
  spanning 1816–1961 that binds a GADM feature is back-projecting a modern outline
  across its whole span. Pages using it must carry `polygon_status: proxy` or
  `estimate` (never `assigned`) and state the direction and magnitude of the
  error; `polygon_vintage_drift` exists for the cases where the vintage is
  unrepresentative of much of the span. Some pages record `polygon_vintage: 2024`
  for GADM 4.1, which is the access year rather than the dataset's; the dataset
  version is 4.1 (2022).
- **It contains no historical entities at all.** GADM cannot tell you whether a
  colony's borders moved; it can only tell you where the successor's borders are
  now. Any claim that a boundary was *stable* across a span has to come from a
  different source, and pages that assert stability against GADM alone are
  asserting it on no evidence.
- **Not redistributable.** The licence permits academic use but not
  redistribution, which is one reason `data/geodata/**` is gitignored and the
  extracts are fetched rather than committed.
- **Coastline resolution differs from the historical sources.** GADM outlines are
  substantially more detailed than CShapes 2.0's, so a GADM-derived area can
  differ from a CShapes-derived one for the same territory without either being
  wrong; `MDV-1800-2025` is the reverse case, where CShapes captured only part of
  the atoll chain (24 km² against ~300) and GADM was fetched to replace it.
