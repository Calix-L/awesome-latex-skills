# latex-fmt worked case

This synthetic task is maintained under the repository's MIT license. It is
an illustrative candidate, not an independent Agent benchmark result.

## Input and task
Read [input.tex](input.tex).
Use the `fmt-column` task in [the case catalog](../../evaluation/cases.json).

## Candidate and decisions
Review [output.tex](output.tex) and [report.md](report.md).
The detail below is rendered from its actual native build; the full page and logs
are in the CI artifact. [Preview provenance](../../assets/previews/README.md).

<img src="../../assets/previews/fmt-column.png" alt="Actual pdfLaTeX column showing a local-width panel, retained table values and resolved references" width="360">

The candidate was authored by the maintainer workflow; decisions and unresolved
content remain reviewable. A different valid output may also satisfy the task.

## Execute and inspect
From the repository root, run `python scripts/als.py examples run --output work/example-run`.
Choose a new destination. The verifier retains actual logs, PDFs, page previews,
source hashes, diffs and limited invariant scores. It requires PyMuPDF and,
unless `--allow-unverified` is explicitly used, pdfLaTeX.

## Limits
Read the candidate's report before reuse. Compilation and literal checks alone
do not establish scientific fidelity, reading quality or venue compliance.
