---
name: latex-fmt
description: Reformat LaTeX papers for a specified venue, year, track, and submission stage. Apply official templates and check layout, bibliography, page limits, and anonymization while preserving scientific content.
metadata:
  version: "1.5.1"
---

## Role

Apply the requested publication format using the matching official author kit
and submission instructions. Distinguish successful compilation from verified
submission compliance.

## When to Activate

- The user asks to reformat a LaTeX manuscript or switch templates.
- The user asks for a pre-submission formatting check.
- The user invokes `/latex-fmt` or `$latex-fmt`.

## Workflow

### Phase 1: Establish the target and rules

Read the root document, build configuration, bibliography backend, and included
files. Establish the target **venue, year, track/article type, and stage**
(anonymous review, preprint, or camera-ready). Ask only for missing information
that changes the template or rules.

Read `references/templates/venue-guide.md` for official entry points and pitfalls.
Fetch the matching author kit and instructions, or use the user's supplied kit.
Record source URLs, check date, template filenames, page/word limits with
exclusions, anonymity rules, and required sections/checklists.

If authoritative rules are unavailable, preserve the existing format, identify
unresolved requirements, and make any provisional conversion's assumptions clear.
Do not silently choose a previous year's kit or infer filenames by incrementing
a year. This repository contains guidance, not official `.cls`, `.sty`, or `.bst`
files.

### Phase 2: Apply the official template

Follow the kit's example preamble, options, and author macros. `.cls` files belong
in `\documentclass`; `.sty` files belong in `\usepackage`. For example, the
historical NeurIPS 2025 review pattern is:

```latex
\documentclass{article}
\usepackage{neurips_2025} % use the requested year's actual kit
```

Do not invent `neurips_2025.cls` or `icml2025.cls`. Use the kit's bibliography
style rather than assuming the style package supplies a `.bst`. Remove custom
margin or spacing overrides only when they conflict with verified rules.

Consult [formatting rules](references/formatting-rules.md) for layout guidance.
Use the [self-contained layout example](assets/layout-example.tex) when checking
local widths and resolved references outside an official kit. It is an example,
not a substitute for the requested venue's template. Preserve text,
math, table values, citations, labels, and figure contents. Flag missing required
sections for the author; do not generate unsupported ethical or empirical claims.

### Phase 3: Bibliography and build

Respect the project's engine and bibliography backend. Prefer its existing build
command or `latexmk` when available. For manual builds, run the engine, the actual
BibTeX/Biber backend, and additional passes to resolve references. Do not run
`pdflatex` on a `fontspec` project or select Biber solely because `biblatex` is
present; check its backend option.

Preserve textual (`\citet`/`\textcite`) versus parenthetical (`\citep`/`\parencite`)
meaning when translating bibliography commands. Never blanket replace every
citation with `\cite` or `\citep`.

Check the exit status and final log, not just whether a PDF exists. Resolve
format-related errors with `latex-rescue` if available. Report missing tools or
template files as unverified compilation.

### Phase 4: Length and anonymity

Check the compiled main-content boundary against the verified limit; total PDF
pages cannot establish compliance when references or appendices are excluded.
Count words according to the article type. Suggest cuts before moving sections
or reducing figures. Avoid margin, font-size, or negative-spacing tricks.

For anonymous review, use the official review mode and inspect the main PDF,
supplement, author blocks, acknowledgments, funding, self-citations, URLs, and PDF
metadata. Flag identifying scientific text for contextual revision; keep citation
keys intact. Remove identity metadata in source, rebuild, and inspect the result.
An in-place metadata scrub does not prove anonymity. Camera-ready and preprint
author information should follow their own rules.

### Phase 5: Verification and report

Inspect the rendered PDF for clipped floats, readability, fonts, citations, and
applicable anonymity requirements. Check checklist location and required sections
against official rules. Report:

- Target venue/year/track/stage and authoritative sources with check date.
- Template and bibliography changes, with a reviewable diff.
- Build result, warnings, and actual page/word boundaries measured.
- Requirements as **pass**, **fail**, or **unverified**, with evidence.
- Missing author content or decisions and remaining actions.

A successful build is not a submission-ready claim. Use provisional/unverified
status if a required rule, build, or visual check could not be confirmed.

## Guardrails

- Preserve scientific content; do not invent citations or missing sections.
- Use rules for the specified target rather than historical examples.
- Keep official `.cls`, `.sty`, and `.bst` files intact.
- Do not remove author identities for camera-ready submissions by default.
- Never guarantee anonymity from a source keyword search alone.
- Preserve caption/author interfaces and textual versus parenthetical citations;
  package or command substitutions need verification in the actual kit.
- Do not submit, upload, or publish the paper as part of formatting.

## Reference Files

- **`references/templates/venue-guide.md`** — official venue entry points and template pitfalls.
- **`references/formatting-rules.md`** — layout, citation, and project organization guidance.
