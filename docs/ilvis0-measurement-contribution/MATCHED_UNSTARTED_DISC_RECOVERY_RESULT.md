# The recovered IMU21 fit completes one four-candidate forecast comparison

The previously unstarted zero-field disc fit passed the original stopping
check. It took eight training evaluations and one forecast call.
All four candidates for this IMU21 recording now have verified forecasts
for the same **148 later GPS reports**.

| Candidate | Horizontal RMS, onboard GPS | Height RMS, onboard GPS | 3D RMS, onboard GPS |
| --- | ---: | ---: | ---: |
| Globe, specified field | 2.18 m | 5.05 m | 5.50 m |
| Disc, specified field | 70.07 m | 8.28 m | 70.56 m |
| Globe, zero field | 134.97 m | 7.64 m | 135.18 m |
| Disc, zero field | 178.86 m | 4.47 m | 178.91 m |

At the same specified field, the globe has lower horizontal and height
errors. At zero field, the globe has lower horizontal and 3D errors and
the disc has lower height error. Both reconstructed GPS references give
these same orderings. This is one recording whose [original in-sample
zero-field costs](../analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md#the-reserved-development-pilot)
favored the disc. The withheld forecasts now show a different ordering
for horizontal and 3D position error.
The [shared-receiver check](MATCHED_IMU21_RECEIVER_HULL_RESULT.md) verifies
that both shape orderings survive the measured GPS spread, including
the disc's lower height error at zero field.

The separate continuation used the original archived source, model,
earlier input and numerical environment. It completed in 169 seconds
on one thread and charged 9 of 31 native calls, with no interruption.
The [replay](matched-unstarted-disc-result.json) verified all four
training prefixes, all three receiver scores and the original charges.
This is one retrospective development recording. The IMU8 zero-field
disc remains a stopping failure and the aircraft error law remains
unqualified.

To reproduce the saved scores from the repository root, run the report
without launching a fit.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_unstarted_report
```

[Continuation plan](MATCHED_UNSTARTED_DISC_RECOVERY_PLAN.md) ·
[Sealed execution](../ilvis0-matched-unstarted-disc-runtime/README.md) ·
[Reproduction bundle](../ilvis0-matched-unstarted-disc-runtime/bundle.zip)
