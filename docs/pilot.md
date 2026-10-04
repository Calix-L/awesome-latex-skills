# A small, attributable evaluation pilot

[简体中文](pilot_CN.md) · [Full protocol](evaluation.md) · [Case catalog](../evaluation/cases.json)

The repository currently has ten synthetic tasks and maintainer-authored
reference artifacts. It does not contain an independent model efficacy result.
This pilot prepares a bounded experiment; preparation calls no model and
proves no improvement.

## Freeze the question before running

Compare baseline and supplied-skill conditions on the same inputs, exact model
version, decoding settings and tool access. Start with these three cases:

| Case | Main question | Evidence beyond literal checks |
|---|---|---|
| `rescue-errors` | Does repair preserve quantities and unknown keys? | Actual compile outcome, unresolved references, math review |
| `polish-scope` | Does editing retain scope and negative claims? | Independent meaning review with exact excerpts |
| `pdf-table` | Does reconstruction preserve cells and uncertainty? | Original/candidate page comparison and reviewer findings |

Use two trials per case to exercise the process: **12 runs, six pairs**. This is
a process pilot, not enough to establish broad quality gains. Decide in advance
who runs tasks, who reviews them, how conditions are concealed from reviewers,
which outcomes will be reported, and a maximum budget. Keep unavailable
token/cost values null; do not estimate them from transcript length.

## Prepare isolated workspaces

```sh
als benchmark prepare --case rescue-errors --case polish-scope --case pdf-table --trials 2 --seed 17 --output evaluation-runs/pilot-01
```

The result must say `prepared-not-run`, with 12 runs. The coordinator reads
`evaluation-runs/pilot-01/batch.json` for the randomized schedule. Expose only
one prepared task to each fresh agent session. Baselines must not discover
global skills, repository references, candidates or reviewer criteria. Record
any context contamination; random scheduling cannot prevent it by itself.

## Execute with actual settings

Use the [configured command runner](evaluation.md) or distinct manual sessions
following that protocol. Record actual agent/model/version/settings/trial/session
identity. Keep original transcripts and native tool evidence. For the command
runner, use your real runner specification:

```sh
als benchmark run --task evaluation-runs/pilot-01/tasks/rescue-errors-01-baseline --spec path/to/actual-baseline-spec.json
```

Run each of the 12 scheduled tasks separately. Every task needs a distinct
session ID, including the paired skill condition; do not reuse one specification
unchanged across sessions. A runner can call a paid provider; preparation and
reporting do not. Do not fill model identity or reviewer identity with examples.
Keep provider credentials outside task files and retained artifacts.

## Review after submission

Export rubrics outside the agent workspace:

```sh
als benchmark review-template --task evaluation-runs/pilot-01/tasks/rescue-errors-01-baseline --output work/rescue-baseline-rubric.json
```

The coordinator gives reviewers opaque candidate IDs and only the input,
submission and necessary evidence, withholding condition/model labels and
expected answers. Fill all rubric criteria with reviewer identity, score,
reason, actual `file:line` and an exact excerpt. The template remains unfilled
until reviewed. Put the completed review at that task's `human-review.json`
only after the agent session ends, following the [full protocol](evaluation.md).

## Retain failures and report separately

```sh
als benchmark report --batch evaluation-runs/pilot-01 --output work/pilot-report-01
```

Read `work/pilot-report-01/report.json` and `report.md`. Report all 12 scheduled
outcomes, including timeouts, missing submissions, contaminated sessions,
unreviewed artifacts and incomparable pairs. Separate literal checks, actual
compile/extraction evidence and human quality judgments. Pair summaries do not
replace failure inspection. Native reporting requires the actual selected
engine where compilation is applicable; absent native tools remain unverified.

Before publishing, check attribution/transcripts and reviewer evidence, redact
secrets, state synthetic task scope and sample size, and explain missing values.
Add failures to [failure-log.md](../evaluation/failure-log.md). Expand to all
skills and authorized real cases only after the pilot process is reproducible.
