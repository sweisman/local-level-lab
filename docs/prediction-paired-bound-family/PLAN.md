# Paired error-law bounds: next generated-aircraft check

**Status: 18 focused checks pass, including four native law/calibration controls
and one end-to-end scoring control; study not frozen or launched.**

The earlier paired-law pilot fitted two assumed IMU error laws to the same
generated recording, but did not calculate bound-aware intervals for either
law. The new `lll.prediction_paired_bound_native` bridge does that without
choosing a law by training score. It saves both physical-position and future
receiver intervals, then their unions, before later truth is opened. Native
two-fit controls pass for both generating laws and calibration cases. This is an integration
test, not an aircraft coverage measurement.

## Frozen study to prepare

Test all three generating Earth candidates, both upstream processing cases,
both generating IMU error laws, and interior and Z-gyro-boundary calibration:
**24 generated recordings and 48 matched candidate-law fits**. Use the same
two-minute, 300 Hz, 119-epoch protocol and existing physical bounds as the
paired-law pilot. Use seed 97, the header-elapsed clock, one start and at most
200 evaluations per fit. The conservative per-recording ceiling is 479,632
native calls and 3,012,102,024 packet visits. Set four single-thread workers
and a five-hour cooperative wall limit. Keep
the recorded IMU and earlier receiver inputs identical between a recording's
two fits. Score physical truth and a future receiver report separately.

Before launch, freeze the exact recipe and seed, finite evaluations and native
call ceilings, source/environment hashes, test qualification, four-worker
allocation, wall limit and interruption-recovery proof. Do not launch while
another study reserves more than zero of those four numerical threads. Use
independent generated data; do not read observed or protected recordings.

Report technical completion, numerical stopping, active bounds, physical
prediction accuracy, interval containment by recording and axis, and width.
All 24 recordings must save both law bounds and their unions before later
truth to pass the technical gate. A failed fit or missing bound remains a
recorded abstention. The 24 recordings are too few to certify 95% coverage;
that requires a separately sized, independently seeded study after the
technical gate. Neither this study nor the software control calibrates an
observed-aircraft uncertainty threshold or an Earth-model decision.
