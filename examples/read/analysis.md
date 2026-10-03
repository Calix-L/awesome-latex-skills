# Evidence-based reading

## Claim and evidence
The Abstract claims 92.3% mAP, whereas the Results table reports 45.8 mAP
for Proposed. Preserve this discrepancy; no corrected number is inferred.
The table shows 286 versus 28 FPS against Baseline A, approximately 10.21x
under the reported device setting. Batch size and timing protocol are missing,
so a broader speed claim remains unverified.
Proposed has 0.4 lower mAP than Baseline B (45.8 versus 46.2), despite higher FPS.

## Mechanism and scope
Method lists a token scorer, top-k selector and sparse attention. Its O(nk)
description does not account for unreported scorer/selection overhead.
The Results ablation reports a 2.1-point mAP drop without the scorer; this is
evidence about that tested intervention, not proof of universal necessity.

## Reproduction questions
Request data splits, preprocessing, scorer/selector configuration, checkpoints,
batch size, timing procedure, repetitions, seeds and versions. Do not fill them
with assumed defaults. No independent reproduction or proof was performed.
