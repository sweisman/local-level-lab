# Why the faster derivative calculation did not qualify

The completed six-case benchmark preserved every predicted position and residual
exactly. It changed only the precision used for parameter derivatives. Its
saved matrices contain **509 derivative entries outside the fixed tolerance**,
across ten parameter columns. This explains why the faster prototype cannot
replace the qualified calculation.

| Parameter sensitivity | Entries outside tolerance |
|---|---:|
| Initial heading (`attitude_z`) | 388 |
| Gyro Z offset | 39 |
| Accelerometer Z offset | 23 |
| Accelerometer X/Y/Z gains | 44 |
| Other initial-motion and gyro terms | 15 |

The largest absolute derivative difference after the study's 0.05 m coordinate
scaling is about 5.24×10⁻⁵. Some derivative magnitudes approach 30 million in
the same units, so the large absolute differences alone are misleading. The
fixed comparison allows both an absolute and a relative error of 2×10⁻¹⁰;
violations occur where a sensitivity becomes small after contributions cancel.
The median violating entry exceeds its own allowed error by about 1.98 times;
the largest by about 429 times. Initial heading accounts for 388/509 violations.

The archived reference and prototype matrices can reproduce these counts:
divide each Jacobian row by its saved `standard_deviation`, then count entries
where `abs(reference - candidate) > 2e-10 + 2e-10*abs(candidate)`.
Use the hash-checked `ClosedStudy` interface for
`data/mixed-tangent-long-controls-20261024`; each identity has a
`comparison.npz` artifact. The source transformation and benchmark manifest
show that the derivative storage/arithmetic changed while the value path did
not. This isolates the failure to reduced derivative precision, without
claiming that a particular arithmetic operation caused each mismatch.

A revised speed method must preserve the vulnerable sensitivities or improve
the existing wide arithmetic, and pass a new source-bound derivative and
training/forecast qualification. No tolerance, fit result or scientific
decision changes from this diagnosis.

[Frozen benchmark result](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
