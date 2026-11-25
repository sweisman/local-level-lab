# Verify the paired-recorder checks on two additional flights

The archive receipt binds the original inputs, recorded charges and
completed results for both flight pairs. Check it from the repository root.
[Results](../MOTION_FALLBACK_RESULT.md) · [Plan](../MOTION_FALLBACK_PLAN.md)

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies check docs/ilvis0-measurement-contribution/motion-fallback-evidence
```
