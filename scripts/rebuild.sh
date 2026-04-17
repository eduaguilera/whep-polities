#!/bin/bash
# Rebuild all derived artifacts from the wiki:
#   1. data/final/polities_database.{csv,gpkg}  (from wiki frontmatter +
#      raw sources under data/geodata/)
#   2. site/polities.{csv,geojson}              (simplified for web)
#   3. site/wiki/                               (markdown copy for the
#                                                in-browser reader)
#
# Prerequisite: raw polygon sources fetched into data/geodata/<slug>/.
# See scripts/sources/<slug>/fetch.* to (re)download them.
set -euo pipefail
PROJ_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ_ROOT"
python3 scripts/build_database.py "$@"
bash site/build_wiki.sh
