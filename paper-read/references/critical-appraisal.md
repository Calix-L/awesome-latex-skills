# Critical Appraisal

Use the parts relevant to the user's question and the paper's contribution.
Evaluate individual claims against the inspected evidence. A checklist omission
is a question to investigate, not by itself proof that a result is invalid.

## Match evidence to the claim

| Claim type | Examine | Limit the conclusion to |
|---|---|---|
| Empirical improvement | Task/split, metric, comparator, evaluation protocol, tuning and run variation | The measured setting and reported uncertainty |
| Efficiency | Hardware, precision, batch size, workload, quality target, implementation and measurement method | The measured resource and operating conditions |
| Generalization or robustness | Held-out populations, shifts, stressors, selection and contamination risks | The domains and perturbations actually assessed |
| Theoretical guarantee | Definitions, theorem statement, assumptions, proof dependencies and applicability | The stated assumptions; a reading is not an independent proof audit |
| Dataset or benchmark | Collection/annotation procedure, consent or access constraints where relevant, coverage, splits, leakage and measurement validity | The documented population and intended use |
| Survey or synthesis | Search scope, inclusion criteria, source versions, conflicting evidence and omissions | The inspected literature and stated search coverage |

Keep an evidence ledger for the claims that determine the answer:

| Claim | Source location | Evidence inspected | What it supports | Gap or next check |
|---|---|---|---|---|
| Authors' claim, with its scope and units | Section/table/figure/equation; distinguish printed page from PDF index | Reported result, proof, data or cited primary source | A bounded conclusion | Missing setup, inaccessible artifact, untested setting or unresolved inference |

Distinguish **supported in the inspected setting**, **partially supported**,
**not established by the inspected material**, and **cannot assess with available
evidence**. These are claim-level descriptions, not a universal paper score.
Missing evidence and contrary evidence are different findings.

## Methods and comparisons

- Identify the problem, intended use and assumptions before judging the method.
  Check whether the description specifies the choices needed for the user's goal.
- Select relevant established and contemporary baselines for the claimed scope.
  Baseline age alone does not determine its strength. Verify an external
  state-of-the-art comparison through primary sources and date the search.
- Align task, split, preprocessing, metric definition, evaluation protocol and
  resources before comparing numbers. Different budgets can be a meaningful
  comparison when disclosed; do not infer equal conditions from a shared dataset name.
- Published baseline numbers can be usable when protocols match. Identify which
  results were rerun, inherited or taken from another source, and which conditions
  are unknown. Mark incomparable results instead of ranking them.
- For component claims, examine controls or ablations that isolate the proposed
  explanation. Interacting components may require joint ablations. Report the
  tested scope; an ablation on one dataset does not establish the mechanism everywhere.
- For a theorem, distinguish a gap in the proof from an assumption that restricts
  its application. Restrictive assumptions do not by themselves invalidate a proof.

## Results, uncertainty and practical value

- Check metric units, denominators, aggregation and operating point. Distinguish
  percentage points from relative percentages. An appropriate primary metric can
  still omit important failure modes or population differences.
- Identify the sources of variation relevant to the claim: sampling, random seeds,
  initialization, prompts, annotators or environments. Record the number and unit
  of repeats and any selection of a best run or checkpoint.
- Interpret intervals, statistical tests and effect sizes using the reported
  method and assumptions. Do not invent significance from a gain's magnitude.
  A single run limits assessment of run variation; it does not automatically
  invalidate deterministic results, theoretical claims or every reported measurement.
- Relate practical value to the task, cost, reliability and baseline. There is no
  universal percentage gain or speedup threshold for novelty or usefulness.
- Inspect qualitative-example selection, failure cases, plotting scales and
  captions. State whether examples are illustrative, typical or systematically
  sampled when the material establishes that distinction.
- Check whether claims of robustness, generalization or efficiency extend beyond
  the evaluated shifts, populations or resource measurements. Narrow the conclusion
  to the evidence rather than labeling the whole paper with a slogan.

## Reproducibility and data integrity

Separate what was **reported**, what is **available**, what you **ran**, and what
you **reproduced**. A repository link is not verification that its code runs.

- Record exact paper/code/checkpoint versions and artifact access dates when
  inspected. A promised future release is unavailable evidence today; do not
  predict whether authors will fulfill the promise.
- Compare paper settings with public-code defaults. Note preprocessing, splits,
  hyperparameters, stopping/checkpoint selection, dependencies and hardware that
  are missing or different. Avoid filling those gaps with guessed defaults.
- For private or restricted datasets, describe documented access or independent
  verification routes and what the reader cannot check. Limited public access is
  a reproducibility constraint, not evidence of fabrication or an invalid result.
- Check split definitions and possible overlap, including participants, time,
  near-duplicates and training/evaluation contamination as appropriate. Distinguish
  demonstrated leakage from a plausible risk and from an unassessed possibility.
- Record runtime, memory, accelerator and measurement conditions when needed to
  assess feasibility. A timing claim without hardware details is hard to transfer
  to another environment; reading it does not establish a universal latency.

## Report for the user's purpose

Explain the contribution relative to inspected prior work: new problem, method,
insight, combination, dataset, benchmark, analysis or incremental improvement.
Novelty and utility depend on context; do not rank them by arbitrary gain thresholds.

For understanding, give the conclusion and its evidence limits. For implementation,
identify usable artifacts, published settings and unresolved blockers. For choosing
a direction, connect benefits and limitations to the user's constraints. Give a
venue-style accept/reject recommendation only when requested and with the relevant
criteria; ordinary paper reading does not require such a verdict.

Assess writing when it affects understanding: consistent terms and notation,
legible figures, traceable evidence, and an abstract that matches the actual scope.
Separate presentation problems from methodological problems. Finish with the
specific evidence that would resolve the most consequential uncertainty.
