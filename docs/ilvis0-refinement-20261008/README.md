# Refining the globe-versus-disc comparison

**The pilot is complete: two recordings favor globe and then rotation across all four
cases; none has a complete flat-favoring result.** Four recordings lack complete comparisons.
See the [pilot findings](PROVISIONAL.md) and the subsequent
[53-stretch findings](../ilvis0-highspeed-segments-20261008/FINDINGS.md).
The sections below preserve the method and development sequence.

The initial calculation needed refinement before its fit differences could be used
scientifically. The main issues are unfinished optimization and calibration freedom
large enough to absorb the predicted signal. Sensor quality alone does not establish
how much of that freedom is needed in these particular logs.

At 140–256 m/s, the spherical horizontal curvature scale is about 4.5–8.3 degrees
per hour. The historical stress test permits a constant offset of ±20 degrees/hour per axis.
The corresponding centripetal acceleration scale is approximately 0.003–0.010 m/s²;
each acceleration axis permits ±0.25 m/s². These comparisons use an explicit
6,371 km spherical radius. They are predicted scales, not measured Earth signals
or the complete globe/disc difference.

On a steady interval, a nearly constant model contrast can be traded against an
unknown constant IMU offset. A deterministic algebraic check shows that an
8-degree/hour constant gyro contrast disappears completely inside the current
20-degree/hour offset envelope; a 1-degree/hour envelope leaves 7 degrees/hour.
This does not show that the actual flight contrast is constant. It explains why
more observations of the same geometry cannot by themselves establish calibration.
Changing speed/direction, independent calibration and controls can break that trade.

## What the refinement should do

1. **Resolve numerical optimization first.** Use accurate derivatives, parameter
   scaling and staged initialization. Finish with all declared nuisance parameters
   free within the same stated bounds. Diagnose actual gradients and derivative
   stability; do not accept a tiny optimizer step as evidence of a minimum. Validate
   the new solver before spending another observed-data fitting allowance.
2. **Ask globe versus disc explicitly.** Treat the rotating and stationary globe
   as a two-member family, preserving the separate rotation question. Compare the
   family's best profile with the disc only when all contributing candidate
   profiles are resolved. Local convergence still does not establish global minima.
3. **Measure calibration sensitivity.** Test assumed constant gyro-offset envelopes of
   ±0.1 and ±1 degrees/hour while holding other assumptions fixed. Independently
   test acceleration/gain sensitivity afterward. Smaller envelopes are hypotheses,
   not established instrument performance or permission to force a preferred result.
   Report which calibration accuracy would be needed for useful separation.
4. **Separate processing hypotheses.** Repeat matched candidates with Earth-rate
   subtraction fixed at zero and with the common subtraction fraction free. Keep
   the same observations, initialization rules and covariance for every candidate.
5. **Use changing geometry and shared calibration carefully.** Prefer intervals
   spanning different speeds/directions according to GPS geometry, before gyro
   comparisons. Pool calibration only within supported sensor/installation epochs;
   hardware identity alone does not prove unchanged mounting or independent flights.

The existing six date/configuration representatives remain the initial development
set; no replacement is chosen because of a gyro outcome. New empirical runs need a
separate finite source/environment/attempt freeze. The preceding corpus study and its
original 764-start aggregate limit remain preserved; that completed study must not be resumed.

## What is implemented now

The separate `ilvis0_refinement` module initially provided the constant-bias control, physical
scale comparison and a direct globe-family/disc profile summary. The latter refuses
to compare unresolved candidate optimizations and always abstains from a calibrated
scientific decision. Five focused tests pass, including false-convergence refusal.

The attached refinement snapshot records the six already completed corpus results
and their hashes. It starts no new model predictions, fits or campaigns, changes
no active source freeze and deletes no data. Further optimization and calibration
sweeps were proposed development work at that snapshot's date, not completed results.

## Numerical method and run scope

`analysis/lll/ilvis0_shape.py` and `ilvis0_tangent.cpp` now implement forward automatic
derivatives through every measured IMU packet. Derivatives cover the effective initial
orientation, calibration offsets/gains, antenna lever arm, gravity, timing and common
Earth-rate removal. Column scaling and a short initial attitude/velocity/position/gain
stage precede the final profile with all declared nuisance parameters free. Every native
sweep counts; a fresh final derivative must satisfy the stationarity check. Derivatives
at exact GPS packet boundaries use the left interval and are flagged. Local convergence
still does not prove global minima.

The professional hardware deserves professional-scale sensitivity assumptions. A
constant fitted offset is not a measurement of time-varying drift, and observed aircraft
motion is not sensor noise. Applanix's POS510 **system** noise/drift figures do not establish
the absolute bias in these logs. Northrop's [LN200 family sheet](https://cdn.northropgrumman.com/-/media/Project/Northrop-Grumman/ngc/what-we-do/mission-solutions/positioning-navigation-timing/LN-200-FOG-Family-datasheet.pdf)
lists gyro bias repeatability of 1–3 degrees/hour for the core variant, 0.5 for enhanced,
and 0.15 for high performance, all one-sigma figures. The exact installed variant is
unconfirmed; none of those figures is a hard calibration bound for this archive.
The new ±0.1 case is an optimistic residual-calibration hypothesis and ±1 a wider
sensitivity. They do not cover every family variant or replace per-unit calibration.
Other gain/acceleration bounds stay unchanged to isolate this sensitivity; time-varying
bias, filtering and transport subtraction remain outside this finite model.

The exact original six recordings and windows are used, with no replacements after
gyro outcomes. Each has four matched cases: two constant-offset bounds, crossed with
Earth-rate removal fixed at zero or profiled over [0,1]. Both globe members are optimized
internally to compare the globe family with the disc without presuming rotation.
Rotation diagnostics are withheld unless every case has converged and its signed
shape contrast favors the globe. Mixed, tied or unfinished shape results abstain.
The result reports which model fits the measurements better. A validated statistical
significance level has not been assigned; the separate scientific significance gate abstains.

The worker is `analysis/tests/ilvis0_shape_worker.py`; output:
`data/ilvis0-shape-refinement-20261008/`. It verifies completion of the preceding v2 corpus
and runs deterministic tests before fitting. At most two
total numerical threads. Scope: 72 primary starts plus 12 interruption retries, at most
two starts per file/case/model identity, and 200 total native evaluations per start,
including fresh derivatives and diagnostics. Journals are fsynced; results are hashed
and atomic; changed inputs, source or environment refuse resume. Completed work never
resumes. No synthetic campaigns, deletions, scientific promotion or git operations.
The worker produces a compact `RESULTS.md` on completion.

Fourteen new focused tests pass, including all candidate derivative/value comparisons,
known position/velocity recovery, shape-before-rotation withholding, budget enforcement,
interrupted-start accounting, corrupt saved results and actual six-file handoff metadata.
Five prior refinement tests also pass. Numerical outcomes are reported separately on completion;
the worker's saved status and attempt journal provide progress while it runs.

## Why the calculation takes hours

An eight-minute recording contains about 96,000 IMU measurement intervals at 200 Hz.
Every fit repeatedly integrates the complete measured stream to predict the GPS path.
It also calculates how that prediction changes with calibration, orientation, timing and
other uncertain quantities, then adjusts them together. The GPS comparison accounts for
errors that are correlated over time, rather than treating every position as independent.

There are 12 fits per recording: three Earth models under four matched assumption cases,
or 72 fits for the six-recording pilot. Each permits up to 200 complete numerical evaluations,
including final convergence checks and diagnostics. This repeated native-packet processing
and joint optimization make an individual fit substantially more work than plotting or
averaging a gyro channel. Compiled kernels perform the integration and derivatives; the
worker uses at most two numerical threads and continues without interactive model calls.

The completed [all-stretch extension](../ilvis0-highspeed-segments-20261008/README.md) uses
six fits per stretch: three models under two processing cases, with the ±1°/hour offset
allowance. The pilot's tighter ±0.1°/hour cases were deferred for that extension.

## Automatic completion report

`package_results.py --watch` waits without fitting or model calls, then audits the
finished six-file/four-case grid, every hashed per-file and per-fit artifact, source
and input hashes, environment, charged starts and the 200-evaluation ceiling. It
recomputes the shape-before-rotation hierarchy before publishing. Four metadata-only
tests cover a valid completion, over-budget fits, corrupt results and a forged rotation
stage. These controls do not simulate flights or consume observed optimizer starts.

After a successful audit it writes `RESULTS.md`, per-fit and shape/rotation CSV tables,
frozen source copies and an evidence receipt in this documentation directory. Rotation
tables include only cases allowed by the shape stage; withheld cases remain explicit.
It updates project readiness from the latest metadata so the corpus completion is
preserved. Watch mode has a 24-hour waiting limit and leaves workers untouched on error.
If the watcher stops, run `package_results.py` without `--watch` after completion;
do not rerun fits to regenerate a report. The report claims no calibrated detection.
