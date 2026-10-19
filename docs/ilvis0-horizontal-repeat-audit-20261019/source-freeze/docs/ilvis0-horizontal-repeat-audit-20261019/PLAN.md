# Saved-fit review of horizontal-only refits

Review every saved fit and all twelve primary/repeat pairs from the completed
two-recording horizontal-only study. Preserve its all-passing individual fits,
failed repeat checks, omitted-height trajectories and original 53-stretch tally.

Use no original recordings, native predictions or nonlinear optimizer starts.
At each of 24 saved endpoints compare the original bounded affine correction
with the same feasible problem expressed in available-range-scaled coordinates:
**48 affine solves maximum**, four numerical threads, two minutes. Retain every
column; use the parent's saved rank rather than rerunning singular decompositions.
Compare each proposed affine cost independently with the feasible zero step.

For every repeat pair report costs, prediction differences, normalized parameter
differences, timing offsets, distances to packet-clock boundaries, stop reasons,
call exhaustion and the local prediction of the other endpoint. Include passing
pairs as controls. Report horizontal and unscored-height RMS for all primary fits.

Freeze input/source/environment hashes and the exact 24 identities before
solving. Use an exclusive lock, durable per-endpoint charges and atomic results.
No retries, expansion or replay of completed work. Rendering saved results makes
no solves. Affine improvements do not relabel fits or establish native improvement.
Any following native diagnostic needs a separate finite freeze.
