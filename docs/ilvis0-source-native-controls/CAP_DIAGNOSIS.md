# The proof used a larger calibration box than required

All six failed broad controls share this comparison:

| Nonlinear allowance | m/s² |
|---|---:|
| Original unchanged cap | 53.99651568022968 |
| New proof with a symmetric box | 54.00585676186987 |
| Proof with the actual asymmetric box | 53.99651568022966 |

These large values belong to deliberately broad generated stress controls;
they are not measured aircraft accelerations or sensor drift.

The reference point is not centered in its allowed box. The first candidate
replaced the true bias/gain intervals with symmetric intervals around that
point. This enlarged the force range and lowered the minimum gain denominator,
so its proof exceeded the cap. The original calibration domain was sufficient.

The corrected proof uses the actual calibration box, including the reference
point where needed for the Taylor path. It retains the maximum parameter
displacements for the remainder terms. All center and row corrections remain
identical; no cap, physical bound or acceptance tolerance changes.

Six bounded analytic comparisons reproduce the result without native trajectory
evaluation or optimization. [Numeric record](CAP_DIAGNOSIS.json) ·
[Reproduction script](diagnose_caps.py).

This diagnosis explains the failed check; it does not relabel the failed study.
The revised implementation needs its own frozen native qualification.
