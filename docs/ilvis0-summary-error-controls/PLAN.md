# Fixed training-summary error certificates

This finite software comparison checks one error-budget family under four
previously declared example laws: receiver correlation times of 10 or 300 seconds,
and gyro power densities of 1e-12 or 1e-10 rad²/s. These are not device estimates.
Acceleration power density is 1e-8 m²/s³; force coupling, receiver scales and the
fixed noise origin are preserved from the joint-noise sensitivity calculation.

Use all 289 earlier epochs from 2 through 290 seconds and 147 later epochs from
292 through 438 seconds. Twelve summary rows use four time-polynomial weights
on each axis, with unit-length weights and exactly zero later-epoch weights.
They depend on timestamps alone. No observations or fitted residuals are inputs.

For each law, certify the twelve summary variances and include all 441 later
coordinate errors in one simultaneous Gaussian error budget of 0.05. The scale
is explicitly supplied as one, not estimated. Cover a common ±1-second clock
interval, retaining the full covariance identity and a separate projection identity.
Compare certified summary upper variances with the independent matrix-free
operator at both clock endpoints. Preserve signed cross-axis/time contributions.

## Fixed allowance

- Four task identities, one worker and one numerical thread.
- At most 600 seconds for the study; no retries or allowance expansion.
- Zero original-file reads, native integrations, optimizer starts or aircraft fits.
- Use the shared study runner, source/input/environment freeze and sealed outputs.

Passing checks establish error-bound arithmetic only for the supplied law.
Nonlinear calibration, observation-law adequacy and actual coverage remain open.
Neither the original 20-metre target nor the physical calibration bounds change.
The 53-stretch findings and protected ESA confirmation data are unchanged.

[Roadmap](../ANALYSIS_ROADMAP.md) ·
[Declared summary method](../ilvis0-joint-projection-controls/NEXT_PLAN.md)
