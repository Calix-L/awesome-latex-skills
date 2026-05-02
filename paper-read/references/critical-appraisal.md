# Critical Appraisal Checklist

Systematic evaluation framework for academic papers. Run through these questions when doing a `read` or `deep` analysis.

---

## Methodology Evaluation

### Problem Framing
- [ ] Is the problem well-defined or vague?
- [ ] Is the motivation clear (why should anyone care)?
- [ ] Is the claimed difficulty genuine or a strawman?
- [ ] Are assumptions stated explicitly?

### Method Soundness
- [ ] Is the approach clearly described? Could you reimplement?
- [ ] Is each design choice justified? (not just "we use X" but "we use X because...")
- [ ] Are there theoretical guarantees? If so, under what assumptions?
- [ ] Are hyperparameters tuned fairly? Same budget for baselines?
- [ ] Is there evidence of overfitting to the test set?

### Baselines and Comparisons
- [ ] Are baselines strong and recent? (≤2 years old)
- [ ] Are baselines properly tuned? Or copied from original papers?
- [ ] Is the comparison fair? Same data, same compute, same tuning budget?
- [ ] Are there obvious baselines missing? (If method is "X + attention", a "X without attention" baseline should exist)

### Reproducibility
- [ ] Are hyperparameters fully specified?
- [ ] Are datasets publicly available? (not internal/proprietary)
- [ ] Is code released? If so, is it documented and runnable?
- [ ] Are computational requirements stated?
- [ ] Are random seeds reported? Multiple runs?

---

## Results Evaluation

### Quantitative Results
- [ ] Are metrics appropriate? (accuracy on imbalanced data? bleu for creative text?)
- [ ] Are error bars/standard deviations reported?
- [ ] Are improvements statistically significant? (p-values? confidence intervals?)
- [ ] Is the improvement practically meaningful? (0.1% on ImageNet vs 3% on a safety-critical task)

### Qualitative Results
- [ ] Are examples cherry-picked? (best-case vs typical-case)
- [ ] Are failure cases shown and analyzed?
- [ ] Are visualizations honest? (same scale, same color range as baselines?)

### Ablation Studies
- [ ] Are all claimed contributions ablated?
- [ ] Is the ablation design clean? (changing one thing at a time)
- [ ] Are negative results reported? (things that didn't help)

---

## Claims Evaluation

### Overclaiming Detection

Red flags that indicate overclaiming:

- **"State-of-the-art"** but only compared to pre-2022 baselines
- **"Generalizes"** but only tested on one dataset family
- **"Efficient"** but only compared to unoptimized baselines
- **"Simple"** but actually requires 3 auxiliary losses and careful initialization
- **"Robust"** but only tested on Gaussian noise, not real distribution shift
- **"We prove..."** followed by a derivation under restrictive assumptions
- **Abstract claims "revolutionizes" or "fundamentally changes"** — science progresses incrementally

### Evidence Quality

Rate the evidence for each major claim:

| Level | Meaning |
|-------|---------|
| A | Convincing: multiple datasets, strong baselines, statistical tests, ablation confirms |
| B | Adequate: reasonable setup, minor concerns about fairness or significance |
| C | Weak: small datasets, weak/old baselines, single run, no error bars |
| D | Missing: claim made but no experiment or citation supports it |

---

## Innovation Assessment

### Type of Contribution

- **New problem**: Defines a previously unarticulated problem
- **New insight**: A counterintuitive finding that changes how we think
- **New method**: Novel architecture/algorithm with clear advantages
- **New combination**: Creative synthesis of existing ideas (this is valuable too, but be honest about it)
- **New benchmark/dataset**: Enables future research
- **Analysis/understanding**: Explains WHY something works
- **Incremental improvement**: Tiny tweak with marginal gains (be honest if this is the case)

### The "Delta" Test

For each contribution, ask: what does the community gain from this paper that was NOT available before?

- High delta: "Now we know why batch norm works" or "A 10x cheaper way to train transformers"
- Medium delta: "A solid new architecture with +3% on standard benchmarks"
- Low delta: "A different optimizer that sometimes helps by 0.3%"

---

## Writing Quality

- [ ] Clear: Can you understand it on first read?
- [ ] Well-organized: Logical flow, not jumping between topics
- [ ] Honest: Limitations acknowledged, not hidden in appendix
- [ ] Figures informative: Self-contained captions, clear legends
- [ ] Related work section helpful: organized thematically, not a laundry list

---

## Overall Verdict

Choose ONE:

- **Strong accept**: Would trust these results enough to build on them
- **Solid paper**: Good contribution, minor reservations
- **Borderline**: Interesting idea but flaws in execution or evaluation
- **Weak**: Flawed methodology, overclaimed, or just not enough novelty
- **Cannot evaluate**: Missing crucial details to make a judgment