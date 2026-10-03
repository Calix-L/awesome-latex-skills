# pdf2tex worked case

This synthetic task is maintained under the repository's MIT license. It is
an illustrative candidate, not an independent Agent benchmark result.

## Input and task
Read [input.pdf](input.pdf).
Use the `pdf-table` task in [the case catalog](../../evaluation/cases.json).

## Candidate and decisions
Review [output.tex](output.tex) and [report.md](report.md).
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
