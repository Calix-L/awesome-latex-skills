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
# Bound reference settling and require unresolved citations/references to be reported as failure
python latex-rescue/scripts/check_build.py path/to/paper.tex --output final-check --until-stable --require-resolved
```

An installed skill contains the same standalone standard-library script. Invoke
it by its installed path; it has no import dependency on the repository. Python
3.10+ and the selected external engine/backend must be available on `PATH`.

## What is retained

- `<root-name>.pdf` and native auxiliary files in a **new** output directory.
  The root basename is preserved by default; `--jobname submission` overrides it.
- Each engine pass's transcript and log, for example `logs/engine-01.txt` and
  `logs/engine-01.log`; a later failure does not inherit the previous pass's log.
  Evidence lives in `logs/` to avoid collisions with the root's output basename.
- `logs/bibliography.txt` / `logs/bibliography.blg` when a backend is requested.
- `build-report.json` (schema 2): root path and starting SHA-256, job name, selected tools, commands,
  working directories, process exit codes, timeout status, evidence filenames,
  final engine diagnostics, auxiliary stability, rerun/unresolved-reference status,
  root-source change detection, failure reason, and verified PDF filename.

The engine runs from the root document's directory with shell escape disabled.
The backend receives that directory in its bibliography/style search paths.
Local `.tex` subdirectories are mirrored as empty output directories so ordinary
nested `\include{chapters/one}` auxiliary files can be written. No source is copied.
The helper does not edit source, reuse existing output, or enable shell escape.
TeX itself still reads project files; this build wrapper is not a sandbox.

## Interpret the result

Exit **0** requires all requested processes to finish successfully, no recognized
errors in the final engine log, and a newly produced PDF header from the final
pass. The previous pass's generated PDF is removed before each next engine pass.
It can still have
undefined citations/references, layout warnings, or rerun requests. Diagnostics
recognize common `!`, file-line, LaTeX/package/class warning, and box messages;
read the complete logs for wrapped messages and other engine/backend diagnostics.

Exit **1** means the attempted build failed or timed out; evidence remains in
the output directory. Exit **2** means invalid arguments, missing prerequisites,
or an I/O failure. A PDF left by a failed pass is not a successful deliverable.
An interruption retains the report with an unverified status.

`--require-resolved` makes recognized unresolved references/citations or rerun
requests fail even when a PDF was produced. It does not prove that citations
point to the intended evidence. The author must still resolve unknown keys.

By default, run two engine passes; with `--backend bibtex` or `--backend biber`,
run the engine once, the backend once, then the engine twice. `--passes 1-5`
sets the total engine passes (at least two with a backend). With `--until-stable`,
it sets a maximum: default five. The helper stops after consecutive nonempty
auxiliary snapshots match and recognized rerun requests disappear. Reaching the
limit without that state fails the check. BibTeX/Biber still runs once after the
first engine pass; workflows requiring repeated backend changes need their own
build system. `--timeout 60` sets the per-process timeout in seconds.
Fixed passes record observed stability without requiring it.

The root hash identifies only that file, not a frozen snapshot of every included
file. A changed root at the end of an otherwise successful build makes the check
fail; the helper preserves the author's new edit. Changes that are reverted between
these two checks and changes to included files are not detected. Verify PDF content
visually and preserve the source diff separately.

Earlier helper versions used a fixed `document` basename. Use `--jobname document`
when a downstream process expects those filenames.

Command semantics: [Web2C manual](https://www.tug.org/texinfohtml/web2c.html),
[Biber manual](https://tug.ctan.org/biblio/biber/base/documentation/biber.pdf).
