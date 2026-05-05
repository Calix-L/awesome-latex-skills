# Math Reconstruction

Mapping extracted PDF math content back to LaTeX math expressions.

## Approach

Math in PDFs can be extracted in two forms:
1. **Character-level**: Individual glyph positions (from pymupdf spans)
2. **Unicode text**: The rendered text (if PDF has ToUnicode mapping)

Use both. Character-level data is better for precise positioning (subscripts, fractions), while Unicode is better for symbol identification.

## Common Glyph → LaTeX Mappings

### Greek Letters

| Unicode | Glyph | LaTeX |
|---|---|---|
| α (U+03B1) | alpha | `\alpha` |
| β (U+03B2) | beta | `\beta` |
| γ (U+03B3) | gamma | `\gamma` |
| δ (U+03B4) | delta | `\delta` |
| ε (U+03B5) | epsilon | `\epsilon` |
| θ (U+03B8) | theta | `\theta` |
| λ (U+03BB) | lambda | `\lambda` |
| μ (U+03BC) | mu | `\mu` |
| σ (U+03C3) | sigma | `\sigma` |
| φ (U+03C6) | phi | `\phi` |
| ω (U+03C9) | omega | `\omega` |
| Γ (U+0393) | Gamma | `\Gamma` |
| Δ (U+0394) | Delta | `\Delta` |
| Σ (U+03A3) | Sigma | `\Sigma` |
| ζ (U+03B6) | zeta | `\zeta` |
| η (U+03B7) | eta | `\eta` |
| ι (U+03B9) | iota | `\iota` |
| κ (U+03BA) | kappa | `\kappa` |
| ν (U+03BD) | nu | `\nu` |
| ξ (U+03BE) | xi | `\xi` |
| π (U+03C0) | pi | `\pi` |
| ρ (U+03C1) | rho | `\rho` |
| τ (U+03C4) | tau | `\tau` |
| υ (U+03C5) | upsilon | `\upsilon` |
| χ (U+03C7) | chi | `\chi` |
| ψ (U+03C8) | psi | `\psi` |
| Ψ (U+03A8) | Psi | `\Psi` |
| Φ (U+03A6) | Phi | `\Phi` |
| ϵ (U+03F5) | varepsilon | `\varepsilon` |
| ϑ (U+03D1) | vartheta | `\vartheta` |
| ϱ (U+03F1) | varrho | `\varrho` |
| ς (U+03C2) | varsigma | `\varsigma` |

### Operators and Symbols

| Unicode | LaTeX |
|---|---|
| × (U+00D7) | `\times` |
| · (U+00B7) | `\cdot` |
| ± (U+00B1) | `\pm` |
| ∓ (U+2213) | `\mp` |
| ÷ (U+00F7) | `\div` |
| √ (U+221A) | `\sqrt{...}` |
| ∞ (U+221E) | `\infty` |
| ∂ (U+2202) | `\partial` |
| ∇ (U+2207) | `\nabla` |
| ∫ (U+222B) | `\int` |
| ∬ (U+222C) | `\iint` |
| ∭ (U+222D) | `\iiint` |
| ∑ (U+2211) | `\sum` |
| ∏ (U+220F) | `\prod` |
| ∪ (U+222A) | `\cup` |
| ∩ (U+2229) | `\cap` |
| ∈ (U+2208) | `\in` |
| ∉ (U+2209) | `\notin` |
| ⊂ (U+2282) | `\subset` |
| ⊆ (U+2286) | `\subseteq` |
| ∀ (U+2200) | `\forall` |
| ∃ (U+2203) | `\exists` |
| ∅ (U+2205) | `\emptyset` |
| ¬ (U+00AC) | `\neg` |
| ∧ (U+2227) | `\land` |
| ∨ (U+2228) | `\lor` |
| → (U+2192) | `\rightarrow` |
| ← (U+2190) | `\leftarrow` |
| ↔ (U+2194) | `\leftrightarrow` |
| ⇒ (U+21D2) | `\Rightarrow` |
| ⇐ (U+21D0) | `\Leftarrow` |
| ⇔ (U+21D4) | `\Leftrightarrow` |
| ≥ (U+2265) | `\geq` |
| ≤ (U+2264) | `\leq` |
| ≠ (U+2260) | `\neq` |
| ≈ (U+2248) | `\approx` |
| ≡ (U+2261) | `\equiv` |
| ∼ (U+223C) | `\sim` |
| ∝ (U+221D) | `\propto` |
| ⊥ (U+22A5) | `\perp` |
| ∥ (U+2225) | `\|` (parallel) |
| ⟨ (U+27E8) | `\langle` |
| ⟩ (U+27E9) | `\rangle` |
| ⊕ (U+2295) | `\oplus` |
| ⊗ (U+2297) | `\otimes` |
| ⊙ (U+2299) | `\odot` |
| ⊢ (U+22A2) | `\vdash` |
| ⊨ (U+22A8) | `\models` |
| △ (U+25B3) | `\triangle` |
| ◇ (U+25C7) | `\Diamond` |
| † (U+2020) | `\dagger` |
| ‡ (U+2021) | `\ddagger` |
| ⋯ (U+22EF) | `\cdots` |
| … (U+2026) | `\ldots` |
| ⋮ (U+22EE) | `\vdots` |
| ⋱ (U+22F1) | `\ddots` |

### Decorative Accents

| Unicode example | LaTeX |
|---|---|
| x̄ (x + macron) | `\bar{x}` / `\overline{x}` |
| x̂ (x + circumflex) | `\hat{x}` / `\widehat{x}` |
| x̃ (x + tilde) | `\tilde{x}` / `\widetilde{x}` |
| ẋ (x + dot) | `\dot{x}` |
| x ̈ (x + diaeresis) | `\ddot{x}` |
| x⃗ (x + arrow) | `\vec{x}` |

### Script and Special Letters

| Unicode | LaTeX |
|---|---|
| ℓ (U+2113) | `\ell` |
| ℜ (U+211C) | `\Re` |
| ℑ (U+2111) | `\Im` |
| ℵ (U+2135) | `\aleph` |
| ℝ (U+211D) | `\mathbb{R}` |
| ℂ (U+2102) | `\mathbb{C}` |
| ℕ (U+2115) | `\mathbb{N}` |
| ℤ (U+2124) | `\mathbb{Z}` |
| ℚ (U+211A) | `\mathbb{Q}` |

## Subscript/Superscript Detection

Uses vertical position relative to baseline:

```
For each span within a math block:
  if span.origin.y is noticeably ABOVE baseline of surrounding text
     AND font_size < surrounding font_size:
    → superscript (^{...})
  if span.origin.y is noticeably BELOW baseline of surrounding text
     AND font_size < surrounding font_size:
    → subscript (_{...})
```

Complex cases:
- Nested super/subscripts: `a_i^2` vs `a_{i+1}`
- Multi-character: use braces `a_{ij}` not `a_ij`

## Fraction Detection

**Signals:**
- Centered horizontal line (from pdfplumber lines/rects)
- Text above and below the line
- Text blocks vertically stacked with a rule between them

→ `\frac{<above>}{<below>}`

## Matrix Detection

**Signals:**
- Grid of short math expressions
- Bounded by large delimiters (stretchy brackets/parentheses)
- Columns aligned, rows spaced regularly

→ `\begin{pmatrix} ... \end{pmatrix}` or `\begin{bmatrix} ... \end{bmatrix}`

## Large Operator Detection

**Signals for ∑, ∫, ∏:**
- Significantly larger than surrounding glyphs
- Often have limits above and below (detected by extreme vertical position)

∑ with limits:
```
\sum_{<lower>}^{<upper>}   % in display math
```

∫ with limits:
```
\int_{<lower>}^{<upper>}   % definite integral
```

## Multi-Line Equation Detection

**Signals:**
- Multiple math blocks aligned vertically (centered)
- May share alignment points (equals signs at same x-position)
- May have equation numbers at each line

→ `\begin{align}...\end{align}` (prefer align; avoid `eqnarray` — deprecated, produces incorrect spacing)

## Cases Environment

**Signals:**
- Large left curly brace spanning multiple lines
- Conditions on right side: ", if x > 0"

→ `\begin{cases} ... \end{cases}`

## Quality Checks for Math

After conversion, run these checks:
1. All `$` signs properly paired
2. Braces `{ }` balanced in each math expression
3. No bare Unicode math symbols outside math mode
4. Subscript/superscript ordering correct: `a_i^2` not `a^2_i` (different meaning)
5. `\left` / `\right` delimiters are matched