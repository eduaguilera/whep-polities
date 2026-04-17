#!/bin/bash
# Build the 'constructed' polygons.
#
# This source is **derived** from other fetched sources — no external file
# to download. It runs scripts/sources/constructed/build.py, which unions
# / intersects / dissolves features from cshapes-2.0 and similar to
# produce polygons for WHEP rows that don't map cleanly to a single
# external feature.
#
# Prerequisite: upstream raw sources (e.g. cshapes-2.0) must be fetched
# first. See scripts/sources.yaml for the dependency set.
set -euo pipefail
PROJ_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJ_ROOT"
python3 scripts/sources/constructed/build.py
