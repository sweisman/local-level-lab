# ESA earlier-data-conditioned forecast check

**Question.** Does the declared IMU-plus-receiver error law predict the 400
later GPS reports better when its fixed-parameter stochastic error state is
conditioned on the 800 earlier GPS errors? The preceding comparison scored
only the uncorrected IMU trajectory. A conditional receiver prediction is a
different quantity under this error law.

Use the sealed 20-minute ESA development recording, its saved weighted fit,
saved uncorrected forecast and early GPS rows. Keep the physical model,
packet-header clock, 26 calibration coordinates, noise law, receiver policy,
split and source environment unchanged. Rebuild the error operator for the
whole interval with **receiver noise included at later times**. Verify that
its early covariance prefix matches the sealed training operator. Apply the
800 saved early receiver-minus-trajectory errors to the operator, then save
the 400 conditional receiver means and their fixed-parameter marginal
variances. Do not refit or use a later GPS value during that calculation.

A separate saved-only reporter opens the already sealed later GPS rows and
scores both the conditional means and the original uncorrected trajectory.
Report horizontal and vertical RMS, the conditional adjustment size and
whether the preset physical-accuracy screen passes. The receiver reports are
an imperfect proxy for physical position. Do not call the assumed variances
calibrated coverage or attach an Earth-model conclusion. Keep the scientific
decision **abstain** regardless of which forecast is closer.

This is one finite, reboot-resumable development task on recording 187. Freeze
its exact inputs and source/environment hashes, at most one numerical thread,
no optimization, and a cooperative two-hour limit. Budget at most 600,000
native calls and 6 billion packet visits; stop without expanding the allowance
if either limit is reached. Qualify exact early-only provenance, prefix
identity, longitude wrapping, no later input, physical units, corruption
rejection, and task-level interruption recovery before launch. The seven
reserved ESA flight groups stay closed.
