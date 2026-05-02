# latex-rescue

Diagnose and fix LaTeX compilation errors automatically. Point it at your paper directory, it compiles, finds errors, and fixes them.

## Prerequisites

- `pdflatex` (or `xelatex`/`lualatex`) installed
- For BibTeX errors: `bibtex` or `biber`

Install LaTeX:
```bash
# macOS
brew install --cask mactex-no-gui

# Ubuntu
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra
```

## Usage

### With Claude Code

Copy to skills directory:
```bash
cp -r latex-rescue ~/.claude/skills/
```

Then in any project:
```
/latex-rescue
```

Or just say "fix my LaTeX errors" and Claude Code will activate this skill.

### With any AI Agent

Tell the agent:
```
Read SKILL.md and follow the workflow to fix LaTeX errors in this directory.
```

## What it fixes automatically

- Typos: `\beginn{` → `\begin{`, `\hlin` → `\hline`, etc.
- Missing `$` around math symbols
- Missing closing `}` and `]`
- Environment begin/end mismatches
- Broken nesting order

## What it flags for review

- Undefined citations (reference not in .bib)
- Missing labels for `\ref{}`
- Package conflicts requiring user decisions
- Content that reveals identity in anonymous submissions

## Skill architecture

```
latex-rescue/
├── SKILL.md           → AI workflow instructions
├── README.md          → This file
├── references/
│   ├── error-catalog.md      → 50+ common errors and fixes
│   ├── package-conflicts.md  → Known package incompatibilities
│   └── debug-workflow.md     → Escalation for stubborn errors
└── agents/
    └── claude.yaml    → Claude Code configuration
```