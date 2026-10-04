# Inspect bibliography headers without inventing references

```sh
als project check path/to/paper --main main.tex --engine pdflatex --backend bibtex --bundle work/bib-inspection
als verify inspection work/bib-inspection
```

Select the project's actual backend: use `--backend biber` for a Biber project,
or record it in `.als.json`. Inspection reads reachable `.bib` files referenced
by literal `bibliography`/`addbibresource` commands. It never changes the database.
Open `report.html` for a table of keys, types, filenames and header line numbers.
JSON adds `bibliography_entries`; repeated headers remain visible individually.

## Recognized structures

Both `@misc{key, ...}` and `@misc(key, ...)` are recognized. Entry type spelling
is normalized to lowercase; keys retain their exact spelling. Nested braced and
quoted values are scanned as one region, so `@misc{...}` inside a title is not a
new definition. `@string` and `@preamble` bodies do not supply entry keys; their
values are not expanded. Balanced brace entries without fields are inventoried.

The scanner reports an unclosed or mismatched region as **unverified**, stops
scanning the remaining region and does not supply its unfinished header as a
known key. Header presence does not prove field validity, supported entry type,
required fields, correct string definitions or accepted backend output.

## Percent signs, comments and duplicate keys

With explicit `--backend bibtex`, scanning resumes at the next `@` after an
`@comment` directive. A percent sign does not begin a TeX-style comment in this
database scanner: `% @misc{key, ...}` can be active BibTeX input. Do not use these
conventions to assume that an entry has been disabled. Without explicit BibTeX
selection, balanced comment bodies containing `@` are skipped and marked
unverified; Biber-specific comment acceptance is not inferred.

Exact duplicate keys are reported within/across reachable databases, with the
first header's location in resource encounter order. A repeated database is not
rescanned. Selected BibTeX also folds ASCII A–Z for duplicate comparison;
Biber/unselected backends use exact spelling. Citation lookup remains exact.
Unicode case conversion, citation aliasing and backend-specific
case acceptance are not inferred. Resolve collisions deliberately and inspect
the native build; entries are never silently merged.

The reviewed syntax basis is the [BibTeX manual](https://tug.ctan.org/biblio/bibtex/base/btxdoc.pdf)
and [pinned implementation](https://github.com/TeX-Live/texlive-source/blob/a645809b018c7895d5326af2cabf73563f85f4bb/texk/web2c/bibtex.web),
specifically entry/field scanning, `@comment` and ASCII case folding. Automated
native controls compare supported common structures with real BibTeX/Biber.

## Limits and next steps

The scanner inventories literal headers, rather than validating all BibTeX or
BibLaTeX grammar. It does not resolve string expansion, aliases, inheritance,
crossref/xdata, remote resources, style rules or source authenticity. Up to
10,000 headers and 10,000 structural issues per database are supported; source reads retain the existing
2,000,000-byte limit. Iterative value scanning avoids a Python recursion limit.
Hashes bind the database bytes read, and observations are rechecked on export.

An unknown citation should lead to the actual source/entry from the author.
Run a [native configured build](project.md), review its log and PDF, and preserve
unresolved author choices. The fixture [headers.bib](../tests/fixtures/bibliography/headers.bib)
contains synthetic controls, not references to real research. See the
[Chinese guide](bibliography_CN.md).
