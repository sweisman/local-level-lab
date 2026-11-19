# Sealed force calibration score bounds

The [evidence bundle](replay.zip) contains the frozen plan, calculation
inputs, source snapshots and both results. It covers the saved calibration
check on one ESA development recording. The run made two bound calls and
started no new fits.

Verify all 369 archived artifacts from the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.portable verify \
  docs/prediction-observed-development/esa-force-score-evidence/replay.zip
```

[Method and results](../ESA_FORCE_SCORE_RESULT.md).
