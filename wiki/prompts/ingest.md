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
   polity codes whose pages should be updated. Cross-check against
   `data/final/polities_database.csv`. If the source establishes that
   a polity existed (with sourced territorial extent and dates) but
   the CSV has no matching row, **create both the wiki page and the
   CSV row** — the wiki drives the CSV, not the reverse. Log the new
   row in `log.md`. If the source's dates or chain structure contradict
   the CSV's existing rows, the source wins: split, merge, or rename
   CSV rows to match the sourced findings and log each change.

   While you are cross-checking the CSV, **audit the rows you are
   about to cite**. Under the critical-stance rule in `wiki/README.md`,
   the CSV is evidence, not authority. Watch for:

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

   For each audit finding: check `docs/` and `wiki/log.md` for a
   prior rationale. If you find one, cite it. If you don't, add a
   `proposal`-kind log entry before proceeding with the ingest. Do
   not rationalize the finding in the polity page body — hedge
   explicitly that the CSV labeling is suspect and flag the proposal
   by slug.

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

7. **Rebuild the visualization site** if the CSV was edited: run
   `bash site/build.sh` from the project root. This updates
   `site/polities.csv` and `site/polities.geojson`.

**Quality gate:** Every polity page must contain at least one sourced
claim from an external source beyond `[database]`. Never bulk-generate
pages from CSV metadata alone — that creates empty shells that violate
the wiki's role as the primary source of truth.

**Chain restructure methodology** (for umbrella rows and legacy chains):
1. Query CShapes for the polity's time-steps (`ogrinfo -sql` on
   `cshapes2_full.gpkg` by cowcode). This gives exact dates and areas
   for every boundary change.
2. Cross-reference with Biger (already ingested) for historical context,
   treaty names, and boundary descriptions.
3. Fetch Wikipedia for exact dates CShapes or Biger don't provide.
   Create a `wikipedia-<country>-<date>.md` source file.
4. Build the chain from sourced findings: split only at real territorial
   changes (area changes in CShapes), not at regime changes (same area).
   Merge administrative CShapes splits that show no area change.
5. Delete old CSV rows (umbrella + legacy sub-rows), create new rows
   matching the sourced chain. Update predecessor/successor fields.
6. Create wiki pages for each new row. Delete old pages.

**Constraints:**
- The agent maintains `data/final/polities_database.csv` directly when
  the wiki's sourced findings require changes. Log each CSV edit in
  `log.md`.
- Never invent a citation. If a claim has no source, mark it `[database]`
  or move it to *Open questions*.
- Sources are immutable. If the source itself is wrong, add a new source
  that supersedes it rather than editing the old file.
