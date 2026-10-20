# Bound the complete calibration relationship

The completed map diagnostic found that all 36 tested linear extremes fail when
their 24 error terms are recomputed from one physical calibration. The next V01
method must preserve that relationship, rather than add more matrix-only cuts.

## Implementation sequence

1. Implement interval values and all 27 first derivatives for scalar arithmetic
   and a skew-matrix exponential. Bound the exponential polynomial's value and
   derivative tails separately. Test signs, reciprocal domains and independent
   trigonometric references.
2. Use those components to enclose the complete 24-component static calibration
   map and its derivatives on a declared physical box. Preserve source bindings,
   normalization scales, zero-error conventions and explicit numerical allowances.
   The center is a fixed box center, never an opened known-truth calibration.
3. Convert the derivative enclosures into necessary affine relationships between
   the existing physical and common-error coordinates. Keep all coordinates;
   quantify interval and export error. Subdivision may tighten a bound but cannot
   drop untested physical regions.
4. Qualify this construction against independent generated controls before a
   separately frozen complete six-group/orientation prediction comparison.

The initial primitive tests are ordinary local checks, not a launched numerical
study. A finite matrix of source-map evaluations, probes, bounds, LP calls and
threads must be recorded before the new study launches. This plan creates no
native, observed-data or retry allowance. Completed studies remain unchanged.

Mean-value relationships require valid derivative enclosures throughout the
declared box. A locally fitted Jacobian, sampled extrema or a feasible nonlinear
point is insufficient. Real-arithmetic bounds, floating-point treatment,
prediction usefulness and calibrated observational coverage remain distinct.

## First source-map qualification allowance

Use the six preserved generated candidate/processing cases from the completed
joint-product prediction study. Cross them with four predeclared domains: the
full original normalized box, orientation sector 4, a fixed point at 0.1, and
a box with the first accelerometer gain fixed at its upper boundary. Each
source reference retains every parameter and derives its own unchanged radii.
Do not open the generated truth calibration to construct a bound or center.

There are **24 identities**, 24 source setups and **48 interval-map evaluations**:
one complete-box evaluation and one at its fixed midpoint per identity. Full,
sector and gain-boundary cases each use 64 probes (both ends, midpoint, then
61 independently seeded points). Fixed domains need only one probe. Total:
**1,158 oracle evaluations and 1,158 separate analytic Jacobians**.

The analytic reference uses explicit calculus and SciPy Frechet derivatives,
not the interval differentiation implementation. For each probe, verify all
24 values, all 24×27 derivatives and all 48 exported coupling inequalities.
This is 48 value endpoint inequalities, 1,296 derivative endpoint inequalities
and 48 coupled inequalities: **1,611,936 scalar inequalities total**. Perform
coupled checks with exact rational arithmetic on the stored binary inputs.

The declared source-value numerical allowance is 3e-10 per normalized error
coordinate. Analytic derivative comparisons allow 3e-8 in normalized derivative
units. That comparison tolerance does not enlarge the exported coupling rows
or supply their gradient bounds. Interval differentiation and analytic tails
provide the mathematical enclosures; finite agreement checks do not prove
all floating-point behavior. Zero-radius source invariants must be tested,
never replaced by artificial denominators. These are numerical assumptions,
not sensor-accuracy claims.

Freeze sources, inputs, environment, seeds and the finite per-identity counters.
Reserve every setup, bound, oracle/Jacobian pair and inequality batch before
execution. Four workers use one numerical thread each, with a 300-second
cooperative wall ceiling. No retries, LP calls, new native predictions,
original-aircraft reads or observed fits. Preserve every failed probe. All
24 identities must pass before a new prediction-support comparison can follow.
Observational coverage and useful full-record widths remain separate gates.
