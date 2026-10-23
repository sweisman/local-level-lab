# Add a declared accumulated-IMU-noise component

This saved-data sensitivity check reuses the six fixed trajectory cases and
the completed receiver-only comparisons. It does not fit a calibration, read
an original recording or perform a new trajectory integration.

Use both predeclared receiver correlation times, 10 and 300 seconds, with the
same covariance components, common coordinate conversion and full-record drift
anchor. Use only the 289 earlier epochs at 2–290 seconds and their original
five-epoch subset. The later prediction and all future observations are excluded.

## Explicit linear-noise examples

Use the previously qualified constant-coupling joint-error operator. Start its
random error state at zero seconds; keep constant calibration uncertainty external.
Add independent isotropic white-error power densities:

| Quantity | Settings |
|---|---|
| Accelerometer PSD | 1e-8 m²/s³ on each axis |
| Gyroscope PSD | 1e-12 or 1e-10 rad²/s on each axis |
| Constant coupling | `[[0,9.81,0],[-9.81,0,0],[0,0,0]]` |

These are **software sensitivity settings, not manufacturer specifications or
measurements of the archive's instruments**. They test the effect of accumulated
noise under a stated linear law. They do not establish that the law describes
the actual aircraft or that its coupling is constant.

The fixed trajectories remain identical. Reuse each sealed receiver-only distance
as its baseline; do not rerun that completed study. Compute the same three pairwise
distances under the joint covariance and preserve raw per-axis RMS differences.
Adding an independent positive covariance cannot increase the separation of the
same deterministic means in noise-scaled units. Check that property and preserve
any violation as a failure. This is not a p-value or a statistical decision.

## Finite allowance and verification

Three models × two processing cases × two receiver correlation times × two
gyro PSDs gives **24 starts**, one worker and one numerical thread, with a
120-second cooperative total allowance. Native calls, packet visits, bound
evaluations and optimizer starts are zero. No retries or budget expansion.

Freeze exact saved means, baseline results, source/input/environment hashes and
noise settings with the common study runner. Before launch, verify the shared
distance interface, exact training-time binding and a strict decrease under
positive added noise. Reuse the joint operator's completed mathematical controls.

Publish every outcome and baseline comparison from sealed results. The study
does not enclose the full nonlinear calibration domain, estimate actual noise,
establish whole-period uncertainty or authorize observed prediction fits.
V01 remains unqualified; the 53-stretch baseline and protected ESA data are unchanged.
