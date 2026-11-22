# The shape ranking survives exact joint calibration, with one reversal

All **36 fits** passed the exact stopping check after correcting the
earlier-only gyro and accelerometer calibration. The globe had smaller
later direction errors in **17 of 18 matched settings**. The same
retained-field GLONASS setting still favors the disc, at **0.0756° RMS**
versus **0.0825°** for the globe. This comparison now passes the local
stopping check for both shapes.

| Matched field setting | Globe / disc lower error | Globe later RMS | Disc later RMS | Paired difference, disc minus globe |
| --- | ---: | ---: | ---: | ---: |
| Zero field | 6 / 0 | 0.240–0.259° | 0.352–0.368° | +0.106 to +0.113° |
| Specified field retained in gyro | 5 / 1 | 0.008–0.083° | 0.065–0.089° | −0.007 to +0.062° |
| Specified field removed from gyro | 6 / 0 | 0.240–0.258° | 0.352–0.367° | +0.107 to +0.112° |

The solver used two or three exact earlier evaluations per fit, including
the starting point. The largest final box-projected gradient was
**7.21 × 10⁻¹¹** against the unchanged **10⁻¹⁰** limit. Every fit still
reached at least one calibration bound. The original approximate results
and failed exact-gradient checks remain preserved.

These are locally stationary fits on one already opened flight. The
retained-field ranking changes across the receiver and averaging sensitivity
settings. The lower zero-field errors for the globe have no calibrated
absolute accuracy threshold. A global calibration range, a measured
direction-error law and independent prediction remain open.

All 36 fits and later value-only replays were saved. The numerical ledger
records 78 derivative evaluations and 36 value-only replays, with no full
inertial fits or original data reads. The 120 original position holdouts and
seven reserved flight groups remained outside the comparison.

## Reproduce the saved result

With the closed `data/esa-direction-exact-correction-v1` study restored,
verify the fits, scores and charges without starting a new search.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_exact_correction report
```

[Frozen design](ESA_DIRECTION_EXACT_CORRECTION_PLAN.md) ·
[All corrected fits, derivative checks and later scores](esa-direction-exact-correction-result.json)
