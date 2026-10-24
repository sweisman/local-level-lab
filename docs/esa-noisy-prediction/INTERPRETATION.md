# The noise test converged, but missed its accuracy target

**All 24 generated fits pass the numerical checks. None passes the physical
prediction-accuracy screen.** Later horizontal RMS error is 83.6–88.6 m against
the unchanged 10 m limit. Height RMS is 5.5–11.2 m, within its 30 m limit.

Each candidate fits data generated from that same candidate. These are checks
of prediction robustness with known truth, not votes between Earth models.
No recorded flight measurements were used.

| Generating candidate | Numerical passes | Accuracy passes | Later horizontal RMS | Later height RMS |
|---|---:|---:|---:|---:|
| Globe with specified field | 8/8 | 0/8 | 84.8–86.4 m | 5.9–11.2 m |
| Globe with zero field | 8/8 | 0/8 | 84.8–88.6 m | 5.7–11.2 m |
| Stationary disc | 8/8 | 0/8 | 83.6–88.5 m | 5.5–11.1 m |

The cases include both processing assumptions, both receiver-error cases and
two starts. Sensor noise is shared across matched starts and receiver cases;
the 24 outputs are not independent flights or independent noise trials.

The calculation adds declared white gyro/accelerometer noise and slowly
changing bias before initialization and fitting. It retains the existing
receiver-only fitting weights. Calibration uses 800 earlier positions; the
continuous forecast is saved before opening the 400 later truth positions.
The noise amplitudes are research stress settings, not measured instrument
specifications.

This result separates numerical convergence from predictive adequacy. More
optimizer iterations are not the immediate remedy: every fit converged, yet
the prediction target was missed. The [analytic error budget](ERROR_BUDGET.md)
shows how gyro error alone can accumulate into tens of metres over this
horizon. It explains a relevant error scale, without identifying the full
cause of these particular forecast errors.

The next method must propagate errors through the [moving-platform
equations](../native-noise-linearization/PLAN.md), preserve temporal correlation
and account for uncertainty from fitted calibration parameters. The
[46-check covariance component](../integrated-noise-covariance/README.md)
provides checked building blocks; its constant-level examples do not qualify
the aircraft error law. The current accuracy limits and all failures remain
preserved. Broader observed fitting stays gated.

The study used 682 native calls and 136,626,619,200 conservative packet/query
work units in 5.26 hours. A saved-data audit verified all 24 outcomes and
charges, then checked all 477 publication artifact hashes. No refitting or
regeneration was needed for publication.

The original 53-stretch findings and completed observed prediction pilots are
unchanged. This test does not calibrate their statistical confidence or open
the seven reserved ESA confirmation groups.

[Frozen result table](README.md) · [Frozen plan](PLAN.md) ·
[Earlier observed-error diagnostic](../esa-error-structure/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
