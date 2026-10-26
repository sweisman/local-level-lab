# Why calibration stopped

**Both starts of one required setting failed the numerical cost-stability check.**
The phase therefore stopped under its predeclared rule; validation did not start.

This review reads eight records selected before inspecting their fit details:
seven saved fits and one interrupted start. The failed pair is compared with
the preceding noise example and the available alternate-processing fit. No
observations were generated, no fits were rerun and no native calculations occurred.

| Saved check | Failed pair | Required limit |
|---|---:|---:|
| Evaluations used | 41 each | At most 200 |
| Fresh stationarity | About 0.0000356 | At most 0.0001 |
| Largest fresh-check position RMS change | About 0.225 mm | At most 1 mm |
| Largest fresh-check position change | About 0.482 mm | At most 10 mm |
| Relative cost change | About 0.000000827 | At most 0.00000001 |

The cost change is about 83 times its frozen tolerance. The predicted positions
pass their physical-error screens, but that does not override numerical
qualification. Both failed starts report “no positive predicted decrease.”
The preceding example passes all four selected starts; the available alternate
processing case also passes. The interrupted flat-model start has no completed
fit and is not treated as a numerical or physical model failure.

The reusable saved-record reader and reporting adapter passed seven software
checks. The immutable evidence snapshot preserves the request, exact selected
records, their hashes, reporting source and unchanged failed labels. Reproduction
uses `lll.prediction_phase_review.run` and the frozen request in a separate
working copy; the original one-review allowance is spent.

[Selected records CSV](results.csv) · [Review plan](PLAN.md) ·
[Phase outcome](../PREDICTION_PHASE_RESULTS.md) ·
[Calibration evidence](../prediction-calibration/README.md).
