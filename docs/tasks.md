# Start with your manuscript task

[简体中文](tasks_CN.md) · [Install](install.md) · [CLI](cli.md)

| Your task | First useful result | Next evidence |
|---|---|---|
| [Repair a build](#repair) | Project settings, missing inputs and problem locations | Native build logs and unresolved references |
| [Polish prose](#polish) | An editable candidate preserving the original claims | Source diff and author review |
| [Change templates](#format) | A scoped migration against the supplied official kit | Actual build, pages and venue checklist |
| [Read a paper](#read) | Claims connected to source locations | Checked assumptions and unresolved questions |
| [Recover PDF source](#recover) | Page extraction and editable reconstruction | Original/candidate page comparison |

These are operator recipes. `als` prepares or checks evidence; editing and
analysis require your agent to follow the selected skill. Commands do not call
an external model. Use `python scripts/als.py` instead of `als` in a checkout
without package installation. Replace sample paths with your own paths. Quote
paths containing spaces. Each output directory must be new and outside the
manuscript source trees. Keep an unchanged original before agent edits.

<a id="repair"></a>

## Repair a build

1. Choose the actual main file, engine and bibliography backend. When known,
   save them once; `project init` creates `.als.json` and refuses an existing
   config. If no bibliography backend is used, omit `--backend`.

   ```sh
   als project init path/to/paper --main main.tex --engine xelatex --backend biber
   als doctor --project path/to/paper --skill latex-rescue
   ```

2. For a project without a config, inspect it with explicit settings:

   ```sh
   als doctor --project path/to/paper --main main.tex --engine xelatex --backend biber --skill latex-rescue
   als project check path/to/paper --main main.tex --engine xelatex --backend biber --bundle work/inspection-01
   ```

   `doctor` prints tool checks and located source diagnostics without writing
   or compiling. Exit 1 means blocked; exit 2 means invalid arguments or an
   unreadable/invalid project. Exit 0 may still say `needs-review`. Open
   `work/inspection-01/report.html` to read/share the static report.

3. Use `latex-rescue` on a separate candidate copy. Supply the original log and
   ask for minimal fixes, unchanged numbers/math/unknown keys, and a report of
   remaining uncertainties. Build a configured candidate:

   ```sh
   als build --project path/to/candidate --output work/build-01 --until-stable --require-resolved
   ```

   Inspect `work/build-01/build-report.json` and retained logs. A failed build
   remains evidence. A tool found on PATH is not proof it can compile this paper.
   [Project settings](project.md) · [Reference problems](bibliography.md)

<a id="polish"></a>

## Polish prose

1. Preserve the original and create a candidate copy. Select `latex-polish` and
   specify light, moderate or strict editing. Identify the sections to edit,
   the intended audience and claims that require author confirmation.
2. Ask the agent to retain quantities, units, causal/negative claims, citation
   keys, equations and TeX commands, and to report substantive wording choices.
3. Review both copies:

   ```sh
   als review --before path/to/original --after path/to/candidate --output work/polish-review
   als verify review work/polish-review
   ```

   Open `work/polish-review/report.html`. Numbers/reference/math changes and
   TODOs help route author review; unchanged literals do not prove unchanged
   meaning. Without `--before-build`/`--after-build`, PDF compilation remains
   unverified. To include native evidence, build each copy with actual settings:

   ```sh
   als build path/to/original/main.tex --output work/polish-before --engine pdflatex --backend bibtex --until-stable --require-resolved
   als build path/to/candidate/main.tex --output work/polish-after --engine pdflatex --backend bibtex --until-stable --require-resolved
   als review --before path/to/original --after path/to/candidate --before-build work/polish-before/build-report.json --after-build work/polish-after/build-report.json --output work/polish-built
   ```

   [Worked polish example](../examples/polish/README.md) · [Review options](review.md)

<a id="format"></a>

## Change templates

1. Supply the official author kit and requested venue, year, track, article
   type and submission stage. Read `latex-fmt`; separate layout changes from
   prose edits. Do not treat the bundled illustrative template as an official kit.
2. Diagnose the candidate using its actual engine/backend:

   ```sh
   als doctor --project path/to/candidate --main main.tex --engine pdflatex --backend bibtex --skill latex-fmt
   ```

3. Build and review the original/candidate with the [review workflow](review.md).
   Inspect overflow, page limits, anonymity, fonts and template-required
   sections in actual pages. Build each copy with its own actual settings,
   then attach the corresponding `build-report.json` files with `--before-build` and
   `--after-build`. Different templates can require different engines/backends.

   [Formatting example](../examples/fmt/README.md) · [Official-source routing](../latex-fmt/references/templates/venue-guide.md)

<a id="read"></a>

## Read a paper

For pasted text, `paper-read` does not require PDF tools. For a digital PDF:

```sh
als doctor --skill paper-read
als extract paper.pdf --output work/reading-pages --render
```

Open `work/reading-pages/report.html`. Choose skim, read or deep mode and give
the agent the paper plus required references. Require page/section locations
for claims, assumptions, methods, limitations and conflicting results. Check
the source pages yourself. A missing optional PyMuPDF probe does not block
pasted-text reading, but extraction itself needs the library.

[Reader example](../examples/read/README.md) · [PDF extraction options](cli.md)

<a id="recover"></a>

## Recover PDF source

```sh
als doctor --skill pdf2tex
als extract original.pdf --output work/recovery-pages --chars --render
```

Open `work/recovery-pages/report.html` and supply that evidence to `pdf2tex`.
Require editable source and a reconstruction report covering page scope,
uncertain symbols, table blanks/precision, vector figures and references.
Compile the candidate with its actual engine, then compare its PDF with the
original pages. Extraction is not OCR and does not recover the original source.
For image-only PDFs, use a separately chosen OCR workflow before reconstruction.

[Two-page recovery example](../examples/pdf2tex/README.md) · [Complete manuscript demonstration](../examples/full-paper/README.md)

## Try a complete demonstration

```sh
python -m pip install ".[pdf]"
als paper --output work/manuscript-demo
```

Requires the native engines/backends listed in the
[complete manuscript case](../examples/full-paper/README.md). Open
`work/manuscript-demo/review/report.html`. All committed examples are synthetic,
MIT-licensed and maintainer-authored. To contribute a real case, follow the
[case acceptance checklist](case-contributions.md). To measure model behavior,
start with the [paired evaluation pilot](pilot.md).

## Start from an exported case

Installed packages can [export any of six cases](examples-export.md) without
the source checkout or optional dependencies. Open its offline guide, verify
initial bytes, then make a separate candidate copy. Keep these maintainer
answers outside blind evaluation sessions. [Documentation index](README.md).
