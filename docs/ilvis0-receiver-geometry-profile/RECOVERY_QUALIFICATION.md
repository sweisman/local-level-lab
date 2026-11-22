# Execution and recovery check

The prepared manifest SHA-256 is
`f91abb0d96287ea9e28b433cbead3b3d9373f2a7f2f0d7f8d795570452b516b2`.
It binds the 29 exact candidate source hashes, segment IDs, model-geometry
code, inputs, numerical environment, one worker and thread, a two-hour
cooperative limit and zero Earth-model fits.

The three focused geometry/source tests and 34 shared study/task-recovery
checks passed: **37/37**. The shared checks cover reboot continuation,
sealed-result reuse, preserved charges, source mutation and duplicate-owner
rejection. The idempotent entry point verifies frozen evidence and journals
before scheduling permitted unfinished work:

```sh
~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- \
  ~/venv/bin/python -m lll.studies run data/ilvis0-receiver-geometry-profile-20261116 \
  --reserved-threads 0
```

This is a technical execution check. It does not establish that aircraft
angular motion is independently known or that a candidate has calibrated
model-discrimination power.
