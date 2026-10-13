# Actual-position stability qualification

The previous boundary-aware trial passed 17/24 fits. Six failures already satisfy
the gradient criterion but fail a local residual-movement threshold; one remains
nonstationary at its evaluation ceiling. Repeated starts reconstruct nearly identical
tracks despite different stopping outcomes.

## Numerical change

Keep the bounded nonlinear stepping method, physical models, nuisance bounds,
nominal 200 Hz timing, shared receiver covariance and processing cases unchanged.
Replace only the final stability rule with a fresh full-model correction that requires:

- The original and corrected points both pass the existing 1e-4 gradient criterion.
- Actual squared-error change is no larger than the existing 1e-8 relative limit.
- Actual receiver-position change is at most 0.001 m RMS on each axis.
- No individual receiver-position change exceeds 0.01 m on any axis.

The physical limits measure numerical repeatability, not receiver accuracy or
statistical uncertainty. Use the same receiver-local conversion to metres for every
candidate, undoing the shared covariance whitening. Save the local prediction and
actual changes; no local residual-movement prerequisite may prevent the fresh check.
Verify conversion against direct native predictions on independent motion controls.

## Frozen archival comparison

Reuse the same preselected three unfinished stretches and completed control:
15 unfinished primary tasks, six controls and three predetermined perturbed repeats.
Start every task from the corresponding **primary endpoint of the completed
boundary-aware trial**; apply the same fixed 0.01 perturbation for repeats.
Use all primary endpoints, irrespective of convergence or model cost, without
choosing the most favorable earlier method or repeat. Hash the complete prior
summary and journals. Original first-pass converged fits are reused for the other
comparisons, and their labels remain unchanged.

The new study permits **24 starts / 14,448 native sweeps maximum**, with 600 fitting
calls and two saved-track predictions per start. No retries, replacement starts or
budget expansion. Interrupted starts remain charged and unresolved. One worker with
two total numerical threads. The inherited first-pass ceiling estimate is 10–14 hours;
many endpoint checks may finish sooner, but runtime is not guaranteed.

Qualification requires all 24 tasks to pass their checks. Completed controls must
agree with the previous primary endpoint within 1e-6 relative objective and 0.01 m
axis-specific track RMS. Each repeat must pass independently and agree with its new
primary under those same limits. No result is promoted solely because its track is
close to an earlier result. A remaining budget failure prevents qualification.

## Evidence and continuation

Seal software tests before freezing the new worker. Preserve source snapshots,
environment, original-file hashes, task identities, precharged journals, saved
tangents and receiver-epoch errors. Changed inputs or code require a new freeze.
Exclusive locks prevent duplicate workers; completed studies cannot restart.

Publish results automatically after completion. Numerical qualification alone does
not establish global optima, physical adequacy or calibrated significance. Preserve
the original 12 globe preferences, zero completed flat preferences and 41 unresolved
labels pending qualified recovery. A full-41 study needs its own finite freeze.
