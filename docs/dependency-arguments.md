# Read dependency arguments as complete declarations

[简体中文](dependency-arguments_CN.md) · [Project inspection](project.md) · [Change review](review.md)

A protected closing bracket inside an option value must not hide a filename:

```tex
\includegraphics[note={literal ] text},width=1cm]{figures/plot}
```

The inspector retains the complete option list and resolves `figures/plot`.
It does **not** validate or execute the `note` key. A native build still needs
a package that actually defines that key. Options that contain `\cite`, `\ref`
or `\input` are not counted as body commands; neither are commands inside
dynamic filename arguments. This prevents phantom references, without proving
whether a macro will execute those contents at runtime.

| Declaration | Literal reader coverage |
|---|---|
| `input` | One braced, bare or double-quoted filename |
| `include`, `bibliographystyle` | One braced filename |
| `includeonly`, `bibliography` | One braced name list; empty `includeonly` excludes all includes |
| `includegraphics` | Optional star, up to two balanced optional groups, one braced filename |
| `addbibresource` | Up to one balanced optional group, one braced filename |
| `graphicspath` | One complete outer group containing literal braced directories |
| `DeclareGraphicsExtensions` | One braced extension list; the inspector separately checks the extension syntax |

The [LaTeX Project graphics guide](https://ctan.math.illinois.edu/macros/latex/required/graphics/grfguide.pdf),
section 4.4, documents the key-value and classic two-optional-argument interfaces,
including the star. The scanner records the argument form; it does not infer
the active driver, option validity or package behavior.

Inspection adds `dependency_inventory`; review adds
`dependency_inventory.before/after`. Each located row has
`file`, `line`, `command`, `value`, `options`, `starred`, `supported` and `issue`.
The bilingual offline table separates declarations from resolved dependencies.
A supported declaration can still point to a missing, dynamic or outside-project
resource. Canonical path lookup and source fingerprints remain separate checks.

Malformed, dynamic, nested filename and unexpected optional/star syntax stay
unverified. `dynamic-reference` remains the project diagnostic;
`dependency-unverified` is the review source issue. Reading an unfinished or
overly deep group conservatively stops later command observations in that file.
At most 128 nested braces and 32 optional groups are read; only the documented
zero/one/two-option forms are supported. These are parser bounds, not TeX limits.

Schema numbers and CLI exit semantics are unchanged; reports without the
optional inventory field still render. Static scanning does not expand macros,
evaluate conditions/group scope or replace a real build. Existing UTF-8,
source-size, project-root and sealed-delivery limits still apply.

Native synthetic controls compare the literal inventory with actual builds under
pdfLaTeX, XeLaTeX and LuaLaTeX, use a deliberately inert local option key, verify
quoted chapter/graphics recorder entries, and compile the classic interface with
both `graphics` and `graphicx`. Installed wheel and rebuilt-source checks repeat
the scanner/report flow outside the checkout.
