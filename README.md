<div align="center">

<img src="./assets/banner.svg" alt="awesome-latex-skills" width="100%">

### Your AI agent wrote `\beginn{table}` again. Fix it in seconds.

Every researcher who uses LaTeX knows the pain: **47 compilation errors at 2 AM**, a reviewer who says *"English needs improvement"*, or a CVPR reject that needs to become an ICML submission by Friday.

**awesome-latex-skills** turns any AI agent into a LaTeX expert with structured workflows, domain-specific references, and guardrails that raw prompts can't provide.

&nbsp;

`47 errors → 0` &nbsp;·&nbsp; `Chinglish → publication-ready` &nbsp;·&nbsp; `CVPR → NeurIPS` &nbsp;·&nbsp; `50 pages → structured notes`

&nbsp;

<a href="https://github.com/Calix-L/awesome-latex-skills/actions"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="CI"></a>
<img src="https://img.shields.io/badge/skills-5-blue" alt="5 skills">
<img src="https://img.shields.io/badge/tests-142_passing-brightgreen" alt="142 tests">
<img src="https://img.shields.io/github/stars/Calix-L/awesome-latex-skills?style=social" alt="Stars">
<img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT">

</div>

---

**[Skills](#skills) · [Demos](#demos) · [Workflows](#workflows) · [Quick Start](#quick-start) · [Compatibility](#compatibility) · [Changelog](./CHANGELOG.md) · [Contributing](./CONTRIBUTING.md)**

---

## Skills

<table>
<tr>
<td width="60" align="center">:ambulance:</td>
<td><strong><a href="./latex-rescue/SKILL.md">latex-rescue</a></strong></td>
<td>Fix compilation errors — 80+ auto-fix patterns, package conflict resolution, Overleaf support</td>
</tr>
<tr>
<td align="center">:pencil2:</td>
<td><strong><a href="./latex-polish/SKILL.md">latex-polish</a></strong></td>
<td>Polish academic writing — 16 Chinglish categories, 100+ phrasebank templates, 3 intensity levels</td>
</tr>
<tr>
<td align="center">:repeat:</td>
<td><strong><a href="./latex-fmt/SKILL.md">latex-fmt</a></strong></td>
<td>Reformat between venues — NeurIPS, ICML, CVPR, ACL, ICLR, ECCV, AAAI, TMLR, IEEE, Nature, Science</td>
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

<details>
<summary>By the numbers</summary>

| Metric | Count |
|---|---|
| Error patterns cataloged | 80+ |
| Package conflicts documented | 14 known pairs |
| Chinglish pattern categories | 16 |
| Phrasebank sentence templates | 100+ |
| Venue formatting rules | 11 |
| Critical appraisal checklist items | 43 |
| Math glyph → LaTeX mappings | 97+ |
| Reference files total | 15 |

</details>

---

## Why skills, not just prompts?

You've tried asking ChatGPT to fix your LaTeX. It guesses. It misses things. It changes your math.

| What happens | Raw LLM | With skill pack |
|---|---|---|
| `\beginn{table}` | "That's an interesting typo" | Auto-corrects to `\begin{table}` |
| "According to the experiment" | Accepts it | Flags `According to` overuse, suggests alternatives |
| NeurIPS submission | Forgets Broader Impact | Flags missing required section |
| PDF → LaTeX | Produces broken markup | 7-phase pipeline with verification |
| `\citep{}` without natbib | Silently ignores | Detects missing package, adds it |

**Why?** Skills inject hundreds of domain-specific rules that LLMs can't reliably produce from memory. Each skill is a **structured workflow + reference knowledge + guardrails** — same input, same expert output, every time.

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

- \usepackage{cite} + \usepackage{natbib}
+ → removed cite (conflicts with natbib)  → package conflict resolved
```

### :pencil2: latex-polish — Reviewer #2 says "English needs improvement"

```diff
- The model can achieves good performance on the dataset.
+ The model achieves strong performance on the benchmark.

- According to the experiment, it makes the accuracy improved by 3.2%.
+ Experiments show that the method improves accuracy by 3.2%.

- Most of methods in this research field can not achieve the same result.
+ Most methods in this field fail to match this result.

- This method proves that our approach is completely novel.
+ This method demonstrates that our approach is novel to our knowledge.
  (hedging: "proves" → "demonstrates", "completely" → removed)
```

### :repeat: latex-fmt — Camera-ready reformat, CVPR → NeurIPS

```diff
- \documentclass{article}
+ \documentclass{neurips_2025}
- \usepackage{cite}
+ \bibliographystyle{neurips_2025}
- \section*{Acknowledgements}
+ [REMOVED — anonymous submission]
- \author{Zhang et al.}
+ \author{Anonymous}
- (no Broader Impact section)
+ ⚠ Broader Impact section required by NeurIPS — flagged for author
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

## Workflows

Skills combine into pipelines for common academic scenarios:

| Scenario | Pipeline | Slash commands |
|---|---|---|
| Deadline crunch | crash → rescue → compile | `/latex-rescue` |
| Review turnaround | draft → polish → format → submit | `/latex-polish` → `/latex-fmt` |
| Rebuttal reformat | CVPR reject → polish → reformat for ICML | `/latex-polish` → `/latex-fmt` |
| Lost source recovery | PDF → reconstruct → fix → polish | `/pdf2tex` → `/latex-rescue` → `/latex-polish` |
| New paper from scratch | read papers → polish draft → format for venue | `/paper-read` → `/latex-polish` → `/latex-fmt` |
| Overleaf user | paste error log → get fixes | `/latex-rescue` |

---

## Quick Start

**Install all skills at once:**
```bash
git clone https://github.com/Calix-L/awesome-latex-skills.git
cp -r awesome-latex-skills/{latex-rescue,latex-polish,latex-fmt,paper-read,pdf2tex} ~/.claude/skills/
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

**Prerequisites**: `latex-rescue` needs a LaTeX install. `pdf2tex` needs `pip install pymupdf`. The other 3 skills need nothing.

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

</details>

---

## License

MIT