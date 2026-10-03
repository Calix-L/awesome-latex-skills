#!/usr/bin/env python3
"""Prepare repeated blind tasks and report every attempted run without model calls."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import random
import shutil
import sys
import tempfile

from evaluate import cases, compare, prepare, score
from project_doctor import commands
from project_support import read_json, safe_path, sha256, write_new_json
from run_examples import load_helper


def prepare_batch(output, trials=3, seed=0):
    output = Path(output).expanduser().absolute()
    if type(trials) is not int or not 1 <= trials <= 20:
        raise ValueError("Trials must be 1–20")
    if output.exists() or output.is_symlink():
        raise ValueError("Batch preparation requires a new directory")
    rows = [{"id": f"{case}-{trial:02}-{mode}", "case_id": case, "mode": mode, "trial": str(trial),
             "directory": f"tasks/{case}-{trial:02}-{mode}"}
            for case in cases() for trial in range(1, trials + 1) for mode in ("baseline", "with-skill")]
    random.Random(seed).shuffle(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".batch-", dir=output.parent) as temporary:
        stage = Path(temporary) / "batch"
        stage.mkdir()
        for row in rows:
            task = stage / row["directory"]
            prepare(row["case_id"], row["mode"], task)
            record = read_json(task / "run.json")
            record["trial"] = row["trial"]
            (task / "run.json").write_text(json.dumps(record, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        write_new_json(stage / "batch.json", {"schema": 1, "trials": trials, "seed": seed, "runs": rows})
        if output.exists() or output.is_symlink():
            raise ValueError("Batch destination appeared during preparation")
        stage.rename(output)
    return {"schema": 1, "status": "prepared-not-run", "runs": len(rows), "output": str(output),
            "next": "Execute each task in a distinct isolated session; retain real attribution, execution.json and raw transcript. No model has been called."}


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def execution_evidence(task):
    path = task / "execution.json"
    if not path.exists():
        return {"status": "not-run", "elapsed_seconds": None, "tokens": None, "cost": None}
    evidence = read_json(path)
    if evidence.get("schema") != 1 or evidence.get("status") not in {"completed", "failed", "timeout"}:
        raise ValueError("Execution evidence needs schema 1 and completed/failed/timeout status")
    if not finite_number(evidence.get("elapsed_seconds")):
        raise ValueError("Elapsed wall time must be an actual nonnegative finite number")
    transcript = safe_path(task, evidence.get("transcript"))
    if not transcript.is_file() or not transcript.stat().st_size:
        raise ValueError("Execution evidence requires a nonempty raw transcript")
    tokens = evidence.get("tokens")
    if tokens is not None and (not isinstance(tokens, dict) or set(tokens) != {"input", "output"}
                               or any(type(value) is not int or value < 0 for value in tokens.values())):
        raise ValueError("Token counts must be actual nonnegative input/output integers or null")
    cost = evidence.get("cost")
    if cost is not None and (not isinstance(cost, dict) or not finite_number(cost.get("amount"))
                            or not isinstance(cost.get("currency"), str) or not cost["currency"].strip()
                            or not isinstance(cost.get("source"), str) or not cost["source"].strip()):
        raise ValueError("Cost requires amount, currency and billing source; use null if unavailable")
    return {**evidence, "transcript_sha256": sha256(transcript)}


def compile_submission(task, destination, engine):
    submission = task / "submission"
    roots = [path for path in submission.rglob("*.tex") if any(item["name"] == "documentclass"
             for item in commands(path.read_text(encoding="utf-8")))]
    if not roots:
        return {"status": "not-applicable", "reason": "No complete LaTeX root submitted"}
    if len(roots) != 1:
        return {"status": "unverified", "reason": "Multiple document roots; selection requires review"}
    source = safe_path(submission, roots[0].relative_to(submission).as_posix())
    if not shutil.which(engine):
        return {"status": "unverified", "reason": f"{engine} unavailable"}
    build = load_helper("batch_compile", "latex-rescue/scripts/check_build.py").build
    evidence = build(source, destination, engine=engine, passes=2)
    return {"status": evidence["status"], "report": str(destination / "build-report.json"),
            "unresolved_references": evidence.get("unresolved_references"), "failure": evidence.get("failure"),
            "interpretation": "Independent two-pass build, no inferred bibliography backend; unresolved keys and fidelity remain separate."}


def report_batch(batch, output, engine="pdflatex"):
    batch = Path(batch).resolve()
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(batch):
        raise ValueError("Report output must be new and outside the blind task tree")
    catalog = read_json(batch / "batch.json")
    trials = catalog.get("trials")
    if catalog.get("schema") != 1 or type(trials) is not int or not 1 <= trials <= 20:
        raise ValueError("Invalid repeated-trial catalog")
    expected = {(case, mode, str(trial)) for case in cases() for mode in ("baseline", "with-skill") for trial in range(1, trials + 1)}
    rows = catalog.get("runs")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Batch needs structured run entries")
    keys = [(row.get("case_id"), row.get("mode"), row.get("trial")) for row in rows]
    if len(keys) != len(expected) or set(keys) != expected or len({row.get("directory") for row in rows}) != len(rows):
        raise ValueError("Batch coverage changed or repeats a task directory")
    for row in rows:
        identifier = f"{row['case_id']}-{int(row['trial']):02}-{row['mode']}"
        if row.get("id") != identifier or row.get("directory") != "tasks/" + identifier:
            raise ValueError("Task ID/directory differs from its scheduled condition")
    output.mkdir(parents=True)
    runs, paired, sessions = [], defaultdict(dict), Counter()
    for row in rows:
        result = {"case_id": row["case_id"], "mode": row["mode"], "trial": row["trial"], "directory": row["directory"]}
        try:
            task = safe_path(batch, row["directory"])
            execution = execution_evidence(task)
            result["execution"] = execution
            if execution["status"] == "not-run":
                result.update(status="not-run", compilation={"status": "unverified"})
            else:
                review = task / "human-review.json"
                scored = score(row["case_id"], task / "submission", task / "run.json", review if review.exists() else None)
                if scored["run"].get("mode") != row["mode"] or scored["run"].get("trial") != row["trial"]:
                    raise ValueError("Recorded condition/trial differs from its scheduled task")
                result.update(status=execution["status"], score=scored,
                              compilation=compile_submission(task, output / "builds" / row["id"], engine))
                session = scored["run"].get("session_id")
                if session:
                    sessions[session] += 1
        except (OSError, ValueError, KeyError, TypeError, UnicodeError, ImportError, RuntimeError) as exc:
            result.update(status="invalid-evidence", error=str(exc))
        runs.append(result)
        paired[(row["case_id"], row["trial"])][row["mode"]] = result
    comparisons = []
    for (case, trial), pair in sorted(paired.items()):
        before, after = pair["baseline"], pair["with-skill"]
        result = {"case_id": case, "trial": trial, "comparable": False, "automatic_delta": None, "human_delta": None}
        if all("score" in item and item["status"] != "invalid-evidence" for item in (before, after)):
            result.update(compare(before["score"], after["score"]))
            if any(sessions[item["score"]["run"].get("session_id")] > 1 for item in (before, after)):
                result.update(comparable=False, automatic_delta=None, human_delta=None)
                result["reasons"].append("A session was reused across scheduled tasks")
        else:
            result["reasons"] = ["Pair missing actual execution or valid score evidence"]
        comparisons.append(result)
    totals = {}
    for mode in ("baseline", "with-skill"):
        selected = [item for item in runs if item["mode"] == mode]
        measurements = [item["execution"] for item in selected if item.get("execution", {}).get("status") != "not-run" and "execution" in item]
        costs = defaultdict(float)
        for item in measurements:
            if item.get("cost"):
                costs[item["cost"]["currency"]] += item["cost"]["amount"]
        totals[mode] = {"scheduled": len(selected), "statuses": dict(Counter(item["status"] for item in selected)),
                        "measured_elapsed_seconds": sum(item["elapsed_seconds"] for item in measurements) if measurements else None,
                        "cost_by_currency": dict(costs) or None, "cost_measured_runs": sum(item.get("cost") is not None for item in measurements),
                        "compilation": dict(Counter(item.get("compilation", {}).get("status", "unverified") for item in selected))}
    report = {"schema": 1, "runs": runs, "pairs": comparisons, "conditions": totals,
              "comparable_pairs": sum(item["comparable"] for item in comparisons),
              "interpretation": "All scheduled runs retained, including failures and missing runs. Literal invariants, native builds, human review, wall time and measured cost are separate. Recorded attribution/transcript hashes do not independently prove provider identity."}
    write_new_json(output / "report.json", report)
    lines = ["# Repeated-trial evaluation", "", report["interpretation"], "", "| Case | Trial | Pair comparable | Literal delta | Human delta |", "|---|---|---|---|---|"]
    for item in comparisons:
        lines.append(f"| {item['case_id']} | {item['trial']} | {item['comparable']} | {item['automatic_delta']} | {item['human_delta']} |")
    lines.extend(["", "Unavailable values are null; inspect report.json for every run and failure."])
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"schema": 1, "scheduled_runs": len(runs), "comparable_pairs": report["comparable_pairs"], "conditions": totals, "output": str(output)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    preparation = sub.add_parser("prepare")
    preparation.add_argument("--trials", type=int, default=3)
    preparation.add_argument("--seed", type=int, default=0)
    preparation.add_argument("--output", type=Path, required=True)
    report = sub.add_parser("report")
    report.add_argument("--batch", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    report.add_argument("--engine", choices=("pdflatex", "xelatex", "lualatex"), default="pdflatex")
    args = parser.parse_args(argv)
    try:
        result = prepare_batch(args.output, args.trials, args.seed) if args.command == "prepare" else report_batch(args.batch, args.output, args.engine)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
