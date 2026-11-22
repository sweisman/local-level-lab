# Fast force variation worsens the later forecast scores

Fast force variation explained the [large force-magnitude discrepancy](ESA_FORCE_VARIATION_RESULT.md),
but using it to set forecast uncertainty made the later position scores
worse. This result holds for both archived IMU error descriptions on the
same flight.

| Variance applied to the forecast errors | Later mean squared standardized error | Increase in negative log score versus constant variance |
| --- | ---: | ---: |
| Constant scale | 4.06 | 0 |
| Scaled by fast variation in each interval | 4.27 | 30.69 |
| Scaled by fast variation with a 15-second decay | 4.22 | 9.05 |

Each method used the earlier 120-report forecast to set a common scale.
The later 120-report forecast used those scales as fixed inputs. The
Gaussian log score includes the cost of making the uncertainty wider.
The incremental and point-rate descriptions give the same values to the
precision shown. These changes affect the assigned uncertainty while the
underlying position predictions remain the sealed forecasts.

Across the four later 30-report blocks, mean fast force variation stayed
between 0.096 and 0.102 m/s². The third block contained about 85.5% of the
east-ordered innovation energy, while the fourth contained about 97% of
the east position error energy. A single force-variation multiplier did
little to distinguish these phases. The [angular maneuver check](ESA_MOTION_ERROR_LAW_RESULT.md)
already found a stronger response tied to the turn. That response and the
substantial height drift in straight flight still need separate physical
and uncertainty checks.

The corrected run scored both archives, using 36,000 and 36,001 original
inertial samples for their respective time supports. The first frozen
attempt stopped before any scoring because the new averaging wrapper
passed lists where NumPy arrays were required. The second freeze corrects
that conversion, adds a unit check and preserves the same science and
per-phase work limits. Both attempts belong to one previously scored
development flight.

[Plan and reproduction](ESA_FAST_FORCE_TRANSFER_PLAN.md) ·
[Corrected freeze](esa-fast-force-transfer-v2-freeze.json) ·
[Earlier scales](esa-fast-force-transfer-earlier.json) ·
[Later scores](esa-fast-force-transfer-result.json) ·
[Technical failure](esa-fast-force-transfer-failure.json) ·
[First freeze](esa-fast-force-transfer-freeze.json) ·
[Original source](esa-fast-force-transfer-v1.py.gz) ·
[Original tests](esa-fast-force-transfer-v1-test.py.gz)
