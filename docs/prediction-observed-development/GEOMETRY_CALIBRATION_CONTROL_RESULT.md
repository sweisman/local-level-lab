# A turn helps the local calibration calculation, but its fits did not qualify

The [four-case generated control](GEOMETRY_CALIBRATION_CONTROL_PLAN.md)
finished all four technical tasks with zero worker errors. Each case used the
same 120-second duration, generating model, calibration limits and **identical
IMU noise increments**. Only course pattern and height pattern changed. The
first 79 receiver reports were used for fitting; 40 later reports were held
out. The one-case technical preflight also passed.

| Case | Course during fitting | Height change during fitting | Fit converged? | Later horizontal path error |
| --- | ---: | ---: | --- | ---: |
| Straight, level | 90° throughout | 0 m | Yes | 2.22 m |
| Straight, shallow climb | 90° throughout | +21 m | Yes | 2.23 m |
| Turning, level | 116° → 88° | 0 m | **No** | 3.22 m |
| Turning, shallow climb | 116° → 88° | +21 m | **No** | 3.24 m |

Both turning fits stopped after 55 evaluations because the optimizer found
no positive predicted decrease; neither exhausted its 200-evaluation limit.
Their point paths are saved, but the nonconverged fits **remain failures**.
The [saved stopping audit](geometry-calibration-stopping-audit.json) checks
the original policy from its frozen source: both turning fits pass the
stationarity and physical-position parts of the final check, but their fresh
relative cost changes are about 1.6 × 10⁻⁷ and 0.9 × 10⁻⁷, above the
required 10⁻⁸. At the end of each trace, an unrestricted local correction
still predicts a small decrease but raises the actual cost. The shrinking
trust steps do not resolve this. This identifies the failing numerical check;
it does not establish that the fitted calibration is correct or that relaxing
the check would be valid.
Only the two straight cases pass the existing numerical and physical screens.
Their fitted sensor settings still differ from the known generated settings
by about 0.80 permitted half-ranges RMS across the 17 sensor parameters;
both Z gyro bias and vertical accelerometer bias sit near their limits.
Convergence and a modest later path error therefore do not establish good
sensor-calibration recovery.

At the saved fit points, the turn increases the weakest training singular
value about 1.42–1.44×, the Z-axis gyro-bias conditional Jacobian-column norm
about 1.44–1.45× and the vertical accelerometer-bias norm about 1.33–1.38×.
Those numbers include the **nonconverged turning points** and are diagnostics,
not accepted factorial effects. The shallow climb changes these norms by only
about 0–4%. It is too small to test the much larger climb in the opened ESA
development recording.

This control points to useful information from a change of course, while
exposing a separate solver limitation on the turning route. The next step is
to qualify numerical optima on a turning generated route with a separately
frozen, finite software trial before repeating a larger motion comparison. A
[fixed-point replay](TURNING_FIXED_POINT_RESULT.md) now shows that both
turning points evaluate repeatably, while every tested fraction of their
bounded correction raises the actual cost. No
Earth-model decision, aircraft error-law coverage or independent replication
follows from this study.

The [verified report](geometry-calibration-control-result.json) preserves all
four fits, exact source and manifest hashes, the nonconvergence reasons,
known sensor-setting errors, local tangents and conditional sensitivities.
The seven reserved ESA groups remain unopened.
