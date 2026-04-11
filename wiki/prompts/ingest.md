# Ingest prompt

Use this when a new raw source (atlas, HGIS release, paper, dataset,
gazetteer) should be added to the wiki.

---

You are maintaining the WHEP polities wiki. Read `wiki/README.md` first
for the schema and rules. Then:

1. **Create the source file.** Copy `wiki/sources/_template.md` to
   `wiki/sources/<source-slug>.md` and fill the frontmatter and all
   three sections. Do not invent fields you cannot verify from the
   source itself.

2. **Identify affected polity pages.** From the source, list the
   polity codes whose pages should be updated. Cross-check against
   `data/final/polities_database.csv` — if the source names a polity
   that has no CSV row, do NOT create a page; instead add an entry to
   `wiki/log.md` of kind `proposal` with the rationale for adding it.

3. **Update each affected polity page.** For each one:
   - Append new facts to *Sourced claims* with inline
     `[<source-slug> §<section>]` citations.
   - If the new source disagrees with an existing claim, add both
     positions to *Contradictions* — never silently overwrite.
   - Update `last_ingest` and add the source slug to `sources:`.
   - If a page doesn't exist yet for a polity in the CSV that this
     source covers, create it from `_template.md` with status `draft`.

4. **Append a log entry.** In `wiki/log.md`, add a new H2 of kind
   `ingest` listing every polity code touched and one or two
   sentences on what the source contributed and any open contradictions.

5. **Update `wiki/index.md`** if any new polity pages were created or
   the source list changed.

**Constraints:**
- Never edit `data/final/polities_database.csv`. Changes to the CSV go
  through a `proposal`-kind log entry that a human applies later.
- Never invent a citation. If a claim has no source, mark it `[database]`
  or move it to *Open questions*.
- Sources are immutable. If the source itself is wrong, add a new source
  that supersedes it rather than editing the old file.
