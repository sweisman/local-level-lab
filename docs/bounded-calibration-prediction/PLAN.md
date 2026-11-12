# A calibration interval that remains valid at a bound

The paired aircraft pilot found active calibration limits in every fit. Its
fixed-parameter prediction intervals therefore omit an important uncertainty.
This software control supplies a conservative reference for an **affine**
prediction with a known Gaussian error law and a declared parameter box.
It does not substitute for nonlinear aircraft validation.

Whiten the training design. Use its retained singular directions to form an
unconstrained Gaussian confidence ellipsoid for the identifiable calibration
combinations. Bound every discarded direction by the declared parameter box.
For each future coordinate, combine the resulting lower and upper conditional
mean limits with a conditional Gaussian future-noise interval. Split the
error allowance between calibration and future noise; the union bound gives
at least the declared marginal coverage when the true calibration is inside
the box and the covariance is correct. A fitted point at a box limit causes
no special exception. Keep all calibration columns and report discarded
directions. Return an abstention for malformed or numerically unsupported
inputs.

Qualify exact interior and boundary examples, rank-deficient designs and
Monte Carlo coverage with an implementation-independent simulator. The code
must label its narrow scope: linear mean, fixed known covariance and supplied
box. It cannot infer an aircraft noise law, validate the nonlinear tangent,
choose among physical models, or claim a detection. After those controls pass,
the next separate finite study can test nonlinear generated aircraft cases
under independent noise seeds, both IMU error laws and interior/boundary
calibration, preserving every failure and abstention. Recorded-aircraft
coverage remains gated on that result.
