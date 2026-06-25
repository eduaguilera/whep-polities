#!/usr/bin/env python3
"""Consolidate textracted FAO/IIA yearbook footnotes into one long table.

Walks the per-source/year/topic/commodity tree of ``footers_*.xlsx`` files and
emits one row per footnote text, with provenance parsed from the path. This is
step 1 of the footnote -> polity-territory pipeline; later steps segment the
text by marker and run LLM structured extraction (see README.md).

Usage:
    python3 consolidate_footnotes.py [INPUT_DIR] [OUTPUT_DIR]

Defaults:
    INPUT_DIR  = ~/Nextcloud/WHEP_ERC 2025/Sources/datasets/textracted_footnotes
    OUTPUT_DIR = ~/Nextcloud/whep/footnote_territory
"""

import os
import re
import sys
import csv
import glob

import openpyxl

DEFAULT_IN = os.path.expanduser(
    "~/Nextcloud/WHEP_ERC 2025/Sources/datasets/textracted_footnotes"
)
DEFAULT_OUT = os.path.expanduser("~/Nextcloud/whep/footnote_territory")

TOPICS = ["population", "livestock", "land_use", "land_uses", "land",
          "crops", "trade", "inputs"]

# High-value, directly-actionable territorial language (EN + FR).
BOUNDARY = re.compile(
    r"(pre-?war|post-?war|present boundar|former boundar|present-day|"
    r"avant-guerre|apr[eè]s-guerre|fronti[eè]res actuelles|"
    r"territoire d|new boundar|nouvelles fronti)", re.I)
NAMED = re.compile(
    r"(included? (under|in|with)|compris (dans|avec)|non compris l|"
    r"excluding |exclud.{0,20}(the )?[A-Z])", re.I)


def parse_meta(path, base):
    rel = os.path.relpath(path, base)
    parts = rel.split(os.sep)
    top = parts[0]
    source = "fao" if top.startswith("fao") else ("iia" if top.startswith("iia") else top)
    ym = re.search(r"_(\d{4})", rel)
    year = ym.group(1) if ym else ""
    topic = next((t for t in TOPICS if t in rel), "")
    leaf = os.path.basename(os.path.dirname(path))
    # commodity / page-range live in the leaf dir name, e.g. fao_crops_1961_39_40_barley
    pages = re.findall(r"_(\d+)_(\d+)_", leaf)
    page_range = "-".join(pages[0]) if pages else ""
    commodity = re.sub(r"^.*?\d+_\d+_", "", leaf) if pages else leaf
    return source, year, topic, commodity, page_range, leaf, rel


def main():
    in_dir = os.path.expanduser(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    out_dir = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(in_dir, "**", "*.xlsx"), recursive=True))
    rows = []
    for f in files:
        source, year, topic, commodity, page_range, leaf, rel = parse_meta(f, in_dir)
        try:
            wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        except Exception as e:  # noqa: BLE001 - skip unreadable OCR exports
            print(f"WARN: cannot read {rel}: {e}", file=sys.stderr)
            continue
        for ws in wb.worksheets:
            for r in ws.iter_rows(values_only=True):
                if not r:
                    continue
                d = list(r) + [None] * (3 - len(r))
                text = d[2]
                if not text or not str(text).strip():
                    continue
                if str(text).strip().lower() == "footer_text":
                    continue
                t = str(text).strip()
                rows.append({
                    "source": source, "year": year, "topic": topic,
                    "commodity": commodity, "page_range": page_range,
                    "page_number": d[0], "table_number": d[1],
                    "footer_text": t,
                    "has_boundary_vintage": bool(BOUNDARY.search(t)),
                    "has_named_territory": bool(NAMED.search(t)),
                    "rel_path": rel,
                })

    out_csv = os.path.join(out_dir, "footnotes_consolidated.csv")
    cols = ["source", "year", "topic", "commodity", "page_range", "page_number",
            "table_number", "footer_text", "has_boundary_vintage",
            "has_named_territory", "rel_path"]
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    # Optional parquet if pandas+pyarrow are present.
    try:
        import pandas as pd
        pd.DataFrame(rows, columns=cols).to_parquet(
            os.path.join(out_dir, "footnotes_consolidated.parquet"), index=False)
    except Exception:  # noqa: BLE001
        pass

    nb = sum(r["has_boundary_vintage"] for r in rows)
    nn = sum(r["has_named_territory"] for r in rows)
    print(f"files: {len(files)}  footnote rows: {len(rows)}")
    print(f"boundary-vintage notes: {nb}  named-territory notes: {nn}")
    print(f"wrote: {out_csv}")


if __name__ == "__main__":
    main()
