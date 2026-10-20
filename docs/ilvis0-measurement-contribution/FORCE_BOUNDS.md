# Propagating uncertainty through the force calculation

All **30 nonlinear force-box checks pass**, including comparisons with an
independent Cartesian trajectory calculation for all three candidates and six
motion types. No original recordings or fitted results are used.

The acceleration-only diagnostic asks whether the measured force magnitude is
compatible with the force needed to follow the receiver trajectory. That
calculation is nonlinear: latitude changes the coordinate metric, while rates,
accelerations, gravity and background-field assumptions interact. A tangent
calculation or a few sampled perturbations need not bound that response.

## What the new calculation does

It takes explicit lower/upper bounds on the nine receiver-derived quantities:
position coordinates, their rates and their accelerations. Separate intervals
declare gravity and the candidate's background field. Interval operations carry
these bounds through the geographic metric, transport terms and required force.
The resulting three component intervals then bound the force magnitude.

The calculation uses the same declared ellipsoidal globe and stationary-disc
metrics as the existing exact-trajectory adapter. It does not infer geometry,
calibration or a background field from the error bounds. Zero-field candidates
cannot receive a nonzero field allowance. Boxes crossing the supported polar
domain or a nonpositive metric are rejected.

This supplies the nonlinear step following the
[derivative-error bounds](DERIVATIVE_BOUNDS.md). It avoids replacing a bounded
nonlinear response with an unqualified linear standard error. It may be loose:
discarding dependencies between coordinates can only enlarge the mathematical
enclosure. Overlapping boxes do not prove that one common calibration and
trajectory fits a complete recording.

## Verification and remaining limits

Independent Cartesian differentiation supplies the reference force on
stationary, slow, eastbound, northbound, changing-course and climbing examples.
Interior and boundary perturbations remain within the propagated boxes. Other
checks cover gravity ranges, point-valued inputs and invalid physical domains.

Arithmetic widens interval endpoints by one representable floating-point value.
This is not a formal certificate for every mathematical-library rounding error.
The bounds are deterministic under their supplied physical envelopes, not
calibrated confidence intervals or evidence of measured instrument accuracy.

The next gate assembles this prediction bound with common time support,
increment/count uncertainty, continuous-force averaging and sensor calibration.
The same declared allowances must apply to all candidates. An uninformative
result is retained, rather than tightening uncertainty to obtain separation.
The main 53-stretch result is unchanged.

[Implementation](../../analysis/lll/ilvis0_force_bounds.py) ·
[Independent checks](../../analysis/tests/test_ilvis0_force_bounds.py) ·
[Contribution overview](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
