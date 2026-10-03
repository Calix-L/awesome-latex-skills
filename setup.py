"""Bundle the existing repository resources in wheels without duplicating source."""
from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent
DIRECTORIES = ("scripts", "latex-rescue", "latex-polish", "latex-fmt", "paper-read", "pdf2tex",
               "assets", "docs", "examples", "evaluation", "maintenance", "tests", ".github", "awesome_latex_skills")
FILES = ("VERSION", "LICENSE", "README.md", "README_CN.md", "CHANGELOG.md", "CONTRIBUTING.md",
         "requirements-dev.txt", ".gitignore", ".gitattributes", "pyproject.toml", "setup.py", "MANIFEST.in")


def sources():
    found = [ROOT / name for name in FILES]
    for name in DIRECTORIES:
        directory = ROOT / name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"Missing regular package resource directory: {name}")
        found.extend(path for path in directory.rglob("*") if "__pycache__" not in path.parts
                     and path.suffix not in {".pyc", ".pyo"} and (path.is_file() or path.is_symlink()))
    for path in found:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Package resource must be a regular file: {path}")
    return found


class BundleBuild(build_py):
    def run(self):
        super().run()
        if self.editable_mode:
            return
        inputs = sources()
        expected = {path.relative_to(ROOT).as_posix() for path in inputs}
        target_root = Path(self.build_lib).resolve() / "awesome_latex_skills/data"
        if target_root.exists():
            for path in target_root.rglob("*"):
                if path.is_symlink() or path.is_file() and path.relative_to(target_root).as_posix() not in expected:
                    raise ValueError("Stale package resources; use a clean build directory before rebuilding")
        for source in inputs:
            target = Path(self.build_lib) / "awesome_latex_skills/data" / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def get_source_files(self):
        return super().get_source_files() + [path.relative_to(ROOT).as_posix() for path in sources()]

    def get_outputs(self, include_bytecode=1):
        extra = [] if self.editable_mode else [str(Path(self.build_lib) / "awesome_latex_skills/data" / path.relative_to(ROOT)) for path in sources()]
        return super().get_outputs(include_bytecode) + extra


setup(cmdclass={"build_py": BundleBuild})
