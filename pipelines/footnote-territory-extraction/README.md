# Footnote → Territory Extraction

Turn FAO/IIA yearbook **footnotes** into structured territorial-coverage claims
that improve how historical data points map to **polity polygons** — replacing
the *guessed* territory basis with the publisher's own stated coverage.

## Why

The historical-production harmonization maps each `(source, country, year, item)`
row to a polity + polygon. The hard part is **which territorial extent a figure
actually covers** — the nominal country name drifts from reality. The
`polity-autoimprove` stage-4 `territory_basis` classifier *guesses* whether a
figure uses its data-year (historical-vintage) border or an assumed/later one.
The yearbook footnotes state it explicitly, so they are ground truth.

## Source

`~/Nextcloud/WHEP_ERC 2025/Sources/datasets/textracted_footnotes/`
(`fao_textracted_footnotes/`, `iia_textracted_footnotes/`), per
source / year / topic / commodity-page table. Each `footers_*.xlsx` has columns
`page_number | table_number | footer_text` (OCR, bilingual EN/FR, marker-keyed).

**Measured (2026-06-25):** 242 files → 503 footnote rows; 57% carry territorial
language — ~113 boundary-vintage notes, ~89 named inclusion/exclusion notes.
FAO 1949–1961 is the bulk; IIA footnotes are sparse (mostly land-use).

## Pipeline

1. **Consolidate** — `consolidate_footnotes.py` walks the tree → one long table
   `footnotes_consolidated.{csv,parquet}` with provenance + cheap
   `has_boundary_vintage` / `has_named_territory` flags.
   ```bash
   python3 consolidate_footnotes.py    # uses default in/out paths
   ```

2. **Segment by marker** — split `footer_text` into individual notes by marker
   (`1 … 2 …` / `a) … b) …`), keep `marker_id`; de-hyphenate OCR
   ("com- pris", "II)"→"11)"); prefer the EN clause, FR as fallback.

3. **LLM structured extraction** (right tool for noisy bilingual OCR). Per note:
   ```
   { source, year, topic, marker_id,
     category: boundary_vintage | inclusion | exclusion | coverage_caveat |
               year_substitution | non_territorial,
     boundary_vintage: prewar | present | former | postwar | NA,
     territory:    <named place, e.g. "Saar", "Pakistan", "Newfoundland">,
     host_country: <for "X included under Y" → Y>,
     item_scope, text_en, confidence }
   ```
   Drop `non_territorial` (forestry/age/fallow/double-counting notes).

4. **Link marker → country.**
   - (a) Note **names** the territory (Saar, Pakistan, Newfoundland, Kashmir):
     usable immediately, no join.
   - (b) **Generic** marker ("10 Prewar"): needs the *marked data table* to know
     which country carries marker 10 — depends on the data extraction preserving
     cell markers (a known gap). Flag, don't block; (a) + boundary-vintage notes
     already cover most of the value.

5. **Map to polity-DB actions:**
   | Footnote | Action |
   |---|---|
   | `boundary_vintage = prewar/former` for (source,country,year) | force `territory_basis` → historical-vintage; crosswalk binds the data-year polity polygon |
   | `boundary_vintage = present` | force fixed/present-extent basis |
   | `inclusion: X under Y` | composed-territory mapping: (source,Y,year) covers Y∪X → point to / create a composed-union polity + alias |
   | `exclusion: Y excludes Z` | extent = Y∖Z: documented coverage caveat + reduced-extent flag |

6. **Validate & feed autoimprove** — cross-check footnote `boundary_vintage`
   against `../polity-autoimprove/state/territory_basis.csv`; emit disagreements
   as high-priority review rows. Footnote-derived inclusions/exclusions become
   ground-truth proposals into `../polity-autoimprove/` (new-polity / alias /
   crosswalk overrides), ranked above the heuristic sweep.

## Output

`~/Nextcloud/whep/footnote_territory/`
- `footnotes_consolidated.{csv,parquet}` (step 1)
- `footnote_territory_claims.parquet` (one row per extracted claim; step 3)
- `review.csv` (classifier disagreements; step 6)

Every claim keeps `text_en` + `rel_path` so each polity edit is
provenance-traceable (per wiki-page standards).

## Status

- [x] Step 1 consolidation (`consolidate_footnotes.py`) — 503 notes
- [x] Step 2 batch prep (`prepare_batches.py`)
- [x] Step 3 LLM extraction — 345 claims in
  `footnote_territory_claims.{csv,parquet}` (108 boundary-vintage, 102
  coverage-caveat, 71 exclusion, 64 inclusion). Run via a Claude Code
  multi-agent workflow (Sonnet/medium, one agent per batch, StructuredOutput
  schema). Re-runnable; see git history / session workflow script.
- [~] Step 4 linkage + mapping — named-territory claims resolvable now;
  boundary-vintage + generic numbered markers need the marked data tables.
- [ ] Steps 5–6 polity-DB actions + autoimprove integration
