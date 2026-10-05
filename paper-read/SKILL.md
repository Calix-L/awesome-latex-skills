---
name: paper-read
description: Summarize and critically analyze academic papers supplied as PDFs, text, arXiv links, or journal URLs. Ground claims in the inspected version and source locations; support focused questions, deeper appraisal, and cross-paper comparison.
metadata:
  version: "1.23.0"
---

## Choose the depth

Match the user's question; a focused question need not produce a full-paper report.

| Mode | Read for | Output |
|---|---|---|
| `skim` | Problem, approach, main results, figures, stated limitations | Concise overview with coverage limits. |
| `read` (default) | Method, setup, results, and claim/evidence alignment | Structured account with source locations. |
| `deep` | Assumptions, equations, ablations, implementation details, supplements | Critical appraisal and unresolved questions. |

Depth describes coverage, not a guaranteed duration. A skim cannot certify
methodological soundness. Use the user's language unless they request otherwise.

## Acquire and identify the evidence

Use the supplied text or accessible PDF. For a link, obtain the paper through
available browsing/download tools; record title, authors, identifier, exact
version, publication status, and available main/supplementary files.
An arXiv `vN` suffix identifies a specific version; preserve it instead of silently
switching to the newest paper. New and legacy identifiers are described in the
[official arXiv identifier guide](https://info.arxiv.org/help/arxiv_identifier.html).

Extract with an available PDF reader, PyMuPDF, or Poppler. Use task-local files
and paths appropriate to the host; do not assume `/tmp` or a particular shell.
If extraction loses columns, math, tables, or figures, inspect rendered pages
and state what remains unreadable. A missing tool does not require installing
software when supplied text or another reader is sufficient.

For inaccessible/paywalled material, look for a legitimate author or repository
copy, identify version differences, or request the relevant text. Do not infer
the full paper from an abstract or pretend the supplement was inspected.

## Analyze the inspected material

Read [reading-framework.md](references/reading-framework.md) for mode-specific
strategies and article-type adjustments. For `read` and `deep`, use the relevant
items from [critical-appraisal.md](references/critical-appraisal.md).

Connect the problem, method, assumptions, training/inference setup, data,
baselines, metrics, and results. Preserve units, denominators, uncertainty,
dataset splits, and relative versus absolute improvements. Do not call a result
statistically significant from its size alone.

For important claims, provide the claim, supporting section/table/figure/equation,
what the evidence establishes, and any gap. Use printed page numbers where
available and distinguish them from PDF page indexes. Distinguish an author's
claim, your interpretation, an algebraic consistency check, and reproduced evidence.
Reading a paper is not an independent reproduction or proof audit.

Treat publication status as context, not a substitute for evidence. The same
criteria apply to a preprint and a peer-reviewed article. A repository listing
or arXiv upload alone does not establish peer-review status.

Verify external comparisons through inspected primary sources. If only the
paper's related-work account is available, attribute that comparison to the
authors; do not invent a literature history or recommend unread papers as evidence.

## Compare papers and report

For multiple papers, align task, dataset/split, metric, evaluation protocol,
resources, and version before comparing numbers. Label incomparable results.
Explain whether apparently contradictory claims involve different settings.

Deliver an answer centered on the user's question, key conclusions with source
locations, strengths and limitations supported by evidence, inspected coverage,
and unresolved uncertainties. For implementation requests, separate published
settings, public-code defaults, and missing details. Relate findings to the user's
stated research goal without assuming one from the author list or venue.

Use `latex-polish` or `latex-fmt` only for an additional requested manuscript task
and only when the corresponding skill is available.
