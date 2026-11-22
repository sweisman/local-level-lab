# Test one receiver error across the paired force comparisons

Use the 991 preselected windows from the two recorded force studies.
Keep the same onboard GPS fixes, both packet clocks, the four matched
geometry and field models, the earlier and later split, and each model's
frozen earlier-only accelerometer gain. This tests the existing lower
force inequalities under the existing shared receiver-error law.

For each recording, form linearized force changes on a single GPS
position error history. Include every window and scenario in that one
system. Project toward the largest remaining deficit in units of its
projected standard deviation, at most 64 times. A deficit above zero
gets a 0.00001 m/s² margin in the proposal to allow for linearization
error. Score the proposed GPS history by recomputing the original
outward force intervals in all windows. Report both the original
upper-bound check and the stronger lower-bound comparison. Preserve
all deficits and the shared correction in metres.

Use two one-thread tasks. Each charges one pass to form the sensitivities,
one projection allowance and one nonlinear scoring pass. Limit source
execution to 991 windows, both clocks and all four candidates each for
the sensitivity and scoring passes, and 128 projection steps total.
Set a 120-second cooperative limit. No original recordings, new inertial
fits or reserved ESA data are needed.

The error law is a sensitivity assumption. This uses later GPS windows
to check compatibility and leaves the earlier gains fixed. It supplies
neither a forecast nor a joint physically feasible inertial history.
The covariance norm describes the example, and an unsuccessful search
cannot exclude a model.
