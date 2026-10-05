# Inspect class/package options and backend declarations

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend biber --bundle work/package-inspection
als verify inspection work/package-inspection
```

The chosen backend remains your explicit CLI/configuration setting. Inspection
compares it with complete, direct literal biblatex assignments; it never changes
the setting or selects a tool from a package default.

## Balanced loader arguments

`documentclass`, `LoadClass`, `usepackage` and `RequirePackage` support one
optional option list, a literal braced name and an optional trailing minimum
release date. Package loaders support comma-separated names; class loaders
require a single name. `LoadClassWithOptions` and `RequirePackageWithOptions`
accept the name/date form; their forwarded options are not evaluated.

Nested braces protect `]` and commas in options. Commands inside the option
argument or trailing date are consumed with that argument and are not treated as
separate loads, inputs or citations. Comments and supported verbatim regions keep
their existing masking rules; command positions retain their opening source line.
Macro-generated/nested/empty names, multiple initial optional lists, starred
loaders, malformed groups or more than 128 brace levels produce located
`package-unverified` findings instead of guessed dependencies.

This syntax improvement does not validate whether a class/package accepts an
option, whether a minimum date is satisfied or whether a declaration executes.

## Exact backend observations

| Direct biblatex option | Inspection behavior |
|---|---|
| `backend=biber` or `backend={biber}` | Compare complete value with the chosen tool |
| `backend=bibtex` or `backend={bibtex}` | Compare complete value with the chosen tool |
| `note={backend=biber},backend=bibtex` | Compare only the top-level `backend` assignment; other option validity remains unchecked |
| `mybackend=biber` | Not a backend assignment |
| `backend=bibtex8` | Explicitly unverified; never treat it as `bibtex` |
| `backend=\macro`, a bare `backend`, or an empty value | Explicitly unverified |
| `backend=biber,backend=bibtex` | Retain both; mark precedence unverified |
| No direct assignment / forwarded or global options | No default or effective backend inferred |

`bibtex8` is a distinct backend documented by biblatex. This project's build
interface supports `biber` and `bibtex`; the diagnostic does not add support for
another tool. Unsupported values produce `backend-options-unverified`; a complete
supported assignment differing from an explicitly selected backend produces
`backend-mismatch` at the declaration's actual file/line. Repeated identical
assignments preserve their occurrence count; no conflicting override is chosen.

## Reports and source review

Schema-1 inspection adds `package_inventory` with `file`, `line`, loader
`command`, package/class `name` and masked literal `options` (including brackets,
or empty when absent). Direct biblatex loader rows add `backend_options` and
`backend_options_complete`, describing only the observed argument. An empty list
does not establish the effective runtime backend. Native control files remain
the evidence for actual build behavior.

Schema-1 review adds `package_inventory.before/after` and expandable bilingual
tables. It inventories all supported `.tex`, `.cls` and `.sty` sources, including
inactive files; inspection follows the chosen root's literal dependencies.
Malformed loaders and unsupported/conflicting backend arguments remain visible
for unchanged review sources. A changed supported option remains visible in the
source diff and before/after table; no semantic content score is inferred.
Legacy reports without these fields still render.

Project configuration requires integer `"schema": 1`; `true`, `1.0`, `"1"` and
missing values are rejected before validating/reading the configured main source.
Existing engine, backend and pass settings are unchanged.

The syntax basis is the [pinned LaTeX kernel class/package implementation](https://github.com/latex3/latex2e/blob/b604e2e24e76d12f9aeb0bb81e017f29b5ddd473/base/ltclass.dtx)
and [biblatex manual, §3.1.1 and §3.16](https://ctan.math.illinois.edu/macros/latex/contrib/biblatex/doc/biblatex.pdf).
Native regressions compile synthetic nested-option loaders and both braced
backend choices; static checks do not expand macros, resolve forwarded/global
options, evaluate conditionals or prove package/style compatibility.

[中文指南](package-options_CN.md) · [Project workflow](project.md) · [Source review](review.md)
