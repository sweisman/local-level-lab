# Training-only error adapter: software qualification

**All 56 checks pass:** 32 interface checks and 24 native calculation cases.
The fitting software can now use the accumulated IMU and receiver-error model
without constructing a dense covariance matrix for the whole recording.

The native cases cover three physical models, both processing assumptions,
both gravity rules and both input formats: recorded increments and converted
rate samples. Every active calibration derivative is retained. Residuals,
derivatives, covariance normalization and earlier-only error corrections agree
with independent dense calculations. Before-cast residuals remain tied to the
exact fitted point, model and error configuration.

The qualification takes about 46 seconds and attempts 8,568 native calls.
An additional 29 legacy forecast/protocol checks pass. No optimizer starts,
original aircraft measurements or protected confirmation recordings are used.

This establishes the adapter's arithmetic, not prediction accuracy or calibrated
confidence. All 24 deliberately displaced calibration points require a linear
correction outside the allowed parameter box; the diagnostic correctly withholds
an unrestricted-calibration covariance. Nonlinear fits and behavior at bounds
remain to test. The earlier noisy study's accuracy failures are unchanged.

The [verified receipt](evidence-receipt.json) preserves 100 source snapshots,
test results, generated native source/binaries and the work journal. All 110
artifact hashes are checked. The [initial fixture failure](../training-adapter-initial/README.md)
remains preserved separately.

[Frozen plan](../TRAINING_PLAN.md) · [Error propagation](../README.md) ·
[Next analyses](../../NEXT_STEPS.md).
