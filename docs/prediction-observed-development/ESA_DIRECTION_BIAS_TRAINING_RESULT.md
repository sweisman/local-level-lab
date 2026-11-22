# The direction forecast still favors the globe after fitting X bias on earlier data

The globe had smaller later force-direction errors in all **18 matched
comparisons** after each shape was allowed to estimate its own X-axis
accelerometer bias and starting rotation from the first eight directions.
With the specified field retained in the gyro, the globe forecast error
was **0.004–0.011° RMS**, compared with **0.111–0.121°** for the disc.

| Matched field setting | Earlier-selected X bias, globe / disc (m/s²) | Later angular RMS, globe / disc |
| --- | ---: | ---: |
| Zero field | +0.0270 to +0.0310 / +0.0460 to +0.0500 | 0.295–0.312° / 0.405–0.430° |
| Specified field retained in gyro | −0.0020 to −0.0005 / +0.0150 to +0.0165 | 0.004–0.011° / 0.111–0.121° |
| Specified field removed from gyro | +0.0275 to +0.0315 / +0.0465 to +0.0510 | 0.297–0.314° / 0.406–0.432° |

The earlier data rule out the positive range **+0.0225 to +0.10 m/s²**
within the retained-field globe's fixed direction calculation. Using
the continuous bound between grid points, the narrowest margin would
survive a uniform change in earlier measured directions of about
**0.0126°** per direction. This is a sufficient perturbation margin,
conditional on the model predictions and all other calibrations being
fixed. No aircraft error bound at that scale has been established.
The same positive range contains the best earlier bias for both globe
settings where the gyro has no retained field. This shows why the
retained-field estimate alone cannot establish the instrument’s bias.

The [fixed-bias transfer](ESA_FORCE_DIRECTION_TRANSFER_RESULT.md) still
reverses at +0.10 m/s² when applied to both models with the specified
field retained. The new comparison answers a different question by
selecting bias solely on the earlier directions. All comparisons reuse
one already opened flight and the later directions have been examined
in prior studies. These are retrospective forecasts under a one-axis
calibration model. The results leave joint calibration, real direction
error and independent-flight coverage open.

All 36 profiles and 18 comparisons completed under their recorded
limits. No full inertial fit, original data read, reserved-flight read or
read of the original position forecast's 120 later receiver reports was
used.

## Reproduce the result

With the closed `data/esa-direction-bias-training-v1` study restored,
run the saved-report command to verify charges and results without
refitting the alignments.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_bias_training report
```

[Frozen design](ESA_DIRECTION_BIAS_TRAINING_PLAN.md) ·
[All profiles, later errors and continuous margins](esa-direction-bias-training-result.json)
