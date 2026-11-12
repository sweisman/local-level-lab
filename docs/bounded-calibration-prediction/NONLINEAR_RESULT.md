# Bound-aware aircraft prediction check

The corrected generated study closed 24/24 cases; 24 passed its technical checks. Numerical stopping checks passed in 23 cases. The withheld-position accuracy screen passed in 24 cases; 23 passed both numerical and accuracy requirements.

Case `sphere_rotating-1-increment-z_gyro_boundary` failed the numerical stopping check (unresolved; 44 evaluations). Its withheld-position accuracy result is reported separately.

Active calibration bounds occurred in 24 technically completed fits.

- Physical position: bounded tangent intervals contain 2880/2880 generated coordinates; fixed-parameter intervals contain 1307/2880.
  Median case interval width: latitude 0.000761028°, longitude 0.000603932°, height 13.0568 m.
- Future receiver report: bounded tangent intervals contain 2880/2880 generated coordinates; fixed-parameter intervals contain 2097/2880.
  Median case interval width: latitude 0.000763765°, longitude 0.000612213°, height 14.6809 m.

The 24 cases share a seed and matched noise streams; their
2,880 coordinates per target are not independent trials.
These are development counts, not a calibrated 95% aircraft
coverage statement. The affine bound
is applied to a nonlinear fitted forecast; its Taylor error
and the actual aircraft error law remain unqualified. Every
scientific decision abstains. No observed or protected flight
data were used.

[Corrected finite plan](NONLINEAR_V2_PLAN.md) · [Per-case results](nonlinear-results.csv) · [Prediction-error roadmap](../PREDICTION_ERROR_LAW_PLAN.md).
