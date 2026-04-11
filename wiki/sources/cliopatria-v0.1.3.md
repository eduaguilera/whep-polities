---
source_slug: cliopatria-v0.1.3
title: "Cliopatria: historical polity boundaries (Seshat Global History Databank)"
author: Seshat Global History Databank
year: 2025
version: v0.1.3 (January 2025)
url: https://github.com/Seshat-Global-History-Databank/cliopatria
project_url: https://seshatdatabank.info/
license: CC BY 4.0
access_date: 2026-04-11
type: dataset
coverage: ~1,600 historical polities worldwide, 3400 BCE to 2024 CE
---

# Cliopatria v0.1.3

## Why it was ingested

WHEP uses Cliopatria as its **pre-1886 fallback** for polities that
have no CShapes coverage and no GADM modern-proxy option. The
Ottoman Empire 1800–1886 row (`OTT-1800-1886`) is the worked example
here: CShapes does not cover that period at all, and the pipeline
loads a Cliopatria polygon for it. Every WHEP polity whose
`polygon_source` column starts with `Cliopatria` inherits this
source's caveats — most importantly the `~25–100 km boundary
uncertainty` and the single-time-step-per-polity pattern.

## What it adds

Derived from `docs/02_DATA_SOURCES.md §2.12`,
`docs/04_POLYGON_SOURCES.md §Aourednik/Cliopatria`, and
`docs/06_KNOWN_ISSUES_AND_DECISIONS.md`. No external fetch yet — a
future ingest should pull the Seshat paper directly if one exists.

### §scope — what Cliopatria covers

- **~1,600 polities, 15,690 GeoJSON features** (hand-traced from
  reference atlases). `[docs/02 §2.12]`
- **Temporal range**: 3400 BCE to 2024 CE. Variable resolution: some
  polities have dense time-step coverage, others have one or two.
- **1800–1886 window**: 1,945 features covering 290+ polities.
  `[docs/02 §2.12]`
- **Per-polity time-step counts for WHEP-relevant cases:**
  - Ottoman Empire: **33 records**
  - Russian Empire: 34 records
  - Qing China: 31 records
  - Qajar Iran: 12 records
  - Ashanti Empire: 20 records
- **Spatial precision**: "~hundreds of vertices per polygon,
  ~25–100 km uncertainty" `[docs/02 §2.12]`.
- **License**: CC BY 4.0 (citation required, redistribution
  permitted).

### §wheps-use — how WHEP loads it

- Pipeline script: `R/12_integrate_cliopatria_polygons.R`.
- Input: `inputs/cliopatria.geojson.zip` (not committed to WHEP
  repo; downloaded from the Seshat GitHub).
- Output: `data/geodata/cliopatria_polygons.gpkg`.
- WHEP **only extracts polygons** for a small number of rows where
  no other source is available: 4 rows called out in docs/02
  (IRN-1800-1828 Qajar, AUH-1800-1867 Austrian Empire,
  SWE-1800-1809 Swedish Empire, SWE-1809-1814 Sweden), plus 6 more
  added via `R/21_cliopatria_polygon_fixes_and_mexico.R`
  (ETH-1800-1889, EGY-1800-1899, ZAN-1856-1964, MOR-1800-1904,
  MAD-1800-1912, OTT-1800-1886).
- **`docs/15_V2.2_CHANGELOG.md §13`** describes the OTT row fix as
  replacing a "small subset" polygon with a "Cliopatria 2.66M km2
  full Ottoman" polygon.

### §single-time-step — the simplification WHEP makes

This is the most important caveat for lint. Cliopatria provides
**many** time-steps for long-lived polities (33 for the Ottoman
Empire, 34 for Russia), but WHEP extracts **one** snapshot per
polity row. `docs/06_KNOWN_ISSUES_AND_DECISIONS.md §Ottoman entries`
literally says:

> "Ottoman entries (OTT-1800-1886 etc.): Cliopatria polygon from one
> time-step applied across periods with significant territorial
> change (~2% temporal coverage)."

That 2% figure is 1 / ~50 years, i.e. the single-snapshot polygon
is treated as valid across the entire row even when the actual
territory moved dramatically (1830 Greek independence, 1830 French
Algeria, 1878 Berlin Congress). Any WHEP polity page citing
Cliopatria for an 1800–1886-scale row must disclose this.

The same one-snapshot treatment applies to the other back-projected
Cliopatria-sourced rows: **EGY-1800-1899** (~16% coverage),
**ZAN-1856-1964** (~26%), **ETH-1800-1889**, **RUS-1800-1886**
(~14–18%), and **MEX-1800-1848** (~21%). See
`docs/06_KNOWN_ISSUES_AND_DECISIONS.md §Remaining known
polygon-date mismatches` for the full list.

## Known limitations

1. **Single-time-step extraction** (see §single-time-step) —
   WHEP's integration is the culprit here, not Cliopatria itself,
   which offers many time-steps.
2. **Spatial precision ~25–100 km**. Much coarser than CShapes or
   GADM. Fine for empire-scale polities, unusable for small states
   or subnational questions.
3. **Some empires are monolithic.** `docs/04 §Aourednik/Cliopatria`
   notes that Cliopatria occasionally "treats empires as a single
   polygon" (e.g. "British Africa" rather than the discrete
   colonies). This is a coding convention for certain polities,
   not a universal rule.
4. **No ISO codes** `[docs/02 §2.13]`. Matching Cliopatria rows to
   WHEP polity codes goes through name matching, which is
   fragile.
5. **Variable quality across time periods.** Pre-1800 polygons are
   based on different atlas sources than 1800–1886; the handful of
   post-1886 records are mostly for continuity with better sources.
6. **Not an authoritative trade-data source.** Cliopatria is a
   boundary dataset. Trade regimes, economic-union membership,
   and customs-union dates must come from other sources.

## License and redistribution

CC BY 4.0: citation required, redistribution and modification
permitted. Citation format not yet pinned down here — a future
ingest of the Seshat paper or Cliopatria README should nail it
down and update this source file. For now, citing "Seshat Global
History Databank, Cliopatria v0.1.3 (January 2025),
https://github.com/Seshat-Global-History-Databank/cliopatria" is
the working form.
