# R-legacy

Previous R scripts (`00_setup.R` through `25_final_fixes.R`) used to build
the WHEP polities database. **Not reproducible** — these scripts have
implicit inter-script ordering, rely on local GADM/CShapes paths, and
their outputs are already checked in at `data/final/polities_database.csv`
(the wiki is the maintained source of truth now, per `wiki/README.md`).

Kept here for provenance; new pipelines should live under
`pipelines/<name>/` with a self-contained README and a single entry
script.

Current maintained pipelines:

- `pipelines/pre1961-matching/` — crosslink the pre-1961 agricultural
  dataset with WHEP polity codes.
