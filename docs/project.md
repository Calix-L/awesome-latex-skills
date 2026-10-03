# Inspect a manuscript project

The project doctor reads a complete source tree and reports literal dependency
edges, source fingerprints and diagnostics with file/line locations. It does
not edit or compile the manuscript.

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend bibtex
als project init path/to/paper --main main.tex --engine pdflatex --backend bibtex --passes 3
als --json project check path/to/paper --output work/inspection-01.json
als build --project path/to/paper --output work/build-01 --require-resolved
```

Without an installed CLI, replace `als` with `python scripts/als.py`. Relative
arguments resolve from the caller's directory. Project dependency lookups use
the main document's directory, matching the build helper's working directory.

`project init` creates a new `.als.json` in the selected project:

```json
{
  "schema": 1,
  "main": "main.tex",
  "engine": "pdflatex",
  "backend": "bibtex",
  "passes": 3
}
```

It refuses to overwrite existing configuration. Edit the file deliberately to
change the selected root/engine/backend. Use null for a project without a
bibliography backend. Explicit `build --engine/--backend/--passes` options
override configured values. Builds always require a fresh output directory.

## What is checked

The doctor selects a unique `documentclass` root or asks for an explicit root
when several exist. It follows ordinary braced `input`/`include` paths,
literal graphics and `graphicspath`, bibliography files, and supplied local
classes/packages. Missing assets, unknown citation/reference keys and duplicate
labels include their source locations. It checks selected tool availability,
`fontspec` versus pdfLaTeX, explicit bibliography backend disagreement, and
simultaneous `natbib`/`biblatex` loading.

Comments and common verbatim forms are excluded from these checks. Project
paths stay inside the selected root; symlinks are refused. Inputs outside this
boundary or dynamic macro arguments are reported as unverified.

The parser handles simple non-nested braced command arguments. It does not
expand macros, evaluate conditionals, interpret unbraced input syntax, resolve
system package/class internals, or reproduce TeX's complete search path.
Consequently a missing literal target can require conditional/search-path
review, and a clean report can still miss build errors. Preserve unknown keys
until the author supplies their intended targets.

`ready` means no supported static issues were found; `needs-review` includes
warnings/unverified checks; `blocked` includes errors and returns exit 1.
Invalid configuration/preconditions return 2. Use the separate
[build evidence guide](../latex-rescue/references/build-check.md) for actual
compilation and the [review guide](review.md) for content/PDF inspection.
