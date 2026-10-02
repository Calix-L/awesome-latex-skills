<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/banner-dark.svg">
  <img src="./assets/banner.svg" alt="awesome-latex-skills — Good research. Clearer manuscripts." width="100%">
</picture>

<br>

### A practical toolkit for your next paper.

Repair LaTeX, polish academic prose, apply publication templates, read papers,<br>and recover editable source — with focused workflows for your AI agent.

<p>
  <a href="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml"><img src="https://github.com/Calix-L/awesome-latex-skills/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="#skills"><img src="https://img.shields.io/badge/skills-5-6254c7?style=flat-square" alt="5 skills"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-317c62?style=flat-square" alt="MIT license"></a>
  <a href="https://github.com/Calix-L/awesome-latex-skills/stargazers"><img src="https://img.shields.io/github/stars/Calix-L/awesome-latex-skills?style=flat-square&amp;color=6254c7" alt="GitHub stars"></a>
</p>

**English** · [简体中文](./README_CN.md)<br><br>
[Quick start](#quick-start) · [Skills](#skills) · [Examples](#examples) · [Workflows](#workflows) · [FAQ](#faq)

</div>

---

## Quick start

**Python 3.10+ · Windows, macOS, Linux · installer has no third-party dependencies**

```sh
git clone https://github.com/Calix-L/awesome-latex-skills.git
cd awesome-latex-skills
python scripts/install.py --agent claude
```

Using **Codex**? Change the last command to `python scripts/install.py --agent codex`.
Use `python3` if that is your system's Python command.

| Agent | Invoke after installation | Default destination |
|---|---|---|
| Claude Code | `/latex-rescue` or a natural-language request | `~/.claude/skills/` |
| Codex | `$latex-rescue` or a natural-language request | `$CODEX_HOME/skills/`, default `~/.codex/skills/` |

<details>
<summary><strong>Install one skill, preview changes, or choose a destination</strong></summary>

```sh
# Preview first; no files are written
python scripts/install.py --agent codex --skill latex-rescue --dry-run

# Install only the selected bundle; repeat --skill to select more
python scripts/install.py --agent codex --skill latex-rescue

# Choose your own skills directory
python scripts/install.py --dest "path/to/skills" --skill paper-read
```

Each installation includes the entrypoint, references, and agent metadata.
Identical bundles stay untouched. If an existing bundle differs, the installer
stops the batch before writing. Back up and move the old bundle away before an
update, or choose another destination.

</details>

<details>
<summary><strong>Using another agent or a chat interface</strong></summary>

Give your agent access to the complete skill directory, then ask:

```text
Read awesome-latex-skills/latex-rescue/SKILL.md and follow its workflow.
```

In a chat-only interface, provide the entrypoint and the relevant reference files.
Pasting `SKILL.md` alone leaves out supporting guidance. Local editing and
compilation depend on the tools available to that agent. The legacy
`agents/config.yaml` files are integration hints, not a universal configuration
API for every platform.

</details>

## Skills

Choose the job you need. Every skill has its own workflow, domain references,
and rules for preserving the author's intent.

| Skill | Start here when… | What you receive |
|---|---|---|
| **[latex-rescue](./latex-rescue/SKILL.md)**<br>Repair | The project fails to compile | Minimal source fixes, build evidence, unresolved issues |
| **[latex-polish](./latex-polish/SKILL.md)**<br>Polish | The prose needs clearer academic English | Reviewable edits at light, moderate, or strict intensity |
| **[latex-fmt](./latex-fmt/SKILL.md)**<br>Format | You are changing venue or preparing a submission | Template changes and a pass/fail/unverified compliance report |
| **[paper-read](./paper-read/SKILL.md)**<br>Read | You need to understand or assess a paper | A skim, structured reading, or deeper appraisal grounded in the paper |
| **[pdf2tex](./pdf2tex/SKILL.md)**<br>Recover | You have the PDF but need editable LaTeX | Reconstructed source with uncertain content marked for review |

**Publication guidance:** NeurIPS · ICML · CVPR · ACL/EMNLP · ICLR · ECCV · AAAI ·
TMLR · IEEE · Nature · Science · COLING · KDD · SIGIR · Interspeech.
The [venue guide](./latex-fmt/references/templates/venue-guide.md) routes to official
instructions; the requested year, track, article type, and submission stage must
be verified. Official author kits are not bundled.

## Examples

Illustrative edits and requests, rather than benchmark results or promises of
automatic completion.

### Repair a syntax error

```diff
- \textbff{Results}
+ \textbf{Results}

- \begin{figure} ... \end{table}
+ \begin{figure} ... \end{figure}
```

Known syntax mistakes can be repaired. Ambiguous equations, table data, citation
keys, and labels remain author decisions; a successful build cannot resolve intent.

### Polish without changing the claim

```diff
- The model can achieves good performance on the dataset.
+ The model achieves good performance on the dataset.

- According to the experiment, the accuracy is improved by 3.2%.
+ The experiments show a 3.2% improvement in accuracy.
```

Technical terms, numbers, uncertainty, and the meaning of “3.2%” stay intact.
The skill does not silently turn a relative percentage into percentage points.

<details>
<summary><strong>More requests: formatting, reading, and PDF recovery</strong></summary>

**Format a paper**

```text
Format this project for NeurIPS 2026, main track, anonymous review.
Use the official author kit. Preserve the scientific content and report
any requirements that could not be verified.
```

**Read with a purpose**

```text
Read this paper in deep mode. Explain the main claim, supporting evidence,
important assumptions, and what I would need to reproduce the result.
Cite the relevant sections, figures, or equations.
```

**Recover editable source**

```text
Reconstruct this text-based PDF as LaTeX. Keep the section order and
mark ambiguous notation, merged table cells, and missing assets.
Report whether the result was compiled and visually checked.
```

</details>

## Workflows

| Your situation | Suggested sequence | Review before finishing |
|---|---|---|
| A draft will not build | `latex-rescue` | Final log, remaining warnings, rendered PDF |
| You are revising a manuscript | `latex-polish` → `latex-rescue` | Meaning-preserving diff and compilation |
| You are switching venues | `latex-fmt` → `latex-rescue` | Official rules, content-page boundary, anonymity |
| The original source is missing | `pdf2tex` → `latex-rescue` | Content coverage, equations, tables, visual comparison |
| You are reading related work | `paper-read` | Claims versus evidence and source locations |

Each step can also be used independently. Formatting does not upload or submit a paper.

## Check your environment

The bundles are instructions; external tools do the extraction and compilation.
Run a read-only prerequisite check before working on a local project:

```sh
python scripts/doctor.py --skill latex-rescue --engine pdflatex

# Match the actual project's engine and bibliography backend
python scripts/doctor.py --skill latex-fmt --engine xelatex --backend biber

# Machine-readable output; exit 1 means a required local tool is missing
python scripts/doctor.py --skill pdf2tex --json
```

| Task | Local prerequisites | If unavailable |
|---|---|---|
| Compile or verify formatting | Project's TeX engine; selected bibliography backend | Diagnose from supplied logs; report compilation as unverified |
| Polish pasted text / read supplied text | No TeX compiler required | Editing/reading can proceed; PDF verification is separate |
| Extract a text-based PDF | PyMuPDF: `python -m pip install pymupdf` | Supply extracted text or configure an extraction tool |
| Recover a scanned PDF | A separate OCR workflow | Standard text extraction is insufficient |
| Apply venue rules | Official kit and author instructions | Mark unresolved rules unverified |

The doctor checks local dependencies. It does not install software, compile a
document, or certify submission readiness.

## FAQ

<details>
<summary><strong>Does installing a skill install LaTeX or a model?</strong></summary>

No. It copies the instruction bundle. Use the AI agent and TeX distribution
already configured for your work; the doctor reports missing local prerequisites.

</details>

<details>
<summary><strong>Can I use this with Overleaf?</strong></summary>

Yes: provide the error log and relevant source for diagnosis, or export the
complete project for local checks. The agent must clearly distinguish a proposed
fix from a repair that has actually been recompiled.

</details>

<details>
<summary><strong>Will PDF recovery recreate my original source exactly?</strong></summary>

No. A PDF loses macros and source structure. Reconstruction aims for editable,
faithful content and marks uncertainty. Equations, tables, references, and layout
need comparison against the original; scanned pages need OCR first.

</details>

<details>
<summary><strong>What does a passing CI badge prove?</strong></summary>

CI validates bundle metadata, local resource and README links, SVG assets,
installation behavior, prerequisite reports, data-preserving fixtures, and real
TeX compilation. Portable checks run on Windows, macOS, and Linux with Python
3.10 and 3.13. It does not certify an AI agent's editing quality or a manuscript's
compliance with current venue rules. See [the test guide](./tests/README.md).

</details>

## Contribute

Found a misleading rule, a missing error pattern, or an installation issue?
Open an [issue](https://github.com/Calix-L/awesome-latex-skills/issues/new/choose)
or send a focused pull request. Include a minimal example, expected behavior,
and an official source for any venue-specific requirement.

[Contributor guide](./CONTRIBUTING.md) · [Test guide](./tests/README.md) ·
[Changelog](./CHANGELOG.md) · [MIT license](./LICENSE)

<div align="center">

<br>

<sub>Built for researchers who want useful assistance and changes they can review.</sub>

</div>
