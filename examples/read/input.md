# Synthetic paper: Sparse detection example

This is fictional evidence for an evaluation task, not a published paper.

## Abstract
The authors claim 10x faster inference and 92.3% mAP on dataset C.

## Method
The method uses a token scorer, a top-k selector, and sparse attention.
Attention cost is described as O(nk); scorer and selection cost are not reported.

## Results
| Method | mAP | FPS on device V |
|---|---|---|
| Baseline A | 42.0 | 28 |
| Baseline B | 46.2 | 42 |
| Proposed | 45.8 | 286 |
Removing the token scorer reduces mAP by 2.1 points.
Batch size, timing protocol, repetitions and seeds are not supplied.

## Conclusion
The authors propose extending the method to video.
