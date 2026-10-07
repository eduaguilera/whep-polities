#!/usr/bin/env python3
"""Consolidate textracted FAO/IIA yearbook and Mitchell footnotes into one table.

Walks the per-source/year/topic/commodity tree of ``footers_*.xlsx`` files and
emits one row per footnote text, with provenance parsed from the path. This is
step 1 of the footnote -> polity-territory pipeline; later steps segment the
text by marker and run LLM structured extraction (see README.md).

Mitchell (*International Historical Statistics*, the Africa/Asia/Oceania and
Americas agriculture volumes) is a third input (issue 689). Its 12
``footers_page<a>-<b>.xlsx`` files sit beside the extracted workbooks under
``sources_original/mitchell/Agriculture without Europe data/page<a>-<b>/`` and
have the same three columns. Their rows are appended AFTER the FAO/IIA rows,
so the row index that ``prepare_batches.py`` uses as the note id is unchanged
for every FAO/IIA note. For Mitchell, ``commodity`` is the workbook stem
(``page51-100``, the layer-B ``source_detail`` without ``.xlsx``) and
``page_number`` / ``table_number`` are workbook-local, the same numbering as
layer B's ``indicator`` (``page_<n>_table_<m>``) in that workbook. Rows that
only say "See p. N for footnotes" (a pointer to a book page whose notes were
not extracted) or are blank carry no note and are counted, not emitted.

Usage:
    python3 consolidate_footnotes.py [INPUT_DIR] [OUTPUT_DIR] [MITCHELL_DIR]

Defaults:
    INPUT_DIR    = ~/Nextcloud/WHEP_ERC 2025/Sources/datasets/textracted_footnotes
    OUTPUT_DIR   = ~/Nextcloud/whep/footnote_territory
    MITCHELL_DIR = ~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_original/mitchell
                   (pass "-" to skip it)
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
DEFAULT_MITCHELL = os.path.expanduser(
    "~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_original/mitchell"
)
# A Mitchell footer row that only points to the book page holding the notes.
POINTER = re.compile(r"^\s*see p\.?\s*\d+\s*for footnotes\.?\s*$", re.I)

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


def _sheet_rows(path):
    """Yield (page_number, table_number, text) for each non-header row."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            if not r:
                continue
            d = list(r) + [None] * (3 - len(r))
            if d[2] is not None and str(d[2]).strip().lower() == "footer_text":
                continue
            yield d[0], d[1], d[2]


def _row(source, year, topic, commodity, page_range, page, table, t, rel):
    return {
        "source": source, "year": year, "topic": topic,
        "commodity": commodity, "page_range": page_range,
        "page_number": page, "table_number": table,
        "footer_text": t,
        "has_boundary_vintage": bool(BOUNDARY.search(t)),
        "has_named_territory": bool(NAMED.search(t)),
        "rel_path": rel,
    }


def mitchell_rows(mitchell_dir):
    """Footnote rows from Mitchell's ``footers_page*.xlsx`` (issue 689)."""
    files = sorted(glob.glob(os.path.join(mitchell_dir, "**", "footers_*.xlsx"),
                             recursive=True))
    rows, n_pointer, n_blank = [], 0, 0
    for f in files:
        rel = os.path.join("mitchell", os.path.relpath(f, mitchell_dir))
        stem = os.path.basename(os.path.dirname(f))  # e.g. page51-100
        pr = re.search(r"(\d+)-(\d+)", stem)
        page_range = f"{pr.group(1)}-{pr.group(2)}" if pr else ""
        for page, table, text in _sheet_rows(f):
            if text is None or not str(text).strip():
                n_blank += 1
                continue
            t = str(text).strip()
            if POINTER.match(t):
                n_pointer += 1
                continue
            rows.append(_row("mitchell", "", "agriculture", stem, page_range,
                             page, table, t, rel))
    return files, rows, n_pointer, n_blank


def main():
    in_dir = os.path.expanduser(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    out_dir = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    mitchell_dir = (os.path.expanduser(sys.argv[3]) if len(sys.argv) > 3
                    else DEFAULT_MITCHELL)
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(in_dir, "**", "*.xlsx"), recursive=True))
    rows = []
    for f in files:
        source, year, topic, commodity, page_range, leaf, rel = parse_meta(f, in_dir)
        try:
            sheet = list(_sheet_rows(f))
        except Exception as e:  # noqa: BLE001 - skip unreadable OCR exports
            print(f"WARN: cannot read {rel}: {e}", file=sys.stderr)
            continue
        for page, table, text in sheet:
            if not text or not str(text).strip():
                continue
            rows.append(_row(source, year, topic, commodity, page_range,
                             page, table, str(text).strip(), rel))

    # Mitchell goes last so the FAO/IIA row indices (the note ids) stay stable.
    m_files, m_rows, m_pointer, m_blank = [], [], 0, 0
    if mitchell_dir != "-" and os.path.isdir(mitchell_dir):
        m_files, m_rows, m_pointer, m_blank = mitchell_rows(mitchell_dir)
        rows.extend(m_rows)
    elif mitchell_dir != "-":
        print(f"WARN: Mitchell dir not found, skipped: {mitchell_dir}",
              file=sys.stderr)

    out_csv = os.path.join(out_dir, "footnotes_consolidated.csv")
    cols = ["source", "year", "topic", "commodity", "page_range", "page_number",
            "table_number", "footer_text", "has_boundary_vintage",
            "has_named_territory", "rel_path"]
    tmp = out_csv + ".tmp"
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, out_csv)

    # Optional parquet if pandas+pyarrow are present.
    try:
        import pandas as pd
        pd.DataFrame(rows, columns=cols).to_parquet(
            os.path.join(out_dir, "footnotes_consolidated.parquet"), index=False)
    except Exception:  # noqa: BLE001
        pass

    nb = sum(r["has_boundary_vintage"] for r in rows)
    nn = sum(r["has_named_territory"] for r in rows)
    print(f"files: {len(files)}  footnote rows: {len(rows) - len(m_rows)}")
    if m_files:
        print(f"mitchell files: {len(m_files)}  rows: "
              f"{len(m_rows) + m_pointer + m_blank}  notes kept: {len(m_rows)}  "
              f"'See p. N' pointers: {m_pointer}  blank: {m_blank}")
    print(f"boundary-vintage notes: {nb}  named-territory notes: {nn}")
    print(f"wrote: {out_csv}")


if __name__ == "__main__":
    main()
