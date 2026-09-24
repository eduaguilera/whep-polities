#!/usr/bin/env python3
"""The set of CI steps that SKIP must be exactly the set we have decided may skip.

A step that prints SKIP and exits 0 is green in the Actions summary, and green is what a working
check looks like. Three `--check` tools skip in CI BY DESIGN, because their inputs are gitignored or
live outside the repo:

    write_feature_index.py --check     the polygon sources in data/geodata/ are never committed
    44_border_stability.py --check     CShapes 2.0 is one of those sources
    08_source_stated_areas.py --check  the IIA/FAO area tables live in the project's Nextcloud

That is honest -- rebuilding from nothing would delete every row -- but it means those three verify
nothing in CI, and nothing distinguished them from a fourth that started skipping because an input
moved. The 2026-09-24 gate audit ran every CI command with HOME pointed nowhere and found exactly
these three skipping, all silently.

HOW. Each of the three prints a fixed token, `SKIP-IN-CI:`, and, when `$WHEP_CI_SKIP_LOG` is set
(validate.yml sets it for the whole job), appends its own file name to that log. This gate runs LAST
and requires the logged set to EQUAL the allowlist below:

  A. a tool that logs a skip and is not allowlisted fails -- a new skip is a decision, not a drift;
  B. an allowlisted tool that did NOT skip fails too -- its input became available in CI, so its
     --check now verifies something and the allowlist should say so (or the token was lost, and the
     skip went silent again);
  C. statically, everywhere: every .py file under scripts/ and pipelines/ that prints the token must
     be allowlisted, so a new SKIP-IN-CI is caught on a laptop before CI sees it.

Outside CI (`$WHEP_CI_SKIP_LOG` unset) arms A and B have nothing to read and say so; C still runs.

Usage:
  python3 scripts/validate_ci_skips.py
"""
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Written split so this file's own source does not contain the token it scans for.
TOKEN = "SKIP-IN" "-CI:"

# The tools that may skip in CI, by file name, and why. Bidirectional (arms A and B).
ALLOWLIST = frozenset({
    "write_feature_index.py",       # data/geodata/ polygon sources are gitignored
    "44_border_stability.py",       # CShapes 2.0 is one of them
    "08_source_stated_areas.py",    # IIA/FAO country-area tables live outside the repo
})


def static_declarers() -> set:
    """File names of every .py under scripts/ and pipelines/ whose source prints the token."""
    out = set()
    paths = glob.glob(os.path.join(REPO, "scripts", "*.py")) + glob.glob(
        os.path.join(REPO, "pipelines", "**", "*.py"), recursive=True)
    pat = re.compile(re.escape(TOKEN))
    for path in paths:
        if os.path.abspath(path) == os.path.abspath(__file__):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                if pat.search(fh.read()):
                    out.add(os.path.basename(path))
        except OSError:
            continue
    return out


def main() -> int:
    problems = []

    declared = static_declarers()
    for name in sorted(declared - ALLOWLIST):
        problems.append(f"C {name} prints {TOKEN} but is not in the allowlist -- a new CI skip is "
                        f"a decision: add it to ALLOWLIST with the reason, or make it verify")

    log = os.environ.get("WHEP_CI_SKIP_LOG")
    if not log:
        print(f"arms A/B: $WHEP_CI_SKIP_LOG unset (not CI), no skip log to compare; "
              f"arm C: {len(declared)} tool(s) declare {TOKEN}")
    else:
        skipped = set()
        if os.path.exists(log):
            with open(log, encoding="utf-8") as fh:
                skipped = {ln.strip() for ln in fh if ln.strip()}
        print(f"skipped in this run: {sorted(skipped) or 'none'}")
        print(f"allowlisted:         {sorted(ALLOWLIST)}")
        for name in sorted(skipped - ALLOWLIST):
            problems.append(f"A {name} skipped in CI but is not allowlisted -- it verified "
                            f"nothing and the step still showed green")
        for name in sorted(ALLOWLIST - skipped):
            problems.append(f"B {name} is allowlisted to skip but did not log a skip -- either its "
                            f"input is now available in CI (remove it from ALLOWLIST) or it lost "
                            f"the {TOKEN} token and skips silently again")

    if problems:
        print(f"FAIL: {len(problems)} CI-skip problem(s)")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"PASS: the CI steps that skip are exactly the {len(ALLOWLIST)} allowlisted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
