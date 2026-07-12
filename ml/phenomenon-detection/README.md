# Phenomenon Detection Scripts

Small standard-library Python scripts that analyze the processed roll-call CSV and render simple SVG charts.

Default source:

```text
ml/pipeline/generated-data/processed/training_data.csv
```

Run from the project root:

```bash
python ml/phenomenon-detection/pass_fail_by_policy_area.py
python ml/phenomenon-detection/pass_fail_by_vote_type.py
python ml/phenomenon-detection/majority_margin_vs_passage_rate.py
```

Outputs are written to `ml/phenomenon-detection/output/` as both `.csv` summaries and `.svg` charts.

Useful options:

```bash
python ml/phenomenon-detection/pass_fail_by_policy_area.py --top 15
python ml/phenomenon-detection/pass_fail_by_vote_type.py --top 15
python ml/phenomenon-detection/majority_margin_vs_passage_rate.py --min-count 20
```
