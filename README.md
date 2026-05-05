<div align="center">

<img src="./assets/banner.svg" alt="awesome-latex-skills" width="100%">

<br>

### Every researcher knows the feeling.

> *47 compilation errors at 2 AM. A reviewer who writes "English needs improvement."*
> *A CVPR reject that needs to become an ICML submission by Friday.*

**awesome-latex-skills** gives any AI agent the domain expertise to handle these — structured workflows, curated references, and guardrails that raw prompts can't replicate.

<br>

`47 errors → 0` &nbsp;·&nbsp; `Chinglish → publication-ready` &nbsp;·&nbsp; `CVPR → NeurIPS` &nbsp;·&nbsp; `50 pages → structured notes`

<br>

<a href="https://github.com/Calix-L/awesome-latex-skills/actions"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="CI"></a>
<img src="https://img.shields.io/badge/skills-5-blue" alt="5 skills">
<img src="https://img.shields.io/badge/tests-151_passing-brightgreen" alt="151 tests">
<img src="https://img.shields.io/github/stars/Calix-L/awesome-latex-skills?style=social" alt="Stars">
<img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">

</div>

---

**[Skills](#skills) · [Demos](#demos) · [Workflows](#workflows) · [Quick Start](#quick-start) · [Compatibility](#compatibility) · [Changelog](./CHANGELOG.md) · [Contributing](./CONTRIBUTING.md)**

---

## Skills

<table>
<tr>
<td width="54" align="center">:ambulance:</td>
<td width="120"><strong><a href="./latex-rescue/SKILL.md">latex-rescue</a></strong></td>
<td>Fix compilation errors — 80+ auto-fix patterns, package conflicts, Overleaf support</td>
</tr>
<tr>
<td align="center">:pencil2:</td>
<td><strong><a href="./latex-polish/SKILL.md">latex-polish</a></strong></td>
<td>Polish academic writing — 18 Chinglish categories, 100+ phrasebank templates, 3 intensity levels</td>
</tr>
<tr>
<td align="center">:repeat:</td>
<td><strong><a href="./latex-fmt/SKILL.md">latex-fmt</a></strong></td>
<td>Reformat between 11 venues — NeurIPS · ICML · CVPR · ACL · ICLR · ECCV · AAAI · TMLR · IEEE · Nature · Science</td>
</tr>
<tr>
<td align="center">:book:</td>
<td><strong><a href="./paper-read/SKILL.md">paper-read</a></strong></td>
<td>Read & analyze papers — skim / read / deep, 43-item critical appraisal, assumption auditing</td>
</tr>
<tr>
<td align="center">:wrench:</td>
<td><strong><a href="./pdf2tex/SKILL.md">pdf2tex</a></strong></td>
<td>Rebuild LaTeX from PDF — 7-phase pipeline, 97+ math glyph mappings, table reconstruction</td>
</tr>
</table>

| | | | |
|---|---|---|---|
| 80+ error patterns | 14 package conflicts | 18 Chinglish categories | 100+ phrasebank templates |
| 11 venue rules | 43 appraisal items | 97+ glyph mappings | 15 reference files |

---

## Why skills, not just prompts?

You've tried asking ChatGPT to fix your LaTeX. It guesses. It misses things. It changes your math.

| What happens | Raw LLM | With skill pack |
|---|---|---|
| `\beginn{table}` | "That's an interesting typo" | Auto-corrects to `\begin{table}` |
| "According to the experiment" | Accepts it | Flags overuse, suggests alternatives |
| NeurIPS submission | Forgets Broader Impact | Flags missing required section |
| PDF → LaTeX | Produces broken markup | 7-phase pipeline with verification |
| `\citep{}` without natbib | Silently ignores | Detects missing package, adds it |

Skills inject **hundreds of domain-specific rules** that LLMs can't reliably recall from memory. Each skill = structured workflow + reference knowledge + guardrails. Same input, same expert output, every time.

---

## Demos

### :ambulance: latex-rescue — *2 AM, 47 errors, deadline tomorrow*

```diff
- \textbff{bold}              → Undefined control sequence
+ \textbf{bold}               → auto-fixed

- x_i is important            → Missing $ inserted
+ $x_i$ is important          → auto-fixed

- \begin{figure}...\end{table}
+ \begin{figure}...\end{figure}  → mismatch fixed
```

### :pencil2: latex-polish — *Reviewer #2 says "English needs improvement"*

```diff
- The model can achieves good performance on the dataset.
+ The model achieves strong performance on the benchmark.

- According to the experiment, it makes the accuracy improved by 3.2%.
+ Experiments show that the method improves accuracy by 3.2%.

- Most of methods in this research field can not achieve the same result.
+ Most methods in this field fail to match this result.
```

### :repeat: latex-fmt — *Camera-ready reformat, CVPR → NeurIPS*

```diff
- \documentclass{article}
+ \documentclass{neurips_2025}
- \author{Zhang et al.}
+ \author{Anonymous}
- (no Broader Impact section)
+ ⚠ Broader Impact required by NeurIPS — flagged
```

### :book: paper-read — *50 papers in your reading list, no time*

```diff
- "This paper proposes a novel transformer-based approach for..."
+ [skim] Object detection · Wang et al., CVPR 2024
+        Novelty: sparse attention for real-time. Verdict: worth deep read.

- (reading every paper front-to-back)
+ [deep] Key eq: sparse attention. Delta: 10x faster.
+        Gap: only tested on COCO. Overclaim: "SOTA" (margin 0.3%).
```

### :wrench: pdf2tex — *Lost the .tex, only the PDF survives*

```diff
- (staring at a compiled PDF, no source files)
+ \documentclass{article}
+ \usepackage{amsmath,amssymb}
+ \section{Introduction}
+ The model achieves $F_1 = 92.3$ on the benchmark.
+ % [UNCERTAIN: math notation — verify subscripts]
```

---

## Workflows

Skills compose into pipelines for real academic scenarios:

| Scenario | What you type | What happens |
|---|---|---|
| Deadline crunch | `/latex-rescue` | Crash → rescue → compile |
| Review turnaround | `/latex-polish` → `/latex-fmt` | Draft → polish → format → submit |
| Rebuttal reformat | `/latex-polish` → `/latex-fmt` | CVPR reject → polish → reformat for ICML |
| Lost source | `/pdf2tex` → `/latex-rescue` | PDF → reconstruct → fix → polish |
| New paper | `/paper-read` → `/latex-polish` → `/latex-fmt` | Read papers → polish → format for venue |
| Overleaf | `/latex-rescue` | Paste error log → get fixes |

---

## Quick Start

**One command to install all 5 skills:**
```bash
git clone https://github.com/Calix-L/awesome-latex-skills.git && \
cp -r awesome-latex-skills/{latex-rescue,latex-polish,latex-fmt,paper-read,pdf2tex} ~/.claude/skills/
```

Then just type `/latex-rescue`, `/latex-polish`, etc. in Claude Code.

**One skill only:**
```bash
cp -r awesome-latex-skills/latex-rescue ~/.claude/skills/
```

**Not using Claude Code?** Just point your agent to the SKILL.md:
```
Read awesome-latex-skills/latex-rescue/SKILL.md and follow the workflow.
```

<sup>No install needed for `latex-polish`, `latex-fmt`, or `paper-read`. `latex-rescue` needs LaTeX. `pdf2tex` needs `pip install pymupdf`.</sup>

---

## Compatibility

| Platform | How to use |
|---|---|
| **Claude Code** | Copy to `~/.claude/skills/`, invoke with `/latex-rescue` |
| **ChatGPT / GPT-4** | Paste SKILL.md as custom instruction or system prompt |
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

</details>

---

## License

MIT