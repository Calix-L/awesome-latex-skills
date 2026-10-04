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
python scripts/als.py project check path/to/paper --output work/inspection.json --html work/inspection.html --html-language zh
python scripts/als.py build --project path/to/paper --output work/build-02
python scripts/als.py review --before path/to/original --after path/to/candidate --output work/review-01
python scripts/als.py review --before path/to/original --after path/to/candidate --output work/review-zh --language zh
python scripts/als.py verify review work/review-zh
python scripts/als.py verify release path/to/downloaded-assets
python scripts/als.py paper --output work/full-paper-run
python scripts/als.py validate
python scripts/als.py evaluate validate
python scripts/als.py examples list
python scripts/als.py benchmark prepare --trials 3 --output evaluation-runs/batch-01
python scripts/als.py benchmark prepare --case polish-scope --trials 1 --output evaluation-runs/pilot-01
python scripts/als.py benchmark run --task evaluation-runs/pilot-01/tasks/polish-scope-01-baseline --spec runner-spec.json
python scripts/als.py benchmark review-template --task evaluation-runs/pilot-01/tasks/polish-scope-01-baseline --output work/baseline-review.json
python scripts/als.py sources
python scripts/als.py release --output dist/1.11.0
```

Use `COMMAND --help` for the native options. Paths supplied by the user resolve
from the current working directory; helper paths resolve from the checkout.
The CLI runs the same Python interpreter that invoked it, without a shell.
Existing direct script commands remain supported.

Build and extraction use the same argument grammar as their standalone helpers.
The wrapper respects `--name=value`, unambiguous long-option abbreviations and
the `--` end-of-options marker. Prefer full option names in saved commands.
For a filename beginning with a dash, put all options before the marker:

```sh
als --json build --output work/build-dash -- --submission.tex
als --json extract --output work/extract-dash -- --paper.pdf
als --json build --project path/to/paper --output work/configured-build --
als build --project path/to/missing-project --help
```

Use a source file or one `--project` directory. Explicit engine/backend/pass
options override project configuration. Repeated ordinary value options follow
the helper's last-value behavior; the wrapper attaches evidence only from the
effective output directory. Earlier output directories are untouched. Repeated
`--project` or a project combined with a source is refused. Build/extraction help
and argument errors do not read project configuration or launch a helper.

See the [Chinese command guide](cli_CN.md) for common project workflows.

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

The additive `invocation` object records the attempted helper's relative path,
Python interpreter, working directory and exact argument list. Configured build
arguments contain the selected source and resolved defaults/overrides. It is
null for build/extraction help, argument-preflight errors, unknown commands and
version queries. This records an execution attempt, not independent proof that
the process launched or completed. Child stdout/stderr and exit codes remain the
evidence for the outcome. Top-level help remains plain text; with `--json`,
build/extraction help is captured in the envelope's `stdout`, with null `result`
and empty `evidence`.

The wrapper preserves each helper's exit code: normally 0 for completed work,
1 for a failed check, and 2 for invalid arguments or preconditions. Extraction
uses 1 for its operational errors; interruption uses 130. Inspect `result` and
native evidence: `examples --allow-unverified` can complete with code 0 and
`status: partial`; a source audit with `--validate-only` validates metadata even
when review is still pending. Compilation success does not imply resolved
citations, faithful prose, or venue compliance.
`review --language zh` and `paper --language zh` select Chinese offline reports;
the original source, notes and compiler diagnostics keep their original text.
`verify` checks [offline artifact integrity](verification.md) without modifying
its target. Passing checks return 0, mismatches/incomplete legacy coverage 1,
and malformed metadata/preconditions 2. It does not authenticate the producer
or infer compilation/content quality.

Build/extraction/example/evaluation/release outputs require fresh destinations.
If an example check fails, its logs and `verification.json` stay in the new
directory for diagnosis. Output directories `work/`, `dist/`, and
`evaluation-runs/` are generated evidence, excluded from source validation and
release packaging.

See [worked examples](../examples/README.md), [evaluation](evaluation.md), and
[complete project](../examples/full-paper/README.md), [project configuration](project.md),
[change review](review.md), and [releases](releases.md).
