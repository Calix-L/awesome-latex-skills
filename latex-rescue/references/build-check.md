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
  Its recorder file is retained as `logs/engine-01.fls` when generated.
  Evidence lives in `logs/` to avoid collisions with the root's output basename.
- `logs/bibliography.txt` / `logs/bibliography.blg` when a backend is requested.
- `build-report.json` (schema 3): root path and starting SHA-256, job name, selected tools, commands,
  working directories, process exit codes, timeout status, evidence filenames,
  per-step diagnostics, failed/diagnostic step names, local input observations,
  auxiliary stability, rerun/unresolved-reference status, root-source change
  detection, failure reason, and verified PDF filename.

The engine runs from the root document's directory with shell escape disabled.
The backend receives that directory in its bibliography/style search paths.
Local `.tex` subdirectories are mirrored as empty output directories so ordinary
nested `\include{chapters/one}` auxiliary files can be written. No source is copied.
The helper does not edit source, reuse existing output, or enable shell escape.
TeX itself still reads project files; this build wrapper is not a sandbox.

## Interpret the result

Exit **0** requires all requested processes to finish successfully, no recognized
errors in the selected engine/backend logs, and a newly produced PDF header from the final
pass. The previous pass's generated PDF is removed before each next engine pass.
It can still have
undefined citations/references, layout warnings, or rerun requests. Diagnostics
recognize common `!`, file-line, LaTeX/package/class warning, and box messages,
plus common BibTeX file/syntax errors and warnings and Biber ERROR/WARN messages.
Read complete logs for wrapped messages and unrecognized diagnostics.

Each `steps` entry names its tool, log/transcript, recorder, and diagnostics with
one-based `log_line` positions in the retained log (or transcript when no native
log exists). On process failure, top-level `diagnostics` comes from `failed_step`,
including a failed bibliography step; otherwise it comes from the final engine
pass. `diagnostic_step` identifies that source. The CLI prints the failed step's
evidence path and first recognized error. Rerun/unresolved-reference flags still
describe the latest engine log, not a bibliography log.

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

## Local input provenance and limits

`local_inputs` lists resolved files under the root document's directory that the
engine recorder names as `INPUT`, excluding the build directory and recorded
`OUTPUT` paths. It includes recorded local chapters, styles and graphics; unused
project files and external TeX distribution files are not fingerprinted. Paths
are relative to the project and deduplicated, including filenames with spaces.

Each file has `observations` with the engine step, SHA-256, byte size and any
read error. Fingerprints are taken **after** each recorded pass and checked again
at the end (`step: "final"`). `input_tracking.recorder_steps` identifies available
recorders; `changed` and `unreadable` identify inconsistent or missing local
inputs. An otherwise successful build fails if either list is nonempty. The
helper preserves the author's current files; it never restores an earlier copy.
Absent recorder files yield no input observation for that pass, and do not by
themselves fail the basic build check. Inspect recorder coverage before relying
on the manifest.

This is observed provenance, not a frozen project snapshot. It cannot detect an
edit before a file's first observation, an edit reverted between observations,
or inputs the engine does not record. BibTeX/Biber's separately read `.bib`/`.bst`
files, remote resources and external fonts/packages are outside this manifest
unless also read and recorded by the engine in the local project scope. Preserve
those versions separately for reproduction. A fingerprint is not an authenticity
or content-correctness guarantee.

The root additionally has a starting hash taken before creating output and an
end-of-build comparison, including ordinarily failed process runs. A changed root
makes an otherwise successful check fail. Interruptions or evidence I/O failures
can leave the change check unverified. Verify PDF content visually and preserve
the source diff separately.

Earlier helper versions used a fixed `document` basename. Use `--jobname document`
when a downstream process expects those filenames.
Schema 3 changes the top-level diagnostic source on backend failure; consumers
should use `diagnostic_step` and the referenced step's log/transcript, rather than
assuming every diagnostic belongs to the final engine log.

Command semantics: [Web2C manual](https://www.tug.org/texinfohtml/web2c.html),
[Biber manual](https://tug.ctan.org/biblio/biber/base/documentation/biber.pdf).
