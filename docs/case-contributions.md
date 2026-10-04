# Contribute a reproducible manuscript case

[简体中文](case-contributions_CN.md) · [Contribution process](../CONTRIBUTING.md)

Existing cases are synthetic. Real cases are welcome when the contributor can
provide redistribution permission, source provenance and reproducible evidence.
Do not describe a fixture as a real user case without that evidence. Anonymizing
a manuscript does not itself establish redistribution permission.

## A case package

Use a new `examples/CASE_ID/` directory with:

| Artifact | Required content |
|---|---|
| `README.md` | Problem, case origin, scope, supported commands, prerequisites, expected outcomes and limitations |
| `PROVENANCE.md` | Synthetic/real classification, original source, redistribution permission/license, attribution and redaction summary |
| `before/` | Minimal original source tree reproducing the problem; original failure preserved |
| `after/` | Reviewable candidate tree; no hidden repairs to the original |
| `decisions.md` | Each substantive edit, unchanged quantities/claims, unresolved choices and actual author confirmation if obtained |

Preserve third-party notices and licenses. Keep generated PDFs/logs/reports in
fresh external output directories; retain downloadable CI evidence instead of
committing environment-specific build directories. A PDF input may be included
when it is essential to recovery and its provenance/permission is documented.

## Acceptance checklist

- Remove credentials, personal identifiers and confidential reviewer/author
  material; inspect TeX, comments, BibTeX, filenames and PDF metadata too.
- Include all required local source/style/figure resources. State separately
  any official kit or external dependency the user must supply. Do not silently
  fetch files during a test.
- Record main file, actual engine/backend, relevant package/font requirements
  and tool versions used to obtain evidence. Multiple roots need explicit selection.
- Reproduce the original failure, the candidate outcome and the protected
  literals. A deliberately unresolved citation must remain explicit.
- Keep actual native logs, source differences, available PDFs/page comparisons
  and source fingerprints. Distinguish missing tools, failed builds and content
  uncertainty. Do not manufacture a PDF for a failed original build.
- Bind checks to meaningful failures: missing input, template conflict,
  changed meaning, absent cell, citation invention or lost page scope. Simple
  string retention alone cannot establish semantic quality.
- Identify whether candidates are maintainer edits or attributed model outputs.
  Only the latter, with paired controls and human review, can enter an efficacy
  comparison under the [evaluation protocol](evaluation.md).

## Initial coverage targets

Prioritize multi-file projects with local styles/classes, Chinese/English
content, BibTeX/Biber resources, multiple document roots and template migrations.
Add a case only when its failure and acceptance criteria differ materially
from an existing case. Recovery cases should include representative math,
table blanks/precision and uncertainty in vector figures or scanned material.

Use the [task recipes](tasks.md) and [project review guide](review.md) to prepare
evidence. Integrate accepted cases into the runner and CI rather than adding
unexercised source trees. Follow the repository's main-only contribution policy;
never commit private original manuscripts as evidence.
