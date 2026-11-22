# The shape comparison across the full range of gyro field retention

The globe had the smaller best attainable direction error in all 64 matched
comparisons. For each shape, allow either zero physical background field or
the specified field with any fraction from 0% to 100% retained in the
gyroscope. The error bounds for the two shapes stayed apart in all eight
windows. The smallest guaranteed difference was 0.0160° RMS.

| Receiver query index | Leg | Smallest gap between the shape error bounds |
| ---: | --- | ---: |
| 15657 | First | 0.0383° |
| 19857 | First | 0.0307° |
| 26577 | First | 0.0440° |
| 30777 | First | 0.0323° |
| 51976 | Second, turn | 0.0665° |
| 53656 | Second | 0.0222° |
| 55336 | Second | 0.0303° |
| 57016 | Second | 0.0160° |

The table gives the smallest lower bound on the disc error minus the globe
error across the eight settings for each window. Each bound covers all
retained fractions, including those between the 81 grid points. The test
matches receiver differentiation, averaging and antenna correction between
shapes.

## Why the turn still matters

The disc had the lower error on this turn when the physical field was fixed
at zero. With the broader choice, the best disc error stayed at the zero
physical field result, roughly 0.078–0.080°. The best globe grid errors
were 0.005–0.013° with 90–97.5% of the specified field retained. That range
describes the grid locations of the minima under the tested assumptions.
Independent measurement of the field's magnitude and its cause remain
separate questions.

The [earlier error references](ESA_DIRECTION_HOLDOUT_SCORE_RESULT.md) remain
available for the three original settings. These references describe one
development recording. The new interval bounds cover the numerical field
search. Independent-flight accuracy and calibrated uncertainty remain open.

The error gap sets a target for that work. An RMS perturbation of size
\(\epsilon\) to the measured angles can change each model's best RMS error
by at most \(\epsilon\). The gap can therefore shrink by at most
\(2\epsilon\). With receiver predictions held fixed, an angle error below
0.0080° RMS would preserve all 64 rankings under the tested models. The
same calculation gives 0.0332° on the strongest turn. These are sufficient
error bounds to test against, and receiver prediction errors spend part of
the same margin. The observed error budget still needs measurement.

## Reproduce the check

The [plan](ESA_DIRECTION_HOLDOUT_FIELD_RANGE_PLAN.md) fixes the model,
predictions, observed angles and continuous bound. All sealed prediction
endpoints reproduced exactly. The largest allowance between adjacent
grid points was 0.00283° RMS. The task passed with 17 charged operations,
3,058,256 charged steps and zero fits in 74 seconds on one numerical thread.
It used the sealed angles and the original receiver reports from recording
187. The seven reserved flight groups remain unopened.

The [verified receipt](esa-direction-holdout-field-range.json) has SHA-256
`cf3de15eb1bc2612b3396ece861c66a7a1d19c66d6fa18d9cb29e3361dc56a8d`.
Manifest SHA-256 is
`e82ac738a039bac96a18fdba0ab9b747a4d477fb0a6e4a0fff6bab025f8d9ccf`.
The [portable evidence bundle](esa-direction-holdout-evidence/field-range/bundle.zip)
contains the frozen code, inputs, charges and outcomes for this stage.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_field_range prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-direction-holdout-field-range-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_field_range report
```
