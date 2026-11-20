# Where the ESA development forecast misses

This saved-data check compares the two already sealed forecasts with the same
400 later GPS receiver positions. It makes no fit or correction. The two
candidate IMU error laws give nearly identical errors, so the table shows the
increment-law forecast; the [machine-readable audit](drift-audit.json) retains
both. The reporter verifies the sealed result, forecast split and receiver
rows before calculating errors.

| Direction | Training RMS | Later RMS | Later error trend |
|---|---:|---:|---:|
| North | 9.25 m | 37.63 m | +3.16 m/min |
| East | 38.88 m | 246.56 m | −41.59 m/min |
| Height | 1.40 m | 4.35 m | +2.14 m/min |

The last **121 training positions**, spanning 120 seconds, already show an
east-error trend of **−23.60 m/min**. Extrapolating that training-only line
predicts about −109.10 m at the first later position, close to the observed
−110.47 m. At the last later position it predicts −266.03 m, while the
observed error is −387.42 m. The error therefore grows faster after the
split; there is no large east-error jump at the first withheld point in this
simple check. This does not establish what changed in the aircraft or model.

The receiver reports mean ground speed of **91.68 m/s** in the final training
tail and **93.90 m/s** later (about 330 and 338 km/h). Mean vertical speed is
near zero in both periods. The later error growth is therefore present during
a roughly level, somewhat faster part of this recording; these averages do
not rule out shorter aircraft maneuvers or identify an inertial calibration
error.

Both saved fits passed their numerical stopping check in nine evaluations,
with no calibration bound marked active. Neither fit establishes that its
individual parameters are identifiable. Their **training horizontal error is
already about 40 m RMS**, above the preset 10 m training limit. The first
priority is therefore to explain the training mismatch under the existing
observation model. A better extrapolation rule alone cannot make that fit
adequate.
For the increment law, the saved weighted residual sum of squares is 13.24
over 2,400 training coordinate components. That small weighted objective
coexists with the 40 m horizontal error because the working uncertainty law
and the physical accuracy screen answer different questions. It does not
establish that the uncertainty law describes this aircraft correctly.

As a numerical handoff check, the reporter compares each saved native
training-coordinate difference with the corresponding saved forecast position
minus the receiver position. The largest mismatch is below **0.000000001 m**
for either error law. Thus saving/casting the forecast did not create the
40 m training miss; this check does not validate the physical model or
calibration.

Over the 399-second later period, the east error moves from about −110 m to
−387 m. A straight line describes **99.2% of the variation** in those east
errors. It is a description made after observing the later positions; its
slope was **not known from training** and cannot be applied as a valid
prediction correction. North and height also trend, but east dominates the
horizontal miss.

The close agreement of the two error-law forecasts shows that choosing
between these two laws alone will not remove the observed miss. The initial
east error agrees with the training-tail extrapolation, but its later growth
still needs explanation. A next development check should test candidate
motion, timing and calibration explanations for the training mismatch on generated
known-answer controls before fitting another observed recording. This audit
does not identify the cause or establish Earth-model evidence.

[Completed continuation](CONTINUATION_RESULT.md) ·
[GPS-only reference](RECEIVER_REFERENCE_RESULT.md) ·
[Generated-error comparison](TRAINING_ADEQUACY_COMPARISON.md) ·
[Saved-only reporter](../../analysis/lll/prediction_observed_drift_report.py).
