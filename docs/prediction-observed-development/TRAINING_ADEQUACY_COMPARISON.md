# Do the generated errors resemble the ESA development miss?

The completed [24-case generated noisy study](../esa-noisy-prediction/README.md)
fits each candidate to its **own known-answer trajectory**. It uses declared
synthetic sensor and receiver errors, including changing bias. The completed
[ESA development continuation](CONTINUATION_RESULT.md) uses recorded IMU and
receiver observations. This saved-data comparison reads both sealed results;
it makes no new fit or propagation.

| Source | Training horizontal RMS | Later horizontal RMS | Passes preset accuracy |
|---|---:|---:|---:|
| 24 generated cases, range | 2.25–3.19 m | 83.55–88.59 m | 24/24 training; 0/24 later |
| ESA development recording, either error law | about 39.96 m | about 249.41 m | neither training nor later |

The observed training miss is over **12 times** the largest miss in this
generated matrix. The generated controls already show that numerical
convergence does not ensure an accurate several-minute prediction: every
generated case misses the later accuracy limit. The recorded case misses
more severely and fails even during training.

This is **not a matched noise experiment**. The generated paths, latitude,
processing assumptions and one fixed random realization differ from the
recording. The synthetic levels are not measured iMAR specifications. The
comparison therefore cannot attribute the recorded mismatch to sensor noise,
timing, mounting, receiver error or the physical model. It does show that
the existing synthetic matrix does not reproduce the observed training-error
scale, so its passing training checks cannot qualify this recording's
observation model.

Next, test the recorded rate-to-increment and timing interpretations against
independent motion/receiver checks and known-answer variants. Keep the
development recording separate from the seven protected ESA confirmation
groups. No Earth-model decision is made here.

The [machine-readable audit](drift-audit.json) binds both studies by manifest
and summary SHA-256, and records the full score ranges. The [saved reporter](../../analysis/lll/prediction_observed_drift_report.py)
recomputes them from sealed artifacts.
