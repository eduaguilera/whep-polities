#!/bin/bash
# Rebuild every derived artifact from the wiki:
#   1. data/final/polities_database.{csv,gpkg}  (from wiki frontmatter +
#      raw sources under data/geodata/)
#   2. site/polities.{csv,geojson}              (simplified for web)
#   3. site/wiki/                               (markdown copy for the
#                                                in-browser reader)
#   4. data/compiled/pre1961/*                  (pre-1961 agricultural
#                                                crosslinks — ONLY if R is
#                                                available; reads the fresh
#                                                site/polities.geojson so its
#                                                no-polygon flags stay in sync)
#   5. site/pre1961/*                           (re-copied after step 4)
#
# Prerequisite: raw polygon sources fetched into data/geodata/<slug>/.
# See scripts/sources/<slug>/fetch.* to (re)download them.
set -euo pipefail
PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ_ROOT"

# Steps 1-3: master DB + site.
python3 scripts/build_database.py "$@"
bash site/build_wiki.sh

# Step 4: pre-1961 crosslink (optional, R-dependent). Re-run so that its
# no-polygon-by-year flags reflect the polygons now in site/polities.geojson.
if command -v Rscript > /dev/null 2>&1 && [ -f data/external/before_1961.csv ]; then
  echo
  echo "Running pre-1961 agricultural crosslink (pipelines/pre1961-matching/match.R)..."
  Rscript pipelines/pre1961-matching/match.R > /dev/null 2>&1 \
    && echo "  pre-1961 crosslink done." \
    || { echo "  WARN: match.R failed; site/pre1961/ may be stale." >&2; }
  # Re-run build_wiki.sh to propagate the refreshed data/compiled/pre1961/
  # files into site/pre1961/.
  bash site/build_wiki.sh > /dev/null 2>&1
  echo "  site/pre1961/ refreshed from data/compiled/pre1961/."
else
  echo
  echo "Skipping pre-1961 crosslink (need Rscript + data/external/before_1961.csv)."
fi
