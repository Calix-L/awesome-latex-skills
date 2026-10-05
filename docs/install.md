# Install the CLI and skills

Python 3.10+ is required. From the repository checkout:

```sh
python -m pip install .
als --version
als install --agent codex --dry-run
als install --agent codex
```

Use `--agent claude` for Claude Code. The `als` executable and
`python -m awesome_latex_skills` entry point use the Python environment where
you installed the package. Keep that environment active. Installing the CLI
does not install a model or TeX distribution.

## Optional dependencies

```sh
python -m pip install ".[pdf,validation]"
als doctor --skill pdf2tex
als validate
```

The core package has no runtime dependencies. The `pdf` extra adds PyMuPDF for
extraction, PDF review and worked examples; `validation` adds the YAML/Markdown
parsers used by repository validation. Native compilation still requires the
project's actual engine, bibliography backend, fonts and packages.

Alternatively, download the wheel or source distribution from
[GitHub Releases](https://github.com/Calix-L/awesome-latex-skills/releases)
and install the local file:

```sh
python -m pip install path/to/awesome_latex_skills-1.19.0-py3-none-any.whl
```

This project does not claim a PyPI publication. Install from the checkout or
the published release asset. Compare the asset with `SHA256SUMS`; checksums
establish integrity, so verify the release/tag and CI separately.

## Development and updates

```sh
python -m pip install -e ".[pdf,validation]"
git pull --ff-only
als install --agent codex --update --dry-run
als install --agent codex --update
```

Editable installation follows the source checkout. For an ordinary package
installation, reinstall from the new checkout/release before updating skill
copies. CLI upgrades and installed skill upgrades are separate operations.
Managed skill updates preserve local edits by refusing a changed bundle; the
[installation details](../README.md#quick-start) describe receipts and recovery.

All resources are included in the wheel: selected-skill installation, examples,
evaluation and release tools work outside the source checkout. CI installs the
wheel in a fresh virtual environment, clears `PYTHONPATH`, executes from another
directory, checks the active interpreter, and compares the installed bundle
with the release source. It also rebuilds the source distribution and repeats
first-use checks on Windows, macOS and Linux.

## First example outside the checkout

```sh
als examples export --case full-paper --output ../my-example
als verify example ../my-example
```

Open `../my-example/report.html`. Export uses only the standard library, keeps
the full source/configuration/assets and does not run a model or TeX. See the
[copy workflow](examples-export.md) ([中文](examples-export_CN.md)) and
[documentation index](README.md). Preserve the initial copy before editing;
verification checks its initial bytes and intentionally rejects later changes.
