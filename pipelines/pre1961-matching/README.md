# pre1961-matching

Self-contained, reproducible R pipeline that crosslinks the pre-1961
agricultural / livestock dataset `data/external/before_1961.csv` with the
WHEP polity database `data/final/polities_database.csv`.

No dependency on `R-legacy/`. Everything this pipeline needs is declared in
`match.R`.

## Run

From the project root:

```bash
Rscript pipelines/pre1961-matching/match.R
```

Required R packages: `readr`, `dplyr`, `tidyr`, `jsonlite`.

## What it does

1. **Loads** the WHEP polity registry and the pre-1961 input.
2. **Normalises ISO3 codes** (`normalise_iso`) so non-ISO-3166 inputs map to
   WHEP's internal codes (YUG → F51/F248, CSK → F77, pre-1920 SRB → SER,
   pre-1948 ISR/PSE → PAL), and pre-independence years are routed to the
   appropriate imperial chain (pre-1921 IRL → GBR, pre-1917 FIN/POL/EST/
   LVA/LTU → F228 Russian Empire, pre-1913 TUR → OTT Ottoman).
3. **Falls back to name-based mapping** (`name_override`) for rows where
   `iso3c == NA` (Korea, Natal, Rwanda-and-Burundi, etc.).
4. **Matches** each (iso3c, year) to a WHEP polity whose
   `[start_year, end_year]` contains `year`. When several candidates
   qualify, prefers `polity_type == "national"` over subnational
   provinces (ES01-ES52, US states, BR states).
5. **Audits each matched row** and assigns a `match_confidence` class
   (see "Confidence audit" below) so silent false positives surface.
6. **Emits**:
   - `data/compiled/pre1961/matched.csv` — per-row matched file with
     `whep_polity_code`, `match_status`, and `match_confidence` columns.
   - `data/compiled/pre1961/summary_by_polity.json` — per-polity
     rollup (rows, years, items, sources). Consumed by the UI.
   - `data/compiled/pre1961/by_item/<slug>.json` — per-item pivot
     `{item, unit, by_year: {year: {polity_code: value}},
     unmatched_by_year: {year: [{iso3c, country, name, value}]}}`.
     One file per crop/commodity; consumed by the map-with-data tab.
   - `data/compiled/pre1961/by_item_index.json` — index of item slugs.
   - `data/compiled/pre1961/suspects.json` — per-bucket list of
     matched-but-suspect rows that need review.
   - `data/compiled/pre1961/report.md` — human-readable report
     (match breakdown, confidence breakdown, unmatched bucket, suspect
     bucket, recommendations).

## Confidence audit

A match isn't automatically correct — `normalise_iso()` can route the
input to the wrong WHEP polity (silent false positive). The pipeline
therefore records a `match_confidence` class for every row and writes
the matched-but-questionable ones to `suspects.json`.

Classes (most to least trustworthy):

| class | meaning |
|-------|---------|
| `iso-equal` | `iso3c` equals WHEP `iso3_code` AND the input country name shares a 3+-char token with the WHEP `polity_name`. Default "safe" bucket. |
| `known-equivalent` | iso matches but names differ in a historically-expected way (Japan ↔ Japanese Empire, Turkey ↔ Türkiye, Ivory Coast ↔ Côte d'Ivoire, Vietnam ↔ Annam/Tonkin, Myanmar ↔ Burma/Konbaung, Iran ↔ Persia, Thailand ↔ Siam, DR Congo ↔ Congo, etc.). Extend the `name_equiv` list in `match.R` when new aliases appear. |
| `trusted-rewrite` | `normalise_iso()` rewrote the input (IRL<1921→GBR, pre-1917 FIN/POL/EST/LVA/LTU→F228, YUG→F51/F248, CSK→F77, etc.) and the resulting polity code sits in the explicit allowlist in `trusted_rewrite()`. |
| `name-overlap` | iso3c did not match WHEP's iso3_code, but the WHEP polity_name shares a token with the input country/polity_name (e.g., SRB→SER, PSE→PAL). |
| `iso-equal-name-mismatch` | **Most likely false positive.** iso matches but the WHEP polity_name doesn't share a token with the input and isn't a known equivalent (e.g., NGA→Nupe Kingdom because Nupe carries `iso3_code=NGA` in WHEP despite being a sub-kingdom). These buckets are listed in `suspects.json` and in the "Top suspect buckets" section of `report.md`. |
| `suspect` | Matched via some non-trivial path but none of the trust rules fire. Also surfaced to `suspects.json`. |
| `none` | Unmatched — the input (iso3c, year) had no WHEP row meeting the rules. Shown in the UI as the red "Unmatched" panel. |

### Guardrail for single-candidate matches

`match_one()` has an extra check: if only one WHEP national row matches
an (iso, year), we still reject it when the WHEP `polity_name` shares no
tokens with the input country and the input iso isn't in `name_equiv`.
This prevents accidents like NGA 1889-1897 → `NUP-1800-1897` (the
Nupe Kingdom is a sub-state, not a Nigeria equivalent). The 12 rows
that previously silently matched are now correctly unmatched.

### When the suspect bucket is non-empty

For each entry in `suspects.json`, decide:

1. **Match is actually correct** → add the WHEP polity_name (or a
   fragment) to the appropriate `name_equiv[[iso]]` list, re-run.
2. **Match is wrong** → fix WHEP's `iso3_code` for that polity (it's
   probably tagged with a country-level iso when it shouldn't be), or
   add a `normalise_iso()` / `name_override` rule that redirects the
   input, then re-run.

Target steady state: zero suspect buckets, with a documented reason
(commit message / log entry) for every addition to `name_equiv` or
`trusted_rewrite`.

## Extending the mapping

When new countries end up unmatched (the `none` bucket), edit
`normalise_iso()` or the `name_override` table in `match.R`. Re-run
to regenerate all outputs:

```bash
Rscript pipelines/pre1961-matching/match.R
bash site/build_wiki.sh
```

The UI picks up the new per-item JSON files automatically (the year
slider in the Data tab drives re-rendering) and the unmatched panel
updates to reflect the new state.
