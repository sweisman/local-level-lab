# Can the ESA rate adapter reconstruct a maneuvering flight?

This software qualification addresses the next ESA prerequisite: complete
geographic motion, rather than component integrals or a quiet trend fitted to
GPS samples. It uses generated observations with known trajectories, not an
ESA recording. The zero-eligible version-1 inventory and reserved confirmation
groups remain unchanged.

## Independent known answers

Generate trajectories directly in fixed Cartesian geometry. Define latitude,
longitude, height and body attitude as analytic functions of time, and obtain
their first and second derivatives analytically. Use the ellipsoid geometry
for both globe candidates and the specified polar-disc geometry for the disc.
Obtain gyro rates from differentiated body-frame axes. Obtain specific force
from Cartesian acceleration, the declared background field and gravity.

The generator must not import the navigation predictor, its coordinate-rate
or transport formulas, or `lll.models`. It supplies true initial position,
velocity and attitude, original rate/force samples, and exact later coordinates.
No fit or receiver-derived attitude enters this test. Both zero upstream
removal and a declared 35% common conventional-field removal are tested.

Use two fixed maneuver patterns: a slow changing course with independently
changing roll, pitch and yaw; and a faster alternating-axis attitude pattern.
Both include changing speed and height. Freeze the precise analytic amplitudes,
periods, phases and starting coordinates below. They define the tested
capability, not a claim about every possible flight.

Use radians internally, WGS84 semi-major axis 6,378,137 m and flattening
1/298.257223563, disc scale 6,371,000 m, gravity 9.81 m/s² and the specified
background magnitude 0.00007292115 rad/s. These are explicit generated inputs.
Starting longitude is −40°. With `a = 6378137`, latitude `p0` equal to ±55°,
and time `t` in seconds, the common coordinate recipe is:

\[
\begin{aligned}
\phi(t)&=p_0+\frac{8}{a k_\phi}\sin(k_\phi t),& k_\phi&=2\pi/300,\\
\lambda(t)&=-40^\circ+\frac{75}{a\cos p_0}
 \left(t+\frac{0.1}{k_\lambda}\sin(k_\lambda t)\right),& k_\lambda&=2\pi/180,\\
h(t)&=600+10\sin(k_h t),& k_h&=2\pi/240.
\end{aligned}
\]

Body-to-local attitude uses yaw–pitch–roll order `Rz(yaw) Ry(pitch) Rx(roll)`.
Each angle is its amplitude times `sin(2πt/period)`, with π/2 added to yaw.
The slow pattern's `(amplitude rad, period s)` values are yaw `(0.12,120)`,
pitch `(0.03,90)` and roll `(0.06,60)`. The faster pattern uses yaw
`(0.25,25)`, pitch `(0.08,13)` and roll `(0.15,9)`. The initial state is the
generator's exact state at zero. These deliberate maneuvers exceed the old
quiet-flight cutoff; they are capability tests, not inferred aircraft behavior.

## Matched calculation

Use the existing streaming `airquantumgrav_increments.IntervalStream` under
each of its three explicit hypotheses: left hold, right hold and linear points.
Preserve its gap, timing, units and chunk-continuation checks. Constructed
increments remain mathematical interpretations of rate samples.

Feed those increments into the unchanged native geographic navigation kernel.
Do not replace the native equations with the truth generator, fit calibration,
reset to later positions or score only selected axes. Use the true initial
state and declared gravity and removal fraction. Antenna lever arm is zero in
this first geographic check; a nonzero lever arm and uncertain initialization
remain separate requirements before an observed-data study.

Test all three physical candidates, starting latitudes +55° and −55°, both
removal assumptions, both maneuver patterns and all three sampling hypotheses:
**72 identities**. Each identity propagates 1,200 seconds at 300 Hz and again
at 600 Hz. Query the same 1,200 epochs, from 0.5 to 1,199.5 seconds at one-second
spacing, avoiding an unsupported final boundary.

## Checks fixed before execution

- Test the generator's derivatives against an independent numerical derivative
  at 0, 7, 31, 143 and 599 seconds. Use a five-point stencil for Cartesian
  derivatives at half-widths 0.5 and 0.25 seconds, with maximum velocity and
  acceleration disagreements of 0.00001 m/s and 0.00001 m/s². Check body-axis
  derivatives separately at 0.01 and 0.005 seconds, with angular-rate
  disagreement at most 0.00000001 rad/s. Check proper body rotations, signed
  gyro axes, specific-force direction and the zero-motion limit.
- Compile both native translation units from the declared isolated source
  snapshot before the study. Missing dependencies block preparation.
- Require every candidate and sampling hypothesis to reconstruct a complete,
  finite trajectory with all three coordinate axes and no hidden position reset.
- For each hold rule, require the finer grid's maximum three-dimensional error
  to be at most 0.6 times the coarse-grid error plus 0.001 m. For linear points,
  require at most 0.4 times coarse error plus 0.001 m. These test the expected
  numerical refinement behavior without pretending the hold rules are identical.
- For the linear-point hypothesis at 300 Hz, require horizontal RMS at most
  1 m, height RMS at most 1 m, and maximum three-dimensional error at most 5 m.
  These are software accuracy targets, not measurement-error specifications.
  Preserve left/right-hold errors even when they exceed those accuracy targets.
- Save per-axis and total errors, maximum errors, refinement ratios, input-array
  hashes and every failed result. Regenerate generated arrays from the frozen
  recipe; do not store 72 duplicate synthetic histories or worker trees.

Measure errors in Cartesian metres under the generating candidate's geometry,
then project them onto its known true local north, east and up axes. Do not use
a globe longitude-to-distance scale for a disc case. The truth generator's
attitude is used only as a known answer in these software controls, never as an
observation supplied by a fused navigation system.

Passing qualifies only the declared generated capability and sampling hypotheses.
It does not identify the instrument's actual averaging, phase, filtering or
onboard corrections, establish observational confidence, or revise selection.
Failure blocks the dependent ESA adapter capability claim; do not relax targets.

## Finite allowance and release gate

One worker uses four numerical threads, after the current NASA pilot releases
its allocation. Freeze source/environment hashes, all analytic parameters and
the generated case identities before starting. Use no original recordings,
observed-data fits or protected data.

Each identity permits exactly two native propagations, at most 1,080,000
constructed intervals and at most 1,296,000,000 conservative packet/query visits.
Across 72 identities the ceilings are **144 native calls, 77,760,000 constructed
intervals and 93,312,000,000 packet/query visits**. Also reserve the analytic
sample evaluations before generation: 360,001 coarse samples, 720,001 fine
samples and 1,200 answer samples per identity, totaling **1,081,202 per identity
and 77,846,544 across the study**. These include interval endpoints and scoring
queries; they are not additional instrument observations. Charge before execution.
Use a four-hour cooperative wall ceiling, no retries and no allowance expansion.
Preparation must check the frozen recipe and actual counts against these limits.

This plan is not an active allowance. The final recipe, derivative and loader
checks, exact definitions and environment freeze are required before launch.
Additional selection, receiver-error, lever-arm, initialization and calibration
qualification still precede ESA model fitting. No NASA calibration bounds or
decision thresholds transfer automatically.

[Motion limitation](../ESA_MOTION.md) ·
[Existing rate/body controls](../esa-rate-qualification/INTERPRETATION.md) ·
[ESA selection proposal](../external-imu-data/ELIGIBILITY_PLAN.md) ·
[Implementation sequence](IMPLEMENTATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
