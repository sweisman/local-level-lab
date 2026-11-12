# What the same-noise check establishes

The corrected study completed all six generated IMU streams. Its saved-data
audit verifies the inputs, six native calls, forecasts and scores. None passes
the existing physical accuracy screen.

With the generating calibration and starting state supplied, later horizontal
RMS error is about **439 m** for the rotating-globe streams, **442 m** for the
still-globe streams and **508 m** for the flat-disc streams. The earlier fitted
forecasts on those same streams are about **84–89 m**. These are comparisons
with each stream's *own* generating truth, not votes between Earth models.

The known-calibration forecast being worse than the fitted forecast means the
earlier error cannot simply be assigned to estimating calibration. The oracle
knows the fixed calibration, but **does not know the realized changing sensor
bias**. Earlier receiver observations can help a fitted forecast adapt to that
bias. This is a possible explanation, not yet a measured attribution.

The separate linear noise benchmark's 33.77 m twenty-minute horizontal scale
is **conditioned on the earlier 800 receiver observations**. This oracle makes
no such receiver update after its true starting state. A [sealed, audited
comparison](conditioning-comparison/README.md) now gives **717.66 m before**
and **33.77 m after** that conditioning, using the same covariance operator.
The 439–508 m realized misses are therefore closer to the unconditioned
expected scale; one realization does not establish prediction coverage.

A [full twenty-minute noise-free control](long-noiseless-control/README.md)
now follows the generating trajectory: later horizontal and height RMS are
0.048 m and 0.060 m, respectively. This rules out large clean propagation
error in that preselected rotating-globe case. A [ten-variant replay](component-decomposition/README.md)
now isolates the same realized errors: changing gyro bias alone gives 376 m
later horizontal RMS, random gyro increments 230 m, accelerometer changing
bias 20 m and random accelerometer increments 6 m. Together they give 439 m;
the clean stream gives 0.048 m. Their error vectors nearly superpose in this
case, but the scalar RMS values do not add. These are **synthetic stress
settings**, not measured archive-device noise. Preserve the original failed
fits and both completed oracle studies.

No actual aircraft data, independent noise seed or protected ESA confirmation
recording was used. This diagnostic does not calibrate aircraft uncertainty or
establish an Earth-model detection.

[Six-case result](README.md) · [Component replay](component-decomposition/README.md) · [Original failed release and correction](RECOVERY.md) ·
[Noise benchmark](../noisy-prediction-benchmark/README.md).
