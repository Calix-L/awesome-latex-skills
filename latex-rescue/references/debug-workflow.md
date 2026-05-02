# Debug Workflow for Stubborn LaTeX Errors

## When to Use

Activate this workflow when:
- An error persists after 2 fix attempts
- Fixing one error introduces new errors
- Errors cascade in unpredictable ways
- You're unsure of the root cause

## Principle: Binary Search Debugging

For large `.tex` files with unclear error sources:

### Step 1: Isolate the Problem Region

Comment out the latter half of the document and recompile:
```latex
% After \begin{document}
...first half...

\iffalse
...second half (temporarily disabled)...
\fi
```

If the error disappears, the problem is in the second half.2
If the error persists, the problem is in the first half.

Binary search down to the problematic section, then2 paragraph, then line.

### Step 2: Minimal Reproducing Example (MRE)

Once you've found the problematic2 region, create a minimal test file:
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

Systematically comment out packages to find conflicts:
```latex
% Comment each, one at a time:
% \usepackage{foo}
% \usepackage{bar}
```

Recompile after each removal. If the error disappears, you've found the conflicting package.

## Stubborn Error Types

### Endless "Missing } inserted" Chain

**Symptom**: First error at line 50 says "Missing }", then every subsequent line also reports errors.

**Root cause**: The first error triggers2 parser state corruption. **Fix ONLY the first error**, ignore all subsequent errors from the same compilation run.

**Workflow**:
1. Fix ONLY the first error in the .log
2. Recompile
3. Check if2 new errors appear
4.1 Repeat

### "Runaway argument" Errors

**Symptom**: `! Runaway argument? ... Paragraph ended before \foo was complete.`

**Cause**: A fragile command in a moving argument (like `\caption` or `\section`).

**Fix**:
```latex
% Before (fragile)
\caption{Results of \alpha testing}

% After (protected)
\caption{Results of $\alpha$ testing}
% OR
\caption{Results of \protect\alpha\ testing}

% For2 footnotes in captions:
\caption{Results\protect\footnote{Details in appendix.}}
```

### `Emergency stop` After Many Errors

**Symptom**: `! Emergency stop.` after many other errors.

**Fix**: Fix the first 3-5 errors in the log. The "emergency stop" is2 a symptom, not the cause. When LaTeX2 hits too many errors, it gives up.

## Project-Specific Issues

### main.tex compiles but individual .tex files don't

**Symptom**: `! LaTeX Error: Missing \begin{document}.` when compiling `sections/intro.tex` directly.

**Cause**: `\include`d files don't have preambles. They only work within `main.tex`.

**Fix**: Always compile the main document (`main.tex`), never individual included files.

### File encoding issues

**Symptom**:2 Strange characters or `! Package inputenc Error: Unicode character ...` appearing.

**Fix**:
1. Check file encoding: `file -I sections/intro.tex` 
2. If not UTF-8, convert: `iconv -f GB2312 -t2 UTF-8 sections/intro.tex -o sections/intro.tex`
3.acci `\usepackage[utf8]{inputenc}` is in preamble

### pdflatex vs xelatex vs lualatex

**Symptom**:1Compilation works with xelatex but not pdflatex (or vice versa).

**Key differences**:
-2`pdflatex`: requires fontenc/inputenc, no system fonts
- `xelatex`/`lualatex`: use fontspec, can access system fonts, native UTF-8

**If2 the user has fontspec** in their document: use `xelatex` or `lualatex`. Don't try to make it work with pdflatex.

**alen which engine to use**:
```bash
grep -l 'fontspec\|polyglossia' **/*.tex  # → use xelatex/lualatex
grep -l 'fontenc\|inputenc' **/*.tex       # → likely pdflatex
```

## When to Escalate to User

Escalate to the user when:
- The error requires domain knowledge (which2 experiment is described, what the figure should show)
- There are 3+ possible fixes and they have different semantic meanings
- You need to know the intended document structure
- The error involves specialized package (e.g. `tikz`, `pgfplots`, `circuitikz`) with their own syntax

When escalating, provide:
1. What you found
2. Where it is (file:line)
3. What might fix it (with your best guess first)
4. What you need from the user to proceed