"""Publish a complete static inspection in a new portable report directory."""
from pathlib import Path
import tempfile

from artifact_integrity import seal_inspection
from project_doctor import inspect_project, ASSET_SUFFIXES, MAX_SOURCE_BYTES
from project_report import write_inspection_reports
from project_support import safe_path
from bounded_io import fingerprint


def export_inspection(root, output, main=None, engine=None, backend=None, language="en"):
    if language not in {"en", "zh"}:
        raise ValueError("Inspection language must be en or zh")
    root = Path(root).expanduser().resolve()
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(root):
        raise ValueError("Inspection bundle must be new and outside the project tree")
    output = output.resolve()
    result = inspect_project(root, main, engine, backend)
    result["bundle"] = {"directory": str(output), "json": "inspection.json",
                        "html": "report.html", "integrity": "integrity.json", "language": language}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".inspection-", dir=output.parent) as temporary:
        staged = Path(temporary) / "bundle"
        write_inspection_reports(staged / "inspection.json", staged / "report.html", result, language, "integrity.json")
        seal_inspection(staged)
        for item in result["observed_files"]:
            path = safe_path(root, item["file"])
            limit = None if path.suffix.lower() in ASSET_SUFFIXES else MAX_SOURCE_BYTES
            if fingerprint(path, limit)["sha256"] != item["sha256"]:
                raise ValueError(f"Project inputs changed before inspection publication: {item['file']}")
        if output.exists() or output.is_symlink():
            raise ValueError("Inspection output appeared during publication")
        staged.rename(output)
    return result
