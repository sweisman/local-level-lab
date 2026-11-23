# Long-recording receiver calculation: software result

The legacy receiver-only projection builds a dense covariance matrix. A single
64,080-report recording would need a 192,240-by-192,240 matrix. The main
motion-fitting class already accepts structured errors; this receiver-law
adapter uses its shared state-space operator
to apply the same declared correlated error law one report at a time. It
whitens residuals and all 26
calibration directions with the same filter; it does not change the recorded
measurements or estimate the error law.

Small full-position, horizontal-only and height-only checks match the dense
reference for residuals, calibration directions, objective and determinant.
They include irregular times, two correlated components, cross-axis receiver
covariance and coordinate transforms. A finite [64,080-report benchmark](structured-receiver-benchmark-64080.json)
used one numerical thread and completed construction plus whitening in
**23.49 seconds**, with **353 MiB peak process memory**. The report records
input and output SHA-256 hashes, adapter and shared-core source hashes, the
benchmark source hash, seed, numerical environment and measured runtime.
The benchmark source SHA-256 is
`f22b600b2b86ed6ebbc07e7c49881ad2ae8cefb0b9914b0e863077e8e4413d1b`.
An independent state-by-state generator with irregular times produced 1,200
correlated histories; their whitened outputs passed the declared mean,
variance and cross-correlation checks. A finite-difference check also agrees
with the objective gradient. A new algebraic adapter translates the earlier
WGS84 receiver law to this structured calculation. Six full, horizontal and
height-only comparisons pass under both zero and nonzero correlation time,
including varying cross-axis formal covariance. All 14 focused software
tests now pass. The benchmark above binds the earlier core adapter; the new
translation function does not alter its whitening loop.

A [saved observed-prefix check](structured-receiver-observed-prefix.json)
then used 120 actual training receiver epochs and the previously saved
predicted positions from one development case. Under the same declared
`h1_v3_tau60` law, the largest dense-versus-structured whitened residual
difference is 1.21×10⁻¹⁵; the largest difference across 26 fixed surrogate
design columns is 1.38×10⁻¹⁴. The objective differs by less than 2×10⁻¹⁶.
No later receiver positions, new native calls or model fits were used. The
design columns are an algebraic software probe, **not** the physical
calibration Jacobian. A matched observed fit remains open.

This establishes feasible memory and runtime for the *assumed covariance
calculation*. It does not establish that the assumed error law describes
aircraft receiver errors, or that a long fitted flight predicts accurately.
A [separately frozen native check](STRUCTURED_RECEIVER_NATIVE_RESULT.md)
now applies both calculations to the same 120-epoch receiver residual and
all 26 **physical** calibration derivatives. It passes at one fixed
parameter point with one charged native call. The subsequent
[matched fit](STRUCTURED_RECEIVER_FIT_RESULT.md) completed: both paths
passed numerical stopping after 61 evaluations and their fitted
trajectories agree at the declared software tolerance. The aircraft
error law and long-recording prediction remain unqualified.

Reproduce the finite benchmark with:

`PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.structured_receiver_benchmark --epochs 64080 --output /tmp/structured-receiver-recheck.json`

The benchmark moved into the shared library. The historical runner named by
the saved benchmark hash is in commit `c41d29132`, at
`analysis/tests/benchmark_structured_receiver.py`.

The output path must be new. Wall time and peak memory vary by machine;
input and output hashes are the deterministic checks in the recorded
Python/NumPy/SciPy environment.
