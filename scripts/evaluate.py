#!/usr/bin/env python3
"""Prepare blind task inputs, audit artifacts, and compare attributed paired runs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

from install import SKILLS, bundle_files
from project_support import ROOT, read_json, safe_path, sha256, write_new_json

INDEX = ROOT / "evaluation/cases.json"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def cases(index=INDEX, root=ROOT):
    document = read_json(index)
    if document.get("schema") != 1 or not isinstance(document.get("cases"), list) or not document["cases"]:
        raise ValueError("Expected a nonempty schema-1 case catalog")
    found = {}
    for case in document["cases"]:
        if not isinstance(case, dict):
            raise ValueError("Each case must be an object")
        identifier = case.get("id", "")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", identifier) or identifier in found:
            raise ValueError(f"Invalid or duplicate case id: {identifier}")
        if case.get("skill") not in SKILLS or not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError(f"Invalid skill/prompt: {identifier}")
        if any(not isinstance(case.get(field), list) or not case[field] or any(not isinstance(item, dict) for item in case[field]) for field in ("inputs", "checks", "review")):
            raise ValueError(f"Case lacks inputs/checks/review: {identifier}")
        names = set()
        for item in case["inputs"]:
            source = safe_path(root, item["source"])
            safe_path(root, item["name"])
            if not source.is_file() or item["name"] in names:
                raise ValueError(f"Missing input or duplicate input name: {identifier}")
            names.add(item["name"])
        check_ids = set()
        for check in case["checks"]:
            safe_path(root, check["file"])
            if (not isinstance(check.get("id"), str) or not check["id"] or check["id"] in check_ids
                    or check.get("operation") not in {"contains", "absent"}
                    or not isinstance(check.get("value"), str) or not check["value"]):
                raise ValueError(f"Invalid automatic check: {identifier}")
            check_ids.add(check["id"])
        review_ids = [item.get("id") for item in case["review"]]
        if len(set(review_ids)) != len(review_ids) or any(not isinstance(x, str) or not x for x in review_ids):
            raise ValueError(f"Invalid review criteria: {identifier}")
        if any(not isinstance(item.get("question"), str) or not item["question"].strip() for item in case["review"]):
            raise ValueError(f"Missing review questions: {identifier}")
        found[identifier] = case
    return found


def input_hashes(case, root=ROOT):
    return {item["name"]: sha256(safe_path(root, item["source"])) for item in case["inputs"]}


def prepare(case_id, mode, output, index=INDEX, root=ROOT):
    case = cases(index, root)[case_id]
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Preparation needs a new output directory")
    record = {"schema": 1, "kind": "model_run", "case_id": case_id, "mode": mode,
              "agent": None, "model": None, "model_version": None, "settings": None, "trial": None, "session_id": None,
              "input_sha256": input_hashes(case, root), "case_sha256": digest(case),
              "context_sha256": {}, "prompt_sha256": None}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".evaluation-", dir=output.parent) as temporary:
        stage = Path(temporary) / "task"
        (stage / "inputs").mkdir(parents=True)
        (stage / "submission").mkdir()
        for item in case["inputs"]:
            destination = safe_path(stage / "inputs", item["name"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_path(root, item["source"]), destination)
        prompt = case["prompt"] + "\n\nKeep inputs unchanged; write deliverables to submission/.\n"
        # The task prompt is identical across modes. Only explicit skill context differs.
        (stage / "TASK.md").write_text(prompt, encoding="utf-8")
        record["prompt_sha256"] = sha256(stage / "TASK.md")
        if mode == "with-skill":
            context = stage / "context" / case["skill"]
            for relative, content in bundle_files(Path(root) / case["skill"]).items():
                target = context / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                record["context_sha256"][relative.as_posix()] = sha256(target)
        elif mode != "baseline":
            raise ValueError("Mode must be baseline or with-skill")
        # Check actual copies, not just the source inventory before copying.
        if record["input_sha256"] != {name: sha256(safe_path(stage / "inputs", name)) for name in record["input_sha256"]}:
            raise ValueError("Input changed while preparing the task")
        write_new_json(stage / "run.json", record)
        if output.exists() or output.is_symlink():
            raise ValueError("Output appeared during preparation")
        stage.rename(output)
    return {"schema": 1, "case_id": case_id, "mode": mode, "output": str(output),
            "next": "Run TASK.md in a fresh session; fill run.json with actual model/settings and attach evidence-backed human review"}


def review_scores(case, submission, review):
    if review is None:
        return {"status": "missing", "score": None, "maximum": 2 * len(case["review"]), "criteria": []}
    if not isinstance(review, dict) or not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip():
        raise ValueError("A human review needs a named reviewer")
    items = review.get("criteria", {})
    if not isinstance(items, dict) or set(items) != {item["id"] for item in case["review"]}:
        raise ValueError("Human review must cover exactly the case's criteria")
    evidence = []
    for criterion in case["review"]:
        item = items[criterion["id"]]
        if not isinstance(item, dict):
            raise ValueError("Each human criterion must be an object")
        score = item.get("score")
        match = re.fullmatch(r"(.+):([1-9][0-9]*)", str(item.get("evidence", "")))
        if type(score) is not int or not 0 <= score <= 2 or not isinstance(item.get("reason"), str) or not item["reason"].strip() or not match:
            raise ValueError("Review scores are 0–2 and require reasons and file:line evidence")
        lines = safe_path(submission, match[1]).read_text(encoding="utf-8").splitlines()
        line = int(match[2]) - 1
        if line >= len(lines) or not isinstance(item.get("excerpt"), str) or not item["excerpt"] or item["excerpt"] not in lines[line]:
            raise ValueError("Review excerpt must occur on the cited artifact line")
        evidence.append({"id": criterion["id"], **item})
    return {"status": "reviewed", "reviewer": review["reviewer"], "score": sum(item["score"] for item in evidence),
            "maximum": 2 * len(evidence), "criteria": evidence}


def score(case_id, submission, record_path=None, review_path=None, index=INDEX, root=ROOT, kind="unattributed_artifact"):
    case = cases(index, root)[case_id]
    submission = Path(submission).resolve()
    if not submission.is_dir():
        raise ValueError("Submission must be a directory of actual artifacts")
    run = {"kind": kind, "case_id": case_id, "mode": None}
    hashes = input_hashes(case, root)
    if record_path is not None:
        run = read_json(record_path)
        if run.get("schema") != 1 or run.get("kind") != "model_run" or run.get("case_id") != case_id or run.get("case_sha256") != digest(case):
            raise ValueError("Run record does not match this case/version")
        prepared = Path(record_path).resolve().parent
        if hashes != run.get("input_sha256") or hashes != {name: sha256(safe_path(prepared / "inputs", name)) for name in hashes}:
            raise ValueError("Prepared inputs differ from the recorded task")
        if sha256(prepared / "TASK.md") != run.get("prompt_sha256"):
            raise ValueError("Prepared task prompt changed")
        expected_context = {}
        if run.get("mode") == "with-skill":
            expected_context = {relative.as_posix(): hashlib.sha256(content).hexdigest()
                                for relative, content in bundle_files(Path(root) / case["skill"]).items()}
            actual_context = {relative.as_posix(): hashlib.sha256(content).hexdigest()
                              for relative, content in bundle_files(prepared / "context" / case["skill"]).items()}
            if expected_context != actual_context or expected_context != run.get("context_sha256"):
                raise ValueError("Skill context changed or does not match this version")
        elif run.get("mode") != "baseline" or run.get("context_sha256") or (prepared / "context").exists():
            raise ValueError("Baseline must have no supplied skill context")
    elif kind not in {"unattributed_artifact", "maintainer_candidate", "negative_control"}:
        raise ValueError("Model runs require a prepared run record")
    checks, artifacts = [], {}
    for check in case["checks"]:
        path = safe_path(submission, check["file"])
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            found = check["value"] in text
            passed = found if check["operation"] == "contains" else not found
            artifacts[check["file"]] = sha256(path)
        else:
            passed = False
        checks.append({"id": check["id"], "file": check["file"], "passed": passed})
    human = review_scores(case, submission, read_json(review_path) if review_path else None)
    return {"schema": 1, "case_id": case_id, "skill": case["skill"], "case_sha256": digest(case),
            "input_sha256": hashes, "submission_sha256": artifacts, "run": run,
            "automatic": {"passed": sum(item["passed"] for item in checks), "total": len(checks), "checks": checks},
            "human": human, "interpretation": "Literal checks audit limited invariants; they do not establish scientific fidelity or a skill's improvement"}


def compare(baseline, treatment):
    for report in (baseline, treatment):
        if not isinstance(report, dict) or any(not isinstance(report.get(field), dict) for field in ("run", "automatic", "human")):
            raise ValueError("Expected structured run, automatic and human evidence")
    reasons = []
    for field in ("schema", "case_id", "case_sha256", "input_sha256"):
        if baseline.get(field) != treatment.get(field):
            reasons.append(f"Mismatched {field}")
    if baseline.get("schema") != 1:
        raise ValueError("Expected schema-1 scored reports")
    for label, report, mode in (("baseline", baseline, "baseline"), ("with-skill", treatment, "with-skill")):
        run = report.get("run", {})
        if run.get("kind") != "model_run" or run.get("mode") != mode:
            reasons.append(f"{label} is not an attributed {mode} model run")
        for field in ("agent", "model", "model_version", "trial", "session_id"):
            if not isinstance(run.get(field), str) or not run[field].strip():
                reasons.append(f"{label} lacks {field}")
        if not isinstance(run.get("settings"), dict) or not run["settings"]:
            reasons.append(f"{label} lacks recorded settings")
        if run.get("case_id") != report.get("case_id") or run.get("input_sha256") != report.get("input_sha256") or run.get("case_sha256") != report.get("case_sha256"):
            reasons.append(f"{label} run provenance does not match its score")
        if not re.fullmatch(r"[0-9a-f]{64}", str(run.get("prompt_sha256", ""))):
            reasons.append(f"{label} lacks a task fingerprint")
        auto = report.get("automatic", {})
        checks = auto.get("checks", [])
        if (not isinstance(checks, list) or not checks or any(not isinstance(item, dict) or type(item.get("passed")) is not bool for item in checks)
                or auto.get("total") != len(checks) or auto.get("passed") != sum(item["passed"] for item in checks)):
            raise ValueError("Invalid automatic score evidence")
    for field in ("agent", "model", "model_version", "settings", "trial", "prompt_sha256"):
        if baseline["run"].get(field) != treatment["run"].get(field):
            reasons.append(f"Changed run condition: {field}")
    if baseline["run"].get("session_id") == treatment["run"].get("session_id"):
        reasons.append("Paired runs require distinct recorded sessions")
    ids = lambda report: [item["id"] for item in report["automatic"]["checks"]]
    if ids(baseline) != ids(treatment):
        reasons.append("Changed automatic criteria")
    comparable = not reasons
    human_ready = all(report.get("human", {}).get("status") == "reviewed" for report in (baseline, treatment))
    if human_ready:
        for report in (baseline, treatment):
            criteria = report["human"].get("criteria", [])
            if (not criteria or any(type(item.get("score")) is not int or not 0 <= item["score"] <= 2 for item in criteria)
                    or report["human"].get("score") != sum(item["score"] for item in criteria)):
                raise ValueError("Invalid human score evidence")
        if [item["id"] for item in baseline["human"]["criteria"]] != [item["id"] for item in treatment["human"]["criteria"]]:
            reasons.append("Changed human criteria")
            comparable = False
    return {"schema": 1, "case_id": baseline.get("case_id"), "comparable": comparable,
            "reasons": reasons, "automatic_delta": treatment["automatic"]["passed"] - baseline["automatic"]["passed"] if comparable else None,
            "human_delta": treatment["human"]["score"] - baseline["human"]["score"] if comparable and human_ready else None,
            "quality_review": "paired" if comparable and human_ready else "unverified",
            "interpretation": "One attributed pair is an observation, not a general improvement estimate; repeat trials and review failures"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    task = commands.add_parser("prepare")
    task.add_argument("--case", required=True)
    task.add_argument("--mode", choices=("baseline", "with-skill"), required=True)
    task.add_argument("--output", type=Path, required=True)
    audit = commands.add_parser("score")
    audit.add_argument("--case", required=True)
    audit.add_argument("--submission", type=Path, required=True)
    audit.add_argument("--record", type=Path)
    audit.add_argument("--review", type=Path)
    audit.add_argument("--kind", choices=("unattributed_artifact", "maintainer_candidate", "negative_control"), default="unattributed_artifact")
    audit.add_argument("--output", type=Path, required=True)
    pair = commands.add_parser("compare")
    pair.add_argument("--baseline", type=Path, required=True)
    pair.add_argument("--with-skill", dest="treatment", type=Path, required=True)
    pair.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            entries = cases()
            result = {"schema": 1, "cases": len(entries), "skills": sorted({case["skill"] for case in entries.values()})}
            status = 0
        elif args.command == "prepare":
            result, status = prepare(args.case, args.mode, args.output), 0
        elif args.command == "score":
            result = score(args.case, args.submission, args.record, args.review, kind=args.kind)
            status = 0 if result["automatic"]["passed"] == result["automatic"]["total"] else 1
            write_new_json(args.output, result)
        else:
            result = compare(read_json(args.baseline), read_json(args.treatment))
            status = 0 if result["comparable"] else 1
            write_new_json(args.output, result)
        print(json.dumps(result, ensure_ascii=True, indent=2) if args.json else json.dumps(result, ensure_ascii=False))
        return status
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        if args.json:
            print(json.dumps({"schema": 1, "error": str(exc)}))
        else:
            print(f"Evaluation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
