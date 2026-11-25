# RF04 velocity reporting execution evidence

The receipt records the hashes of the frozen code, receiver extracts,
charge record and sealed output. [Result](../RF04_VELOCITY_RESOLUTION_RESULT.md) ·
[Plan](../RF04_VELOCITY_RESOLUTION_PLAN.md) · [Receipt](evidence-receipt.json)

From the repository root, verify the archived members with:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies check docs/ilvis0-measurement-contribution/rf04-velocity-resolution-evidence
```
