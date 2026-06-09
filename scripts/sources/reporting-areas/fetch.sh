#!/bin/bash
# Build derived WHEP reporting-area polygons.
#
# Prerequisite: GADM 4.1 component polygons must already be fetched with
# scripts/sources/gadm-4.1/fetch.sh.
set -euo pipefail
PROJ_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJ_ROOT"
python3 scripts/sources/reporting-areas/build.py
