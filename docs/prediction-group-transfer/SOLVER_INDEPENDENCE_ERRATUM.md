# Scope correction for the generated solver checks

The generated forecast studies passed their recorded numerical gates, but
their two named fit providers were **not independent optimizers**.
`near_zero.fit_candidate` calls `trust_v2.fit_candidate` and adds a separate
stopping check for near-zero objectives. In the reported noisy generated
cases, the two providers therefore share the same bounded trust-region
optimization path. Comparing them checks the stopping wrapper and two
starting points; it does not rule out an error common to that optimizer.

This applies to the [full-calibration pilot](FULL_CALIBRATION_SOLVER_RESULT.md),
[multimodel control](MULTIMODEL_SOLVER_RESULT.md),
[nominal 200 Hz control](NOMINAL_200HZ_SOLVER_RESULT.md), and
[longer confirmation](LONG_HORIZON_SOLVER_RESULT.md). Their recorded fit
counts, paths, costs, physical screens, source hashes and failed-fit labels
remain intact. The longer study met its literal preregistered comparison,
but it does **not** meet the intended independent-method qualification.

The next method check must use a genuinely different bounded optimizer on
identical training inputs and compare its saved training cost and withheld
forecast with the existing trust-region result. An existing SciPy `trf`/
`dogbox` control provides a candidate implementation. It needs a finite,
source-frozen generated qualification before use on aircraft data. No
observed stopping label, prediction-coverage claim or Earth-model decision
changes because of this correction.
