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
from install import REPO, SKILLS, RECEIPT, LOCK, bundle_files, default_destination, install, main, installation_lock


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

    def test_concurrent_cli_is_blocked_and_can_retry_after_lock_release(self):
        self.destination.mkdir(parents=True)
        with installation_lock(self.destination):
            original = (self.destination / LOCK).read_bytes()
            command = [sys.executable, "-I", "-S", str(REPO / "scripts/install.py"),
                       "--dest", str(self.destination), "--skill", "latex-fmt"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 1)
            self.assertIn("lock exists", result.stderr)
            self.assertEqual((self.destination / LOCK).read_bytes(), original)
            self.assertFalse((self.destination / "latex-fmt").exists())
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.destination / LOCK).exists())

    def test_dry_run_never_removes_an_existing_lock(self):
        self.destination.mkdir(parents=True)
        lock = self.destination / LOCK
        lock.write_text("stale or active; preserve", encoding="utf-8")
        before = lock.read_bytes()
        self.assertEqual(install(REPO, self.destination, ["latex-fmt"], dry_run=True), [("latex-fmt", "install")])
        self.assertEqual(lock.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "lock exists"):
            install(REPO, self.destination, ["latex-fmt"])
        self.assertEqual(lock.read_bytes(), before)

    def test_lock_releases_on_interrupt_without_deleting_a_replacement(self):
        self.destination.mkdir(parents=True)
        with self.assertRaises(KeyboardInterrupt):
            with installation_lock(self.destination):
                raise KeyboardInterrupt()
        self.assertFalse((self.destination / LOCK).exists())
        with installation_lock(self.destination):
            lock = self.destination / LOCK
            lock.rename(self.destination / "old-lock")
            lock.write_text("other owner", encoding="utf-8")
        self.assertEqual(lock.read_text(), "other owner")


class UpdateTests(unittest.TestCase):
    def setUp(self):
        InstallerTests.setUp(self)
        self.source = self.root / "source"
        self.source.mkdir()
        for name in ("latex-fmt", "pdf2tex"):
            shutil.copytree(REPO / name, self.source / name)

    def change_source(self, name="latex-fmt"):
        (self.source / name / "SKILL.md").write_text("new upstream instructions", encoding="utf-8")

    def test_update_replaces_managed_bundle_including_removed_resources(self):
        old = self.source / "latex-fmt" / "old.txt"
        old.write_text("old resource", encoding="utf-8")
        install(self.source, self.destination, ["latex-fmt"])
        old.unlink()
        self.change_source()
        (self.source / "latex-fmt" / "new.txt").write_text("new resource", encoding="utf-8")
        self.assertEqual(install(self.source, self.destination, ["latex-fmt"], update=True), [("latex-fmt", "update")])
        self.assertEqual(bundle_files(self.source / "latex-fmt"), bundle_files(self.destination / "latex-fmt"))
        self.assertFalse((self.destination / "latex-fmt" / "old.txt").exists())
        self.assertEqual(install(self.source, self.destination, ["latex-fmt"], update=True), [("latex-fmt", "unchanged")])

    def test_update_remains_opt_in(self):
        install(self.source, self.destination, ["latex-fmt"])
        before = bundle_files(self.destination / "latex-fmt")
        self.change_source()
        with self.assertRaisesRegex(ValueError, "Existing skill differs"):
            install(self.source, self.destination, ["latex-fmt"])
        self.assertEqual(bundle_files(self.destination / "latex-fmt"), before)

    def test_update_protects_local_edits_and_preflights_entire_batch(self):
        install(self.source, self.destination, ["latex-fmt"])
        edited = self.destination / "latex-fmt" / "SKILL.md"
        edited.write_text("personal edits", encoding="utf-8")
        self.change_source()
        with self.assertRaisesRegex(ValueError, "locally edited"):
            install(self.source, self.destination, ["pdf2tex", "latex-fmt"], update=True)
        self.assertEqual(edited.read_text(), "personal edits")
        self.assertFalse((self.destination / "pdf2tex").exists())

    def test_update_protects_extra_and_deleted_local_files(self):
        for mutation in ("extra", "deleted"):
            with self.subTest(mutation=mutation):
                destination = self.root / mutation
                install(self.source, destination, ["latex-fmt"])
                if mutation == "extra":
                    (destination / "latex-fmt" / "notes.txt").write_text("keep", encoding="utf-8")
                else:
                    (destination / "latex-fmt" / "agents" / "config.yaml").unlink()
                self.change_source()
                before = bundle_files(destination / "latex-fmt")
                with self.assertRaises(ValueError):
                    install(self.source, destination, ["latex-fmt"], update=True)
                self.assertEqual(bundle_files(destination / "latex-fmt"), before)

    def test_identical_legacy_bundle_can_be_adopted(self):
        self.destination.mkdir(parents=True)
        shutil.copytree(self.source / "latex-fmt", self.destination / "latex-fmt")
        self.assertEqual(install(self.source, self.destination, ["latex-fmt"], update=True), [("latex-fmt", "adopt")])
        self.change_source()
        self.assertEqual(install(self.source, self.destination, ["latex-fmt"], update=True), [("latex-fmt", "update")])

    def test_unmanaged_different_bundle_is_not_adopted(self):
        self.destination.mkdir(parents=True)
        shutil.copytree(self.source / "latex-fmt", self.destination / "latex-fmt")
        self.change_source()
        with self.assertRaisesRegex(ValueError, "Unmanaged"):
            install(self.source, self.destination, ["latex-fmt"], update=True)
        self.assertFalse((self.destination / "latex-fmt" / RECEIPT).exists())

    def test_corrupt_receipt_cannot_authorize_update(self):
        install(self.source, self.destination, ["latex-fmt"])
        receipt = self.destination / "latex-fmt" / RECEIPT
        receipt.write_text("not JSON", encoding="utf-8")
        self.change_source()
        with self.assertRaises(ValueError):
            install(self.source, self.destination, ["latex-fmt"], update=True)
        self.assertEqual(receipt.read_text(), "not JSON")

    def test_dry_run_update_does_not_touch_files_or_receipt(self):
        install(self.source, self.destination, ["latex-fmt"])
        before = {p.relative_to(self.destination): p.read_bytes() for p in self.destination.rglob("*") if p.is_file()}
        self.change_source()
        self.assertEqual(install(self.source, self.destination, ["latex-fmt"], True, True), [("latex-fmt", "update")])
        after = {p.relative_to(self.destination): p.read_bytes() for p in self.destination.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_publish_failure_restores_original_bundles_and_receipts(self):
        install(self.source, self.destination, ["latex-fmt", "pdf2tex"])
        before = {p.relative_to(self.destination): p.read_bytes() for p in self.destination.rglob("*") if p.is_file()}
        self.change_source()
        self.change_source("pdf2tex")
        original = Path.rename

        def fail_second(path, target):
            if path.name == "pdf2tex" and path.parent.name == "new":
                raise OSError("simulated update failure")
            return original(path, target)

        with patch.object(Path, "rename", fail_second), self.assertRaises(OSError):
            install(self.source, self.destination, ["latex-fmt", "pdf2tex"], update=True)
        after = {p.relative_to(self.destination): p.read_bytes() for p in self.destination.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_rollback_failure_preserves_recovery_files(self):
        install(self.source, self.destination, ["latex-fmt"])
        before = bundle_files(self.destination / "latex-fmt")
        self.change_source()
        original = Path.rename

        def fail_publish_and_restore(path, target):
            if path.name == "latex-fmt" and path.parent.name in ("new", "old"):
                raise OSError("simulated failure")
            return original(path, target)

        with patch.object(Path, "rename", fail_publish_and_restore), self.assertRaisesRegex(RuntimeError, "preserved files"):
            install(self.source, self.destination, ["latex-fmt"], update=True)
        backups = list(self.destination.glob(".latex-skills-*/old/latex-fmt"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(bundle_files(backups[0]), before)

    def test_interrupted_update_restores_old_bundle(self):
        install(self.source, self.destination, ["latex-fmt"])
        before = bundle_files(self.destination / "latex-fmt")
        self.change_source()
        original = Path.rename

        def interrupt_publish(path, target):
            if path.parent.name == "new":
                raise KeyboardInterrupt()
            return original(path, target)

        with patch.object(Path, "rename", interrupt_publish), self.assertRaises(KeyboardInterrupt):
            install(self.source, self.destination, ["latex-fmt"], update=True)
        self.assertEqual(bundle_files(self.destination / "latex-fmt"), before)
        self.assertEqual(list(self.destination.glob(".latex-skills-*")), [])

    def test_edit_after_preflight_is_preserved_and_new_publications_roll_back(self):
        install(self.source, self.destination, ["latex-fmt"])
        self.change_source()
        edited = self.destination / "latex-fmt" / "SKILL.md"
        original = Path.write_bytes

        def edit_during_staging(path, data):
            if path.name == "SKILL.md" and path.parent.name == "pdf2tex" and path.parent.parent.name == "new":
                edited.write_text("new personal edit", encoding="utf-8")
            return original(path, data)

        with patch.object(Path, "write_bytes", edit_during_staging), self.assertRaisesRegex(ValueError, "changed during"):
            install(self.source, self.destination, ["pdf2tex", "latex-fmt"], update=True)
        self.assertEqual(edited.read_text(), "new personal edit")
        self.assertFalse((self.destination / "pdf2tex").exists())
