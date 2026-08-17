---
source_slug: federico-tena-2019
title: Federico-Tena World Trade Historical Database — polity list, country notes and bibliography (January 2019)
author: Giovanni Federico and Antonio Tena-Junguito
year: 2019
url: NA (staged locally at data/external/federico_tena/; no canonical URL is recorded in this repo — see Known limitations)
access_date: 2026-08-13
type: dataset
coverage: 243 trading polities dated 1800–1940, of which 146 carry an import and export series, 1800–1938; five continents
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
| `polities.csv` | 243 | one row per trading polity: continent, name, the polity's own first/last year, the first/last year of its import series and of its export series, plus a note |
| `country_notes.csv` | 152 | the compilers' prose note per reporting country: which archival series was used, how gaps were interpolated, which price index deflates it |
| `bibliography.csv` | 316 | the January 2019 reference list |

Measured from `polities.csv` on 2026-08-13: **243 polities** — Asia 59,
Americas 52, Africa 50, Europe 45, Oceania 37. So "1800–1938" describes the
database as a whole, not every polity: each polity's own window is in its row,
and a WHEP page should quote that window rather than the global one.

**Corrected 2026-08-17 (issue 26): only 146 of the 243 polities carry a trade
series at all, and none carries a population series.** The 2026-08-13 reading —
"all 243 carry an import series; 146 also carry an export series", and a
population series alongside — mistook the sheet's column GROUPS. Header rows 5-6
of *List of trading polities* name them: cols 1-2 are the **polity's own**
Starting/End years, 3-4 **Imports**, 5/7 **Exports**, col 9 the **1913
population** as a single value, col 11 "Trade sample serie included". Cols 1-2
are filled for all 243; cols 3-4 and 5/7 for exactly **146**. So 97 polities are
listed with a period and no trade series, and the "population series" never
existed — it was the export window read one group late. See
*Known limitations* and *what the assertions are*.

### polity-granularity

Federico-Tena splits and pools territories on a reporting-statistics test
very close to WHEP's, which is why it is useful here:

- Small territories are estimated jointly with an umbrella polity, stated
  in the note — e.g. Fiji, Gilbert and Ellice, Pitcairn, Solomon Islands,
  Tonga and Tokelau all read "Joint estimation British settlement Oceania".
- Umbrella polities are themselves rows: `British settlement Oceania`
  (polity 1839–1938, trade 1850–1938), `French Settlements in Oceania`
  (polity 1844–1938, trade 1850–1938), `German colonies Oceania`
  (polity 1884–1938, trade 1850–1938), `US settlement Oceania`
  (polity 1859–1938, **no trade series**).
- Pre-federation and pre-unification units are separate rows that end at
  the union: Queensland 1859–1900, Victoria 1853–1900, South Australia
  1838–1900, Western Australia 1838–1900 and Van Diemen's Land 1828–1900 all
  stop where `Australia Commonwealth` (1901–1940) picks up. Corrected
  2026-08-17: those five are polity windows, not import series — **none of the
  five carries a trade series at all**, and `Australia Commonwealth`'s own trade
  series runs 1826–1938, i.e. it is back-cast across the whole colonial period
  that the five separate rows describe. The granularity is in the polity list;
  the trade values behind it are not.

### oceania-cook-islands

Verbatim from the staged files:

- `polities.csv`: `Oceania, Cook Island, 1893–1901`, note
  "1901-1938 New Zealand; Joint estimation New Zealand".
- `polities.csv`: `Oceania, Niue Island, 1900–1901`, note "annexed
  to New Zealand 1901-1938; Joint estimation New Zealand".
- `polities.csv`: `Oceania, Tokelau Island, 1877–1938`, note
  "British colony; administered New Zealand after 1926 Joint estimation
  with British Settlement Oceania".

(Those three year pairs sit in the CSV's `imports_start`/`imports_end` columns
and were quoted as import series until 2026-08-17. They are the polities' own
windows — all three rows are empty in every trade column, consistent with the
notes' "joint estimation". The CSV's column NAMES are shifted one group; see
*Known limitations*.)
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
series' inclusive window: **27,359 rows** for 243 polities, years 1800–1938,
items `imports` (13,018 rows) and `exports` (14,174). Expanding the windows year
by year is the point: it is what makes year containment testable, since every
year the source reports has to land inside some polity's span. Plus 167 rows
carrying the one magnitude the source has, the 1913 population in thousands,
keyed as its own item `population_1913` so its median is not mixed with the
value-less coverage rows. The source's own first/last year for the polity rides
along as `ft_polity_start`/`ft_polity_end`, which `00_intake.py` does not read:
it is not a coverage claim, it is the source's independent dating of the
reporting unit, and it is what the *back-cast* finding below is measured against.

**Corrected 2026-08-17 (issue 26): the first version of this table had 48,569
rows and 44% of them were fabricated.** Reading the column groups one late (see
*scope*) meant the polity-existence window was emitted as an `imports` series
for all 243 polities — including the 97 that have no trade series at all — while
the real import series was labelled `exports` and the real export series was
labelled `population`, a measure the sheet does not contain. The correction is
confirmed against dates the misreading contradicts outright: Korea's series
starts 1876 (Treaty of Ganghwa) and not 1800, when Korea was closed to foreign
trade; Japan 1860 (opened 1859) not 1800; and China 1830, Philippines 1810,
Iceland 1849, Bulgaria 1879, Ireland 1922, Austria / Czechoslovakia / Estonia /
Latvia / Lithuania 1920, Poland 1922, Syria-and-Lebanon 1921 and
Palestine/Jordan 1920 all land on the exact year each became a separate customs
reporter.

The xlsx is read rather than
[polities.csv](../../data/external/federico_tena/polities.csv) because the CSV
is a lossy extract of the same sheet — see *Known limitations*.

### measured result, 2026-08-17

Three states are shown because the middle one is the honest baseline: the first
column is what was published on 2026-08-17 before the column groups were
re-read, and comparing only the first and third would credit the alias work with
the mapping fix.

| | as first published | mapping fixed | + issue-26 aliases |
|---|---|---|---|
| rows in | 48,569 | 27,359 | 27,359 |
| routed by the deterministic pass | 32,870 (67.7%) | 18,765 (68.6%) | 21,155 (**77.3%**) |
| assertions produced | 270 | 228 | **269** |
| distinct candidate polities | 269 | 228 | 269 |
| labels that never route (no alias, no name, no iso) | 76 (9,822 rows) | 33 (4,504) | **32** (4,244) |
| labels that route but with years outside the candidate's span | 66 (5,877 rows) | 54 (4,090) | **37** (1,960) |

Both halves matter and they are different in kind. The mapping fix removed
21,210 rows that the source never reported, and with them **55 of the 142
unresolved entities** — every Trucial sheikhdom, every Central Asian khanate,
every pre-Confederation Canadian province, `Tibet`, `Sikkim`, `Straits
Settlement`, the Boer republics and a dozen Pacific islands. Those labels were
never data gaps: they are polities Federico-Tena lists **without any trade
series**, so nothing was going unrouted except a series that did not exist.
The list is still valuable as a polity list; it is not evidence of missing
coverage.

The aliases then routed 2,390 real rows that were genuinely unrouted.

For scale, layer B measured the same way on the same day — label only, without
the `--iso-col` and `--prior-code-col` its production run gets and this source
cannot supply — routes **88.9%** of 192,670 rows into 994 assertions. So
Federico-Tena is still the harsher test, which is the point of onboarding it,
and the gap is now 11.6 points rather than 21.2.

None of the 242 pending assertions has been verified, and **verification is not
done here** (see *what is left open*). The 27 `reopened` ones are label-level
verdicts inherited from layer B with no evidence hash (issue #8).

56 labels split across more than one candidate polity, which is the
deterministic pass tiling a long Federico-Tena window across a WHEP chain —
`china` into six segments 1800–1938, `ethiopia` into six ending in
`AOI-1936-1941`, `siam` into five, and now the five compound labels below.
Those segment boundaries are exactly what a verifier has to accept or reject.

Passing `--aggregate-col is_aggregate` drops the four umbrella rows
(`British settlement Oceania`, `French Settlements in Oceania`,
`German colonies Oceania`, `US settlement Oceania`), 537 rows — `US settlement
Oceania` contributes none, having no trade series — and raises routing to 78.9%.
The default run keeps them, so their coverage is measured and their status is
decided by verification (`not_a_polity`) rather than by the prep script.

### the five compound labels (issue 26)

Five rows write ONE reporting unit as two alternatives, and no alias matched a
slash-joined name. `norm()` turns the slash into a space, so each label reached a
family only by accident, through the external `common_names.csv` spelling table:
`russia ussr` landed on the USSR name family (1940–1991), `serbia yugoslavia` on
Serbia's (1913–), `ottoman empire turkey` on Türkiye's (1913–). That is why
three of the five read as `year_uncovered` rather than `unresolved` — the name
resolved and the SPAN was wrong — while `Germany/Zollverein` and
`Palestine/Jordan` reached nothing at all.

**The issue's own count of that split was wrong in both directions of the data.**
It said four of the five were `year_uncovered`; measured, three are, on the
broken table *and* on the corrected one.

Each is now split across its chain, one alias row per period, with
`year_end = polity end_year - 1` so consecutive rows do not touch — 28 rows
covering 885 of the 888 intake rows these five labels carry:

| label | source years | routed to | rows |
|---|---|---|---|
| `Russia/USSR` | 1800–1938 | the eight-segment `F228` chain, Russian Empire → RSFSR → USSR | 229 |
| `Germany/Zollverein` | 1821–1938 | `DEU-1800-1866` (Prussia) → … → `DEU-1938-1945` | 222 |
| `Serbia/Yugoslavia` | 1830–1938 | `SER-1816-1878` → `SER-1878-1913` → `SER-1913-1918` → the `F248` chain | 199 |
| `Ottoman Empire/Turkey` | 1830–1938 | the three `OTT` segments to 1911, then the `TUR` chain from 1913 | 197 |
| `Palestine/Jordan` | 1920–1938 | `PAL-1920-1948` | 38 |

Two territorial mismatches are recorded on the alias rows rather than hidden by
them, because an alias here is a *candidate* for verification and not a claim:

- **`Germany/Zollverein` 1834–1865 has no polity.** From 1834 the reporting unit
  is the customs union — Prussia plus most German states — and `DEU-1800-1866`
  is Prussia alone. Routing it to the DEU chain makes the mismatch a visible
  assertion instead of an unrouted label; whether a Zollverein polity is owed is
  left to verification, and none was created here.
- **`Palestine/Jordan` is Palestine AND Transjordan**, while `PAL-1920-1948` is
  Palestine west of the Jordan. Best-available routing, flagged `medium`.

Two rows are deliberately left unrouted:

- **1912 has no whole-empire Ottoman polity.** `OTT-1908-1912` ends at an
  exclusive 1912 and the `TUR` chain begins in 1913, so the year falls between
  them. The alias stops at 1911 rather than claiming a year past its target;
  the one-year hole is a finding this source surfaced and is not fixed here.
  (`TUR-1800-1913`, Turkey/Anatolia, does cover 1912 — but it is a smaller
  territory than the empire whose trade the series reports.)
- **`Palestine/Jordan`'s 1913-keyed population**, which the sheet's own note
  says is in fact a 1920 figure.

### the 76 labels that never route — 32 of them do not exist

**Read the correction first.** 44 of the 76 were artefacts of the column-group
misreading: they carry NO trade series, so the only rows attributed to them were
the fabricated existence-window series. The whole of bucket (C) below is affected
— every Trucial sheikhdom, every Central Asian khanate, `Tibet`, `Sikkim`,
`Straits Settlement`, `Federated Malay States`, the Chinese leased territories,
all six pre-Confederation Canadian provinces, both Boer republics, `Dodecanese
Is.`, `Oman`, `St. Helena`, `Aden` and the Pacific islands are listed by
Federico-Tena as polities and reported by it as nothing. Some retain a single
row, the 1913 population. **They remain interesting as a polity list and are no
longer evidence about coverage**, which is the opposite of how the first version
of this section read them.

The 32 that survive are led by `Danish Virgin Islands`, `Dutch West Indies
(Netherland Antilles)`, `Leeward Islands (…)`, `St. Vincent`, `St. Lucía`,
`Newfoundland`, `Gold Coast`, `Dutch Guayana`, `Ceuta Y Melilla`, `British East
Africa`, `German East Africa (Tanganyika)`, `Nyasaland Protectorate (Malawi)` and
`Zanzibar` — all in bucket (A), i.e. alias gaps against polities that exist.
Closing them is not attempted here (issue 26 scoped this work to the compound
labels and the `year_uncovered` group); the reading below is kept because bucket
(A) is unaffected by the correction.

Hand-checked against `data/final/polities_database.csv`, they fall into three
kinds — **and the kind is a screen, not a verdict**:

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

### what the `year_uncovered` labels are — resolved, 2026-08-17 (issue 26)

These route on the label but observe years the candidate chain does not cover.
There were 54 after the mapping fix, 4,090 rows. **The group is not a set of
period defects in the polity set, and separating its causes turned out to be
screening work after all**, because the source carries the field that separates
them: its own first/last year for each polity, which the corrected prep script
now passes through as `ft_polity_start`/`ft_polity_end`.

**Cause 1 — the label cannot reach the polity, because the early period is named
differently. 16 labels, 1,571 rows, all of them fixable by an alias and none of
them a gap.** Federico-Tena supplies no ISO column, so `matchlib` falls back to
exact normalised-name matching. Where a family's early row carries a different
`polity_name`, the label reaches only the late rows and the early years then read
as `year_uncovered` although the right polity is sitting in the same ISO family:

| label | uncovered years | the polity that was there all along |
|---|---|---|
| `Bermuda` | 1816–1938 | `BMU-1684-1968` *British Crown Colony of Bermuda* |
| `India` | 1800–1892 | `IND-1800-1886` / `IND-1886-1893` *British India* |
| `Persia (Iran)` | 1850–1938 | `IRN-1828-2025` *Iran* |
| `Finland` | 1812–1916 | `FIN-1809-1917` *Grand Duchy of Finland* |
| `Australia Commonwealth` | 1826–1900 | `AUS-1800-1901` *Australian Colonies (to 1901)* |
| `British Honduras (Belize)` | 1816–1885 | `BLZ-1800-1886` *Belize (to 1886)* |
| `Brunei` | 1889–1938 | `BRN-1888-2025` *Brunei Darussalam* |
| `Japan` | 1896–1938 | `JPN-1895-1945` *Japanese Empire* |
| `Tunisia` | 1830–1880 | `TUN-1800-1881` *Beylik of Tunis* |
| `Austria-Hungary` | 1830–1865 | `AUH-1800-1859` / `AUH-1859-1866` *Austrian Empire* |
| `Egypt` | 1850–1884 | `EGY-1820-1885` *Egypt with Sudan* |
| `Netherlands` | 1800–1829 | `NLD-1800-1830` *United Kingdom of the Netherlands* |
| `Colombia` | 1820–1829 | `COL-1800-1830` *Gran Colombia* |
| `Basutoland` | 1913 | `LSO-1886-1966` *Lesotho (1886-1966)* |
| `Mongolia` | 1913 | `MNG-1911-1921` *Bogd Khanate of Mongolia* |
| `Nigeria` | 1886–1913 | `NGA-1886-1914` *Colonial Nigeria* |

Four of these routings were already recorded in the alias registry for OTHER
sources and are simply repeated for this one — `Bermuda`→`BMU-1684-1968`
(fao1952, faostat), `India`→`IND-1800-1886`/`IND-1886-1893` (trade-sources),
`Japan`→`JPN-1895-1945` (fao1952), `Brunei`→`BRN-1888-2025` (faostat) — which is
independent corroboration that the reach failure, not the routing, was the
problem. Three are flagged `medium` because the polity's territory is wider than
the label: `EGY-1820-1885` includes Sudan, which the source reports separately
from 1850; `NLD-1800-1830` includes the future Belgium, which the source reports
separately from 1830; `COL-1800-1830` is Gran Colombia, and Venezuela and Ecuador
have their own rows from 1820.

Two labels in this shape are deliberately NOT routed, because the polity live in
the year is a **different territory** and routing would be worse than leaving the
row unmatched: `Poland` 1913 (the live row is `POL-1815-1918`, Congress Poland,
while the source's Poland is the 1918– state) and `British Cameroon` 1913 (the
live row is `GKM-1912-1916`, German Kamerun). One row each.

**Cause 2 — the source back-casts the territory behind its own dating of the
reporting unit. 35 labels, 1,779 rows, and not a defect in the polity set.** For
every one of these the source's `ft_polity_start` is LATER than the first year of
its own trade series, i.e. Federico-Tena is estimating the trade of the
geographic area before the customs unit it is named after existed. WHEP correctly
has no polity there, and routing the years to the later colony would place
pre-colonial trade on the colony's territory-year. The starts cluster on the
compilers' benchmark years, which is the tell:

    1850  Rwanda and Burundi (polity 1919), French Equatorial Africa (1910),
          Italian Somaliland (1908), British Malaya (1922), Rhodesia (1890),
          French Indochina (1887), Belgian Congo (1885), French Somaliland
          (1887), German South West Africa (1884), Madagascar (1882), Eritrea
          (1882), Sudan (1882), Guinea Bisau (1879), Cameroon (1884)
    1816-1830  Seychelles (1903), French West Africa (1895), Nigeria (1861),
          South Africa (1828), Italy (1861), Falkland Islands (1833),
          Peru/Bolivia (1825), Uruguay (1828), El Salvador/Guatemala (1821),
          Algeria (1831), Belgium (1831), Venezuela (1821), Cyprus (1879)
    1913  the population column, for polities the source itself dates later:
          Saudi Arabia (1924), Czechoslovakia (1918), Iraq (1921), Poland
          (1918), British Cameroon (1914), Syria and Lebanon (1918)

`Known limitations` already warned that "start years are evidence of *when the
compilers could estimate*". This is that warning, measured: 44 of the 243
polities have a trade series beginning before their own stated start, and they
account for essentially the whole residual `year_uncovered` group.

**Cause 3 — a genuine gap. One label, 179 rows.** `CapoVerde`: the source dates
the polity 1800–1938 and reports trade from 1850, and WHEP's only Cape Verde row
is `CPV-1975-2025`. This is the one residual case where the source's own dating
and WHEP's disagree in the direction that indicts WHEP. Issue 26 forbade creating
polities in this pass, so it is named and left open.

After the aliases, 37 `year_uncovered` labels remain over 1,960 rows: the 35
back-casts (1,779), `CapoVerde` (179) and `Ottoman Empire/Turkey`'s 1912 (2).

### what is left open

- **242 pending assertions are unverified.** Chunking them through
  `verify_assertions.workflow.js` (~100/run) and applying the verdicts with
  `apply_verdicts.py` is the remaining half of issue 26. 46 alias rows scoped to
  `source = federico_tena` now exist (28 for the compound labels, 18 for the
  name-reach labels); **no polity was created and no polity's span was changed**,
  and every one of those aliases is unverified candidate routing, which is what
  the assertions are for.
- **The 32 surviving never-route labels are untouched.** They are bucket-(A)
  alias gaps against polities that already exist — `Dutch Guayana` →
  `SUR-1886-1954`, `Gold Coast` → the GHA chain, `Zanzibar` → `ZNZ-1890-1963`
  and so on — and closing them is the same mechanical work done here for the
  `year_uncovered` group, just against a different failure mode. 4,244 rows.
- **`CapoVerde` is a real gap** and is the only one this pass found: see *cause
  3* above.
- **1912 has no whole-empire Ottoman polity.** `OTT-1908-1912` ends at an
  exclusive 1912 and the `TUR` chain starts in 1913.
- **No `source_conventions.csv` entry was added, and there are now three
  candidates.** The four Oceania umbrellas pool named territories; the 1913
  population column is dated to 1913 under *later* borders, which is why
  `estonia`, `latvia`, `lithuania`, `austria` and `ireland` each produce a
  one-year 1913 assertion against a pre-independence polity such as
  `EST-1800-1918`; and — the biggest one, *cause 2* above — **the source
  back-casts a territory's trade behind its own dating of the reporting unit, for
  44 of its 243 polities.** That last is the premise every verifier of a
  `year_uncovered` assertion from this source needs, and it is measurable from
  tracked files. All three are conclusions a verifier should reach and bank with
  evidence, and `validate_source_conventions.py` holds entries to that standard
  (a convention has to name its verification), so none was asserted here.
- **Which bucket-(C) territories deserve a polity row** is a judgement about
  WHEP's scope, not something this intake can settle: a Federico-Tena row is a
  *reporting unit*, and the page already warns that a WHEP row must not be
  created merely because one exists.

## Known limitations

- **`polities.csv`'s COLUMN NAMES ARE WRONG, and it is a lossy extract; read
  `federico_tena_polities.xlsx` instead.** Measured 2026-08-17 while preparing
  the intake table, then re-measured against the sheet's header rows the same
  day: the sheet *List of trading polities* carries eight numeric columns per
  polity, the CSV carries five, and the CSV's five are shifted one group left of
  their headers. What it calls `imports_start`/`imports_end` are the **polity's
  own** first and last year; `exports_start`/`exports_end` are the **imports**
  series; `population_start` is the **exports** series start. There is no
  population series in either file — which is exactly why `population_end` and
  `population_estimate` are empty in **all 243** CSV rows, an emptiness this page
  recorded on 2026-08-13 without drawing the conclusion. The sheet's 1913
  population (in thousands, given for **167** polities), its export END year and
  its "Trade sample serie included" column are absent from the CSV altogether.
  Consequences: the earlier claim that "the three windows the CSV does carry
  agree with the sheet row for row" is true of the VALUES and false of the
  labels; "all 243 carry an import series" is withdrawn — 146 do, and 97 carry
  no trade series at all; and "330 of the series ending in 1938" counted
  polity-window ends among the series ends and is withdrawn with it. Every
  measurement on this page below the 2026-08-13 line now comes from the xlsx
  read positionally against its header rows, which
  [prepare_federico_tena.py](../../pipelines/polity-autoimprove/prepare_federico_tena.py)
  documents.
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
