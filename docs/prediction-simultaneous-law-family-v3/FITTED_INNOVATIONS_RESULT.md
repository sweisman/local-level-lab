# Fitted error pattern in the generated recordings

The [saved-data audit](FITTED_INNOVATIONS_PLAN.md) checked all **96 completed
generated recordings** after verifying the archived continuation and its source
snapshots. It read both saved fits for each recording and repeated no fits.
Of 192 fits, 190 passed their numerical checks. The two failures belong to
one recording, so 95 recordings contribute fitted error patterns.

| Height error after whitening | Increment law | Point law |
|---|---:|---:|
| Median correlation one report apart | −0.043 | −0.043 |
| Median correlation 20 reports apart | −0.005 | −0.005 |
| Largest absolute one-report correlation across a recording | 0.286 | 0.286 |

Both laws produced the same fitted training errors in this cohort. The median
height RMS after whitening was 0.950 for either law. Across the 95 recordings,
the 95th percentile of the larger absolute one-report correlation was 0.251.
The corresponding [ESA training diagnostic](../prediction-observed-development/TRAINING_INNOVATION_RESULT.md)
found height correlations of **0.825** one report apart and **0.538** twenty
reports apart, with whitened RMS **0.077** under both laws.

This contrast makes the persistent ESA height pattern a concrete target for a
matched known-answer control. It is **not** a calibrated rejection of either
aircraft error law: the generated fits used 79 earlier receiver reports, the
ESA fit used 600, and the generated and observed error processes differ.
Fitted residuals also depend on the parameters estimated from those same
reports. The next control must reproduce the ESA sampling and complete fitting
procedure, then measure how often known-answer fits produce a pattern this
strong. The seven reserved ESA groups remain unopened.

[Machine-readable audit](fitted-innovations-result.json) ·
[Original generated coverage result](RESULT.md)
