# What explains the correction to each saved ESA forecast?

Reuse the earlier-only changing-drift range seal and the same 24 starts on
ESA development recording 187. Preserve the four numerical failures. For
every passing start, use its first 400 residuals and both prior receiver
weighting cases. Evaluate the one-step prediction errors in units of their
declared uncertainty and report the full history and each fixed quarter.

Separate the correction into six components of the supplied law: white
receiver error, receiver offset, receiver random walk, and the inertial error
drivers on velocity, acceleration and jerk (three separate drivers). Report
each component's contribution to the squared standardized training error and
to the mean future correction. The last three terms are mathematical inertial
discrepancy terms. Their allocation does not identify the physical cause.

Check the decomposition against the original linear innovations operator. Its
training contributions must sum to the original squared standardized errors,
and its future contributions must reproduce the sealed conditional mean.
Independently verify the algorithm against a small direct covariance calculation.
Do not read any later receiver positions, change the original law or fit a model.

Freeze two operator constructions, at most 48 history evaluations, 400 earlier
reports per history, four integration nodes per interval and one numerical thread.
Bind the earlier observations, forecasts, range seal, source and environment.
Treat results as an error-budget diagnostic under one law, with no fitted
reference distribution, p-value, coverage or Earth-model decision.
