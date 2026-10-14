# Offline evaluation

The dataset in `cases.jsonl` captures deterministic examples for supported local correlation rules. The runner calls the repository's `correlate_locally` function directly, so it does not call an external LLM and does not incur model charges.

Run from the repository root:

```bash
python -m pip install -r backend/requirements.txt
PYTHONPATH=backend python agentops/evaluation/run_eval.py
```

A passing case means the local diagnosis contains the expected terms. It does **not** prove the diagnosis is correct for every cluster, measure LLM quality, or verify that a suggested fix resolves a live incident. Extend the dataset with sanitized, reviewed cases and evaluate evidence attribution, false positives, fix safety, latency, and cost before production use.
