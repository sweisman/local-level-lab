# Corrected single-pass ESA conditional forecast

The [preceding single-pass attempt](CONDITIONAL_FORECAST_V2_RESULT.md) compared
a prefix-matrix hash with the training operator's full-stream hash. Those are
distinct hash definitions. Its terminal technical failure is retained.

A separately frozen task will keep the same ESA development recording,
800/400 split, saved fit, raw trajectory, physical model, clock, error law,
calibration bounds and full-operator single pass. It will verify every early
input hash, then compare the full operator's 800-epoch prefix with the sealed
training operator using quantities defined for **both**: the Gaussian
log-determinant and the whitened cost of the saved 800 early residuals. Both
must match their saved values under declared numerical tolerances. This
checks the actual training covariance without equating unlike hashes.

Only after that replay passes may the task condition the full operator on
the saved early residuals and save 400 conditional receiver means. A separate
reporter scores the later GPS rows. No later value enters the worker; no fit,
model selection or scientific detection is made. The decision remains
**abstain**, and seven ESA confirmation groups remain reserved.

This task has one start, one numerical thread, a one-hour cooperative limit,
at most 450,000 native calls and 1 billion packet visits. The prior terminal
tasks and their charges remain immutable. Qualify the matched-prefix replay,
cost sensitivity, early-only conditioning and interruption recovery before
launch.
