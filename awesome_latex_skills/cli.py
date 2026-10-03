"""Dispatch to packaged helpers using the same Python interpreter."""
from pathlib import Path
import runpy
import sys


def main():
    package = Path(__file__).resolve().parent
    root = package / "data"
    # Source/editable use keeps resources in the checkout; wheels are self-contained.
    if not (root / "VERSION").is_file():
        root = package.parent
    script = root / "scripts/als.py"
    if not script.is_file():
        raise RuntimeError("Packaged manuscript resources are missing; reinstall the wheel")
    sys.path.insert(0, str(root / "scripts"))
    try:
        module = runpy.run_path(str(script))
        return module["main"]()
    finally:
        sys.path.pop(0)
