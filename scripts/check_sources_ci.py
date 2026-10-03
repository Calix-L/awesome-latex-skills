#!/usr/bin/env python3
"""Persist the current-date source audit and fail for pending human review."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import sys
from audit_sources import audit
from project_support import write_new_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        # Explicit UTC+08:00 also works on Windows, where setting TZ is insufficient.
        report = audit(as_of=datetime.now(timezone(timedelta(hours=8))).date().isoformat())
        report["audit_timezone"] = "Asia/Shanghai (UTC+08:00)"
        write_new_json(args.output, report)
        print(json.dumps({"as_of": report["as_of"], "needs_review": report["needs_review"]}))
        return 1 if report["needs_review"] and not args.validate_only else 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Source audit: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
