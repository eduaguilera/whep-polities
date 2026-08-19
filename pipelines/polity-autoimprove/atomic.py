"""Atomic CSV replacement for the tracked state files that hold adjudications.

WHY THIS EXISTS. `open(path, "w")` and `pandas.to_csv(path)` both truncate on open, so a failure
between the truncate and the last row leaves a tracked file half-written. That has cost this
repository two state files already, which is why every tool from `16_source_splices.py` onward
builds its output in memory and then `os.replace`es it.

That lesson never reached the OLDER tools, and issue 431 measured where it matters. Verified per
write site, four truncating writes target a tracked file holding work that cannot be re-derived:

    01_match_and_findings.py    review_ledger.csv
    02_territorial_evidence.py  review_ledger.csv
    apply_verdicts.py           review_ledger.csv
    reconcile_quarantine.py     quarantine.csv

`review_ledger.csv` carries every verification decision ever banked and is truncated by THREE
separate tools. Two of them (01, 02) are worse than a plain truncate: they read the ledger, edit it
in memory and write it back over itself, so a failure between the read and the last row loses the
file rather than corrupting it.

`os.replace` is atomic within a filesystem, so the temporary file is created in the SAME directory
as the target rather than in /tmp -- a cross-device replace is not atomic and would silently
reintroduce the window this closes.

Not used by the seven regenerable measurement tables (issue 431 lists them). A truncation there is
repaired by re-running the tool, so the churn is not worth it.
"""
from __future__ import annotations

import csv
import os
import tempfile


def write_csv_atomic(path: str, fieldnames, rows) -> None:
    """Write `rows` to `path` via a same-directory temp file and an atomic replace.

    `rows` is materialised before anything is written, so a generator that raises part-way cannot
    leave a partial file: the exception escapes with the original `path` untouched.
    """
    rows = list(rows)
    fieldnames = list(fieldnames)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
