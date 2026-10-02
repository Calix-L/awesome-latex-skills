# Debug Workflow for Stubborn LaTeX Errors

## Establish the Build Context

Inspect the actual root, build configuration, and first causal diagnostic before editing:

1. **Which engine?** Check for `fontspec` or `polyglossia` → must use XeLaTeX/LuaLaTeX, not pdflatex
   ```bash
   grep -rl 'fontspec\|polyglossia' *.tex  # → use xelatex
   ```
2. **Stale auxiliary files?** Test fresh output in a temporary copy or with the [build checker](build-check.md). Retain the old logs and generated files. Do not delete `.bbl` indiscriminately: it may be the only available bibliography or a required submission artifact. Confirm which files can be regenerated.
3. **How many errors total?** inspect engine exit status and the final log (`!` and `file.tex:line:` diagnostics); focus on the first error before chasing cascades
4. **Encoding issues?** Inspect source bytes and build settings. A detector's guess is not proof of the original encoding; convert a copy only after establishing it and compare non-ASCII names/symbols.
5. **Missing files?** `grep -c 'File.*not found' build.log` — missing `.sty`, `.cls`, `.bib`, or images cause cascading failures
6. **Bibliography backend mismatch?** Read project configuration and `biblatex`'s `backend=` option. An old `.bcf` or `.aux` reflects a previous build, not necessarily the current configuration. Use the selected backend after its control files are generated.

## When to Use

Activate this workflow when:
- An error persists after 2 fix attempts
- Fixing one error introduces new errors
- Errors cascade in unpredictable ways
- You're unsure of the root cause

## Principle: Binary Search Debugging

For large `.tex` files with unclear error sources:

### Step 1: Isolate the Problem Region

In a disposable copy, isolate complete sections while preserving balanced structure. A possible technique is:
```latex
% After \begin{document}
...first half...

\iffalse
...second half (temporarily disabled)...
\fi
```

If the error disappears, the problem is in the second half.
If the error persists, the problem is in the first half.

Binary search down to the problematic region. Arbitrary `\iffalse` blocks can
interact with conditionals and verbatim content. Keep all isolation edits out of
the delivered source; removing content is not a final repair.

### Step 2: Minimal Reproducing Example (MRE)

Once you've found the problematic region, create a minimal test file:
```latex
\documentclass{article}
% Copy ONLY the packages actually needed
\usepackage{...}
\begin{document}
% Copy ONLY the problematic content
...
\end{document}
```

If the MRE compiles, the issue is interaction with other content.
If the MRE fails, the issue is in the isolated content itself.

### Step 3: Package Elimination

In that temporary copy, test package interactions:
```latex
% Comment each, one at a time:
% \usepackage{foo}
% \usepackage{bar}
```

Recompile after each removal. If the error disappears, investigate that interaction;
this does not establish equivalent fonts, citations, captions, or semantics.
Preserve the official template's choices and consult the relevant package manual.

## Stubborn Error Types

### Endless "Missing } inserted" Chain

**Symptom**: First error at line 50 says "Missing }", then every subsequent line also reports errors.

**Root cause**: The first error triggers parser state corruption. **Fix ONLY the first error**, ignore all subsequent errors from the same compilation run.

**Workflow**:
1. Fix ONLY the first error in the .log
2. Recompile
3. Check if new errors appear
4. Repeat

### "Runaway argument" Errors

**Symptom**: `! Runaway argument? ... Paragraph ended before \foo was complete.`

**Possible causes**: Missing braces/delimiters, unexpected paragraphs inside an
argument, or a fragile command in a moving argument. Inspect the scanned command
and its argument boundary before adding `\protect`.

For an established moving-argument problem, use a documented robust command or
an appropriate short title/caption. This example preserves the long caption while
keeping the math command out of the list of figures:
```latex
\caption[Results for alpha]{Results for $\alpha$}
```

Math mode and moving-argument robustness are separate issues. Simply protecting
a `\footnote` in a caption does not ensure correct placement in a float; use the
class/package's documented footnote mechanism and inspect the PDF.

### `Emergency stop` After Many Errors

**Symptom**: `! Emergency stop.` after many other errors.

**Action**: Read preceding diagnostics. Missing input or an unavailable interactive
response can also cause an emergency stop. Repair the causal issue and rebuild.

## Project-Specific Issues

### main.tex compiles but individual .tex files don't

**Symptom**: `! LaTeX Error: Missing \begin{document}.` when compiling `sections/intro.tex` directly.

**Cause**: An included fragment without a preamble needs the actual root document.

**Fix**: Compile the configured root, whose name need not be `main.tex`. A fragment
with its own supported standalone/subfiles setup may have a separate valid build.

### File encoding issues

**Symptom**: Strange characters or `! Package inputenc Error: Unicode character ...` appearing.

**Fix**:
1. Check file encoding: `file -I file.tex` (macOS) or `file -i file.tex` (Linux)
2. Establish the original encoding before converting a copy. Do not assume GB2312
   or overwrite the original based on a detector's guess.
3. Modern pdfLaTeX defaults to UTF-8; adding `inputenc` does not provide every
   Unicode glyph. Distinguish decoding, font encoding, and missing glyphs. See the
   [LaTeX release note](https://www.latex-project.org/news/2018/04/10/issue28-of-latex2e-news-released/).

### pdflatex vs xelatex vs lualatex

**Symptom**: Compilation works with xelatex but not pdflatex (or vice versa).

**Key differences**:
- `pdflatex`: modern LaTeX defaults to UTF-8 input; font encoding and glyph support are separate choices
- `xelatex`/`lualatex`: use fontspec, can access system fonts, native UTF-8

**If the user has fontspec** in their document: use `xelatex` or `lualatex`. Don't try to make it work with pdflatex.

**Determine which engine to use**:
```bash
grep -rl 'fontspec\|polyglossia' *.tex  # → use xelatex/lualatex
# inputenc/fontenc alone do not establish the intended engine; read configuration
```

## When to Escalate to User

Escalate to the user when:
- The error requires domain knowledge (which experiment is described, what the figure should show)
- Plausible fixes have different scientific or structural meanings
- You need to know the intended document structure
- Required source, assets, or build configuration cannot be obtained from the available project

Unfamiliar package syntax alone calls for its installed/official manual, not an
author decision. After three repair attempts without progress, retain the diff
and logs and report the blocker with compilation unverified.

When escalating, provide:
1. What you found
2. Where it is (file:line)
3. What might fix it (with your best guess first)
4. What you need from the user to proceed

## Common Error Chains

One real error often cascades into many reported errors. Recognizing these chains avoids fixing phantom errors.

### Chain 1: Missing `$` → cascading "Missing } inserted"

```
! Missing $ inserted
(l.42) x_i is important
! Missing } inserted
(l.42) x_i is important
! Extra }, or forgotten $
(l.43) The result shows...
```

**Candidate**: If `x_i` denotes math in this context, wrap it as `$x_i$`. An underscore
in a path, identifier, or literal listing needs a different repair. Rebuild before
deciding which subsequent diagnostics were consequences.

### Chain 2: Undefined control sequence → everything after breaks

```
! Undefined control sequence
(l.10) \textbff{bold text}
! Missing } inserted
(l.10) \textbff{bold text}
! Paragraph ended before \textbf was complete
(l.11) Next sentence here...
```

**Candidate**: Verify custom definitions, then fix a confirmed typo to `\textbf`.
Rebuild and reassess remaining errors; not every later diagnostic shares a cause.

### Chain 3: Missing `}` in preamble → entire document fails

```
! Missing } inserted
(l.5) \usepackage[utf8]{inputenc
! Emergency stop
```

**Fix**: Add the missing `}`. One character fix, all errors disappear.

### Chain 4: Wrong engine → font errors everywhere

```
! Font \TU/cmr/m/n/10 not found
(l.1) \documentclass{article}
! ... (20+ more font errors)
```

**Fix**: The document uses `fontspec` but was compiled with `pdflatex`. Switch to `xelatex`.

### Chain 5: Stale `.aux` → undefined references + missing labels

```
LaTeX Warning: Reference `fig:arch' on page 3 undefined
LaTeX Warning: Reference `tab:results' on page 5 undefined
LaTeX Warning: Citation `smith2023' on page 6 undefined
```

**Action**: Verify the citation system, selected backend, control files, and resource
paths. Test fresh output while preserving old artifacts, particularly `.bbl`.
Run the configured backend after the first engine pass and further engine passes
as needed; preserve genuinely unknown keys and flag them for the author.

### How to Recognize a Chain

If you see 10+ errors, check:
1. Is the first error a "Missing $", "Missing }", or "Undefined control sequence"? → Fix only that one.
2. Do all errors start at the same line? → It's a chain from that line.
3. Are all errors about fonts? → Wrong engine.
4. Are all errors "undefined reference" or "undefined citation"? → Stale aux files.
