---
source_slug: cshapes-2.0
title: "Mapping the International System, 1886-2019: The CShapes 2.0 Dataset"
author: Schvitz, Girardin, Rüegger, Weidmann, Cederman, Gleditsch
year: 2022
journal: Journal of Conflict Resolution 66(1), 144–161
doi: 10.1177/00220027211013563
url: https://doi.org/10.1177/00220027211013563
dataset_url: https://icr.ethz.ch/data/cshapes/
license_paper: CC-BY (SAGE open access)
license_dataset: Free for academic and non-commercial use
pdf_local: wiki/sources/pdfs/schvitz-et-al-2021-mapping-the-international-system-1886-2019-the-cshapes-2-0-dataset.pdf
pdf_sha256: 701b846e6b504fd1de284db2f58a896ef9cb26ff3950e5899706690b991837fb
access_date: 2026-04-11
type: dataset
coverage: Global sovereign states and dependencies, 1886–2019
---

# Schvitz et al. 2022 — CShapes 2.0

This file is the **primary-source** record for the CShapes 2.0 dataset.
It supersedes the earlier docs-derived stub for this slug (see the
2026-04-11 upgrade log entry). All page numbers refer to the published
article (JCR 66(1), 144–161). The PDF lives at `pdf_local` above and
is gitignored; verify with `sha256sum` against `pdf_sha256`.

## Why it was ingested

CShapes 2.0 is the primary polygon source for ~480 of the ~1,220 rows
in `data/final/polities_database.csv`. Without a first-class source
file, every polity page citing CShapes is a `[database]` stub. This
ingest lets polity pages cite specific paper sections and inherit the
paper's own caveats.

## What it adds

### §scope — what CShapes covers (p.144 abstract, p.147)

- "CShapes 2.0, a GIS dataset that maps the borders of states and
  dependent territories from 1886 through 2019" (p.144).
- "extends temporal coverage by tracing international borders all the
  way back to 1886, the year that followed the Berlin conference on
  the partition of Africa" (p.145).
- Final dataset: **"249 political units that are represented by 476
  polygons over time. 152 countries have a single polygon during the
  entire period, while 97 countries have two or more"** (p.152).
- Total territorial changes: **357**, decomposed as **159 creation/
  dissolution events, 112 sovereignty transfers over dependent
  territories, 86 boundary adjustments between existing units**
  (p.152).
- Time resolution: 1 day (Table 1, p.146) — CShapes records the exact
  date of each territorial change. Other datasets are coarser:
  Euratlas 100 years, Centennia 0.1 year.

### §coding-states — independent-state definition and the COW/GW split (p.147–148)

- CShapes codes independence using two different authorities and
  ships **two versions**: "we provide two separate versions CShapes
  2.0 that are based either on the COW or GW coding of independent
  states" (p.148). **This is load-bearing for WHEP lint**: a polity
  coded with different start years under COW vs GW will have
  *different* polygons depending on which version of CShapes was
  loaded.
- COW criteria: "units to exceed a population threshold of 500,000
  and also codes states as independent if they maintain diplomatic
  ties to at least two major powers" (p.147).
- GW criteria: "slightly less restrictive criteria for statehood, and
  often records much earlier independence dates than COW. For example,
  COW codes Canada as an independent state from 1920 onward, while GW
  sets its independence date to 1867" (p.147–148).
- GW also includes "a number of additional states not listed by COW
  (for example: Tibet and Orange Free State)" (p.147).
- WHEP's polity codes carry a `cow_code` column but the repo does not
  explicitly record which of the two CShapes versions was loaded —
  this is an open lint question flagged in `docs/06` as a source of
  column-mismatch bugs.

### §coding-dependencies — colonies, protectorates, mandates (p.148)

- CShapes defines dependent territories as "those units that are
  under the control of an independent state, but that are not
  considered part of its core territory. These are typically
  non-adjacent territories that are ruled as colonies or protectorates"
  (p.148).
- Four dependency categories: "(1) colonies, (2) protectorates, (3)
  international mandates and (4) occupied territories" (p.148).
- **Population threshold for dependencies: 250,000**. "we have
  narrowed down the list of dependencies to those units with a
  population greater than 250,000 during the sample period" (p.148).
  Smaller dependencies are silently excluded — any WHEP polity for a
  sub-250k-population dependency cannot cite CShapes.
- Source for dependency coding: Territorial Change Dataset (Tir, Diehl
  & Goertz 1998) plus the original COW list of dependencies. "The
  coverage of this list ends in 1993. However, this does not
  constitute a problem for our task, since by then all dependencies
  had either become part of core states or gained independence"
  (p.148). I.e. post-1993 new-dependency creation is not covered, but
  by construction this window is empty.

### §coding-borders — how polygons are drawn (p.148–150)

- "we code a state's territory primarily based on its internationally
  recognized boundaries" (p.148).
- **Disputed territory rule:** "Instead of coding disputed territories
  separately, however, we assign them to a given state based on its
  de facto control over the region" (p.149). Golan Heights → Israel.
  Kashmir → Line of Control. De facto states (Abkhazia, South Ossetia,
  Biafra, Republic of Serbian Krajina) are **not** separate units;
  their territory is attributed to the recognized host state.
- **Placeholder polygons:** for regions where borders were undefined
  (parts of Africa, Middle East, East Asia in the 19th century), "we
  therefore add a placeholder polygon that represents the borders as
  they were eventually defined. These polygons are flagged with a
  dummy variable to indicate that their borders were not yet fully
  defined, which enables users to remove or modify these observations
  if necessary" (p.150). **WHEP lint implication**: any polity row
  citing CShapes for an early date should check whether the dummy
  flag is set; if so, the polygon is provisional, not observed.

### §coding-changes — what counts as a territorial change (p.149–151)

- Three types of change: (1) creation/dissolution of political units,
  (2) transfers of sovereignty over dependent territories, (3) border
  adjustments between existing units (p.149–150).
- **Size threshold for border adjustments: 100 × 100 km**. "we have
  restricted our coding efforts to transfers of territory larger than
  100 × 100 km, as done in the previous version of CShapes. This
  threshold causes us to exclude a total of 138 smaller territorial
  changes identified by the Territorial Change Dataset in the
  post-1886 period" (p.150). **Critical for WHEP**: the 1922 Silesia
  Plebiscite (9,702 km² Germany ← Poland) and the 1929 Peru-Chile
  treaty (8,498 km² to Chile) are both named as missed changes
  (p.150–151). A WHEP polity whose existence depends on a sub-10,000 km²
  transfer cannot rely on CShapes and must cite a different source.
- **Wartime rule:** "we also excluded wartime territorial changes,
  unless they were made permanent in treaties signed after the war"
  (p.151). The date of change is "the date of postwar agreements...
  as the date of the change" (p.151).
- Colonial border detail came from Biger 1995 (*Encyclopedia of
  International Boundaries*) and Brownlie & Burns 1979 (*African
  Boundaries*) "to address" the Territorial Change Dataset's
  COW-independent-states-only limitation (p.151).

### §geocoding — how the maps were drawn (p.151)

- Border changes were coded "in reverse chronological order. In other
  words, we started with the earliest observation in the original
  CShapes dataset, and adjusted country polygons to represent borders
  before each territorial change" (p.151). For countries with no
  changes in the period, "we simply backdated their borders to 1886"
  (p.151). **Implication:** a static polygon back to 1886 is literally
  a copy of the later polygon. For a WHEP polity whose borders *did*
  shift in ways CShapes missed (sub-threshold or unrecorded), this
  backdating is silently wrong.

## Known limitations

Drawn from the paper itself, not from downstream summaries:

1. **CShapes is not a sub-national dataset.** "CShapes is limited to
   international boundaries and does not map sub-national
   administrative boundaries. For the latter, other datasets such as
   GADM or Euratlas can be used" (p.146). WHEP's subnational polity
   rows must not cite CShapes for their polygon.
2. **1886 is a hard floor.** Anything before 1886 is out of scope of
   the paper entirely. WHEP's pre-1886 European coverage comes from
   the CShapes-Europe extension, which is a *different* dataset and
   needs its own source file.
3. **2019 is a hard ceiling.** Confirmed by `docs/06` — post-2019
   changes rely on `whep_fixes`, not CShapes.
4. **Two coding versions exist.** Any claim "CShapes says X" is
   incomplete without specifying COW-based or GW-based. The repo
   appears to load one version but does not record which.
5. **Sub-250k-population dependencies are excluded.** (p.148)
6. **Sub-100×100 km transfers are excluded.** (p.150) Lint rule: if
   a WHEP row hinges on a small 19th/20th-century territorial swap,
   CShapes is the wrong source.
7. **De facto states are not coded separately.** (p.149) Abkhazia,
   South Ossetia, Biafra, RSK, Transnistria etc. must be sourced
   elsewhere if WHEP tracks them.
8. **Wartime transient borders are not coded.** (p.151)
9. **Placeholder/undefined-border polygons are flagged.** (p.150) WHEP
   lint should surface every polity whose CShapes record carries the
   dummy-variable flag.
10. **Backdated borders are copies, not observations.** (p.151) 152 of
    the 249 units have a single polygon for the whole 1886–2019 window;
    for these, the "1886 polygon" is the same geometry as the latest
    observation.

## Which version is on disk (2026-04-11)

Direct inspection of `data/geodata/cshapes2_full.gpkg` confirms this
is the **COW-based** distribution. Two pieces of evidence:

1. The `cshapes` layer has `cowcode` but no `gwcode` column.
2. Canada (`cowcode=20`) is coded as `colony` from 1886-01-01 to
   1920-01-09 and `independent` from 1920-01-10, matching COW's
   explicit 1920 independence date `[§coding-states]`. Under GW the
   date would be 1867.

See `wiki/log.md` 2026-04-11 `decision-cshapes-is-cow-based`. Every
polity page in this wiki that cites CShapes 2.0 inherits COW's
state-system criteria (diplomatic ties to two major powers,
population threshold, etc.) for its independence dating.

**Reproducibility:** `REPRODUCIBILITY.md` attributes the generation
of `cshapes2_full.gpkg` to `R/01_build_master_db.R`, but that script
does not call `cshapes::cshp()` and does not write any gpkg. On
2026-04-11 I reproduced the file from scratch with

```r
library(cshapes); library(sf)
cs <- cshp(useGW = FALSE, dependencies = TRUE)  # cshapes v2.0
st_write(cs, "cshapes_cow_fresh.gpkg")
```

and compared feature-by-feature against the on-disk
`data/geodata/cshapes2_full.gpkg`. The match is exact:

- 805 rows in both
- Identical column set (no `gwcode`)
- All (cowcode, country_name, start, end, status) tuples identical
- All 805 geometries `st_equals`-identical

So the on-disk file is bit-equivalent in content to the R package
default for COW + dependencies. This also validates:

- the COW finding (the R call explicitly passes `useGW = FALSE`);
- the 1893 Luxembourg start (it is a canonical cshapes output, not
  a local corruption);
- the full row set, meaning lint and auditing can be redone against
  a freshly regenerated gpkg at any time.

A future reproducibility fix should add a one-line script (e.g.
`R/00b_fetch_cshapes.R`) containing exactly the three lines above and
update `REPRODUCIBILITY.md` to point at it. Tracked in
`log.md 2026-04-11 cshapes-reproducibility-verified`.

## License and redistribution

- Article: SAGE open access under CC-BY (journal page, p.144).
- Dataset: "CShapes 2.0 is freely available for academic and other
  non-commercial purposes" (p.147).
- The local PDF is not redistributed; see `wiki/sources/pdfs/README.md`.
