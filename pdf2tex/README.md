# pdf2tex

Convert PDF documents back into editable, compilable LaTeX source code.

## What it does

- Extracts text, math, tables, figures, and structure from PDFs
- Uses pymupdf (fitz) for content extraction + AI for intelligent reconstruction
- Generates clean, compilable `.tex` files with proper preamble
- Extracts embedded images to a `figures/` directory
- Reconstructs tables, equations, citations, and bibliography

## Prerequisites

```bash
pip install pymupdf pdfplumber
```

Optional for font detection:
```bash
# macOS
brew install poppler  # provides pdffonts

# Ubuntu
sudo apt install poppler-utils
```

## Usage

### With Claude Code

```
/pdf2tex paper.pdf                    # Full reconstruction
/pdf2tex --engine xelatex paper.pdf    # Force engine
/pdf2tex --extract-images-only paper.pdf  # Just extract images
```

Or just say "convert this PDF to LaTeX" — the skill auto-activates.

### Cursor / Windsurf / Any Agent

```
Read awesome-latex-skills/pdf2tex/SKILL.md and follow the workflow.
```

## What gets recovered (and what doesn't)

| Recoverable | Not reliably recoverable |
|---|---|
| Text content, paragraph structure | Custom `\newcommand` macros |
| Section/subsections hierarchy | Comment text |
| Math expressions (inline + display) | Original `\input` file boundaries |
| Table structure and cell content | Exact `\vspace`/`\hspace` values |
| Figure placement and captions | Source bibliography (.bib) file |
| Citation text and key placeholders | Author comments/TODO notes |
| Document class and fonts | Complex user-defined environments |

## Skill architecture

```
pdf2tex/
├── SKILL.md           → AI workflow instructions
├── README.md          → This file
├── references/
│   ├── pdf-extraction-guide.md     → pymupdf API recipes
│   ├── structure-detection.md      → Document structure heuristics
│   ├── math-reconstruction.md      → PDF math → LaTeX mapping
│   └── table-reconstruction.md     → Table extraction strategies
└── agents/
    ├── claude.yaml
    └── openai.yaml
```