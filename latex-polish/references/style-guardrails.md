# Style Guardrails

Choose edits that improve the requested passage while retaining its scientific
meaning. The author's terminology, English variant and supplied style guide
take precedence. Examples offer wording choices; they supply no missing evidence.

## Register Rules

Prefer clear, specific wording over more elaborate synonyms. “Use” and “about”
can be appropriate academic English. Do not automatically replace “difficult”
with “non-trivial”: the latter can have a technical meaning.

| Source wording | Possible edit | Preserve or check |
|---|---|---|
| “We get the predictions from the classifier.” | “We obtain the predictions from the classifier.” | Which component produces the predictions |
| “The model gives good results.” | Ask which result and comparison the author means; keep the supplied wording until clarified | No invented accuracy, effect size or claim strength |
| “The method is kind of robust.” | Clarify the tested conditions and meaning of “robust” | Do not silently change uncertain evidence into established robustness |
| “There are more and more studies on X.” | “An increasing number of studies examine X.” | The trend is still a claim requiring support |
| “This is an awesome new method.” | Flag evaluative wording; describe only properties established in the manuscript | No added novelty, elegance or superiority |

Terms such as “significant”, “efficient”, “optimal” and “robust” may carry
statistical or technical meaning. Do not use them as decorative substitutes.
A supported number can clarify a claim only with its metric, comparison and scope.

## Voice Rules

Use active voice when it clarifies who performed an action. Passive voice can
keep an object or procedure in focus when the agent is clear or irrelevant.
Do not insert “we” when the manuscript attributes the action to another group.

Preserve tense and evidential strength. “Can achieve” describes a capability;
“achieved” describes an observed result. “Suggests”, “is consistent with” and
“demonstrates” are not interchangeable. A proof under stated assumptions can
support a universal claim; a limited experiment has a different scope.

Attribution matters: “It has been shown that...” can refer to prior evidence.
Replace it with a direct citation only if the source and attribution are known;
do not turn it into the current authors' finding.

## Clarity Rules

### Split without removing components or adding causality

Source:

> The model, which uses a transformer architecture with multi-head self-attention
> and a novel gating mechanism that dynamically selects informative features while
> suppressing noise, achieves better performance.

Candidate:

> The model uses a transformer architecture with multi-head self-attention and a
> novel gating mechanism. The gating mechanism dynamically selects informative
> features while suppressing noise. The model achieves better performance.

The split preserves the supplied components and claim. It does not add “As a
result”, which would attribute the improvement to a particular mechanism.
“Novel” and “better performance” remain claims to check, not facts supplied by
the example. Clarifying the comparison may require author input.

### Keep conditions attached to the result

Source:

> The method, when applied to large-scale datasets with careful hyperparameter
> tuning and data augmentation, achieves state-of-the-art results.

Candidate:

> When applied to large-scale datasets with careful hyperparameter tuning and
> data augmentation, the method achieves state-of-the-art results.

The dataset, tuning and augmentation conditions remain attached to the result.
Do not convert this into an unrestricted claim or remove an experimental condition.

### Shorten without losing logical relations

“We conducted an investigation of X” can become “We investigated X”.
“We assessed whether X improves Y” must retain “whether”; “We improved Y with X”
changes an investigation into a successful intervention.

Before removing a phrase, check whether it conveys contrast, attribution,
qualification, time or emphasis relevant to the argument. Sentence length and
line length are not independent quality thresholds.

## Consistency Rules

### Terminology

Confirm that terms name the same concept before standardizing them. A latent
space, embedding space and representation space can describe different objects.
A model can be one component of a framework; replacing both with “method” may
hide that distinction. Retain named entities and notation, and keep a short
terminology ledger for long manuscripts.

### Numbers and units

Follow the supplied style for digits, grouping, decimals, ranges and units.
Preserve the value, displayed precision, denominator, uncertainty and comparison.

- Do not turn a relative 3.2% gain into 3.2 percentage points.
- An accuracy change from 80% to 84% is 4 percentage points or a 5% relative
  increase; use either calculation only when these values and that comparison
  are actually supplied.
- Do not silently change “approximately”, confidence intervals, signs or
  trailing zeros to make a result sound more precise.
- Preserve identifiers, versions, dates, citation keys, code and file paths.
  Numeric typography rules do not apply to those tokens.
- In ordinary TeX text, `--` is an en dash and `---` an em dash. Keep literal
  ASCII hyphens in code and identifiers, and preserve minus signs in math.
- Use unit/number packages only when the project supports them. Switching to
  `siunitx` is a source/package change, not a spelling correction.

### Hyphenation and punctuation

Apply the chosen dictionary/style and the phrase's grammatical role. Some terms
remain hyphenated after a noun, and adverbs ending in “-ly” generally do not take
a modifier hyphen. Avoid a blanket “all predicative compounds lose hyphens” rule.
Keep established technical spellings consistent.

Use the author's serial-comma convention unless it causes ambiguity. A comma
alone may not resolve whether listed people are appositives or additional
recipients; rewrite only after their roles are known.

### Abbreviations

Define unfamiliar abbreviations where the target readership needs them. An
abstract or independently read supplement may need its own definition.
Use the selected venue's convention for headings and repeat definitions.
Do not invent an expansion for an unfamiliar acronym.

## Quick Self-Review

1. Does every finding retain its metric, numbers, uncertainty, conditions and comparison?
2. Are causal relations, negation and attribution unchanged?
3. Do split sentences still contain every original component and logical relation?
4. Were distinct technical terms incorrectly merged?
5. Are math, keys, macro definitions, comments, quotations and code intact?
6. Which changes or missing details need author review?
7. Was compilation actually checked with the project's configured tools?

For section-specific choices, read [section anatomy](section-anatomy.md).
