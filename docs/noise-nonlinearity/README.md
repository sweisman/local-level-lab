# Check the noise approximation against nonlinear motion

**2/4 settings pass the fixed finite check.**

| Input format | Record length | Matched controls passed | Largest non-reversing error | Result |
|---|---:|---:|---:|---|
| Increments | 2 min | 16/16 | 0.000228481 m | Pass |
| Rate points | 2 min | 16/16 | 0.000543138 m | Pass |
| Increments | 20 min | 13/16 | 0.0909278 m | Failed |
| Rate points | 20 min | 15/16 | 0.0506754 m | Failed |

Each control compares positive, negative and half-sized generated errors.
The non-reversing part and change at half amplitude are checked against the larger
of 1 mm and 1% of the predicted coordinate standard deviation.
Seeds are shared across settings: these are not independent aircraft replications.

Known calibration, starting state and nominal geometry are supplied. Passing supports
this finite noise approximation; it does not establish uncertainty after fitting
unknown calibration, a global nonlinear bound, actual instrument noise or calibrated confidence.
No aircraft fit, accuracy screen or reserved confirmation group changes.

[Frozen plan](PLAN.md) · [Construction checks](../noisy-prediction-benchmark/nonlinear-construction-qualification/README.md) ·
[Noise benchmark](../noisy-prediction-benchmark/README.md) · [Next analyses](../NEXT_STEPS.md).
