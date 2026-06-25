#!/usr/bin/env python3
"""Split consolidated footnotes into per-batch JSON files for LLM extraction.

Step 2 input prep: reads ``footnotes_consolidated.csv`` and writes
``batch_NNN.json`` files (a list of ``{id, source, year, topic, commodity,
text}``) that the extraction agents (step 3) consume one batch each. ``id`` is
the consolidated-table row index, so extracted claims join back to provenance.

Usage:
    python3 prepare_batches.py [CONSOLIDATED_CSV] [OUT_DIR] [BATCH_SIZE]

Defaults:
    CONSOLIDATED_CSV = ~/Nextcloud/whep/footnote_territory/footnotes_consolidated.csv
    OUT_DIR          = ~/Nextcloud/whep/footnote_territory/batches
    BATCH_SIZE       = 22
"""

import os
import sys
import csv
import json

DEFAULT_CSV = os.path.expanduser(
    "~/Nextcloud/whep/footnote_territory/footnotes_consolidated.csv")
DEFAULT_OUT = os.path.expanduser(
    "~/Nextcloud/whep/footnote_territory/batches")


def main():
    src = os.path.expanduser(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    out = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    bs = int(sys.argv[3]) if len(sys.argv) > 3 else 22
    os.makedirs(out, exist_ok=True)

    rows = list(csv.DictReader(open(src)))
    notes = [{"id": i, "source": r["source"], "year": r["year"],
              "topic": r["topic"], "commodity": r["commodity"],
              "text": r["footer_text"]} for i, r in enumerate(rows)]
    batches = [notes[i:i + bs] for i in range(0, len(notes), bs)]
    for b, chunk in enumerate(batches):
        json.dump(chunk, open(os.path.join(out, f"batch_{b:03d}.json"), "w"),
                  ensure_ascii=False)
    print(f"notes={len(notes)} batches={len(batches)} (size {bs}) -> {out}")


if __name__ == "__main__":
    main()
