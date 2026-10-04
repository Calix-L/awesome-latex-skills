#!/usr/bin/env python3
"""Audit source metadata and review dates offline; HTTP reachability is not verification."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

from project_support import ROOT, read_json, safe_path

CATALOG = ROOT / "maintenance/sources.json"


def audit(catalog=CATALOG, root=ROOT, as_of=None):
    today = date.fromisoformat(as_of) if as_of else date.today()
    data = read_json(catalog)
    if data.get("schema") != 1 or not isinstance(data.get("sources"), list) or not data["sources"]:
        raise ValueError("Expected a nonempty schema-1 source catalog")
    identifiers, rows = set(), []
    for item in data["sources"]:
        if not isinstance(item, dict):
            raise ValueError("Each source must be an object")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise ValueError("Source ids must be nonempty and unique")
        identifiers.add(identifier)
        url = urlsplit(item.get("url", ""))
        if url.scheme != "https" or not url.netloc or url.username or url.password:
            raise ValueError(f"Expected an official HTTPS source URL: {identifier}")
        if not isinstance(item.get("scope"), str) or not item["scope"].strip() or not item.get("applies_to"):
            raise ValueError(f"Missing scope/files: {identifier}")
        for filename in item["applies_to"]:
            if not safe_path(root, filename).is_file():
                raise ValueError(f"Missing source-dependent file: {filename}")
        if type(item.get("review_after_days")) is not int or item["review_after_days"] < 1:
            raise ValueError(f"Invalid review interval: {identifier}")
        if item.get("verification") not in {"content-reviewed", "entrypoint-only"}:
            raise ValueError(f"Invalid verification level: {identifier}")
        checked = item.get("checked_on")
        if checked is None:
            status, age = "unverified", None
        else:
            checked_date = date.fromisoformat(checked)
            age = (today - checked_date).days
            if age < 0:
                raise ValueError(f"Future review date: {identifier}")
            status = "due" if age >= item["review_after_days"] else "current"
            if item["verification"] == "entrypoint-only":
                status = "entrypoint-only" if status == "current" else "due"
        rows.append({**item, "status": status, "age_days": age})
    return {"schema": 1, "as_of": today.isoformat(), "sources": rows,
            "needs_review": [row["id"] for row in rows if row["status"] in {"due", "unverified", "entrypoint-only"}],
            "interpretation": "Dates record declared content reviews; this audit does not authenticate reviewer identity, make network requests or establish submission compliance"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--as-of", help="Explicit YYYY-MM-DD review date; otherwise local date")
    parser.add_argument("--validate-only", action="store_true", help="Check catalog integrity without failing for pending review")
    args = parser.parse_args(argv)
    try:
        report = audit(args.catalog, as_of=args.as_of)
        if args.json:
            print(json.dumps(report, ensure_ascii=True, indent=2))
        else:
            for row in report["sources"]:
                print(f"[{row['status']}] {row['id']}: {row['scope']}")
        return 0 if args.validate_only or not report["needs_review"] else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}) if args.json else f"Source audit: {exc}", file=sys.stdout if args.json else sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
