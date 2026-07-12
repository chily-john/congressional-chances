# Data Leakage Constraints

The project predicts **roll-call passage** before the outcome is known. Inputs must not include fields that directly reveal, summarize, or are computed from the final vote result.

## Prohibited fields

`ml/config/features.yaml` lists excluded leakage fields. Current prohibited examples include:

- Result labels: `result`, `passed`, `failed`, `passage_status`.
- Vote totals: `yea_total`, `nay_total`, `present_total`, `not_voting_total`, `vote_margin`.
- Outcome-revealing text: `result_text`, `outcome_summary`, `final_action`.

## Why these are excluded

These fields are only known after or during final tabulation. Including them would let the model learn the answer instead of learning pre-vote context. That would produce misleading sample metrics and would not support real pre-vote roll-call passage prediction.

## Review checklist

Before adding a feature, ask:

1. Would this value be available before the roll-call outcome?
2. Is it derived from yea/nay totals, result text, or final action text?
3. Does it encode bill enactment rather than roll-call passage?

If any answer is yes or uncertain, exclude it and record a TODO until the data source is confirmed.

Current scaffold artifacts/metrics are not real model outputs.
