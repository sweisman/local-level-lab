# Why the short controls fail their stopping check

The six saved calibration tangents retain all 26 or 27 parameters, but each has
only 12 numerically distinguishable directions. Constant-speed tracks cannot
separately determine all calibration terms.

| Model | Removal profiled | Existing correction length | Minimum-norm length | Minimum-norm step feasible |
|---|---|---:|---:|---|
| Globe + field | No | 2.095 | 0.732 | No |
| Globe + field | Yes | 0.073 | 0.073 | Yes |
| Globe, zero field | No | 0.466 | 0.097 | Yes |
| Globe, zero field | Yes | 0.147 | 0.147 | Yes |
| Stationary disc | No | 0.00123 | 0.00119 | Yes |
| Stationary disc | Yes | 1.765 | 0.197 | Yes |

Lengths use normalized calibration coordinates. The audit used the nominal-clock
zero start under each model and processing case. It completed 12 linear solves
on saved arrays, with no motion integration, new fit or aircraft observation.

A minimum-norm correction reduces some large steps, but not all, and one leaves
the allowed bounds. It is therefore not a demonstrated general repair. These
linear calculations do not establish how a changed solver behaves on the
nonlinear trajectories. Earlier failed labels remain unchanged.

The next method check should also distinguish an already near-zero objective
from a nonzero optimum. A squared-residual objective cannot be less than zero;
an independently repeated near-zero value can provide a useful numerical
stopping criterion without identifying every calibration parameter. Such a rule
needs its own fixed tolerance and controls, preserves the ordinary stopping
checks elsewhere, and cannot establish scientific significance.

[Fixed audit question](../ilvis0-training-forecast-controls/MINIMUM_NORM_PLAN.md) ·
[Complete control results](../ilvis0-training-forecast-controls/README.md) ·
[Prediction method](../PREDICTION_VALIDATION.md)
