# Saved timing-boundary review

## Question

Do the two failed fits in the fresh calibration place receiver queries close to
internal IMU integration boundaries? Proximity would guide a later diagnostic;
it would not establish the cause of the failure or qualify either fit.

## Fixed scope

Read only the two saved starts for seed 281474977010693, rate-sample errors,
specified-field globe, with field removal allowed. Use the closed calibration
manifest, summary, artifact hashes and unchanged failure labels.

The shared `lll.prediction_phase_review.review_clock` routine reconstructs only
the declared uniform clock. It must reproduce the saved little-endian float64
hashes of every interval duration and query time before reporting distances.
It generates no inertial observations, receiver positions, truth or noise.

One saved-data review, at most two fitted records, one thread and a ten-minute
cooperative ceiling. No optimizer starts, native calls, noise draws, retries,
threshold changes or use of protected aircraft data. Known-answer tests check
boundary hits, both signs, invalid clocks, hash mismatches and retained failures.

## Deliverables and next gate

Preserve a source-bound report and per-query CSV. Report the numerical stopping
failure separately from timing proximity. Any native derivative probe, revised
solver or further calibration needs its own reviewed finite plan.

[Calibration outcome](../prediction-calibration-compensated/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
