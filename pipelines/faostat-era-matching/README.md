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
Rscript --vanilla pipelines/faostat-era-matching/match.R --accept-diff # see below
```

The merge into `applied_aliases.csv` is replace-by-source (every
`source = "faostat"` row is regenerated), and it is **guarded**: if an existing
faostat row would be dropped or re-targeted by the fresh run, the script aborts
and lists the rows instead of silently wiping them. That state means either

- a **hand-edit** in the CSV — never do that; encode the decision as a
  `manual_prefix` / `manual_prefix_replace` / `manual_span_routes` entry in
  `match.R` — or
- an **intentional `match.R` route change** — re-run with `--accept-diff`
  (or `WHEP_FAOSTAT_ACCEPT_DIFF=1`) to accept the listed diff once. Steady-state
  re-runs (only new rows, or no changes) never need the flag.

Requires an accessible WHEP checkout (pins cache + area registry); set
`WHEP_REPO` (default `/home/usuario/WHEP`). R packages: `dplyr`, `readr`,
`purrr`, `tidyr`, `arrow`, `devtools`.

## What it does

1. **Inventory.** Scans the cached FAOSTAT pins (production, FBS new/old,
   CBS new/old, trade totals) for every observed
   `(area_code, area_name, first_year, last_year, n_rows)`. This — not a
   registry listing — is the completeness target: every code that reports
   data must resolve to a polity.
1b. **No-data registry areas.** WHEP's *processed* production imputes rows
   for reporting areas that carry no data in the raw pins (micro-states like
   Andorra, dependent territories). To keep the alias table complete enough
   for WHEP's crosswalk (a swap that dropped them would silently un-map
   them), every crosswalk area below code 900 that was not observed and is
   not an aggregate is added as a no-data area, matched by iso3 family over
   its polity periods (route `registry`, `rows = 0`). No observed data means
   these never produce a coverage-gap or ambiguity finding; a no-data area
   with no polity family at all is a genuine non-country (Antarctica,
   "Unspecified", uninhabited isles, and dependencies the polities DB has
   not yet modelled — Aruba, Gibraltar, Cayman, …) and is written to
   `state/registry_unmapped.csv` as informational, NOT an actionable finding.
   Note: the current WHEP crosswalk folds these into `ROW-1850-2023` via
   `fabio_code == 999`; keeping per-country identity here and deferring the
   RoW collapse is the whep issue #120 intent — the FABIO collapse still
   happens downstream from `fabio_code`, orthogonally to this polity map.
2. **ISO3 attribution.** Takes each area's ISO3 from the WHEP area registry
   (`polity_area_crosswalk`); this is FAOSTAT registry metadata, not a
   polity decision.
3. **Family + period split.** Matches the area to its polity family —
   `iso3_code` in `data/final/polities_database.csv` (retired/superseded
   rows excluded), extended by manual prefix routes where the chain has its
   own prefix: `7 → ANG` (Portuguese Angola), `20 → BEC` (Bechuanaland),
   `51 → F51` (Czechoslovakia), `72 → FRS` (French Somaliland/Djibouti),
   `206 → SUD` (pre-2011 undivided Sudan), `228 → F228` (USSR), `248 →
   F248` (Yugoslav SFR). The observed span is split at every period
   boundary and each segment picks its covering period with three rules:
   type rank (national > colonial > territory > …); within one polity
   prefix the most specific (shortest) period wins over a blanket span;
   and a shared transition year routes to the successor (adjacent WHEP
   periods both include their boundary year — e.g. FAOSTAT
   `206 Sudan (former)` yields 1961–2010 → `SUD-1956-2011` and 2011 →
   `SDN-2011-2025`).
4. **Flags, not guesses.** Segments covered by genuinely simultaneous
   entities under different prefixes (e.g. Malaya vs Sarawak vs North
   Borneo for FAOSTAT "Malaysia" 1961–1962) go to `state/ambiguous.csv`;
   observed years with no covering period are reported as coverage gaps;
   areas with no polity at all land in `state/unmatched.csv`. Statistical
   aggregates (`351 China`, codes ≥ 5000, "excluding intra-trade"
   reporters) are intentionally unrouted. Together these are the
   polity-autoimprove issue queue for the FAOSTAT era — never silent
   routings.
5. **Merge.** `source = "faostat"` rows in `applied_aliases.csv` are wholly
   machine-generated by this pipeline, so the merge is replace-by-source:
   existing faostat rows are dropped and the fresh set appended, while
   rows from every other source are preserved byte-identically. Every row
   carries `source = "faostat"` **and** an explicit year range, so the 01
   matcher's source/year-scoped rule matching can never let these rows
   affect pre-1961 sources.

## Outputs

- `state/faostat_aliases.csv` — full result, including `area_code`, `iso3`,
  `match_route`, `match_status` (the code-keyed registry; the WHEP repo's
  `data-raw/table_mappings.R` can consume this directly once reviewed, in
  place of deriving the mapping from `regions_full.csv`).
- `state/unmatched.csv` — areas with no polity routing plus the reason.
- `state/report.md` — run summary: counts, review rows, unmatched areas.
- Appended rows in `../polity-autoimprove/state/applied_aliases.csv`.

## Review loop

The residual queue (`state/unmatched.csv`, `state/ambiguous.csv`, and
coverage-gap notes on alias rows) is ingested automatically by
`pipelines/polity-autoimprove/01_match_and_findings.py` (Stage 1b) as
`name_unresolved` / `coverage_gap` findings, so the autoimprove loop
works FAOSTAT-era items exactly like Layer-B ones (wiki-first; one commit
per fix). As of 2026-07-02 the queue is empty: 212 observed reporting
areas resolve to 264 aliases with no gaps, no ambiguity, and no unmatched
areas (that pass created 12 polities — COK, NIU, GUF, REU, PSE, BMU-1968,
SGP-1963, BDI/RWA-1922, F237, F249, SRB-2006 — and settled Malaysia
1961-1962 from rubber-production magnitudes).
