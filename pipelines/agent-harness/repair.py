#!/usr/bin/env python3
"""Turn gate failures into a narrow repair, not another rewrite.

THE LESSON THIS ENCODES. A repair prompt that re-asks the original question invites a fresh attempt,
and fresh attempts oscillate: the second fixes the span and breaks the prose, the third fixes the
prose and breaks the span. So a repair must name a NARROW OPERATION -- which fields may change and
which must not -- and the harness must be able to prefer a nearly-right attempt over a differently-
wrong one.

OUR REVIEW IS THE GATE OUTPUT, which is better than a model's opinion: it is deterministic, it names
the failing arm, and it cannot be argued with. That lets failures be classified by WHO SHOULD FIX
THEM, which is the first question and the one an agent cannot answer about itself:

  MECHANICAL   a script can fix it exactly -- rebuild the site, add a reciprocal chain edge on the
               neighbour's page, regenerate a derived table. Never ask an agent to do what a
               deterministic step does correctly every time.
  ARITHMETIC   spans, intervals and codes that must agree. A narrow operation: change the named
               numbers, touch no prose.
  JUDGEMENT    the content is wrong or thin. This is the only class that needs the model, and it
               gets the smallest instruction that can resolve the cited finding.
  UNKNOWN      unclassified. Escalated rather than guessed at, because a repair aimed at the wrong
               class is how oscillation starts.

ATTEMPTS ARE RANKED, NOT JUST COUNTED. When every attempt fails, the best is the one with the fewest
JUDGEMENT failures first and the fewest failures overall second -- so an attempt that fixed the
content while leaving an arithmetic slip is preferred over one that fixed the arithmetic and hollowed
out the page. Length or line count is never a tiebreak: a longer page is not a better one.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

# Gates worth re-running after a page lands. Deliberately not the whole suite: a repair loop that
# takes minutes per attempt gets switched off.
PAGE_GATES = (
    "scripts/validate_polity_containment.py",
    "scripts/validate_code_year_agreement.py",
    "scripts/validate_chain_integrity.py",
    "scripts/validate_references.py",
    "scripts/validate_polygons.py",
)

# Classification by the text a gate emits. Ordered: the first match wins, so put the specific
# patterns before the general ones.
CLASSIFIERS: tuple[tuple[str, str, str], ...] = (
    # (class, regex, the narrow operation this failure implies)
    ("MECHANICAL", r"site/(?:wiki|polities)|rebuild: bash site/build_wiki\.sh",
     "rebuild the site"),
    ("MECHANICAL", r"ASYMMETRY: \d+ (?:successor|predecessor)-only chain edges",
     "add the reciprocal chain edge on the neighbour's page"),
    ("MECHANICAL", r"is stale|out of date|--check",
     "regenerate the derived table"),
    ("ARITHMETIC", r"covers \d+-\d+ but the container's span is|"
                   r"but the member's own span is",
     "the containment interval or the span it sits in disagree"),
    # Real wording, captured from the gate rather than guessed: "code says 1959-2025, columns say
    # 1959-2026". An invented pattern matched none of it and routed a trivially fixable arithmetic
    # slip to the do-nothing UNKNOWN mode.
    ("ARITHMETIC", r"code says .*columns say|code (?:says|embeds).*(?:year|span)|"
                   r"polity_code .* disagree|year.*disagree.*code|code_year",
     "the polity code and the frontmatter span disagree"),
    ("ARITHMETIC", r"self-referential|declared area|area disagreement",
     "the declared area disagrees with the attached geometry"),
    ("JUDGEMENT", r"bad frontmatter key|dangling chain ref|asserted-but-absent|broken page link",
     "a page reference or frontmatter key is wrong"),
    ("JUDGEMENT", r"no source at all|unregistered declared slug",
     "the page cites a source that is not registered"),
)


@dataclass
class Failure:
    gate: str
    line: str
    kind: str
    operation: str


# CLASSIFY BY (GATE, ARM) BEFORE PROSE. A gate names its failing arm -- "C: ..." -- and an arm's
# meaning is stable while its wording is not. Matching prose alone made the classifier depend on an
# apostrophe: "the container's span" against "the container span" silently fell through to UNKNOWN,
# which routes a fixable failure to the do-nothing mode. Arms first, prose as the fallback.
ARM_KINDS: dict[tuple[str, str], tuple[str, str]] = {
    ("validate_polity_containment.py", "A"): ("JUDGEMENT", "an edge names a code that does not exist"),
    ("validate_polity_containment.py", "B"): ("ARITHMETIC", "the edge runs outside the member's own span"),
    ("validate_polity_containment.py", "C"): ("ARITHMETIC", "the edge runs outside the container's span"),
    ("validate_polity_containment.py", "D"): ("JUDGEMENT", "self- or mutual containment"),
    ("validate_polity_containment.py", "E"): ("JUDGEMENT", "a subnational row declares no container"),
    ("validate_polity_containment.py", "F"): ("MECHANICAL", "regenerate the derived table"),
}

ARM_RE = re.compile(r"^\s*([A-F]):\s")


def classify(gate: str, line: str) -> Failure:
    m = ARM_RE.match(line)
    if m:
        hit = ARM_KINDS.get((gate, m.group(1)))
        if hit:
            return Failure(gate, line.strip(), hit[0], hit[1])
        # Arms learned by reading the gate's source are as good as the ones written in above.
        learned = learned_arms().get(f"{gate}|{m.group(1)}")
        if learned:
            return Failure(gate, line.strip(), learned[0], learned[1])
    for kind, pattern, operation in CLASSIFIERS:
        if re.search(pattern, line, re.IGNORECASE):
            return Failure(gate, line.strip(), kind, operation)
    return Failure(gate, line.strip(), "UNKNOWN", "unclassified — escalate rather than guess")


LEARNED_ARMS = HERE / "state" / "gate_arm_kinds.json"
CLASS_SCHEMA = HERE / "schemas" / "failure_class.schema.json"

CLASS_PROMPT = """Classify one arm of one gate in this repository by reading that gate's own source.

An arm the harness cannot classify currently produces NO repair at all -- the failure is real, it is
reported, and nothing is aimed at it. Growing a list of regexes over the gates' prose is the
alternative and it is worse: one apostrophe of difference between "the container's span" and "the
container span" already dropped a fixable arithmetic failure into the do-nothing class. The gate's
source says what the arm compares; that is durable, and it is the same for every row the arm fires on.

Read `{gate}` and classify arm `{arm}`.

A FAILURE LINE FROM THAT ARM (one example; classify the ARM, not this row)
--------------------------------------------------------------------------
{line}
"""


def learned_arms() -> dict[str, list]:
    if LEARNED_ARMS.exists():
        return json.loads(LEARNED_ARMS.read_text(encoding="utf-8"))
    return {}


def learn_arm(gate: str, arm: str, kind: str, operation: str, reasoning: str) -> None:
    all_a = learned_arms()
    all_a[f"{gate}|{arm}"] = [kind, operation, reasoning]
    LEARNED_ARMS.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEARNED_ARMS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(all_a, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, LEARNED_ARMS)


def classify_unknown_arms(fails: list["Failure"], runner) -> list["Failure"]:
    """Ask, once per (gate, arm), what an unclassified arm actually checks; bank and re-apply it.

    Only arms are learned this way. A failure with no arm letter stays UNKNOWN: without a stable
    key there is nothing to bank, and asking per row would re-ask forever.
    """
    banked = learned_arms()
    out: list[Failure] = []
    for f in fails:
        m = ARM_RE.match(f.line)
        if f.kind != "UNKNOWN" or not m:
            out.append(f)
            continue
        arm, key = m.group(1), f"{f.gate}|{m.group(1)}"
        if key not in banked:
            res = runner.call(f"class-{f.gate.replace('.py', '')}-{arm}",
                              CLASS_PROMPT.format(gate=f"scripts/{f.gate}", arm=arm, line=f.line),
                              CLASS_SCHEMA)
            if not res.ok:
                out.append(f)
                continue
            r = res.result
            if r["kind"] == "UNKNOWN":
                print(f"      {f.gate} arm {arm}: declined to classify — {r['reasoning'][:80]}")
                out.append(f)
                continue
            learn_arm(f.gate, arm, r["kind"], r["operation"], r["reasoning"])
            banked = learned_arms()
            print(f"      learned {f.gate} arm {arm} = {r['kind']}: {r['operation'][:70]}")
        kind, operation, _ = banked[key]
        out.append(Failure(f.gate, f.line, kind, operation))
    return out


PROSE_FIELDS = ("summary", "why_this_entry_exists", "territorial_extent",
                "predecessors_and_successors", "sourced_claims", "decisions", "open_questions")


def enforce_arithmetic_narrowness(prev: dict, new: dict) -> tuple[dict, list[str]]:
    """In ARITHMETIC mode, restore every prose field from `prev` and report which ones moved.

    The mode's instruction is "change the named numbers, touch no prose". Asking is not enforcing:
    a run that was supposed to fix one span rewrote predecessors_and_successors, decisions and
    open_questions as well. That is how a repair loop launders content changes through an
    arithmetic fix -- the gate goes green and the page quietly says something different, including
    losing an open question nobody resolved.

    Returns the merged page and the names of the fields that were overwritten, so the attempt can
    report what it tried to do rather than having it disappear.
    """
    merged = dict(new)
    moved: list[str] = []
    for f in PROSE_FIELDS:
        if f in prev and json.dumps(new.get(f), sort_keys=True) != json.dumps(prev[f],
                                                                             sort_keys=True):
            moved.append(f)
            merged[f] = prev[f]
    return merged, moved


def is_arithmetic_only(fails: list["Failure"]) -> bool:
    """True when nothing in this failure set needs a content judgement."""
    return bool(fails) and all(f.kind in ("ARITHMETIC", "MECHANICAL") for f in fails)


def run_gates_detail(codes: tuple[str, ...] = ()) -> tuple[list[Failure], list[str]]:
    """Run the page gates; return (failures naming `codes`, names of every gate that is red).

    The two halves are returned separately because they answer different questions and conflating
    them is a lie in the reassuring direction. Filtering to `codes` is right -- this loop must not
    rewrite a page to fix somebody else's row -- but a gate that is red for reasons that never name
    our code then contributes NOTHING to the returned list, and an empty list previously read as
    `clean`. It is not clean; it is unattributable. The caller needs to be able to say which.
    """
    out: list[Failure] = []
    red: list[str] = []
    for gate in PAGE_GATES:
        if not (REPO / gate).exists():
            continue
        r = subprocess.run(["python3", gate], cwd=str(REPO), capture_output=True, text=True,
                           timeout=600)
        if r.returncode == 0:
            continue
        red.append(Path(gate).name)
        for line in (r.stdout + r.stderr).splitlines():
            s = line.strip()
            if not s or s.startswith("PASS"):
                continue
            # A failure is attributable when it names one of our codes, or when no codes were given.
            if codes and not any(c in s for c in codes):
                continue
            if re.match(r"^(FAIL|\s*[A-F]:|\s*(?:NEW|ASYMMETRY|UNEXPLAINED|PIN))", line) or codes:
                out.append(classify(Path(gate).name, s))
    # De-duplicate: gates repeat a headline and its detail.
    seen, uniq = set(), []
    for f in out:
        key = (f.gate, f.line)
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq, red


def run_gates(codes: tuple[str, ...] = ()) -> list[Failure]:
    """Attributable failures only. Prefer run_gates_detail so the red-but-unattributed gates are
    visible; this wrapper exists for callers that genuinely only want the actionable list."""
    return run_gates_detail(codes)[0]


def rank(attempt_failures: list[Failure]) -> tuple[int, int, int]:
    """Lower is better. JUDGEMENT failures dominate; page size is never a tiebreak."""
    j = sum(1 for f in attempt_failures if f.kind == "JUDGEMENT")
    u = sum(1 for f in attempt_failures if f.kind == "UNKNOWN")
    return (j, u, len(attempt_failures))


def mechanical_fixes(failures: list[Failure]) -> list[str]:
    """Apply what a script fixes exactly. Returns what was done."""
    done: list[str] = []
    ops = {f.operation for f in failures if f.kind == "MECHANICAL"}
    if "rebuild the site" in ops:
        subprocess.run(["bash", "site/build_wiki.sh"], cwd=str(REPO),
                       capture_output=True, text=True, timeout=900)
        done.append("rebuilt site/")
    if "regenerate the derived table" in ops:
        for script in ("scripts/write_polity_containment.py", "scripts/write_manifest.py",
                       "scripts/update_wiki_index.py"):
            subprocess.run(["python3", script], cwd=str(REPO), capture_output=True,
                           text=True, timeout=600)
        done.append("regenerated derived tables")
    # The reciprocal chain edge is deliberately NOT automated: which neighbour gains the edge is a
    # claim about chronology, and the checklist keeps that a human/agent decision. Reported instead.
    return done


REPAIR_MODES = {
    "ARITHMETIC": """RECOVERY MODE: arithmetic repair only.

Change ONLY the numbers and codes named in the findings below. Preserve every sentence of prose
exactly as written -- summary, why_this_entry_exists, territorial_extent, decisions and open
questions must come back byte-identical unless a finding names them. Do not re-argue the entry, do
not add or remove an open question, do not rewrite a decision.

The specific constraints you must satisfy:
- `polity_code` embeds its own span: a code ending -1959-2025 REQUIRES start_year 1959 and
  end_year 2025. Fix one or the other, and say in the relevant decision or open question which you
  moved and why.
- every container edge must lie inside BOTH the member's span and the container's own span. An edge
  running past its container's end_year is rejected; either clip the edge, split it across the
  container's successive eras, or change this entry's span.""",

    "JUDGEMENT": """RECOVERY MODE: localized content repair.

Keep the entry's structure and every section not implicated by the findings. Change the smallest
span of text needed to resolve each cited finding. Do not rewrite the page, do not restate the
summary, and do not delete an open question to make a finding go away -- an unresolved question is
the honest output, and removing it is the failure this mode exists to prevent.""",

    "UNKNOWN": """RECOVERY MODE: none available.

The findings below could not be classified, so no narrow operation is safe to name. Return the entry
UNCHANGED and put what you cannot resolve into an open question. A repair aimed at the wrong class
is worse than an unrepaired page, because it moves the defect instead of fixing it.""",
}


def repair_prompt(failures: list[Failure], previous_page_json: str) -> str:
    kinds = [k for k in ("JUDGEMENT", "ARITHMETIC", "UNKNOWN") if any(f.kind == k for f in failures)]
    mode = REPAIR_MODES[kinds[0]] if kinds else REPAIR_MODES["JUDGEMENT"]
    findings = "\n".join(f"  [{f.kind}] {f.gate}: {f.line}" for f in failures)
    return f"""{mode}

FINDINGS FROM THIS REPOSITORY'S OWN GATES (deterministic; not opinions)
----------------------------------------------------------------------
{findings}

THE ENTRY YOU PREVIOUSLY RETURNED, to repair rather than replace
----------------------------------------------------------------
{previous_page_json}

Return the full object again, satisfying the same schema, with only the changes this mode permits.
"""
