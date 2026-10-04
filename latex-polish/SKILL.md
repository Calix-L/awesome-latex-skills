---
name: latex-polish
description: Edit academic prose in LaTeX manuscripts or supplied text at light, moderate, or strict intensity. Improve grammar and clarity while preserving scientific claims, uncertainty, numbers, citations, and LaTeX structure.
metadata:
  version: "1.7.0"
---

## Scope and intensity

Edit the requested text, section, or manuscript. Infer scope from the request;
ask only when a missing preference changes the work. Default to `moderate`.

| Level | Editing scope |
|---|---|
| `light` | Grammar, spelling, articles, agreement, and necessary syntax fixes. |
| `moderate` | Light edits plus clearer phrasing, concision, and sentence flow. |
| `strict` | Moderate edits plus stronger paragraph organization within the requested scope. |

No level authorizes changing findings, adding evidence, or making a paper
"publication ready" by declaration. Use the author's chosen English variant,
terminology, and venue requirements when supplied.

## Preserve meaning and source structure

- Preserve numbers, units, uncertainty, causal direction, comparisons, named
  entities, and the distinction between relative percentages and percentage points.
- Keep modality and scope: `can`, `may`, `suggests`, and `under these conditions`
  may carry scientific meaning. Removing them can turn a capability into an
  observed result or a qualified claim into a universal claim.
- Do not add significance tests, p-values, citations, mechanisms, novelty, or
  broader-impact claims. Flag missing evidence for the author instead.
- Preserve citation/reference/label keys, bibliography records, equations,
  macro definitions, file paths, comments, and quoted material. Treat LaTeX
  arguments by their role, not by a blanket regular-expression replacement.
- Prose inside `\emph{}`, `\textbf{}`, headings, or captions may be edited when
  it falls within scope; retain the command, options, braces, keys, and math.
  Leave verbatim, listings, minted, and inline code untouched.
- Keep an already clear sentence. Formality does not require heavier synonyms,
  and sentence length alone is not a reason to split it.

## Edit with relevant guidance

Read supporting material only as needed:

- [Style guardrails](references/style-guardrails.md): voice, clarity, notation,
  consistency, and claim strength. These are editing choices, not universal laws.
- [Section anatomy](references/section-anatomy.md): section-specific purposes;
  adapt to the article type and the verified target requirements.
- [Chinglish patterns](references/chinglish-patterns.md): common constructions
  when they actually occur; do not infer errors from the author's identity.
- [Academic phrasebank](references/academic-phrasebank.md): optional phrasing
  patterns. Fill only with claims already supported by the manuscript.

Lead results prose with the finding and its actual evidence. Improve method
descriptions without inventing missing reproducibility details. Suggest missing
limitations or ethics content for author review; formatting requirements belong
to the specified venue/year/track/stage, not to generic prose polishing.

## Verify and deliver

Review the diff for accidental changes to meaning, scientific tokens, commands,
and argument balance. For a local project, use its configured engine/backend to
check compilation when available. For pasted text or missing build tools, mark
compilation as not performed or unverified rather than claiming success.

Return the edited text or changed files, intensity, representative before/after
edits with reasons, substantive questions for the author, and observed build/
visual-check status. Scale the explanation to the edit; a large manuscript can
use a grouped change summary plus the full diff rather than an item for every word.
If new compilation errors arose, repair the text edit or use `latex-rescue` when
available. Preserve unrelated author changes during rollback.
