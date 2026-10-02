from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from install import REPO, SKILLS
from validate_repo import heading_ids, validate, validate_document


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        for name in SKILLS:
            shutil.copytree(REPO / name, self.repo / name)

    def change(self, relative, before, after):
        path = self.repo / relative
        text = path.read_text(encoding="utf-8")
        self.assertIn(before, text)
        path.write_text(text.replace(before, after, 1), encoding="utf-8")

    def test_repository_is_valid(self):
        self.assertEqual(validate(REPO), [])

    def test_missing_entrypoint_fails(self):
        (self.repo / "latex-fmt" / "SKILL.md").unlink()
        self.assertTrue(any("missing SKILL.md" in e for e in validate(self.repo)))

    def test_invalid_yaml_fails(self):
        (self.repo / "latex-fmt" / "agents" / "config.yaml").write_text("name: [", encoding="utf-8")
        self.assertTrue(any("config.yaml" in e for e in validate(self.repo)))

    def test_wrong_skill_name_fails(self):
        self.change("latex-fmt/SKILL.md", "name: latex-fmt", "name: wrong-name")
        self.assertTrue(any("name must match" in e for e in validate(self.repo)))

    def test_unsupported_frontmatter_fails(self):
        self.change("latex-fmt/SKILL.md", "name: latex-fmt", "version: 1.3.0\nname: latex-fmt")
        self.assertTrue(any("unsupported frontmatter" in e for e in validate(self.repo)))

    def test_version_mismatch_fails(self):
        self.change("latex-fmt/SKILL.md", 'version: "1.3.0"', 'version: "1.3.1"')
        self.assertTrue(any("versions differ" in e for e in validate(self.repo)))

    def test_missing_referenced_resource_fails(self):
        (self.repo / "latex-rescue" / "references" / "error-catalog.md").unlink()
        self.assertTrue(any("error-catalog.md" in e for e in validate(self.repo)))

    def test_broken_nested_reference_fails(self):
        path = self.repo / "latex-fmt" / "references" / "formatting-rules.md"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n[Details](missing.md)\n")
        self.assertTrue(any("missing.md" in e for e in validate(self.repo)))

    def test_broken_reference_anchor_fails(self):
        path = self.repo / "latex-rescue" / "SKILL.md"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n[Details](references/error-catalog.md#nonexistent-section)\n")
        self.assertTrue(any("missing heading anchor" in e for e in validate(self.repo)))

    def test_cross_bundle_resource_is_rejected_for_selected_installs(self):
        path = self.repo / "latex-rescue" / "SKILL.md"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n[Required resource](../pdf2tex/SKILL.md)\n")
        self.assertTrue(any("outside this skill bundle" in e for e in validate(self.repo)))

    def test_nested_project_documentation_is_checked(self):
        folder = self.repo / "docs"
        folder.mkdir()
        (folder / "guide.md").write_text("[missing](lost.md)", encoding="utf-8")
        self.assertTrue(any("lost.md" in e for e in validate(self.repo)))

    def test_installation_receipt_cannot_enter_source_bundle(self):
        (self.repo / "latex-rescue" / ".awesome-latex-skills-install.json").write_text("{}", encoding="utf-8")
        self.assertTrue(any("installation receipts" in e for e in validate(self.repo)))

    def test_wrong_agent_entrypoint_fails(self):
        self.change("latex-fmt/agents/config.yaml", "skill_file: latex-fmt/SKILL.md", "skill_file: other/SKILL.md")
        self.assertTrue(any("skill_file" in e for e in validate(self.repo)))

    def test_nonmapping_metadata_fails_without_traceback(self):
        self.change("latex-fmt/SKILL.md", 'metadata:\n  version: "1.3.0"', "metadata: []")
        self.assertTrue(any("metadata must be a mapping" in e for e in validate(self.repo)))

    def test_broken_readme_image_is_rejected(self):
        document = self.repo / "README.md"
        document.write_text('<picture><img src="assets/missing.svg"></picture>', encoding="utf-8")
        self.assertTrue(any("missing.svg" in e for e in validate_document(document, self.repo)))

    def test_broken_readme_navigation_is_rejected(self):
        document = self.repo / "README.md"
        document.write_text("# Title\n[Start](#missing-heading)\n", encoding="utf-8")
        self.assertTrue(any("missing heading" in e for e in validate_document(document, self.repo)))

    def test_chinese_and_duplicate_headings_resolve(self):
        document = self.repo / "README.md"
        document.write_text("## 快速开始\n## Quick start\n## Quick start\n[开始](#快速开始)\n[again](#quick-start-1)\n", encoding="utf-8")
        self.assertEqual(validate_document(document, self.repo), [])

    def test_fenced_examples_do_not_create_fake_links(self):
        document = self.repo / "README.md"
        document.write_text("```md\n# Fake\n[example](missing.md)\n```\n", encoding="utf-8")
        self.assertEqual(validate_document(document, self.repo), [])
        self.assertNotIn("fake", heading_ids(document.read_text(encoding="utf-8")))

    def test_reference_outside_repo_is_rejected(self):
        document = self.repo / "README.md"
        document.write_text("[outside](../private.txt)\n", encoding="utf-8")
        self.assertTrue(any("external local link" in e for e in validate_document(document, self.repo)))
