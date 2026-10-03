# Preview provenance

These PNGs are actual PDF renderings at 144 DPI, without retouching.
They are selected details, not whole-page layout certification.

- [fmt-column.png](fmt-column.png): page 1 of the candidate's pdfLaTeX output,
  clip `(65, 115, 310, 610)` PDF points. Source:
  [examples/fmt/output.tex](../../examples/fmt/output.tex), built by
  [Tests run 37152008850](https://github.com/Calix-L/awesome-latex-skills/actions/runs/37152008850)
  at commit `40604cafeb7a4e9fbc139e77cdd52c02b3ebd4b4`. The candidate remains
  unchanged in this release. Full PDF/logs are in its worked-example artifact.
- [pdf-table.png](pdf-table.png): page 1 of the committed synthetic
  [input.pdf](../../examples/pdf2tex/input.pdf), clip `(37, 130, 503, 299)` points.
  This is original input evidence, not a recovered figure or model response.

Both inputs are maintainer-authored synthetic examples under the repository's
MIT license. Visuals do not measure a skill's effect on an agent.

## Complete manuscript: original failure and repaired pages

The following evidence comes from the successful
[native compile job](https://github.com/Calix-L/awesome-latex-skills/actions/runs/37157603294/job/111304167341)
at commit `55dec72b106ccab7f3847c9c09f3e7c10314520c`. Its complete manuscript
verification reports English before=failed, after=success, Chinese=success,
unchanged inputs, no literal content flags and one open author decision.
The manuscript sources remain unchanged by the later test/docs fixes.

- [full-paper-before.svg](full-paper-before.svg) is a designed log excerpt,
  **not a screenshot or an original PDF**. The actual first error is at
  `before/sections/methods.tex:13`: file `figures/panel-missing` not found.
  The associated local-width source excerpt is copied from the same original
  manuscript. Retained original `main.log` SHA-256:
  `3aa10946e8118cef98b0f27012935fc8d22405b98931f5c35a4c22afb68f1e10`.
- [full-paper-after.png](full-paper-after.png) renders page 1 of the actual
  repaired English PDF with Poppler, crop `(65, 230, 565, 690)` PDF points,
  1000 × 920 pixels. PDF SHA-256:
  `bda46b150e40007d15b590075946dacb39c9178c239fa682f99af01de64c063c`.
- [full-paper-chinese.png](full-paper-chinese.png) renders the whole first
  page of the actual XeLaTeX companion with Poppler. PDF SHA-256:
  `2caee39fbdf9c06dccf5f0894ff91743c81a2b0fa6e0e3a3dedb34e69b3bd49d`.

Download `full-paper-evidence` from that run to inspect the original failure,
repaired PDFs, review HTML and native reports. Reproduce the English crop with:

```sh
pdftoppm -f 1 -l 1 -r 144 -x 130 -y 460 -W 1000 -H 920 -singlefile -png build-after/main.pdf full-paper-after
pdftoppm -f 1 -l 1 -r 144 -singlefile -png build-chinese/main-cn.pdf full-paper-chinese
```

The earlier formatting/table details used PyMuPDF. These complete-project
previews use Poppler; neither pipeline retouches the manuscript's content.
