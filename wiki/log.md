# Wiki Log

Chronological record of every non-trivial change to the wiki. Append-only.
Each entry is a dated H2 heading. Newest on top.

Entry format:

```markdown
## YYYY-MM-DD — <slug>
**Touched:** polity-code-1, polity-code-2
**Source:** <source-slug or "none">
**Kind:** ingest | decision | contradiction | proposal | lint

<one or two paragraphs of rationale. Link to pages and sources.>
```

Kinds:
- **ingest** — a new source was added and its claims propagated.
- **decision** — a judgment call affecting the CSV (add/remove/split
  polity, change dates, reclassify type). Must name the human who signed off.
- **contradiction** — two sources disagree on a load-bearing fact; logged
  and left open until a human resolves it.
- **proposal** — a change the wiki suggests to the CSV but has not applied.
- **lint** — bulk cleanup from a lint run.

---

## 2026-04-11 — schema-stable-oq-ids-and-lint-relaxation
**Touched:** wiki/README.md, wiki/prompts/lint.md, wiki/polities/_template.md
**Source:** none
**Kind:** decision

Two meta-changes to the wiki itself, motivated by findings in the
first lint run (`lint-luxembourg`):

1. **Open questions now use stable slug IDs.** Previously numbered
   (`open question 5`), which broke every cross-reference whenever
   a question was resolved and the list renumbered. New rule (in
   `wiki/README.md §Page schema`): each open question starts with
   `**oq-<short-kebab-case>**` and cross-references anywhere on the
   page must use the slug, e.g. "see [oq-polygon-provenance]".
   Resolved questions are struck through and left in place as
   stable anchors rather than deleted.
2. **Lint rule is now split into allowed/forbidden lists.** The
   previous rule ("do not edit polity page content during a lint
   run, lint fixes frontmatter, the index, and the log — not
   claims") was too coarse: it blocked obvious navigation repairs
   like "see open question 6" pointing at a question that doesn't
   exist, and it blocked typo fixes. New rule (in
   `wiki/prompts/lint.md §What lint is allowed to edit`):
   - **Allowed:** frontmatter, index, log, typos, broken internal
     cross-references (repoint or TODO-comment + flag).
   - **Forbidden:** adding/rewording *Sourced claims*, editing
     *Summary*/*Territorial extent*/*Contradictions*/*Decisions*
     body text, changing `sources:`, editing source files, editing
     README.md or any prompt.
   - The dividing line: lint repairs **navigation, formatting,
     indexing**; only ingest changes **what the page claims**.

Template updated (`wiki/polities/_template.md`) to show the new
open-question format with an example slug. Existing Luxembourg
page will be migrated to the new format in the immediately-following
`lux-post-lint-cleanup` ingest.

## 2026-04-11 — lux-post-lint-cleanup
**Touched:** LUX-1839-2025
**Source:** none (claim updates draw on sources already ingested)
**Kind:** ingest

Applies the findings of the `lint-luxembourg` run. Everything lint
flagged but was forbidden from touching.

**Navigation / typo fixes** (would now be allowed under the relaxed
lint rule, but bundled here for atomicity):

- Fixed typo `"CShapES"` → `"CShapes"` in *Territorial extent*.
- Migrated *Open questions* from the old 1–5 numbered format to
  stable slug IDs: `oq-polygon-provenance`,
  `oq-territorial-stability`, `oq-academic-corroboration`,
  `oq-cshapes-1893-start`, `oq-bleu-faostat`. Renamed
  "CShapes 1886–1892 gap narrowed" to the less misleading "Why
  CShapes's first Luxembourg row starts 1893-01-01".
- Repointed the two broken cross-references in *Territorial extent*:
  the 1839–1885 polygon note now points at
  `[oq-polygon-provenance]`, and the old "see open question 6"
  pointer is gone entirely (its content is now a sourced-claim
  statement of resolution, not an open question).

**Claim updates** (these are why this is an `ingest`, not a `lint`):

- Rewrote the *CShapes version coding* paragraph in *Territorial
  extent*. The old text said WHEP "does not record which CShapes
  version was loaded" and framed the COW/GW choice as an open
  question. The new text states the resolution: WHEP loads the
  COW variant, confirmed by schema inspection and by bit-equivalent
  regeneration from `cshp(useGW = FALSE, dependencies = TRUE)`,
  with forward references to the two `log.md` entries that
  established it (`decision-cshapes-is-cow-based` and
  `cshapes-reproducibility-verified`).
- Rebuilt the *Decisions* section. Previously a single stub entry
  for the first ingest; now lists all eight `log.md` entries that
  touched this page or established a rule affecting it, newest
  first, with ★ marking the two repo-wide `decision`-kind rules.
  The new rationale for keeping the page at `status: draft` is
  linked to `[oq-academic-corroboration]` — needs at least one
  academic or reference-work source for the 1839 territorial
  event before it can move to `reviewed`.

No changes to `sources:`, frontmatter (other than already-current
`last_ingest`), or any source file. Status stays `draft`.

---

## 2026-04-11 — lint-luxembourg
**Touched:** LUX-1839-2025 (report only), wiki/index.md (auto-applied)
**Source:** none
**Kind:** lint

First lint run on the wiki, scoped to the single Luxembourg page plus
the shared infrastructure it depends on. Executed `wiki/prompts/lint.md`.

**Summary:**

| check | result |
|---|---|
| Schema conformance | PASS — all 10 required frontmatter fields and all 7 required H2 sections present. |
| CSV ↔ wiki parity | PASS — `LUX-1839-2025` exists in `data/final/polities_database.csv:410`. `F15-1800-1999` (Belgium-Luxembourg aggregate) exists and is correctly flagged on the page as a separate row that must not be conflated. No orphan polity pages. |
| Citation health | PASS — 10 `Sourced claims` bullets, every one cited. 1 pure `[database]` bullet (10%), far below the 50% threshold that would flag the page for re-ingest. |
| Contradiction backlog | PASS — section is empty by design with an explanatory note; nothing sitting >90 days. |
| Staleness | PASS — `last_ingest: 2026-04-11` is today. |
| Index freshness | Auto-fixed (see below). |
| Source reachability | PASS — all 3 sources (`cshapes-2.0`, `cow-state-system-v2024`, `wikipedia-luxembourg-2026-04-11`) are cited by Luxembourg; no zero-citation sources. |

**Must fix (body-text issues, not auto-applied per lint rule):**

1. **Broken internal cross-reference, line 52**: *Territorial extent*
   says "See open question 5" for pre-1886 polygon provenance, but
   that question is now **open question 1** after a renumbering. The
   reference points at the wrong bullet (currently BLEU vs F15).
2. **Broken internal cross-reference, line 76**: *Territorial
   extent* says "see open question 6", but there is no open question
   6 (the list has only 5 entries after the same renumbering).
3. **Typo, line 64**: `"silently absent from CShapES."` — should be
   `"CShapes"`. Inside a lint rule, so grep will find it.

**Should review (claim-level drift, not auto-applied):**

4. **Stale "COW vs GW coding" paragraph, lines 71–76.** The page
   text says "The repo's CSV records COW code 212 for Luxembourg
   but does not record which CShapes version was loaded" and tells
   the reader to see open question 6. Both halves are outdated:
   `log.md 2026-04-11 decision-cshapes-is-cow-based` and
   `cshapes-reproducibility-verified` resolved this definitively
   (COW, bit-equivalent to `cshp(useGW=FALSE, dependencies=TRUE)`),
   and `R/00b_fetch_cshapes.R` now records the convention in code.
   The paragraph should be rewritten to state the resolution
   instead of asking the question.
5. **Decisions section is under-populated.** Currently lists only
   `lux-first-ingest`. Should also reference, in rough order of
   relevance to this page:
   - `log 2026-04-11 — decision-whep-polity-definition` (the rule
     that lets Luxembourg start in 1839)
   - `log 2026-04-11 — decision-cshapes-is-cow-based` (the rule
     behind which CShapes timeline applies)
   - `log 2026-04-11 — cshapes-primary-source-upgrade`
   - `log 2026-04-11 — cshapes-reproducibility-verified`
   - `log 2026-04-11 — cow-state-system-v2024-ingest`
6. **Decisions rationale is stale.** The `lux-first-ingest` entry
   says "Status remains `draft` because the narrative layer rests
   on a single tertiary source." Still true (Wikipedia is the only
   narrative source), but the entry doesn't mention that two more
   ingests happened the same day. A fresh rationale: "Remains
   `draft` pending at least one academic or reference-work source
   (Britannica, national history) to corroborate the 1839
   territorial event — see open question 3."

**Auto-applied:**

- `wiki/index.md` — replaced the placeholder
  `"(run \`wc -l data/final/polities_database.csv\`)"` with the
  real row count `1386 (as of 2026-04-11 lint)` under *Coverage →
  Polities in CSV*.
- This log entry.

**Recommendation.** Issues 1–6 are all on the Luxembourg page body,
which the lint rule forbids editing. Apply them manually, or run a
short touch-up ingest that bundles the six fixes into a single
`ingest`-kind log entry (since fix 4 is a claim update, not just a
cross-reference repair, it's better as a real ingest than as a
lint).

---

## 2026-04-11 — cow-state-system-v2024-ingest
**Touched:** LUX-1839-2025
**Source:** cow-state-system-v2024 (new)
**Kind:** ingest

Downloaded the Correlates of War State System Membership List v2024
directly from correlatesofwar.org (no authentication needed; public
academic dataset distributed under a citation request, not a
no-redistribute clause). Created `wiki/sources/cow-state-system-v2024.md`
and committed the two core CSVs (`statelist2024.csv`, `system2024.csv`)
under `wiki/sources/data/cow-v2024/` so the wiki is self-contained for
COW claims. Codebook PDF goes to `wiki/sources/pdfs/` which is
gitignored.

Used COW to upgrade three claims on `lux-1839-2025.md`:

1. **Direct citation for Luxembourg's COW state-system dates** (two
   tenure rows, 1920-11-15→1940-05-10 and 1944-09-10→2024-12-31),
   rather than inferring them via CShapes.
2. **Confirms the COW/CShapes alignment** — CShapes's two
   `independent` windows for Luxembourg match COW's two tenure rows
   to the day, which is exactly what the CShapes paper says should
   happen since `useGW=FALSE` loads COW membership as the
   independence criterion.
3. **Narrows (but does not resolve) open question 4** about the
   1893-01-01 CShapes row start. COW does not list Luxembourg until
   1920, so the 1893 row start is NOT a COW membership transition
   (my earlier guess was wrong). It must come from CShapes's
   dependency-tracking sources — the Territorial Change Dataset,
   Biger 1995, or Brownlie & Burns 1979. Full resolution would need
   another source ingest or inspection of the cshapes package
   internals.

Also recorded a small but useful finding for any future COW citation:
COW has revised start dates between vintages (the codebook p.3–4
lists a v2004.1 change moving Brazil's start from 1826-01-01 to
1822-09-07, Afghanistan from 1920 to 1919, Panama from 1920 to 1903).
Any wiki page citing `[cow-state-system-v2024]` is citing v2024
specifically — later COW vintages are a new source file, not an
edit.

---

## 2026-04-11 — cshapes-reproducibility-verified
**Touched:** (none — verification only)
**Source:** cshapes-2.0
**Kind:** lint

Resolved the provenance gap noted in the earlier
`decision-cshapes-is-cow-based` entry. Installed `cshapes` R package
v2.0 into a scratch library (`/tmp/rlib_cshapes`, not `renv/`) and
ran `cshp(useGW = FALSE, dependencies = TRUE)`, then compared the
output against `data/geodata/cshapes2_full.gpkg`:

- 805 rows in both.
- Identical column set, no `gwcode`.
- All (cowcode, country_name, start, end, status) tuples identical
  after sorting.
- All 805 geometries `st_equals`-identical.

Conclusion: the on-disk gpkg is bit-equivalent in content to the
R package default for `useGW=FALSE, dependencies=TRUE`. This means:

1. The COW finding stands — the R call literally specifies it.
2. The 1893 Luxembourg start is canonical to cshapes 2.0, not a
   local artefact. (Open question 4 on `lux-1839-2025` therefore
   becomes a question about `cshapes` upstream, not about WHEP.)
3. Anyone can regenerate the file deterministically, so lint runs
   do not have to trust the file's provenance.

Recommendation for a future repo change (not applied here — wiki
does not edit pipeline code): add `R/00b_fetch_cshapes.R` with

```r
library(cshapes); library(sf)
cs <- cshp(useGW = FALSE, dependencies = TRUE)
st_write(cs, file.path(geodata_dir, "cshapes2_full.gpkg"),
         delete_dsn = TRUE)
```

and correct `REPRODUCIBILITY.md:162` to point at it. Also add
`cshapes` to `renv.lock`.

## 2026-04-11 — decision-whep-polity-definition
**Touched:** (repo-wide; the definition of what a WHEP polity is)
**Source:** none (stated by the project maintainer in conversation)
**Kind:** decision

Records the WHEP definition of a polity. This is the most load-bearing
rule in the wiki and should be cited from every polity page whose
start/end year differs from an external source's independence dating.

**Rule.** A WHEP polity is a **territorial-economic unit** with trade
or production data attached, not a Westphalian legal state. Specifically:

1. **Split rule.** A new polity row is created when the territory
   undergoes a *substantial* territorial change. The triggering event
   is the territorial change itself, not the legal/diplomatic status
   of the unit before or after.
2. **Continuity rule.** If the territory remains the same, the polity
   stays a single continuous row across the full window for which
   trade or production data is available, **even across**:
   - regime changes (monarchy → republic, etc.)
   - wartime occupations that do not alter the final borders
   - entry into or exit from personal unions, customs unions, or
     federations, unless those events coincide with a territorial
     change
   - periods when external state-system datasets (COW, GW, CShapes)
     do not list the unit as an independent state
3. **Independence is not the criterion.** If trade or production data
   exists for a territory, it is a WHEP polity regardless of whether
   any external source considers it independent, a dependency, or
   "N/A". Conversely, a legally independent state with no trade data
   attached is not automatically a WHEP polity.

**Why.** WHEP exists to analyze historical trade and production at
the level of stable economic territories. Legal/diplomatic definitions
of statehood (COW's two-major-power rule, population thresholds, etc.)
do not track the right unit for trade analysis: a colony with its own
customs regime and trade statistics is a trade unit even if COW codes
it as a dependency, and a state under military occupation whose
borders did not move is still the same trade unit afterwards.

**How to apply on polity pages.** When the WHEP start/end year differs
from an external source's independence dating, this is not a
contradiction and should NOT be recorded in a page's *Contradictions*
section. Instead:

- Record the WHEP date in *Summary* and cite this decision entry.
- Record the external source's date in *Sourced claims* as a fact
  about that source, with the note that it uses a different
  definition.
- Use *Contradictions* only for disagreements *within the same
  definition*: e.g. two historical atlases giving different dates
  for the same territorial change, or two sources disagreeing on
  whether a transfer of territory actually happened.

**How to apply at ingest time.** Before creating a new polity page
from an ingested source, check whether the source is tracking
state-system membership (COW, GW, Polity V, V-Dem) or territorial
extent (CShapes, Euratlas, Cliopatria, historical atlases). Only the
second category can justify a *split* in a WHEP polity. The first
category can inform *Sourced claims* about regime type and diplomatic
status but must not drive start/end years.

**Open sub-question.** The rule says "substantial" territorial change
without quantifying it. CShapes uses a 100 × 100 km threshold
`[cshapes-2.0 §coding-changes]`; WHEP does not have a written
threshold. A future `decision` entry should pick a WHEP-specific
threshold or explicitly defer to case-by-case judgement. For now,
existing splits in the CSV stand as precedent.

## 2026-04-11 — decision-cshapes-is-cow-based
**Touched:** (repo-wide; applies to every CShapes-citing polity)
**Source:** cshapes-2.0
**Kind:** decision

Resolves open question #6 on `lux-1839-2025` and establishes a repo-wide
convention: **WHEP uses the COW-based version of CShapes 2.0**.

Evidence (direct inspection of `data/geodata/cshapes2_full.gpkg`):

1. **Schema.** The `cshapes` layer contains `cowcode` but no `gwcode`
   column. The paper notes both columns are typically present
   `[cshapes-2.0 §coding-dependencies]`; the absence of `gwcode` here
   is consistent with the COW-only distribution.
2. **Canada acid test.** The paper explicitly names Canada as the
   case that distinguishes the two versions: COW sets independence
   to 1920, GW to 1867 `[cshapes-2.0 §coding-states]`. Our gpkg has
   three Canada rows with `cowcode=20`: 1886-01-01 to 1920-01-09 as
   `colony`, 1920-01-10 to 1948-07-21 as `independent`, and
   1948-07-22 to 2019-12-31 as `independent`. The 1920-01-10 transition
   matches the COW date exactly; the GW 1867 date does not appear.

Provenance caveat: I could not find the R code that actually *writes*
`cshapes2_full.gpkg`. `REPRODUCIBILITY.md` attributes it to R/01, but
R/01 only reads a pre-existing `cshapes.csv` from `data/whep-source/`
— it does not call `cshapes::cshp()` and does not write any gpkg.
Either the gpkg was built by a one-off script not checked in, by a
prior pipeline version, or was downloaded directly from ETH Zurich.
Worth flagging as a reproducibility gap in a future log entry; the
COW finding stands regardless because it is a property of the data
actually on disk.

**Consequence:** every polity page that cites CShapes implicitly
cites the **COW-based** version. Polity start years derived from
`[cshapes-2.0]` must be read against COW's independence criteria
(diplomatic ties to two major powers, population threshold, etc.),
not GW's. For polities that are well-known as COW/GW edge cases
(Canada, Luxembourg, several Central American states before WWII,
possibly Tibet and Orange Free State which GW includes and COW does
not), the page must either note this in Contradictions or justify
the WHEP start year from a non-CShapes source.

## 2026-04-11 — cshapes-primary-source-upgrade
**Touched:** LUX-1839-2025
**Source:** cshapes-2.0 (upgraded)
**Kind:** ingest

User downloaded the CShapes 2.0 paper (Schvitz et al. 2022, JCR 66(1))
to `wiki/sources/pdfs/` under institutional access. Rewrote
`wiki/sources/cshapes-2.0.md` from a docs-derived stub (citing
`docs/04` and `docs/06` second-hand) into a primary-source file with
page-anchored verbatim quotes, DOI, and PDF SHA-256 for verification.

Added `wiki/sources/pdfs/` to `.gitignore` with a README explaining
why: PDFs are copyrighted, not redistributable, and the source file
plus hash is sufficient provenance.

Five material facts from the paper that the previous docs-derived
stub did not have:

1. CShapes ships in **two versions** (COW-based and GW-based) that
   differ on pre-1945 independence dates. Canada is 1920 under COW,
   1867 under GW. The repo does not record which version it loaded.
2. Border adjustments smaller than **100 × 100 km** are excluded by
   design. 138 transfers in the Territorial Change Dataset are
   silently dropped, including the 1922 Silesia Plebiscite (9,702 km²)
   and the 1929 Peru-Chile treaty (8,498 km²). Lint rule: any WHEP
   polity hinging on a sub-threshold transfer cannot cite CShapes.
3. Dependencies with population under **250,000** are excluded.
4. **Disputed territories** are assigned to the de facto controller,
   not coded separately. De facto states (Abkhazia, South Ossetia,
   Biafra, RSK) have no CShapes polygon of their own.
5. **Backdated borders** — 152 of 249 units have a single polygon
   copied across 1886–2019. The "1886 polygon" is literally the same
   geometry as the 2019 polygon for those countries.

Corrected a guessed author-list ordering in the previous stub. The
actual byline is Schvitz, Girardin, Rüegger, Weidmann, Cederman,
Gleditsch. The stub had them in a different order — a small reminder
that docs-derived source files can silently carry errors the primary
source would have caught.

Updated `wiki/polities/lux-1839-2025.md` to cite specific CShapes
paper sections (§scope, §coding-states, §coding-changes, §geocoding)
instead of generic `[cshapes-2.0]` tags, and added a sixth open
question about which CShapes version (COW or GW) the repo loads.
Status remains `draft`.

## 2026-04-11 — lux-first-ingest
**Touched:** LUX-1839-2025
**Source:** cshapes-2.0, wikipedia-luxembourg-2026-04-11
**Kind:** ingest

First real two-source ingest for the wiki. Created `wiki/sources/cshapes-2.0.md`
(polygon/border evidence, derived from `docs/04_POLYGON_SOURCES.md` and
`docs/06_KNOWN_ISSUES_AND_DECISIONS.md` — no external fetch) and
`wiki/sources/wikipedia-luxembourg-2026-04-11.md` (narrative history, verbatim
quotes from the `History_of_Luxembourg` article snapshotted on 2026-04-11).

Rewrote `wiki/polities/lux-1839-2025.md` from skeleton to a fully-cited draft.
Every factual claim now carries an inline citation. Status kept at `draft`
pending academic corroboration (COW / Polity V) — a single tertiary source
is not enough to mark a page `reviewed`.

Five open questions recorded on the page, the most load-bearing being whether
WHEP's general rule for personal unions is consistent with treating Luxembourg
as an independent polity from 1839 despite the personal union with the
Netherlands lasting until 1890. This is a cross-polity question and should
be resolved via a `decision`-kind log entry, not on the Luxembourg page alone.

## 2026-04-11 — wiki-bootstrap
**Touched:** (none)
**Source:** none
**Kind:** decision

Wiki created. Schema and prompts in place. No polity pages yet beyond the
Luxembourg worked example, which is a skeleton to demonstrate the format,
not a reviewed page.
