# Testing the earlier loss directly leaves the forecast bound unchanged

On the ESA development flight, the upper bound on how far calibration
changes could move the zero-field globe and disc forecast scores remains
**53.04 units**. The original forecast gap is **25.41 units**. The bound
leaves open whether a calibration that fits the earlier observations can
erase the gap.

| Candidate | Ranges checked | Score thresholds checked | Thresholds ruled out | Retained upper bound |
| --- | ---: | ---: | ---: | ---: |
| Zero-field globe | 5 | 20 | 0 | 20.637 |
| Zero-field disc | 6 | 24 | 0 | 32.401 |

The [frozen plan](ESA_LINKED_SCORE_FLOOR_PLAN.md) tested four thresholds per
range. To rule one out, the calculation needed an exact proof that the
earlier loss allowance and the proposed forecast-score threshold could
never both hold. None of the 44 checks produced that proof. The numerical
minimizer reported success on 2 of 44 proposals. Its status alone could
neither rule out a threshold nor establish a feasible calibration. Four
disc ranges still have upper bounds larger than the forecast gap.

All 11 tasks completed in 125 seconds, with 88 charged bound checks and
no new trajectory fits. The checked points from the earlier full integration
remain unchanged. The nonlinear integration error and the aircraft
prediction-error model still need independent bounds before a confirmation
study can use this comparison.

[Per-range results](esa-linked-score-floor-result.json) ·
[Source and execution receipts](esa-linked-score-floor-evidence/README.md) ·
[Reproduction bundle](esa-linked-score-floor-evidence/bundle.zip)
