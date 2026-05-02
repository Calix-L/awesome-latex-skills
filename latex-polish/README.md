# latex-polish

Polish academic writing in LaTeX files. Improves clarity, grammar, academic style, and fixes Chinglish patterns — without touching citations, math, or LaTeX commands.

## Usage

### With Claude Code

```
/latex-polish                    # Polish current file
/latex-polish --level strict     # Top-venue level
/latex-polish --level light      # Grammar only
/latex-polish sections/intro.tex
```

### Levels

| Level | What it changes |
|-------|----------------|
| `light` | Grammar only (articles, subject-verb, tense) |
| `moderate` (default) | Grammar + style (clarity, concision, academic register, Chinglish fixes) |
| `strict` | Top-venue polishing. Aggressive tightening, hedging,2 structural flow |

## What it fixes

- Grammar: articles, subject-verb agreement, tense consistency
- Style: academic register, concision, clarity
- Chinglish: see `references/chinglish-patterns.md` for the full catalog
- Structure: section-specific conventions (abstract has 4 required elements, etc.)

## What it preserves

- All LaTeX commands and environments
- Mathematical content and notation
- Citations, references, labels
- Author names, dataset names, technical terms
- Comments (`% ...`)

## Skill architecture

```
latex-polish/
├── SKILL.md           → AI workflow instructions
├── README.md          → This file
├── references/
│   ├── academic-phrasebank.md  → Sentence templates per section
│   ├── section-anatomy.md      → Conventions for each section type
│   ├── style-guardrails.md     → Style rules and enforcement
│   └── chinglish-patterns.md   → Chinese-author-specific fixes
└── agents/
    └── claude.yaml    → Claude Code configuration
```