# Estimate error size and persistence together

Keep all four turn-and-steady pairs, both instrument error descriptions and
the original held-back forecasts from the [fixed-variance persistence check](ESA_INNOVATION_PERSISTENCE_RESULT.md).
That check improved the score on every omitted window, but most squared-error
scores then fell below the working reference. It held the previously selected
variances fixed while learning dependence across time.

For each original fold, learn six quantities from its six donor windows.
Use one quiet variance per ordered innovation slot, one common increase
during motion, and two persistence times. Keep the 15-second motion response,
the variance-preserving transition and both additive covariance components.
Use the original log-variance limits of −5 to 5. Search quiet and motion
times between 0.25 and 256 seconds; the previous motion choices reached all
four 64-second grid ceilings. The longer range is a sensitivity test, with no
claim that an instrument has that memory. Keep the earlier zero-memory and
fixed-variance comparisons as separate baselines.

Use the archived donor settings with their selected quiet and motion times
for one start, and the same variances with one-second memory for the other.
Minimize the joint Gaussian log score. With each start, cap all scored
parameter vectors, including derivative probes, at 192. Keep the best
evaluated donor setting and record any evaluation cap, failed optimization,
or parameter at a limit. Seal the choice before reading omitted positions.

Score both omitted windows with the frozen parameters. Compare against the
saved diagonal and persistence scores and reproduce them independently.
Retain the original joint error reference and require all eight windows to
meet it under both error descriptions, with better held-back log score than
the fixed-variance persistence comparison. Treat this as a within-flight
test. An independent-flight rule still needs separate qualification.

Allow eight folds, two single-thread workers and a 240-second cooperative
limit. Bind the previously tested recovery and caps before execution. Use
no new trajectories, original measurement reads or reserved flights.
