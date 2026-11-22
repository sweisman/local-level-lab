# Generated and observed training errors

This saved-only check compares the first 600 receiver reports in the ESA
development fit with two independently generated 600-report training fits.
Each generated recording was fitted under both declared IMU error laws using
the same measurements within that recording. No fit was repeated, and no
later receiver position or reserved confirmation flight was used.

| Recording | Whitened error RMS, north | East | Height | Overall |
|---|---:|---:|---:|---:|
| Generated with increment error | 0.966 | 1.007 | 1.010 | 0.995 |
| Generated with point error | 0.978 | 1.019 | 1.016 | 1.004 |
| ESA development recording | **0.062** | **0.046** | **0.077** | **0.063** |

The two fitted candidate laws give virtually identical values within each
recording. The generated errors remain near unit scale after fitting. The ESA
training errors are much smaller under the same declared scaling. Its height
error also retains a correlation of **0.825** between adjacent receiver reports
and **0.538** at 20 reports apart; the generated height correlations are near
zero at those lags. The observed height RMS falls from 0.096 in the first half
to 0.052 in the second half, while the generated height RMS stays near 1.

This comparison identifies where the mismatch lies; it does not identify its
cause. The generated fits reach calibration bounds, the ESA fit does not, and
the synthetic noise assumptions may differ from the recorded measurement
process. Two generated recordings cannot calibrate a tail probability. The
later ESA height predictions still fail their declared accuracy check.
An observed error law and prediction-adequacy rule therefore remain open.

The [saved report](FIT_ADJUSTED_RESIDUAL_REPORT.json) records all three axes,
two half-recording scales, lag correlations and source/study hashes. Its
source and focused tests are in `analysis/lll/esa_fit_adjusted_residual_report.py`
and `analysis/tests/test_esa_fit_adjusted_residual_report.py`. The scientific
decision remains **abstain**.
