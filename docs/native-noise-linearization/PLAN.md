# Propagate errors through the moving-platform equations

The constant-level covariance examples are checked software components. The
next gate must use the actual native motion equations, including the three
physical candidates, gravity variation and recorded-increment sampling.
This first step qualifies a one-packet differential, without fitting a flight.

## Reuse the existing equations

Derive a separate, source-hashed header from the qualified wider-arithmetic
implementation and reuse `step_gravity` and its helpers. Append a small bridge;
do not copy the worker or rewrite the scientific propagation equations. Do not
edit the sources frozen by the running study. Record compiler, flags, source,
binary and scalar-precision bindings.

Preserve extended-precision mean coordinates, velocity and orientation across
native steps. Returning the mean through binary64 after every packet would
discard that property. The bridge takes corrected angle and delta-velocity
increments, actual interval length, physical candidate, gravity, radius,
removal fraction, optional height anchor and fixed lever arm.

## State and input derivatives

Compute nine state-error directions: three right-attitude perturbations, three
NED velocity perturbations and three receiver-chart coordinate perturbations.
Also compute six directions for corrected angle and delta-velocity increments.
Keep these process-error coordinates distinct from the existing 26/27 fitted
calibration parameters; this bridge does not remove their uncertainty.

Seed attitude derivatives analytically as the nominal orientation times a
skew matrix, without changing its mean. Map output orientation derivatives
through the inverse nominal output matrix. Preserve the mean orientation;
do not normalize or repair scientific measurements. Include the lever-arm
observation and its derivatives as well as the propagated state.

## Qualification

Use all three physical candidates and both removal cases, with and without
height-dependent gravity. Include nontrivial orientation, velocity, increments
and a nonzero lever arm. Compare mean observations with the existing wider
one-packet path and compare seeded/unseeded extended means. Check derivatives
with independent finite differences at sufficient precision and simple analytic
level-motion controls. Validate axes, signs and all state/input columns.

The qualification-run allowance is twelve generated candidate/case/gravity combinations,
at most 500 one-packet native evaluations and two cached native builds, with
one numerical thread and no trajectory fits, original reads, protected reads
or random draws. Charge test native evaluations before executing them. Bind a
fresh source/environment qualification before publishing a passing result.

## Further gates before aircraft use

A partial query and the endpoint of one native packet share the same measured
increment and noise. Preserve that cross-correlation when composing packet
transitions; do not replace it with independent noise on interpolated pieces.
Receiver-error persistence and fitted-calibration uncertainty must also remain
in the complete model. Whole-history known-motion and coverage controls are
required before any observed fitting revision.

Passing a one-packet differential qualifies that calculation only. It does not
establish an archive error law, change the running noise experiment, recover
failed fits or open the reserved confirmation groups.

[Covariance component](../integrated-noise-covariance/README.md) ·
[Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
