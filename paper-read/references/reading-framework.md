# Reading Framework

## Skim Strategy (30 seconds)

Goal: decide whether this paper is worth reading.

1. **Read the title**: What field? What specific problem? 
2. **Read the abstract**: Problem → Approach → Result → Implication
3. **Scan figures**: What's Figure 1? What's the main result table? Do the figures tell a coherent story?
4. **Check venue**: arXiv preprint? Workshop? Top conference? This sets baseline expectations.
5. **Look at last paragraph of intro**: Usually contains the contribution list.

After skim, you should know: the problem, the approach in one sentence, and whether you need to read more.

## Read Strategy (5 minutes)

Goal: understand the method well enough to discuss it and apply the insights.

### Introduction
- Identify the 5 funnel components: broad context → narrow problem → gap → approach → contributions
- Check: are the contributions clearly listed? Do they match the experiments?
- Check: do they overclaim? ("First work to..." is often untrue)

### Related Work
- How do they organize it? Thematic? Chronological?
- Do they fairly represent competing work?
- What position do they take vs prior work? ("We improve X" vs "X is fundamentally wrong")

### Method
- **First pass**: Read section titles and figure captions only. Build mental model of the architecture.
- **Second pass**: Read the text of each component. Focus on WHY each design choice was made.
- **Key equations**: Find 2-3 most important equations. What do they mean in plain English?
- **The "trick"**: Every strong paper has a key insight. What's the one thing that makes this work?

### Experiments
- Start with the main result table. What's the headline number? Compared to what?
- Then read setup: datasets, baselines, metrics, hyperparameters.
- Then ablations: what components are tested? Are the right things ablated?
- Look for what's NOT shown: missing baselines, missing datasets, missing failure analysis.

### Conclusion
- Does it accurately reflect the results? Or overclaim?
- Are limitations discussed? (If not, this is a red flag.)
- Is future work specific or generic?

## Deep Read Strategy (15+ minutes)

Goal: evaluate whether the paper's claims are supported, identify hidden assumptions, and find ideas for your own work.

### Line-by-Line Focus Areas
1. **Method section**: Every design choice, every equation. Do they form a coherent story?
2. **Experiment section**: Every baseline, every ablation. Are the right questions being asked?
3. **Appendix**: Often contains the really important results or critical implementation details.

### Consistency Checks
- Notation: same symbol means the same thing everywhere?
- Terminology: same name for same concept?
- Lore: Does intro claim match conclusion? Does method description match experiments?
- Numbers: Do values in tables match values reported in text?

### Assumption Auditing
Explicit assumptions: stated in the text ("We assume i.i.d. data...").
Implicit assumptions: NOT stated but required for the method to work.

Find implicit assumptions:
- What kind of data does this require? (labeled? balanced? clean?)
- What kinds of tasks would this fail on?
- What if the dataset is 100x smaller? Or from a different distribution?

### Idea Mining
For each paper, extract ideas relevant to your own research:
1. **Usable methods**: Things you could directly apply
2. **Adaptable insights**: Ideas you could modify for your context
3. **Open problems**: Questions the paper raises but doesn't answer
4. **Avoided approaches**: Things the paper tried that failed (these are as valuable as successes)

### Forward Citations
After reading, check who has cited this paper (via Semantic Scholar or Google Scholar):
- High citation count → likely influential, worth understanding deeply
- Recent citing papers → shows how the community is building on this work
- Contradictory citations → other papers that challenge or fail to reproduce these results

## Paper Type Adjustments

Not all papers follow the standard method-experiment structure. Adjust your reading strategy:

### Survey / Position Papers
- Focus on: taxonomy of approaches, identification of open problems, quality of coverage
- Less focus on: individual method details (these are summarized, not proposed)
- Key question: Does this survey provide a useful lens for the field, or is it just a reorganization of prior work?

### Theory / Proof-Heavy Papers
- Focus on: theorem assumptions vs conclusions — a strong theorem with weak assumptions is more valuable than the reverse
- Check: Are assumptions realistic? Do they hold in practice?
- Evaluate: Is the proof technique novel, or a straightforward application of known methods?
- Key question: Does the theory explain WHY something works, or just THAT it works?

### Empirical Studies
- Focus on: experimental design, scale of evaluation, fairness of comparisons
- Check: Are claims supported by the data, or do the authors overinterpret?
- Key question: Does this change what the community believes about [topic]?

### Dataset / Benchmark Papers
- Focus on: dataset construction methodology, annotation quality, bias analysis
- Check: Is the dataset representative? What populations are over/under-represented?
- Evaluate: Will this dataset enable meaningful evaluation, or does it embed the authors' assumptions?
- Key question: Does this dataset advance the field, or does it merely reflect existing biases at scale?

## Venue Status and Expectations

Adjust your reading confidence based on publication status:

### Peer-Reviewed (NeurIPS/ICML/CVPR/ACL/ICLR/AAAI)
- Claims have passed reviewer scrutiny — give benefit of the doubt on experimental rigor
- Still verify: reviewers miss things, especially in supplementary material
- Check for: reviewer rebuttals (ICLR/OpenReview) that may reveal weaknesses the authors addressed

### Preprints (arXiv, SSRN, bioRxiv)
- No peer review yet — be more skeptical
- Common issues in preprints: missing baselines, incomplete ablations, overclaimed contributions
- A preprint's claims are proposals, not findings
- Check: has this been subsequently published at a venue? The published version may differ significantly

### Workshop Papers
- Typically early-stage work with incomplete experiments
- Look for promising ideas rather than polished results
- Check: has the work been extended to a full paper since the workshop?

### Journal Versions
- Often stronger than the conference version (more experiments, revisions based on reviewers)
- Check if this is an extended version: "Journal version of [conference paper]"
- Compare to the conference original if cited — what changed?
- Journal versions may have additional theoretical guarantees or more comprehensive experiments

### Technical Reports / White Papers
- Industry reports may have access to resources academics don't — check if results are reproducible
- May have commercial motivations — check for cherry-picked benchmarks
- Often lack implementation details needed for reproduction

## Reading for Implementation

When you're reading a paper to **reimplement** it (not just understand it), adjust your strategy:

### What to prioritize
1. **Algorithm pseudocode**: This is your blueprint — map it directly to code
2. **Architecture diagrams**: Every box → a module, every arrow → data flow
3. **Hyperparameter tables**: You need exact values, not "standard settings"
4. **Training procedure**: Learning rate schedule, batch size, optimizer, epochs — all of it
5. **Loss function**: Write this down verbatim — it's the most common source of bugs

### What to be skeptical of
- Missing implementation details ("we use a standard transformer" — which variant? how many layers?)
- "We found X worked best" without ablation — might be critical or might not matter
- Architecture diagrams that don't match the text — the text is usually more accurate
- Claims about simplicity — if it was simple, the paper wouldn't be 10 pages

### What to skip on first pass
- Related work (unless you need to compare approaches)
- Theoretical analysis (come back after you have working code)
- Qualitative examples (focus on quantitative results first)