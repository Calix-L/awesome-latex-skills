<div align="center">

# awesome-latex-skills

**Prompt packs that make any AI agent a LaTeX expert.**

`47 compilation errors → 0` · `Chinglish → publication-ready` · `CVPR → NeurIPS` · `50 papers → structured notes`

<br>

<a href="https://github.com/Calix-L/awesome-latex-skills/actions"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="CI"></a>
<img src="https://img.shields.io/badge/skills-5-blue" alt="5 skills">
<img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">

</div>

---

**[Skills](#skills) · [Demos](#demos) · [Quick Start](#quick-start) · [Contributing](./CONTRIBUTING.md)**

---

## Skills

- :ambulance: **[latex-rescue](./latex-rescue/)** — fix compilation errors · 50+ error patterns · package conflicts · environment mismatches
- :pencil2: **[latex-polish](./latex-polish/)** — polish academic writing · 16 Chinglish categories · phrasebank by section · level-controlled edits
- :repeat: **[latex-fmt](./latex-fmt/)** — reformat for 11 venues · NeurIPS · ICML · CVPR · ACL · ICLR · ECCV · AAAI · TMLR · IEEE · Nature · Science
- :book: **[paper-read](./paper-read/)** — read & analyze papers · 3 depth levels · critical appraisal · idea mining
- :wrench: **[pdf2tex](./pdf2tex/)** — rebuild LaTeX from PDF · 7-phase pipeline · math & table reconstruction

## Demos

**latex-rescue** — 47 errors, gone.

```diff
- \textbff{bold}              → Undefined control sequence
+ \textbf{bold}               → auto-fixed

- x_i is important            → Missing $ inserted
+ $x_i$ is important          → auto-fixed

- \begin{figure}...\end{table}
+ \begin{figure}...\end{figure}  → mismatch fixed
```

**latex-polish** — Reviewer #2, satisfied.

```diff
- The model can achieves good performance on the dataset.
+ The model achieves strong performance on the benchmark.

- According to the experiment, it makes the accuracy improved by 3.2%.
+ Experiments show that the method improves accuracy by 3.2%.

- Most of methods in this research field can not achieve the same result.
+ Most methods in this field fail to match this result.
```

**latex-fmt** — New venue, one pass.

```diff
- \documentclass{article}
+ \documentclass{neurips_2025}
- \usepackage{cite}
+ \bibliographystyle{neurips_2025}
```

## Quick Start

```bash
git clone https://github.com/Calix-L/awesome-latex-skills.git
```

**Claude Code** — drop a skill into `~/.claude/skills/`:
```bash
cp -r awesome-latex-skills/latex-rescue ~/.claude/skills/
```

**Any agent** — point it at the file:
```
Read awesome-latex-skills/latex-rescue/SKILL.md and follow the workflow.
```

That's it. No servers, no API keys, no dependencies.

<details>
<summary>How it works</summary>

Each skill is a directory the agent reads at runtime:

```
latex-rescue/
├── SKILL.md              # role, triggers, workflow, guardrails
├── references/           # domain knowledge consulted during work
│   ├── error-catalog.md  #   50+ error patterns → fix or escalate
│   ├── package-conflicts.md
│   └── debug-workflow.md
└── agents/               # auto-activation configs
    ├── claude.yaml
    └── openai.yaml
```

1. You type `/latex-rescue` or describe the problem
2. Agent loads `SKILL.md` — structured workflow + guardrails
3. It reads `references/` for precise domain rules at each phase
4. Same workflow → same expert output, every time

The difference from a raw LLM: these skills inject hundreds of precise, domain-specific rules that LLMs can't reliably produce from memory. An LLM knows LaTeX exists. These skills know that `\usepackage{cite}` must become `\bibliographystyle{neurips_2025}` when switching to NeurIPS.

</details>

## License

MIT
