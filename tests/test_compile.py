"""Compile in isolated directories; never treat a produced log/PDF as success."""
import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_build import check_build, REPO

sys.path.insert(0, str(REPO / "scripts"))
from project_doctor import inspect_project

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PDFLATEX = shutil.which("pdflatex")


class CompilationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PDFLATEX:
            if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                raise RuntimeError("pdflatex is required for this run but was not found")
            raise unittest.SkipTest("pdflatex unavailable; real compilation runs in CI")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="latex-skills-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        (self.work / "asset.tex").write_text(
            r"\documentclass{article}\pagestyle{empty}\begin{document}Fixture figure\end{document}",
            encoding="utf-8",
        )
        result = self.compile("asset.tex")
        self.assertEqual(result.returncode, 0, result.stdout[-4000:])
        for name in ("example.pdf", "plot.pdf"):
            shutil.copyfile(self.work / "asset.pdf", self.work / name)

    def compile(self, filename):
        return subprocess.run(
            [PDFLATEX, "-no-shell-escape", "-interaction=nonstopmode", "-file-line-error", filename],
            cwd=self.work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=60,
        )

    def copy_fixture(self, name):
        shutil.copyfile(FIXTURES / "errors" / name, self.work / name)

    def assert_build_success(self, report):
        if report["status"] == "success":
            return
        evidence = [json.dumps(report, indent=2)]
        for step in report["steps"]:
            transcript = Path(report["output"]) / step["transcript"]
            if transcript.is_file():
                evidence.append(f"{step['transcript']}:\n" + transcript.read_text(encoding="utf-8", errors="replace")[-4000:])
        self.fail("\n\n".join(evidence))

    def test_native_internal_parent_paths_match_main_directory_and_recorder(self):
        project = self.work / 'nested-path-project'
        for directory in ('paper', 'styles', 'shared', 'figures'):
            (project / directory).mkdir(parents=True, exist_ok=True)
        source = project / 'paper/main.tex'
        source.write_text(r'\documentclass{../styles/top}\graphicspath{{../figures/}}'
                          r'\begin{document}\input{../shared/part}\ref{shared}.'
                          r'\includegraphics[width=1cm]{plot}\end{document}', encoding='utf-8')
        (project / 'styles/top.cls').write_text(r'\ProvidesClass{../styles/top}\LoadClass{article}'
                                              r'\RequirePackage{graphicx}\RequirePackage{../styles/settings}', encoding='utf-8')
        (project / 'styles/settings.sty').write_text(r'\ProvidesPackage{../styles/settings}\newcommand{\siblingword}{Shared}', encoding='utf-8')
        (project / 'shared/part.tex').write_text(r'\section{Shared}\label{shared}\siblingword{} \input{./local}', encoding='utf-8')
        (project / 'paper/local.tex').write_text('Local source-directory input.', encoding='utf-8')
        shutil.copyfile(self.work / 'plot.pdf', project / 'figures/plot.pdf')
        original = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob('*') if p.is_file()}
        inspection = inspect_project(project, 'paper/main.tex', 'pdflatex')
        self.assertEqual(inspection['diagnostics'], [])
        self.assertEqual(next(r['file'] for r in inspection['dependencies'] if r['requested'] == './local'), 'paper/local.tex')
        output = self.work / 'nested-path-build'
        built = check_build.build(source, output, passes=5, until_stable=True, require_resolved=True)
        self.assert_build_success(built)
        recorded = set()
        for step in built['steps']:
            if not step.get('recorder'):
                continue
            for line in (output / step['recorder']).read_text(encoding='utf-8', errors='replace').splitlines():
                if line.startswith('INPUT '):
                    path = Path(line[6:].strip().strip('"'))
                    path = (path if path.is_absolute() else source.parent / path).resolve()
                    if path.is_relative_to(project):
                        recorded.add(path.relative_to(project).as_posix())
        self.assertTrue({r['file'] for r in inspection['inputs']}.issubset(recorded), (inspection, recorded))
        for name, data in original.items():
            self.assertEqual((project / name).read_bytes(), data)

    def test_native_parent_bibliography_and_local_style_with_both_backends(self):
        for backend in ('bibtex', 'biber'):
            project = self.work / f'parent-bibliography-{backend}'
            for directory in ('paper', 'shared', 'styles'):
                (project / directory).mkdir(parents=True, exist_ok=True)
            source = project / 'paper/main.tex'
            if backend == 'bibtex':
                style = subprocess.check_output(['kpsewhich', 'plain.bst'], text=True, timeout=10).strip()
                shutil.copyfile(style, project / 'styles/local.bst')
                preamble = r'\documentclass{article}'
                bibliography = r'\bibliographystyle{../styles/local}\bibliography{../shared/refs}'
            else:
                preamble = r'\documentclass{article}\usepackage[backend=biber]{biblatex}\addbibresource{../shared/refs.bib}'
                bibliography = r'\printbibliography'
            (project / 'paper/chapters').mkdir()
            (project / 'paper/chapters/one.tex').write_text(r'\section{One}\cite{a}.', encoding='utf-8')
            source.write_text(preamble + r'\begin{document}\include{chapters/one}\cite{a}.' + bibliography + r'\end{document}', encoding='utf-8')
            (project / 'shared/refs.bib').write_text('@book{a, author={Ada Example}, title={Synthetic Parent Path}, publisher={Example}, year={2024}}', encoding='utf-8')
            original = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob('*') if p.is_file()}
            inspection = inspect_project(project, 'paper/main.tex', 'pdflatex', backend)
            self.assertEqual(inspection['diagnostics'], [])
            self.assertEqual(inspection['bibliography_entries'][0]['file'], 'shared/refs.bib')
            output = self.work / f'parent-{backend}-build'
            built = check_build.build(source, output, backend=backend, passes=5, until_stable=True, require_resolved=True)
            self.assert_build_success(built)
            control = (output / ('main.aux' if backend == 'bibtex' else 'main.bcf')).read_text(encoding='utf-8')
            self.assertIn('../shared/refs', control)
            if backend == 'bibtex':
                self.assertIn('../styles/local', control)
                prepared = next(row for row in built['steps'] if row['name'] == 'bibliography')['prepared_inputs']
                self.assertEqual({row['kind'] for row in prepared}, {'bibliography', 'style', 'auxiliary'})
                from review_project import review
                from verify_artifacts import verify_review
                before = self.work / 'parent-bibliography-original'
                shutil.copytree(project, before)
                review_output = self.work / 'parent-bibliography-review'
                review(before, project, review_output, after_build=output / 'build-report.json', language='zh')
                self.assertEqual(verify_review(review_output)['status'], 'verified')
                retained = json.loads((review_output / 'review.json').read_text())['builds']['after']['retained_files']
                self.assertTrue({row['file'] for row in prepared}.issubset({row['file'].removeprefix('evidence/after/') for row in retained}))
            for name, data in original.items():
                self.assertEqual((project / name).read_bytes(), data)

    def test_real_nested_class_and_package_loader_options(self):
        source = self.work / 'main.tex'
        source.write_text(r'\documentclass[note={nested ] text, more=value}]{alsoptionclass}'
                          r'\begin{document}Synthetic option control.\end{document}', encoding='utf-8')
        cls = self.work / 'alsoptionclass.cls'
        cls.write_text(r'\ProvidesClass{alsoptionclass}\DeclareOption*{}\ProcessOptions\relax'
                       r'\LoadClass{article}\RequirePackage[note={nested ] text, more=value}]{alsoptionpackage}', encoding='utf-8')
        sty = self.work / 'alsoptionpackage.sty'
        sty.write_text(r'\ProvidesPackage{alsoptionpackage}\DeclareOption*{}\ProcessOptions\relax', encoding='utf-8')
        expected = {p.name: p.read_bytes() for p in (source, cls, sty)}
        inspected = inspect_project(self.work, engine='pdflatex')
        # setUp's separate figure source is also a root; select this main explicitly.
        self.assertIsNone(inspected['main'])
        inspected = inspect_project(self.work, 'main.tex', 'pdflatex')
        self.assertEqual(inspected['diagnostics'], [])
        self.assertEqual([r['name'] for r in inspected['package_inventory']], ['alsoptionclass', 'article', 'alsoptionpackage'])
        built = check_build.build(source, self.work / 'loader-build', passes=5, until_stable=True, require_resolved=True,
                                  watch_inputs=['alsoptionclass.cls', 'alsoptionpackage.sty'])
        self.assert_build_success(built)
        self.assertTrue({'alsoptionclass.cls', 'alsoptionpackage.sty'}.issubset({r['path'] for r in built['local_inputs']}))
        for path in (source, cls, sty):
            self.assertEqual(path.read_bytes(), expected[path.name])

    def test_real_braced_biblatex_backend_options_and_configured_mismatch(self):
        for backend in ('biber', 'bibtex'):
            folder = self.work / backend
            folder.mkdir()
            source = folder / 'main.tex'
            source.write_text(r'\documentclass{article}\usepackage[backend={' + backend + r'},style=numeric]{biblatex}'
                              r'\addbibresource{refs.bib}\begin{document}\cite{a}.\printbibliography\end{document}', encoding='utf-8')
            refs = folder / 'refs.bib'
            refs.write_text('@book{a,author={Alice Author},title={Synthetic control},year={2020}}', encoding='utf-8')
            expected = {p.name: p.read_bytes() for p in (source, refs)}
            inspected = inspect_project(folder, 'main.tex', 'pdflatex', backend)
            self.assertEqual(inspected['diagnostics'], [])
            row = next(r for r in inspected['package_inventory'] if r['name'] == 'biblatex')
            self.assertEqual(row['backend_options'], [backend])
            self.assertTrue(row['backend_options_complete'])
            other = 'bibtex' if backend == 'biber' else 'biber'
            mismatch = inspect_project(folder, 'main.tex', 'pdflatex', other)
            self.assertEqual([r['code'] for r in mismatch['diagnostics']], ['backend-mismatch'])
            built = check_build.build(source, self.work / f'loader-{backend}', backend=backend, passes=5,
                                      until_stable=True, require_resolved=True, watch_inputs=['refs.bib'])
            self.assert_build_success(built)
            self.assertTrue(any(step['tool'] == backend and step['exit_code'] == 0 for step in built['steps']))
            self.assertEqual((Path(built['output']) / 'main.bcf').exists(), backend == 'biber')
            for path in (source, refs):
                self.assertEqual(path.read_bytes(), expected[path.name])

    def test_real_manual_bibliography_and_definition_only_edit(self):
        from review_project import review
        from verify_artifacts import verify_review
        main_text = (r"\documentclass{article}\begin{document}\cite{a,b}. "
                     r"\begin{thebibliography}{9}\input{references}\end{thebibliography}\end{document}")
        for side, key in (("before", "b"), ("after", "changed")):
            folder = self.work / side
            folder.mkdir()
            source = folder / "main.tex"
            source.write_text(main_text, encoding="utf-8")
            references = folder / "references.tex"
            references.write_text("\\bibitem{a} Synthetic first entry.\n\\bibitem[Author]{" + key + "} Synthetic second entry.", encoding="utf-8")
            expected = {p.name: p.read_bytes() for p in (source, references)}
            inspected = inspect_project(folder, "main.tex", "pdflatex")
            self.assertIsNone(inspected["backend"])
            self.assertEqual([r["key"] for r in inspected["bibitem_inventory"]], ["a", key])
            unknown = [r for r in inspected["diagnostics"] if r["code"] == "unknown-citation"]
            self.assertEqual([r["message"].rsplit(" ", 1)[-1] for r in unknown], [] if side == "before" else ["b"])
            built = check_build.build(source, self.work / f"manual-{side}", passes=5,
                                      until_stable=True, require_resolved=True, watch_inputs=["references.tex"])
            if side == "before":
                self.assert_build_success(built)
            else:
                self.assertEqual(built["status"], "failed")
                self.assertTrue(built["unresolved_references"])
            aux = (Path(built["output"]) / "main.aux").read_text(encoding="utf-8")
            self.assertEqual(set(re.findall(r"\\bibcite\{([^}]+)\}", aux)), {r["key"] for r in inspected["bibitem_inventory"]})
            for path in (source, references):
                self.assertEqual(path.read_bytes(), expected[path.name])
        output = self.work / "manual-review"
        result = review(self.work / "before", self.work / "after", output, language="zh")
        self.assertEqual((result["content_flags"], result["source_scan_issues"]), (1, 0))
        record = json.loads((output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(set(record["content_audit"][0]), {"file", "requires_review", "reference_keys"})
        self.assertEqual(record["content_audit"][0]["file"], "references.tex")
        self.assertEqual(verify_review(output)["status"], "verified")

    def test_real_natbib_manual_labels_and_located_duplicate(self):
        source = self.work / "main.tex"
        source.write_text("\\documentclass{article}\\usepackage{natbib}\\begin{document}\n"
                          "\\citet{a}. \\citep{b}. \\begin{thebibliography}{9}\n"
                          "\\bibitem[Alice(2020)]{a} Synthetic first entry.\n"
                          "\\bibitem[Bob(2021)Bob and Carol]{b} Synthetic second entry.\n"
                          "\\input{extra}\\end{thebibliography}\\end{document}", encoding="utf-8")
        extra = self.work / "extra.tex"
        extra.write_text("", encoding="utf-8")
        expected = source.read_bytes()
        inspection = inspect_project(self.work, "main.tex", "pdflatex")
        self.assertEqual(inspection["diagnostics"], [])
        built = check_build.build(source, self.work / "manual-natbib", passes=5, until_stable=True, require_resolved=True)
        self.assert_build_success(built)
        aux = (Path(built["output"]) / "main.aux").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"\\bibcite\{([^}]+)\}", aux)), {r["key"] for r in inspection["bibitem_inventory"]})
        extra.write_text("\n\\bibitem[Alice(2020)]{a} Synthetic repeated entry.", encoding="utf-8")
        duplicate_bytes = extra.read_bytes()
        inspection = inspect_project(self.work, "main.tex", "pdflatex")
        duplicate = next(r for r in inspection["diagnostics"] if r["code"] == "duplicate-bibitem-key")
        self.assertEqual((duplicate["file"], duplicate["line"]), ("extra.tex", 2))
        self.assertIn("main.tex:3", duplicate["message"])
        built = check_build.build(source, self.work / "manual-natbib-duplicate", passes=5, until_stable=True)
        self.assertEqual(built["status"], "failed")
        self.assertTrue(built["rerun_requested"])
        self.assertIn("did not settle", built["failure"])
        log = (Path(built["output"]) / "main.log").read_text(encoding="utf-8", errors="replace")
        self.assertIn("multiply defined", log)
        self.assertEqual(source.read_bytes(), expected)
        self.assertEqual(extra.read_bytes(), duplicate_bytes)

    def test_real_biblatex_multicites_and_second_group_missing_key(self):
        from review_project import review
        from verify_artifacts import verify_review
        import xml.etree.ElementTree as ET
        refs = "@book{a,author={Alice Author},title={First},year={2020}}\n@book{b,author={Bob Author},title={Second},year={2021}}\n"
        prefix = (r"\documentclass{article}\usepackage[backend=biber,style=authoryear]{biblatex}"
                  r"\addbibresource{refs.bib}\begin{document}")
        body = (r"\parencite[see {nested ] note}][p. 7]{a} \textcite{b}. "
                r"\parencites(see {nested ) note})(together)[p. 2]{a}[p. 3]{b}. "
                r"\autocites{a}{b}. \Textcite{a}. \footcite{b}. ")
        source = prefix + body + r"\printbibliography\end{document}"
        for side, text in (("before", source), ("after", source.replace("[p. 3]{b}", "[p. 3]{missing}"))):
            folder = self.work / side
            folder.mkdir()
            main = folder / "main.tex"
            main.write_text(text, encoding="utf-8")
            (folder / "refs.bib").write_text(refs, encoding="utf-8")
            original = main.read_bytes()
            inspection = inspect_project(folder, "main.tex", "pdflatex", "biber")
            unknown = [r for r in inspection["diagnostics"] if r["code"] == "unknown-citation"]
            self.assertEqual(len(unknown), 0 if side == "before" else 1)
            self.assertFalse(any(r["code"] == "citation-unverified" for r in inspection["diagnostics"]))
            built = check_build.build(main, self.work / f"citation-{side}", backend="biber", passes=5,
                                      until_stable=True, require_resolved=True, watch_inputs=["refs.bib"])
            if side == "before":
                self.assert_build_success(built)
            else:
                self.assertEqual(built["status"], "failed")
                self.assertTrue(built["unresolved_references"])
            control = ET.parse(Path(built["output"]) / "main.bcf")
            actual = {node.text for node in control.iter() if node.tag.endswith("}citekey")}
            self.assertEqual(actual, {r["key"] for r in inspection["citation_inventory"]})
            self.assertEqual(main.read_bytes(), original)
        output = self.work / "citation-review"
        result = review(self.work / "before", self.work / "after", output, language="zh")
        self.assertEqual(result["content_flags"], 1)
        self.assertEqual(result["source_scan_issues"], 0)
        evidence = json.loads((output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(set(evidence["content_audit"][0]), {"file", "requires_review", "reference_keys"})
        self.assertEqual(verify_review(output)["status"], "verified")

    def test_real_natbib_capital_commands_and_prose_wrapper(self):
        source = self.work / "main.tex"
        source.write_text(r"\documentclass{article}\usepackage{natbib}\begin{document}"
                          r"\Citet{a}. \Citep*[see {nested ] note}][p. 7]{b}. "
                          r"\citetext{private communication; \citealp{a}}. "
                          r"\Citeauthor{b}. \bibliographystyle{plainnat}\bibliography{refs}\end{document}", encoding="utf-8")
        (self.work / "refs.bib").write_text("@book{a,author={Alice Author},title={First},year={2020}}\n@book{b,author={Bob Author},title={Second},year={2021}}", encoding="utf-8")
        expected = source.read_bytes()
        inspection = inspect_project(self.work, "main.tex", "pdflatex", "bibtex")
        self.assertEqual(inspection["diagnostics"], [])
        self.assertEqual([r["key"] for r in inspection["citation_inventory"]], ["a", "b", "a", "b"])
        built = check_build.build(source, self.work / "natbib-build", backend="bibtex", passes=5,
                                  until_stable=True, require_resolved=True, watch_inputs=["refs.bib"])
        self.assert_build_success(built)
        aux = (Path(built["output"]) / "main.aux").read_text(encoding="utf-8")
        actual = {key for value in re.findall(r"\\citation\{([^}]+)\}", aux) for key in value.split(",")}
        self.assertEqual(actual, {r["key"] for r in inspection["citation_inventory"]})
        self.assertEqual(source.read_bytes(), expected)

    def test_real_hyperref_cleveref_targets_and_missing_range_endpoint(self):
        from review_project import review
        from verify_artifacts import verify_review
        prefix = (r"\documentclass{article}\usepackage{amsmath}\usepackage{hyperref}\usepackage{cleveref}"
                  r"\begin{document}\section{One}\label{a}\input{two}")
        body = (r"\ref{a}, \eqref{a}, \pageref{a}, \autoref{a}, \autopageref{a}, \nameref*{a}. "
                r"\hyperref[a]{Section \ref*{a}}. \cref{a,b}, \Cref*{a,b}, \cpageref{a,b}, \Cpageref{a,b}. "
                r"\labelcref{a,b}, \labelcpageref{a,b}. \namecref{a}, \nameCref{a}, \lcnamecref{a}, "
                r"\namecrefs{a}, \nameCrefs{a}, \lcnamecrefs{a}. "
                r"\crefrange{a}{b}, \Crefrange{a}{b}, \cpagerefrange{a}{b}, \Cpagerefrange{a}{b}.")
        for side, text in (("before", body), ("after", body.replace(r"\crefrange{a}{b}", r"\crefrange{a}{missing}"))):
            folder = self.work / side
            folder.mkdir()
            main = folder / "main.tex"
            main.write_text(prefix + text + r"\end{document}", encoding="utf-8")
            (folder / "two.tex").write_text(r"\section{Two}\label[section]{b}Body.", encoding="utf-8")
            original = main.read_bytes()
            inspection = inspect_project(folder, "main.tex", "pdflatex")
            self.assertEqual(sum(r["code"] == "unknown-label" for r in inspection["diagnostics"]), 0 if side == "before" else 1)
            self.assertFalse(any(r["code"] == "reference-unverified" for r in inspection["diagnostics"]))
            built = check_build.build(main, self.work / f"reference-{side}", passes=5, until_stable=True, require_resolved=True)
            if side == "before":
                self.assert_build_success(built)
                self.assertTrue(all(r["resolution"] == "defined" for r in inspection["reference_inventory"]))
            else:
                self.assertEqual(built["status"], "failed")
                self.assertTrue(built["unresolved_references"])
            aux = (Path(built["output"]) / "main.aux").read_text(encoding="utf-8")
            actual = {key for key in re.findall(r"\\newlabel\{([^{}]+)\}", aux) if not key.endswith("@cref")}
            self.assertEqual(actual, {r["key"] for r in inspection["label_inventory"]})
            self.assertEqual(main.read_bytes(), original)
        output = self.work / "reference-review"
        result = review(self.work / "before", self.work / "after", output, language="zh")
        self.assertEqual(result["content_flags"], 1)
        self.assertEqual(result["source_scan_issues"], 0)
        evidence = json.loads((output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(set(evidence["content_audit"][0]), {"file", "requires_review", "reference_keys"})
        self.assertEqual(verify_review(output)["status"], "verified")

    def test_real_comma_labels_and_located_duplicate_definitions(self):
        source = self.work / "main.tex"
        prefix = r"\documentclass{article}\usepackage{hyperref}\begin{document}\section{One}\label{a,b}"
        source.write_text(prefix + r"\ref{a,b}, \nameref{a,b}, \hyperref[a,b]{See section}.\end{document}", encoding="utf-8")
        original = source.read_bytes()
        inspection = inspect_project(self.work, "main.tex", "pdflatex")
        self.assertEqual(inspection["diagnostics"], [])
        self.assertEqual({r["key"] for r in inspection["reference_inventory"]}, {"a,b"})
        built = check_build.build(source, self.work / "comma-build", passes=5, until_stable=True, require_resolved=True)
        self.assert_build_success(built)
        self.assertEqual(source.read_bytes(), original)
        (self.work / "two.tex").write_text("\\section{Two}\n\\label{a,b}\n", encoding="utf-8")
        source.write_text(prefix + r"\input{two}\ref{a,b}\end{document}", encoding="utf-8")
        original = source.read_bytes()
        inspection = inspect_project(self.work, "main.tex", "pdflatex")
        duplicate = next(r for r in inspection["diagnostics"] if r["code"] == "duplicate-label")
        self.assertEqual((duplicate["file"], duplicate["line"]), ("two.tex", 2))
        self.assertIn("main.tex:1", duplicate["message"])
        self.assertEqual(inspection["reference_inventory"][0]["resolution"], "ambiguous")
        built = check_build.build(source, self.work / "duplicate-build", passes=5, until_stable=True)
        self.assert_build_success(built)
        log = (Path(built["output"]) / "main.log").read_text(encoding="utf-8", errors="replace")
        self.assertIn("multiply defined", log)
        self.assertEqual(source.read_bytes(), original)

    def test_real_math_environment_changes_compile_and_remain_visible_in_review(self):
        from math_lexer import MATH_ENVIRONMENTS
        from review_project import review
        from verify_artifacts import verify_review
        formulas = []
        for name in sorted(MATH_ENVIRONMENTS):
            body = (r"{2}x&=y& a&=b" if name.startswith("alignat") else
                    r"x&=y&&" if name.startswith("flalign") else
                    r"x&=&y" if name.startswith("eqnarray") else
                    r"x&=y" if name.startswith("align") else "x+y")
            if name == "equation":
                body = r"\begin{split}x&=y+z\\a&=\begin{bmatrix}b&c\end{bmatrix}\end{split}"
            formulas.append(rf"\begin{{{name}}}{body}\end{{{name}}}")
        source = (r"\documentclass{article}\usepackage{amsmath}\begin{document}" + "\n" +
                  "\n".join(formulas) + "\n" + r"\end{document}")
        builds = {}
        for side, text in (("before", source), ("after", source.replace("x+y", "x-y").replace("y+z", "y-z"))):
            folder = self.work / side
            folder.mkdir()
            main = folder / "main.tex"
            main.write_text(text, encoding="utf-8")
            expected = main.read_bytes()
            result = check_build.build(main, self.work / f"{side}-build", until_stable=True, require_resolved=True)
            self.assert_build_success(result)
            self.assertEqual(main.read_bytes(), expected)
            builds[side] = Path(result["output"]) / "build-report.json"
        output = self.work / "math-review"
        result = review(self.work / "before", self.work / "after", output,
                        builds["before"], builds["after"], language="zh")
        self.assertEqual(result["builds"], {"before": "success", "after": "success"})
        evidence = json.loads((output / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(len(evidence["math_environment_inventory"]["after"]), len(MATH_ENVIRONMENTS))
        self.assertEqual(set(evidence["content_audit"][0]), {"file", "requires_review", "math_environments"})
        self.assertFalse(evidence["source_scan_issues"])
        self.assertEqual(verify_review(output)["status"], "verified")
        self.assertIn("带源码位置的公式环境", (output / "report.html").read_text(encoding="utf-8"))

    def test_real_unclosed_math_environment_fails_and_is_located_on_unchanged_sources(self):
        from review_project import review
        source = "\\documentclass{article}\n\\usepackage{amsmath}\n\\begin{document}\n\\begin{equation}x+y\n\\end{document}\n"
        for side in ("before", "after"):
            folder = self.work / side
            folder.mkdir()
            (folder / "main.tex").write_text(source, encoding="utf-8")
        native = check_build.build(self.work / "after/main.tex", self.work / "bad-math-build")
        self.assertEqual(native["status"], "failed")
        result = review(self.work / "before", self.work / "after", self.work / "bad-math-review",
                        after_build=self.work / "bad-math-build/build-report.json")
        self.assertEqual(result["changed_files"], 0)
        evidence = json.loads((self.work / "bad-math-review/review.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["math_environment_inventory"], {"before": [], "after": []})
        self.assertEqual({i["side"] for i in evidence["source_scan_issues"]}, {"before", "after"})
        self.assertTrue(any(i["code"] == "math-environment-unclosed" and i["line"] == 4
                            for i in evidence["source_scan_issues"]))

    def test_real_explicit_bibliography_guards_bind_configured_builds_and_review(self):
        from project_doctor import initialize
        from review_project import review
        from verify_artifacts import verify_review
        for backend in ("bibtex", "biber"):
            with self.subTest(backend=backend):
                if not shutil.which(backend):
                    if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                        self.fail(f"{backend} is required")
                    continue
                project = self.work / f"{backend} guarded project"
                project.mkdir()
                refs = project / "refs.bib"
                refs.write_text("@article{demo, author={Example, Alice}, title={Synthetic bibliography}, journal={Test}, year={2024}}\n", encoding="utf-8")
                if backend == "bibtex":
                    style = subprocess.check_output(["kpsewhich", "plain.bst"], text=True).strip()
                    shutil.copyfile(style, project / "local.bst")
                    body = r"\cite{demo}\bibliographystyle{local}\bibliography{refs}"
                    preamble = ""
                    watched = ["refs.bib", "local.bst"]
                else:
                    body = r"\cite{demo}\printbibliography"
                    preamble = r"\usepackage[backend=biber]{biblatex}\addbibresource{refs.bib}"
                    watched = ["refs.bib"]
                source = project / "main.tex"
                source.write_text(r"\documentclass{article}" + preamble + r"\begin{document}" + body + r"\end{document}", encoding="utf-8")
                initialize(project, "main.tex", backend=backend, passes=5)
                before = self.work / f"{backend} original"
                shutil.copytree(project, before)
                output = self.work / f"{backend} guarded build"
                arguments = [sys.executable, str(REPO / "scripts/als.py"), "--json", "build",
                             "--project", str(project), "--output", str(output), "--until-stable", "--require-resolved"]
                arguments.extend(f"--watch-input={name}" for name in watched)
                process = subprocess.run(arguments, cwd=self.work, capture_output=True, text=True, encoding="utf-8", timeout=180)
                envelope = json.loads(process.stdout)
                self.assertEqual(process.returncode, 0, envelope)
                result = envelope["result"]
                self.assertEqual(result["input_tracking"]["watched_inputs"], watched)
                for name in watched:
                    row = next(item for item in result["local_inputs"] if item["path"] == name)
                    self.assertEqual(row["observations"][0]["step"], "preflight")
                    self.assertIn("bibliography", [o["step"] for o in row["observations"]])
                    self.assertTrue(all(o["sha256"] == row["observations"][0]["sha256"] for o in row["observations"]))
                review_output = self.work / f"{backend} guarded review"
                review(before, project, review_output, after_build=output / "build-report.json", language="zh")
                evidence = json.loads((review_output / "review.json").read_text(encoding="utf-8"))
                self.assertEqual(evidence["builds"]["after"]["watched_inputs"], watched)
                self.assertEqual(verify_review(review_output)["status"], "verified")
                self.assertIn("显式监测的输入文件", (review_output / "report.html").read_text(encoding="utf-8"))
                refs.write_text(refs.read_text(encoding="utf-8").replace("Synthetic bibliography", "Later author edit"), encoding="utf-8")
                stale = self.work / f"{backend} stale review"
                with self.assertRaisesRegex(ValueError, "recorded input changed"):
                    review(before, project, stale, after_build=output / "build-report.json")
                self.assertFalse(stale.exists())

    def test_real_successful_backend_with_concurrent_bibliography_edit_fails_guard(self):
        from unittest.mock import patch
        if not shutil.which("bibtex"):
            if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                self.fail("bibtex required")
            self.skipTest("bibtex unavailable")
        project = self.work / "changed bibliography"
        project.mkdir()
        source, refs = project / "main.tex", project / "refs.bib"
        source.write_text(r"\documentclass{article}\begin{document}\cite{demo}\bibliographystyle{plain}\bibliography{refs}\end{document}", encoding="utf-8")
        refs.write_text("@article{demo,author={Example, Alice},title={Before edit},journal={Test},year={2024}}\n", encoding="utf-8")
        actual = check_build.subprocess.run
        def run_and_edit(command, **kwargs):
            result = actual(command, **kwargs)
            if Path(command[0]).name == "bibtex" and result.returncode == 0:
                refs.write_text(refs.read_text(encoding="utf-8").replace("Before edit", "Concurrent author edit"), encoding="utf-8")
            return result
        with patch.object(check_build.subprocess, "run", side_effect=run_and_edit):
            result = check_build.build(source, self.work / "changed bibliography build", backend="bibtex",
                                       passes=3, require_resolved=True, watch_inputs=["refs.bib"])
        self.assertEqual(result["status"], "failed")
        self.assertTrue(all(step["exit_code"] == 0 for step in result["steps"]))
        self.assertEqual(result["input_tracking"]["changed"], ["refs.bib"])
        self.assertIsNone(result["pdf"])
        self.assertTrue(result["source_unchanged"])
        self.assertIn("Concurrent author edit", refs.read_text(encoding="utf-8"))

    def test_broken_fixture_has_real_compilation_failure(self):
        self.copy_fixture("broken_paper.tex")
        result = self.compile("broken_paper.tex")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Undefined control sequence", result.stdout)

    def test_exported_full_paper_builds_both_languages_without_changing_export(self):
        from export_examples import export_example
        from verify_artifacts import verify_example
        for name in ("xelatex", "bibtex"):
            if shutil.which(name) is None:
                if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                    self.fail(f"{name} is required for the exported manuscript check")
                self.skipTest(f"{name} unavailable")
        exported = self.work / "exported paper"
        result = export_example("full-paper", exported, "zh")
        self.assertEqual(result["status"], "exported-not-run")
        before = check_build.build(exported / "case/before/main.tex", self.work / "export-before", "pdflatex", "bibtex", 3)
        self.assertEqual(before["status"], "failed")
        after = check_build.build(exported / "case/after/main.tex", self.work / "export-after", "pdflatex", "bibtex", 3, require_resolved=True)
        self.assert_build_success(after)
        chinese = check_build.build(exported / "case/after/main-cn.tex", self.work / "export-chinese", "xelatex", "bibtex", 3, require_resolved=True)
        self.assert_build_success(chinese)
        import pymupdf
        with pymupdf.open(self.work / "export-chinese" / chinese["pdf"]) as document:
            text = "\n".join(page.get_text() for page in document)
            self.assertIn("自制样例", text)
            self.assertIn("76.10", text)
        self.assertEqual(verify_example(exported)["status"], "verified")

    def test_project_inspector_matches_native_class_input_and_graphics_selection(self):
        import pymupdf
        project = self.work / "project"
        for directory in ("styles", "chapters", "a", "b"):
            (project / directory).mkdir(parents=True, exist_ok=True)
        (project / "main.tex").write_text(
            r"\documentclass{styles/top}\input settings.tex" + "\n" +
            r"\includeonly{chapters/one}\begin{document}\include{chapters/one}\include{chapters/missing}"
            r"See~\ref{sec:one}.\includegraphics[width=1cm]{figure}\end{document}", encoding="utf-8")
        (project / "styles/top.cls").write_text(r"\ProvidesClass{styles/top}\LoadClass{styles/base}", encoding="utf-8")
        (project / "styles/base.cls").write_text(r"\ProvidesClass{styles/base}\LoadClass{article}\RequirePackage{graphicx}", encoding="utf-8")
        (project / "settings.tex").write_text(r"\graphicspath{{a/}{b/}}\DeclareGraphicsExtensions{.png,.pdf}", encoding="utf-8")
        (project / "chapters/one.tex").write_text(r"\section{One}\label{sec:one}Supplied fixture.", encoding="utf-8")
        with pymupdf.open(self.work / "plot.pdf") as document:
            document[0].get_pixmap().save(project / "a/figure.png")
        shutil.copyfile(self.work / "plot.pdf", project / "b/figure.pdf")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "ready", inspection)
        self.assertTrue(next(item for item in inspection["dependencies"] if item["requested"] == "chapters/missing")["skipped"])
        self.assertEqual(next(item["file"] for item in inspection["dependencies"] if item["command"] == "includegraphics"), "a/figure.png")
        report = check_build.build(project / "main.tex", self.work / "project build", require_resolved=True)
        self.assert_build_success(report)
        observed = {item["path"] for item in report["local_inputs"]}
        self.assertTrue({item["file"] for item in inspection["inputs"]}.issubset(observed), (inspection, report))
        self.assertNotIn("b/figure.pdf", observed)
        self.assertNotIn("chapters/missing.tex", observed)

    def test_project_inspector_does_not_apply_a_later_graphics_path_retroactively(self):
        project = self.work / "late-path"
        (project / "figures").mkdir(parents=True)
        shutil.copyfile(self.work / "plot.pdf", project / "figures/figure.pdf")
        source = project / "main.tex"
        source.write_text(r"\documentclass{article}\usepackage{graphicx}\begin{document}"
                          r"\includegraphics{figure}\graphicspath{{figures/}}\end{document}", encoding="utf-8")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "blocked")
        self.assertFalse(inspection["dependencies"][0]["exists"])
        report = check_build.build(source, self.work / "late-path build")
        self.assertEqual(report["status"], "failed", report)

    def test_literal_scanner_agrees_with_native_comments_verbs_and_control_symbols(self):
        project = self.work / "literal scanner"
        project.mkdir()
        source = project / "main.tex"
        source.write_text(
            "\\documentclass{article}\n% \\begin{verbatim}\n"
            "\\begin{document}\n\\input{live}\n% \\end{verbatim}\n"
            "Example\\\\input{absent}\n"
            "\\verb|\\input{absent} 99|\n"
            "\\verb* 1\\input{absent}1\n"
            "\\verb *\\input{absent}*\n"
            "\\verb a\\input{hidden}a\n"
            "\\verb%\\input{absent}%\n"
            "\\begin{verbatim}\n\\input{absent}\n\\end{verbatim}\n"
            "\\end{document}\n", encoding="utf-8")
        (project / "live.tex").write_text("Actual input.", encoding="utf-8")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "ready", inspection)
        self.assertEqual([item["requested"] for item in inspection["dependencies"]], ["live"])
        report = check_build.build(source, self.work / "literal scanner build", require_resolved=True)
        self.assert_build_success(report)
        self.assertEqual({item["path"] for item in report["local_inputs"]}, {"main.tex", "live.tex"})

    def test_unfinished_inline_verb_is_unverified_and_fails_native_compilation(self):
        project = self.work / "unfinished literal"
        project.mkdir()
        source = project / "main.tex"
        source.write_text("\\documentclass{article}\n\\begin{document}\n\\verb|unfinished\n\\end{document}\n", encoding="utf-8")
        inspection = inspect_project(project, "main.tex", "pdflatex")
        self.assertEqual(inspection["status"], "needs-review")
        self.assertEqual([(item["code"], item["line"]) for item in inspection["diagnostics"]], [("unterminated-verb", 3)])
        report = check_build.build(source, self.work / "unfinished literal build")
        self.assertEqual(report["status"], "failed", report)

    def test_unified_cli_uses_effective_output_for_literal_source_and_configured_builds(self):
        from project_doctor import initialize
        project = self.work / "CLI project with spaces"
        project.mkdir()
        source = project / "--submission.tex"
        source.write_text(r"\documentclass{article}\begin{document}Actual CLI fixture\end{document}", encoding="utf-8")
        original = source.read_bytes()
        initialize(project, source.name, passes=2)
        for mode in ("source", "configuration"):
            with self.subTest(mode=mode):
                ignored, output = self.work / f"{mode} ignored", self.work / f"{mode} actual"
                ignored.mkdir()
                (ignored / "build-report.json").write_text('{"fake":true}', encoding="utf-8")
                args = ["--out=" + str(ignored), "--output", str(output), "--require-resolved"]
                args += ["--", source.name] if mode == "source" else ["--project=" + str(project), "--"]
                result = subprocess.run([sys.executable, str(REPO / "scripts/als.py"), "--json", "build", *args],
                                        cwd=project, capture_output=True, text=True, encoding="utf-8", timeout=60)
                evidence = json.loads(result.stdout)
                self.assertEqual(result.returncode, 0, evidence)
                self.assertEqual(evidence["result"]["status"], "success")
                self.assertEqual(evidence["result"]["source"], str(source))
                self.assertEqual(evidence["evidence"], [str(output / "build-report.json")])
                self.assertEqual(evidence["invocation"]["cwd"], str(project))
                self.assertIn(str(output), evidence["invocation"]["arguments"])
                self.assertTrue(json.loads((ignored / "build-report.json").read_text())["fake"])
                self.assertEqual(source.read_bytes(), original)
                self.assertFalse((project / "--submission.pdf").exists())

    def test_corrected_fixture_builds_pdf_without_tex_errors(self):
        self.copy_fixture("expected_fixed.tex")
        for _ in range(2):
            result = self.compile("expected_fixed.tex")
            self.assertEqual(result.returncode, 0, result.stdout[-6000:])
        pdf = self.work / "expected_fixed.pdf"
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
        log = (self.work / "expected_fixed.log").read_text(encoding="utf-8", errors="replace")
        self.assertIsNone(re.search(r"(?m)^!|^.*\.tex:\d+:.*(?:Error|Undefined control sequence)", log))

    def test_valid_reference_resolves_and_unknown_keys_stay_flagged(self):
        self.copy_fixture("expected_fixed.tex")
        for _ in range(2):
            result = self.compile("expected_fixed.tex")
            self.assertEqual(result.returncode, 0, result.stdout[-6000:])
        log = (self.work / "expected_fixed.log").read_text(encoding="utf-8", errors="replace")
        self.assertNotRegex(log, r"Reference [`']fig:results'")
        self.assertRegex(log, r"Reference [`']sec:missing'.*undefined")
        self.assertRegex(log, r"Citation [`']undefined2024'.*undefined")

    def test_bundled_build_helper_uses_fresh_output_and_retains_warnings(self):
        self.copy_fixture("expected_fixed.tex")
        report = check_build.build(self.work / "expected_fixed.tex", self.work / "fresh build")
        self.assert_build_success(report)
        self.assertTrue(any("undefined" in d["message"] for d in report["diagnostics"]))
        self.assertFalse((self.work / "expected_fixed.pdf").exists())
        self.assertEqual(len(report["steps"]), 2)

    def test_bundled_build_helper_does_not_accept_stale_source_pdf(self):
        self.copy_fixture("broken_paper.tex")
        (self.work / "broken_paper.pdf").write_bytes(b"%PDF-stale")
        report = check_build.build(self.work / "broken_paper.tex", self.work / "failed build")
        self.assertEqual(report["status"], "failed", report)
        self.assertTrue(report["diagnostics"])
        self.assertIsNone(report["pdf"])
        self.assertEqual((self.work / "broken_paper.pdf").read_bytes(), b"%PDF-stale")

    def test_bundled_build_helper_resolves_bibtex_and_paths_with_spaces(self):
        source = self.work / "paper name.tex"
        source.write_text(r"\documentclass{article}\begin{document}"
                          r"\input{section}\bibliographystyle{plain}\bibliography{refs}\end{document}", encoding="utf-8")
        (self.work / "section.tex").write_text(r"A result~\cite{demo}.\label{sec:one} See~\ref{sec:one}.", encoding="utf-8")
        (self.work / "refs.bib").write_text("@article{demo, author={A. Author}, title={Test}, journal={Example}, year={2020}}", encoding="utf-8")
        report = check_build.build(source, self.work / "bibliography build", backend="bibtex")
        self.assert_build_success(report)
        self.assertEqual(len(report["steps"]), 4)
        self.assertFalse(any("undefined" in d["message"] for d in report["diagnostics"]), report)
        self.assertTrue((self.work / "bibliography build/paper name.bbl").is_file())

    def test_bundled_build_helper_resolves_biber_with_project_local_bibliography(self):
        if not shutil.which("biber"):
            if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                self.fail("biber is required for the real backend CI case")
            self.skipTest("biber unavailable")
        source = self.work / "biber paper.tex"
        source.write_text(r"\documentclass{article}\usepackage[backend=biber]{biblatex}"
                          r"\addbibresource{refs.bib}\begin{document}"
                          r"A result~\cite{demo}.\printbibliography\end{document}", encoding="utf-8")
        (self.work / "refs.bib").write_text("@article{demo, author={A. Author}, title={Test}, journal={Example}, year={2020}}", encoding="utf-8")
        report = check_build.build(source, self.work / "biber build", backend="biber")
        self.assert_build_success(report)
        self.assertFalse(any("undefined" in d["message"] for d in report["diagnostics"]), report)
        self.assertTrue((self.work / "biber build/biber paper.bbl").is_file())

    def test_nested_includes_and_root_jobname_build_without_source_artifacts(self):
        source = self.work / "submission.tex"
        source.write_text(r"\documentclass{article}\begin{document}"
                          r"\input{\jobname-content}\include{chapters/one}"
                          r"See section~\ref{sec:one}.\end{document}", encoding="utf-8")
        (self.work / "submission-content.tex").write_text("Main content.", encoding="utf-8")
        (self.work / "chapters").mkdir()
        (self.work / "chapters/one.tex").write_text(r"\section{One}\label{sec:one}Chapter content.", encoding="utf-8")
        report = check_build.build(source, self.work / "nested build", until_stable=True, require_resolved=True)
        self.assert_build_success(report)
        self.assertEqual(report["pdf"], "submission.pdf")
        self.assertTrue(report["auxiliary_stable"])
        self.assertTrue((self.work / "nested build/chapters/one.aux").is_file())
        self.assertFalse((self.work / "chapters/one.aux").exists())
        self.assertFalse((self.work / "submission.aux").exists())
        self.assertEqual({item["path"] for item in report["local_inputs"]},
                         {"submission.tex", "submission-content.tex", "chapters/one.tex"})
        self.assertTrue(all(step["recorder"] for step in report["steps"]))

    def test_real_recorder_captures_local_style_and_graphics_without_unused_files(self):
        source = self.work / "manifest.tex"
        source.write_text(r"\documentclass{article}\usepackage{graphicx}\usepackage{localsettings}"
                          r"\begin{document}\input{part}\includegraphics[width=1cm]{plot.pdf}\end{document}", encoding="utf-8")
        (self.work / "localsettings.sty").write_text(r"\ProvidesPackage{localsettings}\newcommand{\localword}{Local}", encoding="utf-8")
        (self.work / "part.tex").write_text(r"\localword{} content.", encoding="utf-8")
        report = check_build.build(source, self.work / "manifest build")
        self.assert_build_success(report)
        self.assertEqual({item["path"] for item in report["local_inputs"]},
                         {"manifest.tex", "localsettings.sty", "part.tex", "plot.pdf"})
        self.assertEqual(report["input_tracking"]["changed"], [])
        self.assertEqual(report["input_tracking"]["unreadable"], [])
        for item in report["local_inputs"]:
            self.assertEqual(item["observations"][-1]["sha256"], check_build.fingerprint(self.work / item["path"])["sha256"])

    def test_missing_database_reports_real_bibtex_and_biber_failure_diagnostics(self):
        for backend in check_build.BACKENDS:
            with self.subTest(backend=backend):
                if not shutil.which(backend):
                    if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                        self.fail(f"{backend} is required for backend failure coverage")
                    continue
                source = self.work / f"missing-{backend}.tex"
                if backend == "bibtex":
                    content = (r"\documentclass{article}\begin{document}A citation~\cite{demo}."
                               r"\bibliographystyle{plain}\bibliography{nonexistent-latexskills}\end{document}")
                else:
                    content = (r"\documentclass{article}\usepackage[backend=biber]{biblatex}"
                               r"\addbibresource{nonexistent-latexskills.bib}\begin{document}"
                               r"A citation~\cite{demo}.\printbibliography\end{document}")
                source.write_text(content, encoding="utf-8")
                report = check_build.build(source, self.work / f"missing {backend} build", backend=backend)
                self.assertEqual(report["status"], "failed", report)
                self.assertEqual(report["failed_step"], "bibliography", report)
                self.assertEqual(report["diagnostic_step"], "bibliography")
                self.assertTrue(any(item["severity"] == "error" and "nonexistent-latexskills" in item["message"]
                                    for item in report["diagnostics"]), report)
                self.assertEqual(len(report["steps"]), 2)
                self.assertIsNone(report["pdf"])

    def test_installed_build_helper_compiles_without_repository_or_site_packages(self):
        sys.path.insert(0, str(REPO / "scripts"))
        from install import install
        destination = self.work / "installed skills"
        install(REPO, destination, ["latex-rescue"])
        source = self.work / "standalone.tex"
        source.write_text(r"\documentclass{article}\begin{document}Standalone build.\end{document}", encoding="utf-8")
        output = self.work / "installed build"
        result = subprocess.run([sys.executable, "-I", "-S", str(destination / "latex-rescue/scripts/check_build.py"),
                                 str(source), "--output", str(output)], cwd=self.work.parent,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads((output / "build-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "success")
        self.assertEqual({item["path"] for item in report["local_inputs"]}, {"standalone.tex"})

    def test_strict_check_rejects_real_unresolved_reference(self):
        source = self.work / "strict.tex"
        source.write_text(r"\documentclass{article}\begin{document}See~\ref{author:missing}.\end{document}", encoding="utf-8")
        report = check_build.build(source, self.work / "strict build", require_resolved=True)
        self.assertEqual(report["status"], "failed", report)
        self.assertTrue(report["unresolved_references"])
        self.assertTrue((self.work / "strict build/strict.pdf").is_file())

    def test_unicode_engines_compile_fontspec_with_bounded_settling(self):
        source = self.work / "unicode.tex"
        source.write_text("\\documentclass{article}\\usepackage{fontspec}"
                          "\\begin{document}Hôtel. $\\alpha+\\beta$.\\end{document}", encoding="utf-8")
        for engine in ("xelatex", "lualatex"):
            with self.subTest(engine=engine):
                if not shutil.which(engine):
                    if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                        self.fail(f"{engine} is required for the real engine CI case")
                    continue
                report = check_build.build(source, self.work / engine, engine=engine,
                                           until_stable=True, require_resolved=True, timeout=120)
                self.assert_build_success(report)
                self.assertTrue(report["auxiliary_stable"])
                self.assertEqual(report["pdf"], "unicode.pdf")

    def test_reconstruction_example_retains_scripts_cells_and_visible_uncertainty(self):
        import pymupdf
        from test_pdf_extract import extract_pdf

        source = self.work / "reconstruction_edges.tex"
        shutil.copyfile(FIXTURES / "pdf2tex/reconstruction_edges.tex", source)
        before = source.read_bytes()
        report = check_build.build(source, self.work / "reconstruction build",
                                   until_stable=True, require_resolved=True)
        self.assert_build_success(report)
        self.assertEqual(source.read_bytes(), before)
        pdf = Path(report["output"]) / report["pdf"]
        evidence = extract_pdf.extract(pdf, self.work / "reconstruction evidence", characters=True)
        with pymupdf.open(pdf) as doc:
            self.assertEqual(doc.page_count, 1)
            text = " ".join(doc[0].get_text().split())
            words = doc[0].get_text("words")
        for visible in ("76.10", "0.30", "92.3%", "78.2%", "[42]", "A&B",
                        "Spread is blank", "entry was not recovered", "retained as (7)"):
            self.assertIn(visible, text)

        def word(value, above=None):
            matches = [item for item in words if item[4] == value and (above is None or item[1] < above)]
            self.assertEqual(len(matches), 1, (value, matches))
            return matches[0]

        mean, spread, measured = word("76.10"), word("0.30"), word("Measured")
        self.assertLess(mean[2], spread[0])
        self.assertLess(spread[2], measured[0])
        variant = word("Variant")
        row = [item for item in words if abs(item[1] - variant[1]) < 1]
        self.assertIn("--", [item[4] for item in row])
        self.assertIn("Not", [item[4] for item in row])
        self.assertAlmostEqual(next(item[0] for item in row if item[4] == "Not"), measured[0], places=3)
        spread_header = word("Spread", above=mean[1])
        left, right = min(spread[0], spread_header[0]), max(spread[2], spread_header[2])
        self.assertFalse(any(left < (item[0] + item[2]) / 2 < right for item in row), row)

        lines = [line for page in evidence["pages"] for block in page["blocks"]
                 for line in block.get("lines", [])]
        all_chars = [char for line in lines for span in line["spans"] for char in span["chars"]]

        def script_offsets(label):
            line = next(item for item in lines if "".join(span["text"] for span in item["spans"]).startswith(label))
            label_chars = [char for span in line["spans"] for char in span["chars"]]
            colon = next(char for char in label_chars if char["c"] == ":")
            x, baseline = colon["origin"]
            glyphs = [char for char in all_chars if char["c"] in {"a", "i", "2"}
                      and char["origin"][0] > x + 5 and baseline - 8 <= char["origin"][1] <= baseline + 4]
            self.assertEqual(len(glyphs), 3, (label, glyphs))
            origins = {char["c"]: char["origin"] for char in glyphs}
            self.assertEqual(set(origins), {"a", "i", "2"})
            base = origins["a"]
            return {symbol: (point[0] - base[0], point[1] - base[1]) for symbol, point in origins.items()}

        first, second, nested = [script_offsets(label) for label in ("Order A:", "Order B:", "Nested:")]
        for symbol in first:
            for a, b in zip(first[symbol], second[symbol]):
                # Independent PDF positions are rounded; 0.01 pt is subpixel
                # even at 300 DPI, far below the script-grouping difference.
                self.assertAlmostEqual(a, b, delta=0.01)
        self.assertGreater(first["i"][1], 0)
        self.assertLess(first["2"][1], 0)
        self.assertGreater(abs(first["2"][1] - nested["2"][1]), 1)

    def test_literal_bibliography_headers_match_native_bibtex_without_value_fakes(self):
        if not shutil.which("bibtex"):
            self.fail("BibTeX is required for this native integration case")
        project = self.work / "bibtex-project"
        project.mkdir()
        source = project / "main.tex"
        source.write_text(r"\documentclass{article}\begin{document}\cite{brace,paren,percent,comment-active}"
                          r"\bibliographystyle{plain}\bibliography{refs}\end{document}", encoding="utf-8")
        shutil.copyfile(FIXTURES / "bibliography/headers.bib", project / "refs.bib")
        original = {path.name: path.read_bytes() for path in project.iterdir()}
        inspection = inspect_project(project, main="main.tex", engine="pdflatex", backend="bibtex")
        self.assertEqual(inspection["diagnostics"], [])
        report = check_build.build(source, self.work / "bibtex-valid", backend="bibtex", passes=3, require_resolved=True)
        self.assert_build_success(report)
        bbl = (self.work / "bibtex-valid/main.bbl").read_text(encoding="utf-8")
        actual = set(re.findall(r"\\bibitem\{([^}]+)\}", bbl))
        self.assertEqual(actual, {item["key"] for item in inspection["bibliography_entries"]})
        self.assertEqual(actual, {"brace", "paren", "percent", "comment-active"})
        self.assertEqual(original, {path.name: path.read_bytes() for path in project.iterdir()})
        source.write_text(r"\documentclass{article}\begin{document}\cite{fake-braced,fake-quoted,fake-string}"
                          r"\bibliographystyle{plain}\bibliography{refs}\end{document}", encoding="utf-8")
        missing = inspect_project(project, main="main.tex", engine="pdflatex", backend="bibtex")
        self.assertEqual(sum(item["code"] == "unknown-citation" for item in missing["diagnostics"]), 3)
        failed = check_build.build(source, self.work / "bibtex-missing", backend="bibtex", passes=3, require_resolved=True)
        self.assertEqual(failed["status"], "failed")
        transcripts = "\n".join((Path(failed["output"]) / step["transcript"]).read_text(encoding="utf-8", errors="replace") for step in failed["steps"])
        for key in ("fake-braced", "fake-quoted", "fake-string"):
            self.assertIn(f'I didn\'t find a database entry for "{key}"', transcripts)

    def test_literal_bibliography_headers_match_native_biber_for_common_values(self):
        if not shutil.which("biber"):
            if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                self.fail("Biber is required for this native integration case")
            self.skipTest("biber unavailable")
        project = self.work / "biber-project"
        project.mkdir()
        source = project / "main.tex"
        source.write_text(r"\documentclass{article}\usepackage[backend=biber]{biblatex}\addbibresource{refs.bib}"
                          r"\begin{document}\cite{brace,paren}\printbibliography\end{document}", encoding="utf-8")
        (project / "refs.bib").write_text('@string{unused="@misc{fake-string,title={Fake}}"}\n'
                                           '@comment{Ordinary comment}\n'
                                           '@misc{brace,author={Example, Alice},title={@misc{fake-braced,title={Fake}}},year={2026}}\n'
                                           '@misc(paren,author={Example, Bob},title="@misc{fake-quoted,title={Fake}}",year={2026})\n', encoding="utf-8")
        inspection = inspect_project(project, main="main.tex", engine="pdflatex", backend="biber")
        self.assertEqual(inspection["diagnostics"], [])
        report = check_build.build(source, self.work / "biber-valid", backend="biber", passes=3, require_resolved=True)
        self.assert_build_success(report)
        bbl = (self.work / "biber-valid/main.bbl").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"\\entry\{([^}]+)\}", bbl)), {item["key"] for item in inspection["bibliography_entries"]})

    def test_duplicate_bibliography_diagnostic_agrees_with_native_bibtex_failure(self):
        if not shutil.which("bibtex"):
            self.fail("BibTeX is required for this native integration case")
        project = self.work / "duplicate-project"
        project.mkdir()
        source = project / "main.tex"
        source.write_text(r"\documentclass{article}\begin{document}\cite{dup}\bibliographystyle{plain}\bibliography{refs}\end{document}", encoding="utf-8")
        (project / "refs.bib").write_text('@misc{dup,author={Example, Alice},title={First},year={2026}}\n'
                                           '@misc{DUP,author={Example, Bob},title={Second},year={2026}}', encoding="utf-8")
        inspection = inspect_project(project, main="main.tex", engine="pdflatex", backend="bibtex")
        repeated = [item for item in inspection["diagnostics"] if item["code"] == "duplicate-bib-key"]
        self.assertEqual(len(repeated), 1)
        self.assertEqual((repeated[0]["file"], repeated[0]["line"]), ("refs.bib", 2))
        report = check_build.build(source, self.work / "bibtex-duplicate", backend="bibtex")
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["failed_step"], "bibliography")

    def test_sealed_static_inspection_and_native_build_have_distinct_outcomes(self):
        from inspection_bundle import export_inspection
        from verify_artifacts import verify_inspection
        project = self.work / "manuscript"
        project.mkdir()
        (project / "main.tex").write_text("\\documentclass{article}\\begin{document}\\input{part}\\end{document}", encoding="utf-8")
        (project / "part.tex").write_text("Supplied value 42", encoding="utf-8")
        original = {path.name: path.read_bytes() for path in project.iterdir()}
        report = export_inspection(project, self.work / "sealed", engine="pdflatex", language="zh")
        self.assertEqual(report["status"], "ready")
        built = check_build.build(project / "main.tex", self.work / "native", require_resolved=True)
        self.assert_build_success(built)
        self.assertEqual({item["file"] for item in report["inputs"]}, {"main.tex", "part.tex"})
        self.assertEqual(original, {path.name: path.read_bytes() for path in project.iterdir()})
        (project / "part.tex").write_text("\\undefinedInspectionControl", encoding="utf-8")
        second = export_inspection(project, self.work / "static-only", engine="pdflatex")
        self.assertEqual(second["status"], "ready")
        failed = check_build.build(project / "main.tex", self.work / "failed-native")
        self.assertEqual(failed["status"], "failed")
        project.rename(self.work / "moved-manuscript")
        for directory in ("sealed", "static-only"):
            self.assertEqual(verify_inspection(self.work / directory)["status"], "verified")

    def test_installed_layout_example_adapts_to_column_and_minipage_widths(self):
        import pymupdf
        sys.path.insert(0, str(REPO / "scripts"))
        from install import install

        destination = self.work / "formatting skills"
        install(REPO, destination, ["latex-fmt"])
        example = destination / "latex-fmt/assets/layout-example.tex"
        before = example.read_bytes()
        content = example.read_text(encoding="utf-8")
        self.assertEqual(content.count(r"\documentclass[twocolumn]{article}"), 1)
        widths = {}
        for engine in ("pdflatex", "xelatex", "lualatex"):
            if not shutil.which(engine):
                if os.environ.get("LATEX_SKILLS_REQUIRE_TEX") == "1":
                    self.fail(f"{engine} is required for the layout integration case")
                continue
            for mode in ("onecolumn", "twocolumn"):
                with self.subTest(engine=engine, mode=mode):
                    source = self.work / f"layout-{engine}-{mode}.tex"
                    candidate = content.replace(r"\documentclass[twocolumn]{article}",
                                                rf"\documentclass[{mode}]{{article}}")
                    candidate = candidate.replace(r"\begin{document}",
                                                  r"\begin{document}\typeout{EXAMPLE-COLUMN-PT=\the\columnwidth}")
                    source.write_text(candidate, encoding="utf-8")
                    source_before = source.read_bytes()
                    report = check_build.build(source, self.work / f"{engine} {mode} build", engine=engine,
                                               until_stable=True, require_resolved=True)
                    self.assert_build_success(report)
                    self.assertEqual(source.read_bytes(), source_before)
                    last = report["steps"][-1]
                    log = (Path(report["output"]) / last["log"]).read_text(encoding="utf-8", errors="replace")
                    self.assertNotIn("Overfull", log)
                    width_pt = float(re.search(r"EXAMPLE-COLUMN-PT=([0-9.]+)pt", log).group(1))
                    widths[engine, mode] = width_pt
                    # TeX points are 1/72.27 inch; PDF points are 1/72 inch.
                    expected_width = 0.8 * width_pt * 72 / 72.27
                    with pymupdf.open(Path(report["output"]) / report["pdf"]) as doc:
                        text = " ".join(" ".join(page.get_text().split()) for page in doc)
                        panels = [drawing["rect"] for page in doc for drawing in page.get_drawings()
                                  if drawing["rect"].height < 1
                                  and abs(drawing["rect"].width - expected_width) < 0.05]
                        self.assertEqual(len(panels), 2, (expected_width, panels))
                        for page in doc:
                            self.assertTrue(all(0 <= item[0] < item[2] <= page.rect.width
                                                and 0 <= item[1] < item[3] <= page.rect.height
                                                for item in page.get_text("words")))
                    for value in ("76.10", "0.30", "78.20", "0.40", "Figure 1", "Table 1", "(1)"):
                        self.assertIn(value, text)
            self.assertGreater(widths[engine, "onecolumn"], widths[engine, "twocolumn"])
        self.assertEqual(example.read_bytes(), before)
