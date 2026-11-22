# Fit the same forecast-error likelihood in native-whitened coordinates

The [initial transfer result](ESA_COMPONENT_SCALE_TRANSFER_RESULT.md)
found seven optimizer failures across eight checks. This follow-up tests
whether numerical conditioning prevents a complete comparison.

Use the original frozen component-scale study as the input. Bind its
manifest, report and forecast/receiver materials. Retain the same
training windows, withheld pairs, fixed paths, covariance components,
variance bounds, optimizer and stopping rule. Compare its fit outcomes
separately and preserve every earlier failure. Do not refit a physical
trajectory or open a reserved flight.

For each complete path, solve with the triangular native covariance
factor to transform the error vector and all roots. In these coordinates
the native term is identity. Fit the same independent-window composite
Gaussian score on the six training paths in each fold. The transformed
log determinant differs by a known fixed term for each path. Verify
equality of the adjusted likelihood and quadratic scores against the
original metre-coordinate calculation before fitting. Score the returned
scales in metres and retain all optimization outcomes.

Use known-answer controls for equivalent scores, recovery of separate
variance scales, bounds, unsupported terms and a poorly scaled native
covariance. The original held-out errors must stay outside the scale
estimator. If the controls do not pass, diagnose the software before
running the replay. A numerical pass only supplies a missing development
score. Reference counts and held-out log scores determine whether the
tested covariance improves within-flight transfer.

Freeze one task per original fold and two inertial error descriptions,
eight tasks total. Allow one primary fit of the three multipliers and
up to 100 likelihood evaluations in each task, one numerical thread and
a 120-second cooperative limit. Charge work before calculation.
