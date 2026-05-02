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