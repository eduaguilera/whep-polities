# Ingest prompt

Use this when a new raw source (atlas, HGIS release, paper, dataset,
gazetteer) should be added to the wiki.

---

You are maintaining the WHEP polities wiki. Read `wiki/README.md` first
for the schema, rules, and the **coverage goal** (complete
spatiotemporal coverage — every km², every year, no gaps).

**The wiki is the primary source of truth.** It is built on cited
academic sources. The CSV (`data/final/polities_database.csv`) must
conform to the wiki's findings, not the other way around. When your
sourced research contradicts the CSV, file a `proposal`-kind log entry
recommending the CSV be updated. Do not adapt the wiki to match CSV
errors.

**Markdown dual-compatibility rule.** The wiki renders in both GitHub
and Obsidian. Key constraints:
- Never use `<a id="...">` HTML anchors — Obsidian ignores them.
- Never use reference-style link definitions (`[ref]: url` at the
  bottom) — Obsidian can't navigate them. Use inline links only:
  `[text](../sources/file.md#anchor)`.
- Standard `../` relative paths are fine in inline links.
- Log entries: `## slug` (date on a `**Date:**` line inside the body).
- Source sections: `### section-name` (no `§` prefix in the heading;
  `§` is display-only in inline citations like `[source §section]`).

Then:

1. **Create the source file.** Copy `wiki/sources/_template.md` to
   `wiki/sources/<source-slug>.md` and fill the frontmatter and all
   three sections. Do not invent fields you cannot verify from the
   source itself.

2. **Identify affected polity pages.** From the source, list the
   polity codes whose pages should be updated. The CSV at
   `data/final/polities_database.csv` is a **derived artifact** rebuilt
   by `scripts/build_database.py` from the wiki's frontmatter — never
   hand-edit it. If the source establishes a polity that has no wiki
   page yet, create the page and re-run the builder. If the source's
   dates or chain structure contradict an existing wiki page, the source
   wins: update the page, rename/split/merge as needed, and log each
   change in `log.md`.

   While you are cross-checking against the current CSV, **audit the
   rows you are about to cite**. Under the critical-stance rule in
   `wiki/README.md`, any derived artifact is evidence, not authority.
   Watch for:

   - Row labels that contradict their time range (e.g.
     `F228-1905-1914 USSR (1905-1914)` — the USSR did not exist
     until 1922).
   - Overlapping rows for the same entity across the period your
     source covers.
   - Missing rows for entities that your source clearly describes
     (e.g. a major state referenced by the source that has no CSV
     counterpart).
   - Splits at dates that don't match a historical event in your
     source.
   - `notes = NA` on rows where your source has substantive content.

   For each audit finding: check `wiki/log.md` for a prior rationale.
   If you find one, cite it. If you don't, add a `proposal`-kind log
   entry before proceeding with the ingest. Do not rationalize the
   finding in the polity page body — hedge explicitly that the labeling
   is suspect and flag the proposal by slug.

3. **Check predecessor/successor completeness.** For every polity
   page you create or update, verify that its predecessors and
   successors form a closed chain — all territory must be accounted
   for. If a predecessor or successor row exists in the CSV but has
   no wiki page, add a `<!-- TODO: page not yet created -->` reference
   link and note it as a dangling ref in the log entry. If a
   predecessor or successor *doesn't exist in the CSV at all* despite
   being expected (e.g. a dissolution that should produce 5 successor
   states but the CSV only has 3), add a `proposal`-kind log entry.

4. **Update each affected polity page.** For each one:
   - Append new facts to *Sourced claims* with inline
     `[<source-slug> §<section>]` citations.
   - If the new source disagrees with an existing claim, add both
     positions to *Contradictions* — never silently overwrite.
   - Update `last_ingest` and add the source slug to `sources:`.
   - If a page doesn't exist yet for a polity in the CSV that this
     source covers, create it from `_template.md` with status `draft`.

5. **Append a log entry.** In `wiki/log.md`, add a new H2 of kind
   `ingest` listing every polity code touched and one or two
   sentences on what the source contributed and any open contradictions.

6. **Update `wiki/index.md`** if any new polity pages were created or
   the source list changed.

7. **Rebuild derived artifacts** if any frontmatter was edited:
   ```bash
   bash scripts/rebuild.sh   # → data/final/ + site/
   ```
   (Wraps `python3 scripts/build_database.py` + `bash site/build_wiki.sh`.)
   If a polity page cites a `polygon_source` whose raw file isn't on
   disk yet, first run the matching `scripts/sources/<slug>/fetch.*`.
   The builder logs missing sources/features but doesn't abort.

**Quality gate:** Every polity page must contain at least one sourced
claim from an external source beyond `[database]`. Never bulk-generate
pages from CSV metadata alone — that creates empty shells that violate
the wiki's role as the primary source of truth.

**Polygon binding gate:** Every polity page has two coupled pieces
of polygon information — machine-readable frontmatter (consumed by
`scripts/build_database.py`) and human-readable prose (in
`## Territorial extent`). Both must be kept in sync. See
`wiki/polities/_template.md` for the exact field list and
`wiki/README.md` → "Polygon workflow" for semantics.

**Frontmatter fields** (required on every page):
```yaml
polygon_source:       <slug registered in scripts/sources.yaml, or `none`>
polygon_feature_id:   <value matching that source's id_column>
polygon_feature_year: <int, only if the source has a temporal block>
polygon_status:       assigned | proxy | missing | excluded
polygon_area_km2:     <int, optional; ETRS89 LAEA for Europe, equivalent equal-area elsewhere>
```

If `polygon_source` names a slug that isn't in `sources.yaml`, the
ingest must add the source first (new `scripts/sources.yaml` entry +
`scripts/sources/<slug>/fetch.{sh,R}` + description on the page's
source). That kind of change is script-editing work — treat it as a
script update, not a wiki-only ingest, and include it in the same
commit.

**Prose in `## Territorial extent`** must back up the frontmatter with:

1. **Which features are included**, and **which were deliberately
   excluded** (and why). For dissolve-style sources like
   `histogis-1860-habsburg`, enumerate the crownlands.
2. **If a proxy was deliberately NOT used**, explain why with km²
   numbers showing the territory mismatch (e.g., "post-Trianon Hungary
   is ~93k km² vs Transleithania ~325k km² — a 71% loss"). Prevents
   a future maintainer from "helpfully" copying the wrong polygon.
3. **"Why this entry exists"** — what data drove its creation, what it
   was previously matched to and why that was wrong, and what external
   source confirms the entity was distinct.

Boilerplate like "No polygon assigned yet" without reasoning is
unacceptable; prefer `polygon_status: missing` in frontmatter plus a
prose paragraph explaining the gap. The wiki must record *decisions*,
not just *status*.

**Chain restructure methodology** (for umbrella rows and legacy chains):
1. Fetch CShapes 2.0 if not on disk:
   `bash scripts/sources/cshapes-2.0/fetch.sh`. Then query for the
   polity's time-steps:
   `ogrinfo -sql "SELECT gwcode,gwsyear,gweyear,cntry_name,area FROM \"CShapes-2.0\" WHERE gwcode=<N>" data/geodata/cshapes-2.0/CShapes-2.0.shp`.
   This gives exact dates and areas for every boundary change.
   (CShapes 2.0 uses Gleditsch-Ward codes only; for most countries
   G-W == COW, but verify when they differ.)
2. Cross-reference with Biger (already ingested) for historical context,
   treaty names, and boundary descriptions.
3. Fetch Wikipedia for exact dates CShapes or Biger don't provide.
   Create a `wikipedia-<country>-<date>.md` source file.
4. Build the chain from sourced findings: split only at real territorial
   changes (area changes in CShapes), not at regime changes (same area).
   Merge administrative CShapes splits that show no area change. If all
   CShapes time-steps have the same area and the polity existed
   continuously, the correct result is **one row** for the entire
   period — regardless of how many CShapes entries exist.
5. **No overlapping rows.** Never create an "umbrella" row alongside
   sub-rows. Every km² belongs to exactly one row for any given year.
   If the sub-chain doesn't cover the full period, either extend a
   sub-row or create a new row for the gap — do not keep a broad
   umbrella row that overlaps.
6. Create/modify wiki pages for each row in the new chain. Set
   `polygon_feature_id` to the matching gwcode and `polygon_feature_year`
   to the CShapes time-step's `gwsyear`. Update predecessor/successor
   frontmatter and prose. Delete obsolete pages.
7. Rerun `bash scripts/rebuild.sh` to propagate the chain through to
   `data/final/polities_database.{csv,gpkg}` and the site.

**Constraints:**
- `data/final/polities_database.csv` is **never hand-edited** — it is
  regenerated from the wiki by `scripts/rebuild.sh`. Drive changes by
  editing wiki frontmatter/body and rerunning the rebuild.
- Never invent a citation. If a claim has no source, mark it `[database]`
  or move it to *Open questions*.
- Sources are immutable. If the source itself is wrong, add a new source
  that supersedes it rather than editing the old file.
