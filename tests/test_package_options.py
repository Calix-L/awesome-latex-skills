"""Balanced loaders, exact backend observations and config preflight controls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from project_doctor import commands, inspect_project, parse_config
from doctor import diagnose_project
from package_options import backend_options
from project_report import inspection_html
from review_project import review
from review_report import review_html
from inspection_bundle import export_inspection
from verify_artifacts import verify_inspection, verify_review


class PackageOptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paper = self.root / 'paper'
        self.paper.mkdir()

    def put(self, name, text):
        (self.paper / name).write_text(text, encoding='utf-8')

    def check(self, body, backend=None):
        self.put('main.tex', '\\documentclass{article}\n' + body)
        with patch('project_doctor.shutil.which', return_value='test/tool'):
            return inspect_project(self.paper, 'main.tex', 'pdflatex', backend)

    def reviewed(self, old, new):
        for side, text in (('before', old), ('after', new)):
            folder = self.root / side
            folder.mkdir()
            (folder / 'main.tex').write_text('\\documentclass{article}\n' + text, encoding='utf-8')
        output = self.root / 'review'
        result = review(self.root / 'before', self.root / 'after', output, language='zh')
        return result, json.loads((output / 'review.json').read_text(encoding='utf-8')), output

    def test_direct_loaders_read_balanced_options_names_and_version(self):
        for name in ('documentclass', 'LoadClass', 'usepackage', 'RequirePackage'):
            row = list(commands(rf'\{name}[note={{nested ] text, other=value}}]{{local}}[2020/01/01]'))[0]
            self.assertTrue(row['supported'])
            self.assertEqual((row['value'], row['options']), ('local', '[note={nested ] text, other=value}]'))

    def test_forwarding_loaders_accept_name_and_version_but_no_direct_options(self):
        for name in ('LoadClassWithOptions', 'RequirePackageWithOptions'):
            self.assertTrue(list(commands(rf'\{name}{{local}}[2020/01/01]'))[0]['supported'])
            self.assertIn('package_issue', list(commands(rf'\{name}[note=x]{{local}}'))[0])

    def test_commands_inside_options_names_and_version_are_not_executed_by_scanner(self):
        rows = list(commands(r'\usepackage[note={\input{fake}\cite{fake}\usepackage{fontspec}}]{local}[\ref{fake}]\input{real}'))
        self.assertEqual([(r['name'], r['value']) for r in rows], [('usepackage', 'local'), ('input', 'real')])

    def test_comments_crlf_and_nested_brackets_keep_opening_location(self):
        row = list(commands('\r\n\\usepackage % comment\r\n[note={] escaped \\]}]\r\n{local}'))[0]
        self.assertEqual((row['line'], row['value']), (2, 'local'))
        self.assertTrue(row['supported'])

    def test_masked_and_internal_commands_do_not_supply_loaders(self):
        text = '% \\usepackage{fake}\n' + r'\verb|\documentclass{fake}|\begin{verbatim}\usepackage{fake}\end{verbatim}\\usepackage{fake}\usepackage@internal{fake}\RequirePackage{real}'
        self.assertEqual([r['value'] for r in commands(text)], ['real'])

    def test_unclosed_deep_extra_optional_starred_and_dynamic_names_are_unverified(self):
        for text in (r'\usepackage[note={x]{local}', r'\usepackage[a][b]{local}', r'\usepackage*{local}',
                     r'\usepackage{}', r'\usepackage{a,,b}', r'\documentclass{a,b}', r'\usepackage{\macro}', r'\usepackage{a{b}}',
                     r'\usepackage[' + '{' * 129 + 'x' + '}' * 129 + ']{local}'):
            with self.subTest(text=text):
                row = list(commands(text))[0]
                self.assertFalse(row['supported'])
                self.assertIn('package_issue', row)

    def test_nested_option_root_is_selected_without_fake_roots(self):
        self.put('main.tex', r'\documentclass[note={nested ] \documentclass{fake}}]{article}\begin{document}Text\end{document}')
        with patch('project_doctor.shutil.which', return_value='test/tool'):
            report = inspect_project(self.paper, engine='pdflatex')
        self.assertEqual((report['main'], report['root_candidates'], report['diagnostics']), ('main.tex', ['main.tex'], []))

    def test_local_class_and_package_dependencies_survive_nested_options(self):
        self.put('local.cls', r'\LoadClass[note={]}]{article}\RequirePackage[note={a,b}]{local}')
        self.put('local.sty', r'\input{part}')
        self.put('part.tex', r'\label{known}')
        self.put('main.tex', r'\documentclass[note={]}]{local}\ref{known}')
        with patch('project_doctor.shutil.which', return_value='test/tool'):
            report = inspect_project(self.paper, 'main.tex', 'pdflatex')
        self.assertEqual(report['diagnostics'], [])
        self.assertEqual({r['file'] for r in report['inputs']}, {'main.tex', 'local.cls', 'local.sty', 'part.tex'})
        self.assertEqual([r['name'] for r in report['package_inventory']], ['local', 'article', 'local'])

    def test_braced_backend_value_is_exact_and_mismatch_is_located(self):
        report = self.check('\n\\usepackage[backend={bibtex},sorting=none]{biblatex}', 'biber')
        mismatch = next(r for r in report['diagnostics'] if r['code'] == 'backend-mismatch')
        self.assertEqual((mismatch['file'], mismatch['line']), ('main.tex', 3))
        self.assertEqual(report['package_inventory'][-1]['backend_options'], ['bibtex'])
        self.assertTrue(report['package_inventory'][-1]['backend_options_complete'])

    def test_matching_backend_values_do_not_require_backend_inference(self):
        for backend in ('biber', 'bibtex'):
            report = self.check(r'\usepackage[backend={' + backend + '}]{biblatex}', backend)
            self.assertEqual(report['diagnostics'], [])
        report = self.check(r'\usepackage[backend={biber}]{biblatex}')
        self.assertIsNone(report['backend'])

    def test_prefix_suffix_and_embedded_text_are_not_backend_assignments(self):
        values, issues = backend_options('[mybackend=bibtex,note={backend=bibtex, backend=biber},backend=biber]')
        self.assertEqual((values, issues), (['biber'], []))
        self.assertEqual(backend_options('[backend-extra=bibtex,note={backend=bibtex}]'), ([], []))

    def test_bibtex8_and_similar_values_are_never_prefix_matched(self):
        for value in ('bibtex8', 'biber2', 'bibtex-extra', 'Biber'):
            report = self.check(r'\usepackage[backend=' + value + ']{biblatex}', 'bibtex')
            self.assertEqual([r['code'] for r in report['diagnostics']], ['backend-options-unverified'])
            self.assertEqual(report['package_inventory'][-1]['backend_options'], [value])
            self.assertFalse(report['package_inventory'][-1]['backend_options_complete'])

    def test_dynamic_empty_bare_nested_and_trailing_backend_values_are_unverified(self):
        for options in ('[backend=\\macro]', '[\\options]', '[backend]', '[backend=]', '[backend={{bibtex}}]', '[backend={biber} junk]'):
            with self.subTest(options=options):
                self.assertTrue(backend_options(options)[1])

    def test_conflicting_assignments_do_not_choose_first_or_last_backend(self):
        report = self.check(r'\usepackage[backend=biber,backend=bibtex]{biblatex}', 'biber')
        self.assertEqual(report['package_inventory'][-1]['backend_options'], ['biber', 'bibtex'])
        self.assertEqual([r['code'] for r in report['diagnostics']], ['backend-options-unverified'])

    def test_repeated_identical_assignments_retain_multiplicity(self):
        report = self.check(r'\usepackage[backend=bibtex,backend={bibtex}]{biblatex}', 'biber')
        self.assertEqual(report['package_inventory'][-1]['backend_options'], ['bibtex', 'bibtex'])
        self.assertEqual([r['code'] for r in report['diagnostics']], ['backend-mismatch'])

    def test_defaults_and_forwarded_options_do_not_select_or_invent_backend(self):
        report = self.check(r'\PassOptionsToPackage{backend=bibtex}{biblatex}\usepackage{biblatex}')
        self.assertIsNone(report['backend'])
        self.assertEqual(report['package_inventory'][-1]['backend_options'], [])
        self.assertEqual(report['diagnostics'], [])

    def test_excluded_sources_do_not_supply_package_declarations(self):
        self.put('unused.tex', r'\usepackage[backend=bibtex]{biblatex}')
        report = self.check(r'\includeonly{}\include{unused}', 'biber')
        self.assertEqual([r['name'] for r in report['package_inventory']], ['article'])
        self.assertEqual(report['diagnostics'], [])

    def test_doctor_retains_actual_mismatch_and_source_bytes(self):
        self.check(r'\usepackage[backend={bibtex}]{biblatex}', 'biber')
        expected = (self.paper / 'main.tex').read_bytes()
        with patch('shutil.which', return_value='test/tool'):
            report = diagnose_project(self.paper, ['latex-rescue'], engine='pdflatex', backend='biber')
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['backend'], 'biber')
        self.assertEqual((self.paper / 'main.tex').read_bytes(), expected)

    def test_schema_bool_float_and_string_are_rejected_before_main_read_or_probe(self):
        for schema in (True, False, 1.0, '1', None):
            config = json.dumps({'schema': schema, 'main': 'main.tex', 'engine': 'pdflatex'}).encode()
            with patch('project_doctor.validate_main') as main_read, patch('project_doctor.shutil.which') as probe:
                with self.assertRaisesRegex(ValueError, 'schema-1'):
                    parse_config(self.paper, config)
                main_read.assert_not_called()
                probe.assert_not_called()

    def test_valid_integer_schema_and_optional_settings_remain_compatible(self):
        self.put('main.tex', r'\documentclass{article}')
        config = {'schema': 1, 'main': 'main.tex', 'engine': 'pdflatex'}
        self.assertEqual(parse_config(self.paper, json.dumps(config).encode()), config)

    def test_unchanged_malformed_or_conflicting_options_remain_visible_in_review(self):
        result, report, _ = self.reviewed(r'\usepackage[backend=biber,backend=bibtex]{biblatex}', r'\usepackage[backend=biber,backend=bibtex]{biblatex}')
        self.assertEqual(result['source_scan_issues'], 2)
        self.assertEqual({r['side'] for r in report['source_scan_issues']}, {'before', 'after'})
        self.assertTrue(all(r['code'] == 'backend-options-unverified' for r in report['source_scan_issues']))

    def test_review_keeps_both_literal_option_versions_and_sealed_evidence(self):
        result, report, output = self.reviewed(r'\usepackage[backend={bibtex}]{biblatex}', r'\usepackage[backend={biber}]{biblatex}')
        self.assertEqual(result['source_scan_issues'], 0)
        self.assertEqual(report['package_inventory']['before'][-1]['backend_options'], ['bibtex'])
        self.assertEqual(report['package_inventory']['after'][-1]['backend_options'], ['biber'])
        self.assertIn('文档类与宏包声明', (output / 'report.html').read_text(encoding='utf-8'))
        self.assertEqual(verify_review(output)['status'], 'verified')

    def test_bilingual_html_escapes_options_and_legacy_reports_render(self):
        report = self.check(r'\usepackage[note={<tag>}]{local}')
        for language, title in (('en', 'Class and package declarations'), ('zh', '文档类与宏包声明')):
            page = inspection_html(report, language)
            self.assertIn(title, page)
            self.assertIn('&lt;tag&gt;', page)
            self.assertNotIn('<tag>', page)
        del report['package_inventory']
        self.assertNotIn('Class and package declarations', inspection_html(report))
        _, legacy, _ = self.reviewed(r'\usepackage[note={<tag>}]{local}', r'\usepackage[note={<other>}]{local}')
        self.assertIn('&lt;other&gt;', review_html(legacy, {}))
        del legacy['package_inventory']
        self.assertNotIn('Class and package declarations', review_html(legacy, {}))

    def test_sealed_package_inventory_detects_changed_option_bytes(self):
        self.check(r'\usepackage[backend={biber}]{biblatex}', 'biber')
        output = self.root / 'inspection'
        with patch('project_doctor.shutil.which', return_value='test/tool'):
            export_inspection(self.paper, output, 'main.tex', 'pdflatex', 'biber', 'zh')
        self.assertEqual(verify_inspection(output)['status'], 'verified')
        path = output / 'inspection.json'
        report = json.loads(path.read_text(encoding='utf-8'))
        report['package_inventory'][-1]['options'] = '[backend=bibtex]'
        path.write_text(json.dumps(report), encoding='utf-8')
        self.assertEqual(verify_inspection(output)['status'], 'failed')
