# The existing calibration bounds leave steady drift hard to measure

The bounded calculation reproduced more than 99% of every steady
acceleration pattern tested on the saved ESA training interval. Fixing
the accelerometer biases and gravity adjustment at their saved values
still left the fit able to reproduce more than 98.6% of every pattern.
The result holds across both acceleration sizes, both signs and all
three Earth models.

| Direction | Pattern energy left with the existing bounds | Energy left if accelerometer biases and gravity are fixed |
| --- | ---: | ---: |
| North | 0.26–0.56% | 0.35–1.27% |
| East | 0.029–0.16% | 0.041–0.33% |
| Up | 0.45–0.96% | 1.10–1.35% |

These are fractions of the squared test signal after weighting by the
original covariance. Each test asks how closely the local flight-path
adjustment can match a hypothetical displacement from constant acceleration.
The result describes ambiguity in one training design. The test patterns
were constructed at 0.0001 and 0.001 m/s², so the check does not measure
what steady acceleration error the aircraft actually had.

All 72 solutions passed the numerical bound check. The largest gap
between a feasible result and its lower bound was about 3.2 × 10⁻⁸ of
the starting pattern energy. The original model box and the local step
limit of 0.1 in normalized coordinates were applied around each saved
fit. Holding the four parameters fixed is a sensitivity check. It does
not establish their true values or the accuracy of the local linear
approximation for any particular physical change.

**What this changes.** Tighter bounds on accelerometer bias and gravity
alone do little to separate drift from flight calibration in this
interval. A useful next test needs a different source of calibration
information. Compare ground and maneuvering portions of the opened
recording using independently screened motion, and check whether the
same instrument parameters can explain all portions. Fit and assess
aircraft error scales only if the combined design supplies that leverage.

[Plan and reproduction](ESA_BOUNDED_DRIFT_PLAN.md) ·
[Frozen inputs](esa-bounded-drift-freeze.json) ·
[Detailed results](esa-bounded-drift-result.json)
