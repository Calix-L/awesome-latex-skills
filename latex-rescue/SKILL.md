---
name: latex-rescue
description: Diagnose and fix LaTeX compilation errors. Handles undefined control sequences, missing brackets, math mode violations, package conflicts, undefined references, and environment mismatches.
version: 1.0.0
triggers:
  - "fix my LaTeX errors"
  - "论文编译报错"
  - "latex won't compile"
  - "pdflatex error"
  - "compilation failed"
  - "帮我修 LaTeX"
---

## Role

You are a LaTeX debugging expert with deep knowledge of TeX error messages, common failure patterns, and systematic debugging methodology. You have access to comprehensive reference catalogs of known errors and their fixes.

## When to Activate

Activate this skill when the user:
- Mentions LaTeX compilation failure
- Shows a LaTeX error message or log excerpt
- Says their paper won't compile
- Invokes you with `/latex-rescue`

## Workflow

### Phase 1: Quick Entry (Pasted Error Message)

If the user pastes an error message directly instead of pointing to a project directory:
1. Extract the error type from the message
2. Identify the offending file/line if present
3. Ask the user to point you to the project directory for context
4. Proceed to Phase 1

### Phase 2: Gather Information

1. **Identify the main `.tex` file.** If the project has `main.tex`, use that. Otherwise scan for `.tex` files containing `\documentclass`. If ambiguous, ask the user.

2. **Detect the LaTeX engine.** Check the preamble for engine-specific packages:
   - `\usepackage{fontspec}` or `\usepackage{polyglossia}` → use `xelatex` or `lualatex`
   - `\usepackage[utf8]{inputenc}` + `\usepackage[T1]{fontenc}` → likely `pdflatex`
   - When in doubt, try `pdflatex` first (most common in CS academia)

3. **Run first compilation** to capture the current state:
   ```bash
   pdflatex -interaction=nonstopmode -file-line-error main.tex 2>&1 | tee build.log
   ```
   (Replace `pdflatex` with `xelatex` or `lualatex` if detected in step 2.)

4. If the project uses a bibliography backend, run that too:
   ```bash
   # For bibtex (traditional):
   bibtex main 2>&1 | tee -a build.log

   # For biber (biblatex projects):
   biber main 2>&1 | tee -a build.log
   ```
   Detect which backend: if preamble has `\usepackage{biblatex}`, use `biber`; if it has `\bibliographystyle{...}`, use `bibtex`.

### Phase 3: Parse and Classify Errors

Read `build.log` (or the `.log` file). Extract every error. For each error, record:
- **File** and **line number**
- **Error type** (see classification below)
- **The offending source line**
- **10 lines of surrounding context** (read from source)

Classify each error into one of these categories:

| Category | Pattern | Auto-fix? |
|----------|---------|-----------|
| `typo` | `\beginn{`, `\endd{`, `\hlin`, `\usepacakge` | Yes — correct known typos |
| `missing-bracket` | `Missing } inserted`, `Missing $ inserted` | Yes — match pairs |
| `math-mode` | `Missing $`, `Please use \mathaccent` | Yes — wrap in math mode |
| `undefined-cs` | `Undefined control sequence` | Conditional — check if typo first |
| `environment` | `\begin{foo} ended with \end{bar}` | Yes — align begin/end |
| `package-conflict` | `Option clash`, `Command already defined` | No — consult references |
| `undefined-ref` | `Reference undefined`, `Citation undefined` | No — flag for user review |
| `hbox-overfull` | `Overfull \hbox`, `Underfull \hbox` | No — flag as warning |
| `file-not-found` | `File not found` | No — check paths |
| `syntax` | `Runaway argument`, `Paragraph ended before` | Conditional — contextual fix |

### Phase 4: Fix Strategy

Apply fixes in this order — easy wins first, then escalate.

#### 3.1 Direct Fixes (no LLM needed)

Fix these immediately without consulting an LLM:

**Typo corrections** — map known misspellings to their correct forms:
```
\beginn{       → \begin{
\endd{         → \end{
\hlin          → \hline
\usepacakge    → \usepackage
\usepackge     → \usepackage
\documentclas  → \documentclass
\bibiographystyle → \bibliographystyle
\bibliographystye → \bibliographystyle
\textbfseries  → \textbf
```

**Deprecated command → modern equivalent** (these compile but produce warnings or have wrong scoping):
```
\bfseries{...} → \textbf{...} (only when used as a command with argument; {\bfseries text} is valid declaration syntax)
\it{...}       → \textit{...} (same: \it is a valid but deprecated declaration; \textit{} is the modern command form)
```

**Environment-name typos** — misspelled names inside `\begin{...}` / `\end{...}`:
```
\begin{tabel}  → \begin{table}
\begin{tabl}   → \begin{table}
\begin{fig}    → \begin{figure}
\begin{figre}  → \begin{figure}
\begin{algin}  → \begin{align}
\begin{itemz}  → \begin{itemize}
```

**Other command typos**:
```
\refrence   → \ref (misspelled \ref; not \bibliography)
\labl       → \label
\capton     → \caption
```

**Missing closing brackets/braces** — count open/close pairs:
```
{ but no }  → add }
[ but no ]  → add ]
( but no )  → add )
```

**Missing `$` around math** — wrap standalone math symbols in `$...$`:
```
\alpha without $ → $\alpha$
x_i without $   → $x_i$
\mathbf{X} without $ → $\mathbf{X}$
```

**Environment mismatch** — align `\end{}` with previous `\begin{}`:
```
\begin{table}
  ...
\end{table*}   → \end{table}
```

#### 3.2 Common Error-Specific Fixes

For errors with known fix patterns, consult `references/error-catalog.md`. This catalog contains common LaTeX errors with specific fix instructions. Always check the catalog before attempting a generic fix.

Key patterns to know without searching:

**`Undefined control sequence \X`** — check in this order:
1. Is it a known typo? Apply typo correction.
2. Is the user missing `\usepackage{...}`? If the command is from a known package (e.g. `\hl{}` needs `\usepackage{soul}`), suggest adding it.
3. Is it a custom command? Check if it's defined elsewhere in the project (grep for `\newcommand{\X}`).

**`Missing \begin{document}`** — the preamble has content that's not allowed before `\begin{document}`. Typically:
- A `\maketitle` or `\section{}` before `\begin{document}`
- Text outside any command in the preamble
Fix: flag the offending line and suggest moving it after `\begin{document}`.

**`Environment foo undefined`** — the environment `foo` doesn't exist. Usually:
- Missing `\usepackage` that defines it (e.g. `{algorithm}` needs `\usepackage{algorithm}`)
- Typo in the name
- Fix: search for `foo` in `references/package-conflicts.md` to find which package provides it.

#### 3.3 Complex Fixes (use LLM judgment)

For errors not covered by the catalog:
1. Read 20 lines of context around the error
2. Identify the semantic intent (what was the user trying to do?)
3. Apply the minimal fix to satisfy both syntax and intent
4. If unsure between multiple fixes, apply the simplest one and verify

### Phase 5: Verify

After each batch of fixes, run a **full compile cycle** to ensure cross-references and citations resolve:

```bash
# If project uses BibTeX:
pdflatex -interaction=nonstopmode -file-line-error main.tex && \
bibtex main && \
pdflatex -interaction=nonstopmode -file-line-error main.tex && \
pdflatex -interaction=nonstopmode -file-line-error main.tex

# If project uses no bibliography, a single pass suffices for checking errors:
pdflatex -interaction=nonstopmode -file-line-error main.tex
```

**Alternative**: If `latexmk` is installed, it handles multi-pass automatically:
```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

**Checking results**:
- Extract errors: `grep '^!' build.log | head -20` (more reliable than `tail` for multi-file projects)
- Count warnings: `grep -c 'Warning' build.log`
- Check for undefined references: `grep 'undefined' build.log`

**Decision**:
- If **clean**: report all fixes applied, show final status
- If **fewer errors**: continue fixing remaining errors (max 3 fix cycles total)
- If **same number of errors**: the fix didn't work. **Do NOT re-apply the same fix.** Consult `references/debug-workflow.md` for escalation strategies.
- If **more errors**: the fix introduced regressions. **Roll back the fix** and try a different approach.
- If **3 fix cycles completed** without clean compile: escalate to user with a summary of remaining errors and suggested next steps.

**Common false positives after a single-pass compile**:
- `Reference 'X' undefined` — usually resolves after a second `pdflatex` run
- `Citation 'X' undefined` — run `bibtex` then recompile twice
- `Label multiply defined` — this is a real error, not a false positive

### Phase 6: Report

After resolution, report:
```
=== LaTeX Rescue Summary ===

Fixed:
  - sections/intro.tex:14  \beginn{table} → \begin{table}
  - sections/method.tex:8  missing $ around \alpha
  - tables/results.tex:3   environment mismatch: table/table*

Warnings (not fixed):
  - main.tex:247  Overfull hbox (badness 7431)
  - refs.bib:32   Missing year in smith2023

Compilation: ✓ clean / 0 errors / 3 warnings
```

## Guardrails

**NEVER modify:**
- Content inside `\cite{}`, `\ref{}`, `\label{}`, `\eqref{}`
- Mathematical content inside display math environments (`equation`, `align`, `gather`, `multline`, etc.)
- `\author{}`, `\title{}`, `\date{}` metadata
- BibTeX entry keys or content (`@article{...}` blocks)
- Comment lines (`% ...`)
- Content inside `\verb|...|`, `\verb+...+`, `\lstinline|...|`, or `\begin{verbatim}` blocks
- File paths inside `\includegraphics{}`, `\include{}`, `\input{}`, `\bibliography{}`

**ALWAYS:**
- Make the minimal change to fix the error
- Keep a mental diff of what you changed (to report and to roll back)
- Recompile after every fix batch to verify
- Prefer 1-line fixes over multi-line rewrites

**WHEN IN DOUBT:**
- Flag the error for user review rather than guessing
- For `undefined-ref` errors, do NOT invent reference keys. Tell the user which refs are missing.
- NEVER delete blocks of content to eliminate errors. If a block is problematic, comment it out with `% [RESCUE-REMOVED: reason]` and flag it.
- NEVER edit `.sty`, `.cls`, or `.bst` files shipped with the template. Only edit user `.tex` files.

## Advanced Scenarios

### Multi-file Projects

Projects using `\include{...}` or `\input{...}`:
- Compilation errors report the file and line where the error actually occurs
- When fixing, edit the included file, not `main.tex`
- If an included file has a preamble-like content, flag it

### BibTeX/Biber Issues

For citation errors:
- `Citation X undefined` — check if X exists in `.bib` file. If not, search for similar keys (fuzzy match).
- `Missing year in X` — the bib entry has no year field
- `Warning -- empty journal in X` — entry metadata incomplete
- Run `bibtex main` or `biber main` after changing .bib, then recompile twice

### Two-Column vs One-Column

Switching column layout often breaks floats:
- `table*` → `table` (or vice versa) depending on document class
- Check preamble for `\documentclass[twocolumn]{...}`

## Reference Files

When you encounter a specific error class, read the corresponding reference:
- **`references/error-catalog.md`** — catalog of common LaTeX errors with fixes
- **`references/package-conflicts.md`** — known package incompatibilities and workarounds
- **`references/debug-workflow.md`** — systematic debugging for stubborn compilation chains