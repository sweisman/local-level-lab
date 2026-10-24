# Predicting positions that were left out

**One of the three preselected recordings completes the full prediction check.**
On that northern IMU21 stretch, the globe model with the specified background
field follows later receiver positions to about **0.84–1.13 m horizontal RMS**.
Zero-field globe misses by about **496 m**, and the specified disc by about
**793 m**. Height RMS is about **3.3 m, 7.2 m and 35.8 m**, respectively.
This repeats under both clocks and both processing assumptions.

Calibration used the earlier two-thirds of each recording. Later GPS positions
were opened only after the continuous IMU forecast was saved. They did not adjust
its initial state, calibration or path. The reported starting point was chosen
by training cost alone, with every alternative and failure preserved.

## The three recordings

An IMU is an inertial measurement unit containing gyroscopes and accelerometers.
The format codes below identify decoded configurations, not verified individual
instrument identities. These are three distinct conservative flight groups;
they are not automatically three independent instrument installations.

| Stretch | IMU code | Selected length | Median ground speed | Mean latitude | Mean course |
|---|---:|---:|---:|---:|---:|
| A: Ames 510, southern survey | 8 | 11.13 min | 858.0 km/h | 62.65° S | 119.54° |
| B: Ames 610, northern survey | 21 | 7.27 min | 820.7 km/h | 42.29° N | 8.73° |
| C: 610, southern survey | 21 | 11.15 min | 837.7 km/h | 63.96° S | 191.67° |

The later scoring blocks contain 223, 146 and 223 GPS fixes, respectively.
[Exact filenames, hashes and intervals](../ilvis0-prediction-pilot-preparation/selection.csv)
and the [saved split description](../ilvis0-prediction-pilot-preparation/README.md)
identify every input.

## What completed, and what did not

The run returned all **72 planned fits**, using 3,342 native calculations over
3.80 hours. **49 fits passed numerical checks; 23 did not.** Those counts describe
optimizer completion, not votes for physical models. Training-only selection
supplies a qualified primary in 28 of 36 model/clock/processing combinations.

A matched comparison needs a qualified primary for each of the three physical
candidates under the same clock and processing assumption. Five of twelve such
comparisons are complete: all four settings on B, one on C, and none on A.

| Stretch | Complete matched settings | Field-globe horizontal RMS | Zero-field globe horizontal RMS | Disc horizontal RMS |
|---|---:|---:|---:|---:|
| A | 0/4 | No complete matched comparison | — | — |
| B | 4/4 | 0.84–1.13 m | 496.28–496.29 m | 793.42 m |
| C | 1/4 | 3.30 m | 32.31 m | 312.59 m |

The field-globe model has the smallest horizontal and total three-dimensional
RMS in all five complete settings. The four B settings reuse one recording;
they are sensitivity checks, not four independent replications.

On C, the single complete setting is nominal 200 Hz under the zero-removal assumption.
Its height RMS is 8.91 m for field-globe, 6.33 m for zero-field globe and 7.91 m
for disc. Field-globe has the smaller total error because its horizontal error
is much smaller. Other required C settings remain incomplete.

On A, the numerically qualified field-globe primaries have 15.5–19.3 m horizontal
RMS and about 10.5 m height RMS. They fail the frozen horizontal accuracy screen.
Missing required fits also prevent a complete matched comparison. Smaller errors
than the available alternatives do not make A a successful prediction result.

## Accuracy, uncertainty and scope

The original shared manifest carries a generic generated-controls scope label.
This pilot used observed archival data, as specified by its frozen plan, source
references and 72 recorded fit starts. Those records remain unchanged. New study
definitions preserve an explicit purpose in the hashed manifest.

The accuracy screen was fixed before fitting: horizontal RMS at most 10 m,
height RMS at most 30 m, maximum horizontal error at most 50 m and maximum
absolute height error at most 150 m. Seven of 28 qualified primaries pass;
all seven are field-globe fits. B passes in all four settings and C in three
available settings. These are descriptive accuracy limits, not calibrated
goodness-of-fit tests or detection thresholds.

The saved audit verifies every artifact and charge, recomputes physical errors
from saved forecasts and receiver positions, reconciles training costs and
numerical labels, and checks accuracy labels against the frozen limits.
It performs no new fit or forecast. Both starts and their prediction differences
remain available; their spread is sensitivity, not a confidence interval.

This is retrospective development validation: these recordings had already
informed the project. Receiver coordinates retain their conventional geodetic
construction, the error weights are assumed rather than calibrated, and the
background field's magnitude was specified rather than freely measured. This
test establishes neither statistical significance, the field's cause, nor a
solar-versus-sidereal rate distinction. Reserved ESA groups remain untouched.

The original **53 globe preferences, zero flat preferences and zero unresolved**
full-position comparisons are unchanged. This pilot adds a successful unused-data
prediction check on one recording and preserves the limits exposed by the others.
It does not add 72 new flights to the evidence count.

[All primary results and reproducible evidence](README.md) ·
[Frozen scientific plan](PLAN.md) · [Initial packaging failure](../ilvis0-retrospective-prediction-pilot/README.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md) · [Next work](../NEXT_STEPS.md)
