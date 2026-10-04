# Review formula changes before accepting manuscript edits

[中文](math-review_CN.md) · [Complete review workflow](review.md) · [Documentation](README.md)

A candidate can compile successfully after `x+y` becomes `x-y`. Review the
formula change separately from build success, even when numbers and citation
keys remain unchanged.

```sh
als review --before path/to/original --after path/to/candidate --output work/formula-review
als verify review work/formula-review
```

Open `work/formula-review/report.html`. **Math environment changes** lists added
and removed literal formula values. **Located math environments** shows original
and candidate source filenames, opening/closing line numbers and expandable
formula text side by side. This works without TeX, PDF libraries or a model.
Attach actual build reports using the [review workflow](review.md) to include
their logs and successful PDF pages.

For example, these edits now generate a review signal:

```tex
% Original
\begin{equation}x+y\end{equation}
% Candidate
\begin{equation}x-y\end{equation}
```

## Coverage and interpretation

| Checked literally | Coverage |
|---|---|
| Basic environments | `math`, `displaymath`, `equation`, `eqnarray` |
| AMS display environments | `align`, `alignat`, `flalign`, `gather`, `multline` |
| Unnumbered variants | Starred versions of the listed display environments, except `displaymath` |
| Nested content | Entire outer body, including `split`, `aligned`, matrices, argument counts, labels, tags and text |
| File types | `.tex`, `.sty`, `.cls`, including unchanged files and added/removed sources |

Environment names and bodies are compared exactly after the shared scanner
masks comments and supported verbatim forms. Whitespace changes can also flag
review. Identical spans retain their occurrence counts; moving or reordering
identical formulas alone does not add a formula-content signal. This does not
detect an order-dependent change of meaning. Positions remain in the inventory.
Existing delimited-math signals (`$`, `$$`, `\(`, `\[`) remain available.

An unclosed span, mismatched nested close, orphan supported close or dynamic
inner environment name produces a located `source_scan_issues` entry.
Malformed/dynamic spans never supply complete formula values. Later balanced
spans can still be inventoried after recovery at the outer close. Check actual
TeX logs before accepting such a source.

The scanner works within each file under ordinary category codes. It does not
expand macros, evaluate definitions, conditions or groups, join environments
across `input` files, recognize custom outer math environments, validate TeX
grammar, or decide mathematical equivalence. A matched span is literal evidence,
not proof that it executes or compiles. Scientific intent remains an author
decision. Nested spans are retained once inside their outer body, rather than
counted as separate environment formulas.

## Machine evidence and sharing

Schema-1 reviews add `math_environment_inventory.before/after`, each containing
`file`, `environment`, `line`, `end_line` and masked literal `content`.
`math_environment_scope` records supported names and interpretation.
Changed files can add `content_audit[].math_environments` with removed/added
literal values and multiplicities. Previous report fields and schemas remain.

Keep the review directory intact for offline transfer; `verify review` checks
its stored bytes independently of the original project paths. Editing the report
intentionally invalidates its initial integrity manifest.

For intended AMS environment usage, consult the primary
[AMS/LaTeX Project user guide, sections 3.2–3.7](https://texdoc.org/serve/amsldoc.pdf/0).
The tool's coverage is narrower than the full package language.
