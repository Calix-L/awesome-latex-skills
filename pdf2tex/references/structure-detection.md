# Document Structure Detection

Build a page-aware inventory before writing LaTeX. Font size, boldness, position
and numbering suggest a role; they do not prove it. Preserve blocks that do not
fit a guessed template and record unresolved roles.

## Inventory and reading order

For each selected page, record every text block, its bounding box, lines/spans,
font information and candidate role. Keep figure/table regions, captions,
notes and bibliography entries in the same inventory. Record selected coverage
explicitly: omitted pages may contain definitions, references or continuations.

Sorted text can interleave columns. Identify vertical bands separated by
full-width titles, equations or figures, then determine the column order inside
each band. Check both left and right block edges. A block crossing the gutter
must not be discarded or forced into one column. Check the original page when
geometry gives more than one plausible order.

Inspect span-level font sizes instead of assuming a block has one font size.
A heading can contain math, a section number and several fonts. Font-size ranking
alone does not identify heading depth, and a title need not be the largest,
boldest or centered text on the page.

## Assign roles from combined evidence

| Candidate role | Evidence to compare | Common ambiguity |
|---|---|---|
| Title | Wording, position, metadata, relation to author block | Running title versus article title; metadata may be stale |
| Author/affiliation | Names, institutional lines, superscript markers, correspondence text | A marker may link an affiliation or author note |
| Abstract | Label and paragraph boundaries | Full-width abstract above a two-column body |
| Section/subsection | Numbering, typography, contents/bookmarks, neighboring sections | Unnumbered heading, appendix letter, figure label |
| Equation | Math glyphs, spatial grouping, tag and nearby definitions | Displayed algorithm or a line of table content |
| Figure | Visible panel composition and caption association | Vector-only graphics and separate labels have no standalone image block |
| Table | Grid/spacing, header coverage, notes and caption | Borderless table or wrapped prose |
| Footnote | Marker correspondence and text near the page bottom | Footer metadata versus scientific content |
| References | Bibliography heading and entry boundaries | An entry may continue across columns or pages |

Use PDF bookmarks as corroborating evidence, not an authoritative outline.
Embedded-image inventories miss vector graphics and composite figures; inspect
whole-page previews even when no raster image was exported.

Keep the original section order and visible heading text. Choose a plausible
LaTeX hierarchy that reproduces it and document any inference. Do not add a
Methods section or move a conclusion merely because a familiar template expects
one. Likewise, the bibliography's visible location does not impose a universal
appendix order.

## Separate artifacts from content

Compare repeated lines across pages before removing running headers, page numbers
or publisher notices. A repeated scientific term is not a header. A bottom-of-page
note can contain a definition, funding disclosure or experimental condition;
preserve it and its marker unless it is confirmed as an unwanted layout artifact.
Log removed artifacts with page locations.

Join wrapped prose only when the continuation is supported. Distinguish line-end
hyphenation from meaningful hyphens in compounds, chemical names or identifiers.
Keep paragraph boundaries, list items and captions separate. Do not combine a
column's last line with the next geometrically nearby column's first line.

## Reconstruct citations conservatively

A bracketed number may be a citation, interval, array entry or equation label.
Classify it from the sentence and bibliography, rather than a global regex.
For citations, retain the visible marker and map it to the entry only when the
numbering and entry boundaries are supported by the selected pages.

Author/year text does not uniquely identify a bibliography key. Check names,
year suffixes and the actual entry. Newly chosen keys should be documented as
reconstruction choices. Do not invent titles, venues, DOIs or missing authors.

For an unmatched `[42]`, preserve the visible marker and add a visible note
explaining that its bibliography entry was not recovered. Generating a bare
`\cite{ref42}` changes the marker into an undefined citation and conceals what
the PDF actually showed. A source comment can retain provenance, but does not
replace the visible uncertainty note.

## Validate the outline and coverage

Compare every inventory item with its reconstructed location. Check titles,
authors/affiliations, heading levels, paragraph/column order, captions, footnotes,
equations and bibliography continuations. List omitted pages, unavailable assets
and unmatched references separately from confirmed layout artifacts.

Use [math reconstruction](math-reconstruction.md) and
[table reconstruction](table-reconstruction.md) for uncertain notation and grids.
Compilation checks syntax and cross-references; a comparison with the source
is still required for content coverage and structure.
