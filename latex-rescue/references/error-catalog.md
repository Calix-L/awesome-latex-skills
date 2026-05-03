# LaTeX Error Catalog

## Error Message Quick-Map

Look up the log message here to jump to the right section:

| Log Message Substring | Category | Section Below |
|---|---|---|
| `Undefined control sequence` | Typo or missing package | Command Typos / Context-Dependent Typos |
| `Missing $ inserted` | Math mode | Math Mode Errors |
| `Missing } inserted` / `Extra }` | Braces | Bracket/Brace Errors |
| `begin{...} ended by \end{...}` | Environment mismatch | Environment Errors |
| `Missing \endcsname inserted` | Broken label/key | Syntax Errors |
| `Runaway argument` | Fragile command in moving arg | Syntax Errors |
| `Paragraph ended before ... was complete` | Missing brace or fragile cmd | Syntax Errors |
| `Illegal parameter number` | Wrong `\newcommand` definition | Syntax Errors |
| `Option clash` | Package loaded twice with diff options | Package Errors |
| `Command already defined` | Package conflict | Package Errors |
| `File ... not found` | Missing package or file | Package Errors |
| `LaTeX Warning: Citation ... undefined` | Missing .bib entry | Citation Errors |
| `LaTeX Warning: Reference ... undefined` | Missing \label | Reference Errors |
| `Cannot determine size of graphic` | Missing image file | Float Errors |
| `Too many }'s` / `Too few }'s` | Brace mismatch | Bracket/Brace Errors |
| `Misplaced \hline` | Table formatting | Table Errors |
| `Extra alignment tab` | Too many `&` in table row | Table Errors |

## Typo Corrections (auto-fix)

### Command Typos

| Wrong | Correct |
|-------|---------|
| `\beginn{` | `\begin{` |
| `\endd{` | `\end{` |
| `\hlin` | `\hline` |
| `\usepacakge` | `\usepackage` |
| `\usepackge` | `\usepackage` |
| `\documentclas` | `\documentclass` |
| `\bibiographystyle` | `\bibliographystyle` |
| `\bibliographystye` | `\bibliographystyle` |
| `\textbfseries` | `\textbf` |
| `\labl` | `\label` |
| `\capton` | `\caption` |
| `\incluegraphics` | `\includegraphics` |
| `\centeringg` | `\centering` |

### Environment-Name Typos

These appear inside `\begin{...}` or `\end{...}`. Fix the environment name:

| Wrong | Correct | Note |
|-------|---------|------|
| `\tabel` | `\begin{table}` | `table` is an environment, not a command |
| `\tabl` | `\begin{table}` | Same |
| `\fig` | `\begin{figure}` | `figure` is an environment, not a command |
| `\figre` | `\begin{figure}` | Same |
| `\tabluar` | `\begin{tabular}` | Same |
| `\algin` | `\begin{align}` | Same |
| `\itemz` | `\begin{itemize}` | Same |

### Context-Dependent Typos

| Wrong | Correct | Note |
|-------|---------|------|
| `\refrence` | `\bibliography` or `\bibliographystyle` | `\reference` is not a LaTeX command; infer from context |

## Math Mode Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Missing $ inserted` | `\alpha`, `x_i`, `x^2` in text | Wrap in `$...$` |
| Empty math mode | `$ $` or unmatched `$` | Remove space or add missing `$` |
| Double superscript | `x^a^b` | Change to `x^{ab}` or `{x^a}^b`. Ask user. |
| `\left` without `\right` | `\left( x+y` | Add `\right)` or `\right.` |

## Bracket/Brace Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Missing } inserted` | Open `{` without close | Count pairs, add missing `}` |
| `Too many }'s` | Extra `}` | Remove extra |
| Mismatched type | `\textbf[text}` | Replace `[` with `{` |

## Environment Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| Environment undefined | Typo in `\begin{foo}` | Correct typo (see table above) |
| Begin/end mismatch | `\begin{figure}`...`\end{table}` | Match `\end` to `\begin` |
| Missing `\begin{document}` | Content before doc starts | Move content after `\begin{document}` |
| Wrong nesting | `A → B → end A → end B` | Reorder ends (LIFO) |

## Citation and Reference

| Error | Pattern | Fix |
|-------|---------|-----|
| Citation undefined | `\cite{key}` not in .bib | Check .bib, suggest similar keys |
| Reference undefined | `\ref{label}` has no `\label` | Check for missing/wrong label, add if needed |
| Missing bibliography | No `\bibliography{...}` | Add `\bibliographystyle` + `\bibliography` |

## Package Issues

| Error | Pattern | Fix |
|-------|---------|-----|
| `Option clash` | Same package loaded twice with different options | Remove duplicate, merge options |
| `Command already defined` | Two packages define same command | Check load order in `package-conflicts.md` |
| `File not found` | `\usepackage{foo}` where foo.sty missing | Install package or flag missing dep |
| `Package X Error` | Package-specific error | Read error message for package-specific guidance |

## Table/Array Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Extra alignment tab` | Too many `&` for column count | Reduce `&` or add columns |
| `Misplaced \noalign` | `\hline` in wrong position | Check table structure |
| `Illegal unit of measure` | Bad column width spec | Check `p{...}`, `m{...}` arguments |

## Float and Figure Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Float too large` | Figure/table exceeds page | Reduce size with `[width=\textwidth]` |
| `Unknown graphics extension` | Missing file extension | Add .png/.pdf/.jpg extension |
| `Cannot determine size` | Graphics file not found/corrupt | Check file path exists |

## Overfull/Underfull Warnings

| Warning | Meaning | Action |
|---------|---------|--------|
| `Overfull \hbox` | Text exceeds line width | Reword or add hyphenation: `\-` |
| `Underfull \hbox` | Too much stretch in line | Usually ignore unless very bad |
| `Overfull \vbox` | Content exceeds page height | Reduce content or adjust margins |

## Encoding Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Unicode char not set up` | Special character in source | Add `\usepackage[utf8]{inputenc}` or escape char |
| `Invalid UTF-8 byte` | File encoding mismatch | Ensure file is UTF-8, not GB2312 |
| `Package babel Error: Unknown option` | Wrong language/option for babel | Check babel documentation for supported options; ensure correct language name |

## Auxiliary File Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `File ended while scanning use of \@writefile` | Corrupted `.aux` file | Delete all `.aux`, `.toc`, `.lof`, `.lot` files and recompile |
| `I'm not what you think you are` | Stale `.aux` from different document class | Delete `.aux` file and recompile twice |

## Spacing Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `There's no line here to end` | `\\` outside tabular/array or at start of paragraph | Remove `\\` or use `\par` instead |
| `Missing \endgroup inserted` | Misplaced `\\` in moving argument | Use `\protect\\` or restructure |

## Font Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Font ... not found` | Missing font package | Install font or use `\usepackage{lmodern}` |
| `Command \texttildelow unavailable` | Wrong font encoding | Use `\usepackage[T1]{fontenc}` |
| `Some font shapes were not available` | Missing bold/italic variant | Substitution warning, usually harmless. Flag if important. |
| `Corrupted NFSS tables` | Multiple fontenc calls | Only one `\usepackage[...]{fontenc}` allowed |

## Cross-Reference Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `Reference 'X' on page Y undefined` | `\ref{label}` without `\label{label}` | Add `\label{label}` after `\caption{}` or section |
| `Label 'X' multiply defined` | Duplicate `\label{label}` | Rename one of them |
| `\cref format for label type X undefined` | cleveref doesn't know label type | Define with `\crefname{}{}{}` |

## Counter Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `No counter 'X' defined` | `\setcounter` with unknown counter | Check counter name (typo?) |
| `Counter too large` | Too many numbered items | Reset counter or switch to letters |

## Document Structure Errors

| Error | Pattern | Fix |
|-------|---------|-----|
| `\maketitle undefined` or `\title undefined` | Document class doesn't define maketitle | Check if using `standalone` or minimal class |
| `Cannot determine size of graphic` | Missing or corrupt image file | Check file path and format |
| `No \title given` | Missing `\title{}` in preamble | Add `\title{...}` or ignore if intentional |

## Escalation

If an error is not in this catalog:
1. Read 20 lines around the error line
2. Understand the semantic intent
3. Apply minimal fix
4. If fails → consult `debug-workflow.md`