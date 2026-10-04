# A complete manuscript, from broken source to review

This **synthetic software example** includes a two-column English manuscript,
six section files, a local style, grouped table headers, two figure panels, a
real bibliography entry, an appendix, and a Chinese XeLaTeX companion. It is
not a published research paper or an official venue template. Toy values stay
clearly identified as toy values.

| Original project | Candidate project | Purpose |
|---|---|---|
| [before/main.tex](before/main.tex) | [after/main.tex](after/main.tex) | Complete source tree and bibliography |
| [before/sections/methods.tex](before/sections/methods.tex) | [after/sections/methods.tex](after/sections/methods.tex) | Missing graphic and panel-width repairs |
| [before/sections/results.tex](before/sections/results.tex) | [after/sections/results.tex](after/sections/results.tex) | Minimal syntax correction; precision/blank cells retained |
| [before/main-cn.tex](before/main-cn.tex) | [after/main-cn.tex](after/main-cn.tex) | Chinese companion and explicit font/engine |

The original fails its native build. The candidate fixes the missing image
path, local panel widths and `textbff` typo. It retains values, keys, equations
and the unresolved timing protocol. [decisions.md](decisions.md) explains each
edit and the decision still needed from the author.

## Verify everything with one command

From the repository root, or an installed CLI:

```sh
python -m pip install ".[pdf]"
als paper --output work/full-paper-run
```

Requires pdfLaTeX, XeLaTeX, BibTeX and **Noto Serif CJK SC**. CI installs these
dependencies and uploads `full-paper-evidence`. Download that artifact from a
successful [Tests run](https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml).

The runner copies both projects, inspects their dependencies, requires the
original English build to fail, and requires the candidate English/Chinese
builds to succeed with resolved references. It checks the English log for
horizontal overflow, retained PDF values and Chinese text, unchanged source
trees, and content/decision signals in the unified review.

Open `work/full-paper-run/review/report.html`. Inspect `verification.json`,
`inspection-before.json`, `inspection-after.json`, retained build logs/PDFs,
the source diff, English page previews and `chinese-pages/`.
Open `inspection-before.html` and `inspection-after.html` for located static
issues, dependency resolutions and next steps; these reports keep compilation
separate from project inspection.
The failed original has no successful PDF preview; its source and failure
logs remain reviewable. The review does not fabricate an original page.

For source inspection on a machine without TeX:

```sh
als paper --output work/full-paper-portable --allow-unverified
```

This retains explicit unverified build states and a source review. It cannot
replace the native verification. It still requires PyMuPDF for the runner.

## Apply the same workflow to your manuscript

```sh
als project check examples/full-paper/after --html work/project-inspection.html
als build --project examples/full-paper/after --output work/configured-build --require-resolved
```

The candidate includes [.als.json](after/.als.json). Your own manuscript can
record its root/engine/backend with `als project init`; see
[project configuration](../../docs/project.md) and [change review](../../docs/review.md).
