# Sample PDF Reconstruction Test

This file simulates the extracted text blocks from a typical 2-page CS paper PDF, to be used for testing pdf2tex reconstruction logic.

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

- Document class: article (standard, single-column, Computer Modern fonts → pdflatex)
- Math: inline math with $, one display equation in equation environment
- Table: booktabs style (3 columns: l r r r)
- References: numeric citation style → \begin{thebibliography}
- No images detected (no image blocks)