# Locate labels and check cross-reference changes

[中文](cross-references_CN.md) · [Project inspection](project.md) · [Manuscript review](review.md)

Find missing or repeated targets without changing the manuscript:

```sh
als project check path/to/paper --main main.tex --engine pdflatex --bundle work/label-check
als verify inspection work/label-check
```

Open `work/label-check/report.html`. The expandable **Labels and cross-reference
targets** tables retain keys and source locations. A reference shows whether the
selected root's literal dependency graph contains zero, one or multiple
definitions, their count and the first definition's location. Forward references
are resolved after that graph has been scanned. Every later duplicate definition
gets its own diagnostic at its actual file/line, naming the first definition.

## Supported source forms

| Form | Examples | Interpretation |
|---|---|---|
| Definition | `\label{key}`, cleveref's `\label[type]{key}` | One literal key; the optional type is consumed without interpretation |
| Single target | `\ref`, `\eqref`, `\pageref`, `\autoref`, `\autopageref`, `\nameref`, `\Nameref`, cleveref's name commands | One braced key; commas remain part of that key |
| List | `\cref`, `\Cref`, `\cpageref`, `\Cpageref`, `\labelcref`, `\labelcpageref` | A comma-separated list of keys |
| Range | `\crefrange`, `\Crefrange`, `\cpagerefrange`, `\Cpagerefrange` | Two braced endpoint keys, with distinct argument roles |
| Label link | `\hyperref[key]{text}` | The bracketed key is the target; text is not a target; nested supported commands remain visible |

The exact command set is in [reference_lexer.py](../scripts/reference_lexer.py).
Source star/capital variants are retained, without proving package/style
availability. Starred `label`, `eqref`, `Nameref` and `hyperref` forms are explicitly
unverified instead of supplying guessed targets. Labels and single-target keys containing commas remain whole;
cleveref's list grammar alone splits comma-separated targets. Cleveref itself
does not support commas inside label names. Matching is exact, including case.
Locations point to command opening lines, even for multiline arguments.

Comments, escaped backslashes, supported inline verbatim and literal examples
stay out of these inventories. Shared argument reading is iterative and bounded
to 128 brace levels within the project's existing UTF-8 size limits. Malformed,
dynamic, nested/empty targets and unsupported optional syntax produce located
`reference-unverified` findings. Complete earlier range endpoints remain in the
inventory, but any such finding means that inventory may be incomplete.
The older four-braced-argument `\hyperref` syntax is explicitly unverified.

## Review target edits and swapped endpoints

```sh
als review --before path/to/original --after path/to/candidate --output work/label-review
als verify review work/label-review
```

Changing `\hyperref[old]{Same text}` to `\hyperref[new]{Same text}` produces a
`reference_keys` content signal. Swapping `\crefrange{a}{b}` to
`\crefrange{b}{a}` also produces a signal, even though the key set is unchanged:
the review preserves each endpoint's argument role. List-only reordering keeps
the same key counter; repeated keys retain their multiplicity.

Schema-1 inspection adds `label_inventory` and `reference_inventory`. Schema-1
review adds both fields for `before` and `after`, alongside expandable tables.
Review scans inventoried `.tex`, `.sty` and `.cls` files, including inactive
files, so its inventories intentionally make no root-level resolution claim.
Unsupported syntax appears in `source_scan_issues`, even in unchanged files.
Old HTML inputs without these fields still render. Existing source fingerprints
and bundle checksums bind the new inventories to the same observed evidence.

## What a definition count means

Counts describe literal source observations, not the target that TeX actually
used. Macros, definitions, conditionals, repeated execution, active category
codes, external/generated labels (`xr` and similar), package/style semantics,
counter types, label placement relative to captions and correctness of the
referenced claim remain unchecked. Repeated inputs are scanned once and retain
the existing repeated-source finding; excluded includes do not provide labels.
This scanner does not renumber, rename or repair a target. Compile with the
actual project packages and inspect the PDF to confirm target behavior.

Grammar sources reviewed for this coverage: [cleveref §4 and §6](https://tug.ctan.org/macros/latex/contrib/cleveref/cleveref.pdf),
[hyperref §6](https://ctan.math.illinois.edu/macros/latex/contrib/hyperref/doc/hyperref-doc.pdf)
and [nameref's documented frontend](https://ctan.math.illinois.edu/macros/latex/contrib/hyperref/doc/nameref.pdf).
