# Qualify direct source-remainder components

The completed trace locates a large allowance in the rotating force source.
Test a direct mathematical construction before installing it in propagation.
The source and rotation-product inequalities are described in the
[method plan](../ilvis0-eastward-growth/NEXT_PLAN.md).

Freeze 13 known-answer controls: two exact bias/gain calibration laws
(increments and rate equivalents), four clipped-clock references, one shared
calibration/clock product, three noncommuting zero-reference rotation prefixes,
one force-product polynomial, one nonzero-reference nonlinear rotation prefix,
and one rejection group. Rotation values and derivatives come from independent
exact-rational series references. Shared parameters remain shared in the checks.

## Separate finite allowance

- 13 identities; 18 scalar/prefix bound calls, including four rejected attempts.
- Eight rotation-argument packet steps; no native trajectory calls.
- 376 fixed grid/axis probes, four rejection checks and 22 independent rational
  reference calls, including the derivative reference's nested value calls.
- One worker and one numerical thread; 60 seconds overall, checked cooperatively.
- No retries, observed fits, recorded-aircraft reads, LP proposals, protected
  ESA data, allowance expansion or process signals.

Freeze code, control catalog, exact inputs, test-package version and numerical
environment. These controls qualify component arithmetic and the sampled
known-answer paths. The operator-bound derivation, reference-value/derivative
reconciliation, source binding, full native propagation and useful prediction
widths remain distinct requirements. Passing cannot reduce an existing bound
or justify observational confidence by itself.

[Trace interpretation](../ilvis0-eastward-growth/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).

The preceding freeze completed 11 controls. Two checks did not execute because
the wrapper attempted an aggregate charge. This separate freeze charges each
bound call individually, with unchanged mathematics and its own full allowance.
The earlier failed outcomes and unused allowance remain preserved.
