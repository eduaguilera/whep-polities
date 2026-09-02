#!/usr/bin/env python3
"""Tests for the agent harness. Every case here is a regression for a bug the smoke run found.

A harness whose only test is "it produced something" cannot tell a good verdict from a plausible one
built on corrupted evidence -- which is the failure this suite exists to prevent. Each test names the
bug it pins.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


runner = _load("runner")
harness = _load("harness")


def test_cli_schema_strips_only_what_the_cli_rejects():
    """BUG: the CLI exits 1 on `$schema` and on conditional subschemas.

    The projection must drop those and NOTHING else -- dropping `required` or `properties` would
    stop the model being told the shape at all.
    """
    full = json.loads((HERE / "schemas" / "routing_verdict.schema.json").read_text())
    cli = runner.cli_schema(full)
    assert "$schema" not in cli and "allOf" not in cli
    for kept in ("type", "properties", "required", "additionalProperties"):
        assert kept in cli, kept
    # The contract keeps the conditionals: a match verdict naming no code must still be rejected.
    from jsonschema import Draft202012Validator
    v = Draft202012Validator(full)
    assert not v.is_valid({"unit_id": "U", "verdict": "match_existing", "confidence": "high",
                           "reasoning": "x" * 45, "evidence_used": ["a"]})


def test_iso_resolution_does_not_confuse_united_states_with_the_emirates():
    """BUG: a 6-character prefix match resolved 'United States of America' to ARE.

    The verdicts that followed were plausible and built on another country's candidate rows.
    """
    pols = [
        {"polity_code": "ARE-1971-2025", "polity_name": "United Arab Emirates",
         "iso3_code": "ARE", "polity_type": "national", "start_year": "1971", "end_year": "2025"},
        {"polity_code": "USA-1959-2025", "polity_name": "United States of America (1959-2025)",
         "iso3_code": "USA", "polity_type": "national", "start_year": "1959", "end_year": "2025"},
    ]
    assert harness.iso_for_country("United States of America", pols) == "USA"
    assert harness.iso_for_country("United Arab Emirates", pols) == "ARE"
    # An unresolvable country returns "" so the caller can refuse rather than guess a stem.
    assert harness.iso_for_country("Ruritania", pols) == ""


def test_boundary_name_match_is_bidirectional():
    """BUG: the panel calls it 'US Alaska'; a one-directional substring test never matched 'Alaska'.

    Stage 2 had the reverse test and found USA.2_1 while stage 1 reported no boundary at all.
    """
    unit = {"unit_id": "USA-ALASKA", "admin_name": "US Alaska", "country": "United States of America",
            "admin_level": "state", "y0": 1960, "y1": 2025, "rows": 1753,
            "indicators": "area", "source": "USDA NASS Subnational"}
    ev = harness.build_evidence(unit, [], "USA", [("USA.2_1", "Alaska"), ("USA.5_1", "California")],
                                wide=False, sibling_verdicts=[])
    assert "USA.2_1 Alaska" in ev
    assert "USA.5_1" not in ev          # and it must not match everything
    # The length floor stops a short name matching inside an unrelated one.
    short = dict(unit, admin_name="Ohio")
    ev2 = harness.build_evidence(short, [], "USA", [("USA.9_1", "Ohio")], wide=False,
                                 sibling_verdicts=[])
    assert "USA.9_1 Ohio" in ev2


def test_subnational_candidates_are_never_omitted_from_cycle_one():
    """BUG: cycle 1 showed only national rows, hiding ALK-1867-1959 from the Alaska verdict.

    The single most likely `match_existing` candidate is a subnational row, so trimming those is
    exactly backwards. Only the earlier national eras may be trimmed.
    """
    pols = [{"polity_code": "ALK-1867-1959", "polity_name": "Territory of Alaska",
             "iso3_code": "USA", "polity_type": "subnational",
             "start_year": "1867", "end_year": "1959"}]
    pols += [{"polity_code": f"USA-{1800 + i * 10}-{1810 + i * 10}",
              "polity_name": f"United States ({1800 + i * 10})", "iso3_code": "USA",
              "polity_type": "national", "start_year": str(1800 + i * 10),
              "end_year": str(1810 + i * 10)} for i in range(20)]
    unit = {"unit_id": "USA-ALASKA", "admin_name": "US Alaska", "country": "USA",
            "admin_level": "state", "y0": 1960, "y1": 2025, "rows": 1,
            "indicators": "area", "source": "s"}
    ev = harness.build_evidence(unit, pols, "USA", [], wide=False, sibling_verdicts=[])
    assert "ALK-1867-1959" in ev, "a subnational candidate was trimmed on cycle 1"
    assert "trimmed on this cycle" in ev, "trimming must be declared, not silent"


def test_extract_accepts_the_string_envelope_and_rejects_invalid():
    """The CLI returns the payload as a STRING under `result`; a harness expecting an object fails.

    And an object that does not satisfy the contract must be rejected, not passed through.
    """
    from jsonschema import Draft202012Validator
    schema = json.loads((HERE / "schemas" / "routing_verdict.schema.json").read_text())
    v = Draft202012Validator(schema)
    good = {"unit_id": "U", "verdict": "not_a_territory", "confidence": "high",
            "reasoning": "x" * 45, "evidence_used": ["a"]}
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "stdout.json"
        p.write_text(json.dumps({"result": json.dumps(good), "is_error": False}))
        assert runner.ClaudeRunner._extract(p, v) == good
        p.write_text(json.dumps({"result": json.dumps({"verdict": "nonsense"})}))
        assert runner.ClaudeRunner._extract(p, v) is None
        p.write_text("not json at all")
        assert runner.ClaudeRunner._extract(p, v) is None


def test_ledger_round_trip_keeps_stage_two_columns():
    """BUG: stage-1 rows lack the stage-2 keys, and DictWriter raises on a missing field.

    The writer fills them, so a run that reaches stage 2 does not lose stage-1 rows.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        harness.LEDGER = Path(d) / "l.csv"
        harness.write_ledger({"U": {"unit_id": "U", "country": "C", "verdict": "create_new"}})
        back = harness.read_ledger()
        assert back["U"]["verdict"] == "create_new"
        assert back["U"]["polygon_route"] == ""
        for f in harness.LEDGER_FIELDS:
            assert f in back["U"], f


def test_throttle_regex_is_narrow():
    """A loose match would retry genuine schema failures, which are bugs to fix, not waits."""
    for hit in ("HTTP 429", "status: 429", "429 Too Many Requests", "overloaded_error",
                "Selected model is at capacity", "rate_limit_error"):
        assert runner.THROTTLE_RE.search(hit), hit
    for miss in ("schema validation failed", "temporarily unavailable", "slow rate of progress",
                 "invalid JSON in response"):
        assert not runner.THROTTLE_RE.search(miss), miss


def test_mutating_tools_are_denied_on_the_command_line():
    """A verdict-emitting agent must not edit the tree, and that is enforced by the command."""
    r = runner.ClaudeRunner(run_dir=Path("/tmp"))
    cmd = r._command('{"type":"object"}')
    assert "--disallowed-tools" in cmd
    for tool in ("Edit", "Write", "NotebookEdit"):
        assert tool in cmd, tool
    assert "--permission-mode" in cmd and "bypassPermissions" in cmd


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL  {name}: {exc}")
    print(f"\n{'FAIL' if failed else 'PASS'}: {failed} failing")
    sys.exit(1 if failed else 0)
