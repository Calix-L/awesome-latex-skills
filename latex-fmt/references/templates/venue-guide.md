# Venue Guide

This is a source directory and a set of pitfalls, not an official template
distribution. Select **venue + year + track/article type + review/preprint/final**
before applying rules. Follow the exact linked author kit; a `.sty` is a package,
not a document class. Do not invent filenames from the conference name.

## Verified corrections (checked 2026-10-04)

### NeurIPS 2026 main track

- Use the year's style package with `article`, as shown in the official kit.
- Review: 9 content pages; references, technical appendices, and checklist are
  excluded. Camera-ready permits one additional content page.
- Submit paper, references, appendices, and checklist in one PDF. The checklist
  is not a separate required PDF upload.
- Review submissions and linked/supplementary material must be anonymous.
- A section specifically titled "Broader Impact" is not mandatory. Address
  relevant impacts and complete the checklist without inventing claims.

Sources: [2026 call and author-kit link](https://neurips.cc/Conferences/2026/CallForPapers),
[main-track handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook).

### KDD 2026 research track, cycle 2

- Anonymous review; the recommended class options are
  `\documentclass[sigconf,anonymous,review]{acmart}`.
- Main paper: 8 content pages, followed by references and optional appendix
  without page limits. Camera-ready and other tracks have separate rules.
- Do not carry an author-visible camera-ready preamble into review.

Source: [research-track call](https://kdd2026.kdd.org/research-track-call-for-papers/).

### TMLR

- Double-blind review; submissions and supplementary materials are anonymous.
- Use the official TMLR stylefile and template, not plain `article` alone.
- Appendices can follow references; PDF/ZIP supplementary uploads are allowed
  (up to 100 MB). Open reviewing does not mean authors are visible during review.

Source: [author guide](https://jmlr.org/tmlr/author-guide.html).

## Official entry points

Rows below route to rules; they do not certify every current requirement.
For venues not covered by the verified corrections above, read the relevant
year/track's instructions and author kit before declaring compliance.

| Venue | Official entry point | What to establish |
|---|---|---|
| NeurIPS | [2026 call](https://neurips.cc/Conferences/2026/CallForPapers) | Main vs datasets/evaluations vs position track; style options and checklist |
| ICML | [2026 call](https://icml.cc/Conferences/2026/CallForPapers) | `article` plus official style package; review vs accepted mode and `.bst` |
| CVPR | [2026 author guidelines](https://cvpr.thecvf.com/Conferences/2026/AuthorGuidelines) | `article` plus `cvpr` package; review/final options and supplement |
| ACL / EMNLP | [ACL Rolling Review](https://aclrollingreview.org/cfp), [official style repository](https://github.com/acl-org/acl-style-files) | ARR/venue cycle, paper type, Limitations rules, and review option |
| AAAI | [AAAI](https://aaai.org/) | Exact edition/track, official style, page budget, and banned packages |
| ICLR | [ICLR](https://iclr.cc/) | Exact year's author guide, style package, length budget, and review mode |
| ECCV | [2026 author guide](https://eccv.ecva.net/Conferences/2026/AuthorGuide) | Follow linked author kit; do not invent a two-column `eccv.cls` |
| TMLR | [author guide](https://jmlr.org/tmlr/author-guide.html) | Official style and anonymous review; supplement rules |
| IEEE | [template selector](https://template-selector.ieee.org/) | Specific conference/journal, class options, length, and author block |
| Nature | [formatting guide](https://www.nature.com/nature/for-authors/formatting-guide) | Specific journal and article type; word counts, methods, figures |
| Science | [author information](https://www.science.org/content/page/instructions-preparing-initial-manuscript) | Article type, manuscript stage, supplementary structure |
| COLING | [International Committee on Computational Linguistics](https://www.coling.org/) | Exact edition/track, author kit, anonymity, and page limits |
| KDD | [2026 research call](https://kdd2026.kdd.org/research-track-call-for-papers/) | Track/cycle, review vs final length, ACM options, and anonymity |
| SIGIR | [2026 full papers](https://sigir2026.org/en-AU/pages/submissions/full-papers-track) | Full vs short papers, anonymity options, bibliography, and appendix limits |
| Interspeech | [ISCA](https://www.isca-speech.org/) | Exact edition's template, reference-page allowance, anonymity, and audio supplement |

If a page cannot be read, request the official kit or mark its rules unverified.
SIGIR's full-paper page was reachable but not extractable during this update;
this guide does not assert its current limits or anonymity options.

## Historical template example

The repository's `tests/fixtures/fmt/post_neurips.tex` demonstrates the NeurIPS
2025 package-loading pattern, not a complete 2026 submission. Official templates
and bibliography assets are deliberately not bundled. Obtain the requested kit
and follow its sample document, including the bibliography and checklist.
