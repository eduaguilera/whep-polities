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

## Onboarded through 00_intake.py (issue 26)

Registration made the source citable; it did not make it *testable*. Only
`consolidated_layer_b.parquet` (5 sources) and, by a separate code-keyed
matcher, FAOSTAT had ever been through
[00_intake.py](../../pipelines/polity-autoimprove/00_intake.py), so every
assertion in the ledger came from one provenance. Federico-Tena is now the
second independent source through the same door.

`00_intake.py` needed no changes. The preparation is
[prepare_federico_tena.py](../../pipelines/polity-autoimprove/prepare_federico_tena.py),
which reshapes the xlsx into an intake table and nothing else:

```bash
python3 pipelines/polity-autoimprove/prepare_federico_tena.py
python3 pipelines/polity-autoimprove/00_intake.py \
  --input pipelines/polity-autoimprove/state/federico_tena_intake.csv \
  --label-col polity_name --year-col year --item-col item \
  --value-col value --unit-col unit --source-tag federico_tena \
  --out pipelines/polity-autoimprove/state/assertions_federico_tena.json
```

Both outputs are derived per-run artifacts and are gitignored, like
`assertions.json`.

### what the assertions are

Because what is staged is documentation, the claim this source can make is a
**coverage** claim — "Federico-Tena reports a series for a territory called X
in year Y" — so the intake table is one row per (polity, series, year) over each
series' inclusive window: 48,569 rows for 243 polities, years 1800–1940, items
`imports` (21,210 rows), `exports` (13,018), `population` (14,174). Expanding
the windows year by year is the point: it is what makes year containment
testable, since every year the source reports has to land inside some polity's
span. Plus 167 rows carrying the one magnitude the source has, the 1913
population in thousands, keyed as its own item `population_1913` so its median
is not mixed with the value-less coverage rows.

The xlsx is read rather than
[polities.csv](../../data/external/federico_tena/polities.csv) because the CSV
is a lossy extract of the same sheet — see *Known limitations*.

### measured result, 2026-08-17

| | |
|---|---|
| rows in | 48,569 |
| routed by the deterministic pass | 32,870 (**67.7%**) |
| assertions produced | **270** — 240 `pending`, 30 `banked_legacy` |
| distinct candidate polities | 269 |
| labels that never route (no alias, no name, no iso) | **76** (9,822 rows) |
| labels that route but with years outside the candidate's span | **66** (5,877 rows) |

For scale, layer B measured the same way on the same day — label only, without
the `--iso-col` and `--prior-code-col` its production run gets and this source
cannot supply — routes **88.9%** of 192,670 rows into 994 assertions. So
Federico-Tena is a materially harsher test, which is the point of onboarding it.

Routing is *low by design of the comparison*: this is a pre-1938,
colonial-granular trade source read against a polity set built mostly from
20th-century data, and it names reporting units — Trucial sheikhdoms, Central
Asian khanates, pre-Confederation Canadian provinces — that no later source
does. The 30 `banked_legacy` assertions are label-level verdicts inherited from
layer B (Angola, Argentina, Canada, Egypt, Poland, South Africa segments and
others); none of the 240 pending ones has been verified, and **verification is
not done here** (see *what is left open*).

49 labels split across more than one candidate polity, which is the deterministic
pass tiling a long Federico-Tena window across a WHEP chain — `china` into six
segments 1800–1938, `ethiopia` into six ending in `AOI-1936-1941`, `siam` into
five. Those segment boundaries are exactly what a verifier has to accept or
reject.

Passing `--aggregate-col is_aggregate` drops the four umbrella rows
(`British settlement Oceania`, `French Settlements in Oceania`,
`German colonies Oceania`, `US settlement Oceania`), 867 rows, and raises
routing to 68.9%. The default run keeps them, so their coverage is measured and
their status is decided by verification (`not_a_polity`) rather than by the prep
script.

### the 76 labels that never route

This is the harvest the issue predicted: a source with a different provenance
finds different gaps. Hand-checked against `data/final/polities_database.csv`,
they fall into three kinds — **and the kind is a screen, not a verdict**:

**(A) a WHEP polity plainly covers the territory; the label is an alias gap.**
`Dutch Guayana` 1800–1938 → `SUR-1886-1954` *Dutch Guiana* (spelling);
`Gold Coast` 1817–1938 → the `GHA-1821-1888`/`GHA-1888-1898`/`GHA-1898-1957`
chain; `German East Africa (Tanganyika)` → `TAN-1891-1920`;
`Nyasaland Protectorate (Malawi)` → `MWI-1891-1953`;
`Italian Libia Cyrenaica (Lybia)` → the `LBY-1912-1919`… chain;
`Zanzibar` → `ZNZ-1890-1963`; `Newfoundland` → `NFL-1907-1949`;
`Aden` → `ADE-1839-1963`; `St. Lucía` → `LCA-1838-2025`;
`St. Vincent` → `VCT-1800-1833`/`VCT-1833-2025`; `Oman` → `OMN-1856-2025`;
`St. Helena` → `SHN-1834-1967`; `Germany/Zollverein` → the
`DEU-1800-1866` *Prussia* chain; `Leeward Islands (…)` → `BLI-1833-1960`;
`Dutch West Indies (Netherland Antilles)` → `ANT-1816-1961`;
`British Bechuanaland` → `BEC-1885-1966`; `Mayotte and Noissi-be` →
`MYT-1800-2025`.

**(B) the polity exists but starts later than the Federico-Tena window**, so
even with an alias the early years would land in bucket (B)'s sibling below:
`Zanzibar` 1800–1938 vs `ZNZ-1890-1963`; `Newfoundland` 1816–1938 vs
`NFL-1907-1949`; `Gold Coast` from 1817 vs `GHA-1821-1888`. These are the same
question the 66 `year_uncovered` labels ask.

**(C) no WHEP polity for the territory at all.** The largest coherent groups:
the Trucial sheikhdoms reported separately (`Abu Dhabi`, `Ajman`, `Sharjah`,
`Fujairah`, `Umm al Qawain`, `Ras al Khaimah` — WHEP has only
`ARE-1892-2025`); the Central Asian khanates (`Bukhara` to 1920, `Khiva` and
`Kokand`, `Badakhshan`, `Herat`); `Tibet` and `Sikkim`; the Malayan customs
units (`Straits Settlement` 1826–1922, `Federated Malay States` 1895–1922 —
WHEP's Malaysia chain starts 1946 and Singapore's 1946); the Chinese leased
territories (`Kiautchou` 1898–1922, `Kwantung (Port Arthur)`,
`Kwang-Chou-Wan`); the pre-Confederation Canadian provinces (`Ontario`,
`Lower Quebec`, `New Brunswick`, `Nova Scotia Cape Breton Isl.`,
`Prince Edward Island`, `British Columbia`, `Vancouver´s Island` — WHEP has
only the umbrella `CAN-1800-1866`); the Boer republics (`Orange Free State`
1848–1900, `Transvaal` 1856–1902 — `CAP-1800-1895` exists, these do not);
`Crete` 1898–1913, `Ionian islands` 1815–1862 and `Dodecanese Is.` 1912–1938;
`British Protectorate (British Somaliland)`; `Sabah (British Borneo)`;
`Ceuta Y Melilla`; and a dozen Pacific islands (`Midway`, `Wake`, `Palmyra`,
`Gambier`, `Marquesas`, `Society Islands (Tahiti)`, `Gilbert and Ellice`,
`New Hebrides`, `Bonin`).

An automated name-token screen finds a same-token WHEP polity for 36 of the 76
and none for 40. It is crude in both directions — it pairs `Danish Virgin
Islands` with the *British* Virgin Islands and misses `Dutch Guayana` →
*Dutch Guiana* on spelling — so the buckets above are the hand-checked reading
of the same list, and neither is a verdict.

### what the 66 `year_uncovered` labels are

These route on the label but observe years the candidate chain does not cover:
`Russia/USSR` 1800–1938, `Bermuda` 1800–1938, `CapoVerde` 1800–1938,
`Serbia/Yugoslavia` 1816–1938, `Persia (Iran)` from 1829, `India` 1800–1892,
`Ottoman Empire/Turkey` 1800–1912. Two causes are mixed and must not be
conflated:

- **The source's own back-extrapolation.** Export and population series are
  routinely extended behind the import series (`Cameroon (Kamerun)` imports
  start 1884, exports 1850; `Belgian Congo` 1885 vs 1850), and this page's
  *Known limitations* already warns that a start year is evidence of when the
  compilers could *estimate*. Unrouted rows are 1,787 `imports`, 1,869
  `exports` and 2,204 `population` — so the reconstructed series carry the
  majority of the year gaps, and an uncovered year there is weak evidence
  about WHEP.
- **Genuine early-19th-century thinness in the polity set**, which is what the
  `imports` share points at.

Separating the two per label is verification work, not screening work.

### what is left open

- **240 pending assertions are unverified.** Chunking them through
  `verify_assertions.workflow.js` (~100/run) and applying the verdicts with
  `apply_verdicts.py` is the remaining half of issue 26. Nothing in this repo
  has been re-routed, aliased or re-dated on the strength of this source; no
  alias row and no polity was created here.
- **No `source_conventions.csv` entry was added.** Two candidates are visible
  from the notes (the four Oceania umbrellas pool named territories; the 1913
  population column is dated to 1913 under *later* borders, which is why
  `estonia`, `latvia`, `lithuania`, `austria` and `ireland` each produced a
  one-year 1913 assertion against a pre-independence polity such as
  `EST-1800-1918`). Both are conclusions a verifier should reach and bank with
  evidence, and `validate_source_conventions.py` holds entries to that
  standard, so neither was asserted here.
- **Which bucket-(C) territories deserve a polity row** is a judgement about
  WHEP's scope, not something this intake can settle: a Federico-Tena row is a
  *reporting unit*, and the page already warns that a WHEP row must not be
  created merely because one exists.

## Known limitations

- **`polities.csv` is a LOSSY extract of the xlsx; read
  `federico_tena_polities.xlsx` instead.** Measured 2026-08-17 while preparing
  the intake table: the sheet *List of trading polities* carries eight numeric
  columns per polity, the CSV carries five. `population_end` and
  `population_estimate` are empty in **all 243** CSV rows, and the sheet's 1913
  population (in thousands, given for **167** polities) and its
  "Trade sample serie included" column are absent altogether. The three windows
  the CSV does carry agree with the sheet row for row. Consequence for the count
  quoted above: "330 of the series ending in 1938" counts the CSV's 389 import
  and export ends; with the 146 population ends the sheet also has, it is
  **468 of 535** series ends, 191 of the 243 import series among them. Nothing
  above is withdrawn — the CSV is right where it is present — but a new
  measurement should come from the xlsx.
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
