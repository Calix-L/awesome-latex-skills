"""Negative controls for retained review evidence and literal content signals."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_support import ROOT, read_json, sha256, write_new_json
import review_project as tool


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.languages = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.links.append(attrs['href'])
        if tag == 'html':
            self.languages.append(attrs['lang'])


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for side in ('before', 'after'):
            self.put(f'{side}/main.tex', r'\documentclass{article}' + '\nOriginal $x^2$\n')
        self.output = self.root / 'review'

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def record(self, status='failed'):
        source = self.root / 'after/main.tex'
        folder = self.root / 'build'
        folder.mkdir()
        self.put('build/logs/engine.txt', 'Actual retained fixture transcript')
        report = {'schema': 3, 'status': status, 'source': str(source), 'source_sha256': sha256(source),
                  'source_unchanged': True, 'steps': [{'transcript': 'logs/engine.txt'}],
                  'local_inputs': [{'path': 'main.tex', 'observations': [{'sha256': sha256(source)}]}],
                  'input_tracking': {'changed': [], 'unreadable': []}}
        if status == 'success':
            import pymupdf
            with pymupdf.open() as doc:
                doc.new_page().insert_text((70, 70), 'PDF retention fixture')
                doc.save(folder / 'main.pdf')
            report.update(pdf='main.pdf', pdf_sha256=sha256(folder / 'main.pdf'))
        path = folder / 'build-report.json'
        write_new_json(path, report)
        return path

    def test_math_delimiters_ignore_escaped_dollars_and_preserve_display_content(self):
        self.assertEqual(list(tool.simple_math(r'Cost \$5 and \$9; $x+\$a$ $$y^2$$ \(z\) \[w\]')),
                         [('$', r'x+\$a'), ('$$', 'y^2'), (r'\(', 'z'), (r'\[', 'w')])
        self.assertNotEqual(tool.content_tokens('$$x$$')[2], tool.content_tokens('$$y$$')[2])
        self.assertFalse(tool.content_tokens(r'Cost \$5 and \$9')[2])
        self.assertEqual(list(tool.simple_math(r'\\$x$')), [('$', 'x')])
        self.assertEqual(list(tool.simple_math(r'\$$x$')), [('$', 'x')])

    def test_literal_keys_skip_nested_macros_and_include_nocite(self):
        keys = tool.content_tokens(r'\cite{\macro{key}} \nocite{literal} \ref{known}')[1]
        self.assertEqual(keys, {('nocite', 'literal'): 1, ('ref', 'known'): 1})

    def test_comment_examples_do_not_hide_real_numeric_and_reference_changes(self):
        self.put('before/main.tex', '% \\begin{verbatim}\nValue 42 \\ref{old}\n% \\end{verbatim}\n')
        self.put('after/main.tex', '% \\begin{verbatim}\nValue 43 \\ref{new}\n% \\end{verbatim}\n')
        result = tool.review(self.root / 'before', self.root / 'after', self.output)
        report = read_json(self.output / 'review.json')
        self.assertEqual(result['content_flags'], 1)
        self.assertEqual(report['content_audit'][0]['numbers']['added'], [['43', 1]])
        self.assertIn('reference_keys', report['content_audit'][0])
        self.assertEqual(report['source_scan_issues'], [])

    def test_unchanged_unclosed_source_is_visible_in_both_review_sides(self):
        for side in ('before', 'after'):
            self.put(f'{side}/main.tex', '\\documentclass{article}\n\\begin{verbatim}\n99')
        result = tool.review(self.root / 'before', self.root / 'after', self.output, language='zh')
        self.assertEqual(result['changed_files'], 0)
        self.assertEqual(result['source_scan_issues'], 2)
        report = read_json(self.output / 'review.json')
        self.assertEqual([item['side'] for item in report['source_scan_issues']], ['before', 'after'])
        page = (self.output / 'report.html').read_text(encoding='utf-8')
        self.assertIn('未闭合的源码字面区域', page)
        self.assertIn('main.tex:2', page)

    def test_chinese_source_report_lists_binary_changes_and_scope(self):
        (self.root / 'before/panel.png').write_bytes(b'before')
        (self.root / 'after/panel.png').write_bytes(b'after')
        self.put('after/CHAPTER.TEX', 'TODO: <script>decide</script>')
        result = tool.review(self.root / 'before', self.root / 'after', self.output, language='zh')
        self.assertEqual(result['changed_files'], 2)
        self.assertEqual(result['open_decisions'], 1)
        report = read_json(self.output / 'review.json')
        self.assertEqual(report['language'], 'zh')
        self.assertEqual(report['inventory_scope']['other_files'], 'not inspected')
        self.assertIn('.venv', report['inventory_scope']['excluded_directories'])
        page = (self.output / 'report.html').read_text(encoding='utf-8')
        self.assertIn('论文修改审阅', page)
        self.assertIn('panel.png', page)
        self.assertIn('CHAPTER.TEX:1', page)
        self.assertNotIn('<script>', page)
        parsed = Links()
        parsed.feed(page)
        self.assertEqual(parsed.languages, ['zh'])
        self.assertEqual(parsed.links, ['review.json', 'changes.diff', 'integrity.json'])

    def test_cli_chinese_review_runs_from_other_working_directory(self):
        run = subprocess.run([sys.executable, str(ROOT / 'scripts/als.py'), '--json', 'review',
                              '--before', str(self.root / 'before'), '--after', str(self.root / 'after'),
                              '--output', str(self.output), '--language', 'zh'],
                             cwd=self.root, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['result']['builds']['after'], 'unverified')
        self.assertIn('论文修改审阅', (self.output / 'report.html').read_text(encoding='utf-8'))

    def test_missing_declared_log_refuses_publication(self):
        record = self.record()
        (record.parent / 'logs/engine.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'declared build evidence is missing'):
            tool.review(self.root / 'before', self.root / 'after', self.output, after_build=record)
        self.assertFalse(self.output.exists())

    def test_copy_time_mutation_of_report_log_and_pdf_refuses_publication(self):
        record = self.record('success')
        real_copy = shutil.copyfile
        for name in ('build-report.json', 'engine.txt', 'main.pdf'):
            original = record if name == 'build-report.json' else record.parent / ('logs/engine.txt' if name == 'engine.txt' else name)
            old = original.read_bytes()
            def corrupt(src, dst):
                result = real_copy(src, dst)
                if Path(src).name == name:
                    Path(src).write_bytes(Path(src).read_bytes() + b'changed')
                return result
            with self.subTest(name=name), patch.object(tool.shutil, 'copyfile', side_effect=corrupt):
                with self.assertRaisesRegex(ValueError, 'evidence changed during retention'):
                    tool.review(self.root / 'before', self.root / 'after', self.output, after_build=record)
            self.assertFalse(self.output.exists())
            original.write_bytes(old)

    def test_post_render_mutation_of_log_or_page_refuses_publication(self):
        record = self.record('success')
        real_render = tool.render
        for item in ('original-log', 'retained-page'):
            def mutate(bundle, report, diffs):
                real_render(bundle, report, diffs)
                path = record.parent / 'logs/engine.txt' if item == 'original-log' else bundle / 'evidence/after/pages/page-0001.png'
                path.write_bytes(path.read_bytes() + b'changed')
            with self.subTest(item=item), patch.object(tool, 'render', side_effect=mutate):
                with self.assertRaisesRegex(ValueError, 'evidence changed before review publication'):
                    tool.review(self.root / 'before', self.root / 'after', self.output, after_build=record)
            self.assertFalse(self.output.exists())

    def test_source_mutation_after_render_refuses_publication(self):
        real_render = tool.render
        def mutate(bundle, report, diffs):
            real_render(bundle, report, diffs)
            self.put('after/main.tex', 'Changed after rendering')
        with patch.object(tool, 'render', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'Project inputs changed'):
                tool.review(self.root / 'before', self.root / 'after', self.output)
        self.assertFalse(self.output.exists())

    def test_parsed_bytes_must_match_initial_snapshot(self):
        real_read = tool.read_source
        def changed_read(path):
            data = real_read(path)
            return data + b'\nchanged' if path.resolve() == (self.root / 'after/main.tex').resolve() else data
        with patch.object(tool, 'read_source', changed_read):
            with self.assertRaisesRegex(ValueError, 'changed before parsing'):
                tool.review(self.root / 'before', self.root / 'after', self.output)
        self.assertFalse(self.output.exists())

    def test_unreadable_successful_inputs_are_refused(self):
        record = self.record('success')
        data = read_json(record)
        data['input_tracking']['unreadable'] = ['chapter.tex']
        record.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'stable source inputs'):
            tool.review(self.root / 'before', self.root / 'after', self.output, after_build=record)
        self.assertFalse(self.output.exists())

    def test_all_retained_artifacts_have_matching_fingerprints_and_offline_links(self):
        record = self.record('success')
        tool.review(self.root / 'before', self.root / 'after', self.output, after_build=record, language='zh')
        report = read_json(self.output / 'review.json')
        artifacts = report['builds']['after']['retained_files']
        self.assertEqual(len(artifacts), 4)
        for item in artifacts:
            data = (self.output / item['file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'])
            self.assertEqual(len(data), item['bytes'])
        parsed = Links()
        parsed.feed((self.output / 'report.html').read_text(encoding='utf-8'))
        for link in parsed.links:
            self.assertTrue((self.output / link).is_file(), link)

    def test_old_pdf_without_build_time_hash_remains_visibly_unverified(self):
        record = self.record('success')
        data = read_json(record)
        del data['pdf_sha256']
        record.write_text(json.dumps(data), encoding='utf-8')
        tool.review(self.root / 'before', self.root / 'after', self.output, after_build=record, language='zh')
        self.assertEqual(read_json(self.output / 'review.json')['builds']['after']['pdf_binding'], 'unverified-legacy-report')
        self.assertIn('编译时身份仍未验证', (self.output / 'report.html').read_text(encoding='utf-8'))

    def test_reserved_evidence_filename_collision_is_refused(self):
        record = self.record()
        data = read_json(record)
        data['steps'] = [{'log': 'build-report.json'}]
        record.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'path collision'):
            tool.review(self.root / 'before', self.root / 'after', self.output, after_build=record)
        self.assertFalse(self.output.exists())

    def test_equivalent_output_parent_paths_keep_evidence_manifest_relative(self):
        record = self.record('success')
        output = self.root / 'before/../review'
        result = tool.review(self.root / 'before', self.root / 'after', output, after_build=record)
        self.assertEqual(Path(result['output']), self.output.resolve())
        for item in read_json(self.output / 'review.json')['builds']['after']['retained_files']:
            self.assertEqual(sha256(self.output / item['file']), item['sha256'])


if __name__ == '__main__':
    unittest.main()
