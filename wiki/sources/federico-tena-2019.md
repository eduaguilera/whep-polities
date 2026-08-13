---
source_slug: federico-tena-2019
title: Federico-Tena World Trade Historical Database — polity list, country notes and bibliography (January 2019)
author: Giovanni Federico and Antonio Tena-Junguito
year: 2019
url: NA (staged locally at data/external/federico_tena/; no canonical URL is recorded in this repo — see Known limitations)
access_date: 2026-08-13
type: dataset
coverage: 243 trading polities, imports and exports 1800–1938 (a few series to 1940), five continents
---

# Federico-Tena World Trade Historical Database (January 2019)

## Why it was ingested

Eight polity pages already reason from "Federico-Tena", and
[nzl-1840-2025](../polities/nzl-1840-2025.md) carried a citation to a
`federico-tena.md` that had never been written (whep-polities issue 5).
Two pages even named it in frontmatter under two different slugs
(`federico_tena`, `federico-tena-2019`). The reference material is on disk
and has been for months, so the honest fix is to register it as a source
rather than to keep citing a file that does not exist. This page is that
registration; `federico-tena-2019` is now the single slug.

The database is also the repo's main authority on *which territories
reported trade separately* before 1938, which is the same question WHEP
asks when deciding whether a territory earns its own polity row.

## What it adds

### scope

The staged extract lives in
[data/external/federico_tena/](../../data/external/federico_tena/) and is
not the trade values themselves but the dataset's documentation:

| file | rows | what it is |
|---|---|---|
| `polities.csv` | 243 | one row per trading polity: continent, name, first/last year of the import series, of the export series and of the population series, plus a note |
| `country_notes.csv` | 152 | the compilers' prose note per reporting country: which archival series was used, how gaps were interpolated, which price index deflates it |
| `bibliography.csv` | 316 | the January 2019 reference list |

Measured from `polities.csv` on 2026-08-13: **243 polities** — Asia 59,
Americas 52, Africa 50, Europe 45, Oceania 37. All 243 carry an import
series; 146 also carry an export series. Series starts run 1800–1932 and
ends 1833–1940, with **330 of the series ending in 1938**. So "1800–1938"
describes the database as a whole, not every polity: each polity's own
window is in its row, and a WHEP page should quote that window rather than
the global one.

### polity-granularity

Federico-Tena splits and pools territories on a reporting-statistics test
very close to WHEP's, which is why it is useful here:

- Small territories are estimated jointly with an umbrella polity, stated
  in the note — e.g. Fiji, Gilbert and Ellice, Pitcairn, Solomon Islands,
  Tonga and Tokelau all read "Joint estimation British settlement Oceania".
- Umbrella polities are themselves rows: `British settlement Oceania`
  (imports 1839–1938, exports 1850–1938), `French Settlements in Oceania`
  (1844–1938), `German colonies Oceania` (1884–1938), `US settlement
  Oceania` (1859–1938).
- Pre-federation and pre-unification units are separate rows that end at
  the union: Queensland (imports 1859–1900), Victoria (1853–1900), South
  Australia (1838–1900), Western Australia (1838–1900), Van Diemen's Land
  (1828–1900) all stop where `Australia Commonwealth` picks up
  (imports 1901–1940, exports from 1826).

### oceania-cook-islands

Verbatim from the staged files:

- `polities.csv`: `Oceania, Cook Island, imports 1893–1901`, note
  "1901-1938 New Zealand; Joint estimation New Zealand".
- `polities.csv`: `Oceania, Niue Island, imports 1900–1901`, note "annexed
  to New Zealand 1901-1938; Joint estimation New Zealand".
- `polities.csv`: `Oceania, Tokelau Island, imports 1877–1938`, note
  "British colony; administered New Zealand after 1926 Joint estimation
  with British Settlement Oceania".
- `country_notes.csv`, *British Settlements Oceania*: "The British Western
  Pacific Territories was the name of a British colonial entity, created in
  1877 ... Composed by: Fiji (1877 to 1952) ...; **Cook Islands (1893 to
  1901)** — now a self-governing state in free association with New
  Zealand; ...; **Savage Island (1900 to 1901)** — now Niue ...;
  **Union Islands (1877 to 1926)** — now Tokelau, a dependent territory of
  New Zealand."
- `country_notes.csv`, *New Zealand*: "New Zealand, originally part of the
  colony of New South Wales, became a separate Colony of New Zealand on
  1 July 1841. ... In 1907, at the request of the New Zealand Parliament,
  King Edward VII proclaimed New Zealand a dominion within the British
  Empire. We get series of trade at current prices in british sterling
  pounds from 1842 onwards from Bloomfield (1984 tab VII.2) and we
  extrapolate exports to 1826 following the Australian series."

So Cook Islands trade is inside `British settlement Oceania` for 1893–1901
and inside New Zealand from 1901 — which is what
[nzl-1840-2025](../polities/nzl-1840-2025.md) says. What Federico-Tena does
**not** contain is any row-level "trade with cook islands" series; that
label belongs to the IIA yearbook footnotes (see *Known limitations*).

### aof-and-french-west-africa

Already quoted on [aof-1895-1960](../polities/aof-1895-1960.md) from the
same files: the AOF series runs 1895–1938 and "Since 1892 we use the data
from France. Statistical Yearbook (1939) referring to Dahomey, Cote de
Ivory, French Niguer, High Senegal and Niguer until 1920 and to the French
West Africa thereafter", with French Togoland's trade included from 1922.

Polity slugs that cite this source:
[nzl-1840-2025](../polities/nzl-1840-2025.md),
[aof-1895-1960](../polities/aof-1895-1960.md),
[reu-1816-1946](../polities/reu-1816-1946.md).

## Known limitations

- **This is the documentation, not the data.** No trade values are staged
  in the repo, so no claim about a *magnitude* can be sourced here — only
  claims about coverage windows, pooling and compilation method. A page
  citing this source for a number is citing the wrong thing.
- **The 21 "trade with cook islands" rows are not Federico-Tena.** The
  nzl page attributed them here; they are IIA yearbook footnote rows, and
  the count is verifiable in
  [pipelines/polity-autoimprove/state/iia_territorial_notes.csv](../../pipelines/polity-autoimprove/state/iia_territorial_notes.csv):
  `new zealand,trade with cook islands,1928,1938,21`. The page has been
  corrected to cite that file.
- **Its polities are reporting units, not territories.** Umbrella rows such
  as `British settlement Oceania` pool a dozen scattered island groups and
  interpolate 1915–1921 from the French Settlements series; a WHEP row must
  not be created merely because a Federico-Tena row exists, nor its dates
  copied without reading the note.
- **Heavily reconstructed.** Many series are back-extrapolated from a
  neighbour or deflated with a proxy price index (Angola's exports are
  extended to 1828 "with the series of current exports from Ghana"). Start
  years are therefore evidence of *when the compilers could estimate*, not
  necessarily of when a customs administration existed.
- Spelling in the staged CSVs is the compilers' own ("French Niguer",
  "Dutch new Guinea", "joit estimate"); quotes above preserve it.
- The published version is January 2019; a later revision may change
  windows. Treat this file as the 2019 snapshot and ingest a new source
  file if a later release is used.
- **No canonical URL is recorded.** The staged CSVs carry no provenance
  header and no download URL is documented anywhere in this repo, so the
  frontmatter `url` deliberately says NA rather than a guessed handle. The
  bibliography names Federico and Tena-Junguito's own working papers
  (Instituto Figuerola, UC3M) as the underlying method references. Whoever
  next touches this source should record where the files came from.
