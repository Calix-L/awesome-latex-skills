# Review source changes and actual build evidence

Keep separate original and candidate project directories. The review tool
does not edit either one; its destination must be new and outside both trees.

```sh
als build path/to/before/main.tex --output work/before-build --backend bibtex --passes 3
als build path/to/after/main.tex --output work/after-build --backend bibtex --passes 3
als review --before path/to/before --after path/to/after --before-build work/before-build/build-report.json --after-build work/after-build/build-report.json --notes decisions.md --output work/review-01
# Chinese interface; original source/log/notes text stays unchanged
als review --before path/to/before --after path/to/after --output work/review-zh --language zh
```

Open `work/review-01/report.html` in a browser. Keep the generated directory
together: it includes an offline HTML report, JSON evidence, source diff,
retained build reports/logs, successful PDFs and page previews. No remote assets
or scripts are required. PyMuPDF is required when successful PDFs are supplied.
Source-only review needs only the Python standard library. The report opens with
counts, build states and a file-change list, followed by expandable source diffs,
added/removed literal values, author decisions and supplied PDF pages. Binary
changes remain visible even when a text diff cannot be produced. English is the
default; `--language zh` selects Chinese interface labels.

## Evidence remains separate

- **Source changes:** fingerprints and a unified diff for source, bibliography,
  styles/classes and project configuration; asset changes are listed by hash.
- **Content signals:** changed literal numbers, reference keys (including
  `nocite`), math delimited by `$`, `$$`, `\(` or `\[`, and complete literal
  common math environments such as `equation` and `align`.
  These flag review needs; unchanged tokens do not prove unchanged meaning.
- **Builds:** the supplied schema-3 build's status, engine/backend, diagnostics
  and logs. A failed build remains visible with its failure evidence.
- **PDFs:** previews from successful builds, aligned by page index. Pagination
  changes need manual comparison. A failed build's partial PDF is not a
  successful comparison.
- **Author decisions:** visible `TODO`/`[UNCERTAIN]` source locations and supplied
  notes. The author must resolve scientific intent.

Each build report must identify a source inside its corresponding project with
a matching source hash. Recorded local inputs must still match every retained
observation. New builds also bind their PDF with `pdf_sha256`; modified PDFs
are refused. Older schema-3 reports without this field are visibly marked with
an unverified build-time PDF identity. File hashes establish correspondence,
not independent authentication of a report's producer.

Declared transcript/log/recorder paths must exist; missing files are refused
instead of silently dropped. Retained reports, logs, PDFs and generated page
previews add `retained_files` entries with relative path, SHA-256 and byte size.
Copied evidence is checked against the original bytes, and both original and
retained evidence are rechecked after rendering, before the bundle is published.
Successful reports that declare unreadable local inputs are also refused.
These are point-in-time consistency checks, not a lock or an immutable snapshot
of a concurrently edited project. Legacy PDFs still retain their explicit
unverified build-time identity.

New bundles add `integrity.json`, covering HTML, JSON, diff and every retained
file. After transfer, run `als verify review path/to/bundle`; original project
paths are not needed. Keep annotations and verification output outside the
sealed directory. See [offline verification](verification.md) for coverage,
legacy handling, limits and the distinction between integrity and authenticity.

Without `--before-build`/`--after-build`, the corresponding side is explicitly
unverified. Stale inputs, render failures and publication errors leave no
partially published review directory. Source/configuration/asset snapshots are
checked again before publication; generated build files are excluded.

The additive schema-1 `inventory_scope` records supported source/asset
extensions, `.als.json`, and excluded directory names. Other file types are
not inspected. Place manuscript inputs outside generated/environment trees
if you want them included in the source change inventory. Numbers are literal
text tokens, not recognized measurements. Escaped dollars are not math
delimiters. Supported named environments have their own located inventory and
change signals; see [formula-review coverage](math-review.md). Macro expansion,
custom outer math environments, catcode changes and scientific semantics remain
outside the literal math check. Comments and common
verbatim forms are masked for content signals; visible author markers are
scanned in source text, including comments.

Commented code examples cannot mask live number/reference changes. Supported
verbatim examples do not contribute literal content signals. The additive
`source_scan_issues` field and a separate HTML section locate unfinished inline
verbs and verbatim regions on both sides, including unchanged TeX/class/package
files. Absent content flags cannot establish fidelity when regions are incomplete.
See the [literal scanner coverage](project.md) before interpreting these signals.

The report escapes source/notes and supports narrow screens and dark mode.
See the [complete project example](../examples/full-paper/README.md) for a
repair workflow with English and Chinese builds and an unresolved author choice.
See the [Chinese review guide](review_CN.md) for the same workflow in Chinese.

## Selected backend-resource consistency

Builds using repeated `--watch-input` can bind explicit local bibliography/styles
from preflight onward, even without engine recorder coverage. Review rechecks all
their starting/step hashes, rejects later source changes and displays the selected
scope beside the retained build. Legacy reports with no selection metadata remain
usable; this does not infer backend consumption. [Build-input guide](build-inputs.md).

## Citation key changes

The shared scanner now catches common natbib/biblatex citation changes, including
a second or later multicite group. Both source versions retain located inventories;
unsupported syntax appears in `source_scan_issues` even in unchanged files.
[Coverage and example](citations.md).

## Cross-reference edits

Review now retains label/reference inventories for both versions. Hyperref label
target edits and reversed range endpoints enter the existing `reference_keys`
signal; list-only reordering preserves its key counter. Unsupported syntax is
visible even when a source is unchanged. [Coverage](cross-references.md).

## Manual entry key edits

Changing only a literal `bibitem` key now triggers `reference_keys`. Both versions
retain located entries; unsupported syntax stays visible for unchanged files.
[Interpretation](bibliography.md#manual-bibliographies).

## Loader and backend option observations

Both source versions retain literal class/package declarations. Malformed loaders
and unsupported/conflicting direct backend assignments remain visible even for
unchanged sources. [Scope and interpretation](package-options.md).

## Large files and review notes

Project assets, supplied build metadata, retained logs/PDFs and review notes now
use bounded regular-file reads. Notes allow 2,000,000 bytes, JSON allows 16 MiB,
and individual hashed/copied evidence allows 512 MiB. A report digest binds the
exact parsed bytes. Failures leave no published review. [Limits](input-limits.md).
