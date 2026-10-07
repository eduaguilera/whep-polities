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

**Mitchell (third input, issue 689).** `~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/
sources_original/mitchell/Agriculture without Europe data/page<a>-<b>/footers_page<a>-<b>.xlsx`,
12 files, 558 rows, same three columns. `consolidate_footnotes.py` appends them after the
FAO/IIA rows (`source = mitchell`, `commodity` = workbook stem, `page_number`/`table_number`
workbook-local, as in layer B's `indicator`), so the FAO/IIA note ids are unchanged.
**Measured (2026-10-07):** only **12** of the 558 rows carry note text. 360 are
"See p. N for footnotes" pointers to a book page whose notes were not extracted, and 186 are
blank. So most of Mitchell's table notes (all of C1 crop area to p. 28, livestock, C5 cocoa ...)
are **not** in this corpus. The manual PDF pass in #688 read some of them, for example Lower
Burma, Ghana with British Togoland and Nigeria with British Cameroons. The 12 rows split into
43 marker-level claims. A note joins to its column through the marker the extract keeps glued to the
header (`Indonesia 8`, `Maize 10`, `Korea¹ 13`). The marker is also glued to the cells of the
line-break years (`58958` = 5,895 + note 8), which dates the break.

Mitchell routing check (2026-10-07, `mitchell_footnote_routing_check.csv` in the output dir):
fixed by unit-scoped relabels: `indonesia` C2/C4 output to 1948 → IDN-JVM-1800-1949 (175 rows),
`indochina` maize to 1926 → VNM-1887-1954 (11). Mismatches with no target polity, left in
place: `india` C2 1928/1932-1936 excludes Burma while IND-1914-1937 includes it (34 rows),
`syrian arab republic` C1 area 1922-1938 excludes Lattakia and Jebel Druze (34), `indonesia`
rice 1946-1948 and sweet potatoes 1949-1952 cover Java, Madura, Bali and Lombok (6). Not
certain: `malaysia` C2 1920-1945 'Malay states' vs GBM-1895-1946 (32), and `israel/palestine`
wheat 1947-1948 after 'Palestine to 1946' (2).

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
- [x] Step 4 mapping — 216 named-claim proposals (host country resolved, polity
  codes matched) via a Sonnet/medium workflow →
  `footnote_polity_proposals.{csv,parquet}`.
- [x] Step 5 validate + categorize (`validate_proposals.py`): 121 kept
  (conf >= 0.85, self-referential dropped) → `footnote_proposals_validated.csv`;
  19-territory creation backlog → `footnote_territory_gaps.csv`; boundary-vintage
  vs classifier → `footnote_territory_basis_crosscheck.csv` (surfaced e.g. West
  Germany `F78-1949-1990` flagged "Bizone only" 1950 while the classifier had
  `assumed_constant`).
- [~] Step 6 apply:
  - [x] **priority_review wiring** — flagged hosts written to
    `../polity-autoimprove/state/footnote_flags.csv` (28 polities), which
    `04_territory_basis.py` now unions into `priority_review` (durable across
    classifier re-runs; bypasses the polygon-vintage gate since a footnote is
    direct coverage evidence). Adds e.g. West Germany Bizone, Syria⊃Lebanon.
  - [x] **Mitchell** (issue 689): footers consolidated (12 notes / 43 claims appended to
    `footnote_territory_claims.csv`) and checked against routing directly. The FAO-style
    step 4/5 (`footnote_polity_proposals.csv` → `validate_proposals.py`) was not re-run:
    re-running it on the stored proposals no longer reproduces the committed
    `footnote_flags.csv`. The proposals still name CAN-1948-2025, which the flags file renamed
    to CAN-1949-2025 when Canada's boundary moved to the Newfoundland accession.
  - [ ] create the 19 gap polities / compose unions / aliases (each needs a wiki
    page per standards). Boundary-vintage for generic numbered markers still
    needs the marked data tables.
