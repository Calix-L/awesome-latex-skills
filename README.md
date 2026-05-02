# awesome-latex-skills

<p align="center">
  <b>AI Agent skills for LaTeX.</b><br>
  Fix compilation errors. Polish academic writing. Format for journals.<br>
  <i>Designed for Claude Code, Cursor, Windsurf, OpenClaw — any agent that reads markdown and runs commands.</i>
</p>

---

## The Problem

LaTeX powers virtually all of computer science, physics, and mathematics publishing. Everyone who uses it shares the same three nightmares:

1. **2 AM before deadline**: 47 cryptic compilation errors, none of which make sense
2. **Reviewer #2**: "The English needs significant improvement"
3. **Paper accepted!**: Now reformat the entire thing for the camera-ready template

These are knowledge problems, not tooling problems. They're solved by expertise — the kind of expertise an AI agent can be given.

## What This Is

Three AI agent skills. Each is a self-contained prompt pack: a `SKILL.md` with a step-by-step workflow, backed by `references/` with deep domain knowledge. No servers, no API keys, no dependencies.

| Skill | What it does | For when |
|---|---|---|
| **[latex-rescue](./latex-rescue/)** | Diagnoses and fixes LaTeX compilation errors | `pdflatex` explodes with 50 errors |
| **[latex-polish](./latex-polish/)** | Improves academic writing style and clarity | Reviewer complains about your English |
| **[latex-fmt](./latex-fmt/)** | Reformats papers for target venues | Switching from CVPR → NeurIPS template |

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/awesome-latex-skills.git
```

### Claude Code

```bash
cp -r awesome-latex-skills/latex-rescue ~/.claude/skills/
```

Then type `/latex-rescue` in any project. Or just say "fix my LaTeX errors" — the skill auto-activates from the trigger words.

### Cursor / Windsurf / Any Agent

Point the agent to the skill file:

```
Read awesome-latex-skills/latex-rescue/SKILL.md and follow the workflow.
```

## How a Skill Works

```
latex-rescue/
├── SKILL.md       ← The AI's playbook: role, triggers, 5-phase workflow, guardrails
├── README.md      ← Human-readable docs and examples
├── references/    ← Deep knowledge the AI consults while working
│   ├── error-catalog.md       → 50+ error patterns with fix strategies
│   ├── package-conflicts.md   → 15 known incompatibilities
│   └── debug-workflow.md      → Binary-search debugging for stubborn errors
└── agents/        ← Platform config (Claude Code, OpenAI-compatible)
    ├── claude.yaml
    └── openai.yaml
```

The AI loads `SKILL.md`, follows the workflow step by step, and reads reference files as needed. The reference files are what make the difference — they encode hundreds of specific rules (exact typo → exact fix, package A conflicts with package B, Chinese author pattern → English correction) that the LLM can't reliably produce from memory alone.

## What `latex-rescue` Actually Does

Given a broken LaTeX project:

1. **Compiles** with `pdflatex -interaction=nonstopmode -file-line-error`, captures the log
2. **Parses** every error, extracting file:line:type, reading surrounding source context
3. **Classifies** each error into one of 10 categories (typo, missing-bracket, math-mode, undefined-cs, environment, package-conflict, undefined-ref, hbox-overfull, file-not-found, syntax)
4. **Fixes auto-fixable errors** first: known typos (`\beginn{`→`\begin{`), missing `$` around math, mismatched brackets, broken environment nesting — no LLM needed for these
5. **Consults the error catalog** for known patterns, escalates complex cases to LLM
6. **Recompiles** after each fix batch, verifies progress
7. **Reports** everything that was changed, plus warnings that need human review

## What `latex-polish` Actually Does

Given a LaTeX paper draft:

1. **Determines scope and level** (`light` = grammar only, `moderate` = grammar + style, `strict` = top-venue)
2. **Identifies all LaTeX structures to preserve**: commands, math, citations, references, figures, comments
3. **Applies section-aware strategies**: abstracts need 4 specific components; introductions need a funnel; related work needs thematic grouping not laundry lists
4. **Fixes** grammar, article usage, tense consistency, academic register, clarity, concision
5. **Targets Chinese-author patterns**: 14 categories of recurring issues (article omission, subject-verb agreement, "can" overuse, preposition errors, "make/let" constructions, etc.)
6. **Reports** changes and flags substantive issues (missing citations, weak logic) for author review

## Installation Requirements

Your AI agent needs the ability to read/write files and execute shell commands.

For `latex-rescue`, the machine needs LaTeX installed:

```bash
# macOS
brew install --cask mactex-no-gui

# Ubuntu (minimal, ~500MB)
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra
```

## Contributing

These skills improve with more reference knowledge:

- New error patterns → `latex-rescue/references/error-catalog.md`
- Journal templates → `latex-fmt/references/templates/`
- Phrasebank entries → `latex-polish/references/academic-phrasebank.md`
- Chinglish patterns → `latex-polish/references/chinglish-patterns.md`

PRs welcome. If you discover a recurring LaTeX error that the catalog doesn't cover, or a Chinese-author writing pattern that should be caught, add it.

## License

MIT — see [LICENSE](./LICENSE)