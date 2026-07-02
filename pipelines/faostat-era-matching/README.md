# faostat-era-matching

Deterministic matcher that makes the alias table
(`pipelines/polity-autoimprove/state/applied_aliases.csv`) know about the
**FAOSTAT era (1961+)**: every reporting area that actually carries data in
the WHEP FAOSTAT pins is matched to the WHEP polity period(s) covering its
observed year span, and the result is emitted as year-ranged, source-scoped
routing aliases (`source = "faostat"`).

This is the FAOSTAT-era sibling of
[`pipelines/pre1961-matching`](../pre1961-matching/README.md): that pipeline
crosslinks the pre-1961 printed-statistics union ("Layer B") by *name*; this
one crosslinks the FAOSTAT reporting universe by *numeric area code*, then
records the result under the area's verbatim FAOSTAT name so the shared alias
machinery (name + source + year range) can use it.

## Run

From the project root:

```bash
Rscript --vanilla pipelines/faostat-era-matching/match.R           # match + merge
Rscript --vanilla pipelines/faostat-era-matching/match.R --no-apply # match only
```

Requires an accessible WHEP checkout (pins cache + area registry); set
`WHEP_REPO` (default `/home/usuario/WHEP`). R packages: `dplyr`, `readr`,
`purrr`, `tidyr`, `arrow`, `devtools`.

## What it does

1. **Inventory.** Scans the cached FAOSTAT pins (production, FBS new/old,
   CBS new/old, trade totals) for every observed
   `(area_code, area_name, first_year, last_year, n_rows)`. This — not a
   registry listing — is the completeness target: every code that reports
   data must resolve to a polity.
2. **ISO3 attribution.** Takes each area's ISO3 from the WHEP area registry
   (`polity_area_crosswalk`); this is FAOSTAT registry metadata, not a
   polity decision.
3. **Family + period split.** Matches the area to its polity family
   (`iso3_code` in `data/final/polities_database.csv`; national periods
   preferred) and splits the observed span across the periods it intersects
   — e.g. FAOSTAT `79 Germany` (1961–) yields one alias row for
   `DEU-1949-1990` and one for `DEU-1990-2025`. Manual family routes mirror
   the reporting composites: `51 → F51` (Czechoslovakia), `228 → F228`
   (USSR), `248 → F248` (Yugoslav SFR), and `206 Sudan (former) → SUD`
   (the pre-2011 undivided Sudan, *not* the post-2011 rump SDN).
4. **Flags, not guesses.** Spans not fully covered by polity periods,
   overlapping periods, and areas with no family at all (statistical
   aggregates like `351 China`, regional buckets, "Unspecified") are emitted
   with `confidence = "review"` or into `state/unmatched.csv` — these are
   the polity-autoimprove issue queue for the FAOSTAT era, never silent
   routings.
5. **Merge.** High-confidence and review rows are appended idempotently to
   `applied_aliases.csv` keyed by
   `(original_name, source, year_start, year_end)`. Every row carries
   `source = "faostat"` **and** an explicit year range, so the 01 matcher's
   source/year-scoped rule matching can never let these rows affect
   pre-1961 sources.

## Outputs

- `state/faostat_aliases.csv` — full result, including `area_code`, `iso3`,
  `match_route`, `match_status` (the code-keyed registry; the WHEP repo's
  `data-raw/table_mappings.R` can consume this directly once reviewed, in
  place of deriving the mapping from `regions_full.csv`).
- `state/unmatched.csv` — areas with no polity routing plus the reason.
- `state/report.md` — run summary: counts, review rows, unmatched areas.
- Appended rows in `../polity-autoimprove/state/applied_aliases.csv`.

## Review loop

Rows with `confidence = "review"` and everything in `state/unmatched.csv`
are meant to be worked through the
[`polity-autoimprove`](../polity-autoimprove/README.md) loop (wiki-first;
one commit per fix): missing pre-1990 Yemen polities, the Serbia 2006–2008
gap, and similar findings surface here as evidence-backed issues rather
than being resolved by convention.
