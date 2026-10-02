# Build evidence for conventional projects

Use the project's existing build system for custom working directories, generated
assets, MakeIndex/glossaries, split auxiliary directories, or required shell
escape. The bundled helper handles a root `.tex` document, local inputs/assets,
and an optional explicitly selected BibTeX or Biber step. It does not infer the
root, engine, backend, or venue requirements.

From the repository root:

```sh
python latex-rescue/scripts/check_build.py path/to/paper.tex --output fresh-build
python latex-rescue/scripts/check_build.py path/to/paper.tex --output fresh-bibliography-build --engine xelatex --backend biber
```

An installed skill contains the same standalone standard-library script. Invoke
it by its installed path; it has no import dependency on the repository. Python
3.10+ and the selected external engine/backend must be available on `PATH`.

## What is retained

- `document.pdf` and native auxiliary files in a **new** output directory.
- Each engine pass's transcript and log, for example `engine-01.txt` and
  `engine-01.log`; a later failure does not inherit the previous pass's log.
- `bibliography.txt` / `bibliography.blg` when a backend is requested.
- `build-report.json` (schema 1): root path and SHA-256, selected tools, commands,
  working directories, process exit codes, timeout status, evidence filenames,
  final engine diagnostics, failure reason, and verified PDF filename.

The engine runs from the root document's directory with shell escape disabled.
The backend receives that directory in its bibliography/style search paths.
The helper does not edit source, reuse existing output, or enable shell escape.
TeX itself still reads project files; this build wrapper is not a sandbox.

## Interpret the result

Exit **0** requires all requested processes to finish successfully, no recognized
errors in the final engine log, and a newly produced PDF header. It can still have
undefined citations/references, layout warnings, or rerun requests. Diagnostics
recognize common `!`, file-line, LaTeX/package/class warning, and box messages;
read the complete logs for wrapped messages and other engine/backend diagnostics.

Exit **1** means the attempted build failed or timed out; evidence remains in
the output directory. Exit **2** means invalid arguments, missing prerequisites,
or an I/O failure. A PDF left by a failed pass is not a successful deliverable.
An interruption retains the report with an unverified status.

By default, run two engine passes; with `--backend bibtex` or `--backend biber`,
run the engine once, the backend once, then the engine twice. `--passes 1-5`
sets the total engine passes (at least two with a backend). `--timeout 60` sets
the per-process timeout in seconds. Fixed passes do not certify convergence;
inspect rerun warnings and use a new output directory for a further check.

The root hash identifies only that file, not a frozen snapshot of every included
file. Verify PDF content visually and preserve the source diff separately.

Command semantics: [Web2C manual](https://www.tug.org/texinfohtml/web2c.html),
[Biber manual](https://tug.ctan.org/biblio/biber/base/documentation/biber.pdf).
