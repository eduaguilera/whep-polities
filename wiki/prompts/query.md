# Query prompt

Use this when you want to answer a research question from the wiki
without editing the database.

---

You are answering a question from the WHEP polities wiki. Read
`wiki/README.md` for the schema, rules, the coverage goal
(complete spatiotemporal coverage — no gaps), and the
dual-renderer rule (GitHub + Obsidian — inline links only,
no reference-style defs).

**The wiki is the primary source of truth.** When answering questions,
trust the wiki's sourced claims over the CSV. If the CSV contradicts
a sourced wiki claim, the CSV is the one that needs updating.

1. **Scope the question.** Identify which polity pages, source files,
   and log entries are relevant. Prefer `wiki/polities/` and
   `wiki/sources/` over `docs/` — `docs/` is methodology, the wiki is
   evidence.

2. **Synthesize from sourced claims only.** Every factual sentence in
   your answer must trace to a `[source-slug §...]` or `[database]`
   citation that already exists in the wiki. If you cannot find one,
   say so explicitly and list the gap under *What the wiki doesn't
   know*.

3. **Surface contradictions.** If the answer depends on a point where
   sources disagree, show both positions and which one the database
   currently follows.

4. **File discoveries back.** If answering the question required you
   to notice a fact that isn't yet on a polity page — but it IS
   supported by a source already ingested — add it to that page's
   *Sourced claims* and append a short `lint`-kind entry to `log.md`.
   If the fact is NOT supported by an ingested source, add it to the
   page's *Open questions* instead.

5. **Never invent citations.** If the wiki doesn't have the answer,
   the correct response is "the wiki doesn't know, here's what ingest
   would need to fill the gap."

Output format for the user:
- **Answer** — 1–3 paragraphs, cited.
- **Confidence** — high / medium / low, with reasoning.
- **What the wiki doesn't know** — the gaps a future ingest should fill.
