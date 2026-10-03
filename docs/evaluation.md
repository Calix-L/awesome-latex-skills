# Evaluate behavior, with evidence

The [catalog](../evaluation/cases.json) contains ten synthetic tasks: two per
skill. They cover unresolved keys, ambiguous scripts, causal/negative claims,
local widths, missing author kits, conflicting results, conditional proofs,
blank cells, vector figures, and selected-page scope. The supplied candidates
are **maintainer-authored examples**, not independent model responses.

## Prepare an honest paired comparison

```sh
python scripts/als.py evaluate validate
python scripts/als.py evaluate prepare --case polish-scope --mode baseline --output evaluation-runs/baseline-01
python scripts/als.py evaluate prepare --case polish-scope --mode with-skill --output evaluation-runs/skill-01
```

Each task contains identical `TASK.md`, unchanged `inputs/`, an empty
`submission/`, and `run.json`. Only the skill condition receives the selected
self-contained bundle in `context/`. Neither preparation includes reference
answers, automatic checks, or reviewer criteria. Keep those outside the agent's
workspace. Do not expose the repository to a supposedly blind baseline.

Run the two tasks in **fresh, distinct sessions** with the same agent, exact model
version, decoding settings, tool access and task prompt. Disable automatic/global
skill discovery in the baseline; record any unavoidable implicit context. Load
only the supplied context in the skill condition. Fill `agent`, `model`,
`model_version`, `settings` (including tools/temperature/context policy), `trial`,
and `session_id` with actual values in `run.json`; never substitute guessed
values. The suite does not call an external model or incur model charges.

Input, prompt, case and skill SHA-256 fingerprints detect changed prepared
inputs or context. They establish artifact provenance, not proof that a claimed
model/session actually ran: retain raw agent transcripts and tool evidence too.

## Score artifacts, then review quality

```sh
python scripts/als.py evaluate score --case polish-scope --submission evaluation-runs/baseline-01/submission --record evaluation-runs/baseline-01/run.json --output evaluation-runs/baseline-score.json
python scripts/als.py evaluate score --case polish-scope --submission evaluation-runs/skill-01/submission --record evaluation-runs/skill-01/run.json --output evaluation-runs/skill-score.json
python scripts/als.py evaluate compare --baseline evaluation-runs/baseline-score.json --with-skill evaluation-runs/skill-score.json --output evaluation-runs/comparison.json
```

Automatic checks audit **literal invariants only**. A retained number can still
have the wrong unit, row or meaning. Missing deliverables fail even an `absent`
check. Actual compilation/extraction and human review remain separate evidence.
Read the case's four reviewer questions after the agent has submitted.

For human review, give each criterion 0 (failed), 1 (partial), or 2 (satisfied),
with an explanation, an actual artifact `file:line` and an exact excerpt on that
line. Use a named reviewer and cover all criterion IDs. For example, the
structure below illustrates **one entry**; provide every criterion in the case:

```json
{
  "reviewer": "actual reviewer name",
  "criteria": {
    "meaning": {
      "score": 2,
      "reason": "Explain why the complete result preserves the source claim.",
      "evidence": "output.tex:7",
      "excerpt": "an exact excerpt from that actual line"
    }
  }
}
```

Pass `--review review.json` when scoring. The script validates the score and
evidence location; it cannot validate a reviewer's judgment. Without review,
the human score stays null. An unmatched or incomplete pair is refused; examples
and negative controls cannot become model comparisons. A single attributed pair
is an observation, not a general improvement estimate.

## Repeat and investigate failures

Prepare all ten cases with three trials per condition (60 independent tasks):

```sh
als benchmark prepare --trials 3 --seed 0 --output evaluation-runs/batch-01
als benchmark report --batch evaluation-runs/batch-01 --output work/batch-report-01
```

The seeded schedule randomizes task order. Preparation makes no model calls;
an untouched batch reports every task as **not-run**, with null time/cost and
zero comparable pairs. Each agent sees only its own prepared task directory.
Do not expose `batch.json`, other tasks, reference answers or scorer criteria
to it. Use a fresh session for every task, with the same actual model/settings.

Alongside each task's completed `run.json`, retain a nonempty raw transcript
and actual `execution.json`:

```json
{
  "schema": 1,
  "status": "completed",
  "elapsed_seconds": 12.5,
  "transcript": "raw-transcript.jsonl",
  "tokens": null,
  "cost": null
}
```

These values illustrate the schema, not a measured run. Measure elapsed wall
time from dispatch to completion, and explain queue/tool time in the actual
transcript or record. Status can be `completed`, `failed` or `timeout`; failed
runs remain included even with an empty submission. If the provider supplies
token counts, use `{"input": 123, "output": 45}`. A supplied cost needs a
nonnegative `amount`, `currency` and billing `source`; leave unavailable data
null instead of estimating it from an assumed price. Keep the transcript path
relative to its task. Human review, when performed, goes in `human-review.json`
with the existing evidence-backed rubric format.

The report retains every scheduled run, raw-transcript fingerprints, literal
checks, human evidence and pair rejection reasons. Reused sessions, changed
conditions or missing exact attribution prevent comparable pairs. A failed
run with valid attribution is still part of its pair; it is never silently
discarded. Native compilation runs independently on a unique submitted LaTeX
root with the selected engine, two passes and no guessed bibliography backend.
No root is `not-applicable`; absent tools or ambiguous roots are unverified.
Inspect unresolved references and build diagnostics separately from status.

JSON and Markdown summaries keep runtime outcomes, literal deltas, human
deltas, compilation, elapsed time and measured cost separate. Costs aggregate
only within their recorded currency, with the number of measured runs. There
is no inferred model identity, automatic human score or general improvement
claim. Preserve the complete batch and raw evidence when sharing a result.

Use multiple trials per case, preserve both conditions' failures, randomize
review order and conceal the condition from reviewers where possible. Report
model/settings, task coverage, compilation failures, literal checks and human
scores separately; include uncertainty and all attempted trials. Keep a failure
record with case ID, exact artifact/transcript, missed criterion, suspected
cause, proposed fix and fresh rerun. Confirm that fixing one case does not
remove source content or overfit its particular words.

The tests deliberately corrupt protected values, modify prepared context and
reuse session IDs to check rejection. These are regression controls for the
tooling; they are not measurements of a model's ability. No measured model gain
is claimed by this release.
