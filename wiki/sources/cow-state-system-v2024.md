---
source_slug: cow-state-system-v2024
title: "Correlates of War: State System Membership List, v2024"
author: Correlates of War Project
year: 2024
url: https://correlatesofwar.org/data-sets/state-system-membership/
access_date: 2026-04-11
type: dataset
coverage: Global list of states in the international system, 1816–2024
citation: "Correlates of War Project. 2024. \"State System Membership List, v2024.\" Online, http://correlatesofwar.org."
local_data:
  - wiki/sources/data/cow-v2024/statelist2024.csv
  - wiki/sources/data/cow-v2024/system2024.csv
local_codebook: wiki/sources/pdfs/state-system-membership-codebook-v2024.pdf
codebook_sha256: d4be488fb2802ce482d21dba29d0e2ffafc110e5ea23e229017dafa0f0277177
statelist_sha256: 722153b45eda9c39826a04aab80ca7b29a8b1cfdfe5d92714503420555675484
system_sha256: 1186f0c30fe549967bb5d33d0084ca47d6ab8215e298ec5ad83d34b6dbb04ea8
---

# Correlates of War State System Membership List, v2024

## Why it was ingested

Because WHEP's polity definition is territorial-economic, not
state-system-membership
[log decision-whep-polity-definition](log.md#decision-whep-polity-definition), COW is not WHEP's
primary source for start/end dates. But COW *is* the definition that
CShapes 2.0 uses (`useGW=FALSE`), so every claim about CShapes's
dating implicitly cites COW. Having COW as a first-class source lets
the wiki cite diplomatic-status facts directly instead of routing
them through CShapes, and lets polity pages separate "WHEP start
year" from "COW state-system entry date" cleanly under the polity
definition rule.

## What it adds

### overview
*what the dataset is (codebook p.1).*

- "This data set contains the list of states in the international
  system as updated and distributed by the Correlates of War
  Project. Version 2024 extends the temporal domain of the system to
  December 31, 2024."
- The distribution includes six files; WHEP loads two of them:
  - `states2024.csv` — "the entry and exit dates of states, country
    codes, and abbreviations" (codebook p.1). 244 data rows (plus
    header), one row per tenure period. States that left and
    re-entered have multiple rows.
  - `system2024.csv` — "year-by-year list of state system membership
    (and so, is a base country-year dataset). A state is listed as
    being a member of the state system if it is recorded in
    `states.csv` as present in the system at any time during the
    relevant year" (codebook p.2). 17,511 data rows.
- The other four distribution files (`majors2024`, `nondirected...`,
  `directed...`, codebook, FAQ) are not currently ingested.

### schema
*column definitions (codebook p.2).*

`statelist2024.csv` columns:

| column | meaning |
|---|---|
| `stateabb` | COW state abbreviation |
| `ccode` | COW state number |
| `statenme` | Primary COW state name |
| `styear, stmonth, stday` | Beginning year / month / day of state tenure |
| `endyear, endmonth, endday` | Ending year / month / day of state tenure |
| `version` | Data file version number |

`system2024.csv` columns: `ccode`, `stateabb`, `statenme`, `year`,
`version`.

### inclusion
*how COW decides who is in.*

The codebook itself does not restate the membership criteria (it is
a schema/version reference, not a conceptual overview). The criteria
are stated in the founding papers and re-stated in
[cshapes-2.0 §coding-states](cshapes-2.0.md#coding-states):

- Before 1920: "diplomatic recognition by Britain or France" and a
  population above 500,000.
- 1920 onward: "membership of the League of Nations or the United
  Nations" plus the 500,000 population threshold.
- Units that never meet these criteria never appear in COW, even if
  they exist as historical polities.

This is why the Papal States disappear after 1870, why Luxembourg
does not appear until 1920, and why many small African and Pacific
entities are absent entirely. These are features of COW's purpose
(interstate conflict analysis), not defects — but they mean COW is
wrong to cite as a general polity list.

### key-dates
*directly-citable dates.*

A few dates that are load-bearing for WHEP polity pages and came out
of direct inspection of `wiki/sources/data/cow-v2024/statelist2024.csv`.
Any of these can be cited as [cow-state-system-v2024 §key-dates]:

- **Luxembourg (LUX, ccode=212)**:
  `1920-11-15 → 1940-05-10` and `1944-09-10 → 2024-12-31`. Two
  tenure rows, with a gap during German occupation. Pre-1920 and
  the 1940–1944 window are absent entirely — COW does not consider
  Luxembourg a state system member before 1920-11-15 (no League of
  Nations membership until post-WWI) and does not consider it a
  state system member during occupation.
- **Canada (CAN, ccode=20)**: `1920-01-10 → 2024-12-31`. Single
  tenure row starting 1920-01-10, which is the acid-test date the
  CShapes paper names for distinguishing COW (1920) from GW (1867)
  [cshapes-2.0 §coding-states](cshapes-2.0.md#coding-states).
- **Cuba (CUB, ccode=40)**: `1902-05-20 → 1906-09-25` and
  `1909-01-23 → 2024-12-31`. The 1906–1909 gap is the Second U.S.
  Occupation.
- **Haiti (HAI, ccode=41)**: `1859-01-01 → 1915-07-28` and
  `1934-08-15 → 2024-12-31`. The gap is the U.S. occupation of
  Haiti 1915–1934.

### version-history
*what changed (codebook p.3–4).*

The codebook records dated revisions from earlier versions, most
important for WHEP:

- v2016: end dates for all states in existence in 2016 extended to
  2016-12-31; major-powers Russia abbreviation changed from `USR`
  to `RUS`.
- v2011: new member state South Sudan (ccode=626, start 2011-07-09).
- v2008.1: file format updated so variable names are at most 8
  characters long, no spaces (still the current convention).
- v2004.1: start-date corrections for 17 states, including
  substantive ones like Brazil (**1/1/1826 → 9/7/1822**, i.e. COW
  moved Brazil's state-system entry back four years to the actual
  declaration of independence), Afghanistan
  (**1/1/1920 → 8/8/1919**), and Panama (**1/1/1920 → 11/3/1903**).
  These are important for any WHEP polity page citing COW as
  secondary evidence — the COW start year may have moved between
  vintages.

## Known limitations

1. **COW is a state-system list, not a polity list.** Entities that
   exist historically and produce trade data but do not meet COW's
   recognition + population criteria are absent by design.
   Luxembourg 1839–1919, most colonial dependencies, Tibet, the
   Orange Free State, the Papal States post-1870, pre-1822 Brazil,
   and many others. Under the WHEP polity definition
   [log decision-whep-polity-definition](log.md#decision-whep-polity-definition) this is not a
   defect; it simply means COW cannot justify or refute a WHEP
   start/end year on its own.
2. **Changing vintages.** Start/end dates can and do change between
   COW versions (see §version-history). Any page citing
   [cow-state-system-v2024](cow-state-system-v2024.md) is citing v2024 specifically; a later
   vintage may supersede it and will need its own source file, not
   an edit of this one.
3. **Day precision is uneven.** Many rows use `1` for `stmonth` and
   `stday` (i.e. 1 January) when the exact date is unknown or when
   the entry is based on a year-granularity source. Do not read
   January-1 values as actual January-1 events.
4. **No spatial component.** COW tells you whether a state is in the
   system, not where its borders are. For borders, use CShapes.
5. **Citation obligation.** COW asks users to cite the dataset (see
   frontmatter `citation` field). Any paper or analysis downstream
   of this wiki that rests on COW claims should include this
   citation.

## License and redistribution

Distributed freely from correlatesofwar.org with a citation request
rather than a no-redistribution clause. The codebook's only
restriction is "We ask users of the data set to cite this data set
as follows..." (codebook p.1). The two CSVs are committed to the
repo at `wiki/sources/data/cow-v2024/` so the wiki is self-contained;
the codebook PDF is under `wiki/sources/pdfs/` (gitignored,
re-fetchable from the URL above).
