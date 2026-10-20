# Shared error-scale calculation: software qualification passed

All **eight generated families passed**, covering 8,192 scale assessments in
4.19 seconds. Every family's exact one-sided 99% coverage lower limit exceeds
the frozen 0.97 software threshold. The smallest is 0.97912. This is a finite
software qualification around nominal 0.99 model coverage, not measured aircraft
coverage. All 44 publication artifacts pass their SHA-256 checks.

The reference projection is fixed before seeing its training errors, and the
error model is shared across physical candidates. A candidate cannot enlarge
its own measurement uncertainty to explain its poor fit. No withheld positions,
archive fits or protected observations enter these controls.

Unlike the earlier bounded-mean construction, this separate method does not
need a small reference-trajectory remainder. Under the declared Gaussian law,
an incorrect deterministic reference mean can inflate the upper scale bound
without making it anti-conservative. The deliberately poor-mean control gives
a median upper bound about 873 times the actual scale: safe containment can
be uninformative. Central controls give median ratios around 1.20.

[Results](README.md) · [Derivation and assumptions](MATHEMATICS.md) ·
[Frozen limits](PLAN.md).

## Remaining work

The covariance shape and Gaussian law are supplied assumptions. Their adequacy
for receiver data, effects of eligibility selection, and an appropriate numerical
allowance remain separate observational requirements. A reference learned from
the same errors, an unknown distribution, missing numerical allowance or zero
residual dimension supplies no scale bound.

This result also does not narrow the [recording-scale nonlinear bounds](../ilvis0-recording-scale-bounds/INTERPRETATION.md).
Those remain too wide for useful prediction intervals. Their finite study ended
with three complete histories, one partial and two unstarted; it must not restart.
New aircraft prediction fits remain blocked while that method gate is open.
The independent [gyro-prediction companion](../GYRO_PREDICTION.md) can proceed as
a descriptive analysis with explicit orientation assumptions and no new fits.

[Roadmap](../ANALYSIS_ROADMAP.md).
