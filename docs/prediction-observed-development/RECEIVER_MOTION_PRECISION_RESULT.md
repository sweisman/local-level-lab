# Receiver course and climb rates cannot supply the needed motion bound

The three ESA training windows have modeled rate differences below
1°/h after allowing a constant instrument offset. If each model can
have its own unknown motion error, **0.065–0.341°/h RMS per model**
can close those gaps. The exact value depends on the window and model
pair. This is the required scale for an independent motion constraint
in that rate-only comparison.

The receiver's reported velocity precision gives much larger
uncertainty for directional rates.

| Smoothed slope | Median course-rate SD assuming independent errors | Median flight-path-angle-rate SD assuming independent errors | Median course-rate SD upper bound with unknown time correlation |
|---|---:|---:|---:|
| 30 seconds | 34.7–38.4°/h | 72.6–81.0°/h | 167–185°/h |
| 120 seconds | 4.5–5.0°/h | 9.5–10.5°/h | 43–48°/h |

The standard deviations are calculated from the exported marginal
velocity covariance. They are working precision scales, not measured
errors. The arbitrary-correlation column bounds the standard
deviation for any time correlation consistent with those marginal
variances. The error budget applies to a full vector rate path, while
the table describes smoothed individual directions. Their comparison
shows the scale gap without treating the numbers as identical
observables.

Ground course and climb angle describe how the aircraft travels.
Changes in the difference between heading and ground course, changes
in angle of attack and roll all remain outside these proxies. The
receiver export alone therefore cannot supply the independent motion
reference for the current rate-only comparison. The full inertial
forecast has a different error model and still needs its own
qualification.

All 2,400 fixed training reports were decoded and the receiver source
hash verified. The calculation used no inertial record, later scoring
position or reserved flight group.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.receiver_motion_precision replay
```

[Fixed design](RECEIVER_MOTION_PRECISION_PLAN.md) ·
[Frozen inputs](receiver-motion-precision-freeze.json) ·
[All motion precision and gap values](receiver-motion-precision-result.json)
