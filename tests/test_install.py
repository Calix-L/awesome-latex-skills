import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from install import REPO, SKILLS, bundle_files, default_destination, install, main


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.destination = self.root / "directory with spaces" / "skills"

    def test_all_resources_roundtrip(self):
        result = install(REPO, self.destination, SKILLS)
        self.assertEqual(len(result), 5)
        for name in SKILLS:
            self.assertEqual(bundle_files(REPO / name), bundle_files(self.destination / name))

    def test_select_only_requested_skills(self):
        install(REPO, self.destination, ["pdf2tex", "latex-rescue"])
        self.assertEqual({p.name for p in self.destination.iterdir()}, {"pdf2tex", "latex-rescue"})

    def test_dry_run_creates_nothing(self):
        self.assertEqual(install(REPO, self.destination, ["latex-fmt"], True), [("latex-fmt", "install")])
        self.assertFalse(self.destination.parent.exists())

    def test_repeat_install_is_idempotent(self):
        install(REPO, self.destination, ["latex-fmt"])
        source = self.destination / "latex-fmt" / "SKILL.md"
        before = source.stat().st_mtime_ns
        self.assertEqual(install(REPO, self.destination, ["latex-fmt"]), [("latex-fmt", "unchanged")])
        self.assertEqual(source.stat().st_mtime_ns, before)

    def test_conflict_prevents_entire_batch(self):
        install(REPO, self.destination, ["latex-fmt"])
        edited = self.destination / "latex-fmt" / "SKILL.md"
        edited.write_text("user edits", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Existing skill differs"):
            install(REPO, self.destination, ["latex-rescue", "latex-fmt"])
        self.assertEqual(edited.read_text(), "user edits")
        self.assertFalse((self.destination / "latex-rescue").exists())

    def test_extra_user_resource_is_preserved(self):
        install(REPO, self.destination, ["latex-fmt"])
        extra = self.destination / "latex-fmt" / "notes.txt"
        extra.write_text("personal", encoding="utf-8")
        with self.assertRaises(ValueError):
            install(REPO, self.destination, ["latex-fmt"])
        self.assertEqual(extra.read_text(), "personal")

    def test_duplicate_selection_is_deduplicated(self):
        self.assertEqual(len(install(REPO, self.destination, ["latex-fmt", "latex-fmt"])), 1)

    def test_unknown_skill_cannot_traverse_paths(self):
        with self.assertRaisesRegex(ValueError, "Unknown skill"):
            install(REPO, self.destination, ["../elsewhere"])
        self.assertFalse(self.destination.exists())

    def test_source_destination_overlap_is_refused(self):
        with self.assertRaisesRegex(ValueError, "outside the source"):
            install(REPO, REPO / "installed", ["latex-fmt"])

    def test_file_destination_is_refused(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_text("keep", encoding="utf-8")
        with self.assertRaises(ValueError):
            install(REPO, self.destination, ["latex-fmt"])
        self.assertEqual(self.destination.read_text(), "keep")

    def test_missing_bundle_does_not_publish_other_skills(self):
        source = self.root / "source"
        source.mkdir()
        shutil.copytree(REPO / "latex-fmt", source / "latex-fmt")
        with self.assertRaises(ValueError):
            install(source, self.destination, ["latex-fmt", "pdf2tex"])
        self.assertFalse(self.destination.exists())

    def test_codex_home_is_respected(self):
        with patch.dict(os.environ, {"CODEX_HOME": str(self.root / "custom-codex")}):
            self.assertEqual(default_destination("codex"), self.root / "custom-codex" / "skills")

    def test_cli_dry_run(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = main(["--agent", "codex", "--dest", str(self.destination), "--skill", "latex-fmt", "--dry-run"])
        self.assertEqual(status, 0)
        self.assertIn("Would install: latex-fmt", output.getvalue())
        self.assertFalse(self.destination.exists())

    def test_installer_runs_without_site_packages(self):
        result = subprocess.run(
            [sys.executable, "-I", "-S", str(REPO / "scripts" / "install.py"),
             "--dest", str(self.destination), "--skill", "pdf2tex"],
            text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(bundle_files(REPO / "pdf2tex"), bundle_files(self.destination / "pdf2tex"))

    def test_cli_conflict_returns_failure(self):
        self.destination.mkdir(parents=True)
        (self.destination / "latex-fmt").write_text("keep", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            status = main(["--dest", str(self.destination), "--skill", "latex-fmt"])
        self.assertEqual(status, 1)

    def test_publish_failure_rolls_back_new_bundles(self):
        original = Path.rename

        def fail_second(path, target):
            if path.name == "pdf2tex":
                raise OSError("simulated publish failure")
            return original(path, target)

        with patch.object(Path, "rename", fail_second):
            with self.assertRaisesRegex(OSError, "simulated"):
                install(REPO, self.destination, ["latex-fmt", "pdf2tex"])
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_target_symlink_is_refused(self):
        self.destination.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.destination / "latex-fmt").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks requires privileges on this system")
        with self.assertRaisesRegex(ValueError, "symlink"):
            install(REPO, self.destination, ["latex-fmt"])
        self.assertEqual(list(outside.iterdir()), [])
