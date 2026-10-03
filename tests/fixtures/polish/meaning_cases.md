# Meaning-preserving editing cases

Synthetic passages for manual evaluation of `latex-polish`. Values, methods and
claims below are examples, not results or evidence from a real study. A candidate
is acceptable only if its grammar and scientific meaning survive review; matching
words or compiling LaTeX alone does not establish editing quality.

## Components and causality

Source:

> The model, which uses a transformer architecture with multi-head self-attention
> and a gating mechanism that selects informative features while suppressing
> noise, achieves better performance on the supplied benchmark.

Candidate:

> The model uses a transformer architecture with multi-head self-attention and
> a gating mechanism. The gating mechanism selects informative features while
> suppressing noise. The model achieves better performance on the supplied benchmark.

Retain both components and the benchmark scope. Adding “Consequently” or “As a
result” would assign a cause that the passage does not establish. The comparison
is underspecified; flag it for the author rather than inventing a baseline.

## Capability, uncertainty and conditions

Source:

> Under the tested noise levels, the model may improve robustness, but the
> experiments do not establish that it generalizes to unseen corruptions.

Candidate:

> At the tested noise levels, the model may improve robustness. However, the
> experiments do not establish generalization to unseen corruptions.

Retain “may”, the tested conditions and the negative statement. “The model is
robust to unseen corruptions” reverses the evidence. Ask what “robustness” means
if the surrounding manuscript does not define it.

## Percentages and precision

Source:

> Accuracy increased from 80.0\% to 84.0\% on dataset D.

Candidate:

> On dataset D, accuracy increased from 80.0\% to 84.0\%.

Retain both values, decimal precision, dataset and direction. The observed
change is 4 percentage points or a 5% relative increase, not “a 4% increase”.
Preserving the original values avoids choosing a new reporting convention.

## Distinct technical objects

Source:

> The encoder maps the observations to an embedding space. The generative
> model samples a separate latent space.

Candidate:

> The encoder maps observations to an embedding space. The generative model
> samples a separate latent space.

Do not standardize the two spaces to one term. Their relation is not supplied.

## LaTeX argument roles

Source:

```latex
\newcommand{\modelname}{Model-A}
Under assumption~\ref{ass:bounded}, $a_i^2$ can be bounded as in
\citet[Theorem~2]{Author2024}. See \textbf{the original comparison}.
% The quoted claim and command examples below must remain untouched.
\verb|\citep{Example2024}| is an example command.
```

Candidate:

```latex
\newcommand{\modelname}{Model-A}
Under assumption~\ref{ass:bounded}, $a_i^2$ admits the bound in
\citet[Theorem~2]{Author2024}. See \textbf{the original comparison}.
% The quoted claim and command examples below must remain untouched.
\verb|\citep{Example2024}| is an example command.
```

Check the candidate against the surrounding theorem before accepting it. Preserve
the assumption key, formula, textual citation role, locator, citation key, macro
definition, comment and verbatim example. These fragments are not standalone
documents; the referenced theorem and bibliography were not supplied.
