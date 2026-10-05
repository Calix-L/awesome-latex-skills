# Manuscripts in subdirectories

[简体中文](relative-paths_CN.md) · [Project inspection](project.md) · [Build evidence](build-inputs.md)

Choose a project root that contains the main source and its shared resources:

```text
manuscript/
├── paper/main.tex
├── shared/section.tex
├── shared/refs.bib
├── styles/local.sty
└── figures/plot.pdf
```

Inside `paper/main.tex`, literal `../shared/section`, `../shared/refs` and
`../styles/local` are internal project dependencies. Inspection resolves them
relative to **the selected main source directory**, including commands found in
included sources and local classes/packages. It does not switch the working
directory whenever another source is read. Dot prefixes remain supported.

```sh
als project init manuscript --main paper/main.tex --engine pdflatex --backend bibtex
als project check manuscript --bundle ../inspection
als verify inspection ../inspection
als build --project manuscript --output ../build --until-stable --require-resolved
```

The report keeps the literal request and source location, while resolved files
and fingerprints use canonical paths from the project root (`shared/section.tex`).
Aliases therefore share graph identity: repeated inputs are flagged and cycles
are detected. `includeonly` comparison remains literal, matching its declared
names rather than assuming two spellings have the same runtime meaning.

Each traversed component is checked before normalization. Paths that leave the
root, symlinks even in cancelled components, and `..` through missing directories
or ordinary files are refused. Absolute paths, drive names, backslash/control
characters and macro expansion are not made into guessed local paths. Main
configuration, watched-input selectors and delivery manifest paths retain their
existing strict portable syntax. This changes dependency lookup only.

## BibTeX with explicit relative names

BibTeX runs in the fresh output directory so its logs, BBL and child AUX files
remain isolated. Names beginning `./` or `../` bypass ordinary Kpathsea search
paths, so setting `BIBINPUTS` alone cannot give them the main directory's meaning.
[Kpathsea search rules](https://tug.ctan.org/systems/doc/kpathsea/kpathsea.html#Searching-overview)
and [BibTeX invocation](https://www.tug.org/texinfohtml/web2c.html#bibtex-invocation)
describe the relevant interfaces.

For literal explicit relative database/style declarations in reachable generated
AUX files, the helper stages exact resource copies with output-local aliases and
an adapted AUX tree inside `bibtex-inputs/`. Preparation does not edit source or
original AUX bytes; later native passes still update their output AUX normally.
Ordinary names retain the previous invocation. Child AUX references
are adapted to staged copies; comments and unrelated AUX files are ignored.

The bibliography step's additive `prepared_inputs` rows record actual retained
filenames, byte counts, hashes, kinds and original resource paths. Copies and
original resources are checked around bibliography execution and at the end.
Review retains the staged AUX/database/style evidence, verifies its hashes and
binds original resources inside the supplied project. Missing, changed or external
originals prevent publishing a review. No report schema numbers change.

Preparation supports literal one-line `bibdata`, `bibstyle` and `@input` records,
without interpreting custom AUX syntax or expanding macros. It reads at most
128 reachable AUX files of 2,000,000 bytes each, and prepares at most 128 resources
of 64 MiB each and 256 MiB total. Missing or oversized inputs fail explicitly.
Native `--watch-input` remains relative to the main source directory; this is
not a claim that every external/generated native input is monitored.

Native controls compile shared sections, local class/package paths and parent
graphics, compare observed recorder paths, and run both BibTeX and Biber with
parent bibliographies. They also verify retained staged evidence and unchanged
source bytes. These are synthetic tooling checks, not scientific validation.
