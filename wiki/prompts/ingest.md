# Ingest prompt

Use this when a new raw source (atlas, HGIS release, paper, dataset,
gazetteer) should be added to the wiki.

---

You are maintaining the WHEP polities wiki. Read `wiki/README.md` first
for the schema, rules, and the **coverage goal** (complete
spatiotemporal coverage — every km², every year, no gaps).

**Markdown dual-compatibility rule.** The wiki renders in both GitHub
and Obsidian. Key constraints:
- Never use `<a id="...">` HTML anchors — Obsidian ignores them.
- Never use `../` directory prefixes in links — Obsidian can't resolve
  them. Use filename-only paths: `(cshapes-2.0.md#scope)` not
  `(../sources/cshapes-2.0.md#scope)`.
- Never use reference-style link definitions — Obsidian can't navigate
  them. Use inline links: `[text](file.md#anchor)`.
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
   `data/final/polities_database.csv` — if the source names a polity
   that has no CSV row, do NOT create a page; instead add an entry to
   `wiki/log.md` of kind `proposal` with the rationale for adding it.

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

**Constraints:**
- Never edit `data/final/polities_database.csv`. Changes to the CSV go
  through a `proposal`-kind log entry that a human applies later.
- Never invent a citation. If a claim has no source, mark it `[database]`
  or move it to *Open questions*.
- Sources are immutable. If the source itself is wrong, add a new source
  that supersedes it rather than editing the old file.
