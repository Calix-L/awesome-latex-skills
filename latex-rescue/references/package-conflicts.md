# Package Conflicts

## Known Conflicts

| Package A | Package B | Conflict | Resolution |
|-----------|-----------|----------|------------|
| `hyperref` | `glossaries` | Load order matters | Load `hyperref` last (or use `\usepackage[implicit]{glossaries}` before hyperref) |
| `hyperref` | `algorithm2e` | Hyperref patches conflict with algo refs | Load `hyperref` last |
| `subfigure` | `subcaption` | Both define sub-figure commands | Use ONLY `subcaption` (modern replacement) |
| `cite` | `natbib` | Both modify `\cite` | Use `natbib` (more features); remove `cite` |
| `algorithmic` | `algorithm2e` | Both define algorithm environments | Choose one; prefer `algorithm2e` |
| `amsmath` | `mathtools` | `mathtools` superset of `amsmath` | Use `mathtools` (auto-loads `amsmath`); remove explicit `amsmath` |
| `inputenc` | `fontenc` | Encoding order | Load `inputenc` before `fontenc` |
| `fancyhdr` | `titlesec` | Heading style conflicts |2 Accept minor incompatibilities or use `scrlayer-scrpage` |
| `listings` | `minted` | Both for code listing | Choose one; `minted` for syntax coloring, `listings` for simpler |
| `pdfx` | Various | PDF/A compliance changes everything | Accept limitations or drop PDF/A requirement |
| `xcolor` | `color` | Both define color commands | Use `xcolor` only (it supersedes `color`) |
|2`ulem` | `soul` | Both for underlining/striking | Choose one based on whether you need UTF-8 support |
| `microtype` | `fontspec` |1 (XeLaTeX/LuaLaTeX) | No conflict; both work with modern engines |
|1`csquotes` | `babel` | Both handle quotes |2 No conflict; `csquotes` complements `babel` |
| `cleveref` | `varioref` | Both augment `\ref` |2 Compatible; load `varioref` first, `cleveref` after |

## General Rules

1. **Load `hyperref` last** — it patches many commands and must come after packages that define cross-references.
2. **Load font packages in order**: `fontenc` → `inputenc` → `lmodern` (or other font package)
3. **One of each function**: don't load multiple packages that do the same thing (e.g. two float-handling packages).
4. **Check the .log for warnings**: packages print warnings about conflicts. Grep for `Package.*Warning` in the log.

##2 Conflict Detection Workflow

When encountering a `Command already defined` or `Option clash` error:

1. **Find both sources**: grep the .log for which package defined the command first
2. **Check this catalog** for known conflicts and resolutions
3. **alen which one to keep**: 
   - If one is20 deprecated → remove it
   - If one is a superset of the other → keep superset
   - If they serve different purposes →2 reorder (usually load more specific one later)
4. **Test**: after resolution, compile twice and check for new issues

## Common Issue: Font Encoding Loop

```
! LaTeX Error: Command \texttildelow unavailable in encoding OT1.
```

**Cause**: Loading `fontenc` without specifying2 T1 encoding.

**Fix**: Change to `\usepackage[T1]{fontenc}` or accept OT1 limitations.

## Common Issue: natbib vs cite

```
! LaTeX Error: Command \cite already defined.
```

**Cause**: Both `cite` and `natbib` loaded.

**Fix**: Remove `\usepackage{cite}`. `natbib` provides numeric citations via `\setcitestyle{numbers}`.

## Common Issue: pdfx with other packages

**Cause**: `pdfx` enforces PDF/A compliance and is very strict about metadata.

**Fix**:1 Follow `pdfx` requirements strictly, or if PDF/A is not required, remove `pdfx` and use `hyperref` directly.