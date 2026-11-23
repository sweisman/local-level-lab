# How accurate must the aircraft GPS ranges be?

Nuuk Museum observations cover 99.98% of the range-weight norm in the
two-minute ESA development score. With the same example assumptions, this
raises the allowable error in the covered directions from **0.62 mm to
0.96 mm RMS**. The comparison uses the same aircraft observations, the
same model-score gap and the checked geometric approximation allowance
for both stations.

| Error in the aircraft ranges | Score change per millimetre RMS with Qaqortoq’s coverage | With Nuuk Museum’s coverage |
| --- | ---: | ---: |
| Directions covered by the ground measurements | 0.02237 | 0.02282 |
| Remaining directions | 0.00452 | 0.00047 |

The example assumes one metre of position error per coordinate at each
reference time, two millimetres RMS of range error outside the match, and
1.876 mm/s² RMS acceleration of the position error. These are input assumptions.
The 0.96 mm is the limit those assumptions leave for the covered directions,
given the saved gap of 0.044958. Both RMS terms are defined over the original
2,496 signed half-second values projected onto their respective directions.
The calculation uses the original aircraft ranges without a station
correction. The earlier transfer test found that applying either trained
station correction barely changed the later ranges. [Ground correction test](ESA_NKAR_PHASE_TRANSFER_RESULT.md)

The archived flight 187 RINEX header identifies a Javad Delta receiver and
leaves the antenna model blank. The campaign paper describes three
receivers sharing one roof antenna and gives estimated offsets from the
antenna to the inertial instruments. Those offsets describe the installation.
A carrier-phase calibration also needs the antenna response as the direction
to each satellite changes. The receiver comparisons and ground matches leave
aircraft antenna, tracking, anchor position and motion errors open. [Campaign instrumentation](https://essd.copernicus.org/articles/17/1667/2025/index.html#section2.3) · [IGS antenna calibrations](https://igs.org/wg/antenna/)

The [calibration inventory](ESA_ANTEX_INTAKE.md) identifies published
patterns for the Nuuk Museum antenna and all 11 GPS satellites. Applying
these patterns on the saved times changed less than 0.002% of the score
gap. The airborne antenna remains unidentified. [Antenna replay](ESA_NKAR_ANTENNA_RESULT.md)

The [motion-axis check](ESA_MOTION_AXIS_SUPPORT_RESULT.md) shows that the
score gap can be spanned by an error entirely in the north–south direction.
An independent motion check therefore needs sensitivity to horizontal error.

The result abstains. All four independent error caps remain missing. It
uses one development flight, with no new fits and zero reserved flight reads.
[Frozen method](ESA_NKAR_ERROR_BUDGET_PLAN.md) · [Numerical receipt](esa-nkar-error-budget-v1.json)

Run this from the repository root to verify the receipt from the saved
reports. The original flight downloads are unnecessary for this check.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.esa_nkar_error_budget check
```
