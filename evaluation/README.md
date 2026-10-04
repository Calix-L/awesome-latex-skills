# Evaluation suite

Ten tasks, two per skill. [cases.json](cases.json) defines original inputs,
blind task prompts, limited literal invariants, and four human review questions
per task. Reference artifacts are maintainer-authored regression examples.

Read the [evaluation protocol](../docs/evaluation.md) ([中文指南](../docs/evaluation_CN.md)) before preparing paired
sessions. It explains isolation, attribution, fingerprints, scoring, evidence
review, repeated trials and failure analysis. Do not include this directory or
reference artifacts in an agent's prepared task workspace.

```sh
python scripts/als.py evaluate validate
python scripts/als.py evaluate prepare --case pdf-table --mode with-skill --output evaluation-runs/pdf-01
python scripts/als.py benchmark prepare --case polish-scope --trials 1 --output evaluation-runs/pilot-01
```
