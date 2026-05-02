# Tests for awesome-latex-skills

## Structure

```
tests/
├── README.md                    # This file
├── run_tests.sh                 # Automated test runner
└── fixtures/
    ├── errors/
    │   ├── broken_paper.tex     # Deliberately broken: 15 errors
    │   └── expected_fixed.tex   # What broken_paper.tex should look like after rescue
    ├── polish/
    │   └── chinglish_sample.tex # Sample with Chinese-author issues
    └── fmt/
        └── pre_neurips.tex      # CVPR-formatted paper to convert to NeurIPS
```

## How to Run

### Test latex-rescue

```bash
# 1. Compile the broken file (should produce errors)
cd tests/fixtures/errors
pdflatex -interaction=nonstopmode -file-line-error broken_paper.tex

# 2. Count the errors
grep -c '!' broken_paper.log

# 3. Activate latex-rescue skill in your AI agent
#    and point it at broken_paper.tex

# 4. After rescue, verify:
pdflatex -interaction=nonstopmode -file-line-error broken_paper.tex
# Should compile clean (0 errors)
```

### Test latex-polish

```bash
#1 Feed chinglish_sample.tex to the AI with latex-polish activated
# Verify: check for article usage, tense consistency, removed "can", etc.
```

### Test latex-fmt

```bash
# Feed pre_neurips.tex and ask AI to format for NeurIPS
# Verify: check documentclass changed, forbidden packages removed
```

## Expected Errors in broken_paper.tex

| Line | Error | Type | Auto-fix? |
|------|-------|------|-----------|
| 16 | `\beginn{itemize}` | typo | Yes |
| 18 | `\hlin` in text | typo | Yes |
| 19 | `\usepacakge` in text | typo | Yes |
| 20 | `\textbfseries` in text | typo | Yes |
| 21 | `\endd{itemize}` | typo | Yes |
| 26 | `\alpha` outside math | math-mode | Yes |
| 27 | `x_i` outside math | math-mode | Yes |
| 27 | `x^2` outside math | math-mode | Yes |
| 30 | `x^a^b` double superscript | math-mode | No (ask) |
| 37 | Missing `}` in `\textbf{}` | missing-bracket | Yes |
| 40 | Extra `}` | brace | Yes |
| 45 | `\end{table}` should be `\end{figure}` | environment | Yes |
| 51 | `\end{table}` and `\end{tabular}` swapped | nesting | Yes |
| 57 | `\ref{sec:missing}` undefined | undefined-ref | No (flag) |
| 57 | `\cite{undefined2024}` undefined | undefined-cite | No (flag) |