"""Offline artifact checks must detect corruption and never extract or execute."""
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import artifact_integrity as inventory
from package_release import package
from project_support import ROOT, read_json, sha256
from review_project import review
import verify_artifacts as verifier


class IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.template.cleanup)
        cls.release_template = Path(cls.template.name) / 'release'
        package(cls.release_template)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def release(self):
        destination = self.root / 'release'
        shutil.copytree(self.release_template, destination)
        return destination

    def review(self):
        for side in ('before', 'after'):
            folder = self.root / side
            folder.mkdir()
            (folder / 'main.tex').write_text('Original $x$\n', encoding='utf-8')
        output = self.root / 'review'
        review(self.root / 'before', self.root / 'after', output, language='zh')
        return output

    def update_manifest(self, root, manifest, refresh_assets=True):
        if refresh_assets:
            for item in manifest['archives']:
                path = root / item['file']
                item.update(sha256=sha256(path), bytes=path.stat().st_size)
        path = root / 'release-manifest.json'
        path.write_text(json.dumps(manifest), encoding='utf-8')
        (root / 'SHA256SUMS').write_text(''.join(f"{row['sha256']}  {row['file']}\n" for row in manifest['archives'])
                                      + f"{sha256(path)}  release-manifest.json\n", encoding='utf-8')

    def append_distributions(self, root):
        manifest = read_json(root / 'release-manifest.json')
        current = manifest['version']
        with zipfile.ZipFile(root / f'awesome-latex-skills-{current}.zip') as source:
            contents = {name: source.read(name) for name in source.namelist()}
        wheel_name = f'awesome_latex_skills-{current}-py3-none-any.whl'
        with zipfile.ZipFile(root / wheel_name, 'w') as wheel:
            for name, content in contents.items():
                wheel.writestr('awesome_latex_skills/data/' + name, content)
            wheel.writestr('awesome_latex_skills/cli.py', '# Synthetic packaging fixture; never executed\n')
        tar_name = f'awesome_latex_skills-{current}.tar.gz'
        with tarfile.open(root / tar_name, 'w:gz') as archive:
            for name, content in contents.items():
                member = tarfile.TarInfo(f'awesome_latex_skills-{current}/{name}')
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
        manifest['archives'].extend({'file': name, 'sha256': sha256(root / name), 'bytes': (root / name).stat().st_size,
                                     'entries': None} for name in (wheel_name, tar_name))
        self.update_manifest(root, manifest)
        return wheel_name, tar_name

    def test_release_checks_all_members_without_extraction_and_changes_nothing(self):
        root = self.release()
        before = inventory.file_inventory(root)
        with patch.object(zipfile.ZipFile, 'extractall', side_effect=AssertionError('No extraction')):
            result = verifier.verify_release(root)
        self.assertEqual(result['status'], 'verified', result)
        self.assertEqual(result['archives_checked'], 6)
        self.assertEqual(result['authentication'], 'not verified')
        self.assertEqual(before, inventory.file_inventory(root))

    def test_complete_review_can_be_moved_without_original_projects(self):
        root = self.review()
        moved = self.root / 'moved-review'
        root.rename(moved)
        for side in ('before', 'after'):
            (self.root / side).rename(self.root / ('gone-' + side))
        result = verifier.verify_review(moved)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['files_checked'], 3)

    def test_review_detects_changed_html_json_and_diff(self):
        root = self.review()
        for name in ('report.html', 'review.json', 'changes.diff'):
            path = root / name
            old = path.read_bytes()
            path.write_bytes(old + b'changed')
            with self.subTest(name=name):
                result = verifier.verify_review(root)
                self.assertEqual(result['status'], 'failed')
                self.assertTrue(any(row['file'] == name and row['code'] == 'changed-file' for row in result['findings']))
            path.write_bytes(old)

    def test_review_reports_missing_and_uninventoried_files(self):
        root = self.review()
        (root / 'report.html').unlink()
        (root / '.hidden-extra').write_bytes(b'extra')
        result = verifier.verify_review(root)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual({row['code'] for row in result['findings']}, {'missing-file', 'unexpected-file'})

    def test_legacy_review_stays_unverified_including_source_only_case(self):
        root = self.review()
        (root / 'integrity.json').unlink()
        result = verifier.verify_review(root)
        self.assertEqual(result['status'], 'unverified')
        self.assertEqual(result['files_checked'], 0)
        extra = root / 'legacy-log.txt'
        extra.write_bytes(b'actual legacy bytes')
        report = read_json(root / 'review.json')
        report['builds']['after']['retained_files'] = [{'file': extra.name, 'sha256': sha256(extra), 'bytes': extra.stat().st_size}]
        (root / 'review.json').write_text(json.dumps(report), encoding='utf-8')
        self.assertEqual(verifier.verify_review(root)['status'], 'unverified')
        extra.write_bytes(b'changed')
        self.assertEqual(verifier.verify_review(root)['status'], 'failed')

    def test_invalid_paths_duplicates_hashes_and_byte_counts_are_refused(self):
        root = self.review()
        original = read_json(root / 'integrity.json')
        for field, value in (('file', '../outside'), ('file', 'a//b'), ('file', 'a/./b'), ('file', 'C:/outside'),
                             ('sha256', 'not-a-hash'), ('bytes', True), ('bytes', -1), ('bytes', 10**100)):
            manifest = json.loads(json.dumps(original))
            manifest['files'][0][field] = value
            (root / 'integrity.json').write_text(json.dumps(manifest), encoding='utf-8')
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                verifier.verify_review(root)
        for duplicate in (original['files'][0], {**original['files'][0], 'file': original['files'][0]['file'].upper()}):
            manifest = {**original, 'files': original['files'] + [duplicate]}
            (root / 'integrity.json').write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Duplicate or case-colliding'):
                verifier.verify_review(root)

    def test_manifest_cannot_omit_report_files_or_include_itself(self):
        root = self.review()
        original = read_json(root / 'integrity.json')
        for rows in (original['files'][1:], original['files'] + [{'file': 'integrity.json', 'sha256': sha256(root / 'integrity.json'), 'bytes': 0}]):
            (root / 'integrity.json').write_text(json.dumps({**original, 'files': rows}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'must cover HTML/JSON/diff'):
                verifier.verify_review(root)

    def test_sealing_never_replaces_existing_manifest(self):
        root = self.review()
        before = inventory.file_inventory(root)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            inventory.seal_review(root)
        self.assertEqual(before, inventory.file_inventory(root))

    def test_release_detects_missing_changed_and_extra_assets(self):
        root = self.release()
        manifest = read_json(root / 'release-manifest.json')
        assets = [root / row['file'] for row in manifest['archives']]
        assets[0].unlink()
        assets[1].write_bytes(assets[1].read_bytes() + b'changed')
        (root / 'extra.txt').write_bytes(b'extra')
        result = verifier.verify_release(root)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual({row['code'] for row in result['findings']}, {'missing-file', 'changed-file', 'unexpected-file'})

    def test_checksum_disagreement_and_malformed_coverage_are_not_hidden(self):
        root = self.release()
        path = root / 'SHA256SUMS'
        old = path.read_text(encoding='utf-8')
        path.write_text('0'*64 + old[64:], encoding='utf-8')
        self.assertIn('checksum-disagreement', {row['code'] for row in verifier.verify_release(root)['findings']})
        for content in (old + old.splitlines()[0] + '\n', '\n'.join(old.splitlines()[1:]) + '\n', 'malformed\n'):
            path.write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):
                verifier.verify_release(root)

    def test_source_member_changes_are_detected_even_with_new_outer_checksums(self):
        root = self.release()
        manifest = read_json(root / 'release-manifest.json')
        path = root / f"latex-polish-{manifest['version']}.zip"
        with zipfile.ZipFile(path) as archive:
            data = {name: archive.read(name) for name in archive.namelist()}
        data['latex-polish/SKILL.md'] += b'changed'
        with zipfile.ZipFile(path, 'w') as archive:
            for name, content in data.items():
                archive.writestr(name, content)
        self.update_manifest(root, manifest)
        result = verifier.verify_release(root)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any('source fingerprint' in row['message'] for row in result['findings']))

    def test_zip_traversal_duplicate_and_link_members_are_refused(self):
        root = self.release()
        manifest = read_json(root / 'release-manifest.json')
        path = root / f"latex-polish-{manifest['version']}.zip"
        original = path.read_bytes()
        for kind in ('traversal', 'duplicate', 'symlink'):
            path.write_bytes(original)
            with zipfile.ZipFile(path, 'a') as archive:
                if kind == 'symlink':
                    member = zipfile.ZipInfo('link')
                    member.create_system = 3
                    member.external_attr = 0o120777 << 16
                    archive.writestr(member, b'outside')
                else:
                    name = '../outside' if kind == 'traversal' else 'LICENSE'
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', UserWarning)
                        archive.writestr(name, b'outside')
            self.update_manifest(root, manifest)
            with self.subTest(kind=kind):
                result = verifier.verify_release(root)
                self.assertEqual(result['status'], 'failed')
                self.assertIn('invalid-archive', {row['code'] for row in result['findings']})
        self.assertFalse((self.root / 'outside').exists())

    def test_zip_parser_metadata_and_expansion_are_bounded(self):
        path = self.root / 'tiny.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('value', b'1234')
        with patch.object(verifier, 'MAX_METADATA_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'central directory'):
                verifier.zip_preflight(path)
        with zipfile.ZipFile(path) as archive, patch.object(verifier, 'MAX_TOTAL_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'byte limits'):
                verifier.zip_inventory(self.root, archive)
        with zipfile.ZipFile(path) as archive, patch.object(archive, 'infolist', return_value=[zipfile.ZipInfo('value\x00hidden')]):
            with self.assertRaisesRegex(ValueError, 'raw member name'):
                verifier.zip_inventory(self.root, archive)
        data = path.read_bytes()
        offset = data.rfind(b'PK\x05\x06')
        malicious = bytearray(data)
        struct.pack_into('<H', malicious, offset + 10, 65535)
        path.write_bytes(malicious)
        with self.assertRaisesRegex(ValueError, 'ZIP64/count'):
            verifier.zip_preflight(path)

    def test_wheel_and_source_resources_are_bound_without_extraction(self):
        root = self.release()
        self.append_distributions(root)
        with patch.object(zipfile.ZipFile, 'extractall', side_effect=AssertionError('No extraction')), patch.object(tarfile.TarFile, 'extractall', side_effect=AssertionError('No extraction')):
            result = verifier.verify_release(root)
        self.assertEqual(result['status'], 'verified', result)
        self.assertEqual(result['archives_checked'], 8)

    def test_source_archive_links_and_missing_resource_are_refused(self):
        root = self.release()
        _, name = self.append_distributions(root)
        manifest = read_json(root / 'release-manifest.json')
        path = root / name
        for kind in ('link', 'missing'):
            with tarfile.open(path, 'w:gz') as archive:
                member = tarfile.TarInfo(f"awesome_latex_skills-{manifest['version']}/link")
                member.type = tarfile.SYMTYPE if kind == 'link' else tarfile.REGTYPE
                member.linkname = '../outside'
                archive.addfile(member, None if kind == 'link' else io.BytesIO(b''))
            self.update_manifest(root, manifest)
            with self.subTest(kind=kind):
                self.assertEqual(verifier.verify_release(root)['status'], 'failed')

    def test_tar_metadata_reads_and_uncompressed_seeks_are_bounded(self):
        reader = verifier.BoundedTarReader(io.BytesIO(b'header'))
        self.assertEqual(reader.read(3), b'hea')
        with self.assertRaisesRegex(ValueError, 'metadata or expanded'):
            reader.read(verifier.MAX_METADATA_BYTES + 1)
        with self.assertRaisesRegex(ValueError, 'seek exceeds'):
            reader.seek(verifier.MAX_TOTAL_BYTES + 1)

    def test_truncated_gzip_and_decompression_errors_are_structured_failures(self):
        root = self.release()
        _, name = self.append_distributions(root)
        manifest = read_json(root / 'release-manifest.json')
        path = root / name
        path.write_bytes(path.read_bytes()[:12])
        self.update_manifest(root, manifest)
        result = verifier.verify_release(root)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any(row['file'] == name and row['code'] == 'invalid-archive' for row in result['findings']))
        import zlib
        with patch.object(verifier, 'check_zip', side_effect=zlib.error('Malformed compressed member')):
            result = verifier.verify_release(root)
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Malformed compressed member', str(result['findings']))

    def test_cli_uses_failure_unverified_and_invalid_precondition_exit_codes(self):
        root = self.review()
        def run(*args):
            process = subprocess.run([sys.executable, str(ROOT / 'scripts/als.py'), '--json', 'verify', *map(str, args)],
                                     cwd=self.root, capture_output=True, encoding='utf-8')
            return process.returncode, json.loads(process.stdout)
        code, result = run('review', root)
        self.assertEqual(code, 0)
        self.assertEqual(result['result']['status'], 'verified')
        (root / 'changes.diff').write_text('changed', encoding='utf-8')
        code, result = run('review', root)
        self.assertEqual(code, 1)
        self.assertEqual(result['result']['status'], 'failed')
        (root / 'integrity.json').unlink()
        code, result = run('review', root)
        self.assertEqual(code, 1)
        self.assertEqual(result['result']['status'], 'unverified')
        self.assertEqual(run('release', self.root / 'missing')[0], 2)

    def test_verifier_refuses_symlinks_without_following_them(self):
        root = self.review()
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'marker').write_bytes(b'outside')
        try:
            (root / 'linked').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlink creation is unavailable')
        with self.assertRaisesRegex(ValueError, 'Symlink or escaping'):
            verifier.verify_review(root)

    def test_metadata_limits_apply_before_parsing_or_hashing_oversized_inputs(self):
        root = self.release()
        with patch.object(verifier, 'MAX_METADATA_BYTES', 4), patch.object(verifier, 'parse_json', side_effect=AssertionError('Must not parse oversized metadata')):
            with self.assertRaisesRegex(ValueError, 'size limit'):
                verifier.verify_release(root)
        with patch.object(verifier, 'MAX_FILE_BYTES', 4):
            with self.assertRaisesRegex(ValueError, 'size limit'):
                verifier.bounded_file_hash(root / 'release-manifest.json')

    def test_failed_manifest_creation_never_publishes_partial_review(self):
        with patch('review_project.seal_review', side_effect=OSError('Deliberate manifest write failure')):
            with self.assertRaisesRegex(OSError, 'manifest write failure'):
                self.review()
        self.assertFalse((self.root / 'review').exists())


if __name__ == '__main__':
    unittest.main()
