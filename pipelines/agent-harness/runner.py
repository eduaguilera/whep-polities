#!/usr/bin/env python3
"""Own the agent subprocess: one schema-validated result per job, cached and retried.

WHY A HARNESS WE OWN. The agent loops in this repository were `.workflow.js` scripts driven by an
external orchestrator. That made the decisions untestable from here, the model's output trusted
rather than validated, and the whole loop unavailable to anything but an interactive session. This
module is the replacement: a subprocess we launch, a schema the model MUST satisfy, and a result we
either validate or reject.

EVERY DEFENCE BELOW EXISTS BECAUSE THE OBVIOUS IMPLEMENTATION FAILS IN PRODUCTION:

  * OUTPUT GOES TO FILES, NEVER TO PIPES. Tool descendants inherit the CLI's stdout and stderr
    descriptors, so `communicate()` blocks on descendant-held pipe EOF long after the CLI itself has
    exited. A harness that pipes stdout hangs on exactly the jobs that did the most work.
  * A TIMEOUT IS NOT PROOF OF FAILURE. The CLI can durably write a schema-valid result and then be
    held open by a descendant. Deleting that proven output forces an identical expensive retry, so a
    timeout first checks for a valid result already on disk and keeps it.
  * THROTTLE DETECTION IS DELIBERATELY NARROW. Only unambiguous capacity signals retry. Matching
    loose words like "rate" or "unavailable" would silently retry genuine schema failures, which are
    a bug to fix rather than a condition to wait out.
  * ABORTING KILLS THE GROUP. `start_new_session=True` plus `killpg` reaps every command the agent
    launched; otherwise an interrupted run leaves children writing to the tree behind us.
  * IDENTICAL WORK IS NOT REPEATED. A job is fingerprinted over (prompt, schema, model, effort). Re-
    running a cycle re-uses proven results and spends tokens only on what actually changed.

READ-ONLY BY CONSTRUCTION. The mutating tools are denied on the command line rather than trusted to
the prompt, because a verdict-emitting agent has no business editing the tree. Applying verdicts is
this harness's job, in Python, where it can be tested.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parent.parent.parent

# Only unambiguous transient capacity failures. See the module docstring on why this is not loose.
THROTTLE_RE = re.compile(
    r"(?:\bHTTP(?:/\d(?:\.\d)?)?\s*(?:status(?:\s+code)?\s*[:=]?)?\s*429\b"
    r"|\bstatus(?:\s+code)?\s*[:=]\s*429\b"
    r"|\b429\s+Too\s+Many\s+Requests\b"
    r"|\brate[_ ]limit(?:_error|ed)?\b"
    r"|\boverloaded_error\b"
    r"|\bat\s+capacity\b)",
    re.IGNORECASE,
)

# Denied rather than merely unmentioned: a verdict-emitting agent must not write to the tree.
MUTATING_TOOLS = ("Edit", "Write", "NotebookEdit")

# THE CLI SCHEMA IS A HINT; OUR VALIDATOR IS THE CONTRACT. `--json-schema` rejects a `$schema` draft
# ref outright and does not support conditional subschemas, so these keywords are stripped from the
# copy handed to the CLI. They are NOT dropped from the schema we validate against -- that is where
# rules like "match_existing requires a matched_polity_code" live, and giving them up to satisfy the
# CLI would mean accepting a verdict that names nothing. Measured: with `$schema` present the CLI
# exits 1; with `allOf` present it exits 1; with both stripped it succeeds.
CLI_UNSUPPORTED = ("$schema", "allOf", "anyOf", "oneOf", "not", "if", "then", "else",
                   "dependentSchemas", "dependentRequired")


def cli_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """The schema as the CLI will accept it: conditionals stripped, shape kept."""
    return {k: v for k, v in schema.items() if k not in CLI_UNSUPPORTED}

GRACE_SECONDS = 10


def digest(*values: str) -> str:
    h = hashlib.sha256()
    for v in values:
        h.update(v.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class JobResult:
    job: str
    ok: bool
    result: dict[str, Any] | None
    attempts: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    cached: bool = False


@dataclass
class ClaudeRunner:
    """Launch one agent job and return a schema-valid object, or an explained failure."""

    run_dir: Path
    model: str = "sonnet"
    effort: str = "low"
    timeout: int = 600
    max_throttle_retries: int = 2
    throttle_backoff_seconds: float = 4.0
    max_schema_retries: int = 1
    max_budget_usd: float | None = None
    allowed_tools: tuple[str, ...] = ("Read", "Grep", "Glob")

    def _command(self, schema_text: str) -> list[str]:
        # schema_text here is already the CLI-safe projection; see cli_schema().
        cmd = [
            "claude", "-p",
            "--model", self.model,
            "--effort", self.effort,
            "--output-format", "json",
            "--json-schema", schema_text,
            "--permission-mode", "bypassPermissions",
            "--disallowed-tools", *MUTATING_TOOLS,
        ]
        if self.allowed_tools:
            cmd += ["--allowed-tools", *self.allowed_tools]
        if self.max_budget_usd is not None:
            cmd += ["--max-budget-usd", str(self.max_budget_usd)]
        return cmd

    @staticmethod
    def _extract(stdout_path: Path, validator: Draft202012Validator) -> dict[str, Any] | None:
        """Pull a schema-valid object out of the CLI's JSON envelope.

        Tolerant of shape by design: the envelope has carried the payload under `result` and as a
        bare object across versions, and a harness that hard-codes one of them breaks on upgrade
        rather than on a real defect.
        """
        if not stdout_path.is_file():
            return None
        try:
            raw = json.loads(stdout_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        candidates: list[Any] = []
        if isinstance(raw, dict):
            candidates.append(raw)
            for key in ("result", "structured_output", "output", "content"):
                if key in raw:
                    candidates.append(raw[key])
        for cand in candidates:
            if isinstance(cand, str):
                try:
                    cand = json.loads(cand)
                except json.JSONDecodeError:
                    continue
            if isinstance(cand, dict) and validator.is_valid(cand):
                return cand
        return None

    def call(self, job: str, prompt: str, schema_path: Path, *, refresh: bool = False) -> JobResult:
        job_dir = self.run_dir / "agents" / job
        job_dir.mkdir(parents=True, exist_ok=True)
        result_path = job_dir / "result.json"
        meta_path = job_dir / "meta.json"
        full_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(full_schema)          # the CONTRACT
        schema_text = json.dumps(cli_schema(full_schema))      # the HINT
        # Fingerprint over the FULL schema: tightening a conditional rule must invalidate the cache
        # even though the CLI never sees that rule.
        fingerprint = digest(prompt, json.dumps(full_schema, sort_keys=True),
                             self.model, self.effort)

        # Identical work is not repeated. The fingerprint covers the prompt AND the schema AND the
        # model AND the effort, so any change that could alter the answer invalidates the cache.
        if not refresh and result_path.is_file() and meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                cached = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta, cached = {}, None
            if meta.get("fingerprint") == fingerprint and validator.is_valid(cached):
                return JobResult(job, True, cached, meta.get("attempts", []), cached=True)

        (job_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        command = self._command(schema_text)
        attempts: list[dict[str, Any]] = []
        result: dict[str, Any] | None = None
        error = ""

        for attempt_no in range(1, self.max_throttle_retries + self.max_schema_retries + 2):
            stdout_path = job_dir / f"stdout.attempt-{attempt_no:02d}.json"
            stderr_path = job_dir / f"stderr.attempt-{attempt_no:02d}.log"
            started = utc_now()
            timed_out = False
            # Files, not pipes: see the module docstring.
            with open(stdout_path, "w") as out, open(stderr_path, "w") as err:
                proc = subprocess.Popen(
                    command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                    text=True, cwd=str(REPO), start_new_session=True,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                try:
                    proc.communicate(prompt, timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    self._terminate(proc)
                except BaseException:
                    self._terminate(proc)
                    raise
            rc = proc.returncode
            found = self._extract(stdout_path, validator)
            stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            attempts.append({"attempt": attempt_no, "started": started, "return_code": rc,
                             "timed_out": timed_out, "schema_valid": found is not None})

            # A timeout is not proof of failure: keep a durable, schema-valid result.
            if found is not None:
                result = found
                break
            if timed_out:
                error = f"timed out after {self.timeout}s with no schema-valid result"
                continue
            if THROTTLE_RE.search(stderr_text):
                error = "throttled"
                time.sleep(self.throttle_backoff_seconds * attempt_no)
                continue
            error = f"return code {rc}, no schema-valid result"

        meta = {"job": job, "fingerprint": fingerprint, "model": self.model,
                "effort": self.effort, "attempts": attempts, "finished": utc_now(),
                "ok": result is not None, "error": error if result is None else ""}
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if result is not None:
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return JobResult(job, result is not None, result, attempts, error)

    @staticmethod
    def _terminate(proc: subprocess.Popen) -> None:
        """Reap the agent and every command it launched."""
        if proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
