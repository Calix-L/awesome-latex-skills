# latex-fmt

Reformat LaTeX papers for target journals and conferences. Document class changes, margin adjustments, citation style conversion, formatting compliance checks.

## Usage

### With Claude Code

```
/latex-fmt --to neurips     # Format for NeurIPS submission
/latex-fmt --to icml        # Format for ICML
/latex-fmt --to cvpr        # Format for CVPR
/latex-fmt check            # Pre-submission compliance check (no changes)
```

### Supported Venues

- NeurIPS (2025/2026)
- ICML (2025/2026)
- CVPR (2026)
- ACL / EMNLP
- AAAI
- ICLR
- IEEE (Computer Society)
- Nature / Science (structural guidance, template provided by journal)

## What it does

1. Replaces `\documentclass` and required packages
2. Removes forbidden packages for the target venue
3. Adjusts section ordering if venue requires specific structure
4. Checks page count against venue limits
5. Verifies anonymization (for double-blind venues)
6. Converts citation style if needed
7. Runs full compliance checklist

## What it DOES NOT do

- Generate content for missing sections (Broader Impact, Limitations, etc.) — flags them
- Alter your scientific claims or results
- Add or remove references

## Skill architecture

```
latex-fmt/
├── SKILL.md           → AI workflow instructions
├── README.md          → This file
├── references/
│   └── templates/
│       └── venue-guide.md  → Config for each venue
└── agents/
    └── claude.yaml    → Claude Code configuration
```