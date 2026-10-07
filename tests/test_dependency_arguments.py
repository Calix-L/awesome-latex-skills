"""Complete dependency arguments, scoped command observations and portable reports."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from project_doctor import commands, inspect_project
from project_support import read_json
from inspection_bundle import export_inspection
from verify_artifacts import verify_inspection, verify_review
from review_project import review
from review_report import review_html
from project_report import inspection_html


class DependencyArguments(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / 'paper'
        self.project.mkdir()

    def put(self, name, text):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def inspect(self, body):
        self.put('main.tex', '\\documentclass{article}\n' + body)
        with patch('project_doctor.shutil.which', return_value='synthetic/tool'):
            return inspect_project(self.project, 'main.tex', 'pdflatex')

    def test_graphics_options_protect_closing_brackets_with_braces(self):
        rows = list(commands(r'\includegraphics*[note={nested ] text, other={value}},width=1cm]{plot}\ref{real}'))
        self.assertEqual([row['name'] for row in rows], ['includegraphics', 'ref'])
        self.assertTrue(rows[0]['supported'])
        self.assertTrue(rows[0]['starred'])
        self.assertEqual(rows[0]['value'], 'plot')
        self.assertEqual(rows[0]['options'], '[note={nested ] text, other={value}},width=1cm]')

    def test_option_commands_are_not_scanned_as_body_dependencies_or_keys(self):
        rows = list(commands(r'\includegraphics[note={\input{absent}\cite{fake}\label{fake}}]{plot}\cite{real}'))
        self.assertEqual([row['name'] for row in rows], ['includegraphics', 'cite'])
        self.assertEqual(rows[-1]['value'], 'real')

    def test_dynamic_filename_commands_do_not_create_phantom_keys(self):
        rows = list(commands(r'\input{\folder\cite{fake}\ref{fake}}\label{real}'))
        self.assertEqual([row['name'] for row in rows], ['input', 'label'])
        self.assertFalse(rows[0]['supported'])
        self.assertIn('Dynamic', rows[0]['dependency_issue'])

    def test_nested_filename_is_unverified_and_following_body_is_visible(self):
        rows = list(commands(r'\includegraphics{{plot}.pdf}\ref{real}'))
        self.assertFalse(rows[0]['supported'])
        self.assertIn('Nested', rows[0]['dependency_issue'])
        self.assertEqual(rows[1]['value'], 'real')

    def test_quoted_and_bare_input_keep_next_body_command(self):
        rows = list(commands('\\input "with spaces.tex"\n\\input part.tex\n\\cite{real}'))
        self.assertEqual([row['value'] for row in rows], ['"with spaces.tex"', 'part.tex', 'real'])
        self.assertEqual([row['line'] for row in rows], [1, 2, 3])
        self.assertTrue(all(row['supported'] for row in rows))

    def test_unclosed_input_quote_has_a_located_issue(self):
        rows = list(commands('\\input "missing\n\\ref{real}'))
        self.assertFalse(rows[0]['supported'])
        self.assertIn('Unclosed quoted', rows[0]['dependency_issue'])
        self.assertEqual(rows[1]['value'], 'real')

    def test_classic_two_optional_graphics_arguments_are_retained(self):
        rows = list(commands(r'\includegraphics*[0,0][72,72]{plot.pdf}\input{part}'))
        self.assertTrue(rows[0]['supported'])
        self.assertEqual(rows[0]['options'], '[0,0][72,72]')
        self.assertEqual(rows[0]['value'], 'plot.pdf')
        self.assertEqual(rows[1]['value'], 'part')

    def test_addbibresource_options_are_complete_and_scoped(self):
        rows = list(commands(r'\addbibresource[location={local},note={]\cite{fake}}]{refs.bib}\cite{real}'))
        self.assertEqual([row['name'] for row in rows], ['addbibresource', 'cite'])
        self.assertTrue(rows[0]['supported'])
        self.assertEqual(rows[0]['value'], 'refs.bib')

    def test_unexpected_options_and_stars_are_not_guessed_as_filenames(self):
        for text in (r'\input[note={\cite{fake}}]{part}\cite{real}',
                     r'\bibliography*[x]{refs}\cite{real}',
                     r'\includegraphics[a][b][c]{plot}\cite{real}',
                     r'\includegraphics[a][b][c][note={\cite{fake}}]{plot}\cite{real}',
                     r'\addbibresource[a][b]{refs.bib}\cite{real}'):
            with self.subTest(text=text):
                rows = list(commands(text))
                self.assertFalse(rows[0]['supported'])
                self.assertEqual([row['value'] for row in rows if row['name'] == 'cite'], ['real'])

    def test_empty_includeonly_and_graphics_path_are_valid_literal_declarations(self):
        rows = list(commands(r'\includeonly{}\graphicspath{}\input{}\bibliography{one,,two}'))
        self.assertEqual([row['supported'] for row in rows], [True, True, False, False])

    def test_graphics_paths_require_complete_braced_directory_lists(self):
        rows = list(commands(r'\graphicspath{{figures/}{../shared/}}\graphicspath{{figures/}junk}\ref{real}'))
        self.assertTrue(rows[0]['supported'])
        self.assertFalse(rows[1]['supported'])
        self.assertEqual(rows[-1]['value'], 'real')

    def test_malformed_group_is_visible_and_does_not_invent_later_keys(self):
        for text in (r'\includegraphics[note={unterminated]\cite{fake}',
                     r'\input{unfinished\ref{fake}',
                     r'\includegraphics[note=oops}]{plot}\cite{fake}'):
            with self.subTest(text=text):
                rows = list(commands(text))
                self.assertEqual(len(rows), 1)
                self.assertFalse(rows[0]['supported'])
                self.assertIn('argument', rows[0]['dependency_issue'])

    def test_argument_depth_limit_is_iterative_and_located(self):
        rows = list(commands('\\includegraphics[note=' + '{' * 129 + 'x' + '}' * 129 + ']{plot}\\cite{fake}'))
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]['supported'])
        self.assertIn('128', rows[0]['dependency_issue'])
        rows = list(commands('\\includegraphics' + '[note={\\cite{fake}}]' * 33 + '{plot}\\cite{later}'))
        self.assertEqual(len(rows), 1)
        self.assertIn('32', rows[0]['dependency_issue'])

    def test_inspection_resolves_real_graphic_and_records_complete_option_bytes(self):
        self.put('figures/plot.pdf', '%PDF-synthetic asset')
        report = self.inspect(r'\graphicspath{{figures/}}\DeclareGraphicsExtensions{.pdf}'
                              r'\includegraphics[note={] \cite{phantom}\input{absent}},width=1cm]{plot}')
        self.assertEqual(report['diagnostics'], [])
        self.assertEqual(report['dependencies'][0]['file'], 'figures/plot.pdf')
        self.assertEqual(report['citation_inventory'], [])
        row = report['dependency_inventory'][-1]
        self.assertEqual((row['file'], row['line']), ('main.tex', 2))
        self.assertIn('\\cite{phantom}', row['options'])
        self.assertTrue(row['supported'])

    def test_unsupported_graphics_declaration_invalidates_later_search(self):
        report = self.inspect(r'\graphicspath{{figures/}junk}\includegraphics{plot}')
        self.assertEqual({row['code'] for row in report['diagnostics']}, {'dynamic-reference', 'graphics-search-unverified'})
        self.assertEqual(report['dependencies'], [])
        self.assertFalse(report['dependency_inventory'][0]['supported'])

    def test_empty_includeonly_excludes_missing_include_without_reading_it(self):
        report = self.inspect(r'\includeonly{}\include{absent}')
        self.assertEqual(report['diagnostics'], [])
        self.assertTrue(report['dependencies'][0]['skipped'])
        self.assertEqual(len(report['dependency_inventory']), 2)

    def test_bilingual_inspection_tables_are_escaped_and_remain_portable(self):
        self.put('plot.pdf', '%PDF-synthetic asset')
        self.inspect(r'\includegraphics[note={] <script>\cite{fake}}]{plot}\input{\macro}')
        for language in ('en', 'zh'):
            bundle = self.root / ('inspection-' + language)
            with patch('project_doctor.shutil.which', return_value='synthetic/tool'):
                report = export_inspection(self.project, bundle, 'main.tex', 'pdflatex', language=language)
            page = (bundle / 'report.html').read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;', page)
            self.assertNotIn('<script>', page)
            self.assertEqual(len(report['dependency_inventory']), 2)
            self.assertTrue(any(row['code'] == 'dynamic-reference' for row in report['diagnostics']))
            moved = self.root / ('moved-' + language)
            bundle.rename(moved)
            self.assertEqual(verify_inspection(moved)['status'], 'verified')

    def test_review_records_both_versions_without_phantom_citation_changes(self):
        before, after = self.root / 'before', self.root / 'after'
        before.mkdir()
        after.mkdir()
        (before / 'main.tex').write_text(r'\includegraphics[note={] \cite{old-fake}}]{plot}\input{\folder\ref{old-fake}}', encoding='utf-8')
        (after / 'main.tex').write_text(r'\includegraphics[note={] \cite{new-fake}}]{plot}\input{\folder\ref{new-fake}}', encoding='utf-8')
        for language in ('en', 'zh'):
            output = self.root / ('review-' + language)
            review(before, after, output, language=language)
            report = read_json(output / 'review.json')
            self.assertEqual(report['citation_inventory'], {'before': [], 'after': []})
            self.assertEqual(report['reference_inventory'], {'before': [], 'after': []})
            self.assertEqual(report['content_audit'], [])
            self.assertEqual([row['code'] for row in report['source_scan_issues']], ['dependency-unverified'] * 2)
            self.assertEqual(len(report['dependency_inventory']['before']), 2)
            self.assertEqual(len(report['dependency_inventory']['after']), 2)
            self.assertIn('old-fake', (output / 'report.html').read_text(encoding='utf-8'))
            self.assertEqual(verify_review(output)['status'], 'verified')

    def test_legacy_reports_without_dependency_inventory_still_render(self):
        inspected = self.inspect('Plain body')
        inspected.pop('dependency_inventory')
        self.assertIn('<!doctype html>', inspection_html(inspected))
        before = self.root / 'original'
        before.mkdir()
        (before / 'main.tex').write_text('Plain body', encoding='utf-8')
        output = self.root / 'review'
        review(before, self.project, output)
        report = read_json(output / 'review.json')
        report.pop('dependency_inventory')
        self.assertIn('<!doctype html>', review_html(report, {}))


if __name__ == '__main__':
    unittest.main()
