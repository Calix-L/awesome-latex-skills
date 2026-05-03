<div align="center">

<img src="./assets/banner.svg" alt="awesome-latex-skills" width="100%">

**Prompt packs that make any AI agent a LaTeX expert.**

`47 errors → 0` · `Chinglish → publication-ready` · `CVPR → NeurIPS` · `50 pages → structured notes`

<br>

<a href="https://github.com/Calix-L/awesome-latex-skills/actions"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="CI"></a>
<img src="https://img.shields.io/badge/skills-5-blue" alt="5 skills">
<img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">

</div>

---

**[Skills](#skills) · [Demos](#demos) · [Quick Start](#quick-start) · [Compatibility](#compatibility) · [Contributing](./CONTRIBUTING.md)**

---

## Skills

| | Skill | What it does |
|---|---|---|
| :ambulance: | **[latex-rescue](./latex-rescue/SKILL.md)** | Fix compilation errors — 50+ patterns, package conflicts, environment mismatches |
| :pencil2: | **[latex-polish](./latex-polish/SKILL.md)** | Polish academic writing — 16 Chinglish categories, phrasebank, 3 intensity levels |
| :repeat: | **[latex-fmt](./latex-fmt/SKILL.md)** | Reformat for 11 venues — NeurIPS, ICML, CVPR, ACL, ICLR, ECCV, AAAI, TMLR, IEEE, Nature, Science |
| :book: | **[paper-read](./paper-read/SKILL.md)** | Read & analyze papers — 3 depth levels, critical appraisal, assumption auditing |
| :wrench: | **[pdf2tex](./pdf2tex/SKILL.md)** | Rebuild LaTeX from PDF — 7-phase pipeline, math & table reconstruction |

---

## Demos

### :ambulance: latex-rescue — 2 AM, 47 errors, deadline tomorrow

```diff
- \textbff{bold}              → Undefined control sequence
+ \textbf{bold}               → auto-fixed

- x_i is important            → Missing $ inserted
+ $x_i$ is important          → auto-fixed

- \begin{figure}...\end{table}
+ \begin{figure}...\end{figure}  → mismatch fixed
```

### :pencil2: latex-polish — Reviewer #2 says "English needs improvement"

```diff
- The model can achieves good performance on the dataset.
+ The model achieves strong performance on the benchmark.

- According to the experiment, it makes the accuracy improved by 3.2%.
+ Experiments show that the method improves accuracy by 3.2%.

- Most of methods in this research field can not achieve the same result.
+ Most methods in this field fail to match this result.
```

### :repeat: latex-fmt — Camera-ready reformat, CVPR → NeurIPS

```diff
- \documentclass{article}
+ \documentclass{neurips_2025}
- \usepackage{cite}
+ \bibliographystyle{neurips_2025}
- \section*{Acknowledgements}
+ [REMOVED — anonymous submission]
```

### :book: paper-read — 50 papers in your reading list, no time

```diff
- "This paper proposes a novel transformer-based approach for..."
+ [skim] Object detection via transformers · Wang et al., CVPR 2024
+        Novelty: sparse attention for real-time. Verdict: worth deep read.

- (reading every paper front-to-back)
+ [deep] Key equation: Eq.3 sparse attention. Delta: 10x faster.
+        Gap: only tested on COCO. Overclaim: "state-of-the-art" (margin 0.3%).
```

### :wrench: pdf2tex — Lost the .tex, only the PDF survives

```diff
- (staring at a compiled PDF, no source files)
+ \documentclass{article}
+ \usepackage{amsmath,amssymb}
+ \section{Introduction}
+ The model achieves $F_1 = 92.3$ on the benchmark.
+ % [UNCERTAIN: math notation — verify subscripts]
```

---

## Quick Start

**Install all skills at once:**
```bash
git clone https://github.com/Calix-L/awesome-latex-skills.git
cp -r awesome-latex-skills/latex-rescue awesome-latex-skills/latex-polish \
      awesome-latex-skills/latex-fmt awesome-latex-skills/paper-read \
      awesome-latex-skills/pdf2tex ~/.claude/skills/
```

**Or install one skill:**
```bash
cp -r awesome-latex-skills/latex-rescue ~/.claude/skills/
# Then type /latex-rescue in Claude Code
```

**Any agent** — point it to the SKILL.md:
```
Read awesome-latex-skills/latex-rescue/SKILL.md and follow the workflow.
```

**Prerequisites**: latex-rescue needs a LaTeX install. pdf2tex needs `pip install pymupdf`. The other 3 skills need nothing.

---

## Compatibility

| Platform | How to use |
|---|---|
| **Claude Code** | Copy skill folder to `~/.claude/skills/`, invoke with `/latex-rescue` |
| **ChatGPT / GPT-4** | Paste SKILL.md as a custom instruction or system prompt |
| **Cursor** | Add SKILL.md content to `.cursor/rules/` |
| **Copilot** | Add SKILL.md content to `.github/copilot-instructions.md` |
| **Any LLM** | Send SKILL.md as context, then ask your question |

---

<details>
<summary>How it works</summary>

Each skill is a self-contained directory:

```
latex-rescue/
├── SKILL.md              # the prompt — role, triggers, workflow, guardrails
├── references/           # domain knowledge the agent reads at each phase
│   ├── error-catalog.md
│   ├── package-conflicts.md
│   └── debug-workflow.md
└── agents/
    └── config.yaml       # auto-activation triggers and platform settings
```

1. You type `/latex-rescue` or say "fix my LaTeX errors"
2. Agent loads `SKILL.md` — now it has a structured workflow + guardrails
3. It reads `references/` for precise domain rules at each phase
4. Same workflow → same expert output, every time

The difference from a raw LLM: these skills inject hundreds of precise, domain-specific rules that LLMs can't reliably produce from memory. An LLM knows LaTeX exists. These skills know that `\usepackage{cite}` must become `\bibliographystyle{neurips_2025}` when switching to NeurIPS.

</details>

---

## License

MIT