# Qualify the value-only trial calculation through full fits

Compare eight generated fits with their saved wider-arithmetic references.
Use all four candidates in each of two settings from the earlier study.
The specified-field disc history with profiled removal had the most rejected
trial evaluations among complete profiled settings. The zero-field globe
history without removal contains the only wider stopping failure. Both use
the original ±20°/hour calibration limit. This selection exercises solver
branches. It makes no claim about aircraft or model frequency.

Keep the original starts, 80 training evaluations per fit, calibration bounds,
training likelihood, native tangent and final stopping checks. Use the wider
value calculation to screen proposals and require exact agreement with the
full tangent at each accepted point. Compare the complete solver records,
including the accepted and rejected steps and the failed stop, with the
sealed references. Require exact agreement in the saved observations-free
forecasts. Report the actual native evaluation counts rather than treating
a value-only call as having the same cost as a tangent call.

Freeze the generated inputs, reference outcomes, numerical environment and
sources. Allow eight generated starts, up to 160 native training calls and
one forecast per start, four single-thread workers and a 20-minute cooperative
wall limit. Charge all value and tangent work before execution. The original
reference fits are read from the archive. No aircraft data are used.

[Earlier generated comparison](MATCHED_WIDE_RESULT.md) ·
[Saved aircraft point check](MATCHED_TRIAL_PROBE_RESULT.md).
