# Test the norm constraint against the actual saved source

This preflight tests a value range before any new native propagation candidate.
Use all six existing generated candidate/processing groups, always original
yaw sector 4 and its saved physical domain. The fixed selection does not depend
on which interval looks favorable. Keep all 27 physical coordinates and the
training-derived acceleration limits already in use.

Let `R` be the initial installation/correction map, `P` the accumulated body
rotation, `f` the calibrated first force sample, `A=R f` and `B=R(P−I)f`.
The frozen body-prefix operations provide the original bound on `B`. The saved
training-conditioned acceleration and gravity ranges provide the bound on `A`.
Rotation preserves vector length. Bound the small metric defect of the literal
installation matrix explicitly from `R0ᵀR0−I`; do not normalize the input.
Use that bounded norm relation to compute a vertical interval for `B`.

Report the original, raw geometric and intersected vertical ranges. Establish
the sign branch over the complete supplied domain. An unsupported branch must
remain unsupported. This is **value-only**: it does not qualify a Taylor
remainder or establish equality of native reference coefficients.

After fixing every interval, evaluate the existing known in-sector control once
per identity using independent quaternion rotations and point calibration.
Check all three `A` components, all three original `B` components and the new
vertical interval. The declared point-comparison margin is 1e-10 m/s²; it is
not a measurement-noise model or a floating-execution proof.

Finite allowance: **six identities, six reference setups, six bounded body
prefixes, six norm intervals, six point oracles and 84 scalar containment
checks**. Precharge at most 1,600 packet visits per bounded prefix and per point
oracle: **19,200 visits total**. Record actual visits separately; reserved visits
remain charged. Four workers use one numerical thread each; the cooperative
overall ceiling is **120 seconds**. No retries, extensions, signals, full native
trajectory calls, propagation bounds, LPs, optimizer starts, original-aircraft
reads or protected ESA data.

Successful containment and a tighter value interval would justify a source
reference-coefficient investigation. They do not permit aircraft fitting or
another complete prediction run. Preserve the failed earlier comparison and
its unused allowance.

[Operator derivation](../ilvis0-directional-dynamics/OPERATOR_DERIVATION.md) ·
[Baseline diagnosis](../ilvis0-directional-prediction/BASELINE_DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
