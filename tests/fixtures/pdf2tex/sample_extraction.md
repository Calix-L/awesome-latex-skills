# Sample PDF Reconstruction Test

This synthetic fixture simulates extracted blocks from a two-page CS paper.
Its claims and results are invented for manual reconstruction evaluation; they
are not evidence about a real method. The abstract/table discrepancy is deliberate.

## Metadata (from PDF)

- Creator: "LaTeX with hyperref"
- Producer: "pdfTeX-1.40.25"
- Title: "A Simple Baseline for Image Classification"
- Author: "Zhang, Li, Wang"

## Extracted Font Info (from pdffonts)

- CMR10 → Computer Modern Roman (standard LaTeX)
- CMBX12 → Computer Modern Bold (section headings)
- CMMI10 → Computer Modern Math Italic (inline math)
- CMSY10 → Computer Modern Symbol (math operators)

## Page 1 Text Blocks

### Title Block
- Font: CMBX12, Size: 14.4, Bold, Centered
- Text: "A Simple Baseline for Image Classification"

### Author Block
- Font: CMR10, Size: 10, Centered
- Text: "Zhang, Li, Wang"
- Text: "Tsinghua University"

### Abstract
- Font: CMBX10 + CMR10, Size: 10
- Text: "Abstract — We propose a simple baseline for image classification that achieves 92.3% top-1 accuracy on ImageNet using a standard ResNet-50 architecture with minor modifications. Our method outperforms more complex approaches while being fully reproducible."

### Section 1: Introduction
- Font: CMBX12, Size: 12, Bold
- Text: "1 Introduction"
- Body: "Image classification has been a fundamental task in computer vision. Deep learning methods have achieved remarkable progress on large-scale benchmarks such as ImageNet. However, recent methods increasingly rely on complex training strategies that are difficult to reproduce."

### Section 2: Method
- Font: CMBX12, Size: 12, Bold
- Text: "2 Method"
- Body: "Our approach consists of three components: data augmentation, label smoothing, and knowledge distillation. Let $x$ denote the input image and $y$ the label. The training objective is:"
- Math block (display, CMMI10+CMSY10):
  "$\mathcal{L} = \mathcal{L}_{CE}(f(x), y) + \lambda \mathcal{L}_{KD}(f(x), g(x))$"
- Body: "where $f$ is the student model, $g$ is the teacher model, and $\lambda = 0.5$ controls the distillation strength."

### Section 3: Experiments
- Font: CMBX12, Size: 12, Bold
- Text: "3 Experiments"

- Table region:
  - Header: Method | Top-1 | Top-5 | FPS
  - Row 1: ResNet-50 | 76.1 | 92.9 | 286
  - Row 2: ResNet-101 | 77.6 | 93.7 | 142
  - Row 3: Ours | 78.2 | 94.1 | 268

## Page 2 Text Blocks

### Section 4: Conclusion
- Font: CMBX12, Size: 12, Bold
- Text: "4 Conclusion"
- Body: "We presented a simple yet effective baseline for image classification. Our results demonstrate that careful training strategies can match or exceed complex architectures while remaining easy to reproduce."

### References
- Font: CMR9, Size: 9
- [1] He, K. et al. Deep residual learning. CVPR 2016.
- [2] Hinton, G. et al. Distilling the knowledge. NeurIPS 2015.
- [3] Zhang, H. et al. MixUp. ICLR 2018.

## Expected Reconstruction Notes

- Candidate class/engine: `article` with pdfLaTeX can reproduce the supplied
  content. Font and producer metadata do not recover the original source setup.
- Preserve the loss terms and `lambda = 0.5`; do not infer extra definitions or
  alter grouping. The display can use `equation` if a number is desired; no
  original equation tag was supplied here.
- Preserve all four table columns (`l r r r`) and their values. `booktabs` is an
  optional candidate style, not a recovered original package.
- Preserve both the abstract's 92.3% top-1 claim and the table's 78.2% value for
  Ours. Flag their inconsistency with locations; do not silently reconcile them.
- Keep the supplied reference strings and numeric markers. A reconstructed
  `thebibliography` is a possible output choice; no original `.bib` database,
  source keys or complete bibliographic metadata were supplied.
- No image blocks were supplied. This does not rule out vector/composite figures
  in a real PDF; unavailable visual evidence remains unverified.

For an independently compilable edge-case example, see
[reconstruction_edges.tex](reconstruction_edges.tex). It exercises grouping,
merged headers, blank cells, precision and visible uncertainty; it is not an
automatically recovered version of this paper.
