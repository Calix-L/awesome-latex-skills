#!/usr/bin/env python3
"""Verify wheel first use and an independently rebuilt source distribution."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from check_distribution import check_distribution
from project_support import sha256, version, write_new_json


def check_packages(directory, output):
    directory = Path(directory).resolve()
    output = Path(output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Package verification requires a new directory")
    current = version()
    wheel = directory / f"awesome_latex_skills-{current}-py3-none-any.whl"
    sdist = directory / f"awesome_latex_skills-{current}.tar.gz"
    if any(not path.is_file() or path.is_symlink() for path in (wheel, sdist)):
        raise ValueError("Supply both current-version distributions from python -m build")
    output.mkdir(parents=True)
    output = output.resolve()
    report = {"schema": 1, "version": current, "status": "failed", "sdist_sha256": sha256(sdist)}
    try:
        report["wheel"] = check_distribution(wheel, output / "wheel")
        if report["wheel"]["status"] != "verified":
            raise ValueError("Wheel first-use verification failed")
        destination = output / "rebuilt"
        destination.mkdir()
        process = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(destination), str(sdist)],
                                 cwd=output, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        report["rebuild"] = {"exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr}
        if process.returncode:
            raise ValueError("Source distribution could not be rebuilt")
        rebuilt = list(destination.glob("*.whl"))
        if len(rebuilt) != 1 or rebuilt[0].name != wheel.name:
            raise ValueError("Source rebuild did not produce the expected wheel")
        report["sdist_first_use"] = check_distribution(rebuilt[0], output / "sdist")
        if report["sdist_first_use"]["status"] != "verified":
            raise ValueError("Source-distribution first-use verification failed")
        report["status"] = "verified"
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report["error"] = str(exc)
    write_new_json(output / "verification.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = check_packages(args.directory, args.output)
        print(json.dumps({key: value for key, value in report.items() if key not in {"wheel", "sdist_first_use", "rebuild"}}))
        return 0 if report["status"] == "verified" else 1
    except (OSError, ValueError) as exc:
        print(f"Package verification: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
