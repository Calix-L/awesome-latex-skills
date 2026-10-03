# Formatting Rules

Apply the verified author kit for the requested venue, year, track/article type
and stage. These suggestions help diagnose layout; they do not override a kit.
A compiling PDF is not evidence of submission compliance.

## Fonts

Preserve the kit's text/math fonts, size and engine requirements. Do not shrink
text or substitute fonts to meet a page limit. If a font is required, check that
the actual environment supplies it; “Times New Roman” is not universally installed.

`fontspec` is for XeLaTeX/LuaLaTeX. A supplied pdfLaTeX template may use a
different font package and must not be converted merely to use a preferred font.
For a document without mandatory styling, choose an available setup and record
it as a choice. See the [fontspec documentation](https://latex3.github.io/fontspec/).

## Margins and Spacing

Use the kit's page size, text area, spacing and column settings. Existing
`geometry`, `setspace`, `\linespread`, `\vspace` or page-break commands are
candidates to inspect, not a universal deletion list. Some official kits use
such commands themselves.

Remove or adjust an override only when its conflict is established. Check the
rendered consequences and preserve intentional breaks, mathematical spacing
and class-controlled section/float layout.

## Headings

Use the class's heading hierarchy and numbering conventions. Preserve heading
text and labels during a format conversion. Capitalization and numbering depend
on the target; an arbitrary word limit does not determine a good heading.

Do not turn custom environments or an appendix's structure into ordinary
sections without checking their role. A formatting request does not authorize
rewriting the paper's scientific organization.

## Figures

Use the width available in the containing context. In a normal single-column
float `\linewidth` follows that column; inside a minipage it follows the
minipage. A two-column `\textwidth` can overflow an ordinary `figure`.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\linewidth]{figures/architecture.pdf}
  \caption{The supplied caption.}
  \label{fig:architecture}
\end{figure}
```

This requires `graphicx` and the actual asset. Full available width is only
a candidate: choose a smaller width when appropriate. A double-column
`figure*` has a different width and class-dependent placement behavior.
Do not wrap a float inside another float or a minipage.
See the [graphicx package and documentation](https://ctan.org/pkg/graphicx).

Preserve aspect ratio, panel labels and legibility at the final physical size.
Check raster resolution at that size against the target's instructions; a
single DPI threshold cannot establish quality. Vector plots can retain scalable
lines and text, whereas a photograph may appropriately remain raster.

Use the kit's caption/subfigure mechanisms and caption placement. With standard
LaTeX counters, put `\label` after `\caption`; custom kit macros may provide
their own interface. Keep label keys and all referring text intact.

## Tables

Preserve the cell grid, values, precision, units, notes and caption. Follow
required caption placement and rule style; “no vertical rules” is a design
preference for some table styles, not a universal submission rule.

`booktabs` is an optional table package when compatible with the kit. Wrapping
text in `p{...}` columns or restructuring a wide table may help readability.
A full-width table may use `table*` when the class supports it. Do not scale
all text below legibility or silently move values between columns.

For recovery of uncertain or merged cells, use page evidence; a formatting
change must not guess missing contents.

## Mathematics

Retain formula grouping, notation, tags and references. Select an environment
that matches the layout: `equation` for one numbered display, `align` for
aligned relations, `gather` for separate centered displays and `multline`
for one long equation split across lines. Starred forms generally suppress
automatic numbering in the `amsmath` environments.

Load packages only when needed and compatible with the class's setup.
`\bm` and `\mathbf` have different roles; do not substitute one globally.
Preserve the punctuation required by the sentence around a display.

See the [official amsmath guide](https://www.latex-project.org/help/documentation/amsldoc.pdf).

## Cross-References and Bibliography

Preserve label/citation keys and check resolution in the final log and PDF.
Prefixes such as `fig:` or `sec:` are project conventions, not required syntax.

Keep the kit's bibliography system, styles and package choices. Loading both
`cite` and `natbib` can conflict, but which package to remove depends on
the kit; `natbib` is not a universal replacement. Do not introduce
`biblatex` merely to simplify command names.

| Citation purpose | natbib candidate | biblatex candidate |
|---|---|---|
| Author is part of the sentence | `\citet{key}` | `\textcite{key}` |
| Parenthetical citation | `\citep{key}` | `\parencite{key}` |

This is a starting point when migration is required, not a global substitution
rule. Preserve pre/postnotes, locators, multiple keys, starred author forms,
language and punctuation; check how the actual style renders them.
A bare `\cite` is style-dependent and cannot always be assigned a role from
its name. See the [natbib documentation](https://ctan.org/pkg/natbib) and
[biblatex documentation](https://ctan.org/pkg/biblatex).

`cleveref` is optional. If it is supported and both it and `hyperref` are
used, load `cleveref` after `hyperref`, following the kit and package
instructions. Do not add it to a kit that supplies its own reference interface.
See the [cleveref manual](https://mirrors.ctan.org/macros/latex/contrib/cleveref/cleveref.pdf).

## Page Numbers, Front Matter and Required Sections

Verify review, preprint and final requirements separately. Anonymity alone
does not decide page numbering, visible author blocks or funding statements.
Check PDF metadata and any supplements when the requested stage requires it.

Follow the kit for title/abstract placement, word limits and abstract citations.
There is no universal 150–300-word limit or citation ban for every article type.
Likewise, acknowledgment and appendix placement depend on the actual target.
Use its appendix interface and numbering rather than imposing one ordering.

A missing required disclosure, result or author contribution is an author
decision. Record it as missing/unverified; do not generate scientific content
to make the formatting checklist pass.

## Project Structure Conventions

Preserve a working structure, paths and macro definitions. Small documents can
remain in one file; large projects may benefit from separate sections and assets.

`\input` inserts a file without the page breaks associated with `\include`.
`\include` can be appropriate for chapters and `\includeonly` workflows;
do not replace it globally. Check included files and existing build assumptions
before reorganizing. Keep the original bibliography data and official style files.

## Worked Layout Example

[layout-example.tex](../assets/layout-example.tex) is a self-contained `article`
example included when installing only `latex-fmt`. It uses common TeX packages,
a column-relative panel, a table and resolved equation/figure/table references.
It needs no external graphics, fonts, bibliography or official kit.

Copy it into a new working directory and run the project's actual engine twice,
for example `pdflatex -no-shell-escape -interaction=nonstopmode layout-example.tex`.
The initial class option is `twocolumn`; change it to `onecolumn` to inspect
the same content in a wider layout. The internal panel demonstrates a minipage's
local `\linewidth`; replace the illustrative content only when adapting it.

CI compiles both modes with pdfLaTeX, XeLaTeX and LuaLaTeX and checks the panel
width and reference resolution. This exercises the example, not any venue's
official template. Obtain and verify the requested kit separately.

## Per-Venue Rules and Pre-Submission Checks

Use [the venue guide](templates/venue-guide.md) for official entry points.
Check current year/track/stage requirements rather than universal “gotchas”.
The main-content page boundary, excluded material, required disclosures,
metadata and supplements need checks against those requirements.

Searches over source can locate candidates, but cannot prove compliance:
custom macros, included files and rendered content require context. Deliver
pass/fail/unverified findings with source locations, rule sources and observed
build/visual-check results.
