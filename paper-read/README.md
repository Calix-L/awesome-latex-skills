# paper-read

Read, analyze, and extract knowledge from academic papers. From 30-second skims to deep critical reviews.

## Prerequisites

- `pdftotext` for PDF extraction (or agent needs built-in PDF reading)
- For arXiv support: curl

```bash
# macOS
brew install poppler

# Ubuntu
sudo apt install poppler-utils
```

## Usage

### With Claude Code

```
/paper-read paper.pdf                    # Full structured read
/paper-read arxiv.org/abs/2307.xxxxx     # arXiv paper
/paper-read --level skim paper.pdf        # 5-bullet quick summary
/paper-read --level deep paper.pdf        # Full critical review
/paper-read paperA.pdf paperB.pdf         # Compare two papers
```

### Reading Levels

| Level | Output | When to use |
|-------|--------|-------------|
| `skim` | 5-bullet summary | Deciding whether to read |
| `read` | Structured report (problem, method, results, critique) | Understanding a relevant paper |
| `deep` | Full critical review with claim-evidence mapping | Reviewing, building on, or challenging |

## What it extracts

- **Problem framing** — honest or oversold?
- **Core method** — the key insight in 2-3 sentences
- **Key experiments** — with context on baseline strength
- **Claims vs evidence** — mapped side by side
- **Critical weaknesses** — missing ablations, weak baselines, overclaims
- **Relevance to you** — actionable takeaways

## Skill architecture

```
paper-read/
├── SKILL.md           → AI workflow instructions
├── README.md          → This file
├── references/
│   ├── reading-framework.md     → Paper section reading strategy
│   └── critical-appraisal.md    → Systematic evaluation checklist
└── agents/
    ├── claude.yaml
    └── openai.yaml
```