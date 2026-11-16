# What the matched ESA forecasts show

On one already opened airborne-survey recording, each model was fitted to
the first 400 receiver reports and then predicted the next 120 without using
their positions for fitting. The same recorded IMU increments and receiver
times were used for every model.

The two complete settings both allowed the declared common upstream-removal
fraction to be fitted. Their **withheld horizontal RMS errors** were:

| IMU error convention | Globe with specified field | Globe with zero field | Tested flat disc |
|---|---:|---:|---:|
| Increment error | 5.18 m | 2,589.50 m | 3,997.37 m |
| Point error | 5.18 m | 2,589.50 m | 3,997.37 m |

These numbers come from training-selected starts, not starts chosen by their
later errors. The specified-field globe also passed the study's separate
position-error screen on both training and withheld reports. The other two
models did not. Under the *zero-removal* assumption, all four flat-disc
starts stopped without numerical convergence; those two matched settings
therefore remain **unresolved**, even though the globe fits completed. The
[saved stopping diagnostic](ESA_400_120_MODEL_MATRIX_STOPPING.md) identifies
the failed fresh-position check without changing those outcomes.

This is a substantial matched prediction difference on a **single
development flight**. The 120-report horizon was chosen after earlier work
on that flight. It does not measure how often the same ranking would occur on
independent flights, establish an aircraft prediction-error distribution, or
calibrate a false-decision rate. The study's scientific decision remains
**abstain**. The seven reserved ESA flight groups remain closed.

[Complete setting table](ESA_400_120_MODEL_MATRIX_RESULT.md) ·
[Every fit and error](ESA_400_120_MODEL_MATRIX_FITS.csv) ·
[Frozen plan](ESA_400_120_MODEL_MATRIX_PLAN.md) ·
[Execution record](ESA_400_120_MODEL_MATRIX_RUNTIME.md) ·
[Portable evidence](esa-400-120-matrix/runtime/portable-evidence.zip).
