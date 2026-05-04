# Style Guardrails

## Register Rules

### Use Academic, Not Conversational

| Conversational | Academic |
|----------------|----------|
| really / very / huge / big | substantial, considerable, marked |
| a lot / lots of | many, numerous, considerable |
| get / got | obtain, receive, achieve |
| kind of / sort of | somewhat, relatively, rather |
| thing | aspect, element, factor, component |
| till / till now | until / to date |

### Formal Lexicon, Not Slang

| Informal | Formal |
|----------|--------|
| nowadays | currently, at present, in recent years |
| more and more | increasingly |
| hard (difficult) | challenging, non-trivial, complex |
| cool / awesome | compelling, elegant, innovative |

### Precise, Not Vague

| Vague | Precise |
|-------|---------|
| good results | strong results (or state the number) |
| works well | achieves 92.3% accuracy |
| better | improves by 3.2% / outperforms |
| some | several, [N], a subset of |

---

## Voice Rules

### Active vs Passive

**When to use active**: Your contributions, your choices, your analysis.
```
We propose...  We design...  We find that...
```

**When to use passive (OK in CS papers)**:
```
The model is trained...  Features are extracted...  The data was collected...
```

**Avoid**: "It is believed that..." / "It is considered that..." (too vague — who believes?)

### Hedging Appropriately

**When to hedge**: When a finding suggests but doesn't prove.
- "These results suggest that..."
- "This finding indicates a possible..."
- "Our experiments are consistent with the hypothesis that..."

**Don't hedge**: When your own results are clear.
- Bad: "Our method seems to improve performance somewhat."
- Good: "Our method improves F1 by 3.2 points (p < 0.01)."

**Overconfident to avoid**:
- "proves" → "demonstrates" / "shows" (science doesn't prove)
- "solves" → "addresses" / "mitigates" (you've made progress, not eliminated the problem)
- "completely" / "always" / "never" → remove, these are rarely true

---

## Clarity Rules

### One Idea Per Sentence

**Weak** (overloaded):
> The model, which uses a transformer architecture with multi-head self-attention and a novel gating mechanism that dynamically selects informative features while suppressing noise, achieves better performance.

**Strong** (split):
> The model uses a transformer architecture with a novel gating mechanism. This mechanism dynamically selects informative features while suppressing noise. As a result, the model achieves better performance.

### Subject-Verb Proximity

Keep the subject and verb close together.

**Weak** (separated):
> The method, when applied to large-scale datasets with careful hyperparameter tuning and data augmentation, achieves state-of-the-art results.

**Strong** (close):
> When applied to large-scale datasets, the method achieves state-of-the-art results with careful hyperparameter tuning and data augmentation.

### Avoid Nominalizations

| Heavy (noun form) | Lighter (verb form) |
|-------------------|---------------------|
| We conducted an investigation of | We investigated |
| The model performs classification of | The model classifies |
| We provide a demonstration that | We demonstrate that |

---

## Length Rules

### Cut Filler Phrases

| Remove | Keep | Reason |
|--------|------|--------|
| It is worth noting that | (delete) | If it's worth noting, just note it |
| It should be noted that | (delete) | Same |
| Interestingly, | (delete) | Let the reader decide what's interesting |
| As a matter of fact, | (delete) | Always filler |
| It has been shown that | (cite directly) | "Smith et al. showed that" |
| With respect to | Regarding | "About" is too informal for academic register |
| For the purpose of | To / For | |
| In order to | To | |
| The fact that | (rephrase) | |
| Due to the fact that | Because | |
| At the present time | Now / Currently | |
| A number of | Many / Several | |
| Is able to | Can | |

---

## Consistency Rules

### Terminology

Use the **exact same term** for the **exact same concept** throughout the paper.

| Wrong (inconsistent, same concept) | Right (pick one) |
|------------------------------------|------------------|
| "latent space" / "embedding space" / "representation space" | Pick ONE and use it everywhere |
| "our model" / "our framework" / "our approach" | Pick ONE for each distinct thing |
| "XNet" / "the proposed XNet" / "XNet model" | Pick ONE naming pattern |

### Number Formatting

- Spell out numbers below 10 in running text: "three baselines", "five datasets"
- Use digits for 10 and above: "12 layers", "100 images"
- Always use digits with units: "3 epochs", "5 Hz", "8 GPUs"
- Always use digits in comparisons and with percentages: "3.2% improvement", "5× speedup"
- Use comma grouping for 4+ digits: "10,000" (not "10000")
- In LaTeX, use `\,` for thin-space grouping in math: `$10\,000$` or use `\num{10000}` from `siunitx`
- Ranges use en-dash: "3--5 layers" (not "3-5")
- Scientific notation: `$3.2 \times 10^{-4}$` (not "3.2e-4")

### Hyphenation

- Compound modifiers before a noun are hyphenated: "state-of-the-art method", "end-to-end training"
- Same words after the noun are NOT hyphenated: "the method is state of the art"
- Common CS terms: "multi-layer" or "multilayer" (pick one, be consistent)
- "fine-tuned model" (adjective) vs "the model was fine-tuned" (verb)
- LaTeX dashes: hyphen (`-`) for compound words, en-dash (`--`) for ranges, em-dash (`---`) for parenthetical breaks

### Abbreviation

- Define on first use: `Large Language Models (LLMs)` → then use `LLMs` consistently
- Don't re-define abbreviations in later sections
- Avoid abbreviations in section headings unless universally known (e.g. "BERT" is OK, domain-specific ones are not)

### Oxford Comma

Use the Oxford (serial) comma consistently throughout the paper:
- With: "We evaluate on ImageNet, COCO, and ADE20K."
- Without: "We evaluate on ImageNet, COCO and ADE20K."
- Pick one style and apply it everywhere — do not mix within the same paper
- Default recommendation: **use the Oxford comma** (most CS style guides prefer it, and it prevents ambiguity)
- Ambiguity the Oxford comma resolves: "We thank my advisors, Alice and Bob" → are Alice and Bob the advisors, or two additional people? "We thank my advisors, Alice, and Bob" is unambiguous.

---

## Quick Self-Review

Before marking polishing as done, check:
1. Can any sentence be split into two? (If so, do it)
2. Is any sentence >2 lines? (flag it)
3. Are all acronyms defined on first use?
4. Is the same term used for the same concept everywhere?
5. Did you remove "It is worth noting that", "Interestingly", "As a matter of fact"?
6. Are you hedging claims where appropriate but not hedging your own results?
7. Are numbers formatted consistently? (digits vs spelled out, comma grouping, ranges with en-dash)
8. Are compound modifiers hyphenated when attributive, unhyphenated when predicative?