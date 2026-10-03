# Unified CLI

Run from a source checkout or the full release archive with Python 3.10+.
Or [install the package](install.md) and use `als` / `python -m awesome_latex_skills`
from any working directory. These entry points use the same command interface.
The installer and maintenance tools use the standard library. Validation needs
`requirements-dev.txt`; extraction and the worked-example runner need
PyMuPDF 1.24.10+. Native builds need the selected TeX engine and actual packages.
Individual installed skill bundles retain their own helpers; they do not include
this project-level CLI.

```sh
python scripts/als.py --help
python scripts/als.py --version
python scripts/als.py install --agent codex --dry-run
python scripts/als.py --json doctor --engine pdflatex
python scripts/als.py build manuscript.tex --output work/build-01 --require-resolved
python scripts/als.py extract original.pdf --output work/pdf-01 --chars --render
python scripts/als.py project init path/to/paper --main main.tex --engine pdflatex
python scripts/als.py project check path/to/paper
python scripts/als.py build --project path/to/paper --output work/build-02
python scripts/als.py review --before path/to/original --after path/to/candidate --output work/review-01
python scripts/als.py paper --output work/full-paper-run
python scripts/als.py validate
python scripts/als.py evaluate validate
python scripts/als.py examples list
python scripts/als.py benchmark prepare --trials 3 --output evaluation-runs/batch-01
python scripts/als.py sources
python scripts/als.py release --output dist/1.5.1
```

Use `COMMAND --help` for the native options. Paths supplied by the user resolve
from the current working directory; helper paths resolve from the checkout.
The CLI runs the same Python interpreter that invoked it, without a shell.
Existing direct script commands remain supported.

## Reports and exit codes

Put `--json` **before** the command:

```sh
python scripts/als.py --json extract original.pdf --output work/pdf-02 --render
```

The schema-1 envelope contains `version`, `command`, `status`, `exit_code`,
`result`, `evidence`, `stdout`, and `stderr`. Build and extraction reports are
loaded only from a newly created output directory. Existing output evidence is
never attached as if produced by this invocation. Native build reports remain
schema 3; PDF extraction reports remain schema 2. `--help` is plain text.

The wrapper preserves each helper's exit code: normally 0 for completed work,
1 for a failed check, and 2 for invalid arguments or preconditions. Extraction
uses 1 for its operational errors; interruption uses 130. Inspect `result` and
native evidence: `examples --allow-unverified` can complete with code 0 and
`status: partial`; a source audit with `--validate-only` validates metadata even
when review is still pending. Compilation success does not imply resolved
citations, faithful prose, or venue compliance.

Build/extraction/example/evaluation/release outputs require fresh destinations.
If an example check fails, its logs and `verification.json` stay in the new
directory for diagnosis. Output directories `work/`, `dist/`, and
`evaluation-runs/` are generated evidence, excluded from source validation and
release packaging.

See [worked examples](../examples/README.md), [evaluation](evaluation.md), and
[complete project](../examples/full-paper/README.md), [project configuration](project.md),
[change review](review.md), and [releases](releases.md).
