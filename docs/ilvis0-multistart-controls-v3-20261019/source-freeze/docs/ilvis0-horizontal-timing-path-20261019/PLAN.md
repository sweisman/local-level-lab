# Timing path and derivative qualification

The preceding fixed-point study reproduced every saved endpoint. Its full
affine corrections did not reconcile the two IMU21 zero-field globe solutions.
Swapping only their approximately 19 ms timing difference increased cost from
about 5.56 to 18.73, whereas moving all parameters halfway gave 5.5695. Timing
and calibration therefore need to be examined together; neither a larger
iteration allowance nor a clock change is justified by these probes alone.

## Fixed observations and points

Use the same preselected IMU21 stretch, both processing cases and the zero-field
globe model. In each case evaluate thirteen fixed full parameter vectors:

- Both saved endpoints, reproduced exactly against their sealed arrays.
- Seven equally spaced interior points on the complete primary-to-repeat
  parameter path. All columns vary along this path, including timing.
- Symmetric timing-only perturbations of one microsecond around each endpoint.

The IMU8 unsubtracted specified-field globe primary is the control: its saved
center plus the same two timing-only perturbations. This gives **three diagnostic
identities /29 native tangent evaluations**, with **zero optimizer starts**.

## Analysis and limits

Compare the timing Jacobian column with the independently centered residual
finite difference; report absolute and relative errors and cost slopes. Record
distance to nominal integration boundaries rather than assuming a perturbation
stays within a smooth branch. The nine-point full path shows sampled cost
structure, not a minimized timing profile or a global optimum.

Keep the original covariance, nominal 200 Hz increment convention, bounds,
physical models and horizontal score unchanged. Preserve full predictions and
unscored height changes. Freeze source, input, environment and original hashes;
charge every call before execution under exclusive locks. No adaptive point
selection, retries, refits or label changes are permitted.

Use **four numerical threads**, a **15-minute wall ceiling**, and a maximum of
thirteen calls per identity /29 overall. Unused allowance is closed at completion
or failure. Publication reads saved artifacts only. The original 53-stretch
findings and the separate one-resolved/one-unresolved horizontal comparison stay
unchanged. The unscored height paths remain physically implausible and cannot be
presented as valid full-flight reconstructions.
