"""Run an explicitly configured external command and retain measured evidence."""
import json
from pathlib import Path
import subprocess
import time

from evaluate import cases, score
from project_support import read_json, safe_path, sha256, write_new_json


def submission_hashes(task):
    root = safe_path(task, "submission")
    if not root.is_dir():
        raise ValueError("Submission directory is missing")
    inventory = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        checked = safe_path(root, relative)
        if checked.is_file():
            inventory[relative] = sha256(checked)
        elif not checked.is_dir():
            raise ValueError(f"Unsupported submission entry: {relative}")
        if len(inventory) > 5000:
            raise ValueError("Submission exceeds 5000 files")
    return inventory


def run_task(task, specification, timeout=600):
    task = Path(task).expanduser().resolve()
    specification = read_json(specification)
    arguments = specification.get("command")
    if (specification.get("schema") != 1 or not isinstance(arguments, list) or not arguments
            or any(not isinstance(item, str) or not item or "\x00" in item for item in arguments)):
        raise ValueError("Runner specification needs schema 1 and a nonempty command argument list")
    if type(timeout) not in (int, float) or not 0 < timeout <= 86400:
        raise ValueError("Timeout must be greater than zero and at most 86400 seconds")
    metadata = {}
    for field in ("agent", "model", "model_version", "session_id"):
        value = specification.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Runner specification requires actual {field}")
        metadata[field] = value
    settings = specification.get("settings")
    if not isinstance(settings, dict) or not settings:
        raise ValueError("Record actual nonempty settings, including context/tool policy")
    metadata["settings"] = settings
    original = read_json(safe_path(task, "run.json"))
    trial = original.get("trial") or specification.get("trial")
    if not isinstance(trial, str) or not trial.strip():
        raise ValueError("Use a prepared batch task or specify a trial string")
    if specification.get("trial", trial) != trial:
        raise ValueError("Runner trial differs from the prepared schedule")
    score(original["case_id"], safe_path(task, "submission"), safe_path(task, "run.json"))
    if (any((task / name).exists() or (task / name).is_symlink()
            for name in ("execution.json", "runner", "human-review.json"))
            or any(safe_path(task, "submission").iterdir())
            or any(original.get(field) is not None for field in metadata)):
        raise ValueError("Run requires an untouched prepared task; prepare a fresh task for a retry")
    lock = task / ".execution.lock"
    lock.mkdir()  # Exclusive ownership; never expire another running command's lock.
    try:
        runner = task / "runner"
        runner.mkdir()
        write_new_json(runner / "prepared-run.json", original)
        attributed = {**original, **metadata, "trial": trial}
        write_new_json(runner / "attributed-run.json", attributed)
        (task / "run.json").write_text(json.dumps(attributed, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        recorded_hash = sha256(task / "run.json")
        evidence = {"schema": 1, "producer": "als-command-runner", "command": arguments,
                    "status": "failed", "exit_code": None, "elapsed_seconds": None,
                    "transcript": "runner/transcript.log", "tokens": None, "cost": None,
                    "run_sha256": recorded_hash, "submission_sha256": None,
                    "integrity_error": None}
        start = time.monotonic()
        with (runner / "transcript.log").open("xb") as transcript, (task / "TASK.md").open("rb") as prompt:
            transcript.write(b"[als runner] stdin: TASK.md; cwd: prepared task; stdout and stderr follow\n")
            transcript.flush()
            try:
                child = subprocess.run(arguments, cwd=task, stdin=prompt, stdout=transcript,
                                       stderr=subprocess.STDOUT, timeout=timeout, shell=False)
                evidence.update(exit_code=child.returncode, status="completed" if child.returncode == 0 else "failed")
            except subprocess.TimeoutExpired:
                evidence.update(status="timeout", error="Command exceeded the configured timeout")
            except OSError as exc:
                evidence["error"] = str(exc)
            except KeyboardInterrupt:
                evidence.update(status="failed", error="Command interrupted", interrupted=True)
            evidence["elapsed_seconds"] = time.monotonic() - start
            trailer = f"\n[als runner] status={evidence['status']} exit_code={evidence['exit_code']}\n"
            transcript.write(trailer.encode("utf-8"))
        evidence["transcript_sha256"] = sha256(safe_path(task, evidence["transcript"]))
        try:
            if sha256(safe_path(task, "run.json")) != recorded_hash:
                raise ValueError("Command modified the attributed run record")
            score(original["case_id"], safe_path(task, "submission"), safe_path(task, "run.json"))
            evidence["submission_sha256"] = submission_hashes(task)
        except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
            evidence["integrity_error"] = str(exc)
        write_new_json(safe_path(task, "execution.json"), evidence)
        return {"schema": 1, "status": evidence["status"], "exit_code": evidence["exit_code"],
                "elapsed_seconds": evidence["elapsed_seconds"], "integrity_error": evidence["integrity_error"],
                "interrupted": evidence.get("interrupted", False),
                "task": str(task), "evidence": str(task / "execution.json")}
    finally:
        lock.rmdir()


def review_template(task, output):
    task = Path(task).resolve()
    output = Path(output).expanduser().resolve()
    if output.is_relative_to(task):
        raise ValueError("Keep reviewer criteria outside the agent task until execution is finished")
    record = read_json(safe_path(task, "run.json"))
    case = cases()[record["case_id"]]
    score(record["case_id"], safe_path(task, "submission"), safe_path(task, "run.json"))
    template = {"reviewer": None, "criteria": {
        item["id"]: {"question": item["question"], "score": None, "reason": "", "evidence": "", "excerpt": ""}
        for item in case["review"]}}
    write_new_json(output, template)
    return {"schema": 1, "status": "unfilled", "output": str(output),
            "next": "A named human reviewer must fill every score, reason and actual file:line excerpt; null scores are not accepted as a review."}
