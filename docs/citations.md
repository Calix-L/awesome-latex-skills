# Check citation commands and changed keys

[中文](citations_CN.md) · [Project inspection](project.md) · [Change review](review.md)

Use the same source scanner to locate citations and to catch changed keys during
manuscript editing. It understands common LaTeX, natbib and biblatex forms:

| Form | Examples | Literal arguments checked |
|---|---|---|
| Single group | `\cite`, `\citep`, `\Citet`, `\parencite`, `\textcite`, `\autocite`, `\footcite` | Up to two bracketed notes followed by `{key,key}` |
| Multiple groups | `\cites`, `\parencites`, `\textcites`, `\autocites`, `\footcites` | Up to two global `(notes)`, then every `[note][note]{key,key}` group |
| Author/title/year and related forms | `\citeauthor`, `\citetitle`, `\citeyear`, `\fullcite`, `\notecite` | Literal key group; notes are not keys |
| Bibliography selection | `\nocite{key}` / `\nocite{*}` | Keys retained; only `nocite` treats `*` as the all-entries selector |
| Prose wrapper | `\citetext{prose; \citealp{key}}` | Prose is not a key; nested citation commands are scanned |

The exact supported command set is in [citation_lexer.py](../scripts/citation_lexer.py).
Source star/capital variants are retained, without proving that a particular
package/style implements them. Optional notes may contain brace-protected
closing delimiters and escaped control symbols. Comments and supported verbatim
examples stay outside the inventory. Citation arguments are scanned iteratively,
with a maximum brace depth of 128 inside the inspector's bounded UTF-8 sources.

## Inspect a project

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend biber --bundle work/citation-check
als verify inspection work/citation-check
```

Open `work/citation-check/report.html`. Each citation row shows its key, command,
star variant, argument-group index and **command opening line**. Multiline groups
share that command line. Missing bibliography keys are reported there, including
keys in the second or later multicite group. Matching is exact and case-sensitive.
The schema-1 JSON adds `citation_inventory`; parsed bibliography headers remain
in `bibliography_entries`. The inventory is bound to the observed source hashes
and sealed along with the HTML/JSON report.

## Review a key change

```sh
als review --before path/to/original --after path/to/candidate --output work/citation-review
als verify review work/citation-review
```

Changing only the second key in `\parencites{known}{old}` to `new` now raises a
`reference_keys` signal, even when all numbers and formulas stay the same. Counts
retain repeated keys; merely reordering the same keys within the same command
does not invent a key-change signal. The review adds both source versions'
`citation_inventory` and expandable tables. Review scans inventoried `.tex`,
`.sty` and `.cls` files, including inactive files; inspection instead scans the
selected root's literal dependency graph. Source-only review does not run TeX.

## Incomplete syntax stays visible

Malformed notes, unbraced/dynamic/nested/empty keys, excessive note counts and
unsupported special forms such as `\volcite` or `\citefield` produce located
`citation-unverified` findings. Complete earlier multicite groups remain in the
inventory, but a finding means that inventory may be incomplete. Custom
`cite...` names are not assumed to use the ordinary key grammar.

This is a literal scanner. It does not expand macros, evaluate definitions,
conditionals, active catcodes, refsections, aliases, commands inside notes,
custom commands with unrelated names, manual `\bibitem` definitions or external
bibliography resources. It does not validate command/style availability, note
semantics, fields, citation ordering or whether a cited paper supports a claim.
Use the configured native backend and inspect the actual PDF separately.

Grammar sources reviewed for this coverage: [biblatex manual, §3.9](https://ctan.math.illinois.edu/macros/latex/contrib/biblatex/doc/biblatex.pdf)
and [natbib manual, §2.3–2.5](https://mirrors.ctan.org/macros/latex/contrib/natbib/natbib.pdf).
