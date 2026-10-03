# Worked examples / 可复现案例

Five small, synthetic, MIT-licensed cases show the complete path from input to
candidate, report and executable evidence. All candidates are maintainer-authored;
they demonstrate reviewable deliverables and do not establish model improvement.

| Skill | Input → candidate | What to inspect |
| --- | --- | --- |
| [Rescue](rescue/README.md) | Broken TeX → minimal repair | Numbers and unknown keys survive; ambiguous math stays flagged. Ordinary build succeeds, strict references intentionally fail. |
| [Polish](polish/README.md) | Toy academic prose → grammatical edit | Components, negative claims, math, scope and comments stay intact. |
| [Format](fmt/README.md) | Two-column overflow → local-width panel | A real build detects input overflow and verifies its removal; this is not an official venue kit. |
| [Read](read/README.md) | Fictional paper → evidence map | Conflicting claims and missing timing details remain explicit. |
| [PDF → TeX](pdf2tex/README.md) | Two-page PDF → reconstructed TeX | Grouped header, blank cell, precision, vector diagram uncertainty and unmatched citation remain visible. |

```sh
python scripts/als.py examples list
python scripts/als.py examples run --output work/example-run
# When TeX is unavailable, explicitly retain an unverified build status:
python scripts/als.py examples run --output work/portable-run --allow-unverified
```

Requires PyMuPDF 1.24.10+; the default run also requires pdfLaTeX and the packages
in the examples. Choose `--engine xelatex` or `--engine lualatex` if installed.
The runner copies source artifacts, records SHA-256, writes TeX diffs, audits
protected literals, executes fresh builds/extraction and saves page PNG previews.
All failures retain their evidence. A missing engine fails before output creation
unless portable mode is explicitly selected. The reader example has literal
checks only; semantic review is always required.

CI attaches the actual `worked-example-evidence` artifact. It includes
`verification.json`, per-case reports, logs, PDFs, previews and extraction HTML.
See the [Tests workflow](https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml)
for a run corresponding to the commit you use. The README overview is an
illustration, not a screenshot of independent agent performance.

The committed PDF is ready to use. Optional regeneration needs ReportLab 4.x:
`python examples/pdf2tex/generate_input.py --output path/to/new-input.pdf`.
The generator refuses an existing destination. ReportLab is not a core dependency.

中文：所有输入均为自制样例，配套候选结果、说明和核验入口。运行后检查
`verification.json` 与 PDF 预览；`partial` 表示仍有未验证的编译步骤。人工内容
审查不能由关键词检查替代。详见[评测协议](../docs/evaluation.md)。
