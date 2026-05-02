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
| `fancyhdr` | `titlesec` | Heading style conflicts | Accept minor incompatibilities or use `scrlayer-scrpage` |
| `listings` | `minted` | Both for code listing | Choose one; `minted` for syntax coloring, `listings` for simpler |
| `pdfx` | Various | PDF/A compliance changes everything | Accept limitations or drop PDF/A requirement |
| `xcolor` | `color` | Both define color commands | Use `xcolor` only (it supersedes `color`) |
| `ulem` | `soul` | Both for underlining/striking | Choose one based on whether you need UTF-8 support |
| `natbib` | `biblatex` | Both modify citation system | Cannot coexist; choose one (`biblatex` is modern, `natbib` is traditional) |
| `todonotes` | `xcolor` | Option clash on color model | Load `xcolor` before `todonotes`, or pass options via `\PassOptionsToPackage` |
| `cleveref` | `varioref` | Both augment `\ref` | Compatible; load `varioref` first, `cleveref` after |

## No-Conflict Pairs (commonly confused)

These pairs are sometimes assumed to conflict but actually work together:

| Package A | Package B | Note |
|-----------|-----------|------|
| `microtype` | `fontspec` | No conflict; both work with modern engines (XeLaTeX/LuaLaTeX) |
| `csquotes` | `babel` | No conflict; `csquotes` complements `babel` |

## General Rules

1. **Load `hyperref` late** — it patches many commands and must come after packages that define cross-references. Exception: `cleveref` must come AFTER `hyperref`, so the load order is `...hyperref...cleveref`.
2. **Load font/encoding packages in order**: `inputenc` → `fontenc` → `lmodern` (or other font package). This is standard recommended practice, not a conflict.
3. **One of each function**: don't load multiple packages that do the same thing (e.g. two float-handling packages).
4. **Check the .log for warnings**: packages print warnings about conflicts. Grep for `Package.*Warning` in the log.
5. **Use `\PassOptionsToPackage`** to resolve option clashes without changing package load order.

## Conflict Detection Workflow

When encountering a `Command already defined` or `Option clash` error:

1. **Find both sources**: grep the .log for which package defined the command first
2. **Check this catalog** for known conflicts and resolutions
3. **Determine which one to keep**:
   - If one is deprecated → remove it
   - If one is a superset of the other → keep superset
   - If they serve different purposes → reorder (usually load more specific one later)
4. **Test**: after resolution, compile twice and check for new issues

## Common Issue: Font Encoding Loop

```
! LaTeX Error: Command \texttildelow unavailable in encoding OT1.
```

**Cause**: Loading `fontenc` without specifying T1 encoding.

**Fix**: Change to `\usepackage[T1]{fontenc}` or accept OT1 limitations.

## Common Issue: natbib vs cite

```
! LaTeX Error: Command \cite already defined.
```

**Cause**: Both `cite` and `natbib` loaded.

**Fix**: Remove `\usepackage{cite}`. `natbib` provides numeric citations via `\setcitestyle{numbers}`.

## Common Issue: biblatex vs natbib

```
! LaTeX Error: Command \cite already defined.
```

**Cause**: Both `biblatex` and `natbib` loaded — these are incompatible.

**Fix**: Choose one. `biblatex` is the modern system (uses `biber` backend); `natbib` is traditional (uses `bibtex`). Remove the other completely, including the corresponding backend call.

## Common Issue: pdfx with other packages

**Cause**: `pdfx` enforces PDF/A compliance and is very strict about metadata.

**Fix**: Follow `pdfx` requirements strictly, or if PDF/A is not required, remove `pdfx` and use `hyperref` directly.