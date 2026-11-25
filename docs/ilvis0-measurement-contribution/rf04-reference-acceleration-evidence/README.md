# RF04 receiver acceleration execution evidence

The receipt records the SHA-256 hashes of the frozen code, velocity
extract, matched path receipts, charge record and sealed output.
[Result](../RF04_REFERENCE_ACCELERATION_RESULT.md) ·
[Plan](../RF04_REFERENCE_ACCELERATION_PLAN.md) · [Receipt](evidence-receipt.json)

From the repository root, verify the archived members with:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies check docs/ilvis0-measurement-contribution/rf04-reference-acceleration-evidence
```
