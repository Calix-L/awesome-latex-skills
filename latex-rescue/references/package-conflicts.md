# Package Conflicts

Determine the loaded class, packages, options, and versions from the source and
log. Classes can load packages implicitly. Preserve the official template's
choices; a newer package or broader feature set is not a reason to replace them.

## Common Interactions

| Packages | What to check | Contextual resolution |
|---|---|---|
| `hyperref`, `glossaries` | Hyperlinked glossary support | Load `hyperref` before `glossaries` when using it; follow the glossary manual and class instructions |
| `hyperref`, `cleveref` | Reference patches | Load `cleveref` after `hyperref`, subject to documented class/package requirements |
| `varioref`, `cleveref` | Enhanced references | They can coexist; `varioref` precedes `cleveref` |
| `subfigure`, `subfig`, `subcaption` | Incompatible interfaces and caption rules | Retain the interface required by the class; migrate source calls only if authorized and verify captions/references |
| `cite`, `natbib` | Competing citation interfaces | Retain the citation system prescribed by the template; do not choose by feature count |
| `natbib`, `biblatex` | Different bibliography systems | Choose the configured/required system; align source commands and backend while preserving records and citation meaning |
| `algorithm`, `algorithm2e` | Both can define an algorithm float | Choose a compatible float interface and preserve content/numbering |
| `algorithmic`, `algorithmicx`, `algpseudocode` | Algorithm body syntax and definitions | Check the actual syntax; sharing a purpose does not prove a conflict with an outer float |
| `amsmath`, `mathtools` | Options and loading | `mathtools` extends and loads `amsmath`; loading both is not inherently a conflict |
| `xcolor`, `color` | Already loaded support/options | Inspect first loading and options before changing anything; avoid incompatible reloads |
| `todonotes`, `xcolor` | Color option clashes | Pass supported required options before the first load; retain the template's color model |
| `listings`, `minted` | Code environments and external tooling | Presence alone is not an error; resolve the actual diagnostic and keep source code literal |
| `fancyhdr`, `titlesec` | Class-specific page styles | Reproduce the conflict and inspect class guidance before substituting layout packages |
| `pdfx` and metadata/hyperlink packages | Required archival format | Keep required PDF/A/PDF/X constraints; follow documented setup and verify output separately |
| `microtype`, `fontspec` | Engine-dependent typography | They can coexist; supported microtype features differ by engine |
| `csquotes`, `babel` | Language-aware quotations | They are normally complementary; inspect options and language support |

## Diagnose an Option Clash

Find the first loading point, including class files, before changing load order.
For a supported option required by this project, pass it before that first load:

```latex
% Example only: use the option actually required by the project.
\PassOptionsToPackage{dvipsnames}{xcolor}
\documentclass{article}
\usepackage{xcolor}
```

`\PassOptionsToPackage` does not make incompatible options or engines compatible.
Do not edit an official class/style file to suppress the clash. Explain when the
class's requirements cannot be satisfied with the proposed feature.

## Diagnose a Duplicate Definition

Find both definitions and the source calls that depend on them. Test a candidate
change in a temporary copy. Do not blindly undefine a command, rename an environment,
or remove a package: the result may compile while changing caption numbers,
citation punctuation, cross-references, or algorithm semantics.

After a minimal correction, run the project's required engine/backend workflow
and inspect the affected features in the PDF. Keep unrelated package choices.

## Font and Bibliography Setup

Modern pdfLaTeX accepts UTF-8 source by default. `fontenc` selects output font
encoding; it is not a general cure for source decoding or missing glyphs.
XeLaTeX/LuaLaTeX with `fontspec` use Unicode fonts. Use the engine and fonts required
by the project rather than copying a universal preamble.

For `biblatex`, inspect the configured `backend=` option rather than assuming
Biber. When changing citation systems as part of an authorized template migration,
align commands, style, resources, and build steps together. Successful compilation
alone does not establish equivalent citations or venue compliance.

## Official References

- [Glossaries manual](https://tug.ctan.org/macros/latex/contrib/glossaries/glossaries-user.html): hyperlink setup and package loading.
- [Mathtools](https://ctan.org/pkg/mathtools): extensions to `amsmath`.
- [LaTeX UTF-8 default](https://www.latex-project.org/news/2018/04/10/issue28-of-latex2e-news-released/): input encoding versus font setup.
- [BibLaTeX](https://ctan.org/pkg/biblatex): bibliography system and backend options.

Use the manual matching the installed package version, obtainable through `texdoc`
when available. There is no preamble order that guarantees conflict-free output.
