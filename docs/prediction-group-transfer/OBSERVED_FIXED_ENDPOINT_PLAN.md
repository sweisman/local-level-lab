# Fixed-endpoint timing check for the recorded-data pilot

## Question

The [24-fit pilot](OBSERVED_METHOD_PILOT_V2_RESULT.md) completed technically
but failed its numerical qualification. Two receiver cuts gave later paths
that differed by 0.752 m and 0.320 m, despite close training costs. Both also
have unusually different fitted receiver/IMU time offsets. At those exact
saved parameter vectors, is the training calculation repeatable, and does
moving only the time offset cross packet-interval boundaries or produce a
non-smooth cost response?

This check diagnoses the existing fits. It does not refit them, change their
stopping labels, inspect another flight, or test an Earth model.

## Preselected comparisons

Use the two sealed fits that produced each maximum later-path difference,
plus the same solver/start identities on that recording's outer cut as
controls. The [saved audit](observed-method-v2-diagnosis.json) fixes these
identities before any new calculation:

| Recording | Inner pair | Outer control pair |
|---|---|---|
| 2010 northern recording | trust-region start 1; SciPy TRF start 1 | trust-region start 1; SciPy TRF start 1 |
| 2015 southern recording | SciPy TRF starts 0 and 1 | SciPy TRF starts 0 and 1 |

There are eight fixed endpoints. Reuse the pilot's sealed training-only IMU
and receiver inputs, model, timing convention, physical bounds and saved fit
vectors. Withhold the later receiver positions throughout this calculation.
Do not select endpoints by a new numerical outcome.

## Calculation and finite allowance

At each endpoint, repeat the complete training prediction/tangent calculation
twice at the same point. Then evaluate time offset at ±0.1 microsecond,
±10 microseconds, ±1 millisecond and ±4 milliseconds, using the existing
`lll.ilvis0_timing_probes` calculation. Record actual cost, the analytic and
finite-difference timing derivatives, packet-boundary crossings and receiver
position changes. A perturbation outside the original parameter bounds or
time support is an explicit diagnostic failure, not silently clipped.

Limit each endpoint to ten complete prediction/tangent calls and its exact
packet-count × training-epoch charge. Across all eight endpoints the cap is
80 calls and 1,468,313,700 packet visits. Use four one-thread workers and a
cooperative one-hour wall limit. Every call must be charged before execution.
Preserve completed and failed tasks. A host interruption may recover only
unfinished tasks under a separately finite, qualified task-level continuation;
no completed endpoint may run again.

## Interpretation

An exact same-point replay would establish repeatability at these eight
points only. A boundary crossing or asymmetric finite difference would
identify a specific timing mechanism worth testing in generated controls.
Neither result by itself qualifies a changed stopping rule, proves the
forecast is adequate, or supports a shape or rotation conclusion. Any
revised method needs separate generated known-answer tests and a newly frozen
recorded-data comparison before use in the broader roadmap.
