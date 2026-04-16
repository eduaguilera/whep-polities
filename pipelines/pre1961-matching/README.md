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
2. **Normalises ISO3 codes** (`normalise_iso`) with ~30 rewrite rules:
   - **Composite entities:** YUG → F248 (Yugoslavia), CSK → F51 (Czechoslovakia)
   - **Pre-independence routing:** AUT/HUN < 1918 → AUH (Austria-Hungary),
     IRL < 1921 → GBR, FIN < 1917 → F228 (Russian Empire),
     TUR < 1913 → OTT (Ottoman), DEU 1949-1990 → F78 (West Germany)
   - **Colonial routing:** TZA < 1964 → TAN (Tanganyika),
     BWA < 1966 → BEC (Bechuanaland), MRT < 1960 → MAU,
     SOM < 1960 → ITS (Italian Somaliland), SDN < 2011 → SUD,
     MWI/ZWE/ZMB 1953-1964 → FRN (Central African Federation),
     MYS < 1946 → BMA (British Malaya), RWA < 1962 → RWB (Ruanda-Urundi),
     PAK < 1947 → IND (British India), BGD < 1971 → PAK
3. **Falls back to name-based mapping** (`name_override` + `country` column)
   for rows where `iso3c == NA` (Korea, Natal, Cape Colony, Indochina,
   Manchuria, Rwanda-Burundi, Israel/Palestine). Post-resolution rules
   adjust time-dependent entities (Natal/Cape → ZAF after 1910 Union,
   Manchuria → MAN for 1932-45 Manchukuo / CHN otherwise).
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

## Creating new polity entries

When no existing WHEP polity matches the input data, create one. Every
new polity needs three things: a CSV row, a wiki page, and a polygon
decision. The wiki page is the primary documentation — it must record
the reasoning, not just the metadata.

### Wiki page requirements

Every wiki page **must** include in its `## Territorial extent` section:

1. **Polygon status** — one of:
   - `Copied from [CODE](code.md) (reason why this proxy is valid)`
   - `Not yet assigned. **Proxy deliberately not copied** because
     [reason the available polygon is wrong, with km² numbers]`
   - `Not yet assigned. No polygon available in the GeoPackage for
     this period.`

2. **Why this entry exists** — answering:
   - What input data does this polity capture? (country name, iso,
     year range, row count)
   - What was this data previously matched to, and why was that wrong?
   - What historical source confirms this entity was distinct?
     (e.g., Federico-Tena treats it as a separate trading polity)

3. **Territory description** — what area does this polity cover, in
   terms a reader can locate on a modern map? Include approximate
   km² if known.

### Polygon proxy rules

When copying a polygon from another period of the same polity:

- **Copy if** the territory is essentially unchanged (e.g., Finland
  at independence 1917 ≈ Grand Duchy of Finland 1809-1917).
- **Do NOT copy if** the territory changed dramatically (e.g.,
  post-Trianon Hungary is 71% smaller than Transleithania; post-1918
  Poland is 3x larger than Congress Poland). Document why the proxy
  was rejected and what a correct polygon would look like.
- **Note approximations** (e.g., "post-1921 Ireland polygon excludes
  Northern Ireland; pre-1921 data covers the whole island — ~15%
  larger").
