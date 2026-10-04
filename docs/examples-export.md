# Copy an example into your own workspace

[简体中文](examples-export_CN.md) · [Task recipes](tasks.md) · [Documentation index](README.md)

The installed wheel contains all examples. `examples export` copies one into
a new workspace without TeX, PyMuPDF, model access or the source checkout:

```sh
als examples list
als examples export --case full-paper --output ../my-example
als verify example ../my-example
```

From a checkout without installing the CLI, use `python scripts/als.py` instead
of `als`. Choose a new destination outside the checkout or installed package's
bundled resources. The example paths below are relative to that destination.

Open `../my-example/report.html` for an offline guide with original/candidate
links, decisions, prerequisites and commands. `README.md` provides the same
instructions as Markdown. `--language zh` selects Chinese for these generated
guides; original source/decision text retains its own language.

## Choose a case

| `--case` | Original → candidate | What remains explicit |
|---|---|---|
| `full-paper` (default) | `case/before/` → `case/after/` | Full English/Chinese project, actual backend/font dependencies and unresolved timing protocol |
| `rescue` | `case/input.tex` → `case/output.tex` | Minimal error fixes, preserved unknown keys and ambiguous math |
| `polish` | `case/input.tex` → `case/output.tex` | Quantities, scope and negative claims require meaning review |
| `fmt` | `case/input.tex` → `case/output.tex` | Local-width repair; this is not an official venue kit |
| `read` | `case/input.md` → `case/analysis.md` | Conflicting results, assumptions and absent timing information |
| `pdf2tex` | `case/input.pdf` → `case/output.tex` | Table blanks/precision, figure uncertainty and unmatched references |

`examples list` keeps its five worked-example entries and adds the six
`export_cases`, including the separate complete manuscript. Only one case is
copied per export; use distinct destinations for different cases.

## Inspect, then work on a separate candidate

The full-paper export preserves hidden `case/after/.als.json`, local styles,
figures, bibliography and chapter files. Repository-level README links are
replaced by a generated standalone guide; source artifacts/decisions and the
MIT license retain their exact bytes.

From the exported directory, with the CLI installed:

```sh
als doctor --project case/after --skill latex-rescue
als build --project case/after --output ../example-build --until-stable --require-resolved
als build case/after/main-cn.tex --engine xelatex --backend bibtex --passes 3 --output ../example-chinese --require-resolved
```

The complete English candidate needs pdfLaTeX/BibTeX; the Chinese companion
needs XeLaTeX/BibTeX and Noto Serif CJK SC. Build helpers isolate generated
outputs from source trees. A native CI regression builds the exported original
(expected failure), English candidate and Chinese companion, then re-verifies
the unchanged export. For other cases, follow their generated guides. PDF
extraction/review needs the optional PyMuPDF library; copying a PDF does not.

Preserve an untouched export, create a separate candidate copy before agent
editing, and retain new build outputs outside both. Use the
[review workflow](review.md) to inspect changes. Original/candidate material is
maintainer-authored and synthetic. It contains answers/decisions and must not
be used as a blind agent evaluation workspace; use [pilot preparation](pilot.md)
for that purpose.

## Transfer and verify the initial bytes

Keep the entire exported directory together:

- `example.json` records case, source version, synthetic provenance, entry
  paths and each copied source path/size/SHA-256.
- `integrity.json` covers all exported files except itself, including both
  guides, the receipt, license and source files.
- `als verify example DIRECTORY` works after moving the directory, without
  reading the original package or repository. Changed, missing or additional
  files fail; copied-source receipt disagreements also fail.

Export status is `exported-not-run`, never a build or model-quality result.
Exit 0 means a complete initial copy; invalid inputs or failed publication
return 2. Verification returns 0 for matching bytes, 1 for mismatches, and 2
for invalid/missing manifests or malformed receipts consistent with their
manifest. Corrupted receipt bytes are reported as changed without interpreting
them. Anyone who can replace all files and manifests can produce a matching
directory; byte checks do not authenticate the publisher or scientific content.

Files are prepared in a temporary sibling directory, sealed, source membership
and bytes rechecked, and the complete staged delivery verified before rename.
Failed copying/rendering/sealing or a changed source produces no partial final
directory. Keep sources and destination unchanged during these point-in-time
checks; no concurrent editing lock or crash-durability guarantee is provided.
Copies are bounded to 2,000 source files, 8 MiB per source file or read
version/catalog metadata file, and 64 MiB total source/license bytes. Generated
receipt/manifest reads also obey the [artifact verifier's limits](verification.md).
