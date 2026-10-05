---
name: latex-rescue
description: Diagnose and repair LaTeX build failures in local projects or supplied logs. Make minimal source fixes, preserve scientific content and reference keys, and report actual build evidence and unresolved errors.
metadata:
  version: "1.22.0"
---

## Purpose

Repair the requested project with the smallest change that addresses the actual
failure. Compilation success does not establish mathematical correctness.

## Establish the failing build

- For a pasted error, give a diagnosis using the supplied context. Request source
  or logs only when they are needed to distinguish plausible fixes; a project
  directory is not required for a useful diagnosis.
- For a local project, identify its root document from the build command,
  configuration, magic comments, and `\documentclass`. A file named `main.tex`
  is a candidate, not proof that it is the root. Resolve ambiguous roots before editing.
- Respect the engine, auxiliary/output directories, bibliography backend, and
  any custom build steps. `fontspec` requires XeLaTeX or LuaLaTeX. Check
  `biblatex`'s backend option rather than assuming Biber in every project.
- Reproduce the failure with the existing build command where available. Retain
  exit codes and the final engine/backend logs. A stale PDF is not build evidence.
  Missing tools or project files mean compilation remains unverified.

For manual builds, use the actual root and engine, for example:

```sh
pdflatex -no-shell-escape -interaction=nonstopmode -file-line-error main.tex
```

Use the shell's own exit-status handling when capturing output. Bash pipelines
need `set -o pipefail`; do not assume Bash syntax works in PowerShell. Do not
enable shell escape merely to silence an error; follow the project's actual
requirements and the user's execution permissions.

## Diagnose and repair

Read the first causal error, its source context, and subsequent diagnostics.
File-line diagnostics may appear as `file.tex:line:` rather than starting with `!`.
Undefined references and overfull boxes are generally warnings, not syntax failures.

Consult only the relevant resources:

- [Error catalog](references/error-catalog.md): known typos, missing packages,
  encoding, references, and environment errors.
- [Package conflicts](references/package-conflicts.md): option clashes or
  competing definitions; preserve the official template's package choices.
- [Debug workflow](references/debug-workflow.md): cascading errors and failures
  that remain after an initial contextual fix.

Check whether an apparently misspelled command or environment is user-defined
before replacing it. Inspect balanced argument structure rather than counting
all braces or dollar signs across comments, escaped characters, and verbatim.
Prefer the causal fix over patching every downstream diagnostic.

Preserve equation meaning, table cells, citation and label keys, bibliography
records, file paths, metadata, comments, and literal/code environments. Syntax
repairs inside an equation are possible when their meaning is unambiguous;
flag alternative mathematical interpretations instead of choosing one to compile.
Never delete or disable content, invent a missing reference, or edit an official
`.sty`, `.cls`, or `.bst` file to make the build pass.

Use a temporary copy for diagnostic isolation. Keep a reviewable source diff so
an unsuccessful edit can be reverted without discarding the author's other work.

## Verify and report

Rebuild after a meaningful repair batch. Prefer the configured `latexmk` mode
when available; otherwise run the selected engine, required BibTeX/Biber step
after auxiliary files exist, and further engine passes to settle references.
Do not invoke a bibliography backend on projects that do not use one.

For a conventional root document without custom build steps, the bundled
[build checker](references/build-check.md) records fresh-output evidence across
engine/backend passes. Run `scripts/check_build.py` with the actual root,
selected engine/backend, and a new `--output` directory. Preserve configured
build systems for projects beyond that helper's scope.
Its default job name follows the root file. Use `--until-stable` for bounded
auxiliary settling and `--require-resolved` when unresolved references must fail
the check; these flags do not decide missing reference targets for the author.
The report retains recorder-based local input fingerprints and identifies the
failed engine/backend step. These observations do not freeze project inputs or
cover every bibliography/system resource; inspect the guide's provenance limits.
When local backend resources need consistency checks, select them explicitly
with repeated `--watch-input` options as described in that guide; selection does
not establish which resources the backend actually read.

Read the final logs and inspect the resulting PDF when rendering tools are
available. Report build failure separately from unresolved references, duplicate
labels, and layout warnings. If a change introduces regressions, revert that
change; if the same failure repeats, change the diagnosis. After three repair
attempts without progress, report the blocker and the evidence needed to proceed.

Deliver the changed files and concise reasons, engine/backend/build command,
observed exit result, log/PDF locations, visual-check status, remaining warnings,
and unresolved author decisions. For Overleaf-only material, distinguish a
proposed repair from one verified through a fresh Overleaf or local build.

Use `latex-polish` or `latex-fmt` only if the user also needs prose editing or a
format conversion and the corresponding skill is available.
