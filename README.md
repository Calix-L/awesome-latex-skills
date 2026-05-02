# awesome-latex-skills

<p align="center">
  <a href="https://github.com/Calix-L/awesome-latex-skills/actions"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/skills-4-blue" alt="skills">
  <img src="https://img.shields.io/badge/tests-38%2F38%20passed-green" alt="tests">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="license">
  <img src="https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Cursor%20%7C%20Windsurf-purple" alt="platform">
</p>

<p align="center">
  <b>AI Agent skills for LaTeX & academic workflows.</b><br>
  Fix compilation errors. Polish academic writing. Format for journals. Read papers.<br>
  <i>Pure markdown prompt packs — no servers, no API keys, no dependencies.</i>
</p>

---

## Table of Contents

- [The Problem](#the-problem)
- [Skills](#skills)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Installation Requirements](#installation-requirements)
- [Project Stats](#project-stats)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)

---

## The Problem

LaTeX powers virtually all of computer science, physics, and mathematics publishing. Everyone who uses it shares the same nightmares:

1. **2 AM before deadline**: 47 cryptic compilation errors, none of which make sense
2. **Reviewer #2**: "The English needs significant improvement"
3. **Paper accepted!**: Now reformat the entire thing for the camera-ready template
4. **50 papers to read**: Can't keep up with arxiv, can't remember what you read last week

These are knowledge problems, not tooling problems. They're solved by expertise — the kind of expertise an AI agent can be given.

## Skills

| Skill | What it does | For when |
|---|---|---|
| **[latex-rescue](./latex-rescue/)** | Diagnoses and fixes LaTeX compilation errors | `pdflatex` explodes with 50 errors |
| **[latex-polish](./latex-polish/)** | Improves academic writing style and clarity | Reviewer complains about your English |
| **[latex-fmt](./latex-fmt/)** | Reformats papers for 9 major CS venues | Switching from CVPR to NeurIPS template |
| **[paper-read](./paper-read/)** | Reads and analyzes academic papers | You have a mountain of PDFs and no time |

### Skill Details

**latex-rescue** — The LaTeX emergency room.
- Auto-detects engine (pdflatex / xelatex / lualatex)
- Classifies errors into 10 categories
- Fixes typos (`\beginn{` → `\begin{`), missing `$`, broken brackets, environment nesting
- 85+ error patterns with auto-fix strategies

**latex-polish** — Your ruthless copy editor.
- 3 levels: light (grammar), moderate (grammar + style), strict (top-venue ready)
- Section-aware strategies for Abstract through Conclusion
- 16 categories of Chinese-author (Chinglish) patterns
- 9-section academic phrasebank with curated sentence templates

**latex-fmt** — One click, new template.
- 9 venues supported: NeurIPS, ICML, CVPR, ACL, AAAI, ICLR, IEEE, Nature, Science
- Handles page limits, anonymization, section reordering, citation style conversion
- Universal LaTeX formatting rules (booktabs, cleveref, no vertical lines in tables)

**paper-read** — Read papers like a reviewer.
- 3 levels: skim (30s), read (5min), deep (15min with critical appraisal)
- Claims vs evidence mapping table
- Cross-paper comparison mode
- Systematic evaluation checklist covering methodology, results, and innovation

## Quick Start

```bash
git clone https://github.com/Calix-L/awesome-latex-skills.git
```

### Claude Code

```bash
cp -r awesome-latex-skills/latex-rescue ~/.claude/skills/
```

Then type `/latex-rescue` in any LaTeX project. Or just say "fix my LaTeX errors" — the skill auto-activates from trigger words.

### Cursor / Windsurf / Any Agent

Point the agent to the skill file:

```
Read awesome-latex-skills/latex-rescue/SKILL.md and follow the workflow.
```

## How It Works

```
latex-rescue/
├── SKILL.md       ← The AI's playbook: role, triggers, 5-phase workflow, guardrails
├── README.md      ← Human-readable docs and examples
├── references/    ← Deep knowledge the AI consults while working
│   ├── error-catalog.md       → 85+ error patterns with fix strategies
│   ├── package-conflicts.md   → 15 known incompatibilities
│   └── debug-workflow.md      → Binary-search debugging for stubborn errors
└── agents/        ← Platform config (Claude Code, OpenAI-compatible)
    ├── claude.yaml
    └── openai.yaml
```

The AI loads `SKILL.md`, follows the workflow step by step, and reads reference files as needed. The reference files are the differentiator — they encode hundreds of specific rules that even large models can't reliably produce from memory alone.

## Installation Requirements

Your AI agent needs the ability to read/write files and execute shell commands.

For `latex-rescue`, the machine needs LaTeX installed:

```bash
# macOS
brew install --cask basictex

# Ubuntu (minimal, ~500MB)
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra
```

## Project Stats

| | |
|---|---|
| Skills | 4 |
| Reference files | 14 |
| Error patterns cataloged | 85+ |
| Venues supported | 9 |
| Chinese author patterns | 16 categories |
| Test coverage | 38/38 passing |
| CI | GitHub Actions enabled |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Add error patterns, phrasebank entries, venue templates, or Chinglish fixes.

## Roadmap

See [ROADMAP.md](./ROADMAP.md). Next up: `review-response` (parse reviewer comments → generate response letter), `grant-writing`, and `arxiv-digest`.

## License

MIT — see [LICENSE](./LICENSE)