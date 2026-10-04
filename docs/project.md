# Inspect a manuscript project

The project doctor reads a complete source tree and reports literal dependency
edges, source fingerprints and diagnostics with file/line locations. It does
not edit or compile the manuscript.

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend bibtex
als project init path/to/paper --main main.tex --engine pdflatex --backend bibtex --passes 3
als --json project check path/to/paper --output work/inspection-01.json
als project check path/to/paper --output work/inspection-02.json --html work/inspection-02.html
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

Main files must be existing UTF-8 `.tex` sources outside reserved generated
directories; invalid settings are refused before creating configuration. UTF-8
with a BOM is accepted. The configuration hash is retained in an inspection.

## Open an offline inspection report

Open the generated `.html` file in your browser. It contains issue counts,
source locations and next steps, dependency resolutions, selected tools,
input hashes and the complete evidence. It needs no network connection or
JavaScript. Missing dependencies, unverified checks and `includeonly` exclusions
have distinct states; the report explicitly says that compilation has not run.

Use `--html-language zh` for Chinese interface labels. Diagnostic messages stay
the same as the JSON record. HTML and JSON filenames must be distinct and new;
an existing destination is refused before either is written. When they share a
directory, HTML links to the JSON by an escaped relative filename. HTML needs
`.html` or `.htm`; keep generated reports together when sharing them.

The [complete manuscript runner](../examples/full-paper/README.md) also exports
`inspection-before.html` and `inspection-after.html`, alongside its build/PDF
review. See the [Chinese project guide](project_CN.md).

## What is checked

The doctor selects a unique `documentclass` root or asks for an explicit root
when several exist. Explicit `--main` or configured roots inspect their reachable
sources without parsing unrelated `.tex` files. `root_selection` and
`root_candidate_scope` record whether candidates cover the full inventory or
only the selected root.

`inputs` contains reachable dependency inputs. `observed_files` contains every
file read in this inspection, including other `.tex` sources used for automatic
root selection, the parsed configuration and its validated main source. Even an ambiguous-root `blocked`
report retains these fingerprints and rechecks the observed files before return.
HTML displays both lists separately. Fingerprints bind parsed bytes; they do not
lock concurrent edits or authenticate authors.

It follows braced and ordinary unbraced `input`, multiline literal arguments,
quoted filenames, `include`, literal `includeonly`, graphics, bibliography
files, local bibliography styles, and supplied local classes/packages, including
`LoadClass[WithOptions]` and `RequirePackageWithOptions`. Excluded includes are
recorded as skipped without testing their existence; `input` is not excluded.
Literal cycles are blocked, while repeated source execution is unverified.
Repeated package loading does not rescan the same package.

Missing assets, unknown citation/reference keys and duplicate
labels include their source locations. It checks selected tool availability,
`fontspec` versus pdfLaTeX, explicit bibliography backend disagreement, and
simultaneous `natbib`/`biblatex` loading.

Literal inputs are visited in source order, so declarations in an input affect
the following commands. `graphicspath` replaces earlier paths. Extension search
precedes directory search, and literal `DeclareGraphicsExtensions` overrides the
default common PDF-engine subset. This behavior is based on the
[LaTeX graphics source](https://github.com/latex3/latex2e/blob/develop/required/graphics/graphics.dtx).
An unsupported dynamic declaration makes subsequent graphics lookup unverified
instead of reusing an older path as if it were current. Exact driver rules,
automatic conversions and TeX search configuration still require actual builds.

## Literal examples and incomplete regions

Scanning follows source order: a commented verbatim opener cannot mask later
live input. Escaped percent signs remain literal; the control symbol `\\` does
not create a second command. `verb`/`verb*` supports horizontal spaces before
the delimiter and numeric delimiters. Literal `verbatim`/`verbatim*`, `lstlisting`
and `minted` regions are masked while preserving offsets, line numbers and CRLF.
Inline behavior is based on the
[LaTeX kernel source](https://github.com/latex3/latex2e/blob/main/base/ltmiscen.dtx).
The `verb*` star must immediately follow the command; after a space it becomes
the literal delimiter instead. Tabs before an inline delimiter are explicitly
unverified because their tokenization depends on the kernel; masking is approximate.

An unfinished inline verb masks only its current line. An environment without
a literal end marker masks the remaining source. Both emit located unverified
diagnostics, so absent dependency signals cannot establish completeness. Category
code changes, custom verbatim environments and package escape/termination options
are not interpreted. An actual build remains necessary. Source/configuration
reads are bounded to 2,000,000 bytes, including files growing after inventory.

Comments and supported literal regions are excluded from these checks. Project
paths stay inside the selected root; symlinks are refused. Inputs outside this
boundary or dynamic macro arguments are reported as unverified. File hashes bind
the actual parsed bytes; changes during inspection are refused.

Inventory traversal prunes `.git`, `work`, `dist`, `build`, `.als-runs`,
`__pycache__`, `evaluation-runs`, `.venv`, `venv` and `node_modules` before descent.
These trees cannot supply automatic root candidates. Keep manuscript sources
outside generated directories so the separate source-review inventory includes
them. An explicitly referenced local dependency can still be followed within
the project boundary.

The parser handles simple non-nested braced command arguments. It does not
expand macros, evaluate grouping/conditionals, resolve system package/class
internals, or reproduce TeX's complete search path. Local literal declarations
are followed; class/package macro execution is not emulated. Excluded chapters'
old auxiliary files and their generated label definitions are not evaluated.
Consequently a missing literal target can require conditional/search-path
review, and a clean report can still miss build errors. Preserve unknown keys
until the author supplies their intended targets.

`ready` means no supported static issues were found; `needs-review` includes
warnings/unverified checks; `blocked` includes errors and returns exit 1.
Invalid configuration/preconditions return 2. Use the separate
[build evidence guide](../latex-rescue/references/build-check.md) for actual
compilation and the [review guide](review.md) for content/PDF inspection.
