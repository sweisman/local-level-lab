# Qualify direction-preserving calibrated-force bounds

Use the six existing generated candidate/processing inputs and four fixed
domains: the full calibration box, original yaw sector 4, a fixed calibration,
and the existing acceleration-gain boundary control. The same rule applies to
every candidate. There are **24 identities**. This tests a static force action,
not integrated aircraft motion.

Convert the first recorded velocity increment into a force interval with its
actual period and the supplied accelerometer bias/gain ranges. Bound the
rotation-vector action component by component; apply the exact supplied
installation matrix without renormalizing it. Add the declared gravity range.
Compare with the original norm-based acceleration bound and preserve wider
outcomes. No bound is reduced by observing a probe.

Validate each interval against an independent point calculation using the
existing source oracle and matrix exponential. Use 64 fixed probes per nonfixed
domain: lower corner, upper corner, midpoint and 61 seeded interior points.
The fixed domain uses one probe. All three axes must contain every probe within
an explicitly declared **1e-10 m/s² point-comparison margin**. That margin is not
a sensor-noise estimate or a floating-execution enclosure.

Finite allowance: **24 reference setups, 24 interval actions, 1,158 point oracles
and 6,948 scalar containment checks**. Reserve before execution and retain all
failures. Four workers use one numerical thread each; the cooperative overall
ceiling is **120 seconds**. No retries, expansion, process signals, native
trajectory integrations, original-aircraft reads, optimization or protected ESA
data. These controls do not qualify a full native propagation replacement.

Keep all 27 physical coordinates in domains and probes. This component depends
only on mounting, accelerometer calibration and gravity; it does not remove
other parameters from any subsequent model. Preserve raw input hashes, source
and numerical-environment versions, journals and atomic evidence.

[Rotation derivation](../ilvis0-directional-rotation/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
