# Review source changes and actual build evidence

Keep separate original and candidate project directories. The review tool
does not edit either one; its destination must be new and outside both trees.

```sh
als build path/to/before/main.tex --output work/before-build --backend bibtex --passes 3
als build path/to/after/main.tex --output work/after-build --backend bibtex --passes 3
als review --before path/to/before --after path/to/after --before-build work/before-build/build-report.json --after-build work/after-build/build-report.json --notes decisions.md --output work/review-01
```

Open `work/review-01/report.html` in a browser. Keep the generated directory
together: it includes an offline HTML report, JSON evidence, source diff,
retained build reports/logs, successful PDFs and page previews. No remote assets
or scripts are required. PyMuPDF is required when successful PDFs are supplied.

## Evidence remains separate

- **Source changes:** fingerprints and a unified diff for source, bibliography,
  styles/classes and project configuration; asset changes are listed by hash.
- **Content signals:** changed literal numbers, reference keys and simple math.
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

Without `--before-build`/`--after-build`, the corresponding side is explicitly
unverified. Stale inputs, render failures and publication errors leave no
partially published review directory. Source/configuration/asset snapshots are
checked again before publication; generated build files are excluded.

The report escapes source/notes and supports narrow screens and dark mode.
See the [complete project example](../examples/full-paper/README.md) for a
repair workflow with English and Chinese builds and an unresolved author choice.
