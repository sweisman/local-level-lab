# Antenna and calibration calculation checks

## Question

Does the existing continuous forecast apply known antenna offsets, sensor
calibration and starting-state corrections correctly on maneuvering trajectories?
This is the next software check within E01, not an ESA model comparison.

The preceding [geographic controls](../esa-geographic-rate-controls/README.md)
used exact starting conditions and zero antenna offset. This extension adds
known synthetic errors. It does **not** test whether a flight can determine those
errors uniquely or whether the real instrument satisfies particular bounds.

## Frozen comparison

- Twenty-four generated identities: three candidates, latitudes −55° and +55°,
  common field-removal fractions 0 and 0.35, and two opposite calibration signs.
- Each identity uses the earlier independent fast-maneuver trajectory for
  1,200 seconds at 300 Hz, with the explicit linear-point sampling hypothesis.
  Query times run from 0.5 through 1,199.5 seconds in one-second steps.
- Generated sensor channels have constant per-axis bias and gain errors.
  Starting position, velocity and attitude are offset; the antenna is displaced
  in sensor coordinates. Query latency and the reference gravity are offset too.
  Exact values live in the versioned recipe and independent generator.
- Antenna truth is the Cartesian IMU position plus the differentiated geometry's
  sensor axes times the antenna vector. No navigation output supplies truth.
- One forecast uses the exact known correction vector with all 27 nuisance
  columns retained. Three value-only calls check its agreement with the existing
  value kernel, one mixed-direction derivative, and zero correction as a diagnostic.
  The correction vector is supplied, not estimated. No solver is run.
- Corrected horizontal and height RMS must each be at most 1 m; maximum spatial
  error at most 5 m. Value/tangent coordinate disagreement, scaled by
  `[6378137, 6378137, 1]`, must be at most 0.0001 m. The forward difference uses
  a normalized step of 0.000001; its largest discrepancy must be at most
  `0.5 + 0.002 * largest absolute directional derivative` in scaled metres per
  normalized unit. All quantities and diagnostic failures are preserved.
- A zero sensor/state-correction error is reported, keeping the same field-removal
  fraction. It is not an acceptance requirement.

## Finite allowance and evidence

One worker, four numerical threads, a cooperative two-hour ceiling, no retries.
Each identity allows four native calls and 1,728,000,000 packet/query visits:
96 calls and 41,472,000,000 visits in total. Each constructs 360,000 intervals
from 360,001 samples, plus 1,200 independent answer samples. Construction and
native work are charged before execution; interrupted work remains charged.

Before launch, bind the complete source closure, compiler/runtime environment,
recipe and passing focused tests. Use `lll.studies` for exclusive execution,
atomic results, journals and archived publication. Source preparation and cheap
local tests precede the study; no trial consumes its allowance before freezing.

## Implementation and checks

1. Add independent observation construction in
   `analysis/lll/airquantumgrav_observation_truth.py`. Test known signed sensor
   transformations, Cartesian antenna displacement, inverse starting-state
   corrections and failure on invalid inputs. Keep navigation imports absent.
2. Add a small definition/evaluator in
   `analysis/lll/airquantumgrav_observation_controls.py`, reusing the existing
   rate constructor, native forecast, value kernel and study framework. Test
   real short trajectories, preserved nuisance columns, exact charges and
   rejection before execution when source qualification is absent.
   Check actual runner-assigned fields and persisted construction journals.
   Mixed native tasks require each call to declare value or derivative work;
   existing fixed-kind tasks cannot be reclassified or gain extra allowance.
3. Freeze and execute the declared 24 identities only after those tests pass.
   Audit saved errors, derivative comparisons and both charge streams without
   propagating again. Publish every outcome and update the roadmap.

## Remaining boundaries

A pass establishes correct application of declared corrections, not their
recoverability from training observations, a measured device specification,
actual sample averaging, or an error distribution. Training-only initialization
and calibration estimation, receiver uncertainty and a new selection freeze
remain requirements before observed ESA fits. The version-1 zero-eligible
inventory, NASA results and seven reserved ESA confirmation groups are unchanged.

[Next analyses](../NEXT_STEPS.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
