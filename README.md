# awesome-latex-skills

<p align="center">
  <img src="https://img.shields.io/badge/skills-4-blue" alt="skills">
  <img src="https://img.shields.io/badge/tests-29%2F29%20passed-green" alt="tests">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="license">
  <img src="https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Cursor%20%7C%20Windsurf-purple" alt="platform">
</p>

<p align="center">
  <b>AI Agent skills for LaTeX & academic workflows.</b><br>
  Fix compilation errors. Polish academic writing. Format for journals. Read papers.<br>
  <i>Pure markdown prompt packs — no servers, no API keys, no dependencies.</i>
</p>

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
| **[latex-fmt](./latex-fmt/)** | Reformats papers for 9 major CS venues | Switching from CVPR → NeurIPS template |
| **[paper-read](./paper-read/)** | Reads and analyzes academic papers | You have a mountain of PDFs and no time |

## Quick Start

```bash
git clone https://github.com/Calix-L/awesome-latex-skills.git
```

### Claude Code

```bash
cp -r awesome-latex-skills/latex-rescue ~/.claude/skills/
```

Then type `/latex-rescue` in any LaTeX project. Or just say "fix my LaTeX errors" — the skill auto-activates.

### Cursor / Windsurf / Any Agent

```
Read awesome-latex-skills/latex-rescue/SKILL.md and follow the workflow.
```

## How a Skill Works

```
latex-rescue/
├── SKILL.md       ← The AI's playbook: role, triggers, 5-phase workflow, guardrails
├── README.md      ← Human-readable docs and examples
├── references/    ← Deep knowledge the AI consults while working
│   ├── error-catalog.md       → 85+ error patterns with fix strategies
│   ├── package-conflicts.md   → 15 known incompatibilities
│   └── debug-workflow.md      → Binary-search debugging for stubborn errors
└── agents/        ← Platform config (Claude Code, OpenAI-compatible)
```

The AI loads `SKILL.md`, follows the workflow step by step, and reads reference files as needed. The reference files are what make the difference — they encode hundreds of specific rules that the LLM can't reliably produce from memory.

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
| Reference files | 12 |
| Error patterns cataloged | 85+ |
| Venues supported | 9 |
| Chinese author patterns | 16 categories |
| Test coverage | 29/29 passing |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Add error patterns, phrasebank entries, venue templates, or Chinglish fixes.

## Roadmap

See [ROADMAP.md](./ROADMAP.md). Next: `review-response` skill, `grant-writing` skill, `arxiv-digest` skill.

## License

MIT — see [LICENSE](./LICENSE)