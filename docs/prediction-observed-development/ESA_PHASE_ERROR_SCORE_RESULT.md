# The shape score is more sensitive to coordinated GPS errors

The saved carrier-phase path for ESA development flight 187 scored **−7.13**.
That favors the zero-field globe over the zero-field disc, with a tie at zero.
How far a GPS error moves that score depends on how it varies across satellites
and time.

| Assumed error pattern | Scale needed to reach the margin in the linearized score |
| --- | ---: |
| Independent range errors, one score standard deviation | 39.7 cm standard deviation per satellite observation |
| Bounded errors aligned in the worst possible pattern | 3.01 cm peak per satellite observation |
| Linear drift, with the worst combination of satellite signs | 5.87 m/min per satellite |

The calculation traces **1,038** half-second displacement steps back to the
carrier observations at their endpoints. Each shared observation enters
successive steps with opposite signs. Ignoring that cancellation and treating
step errors as independent would overstate the forecast-score standard
deviation by **3.83 times** under the independent-observation assumption.
A phase offset held constant for each satellite cancels. A range offset
common to all satellites at any given epoch also cancels through the fitted
receiver clock change.

These sensitivities apply to the original fixed paths and score. They supply
scales an aircraft error model needs to address. Actual phase error, errors
shared by the receiver solutions, and nonlinear calibration effects remain
unqualified. No new inertial fit, receiver solution or protected flight data
entered the study.

The task used one numerical thread and completed in 20 seconds. Six focused
tests passed. The linearized calculation reproduced all 12 earlier satellite
omission score shifts within 0.00000007 score units.

[Frozen method](ESA_PHASE_ERROR_SCORE_PLAN.md) ·
[Numerical results](esa-phase-error-score-result.json) ·
[Source and execution receipts](esa-phase-error-score-evidence/README.md) ·
[Reproduction bundle](esa-phase-error-score-evidence/bundle.zip)
