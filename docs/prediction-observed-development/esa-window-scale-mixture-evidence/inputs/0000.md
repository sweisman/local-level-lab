# Test whether forecast error varies more from window to window

The [ESA forecast diagnostic](ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_RESULT.md)
found both excessive and unusually small residuals in different windows on
recording 187. A [test of motion before the forecast](ESA_PERSISTENCE_HISTORY_RESULT.md)
left the same two misses. Test whether a forecast error model with a single
random variance multiplier across each whole window predicts those errors
better than a fixed Gaussian model.

Keep the forecast mean and expected covariance from the
[donor-only covariance comparison](ESA_JOINT_PERSISTENCE_ANALYTIC_RESULT.md).
Give the multiplier an inverse-gamma distribution with mean one. The
resulting Student distribution has the same covariance as the Gaussian and
allows more variation in window-wide residual size. Its candidate degrees
of freedom are 10, 20, 40, 80, 160 and 320, plus the Gaussian limit.

For each of the four fixed omitted pairs and each of the two covariance
laws, choose one setting by summed normalized negative log likelihood on
the six earlier-design donor windows. Prefer Gaussian, then the largest
degrees of freedom, on ties. Save that choice before reading either
omitted window. Score both omitted windows with the chosen law and the
Gaussian reference. Record proper log scores and the model-based quadratic
reference at the original tail probabilities. Report improvement only
if the omitted-window score improves under each covariance law separately.
Keep all failed reference checks. This test uses overlapping development
folds from one flight and cannot qualify coverage or open the reserved flights.

Freeze the previous report, saved forecast inputs, source hashes, environment,
and independent density and quantile checks. Use eight tasks with two
one-thread workers, at most 25 score charges and 68 charged steps per task,
zero native trajectory evaluations and a 180-second cooperative wall
allowance. Preserve completed tasks. For a technical interruption use
the qualified shared task-recovery workflow, with one additional attempt
per unfinished task and a separate 180-second allowance.
