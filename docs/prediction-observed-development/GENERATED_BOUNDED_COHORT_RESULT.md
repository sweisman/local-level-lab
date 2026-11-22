# Eight fresh generated fits repeat the physical-path problem

The [finite cohort](GENERATED_BOUNDED_COHORT_PLAN.md) closed **8/8 technical
tasks**: four independent noise seeds for each of two generated IMU error
laws, all on the same known 15-minute route. All eight fits passed numerical
checks. **None passed the source code's physical accuracy screen.**

| Generated error law | Fits | Later horizontal path error, median | Range across seeds | Median sensor-calibration difference |
|---|---:|---:|---:|---:|
| Increment | 4 | 146 m | 109–197 m | 0.46 allowed half-ranges |
| Point | 4 | 117 m | 67–182 m | 0.51 allowed half-ranges |

All eight fitted calibrations reached at least one allowed limit. The
original code requires no more than **0.1 m horizontal RMS**, 0.1 m vertical
RMS and 0.5 m maximum 3D error in both training and later periods. An
[accuracy-rule correction](GENERATED_ACCURACY_RULE_ERRATUM.md) records why
some frozen prose says 10 m. No cohort horizontal result falls between those
two numbers, so the wording error changes none of these failure labels.

Each case's known future truth lies inside **all 900 reported marginal
coordinate intervals**. That is a descriptive containment count, not an
independent 95% coverage validation. The intervals are broad: across cases,
their typical full widths are about 109 m north, 102 m east and 23 m up, with
much wider ranges near the end of the forecast. The interval uses an
earlier-only conditioned center and an assumed Gaussian error law; its
containment does not make the raw fitted path physically accurate.

This result extends the earlier two-case warning to eight fresh noise
realizations, while keeping the route, calibration box and model fixed. It
does not estimate the frequency of failure on real aircraft or qualify that
instrument's error law. No recorded or reserved aircraft data were opened.
The scientific decision remains **abstain**.

[Verified machine report](generated-bounded-cohort-result.json) ·
[Reporting rules](GENERATED_BOUNDED_COHORT_REPORT_PLAN.md) ·
[Calibration-substitution control](GENERATED_CALIBRATION_SUBSTITUTION_RESULT.md)
