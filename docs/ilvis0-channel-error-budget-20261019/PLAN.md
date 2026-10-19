# Channel-diagnostic approximation and error budget

## Purpose

Measure the software diagnostic's sensitivity to receiver-trajectory truncation,
nonlinear propagation and acceleration averaging before any recorded-data use.
Preserve the completed exact-trajectory controls and the main flight results.
These deterministic controls do not estimate a false-rejection rate or an
observational confidence interval.

## Matrix fixed before execution

- Thirty-six trajectory cases: three reference models, degree 2 or 4, half-windows
  of 4, 8 or 16 seconds, and receiver-noise multipliers 1 or 50. All candidates are
  evaluated in each case. The same analytic trajectory has small sinusoidal
  latitude, longitude and height changes. It is deliberately not polynomial.
- Receiver coordinates are sampled every second. The declared fixture covariance
  has 0.3/0.3/0.7 m north/east/height scales, 60-second exponential correlation
  plus a 10% independent term, and cross-axis correlations. A common spherical
  reporting metric converts these assumptions to coordinate units for every
  candidate. These are known control assumptions, not measured receiver errors.
- Full position/rate/acceleration covariance is retained. Symmetric derivatives
  at 0.01 and 0.02 standard-normal steps provide a local delta approximation.
  A separate 18-point spherical-radial cubature probes nonlinear response. The
  cubature is an approximation check, not exact Gaussian coverage.
- Six one-second rotation controls at 0, 0.1, 1, 5, 20 and 90 degrees compare
  mean packet magnitudes with the magnitude of summed increments at 200 Hz.
  Increments are exact integrals of a rotating constant-magnitude force.
- Four isotropic acceleration-noise controls use standard deviations 0.001,
  0.01, 0.1 and 0.5 m/s². Independent order-5 and order-9 Gaussian quadrature
  measure magnitude bias and compare with the small-noise expansion.

## Finite allowance

| Work | Maximum |
|---|---:|
| Diagnostic identities | 46 |
| Candidate force evaluations | 6,048 |
| Constructed rotation increments | 1,200 |
| Scalar quadrature evaluations | 3,416 |
| Observed fits / native integrations / original reads | 0 / 0 / 0 |
| Threads | Four total, one worker |
| Runtime | 120 seconds |
| Retries | Zero |

Seal sources, environment, tasks, constants and limits before launch. Reserve
each identity's full allowance before evaluation. Preserve failed identities;
completed work cannot restart or transfer its unused allowance.

## Checks and interpretation

Software correctness requires finite results, independent-reference force
agreement within 10⁻⁹ m/s², exact formula-call counts, and rotation-integral
agreement within 10⁻¹¹ m/s². Quadrature orders must agree on magnitude bias to
within 1% or 10⁻¹¹ m/s², whichever is larger; the small-noise expansion is a
separate reported comparison.

For each candidate, flag a local approximation when derivative disagreement
exceeds 1%, cubature and linear standard deviations differ by more than 5%, or
the nonlinear mean shift exceeds 0.1 linear standard deviation. Also report
trajectory-truncation bias relative to linear standard deviation; a ratio above
0.25 fails the control's declared truncation screen. These screens are numerical
development rules, not calibrated scientific acceptance thresholds. Stress cases
are allowed to fail these screens; no window or model is selected by the outcome.

Show all cases and all candidates. Do not infer real instrument noise from these
assumed inputs, qualify a recorded-data likelihood, or change the 53-stretch result.
