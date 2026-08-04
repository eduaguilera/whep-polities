#!/usr/bin/env python3
"""The verification PROTOCOL version — declared in the workflow, read by scripts.

The substantive rules of verification (the historian prompt, the verdict schema,
the confirm_kind definition, the anti-circularity rule) live in
`verify_assertions.workflow.js`. So that is where `PROTOCOL_VERSION` is
DECLARED, and this module is the one place that parses it out for the Python
side of the pipeline:

  - `apply_verdicts.py` STAMPS it onto every ledger row it banks;
  - `00_intake.py` COMPARES it against each banked row and reopens the ones
    banked under an older protocol.

Direction of the dependency is forced: the workflow runs in a sandbox with no
filesystem access, so it cannot read a Python constant — but the scripts can
read the .js. And the value reaches the ledger BY SCRIPT, never by an agent
echoing a string, for exactly the reason `evidence_hash` is script-stamped: an
LLM transcribing an identifier is not a trustworthy record of what it did.
"""
import os, re

WORKFLOW = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "verify_assertions.workflow.js")
_RE = re.compile(r"^\s*export\s+const\s+PROTOCOL_VERSION\s*=\s*(\d+)", re.M)


def protocol_version(path=WORKFLOW):
    """Current verification protocol version (int), from the workflow file."""
    try:
        txt = open(path).read()
    except OSError as e:
        raise SystemExit(f"cannot read the verification workflow ({e}) — the "
                         "protocol version lives there and is not optional")
    m = _RE.search(txt)
    if not m:
        raise SystemExit(f"no `export const PROTOCOL_VERSION = <int>` in {path} "
                         "— the ledger cannot tell which rules a verdict was "
                         "produced under without it")
    return int(m.group(1))


def ledger_protocol_version(row):
    """Protocol version a ledger row was banked under; 0 when unstamped."""
    v = str((row or {}).get("protocol_version") or "").strip()
    return int(v) if v.isdigit() else 0
