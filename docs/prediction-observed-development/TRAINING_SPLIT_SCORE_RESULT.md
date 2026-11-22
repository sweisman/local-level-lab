# What the shorter ESA forecast shows

The first ESA development recording has 1,200 receiver reports over about
20 minutes. This retrospective check fitted the same globe-with-specified-field
model to reports 0–599, predicted reports 600–799, and opened those 200 later
positions only after both fits and their fixed-law conditioning calculations
had closed. Both declared IMU error laws passed their technical checks. Neither
fit reached a calibration bound; each training Jacobian had descriptive rank
26 of 26.

| Scored later reports | Raw horizontal RMS | Conditioned horizontal RMS | Raw height RMS | Conditioned height RMS | Heights inside nominal 95% ranges |
|---|---:|---:|---:|---:|---:|
| 600–799, increment law | 36.97 m | **1.94 m** | 0.34 m | **0.24 m** | 200/200 |
| 600–799, point law | 36.97 m | **1.94 m** | 0.34 m | **0.24 m** | 200/200 |
| 800–1199, earlier 800-report fit | 249.41 m | **2.85 m** | 4.35 m | **11.88 m** | 25/400 |

The last row is the previously completed [longer forecast](CONDITIONAL_COVERAGE_RESULT.md),
which used reports 0–799 for training. Adding its local fitted-parameter
uncertainty raised nominal height coverage only to **26/400**. The rows use
different training lengths and forecast periods; they are not competing fits
to the same 200 positions.

The shorter forecast supplies **no early warning** of the later height-range
failure. Both input-error laws give almost identical results here. The height
errors remain strongly correlated from one second to the next, so 200/200
inside nominal intervals on one recording does not establish 95% coverage for
future flights. The source of the later drift remains unknown.

The [saved score](training-split-score.json) contains every later timestamp,
signed north/east/up error, nominal interval half-width, fit rank and bound
status. The [fit result](TRAINING_SPLIT_FIT_RESULT.md) and the two hash-sealed
study completions document the source and work charges. No protected ESA
confirmation group was opened. This is development diagnosis, not an
Earth-model decision or independent validation; the scientific decision is
**abstain**.

The next gate is to explain or constrain the changing height error using
training-only evidence and independently justified error assumptions before
any reserved flight group is used for confirmation.
