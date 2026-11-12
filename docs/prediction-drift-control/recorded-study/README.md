# Can earlier residuals predict the later drift?

This saved-data development check kept the original 36 settings and their training-cost-selected starts. Twenty-eight had a qualified start; eight remained numerical abstentions. No Earth-model fit, original IMU read or protected ESA recording was added.

The only new correction used the final two minutes of earlier receiver residuals. Its mean and straight-line trend were fixed before looking at the later score. The original model predictions and their accuracy labels remain unchanged.

| Candidate | Qualified / 12 | Constant: median later horizontal RMS ratio | Linear: median later horizontal RMS ratio | Linear improved / worsened |
|---|---:|---:|---:|---:|
| globe with specified field | 9 / 12 | 1.004 | 1.012 | 2 / 7 |
| globe with zero field | 9 / 12 | 1.035 | 0.820 | 9 / 0 |
| stationary disc | 10 / 12 | 1.045 | 0.835 | 10 / 0 |

A ratio below one means the empirical correction reduced that setting’s withheld error; above one means it made it worse. The median horizontal RMS before and after the linear correction is globe with specified field: 2.18 to 2.21 m; globe with zero field: 496.29 to 494.87 m; stationary disc: 585.62 to 488.85 m. The verified report also gives height and three-dimensional errors and every individual setting. The three recordings are retrospective development data. A correction can absorb physical-model mismatch or shared receiver error, so lower corrected error is not evidence for an Earth model. The earlier residuals were themselves left after the original training fit. This check tests predictability of one simple drift rule, not a calibrated uncertainty law.

The finite study, source and environment hashes, original scores, all abstentions and recovery qualification are in the sealed study evidence. Reproduce this report with `~/venv/bin/python -m lll.prediction_drift_audit`.
