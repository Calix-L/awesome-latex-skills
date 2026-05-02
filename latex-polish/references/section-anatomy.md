# Section Anatomy: Writing Conventions by Section

## Abstract

**Purpose**: Standalone summary. Someone should understand the entire paper from just the abstract.

**Structure** (4 components, 1-2 sentences each):
1. **Context/Problem**: What broader area, what specific problem
2. **Approach**: What did you do (one sentence)
3. **Key Results**: Numbers, comparisons, main finding
4. **Implication**: Why it matters

**Length**: 100-250 words (venue-dependent)

**Common mistakes to flag**:
- Missing quantitative results ("improves performance" vs "improves F1 by 3.2 points")
- Vague contribution ("presents a method" vs "presents a graph-based method that")
- Overclaiming ("revolutionizes" / "solves completely")

---

## Introduction

**Purpose**: Frame the problem, establish the gap, preview the solution.

**Structure (funnel)**:
1. **Broad context** (1-2 sentences): Why this area matters
2. **Narrow to problem** (2-3 sentences): Current approaches and their limits
3. **The gap** (1-2 sentences): What's specifically unsolved
4. **Your approach** (2-3 sentences): What you did
5. **Contributions** (1 paragraph, bullet or numbered): What this paper provides

**Common mistakes**:
- Starting too broad ("AI has transformed many industries...")
- Not stating contributions explicitly
- Forgetting to preview results

---

## Related Work

**Purpose**: Situate your work in the literature. Show you understand the landscape and identify the gap you fill.

**Structure**: Thematic grouping, NOT chronological listing.

Each paragraph:
1. **Topic sentence**: "Work on [theme] has explored [approaches]."
2. **Specific examples** (2-4 papers): Key approaches and their results
3. **Critique/gap**: "However, these methods [limitation]."
4. **Transition**: (sets up next theme or your work's positioning)

**Common mistakes**:
- Laundry list: "A [1] did X. B [2] did Y. C [3] did Z." (no narrative)
- Missing critique: just saying what others did without saying what's wrong
- Omitting key competing work (reviewers will notice)

---

## Method

**Purpose**: A reproducible description of what you did.

**Plan**:
1. Overview paragraph + architecture diagram reference
2. Problem formalization (notation, objective)
3. Component-by-component description
4. Training/inference procedure
5. Implementation details

**Each component description**:
- What it does (one sentence)
- How it does it (details)
- Why this way (justification)
- How it connects to other components

**Common mistakes**:
- Inconsistent notation between sections
- Missing justification for design choices
- Too much detail (if a component is standard, cite a reference instead of re-deriving)

---

## Experimental Setup

**Purpose**: Enable exact reproduction.

**Must include**:
- Datasets (statistics, splits, preprocessing)
- Baselines (cite origin of each, note if you re-implemented)
- Metrics (formula or citation for each)
- Hyperparameters (how selected, ranges for tuning)
- Hardware/software (GPU, framework, approximate runtime)

---

## Results

**Purpose**: Present findings objectively.

**Structure for each experiment**:
1. **Lead with the finding**: "[Method] outperforms all baselines on [metric]."
2. **Show the evidence**: Table/figure reference with numbers
3. **Analyze meaning**: Why was there improvement? What does it suggest?
4. **Note surprises**: Unexpected results, negative results (these build credibility)

**Common mistakes**:
- Describing tables without interpreting them ("Table 1 shows results" → state what the results MEAN)
- Hiding negative results
- Comparing unfairly (tuned your method more than baselines)

---

## Discussion

**Purpose**: Interpret results broadly. Connect findings to bigger picture.

**Content**:
- What your results mean for the field
- How they connect to or contradict prior work
- Limitations (be honest — this builds trust with reviewers)
- Open questions and next steps

**Common mistakes**:
- Repeating results without interpretation
- Not acknowledging limitations or caveats
- Overgeneralizing from limited experiments

---

## Limitations

**Purpose**: Honest assessment of what the work does NOT address. Required at ACL/EMNLP, strongly encouraged at NeurIPS.

**Structure**:
1. **Scope limitations**: What problems/settings does the method NOT cover?
2. **Assumption violations**: What assumptions might fail in practice?
3. **Resource constraints**: Compute, data, or accessibility limitations
4. **Generalizability concerns**: Where might the results NOT hold?

**Common mistakes**:
- Writing token limitations just to check the box (reviewers notice)
- Using "limitations" as a chance to pitch future work instead of acknowledging real weaknesses
- Omitting limitations that are obvious to reviewers (they'll flag them anyway)

---

## Appendix

**Purpose**: Supplementary material that supports the main paper but would break the flow.

**Typical content**:
- Additional experimental results (more datasets, more baselines)
- Proofs and derivations
- Implementation details (architecture specifics, hyperparameter tables)
- Example outputs / qualitative results

**Common mistakes**:
- Putting crucial content in the appendix to save space (reviewers may miss it)
- Forgetting to anonymize supplementary material
- Not cross-referencing appendix content from the main paper

---

## Conclusion

**Purpose**: Close the loop. Mirror the introduction.

**Structure**:
1. **Problem → Solution → Result** (1-2 sentences, same as abstract but different wording)
2. **Limitations** (1-2 sentences, honest assessment)
3. **Future work** (1 sentence, specific direction, not generic)

**Common mistakes**:
- Copying the abstract verbatim
- Generic future work ("investigating other applications")
- Not acknowledging limitations